# Fabric Lineage Explorer

[![Rayfin](https://img.shields.io/badge/Rayfin-Fabric%20App-blue.svg)](https://learn.microsoft.com/fabric/apps/overview)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Fabric Apps Hackathon 2026 Submission**

## Overview

Fabric Lineage Explorer is a Microsoft Fabric App built using Rayfin that enables users to visualize and explore relationships among Fabric assets through an interactive graph-based experience.

The application simplifies dependency discovery and impact analysis by transforming Fabric lineage data into an intuitive and navigable view.

## Business Challenge

As Microsoft Fabric implementations grow, understanding how assets interact becomes increasingly complex.

Common questions include:

- Which reports depend on this semantic model?
- What systems will be affected by a modification?
- What are the upstream sources feeding this asset?
- How can administrators quickly identify critical dependencies?

Fabric Lineage Explorer addresses these challenges through visual lineage exploration.

## Features

### Interactive Graph Visualization

Display assets and relationships as an interactive graph with full medallion architecture support (Source → Bronze → Silver → Gold → Semantic → Report).

### Column-Level Lineage

Trace individual columns through transformation layers — click any column to highlight its complete upstream origins and downstream consumers across the entire data pipeline.

### Dependency Analysis

Explore:

- Upstream dependencies
- Downstream dependencies
- Related assets
- Column-to-column transformations (cast, filter, join, SUM, etc.)

### Intelligent Data Agent

Built-in chat interface powered by a data agent that answers lineage questions in natural language:

- "What feeds fact_sales?"
- "What is downstream of Customers?"
- "How many ADF edges are there?"

Works with both a remote Rayfin GraphQL backend and local heuristic mode.

### Search Experience

Locate and navigate to specific Fabric assets.

### Impact Assessment

Identify potentially affected assets before implementing changes.

### Fabric Integration

Built using Microsoft Fabric Apps (Rayfin) to demonstrate modern application patterns within Microsoft Fabric.

## Architecture

### Components

| Component | Purpose |
|-----------|---------|
| Microsoft Fabric | Metadata source |
| Fabric APIs | Retrieve lineage information |
| Rayfin App Backend | GraphQL API, entity storage, authentication |
| Graph Engine | Generates relationship model with longest-path leveling |
| Visualization Layer | Interactive SVG graph rendering with Fluent UI |
| Data Agent | Natural language lineage queries |

### Solution Flow

```
Microsoft Fabric
│
▼
Lineage Metadata (ADF, T-SQL, Power BI, Spark, Pipelines, Dataflows)
│
▼
Harvest Notebooks (scheduled Data Pipeline)
│
▼
OneLake Delta Table (lineage.edges)
│
▼
Rayfin GraphQL API (User Data Functions)
│
▼
Interactive User Experience (React + Fluent UI + SVG Graph)
```

### Data Entities

| Entity | Purpose |
|--------|---------|
| **LineageEdge** | Core edge records: source → process → target with qualified names |
| **DataAsset** | Asset metadata with Purview integration (purviewGuid) |
| **HarvestRun** | Tracks harvest operations, status, edge counts |
| **Domain** | Governance domains with hierarchical parent support |

### Tech Stack

| Technology | Role |
|------------|------|
| React 18 + TypeScript | Frontend framework |
| Fluent UI v9 | Microsoft design system |
| Vite | Build tooling |
| Rayfin Core | Fabric App backend (GraphQL, auth, SQL DB) |
| SVG + Custom Graph Engine | Column-level lineage visualization |
| NetworkX-style leveling | Longest-path algorithm for clean layer layout |

## Sample Use Cases

### Governance

Understand data movement and dependencies across the Fabric estate.

### Modernization

Assess impacts before migrations — see exactly which downstream reports break if a source table changes.

### Operations

Troubleshoot failures more quickly by tracing data flows end-to-end.

### Architecture Reviews

Visualize end-to-end data flows from source systems through medallion layers to executive reports.

## Getting Started

### Prerequisites

- Node.js 20+
- Rayfin CLI: `npm i -g @microsoft/rayfin-cli`
- Fabric workspace with Fabric Apps (preview) enabled

### Local Development

```bash
npm install
npm run dev          # Vite dev server on port 5173
```

### Build

```bash
npm run build        # TypeScript + Vite production build → dist/
npm run preview      # Preview dist/ locally
```

### Deploy to Fabric

```bash
npx rayfin login
npx rayfin up --dry-run --verbose    # Preview
npx rayfin up --workspace <wsname>   # Deploy
```

## Team

| Name | Role |
|------|------|
| **Naga Venkata Cheruvu** | Solution Architecture, Rayfin Development, Fabric Integration, Project Leadership |
| **Paul Singh** | Solution Review, Business Scenario Validation, Architecture Feedback, UX Recommendations |
| **Matthew Thanakit** | Fabric Architecture Review, Technical Validation, Deployment Review, Testing Support |

## Future Enhancements

- AI-generated lineage explanations
- Governance recommendations
- Critical asset identification
- Purview integration for cross-platform lineage
- Historical lineage comparison
- Natural language search with semantic understanding

## References

- [Fabric Apps overview](https://learn.microsoft.com/fabric/apps/overview)
- [Rayfin SDK overview](https://learn.microsoft.com/javascript/api/fabric-apps-sdk-javascript/rayfin-overview)
- [Define data permissions](https://learn.microsoft.com/fabric/apps/data-permissions)
- [CLI reference](https://learn.microsoft.com/fabric/apps/cli-reference)
- [GitHub: aka.ms/rayfin/GH](https://aka.ms/rayfin/GH)

## License

This project is licensed under the [MIT License](../../LICENSE).
