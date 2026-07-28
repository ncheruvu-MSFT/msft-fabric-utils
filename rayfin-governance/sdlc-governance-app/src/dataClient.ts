// Thin data client for the sdlc-governance-app frontend.
//
// In a deployed Fabric app the Rayfin backend exposes a GraphQL endpoint at
// `${VITE_RAYFIN_API_URL}/api/graphql`. This client posts GraphQL there when an
// API URL is configured, and otherwise returns local seed data so the UI builds
// and runs without the preview backend.
//
// The generated `@microsoft/rayfin-client` (preview) can replace this module
// once the package is available in your registry — the entity contract lives in
// `rayfin/data/*.ts`.

export type AttestationResult = 'Pass' | 'Fail' | 'Warning';

export interface AttestationRun {
  id: string;
  workspaceId: string;
  policyName: string;
  result: AttestationResult;
  pipelineRunUrl: string;
  commitSha: string;
  submittedBy: string;
  runAt: string;
}

const API_URL = import.meta.env.VITE_RAYFIN_API_URL;

const SEED: AttestationRun[] = [
  {
    id: '1',
    workspaceId: 'Contoso-Retail-Sales-prod',
    policyName: 'domain-ownership-required',
    result: 'Pass',
    pipelineRunUrl: 'https://dev.azure.com/contoso/_build/results?buildId=4821',
    commitSha: 'a1b2c3d',
    submittedBy: 'pipeline@contoso.com',
    runAt: '2026-06-10T08:02:00Z',
  },
  {
    id: '2',
    workspaceId: 'Contoso-Retail-Catalog-prod',
    policyName: 'cde-classification-coverage',
    result: 'Warning',
    pipelineRunUrl: 'https://dev.azure.com/contoso/_build/results?buildId=4822',
    commitSha: 'e4f5a6b',
    submittedBy: 'pipeline@contoso.com',
    runAt: '2026-06-10T08:05:00Z',
  },
  {
    id: '3',
    workspaceId: 'Contoso-HR-Compensation-prod',
    policyName: 'sensitivity-label-required',
    result: 'Fail',
    pipelineRunUrl: 'https://dev.azure.com/contoso/_build/results?buildId=4823',
    commitSha: 'c7d8e9f',
    submittedBy: 'pipeline@contoso.com',
    runAt: '2026-06-10T08:09:00Z',
  },
  {
    id: '4',
    workspaceId: 'Contoso-Marketing-Telemetry-test',
    policyName: 'retention-policy-attached',
    result: 'Pass',
    pipelineRunUrl: 'https://dev.azure.com/contoso/_build/results?buildId=4810',
    commitSha: 'b0c1d2e',
    submittedBy: 'pipeline@contoso.com',
    runAt: '2026-06-09T21:44:00Z',
  },
  {
    id: '5',
    workspaceId: 'Contoso-Retail-Sales-dev',
    policyName: 'domain-ownership-required',
    result: 'Pass',
    pipelineRunUrl: 'https://dev.azure.com/contoso/_build/results?buildId=4799',
    commitSha: 'f3a4b5c',
    submittedBy: 'pipeline@contoso.com',
    runAt: '2026-06-09T15:12:00Z',
  },
];

const LIST_QUERY = `
  query AttestationRuns {
    attestationRuns {
      id
      workspaceId
      policyName
      result
      pipelineRunUrl
      commitSha
      submittedBy
      runAt
    }
  }
`;

export interface DataClientResult {
  runs: AttestationRun[];
  source: 'backend' | 'seed';
}

export async function listAttestationRuns(): Promise<DataClientResult> {
  if (!API_URL) {
    return { runs: SEED, source: 'seed' };
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
      data?: { attestationRuns?: AttestationRun[] };
      errors?: unknown;
    };
    if (json.errors) {
      throw new Error(JSON.stringify(json.errors));
    }
    const runs = json.data?.attestationRuns ?? [];
    if (runs.length === 0) {
      return { runs: SEED, source: 'seed' };
    }
    return { runs, source: 'backend' };
  } catch {
    return { runs: SEED, source: 'seed' };
  }
}
