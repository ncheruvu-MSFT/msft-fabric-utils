"""Create Purview self-service workflows:
   1. Access request workflow on each domain (data-product consumer requests)
   2. Term approval workflow (steward review)
   3. Glossary publishing workflow
Uses POST /workflowruns/api/workflows.
"""
from __future__ import annotations
import os, json, requests, pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT/".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1); os.environ.setdefault(k,v)
PURVIEW=os.environ.get("PURVIEW_ACCOUNT","ngpurview")
BASE=f"https://{PURVIEW}.purview.azure.com/workflowruns/api"

def tok():
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token
def H(): return {"Authorization":f"Bearer {tok()}","Content-Type":"application/json"}

WORKFLOWS = [
    {
        "name":"Self-Service Access Request",
        "description":"Consumer requests access to a data product; routes to domain steward",
        "triggers":[{"type":"when_data_access_grant_request"}],
        "actions":[
            {"type":"approval","name":"Steward review",
             "approvers":[{"objectId":"admin@MngEnvMCAP219373.onmicrosoft.com"}],
             "approvalType":"any","reminderEnabled":True,"reminderTimeInHours":24},
            {"type":"grant_access","onApprove":True}
        ]
    },
    {
        "name":"Glossary Term Approval",
        "description":"New/changed terms need steward approval before publish",
        "triggers":[{"type":"when_term_create_or_update"}],
        "actions":[
            {"type":"approval","name":"Term review",
             "approvers":[{"objectId":"admin@MngEnvMCAP219373.onmicrosoft.com"}],
             "approvalType":"any"},
            {"type":"publish_term","onApprove":True}
        ]
    },
    {
        "name":"Data Product Publishing",
        "description":"Promote data product from Draft to Published",
        "triggers":[{"type":"when_data_product_publish_request"}],
        "actions":[
            {"type":"approval","name":"Domain owner approval",
             "approvers":[{"objectId":"admin@MngEnvMCAP219373.onmicrosoft.com"}],
             "approvalType":"any"},
            {"type":"publish_data_product","onApprove":True}
        ]
    }
]

def upsert(wf):
    # list existing
    r=requests.get(f"{BASE}/workflows?api-version=2022-05-01-preview",headers=H())
    if r.ok:
        for w in r.json().get("value",[]):
            if w.get("name")==wf["name"]:
                print(f"  exists: {wf['name']}"); return
    body={"name":wf["name"],"description":wf["description"],"isEnabled":True,
          "triggers":wf["triggers"],"actionDag":{"actions":wf["actions"]}}
    r=requests.post(f"{BASE}/workflows?api-version=2022-05-01-preview",headers=H(),json=body)
    print(f"  {wf['name']}: {r.status_code} {r.text[:160] if not r.ok else 'created'}")

def main():
    print(f"Purview workflows at {BASE}")
    for wf in WORKFLOWS: upsert(wf)
    print("\nWorkflows visible at https://purview.microsoft.com/.../workflow-management")
    print("Consumer self-service URL: https://purview.microsoft.com/.../catalog → Browse → Request access")

if __name__=="__main__": main()
