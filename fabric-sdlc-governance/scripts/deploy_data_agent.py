"""Create/update a Fabric Data Agent via REST — no Spark notebook execution required.

Driven by the agent_guidance block of the ontology YAML. Reads the lakehouse from the
target workspace, builds the Data Agent definition (data_agent.json, stage_config.json,
datasource.json, fewshots.json) per the public schema, base64-encodes the parts, and
POSTs to `/v1/workspaces/{w}/items` (or updateDefinition if the item already exists).

Schema reference: https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/data-agent-definition
"""
from __future__ import annotations
import argparse, base64, json, sys, time, uuid, pathlib
import requests, yaml
from azure.identity import DefaultAzureCredential

FABRIC = "https://api.fabric.microsoft.com/v1"

def _tok() -> str:
    return DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token

def _h() -> dict:
    return {"Authorization": f"Bearer {_tok()}", "Content-Type": "application/json"}

def _b64(obj: dict) -> str:
    return base64.b64encode(json.dumps(obj).encode("utf-8")).decode("ascii")

def _resolve_workspace_id(name: str) -> str:
    r = requests.get(f"{FABRIC}/workspaces", headers=_h()); r.raise_for_status()
    for w in r.json().get("value", []):
        if w["displayName"] == name:
            return w["id"]
    sys.exit(f"workspace not found: {name}")

def _resolve_item_id(ws_id: str, name: str, item_type: str) -> str | None:
    r = requests.get(f"{FABRIC}/workspaces/{ws_id}/items?type={item_type}", headers=_h())
    r.raise_for_status()
    for it in r.json().get("value", []):
        if it["displayName"] == name:
            return it["id"]
    return None

def _await_lro(resp: requests.Response) -> None:
    if resp.status_code in (200, 201):
        return
    if resp.status_code != 202:
        sys.exit(f"failed {resp.status_code}: {resp.text}")
    loc = resp.headers.get("Location")
    if not loc:
        return
    for _ in range(60):
        time.sleep(5)
        rr = requests.get(loc, headers=_h())
        if rr.status_code == 200 and rr.json().get("status") in ("Succeeded", "Completed"):
            return
        if rr.status_code == 200 and rr.json().get("status") == "Failed":
            sys.exit(f"LRO failed: {rr.text}")
    sys.exit("LRO timed out")

def build_definition(ws_id: str, lakehouse_id: str, lakehouse_name: str,
                     instructions: str, tables: list[str],
                     fewshots: list[dict], description: str) -> dict:
    """Build a published Data Agent definition with one lakehouse_tables datasource."""
    ds_folder = f"lakehouse_tables-{lakehouse_name}"
    elements = [{
        "id": str(uuid.uuid4()),
        "is_selected": True,
        "display_name": "dbo",
        "type": "lakehouse_tables.schema",
        "children": [
            {
                "id": str(uuid.uuid4()),
                "is_selected": True,
                "display_name": t,
                "type": "lakehouse_tables.table",
            }
            for t in tables
        ],
    }]
    datasource = {
        "$schema": "1.0.0",
        "artifactId": lakehouse_id,
        "workspaceId": ws_id,
        "displayName": lakehouse_name,
        "type": "lakehouse_tables",
        "dataSourceInstructions": (
            "Tables: opportunities, leads, accounts, sales_reps, stage_probability. "
            "Open opportunities have stage NOT IN ('ClosedWon','ClosedLost'). "
            "Lead score >= 70 means 'qualified'. Join opportunities.account_id = "
            "accounts.account_id and opportunities.owner_id = sales_reps.rep_id."
        ),
        "elements": elements,
    }
    fewshots_doc = {
        "$schema": "1.0.0",
        "fewShots": [
            {"id": str(uuid.uuid4()), "question": q, "query": sql}
            for q, sql in fewshots
        ],
    }
    stage = {"$schema": "1.0.0", "aiInstructions": instructions}
    parts = [
        {"path": "Files/Config/data_agent.json",
         "payload": _b64({"$schema": "2.1.0"}), "payloadType": "InlineBase64"},
        {"path": "Files/Config/draft/stage_config.json",
         "payload": _b64(stage), "payloadType": "InlineBase64"},
        {"path": f"Files/Config/draft/{ds_folder}/datasource.json",
         "payload": _b64(datasource), "payloadType": "InlineBase64"},
        {"path": f"Files/Config/draft/{ds_folder}/fewshots.json",
         "payload": _b64(fewshots_doc), "payloadType": "InlineBase64"},
        {"path": "Files/Config/published/stage_config.json",
         "payload": _b64(stage), "payloadType": "InlineBase64"},
        {"path": f"Files/Config/published/{ds_folder}/datasource.json",
         "payload": _b64(datasource), "payloadType": "InlineBase64"},
        {"path": f"Files/Config/published/{ds_folder}/fewshots.json",
         "payload": _b64(fewshots_doc), "payloadType": "InlineBase64"},
        {"path": "Files/Config/publish_info.json",
         "payload": _b64({"$schema": "1.0.0", "description": description}),
         "payloadType": "InlineBase64"},
    ]
    return {"parts": parts}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--ontology",  required=True)
    ap.add_argument("--agent-name", default=None,
                    help="Override the agent display name (defaults to ontology agent_guidance.agent_name)")
    args = ap.parse_args()

    onto = yaml.safe_load(pathlib.Path(args.ontology).read_text(encoding="utf-8"))
    g = onto.get("agent_guidance", {})
    agent_name      = args.agent_name or g.get("agent_name", "sales_pipeline_agent")
    lakehouse_name  = g.get("lakehouse", "lh_silver")
    instructions    = g.get("instructions", "").strip()
    tables          = g.get("tables", [
        "opportunities", "leads", "accounts", "sales_reps", "stage_probability"
    ])
    fewshots        = [
        ("What is total open pipeline by stage?",
         "SELECT stage, SUM(amount) FROM opportunities WHERE stage NOT IN ('ClosedWon','ClosedLost') GROUP BY stage"),
        ("Top 5 accounts by open opportunity value",
         "SELECT a.name, SUM(o.amount) AS total FROM opportunities o JOIN accounts a ON o.account_id=a.account_id WHERE o.stage NOT IN ('ClosedWon','ClosedLost') GROUP BY a.name ORDER BY total DESC LIMIT 5"),
        ("How many qualified leads are there?",
         "SELECT COUNT(*) FROM leads WHERE score >= 70"),
    ]
    description     = f"Sales pipeline Data Agent — published via GitHub Actions from {args.ontology}"

    ws_id = _resolve_workspace_id(args.workspace)
    lh_id = _resolve_item_id(ws_id, lakehouse_name, "Lakehouse")
    if not lh_id:
        sys.exit(f"lakehouse not found: {lakehouse_name} (run seed_sales_samples.py first)")
    print(f"workspace = {args.workspace} ({ws_id})")
    print(f"lakehouse = {lakehouse_name} ({lh_id})")

    definition = build_definition(ws_id, lh_id, lakehouse_name, instructions,
                                  tables, fewshots, description)

    existing = _resolve_item_id(ws_id, agent_name, "DataAgent")
    if existing:
        print(f"updating DataAgent {agent_name} ({existing})")
        r = requests.post(
            f"{FABRIC}/workspaces/{ws_id}/items/{existing}/updateDefinition",
            headers=_h(), data=json.dumps({"definition": definition}),
        )
        _await_lro(r)
        print("updated.")
    else:
        print(f"creating DataAgent {agent_name}")
        body = {"displayName": agent_name, "type": "DataAgent", "definition": definition}
        r = requests.post(f"{FABRIC}/workspaces/{ws_id}/items",
                          headers=_h(), data=json.dumps(body))
        _await_lro(r)
        new_id = _resolve_item_id(ws_id, agent_name, "DataAgent")
        print(f"created: {new_id}")

if __name__ == "__main__":
    main()
