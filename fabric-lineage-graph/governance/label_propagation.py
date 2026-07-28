"""Sensitivity-label propagation across the lineage graph.

Inputs:
  * NetworkX MultiDiGraph from `graph.build_graph`
  * `classifications`: dict[node_qname, list[classification_name]]
  * `seed_labels`:    dict[node_qname, label_name]  (optional)
  * `policy`:         loaded sensitivity-labels.yml from
                      fabric-sdlc-governance/contracts/labels/

Algorithm:
  1. For each node, compute its OWN label = highest-priority label matching
     its classifications via the policy's `auto_label_rules`. If none match,
     fall back to the seed label or the policy default.
  2. Topologically walk the graph; each downstream node inherits the MAX
     priority of (own_label, all_upstream_labels).
  3. Return dict[node_qname, label_name].

This mirrors how MIP would auto-classify scanned assets in Purview, but runs
deterministically against our local edges so tests stay reproducible.
"""
from __future__ import annotations
import pathlib
from typing import Any

import networkx as nx
import yaml


def load_policy(path: str | pathlib.Path) -> dict[str, Any]:
    return yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))


def _priority(policy: dict, label_name: str | None) -> int:
    if not label_name:
        return -1
    for lbl in policy["labels"]:
        if lbl["name"] == label_name:
            return int(lbl.get("priority", 0))
    return -1


def _own_label(classifications: list[str], rules: list[dict],
               default: str) -> str:
    cs = set(classifications)
    fallback = default
    for r in rules:
        if "default" in r:
            fallback = r["default"]
            continue
        any_cs = set(r.get("if_classifications_any", []))
        if any_cs & cs:
            return r["apply_label"]
    return fallback


def propagate(graph: nx.MultiDiGraph,
              classifications: dict[str, list[str]],
              policy: dict[str, Any],
              seed_labels: dict[str, str] | None = None,
              default_label: str = "Internal") -> dict[str, str]:
    seed_labels = seed_labels or {}
    rules = policy.get("auto_label_rules", [])

    own: dict[str, str] = {}
    for node in graph.nodes():
        cls = classifications.get(node, [])
        seed = seed_labels.get(node)
        chosen = _own_label(cls, rules, seed or default_label)
        # If the seed is higher priority than what classifications imply, keep seed.
        if seed and _priority(policy, seed) > _priority(policy, chosen):
            chosen = seed
        own[node] = chosen

    # Topological propagation. If there are cycles fall back to the per-node
    # iterative fixed-point (rare for lineage but defensive).
    try:
        order = list(nx.topological_sort(graph))
    except nx.NetworkXUnfeasible:
        order = list(graph.nodes())

    propagated = dict(own)
    changed = True
    iterations = 0
    while changed and iterations < len(order) + 5:
        changed = False
        for node in order:
            best = propagated[node]
            best_prio = _priority(policy, best)
            for pred in graph.predecessors(node):
                pred_lbl = propagated.get(pred, default_label)
                pred_prio = _priority(policy, pred_lbl)
                if pred_prio > best_prio:
                    best, best_prio = pred_lbl, pred_prio
            if best != propagated[node]:
                propagated[node] = best
                changed = True
        iterations += 1

    return propagated
