// Rayfin SDK client singleton.
//
// Replaces the previous hand-built `fetch('/api/graphql')` calls with the
// official `@microsoft/rayfin-client` SDK (the data-access pattern the Rayfin
// skill mandates: always go through `client.data.<Entity>`, never raw fetch).
//
// The client is configured from Vite env vars that `rayfin up` / deployment
// can inject. When the publishable key is absent the app runs in seed mode and
// `getRayfinClient()` returns null so callers fall back to local examples.
import { RayfinClient } from '@microsoft/rayfin-client';

/**
 * Row shapes of the backend entities (mirrors `rayfin/data/*.ts`). Declared
 * locally so the browser bundle never imports the decorator-based entity
 * classes — those compile under the Rayfin CLI, not Vite.
 */
export interface TermRow {
  id: string;
  name: string;
  definition: string;
  domainId: string;
  status: string;
  submittedBySub: string;
  approvedBySub?: string;
  purviewQualifiedName?: string;
  auditCreatedAt: string;
  auditUpdatedAt?: string;
}

export interface DomainRow {
  id: string;
  name: string;
  description?: string;
  parentId?: string;
  ownerSub: string;
  isActive: boolean;
  auditCreatedAt: string;
  auditUpdatedAt?: string;
}

export interface ApprovalRequestRow {
  id: string;
  targetType: string;
  targetId: string;
  workflowName: string;
  status: string;
  requesterSub: string;
  assigneeSub?: string;
  decisionNote?: string;
  auditCreatedAt: string;
  decidedAt?: string;
}

export interface GlossarySchema {
  Term: TermRow;
  Domain: DomainRow;
  ApprovalRequest: ApprovalRequestRow;
}

const BASE_URL = import.meta.env.VITE_RAYFIN_API_URL;
const PUBLISHABLE_KEY = import.meta.env.VITE_RAYFIN_PUBLISHABLE_KEY;
const ITEM_ID = import.meta.env.VITE_FABRIC_ITEM_ID;

let client: RayfinClient<GlossarySchema> | null = null;
let initialized = false;

/**
 * Lazily create the singleton RayfinClient. Returns null when no backend is
 * configured (publishable key / base URL missing) so callers can fall back to
 * seed data.
 */
export function getRayfinClient(): RayfinClient<GlossarySchema> | null {
  if (initialized) {
    return client;
  }
  initialized = true;

  if (!BASE_URL || !PUBLISHABLE_KEY) {
    client = null;
    return null;
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Origin: window.location.origin,
  };
  // Managed-hosting moniker, set on the Fabric item by `rayfin up`.
  if (ITEM_ID) {
    headers['x-ms-workload-resource-moniker'] = ITEM_ID;
  }

  client = new RayfinClient<GlossarySchema>({
    baseUrl: BASE_URL,
    publishableKey: PUBLISHABLE_KEY,
    useProxy: false,
    headers,
    authStorage: true,
  });
  return client;
}

/** True when a backend is configured (client could be created). */
export function isBackendConfigured(): boolean {
  return Boolean(BASE_URL && PUBLISHABLE_KEY);
}
