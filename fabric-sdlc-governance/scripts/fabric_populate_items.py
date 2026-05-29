"""Populate each Fabric workspace from .workspaces.json with a notebook,
data pipeline and warehouse so the Purview Unified Catalog (Fabric source)
has assets to surface beyond the lakehouses.

Idempotent: items are matched by displayName.
"""
from __future__ import annotations
import os, json, time, base64, pathlib, requests
from requests.adapters import HTTPAdapter
try: from urllib3.util.retry import Retry
except ImportError: from requests.packages.urllib3.util.retry import Retry  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIDE = ROOT / "contracts" / "governance" / ".workspaces.json"
for env in (ROOT/".env",):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1); os.environ.setdefault(k,v)

API = "https://api.fabric.microsoft.com/v1"
_TOK = {"t": None, "exp": 0}
def token():
    now=int(time.time())
    if _TOK["t"] and _TOK["exp"]-120>now: return _TOK["t"]
    from azure.identity import DefaultAzureCredential
    tk=DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default")
    _TOK["t"]=tk.token; _TOK["exp"]=tk.expires_on
    return tk.token
def H(): return {"Authorization":f"Bearer {token()}","Content-Type":"application/json"}

S=requests.Session()
S.mount("https://",HTTPAdapter(max_retries=Retry(total=6,backoff_factor=1.5,
    status_forcelist=(429,500,502,503,504),
    allowed_methods=frozenset(["GET","POST","PUT","DELETE"]))))

def list_items(ws:str, kind:str|None=None)->list[dict]:
    url=f"{API}/workspaces/{ws}/items"
    if kind: url+=f"?type={kind}"
    r=S.get(url, headers=H(), timeout=60)
    return r.json().get("value",[]) if r.ok else []

def wait_lro(loc:str, retry_after:int=5, max_wait:int=180):
    end=time.time()+max_wait
    while time.time()<end:
        r=S.get(loc, headers=H(), timeout=30)
        if r.status_code==200:
            try: j=r.json()
            except Exception: j={}
            if j.get("status") in ("Succeeded","Failed"): return j
        time.sleep(retry_after)
    return {}

def create_item(ws:str, name:str, kind:str, definition:dict|None=None)->str|None:
    body={"displayName":name,"type":kind}
    if definition: body["definition"]=definition
    r=S.post(f"{API}/workspaces/{ws}/items", headers=H(), json=body, timeout=120)
    if r.status_code in (200,201): return r.json().get("id")
    if r.status_code==202:
        loc=r.headers.get("Location")
        if loc: wait_lro(loc)
        for it in list_items(ws, kind):
            if it.get("displayName")==name: return it.get("id")
    print(f"    ! create {kind} {name}: {r.status_code} {r.text[:200]}")
    return None

def b64(s:str)->str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")

# ---- payload builders ------------------------------------------------------
def notebook_def(ws_name:str)->dict:
    """Minimal Fabric-ipynb (PySpark) notebook payload."""
    nb = {
      "cells":[
        {"cell_type":"markdown","metadata":{},"source":[
          f"# Build Silver — {ws_name}\n",
          "Reads raw sources, cleans, writes to `lh_silver`."]},
        {"cell_type":"code","metadata":{},"source":[
          "df = spark.read.format('delta').load('Tables/raw_orders')\n",
          "df.write.mode('overwrite').format('delta').saveAsTable('orders_silver')\n"],
          "outputs":[],"execution_count":None}
      ],
      "metadata":{
        "kernelspec":{"display_name":"Synapse PySpark","language":"python","name":"synapse_pyspark"},
        "language_info":{"name":"python"},
        "microsoft":{"language":"python","language_group":"synapse_pyspark"},
        "nteract":{"version":"nteract-front-end@1.0.0"}
      },
      "nbformat":4,"nbformat_minor":5
    }
    return {"format":"ipynb","parts":[
      {"path":"notebook-content.ipynb","payload":b64(json.dumps(nb)),"payloadType":"InlineBase64"}]}

def pipeline_def()->dict:
    """Trivial Data Factory pipeline that just runs a Wait activity."""
    pl = {
      "properties":{
        "activities":[{
          "name":"Wait1","type":"Wait",
          "dependsOn":[],"userProperties":[],
          "typeProperties":{"waitTimeInSeconds":1}
        }],
        "annotations":[]
      }
    }
    return {"parts":[
      {"path":"pipeline-content.json","payload":b64(json.dumps(pl)),"payloadType":"InlineBase64"}]}

# ---- main ------------------------------------------------------------------
def main():
    if not SIDE.exists():
        print("No .workspaces.json — run fabric_workspaces_apply.py first."); return
    side = json.loads(SIDE.read_text())
    only = os.environ.get("FABRIC_ENV","").strip().lower()

    for env_key, info in side.items():
        if only and only != "all" and env_key != only: continue
        ws_id = info["id"]; ws_name = info["name"]
        print(f"\n== {env_key.upper()} workspace: {ws_name}  ({ws_id})")

        existing = {it["displayName"]: (it["type"], it["id"]) for it in list_items(ws_id)}

        plan = [
          ("Notebook",     "nb_build_silver",    lambda: notebook_def(ws_name)),
          ("DataPipeline", "pl_silver_to_gold",  lambda: pipeline_def()),
          ("Warehouse",    "wh_reporting",       lambda: None),  # warehouse needs no definition
        ]
        for kind, name, defb in plan:
            if name in existing:
                print(f"  = exists {kind:14s} {name} ({existing[name][1]})")
                continue
            d = defb()
            iid = create_item(ws_id, name, kind, d)
            if iid: print(f"  + created {kind:14s} {name} ({iid})")

if __name__ == "__main__":
    main()
