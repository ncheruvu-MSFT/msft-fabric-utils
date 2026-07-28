import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims) => claims.role.eq('lineage-admin'),
})
export class DataAsset {
  @uuid() id!: string;
  @text({ max: 400 }) qualifiedName!: string;
  @text({ max: 100 }) assetType!: string;
  @text({ max: 200 }) displayName!: string;
  @text({ optional: true, max: 200 }) domainId?: string;
  @text({ optional: true, max: 200 }) purviewGuid?: string;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
