"""Unit tests for label propagation + DLP gate."""
from __future__ import annotations
import pathlib

import networkx as nx
import pytest

from governance.label_propagation import propagate, load_policy
from governance.dlp_gate import evaluate

POLICY = load_policy(
    pathlib.Path(__file__).resolve().parents[2]
    / "fabric-sdlc-governance" / "contracts" / "labels" / "sensitivity-labels.yml"
)


def _g(edges):
    g = nx.MultiDiGraph()
    for s, t in edges:
        g.add_node(s); g.add_node(t)
        g.add_edge(s, t)
    return g


def test_pii_propagates_to_downstream():
    g = _g([("src", "mid"), ("mid", "tgt")])
    labels = propagate(g, {"src": ["MICROSOFT.PERSONAL.EMAIL"]}, POLICY)
    assert labels["src"] == "Confidential-PII"
    assert labels["mid"] == "Confidential-PII"
    assert labels["tgt"] == "Confidential-PII"


def test_higher_priority_wins_over_lower():
    g = _g([("pii", "join"), ("hr", "join")])
    labels = propagate(g, {
        "pii": ["MICROSOFT.PERSONAL.EMAIL"],
        "hr":  ["HR_COMPENSATION"],
    }, POLICY)
    assert labels["join"] == "Highly-Confidential-Restricted"


def test_dlp_flags_downgrade_attempt():
    g = _g([("pii_src", "pub_tgt")])
    labels = propagate(g, {"pii_src": ["MICROSOFT.PERSONAL.EMAIL"]}, POLICY,
                       seed_labels={"pub_tgt": "Public"})
    violations = evaluate(g, labels, {"pub_tgt": "Public"}, POLICY)
    rules = {v["rule"] for v in violations}
    assert "label_downgrade_blocked" in rules


def test_dlp_flags_highly_confidential_to_public():
    g = _g([("hr_src", "pub_dest")])
    labels = propagate(g, {"hr_src": ["HR_COMPENSATION"]}, POLICY,
                       seed_labels={"pub_dest": "Public"})
    violations = evaluate(g, labels, {"pub_dest": "Public"}, POLICY)
    assert any(v["rule"] == "highly_confidential_to_public_destination" for v in violations)
