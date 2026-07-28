import { entity, uuid, text, boolean, authenticated } from '@microsoft/rayfin-core';

@entity()
@authenticated(['read'])
@authenticated(['create', 'update', 'delete'], {
  policy: (claims) => claims.role.eq('governance-admin'),
})
export class Workspace {
  @uuid() id!: string;
  @text({ max: 200 }) name!: string;
  @text({ max: 200 }) fabricWorkspaceId!: string;
  @text({ max: 100 }) envKey!: string;
  @text({ max: 200 }) domainId!: string;
  @boolean() isPrivateLink!: boolean;
  @text({ max: 200 }) ownerEmail!: string;
}
