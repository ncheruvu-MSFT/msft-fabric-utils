"""Fabric Data App — entry point.

Deploy via `infra/deploy_fabric_items.py` (creates a Data App item bound to
this Streamlit script). Inside Fabric the app runs with the workspace
identity, so OneLake reads/writes use the runtime token automatically.

Locally:
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations
import streamlit as st


st.set_page_config(
    page_title="Fabric Lineage & Governance",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Fabric Lineage & Governance")
st.caption(
    "Cross-artifact lineage (ADF, Power BI, T-SQL, notebooks, Fabric pipelines, "
    "Dataflows Gen2) + glossary editor + Entra-driven self-approval workflows."
)

st.markdown(
    """
    Use the sidebar to navigate:

    * **Lineage graph** — interactive PyVis view of `lineage.edges`
    * **Glossary editor** — create / approve / publish Purview terms
    * **Access requests** — self-service request → Entra group → Purview role

    All write actions call the Fabric **User Data Function** APIs in
    [`api/`](../api/) — the UI never talks to Purview directly.
    """
)

st.divider()
st.subheader("System status")
col1, col2, col3 = st.columns(3)
col1.metric("Edges (Delta)", "—", help="Loaded on the Lineage graph page")
col2.metric("Glossary terms", "—", help="Loaded on the Glossary editor page")
col3.metric("Open access requests", "—", help="Loaded on the Access requests page")
