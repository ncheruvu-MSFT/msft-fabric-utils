// Thin data client for the glossary-app frontend.
//
// Data access goes through the official `@microsoft/rayfin-client` SDK
// (`client.data.<Entity>`) — the pattern the Rayfin skill mandates over
// hand-built GraphQL/`fetch`. When no backend is configured (no publishable
// key) the client is null and we return local seed data so the UI still builds
// and runs. The entity contract lives in `rayfin/data/*.ts`.

import { planGroups } from './graphClient';
import { getRayfinClient, isBackendConfigured } from './rayfinClient';

export type TermStatus =
  | 'Draft'
  | 'Pending'
  | 'Approved'
  | 'Rejected'
  | 'Deprecated';

/** Atlas-style sensitivity / classification label. */
export type Classification =
  | 'Public'
  | 'Internal'
  | 'Confidential'
  | 'Highly Confidential'
  | 'PII';

/** One entry in a term's approval / lifecycle audit trail. */
export interface ApprovalEvent {
  action: 'Submitted' | 'Approved' | 'Rejected' | 'Deprecated' | 'Reopened';
  actor: string;
  note?: string;
  at: string;
}

/** Access tier that maps 1:1 to an Entra ID security group. */
export type AccessRole = 'Reader' | 'Contributor' | 'Owner';

/** An Entra ID security group backing one access tier of a term/data product. */
export interface EntraGroup {
  /** Stable local id (`<slug>-<role>`). */
  id: string;
  /** Entra group displayName, e.g. `GLOSSARY-net-revenue-Readers`. */
  displayName: string;
  /** Entra mailNickname. */
  mailNickname: string;
  role: AccessRole;
  /** Azure AD object id once provisioned via Graph (`sim-…` when simulated). */
  objectId?: string;
  /** Member UPNs currently in the group. */
  members: string[];
  /** Whether the group has been provisioned in Entra ID. */
  provisioned: boolean;
}

export type AccessRequestStatus = 'Pending' | 'Approved' | 'Rejected';

/** Who is responsible for approving a stage of an access-request workflow. */
export type ApproverType =
  | 'Manager'
  | 'Data owner'
  | 'Data steward'
  | 'Security admin'
  | 'Custom';

/** One configurable stage in an access-request approval workflow template. */
export interface ApprovalStage {
  id: string;
  name: string;
  approverType: ApproverType;
  /** Explicit approver UPN (used for Custom, or to override a resolved role). */
  approverUpn?: string;
  /** Service-level target for this stage, in hours. */
  slaHours?: number;
}

/**
 * An editable approval-workflow template. A data-map admin / data owner can
 * define the approval chain and bind it to one or more classifications.
 */
export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  /** Classifications this template applies to; '*' is the default fallback. */
  appliesTo: Classification[] | '*';
  stages: ApprovalStage[];
}

/** Recorded decision for one stage of an in-flight access request. */
export interface StageDecision {
  stageId: string;
  stageName: string;
  approverType: ApproverType;
  /** Resolved approver UPN for this stage. */
  approver: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  decidedBy?: string;
  decidedAt?: string;
  note?: string;
}

/** A request for a user to be granted an access role on a term/data product. */
export interface AccessRequest {
  id: string;
  requester: string;
  role: AccessRole;
  justification?: string;
  status: AccessRequestStatus;
  requestedAt: string;
  decidedBy?: string;
  decidedAt?: string;
  note?: string;
  // ---- Multi-stage workflow (self-service routing) -----------------------
  workflowId?: string;
  workflowName?: string;
  /** Ordered approval stages; absent for legacy single-step requests. */
  stages?: StageDecision[];
  /** Index of the stage currently awaiting a decision. */
  currentStage?: number;
}

export interface Term {
  id: string;
  name: string;
  definition: string;
  domainName: string;
  status: TermStatus;
  submittedBy: string;
  updatedAt: string;
  // ---- Atlas-style governance metadata -----------------------------------
  businessOwner: string;
  dataSteward: string;
  sme?: string;
  classification: Classification;
  sourceQualifiedName?: string;
  reviewDueAt?: string;
  approvals: ApprovalEvent[];
  // ---- Entra access control ----------------------------------------------
  /** Security groups (Reader/Contributor/Owner) backing access to this item. */
  groups: EntraGroup[];
  /** Access requests whose approval adds the requester to the matching group. */
  accessRequests: AccessRequest[];
}

/** Build simulated, already-provisioned seed groups with optional members. */
function seedGroups(
  name: string,
  members: Partial<Record<AccessRole, string[]>> = {},
): EntraGroup[] {
  return planGroups(name).map((g) => ({
    ...g,
    provisioned: true,
    objectId: `sim-${g.id}`,
    members: members[g.role] ?? [],
  }));
}

const SEED: Term[] = [
  {
    id: '1',
    name: 'Customer',
    definition: 'A party that has a verified account and can place orders.',
    domainName: 'Sales',
    status: 'Approved',
    submittedBy: 'avery@contoso.com',
    updatedAt: '2026-05-30T14:12:00Z',
    businessOwner: 'dana@contoso.com',
    dataSteward: 'avery@contoso.com',
    sme: 'lee@contoso.com',
    classification: 'Internal',
    sourceQualifiedName: 'purview://contoso/sales/dbo/Customers',
    reviewDueAt: '2026-11-30T00:00:00Z',
    approvals: [
      { action: 'Submitted', actor: 'avery@contoso.com', at: '2026-05-28T10:00:00Z' },
      {
        action: 'Approved',
        actor: 'dana@contoso.com',
        note: 'Aligned with the enterprise customer master.',
        at: '2026-05-30T14:12:00Z',
      },
    ],
    groups: seedGroups('Customer', {
      Owner: ['dana@contoso.com'],
      Contributor: ['avery@contoso.com'],
      Reader: ['lee@contoso.com', 'analytics-team@contoso.com'],
    }),
    accessRequests: [
      {
        id: 'ar-1',
        requester: 'newhire@contoso.com',
        role: 'Reader',
        justification: 'Building the customer 360 dashboard.',
        status: 'Pending',
        requestedAt: '2026-06-15T08:30:00Z',
        workflowId: 'wf-standard',
        workflowName: 'Standard self-service',
        currentStage: 0,
        stages: [
          {
            stageId: 's1',
            stageName: 'Manager approval',
            approverType: 'Manager',
            approver: 'dana@contoso.com',
            status: 'Pending',
          },
          {
            stageId: 's2',
            stageName: 'Data owner approval',
            approverType: 'Data owner',
            approver: 'dana@contoso.com',
            status: 'Pending',
          },
        ],
      },
    ],
  },
  {
    id: '2',
    name: 'Order',
    definition: 'A purchase transaction containing one or more line items.',
    domainName: 'Sales',
    status: 'Approved',
    submittedBy: 'avery@contoso.com',
    updatedAt: '2026-05-30T14:18:00Z',
    businessOwner: 'dana@contoso.com',
    dataSteward: 'avery@contoso.com',
    classification: 'Internal',
    sourceQualifiedName: 'purview://contoso/sales/dbo/Orders',
    reviewDueAt: '2026-11-30T00:00:00Z',
    approvals: [
      { action: 'Submitted', actor: 'avery@contoso.com', at: '2026-05-28T10:05:00Z' },
      { action: 'Approved', actor: 'dana@contoso.com', at: '2026-05-30T14:18:00Z' },
    ],
    groups: seedGroups('Order', {
      Owner: ['dana@contoso.com'],
      Contributor: ['avery@contoso.com'],
      Reader: ['analytics-team@contoso.com'],
    }),
    accessRequests: [],
  },
  {
    id: '3',
    name: 'Net Revenue',
    definition:
      'Recognized revenue per order line, net of returns and discounts.',
    domainName: 'Revenue',
    status: 'Pending',
    submittedBy: 'jordan@contoso.com',
    updatedAt: '2026-06-08T09:41:00Z',
    businessOwner: 'priya@contoso.com',
    dataSteward: 'jordan@contoso.com',
    sme: 'finance-coe@contoso.com',
    classification: 'Confidential',
    sourceQualifiedName: 'purview://contoso/warehouse/gold/fact_sales',
    approvals: [
      { action: 'Submitted', actor: 'jordan@contoso.com', at: '2026-06-08T09:41:00Z' },
    ],
    groups: seedGroups('Net Revenue', {
      Owner: ['priya@contoso.com'],
      Contributor: ['jordan@contoso.com'],
      Reader: ['finance-coe@contoso.com'],
    }),
    accessRequests: [
      {
        id: 'ar-2',
        requester: 'sales-ops@contoso.com',
        role: 'Reader',
        justification: 'Quarterly revenue reconciliation.',
        status: 'Pending',
        requestedAt: '2026-06-14T16:10:00Z',
        workflowId: 'wf-sensitive',
        workflowName: 'Sensitive data',
        currentStage: 1,
        stages: [
          {
            stageId: 's1',
            stageName: 'Manager approval',
            approverType: 'Manager',
            approver: 'priya@contoso.com',
            status: 'Approved',
            decidedBy: 'priya@contoso.com',
            decidedAt: '2026-06-14T17:00:00Z',
          },
          {
            stageId: 's2',
            stageName: 'Data steward review',
            approverType: 'Data steward',
            approver: 'jordan@contoso.com',
            status: 'Pending',
          },
          {
            stageId: 's3',
            stageName: 'Data owner approval',
            approverType: 'Data owner',
            approver: 'priya@contoso.com',
            status: 'Pending',
          },
        ],
      },
      {
        id: 'ar-3',
        requester: 'kai@contoso.com',
        role: 'Contributor',
        status: 'Approved',
        requestedAt: '2026-06-10T11:00:00Z',
        decidedBy: 'priya@contoso.com',
        decidedAt: '2026-06-11T09:00:00Z',
        note: 'Owns the gold fact table refresh.',
      },
    ],
  },
  {
    id: '4',
    name: 'Compensation Package',
    definition:
      'Total pay, bonus, and equity for an employee. Highly confidential.',
    domainName: 'Compensation',
    status: 'Draft',
    submittedBy: 'morgan@contoso.com',
    updatedAt: '2026-06-09T07:05:00Z',
    businessOwner: 'hr-director@contoso.com',
    dataSteward: 'morgan@contoso.com',
    classification: 'Highly Confidential',
    approvals: [],
    groups: seedGroups('Compensation Package', {
      Owner: ['hr-director@contoso.com'],
      Contributor: ['morgan@contoso.com'],
    }),
    accessRequests: [],
  },
  {
    id: '5',
    name: 'Clickstream Event',
    definition:
      'A single user interaction captured from web or mobile telemetry.',
    domainName: 'Telemetry',
    status: 'Rejected',
    submittedBy: 'sam@contoso.com',
    updatedAt: '2026-06-02T19:30:00Z',
    businessOwner: 'platform-lead@contoso.com',
    dataSteward: 'sam@contoso.com',
    classification: 'PII',
    sourceQualifiedName: 'purview://contoso/lakehouse/silver/clickstream',
    approvals: [
      { action: 'Submitted', actor: 'sam@contoso.com', at: '2026-06-01T12:00:00Z' },
      {
        action: 'Rejected',
        actor: 'platform-lead@contoso.com',
        note: 'Needs a PII handling note and retention policy before approval.',
        at: '2026-06-02T19:30:00Z',
      },
    ],
    groups: seedGroups('Clickstream Event', {
      Owner: ['platform-lead@contoso.com'],
      Contributor: ['sam@contoso.com'],
    }),
    accessRequests: [],
  },
];

export interface DataClientResult {
  terms: Term[];
  source: 'backend' | 'seed';
}

const TERM_STATUSES: TermStatus[] = [
  'Draft',
  'Pending',
  'Approved',
  'Rejected',
  'Deprecated',
];

/** Normalize a backend status string to the frontend TermStatus union. */
function toTermStatus(raw: string): TermStatus {
  const match = TERM_STATUSES.find(
    (s) => s.toLowerCase() === raw?.toLowerCase(),
  );
  return match ?? 'Draft';
}

/**
 * Map a backend Term row to the richer frontend Term shape. Governance,
 * group, and access-request metadata are not yet persisted in the backend
 * entity, so they default to empty/sensible values for backend-sourced rows.
 */
function rowToTerm(row: {
  id: string;
  name: string;
  definition: string;
  domainId?: string;
  status: string;
  submittedBySub?: string;
  auditCreatedAt?: string;
  auditUpdatedAt?: string;
  purviewQualifiedName?: string;
}): Term {
  const owner = row.submittedBySub ?? 'unknown';
  return {
    id: row.id,
    name: row.name,
    definition: row.definition,
    domainName: row.domainId ?? '',
    status: toTermStatus(row.status),
    submittedBy: owner,
    updatedAt: row.auditUpdatedAt ?? row.auditCreatedAt ?? new Date().toISOString(),
    businessOwner: owner,
    dataSteward: owner,
    classification: 'Internal',
    sourceQualifiedName: row.purviewQualifiedName,
    approvals: [],
    groups: planGroups(row.name).map((g) => ({
      ...g,
      provisioned: false,
      members: [],
    })),
    accessRequests: [],
  };
}

export async function listTerms(): Promise<DataClientResult> {
  const client = getRayfinClient();
  if (!client) {
    return { terms: SEED, source: 'seed' };
  }
  // When a backend is configured we try the SDK first, but fall back to the
  // seed examples if it is unreachable (e.g. the static page lacks the auth /
  // CORS context for the Rayfin data-plane). This keeps the summary populated
  // instead of surfacing a "Failed to fetch" error.
  try {
    const rows = await client.data.Term.select([
      'id',
      'name',
      'definition',
      'domainId',
      'status',
      'submittedBySub',
      'purviewQualifiedName',
      'auditCreatedAt',
      'auditUpdatedAt',
    ]).execute();
    // An empty backend (freshly provisioned schema) still shows the examples
    // so the dashboard is not blank.
    if (!rows || rows.length === 0) {
      return { terms: SEED, source: 'seed' };
    }
    return { terms: rows.map(rowToTerm), source: 'backend' };
  } catch {
    return { terms: SEED, source: 'seed' };
  }
}

/** Whether a Rayfin backend is configured (vs. seed-only mode). */
export { isBackendConfigured };

