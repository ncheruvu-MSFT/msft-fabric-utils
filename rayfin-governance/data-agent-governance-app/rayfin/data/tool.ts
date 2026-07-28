import { entity, uuid, text, boolean, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims) => claims.role.eq('agent-admin'),
})
export class Tool {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ max: 100 }) kind!: string;
  @text({ max: 400 }) endpoint!: string;
  @text({ max: 100 }) authMode!: string;
  @boolean() isSensitive!: boolean;
  @text({ optional: true, max: 4000 }) allowedDomainsCsv?: string;
}
