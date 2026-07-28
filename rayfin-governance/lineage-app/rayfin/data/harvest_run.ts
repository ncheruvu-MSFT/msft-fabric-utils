import { entity, uuid, text, int, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create'])
@authenticated(['update', 'delete'], {
  policy: (claims, item) =>
    claims.role.eq('lineage-admin').or(claims.sub.eq(item.triggeredBySub)),
})
export class HarvestRun {
  @uuid() id!: string;
  @text({ max: 100 }) harvesterType!: string;
  @text({ max: 100 }) status!: string;
  @int() edgeCount!: number;
  @text({ max: 200 }) triggeredBySub!: string;
  @text({ optional: true, max: 4000 }) errorMessage?: string;
  @date() startedAt!: Date;
  @date({ optional: true }) finishedAt?: Date;
}
