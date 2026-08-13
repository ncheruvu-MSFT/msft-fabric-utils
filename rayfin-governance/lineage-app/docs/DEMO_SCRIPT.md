# Two-Minute Demo Script

## Slide / Screen 1 — Introduction (20 sec)

"Hello everyone.

We are Team Fabric Lineage Explorer.

Our solution addresses a common challenge in Microsoft Fabric environments: understanding relationships between data assets and determining the impact of changes before they happen.

We built a Fabric App using Rayfin that transforms lineage information into an interactive graph experience."

## Slide / Screen 2 — Problem (20 sec)

"As Fabric environments scale, it becomes increasingly difficult to understand how reports, semantic models, warehouses, lakehouses, and pipelines are connected.

This can make troubleshooting, governance, modernization efforts, and impact analysis both time consuming and risky."

## Slide / Screen 3 — Solution Overview (20 sec)

"Fabric Lineage Explorer provides a visual representation of relationships across Fabric assets.

Instead of searching through disconnected views, users can immediately see upstream and downstream dependencies and navigate through related resources."

## Demo (40 sec)

"Let me show you the application.

Here you can see the lineage edge grid — showing all harvested relationships between data assets. Each edge shows the source, the process type — ADF, T-SQL, Power BI, Spark — and the target.

Now let me switch to the column graph view. This is where it gets powerful.

We can see the full medallion architecture — from source Azure SQL tables through bronze, silver, gold layers, all the way to semantic models and executive reports.

Watch what happens when I click on a column — say, Amount in the source orders table. The entire transformation path lights up — you can see it flows through bronze, gets cast to decimal in silver, becomes GrossAmount, feeds into NetAmount with a discount calculation in gold, then aggregates through the semantic model into the Revenue KPI tile.

That's column-level lineage, end to end, in one click.

And here's the data agent — I can ask in natural language: 'What feeds fact_sales?' — and get an instant answer."

## Business Value (15 sec)

"The solution helps organizations:

- Reduce operational risk
- Accelerate troubleshooting
- Improve governance visibility
- Support modernization initiatives
- Increase understanding of complex Fabric environments"

## Closing (5 sec)

"Thank you for reviewing Fabric Lineage Explorer — our Rayfin-powered approach to simplifying Microsoft Fabric lineage visualization and impact analysis."
