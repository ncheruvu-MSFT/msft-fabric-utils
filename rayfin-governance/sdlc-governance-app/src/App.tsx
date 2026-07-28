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
  Link,
  Spinner,
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
  ArrowSyncRegular,
  CheckmarkCircleRegular,
  CloudRegular,
  PlugDisconnectedRegular,
  ShieldTaskRegular,
  SparkleRegular,
} from '@fluentui/react-icons';
import { HEADER_GRADIENT } from './theme';
import {
  AttestationResult,
  AttestationRun,
  listAttestationRuns,
} from './dataClient';
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

const resultAppearance: Record<
  AttestationResult,
  'success' | 'warning' | 'danger'
> = {
  Pass: 'success',
  Warning: 'warning',
  Fail: 'danger',
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const columns: TableColumnDefinition<AttestationRun>[] = [
  createTableColumn<AttestationRun>({
    columnId: 'workspaceId',
    compare: (a, b) => a.workspaceId.localeCompare(b.workspaceId),
    renderHeaderCell: () => 'Workspace',
    renderCell: (item) => (
      <TableCellLayout media={<ShieldTaskRegular />}>
        <strong>{item.workspaceId}</strong>
      </TableCellLayout>
    ),
  }),
  createTableColumn<AttestationRun>({
    columnId: 'policyName',
    compare: (a, b) => a.policyName.localeCompare(b.policyName),
    renderHeaderCell: () => 'Policy',
    renderCell: (item) => <TableCellLayout>{item.policyName}</TableCellLayout>,
  }),
  createTableColumn<AttestationRun>({
    columnId: 'result',
    compare: (a, b) => a.result.localeCompare(b.result),
    renderHeaderCell: () => 'Result',
    renderCell: (item) => (
      <Badge appearance="filled" color={resultAppearance[item.result]}>
        {item.result}
      </Badge>
    ),
  }),
  createTableColumn<AttestationRun>({
    columnId: 'commitSha',
    compare: (a, b) => a.commitSha.localeCompare(b.commitSha),
    renderHeaderCell: () => 'Commit',
    renderCell: (item) => (
      <TableCellLayout>
        <code>{item.commitSha}</code>
      </TableCellLayout>
    ),
  }),
  createTableColumn<AttestationRun>({
    columnId: 'pipelineRunUrl',
    renderHeaderCell: () => 'Pipeline run',
    renderCell: (item) => (
      <TableCellLayout>
        <Link href={item.pipelineRunUrl} target="_blank">
          Open
        </Link>
      </TableCellLayout>
    ),
  }),
  createTableColumn<AttestationRun>({
    columnId: 'runAt',
    compare: (a, b) =>
      new Date(a.runAt).getTime() - new Date(b.runAt).getTime(),
    renderHeaderCell: () => 'Ran at',
    renderCell: (item) => (
      <TableCellLayout>{formatDateTime(item.runAt)}</TableCellLayout>
    ),
  }),
];

export function App() {
  const styles = useStyles();
  const [runs, setRuns] = useState<AttestationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<'backend' | 'seed'>('seed');
  const [err, setErr] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<
    'all' | 'Pass' | 'Warning' | 'Fail'
  >('all');

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await listAttestationRuns();
      setRuns(res.runs);
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
    const by = (r: AttestationResult) =>
      runs.filter((x) => x.result === r).length;
    return {
      total: runs.length,
      pass: by('Pass'),
      warning: by('Warning'),
      fail: by('Fail'),
    };
  }, [runs]);

  const visibleRuns = useMemo(
    () =>
      statusFilter === 'all'
        ? runs
        : runs.filter((x) => x.result === statusFilter),
    [runs, statusFilter],
  );

  const filterTile = (value: 'all' | 'Pass' | 'Warning' | 'Fail') => ({
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
          <CheckmarkCircleRegular />
        </span>
        <div className={styles.headerTitles}>
          <Title3>SDLC Governance</Title3>
          <Caption1>Microsoft Fabric · Policy attestation</Caption1>
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
        <Body1>Attestation runs</Body1>
      </div>

      <main className={styles.content}>
        <div className={styles.statsRow}>
          <Card {...filterTile('all')}>
            <Caption1>Total runs</Caption1>
            <span className={styles.statValue}>{stats.total}</span>
          </Card>
          <Card {...filterTile('Pass')}>
            <Caption1>Passing</Caption1>
            <span className={styles.statValue}>{stats.pass}</span>
          </Card>
          <Card {...filterTile('Warning')}>
            <Caption1>Warnings</Caption1>
            <span className={styles.statValue}>{stats.warning}</span>
          </Card>
          <Card {...filterTile('Fail')}>
            <Caption1>Failing</Caption1>
            <span className={styles.statValue}>{stats.fail}</span>
          </Card>
        </div>

        <Card className={styles.toolbarCard}>
          <div className={styles.toolbarRow}>
            <Button
              appearance="primary"
              icon={<ArrowSyncRegular />}
              onClick={() => void load()}
            >
              Refresh
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
              as="a"
              href="https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration"
              target="_blank"
            >
              CI/CD docs
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
              <Spinner label="Loading attestation runs…" />
            </div>
          ) : (
            <DataGrid
              items={visibleRuns}
              columns={columns}
              getRowId={(item) => item.id}
              sortable
              defaultSortState={{
                sortColumn: 'runAt',
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
              <DataGridBody<AttestationRun>>
                {({ item, rowId }) => (
                  <DataGridRow<AttestationRun> key={rowId}>
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

      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        title="SDLC governance agent"
        subtitle="Ask about attestation results, policies, and workspaces"
        suggestions={[
          'Which workspaces are failing?',
          'How many runs passed?',
          'Show warnings',
          'Runs for domain-ownership-required',
        ]}
        onAsk={(q) => askAgent(q, runs)}
      />
    </div>
  );
}
