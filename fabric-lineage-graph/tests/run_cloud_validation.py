"""End-to-end validation runner for the CLOUD tier.

Unlike tests/run_validation.py (which exercises the easy/medium/complex local
file samples), this runner connects to the actual PaaS sources deployed by
samples/cloud/infra/deploy.ps1, harvests live lineage from each catalog,
propagates labels, evaluates the DLP gate, and renders the graph.

Usage:
    # After deploy.ps1 + run_all.py have run successfully:
    python -m tests.run_cloud_validation
    python -m tests.run_cloud_validation --only sql,pg,cosmos,declared

Expectations live in samples/cloud/seed_classifications.json. All asset paths
use ${ENV_VAR} placeholders which are resolved from .env.cloud at runtime.
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CLOUD_DIR = ROOT / "samples" / "cloud"
OUT_DIR = ROOT / "out" / "cloud"
ENV_FILE = ROOT / ".env.cloud"


def _load_env() -> None:
    if not ENV_FILE.exists():
        print(f"FATAL: {ENV_FILE} not found. Run samples/cloud/infra/deploy.ps1 first.")
        sys.exit(2)
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand(value: str) -> str:
    return _VAR.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)


def _expand_keys(d: dict) -> dict:
    return {_expand(k): v for k, v in d.items()}


def _green(s): return f"\033[32m{s}\033[0m"
def _red(s):   return f"\033[31m{s}\033[0m"
def _yel(s):   return f"\033[33m{s}\033[0m"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--only", help="Comma-separated subset: sql,pg,cosmos,oracle,declared")
    args = p.parse_args()

    _load_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    from harvesters.mssql_live import MssqlLiveHarvester
    from harvesters.postgres_live import PostgresLiveHarvester
    from harvesters.cosmos_live import CosmosLiveHarvester
    from harvesters.oracle_live import OracleLiveHarvester
    from harvesters.databricks_live import DatabricksLiveHarvester
    from harvesters.declared import DeclaredEdgesHarvester
    from graph.build_graph import build_graph
    from graph.render_pyvis import render
    from governance.label_propagation import propagate, load_policy
    from governance.column_propagation import (
        propagate_columns, flatten_column_classifications,
    )
    from governance.dlp_gate import evaluate as evaluate_dlp

    policy_path = ROOT.parent / "fabric-sdlc-governance" / "contracts" / "labels" / "sensitivity-labels.yml"
    policy = load_policy(policy_path)

    targets = set(args.only.split(",")) if args.only else {"sql", "pg", "cosmos", "oracle", "databricks", "declared"}
    runners = [
        ("sql",        lambda: MssqlLiveHarvester()),
        ("pg",         lambda: PostgresLiveHarvester()),
        ("cosmos",     lambda: CosmosLiveHarvester()),
        ("oracle",     lambda: OracleLiveHarvester()),
        ("databricks", lambda: DatabricksLiveHarvester()),
        ("declared",   lambda: DeclaredEdgesHarvester(CLOUD_DIR / "cross_system_edges.json")),
    ]

    all_edges = []
    per_source_counts: dict[str, int] = {}
    for name, factory in runners:
        if name not in targets:
            continue
        try:
            h = factory()
            edges = list(h.harvest())
            per_source_counts[name] = len(edges)
            all_edges.extend(edges)
            print(f"  {name:10} -> {len(edges):>4} edges")
        except Exception as exc:
            print(_red(f"  {name:10} FAILED: {exc!r}"))
            per_source_counts[name] = -1

    (OUT_DIR / "edges.json").write_text(
        json.dumps([e.to_row() for e in all_edges], indent=2, default=str),
        encoding="utf-8",
    )

    g = build_graph(all_edges)
    print(f"\nGraph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")

    seed = json.loads((CLOUD_DIR / "seed_classifications.json").read_text(encoding="utf-8"))
    classifications = _expand_keys(seed.get("classifications", {}))
    seed_labels = _expand_keys(seed.get("seed_labels", {}))
    expected_min = _expand_keys(seed.get("expected_labels_minimums", {}))

    labels = propagate(g, classifications=classifications, policy=policy, seed_labels=seed_labels)
    (OUT_DIR / "labels.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")

    # Column-level propagation (uses column_classifications when supplied).
    column_classifications = flatten_column_classifications(
        _expand_keys(seed.get("column_classifications", {}))
    )
    column_seed_labels_raw = seed.get("column_seed_labels", {})
    column_seed_labels = {
        (_expand(asset), col): lbl
        for asset, cols in column_seed_labels_raw.items()
        for col, lbl in cols.items()
    }
    column_labels = propagate_columns(g, column_classifications, labels, policy)
    (OUT_DIR / "column_labels.json").write_text(
        json.dumps(
            [{"asset": a, "column": c, "label": l} for (a, c), l in column_labels.items()],
            indent=2,
        ),
        encoding="utf-8",
    )

    violations = evaluate_dlp(
        g, labels, seed_labels, policy,
        column_labels=column_labels, column_seed_labels=column_seed_labels,
    )
    (OUT_DIR / "violations.json").write_text(json.dumps(violations, indent=2), encoding="utf-8")

    render(g, str(OUT_DIR / "graph.html"), column_labels=column_labels)

    # Count column edges to confirm column-level lineage actually fired.
    col_edge_count = sum(
        len(d.get("columns") or []) for _, _, d in g.edges(data=True)
    )
    print(f"Column-level edges: {col_edge_count}  (asset edges: {g.number_of_edges()})")

    # ---- Diff against expectations ----
    failures: list[str] = []
    for asset, min_label in expected_min.items():
        actual = labels.get(asset)
        if actual is None:
            failures.append(f"label[{asset}] missing (expected >= {min_label})")
            continue
        a_prio = next((l["priority"] for l in policy["labels"] if l["name"] == actual), -1)
        m_prio = next((l["priority"] for l in policy["labels"] if l["name"] == min_label), -1)
        if a_prio < m_prio:
            failures.append(f"label[{asset}] expected >= {min_label}, got {actual}")

    print(f"\nViolations:        {len(violations)}")
    for v in violations:
        print(f"  {_yel('[' + v['severity'].upper() + ']')} {v['rule']}: {v['asset']}")

    if failures:
        print(_red(f"\nFAILED: {len(failures)} expectation mismatch(es):"))
        for f in failures:
            print(_red(f"  - {f}"))
        print(f"\nArtifacts in {OUT_DIR}/")
        return 1

    print(_green(f"\nPASS — cloud-tier lineage + label propagation validated."))
    print(f"Artifacts in {OUT_DIR}/  (open graph.html in a browser)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
