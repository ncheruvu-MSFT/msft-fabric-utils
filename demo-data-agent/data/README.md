# Sample Data — Governed Sales Star Schema

A small, fictitious sales dataset used by both Data Agent demos. The data is generated
deterministically (`SEED = 42`) so demo answers are reproducible.

Re-generate with:

```bash
python generate_sample_data.py
```

## Tables

### `FactSales` (grain: one row per order line)

| Column | Type | Notes |
|--------|------|-------|
| `SalesID` | int | Surrogate key |
| `DateKey` | int | FK → `DimDate.DateKey` (yyyymmdd) |
| `ProductKey` | int | FK → `DimProduct.ProductKey` |
| `RegionKey` | int | FK → `DimRegion.RegionKey` |
| `CustomerKey` | int | FK → `DimCustomer.CustomerKey` |
| `Quantity` | int | Units sold |
| `ListPrice` | decimal | Catalog price per unit |
| `Discount` | decimal | Fractional discount applied (0–1) |
| `UnitPrice` | decimal | `ListPrice × (1 − Discount)` |
| `Revenue` | decimal | `UnitPrice × Quantity` |
| `Cost` | decimal | `StandardCost × Quantity` |

### `DimDate` (calendar, 2024-01-01 → 2025-12-31)

`DateKey`, `Date`, `Year`, `Quarter`, `QuarterNumber`, `MonthNumber`, `MonthName`,
`WeekOfYear`, `DayName`, `IsWeekend`

### `DimProduct`

`ProductKey`, `ProductName`, `Subcategory`, `Category`, `StandardCost`, `ListPrice`
Hierarchy: **Category → Subcategory → ProductName**

### `DimRegion`

`RegionKey`, `Region`, `Country`, `SalesManager`
Hierarchy: **Region → Country**

### `DimCustomer`

`CustomerKey`, `CustomerName`, `Segment` (Enterprise / Mid-Market / Small Business)

## Star schema

```
              DimDate
                 │
   DimRegion ── FactSales ── DimProduct
                 │
            DimCustomer
```

## Built-in demo signal

The generator bakes in realistic, explainable patterns so the agents have something to
"discover":

- **YoY growth** — 2025 revenue is ~18% above 2024.
- **Seasonality** — Mobile peaks in Q4 (Nov/Dec); Computers peak in Sep–Oct.
- **Segment behavior** — Enterprise customers buy larger quantities at deeper discounts.
