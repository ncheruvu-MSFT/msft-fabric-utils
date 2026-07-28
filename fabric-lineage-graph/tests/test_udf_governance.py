"""Tests for the governance push/sync layer — Purview classifications and
the Entra-group <-> Purview-policystore binding. All HTTP is mocked so the
suite runs offline.
"""
from __future__ import annotations
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# push_purview_classifications
# ---------------------------------------------------------------------------

def test_push_purview_classifications_posts_label_type():
    from governance.push_labels import push_purview_classifications

    # Create one fake session: first POST is the search, second is the
    # classification. We use side_effect with response stubs.
    search_resp = MagicMock(status_code=200)
    search_resp.json.return_value = {"value": [{"id": "guid-1"}]}

    classify_resp = MagicMock(status_code=204)

    fake_session = MagicMock()
    fake_session.post.side_effect = [search_resp, classify_resp]

    with patch("governance.push_labels._session", return_value=fake_session), \
         patch("governance.push_labels._atlas_base", return_value="https://x/atlas"), \
         patch("governance.push_labels._headers", return_value={}):
        counts = push_purview_classifications({"q/name": "Confidential-PII"})

    assert counts == {"ok": 1, "fail": 0, "skip": 0}
    # second call body has the right classification name
    call_args = fake_session.post.call_args_list[1]
    body = call_args.kwargs["json"]
    assert body[0]["typeName"] == "LABEL_CONFIDENTIAL_PII"
    assert body[0]["propagate"] is True


def test_push_purview_classifications_skips_missing_asset():
    from governance.push_labels import push_purview_classifications

    search_resp = MagicMock(status_code=200)
    search_resp.json.return_value = {"value": []}

    fake_session = MagicMock()
    fake_session.post.side_effect = [search_resp]

    with patch("governance.push_labels._session", return_value=fake_session), \
         patch("governance.push_labels._atlas_base", return_value="https://x/atlas"), \
         patch("governance.push_labels._headers", return_value={}):
        counts = push_purview_classifications({"missing/qname": "Internal"})

    assert counts == {"ok": 0, "fail": 0, "skip": 1}


# ---------------------------------------------------------------------------
# ensure_group_on_collection
# ---------------------------------------------------------------------------

def _fake_policy_with_role(role_token="reader", existing_principals=None):
    return {
        "properties": {
            "attributeRules": [
                {
                    "id": f"permission:{role_token}",
                    "dnfCondition": [
                        [
                            {
                                "attributeName": "principal.microsoft.id",
                                "attributeValueIncludedIn": list(
                                    existing_principals or []
                                ),
                            },
                            {
                                "attributeName": "resource.purview.collection",
                                "attributeValueIncludes": "demo",
                            },
                        ]
                    ],
                }
            ]
        }
    }


def test_ensure_group_on_collection_adds_principal():
    from api import udf_entra_sync

    get_resp = MagicMock(status_code=200)
    get_resp.json.return_value = _fake_policy_with_role()
    put_resp = MagicMock(status_code=200)

    with patch("api.udf_entra_sync.requests.get", return_value=get_resp) as g, \
         patch("api.udf_entra_sync.requests.put", return_value=put_resp) as p, \
         patch("api.udf_entra_sync._purview_hdr", return_value={}):
        out = udf_entra_sync.ensure_group_on_collection(
            "group-oid-1", "demo", role="collection-reader"
        )

    assert out["status"] == "bound"
    g.assert_called_once()
    p.assert_called_once()
    # Verify the PUT body included our new principal.
    put_body = p.call_args.kwargs["json"]
    matchers = put_body["properties"]["attributeRules"][0]["dnfCondition"][0]
    principal_matcher = next(
        m for m in matchers if m["attributeName"] == "principal.microsoft.id"
    )
    assert "group-oid-1" in principal_matcher["attributeValueIncludedIn"]


def test_ensure_group_on_collection_idempotent_when_already_bound():
    from api import udf_entra_sync

    get_resp = MagicMock(status_code=200)
    get_resp.json.return_value = _fake_policy_with_role(
        existing_principals=["group-oid-1"]
    )

    with patch("api.udf_entra_sync.requests.get", return_value=get_resp), \
         patch("api.udf_entra_sync.requests.put") as p, \
         patch("api.udf_entra_sync._purview_hdr", return_value={}):
        out = udf_entra_sync.ensure_group_on_collection(
            "group-oid-1", "demo", role="collection-reader"
        )

    assert out["status"] == "already_bound"
    p.assert_not_called()


def test_ensure_group_on_collection_reports_missing_role():
    from api import udf_entra_sync

    get_resp = MagicMock(status_code=200)
    get_resp.json.return_value = _fake_policy_with_role(role_token="reader")

    with patch("api.udf_entra_sync.requests.get", return_value=get_resp), \
         patch("api.udf_entra_sync.requests.put") as p, \
         patch("api.udf_entra_sync._purview_hdr", return_value={}):
        out = udf_entra_sync.ensure_group_on_collection(
            "g", "demo", role="data-curator"
        )

    assert out["status"] == "role_not_found"
    p.assert_not_called()


def test_ensure_group_on_collection_handles_missing_collection():
    from api import udf_entra_sync

    get_resp = MagicMock(status_code=404)

    with patch("api.udf_entra_sync.requests.get", return_value=get_resp), \
         patch("api.udf_entra_sync._purview_hdr", return_value={}):
        out = udf_entra_sync.ensure_group_on_collection("g", "nope")

    assert out["status"] == "collection_not_found"


# ---------------------------------------------------------------------------
# add_user_to_group
# ---------------------------------------------------------------------------

def test_add_user_to_group_calls_graph_with_correct_body():
    from api import udf_entra_sync

    resp = MagicMock(status_code=204)
    with patch("api.udf_entra_sync.requests.post", return_value=resp) as p, \
         patch("api.udf_entra_sync._graph_hdr", return_value={}):
        out = udf_entra_sync.add_user_to_group("user-oid", "grp-oid")

    assert out["status"] == 204
    body = p.call_args.kwargs["json"]
    assert body["@odata.id"].endswith("/directoryObjects/user-oid")


# ---------------------------------------------------------------------------
# MIP label GUID resolver
# ---------------------------------------------------------------------------

def test_resolve_label_guids_merges_by_name():
    from governance.mip_labels import resolve_label_guids

    policy = {"labels": [
        {"name": "Public", "priority": 0},
        {"name": "Confidential-PII", "priority": 2},
    ]}
    tenant = [
        {"name": "Public", "id": "guid-pub", "displayName": "Public"},
        {"name": "Confidential-PII", "id": "guid-pii", "displayName": "Confidential PII"},
    ]
    merged = resolve_label_guids(policy, tenant)
    by_name = {lbl["name"]: lbl for lbl in merged["labels"]}
    assert by_name["Public"]["mip_label_id"] == "guid-pub"
    assert by_name["Confidential-PII"]["mip_label_id"] == "guid-pii"


def test_resolve_label_guids_falls_back_to_display_name():
    from governance.mip_labels import resolve_label_guids

    policy = {"labels": [{"name": "Public", "priority": 0}]}
    tenant = [{"name": "Confidential", "id": "guid-other", "displayName": "Public"}]
    merged = resolve_label_guids(policy, tenant)
    assert merged["labels"][0]["mip_label_id"] == "guid-other"
