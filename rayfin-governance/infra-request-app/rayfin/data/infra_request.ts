import { entity, uuid, text, int, date, authenticated } from '@microsoft/rayfin-core';

// One row per infrastructure request raised from the frontend form.
//
// Lifecycle: Pending -> Approved | Rejected -> Submitted (GitHub issue opened
// by the provisioning workflow) -> Completed (platform team closes the loop).
//
// The static frontend only ever CREATES requests and (for approvers) flips the
// status to Approved/Rejected. The GitHub Actions workflow authenticates as the
// `pipeline` role to stamp `githubIssueUrl` / `githubIssueNumber` / Submitted.
@entity()
@authenticated(['read'])
@authenticated(['create'])
@authenticated(['update'], {
  // Approvers/admins drive the approval gate; the automation role stamps the
  // GitHub fields; owners may still edit their own request while it is pending.
  policy: (claims, item) =>
    claims.role
      .eq('infra-approver')
      .or(claims.role.eq('governance-admin'))
      .or(claims.role.eq('pipeline'))
      .or(claims.sub.eq(item.ownerSub)),
})
@authenticated(['delete'], {
  policy: (claims) => claims.role.eq('governance-admin'),
})
export class InfraRequest {
  @uuid() id!: string;

  // 'Capacity' | 'Workspace'
  @text({ max: 40 }) requestType!: string;

  // Requested capacity / workspace name.
  @text({ max: 200 }) displayName!: string;

  // 'dev' | 'test' | 'prod'
  @text({ max: 40 }) environment!: string;

  // Governance domain the request belongs to (free-text natural key).
  @text({ optional: true, max: 200 }) domain?: string;

  // --- Capacity-only fields ---
  // F-SKU, e.g. F2 / F8 / F64.
  @text({ optional: true, max: 40 }) capacitySku?: string;
  // Azure region, e.g. westus2 / eastus2.
  @text({ optional: true, max: 80 }) region?: string;

  // --- Workspace-only field ---
  // Capacity (id or name) the workspace should be bound to.
  @text({ optional: true, max: 200 }) targetCapacity?: string;

  // Business context.
  @text({ max: 4000 }) justification!: string;
  @text({ optional: true, max: 100 }) costCenter?: string;

  // Workflow state: 'Pending' | 'Approved' | 'Rejected' | 'Submitted' | 'Completed'
  @text({ max: 40 }) status!: string;

  // --- Approval ---
  @text({ optional: true, max: 200 }) approverSub?: string;
  @text({ optional: true, max: 2000 }) approvalNote?: string;

  // --- GitHub linkage (stamped by the provisioning workflow) ---
  @text({ optional: true, max: 400 }) githubIssueUrl?: string;
  @int({ optional: true }) githubIssueNumber?: number;

  // --- Ownership + audit (Rayfin does not auto-stamp these) ---
  @text({ max: 200 }) ownerSub!: string;
  @text({ max: 200 }) auditCreatedBy!: string;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
