"""DLP gate — turns propagated labels into actionable violations.

Rules (encoded as small functions so each is independently auditable):

  R1  label_downgrade_blocked
      If a node has a seed_label whose priority is LOWER than the propagated
      label, this is a downgrade attempt and must be flagged. Mirrors the
      Fabric/Purview DLP rule "Protected data cannot be relabeled lower".

  R2  highly_confidential_to_public_destination
      Any edge whose source label >= Highly-Confidential-Restricted feeding
      into a target whose seed/intent is Public is a violation regardless of
      propagation. Catches the "leak into a public mart" pattern.

  R3  pii_in_report_without_rls
      Any node with label >= Confidential-PII whose downstream kind is
      `powerbi_report` and is not annotated with `rls_enforced=true` in
      `extra` is flagged. (Annotation comes from the PowerBI harvester once
      implemented; for now, any PBI report consuming PII is flagged.)
"""
from __future__ import annotations
from typing import Any

import networkx as nx


def _prio(policy: dict, name: str | None) -> int:
    if not name:
        return -1
    for lbl in policy["labels"]:
        if lbl["name"] == name:
            return int(lbl.get("priority", 0))
    return -1


def evaluate(graph: nx.MultiDiGraph,
             labels: dict[str, str],
             seed_labels: dict[str, str],
             policy: dict[str, Any],
             column_labels: dict[tuple[str, str], str] | None = None,
             column_seed_labels: dict[tuple[str, str], str] | None = None) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    column_labels = column_labels or {}
    column_seed_labels = column_seed_labels or {}

    # R1 — downgrade blocked
    for node, seed in seed_labels.items():
        propagated = labels.get(node)
        if propagated and _prio(policy, seed) < _prio(policy, propagated):
            violations.append({
                "rule": "label_downgrade_blocked",
                "asset": node,
                "seed_label": seed,
                "propagated_label": propagated,
                "severity": "high",
                "remediation": (
                    f"Asset {node} is downstream of {propagated} data. "
                    f"Remove the seed label or restrict the upstream feed."
                ),
            })

    # R2 — highly-confidential into public destination
    for src, tgt in graph.edges():
        s_lbl = labels.get(src)
        t_seed = seed_labels.get(tgt)
        if _prio(policy, s_lbl) >= _prio(policy, "Highly-Confidential-Restricted") \
                and t_seed == "Public":
            violations.append({
                "rule": "highly_confidential_to_public_destination",
                "asset": tgt,
                "upstream": src,
                "upstream_label": s_lbl,
                "severity": "critical",
                "remediation": (
                    f"Edge {src} -> {tgt} moves Highly-Confidential data into "
                    f"a Public-intent target. Block the pipeline."
                ),
            })

    # R3 — PII flowing into Power BI reports
    pii_prio = _prio(policy, "Confidential-PII")
    for node, data in graph.nodes(data=True):
        if data.get("kind") != "powerbi_report":
            continue
        if _prio(policy, labels.get(node)) < pii_prio:
            continue
        rls = data.get("extra", {}).get("rls_enforced", "false").lower() == "true"
        if not rls:
            violations.append({
                "rule": "pii_in_report_without_rls",
                "asset": node,
                "label": labels.get(node),
                "severity": "medium",
                "remediation": (
                    f"Power BI report {node} consumes PII without row-level "
                    f"security. Add RLS roles or restrict the dataset."
                ),
            })

    # R4 — column-level downgrade blocked.
    # Per-column equivalent of R1: any column whose propagated label is
    # higher-priority than its declared seed label is a downgrade attempt.
    for (asset, col), seed in column_seed_labels.items():
        propagated = column_labels.get((asset, col))
        if propagated and _prio(policy, seed) < _prio(policy, propagated):
            violations.append({
                "rule": "column_label_downgrade_blocked",
                "asset": asset,
                "column": col,
                "seed_label": seed,
                "propagated_label": propagated,
                "severity": "high",
                "remediation": (
                    f"Column {asset}.{col} is downstream of {propagated} "
                    f"data. Remove the column seed label or restrict the upstream feed."
                ),
            })

    # R5 — sensitive column landing in a Public-intent column.
    # Walks edge column-maps directly so per-column flows produce per-column
    # violations even when the asset-level R2 doesn't fire.
    hcr_prio = _prio(policy, "Highly-Confidential-Restricted")
    for src, tgt, data in graph.edges(data=True):
        for pair in data.get("columns") or []:
            if len(pair) != 2:
                continue
            src_col, tgt_col = pair
            s_lbl = column_labels.get((src, src_col))
            t_seed = column_seed_labels.get((tgt, tgt_col))
            if (
                _prio(policy, s_lbl) >= hcr_prio
                and t_seed == "Public"
            ):
                violations.append({
                    "rule": "column_highly_confidential_to_public",
                    "asset": tgt,
                    "column": tgt_col,
                    "upstream": src,
                    "upstream_column": src_col,
                    "upstream_label": s_lbl,
                    "severity": "critical",
                    "remediation": (
                        f"Column flow {src}.{src_col} -> {tgt}.{tgt_col} moves "
                        f"Highly-Confidential data into a Public-intent column. "
                        f"Block the pipeline."
                    ),
                })

    return violations
