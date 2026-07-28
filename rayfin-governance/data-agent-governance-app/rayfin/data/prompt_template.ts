import { entity, uuid, text, int, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update'], {
  policy: (claims, item) =>
    claims.role.eq('agent-author').or(claims.sub.eq(item.ownerSub)),
})
@authenticated(['delete'], {
  policy: (claims) => claims.role.eq('agent-admin'),
})
export class PromptTemplate {
  @uuid() id!: string;
  @text({ max: 200 }) agentId!: string;
  @text({ max: 200 }) name!: string;
  @int() version!: number;
  @text({ max: 4000 }) body!: string;
  @text({ max: 200 }) ownerSub!: string;
  @date() auditCreatedAt!: Date;
}
