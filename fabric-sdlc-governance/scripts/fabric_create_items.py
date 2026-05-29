"""Create Fabric items: Lakehouse, Warehouse, and a Data Agent (AI skill).
Idempotent. Run per environment."""
from __future__ import annotations
import os, sys, json, time, pathlib, requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
for env in (ROOT/".sources.env", ROOT/".env"):
    if env.exists():
        for ln in env.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k,v=ln.split("=",1); os.environ.setdefault(k,v)

FABRIC = "https://api.fabric.microsoft.com/v1"

def token():
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token
def H(): return {"Authorization":f"Bearer {token()}","Content-Type":"application/json"}

def ws_id(name):
    r=requests.get(f"{FABRIC}/workspaces",headers=H()); r.raise_for_status()
    for w in r.json()["value"]:
        if w["displayName"].lower()==name.lower(): return w["id"]
    sys.exit(f"workspace {name} not found")

def upsert(ws, kind_plural, payload, kind_get=None):
    name=payload["displayName"]
    r=requests.get(f"{FABRIC}/workspaces/{ws}/{kind_get or kind_plural}",headers=H())
    if r.ok:
        for it in r.json().get("value",[]):
            if it["displayName"]==name:
                print(f"  exists {kind_plural}: {name}"); return it["id"]
    r=requests.post(f"{FABRIC}/workspaces/{ws}/{kind_plural}",headers=H(),json=payload)
    print(f"  {r.status_code} create {kind_plural} {name}: {r.text[:200] if not r.ok else 'ok'}")
    return r.json().get("id") if r.ok and r.text else None

def main():
    env=sys.argv[1] if len(sys.argv)>1 else "dev"
    ws=ws_id(os.environ.get("FABRIC_WORKSPACE", f"fabric-de-{env}"))

    print("Lakehouse:")
    lh = upsert(ws, "lakehouses", {"displayName":"lh_contoso_bronze",
        "description":"Bronze landing zone for mirrored sources"})

    print("Lakehouse (silver):")
    lh_s = upsert(ws, "lakehouses", {"displayName":"lh_contoso_silver",
        "description":"Silver: cleansed + joined cross-source"})

    print("Warehouse:")
    wh = upsert(ws, "warehouses", {"displayName":"wh_contoso_gold",
        "description":"Gold: serving warehouse for BI / agents"})

    print("Data Agent (AI Skill):")
    agent_def = {
        "displayName": "agent_contoso_assistant",
        "description": "Contoso retail data assistant. Answers questions over mirrored sources + warehouse.",
        # AI Skill item type — payload follows Fabric REST schema
        "definition": {
            "parts": [{
                "path": "ai-skill.json",
                "payload": "",  # base64 set below
                "payloadType": "InlineBase64"
            }]
        }
    }
    import base64
    skill_payload = {
        "version":"1.0",
        "instructions":"You are Contoso's retail data assistant. Use the warehouse wh_contoso_gold and lakehouse lh_contoso_silver. Respect data sensitivity labels — refuse Highly-Confidential queries unless user has explicit access.",
        "dataSources":[
            {"type":"Warehouse","name":"wh_contoso_gold"},
            {"type":"Lakehouse","name":"lh_contoso_silver"}
        ],
        "examples":[
            {"q":"Top 5 products by revenue last quarter","a":"SELECT TOP 5 p.name,SUM(o.total_amount) FROM ..."},
            {"q":"Customers in Loyalty program","a":"SELECT * FROM customers WHERE loyalty_id IS NOT NULL"}
        ]
    }
    agent_def["definition"]["parts"][0]["payload"] = base64.b64encode(json.dumps(skill_payload).encode()).decode()
    upsert(ws, "aiSkills", agent_def)

    print("Notebook (silver builder):")
    nb_src = """{"nbformat":4,"nbformat_minor":2,"cells":[
      {"cell_type":"markdown","source":["# Silver builder\\nJoins mirrored sources into curated silver tables."]},
      {"cell_type":"code","source":["df_cust = spark.read.table('mirror_sql_retail.dbo.customers')\\n",
       "df_ord = spark.read.table('mirror_sql_retail.dbo.orders')\\n",
       "df_emp = spark.read.table('mirror_pg_hr.public.employees')\\n",
       "df_tel = spark.read.table('mirror_cosmos_telemetry.cosmos.events')\\n",
       "df_prod = spark.read.table('mirror_databricks_retail.retail.products')\\n",
       "\\n# Cross-source join\\ngold = df_ord.join(df_cust,'customer_id').join(df_prod, df_ord.product_id==df_prod.product_id,'left')\\n",
       "gold.write.mode('overwrite').saveAsTable('lh_contoso_silver.customer_orders_enriched')"]}
    ]}"""
    upsert(ws, "notebooks", {
        "displayName":"nb_build_silver",
        "definition":{"parts":[{
            "path":"notebook-content.ipynb",
            "payload": base64.b64encode(nb_src.encode()).decode(),
            "payloadType":"InlineBase64"}]}
    })

if __name__=="__main__": main()
