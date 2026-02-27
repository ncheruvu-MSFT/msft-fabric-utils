# Azure Container Apps – Private VNet Deployment with ExpressRoute

This sample deploys an **Azure Container Apps (ACA) environment** that is:

- Injected into a **Virtual Network** (internal-only, no public IP)
- **Public network access disabled**
- Accessible via **Private Endpoint** + **Private DNS Zone**
- Reachable from on-premises over **ExpressRoute** with proper **DNS forwarding**

> **Note:** The VNet and subnets must already exist before deploying. The Private
> Endpoint subnet can be in a **different VNet, subscription, and resource group**
> from the ACA environment.

---

## Architecture

```
On-Premises Network
  │
  ├── ExpressRoute Circuit ──── ExpressRoute Gateway
  │                                    │
  │   On-Prem DNS Server               │
  │   (conditional forwarder ───►  Azure Private DNS Resolver / DNS forwarder VM)
  │    *.azurecontainerapps.io)         │
  │                                    │
  └────────────────────────────── Azure VNet (existing)
                                       ├── snet-aca-infra         ← ACA Environment (delegated, /23+)
                                       └── (optional) snet-dns-resolver ← DNS forwarder

                                  PE VNet (same or different VNet/subscription)
                                       └── snet-private-endpoints ← Private Endpoint

                                  Private DNS Zone:
                                    <env-unique-id>.<region>.azurecontainerapps.io
                                      *.  → ACA static IP
                                      @   → ACA static IP
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Azure CLI ≥ 2.61 | `az upgrade` |
| Bicep CLI ≥ 0.28 | Bundled with Azure CLI |
| Azure subscription | With `Contributor` + `Network Contributor` roles |
| Resource providers | `Microsoft.App`, `Microsoft.Network`, `Microsoft.OperationalInsights` registered |
| VNet + ACA subnet | Existing VNet with a subnet delegated to `Microsoft.App/environments` (/23 minimum) |
| PE subnet | Existing subnet for private endpoints (can be in a different VNet/subscription) |
| ExpressRoute circuit | Already provisioned and connected (for on-prem connectivity) |

---

## Step 1 – Deploy Everything (Automated)

The easiest way is to use the deploy script which orchestrates both phases:

```powershell
cd aca-private-deployment

# PE subnet in the same VNet as ACA
.\deploy.ps1 -ResourceGroupName "rg-aca-private-demo" -Location "eastus2" `
    -AcaSubnetId "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-aca-infra" `
    -PeSubnetId  "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-pe"

# PE subnet in a different VNet / subscription / resource group
.\deploy.ps1 -ResourceGroupName "rg-aca-demo" -Location "eastus2" `
    -AcaSubnetId "/subscriptions/<aca-sub>/resourceGroups/<aca-rg>/providers/Microsoft.Network/virtualNetworks/<aca-vnet>/subnets/snet-aca" `
    -PeSubnetId  "/subscriptions/<pe-sub>/resourceGroups/<pe-rg>/providers/Microsoft.Network/virtualNetworks/<pe-vnet>/subnets/snet-pe"
```

This script:
1. Registers required resource providers
2. Creates the resource group
3. **Phase 1** – Deploys ACA Environment and Hello-World app into the existing VNet/subnet
4. **Phase 2** – Uses runtime outputs to create Private DNS Zone + Private Endpoint
5. Disables public network access via CLI

### Manual Deployment (Step-by-Step)

```powershell
$RG         = "rg-aca-private-demo"
$LOCATION   = "eastus2"
$ACA_SUBNET = "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-aca-infra"
$PE_SUBNET  = "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/snet-pe"

# Create resource group
az group create --name $RG --location $LOCATION

# Phase 1: ACA Environment + Hello-World (uses existing VNet/subnet)
az deployment group create `
  --name "aca-private-phase1" `
  --resource-group $RG `
  --template-file ./infra/main.bicep `
  --parameters ./infra/main.bicepparam `
  --parameters location=$LOCATION acaSubnetId=$ACA_SUBNET
```

### Capture Phase 1 outputs and deploy Phase 2

```powershell
$outputs = az deployment group show `
  --name "aca-private-phase1" `
  --resource-group $RG `
  --query "properties.outputs" -o json | ConvertFrom-Json

$ACA_FQDN      = $outputs.containerAppFqdn.value
$ACA_STATIC_IP = $outputs.acaEnvironmentStaticIp.value
$ACA_DOMAIN    = $outputs.acaEnvironmentDefaultDomain.value
$ACA_ENV_ID    = $outputs.acaEnvironmentId.value
$ACA_ENV_NAME  = $outputs.acaEnvironmentName.value

# Derive VNet info from subnet IDs
$ACA_VNET_ID   = ($ACA_SUBNET -split '/subnets/')[0]
$ACA_VNET_NAME = ($ACA_VNET_ID -split '/')[-1]
$PE_VNET_ID    = ($PE_SUBNET -split '/subnets/')[0]
$PE_VNET_NAME  = ($PE_VNET_ID -split '/')[-1]

Write-Host "App FQDN     : $ACA_FQDN"
Write-Host "Static IP    : $ACA_STATIC_IP"
Write-Host "ACA Domain   : $ACA_DOMAIN"

# Phase 2: Private DNS Zone + Private Endpoint
az deployment group create `
  --name "aca-private-phase2" `
  --resource-group $RG `
  --template-file ./infra/private-dns.bicep `
  --parameters `
    location=$LOCATION `
    acaDefaultDomain=$ACA_DOMAIN `
    acaStaticIp=$ACA_STATIC_IP `
    acaEnvironmentId=$ACA_ENV_ID `
    acaEnvironmentName=$ACA_ENV_NAME `
    acaVnetId=$ACA_VNET_ID `
    acaVnetName=$ACA_VNET_NAME `
    peSubnetId=$PE_SUBNET `
    peVnetId=$PE_VNET_ID `
    peVnetName=$PE_VNET_NAME

# Disable public network access
az containerapp env update `
  --name $ACA_ENV_NAME `
  --resource-group $RG `
  --enable-public-network-access false
```

---

## Step 2 – Verify Deployment

### From a VM inside the same VNet (or peered VNet)

```bash
# DNS resolution should return the ACA static IP
nslookup <your-app>.internal.<region>.azurecontainerapps.io

# Curl the hello-world app
curl https://<your-app-fqdn>
```

### From Azure Cloud Shell (won't work – expected)

Because public network access is disabled, the app is **not reachable from the public internet**. This is by design.

---

## Step 3 – Connect ExpressRoute Gateway to the VNet

If you already have an ExpressRoute circuit and gateway, peer them to this VNet:

```powershell
# Create a GatewaySubnet if not present (required for ExpressRoute gw)
az network vnet subnet create `
  --resource-group $RG `
  --vnet-name "<vnet-name>" `
  --name GatewaySubnet `
  --address-prefixes "10.100.4.0/27"

# Create the ExpressRoute gateway
az network vnet-gateway create `
  --resource-group $RG `
  --name "ergw-aca-private" `
  --vnet "<vnet-name>" `
  --gateway-type ExpressRoute `
  --sku Standard `
  --location $LOCATION

# Create connection to your existing ExpressRoute circuit
az network vpn-connection create `
  --resource-group $RG `
  --name "er-connection" `
  --vnet-gateway1 "ergw-aca-private" `
  --express-route-circuit2 "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/expressRouteCircuits/<circuit-name>" `
  --location $LOCATION
```

---

## Step 4 – DNS Forwarding for On-Premises Resolution (AD / ExpressRoute)

For on-premises clients (connected via ExpressRoute) to resolve the ACA environment's private FQDN, you need **DNS forwarding** from on-prem DNS servers to Azure.

### Option A: Azure DNS Private Resolver (Recommended)

This is the **managed, serverless** approach — no VMs to maintain.

```powershell
# 1. Create a DNS Resolver subnet (minimum /28, no other delegations)
az network vnet subnet create `
  --resource-group $RG `
  --vnet-name "<vnet-name>" `
  --name "snet-dns-resolver" `
  --address-prefixes "10.100.3.0/28" `
  --delegations "Microsoft.Network/dnsResolvers"

# 2. Create the DNS Private Resolver
az dns-resolver create `
  --resource-group $RG `
  --name "dnspr-aca-private" `
  --location $LOCATION `
  --id "/subscriptions/<sub>/resourceGroups/$RG/providers/Microsoft.Network/virtualNetworks/<vnet-name>"

# 3. Create an Inbound Endpoint (this is what on-prem DNS forwards to)
az dns-resolver inbound-endpoint create `
  --resource-group $RG `
  --dns-resolver-name "dnspr-aca-private" `
  --name "inbound-ep" `
  --location $LOCATION `
  --ip-configurations '[{"private-ip-allocation-method":"Dynamic","id":"/subscriptions/<sub>/resourceGroups/'$RG'/providers/Microsoft.Network/virtualNetworks/<vnet-name>/subnets/snet-dns-resolver"}]'

# 4. Note the inbound endpoint IP
az dns-resolver inbound-endpoint show `
  --resource-group $RG `
  --dns-resolver-name "dnspr-aca-private" `
  --name "inbound-ep" `
  --query "ipConfigurations[0].privateIpAddress" -o tsv
```

The **inbound endpoint IP** (e.g., `10.100.3.4`) is what you configure on your on-prem DNS servers as the forwarding target.

### Option B: DNS Forwarder VM (Legacy)

Deploy a Windows Server or Linux VM in the VNet with DNS forwarding configured:

```powershell
# Example: Windows Server with DNS role
# After deploying a Windows Server VM in the VNet:

# On the VM (PowerShell):
Install-WindowsFeature -Name DNS -IncludeManagementTools

# Add a conditional forwarder for the ACA domain
Add-DnsServerConditionalForwarderZone `
  -Name "<env-id>.<region>.azurecontainerapps.io" `
  -MasterServers 168.63.129.16   # Azure DNS virtual server IP
```

> **Note:** `168.63.129.16` is Azure's recursive DNS resolver. It resolves private DNS zone records when queried from within the VNet.

---

## Step 5 – Configure On-Premises DNS (Active Directory DNS)

On your **on-premises Active Directory DNS servers**, create a conditional forwarder:

### Windows Server DNS (GUI)

1. Open **DNS Manager** → right-click **Conditional Forwarders** → **New Conditional Forwarder**
2. **DNS Domain**: enter the ACA environment's default domain  
   Example: `kindocean-a1b2c3d4.eastus2.azurecontainerapps.io`
3. **IP addresses**: enter the Azure DNS Private Resolver inbound endpoint IP  
   Example: `10.100.3.4`
4. Check **Store this conditional forwarder in Active Directory** → select replication scope
5. Click **OK**

### Windows Server DNS (PowerShell)

```powershell
# Run on each AD DNS server (or one if stored in AD-integrated zone)
Add-DnsServerConditionalForwarderZone `
  -Name "<env-id>.<region>.azurecontainerapps.io" `
  -MasterServers "10.100.3.4" `
  -ReplicationScope "Forest"
```

### For all Azure private DNS zones (broader approach)

If you use multiple Azure private DNS zones, you may want a broader forwarder:

```powershell
# Forward ALL azurecontainerapps.io queries to Azure
Add-DnsServerConditionalForwarderZone `
  -Name "azurecontainerapps.io" `
  -MasterServers "10.100.3.4" `
  -ReplicationScope "Forest"

# Also consider forwarding other Azure private zones:
# - privatelink.azurecr.io
# - privatelink.vaultcore.azure.net
# - privatelink.blob.core.windows.net
# etc.
```

---

## Step 6 – Test End-to-End from On-Premises

```powershell
# 1. Verify DNS resolution
nslookup helloworld.kindocean-a1b2c3d4.eastus2.azurecontainerapps.io

# Expected: returns the ACA static IP (e.g., 10.100.0.x)

# 2. Test HTTP connectivity
curl https://helloworld.kindocean-a1b2c3d4.eastus2.azurecontainerapps.io

# 3. If using PowerShell:
Invoke-WebRequest -Uri "https://helloworld.kindocean-a1b2c3d4.eastus2.azurecontainerapps.io" -UseBasicParsing
```

---

## DNS Forwarding Flow (ExpressRoute)

```
On-Prem Client
    │
    │  DNS query: helloworld.<env>.<region>.azurecontainerapps.io
    ▼
On-Prem AD DNS Server
    │
    │  Conditional forwarder → 10.100.3.4 (Azure DNS Private Resolver)
    ▼
Azure DNS Private Resolver (Inbound Endpoint)
    │
    │  Resolves via linked Private DNS Zone
    ▼
Private DNS Zone: <env>.<region>.azurecontainerapps.io
    │
    │  * A record → 10.100.0.X (ACA static IP)
    ▼
Response returned to on-prem client → 10.100.0.X

On-Prem Client
    │
    │  HTTPS request to 10.100.0.X via ExpressRoute
    ▼
ACA Environment (private, VNet-injected)
    │
    ▼
Hello World Container App responds
```

---

## Troubleshooting

| Issue | Resolution |
|---|---|
| `nslookup` returns NXDOMAIN | Verify the private DNS zone name matches `acaEnv.properties.defaultDomain`. Check VNet link is active. |
| DNS works but HTTP times out | Verify NSG on the ACA subnet allows traffic. Check ExpressRoute route propagation. |
| `publicNetworkAccess` error | Ensure Azure CLI and `Microsoft.App` provider are up-to-date. |
| On-prem can't resolve | Confirm conditional forwarder IP matches the Azure DNS Private Resolver inbound endpoint. |
| TLS certificate error | The ACA environment uses a Microsoft-managed certificate for `*.azurecontainerapps.io`. Ensure you're using the correct FQDN. |

---

## Clean Up

```powershell
az group delete --name $RG --yes --no-wait
```

---

## References

- [Azure Container Apps networking – VNet integration](https://learn.microsoft.com/azure/container-apps/networking)
- [Azure Container Apps with private endpoint](https://learn.microsoft.com/azure/container-apps/networking?tabs=workload-profiles-env%2Cazure-cli#private-endpoint)
- [Azure DNS Private Resolver](https://learn.microsoft.com/azure/dns/dns-private-resolver-overview)
- [Configure DNS forwarders for Azure private endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-dns#on-premises-workloads-using-a-dns-forwarder)
- [ExpressRoute with private endpoints](https://learn.microsoft.com/azure/expressroute/expressroute-private-peering)
