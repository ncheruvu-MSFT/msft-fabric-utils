"""Deploy the demo-data-agent assets into an existing Fabric workspace.

Steps (pure REST, no Spark):
  1. Resolve the target workspace.
  2. Create (or reuse) the Lakehouse.
  3. Upload the 5 demo CSVs to OneLake  Files/demo/.
  4. Load each CSV into a Delta table  Tables/<name>.
  5. Create (or update) two Data Agents grounded on the Lakehouse:
       - Example 1: Governed Analytics Assistant
       - Example 2: Fabric IQ Enterprise Assistant

Auth: uses AzureCliCredential (your `az login`).  Service principals are NOT used
because this tenant returns 403 AuthorizationFailure on OneLake data-plane writes
for SP identities — a user token via az CLI works for both control and data plane.

Usage:
    python deploy.py --workspace ng_poc_01
    python deploy.py --workspace ng_poc_01 --lakehouse lh_demo_sales --skip-data-agents
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys
import time
import uuid

import requests
from azure.identity import AzureCliCredential

FABRIC = "https://api.fabric.microsoft.com/v1"
DATA_DIR = pathlib.Path(__file__).parent / "data"
ONELAKE_FOLDER = "demo"

# CSV file -> Delta table name
TABLES = {
    "DimDate.csv": "DimDate",
    "DimProduct.csv": "DimProduct",
    "DimRegion.csv": "DimRegion",
    "DimCustomer.csv": "DimCustomer",
    "FactSales.csv": "FactSales",
}

_cred = AzureCliCredential()


def _fab_tok() -> str:
    return _cred.get_token("https://api.fabric.microsoft.com/.default").token


def _stg_tok() -> str:
    return _cred.get_token("https://storage.azure.com/.default").token


def _h() -> dict:
    return {"Authorization": f"Bearer {_fab_tok()}", "Content-Type": "application/json"}


def _b64(obj: dict) -> str:
    return base64.b64encode(json.dumps(obj).encode("utf-8")).decode("ascii")


def _await_lro(resp: requests.Response, what: str) -> None:
    if resp.status_code in (200, 201):
        return
    if resp.status_code != 202:
        sys.exit(f"  [fail] {what}: {resp.status_code} {resp.text[:300]}")
    loc = resp.headers.get("Location")
    if not loc:
        return
    for _ in range(60):
        time.sleep(5)
        rr = requests.get(loc, headers={"Authorization": f"Bearer {_fab_tok()}"})
        if rr.status_code == 200:
            st = rr.json().get("status")
            if st in ("Succeeded", "Completed"):
                return
            if st == "Failed":
                sys.exit(f"  [fail] {what}: {rr.text[:300]}")
    sys.exit(f"  [timeout] {what}")


# ---------------------------------------------------------------------------
# Workspace + lakehouse
# ---------------------------------------------------------------------------
def resolve_workspace(name: str) -> str:
    r = requests.get(f"{FABRIC}/workspaces", headers=_h())
    r.raise_for_status()
    for w in r.json().get("value", []):
        if w["displayName"] == name:
            return w["id"]
    sys.exit(f"workspace not found: {name}")


def find_item(ws_id: str, name: str, item_type: str) -> str | None:
    r = requests.get(f"{FABRIC}/workspaces/{ws_id}/items?type={item_type}", headers=_h())
    r.raise_for_status()
    for it in r.json().get("value", []):
        if it["displayName"] == name:
            return it["id"]
    return None


def ensure_lakehouse(ws_id: str, name: str) -> str:
    lh_id = find_item(ws_id, name, "Lakehouse")
    if lh_id:
        print(f"  lakehouse exists: {name} ({lh_id})")
        return lh_id
    print(f"  creating lakehouse: {name}")
    r = requests.post(f"{FABRIC}/workspaces/{ws_id}/lakehouses",
                      headers=_h(), json={"displayName": name})
    _await_lro(r, "create lakehouse")
    for _ in range(20):
        lh_id = find_item(ws_id, name, "Lakehouse")
        if lh_id:
            print(f"  created lakehouse: {name} ({lh_id})")
            return lh_id
        time.sleep(3)
    sys.exit("lakehouse not found after create")


# ---------------------------------------------------------------------------
# OneLake upload + table load
# ---------------------------------------------------------------------------
def upload_csv(ws_name: str, lh_name: str, path: pathlib.Path) -> None:
    tok = _stg_tok()
    h = {"Authorization": f"Bearer {tok}"}
    base = (f"https://onelake.dfs.fabric.microsoft.com/{ws_name}/"
            f"{lh_name}.Lakehouse/Files/{ONELAKE_FOLDER}/{path.name}")
    data = path.read_bytes()
    requests.put(base + "?resource=file", headers=h).raise_for_status()
    requests.patch(base + "?action=append&position=0",
                   headers={**h, "Content-Length": str(len(data))},
                   data=data).raise_for_status()
    requests.patch(base + f"?action=flush&position={len(data)}",
                   headers=h).raise_for_status()
    print(f"  uploaded {path.name} -> Files/{ONELAKE_FOLDER}/{path.name}")


def load_table(ws_id: str, lh_id: str, table: str, csv_name: str) -> None:
    body = {
        "relativePath": f"Files/{ONELAKE_FOLDER}/{csv_name}",
        "pathType": "File",
        "mode": "Overwrite",
        "recursive": False,
        "formatOptions": {"format": "Csv", "header": True, "delimiter": ","},
    }
    r = requests.post(
        f"{FABRIC}/workspaces/{ws_id}/lakehouses/{lh_id}/tables/{table}/load",
        headers=_h(), json=body)
    _await_lro(r, f"load table {table}")
    print(f"  loaded Tables/{table}")


# ---------------------------------------------------------------------------
# Data Agent
# ---------------------------------------------------------------------------
def _instructions_from(prompt_file: pathlib.Path) -> str:
    """Return the prompt body (everything after the first '---' separator line)."""
    text = prompt_file.read_text(encoding="utf-8")
    if "\n---\n" in text:
        return text.split("\n---\n", 1)[1].strip()
    return text.strip()


def build_agent_definition(ws_id: str, lh_id: str, lh_name: str,
                           instructions: str, tables: list[str],
                           ds_instructions: str, fewshots: list[tuple[str, str]],
                           description: str) -> dict:
    ds_folder = f"lakehouse_tables-{lh_name}"
    elements = [{
        "id": str(uuid.uuid4()),
        "is_selected": True,
        "display_name": "dbo",
        "type": "lakehouse_tables.schema",
        "children": [
            {"id": str(uuid.uuid4()), "is_selected": True,
             "display_name": t, "type": "lakehouse_tables.table"}
            for t in tables
        ],
    }]
    datasource = {
        "$schema": "1.0.0",
        "artifactId": lh_id,
        "workspaceId": ws_id,
        "displayName": lh_name,
        "type": "lakehouse_tables",
        "dataSourceInstructions": ds_instructions,
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


def deploy_agent(ws_id: str, agent_name: str, definition: dict) -> None:
    existing = find_item(ws_id, agent_name, "DataAgent")
    if existing:
        print(f"  updating DataAgent: {agent_name} ({existing})")
        r = requests.post(
            f"{FABRIC}/workspaces/{ws_id}/items/{existing}/updateDefinition",
            headers=_h(), data=json.dumps({"definition": definition}))
        _await_lro(r, "updateDefinition")
    else:
        print(f"  creating DataAgent: {agent_name}")
        body = {"displayName": agent_name, "type": "DataAgent", "definition": definition}
        r = requests.post(f"{FABRIC}/workspaces/{ws_id}/items",
                          headers=_h(), data=json.dumps(body))
        _await_lro(r, "create DataAgent")
    print(f"  done: {agent_name}")


# Shared governed datasource hint and fewshots (validated SQL over the star schema)
DS_INSTRUCTIONS = (
    "Sales star schema. Grain of FactSales is one order line. "
    "Revenue is net of discount (do NOT use ListPrice*Quantity as revenue). "
    "Joins: FactSales.DateKey=DimDate.DateKey, FactSales.ProductKey=DimProduct.ProductKey, "
    "FactSales.RegionKey=DimRegion.RegionKey, FactSales.CustomerKey=DimCustomer.CustomerKey. "
    "Product hierarchy: Category>Subcategory>ProductName. Geography: Region>Country. "
    "Customer Segment in (Enterprise, Mid-Market, Small Business)."
)

FEWSHOTS = [
    ("What was total revenue in 2025 versus 2024?",
     "SELECT d.Year, SUM(f.Revenue) AS Revenue FROM FactSales f "
     "JOIN DimDate d ON f.DateKey=d.DateKey WHERE d.Year IN (2024,2025) GROUP BY d.Year"),
    ("Show 2025 revenue and gross margin percent by product category.",
     "SELECT p.Category, SUM(f.Revenue) AS Revenue, "
     "(SUM(f.Revenue)-SUM(f.Cost))/SUM(f.Revenue) AS GrossMarginPct "
     "FROM FactSales f JOIN DimDate d ON f.DateKey=d.DateKey "
     "JOIN DimProduct p ON f.ProductKey=p.ProductKey WHERE d.Year=2025 "
     "GROUP BY p.Category ORDER BY Revenue DESC"),
    ("Top 5 customers by revenue in 2025.",
     "SELECT TOP 5 c.CustomerName, SUM(f.Revenue) AS Revenue FROM FactSales f "
     "JOIN DimDate d ON f.DateKey=d.DateKey JOIN DimCustomer c ON f.CustomerKey=c.CustomerKey "
     "WHERE d.Year=2025 GROUP BY c.CustomerName ORDER BY Revenue DESC"),
    ("Monthly revenue trend for the Mobile category in 2025.",
     "SELECT d.MonthNumber, d.MonthName, SUM(f.Revenue) AS Revenue FROM FactSales f "
     "JOIN DimDate d ON f.DateKey=d.DateKey JOIN DimProduct p ON f.ProductKey=p.ProductKey "
     "WHERE d.Year=2025 AND p.Category='Mobile' GROUP BY d.MonthNumber, d.MonthName "
     "ORDER BY d.MonthNumber"),
    ("Average order value by customer segment in 2025.",
     "SELECT c.Segment, SUM(f.Revenue)/COUNT(DISTINCT f.SalesID) AS AvgOrderValue "
     "FROM FactSales f JOIN DimDate d ON f.DateKey=d.DateKey "
     "JOIN DimCustomer c ON f.CustomerKey=c.CustomerKey WHERE d.Year=2025 "
     "GROUP BY c.Segment ORDER BY AvgOrderValue DESC"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--lakehouse", default="lh_demo_sales")
    ap.add_argument("--skip-data", action="store_true", help="Skip CSV upload + table load")
    ap.add_argument("--skip-data-agents", action="store_true", help="Skip Data Agent creation")
    args = ap.parse_args()

    root = pathlib.Path(__file__).parent
    print(f"== Deploy demo-data-agent -> workspace '{args.workspace}' ==")
    ws_id = resolve_workspace(args.workspace)
    print(f"  workspace id: {ws_id}")
    lh_id = ensure_lakehouse(ws_id, args.lakehouse)

    if not args.skip_data:
        print("-- Uploading CSVs to OneLake --")
        for csv_name in TABLES:
            upload_csv(args.workspace, args.lakehouse, DATA_DIR / csv_name)
        print("-- Loading Delta tables --")
        for csv_name, table in TABLES.items():
            load_table(ws_id, lh_id, table, csv_name)

    if not args.skip_data_agents:
        tables = list(TABLES.values())
        print("-- Deploying Data Agent: Example 1 (Governed Analytics) --")
        instr1 = _instructions_from(
            root / "example-01-governed-analytics-assistant" / "system-prompt.md")
        deploy_agent(ws_id, "Governed Analytics Assistant",
                     build_agent_definition(ws_id, lh_id, args.lakehouse, instr1, tables,
                                             DS_INSTRUCTIONS, FEWSHOTS,
                                             "Demo: governed NL->SQL analytics assistant"))

        print("-- Deploying Data Agent: Example 2 (Fabric IQ) --")
        instr2 = _instructions_from(
            root / "example-02-fabric-iq-assistant" / "system-prompt.md")
        deploy_agent(ws_id, "Enterprise Insight Assistant",
                     build_agent_definition(ws_id, lh_id, args.lakehouse, instr2, tables,
                                             DS_INSTRUCTIONS, FEWSHOTS,
                                             "Demo: Fabric IQ insight + action assistant"))

    print("== Done ==")


if __name__ == "__main__":
    main()
