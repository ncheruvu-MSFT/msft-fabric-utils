// Fabric SSO authentication service.
//
// Wraps `@microsoft/rayfin-auth-provider-fabric` to sign the user in with
// their Fabric (Entra ID) identity — the only auth method deployed Fabric apps
// support. Email/password remains a local-dev concern and is not used here.
//
// Usage:
//   - call `initEmbeddedSession()` once on app load (safe, no popup) to pick up
//     an existing session when the app is embedded in the Fabric Portal iframe.
//   - call `signInWithFabric()` from a button click (user gesture) to open the
//     Fabric broker tab when no session exists.
import {
  ensureSignedInWithFabric,
  initEmbeddedAuth,
  type FabricAuthOptions,
} from '@microsoft/rayfin-auth-provider-fabric';

import { getRayfinClient } from './rayfinClient';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

const WORKSPACE_ID = import.meta.env.VITE_FABRIC_WORKSPACE_ID;
const ITEM_ID = import.meta.env.VITE_FABRIC_ITEM_ID;
const FABRIC_PORTAL_URL =
  import.meta.env.VITE_FABRIC_PORTAL_URL ?? 'https://app.fabric.microsoft.com';

/** True when the env carries the Fabric identifiers needed for SSO. */
export function isFabricAuthConfigured(): boolean {
  return Boolean(WORKSPACE_ID && ITEM_ID && getRayfinClient());
}

function options(): FabricAuthOptions {
  return {
    workspaceId: WORKSPACE_ID as string,
    projectId: ITEM_ID as string,
    fabricPortalUrl: FABRIC_PORTAL_URL,
    returnOrigin: window.location.origin,
  };
}

function toUser(user: { id: string; email: string } | null): AuthUser | null {
  if (!user) return null;
  return {
    id: user.id,
    email: user.email,
    name: user.email.split('@')[0],
  };
}

/**
 * Resume an embedded Fabric session on load (no popup). Returns the signed-in
 * user, or null when not embedded / not configured.
 */
export async function initEmbeddedSession(): Promise<AuthUser | null> {
  const client = getRayfinClient();
  if (!client || !WORKSPACE_ID || !ITEM_ID) return null;
  try {
    const session = await initEmbeddedAuth(client.auth, options());
    if (!session?.isAuthenticated) return null;
    return toUser(session.user);
  } catch {
    return null;
  }
}

/**
 * Sign in with Fabric (Entra ID). Must be called from a user-gesture handler
 * because it may open the Fabric broker in a new tab. Throws on failure.
 */
export async function signInWithFabric(): Promise<AuthUser> {
  const client = getRayfinClient();
  if (!client || !WORKSPACE_ID || !ITEM_ID) {
    throw new Error('Fabric authentication is not configured for this app.');
  }
  const session = await ensureSignedInWithFabric(client.auth, options());
  const user = toUser(session.user);
  if (!session.isAuthenticated || !user) {
    throw new Error('Fabric sign-in completed but no session was established.');
  }
  return user;
}

/** Sign the current user out of the Rayfin session. */
export async function signOut(): Promise<void> {
  const client = getRayfinClient();
  if (!client) return;
  await client.auth.signOut();
}

/** Current user from an existing session, or null. */
export function currentUser(): AuthUser | null {
  const client = getRayfinClient();
  if (!client) return null;
  const session = client.auth.getSession();
  return session.isAuthenticated ? toUser(session.user) : null;
}
