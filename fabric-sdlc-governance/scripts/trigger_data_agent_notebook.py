"""Trigger the Fabric Data Agent notebook (sales_pipeline_agent) via Fabric REST.

Workflow (CI/CD friendly — no interactive UI):
  1. Resolve workspace + notebook IDs.
  2. POST /workspaces/{w}/items/{n}/jobs/instances?jobType=RunNotebook
  3. Poll the returned Location header (job instance) until Completed | Failed.

Optionally injects ontology-driven instructions into the notebook params (parameterCell).

Auth: DefaultAzureCredential (works with WIF in ADO; falls back to az CLI locally).
Scope: https://api.fabric.microsoft.com/.default
"""
from __future__ import annotations
import argparse, json, os, sys, time, pathlib
import requests, yaml
from azure.identity import DefaultAzureCredential

FABRIC = "https://api.fabric.microsoft.com/v1"

def token() -> str:
    return DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token

def headers() -> dict:
    return {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}

def resolve_workspace_id(name: str) -> str:
    r = requests.get(f"{FABRIC}/workspaces", headers=headers()); r.raise_for_status()
    for w in r.json().get("value", []):
        if w["displayName"] == name:
            return w["id"]
    sys.exit(f"workspace not found: {name}")

def resolve_item_id(ws_id: str, name: str, item_type: str = "Notebook") -> str:
    r = requests.get(f"{FABRIC}/workspaces/{ws_id}/items?type={item_type}", headers=headers())
    r.raise_for_status()
    for it in r.json().get("value", []):
        if it["displayName"] == name:
            return it["id"]
    sys.exit(f"{item_type} not found in workspace: {name}")

def run_notebook(ws_id: str, nb_id: str, params: dict | None = None) -> str:
    """Returns job instance URL (poll until Completed)."""
    body = {"executionData": {"parameters": params or {}}}
    r = requests.post(
        f"{FABRIC}/workspaces/{ws_id}/items/{nb_id}/jobs/instances?jobType=RunNotebook",
        headers=headers(), data=json.dumps(body),
    )
    if r.status_code not in (200, 202):
        sys.exit(f"job start failed: {r.status_code} {r.text}")
    loc = r.headers.get("Location")
    if not loc:
        sys.exit("no Location header on job start response")
    return loc

def wait(job_url: str, timeout_s: int = 1800) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.get(job_url, headers=headers()); r.raise_for_status()
        j = r.json()
        status = j.get("status")
        print(f"  job status: {status}")
        if status in ("Completed", "Failed", "Cancelled", "Deduped"):
            return j
        time.sleep(15)
    sys.exit("job timed out")

def parameter_cell_from_ontology(ontology_yaml: pathlib.Path) -> dict:
    """Convert agent_guidance block into the notebook's tagged 'parameters' cell."""
    o = yaml.safe_load(ontology_yaml.read_text(encoding="utf-8"))
    g = o.get("agent_guidance", {})
    return {
        "AGENT_NAME":         {"value": g.get("agent_name", "sales_pipeline_agent"), "type": "string"},
        "LAKEHOUSE_NAME":     {"value": g.get("lakehouse",  "lh_silver"),            "type": "string"},
        "WAREHOUSE_NAME":     {"value": g.get("warehouse",  "wh_gold"),              "type": "string"},
        "AGENT_INSTRUCTIONS": {"value": g.get("instructions", "").strip(),           "type": "string"},
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--notebook",  default="fabric-data-agent-sales-demo")
    ap.add_argument("--ontology",  default="contracts/ontology/sales.yml")
    ap.add_argument("--timeout",   type=int, default=1800)
    args = ap.parse_args()

    ws_id = resolve_workspace_id(args.workspace)
    nb_id = resolve_item_id(ws_id, args.notebook, "Notebook")
    print(f"workspace={args.workspace} ({ws_id})")
    print(f"notebook ={args.notebook} ({nb_id})")

    params = parameter_cell_from_ontology(pathlib.Path(args.ontology))
    print(f"params   = AGENT_NAME={params['AGENT_NAME']['value']}, "
          f"LH={params['LAKEHOUSE_NAME']['value']}, WH={params['WAREHOUSE_NAME']['value']}")

    job_url = run_notebook(ws_id, nb_id, params)
    print(f"job      = {job_url}")
    result  = wait(job_url, args.timeout)

    if result.get("status") != "Completed":
        print(json.dumps(result, indent=2)); sys.exit(1)
    print("Data Agent notebook completed successfully.")

if __name__ == "__main__":
    main()
