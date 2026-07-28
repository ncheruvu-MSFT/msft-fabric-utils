"""Glossary editor — proxies to the `udf_glossary` Fabric User Data Function.

The UI never calls Purview directly; all CRUD goes through the UDF so the
audit trail (who/when/from-which-app) is consistent.
"""
from __future__ import annotations
import os
import requests
import streamlit as st


UDF_BASE = os.environ.get("UDF_BASE_URL", "")  # set by deploy_fabric_items.py

st.title("Glossary editor")

if not UDF_BASE:
    st.warning("`UDF_BASE_URL` not configured. Deploy the User Data Functions first "
               "(`python infra/deploy_fabric_items.py`).")
    st.stop()


def _get_terms() -> list[dict]:
    r = requests.get(f"{UDF_BASE}/glossary/terms", timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])


with st.spinner("Loading terms..."):
    terms = _get_terms()
st.metric("Glossary terms", len(terms))

st.subheader("Existing terms")
st.dataframe(terms, use_container_width=True)

st.divider()
st.subheader("Create / update term")
with st.form("upsert_term"):
    name = st.text_input("Name")
    definition = st.text_area("Definition")
    steward_email = st.text_input("Steward (email)")
    submit = st.form_submit_button("Submit for approval")
    if submit:
        payload = {"name": name, "definition": definition, "steward": steward_email}
        r = requests.post(f"{UDF_BASE}/glossary/terms", json=payload, timeout=60)
        if r.ok:
            st.success("Submitted. The Create-Glossary-Term workflow has been triggered "
                       "in Purview — approver will see it under Workflows.")
        else:
            st.error(f"Failed: {r.status_code} — {r.text}")
