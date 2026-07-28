import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Badge,
  Body1,
  Button,
  Caption1,
  Card,
  DataGrid,
  DataGridBody,
  DataGridCell,
  DataGridHeader,
  DataGridHeaderCell,
  DataGridRow,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  DialogTrigger,
  Dropdown,
  Field,
  Input,
  Option,
  Spinner,
  TableCellLayout,
  TableColumnDefinition,
  Textarea,
  Title3,
  Tooltip,
  createTableColumn,
  mergeClasses,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  AddRegular,
  ArrowSyncRegular,
  BookDatabaseRegular,
  CloudRegular,
  FlowRegular,
  PersonRegular,
  PlugDisconnectedRegular,
  ShieldRegular,
  SparkleRegular,
} from '@fluentui/react-icons';
import { HEADER_GRADIENT } from './theme';
import { Term, TermStatus, Classification, AccessRole, WorkflowTemplate, listTerms } from './dataClient';
import { askAgent } from './agentClient';
import { ChatPanel } from './ChatPanel';
import { TermDetail } from './TermDetail';
import { WorkflowEditor } from './WorkflowEditor';
import {
  CLASSIFICATION_APPEARANCE,
  LifecycleAction,
  applyAction,
} from './governance';
import { provisionGroups } from './graphClient';
import {
  decideStage,
  defaultWorkflows,
  pickWorkflow,
  submitAccessRequest,
} from './workflow';

const useStyles = makeStyles({
  root: {
    minHeight: '100vh',
    backgroundColor: tokens.colorNeutralBackground2,
    backgroundImage: `radial-gradient(1200px 500px at 100% -10%, ${tokens.colorBrandBackground2} 0%, transparent 60%)`,
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('14px'),
    ...shorthands.padding('16px', '24px'),
    backgroundImage: HEADER_GRADIENT,
    color: tokens.colorNeutralForegroundOnBrand,
    boxShadow: tokens.shadow16,
    position: 'relative',
    zIndex: 1,
  },
  headerIcon: {
    fontSize: '22px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '38px',
    height: '38px',
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
    boxShadow: 'inset 0 0 0 1px rgba(255, 255, 255, 0.25)',
  },
  headerTitles: { display: 'flex', flexDirection: 'column' },
  headerSpacer: { flexGrow: 1 },
  rayfinPill: {
    display: 'inline-flex',
    alignItems: 'center',
    ...shorthands.gap('6px'),
    ...shorthands.padding('4px', '10px'),
    ...shorthands.borderRadius(tokens.borderRadiusCircular),
    ...shorthands.border('1px', 'solid', 'rgba(255, 255, 255, 0.35)'),
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    color: tokens.colorNeutralForegroundOnBrand,
    fontSize: tokens.fontSizeBase200,
    fontWeight: tokens.fontWeightSemibold,
    letterSpacing: '0.02em',
    whiteSpace: 'nowrap',
  },
  breadcrumbBar: {
    ...shorthands.padding('8px', '24px'),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderBottom('1px', 'solid', tokens.colorNeutralStroke2),
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
  },
  content: {
    ...shorthands.padding('24px'),
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('16px'),
    maxWidth: '1200px',
    width: '100%',
    boxSizing: 'border-box',
    alignSelf: 'center',
  },
  toolbarCard: {
    ...shorthands.padding('4px', '8px'),
  },
  gridCard: {
    ...shorthands.padding('0'),
    ...shorthands.overflow('hidden'),
    boxShadow: tokens.shadow8,
  },
  statsRow: {
    display: 'flex',
    ...shorthands.gap('12px'),
    flexWrap: 'wrap',
  },
  statCard: {
    minWidth: '150px',
    ...shorthands.padding('14px', '18px'),
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('2px'),
    ...shorthands.borderLeft('3px', 'solid', tokens.colorBrandStroke1),
    boxShadow: tokens.shadow4,
  },
  statValue: {
    fontSize: tokens.fontSizeHero700,
    fontWeight: tokens.fontWeightSemibold,
    lineHeight: tokens.lineHeightHero700,
    color: tokens.colorBrandForeground1,
  },
  statCardButton: {
    cursor: 'pointer',
    transitionProperty: 'transform, box-shadow, background-color, border-color',
    transitionDuration: tokens.durationNormal,
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow16,
    },
    ':focus-visible': {
      outlineWidth: '2px',
      outlineStyle: 'solid',
      outlineColor: tokens.colorBrandStroke1,
      outlineOffset: '2px',
    },
  },
  statCardActive: {
    ...shorthands.borderLeft('3px', 'solid', tokens.colorBrandForeground1),
    backgroundColor: tokens.colorBrandBackground2,
    boxShadow: tokens.shadow16,
  },
  toolbarRow: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
    flexWrap: 'wrap',
  },
  gridHeader: {
    backgroundColor: tokens.colorNeutralBackground3,
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.padding('48px'),
  },
});

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

function statusLabel(s: TermStatus): string {
  return s === 'Pending' ? 'In review' : s;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

const columns: TableColumnDefinition<Term>[] = [
  createTableColumn<Term>({
    columnId: 'name',
    compare: (a, b) => a.name.localeCompare(b.name),
    renderHeaderCell: () => 'Term',
    renderCell: (item) => (
      <TableCellLayout media={<BookDatabaseRegular />}>
        <strong>{item.name}</strong>
      </TableCellLayout>
    ),
  }),
  createTableColumn<Term>({
    columnId: 'domainName',
    compare: (a, b) => a.domainName.localeCompare(b.domainName),
    renderHeaderCell: () => 'Domain',
    renderCell: (item) => <TableCellLayout>{item.domainName}</TableCellLayout>,
  }),
  createTableColumn<Term>({
    columnId: 'businessOwner',
    compare: (a, b) => a.businessOwner.localeCompare(b.businessOwner),
    renderHeaderCell: () => 'Business owner',
    renderCell: (item) => (
      <TableCellLayout media={<PersonRegular />}>
        {item.businessOwner}
      </TableCellLayout>
    ),
  }),
  createTableColumn<Term>({
    columnId: 'classification',
    compare: (a, b) => a.classification.localeCompare(b.classification),
    renderHeaderCell: () => 'Classification',
    renderCell: (item) => (
      <Badge
        appearance="tint"
        color={CLASSIFICATION_APPEARANCE[item.classification]}
        icon={<ShieldRegular />}
      >
        {item.classification}
      </Badge>
    ),
  }),
  createTableColumn<Term>({
    columnId: 'status',
    compare: (a, b) => a.status.localeCompare(b.status),
    renderHeaderCell: () => 'Status',
    renderCell: (item) => (
      <Badge appearance="filled" color={statusAppearance[item.status]}>
        {statusLabel(item.status)}
      </Badge>
    ),
  }),
  createTableColumn<Term>({
    columnId: 'updatedAt',
    compare: (a, b) =>
      new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime(),
    renderHeaderCell: () => 'Updated',
    renderCell: (item) => (
      <TableCellLayout>{formatDate(item.updatedAt)}</TableCellLayout>
    ),
  }),
];

export function App() {
  const styles = useStyles();
  const [terms, setTerms] = useState<Term[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<'backend' | 'seed'>('seed');
  const [err, setErr] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<
    'all' | 'Approved' | 'Pending' | 'Draft'
  >('all');
  const [wfEditorOpen, setWfEditorOpen] = useState(false);
  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>(
    defaultWorkflows(),
  );
  const [form, setForm] = useState({
    name: '',
    definition: '',
    domainName: '',
    businessOwner: '',
    dataSteward: '',
    classification: 'Internal' as Classification,
  });

  const resetForm = () =>
    setForm({
      name: '',
      definition: '',
      domainName: '',
      businessOwner: '',
      dataSteward: '',
      classification: 'Internal',
    });

  const handleAdd = async () => {
    if (!form.name.trim()) return;
    const now = new Date().toISOString();
    const me = 'you@contoso.com';
    const ownerUpn = form.businessOwner.trim() || me;
    // Provision the Entra security groups for the new data product / term and
    // seed the Owners group with the business owner.
    let groups = await provisionGroups(form.name.trim());
    groups = groups.map((g) =>
      g.role === 'Owner' ? { ...g, members: [...g.members, ownerUpn] } : g,
    );
    const term: Term = {
      id:
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `local-${Date.now()}`,
      name: form.name.trim(),
      definition: form.definition.trim() || 'No definition provided yet.',
      domainName: form.domainName.trim() || 'Unassigned',
      status: 'Draft',
      submittedBy: me,
      updatedAt: now,
      businessOwner: ownerUpn,
      dataSteward: form.dataSteward.trim() || me,
      classification: form.classification,
      approvals: [],
      groups,
      accessRequests: [],
    };
    setTerms((prev) => [term, ...prev]);
    setAddOpen(false);
    setSelectedId(term.id);
    resetForm();
  };

  const handleLifecycle = (action: LifecycleAction, note?: string) => {
    if (!selectedId) return;
    setTerms((prev) =>
      prev.map((t) =>
        t.id === selectedId ? applyAction(t, action, 'you@contoso.com', note) : t,
      ),
    );
  };

  const handleRequestAccess = async (
    role: AccessRole,
    justification?: string,
  ) => {
    if (!selectedId) return;
    const target = terms.find((t) => t.id === selectedId);
    if (!target) return;
    const template = pickWorkflow(workflows, target);
    const updated = await submitAccessRequest(
      target,
      'you@contoso.com',
      role,
      justification,
      template,
    );
    setTerms((prev) => prev.map((t) => (t.id === selectedId ? updated : t)));
  };

  const handleDecideAccess = async (
    requestId: string,
    decision: 'Approved' | 'Rejected',
    note?: string,
  ) => {
    if (!selectedId) return;
    const target = terms.find((t) => t.id === selectedId);
    if (!target) return;
    const updated = await decideStage(
      target,
      requestId,
      decision,
      'you@contoso.com',
      note,
    );
    setTerms((prev) => prev.map((t) => (t.id === selectedId ? updated : t)));
  };

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await listTerms();
      setTerms(res.terms);
      setSource(res.source);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const stats = useMemo(() => {
    const by = (s: TermStatus) => terms.filter((t) => t.status === s).length;
    return {
      total: terms.length,
      approved: by('Approved'),
      pending: by('Pending'),
      draft: by('Draft'),
    };
  }, [terms]);

  const visibleTerms = useMemo(
    () =>
      statusFilter === 'all'
        ? terms
        : terms.filter((t) => t.status === statusFilter),
    [terms, statusFilter],
  );

  const filterTile = (value: 'all' | 'Approved' | 'Pending' | 'Draft') => ({
    className: mergeClasses(
      styles.statCard,
      styles.statCardButton,
      statusFilter === value && styles.statCardActive,
    ),
    role: 'button' as const,
    tabIndex: 0,
    'aria-pressed': statusFilter === value,
    onClick: () => setStatusFilter(value),
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        setStatusFilter(value);
      }
    },
  });

  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <span className={styles.headerIcon}>
          <BookDatabaseRegular />
        </span>
        <div className={styles.headerTitles}>
          <Title3>Glossary</Title3>
          <Caption1>Microsoft Fabric · Data governance</Caption1>
        </div>
        <span className={styles.rayfinPill}>
          <SparkleRegular />
          Rayfin app
        </span>
        <div className={styles.headerSpacer} />
        <Tooltip
          content={
            source === 'backend'
              ? 'Connected to the Rayfin GraphQL backend'
              : 'Showing local seed data (no backend configured)'
          }
          relationship="label"
        >
          <Badge
            appearance="tint"
            color={source === 'backend' ? 'success' : 'warning'}
            icon={source === 'backend' ? <CloudRegular /> : <PlugDisconnectedRegular />}
          >
            {source === 'backend' ? 'Live backend' : 'Seed data'}
          </Badge>
        </Tooltip>
      </header>

      <div className={styles.breadcrumbBar}>
        <Caption1>Workspace</Caption1>
        <Caption1>/</Caption1>
        <Caption1>Governance</Caption1>
        <Caption1>/</Caption1>
        <Body1>Glossary terms</Body1>
      </div>

      <main className={styles.content}>
        <div className={styles.statsRow}>
          <Card {...filterTile('all')}>
            <Caption1>Total terms</Caption1>
            <span className={styles.statValue}>{stats.total}</span>
          </Card>
          <Card {...filterTile('Approved')}>
            <Caption1>Approved</Caption1>
            <span className={styles.statValue}>{stats.approved}</span>
          </Card>
          <Card {...filterTile('Pending')}>
            <Caption1>Pending approval</Caption1>
            <span className={styles.statValue}>{stats.pending}</span>
          </Card>
          <Card {...filterTile('Draft')}>
            <Caption1>Draft</Caption1>
            <span className={styles.statValue}>{stats.draft}</span>
          </Card>
        </div>

        <Card className={styles.toolbarCard}>
          <div className={styles.toolbarRow}>
            <Button
              appearance="primary"
              icon={<AddRegular />}
              onClick={() => setAddOpen(true)}
            >
              New term
            </Button>
            <Button
              appearance="secondary"
              icon={<SparkleRegular />}
              onClick={() => setChatOpen(true)}
            >
              Ask data agent
            </Button>
            <Button
              appearance="secondary"
              icon={<FlowRegular />}
              onClick={() => setWfEditorOpen(true)}
            >
              Approval workflows
            </Button>
            <div className={styles.headerSpacer} />
            <Button
              appearance="secondary"
              icon={<ArrowSyncRegular />}
              onClick={() => void load()}
            >
              Refresh
            </Button>
          </div>
        </Card>

        {err && (
          <Card>
            <Body1 style={{ color: tokens.colorPaletteRedForeground1 }}>
              {err}
            </Body1>
          </Card>
        )}

        <Card className={styles.gridCard}>
          {loading ? (
            <div className={styles.loading}>
              <Spinner label="Loading terms…" />
            </div>
          ) : (
            <DataGrid
              items={visibleTerms}
              columns={columns}
              getRowId={(item) => item.id}
              sortable
              defaultSortState={{
                sortColumn: 'updatedAt',
                sortDirection: 'descending',
              }}
              focusMode="composite"
            >
              <DataGridHeader className={styles.gridHeader}>
                <DataGridRow>
                  {({ renderHeaderCell }) => (
                    <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>
                  )}
                </DataGridRow>
              </DataGridHeader>
              <DataGridBody<Term>>
                {({ item, rowId }) => (
                  <DataGridRow<Term>
                    key={rowId}
                    onClick={() => setSelectedId(item.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    {({ renderCell }) => (
                      <DataGridCell>{renderCell(item)}</DataGridCell>
                    )}
                  </DataGridRow>
                )}
              </DataGridBody>
            </DataGrid>
          )}
        </Card>

        <Button
          appearance="transparent"
          as="a"
          href="https://learn.microsoft.com/fabric/apps/overview"
          target="_blank"
        >
          About Fabric Apps · Rayfin
        </Button>
      </main>

      <Dialog open={addOpen} onOpenChange={(_, d) => setAddOpen(d.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>New glossary term</DialogTitle>
            <DialogContent
              style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
            >
              <Field label="Term name" required>
                <Input
                  value={form.name}
                  onChange={(_, d) => setForm((f) => ({ ...f, name: d.value }))}
                  placeholder="e.g. Gross Margin"
                />
              </Field>
              <Field label="Definition">
                <Textarea
                  value={form.definition}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, definition: d.value }))
                  }
                  placeholder="Business meaning of this term"
                  rows={3}
                />
              </Field>
              <Field label="Domain">
                <Input
                  value={form.domainName}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, domainName: d.value }))
                  }
                  placeholder="e.g. Sales"
                />
              </Field>
              <Field label="Business owner">
                <Input
                  value={form.businessOwner}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, businessOwner: d.value }))
                  }
                  placeholder="accountable owner, e.g. dana@contoso.com"
                />
              </Field>
              <Field label="Data steward">
                <Input
                  value={form.dataSteward}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, dataSteward: d.value }))
                  }
                  placeholder="responsible steward, e.g. avery@contoso.com"
                />
              </Field>
              <Field
                label="Classification"
                hint="New terms start as Draft — submit for review from the detail panel."
              >
                <Dropdown
                  value={form.classification}
                  selectedOptions={[form.classification]}
                  onOptionSelect={(_, d) =>
                    setForm((f) => ({
                      ...f,
                      classification:
                        (d.optionValue as Classification) ?? 'Internal',
                    }))
                  }
                >
                  <Option value="Public">Public</Option>
                  <Option value="Internal">Internal</Option>
                  <Option value="Confidential">Confidential</Option>
                  <Option value="Highly Confidential">Highly Confidential</Option>
                  <Option value="PII">PII</Option>
                </Dropdown>
              </Field>
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button appearance="secondary">Cancel</Button>
              </DialogTrigger>
              <Button
                appearance="primary"
                disabled={!form.name.trim()}
                onClick={handleAdd}
              >
                Add term
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      <TermDetail
        term={terms.find((t) => t.id === selectedId) ?? null}
        open={selectedId != null}
        onClose={() => setSelectedId(null)}
        onAction={handleLifecycle}
        onRequestAccess={handleRequestAccess}
        onDecideAccess={handleDecideAccess}
        workflows={workflows}
      />

      <WorkflowEditor
        open={wfEditorOpen}
        onClose={() => setWfEditorOpen(false)}
        templates={workflows}
        onChange={setWorkflows}
      />

      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        title="Glossary data agent"
        subtitle="Ask about terms, statuses, owners, and domains"
        suggestions={[
          'How many terms are pending?',
          'What does Net Revenue mean?',
          'List approved terms',
          'Show terms in the Sales domain',
        ]}
        onAsk={(q) => askAgent(q, terms)}
      />
    </div>
  );
}
