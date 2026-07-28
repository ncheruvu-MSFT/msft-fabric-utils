import { useCallback, useEffect, useMemo, useState } from 'react';
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
  Field,
  Input,
  Spinner,
  Tab,
  TabList,
  TableCellLayout,
  TableColumnDefinition,
  Title3,
  Tooltip,
  createTableColumn,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  AddRegular,
  ArrowRightRegular,
  ArrowSyncRegular,
  BranchRegular,
  CloudRegular,
  DatabaseRegular,
  PlugDisconnectedRegular,
  SparkleRegular,
} from '@fluentui/react-icons';
import { HEADER_GRADIENT } from './theme';
import {
  LineageEdge,
  ProcessCategory,
  categorize,
  listEdges,
  shortName,
} from './dataClient';
import { askAgent } from './agentClient';
import { ChatPanel } from './ChatPanel';
import { ColumnGraph, loadColumnGraph } from './columnLineage';
import { LineageGraph } from './LineageGraph';

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
  toolbarRow: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
    flexWrap: 'wrap',
  },
  gridHeader: {
    backgroundColor: tokens.colorNeutralBackground3,
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
  flowCell: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('6px'),
  },
  arrow: {
    color: tokens.colorNeutralForeground3,
    display: 'flex',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.padding('48px'),
  },
});

const categoryAppearance: Record<
  ProcessCategory,
  'brand' | 'danger' | 'important' | 'informative' | 'severe' | 'subtle' | 'success' | 'warning'
> = {
  ADF: 'informative',
  'T-SQL': 'brand',
  'Power BI': 'warning',
  Spark: 'severe',
  Pipeline: 'success',
  Dataflow: 'important',
  Other: 'subtle',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function AssetCell({ qname, type }: { qname: string; type: string }) {
  return (
    <TableCellLayout media={<DatabaseRegular />}>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <strong>{shortName(qname)}</strong>
        <Caption1>{type}</Caption1>
      </div>
    </TableCellLayout>
  );
}

const columns: TableColumnDefinition<LineageEdge>[] = [
  createTableColumn<LineageEdge>({
    columnId: 'source',
    compare: (a, b) => a.sourceQname.localeCompare(b.sourceQname),
    renderHeaderCell: () => 'Source',
    renderCell: (item) => (
      <AssetCell qname={item.sourceQname} type={item.sourceType} />
    ),
  }),
  createTableColumn<LineageEdge>({
    columnId: 'flow',
    renderHeaderCell: () => '',
    renderCell: () => (
      <TableCellLayout>
        <ArrowRightRegular />
      </TableCellLayout>
    ),
  }),
  createTableColumn<LineageEdge>({
    columnId: 'target',
    compare: (a, b) => a.targetQname.localeCompare(b.targetQname),
    renderHeaderCell: () => 'Target',
    renderCell: (item) => (
      <AssetCell qname={item.targetQname} type={item.targetType} />
    ),
  }),
  createTableColumn<LineageEdge>({
    columnId: 'process',
    compare: (a, b) => a.processName.localeCompare(b.processName),
    renderHeaderCell: () => 'Process',
    renderCell: (item) => {
      const cat = categorize(item.processType);
      return (
        <TableCellLayout>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Badge appearance="filled" color={categoryAppearance[cat]}>
              {cat}
            </Badge>
            <Caption1>{item.processName}</Caption1>
          </div>
        </TableCellLayout>
      );
    },
  }),
  createTableColumn<LineageEdge>({
    columnId: 'harvestedAt',
    compare: (a, b) =>
      new Date(a.harvestedAt).getTime() - new Date(b.harvestedAt).getTime(),
    renderHeaderCell: () => 'Harvested',
    renderCell: (item) => (
      <TableCellLayout>{formatDate(item.harvestedAt)}</TableCellLayout>
    ),
  }),
];

export function App() {
  const styles = useStyles();
  const [edges, setEdges] = useState<LineageEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<'backend' | 'seed'>('seed');
  const [err, setErr] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [view, setView] = useState<'edges' | 'graph'>('edges');
  const [columnGraph, setColumnGraph] = useState<ColumnGraph | null>(null);
  const [columnSource, setColumnSource] = useState<'scanned' | 'demo'>('demo');
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({
    sourceQname: '',
    sourceType: '',
    targetQname: '',
    targetType: '',
    processName: '',
    processType: '',
  });

  const resetForm = () =>
    setForm({
      sourceQname: '',
      sourceType: '',
      targetQname: '',
      targetType: '',
      processName: '',
      processType: '',
    });

  const handleAdd = () => {
    if (!form.sourceQname.trim() || !form.targetQname.trim()) return;
    const edge: LineageEdge = {
      id:
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `local-${Date.now()}`,
      sourceQname: form.sourceQname.trim(),
      sourceType: form.sourceType.trim() || 'unknown',
      targetQname: form.targetQname.trim(),
      targetType: form.targetType.trim() || 'unknown',
      processName: form.processName.trim() || 'manual:edge',
      processType: form.processType.trim() || 'manual',
      artifactRef: 'manual-entry',
      harvestedAt: new Date().toISOString(),
    };
    setEdges((prev) => [edge, ...prev]);
    setAddOpen(false);
    resetForm();
  };

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await listEdges();
      setEdges(res.edges);
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

  useEffect(() => {
    void loadColumnGraph().then(({ graph, source }) => {
      setColumnGraph(graph);
      setColumnSource(source);
    });
  }, []);

  const stats = useMemo(() => {
    const assets = new Set<string>();
    const processes = new Set<string>();
    const sources = new Set<string>();
    const targets = new Set<string>();
    for (const e of edges) {
      assets.add(e.sourceQname);
      assets.add(e.targetQname);
      processes.add(e.processName);
      sources.add(e.sourceQname);
      targets.add(e.targetQname);
    }
    const roots = [...sources].filter((s) => !targets.has(s)).length;
    return {
      total: edges.length,
      assets: assets.size,
      processes: processes.size,
      roots,
    };
  }, [edges]);

  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <span className={styles.headerIcon}>
          <BranchRegular />
        </span>
        <div className={styles.headerTitles}>
          <Title3>Lineage Graph</Title3>
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
        <Body1>Lineage edges</Body1>
      </div>

      <main className={styles.content}>
        <div className={styles.statsRow}>
          <Card className={styles.statCard}>
            <Caption1>Lineage edges</Caption1>
            <span className={styles.statValue}>{stats.total}</span>
          </Card>
          <Card className={styles.statCard}>
            <Caption1>Data assets</Caption1>
            <span className={styles.statValue}>{stats.assets}</span>
          </Card>
          <Card className={styles.statCard}>
            <Caption1>Processes</Caption1>
            <span className={styles.statValue}>{stats.processes}</span>
          </Card>
          <Card className={styles.statCard}>
            <Caption1>Source roots</Caption1>
            <span className={styles.statValue}>{stats.roots}</span>
          </Card>
        </div>

        <Card className={styles.toolbarCard}>
          <div className={styles.toolbarRow}>
            <Button
              appearance="primary"
              icon={<AddRegular />}
              onClick={() => setAddOpen(true)}
            >
              Add edge
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

        <TabList
          selectedValue={view}
          onTabSelect={(_, d) => setView(d.value as 'edges' | 'graph')}
        >
          <Tab value="edges" icon={<ArrowRightRegular />}>
            Lineage edges
          </Tab>
          <Tab value="graph" icon={<BranchRegular />}>
            Column graph
          </Tab>
        </TabList>

        {view === 'edges' ? (
          <Card className={styles.gridCard}>
            {loading ? (
              <div className={styles.loading}>
                <Spinner label="Loading lineage…" />
              </div>
            ) : (
              <DataGrid
                items={edges}
                columns={columns}
                getRowId={(item) => item.id}
                sortable
                defaultSortState={{
                  sortColumn: 'harvestedAt',
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
                <DataGridBody<LineageEdge>>
                  {({ item, rowId }) => (
                    <DataGridRow<LineageEdge> key={rowId}>
                      {({ renderCell }) => (
                        <DataGridCell>{renderCell(item)}</DataGridCell>
                      )}
                    </DataGridRow>
                  )}
                </DataGridBody>
              </DataGrid>
            )}
          </Card>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Tooltip
                content={
                  columnSource === 'scanned'
                    ? 'Column lineage scanned from notebooks / SQL / Python code'
                    : 'Demo column lineage — run the repo scanner to load real edges'
                }
                relationship="label"
              >
                <Badge
                  appearance="tint"
                  color={columnSource === 'scanned' ? 'success' : 'warning'}
                  icon={columnSource === 'scanned' ? <BranchRegular /> : <PlugDisconnectedRegular />}
                >
                  {columnSource === 'scanned' ? 'Scanned from code' : 'Demo column data'}
                </Badge>
              </Tooltip>
              <Caption1>
                Click any column to trace its upstream origins and downstream consumers.
              </Caption1>
            </div>
            {columnGraph ? (
              <LineageGraph graph={columnGraph} />
            ) : (
              <div className={styles.loading}>
                <Spinner label="Loading column lineage…" />
              </div>
            )}
          </>
        )}

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
            <DialogTitle>Add lineage edge</DialogTitle>
            <DialogContent
              style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
            >
              <Field label="Source qualified name" required>
                <Input
                  value={form.sourceQname}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, sourceQname: d.value }))
                  }
                  placeholder="mssql://prod-sql/sales/dbo/Customers"
                />
              </Field>
              <Field label="Source type">
                <Input
                  value={form.sourceType}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, sourceType: d.value }))
                  }
                  placeholder="azure_sql_table"
                />
              </Field>
              <Field label="Target qualified name" required>
                <Input
                  value={form.targetQname}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, targetQname: d.value }))
                  }
                  placeholder="fabric://lakehouse/silver/customers"
                />
              </Field>
              <Field label="Target type">
                <Input
                  value={form.targetType}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, targetType: d.value }))
                  }
                  placeholder="fabric_lakehouse_table"
                />
              </Field>
              <Field label="Process name">
                <Input
                  value={form.processName}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, processName: d.value }))
                  }
                  placeholder="adf:CopyCustomers"
                />
              </Field>
              <Field
                label="Process type"
                hint="adf_*, tsql_*, spark_*, pbi_*, dataflow_* or pipeline"
              >
                <Input
                  value={form.processType}
                  onChange={(_, d) =>
                    setForm((f) => ({ ...f, processType: d.value }))
                  }
                  placeholder="adf_copy"
                />
              </Field>
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button appearance="secondary">Cancel</Button>
              </DialogTrigger>
              <Button
                appearance="primary"
                disabled={!form.sourceQname.trim() || !form.targetQname.trim()}
                onClick={handleAdd}
              >
                Add edge
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        title="Lineage data agent"
        subtitle="Ask about upstream/downstream lineage, assets, and processes"
        suggestions={[
          'What feeds fact_sales?',
          'What is downstream of Customers?',
          'How many ADF edges are there?',
          'List Power BI edges',
        ]}
        onAsk={(q) => askAgent(q, edges)}
      />
    </div>
  );
}
