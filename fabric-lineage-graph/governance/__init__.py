"""Governance layer — label propagation, DLP gate, Purview/Fabric label push."""
from .label_propagation import propagate, load_policy
from .dlp_gate import evaluate as evaluate_dlp
from .push_labels import push_purview_classifications, push_fabric_labels

__all__ = [
    "propagate", "load_policy",
    "evaluate_dlp",
    "push_purview_classifications", "push_fabric_labels",
]
