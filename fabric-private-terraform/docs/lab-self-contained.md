# Self-contained demo lab — fake on-prem in Azure

This sample includes an optional **simulated on-premises** module: a peered VNet (10.60.0.0/16) plus a Windows Server 2022 VM auto-promoted to a **new AD DS forest with AD-integrated DNS**. With it enabled, you get an end-to-end Fabric-private-link demo entirely in one Azure subscription — no ExpressRoute, no VPN, no real on-prem hardware.

```
                          (your laptop)
                              │  RDP
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │   "Fake on-prem" VNet  10.60.0.0/16                     │
   │                                                         │
   │   ┌───────────────────────────┐   custom DNS server     │
   │   │  labdc01  (Windows 2022)  │   for the VNet          │
   │   │  AD DS + DNS              │                         │
   │   │  10.60.1.10               │                         │
   │   │                           │                         │
   │   │  Conditional forwarders ──┼───┐                     │
   │   │   privatelink.analysis... │   │                     │
   │   │   privatelink.pbi...      │   │                     │
   │   │   ...                     │   │                     │
   │   └───────────────────────────┘   │                     │
   │                                   │                     │
   └───────────── peering ─────────────┼─────────────────────┘
                                       │
                                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │   Hub VNet  10.50.0.0/16                                │
   │                                                         │
   │   Private DNS Resolver       Azure Firewall             │
   │   inbound  10.50.2.x   ◀─┐   service-tag rules          │
   │                          │                              │
   │   Private DNS zones      │                              │
   │   (linked to hub)        │                              │
   │   privatelink.analysis...│                              │
   │   ...                    │                              │
   │                          │                              │
   │   Private endpoint       │                              │
   │   for Fabric tenant ─────┘                              │
   │   (privateLinkServicesForPowerBI)                       │
   └─────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                                Microsoft Fabric tenant
```

## What the simulated-onprem module gives you

| Resource | Purpose |
|---|---|
| Spoke VNet `10.60.0.0/16` | Acts as the "on-prem" L3. Custom DNS = lab DC. |
| Bidirectional VNet peering with hub | Replaces ExpressRoute Private Peering for the demo. |
| `vm-<prefix>-dc` Windows Server 2022 | AD DS forest root + AD-integrated DNS. |
| Custom Script Extension | Installs AD DS, promotes forest, schedules a one-shot task to add Fabric conditional forwarders after reboot. |
| Optional public IP + NSG | RDP for the demo operator (locked down to your CIDR). |

The conditional forwarders point all 8 Fabric DNS zones at the **Private DNS Resolver inbound endpoint** in the hub — this is the same configuration you'd push to a real on-prem Windows DNS server.

## Why this works for the demo

A Fabric customer running this in production has on-prem AD-integrated DNS forwarding the 8 Fabric private zones to the cloud resolver inbound IP — that's the supported pattern in the [Fabric Private Link reference architecture](https://learn.microsoft.com/fabric/security/security-private-links-overview).

**The same DNS chain works inside this lab**, because:

- DC's NIC DNS = its own loopback (set by AD DS install)
- Spoke VNet's custom DNS = DC IP (set by Terraform)
- DC has conditional forwarders for `privatelink.analysis.windows.net`, etc. → Resolver inbound IP
- Resolver answers from the Private DNS zones linked to the hub
- Private DNS zones return the private IP of the `Microsoft.PowerBI/privateLinkServicesForPowerBI` private endpoint
- Traffic flows over the peering to the hub PE subnet

So when you `Resolve-DnsName <tenantId>-api.privatelink.analysis.windows.net` on the lab DC, you get a `10.50.3.x` answer, not a public IP. Power BI Desktop / SSMS / `Test-NetConnection -Port 1433` will all use the private path.

## Cost / quota caveats

- **VM quota.** The DC needs ~2 vCPU. Some MCAPS-governed subscriptions have 0 VM quota by default — request quota in the target region first or skip this module.
- **B2ms** is the smallest size that runs AD DS + DNS without timing out the Custom Script Extension. B1ms tends to fail promotion.
- **Public IP.** Default `onprem_enable_public_ip = true` so you can RDP. Set false and use Bastion if your tenant disallows public IPs on VMs.
- **Password sensitivity.** `onprem_admin_password` is sensitive and required when the toggle is on. Use a vault-backed source (e.g. `TF_VAR_onprem_admin_password = (Get-Secret …)`).

## Quickstart

```powershell
# Prereqs: az login, terraform installed, fabric_tenant_id known.

cd fabric-private-terraform

$env:TF_VAR_onprem_admin_password = 'P@ssw0rd-CHANGEME-12345!'

terraform init
terraform plan  -var-file terraform.tfvars `
                -var enable_simulated_onprem=true `
                -var onprem_admin_source_ip_cidr=$(curl -s https://api.ipify.org)/32

terraform apply -var-file terraform.tfvars `
                -var enable_simulated_onprem=true `
                -var onprem_admin_source_ip_cidr=$(curl -s https://api.ipify.org)/32
```

After ~12-15 min the AD bootstrap is done. Get the outputs:

```powershell
terraform output onprem_dc_public_ip
terraform output onprem_rdp_login_user        # LAB\labadmin
terraform output dns_resolver_inbound_ip      # used by the conditional forwarders
```

## Verifying the lab end-to-end

> All commands below run **on the lab DC** over RDP — that's the whole point of the lab: simulating an on-prem operator.

### 1. Confirm the DC's role

```powershell
Get-ADDomain                  # should return your domain (e.g. lab.contoso.local)
Get-DnsServerZone             # should list privatelink.* zones with ZoneType=Forwarder
Get-DnsServerForwarder
```

### 2. Confirm Fabric DNS resolves to private IPs

```powershell
C:\Tools\Test-FabricResolution.ps1
```

Sample expected output — note the private 10.50.x.x answers, not public:

```
==> <tenantId>-api.privatelink.analysis.windows.net
Name                                            Type   IPAddress
----                                            ----   ---------
<tenantId>-api.privatelink.analysis.windows.net A      10.50.3.4
```

### 3. Confirm TCP reachability

```powershell
Test-NetConnection -ComputerName "<tenantId>-api.privatelink.analysis.windows.net" -Port 443
Test-NetConnection -ComputerName "<tenantId>-warehouse.privatelink.analysis.windows.net" -Port 1433
```

Both should show `TcpTestSucceeded : True`. (Tenant-level Azure Private Link must be enabled in the Fabric portal first — see [post-deploy.md](./post-deploy.md).)

### 4. Negative test (proves the private path is being used)

Disable the conditional forwarder for one zone and re-run the resolution test:

```powershell
Remove-DnsServerZone -Name privatelink.analysis.windows.net -Force
C:\Tools\Test-FabricResolution.ps1
# Now resolves to a public IP — proves the private path was actually engaged.
Add-DnsServerConditionalForwarderZone `
  -Name privatelink.analysis.windows.net `
  -MasterServers <resolver_inbound_ip> `
  -ReplicationScope Forest
```

### 5. Run the Power BI Desktop / SSMS demo

Install on the lab DC (download from [https://aka.ms/pbidesktop](https://aka.ms/pbidesktop), [https://aka.ms/ssmsfullsetup](https://aka.ms/ssmsfullsetup)) and connect to your Fabric workspace's Warehouse private FQDN. Connection traverses peering → hub PE → Fabric tenant — all without going to the Internet.

### 6. (Optional) Fabric Managed Private Endpoint demo

Once a private data source exists (e.g. a private Azure SQL DB), run [`scripts/fabric/Create-FabricMpe.ps1`](../scripts/fabric/Create-FabricMpe.ps1) from the DC. See [`managed-private-endpoints.md`](./managed-private-endpoints.md) for the full flow.

## Troubleshooting

- **Custom Script Extension stuck at "Provisioning succeeded" but AD not promoted.** RDP to the VM, check `C:\bootstrap\install-ad.log`. Most common cause: weak password (must satisfy default Windows complexity).
- **Phase 2 task didn't run.** Check `C:\bootstrap\phase2.log`. The task runs at startup; verify the post-promo reboot actually happened.
- **DNS resolves to public IP from the DC.** Either (a) the conditional forwarder is missing — check `Get-DnsServerZone | Where ZoneType -eq 'Forwarder'`, or (b) tenant Azure Private Link is not yet enabled in the Fabric portal — that takes ~15min to propagate.
- **`Test-NetConnection` to 443 succeeds but to 1433 fails.** Likely the firewall network rule for `Sql` service tag isn't reaching the warehouse private IP. Check the firewall rule collection group `rcg-fabric-network` and confirm the spoke VNet UDR points the destination at the firewall.
- **Cannot RDP — connection times out.** Public IP NSG only allows your `onprem_admin_source_ip_cidr`; if your IP changed, run `terraform apply` with the new value.
