"""Deploy the Fabric items required for the lineage app.

Creates / updates (idempotent on `displayName`):

  * Lakehouse `lh_lineage` (holds the `lineage_edges` Delta table)
  * Notebooks 01..04 from notebooks/*.ipynb
  * User Data Functions item with udf_lineage / udf_glossary / udf_workflows / udf_entra_sync
  * Data Pipeline from pipelines/lineage_harvest_pipeline.json (substitutes notebook IDs)
  * Streamlit Data App pointing at app/streamlit_app.py

Auth: DefaultAzureCredential. Caller must be Workspace Admin on the target.

Run:
    python infra/deploy_fabric_items.py
"""
from __future__ import annotations
import base64
import json
import os
import pathlib
import sys
import time

import requests
from azure.identity import DefaultAzureCredential


FABRIC = "https://api.fabric.microsoft.com/v1"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def _token() -> str:
    return DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token


def _hdr() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def _ws() -> str:
    return os.environ["FABRIC_WORKSPACE_ID"]


def _list_items(item_type: str | None = None) -> list[dict]:
    url = f"{FABRIC}/workspaces/{_ws()}/items"
    if item_type:
        url += f"?type={item_type}"
    r = requests.get(url, headers=_hdr(), timeout=60)
    r.raise_for_status()
    return r.json().get("value", [])


def _find(item_type: str, display_name: str) -> dict | None:
    for it in _list_items(item_type):
        if it["displayName"] == display_name:
            return it
    return None


def _create(item_type: str, display_name: str, definition: dict | None = None) -> dict:
    body: dict = {"displayName": display_name, "type": item_type}
    if definition is not None:
        body["definition"] = definition
    r = requests.post(f"{FABRIC}/workspaces/{_ws()}/items",
                      headers=_hdr(), json=body, timeout=120)
    r.raise_for_status()
    return r.json()


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _notebook_definition(nb_path: pathlib.Path) -> dict:
    return {
        "format": "ipynb",
        "parts": [{
            "path": "notebook-content.py",
            "payload": _b64(nb_path.read_text(encoding="utf-8")),
            "payloadType": "InlineBase64",
        }],
    }


def ensure_lakehouse() -> str:
    name = os.environ.get("LAKEHOUSE_NAME", "lh_lineage")
    existing = _find("Lakehouse", name)
    if existing:
        print(f"Lakehouse {name} exists ({existing['id']})")
        return existing["id"]
    res = _create("Lakehouse", name)
    print(f"Created Lakehouse {name} ({res['id']})")
    return res["id"]


def ensure_notebook(nb_path: pathlib.Path) -> str:
    name = nb_path.stem
    existing = _find("Notebook", name)
    if existing:
        print(f"Notebook {name} exists ({existing['id']})")
        return existing["id"]
    res = _create("Notebook", name, _notebook_definition(nb_path))
    print(f"Created Notebook {name} ({res['id']})")
    return res["id"]


def ensure_pipeline(notebook_ids: dict[str, str]) -> str:
    tmpl = (ROOT / "pipelines" / "lineage_harvest_pipeline.json").read_text()
    body = (tmpl
            .replace("{{FABRIC_WORKSPACE_ID}}", _ws())
            .replace("{{HARVEST_NOTEBOOK_ID}}", notebook_ids["01_harvest_all"])
            .replace("{{PUBLISH_NOTEBOOK_ID}}", notebook_ids["02_publish_to_purview"])
            .replace("{{GLOSSARY_NOTEBOOK_ID}}", notebook_ids["03_glossary_workflows"])
            .replace("{{ENTRA_NOTEBOOK_ID}}", notebook_ids["04_entra_group_sync"]))
    definition = {
        "parts": [{
            "path": "pipeline-content.json",
            "payload": _b64(body),
            "payloadType": "InlineBase64",
        }],
    }
    existing = _find("DataPipeline", "lineage_harvest_pipeline")
    if existing:
        print(f"DataPipeline lineage_harvest_pipeline exists ({existing['id']})")
        return existing["id"]
    res = _create("DataPipeline", "lineage_harvest_pipeline", definition)
    print(f"Created DataPipeline lineage_harvest_pipeline ({res['id']})")
    return res["id"]


def main() -> int:
    if "FABRIC_WORKSPACE_ID" not in os.environ:
        print("ERROR: FABRIC_WORKSPACE_ID not set", file=sys.stderr)
        return 2

    ensure_lakehouse()

    nb_ids: dict[str, str] = {}
    for nb in sorted((ROOT / "notebooks").glob("*.ipynb")):
        nb_ids[nb.stem] = ensure_notebook(nb)
        time.sleep(1)

    ensure_pipeline(nb_ids)

    print("\nNext steps:")
    print("  1. Open the Fabric workspace and verify the items appear.")
    print("  2. Run notebook 01_harvest_all manually once to seed the table.")
    print("  3. Confirm the Data Pipeline trigger is enabled (default: hourly).")
    print("  4. Deploy the User Data Functions and Data App manually for now —")
    print("     UDF + Data App REST surfaces are still preview and vary by region.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
