# Fabric Data Agent — Demo Examples

Two ready-to-run **Microsoft Fabric Data Agent** demos that show how to put governed,
business-friendly analytics in front of natural-language questions. Both share the same
sample star-schema dataset and semantic model so you can stand up the data once and run
either agent on top of it.

| # | Example | What it shows |
|---|---------|---------------|
| 1 | [Governed Analytics Assistant](example-01-governed-analytics-assistant/) | A disciplined NL → SQL/DAX/KQL assistant that answers **only** from connected, governed Fabric sources and respects semantic-model definitions. |
| 2 | [Fabric IQ Enterprise Assistant](example-02-fabric-iq-assistant/) | An insight-driven assistant that reasons over a **business ontology (Fabric IQ)** + the Data Agent to deliver answers, drivers, and recommended actions. |

## Architecture

```
                         Natural-language question
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                        │
   Example 1                                                Example 2
   Data Agent  ── grounds on ──► Semantic Model        Fabric IQ (ontology + KPIs)
        │                          (measures/KPIs)              │ interprets concepts
        │                                                        ▼
        └──────────────► Lakehouse star schema ◄──────── Data Agent (governed queries)
                         DimDate · DimProduct
                         DimRegion · DimCustomer
                         FactSales
```

## What's included

| Asset | Path | Description |
|-------|------|-------------|
| **Sample data generator** | [data/generate_sample_data.py](data/generate_sample_data.py) | Deterministic Python script that emits the 5 CSV tables below. |
| **Sample CSVs** | `data/*.csv` | A 2-year (2024–2025) sales star schema ready to load into a Lakehouse. |
| **Semantic model** | [semantic-model/](semantic-model/) | DAX measures, KPIs, hierarchies, and relationships the agents must respect. |
| **Example 1** | [example-01-governed-analytics-assistant/](example-01-governed-analytics-assistant/) | System prompt, agent config, setup walkthrough, sample Q&A. |
| **Example 2** | [example-02-fabric-iq-assistant/](example-02-fabric-iq-assistant/) | System prompt, business ontology, KPI catalog, setup walkthrough, sample Q&A. |

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Microsoft Fabric** | Trial, Premium, or Fabric capacity with the **Data Agent** (preview) enabled |
| **Workspace Role** | Admin or Member |
| **Items** | A Lakehouse (data) + a Semantic model (definitions) in the same workspace |
| **Python** | 3.9+ to (re)generate the sample data locally |

## Quick start

1. **Generate the data** (already generated CSVs are committed; re-run only if you change the script):

   ```bash
   cd demo-data-agent/data
   python generate_sample_data.py
   ```

2. **Create a Lakehouse** in your Fabric workspace and upload the CSVs to `Files/`, then
   **Load to Tables** (one table per CSV: `DimDate`, `DimProduct`, `DimRegion`,
   `DimCustomer`, `FactSales`).

3. **Build the semantic model** following [semantic-model/README.md](semantic-model/README.md)
   (relationships + DAX measures).

4. **Create a Data Agent**, attach the Lakehouse (and/or semantic model), and paste the
   system prompt from the example you want. See each example's `README.md` for the exact steps.

5. **Ask the sample questions** in `sample-questions.md` and confirm the agent grounds its
   answers in the governed model.

> The sample data is fictitious and generated with a fixed random seed, so demo answers
> are reproducible across runs.
