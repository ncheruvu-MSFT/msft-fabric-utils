import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create'], {
  policy: (claims) =>
    claims.role.eq('red-team').or(claims.role.eq('agent-admin')),
})
@authenticated(['update'], {
  policy: (claims, item) =>
    claims.role.eq('agent-admin').or(claims.sub.eq(item.assigneeSub)),
})
@authenticated(['delete'], {
  policy: (claims) => claims.role.eq('agent-admin'),
})
export class RedTeamFinding {
  @uuid() id!: string;
  @text({ max: 200 }) agentId!: string;
  @text({ max: 100 }) severity!: string;
  @text({ max: 100 }) category!: string;
  @text({ max: 200 }) title!: string;
  @text({ max: 4000 }) description!: string;
  @text({ max: 100 }) status!: string;
  @text({ max: 200 }) reporterSub!: string;
  @text({ optional: true, max: 200 }) assigneeSub?: string;
  @text({ optional: true, max: 4000 }) mitigationNote?: string;
  @date() reportedAt!: Date;
  @date({ optional: true }) resolvedAt?: Date;
}
