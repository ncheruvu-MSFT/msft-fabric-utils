# Semantic Model — Governed Business Definitions

This is the single source of truth for **how the business measures performance**. Both
Data Agents must answer using these definitions (measures, KPIs, hierarchies) rather than
ad-hoc aggregations over raw columns.

Build this as a Fabric **semantic model** over the Lakehouse tables, or define the measures
directly in the model the Data Agent is grounded on.

## Relationships (single-direction, many-to-one)

| From (many) | To (one) | Cardinality |
|-------------|----------|-------------|
| `FactSales[DateKey]` | `DimDate[DateKey]` | * → 1 |
| `FactSales[ProductKey]` | `DimProduct[ProductKey]` | * → 1 |
| `FactSales[RegionKey]` | `DimRegion[RegionKey]` | * → 1 |
| `FactSales[CustomerKey]` | `DimCustomer[CustomerKey]` | * → 1 |

Mark `DimDate` as the model's **Date table** (using `DimDate[Date]`).

## Hierarchies

- **Product**: `Category` → `Subcategory` → `ProductName`
- **Geography**: `Region` → `Country`
- **Calendar**: `Year` → `Quarter` → `MonthName`

## Core measures (DAX)

```dax
Total Revenue = SUM ( FactSales[Revenue] )

Total Cost = SUM ( FactSales[Cost] )

Units Sold = SUM ( FactSales[Quantity] )

Order Count = DISTINCTCOUNT ( FactSales[SalesID] )

Gross Margin = [Total Revenue] - [Total Cost]

Gross Margin % =
DIVIDE ( [Gross Margin], [Total Revenue] )

Average Selling Price =
DIVIDE ( [Total Revenue], [Units Sold] )

Average Order Value =
DIVIDE ( [Total Revenue], [Order Count] )

Average Discount % =
AVERAGE ( FactSales[Discount] )
```

## Time-intelligence KPIs (DAX)

```dax
Revenue PY =
CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( DimDate[Date] ) )

Revenue YoY % =
DIVIDE ( [Total Revenue] - [Revenue PY], [Revenue PY] )

Revenue YTD =
TOTALYTD ( [Total Revenue], DimDate[Date] )

Revenue MoM % =
VAR Prev =
    CALCULATE ( [Total Revenue], DATEADD ( DimDate[Date], -1, MONTH ) )
RETURN
    DIVIDE ( [Total Revenue] - Prev, Prev )
```

## KPI catalog (business meaning)

| KPI | Definition | Good direction |
|-----|------------|----------------|
| **Total Revenue** | Net revenue after discount | ↑ |
| **Gross Margin %** | Margin as a share of revenue | ↑ |
| **Revenue YoY %** | Growth vs. same period last year | ↑ |
| **Average Order Value** | Revenue per distinct order | ↑ |
| **Average Discount %** | Mean discount applied | ↓ (watch margin) |
| **Units Sold** | Total quantity | ↑ |

## Governance rules the agents must honor

1. Always use the **measure** (e.g., `Gross Margin %`), never re-derive it from raw columns.
2. Respect the **hierarchies** when a user asks to "drill down" or "break down".
3. Revenue is **net of discount**; never report `ListPrice × Quantity` as revenue.
4. If a requested metric has no defined measure, say so — do not invent a formula.
