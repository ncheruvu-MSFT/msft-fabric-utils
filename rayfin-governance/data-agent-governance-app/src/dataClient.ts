// Thin data client for the data-agent-governance-app frontend.
//
// In a deployed Fabric app the Rayfin backend exposes a GraphQL endpoint at
// `${VITE_RAYFIN_API_URL}/api/graphql`. This client posts GraphQL there when an
// API URL is configured, and otherwise returns local seed data so the UI builds
// and runs without the preview backend.
//
// The generated `@microsoft/rayfin-client` (preview) can replace this module
// once the package is available in your registry — the entity contract lives in
// `rayfin/data/*.ts`.

export type AgentStatus = 'Draft' | 'In review' | 'Approved' | 'Suspended';

export interface Agent {
  id: string;
  name: string;
  domain: string;
  status: AgentStatus;
  modelDeployment: string;
  requiresHumanApproval: boolean;
  owner: string;
  updatedAt: string;
}

const API_URL = import.meta.env.VITE_RAYFIN_API_URL;

const SEED: Agent[] = [
  {
    id: '1',
    name: 'Sales Insights Copilot',
    domain: 'Sales',
    status: 'Approved',
    modelDeployment: 'gpt-4o-2026-05',
    requiresHumanApproval: false,
    owner: 'avery@contoso.com',
    updatedAt: '2026-06-07T11:20:00Z',
  },
  {
    id: '2',
    name: 'Revenue Forecast Agent',
    domain: 'Revenue',
    status: 'In review',
    modelDeployment: 'gpt-4o-2026-05',
    requiresHumanApproval: true,
    owner: 'jordan@contoso.com',
    updatedAt: '2026-06-09T16:48:00Z',
  },
  {
    id: '3',
    name: 'HR Policy Assistant',
    domain: 'Compensation',
    status: 'Suspended',
    modelDeployment: 'gpt-4o-mini-2026-04',
    requiresHumanApproval: true,
    owner: 'morgan@contoso.com',
    updatedAt: '2026-06-08T09:02:00Z',
  },
  {
    id: '4',
    name: 'Catalog Tagging Agent',
    domain: 'Catalog',
    status: 'Draft',
    modelDeployment: 'gpt-4o-mini-2026-04',
    requiresHumanApproval: false,
    owner: 'sam@contoso.com',
    updatedAt: '2026-06-10T07:31:00Z',
  },
  {
    id: '5',
    name: 'Telemetry Anomaly Triage',
    domain: 'Telemetry',
    status: 'Approved',
    modelDeployment: 'gpt-4o-2026-05',
    requiresHumanApproval: false,
    owner: 'sam@contoso.com',
    updatedAt: '2026-06-06T13:55:00Z',
  },
];

const LIST_QUERY = `
  query Agents {
    agents {
      id
      name
      domain
      status
      modelDeployment
      requiresHumanApproval
      owner
      updatedAt
    }
  }
`;

export interface DataClientResult {
  agents: Agent[];
  source: 'backend' | 'seed';
}

export async function listAgents(): Promise<DataClientResult> {
  if (!API_URL) {
    return { agents: SEED, source: 'seed' };
  }
  // Try the backend, but fall back to seed examples if it is unreachable so the
  // dashboard summary stays populated instead of showing a fetch error.
  try {
    const res = await fetch(`${API_URL}/api/graphql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: LIST_QUERY }),
      credentials: 'include',
    });
    if (!res.ok) {
      throw new Error(`GraphQL ${res.status}: ${await res.text()}`);
    }
    const json = (await res.json()) as {
      data?: { agents?: Agent[] };
      errors?: unknown;
    };
    if (json.errors) {
      throw new Error(JSON.stringify(json.errors));
    }
    const agents = json.data?.agents ?? [];
    if (agents.length === 0) {
      return { agents: SEED, source: 'seed' };
    }
    return { agents, source: 'backend' };
  } catch {
    return { agents: SEED, source: 'seed' };
  }
}
