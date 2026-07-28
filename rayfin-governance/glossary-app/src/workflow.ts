// Self-service access-request workflows for the glossary-app.
//
// A user submits an access request for a term / data product. Instead of a
// single approval, the request is routed through a configurable chain of
// approval stages — typically the requester's manager, then the data owner,
// with extra steward / security reviews for sensitive data. A data-map admin /
// data owner edits these templates (see WorkflowEditor) and binds them to
// classifications. When the final stage is approved the requester is added to
// the Entra security group for the granted role.

import type {
  AccessRequest,
  AccessRole,
  ApprovalStage,
  StageDecision,
  Term,
  WorkflowTemplate,
} from './dataClient';
import { addGroupMember, managerOf } from './graphClient';

function newId(prefix: string): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? `${prefix}-${crypto.randomUUID()}`
    : `${prefix}-${Date.now()}`;
}

/** Seed approval-workflow templates a data-map admin can edit/extend. */
export function defaultWorkflows(): WorkflowTemplate[] {
  return [
    {
      id: 'wf-standard',
      name: 'Standard self-service',
      description:
        'Requester → manager → data owner. For Public and Internal data.',
      appliesTo: ['Public', 'Internal'],
      stages: [
        { id: 's1', name: 'Manager approval', approverType: 'Manager', slaHours: 48 },
        { id: 's2', name: 'Data owner approval', approverType: 'Data owner', slaHours: 72 },
      ],
    },
    {
      id: 'wf-sensitive',
      name: 'Sensitive data',
      description:
        'Adds a data steward review before the owner signs off. For Confidential data.',
      appliesTo: ['Confidential'],
      stages: [
        { id: 's1', name: 'Manager approval', approverType: 'Manager', slaHours: 48 },
        { id: 's2', name: 'Data steward review', approverType: 'Data steward', slaHours: 72 },
        { id: 's3', name: 'Data owner approval', approverType: 'Data owner', slaHours: 72 },
      ],
    },
    {
      id: 'wf-restricted',
      name: 'Restricted / PII',
      description:
        'Highest scrutiny: manager, steward, security admin, then owner. For Highly Confidential and PII data.',
      appliesTo: ['Highly Confidential', 'PII'],
      stages: [
        { id: 's1', name: 'Manager approval', approverType: 'Manager', slaHours: 24 },
        { id: 's2', name: 'Data steward review', approverType: 'Data steward', slaHours: 48 },
        { id: 's3', name: 'Security admin sign-off', approverType: 'Security admin', slaHours: 48 },
        { id: 's4', name: 'Data owner approval', approverType: 'Data owner', slaHours: 48 },
      ],
    },
  ];
}

/** Pick the workflow template that applies to a term (by classification). */
export function pickWorkflow(
  templates: WorkflowTemplate[],
  term: Term,
): WorkflowTemplate {
  const match = templates.find(
    (t) => t.appliesTo !== '*' && t.appliesTo.includes(term.classification),
  );
  return (
    match ?? templates.find((t) => t.appliesTo === '*') ?? templates[0]
  );
}

/** Resolve the concrete approver UPN for a stage, given the term + requester. */
async function resolveApprover(
  stage: ApprovalStage,
  term: Term,
  requester: string,
): Promise<string> {
  if (stage.approverUpn && stage.approverUpn.trim()) return stage.approverUpn.trim();
  switch (stage.approverType) {
    case 'Manager':
      return managerOf(requester);
    case 'Data owner':
      return term.businessOwner;
    case 'Data steward':
      return term.dataSteward;
    case 'Security admin':
      return 'security-admin@contoso.com';
    case 'Custom':
    default:
      return 'unassigned@contoso.com';
  }
}

/** Materialise a template's stages into pending StageDecisions for a request. */
export async function buildStages(
  template: WorkflowTemplate,
  term: Term,
  requester: string,
): Promise<StageDecision[]> {
  const out: StageDecision[] = [];
  for (const s of template.stages) {
    out.push({
      stageId: s.id,
      stageName: s.name,
      approverType: s.approverType,
      approver: await resolveApprover(s, term, requester),
      status: 'Pending',
    });
  }
  return out;
}

/** Submit a self-service access request routed through the given workflow. */
export async function submitAccessRequest(
  term: Term,
  requester: string,
  role: AccessRole,
  justification: string | undefined,
  template: WorkflowTemplate,
): Promise<Term> {
  const stages = await buildStages(template, term, requester);
  const req: AccessRequest = {
    id: newId('ar'),
    requester,
    role,
    justification: justification?.trim() || undefined,
    status: 'Pending',
    requestedAt: new Date().toISOString(),
    workflowId: template.id,
    workflowName: template.name,
    stages,
    currentStage: 0,
  };
  return { ...term, accessRequests: [...term.accessRequests, req] };
}

/**
 * Record a decision on the current stage of an access request. Approving a
 * non-final stage advances the request; approving the final stage grants access
 * by adding the requester to the Entra group for the role. Rejecting any stage
 * rejects the whole request. Legacy requests without stages are decided in one
 * step.
 */
export async function decideStage(
  term: Term,
  requestId: string,
  decision: 'Approved' | 'Rejected',
  decider: string,
  note?: string,
): Promise<Term> {
  const req = term.accessRequests.find((r) => r.id === requestId);
  if (!req || req.status !== 'Pending') return term;

  const now = new Date().toISOString();
  const trimmedNote = note?.trim() || undefined;

  const grant = async () => {
    const idx = term.groups.findIndex((g) => g.role === req.role);
    if (idx < 0) return term.groups;
    const updated = await addGroupMember(term.groups[idx], req.requester);
    return term.groups.map((g, i) => (i === idx ? updated : g));
  };

  // Legacy / single-step request (no staged workflow).
  if (!req.stages || req.stages.length === 0) {
    const groups = decision === 'Approved' ? await grant() : term.groups;
    const accessRequests = term.accessRequests.map((r) =>
      r.id === requestId
        ? { ...r, status: decision, decidedBy: decider, decidedAt: now, note: trimmedNote }
        : r,
    );
    return { ...term, groups, accessRequests };
  }

  const stageIdx = req.currentStage ?? 0;
  const stages = req.stages.map((s, i) =>
    i === stageIdx
      ? { ...s, status: decision, decidedBy: decider, decidedAt: now, note: trimmedNote }
      : s,
  );

  let groups = term.groups;
  let reqStatus: AccessRequest['status'] = req.status;
  let nextStage = stageIdx;

  if (decision === 'Rejected') {
    reqStatus = 'Rejected';
  } else if (stageIdx + 1 < stages.length) {
    nextStage = stageIdx + 1; // advance to the next approver
  } else {
    reqStatus = 'Approved'; // final stage approved → grant access
    groups = await grant();
  }

  const finalised = reqStatus !== 'Pending';
  const accessRequests = term.accessRequests.map((r) =>
    r.id === requestId
      ? {
          ...r,
          stages,
          currentStage: nextStage,
          status: reqStatus,
          decidedBy: finalised ? decider : r.decidedBy,
          decidedAt: finalised ? now : r.decidedAt,
          note: finalised ? trimmedNote : r.note,
        }
      : r,
  );
  return { ...term, groups, accessRequests };
}
