import { entity, uuid, text, date, boolean, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims, item) => claims.role.eq('domain-admin').or(claims.sub.eq(item.ownerSub)),
})
export class Domain {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ optional: true, max: 1000 }) description?: string;
  @text({ optional: true, max: 200 }) parentId?: string;
  @text({ max: 200 }) ownerSub!: string;
  @boolean() isActive!: boolean;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
