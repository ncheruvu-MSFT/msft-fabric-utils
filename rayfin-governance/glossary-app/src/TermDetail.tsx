import { useState } from 'react';
import {
  Badge,
  Body1,
  Button,
  Caption1,
  Divider,
  Dropdown,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  Field,
  Input,
  Option,
  OverlayDrawer,
  Textarea,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  CheckmarkCircleRegular,
  DismissRegular,
  KeyRegular,
  PeopleTeamRegular,
  PersonRegular,
  ShieldRegular,
  TagRegular,
} from '@fluentui/react-icons';
import {
  AccessRole,
  ApprovalEvent,
  Term,
  TermStatus,
  WorkflowTemplate,
} from './dataClient';
import {
  CLASSIFICATION_APPEARANCE,
  LIFECYCLE,
  LIFECYCLE_STAGES,
  LifecycleAction,
  availableActions,
} from './governance';
import { ACCESS_ROLES, ROLE_PERMISSION } from './graphClient';
import { pickWorkflow } from './workflow';

const statusAppearance: Record<
  TermStatus,
  'success' | 'warning' | 'danger' | 'informative' | 'subtle'
> = {
  Approved: 'success',
  Pending: 'warning',
  Rejected: 'danger',
  Draft: 'informative',
  Deprecated: 'subtle',
};

const roleColor: Record<AccessRole, 'brand' | 'informative' | 'success'> = {
  Reader: 'informative',
  Contributor: 'brand',
  Owner: 'success',
};

const eventColor: Record<
  ApprovalEvent['action'],
  'success' | 'warning' | 'danger' | 'informative' | 'subtle'
> = {
  Submitted: 'informative',
  Approved: 'success',
  Rejected: 'danger',
  Deprecated: 'subtle',
  Reopened: 'warning',
};

const useStyles = makeStyles({
  body: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('16px'),
  },
  section: { display: 'flex', flexDirection: 'column', ...shorthands.gap('6px') },
  sectionHead: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('6px'),
    color: tokens.colorNeutralForeground2,
  },
  roleGrid: {
    display: 'grid',
    gridTemplateColumns: '120px 1fr',
    ...shorthands.gap('4px', '12px'),
    alignItems: 'center',
  },
  roleLabel: { color: tokens.colorNeutralForeground3 },
  stepper: { display: 'flex', alignItems: 'center', ...shorthands.gap('4px') },
  step: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    ...shorthands.gap('2px'),
    flexGrow: 1,
  },
  dot: {
    width: '14px',
    height: '14px',
    ...shorthands.borderRadius('50%'),
    ...shorthands.border('2px', 'solid', tokens.colorNeutralStroke2),
  },
  dotDone: {
    backgroundColor: tokens.colorBrandBackground,
    ...shorthands.border('2px', 'solid', tokens.colorBrandBackground),
  },
  dotCurrent: {
    ...shorthands.border('2px', 'solid', tokens.colorBrandBackground),
    backgroundColor: tokens.colorNeutralBackground1,
  },
  connector: { height: '2px', flexGrow: 1, backgroundColor: tokens.colorNeutralStroke2 },
  connectorDone: { backgroundColor: tokens.colorBrandBackground },
  timeline: { display: 'flex', flexDirection: 'column', ...shorthands.gap('10px') },
  event: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('2px'),
    ...shorthands.borderLeft('2px', 'solid', tokens.colorNeutralStroke2),
    ...shorthands.padding('0', '0', '0', '12px'),
  },
  actions: { display: 'flex', ...shorthands.gap('8px'), flexWrap: 'wrap' },
  group: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('4px'),
    ...shorthands.padding('10px', '12px'),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorNeutralBackground2,
  },
  groupHead: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shorthands.gap('8px'),
  },
  members: { display: 'flex', flexWrap: 'wrap', ...shorthands.gap('4px') },
  request: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('6px'),
    ...shorthands.padding('10px', '12px'),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
  },
  requestRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shorthands.gap('8px'),
    flexWrap: 'wrap',
  },
  stageList: { display: 'flex', flexDirection: 'column', ...shorthands.gap('4px') },
  stageItem: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
  },
  stageDot: {
    width: '10px',
    height: '10px',
    flexShrink: 0,
    ...shorthands.borderRadius('50%'),
    backgroundColor: tokens.colorNeutralStroke2,
  },
  stageDotDone: { backgroundColor: tokens.colorPaletteGreenBackground3 },
  stageDotCurrent: { backgroundColor: tokens.colorBrandBackground },
  stageDotRejected: { backgroundColor: tokens.colorPaletteRedBackground3 },
  chain: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    ...shorthands.gap('4px'),
  },
});

function fmt(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function Role({ label, value }: { label: string; value?: string }) {
  return (
    <>
      <Caption1>{label}</Caption1>
      <Body1>{value && value.trim() ? value : '—'}</Body1>
    </>
  );
}

export interface TermDetailProps {
  term: Term | null;
  open: boolean;
  onClose: () => void;
  onAction: (action: LifecycleAction, note?: string) => void;
  onRequestAccess: (role: AccessRole, justification?: string) => void;
  onDecideAccess: (
    requestId: string,
    decision: 'Approved' | 'Rejected',
    note?: string,
  ) => void;
  workflows: WorkflowTemplate[];
}

export function TermDetail({
  term,
  open,
  onClose,
  onAction,
  onRequestAccess,
  onDecideAccess,
  workflows,
}: TermDetailProps) {
  const styles = useStyles();
  const [note, setNote] = useState('');
  const [reqRole, setReqRole] = useState<AccessRole>('Reader');
  const [reqJustification, setReqJustification] = useState('');
  const [decisionNote, setDecisionNote] = useState('');

  if (!term) return null;

  const actions = availableActions(term);
  const activeWorkflow = pickWorkflow(workflows, term);
  const pendingRequests = term.accessRequests.filter(
    (r) => r.status === 'Pending',
  );
  const decidedRequests = term.accessRequests.filter(
    (r) => r.status !== 'Pending',
  );
  const currentIdx = LIFECYCLE_STAGES.findIndex((s) => s.status === term.status);
  // Rejected isn't a forward stage; treat it as "in review" position visually.
  const activeIdx =
    term.status === 'Rejected' ? 1 : currentIdx === -1 ? 0 : currentIdx;

  const run = (a: LifecycleAction) => {
    onAction(a, note);
    setNote('');
  };

  return (
    <OverlayDrawer
      position="end"
      open={open}
      onOpenChange={(_, d) => !d.open && onClose()}
      size="medium"
    >
      <DrawerHeader>
        <DrawerHeaderTitle
          action={
            <Button
              appearance="subtle"
              icon={<DismissRegular />}
              aria-label="Close"
              onClick={onClose}
            />
          }
        >
          {term.name}
        </DrawerHeaderTitle>
      </DrawerHeader>
      <DrawerBody>
        <div className={styles.body}>
          <div className={styles.section}>
            <div className={styles.actions}>
              <Badge appearance="filled" color={statusAppearance[term.status]}>
                {term.status === 'Pending' ? 'In review' : term.status}
              </Badge>
              <Badge
                appearance="tint"
                color={CLASSIFICATION_APPEARANCE[term.classification]}
                icon={<ShieldRegular />}
              >
                {term.classification}
              </Badge>
              <Badge appearance="outline" icon={<TagRegular />}>
                {term.domainName}
              </Badge>
            </div>
            <Body1>{term.definition}</Body1>
          </div>

          <Divider />

          {/* lifecycle stepper */}
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <CheckmarkCircleRegular />
              <Caption1>Lifecycle</Caption1>
            </div>
            <div className={styles.stepper}>
              {LIFECYCLE_STAGES.map((s, i) => (
                <div className={styles.step} key={s.status}>
                  <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    {i > 0 && (
                      <div
                        className={`${styles.connector} ${
                          i <= activeIdx ? styles.connectorDone : ''
                        }`}
                      />
                    )}
                    <div
                      className={`${styles.dot} ${
                        i < activeIdx ? styles.dotDone : ''
                      } ${i === activeIdx ? styles.dotCurrent : ''}`}
                    />
                    {i < LIFECYCLE_STAGES.length - 1 && (
                      <div
                        className={`${styles.connector} ${
                          i < activeIdx ? styles.connectorDone : ''
                        }`}
                      />
                    )}
                  </div>
                  <Caption1>{s.label}</Caption1>
                </div>
              ))}
            </div>
          </div>

          <Divider />

          {/* governance roles (Atlas-style ownership) */}
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <PersonRegular />
              <Caption1>Ownership &amp; accountability</Caption1>
            </div>
            <div className={styles.roleGrid}>
              <Role label="Business owner" value={term.businessOwner} />
              <Role label="Data steward" value={term.dataSteward} />
              <Role label="SME / expert" value={term.sme} />
              <Role label="Submitted by" value={term.submittedBy} />
            </div>
          </div>

          <Divider />

          {/* source linkage + review */}
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <TagRegular />
              <Caption1>Source &amp; review</Caption1>
            </div>
            <div className={styles.roleGrid}>
              <Role
                label="Source asset"
                value={term.sourceQualifiedName ?? 'Not linked'}
              />
              <Role
                label="Next review"
                value={term.reviewDueAt ? fmt(term.reviewDueAt) : 'Not scheduled'}
              />
              <Role label="Last updated" value={fmt(term.updatedAt)} />
            </div>
          </div>

          <Divider />

          {/* approval audit trail */}
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <CheckmarkCircleRegular />
              <Caption1>Approval history</Caption1>
            </div>
            {term.approvals.length === 0 ? (
              <Caption1>No lifecycle events yet — still a draft.</Caption1>
            ) : (
              <div className={styles.timeline}>
                {[...term.approvals].reverse().map((e, i) => (
                  <div className={styles.event} key={i}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <Badge appearance="tint" color={eventColor[e.action]}>
                        {e.action}
                      </Badge>
                      <Caption1>{fmt(e.at)}</Caption1>
                    </div>
                    <Caption1>by {e.actor}</Caption1>
                    {e.note && <Body1>{e.note}</Body1>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Entra security groups */}
          <Divider />
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <PeopleTeamRegular />
              <Caption1>Entra security groups</Caption1>
            </div>
            <Caption1>
              Access is granted by membership in these Entra ID groups. Approving
              a request adds the user to the group for the granted role.
            </Caption1>
            {term.groups.length === 0 ? (
              <Caption1>No groups provisioned yet.</Caption1>
            ) : (
              term.groups.map((g) => (
                <div className={styles.group} key={g.id}>
                  <div className={styles.groupHead}>
                    <div
                      style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                    >
                      <Badge appearance="filled" color={roleColor[g.role]}>
                        {g.role}
                      </Badge>
                      <Body1 style={{ fontFamily: tokens.fontFamilyMonospace }}>
                        {g.displayName}
                      </Body1>
                    </div>
                    <Badge appearance="ghost">
                      {g.members.length}{' '}
                      {g.members.length === 1 ? 'member' : 'members'}
                    </Badge>
                  </div>
                  <Caption1>{ROLE_PERMISSION[g.role]}</Caption1>
                  {g.members.length > 0 && (
                    <div className={styles.members}>
                      {g.members.map((m) => (
                        <Badge
                          key={m}
                          appearance="outline"
                          icon={<PersonRegular />}
                        >
                          {m}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Access requests */}
          <Divider />
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <KeyRegular />
              <Caption1>Access requests</Caption1>
            </div>

            {pendingRequests.length > 0 && (
              <Field label="Decision note (optional)">
                <Input
                  value={decisionNote}
                  onChange={(_, d) => setDecisionNote(d.value)}
                  placeholder="Reason for this access decision…"
                />
              </Field>
            )}

            {pendingRequests.length === 0 ? (
              <Caption1>No pending access requests.</Caption1>
            ) : (
              pendingRequests.map((r) => {
                const stages = r.stages ?? [];
                const curIdx = r.currentStage ?? 0;
                const curStage = stages[curIdx];
                const isFinalStage = stages.length === 0 || curIdx >= stages.length - 1;
                return (
                  <div className={styles.request} key={r.id}>
                    <div className={styles.requestRow}>
                      <div
                        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                      >
                        <Badge appearance="tint" color={roleColor[r.role]}>
                          {r.role}
                        </Badge>
                        <Body1>{r.requester}</Body1>
                      </div>
                      <div className={styles.actions}>
                        <Button
                          size="small"
                          appearance="primary"
                          onClick={() => {
                            onDecideAccess(r.id, 'Approved', decisionNote);
                            setDecisionNote('');
                          }}
                        >
                          {isFinalStage ? 'Approve & grant' : 'Approve stage'}
                        </Button>
                        <Button
                          size="small"
                          appearance="secondary"
                          onClick={() => {
                            onDecideAccess(r.id, 'Rejected', decisionNote);
                            setDecisionNote('');
                          }}
                        >
                          Reject
                        </Button>
                      </div>
                    </div>
                    {r.justification && <Caption1>{r.justification}</Caption1>}
                    {r.workflowName && (
                      <Caption1>
                        Workflow: <strong>{r.workflowName}</strong>
                        {curStage ? ` · awaiting ${curStage.approver}` : ''}
                      </Caption1>
                    )}
                    {stages.length > 0 && (
                      <div className={styles.stageList}>
                        {stages.map((s, i) => (
                          <div className={styles.stageItem} key={s.stageId}>
                            <div
                              className={`${styles.stageDot} ${
                                s.status === 'Approved'
                                  ? styles.stageDotDone
                                  : s.status === 'Rejected'
                                  ? styles.stageDotRejected
                                  : i === curIdx
                                  ? styles.stageDotCurrent
                                  : ''
                              }`}
                            />
                            <Caption1>
                              {i + 1}. {s.stageName} — {s.approver}
                              {s.status === 'Approved'
                                ? ' ✓'
                                : i === curIdx
                                ? ' (awaiting)'
                                : ''}
                            </Caption1>
                          </div>
                        ))}
                      </div>
                    )}
                    <Caption1>Requested {fmt(r.requestedAt)}</Caption1>
                  </div>
                );
              })
            )}

            {decidedRequests.length > 0 && (
              <div className={styles.timeline} style={{ marginTop: 8 }}>
                {[...decidedRequests].reverse().map((r) => (
                  <div className={styles.event} key={r.id}>
                    <div
                      style={{ display: 'flex', gap: 8, alignItems: 'center' }}
                    >
                      <Badge
                        appearance="tint"
                        color={r.status === 'Approved' ? 'success' : 'danger'}
                      >
                        {r.status}
                      </Badge>
                      <Caption1>
                        {r.role} · {r.requester}
                      </Caption1>
                    </div>
                    <Caption1>
                      {r.decidedBy ? `by ${r.decidedBy}` : ''}
                      {r.decidedAt ? ` · ${fmt(r.decidedAt)}` : ''}
                    </Caption1>
                    {r.note && <Caption1>{r.note}</Caption1>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Request access form */}
          <Divider />
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <KeyRegular />
              <Caption1>Request access</Caption1>
            </div>
            <Caption1>
              Self-service request — routed through the{' '}
              <strong>{activeWorkflow.name}</strong> approval path:
            </Caption1>
            <div className={styles.chain}>
              <Badge appearance="outline">You</Badge>
              {activeWorkflow.stages.map((s) => (
                <span key={s.id} className={styles.chain}>
                  <Caption1>→</Caption1>
                  <Badge appearance="tint" color="brand">
                    {s.approverUpn?.trim() || s.approverType}
                  </Badge>
                </span>
              ))}
              <Caption1>→</Caption1>
              <Badge appearance="tint" color="success">
                Group access
              </Badge>
            </div>
            <Field label="Access role">
              <Dropdown
                value={reqRole}
                selectedOptions={[reqRole]}
                onOptionSelect={(_, d) =>
                  setReqRole((d.optionValue as AccessRole) ?? 'Reader')
                }
              >
                {ACCESS_ROLES.map((role) => (
                  <Option key={role} value={role} text={role}>
                    {role} — {ROLE_PERMISSION[role]}
                  </Option>
                ))}
              </Dropdown>
            </Field>
            <Field label="Business justification">
              <Input
                value={reqJustification}
                onChange={(_, d) => setReqJustification(d.value)}
                placeholder="Why do you need this access?"
              />
            </Field>
            <div className={styles.actions}>
              <Button
                appearance="primary"
                onClick={() => {
                  onRequestAccess(reqRole, reqJustification);
                  setReqJustification('');
                }}
              >
                Submit request
              </Button>
            </div>
          </div>

          {actions.length > 0 && (
            <>
              <Divider />
              <div className={styles.section}>
                <Title3 as="h3" style={{ fontSize: tokens.fontSizeBase400 }}>
                  Take action
                </Title3>
                <Field label="Decision note (optional)">
                  <Textarea
                    value={note}
                    onChange={(_, d) => setNote(d.value)}
                    placeholder="Add context for this decision…"
                    rows={2}
                  />
                </Field>
                <div className={styles.actions}>
                  {actions.map((a) => (
                    <Button
                      key={a}
                      appearance={a === 'approve' ? 'primary' : 'secondary'}
                      onClick={() => run(a)}
                    >
                      {LIFECYCLE[a].label}
                    </Button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </DrawerBody>
    </OverlayDrawer>
  );
}
