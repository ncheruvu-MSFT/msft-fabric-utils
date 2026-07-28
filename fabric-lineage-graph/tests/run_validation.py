"""End-to-end validation runner — runs the easy / medium / complex sample
tiers locally (no Fabric/Purview required) and writes a verdict per tier.

Each tier:
  1. Runs TsqlHarvester over samples/<tier>/**/*.sql
  2. Runs NotebookHarvester over samples/<tier>/**/*.py
  3. Builds the NetworkX graph
  4. Propagates MIP labels using the seed classifications + the
     contracts/labels/sensitivity-labels.yml policy from fabric-sdlc-governance
  5. Evaluates the DLP gate
  6. Diffs actuals against expected_* in samples/<tier>/seed_classifications.json
  7. Renders an interactive PyVis graph to out/<tier>/graph.html

Exits non-zero if any tier fails its expectations.

Usage:
    python -m tests.run_validation                 # all tiers
    python -m tests.run_validation --tier easy
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harvesters.tsql import TsqlHarvester  # noqa: E402
from harvesters.notebook import NotebookHarvester  # noqa: E402
from graph.build_graph import build_graph  # noqa: E402
from graph.render_pyvis import render  # noqa: E402
from governance.label_propagation import propagate, load_policy  # noqa: E402
from governance.dlp_gate import evaluate as evaluate_dlp  # noqa: E402


POLICY_PATH = (
    ROOT.parent / "fabric-sdlc-governance" / "contracts" / "labels"
    / "sensitivity-labels.yml"
)


def _green(s: str) -> str: return f"\033[32m{s}\033[0m"
def _red(s: str) -> str: return f"\033[31m{s}\033[0m"
def _yel(s: str) -> str: return f"\033[33m{s}\033[0m"


def run_tier(tier: str, policy: dict) -> dict:
    sample_dir = ROOT / "samples" / tier
    out_dir = ROOT / "out" / tier
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_file = sample_dir / "seed_classifications.json"
    seed = json.loads(seed_file.read_text(encoding="utf-8")) if seed_file.exists() else {}

    # 1+2. Harvest
    tsql_edges = list(TsqlHarvester(sample_dir).harvest())
    nb_edges = list(NotebookHarvester(sample_dir).harvest())
    all_edges = tsql_edges + nb_edges

    (out_dir / "edges.json").write_text(
        json.dumps([e.to_row() for e in all_edges], indent=2, default=str)
    )

    # 3. Graph
    g = build_graph(all_edges)

    # 4. Propagate labels
    labels = propagate(
        g,
        classifications=seed.get("classifications", {}),
        policy=policy,
        seed_labels=seed.get("seed_labels", {}),
    )
    (out_dir / "labels.json").write_text(json.dumps(labels, indent=2))

    # 5. DLP gate
    violations = evaluate_dlp(g, labels, seed.get("seed_labels", {}), policy)
    (out_dir / "violations.json").write_text(json.dumps(violations, indent=2))

    # 6. Render
    render(g, str(out_dir / "graph.html"))

    # 7. Diff vs expectations
    failures: list[str] = []

    exp_tsql = seed.get("expected_edges_tsql", seed.get("expected_edges"))
    if exp_tsql is not None and len(tsql_edges) != exp_tsql:
        failures.append(f"expected {exp_tsql} T-SQL edges, got {len(tsql_edges)}")

    exp_nb = seed.get("expected_edges_notebook")
    if exp_nb is not None and len(nb_edges) != exp_nb:
        failures.append(f"expected {exp_nb} notebook edges, got {len(nb_edges)}")

    for asset, expected in seed.get("expected_labels", {}).items():
        actual = labels.get(asset)
        if actual != expected:
            failures.append(f"label[{asset}] expected={expected} actual={actual}")

    for asset, min_label in seed.get("expected_labels_minimums", {}).items():
        actual = labels.get(asset)
        if actual is None:
            failures.append(f"label[{asset}] missing (expected >= {min_label})")
            continue
        a_prio = next((l["priority"] for l in policy["labels"] if l["name"] == actual), -1)
        m_prio = next((l["priority"] for l in policy["labels"] if l["name"] == min_label), -1)
        if a_prio < m_prio:
            failures.append(f"label[{asset}] expected >= {min_label}, got {actual}")

    expected_violations = seed.get("expected_violations", [])
    for ev in expected_violations:
        match = [v for v in violations
                 if v["asset"] == ev["asset"] and v["rule"] == ev["rule"]]
        if not match:
            failures.append(f"expected violation {ev['rule']} on {ev['asset']} not found")

    return {
        "tier": tier,
        "tsql_edges": len(tsql_edges),
        "nb_edges": len(nb_edges),
        "nodes": g.number_of_nodes(),
        "labels": labels,
        "violations": violations,
        "failures": failures,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tier", choices=["easy", "medium", "complex"],
                   help="Run only the named tier (default: all)")
    args = p.parse_args()

    if not POLICY_PATH.exists():
        print(_red(f"Policy file not found: {POLICY_PATH}"))
        print("Expected at fabric-sdlc-governance/contracts/labels/sensitivity-labels.yml")
        return 2

    policy = load_policy(POLICY_PATH)

    tiers = [args.tier] if args.tier else ["easy", "medium", "complex"]
    overall_ok = True
    for tier in tiers:
        print(f"\n=== Tier: {tier} ===")
        res = run_tier(tier, policy)
        print(f"  edges:      tsql={res['tsql_edges']:>2}  notebook={res['nb_edges']:>2}  nodes={res['nodes']:>2}")
        print(f"  violations: {len(res['violations'])}")
        for v in res["violations"]:
            print(f"    {_yel('[' + v['severity'].upper() + ']')} {v['rule']}: {v['asset']}")
        if res["failures"]:
            overall_ok = False
            print(_red(f"  FAILED ({len(res['failures'])}):"))
            for f in res["failures"]:
                print(_red(f"    - {f}"))
        else:
            print(_green("  PASS"))
        print(f"  artifacts: out/{tier}/")

    print()
    print(_green("ALL TIERS PASSED") if overall_ok else _red("FAILURES PRESENT"))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
