import { entity, uuid, text, authenticated } from '@microsoft/rayfin-core';

// Mirrors `critical_data_elements:` in
// fabric-sdlc-governance/contracts/governance/critical_data_elements.yml
@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims) =>
    claims.role.eq('governance-admin').or(claims.role.eq('domain-steward')),
})
export class CriticalDataElement {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ max: 200 }) domainId!: string;
  @text({ max: 1000 }) description!: string;
  @text({ max: 100 }) dataType!: string;
  @text({ max: 100 }) sensitivity!: string;
  @text({ optional: true, max: 4000 }) columnsJson?: string;
  @text({ optional: true, max: 4000 }) relatedTermsCsv?: string;
  @text({ max: 100 }) envKey!: string;
}
