# Fabric Identity Perimeter — recommended default

> Companion to [`../fabric-private-terraform/`](../fabric-private-terraform/). That directory shows you **how** to go fully private with VNet + tenant Private Link + MPEs. This directory exists to explain **why most teams shouldn't**, and how an **identity-centric perimeter** (Entra ID Conditional Access, Continuous Access Evaluation, Workspace Identities, Trusted Workspace Access) gives you most of the same security posture with a fraction of the operational and feature cost.

Source of the position: ["Microsoft Fabric: Public vs. Private Endpoints — What You Need to Know"](https://medium.com/@rjtimbers00/microsoft-fabric-public-vs-private-endpoints-what-you-need-to-know-16a58ccd96ac) (Richard Timbers, April 2026) — cross-referenced against Microsoft Learn docs on [Private Links](https://learn.microsoft.com/fabric/security/security-private-links-overview), [Managed Private Endpoints](https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-overview), [Conditional Access for Fabric](https://learn.microsoft.com/fabric/security/security-conditional-access), [Workspace Identity](https://learn.microsoft.com/fabric/security/workspace-identity), and [Trusted Workspace Access](https://learn.microsoft.com/fabric/security/security-trusted-workspace-access).

---

## TL;DR

| Posture | When to choose | Cost of being wrong |
|---|---|---|
| **Default (public + Entra hardening)** | Most enterprise workloads. Regulated industries that can show compensating controls. | Low. You preserve every Fabric feature. |
| **Hybrid (public Fabric + Managed Private Endpoints to private sources)** | Source data is in private-only Storage / SQL / Cosmos and you need notebooks / pipelines / Spark to reach it. | Medium. Requires F64+, loses Spark Starter Pools, OneLake shortcuts to ADLS via MPE unsupported. |
| **Full private (Private Link inbound + Block Public Internet Access + MPEs)** | Hard regulatory requirement: PCI-DSS / HIPAA / ISO 27001 with a documented "no public Internet" rule, or a contract that explicitly forbids public service endpoints. | High. Disables Copilot sidecar, Database Mirroring (most types), Visual Query in Warehouse, Publish to Web, email subscriptions, several MIP scenarios, Trial capacities, and forces F64+ for outbound. |

The recommendation: **default to the identity perimeter**. Only step up when a specific control objective truly requires network-layer isolation.

---

## Why "public" is not "exposed"

Every request to Fabric is authenticated through Entra ID. That means the controls Entra ships with — Conditional Access, CAE, named locations, device compliance, sign-in risk — apply to Fabric for free. Those controls are policy-evaluated **on every token issuance and (with CAE) on every critical event during the session**.

A correctly-configured identity perimeter answers the same questions a network perimeter answers, just differently:

| Question | Network perimeter | Identity perimeter |
|---|---|---|
| Can this request even reach the service? | "Only from these IPs / VNets." | "Only from these device states + named locations + sign-in risk = Low." |
| Can the principal still act if compromised? | Requires firewall/NSG change. | CAE revokes within minutes of sign-out / password change / risk elevation. |
| Can data exfiltrate to a third party? | "All outbound through firewall." | Workspace Identity + Trusted Workspace Access on storage; MIP labels on artifacts. |
| Audit trail? | Firewall logs (NW45, NSG flow). | SigninLogs, AuditLogs, ServicePrincipalSignIns, FabricUserActivity — all in M365 unified audit + Log Analytics. |

---

## What you actually lose by going full-private

Take this seriously before flipping the **Block Public Internet Access** tenant toggle. (Source: article + Microsoft Learn.)

| Feature | Status under Block Public Internet Access |
|---|---|
| **Copilot sidecar chat** | Disabled. Inline completion still works. |
| **Database Mirroring** (most types) | Active mirrored DBs are paused, can't restart. Limited exceptions: Cosmos DB, SQL MI, SQL Server 2025. |
| **Visual Query in Warehouse** | Not supported. |
| **Publish to Web** | Blocked. |
| **Email subscriptions** | Blocked. |
| **Semantic models referencing other semantic models / Dataflow Gen1** | Connections fail. |
| **MIP sensitivity labels in PBI Desktop on isolated networks** | Labels stop working; `.pbix` decryption fails. |
| **Trial capacities** | Unavailable. |
| **Spark Starter Pools** (workspace with managed VNet for MPE) | Disabled. Cold starts ~2-3 min. |
| **OneLake Shortcuts via MPE for ADLS Gen2 / Blob** | Not supported. Use direct connections. |
| **Eventstream MPEs** | Limited to Azure Event Hubs and IoT Hub. |
| **FQDN-based MPEs** | UI not supported — REST API only. |
| **F2 / F4 / F8 / F16 / F32 capacities** | MPEs require F64+. |
| **MPE recreate** | 15-minute cooldown after delete. |

If any of those are core to your workload, the **identity perimeter is the only reasonable answer right now**.

---

## The identity-perimeter control set

The diagram in [`diagrams/identity-vs-network-perimeter.drawio`](diagrams/identity-vs-network-perimeter.drawio) (open in [draw.io](https://app.diagrams.net) or VS Code Drawio extension; two tabs) shows these visually. Walkthrough:

### 1. Conditional Access (the front door)

Requires **Entra ID P1**. Apply policies scoped to the *Microsoft Fabric* and *Power BI Service* cloud apps:

- Require **MFA** for all human sign-ins.
- Require **device compliance** or **hybrid Entra-joined** device.
- Restrict sign-in to **named locations** (corporate egress IPs, allowlisted countries).
- Block **legacy authentication** (no Basic auth, no IMAP).
- Block **high sign-in risk** outright; require step-up for medium risk.
- For automation: a separate policy scoped to **workload identities** (service principals) that enforces certificate-based credentials or restricts to specific source IPs.

Sample policy export in [`samples/conditional-access-policy-fabric.json`](samples/conditional-access-policy-fabric.json). Deploy via Microsoft Graph (`POST /identity/conditionalAccess/policies`) or your CA-as-code pipeline.

### 2. Continuous Access Evaluation (the keep-out-during-session control)

CAE is the answer to *"my token is still valid even though the user was disabled."*

- Enabled by default on tenants with supported workloads (Fabric / Power BI is one).
- Token lifetimes extend to **up to 28 hours** in CAE-aware sessions — longer is *more* secure here, because revocation is event-driven, not timeout-driven.
- Critical events that revoke a session within minutes: user account disable, password change, MFA registration, CA policy change, risky-user marker, IP change out of a named location, tenant-wide sign-out.
- Verify a Fabric session is CAE-aware: in `SigninLogs`, look for `IsCaeToken == true` and `SessionLifetimePolicies` populated.

Sample KQL in [`samples/kusto-cae-coverage.kql`](samples/kusto-cae-coverage.kql) — shows the share of Fabric / Power BI sign-ins that are CAE-protected vs not. Anything < 95% is worth investigating.

### 3. Workspace Identity (the no-secrets-on-disk pattern)

Fabric **Workspace Identity** is a system-managed Entra service principal per workspace. Pipelines and Spark jobs running inside the workspace authenticate as it.

- No client secrets / certs to rotate.
- Used for **Trusted Workspace Access** (below).
- One gotcha: if you have a CA policy scoped to *All service principals*, exclude the Fabric workspace identity service principals (`appId 871c010f-5e61-4fb1-83ac-98610a7e9110` and friends) or pipelines will fail.

### 4. Trusted Workspace Access (the network-isolation-without-Private-Link pattern)

On Storage accounts that hold your data: enable **Trusted services** + scope to the **Workspace Identity** of the specific Fabric workspace.

- Storage stays `publicNetworkAccess = Disabled` for *general* public traffic.
- Fabric workspaces you trust still reach it, authenticated as their workspace identity.
- Equivalent network outcome to an MPE for the OneLake shortcut / lakehouse load case — but doesn't require F64, doesn't kill Spark Starter Pools, and works for OneLake shortcuts (which MPE-to-ADLS still doesn't).

Sample script in [`samples/Enable-TrustedWorkspaceAccess.ps1`](samples/Enable-TrustedWorkspaceAccess.ps1).

### 5. Sensitivity labels + DLP for Power BI

MIP + DLP for Power BI continue to work on the public endpoint. Several of those scenarios *break* under Block Public Internet Access. Lean on them harder here.

### 6. Capacity-level governance

- Capacity admins, workspace roles, item permissions → enforce **least privilege via Entra groups**.
- Diagnostic settings → ship `FabricUserActivity`, `FabricGenericActivity`, Power BI audit to Log Analytics; build alerts on unusual sign-in geography or token replay patterns.

---

## Decision tree

```
Are you contractually / regulatorily required to disable public Internet
to the Fabric service?
│
├─ YES ──► Full-private: see ../fabric-private-terraform/. Build a feature
│         dependency map FIRST. Plan around Copilot / mirroring / etc.
│         Budget for F64+. Expect 2-3 month bring-up.
│
└─ NO ───► Do you have private-only data sources that Fabric must reach?
           │
           ├─ YES ──► Hybrid: public Fabric + MPE just for those sources.
           │         Requires F64+. See ../fabric-private-terraform/docs/managed-private-endpoints.md.
           │
           └─ NO ───► Identity perimeter (this directory). F2 works.
                     Implement CA + CAE + Workspace Identity + Trusted
                     Workspace Access + MIP. Keep every Fabric feature.
```

---

## Layout

```
fabric-identity-perimeter/
├── README.md                                       # this file
├── diagrams/
│   └── identity-vs-network-perimeter.drawio       # two tabs (private | identity)
└── samples/
    ├── conditional-access-policy-fabric.json       # CA policy for Fabric cloud app
    ├── Enable-TrustedWorkspaceAccess.ps1           # storage account + workspace identity
    └── kusto-cae-coverage.kql                      # measure CAE coverage of Fabric sign-ins
```

## References

- [Microsoft Fabric: Public vs. Private Endpoints — What You Need to Know (Medium)](https://medium.com/@rjtimbers00/microsoft-fabric-public-vs-private-endpoints-what-you-need-to-know-16a58ccd96ac)
- [Conditional Access in Microsoft Fabric](https://learn.microsoft.com/fabric/security/security-conditional-access)
- [Continuous Access Evaluation in Microsoft Entra](https://learn.microsoft.com/entra/identity/conditional-access/concept-continuous-access-evaluation)
- [Workspace Identity in Microsoft Fabric](https://learn.microsoft.com/fabric/security/workspace-identity)
- [Trusted Workspace Access for Fabric](https://learn.microsoft.com/fabric/security/security-trusted-workspace-access)
- [Private links for Fabric tenants](https://learn.microsoft.com/fabric/security/security-private-links-overview)
- [Managed private endpoints in Microsoft Fabric](https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-overview)
- [Sensitivity labels in Power BI](https://learn.microsoft.com/power-bi/enterprise/service-security-sensitivity-label-overview)
