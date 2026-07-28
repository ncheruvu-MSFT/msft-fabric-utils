# Testing the private path from on-premises

Once the stack is deployed, conditional forwarders are in place, and the
tenant-level Azure Private Link toggle is on, walk through this checklist from
an **on-prem** workstation that routes to Azure over ExpressRoute or VPN.

## 0. Prerequisites checklist

- [ ] `terraform apply` completed cleanly.
- [ ] `terraform output dns_resolver_inbound_ip` returns an IP inside
      `subnet_dnsr_inbound_prefix` (default 10.50.2.0/28).
- [ ] On-prem AD DNS has conditional forwarders for the 8 zones listed in
      [`on-prem-dns-forwarding.md`](on-prem-dns-forwarding.md).
- [ ] ExpressRoute/VPN routes 10.50.0.0/16 (or whatever you chose for the hub
      VNet) reachable from the on-prem workstation.
- [ ] Fabric admin enabled **Azure Private Link** in the tenant settings.
- [ ] Private endpoint shows **Approved** in the Azure portal.

## 1. DNS — confirm private IPs

```pwsh
$tenantNoDash = (Get-AzContext).Tenant.Id -replace '-',''
nslookup app.fabric.microsoft.com
nslookup api.powerbi.com
nslookup "$tenantNoDash-api.privatelink.analysis.windows.net"
nslookup "$tenantNoDash-onelake.privatelink.analysis.windows.net"
nslookup "$tenantNoDash-warehouse.privatelink.analysis.windows.net"
```

Expected: every answer points to your PE subnet (e.g. `10.50.3.x`).

If you still see public IPs, check:
1. `Resolve-DnsName -Server <on-prem-dns> app.fabric.microsoft.com` — chase the
   chain. The CNAME should land on `*.privatelink.analysis.windows.net`.
2. `Resolve-DnsName -Server 10.50.2.4 app.fabric.microsoft.com` — bypass on-prem
   DNS and go straight to the resolver. If this returns a private IP, the
   conditional forwarder is misconfigured.

## 2. TCP — confirm the PE responds

```pwsh
Test-NetConnection -ComputerName app.fabric.microsoft.com -Port 443
Test-NetConnection -ComputerName "$tenantNoDash-onelake.privatelink.analysis.windows.net" -Port 443
```

A successful `TcpTestSucceeded : True` proves:
- Name resolution returned a private IP.
- The IP is routable from on-prem (ExpressRoute / VPN works).
- Azure Firewall allows the flow (if force-tunneled through it).

## 3. Power BI Desktop

1. **File → Get Data → Microsoft Fabric → Lakehouses / Warehouses**.
2. Sign in with a user that's a member of your Fabric workspace.
3. The data source picker should populate with your F2-backed workspace.
4. Network trace (e.g. `Wireshark`) should show traffic going **only** to your
   PE subnet IPs.

## 4. SSMS / sqlcmd against the Warehouse SQL endpoint

```pwsh
$server = "<warehouse-name>.<tenantIdNoHyphens>-onelake.privatelink.analysis.windows.net"
# Open SSMS, "Connect to Database Engine":
#   Server name: $server,1433
#   Authentication: Azure Active Directory - Interactive
```

Or from the CLI:

```pwsh
sqlcmd -S "$server,1433" -G -d <warehouse-name> -Q "SELECT TOP 10 * FROM sys.tables"
```

Confirm with a packet capture that the destination is `10.50.3.x`.

## 5. Azure Firewall — confirm enforcement

Generate a request from inside the VNet (e.g. via the optional jumpbox) and
inspect logs:

```kusto
// AzureDiagnostics — AzureFirewallNetworkRule
AzureDiagnostics
| where Category == "AzureFirewallNetworkRule"
| where TimeGenerated > ago(15m)
| project TimeGenerated, msg_s
| order by TimeGenerated desc
```

Confirm:
- Allowed flows reference `RC: allow-fabric-sql` / `allow-powerbi` etc.
- Denied flows (set up an `nslookup malicious.example.com` for proof) reference
  the implicit deny.

## 6. Negative test

Temporarily remove the on-prem conditional forwarder for
`privatelink.analysis.windows.net` and repeat `Test-NetConnection`. You should
see public Microsoft IPs and — if **Block Public Internet Access** is enabled
in Fabric — the connection should fail at the Fabric service. Re-add the
forwarder when done.

## 7. Tear-down

```pwsh
terraform destroy
```

Before destroy, **detach the workspace from the capacity** in the Fabric portal,
otherwise the capacity delete will fail or leave the workspace orphaned. Also
remove the conditional forwarders from on-prem DNS if you don't intend to
redeploy.
