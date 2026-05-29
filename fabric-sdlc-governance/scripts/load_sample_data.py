"""Generate Contoso Retail sample data (PII-rich) and load into a Fabric Lakehouse.

Tables:
  customers     – PII heavy (email, phone, address, SSN-like loyalty_id)
  employees     – internal sensitive (salary, manager hierarchy)
  products      – non-sensitive catalogue
  orders        – transactional
  order_items   – line items
"""
from __future__ import annotations
import argparse, csv, os, random, datetime as dt, pathlib, json

random.seed(42)
OUT = pathlib.Path("data/contoso")
OUT.mkdir(parents=True, exist_ok=True)

FIRST = ["Alex","Sam","Jordan","Riley","Casey","Morgan","Taylor","Avery","Jamie","Drew"]
LAST  = ["Smith","Patel","Garcia","Khan","Nguyen","Brown","Lopez","Singh","Chen","Park"]
CITY  = ["Redmond","Seattle","Austin","Bellevue","Toronto","Boston","Atlanta","Denver"]
CAT   = ["Electronics","Apparel","Grocery","Books","Toys","Home"]

def cust(n):
    rows=[]
    for i in range(1,n+1):
        rows.append({
            "customer_id":i,
            "first_name":random.choice(FIRST),
            "last_name":random.choice(LAST),
            "email":f"user{i}@example.com",
            "phone":f"+1-555-{random.randint(1000,9999)}",
            "city":random.choice(CITY),
            "loyalty_id":f"LOY-{random.randint(10**8,10**9-1)}",   # SSN-like 9-digit
            "credit_card_last4":f"{random.randint(0,9999):04d}",
            "signup_date":(dt.date(2023,1,1)+dt.timedelta(days=random.randint(0,800))).isoformat(),
        })
    return rows

def emp(n):
    rows=[]
    for i in range(1,n+1):
        rows.append({
            "employee_id":i,
            "first_name":random.choice(FIRST),
            "last_name":random.choice(LAST),
            "corporate_email":f"emp{i}@contoso.com",
            "manager_id":max(1,i-random.randint(1,5)) if i>1 else None,
            "department":random.choice(["Sales","Eng","Ops","Finance","HR"]),
            "salary_usd":random.randint(60000,220000),
            "hire_date":(dt.date(2018,1,1)+dt.timedelta(days=random.randint(0,2500))).isoformat(),
        })
    return rows

def prod(n):
    return [{"product_id":i,"sku":f"SKU-{i:05d}","name":f"Product {i}",
             "category":random.choice(CAT),"unit_price":round(random.uniform(5,500),2)}
            for i in range(1,n+1)]

def orders(n, ncust):
    rows=[]
    for i in range(1,n+1):
        rows.append({
            "order_id":i,
            "customer_id":random.randint(1,ncust),
            "order_ts":(dt.datetime(2024,1,1)+dt.timedelta(minutes=random.randint(0,500000))).isoformat(),
            "channel":random.choice(["web","store","mobile","partner"]),
            "total_usd":round(random.uniform(10,2000),2),
        })
    return rows

def items(orders_rows, nprod):
    rows=[]; oi=1
    for o in orders_rows:
        for _ in range(random.randint(1,4)):
            rows.append({
                "order_item_id":oi, "order_id":o["order_id"],
                "product_id":random.randint(1,nprod),
                "qty":random.randint(1,3),
                "unit_price":round(random.uniform(5,500),2),
            }); oi+=1
    return rows

def write(name,rows):
    p = OUT / f"{name}.csv"
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    return p

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace"); ap.add_argument("--lakehouse")
    ap.add_argument("--customers",type=int,default=500)
    ap.add_argument("--employees",type=int,default=80)
    ap.add_argument("--products",type=int,default=120)
    ap.add_argument("--orders",type=int,default=2000)
    args=ap.parse_args()

    c=cust(args.customers); e=emp(args.employees); p=prod(args.products)
    o=orders(args.orders,args.customers); it=items(o,args.products)
    for name,rows in [("customers",c),("employees",e),("products",p),("orders",o),("order_items",it)]:
        path=write(name,rows); print(f"  wrote {path}  ({len(rows)} rows)")

    print(f"\nTarget lakehouse: {args.lakehouse} in workspace {args.workspace}")
    print("Upload via Fabric REST OneLake API (Files/contoso/<name>.csv) — handled by fabric-cicd post-deploy hook.")
    # In a real deploy this step would PUT the CSVs into onelake.dfs.fabric.microsoft.com
    # via the workspace's federated token. Left as plain CSV emit here for portability.

if __name__=="__main__":
    main()
