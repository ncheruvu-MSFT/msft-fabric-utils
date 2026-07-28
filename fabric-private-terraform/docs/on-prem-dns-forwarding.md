# On-premises DNS forwarding for Fabric private endpoints

## Why

Without forwarding, on-prem clients resolve Fabric FQDNs to **public** Microsoft
front-door IPs (because public DNS still returns CNAMEs into
`*.privatelink.analysis.windows.net`). The TLS handshake then either:

1. Goes out the on-prem internet egress → fails when **Block Public Internet
   Access** is enabled on the Fabric tenant, or
2. Goes through the ExpressRoute / VPN but lands on a public IP that doesn't
   route inside your VNet.

Both are fixed by forwarding the relevant DNS zones to the **Azure Private DNS
Resolver inbound endpoint**, which knows about the auto-registered A records in
your Azure Private DNS zones (one per Fabric private endpoint).

## Get the inbound IP

```pwsh
terraform output dns_resolver_inbound_ip
# Example: 10.50.2.4
```

## Windows Server (AD DNS)

```powershell
$resolverIp = '10.50.2.4'

$zones = @(
  'privatelink.analysis.windows.net',
  'privatelink.pbidedicated.windows.net',
  'privatelink.prod.powerquery.microsoft.com',
  # Apex zones — needed because Fabric returns CNAMEs from apex to privatelink.*
  'analysis.windows.net',
  'pbidedicated.windows.net',
  'powerquery.microsoft.com',
  'fabric.microsoft.com',
  'powerbi.com'
)

foreach ($z in $zones) {
  Add-DnsServerConditionalForwarderZone `
    -Name $z `
    -MasterServers $resolverIp `
    -ReplicationScope Forest `
    -UseRecursion $false
}
```

> If you previously had a conditional forwarder for any of these zones (e.g.
> `Get-DnsServerZone | ? IsDsIntegrated`), remove it first or use
> `Set-DnsServerConditionalForwarderZone` to update the master.

## BIND 9 (Linux DNS)

```text
zone "privatelink.analysis.windows.net" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "privatelink.pbidedicated.windows.net" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "privatelink.prod.powerquery.microsoft.com" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "analysis.windows.net" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "pbidedicated.windows.net" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "powerquery.microsoft.com" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "fabric.microsoft.com" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
zone "powerbi.com" {
    type forward;
    forwarders { 10.50.2.4; };
    forward only;
};
```

## Infoblox

NIOS → Data Management → DNS → **Forward Zones** → Add. Create one forward zone
per FQDN above with **External Servers** set to the resolver inbound IP.

## Verify

From any on-prem workstation/server:

```pwsh
nslookup app.fabric.microsoft.com
nslookup <tenantIdNoHyphens>-api.privatelink.analysis.windows.net
nslookup <tenantIdNoHyphens>-onelake.privatelink.analysis.windows.net
```

Expected behaviour:
- `Server: <on-prem DNS>` — query went to your AD DNS first.
- Response addresses are inside your VNet PE subnet (e.g. `10.50.3.x`), **not**
  a public Microsoft IP.

If you still see a public IP:
1. Confirm the on-prem DNS server resolves the conditional-forwarded zone to
   the resolver IP (`Resolve-DnsName -Server <on-prem-dns> ... -DnssecOk:$false`).
2. Confirm the on-prem DNS server has IP route reachability to the resolver IP
   (it must traverse ExpressRoute / VPN — Private DNS Resolver doesn't accept
   queries from the internet).
3. Confirm the Private DNS zones in Azure have a **VNet link** to the hub VNet
   (Terraform does this automatically).
4. Confirm the private endpoint is in **Approved** state (Azure portal → Private
   Endpoint → Connections).

## Caveats

- Only **one tenant per network** can be Fabric-private-linked at a time. If
  another team already has a `privatelink.analysis.windows.net` zone pointing to
  a different tenant's PE, you must coordinate.
- For Fabric workspace-level private links, additional zones may apply — repeat
  the same pattern.
- Private DNS Resolver has a per-endpoint QPS limit (~10k QPS inbound). Plan
  capacity if many on-prem clients use Fabric.
