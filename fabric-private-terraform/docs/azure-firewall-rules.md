# Azure Firewall rules for Fabric

Reference for the rules created by `modules/firewall`.

Sources:
- [Fabric service tags](https://learn.microsoft.com/fabric/security/security-service-tags)
- [Power BI/Fabric allow-list URLs](https://learn.microsoft.com/fabric/security/power-bi-allow-list-urls)
- [Azure Firewall service tags](https://learn.microsoft.com/azure/firewall/service-tags)

## Network rule collection group — `rcg-fabric-network` (priority 1000)

| Collection | Pri | Rule | Protocol | Ports | Source | Destination service tag(s) | Why |
|---|---|---|---|---|---|---|---|
| `allow-fabric-sql` | 1100 | `fabric-sql-warehouse` | TCP | 1433, 11000-11999 | `*` | `Sql.<home>`, `Sql.<paired>` | Warehouse + SQL endpoint + redirect range |
| `allow-powerbi` | 1200 | `powerbi` | TCP | 443 | `*` | `PowerBI.<home>`, `PowerBI.<paired>` | Portal, item APIs |
| `allow-datafactory` | 1300 | `datafactory` | TCP | 443 | `*` | `DataFactory.<home>`, `DataFactory.<paired>` | Pipelines, copy activities |
| `allow-datafactory` | 1300 | `datafactory-management` | TCP | 443 | `*` | `DataFactoryManagement` | On-prem pipeline / SHIR mgmt plane (outbound only) |
| `allow-eventhub` | 1400 | `eventhub` | TCP | 443, 5671-5672 | `*` | `EventHub.<home>`, `EventHub.<paired>` | Real-Time Intelligence |
| `allow-global-tags` | 1900 | `aad` | TCP | 443 | `*` | `AzureActiveDirectory` | Sign-in & token endpoints |
| `allow-global-tags` | 1900 | `powerquery` | TCP | 443 | `*` | `PowerQueryOnline` | Mashup engine |
| `allow-global-tags` | 1900 | `monitor` | TCP | 443 | `*` | `AzureMonitor` | Diagnostics |
| `allow-global-tags` | 1900 | `storage` | TCP | 443 | `*` | `Storage` | OneLake fallback / staging |

> The Fabric service-tag doc lists `KustoAnalytics` but explicitly notes it is
> **not** usable with Azure Firewall — that's why it isn't here. For Kusto /
> Real-Time Analytics outbound, use the application rule on `*.kusto.windows.net`
> (add it if your demo needs it).

## Application rule collection group — `rcg-fabric-application` (priority 2000)

| Collection | Pri | Rule | Type/port | Destinations |
|---|---|---|---|---|
| `allow-fabric-fqdns` | 2100 | `fabric-portal-and-apis` | HTTPS/443 | `app.fabric.microsoft.com`, `api.fabric.microsoft.com`, `api.powerbi.com`, `content.powerapps.com`, `dc.services.visualstudio.com`, `gatewayadminportal.azure.com` |
| `allow-fabric-fqdns` | 2100 | `fabric-wildcards` | HTTPS/443 | `*.fabric.microsoft.com`, `*.powerbi.com`, `*.analysis.windows.net`, `*.pbidedicated.windows.net`, `*.datawarehouse.fabric.microsoft.com`, `*.datamart.fabric.microsoft.com`, `*.database.fabric.microsoft.com`, `*.powerquery.microsoft.com`, `*.servicebus.windows.net`, `*.events.data.microsoft.com` |
| `allow-fabric-fqdns` | 2100 | `aad-login` | HTTPS/443 | `login.microsoftonline.com`, `login.windows.net`, `aadcdn.msftauth.net`, `aadcdn.msauth.net`, `*.msftidentity.com`, `*.msauth.net` |
| `allow-fqdn-tags` | 2200 | `windows-update` | (FQDN tags) | `WindowsUpdate`, `WindowsDiagnostics`, `MicrosoftActiveProtectionService` |

## DNS proxy

The firewall policy enables **DNS proxy** (`dns.proxy_enabled = true`). When
spoke / on-prem clients use the firewall's private IP as their DNS server (push
it via DHCP option 6 in the spoke, or via your on-prem DHCP), the firewall
forwards to Azure-provided DNS — which in turn resolves the private endpoint
records correctly because the hub VNet is linked to the Fabric private DNS
zones.

This pattern is an **alternative** to the Private DNS Resolver: pick one or the
other, not both, for the same client. Recommended split:
- **In-VNet workloads**: point DNS at the Firewall private IP.
- **On-prem workloads**: point conditional forwarders at the Private DNS
  Resolver inbound IP (firewall DNS proxy doesn't accept queries from on-prem
  by default — it only proxies for VNet clients).

## Things this stack does NOT cover

- **Forced tunneling** of on-prem default route into the firewall (set
  `azurerm_firewall.this.firewall_force_tunnel_address` and add the management
  subnet if you need symmetric routing of internet traffic).
- **Threat Intel** in alert-only or deny mode — enable in
  `azurerm_firewall_policy` if your security team requires it.
- **TLS inspection** — requires Firewall Premium tier and a CA hierarchy.
- **NSG-level service tags** for the PE subnet — Microsoft recommends leaving
  the PE subnet wide open (no NSG) because Azure platform manages PE traffic.
  We attach an empty NSG for diagnostics flow logs only.
