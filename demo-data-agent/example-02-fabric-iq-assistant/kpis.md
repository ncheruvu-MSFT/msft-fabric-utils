# KPI Catalog — Fabric IQ Enterprise Assistant

The assistant must interpret every business question against these definitions. Paste this
into the agent's instructions or a data-source note so KPI meaning is consistent.

| KPI | Business meaning | Formula (governed) | Good direction |
|-----|------------------|--------------------|----------------|
| **Total Revenue** | Money earned, net of discount | `SUM(Revenue)` | ↑ |
| **Total Cost** | Cost of goods sold | `SUM(Cost)` | ↓ |
| **Gross Margin** | Profit before opex | `Revenue − Cost` | ↑ |
| **Gross Margin %** | Profitability of each sales dollar | `Gross Margin / Revenue` | ↑ |
| **Units Sold** | Volume | `SUM(Quantity)` | ↑ |
| **Order Count** | Number of distinct orders | `DISTINCTCOUNT(SalesID)` | ↑ |
| **Average Order Value** | Revenue per order | `Revenue / Order Count` | ↑ |
| **Average Discount %** | Pricing pressure | `AVG(Discount)` | ↓ (watch margin) |
| **Revenue YoY %** | Growth vs. last year | `(Rev − Rev PY) / Rev PY` | ↑ |
| **Revenue YTD** | Cumulative revenue this year | `TOTALYTD(Revenue)` | ↑ |

## Interpretation rules

- "Sales", "turnover", "top line" → **Total Revenue**.
- "Profitability", "margin" → **Gross Margin %**.
- "Growth" → **Revenue YoY %** unless another period is specified.
- "Deal size", "basket" → **Average Order Value**.
- "Discounting", "pricing pressure" → **Average Discount %** (and check its effect on margin).

## Dimensions available for breakdowns

- **Time**: Year → Quarter → Month
- **Product**: Category → Subcategory → Product
- **Geography**: Region → Country
- **Customer**: Segment → Customer

## Not available (must refuse / flag as missing)

Churn, NPS / satisfaction, inventory / stock, marketing spend, pipeline / forecast,
headcount. If asked, state the gap and suggest the nearest answerable question.
