import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create'])
@authenticated(['update', 'delete'], {
  policy: (claims, item) =>
    claims.role.eq('steward').or(claims.sub.eq(item.submittedBySub)),
})
export class Term {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ max: 4000 }) definition!: string;
  @text({ max: 200 }) domainId!: string;
  @text({ max: 100 }) status!: string;
  @text({ max: 200 }) submittedBySub!: string;
  @text({ optional: true, max: 200 }) approvedBySub?: string;
  @text({ optional: true, max: 400 }) purviewQualifiedName?: string;
  @date() auditCreatedAt!: Date;
  @date({ optional: true }) auditUpdatedAt?: Date;
}
