"""
Generate sample governed sales data for the Fabric Data Agent demos.

Produces a small star schema as CSV files that can be uploaded to a Fabric
Lakehouse (Files -> Load to Tables) and modeled with the included semantic model:

    DimDate.csv      - calendar dimension (2 years)
    DimProduct.csv   - product / category hierarchy
    DimRegion.csv    - region / country geography
    DimCustomer.csv  - customer + segment
    FactSales.csv    - sales transactions (the measures source)

The data is deterministic (fixed RNG seed) so the demo answers are reproducible.

Usage:
    python generate_sample_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
START = date(2024, 1, 1)
END = date(2025, 12, 31)
OUT_DIR = Path(__file__).parent

random.seed(SEED)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
REGIONS = [
    # RegionKey, Region, Country, SalesManager
    (1, "North America", "United States", "Dana Reed"),
    (2, "North America", "Canada", "Marcus Liu"),
    (3, "Europe", "United Kingdom", "Sofia Almeida"),
    (4, "Europe", "Germany", "Jonas Becker"),
    (5, "Asia Pacific", "Australia", "Priya Nair"),
    (6, "Asia Pacific", "Japan", "Ken Tanaka"),
]

PRODUCTS = [
    # ProductKey, ProductName, Subcategory, Category, StandardCost, ListPrice
    (101, "Aurora Laptop 14", "Laptops", "Computers", 720, 1299),
    (102, "Aurora Laptop 16 Pro", "Laptops", "Computers", 1040, 1899),
    (103, "Nimbus Tablet 11", "Tablets", "Computers", 280, 549),
    (104, "Nimbus Tablet 13 Pro", "Tablets", "Computers", 430, 899),
    (201, "Pulse Wireless Mouse", "Accessories", "Peripherals", 9, 29),
    (202, "Pulse Mechanical Keyboard", "Accessories", "Peripherals", 38, 119),
    (203, "Vista 27 Monitor", "Monitors", "Peripherals", 165, 379),
    (204, "Vista 34 Ultrawide", "Monitors", "Peripherals", 320, 749),
    (301, "EchoBuds Pro", "Audio", "Mobile", 44, 149),
    (302, "EchoBand Watch", "Wearables", "Mobile", 78, 249),
    (303, "Sentinel Phone X", "Phones", "Mobile", 410, 999),
    (304, "Sentinel Phone SE", "Phones", "Mobile", 210, 549),
]

CUSTOMERS = [
    # CustomerKey, CustomerName, Segment
    (1001, "Contoso Ltd", "Enterprise"),
    (1002, "Fabrikam Inc", "Enterprise"),
    (1003, "Northwind Traders", "Mid-Market"),
    (1004, "Adventure Works", "Mid-Market"),
    (1005, "Tailspin Toys", "Small Business"),
    (1006, "Wide World Importers", "Small Business"),
    (1007, "Proseware Inc", "Enterprise"),
    (1008, "Litware Inc", "Mid-Market"),
    (1009, "Coho Vineyard", "Small Business"),
    (1010, "Margie's Travel", "Small Business"),
]

# Segment-driven demand multipliers and discount behavior
SEGMENT_FACTORS = {
    "Enterprise": (3.0, (0.05, 0.20)),
    "Mid-Market": (1.6, (0.02, 0.12)),
    "Small Business": (1.0, (0.00, 0.08)),
}

# Category seasonality weight by month (1-12); Mobile peaks in Q4, etc.
SEASONALITY = {
    "Computers": [0.9, 0.8, 1.0, 1.0, 1.0, 0.9, 0.9, 1.1, 1.3, 1.2, 1.1, 1.0],
    "Peripherals": [1.0, 0.9, 1.0, 1.0, 1.1, 1.0, 0.9, 1.0, 1.1, 1.1, 1.2, 1.1],
    "Mobile": [0.8, 0.8, 0.9, 0.9, 1.0, 1.0, 1.0, 1.1, 1.2, 1.3, 1.6, 1.5],
}

# Year-over-year growth applied to 2025 vs 2024
YOY_GROWTH = 1.18


def write_csv(name: str, header: list[str], rows: list) -> None:
    path = OUT_DIR / name
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  wrote {path.name:18s} ({len(rows):>5d} rows)")


def build_dim_date() -> list:
    rows = []
    d = START
    while d <= END:
        quarter = (d.month - 1) // 3 + 1
        rows.append(
            [
                int(d.strftime("%Y%m%d")),  # DateKey
                d.isoformat(),               # Date
                d.year,
                f"{d.year}-Q{quarter}",
                quarter,
                d.month,
                d.strftime("%B"),
                d.isocalendar().week,
                d.strftime("%A"),
                1 if d.weekday() >= 5 else 0,  # IsWeekend
            ]
        )
        d += timedelta(days=1)
    return rows


def build_fact_sales() -> list:
    rows = []
    sales_id = 1
    d = START
    while d <= END:
        month_idx = d.month - 1
        year_factor = YOY_GROWTH if d.year == 2025 else 1.0
        # Base number of orders for the day
        base_orders = 6
        for _ in range(base_orders):
            product = random.choice(PRODUCTS)
            customer = random.choice(CUSTOMERS)
            region = random.choice(REGIONS)

            p_key, _p_name, _sub, category, std_cost, list_price = product
            c_key, _c_name, segment = customer
            r_key = region[0]

            seg_mult, (disc_lo, disc_hi) = SEGMENT_FACTORS[segment]
            season = SEASONALITY[category][month_idx]

            demand = seg_mult * season * year_factor
            qty = max(1, int(random.gauss(4 * demand, 2)))
            discount = round(random.uniform(disc_lo, disc_hi), 3)

            unit_price = round(list_price * (1 - discount), 2)
            revenue = round(unit_price * qty, 2)
            cost = round(std_cost * qty, 2)

            rows.append(
                [
                    sales_id,
                    int(d.strftime("%Y%m%d")),
                    p_key,
                    r_key,
                    c_key,
                    qty,
                    list_price,
                    discount,
                    unit_price,
                    revenue,
                    cost,
                ]
            )
            sales_id += 1
        d += timedelta(days=1)
    return rows


def main() -> None:
    print("Generating sample governed data ->", OUT_DIR)

    write_csv(
        "DimDate.csv",
        ["DateKey", "Date", "Year", "Quarter", "QuarterNumber", "MonthNumber",
         "MonthName", "WeekOfYear", "DayName", "IsWeekend"],
        build_dim_date(),
    )

    write_csv(
        "DimRegion.csv",
        ["RegionKey", "Region", "Country", "SalesManager"],
        [list(r) for r in REGIONS],
    )

    write_csv(
        "DimProduct.csv",
        ["ProductKey", "ProductName", "Subcategory", "Category",
         "StandardCost", "ListPrice"],
        [list(p) for p in PRODUCTS],
    )

    write_csv(
        "DimCustomer.csv",
        ["CustomerKey", "CustomerName", "Segment"],
        [list(c) for c in CUSTOMERS],
    )

    write_csv(
        "FactSales.csv",
        ["SalesID", "DateKey", "ProductKey", "RegionKey", "CustomerKey",
         "Quantity", "ListPrice", "Discount", "UnitPrice", "Revenue", "Cost"],
        build_fact_sales(),
    )

    print("Done.")


if __name__ == "__main__":
    main()
