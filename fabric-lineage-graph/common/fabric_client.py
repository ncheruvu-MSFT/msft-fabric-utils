"""Fabric REST client — workspaces, items, Power BI scanner, Data Factory.

Auth uses DefaultAzureCredential — works with `az login` locally and with the
notebook's runtime identity inside Fabric.
"""
from __future__ import annotations
import os
import time
import requests


FABRIC_BASE = "https://api.fabric.microsoft.com/v1"
PBI_BASE = "https://api.powerbi.com/v1.0/myorg"


def _token(scope: str = "https://api.fabric.microsoft.com/.default") -> str:
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token(scope).token


def _headers(scope: str = "https://api.fabric.microsoft.com/.default") -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(scope)}", "Content-Type": "application/json"}


# ---------- Fabric items ----------

def list_items(workspace_id: str, item_type: str | None = None) -> list[dict]:
    url = f"{FABRIC_BASE}/workspaces/{workspace_id}/items"
    if item_type:
        url += f"?type={item_type}"
    r = requests.get(url, headers=_headers(), timeout=60)
    r.raise_for_status()
    return r.json().get("value", [])


def get_notebook_definition(workspace_id: str, notebook_id: str) -> dict:
    """Returns the notebook .ipynb payload base64-decoded as JSON."""
    url = f"{FABRIC_BASE}/workspaces/{workspace_id}/notebooks/{notebook_id}/getDefinition"
    r = requests.post(url, headers=_headers(), timeout=120)
    r.raise_for_status()
    return r.json()


def get_pipeline_definition(workspace_id: str, pipeline_id: str) -> dict:
    url = f"{FABRIC_BASE}/workspaces/{workspace_id}/dataPipelines/{pipeline_id}/getDefinition"
    r = requests.post(url, headers=_headers(), timeout=120)
    r.raise_for_status()
    return r.json()


# ---------- Power BI scanner ----------

def pbi_scanner_workspaces(workspace_ids: list[str]) -> dict:
    """Kicks off a scanner job and polls until results are ready. Returns the
    full workspace metadata payload incl. dataset tables, measures, M sources.
    """
    hdr = _headers("https://analysis.windows.net/powerbi/api/.default")
    init = requests.post(
        f"{PBI_BASE}/admin/workspaces/getInfo?datasetSchema=true&datasetExpressions=true&lineage=true",
        headers=hdr,
        json={"workspaces": workspace_ids},
        timeout=60,
    )
    init.raise_for_status()
    scan_id = init.json()["id"]
    for _ in range(60):
        st = requests.get(f"{PBI_BASE}/admin/workspaces/scanStatus/{scan_id}",
                          headers=hdr, timeout=30).json()
        if st.get("status") == "Succeeded":
            break
        time.sleep(5)
    out = requests.get(f"{PBI_BASE}/admin/workspaces/scanResult/{scan_id}",
                       headers=hdr, timeout=120)
    out.raise_for_status()
    return out.json()


# ---------- Azure Data Factory ----------

def adf_list_pipelines(sub_id: str, rg: str, factory: str) -> list[dict]:
    hdr = _headers("https://management.azure.com/.default")
    url = (f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg}"
           f"/providers/Microsoft.DataFactory/factories/{factory}/pipelines?api-version=2018-06-01")
    r = requests.get(url, headers=hdr, timeout=60)
    r.raise_for_status()
    return r.json().get("value", [])


def adf_get_dataset(sub_id: str, rg: str, factory: str, dataset_name: str) -> dict:
    hdr = _headers("https://management.azure.com/.default")
    url = (f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg}"
           f"/providers/Microsoft.DataFactory/factories/{factory}"
           f"/datasets/{dataset_name}?api-version=2018-06-01")
    r = requests.get(url, headers=hdr, timeout=60)
    r.raise_for_status()
    return r.json()
