"""Load sample Contoso retail data into all 4 source systems.

Reads endpoints from ../.sources.env (created by deploy_sources.ps1).
Generates the same logical dataset across SQL / Postgres / Cosmos / Databricks
so we can demonstrate cross-source lineage in Fabric mirroring.
"""
from __future__ import annotations
import os, sys, json, random, datetime as dt, uuid, pathlib
from typing import Iterator

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV  = ROOT / ".sources.env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); os.environ.setdefault(k, v)

random.seed(42)
N_CUST, N_PROD, N_ORDERS = 200, 50, 500
DEPTS = ["Retail","Online","Wholesale","Loyalty"]

def customers() -> Iterator[dict]:
    for i in range(1, N_CUST+1):
        yield {
            "customer_id": i,
            "email": f"cust{i:04d}@contoso.com",
            "full_name": f"Customer {i}",
            "phone": f"+1-555-{random.randint(1000,9999):04d}",
            "loyalty_id": f"LOY-{i:09d}",
            "city": random.choice(["Seattle","Boston","Austin","Denver"]),
            "signup_date": (dt.date(2023,1,1)+dt.timedelta(days=random.randint(0,800))).isoformat(),
        }
def products() -> Iterator[dict]:
    cats = ["Electronics","Apparel","Home","Books","Grocery"]
    for i in range(1, N_PROD+1):
        yield {"product_id": i, "sku": f"SKU-{i:05d}", "name": f"Product {i}",
               "category": random.choice(cats), "price_usd": round(random.uniform(5,500),2),
               "stock_qty": random.randint(0,1000)}
def orders() -> Iterator[dict]:
    for i in range(1, N_ORDERS+1):
        yield {"order_id": i, "customer_id": random.randint(1,N_CUST),
               "order_date": (dt.date(2024,1,1)+dt.timedelta(days=random.randint(0,500))).isoformat(),
               "total_amount": round(random.uniform(20,2000),2),
               "department": random.choice(DEPTS)}
def telemetry() -> Iterator[dict]:
    for _ in range(2000):
        yield {"id": str(uuid.uuid4()), "customerId": str(random.randint(1,N_CUST)),
               "event": random.choice(["page_view","add_to_cart","checkout","search"]),
               "ts": (dt.datetime(2025,1,1)+dt.timedelta(seconds=random.randint(0,30_000_000))).isoformat(),
               "device": random.choice(["mobile","web","tablet"]),
               "session": str(uuid.uuid4())[:8]}

# ---------------- Azure SQL: customers + orders (Entra-only auth) ----------------
def load_sql():
    try: import pyodbc, struct
    except ImportError:
        print("SKIP SQL (pyodbc not installed)"); return
    fqdn=os.environ.get("SOURCE_SQL_FQDN"); db=os.environ.get("SOURCE_SQL_DB","retail")
    if not fqdn: print("SKIP SQL (no fqdn)"); return
    from azure.identity import DefaultAzureCredential
    token = DefaultAzureCredential().get_token("https://database.windows.net/.default").token
    tok_b = token.encode("utf-16-le"); tok_struct = struct.pack(f"<I{len(tok_b)}s", len(tok_b), tok_b)
    SQL_COPT_SS_ACCESS_TOKEN = 1256
    drv = "ODBC Driver 18 for SQL Server"
    try:
        import pyodbc as _p
        if drv not in _p.drivers(): drv = "ODBC Driver 17 for SQL Server"
    except Exception: pass
    conn = pyodbc.connect(
        f"Driver={{{drv}}};Server={fqdn};Database={db};Encrypt=yes;TrustServerCertificate=no;",
        attrs_before={SQL_COPT_SS_ACCESS_TOKEN: tok_struct})
    cur=conn.cursor()
    cur.execute("""IF OBJECT_ID('dbo.customers') IS NULL CREATE TABLE dbo.customers
        (customer_id INT PRIMARY KEY, email NVARCHAR(200), full_name NVARCHAR(200),
         phone NVARCHAR(40), loyalty_id NVARCHAR(40), city NVARCHAR(80), signup_date DATE);""")
    cur.execute("""IF OBJECT_ID('dbo.orders') IS NULL CREATE TABLE dbo.orders
        (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL(12,2), department NVARCHAR(40));""")
    cur.execute("TRUNCATE TABLE dbo.customers"); cur.execute("TRUNCATE TABLE dbo.orders")
    cur.fast_executemany=True
    cur.executemany("INSERT INTO dbo.customers VALUES (?,?,?,?,?,?,?)",
                    [(c["customer_id"],c["email"],c["full_name"],c["phone"],c["loyalty_id"],c["city"],c["signup_date"]) for c in customers()])
    cur.executemany("INSERT INTO dbo.orders VALUES (?,?,?,?,?)",
                    [(o["order_id"],o["customer_id"],o["order_date"],o["total_amount"],o["department"]) for o in orders()])
    conn.commit(); conn.close()
    print(f"SQL loaded: {N_CUST} customers + {N_ORDERS} orders")

# ---------------- Postgres: employees (HR domain) ----------------
def load_pg():
    try: import psycopg2
    except ImportError: print("SKIP PG (psycopg2 not installed)"); return
    fqdn=os.environ.get("SOURCE_PG_FQDN"); db=os.environ.get("SOURCE_PG_DB","hr")
    if not fqdn: print("SKIP PG"); return
    conn=psycopg2.connect(host=fqdn, dbname=db,
                          user=os.environ.get("SOURCE_PG_LOGIN","pgadmin"),
                          password=os.environ["SOURCE_PG_PASSWORD"], sslmode="require")
    cur=conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS employees(
        emp_id SERIAL PRIMARY KEY, email TEXT, full_name TEXT,
        department TEXT, salary NUMERIC(12,2), hire_date DATE);""")
    cur.execute("TRUNCATE employees")
    for i in range(1,101):
        cur.execute("INSERT INTO employees(email,full_name,department,salary,hire_date) VALUES (%s,%s,%s,%s,%s)",
                    (f"emp{i}@contoso.com", f"Employee {i}", random.choice(DEPTS),
                     round(random.uniform(45000,180000),2),
                     (dt.date(2020,1,1)+dt.timedelta(days=random.randint(0,1800))).isoformat()))
    conn.commit(); conn.close()
    print("PG loaded: 100 employees")

# ---------------- Cosmos: telemetry events ----------------
def load_cosmos():
    try: from azure.cosmos import CosmosClient
    except ImportError: print("SKIP Cosmos (azure-cosmos not installed)"); return
    ep=os.environ.get("SOURCE_COSMOS_EP")
    if not ep: print("SKIP Cosmos"); return
    from azure.identity import DefaultAzureCredential
    c=CosmosClient(ep, credential=DefaultAzureCredential())
    db=c.get_database_client("telemetry"); cont=db.get_container_client("events")
    for ev in telemetry():
        cont.upsert_item(ev)
    print("Cosmos loaded: 2000 telemetry events")

# ---------------- Databricks: products (Unity Catalog) ----------------
def load_databricks():
    """Writes a Databricks notebook job spec. Actual load is done via job-trigger.
    We just emit the SQL the demo will run; provisioning a UC catalog needs portal one-time."""
    out = ROOT / "fabric-sdlc-governance" / "scripts" / "sources" / "databricks_load.sql"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("""CREATE CATALOG IF NOT EXISTS contoso;
CREATE SCHEMA IF NOT EXISTS contoso.retail;
CREATE TABLE IF NOT EXISTS contoso.retail.products (
    product_id INT, sku STRING, name STRING, category STRING, price_usd DOUBLE, stock_qty INT);
DELETE FROM contoso.retail.products;
INSERT INTO contoso.retail.products VALUES
""" + ",\n".join(f"({p['product_id']},'{p['sku']}','{p['name']}','{p['category']}',{p['price_usd']},{p['stock_qty']})" for p in products()) + ";\n")
    print(f"Databricks SQL emitted -> {out}")

if __name__ == "__main__":
    targets = sys.argv[1:] or ["sql","pg","cosmos","databricks"]
    if "sql" in targets: load_sql()
    if "pg" in targets: load_pg()
    if "cosmos" in targets: load_cosmos()
    if "databricks" in targets: load_databricks()
