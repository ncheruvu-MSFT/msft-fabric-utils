# Fabric Apps Hackathon 2026 — Judge Summary

## Project Name

**Fabric Lineage Explorer**

## Team

| Name | Title |
|------|-------|
| Naga Venkata Cheruvu | Senior Cloud Solution Architect |
| Paul Singh | Principal Cloud Solution Architect |
| Matthew Thanakit | Principal Cloud Solution Architect |

## Problem

Organizations adopting Microsoft Fabric often struggle to understand how data assets are connected across workspaces, semantic models, lakehouses, warehouses, reports, and pipelines. Existing lineage experiences provide valuable information but can become difficult to navigate as environments grow.

This creates challenges for:

- Change impact analysis
- Governance and compliance reviews
- Troubleshooting broken dependencies
- Migration and modernization planning
- Knowledge transfer between teams

## Solution

Fabric Lineage Explorer is a Rayfin-powered Microsoft Fabric App that transforms lineage metadata into an interactive graph experience.

Users can:

- Discover upstream and downstream dependencies
- Visualize end-to-end data flows across medallion architecture layers
- Trace individual columns through transformations (Source → Bronze → Silver → Gold → Semantic → Report)
- Analyze potential impacts before making changes
- Navigate relationships across Fabric assets using natural language queries
- Better understand complex Fabric environments

## Why Rayfin?

The project demonstrates how Fabric Apps (Rayfin) can be used to build governed applications directly within the Fabric ecosystem, bringing business logic, visualization, and metadata experiences close to the data platform.

- TypeScript entity classes → Fabric SQL DB schema, GraphQL CRUD, typed client
- Row-level authorization via `@role` policies with Entra claims
- Fabric SSO built in — no custom MSAL wiring
- Apps + child SQL DB inherit workspace RBAC, sensitivity labels, audit, capacity governance

## Key Capabilities

- ✅ Interactive column-level lineage graph visualization (SVG)
- ✅ Table-level lineage edge grid with sortable, filterable data
- ✅ Upstream and downstream dependency exploration
- ✅ Impact analysis with column tracing
- ✅ Intelligent data agent (chat interface) for natural language lineage queries
- ✅ Relationship discovery across 6 medallion layers
- ✅ Search and navigation
- ✅ Fabric-native application experience with Fluent UI v9
- ✅ Dual-mode operation (live backend + seed data fallback)
- ✅ RBAC-protected entities with admin/owner policies

## Business Value

Fabric Lineage Explorer helps reduce risk associated with platform changes while improving operational efficiency and governance visibility.

Potential benefits:

- Faster troubleshooting through visual end-to-end tracing
- Easier modernization planning with impact analysis
- Better governance visibility across the data estate
- Reduced change-management risk
- Improved cross-team collaboration and knowledge sharing

## Innovation

Rather than displaying lineage as static tables or isolated dependency views, the application presents lineage as a navigable, interactive graph experience optimized for discovery and impact analysis — with column-level granularity across the full medallion architecture and a conversational data agent for natural language queries.

## Architecture

```
+----------------------------------+
| Microsoft Fabric                 |
| Workspaces / Assets / Lineage    |
+---------------+------------------+
                |
                v
+----------------------------------+
| Metadata Retrieval Layer         |
| Fabric APIs + Harvest Notebooks  |
+---------------+------------------+
                |
                v
+----------------------------------+
| OneLake Delta Table              |
| lineage.edges (unified schema)   |
+---------------+------------------+
                |
                v
+----------------------------------+
| Rayfin App Backend               |
| GraphQL API + Entity Storage     |
+---------------+------------------+
                |
                v
+----------------------------------+
| React + Fluent UI + SVG Graph    |
| Search | Navigate | Chat | Trace |
+----------------------------------+
```
