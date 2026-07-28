import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create'])
@authenticated(['update', 'delete'], {
  policy: (claims, item) =>
    claims.role.eq('lineage-admin').or(claims.sub.eq(item.harvestedBySub)),
})
export class LineageEdge {
  @uuid() id!: string;
  @text({ max: 400 }) sourceQname!: string;
  @text({ max: 100 }) sourceType!: string;
  @text({ max: 400 }) targetQname!: string;
  @text({ max: 100 }) targetType!: string;
  @text({ max: 200 }) processName!: string;
  @text({ max: 100 }) processType!: string;
  @text({ max: 400 }) artifactRef!: string;
  @text({ max: 200 }) harvestedBySub!: string;
  @text({ optional: true, max: 4000 }) columnsJson?: string;
  @text({ optional: true, max: 4000 }) extraJson?: string;
  @date() harvestedAt!: Date;
}
