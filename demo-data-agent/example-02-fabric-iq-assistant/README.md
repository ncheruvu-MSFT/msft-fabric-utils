# Example 2 — Fabric IQ Enterprise Assistant

An insight-driven enterprise assistant. Instead of mapping questions to tables, it reasons
over a **business ontology (Fabric IQ)** — Customer, Product, Region, Revenue, Order — and
uses the **Data Agent** to fetch governed numbers. Every answer leads with a conclusion,
then explains insights, drivers, and recommended actions.

| | |
|---|---|
| **Interpretation layer** | Fabric IQ business ontology + KPI catalog |
| **Execution layer** | Data Agent over the same star schema / semantic model |
| **Personality** | Business-friendly, insight-driven, actionable |

## Files

| File | Purpose |
|------|---------|
| [system-prompt.md](system-prompt.md) | Paste into the agent's **instructions** |
| [business-ontology.json](business-ontology.json) | Concepts, relationships, and concept→data mappings |
| [kpis.md](kpis.md) | Business KPI catalog with meaning + good direction |
| [sample-questions.md](sample-questions.md) | Demo script (answer → insight → action) |

## How it differs from Example 1

| | Example 1 (Governed Analytics) | Example 2 (Fabric IQ) |
|---|---|---|
| Primary job | Translate NL → correct query | Interpret business meaning, then reason |
| Output | Validated numbers + trend | Answer → insights → drivers → **actions** |
| Mental model | Tables, measures | Concepts, relationships, KPIs |
| Uses | Semantic model + Lakehouse | Ontology (interpret) + Data Agent (retrieve) |

## Setup in Fabric

> **Fabric IQ** is the business semantic layer / ontology. Where your tenant doesn't yet have
> Fabric IQ enabled, you can emulate it by attaching the **semantic model** as the
> interpretation layer and using [business-ontology.json](business-ontology.json) as the
> concept dictionary inside the agent's instructions.

1. **Prepare data & semantic model** — Follow the
   [top-level README](../README.md#quick-start).

2. **Define the business ontology (Fabric IQ)**
   - In Fabric IQ, model the concepts in [business-ontology.json](business-ontology.json)
     (Customer, Product, Region, Order, Revenue) and their relationships.
   - Map each concept/attribute to the underlying Lakehouse columns and semantic-model
     measures using the `mapsTo` hints in the JSON.

3. **Create the Data Agent**
   - **New → Data agent**, name it `Enterprise Insight Assistant`.
   - Attach the **semantic model** (governed measures) and the **Lakehouse**.
   - If Fabric IQ is available, connect it so the agent resolves concepts → data.

4. **Set instructions**
   - Paste [system-prompt.md](system-prompt.md) into the agent's **Instructions**.
   - Paste the KPI definitions from [kpis.md](kpis.md) into a data-source note or the
     instructions so the agent interprets KPIs consistently.

5. **Test** — Run the [sample questions](sample-questions.md) and confirm each answer
   follows the **Answer → Insights → Drivers → Actions** structure and never invents data.

## What "good" looks like

> **Q:** "Why did margin slip in Q4?"
>
> **A (answer):** Gross margin % fell ~2.3 pts in Q4 vs Q3.
> **Insights:** Mobile, our highest-volume Q4 category, carries the lowest margin and
> Enterprise discounting deepened.
> **Drivers:** Q4 mix shifted toward discounted Enterprise Mobile orders.
> **Actions:** Tighten Enterprise discount approval on Mobile; promote higher-margin
> Peripherals bundles in Q4.
