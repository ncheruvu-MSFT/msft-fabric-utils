import { entity, uuid, text, boolean, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update'], {
  policy: (claims, item) =>
    claims.role.eq('agent-author').or(claims.sub.eq(item.ownerSub)),
})
@authenticated(['delete'], {
  policy: (claims) => claims.role.eq('agent-admin'),
})
export class Agent {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ max: 4000 }) description!: string;
  @text({ max: 200 }) domainId!: string;
  @text({ max: 200 }) ownerSub!: string;
  @text({ max: 100 }) status!: string;
  @text({ max: 200 }) modelDeployment!: string;
  @boolean() requiresHumanApproval!: boolean;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
