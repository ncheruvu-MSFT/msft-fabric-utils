# Azure Subscription Resource Inventory

Jupyter notebook that **auto-discovers every Azure resource** across one or more subscriptions and exports a comprehensive **Excel workbook** with:

- **One tab per subscription** — full resource listing (name, type, resource group, location, SKU, kind, tags)
- **Summary tab** — aggregated resource-type counts across all subscriptions
- **Summary (Pivot) tab** — pivot table with subscriptions as columns for side-by-side comparison

## Features

| Feature | Details |
|---------|---------|
| **Multi-Subscription** | Supply a list of subscription IDs or auto-discover all accessible ones |
| **Azure Resource Graph** | Uses the `resources` table for fast, cross-subscription queries |
| **Pagination** | Handles `$skipToken` for subscriptions with thousands of resources |
| **Rate-Limit Handling** | Sliding-window tracker (15 req / 5s) + exponential backoff with jitter |
| **Retry-After Support** | Honours the `Retry-After` header on HTTP 429 responses |
| **Excel Export** | Auto-fitted columns, sanitised sheet names, duplicate-name handling |

## Prerequisites

### Permissions

| Scope | Required Role |
|-------|---------------|
| Each subscription | **Reader** (minimum) |
| Azure Resource Graph | No additional role needed |

### Python Packages

The notebook installs these automatically:

- `azure-identity`
- `azure-mgmt-resourcegraph`
- `azure-mgmt-resource`
- `pandas`
- `openpyxl`

### Authentication

Uses `DefaultAzureCredential`, which tries (in order):

1. Environment variables
2. Managed Identity
3. Azure CLI (`az login`)
4. VS Code Azure extension
5. Azure PowerShell
6. Interactive browser

Run `az login` before launching the notebook if running locally.

## Quick Start

```bash
# 1. Clone the repo & navigate
cd azure-resource-inventory

# 2. (Optional) Create a virtual environment
python -m venv .venv && .venv\Scripts\Activate.ps1   # Windows
# python -m venv .venv && source .venv/bin/activate  # Linux/macOS

# 3. Authenticate
az login

# 4. Open the notebook
jupyter notebook azure-subscription-resource-inventory.ipynb
```

Edit the **Configuration** cell to supply specific subscription IDs or leave empty-to auto-discover all.

## API Limits & Throttling

| API | Limit | Handling |
|-----|-------|----------|
| Resource Graph (per tenant) | 15 requests / 5 seconds | Sliding-window auto-throttle |
| Resource Graph (per query) | 1000 rows / page | Automatic `$skipToken` pagination |
| ARM Management | 12,000 reads / hour | Tracked; unlikely to hit |
| HTTP 429 / 5xx | Retryable | Exponential backoff (up to 5 min), `Retry-After` header |

## Output

The notebook generates `azure-resource-inventory.xlsx` with:

| Sheet | Contents |
|-------|----------|
| **Summary** | Flat table: Service Provider, Resource Type, Total Count |
| **Summary (Pivot)** | Pivot: rows = resource types, columns = subscriptions, values = counts |
| **\<Subscription Name\>** | One sheet per subscription with full resource details |

## References

| Topic | Link |
|-------|------|
| Azure Resource Graph | https://learn.microsoft.com/en-us/azure/governance/resource-graph/overview |
| Query language | https://learn.microsoft.com/en-us/azure/governance/resource-graph/concepts/query-language |
| Throttling guidance | https://learn.microsoft.com/en-us/azure/governance/resource-graph/concepts/guidance-for-throttled-requests |
| ARM rate limits | https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/request-limits-and-throttling |
