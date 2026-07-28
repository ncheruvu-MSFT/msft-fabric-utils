import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';

// One row per attestation run posted by an ADO pipeline against a workspace.
@entity()
@authenticated(['read'])
@authenticated(['create'], {
  policy: (claims) =>
    claims.role.eq('pipeline').or(claims.role.eq('governance-admin')),
})
@authenticated(['update', 'delete'], {
  policy: (claims) => claims.role.eq('governance-admin'),
})
export class AttestationRun {
  @uuid() id!: string;
  @text({ max: 200 }) workspaceId!: string;
  @text({ max: 200 }) policyName!: string;
  @text({ max: 100 }) result!: string;
  @text({ max: 400 }) pipelineRunUrl!: string;
  @text({ max: 100 }) commitSha!: string;
  @text({ max: 200 }) submittedBySub!: string;
  @text({ optional: true, max: 4000 }) findingsJson?: string;
  @date() runAt!: Date;
}
