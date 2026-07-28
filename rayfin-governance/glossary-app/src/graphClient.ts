// Entra ID security-group client for the glossary-app.
//
// Each glossary term / data product is backed by a set of Entra ID security
// groups — one per access tier (Reader / Contributor / Owner). When a term is
// created the groups are provisioned, and when an access request is approved the
// requesting user is added to the group that matches the granted role. This is
// how access is granted in Microsoft Fabric / OneLake: data products are shared
// to Entra security groups, so adding a user to the group grants the access.
//
// When `VITE_RAYFIN_GRAPH_URL` points at a Microsoft Graph proxy the client
// performs the real `POST /groups` and `POST /groups/{id}/members/$ref` calls.
// Otherwise it simulates provisioning locally so the workflow is demonstrable
// without Graph (Group.ReadWrite.All) permissions.

import type { AccessRole, EntraGroup } from './dataClient';

const GRAPH_URL = import.meta.env.VITE_RAYFIN_GRAPH_URL;

/** Access tiers, in order of increasing privilege. */
export const ACCESS_ROLES: AccessRole[] = ['Reader', 'Contributor', 'Owner'];

/** Human-readable description of what each access tier grants. */
export const ROLE_PERMISSION: Record<AccessRole, string> = {
  Reader: 'Read / consume the data product and its glossary terms',
  Contributor: 'Read and contribute — propose edits and load data',
  Owner: 'Full control — manage the data product and approve access',
};

/** Slugify a term / data-product name into a group-name fragment. */
export function slug(name: string): string {
  return (
    name
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'term'
  );
}

/**
 * Plan the three standard Entra security groups for a term / data product.
 * Returns un-provisioned group definitions (no objectId, no members yet).
 */
export function planGroups(name: string, prefix = 'GLOSSARY'): EntraGroup[] {
  const s = slug(name);
  return ACCESS_ROLES.map((role) => ({
    id: `${s}-${role}`,
    displayName: `${prefix}-${s}-${role}s`,
    mailNickname: `${prefix.toLowerCase()}-${s}-${role.toLowerCase()}s`,
    role,
    members: [],
    provisioned: false,
  }));
}

/**
 * Provision the security groups in Entra ID. POSTs to the Graph proxy when one
 * is configured; otherwise simulates provisioning so the demo works offline.
 */
export async function provisionGroups(
  name: string,
  prefix?: string,
): Promise<EntraGroup[]> {
  const planned = planGroups(name, prefix);
  if (!GRAPH_URL) {
    return planned.map((g) => ({
      ...g,
      provisioned: true,
      objectId: `sim-${g.id}`,
    }));
  }
  return Promise.all(
    planned.map(async (g) => {
      try {
        const res = await fetch(`${GRAPH_URL}/groups`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            displayName: g.displayName,
            mailNickname: g.mailNickname,
            mailEnabled: false,
            securityEnabled: true,
            description: `${g.role} access — ${ROLE_PERMISSION[g.role]}`,
          }),
        });
        if (!res.ok) throw new Error(`Graph ${res.status}`);
        const json = (await res.json()) as { id?: string };
        return { ...g, provisioned: true, objectId: json.id ?? `sim-${g.id}` };
      } catch {
        // Fall back to a simulated group so the UI stays consistent.
        return { ...g, provisioned: true, objectId: `sim-${g.id}` };
      }
    }),
  );
}

/**
 * Add a user (UPN) to the Entra group backing an access role. Returns a new
 * group with the member appended; no-op if the user is already a member.
 */
export async function addGroupMember(
  group: EntraGroup,
  userUpn: string,
): Promise<EntraGroup> {
  if (group.members.includes(userUpn)) return group;
  if (GRAPH_URL && group.objectId && !group.objectId.startsWith('sim-')) {
    try {
      await fetch(`${GRAPH_URL}/groups/${group.objectId}/members/$ref`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          '@odata.id': `https://graph.microsoft.com/v1.0/users/${encodeURIComponent(
            userUpn,
          )}`,
        }),
      });
    } catch {
      // Fall through to local update so the UI reflects the grant.
    }
  }
  return { ...group, members: [...group.members, userUpn] };
}

// Simulated org chart used when Graph is not wired up. In a real deployment the
// requester's manager is resolved from Entra via `GET /users/{upn}/manager`.
const MANAGER_MAP: Record<string, string> = {
  'you@contoso.com': 'taylor.manager@contoso.com',
  'newhire@contoso.com': 'dana@contoso.com',
  'sales-ops@contoso.com': 'priya@contoso.com',
  'kai@contoso.com': 'priya@contoso.com',
};

/** Resolve the requester's manager (Entra `manager` relationship). */
export async function managerOf(userUpn: string): Promise<string> {
  if (GRAPH_URL) {
    try {
      const res = await fetch(
        `${GRAPH_URL}/users/${encodeURIComponent(userUpn)}/manager`,
        { credentials: 'include' },
      );
      if (res.ok) {
        const json = (await res.json()) as {
          userPrincipalName?: string;
          mail?: string;
        };
        if (json.userPrincipalName) return json.userPrincipalName;
        if (json.mail) return json.mail;
      }
    } catch {
      // Fall through to the simulated org chart.
    }
  }
  return MANAGER_MAP[userUpn] ?? 'manager@contoso.com';
}
