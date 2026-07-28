// Atlas-style glossary lifecycle for the glossary-app.
//
// Glossary terms follow a governed approval workflow modelled on Apache Atlas /
// Microsoft Purview: a term is drafted, submitted for review, then approved or
// rejected by a business owner / steward, and can later be deprecated. Every
// transition is appended to the term's `approvals` audit trail.

import { ApprovalEvent, Term, TermStatus } from './dataClient';

export type LifecycleAction =
  | 'submit'
  | 'approve'
  | 'reject'
  | 'deprecate'
  | 'reopen';

interface ActionMeta {
  label: string;
  /** Statuses from which this action is allowed. */
  from: TermStatus[];
  to: TermStatus;
  event: ApprovalEvent['action'];
  /** Whether this action is a steward/owner decision (vs. an author action). */
  decision: boolean;
}

export const LIFECYCLE: Record<LifecycleAction, ActionMeta> = {
  submit: {
    label: 'Submit for review',
    from: ['Draft', 'Rejected'],
    to: 'Pending',
    event: 'Submitted',
    decision: false,
  },
  approve: {
    label: 'Approve',
    from: ['Pending'],
    to: 'Approved',
    event: 'Approved',
    decision: true,
  },
  reject: {
    label: 'Reject',
    from: ['Pending'],
    to: 'Rejected',
    event: 'Rejected',
    decision: true,
  },
  deprecate: {
    label: 'Deprecate',
    from: ['Approved'],
    to: 'Deprecated',
    event: 'Deprecated',
    decision: true,
  },
  reopen: {
    label: 'Reopen as draft',
    from: ['Deprecated', 'Rejected'],
    to: 'Draft',
    event: 'Reopened',
    decision: false,
  },
};

/** Ordered lifecycle stages used to render a progress stepper. */
export const LIFECYCLE_STAGES: { status: TermStatus; label: string }[] = [
  { status: 'Draft', label: 'Draft' },
  { status: 'Pending', label: 'In review' },
  { status: 'Approved', label: 'Approved' },
  { status: 'Deprecated', label: 'Deprecated' },
];

/** Which actions are currently available for a term, given its status. */
export function availableActions(term: Term): LifecycleAction[] {
  return (Object.keys(LIFECYCLE) as LifecycleAction[]).filter((a) =>
    LIFECYCLE[a].from.includes(term.status),
  );
}

/** Apply a lifecycle transition, returning a new Term with an appended event. */
export function applyAction(
  term: Term,
  action: LifecycleAction,
  actor: string,
  note?: string,
): Term {
  const meta = LIFECYCLE[action];
  if (!meta.from.includes(term.status)) return term;
  const now = new Date().toISOString();
  const event: ApprovalEvent = {
    action: meta.event,
    actor,
    note: note?.trim() || undefined,
    at: now,
  };
  return {
    ...term,
    status: meta.to,
    updatedAt: now,
    approvals: [...term.approvals, event],
  };
}

export const CLASSIFICATION_APPEARANCE: Record<
  Term['classification'],
  'success' | 'informative' | 'warning' | 'danger' | 'severe'
> = {
  Public: 'success',
  Internal: 'informative',
  Confidential: 'warning',
  'Highly Confidential': 'danger',
  PII: 'severe',
};

