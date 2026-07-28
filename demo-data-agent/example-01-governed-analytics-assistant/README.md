# Example 1 — Governed Analytics Assistant

A disciplined natural-language analytics assistant. It translates business questions into
the correct analytical query (SQL / DAX / KQL) and returns **only validated, governed
results** from the connected Fabric sources — never invented data.

| | |
|---|---|
| **Grounding** | Lakehouse star schema + [semantic model](../semantic-model/README.md) |
| **Query languages** | SQL (Lakehouse SQL endpoint), DAX (semantic model), KQL (if an Eventhouse is attached) |
| **Personality** | Concise, business-friendly, governance-first |

## Files

| File | Purpose |
|------|---------|
| [system-prompt.md](system-prompt.md) | Paste into the Data Agent's **instructions** |
| [agent-config.json](agent-config.json) | Reference config (data sources, example queries, guardrails) |
| [sample-questions.md](sample-questions.md) | Demo script with expected behavior |

## Setup in Fabric

1. **Prepare data** — Complete the steps in the [top-level README](../README.md#quick-start)
   so you have a Lakehouse with the 5 tables and a semantic model with the measures.

2. **Create a Data Agent**
   - In your workspace: **New → Data agent** (preview).
   - Name it e.g. `Governed Analytics Assistant`.

3. **Add data sources**
   - Attach the **Lakehouse** (SQL analytics endpoint) — gives the agent SQL access.
   - Attach the **semantic model** — gives the agent governed DAX measures/KPIs.
   - (Optional) Attach an **Eventhouse/KQL database** for the KQL demo.

4. **Set instructions**
   - Open the agent's **Instructions** and paste the contents of
     [system-prompt.md](system-prompt.md).

5. **Add per-source notes** (recommended)
   - On the semantic-model source, add: *"Always use defined measures (Total Revenue,
     Gross Margin %, Revenue YoY %). Revenue is net of discount."*
   - On the Lakehouse source, add the join keys from
     [agent-config.json](agent-config.json) so generated SQL joins correctly.

6. **Add example queries** (optional but improves accuracy)
   - Copy the validated SQL/DAX snippets from [agent-config.json](agent-config.json) into
     the agent's example queries.

7. **Test** — Run the [sample questions](sample-questions.md) and confirm the agent:
   - returns governed numbers,
   - shows trends/breakdowns,
   - and **refuses** to answer when the data isn't present.

## What "good" looks like

- ✅ "Total 2025 revenue was **$X.XM**, up **~18% YoY**, led by the Mobile category in Q4."
- ✅ "I don't have churn data in the connected sources, so I can't answer that."
- ❌ Inventing a churn rate, or reporting `ListPrice × Quantity` as revenue.
