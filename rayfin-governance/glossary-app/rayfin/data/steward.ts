import { entity, uuid, text, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims) => claims.role.eq('domain-admin'),
})
export class Steward {
  @uuid() id!: string;
  @text({ max: 200 }) domainId!: string;
  @text({ max: 200 }) userSub!: string;
  @text({ max: 200 }) userEmail!: string;
  @text({ max: 100 }) role!: string;
}
