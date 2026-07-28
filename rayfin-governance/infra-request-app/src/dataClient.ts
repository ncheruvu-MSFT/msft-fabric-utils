// Thin data client for the infra-request-app frontend.
//
// In a deployed Fabric app the Rayfin backend exposes a GraphQL endpoint at
// `${VITE_RAYFIN_API_URL}/api/graphql`. This client posts GraphQL there when an
// API URL is configured, and otherwise keeps an in-memory list seeded with
// examples so the form and grid work without the preview backend.
//
// The generated `@microsoft/rayfin-client` (preview) can replace this module
// once the package is available in your registry — the entity contract lives in
// `rayfin/data/infra_request.ts`.

export type RequestType = 'Capacity' | 'Workspace';
export type RequestStatus =
  | 'Pending'
  | 'Approved'
  | 'Rejected'
  | 'Submitted'
  | 'Completed';

export interface InfraRequest {
  id: string;
  requestType: RequestType;
  displayName: string;
  environment: string;
  domain?: string;
  capacitySku?: string;
  region?: string;
  targetCapacity?: string;
  justification: string;
  costCenter?: string;
  status: RequestStatus;
  approverSub?: string;
  approvalNote?: string;
  githubIssueUrl?: string;
  githubIssueNumber?: number;
  ownerSub: string;
  auditCreatedBy: string;
  auditCreatedAt: string;
  auditUpdatedAt?: string;
}

// Fields the form collects. Owner/audit/status are stamped by the client.
export type NewInfraRequest = Pick<
  InfraRequest,
  | 'requestType'
  | 'displayName'
  | 'environment'
  | 'justification'
> &
  Partial<
    Pick<
      InfraRequest,
      | 'domain'
      | 'capacitySku'
      | 'region'
      | 'targetCapacity'
      | 'costCenter'
    >
  >;

const API_URL = import.meta.env.VITE_RAYFIN_API_URL;

const SEED: InfraRequest[] = [
  {
    id: '1',
    requestType: 'Capacity',
    displayName: 'Contoso-Analytics-prod',
    environment: 'prod',
    domain: 'retail-sales',
    capacitySku: 'F64',
    region: 'westus2',
    justification:
      'Net-new production capacity for the retail sales analytics domain.',
    costCenter: 'CC-4821',
    status: 'Pending',
    ownerSub: 'avery@contoso.com',
    auditCreatedBy: 'avery@contoso.com',
    auditCreatedAt: '2026-06-28T14:02:00Z',
  },
  {
    id: '2',
    requestType: 'Workspace',
    displayName: 'Contoso-Marketing-Telemetry-dev',
    environment: 'dev',
    domain: 'marketing',
    targetCapacity: 'Contoso-Shared-dev (F8)',
    justification:
      'Dev workspace for the marketing telemetry pipeline POC.',
    costCenter: 'CC-3310',
    status: 'Approved',
    approverSub: 'platform-lead@contoso.com',
    approvalNote: 'Approved against shared dev capacity.',
    ownerSub: 'jordan@contoso.com',
    auditCreatedBy: 'jordan@contoso.com',
    auditCreatedAt: '2026-06-27T09:15:00Z',
    auditUpdatedAt: '2026-06-27T16:40:00Z',
  },
  {
    id: '3',
    requestType: 'Workspace',
    displayName: 'Contoso-HR-Compensation-prod',
    environment: 'prod',
    domain: 'hr',
    targetCapacity: 'Contoso-HR-prod (F32)',
    justification: 'Production workspace for compensation reporting.',
    status: 'Submitted',
    approverSub: 'platform-lead@contoso.com',
    githubIssueUrl: 'https://github.com/contoso/fabric-infra/issues/142',
    githubIssueNumber: 142,
    ownerSub: 'sam@contoso.com',
    auditCreatedBy: 'sam@contoso.com',
    auditCreatedAt: '2026-06-25T11:00:00Z',
    auditUpdatedAt: '2026-06-26T08:05:00Z',
  },
];

// In-memory store used only in seed mode so the UI reflects submissions/approvals.
let seedStore: InfraRequest[] = [...SEED];

export interface ListResult {
  requests: InfraRequest[];
  source: 'backend' | 'seed';
}

const LIST_QUERY = `
  query InfraRequests {
    infraRequests {
      id
      requestType
      displayName
      environment
      domain
      capacitySku
      region
      targetCapacity
      justification
      costCenter
      status
      approverSub
      approvalNote
      githubIssueUrl
      githubIssueNumber
      ownerSub
      auditCreatedBy
      auditCreatedAt
      auditUpdatedAt
    }
  }
`;

const CREATE_MUTATION = `
  mutation CreateInfraRequest($item: CreateInfraRequestInput!) {
    createInfraRequest(item: $item) {
      id
    }
  }
`;

const UPDATE_MUTATION = `
  mutation UpdateInfraRequest($id: ID!, $item: UpdateInfraRequestInput!) {
    updateInfraRequest(id: $id, item: $item) {
      id
    }
  }
`;

async function gql<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_URL}/api/graphql`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`GraphQL ${res.status}: ${await res.text()}`);
  }
  const json = (await res.json()) as { data?: T; errors?: unknown };
  if (json.errors) {
    throw new Error(`GraphQL errors: ${JSON.stringify(json.errors)}`);
  }
  return json.data as T;
}

export async function listInfraRequests(): Promise<ListResult> {
  if (!API_URL) {
    return { requests: [...seedStore], source: 'seed' };
  }
  try {
    const data = await gql<{ infraRequests?: InfraRequest[] }>(LIST_QUERY);
    return { requests: data.infraRequests ?? [], source: 'backend' };
  } catch {
    // Fall back to seed so the grid stays populated when the backend is down.
    return { requests: [...seedStore], source: 'seed' };
  }
}

export async function createInfraRequest(
  input: NewInfraRequest,
  requesterSub: string,
): Promise<void> {
  const now = new Date().toISOString();
  if (!API_URL) {
    seedStore = [
      {
        ...input,
        id: crypto.randomUUID(),
        status: 'Pending',
        ownerSub: requesterSub,
        auditCreatedBy: requesterSub,
        auditCreatedAt: now,
      },
      ...seedStore,
    ];
    return;
  }
  await gql(CREATE_MUTATION, {
    item: {
      ...input,
      status: 'Pending',
      ownerSub: requesterSub,
      auditCreatedBy: requesterSub,
      auditCreatedAt: now,
    },
  });
}

export async function setRequestStatus(
  id: string,
  status: Extract<RequestStatus, 'Approved' | 'Rejected'>,
  approverSub: string,
  approvalNote?: string,
): Promise<void> {
  const now = new Date().toISOString();
  if (!API_URL) {
    seedStore = seedStore.map((r) =>
      r.id === id
        ? { ...r, status, approverSub, approvalNote, auditUpdatedAt: now }
        : r,
    );
    return;
  }
  await gql(UPDATE_MUTATION, {
    id,
    item: { status, approverSub, approvalNote, auditUpdatedAt: now },
  });
}
