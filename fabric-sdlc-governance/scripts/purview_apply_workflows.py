"""Create sample Purview governance workflows so the Workflows tab in the
Purview portal shows real, customer-grade examples of:

  1. Create-Glossary-Term — approval before publish
  2. Data-Access-Request    — approval gate for self-serve access
  3. Asset-Curation-Update  — approval before description/tag changes

Idempotent: PUT overwrites. Workflow IDs are deterministic UUIDv5 so re-runs
update the same workflows in place.

Auth: uses DefaultAzureCredential — works with both interactive `az login`
and the SPN-cert env vars set by setup_spn_cert.py.
"""
from __future__ import annotations
import os, uuid, json, pathlib, time, requests
from azure.identity import DefaultAzureCredential, AzureCliCredential

def _retry_put(url, headers, body, tries=4):
    last = None
    for i in range(tries):
        try:
            return requests.put(url, headers=headers, json=body, timeout=60)
        except requests.exceptions.RequestException as e:
            last = e; time.sleep(2 * (i+1))
    raise last

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Note: workflow PUT requires the *creator* identity. The SPN doesn't have
# workflow-administrator (and would need its own role grant), so prefer the
# logged-in az user. Skip loading SPN-cert env vars from .env.
_SKIP_ENV = {"AZURE_TENANT_ID","AZURE_CLIENT_ID","AZURE_CLIENT_CERTIFICATE_PATH",
             "AZURE_CLIENT_SEND_CERTIFICATE_CHAIN","AZURE_CLIENT_SECRET"}
for env in (ROOT/".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1)
                if k in _SKIP_ENV: continue
                os.environ.setdefault(k,v)

PURVIEW = os.environ.get("PURVIEW_ACCOUNT","ngpurview")
BASE    = f"https://{PURVIEW}.purview.azure.com/workflow/workflows"
APIV    = "2023-10-01-preview"
NS      = uuid.UUID("11111111-1111-1111-1111-111111111111")

# Approver — your Entra object ID (governance lead). Override with env GOV_APPROVER_OID.
APPROVER = os.environ.get("GOV_APPROVER_OID", "e5fde933-199e-4b54-917a-8e6741be6941")
# Default glossary id (term triggers require an underGlossaryHierarchy)
GLOSSARY = os.environ.get("GOV_GLOSSARY_ID", "c9eb6b20-b448-4e02-b8bc-40bc9cdf862e")
GLOSS_PATH = f"/glossaries/{GLOSSARY}"

def tok():
    # AzureCliCredential fails on Windows store-Python because subprocess can't
    # find `az` without shell=True. Call az ourselves.
    import subprocess
    return subprocess.check_output(
        "az account get-access-token --resource https://purview.azure.net --query accessToken -o tsv",
        text=True, shell=True).strip()
def H(): return {"Authorization":f"Bearer {tok()}","Content-Type":"application/json"}

def email_action(name:str, subj:str, body:str, after:dict|None=None)->dict:
    return {"type":"EmailNotification",
            "inputs":{"parameters":{"emailSubject":subj,"emailMessage":body,
                                    "emailRecipients":["@{runInput()['requestor']}"]}},
            "runAfter": after or {}}

def approval_dag(title:str, on_approve:dict, reject_subj:str, reject_msg:str)->dict:
    return {"actions":{
      "Start and wait for an approval":{
        "type":"Approval",
        "inputs":{"parameters":{
          "approvalType":"PendingOnAll","title":title,"assignedTo":[APPROVER]}},
        "runAfter":{}},
      "Condition":{
        "type":"If",
        "expression":{"and":[{"equals":[
          "@{outputs('Start and wait for an approval')['outcome']}","Approved"]}]},
        "actions": on_approve,
        "else":{"actions":{
          "Send reject email": email_action("rej", reject_subj, reject_msg)}},
        "runAfter":{"Start and wait for an approval":["Succeeded"]}
      }}}

def workflows()->list[dict]:
    return [
      # 1) Create glossary term — gates new term publication
      {"name":"Create Glossary Term — approval",
       "description":"Approval workflow for new glossary term requests.",
       "isEnabled": True,
       "triggers":[{"type":"when_term_creation_is_requested","underGlossaryHierarchy":GLOSS_PATH}],
       "actionDag": approval_dag(
         "Approve new glossary term",
         {"Create glossary term":{"type":"CreateTerm","runAfter":{}},
          "Notify approval": email_action("ok",
             "Glossary Term Create — APPROVED",
             "Your term @{runInput()['term']['name']} is approved.",
             {"Create glossary term":["Succeeded"]})},
         "Glossary Term Create — REJECTED",
         "Your request for term @{runInput()['term']['name']} was rejected.")},

      # 2) Update glossary term — gates edits to descriptions/owners
      {"name":"Update Glossary Term — approval",
       "description":"Approval gate before glossary term changes go live.",
       "isEnabled": True,
       "triggers":[{"type":"when_term_update_is_requested","underGlossaryHierarchy":GLOSS_PATH}],
       "actionDag": approval_dag(
         "Approve glossary term update",
         {"Update glossary term":{"type":"UpdateTerm","runAfter":{}},
          "Notify approval": email_action("ok",
             "Glossary Term Update — APPROVED",
             "Update for @{runInput()['term']['name']} approved.",
             {"Update glossary term":["Succeeded"]})},
         "Glossary Term Update — REJECTED",
         "Update for @{runInput()['term']['name']} was rejected.")},

      # 3) Delete glossary term — approval before removal
      {"name":"Delete Glossary Term — approval",
       "description":"Approval gate for glossary term deletion.",
       "isEnabled": True,
       "triggers":[{"type":"when_term_deletion_is_requested","underGlossaryHierarchy":GLOSS_PATH}],
       "actionDag": approval_dag(
         "Approve glossary term deletion",
         {"Delete glossary term":{"type":"DeleteTerm","runAfter":{}},
          "Notify approval": email_action("ok",
             "Glossary Term Delete — APPROVED",
             "Deletion of @{runInput()['term']['name']} approved.",
             {"Delete glossary term":["Succeeded"]})},
         "Glossary Term Delete — REJECTED",
         "Deletion of @{runInput()['term']['name']} was rejected.")},
    ]

def existing_by_name() -> dict[str,str]:
    for v in ("2022-05-01-preview","2023-10-01-preview"):
        r = requests.get(f"{BASE}?api-version={v}", headers=H())
        if r.ok:
            return {w["name"]: w["id"] for w in r.json().get("value",[])}
    return {}

STATE = ROOT/".workflows.json"

def load_state() -> dict[str,str]:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {}

def save_state(s: dict[str,str]) -> None:
    STATE.write_text(json.dumps(s, indent=2))

def main():
    print(f"Purview workflow base: {BASE}")
    state = load_state()
    for wf in workflows():
        wid = state.get(wf['name']) or str(uuid.uuid4())
        r = _retry_put(f"{BASE}/{wid}?api-version={APIV}", H(), wf)
        print(f"  {r.status_code}  {wf['name']:45s}  {wid}")
        if r.status_code >= 400:
            print(f"    ! {r.text[:300]}")
        else:
            state[wf['name']] = wid
            save_state(state)
    # Print final list
    # Best-effort listing; some Purview accounts don't expose a list endpoint.
    for v in ("2022-05-01-preview","2023-10-01-preview"):
        r = requests.get(f"{BASE}?api-version={v}", headers=H())
        if r.ok:
            print("\nWorkflows in account:")
            for w in r.json().get("value",[]):
                print(f"  - {w['name']}  [{w.get('type','UserManaged')}]  enabled={w.get('isEnabled')}")
            break

if __name__ == "__main__":
    main()
