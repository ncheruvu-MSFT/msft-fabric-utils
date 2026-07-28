"""Self-service access requests.

The user picks an asset (from `lineage.edges` distinct source/target nodes)
and a permission level. The Fabric UDF:

1. Triggers the Purview `Data-Access-Request` workflow (already defined in
   fabric-sdlc-governance/scripts/purview_apply_workflows.py).
2. On approval, syncs the requester to the configured Entra security group
   (via the udf_entra_sync function) which is bound to the corresponding
   Purview collection role.
"""
from __future__ import annotations
import os
import requests
import streamlit as st


UDF_BASE = os.environ.get("UDF_BASE_URL", "")
st.title("Access requests")

if not UDF_BASE:
    st.warning("`UDF_BASE_URL` not configured. Deploy the User Data Functions first.")
    st.stop()

with st.form("access_request"):
    asset_qname = st.text_input("Asset (qualifiedName)",
                                placeholder="fabric://ngfabric/lh_silver/customers")
    permission = st.selectbox("Permission", ["Read", "Read+Write", "Owner"])
    business_justification = st.text_area("Business justification")
    submit = st.form_submit_button("Submit request")
    if submit:
        payload = {
            "asset_qname": asset_qname,
            "permission": permission,
            "justification": business_justification,
        }
        r = requests.post(f"{UDF_BASE}/access-requests", json=payload, timeout=60)
        if r.ok:
            st.success("Request submitted. Approver will receive a Purview workflow task.")
        else:
            st.error(f"Failed: {r.status_code} — {r.text}")

st.divider()
st.subheader("My open requests")
r = requests.get(f"{UDF_BASE}/access-requests/mine", timeout=30)
if r.ok:
    st.dataframe(r.json().get("value", []), use_container_width=True)
else:
    st.info("No open requests visible.")
