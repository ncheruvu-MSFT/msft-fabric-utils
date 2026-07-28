import { entity, uuid, text, boolean, date, authenticated } from '@microsoft/rayfin-core';

// Mirrors the `domains:` block in
// fabric-sdlc-governance/contracts/governance/domains.yml
@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims) => claims.role.eq('governance-admin'),
})
export class Domain {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ optional: true, max: 1000 }) description?: string;
  @text({ max: 100 }) type!: string;
  @text({ max: 100 }) envKey!: string;
  @text({ max: 100 }) status!: string;
  @text({ optional: true, max: 200 }) parentId?: string;
  @text({ optional: true, max: 200 }) fabricWorkspace?: string;
  @text({ optional: true, max: 200 }) purviewCollection?: string;
  @text({ max: 200 }) ownerEmail!: string;
  @boolean() isActive!: boolean;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
