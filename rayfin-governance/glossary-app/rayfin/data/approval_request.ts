import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['create', 'read'])
@authenticated(['update'], {
  policy: (claims, item) =>
    claims.role.eq('steward').or(claims.sub.eq(item.assigneeSub)),
})
export class ApprovalRequest {
  @uuid() id!: string;
  @text({ max: 100 }) targetType!: string;
  @text({ max: 200 }) targetId!: string;
  @text({ max: 200 }) workflowName!: string;
  @text({ max: 100 }) status!: string;
  @text({ max: 200 }) requesterSub!: string;
  @text({ optional: true, max: 200 }) assigneeSub?: string;
  @text({ optional: true, max: 4000 }) decisionNote?: string;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) decidedAt?: Date;
}
