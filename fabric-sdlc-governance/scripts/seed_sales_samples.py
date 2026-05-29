"""Generate Contoso Sales sample data and (optionally) upload to a Fabric Lakehouse via OneLake.

Tables emitted as CSV under ./data/sales/:
  accounts, contacts, leads, opportunities, stage_probability,
  sales_reps, fact_quota, fact_sales

If --upload is passed, each CSV is PUT into:
  https://onelake.dfs.fabric.microsoft.com/<workspace>/<lakehouse>.Lakehouse/Files/sales/<name>.csv

Auth: AzureCliCredential (works locally) or DefaultAzureCredential in CI (WIF).
"""
from __future__ import annotations
import argparse, csv, os, random, datetime as dt, pathlib, sys

random.seed(7)
OUT = pathlib.Path("data/sales")
OUT.mkdir(parents=True, exist_ok=True)

FIRST = ["Alex","Sam","Jordan","Riley","Casey","Morgan","Taylor","Avery","Jamie","Drew","Priya","Wei","Ana","Luis","Sara"]
LAST  = ["Smith","Patel","Garcia","Khan","Nguyen","Brown","Lopez","Singh","Chen","Park","Müller","Rossi","Kim","Davis"]
INDUSTRY = ["Manufacturing","Retail","FinServ","Healthcare","Public Sector","Tech","Energy"]
STAGES = [
    ("Prospecting",   0.10),
    ("Qualification", 0.25),
    ("Proposal",      0.50),
    ("Negotiation",   0.75),
    ("ClosedWon",     1.00),
    ("ClosedLost",    0.00),
]
SOURCES = ["Web","Event","Referral","Outbound","Partner"]

def names(n_first=FIRST, n_last=LAST):
    return random.choice(n_first), random.choice(n_last)

def accounts(n):
    return [{
        "account_id": i,
        "account_name": f"Contoso Customer {i:04d}",
        "industry": random.choice(INDUSTRY),
        "country": random.choice(["USA","CAN","GBR","DEU","JPN","BRA","IND"]),
        "annual_revenue_usd": random.randint(1_000_000, 5_000_000_000),
    } for i in range(1, n+1)]

def contacts(n, n_accounts):
    rows=[]
    for i in range(1, n+1):
        fn, ln = names()
        rows.append({
            "contact_id": i,
            "account_id": random.randint(1, n_accounts),
            "first_name": fn, "last_name": ln,
            "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
            "title": random.choice(["VP Eng","CFO","CIO","Director","Manager","Buyer"]),
            "is_decision_maker": random.random() < 0.3,
        })
    return rows

def sales_reps(n):
    rows=[]
    for i in range(1, n+1):
        fn, ln = names()
        rows.append({
            "rep_id": i,
            "full_name": f"{fn} {ln}",
            "email": f"{fn.lower()}.{ln.lower()}@contoso.com",
            "region": random.choice(["NA-East","NA-West","EMEA","APAC","LATAM"]),
            "segment": random.choice(["Enterprise","Commercial","SMB"]),
            "hire_date": (dt.date(2018,1,1)+dt.timedelta(days=random.randint(0,2500))).isoformat(),
        })
    return rows

def leads(n, n_reps):
    rows=[]
    for i in range(1, n+1):
        fn, ln = names()
        rows.append({
            "lead_id": i,
            "owner_id": random.randint(1, n_reps),
            "first_name": fn, "last_name": ln,
            "email": f"lead{i}@example.com",
            "company": f"Prospect {i:04d}",
            "source": random.choice(SOURCES),
            "lead_score": random.randint(0, 100),
            "created_date": (dt.date.today() - dt.timedelta(days=random.randint(0, 120))).isoformat(),
            "converted": random.random() < 0.18,
        })
    return rows

def opportunities(n, n_accounts, n_reps):
    rows=[]
    today = dt.date.today()
    for i in range(1, n+1):
        stage, prob = random.choice(STAGES)
        rows.append({
            "opportunity_id": i,
            "account_id": random.randint(1, n_accounts),
            "owner_id": random.randint(1, n_reps),
            "name": f"Opp {i:05d}",
            "amount": round(random.uniform(10_000, 500_000), 2),
            "stage": stage,
            "probability": prob,
            "close_date": (today + dt.timedelta(days=random.randint(-180, 180))).isoformat(),
            "created_date": (today - dt.timedelta(days=random.randint(0, 365))).isoformat(),
        })
    return rows

def stage_probability():
    return [{"stage": s, "probability": p} for s, p in STAGES]

def fact_quota(reps_rows):
    # current and previous quarter
    today = dt.date.today()
    q_now  = f"{today.year}Q{((today.month-1)//3)+1}"
    prev   = today.replace(day=1) - dt.timedelta(days=1)
    q_prev = f"{prev.year}Q{((prev.month-1)//3)+1}"
    rows=[]
    for r in reps_rows:
        for q in (q_prev, q_now):
            rows.append({
                "rep_id": r["rep_id"],
                "quarter": q,
                "quota_amount": random.choice([250_000, 500_000, 750_000, 1_000_000]),
            })
    return rows

def fact_sales(opps_rows):
    rows=[]; sid=1
    for o in opps_rows:
        if o["stage"] != "ClosedWon":
            continue
        close = dt.date.fromisoformat(o["close_date"])
        q = f"{close.year}Q{((close.month-1)//3)+1}"
        rows.append({
            "sale_id": sid,
            "opportunity_id": o["opportunity_id"],
            "account_id": o["account_id"],
            "rep_id": o["owner_id"],
            "amount": o["amount"],
            "close_date": o["close_date"],
            "quarter": q,
        })
        sid += 1
    return rows

def write_csv(name, rows):
    p = OUT / f"{name}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    return p

def _fabric_token() -> str:
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)\
        .get_token("https://api.fabric.microsoft.com/.default").token


def _resolve_workspace_id(workspace: str, tok: str) -> str:
    import requests
    r = requests.get("https://api.fabric.microsoft.com/v1/workspaces",
                     headers={"Authorization": f"Bearer {tok}"})
    r.raise_for_status()
    for w in r.json().get("value", []):
        if w["displayName"] == workspace:
            return w["id"]
    raise SystemExit(f"workspace not found: {workspace}")


def ensure_lakehouse(workspace: str, lakehouse: str) -> None:
    """Create the Lakehouse via Fabric REST if it does not already exist."""
    import requests
    tok = _fabric_token()
    ws_id = _resolve_workspace_id(workspace, tok)
    hdr = {"Authorization": f"Bearer {tok}"}
    r = requests.get(f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items?type=Lakehouse",
                     headers=hdr); r.raise_for_status()
    if any(it["displayName"] == lakehouse for it in r.json().get("value", [])):
        print(f"  lakehouse exists: {lakehouse}")
        return
    print(f"  creating lakehouse: {lakehouse}")
    r = requests.post(f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/lakehouses",
                      headers={**hdr, "Content-Type": "application/json"},
                      json={"displayName": lakehouse})
    if r.status_code not in (200, 201, 202):
        raise SystemExit(f"lakehouse create failed {r.status_code}: {r.text}")


def materialize_delta_tables(workspace: str, lakehouse: str, files: list[pathlib.Path]) -> None:
    """For each uploaded CSV, call Fabric's Load Table API to convert it into a Delta table.

    Fabric runs the CSV->Delta conversion server-side (no Spark from our side). Required so
    Data Agent datasources of type `lakehouse_tables` see the data via the SQL endpoint.
    Docs: https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table
    """
    import requests, time
    tok = _fabric_token()
    ws_id = _resolve_workspace_id(workspace, tok)
    hdr = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    # Resolve lakehouse id
    r = requests.get(f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items?type=Lakehouse",
                     headers={"Authorization": f"Bearer {tok}"})
    r.raise_for_status()
    lh_id = next((it["id"] for it in r.json().get("value", []) if it["displayName"] == lakehouse), None)
    if not lh_id:
        raise SystemExit(f"lakehouse not found: {lakehouse}")

    for p in files:
        name = p.stem
        body = {
            "relativePath": f"Files/sales/{p.name}",
            "pathType": "File",
            "mode": "Overwrite",
            "recursive": False,
            "formatOptions": {"format": "Csv", "header": True, "delimiter": ","},
        }
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/lakehouses/{lh_id}/tables/{name}/load"
        r = requests.post(url, headers=hdr, json=body)
        if r.status_code not in (200, 201, 202):
            print(f"  [skip] {name}: {r.status_code} {r.text[:200]}")
            continue
        loc = r.headers.get("Location")
        # poll LRO
        for _ in range(40):
            time.sleep(3)
            rr = requests.get(loc, headers={"Authorization": f"Bearer {tok}"})
            if rr.status_code == 200:
                status = rr.json().get("status")
                if status in ("Succeeded", "Completed"):
                    print(f"  loaded Tables/{name}  (from Files/sales/{p.name})")
                    break
                if status == "Failed":
                    print(f"  [fail] {name}: {rr.text[:200]}")
                    break
        else:
            print(f"  [timeout] {name}")


def upload_to_onelake(workspace: str, lakehouse: str, files: list[pathlib.Path], folder: str = "sales") -> None:
    """PUT each CSV into Files/<folder>/ of the Lakehouse via OneLake DFS endpoint."""
    import requests
    try:
        from azure.identity import DefaultAzureCredential
        token = DefaultAzureCredential(exclude_interactive_browser_credential=False)\
            .get_token("https://storage.azure.com/.default").token
    except Exception as e:
        print(f"[upload] auth failed: {e}", file=sys.stderr); sys.exit(2)

    base = f"https://onelake.dfs.fabric.microsoft.com/{workspace}/{lakehouse}.Lakehouse/Files/{folder}"
    headers = {"Authorization": f"Bearer {token}"}

    for p in files:
        url = f"{base}/{p.name}"
        data = p.read_bytes()
        # ADLS Gen2 two-step: create then append+flush
        r = requests.put(url + "?resource=file", headers=headers); r.raise_for_status()
        r = requests.patch(url + f"?action=append&position=0",
                           headers={**headers, "Content-Length": str(len(data))},
                           data=data); r.raise_for_status()
        r = requests.patch(url + f"?action=flush&position={len(data)}",
                           headers=headers); r.raise_for_status()
        print(f"  uploaded {p.name} -> Files/{folder}/{p.name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", help="Fabric workspace name (required with --upload)")
    ap.add_argument("--lakehouse", help="Fabric lakehouse name (required with --upload)")
    ap.add_argument("--upload", action="store_true", help="Upload CSVs to OneLake Files/sales/")
    ap.add_argument("--accounts", type=int, default=200)
    ap.add_argument("--contacts", type=int, default=600)
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--leads", type=int, default=800)
    ap.add_argument("--opportunities", type=int, default=1500)
    args = ap.parse_args()

    a  = accounts(args.accounts)
    c  = contacts(args.contacts, args.accounts)
    r  = sales_reps(args.reps)
    l  = leads(args.leads, args.reps)
    o  = opportunities(args.opportunities, args.accounts, args.reps)
    sp = stage_probability()
    fq = fact_quota(r)
    fs = fact_sales(o)

    paths = []
    for name, rows in [("accounts",a),("contacts",c),("sales_reps",r),("leads",l),
                       ("opportunities",o),("stage_probability",sp),
                       ("fact_quota",fq),("fact_sales",fs)]:
        p = write_csv(name, rows)
        paths.append(p)
        print(f"  wrote {p}  ({len(rows)} rows)")

    if args.upload:
        if not (args.workspace and args.lakehouse):
            print("--upload requires --workspace and --lakehouse", file=sys.stderr); sys.exit(2)
        print(f"\nEnsuring lakehouse: {args.workspace} / {args.lakehouse}")
        ensure_lakehouse(args.workspace, args.lakehouse)
        print(f"\nUploading to OneLake: {args.workspace} / {args.lakehouse}.Lakehouse / Files/sales/")
        upload_to_onelake(args.workspace, args.lakehouse, paths)
        print(f"\nMaterializing Delta tables in {args.lakehouse}.Lakehouse/Tables/")
        materialize_delta_tables(args.workspace, args.lakehouse, paths)

if __name__ == "__main__":
    main()
