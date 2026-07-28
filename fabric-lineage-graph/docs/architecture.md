# Architecture

## Layers

```
+--------------------------------------------------------------+
|                       Streamlit Data App                     |
|        (lineage graph + glossary editor + access reqs)       |
+----------+------------------------+--------------------------+
           |                        |
           v                        v
+----------+----------+   +---------+---------+
|  User Data Function |   |  User Data Function|
|   udf_lineage       |   |  udf_glossary      |
|   udf_workflows     |   |  udf_entra_sync    |
+----------+----------+   +---------+----------+
           |                        |
           v                        v
+----------+--------------------------------+
|        OneLake Lakehouse `lh_lineage`     |
|           Delta table: lineage_edges      |
+----------+--------------------------------+
           ^
           | (append)
+----------+----------+
|  Scheduled Notebook |
|  01_harvest_all     |
+---+----+----+----+--+
    |    |    |    |
    v    v    v    v
  ADF  PBI T-SQL Notebooks
       ...   (sqlglot, ast walk, REST)

[02_publish_to_purview]  --reads lineage_edges, upserts Atlas v2-->  Purview
[03_glossary_workflows]  --triggers Create-Term, Bulk-Update -------> Purview workflows
[04_entra_group_sync]    --reconciles approved-access users --------> MS Graph + Purview RBAC
```

## Why this shape

- **Single source of truth = OneLake Delta**. The graph backing store lives in the
  customer's tenant, so the lineage view works even when Purview is unreachable
  or pricier than warranted.
- **Purview is the publication target**, not the primary store. Edges flow one
  way: harvester → Delta → Purview. If a customer deletes Purview, the graph
  still works.
- **All write paths go through UDFs**. The Streamlit app never writes Purview
  directly — this gives one audit point and lets the same APIs be reused by
  CI/CD pipelines, external apps, or a future Blazor UI.
- **Scheduled by Fabric Data Pipeline**, not Azure-side cron. Customer needs no
  extra Function App / Logic App for the harvest cadence.

## Identity flow

| Caller | Token | Used for |
|---|---|---|
| Streamlit app (in Fabric) | Workspace MI | Calling UDFs, reading lineage_edges |
| User Data Functions | Function MI | Purview Atlas, MS Graph, OneLake |
| Scheduled notebooks | Notebook runtime identity | OneLake write, ADF REST, PBI Scanner |
| Local dev (`az login`) | `AzureCliCredential` | Same surfaces, for testing |

The MCAPS deny-policy concerns recorded in user memory (`SP data-plane 403s`)
do not apply here because every Fabric runtime uses a workload identity, not a
classic SPN.

## Failure modes & guardrails

| Risk | Mitigation |
|---|---|
| One harvester crashes -> full pipeline fails | Notebook 01 wraps each harvester in `try/except`, logs and continues |
| Lineage edges balloon (long retention) | `lineage_edges` is a Delta table — apply OPTIMIZE + VACUUM via a weekly notebook (not yet scaffolded) |
| Purview throttles on bulk upsert | `purview_client.upsert_edges` retries on 429 with exp. backoff |
| Power BI scanner API requires tenant admin | If permissions missing, harvester returns 0 edges, doesn't crash |
| Static parsing misses dynamic SQL / param paths | Parsers capture the raw expression in `extra["raw_arg"]` for downstream resolution |

## Out of scope / explicitly NOT built

- Runtime hooks (Spark listener, SQL query store) — static parsing first, runtime collector is a follow-up.
- Column-level lineage for Power BI DAX (M-step lineage only in the first cut).
- De-provisioning workflow (remove user from group on access expiry) — placeholder noted in `04_entra_group_sync.ipynb`.
- Delta retention/optimize job — should be added before going to a real customer estate.
