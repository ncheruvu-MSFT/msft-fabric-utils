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
  Switch,
  TableCellLayout,
  TableColumnDefinition,
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
  BotRegular,
  CloudRegular,
  PersonRegular,
  PlugDisconnectedRegular,
  SparkleRegular,
} from '@fluentui/react-icons';
import { HEADER_GRADIENT } from './theme';
import { Agent, AgentStatus, listAgents } from './dataClient';
import { askAgent } from './agentClient';
import { ChatPanel } from './ChatPanel';

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
  AgentStatus,
  'success' | 'warning' | 'danger' | 'informative'
> = {
  Approved: 'success',
  'In review': 'warning',
  Suspended: 'danger',
  Draft: 'informative',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

const columns: TableColumnDefinition<Agent>[] = [
  createTableColumn<Agent>({
    columnId: 'name',
    compare: (a, b) => a.name.localeCompare(b.name),
    renderHeaderCell: () => 'Agent',
    renderCell: (item) => (
      <TableCellLayout media={<BotRegular />}>
        <strong>{item.name}</strong>
      </TableCellLayout>
    ),
  }),
  createTableColumn<Agent>({
    columnId: 'domain',
    compare: (a, b) => a.domain.localeCompare(b.domain),
    renderHeaderCell: () => 'Domain',
    renderCell: (item) => <TableCellLayout>{item.domain}</TableCellLayout>,
  }),
  createTableColumn<Agent>({
    columnId: 'status',
    compare: (a, b) => a.status.localeCompare(b.status),
    renderHeaderCell: () => 'Status',
    renderCell: (item) => (
      <Badge appearance="filled" color={statusAppearance[item.status]}>
        {item.status}
      </Badge>
    ),
  }),
  createTableColumn<Agent>({
    columnId: 'modelDeployment',
    compare: (a, b) => a.modelDeployment.localeCompare(b.modelDeployment),
    renderHeaderCell: () => 'Model',
    renderCell: (item) => (
      <TableCellLayout>
        <code>{item.modelDeployment}</code>
      </TableCellLayout>
    ),
  }),
  createTableColumn<Agent>({
    columnId: 'requiresHumanApproval',
    renderHeaderCell: () => 'Human approval',
    renderCell: (item) =>
      item.requiresHumanApproval ? (
        <Badge appearance="tint" color="brand" icon={<PersonRegular />}>
          Required
        </Badge>
      ) : (
        <TableCellLayout>—</TableCellLayout>
      ),
  }),
  createTableColumn<Agent>({
    columnId: 'owner',
    compare: (a, b) => a.owner.localeCompare(b.owner),
    renderHeaderCell: () => 'Owner',
    renderCell: (item) => <TableCellLayout>{item.owner}</TableCellLayout>,
  }),
  createTableColumn<Agent>({
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
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<'backend' | 'seed'>('seed');
  const [err, setErr] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<
    'all' | 'Approved' | 'In review' | 'Suspended'
  >('all');
  const [form, setForm] = useState({
    name: '',
    domain: '',
    modelDeployment: '',
    status: 'Draft' as AgentStatus,
    requiresHumanApproval: true,
  });

  const resetForm = () =>
    setForm({
      name: '',
      domain: '',
      modelDeployment: '',
      status: 'Draft',
      requiresHumanApproval: true,
    });

  const handleAdd = () => {
    if (!form.name.trim()) return;
    const agent: Agent = {
      id:
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `local-${Date.now()}`,
      name: form.name.trim(),
      domain: form.domain.trim() || 'Unassigned',
      status: form.status,
      modelDeployment: form.modelDeployment.trim() || 'gpt-4o',
      requiresHumanApproval: form.requiresHumanApproval,
      owner: 'you@contoso.com',
      updatedAt: new Date().toISOString(),
    };
    setAgents((prev) => [agent, ...prev]);
    setAddOpen(false);
    resetForm();
  };

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await listAgents();
      setAgents(res.agents);
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
    const by = (s: AgentStatus) => agents.filter((a) => a.status === s).length;
    return {
      total: agents.length,
      approved: by('Approved'),
      review: by('In review'),
      suspended: by('Suspended'),
    };
  }, [agents]);

  const visibleAgents = useMemo(
    () =>
      statusFilter === 'all'
        ? agents
        : agents.filter((a) => a.status === statusFilter),
    [agents, statusFilter],
  );

  const filterTile = (
    value: 'all' | 'Approved' | 'In review' | 'Suspended',
  ) => ({
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
          <BotRegular />
        </span>
        <div className={styles.headerTitles}>
          <Title3>Data Agent Governance</Title3>
          <Caption1>Microsoft Fabric · Agent registry</Caption1>
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
            icon={
              source === 'backend' ? <CloudRegular /> : <PlugDisconnectedRegular />
            }
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
        <Body1>Data agents</Body1>
      </div>

      <main className={styles.content}>
        <div className={styles.statsRow}>
          <Card {...filterTile('all')}>
            <Caption1>Total agents</Caption1>
            <span className={styles.statValue}>{stats.total}</span>
          </Card>
          <Card {...filterTile('Approved')}>
            <Caption1>Approved</Caption1>
            <span className={styles.statValue}>{stats.approved}</span>
          </Card>
          <Card {...filterTile('In review')}>
            <Caption1>In review</Caption1>
            <span className={styles.statValue}>{stats.review}</span>
          </Card>
          <Card {...filterTile('Suspended')}>
            <Caption1>Suspended</Caption1>
            <span className={styles.statValue}>{stats.suspended}</span>
          </Card>
        </div>

        <Card className={styles.toolbarCard}>
          <div className={styles.toolbarRow}>
            <Button
              appearance="primary"
              icon={<AddRegular />}
              onClick={() => setAddOpen(true)}
            >
              Register agent
            </Button>
            <Button
              appearance="secondary"
              icon={<SparkleRegular />}
              onClick={() => setChatOpen(true)}
            >
              Ask data agent
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
              <Spinner label="Loading agents…" />
            </div>
          ) : (
            <DataGrid
              items={visibleAgents}
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
              <DataGridBody<Agent>>
                {({ item, rowId }) => (
                  <DataGridRow<Agent> key={rowId}>
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
          About Fabric Apps
        </Button>
      </main>

      <Dialog open={addOpen} onOpenChange={(_, d) => setAddOpen(d.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Register data agent</DialogTitle>
            <DialogContent
              style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
            >
              <Field label="Agent name" required>
                <Input
                  value={form.name}
                  onChange={(_, d) => setForm((f) => ({ ...f, name: d.value }))}
                  placeholder="e.g. Finance Insights Copilot"
                />
              </Field>
              <Field label="Domain">
                <Input
                  value={form.domain}
                  onChange={(_, d) => setForm((f) => ({ ...f, domain: d.value }))}
                  placeholder="e.g. Finance"
                />
              </Field>
              <Field label="Model deployment">
                <Input
                  value={form.modelDeployment}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, modelDeployment: d.value }))
                  }
                  placeholder="e.g. gpt-4o"
                />
              </Field>
              <Field label="Status">
                <Dropdown
                  value={form.status}
                  selectedOptions={[form.status]}
                  onOptionSelect={(_, d) =>
                    setForm((f) => ({
                      ...f,
                      status: (d.optionValue as AgentStatus) ?? 'Draft',
                    }))
                  }
                >
                  <Option value="Draft">Draft</Option>
                  <Option value="In review">In review</Option>
                  <Option value="Approved">Approved</Option>
                  <Option value="Suspended">Suspended</Option>
                </Dropdown>
              </Field>
              <Switch
                label="Requires human approval"
                checked={form.requiresHumanApproval}
                onChange={(_, d) =>
                  setForm((f) => ({ ...f, requiresHumanApproval: d.checked }))
                }
              />
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
                Register
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        title="Agent registry agent"
        subtitle="Ask about agents, approvals, models, and domains"
        suggestions={[
          'Which agents need human approval?',
          'How many agents are approved?',
          'Show suspended agents',
          'Agents in the Sales domain',
        ]}
        onAsk={(q) => askAgent(q, agents)}
      />
    </div>
  );
}
