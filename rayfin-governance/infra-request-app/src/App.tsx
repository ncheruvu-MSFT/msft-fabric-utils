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
  Dropdown,
  Field,
  Input,
  Link,
  Option,
  Spinner,
  TableCellLayout,
  TableColumnDefinition,
  Textarea,
  Title3,
  Toolbar,
  ToolbarButton,
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
  CheckmarkCircleRegular,
  CloudRegular,
  DatabaseRegular,
  DismissCircleRegular,
  PlugDisconnectedRegular,
  RocketRegular,
  SparkleRegular,
} from '@fluentui/react-icons';
import { HEADER_GRADIENT } from './theme';
import {
  InfraRequest,
  NewInfraRequest,
  RequestStatus,
  RequestType,
  createInfraRequest,
  listInfraRequests,
  setRequestStatus,
} from './dataClient';

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
  identityField: { minWidth: '220px' },
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
  statsRow: { display: 'flex', ...shorthands.gap('12px'), flexWrap: 'wrap' },
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
  gridHeader: {
    backgroundColor: tokens.colorNeutralBackground3,
  },
  formCard: {
    ...shorthands.padding('20px', '24px'),
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('16px'),
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    ...shorthands.gap('16px'),
  },
  formActions: { display: 'flex', ...shorthands.gap('8px'), alignItems: 'center' },
  gridCard: { ...shorthands.padding('0'), ...shorthands.overflow('hidden'), boxShadow: tokens.shadow8 },
  rowActions: { display: 'flex', ...shorthands.gap('4px') },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.padding('48px'),
  },
  banner: { ...shorthands.padding('12px', '16px') },
});

const statusColor: Record<RequestStatus, 'success' | 'warning' | 'danger' | 'brand' | 'informative'> = {
  Pending: 'warning',
  Approved: 'brand',
  Rejected: 'danger',
  Submitted: 'informative',
  Completed: 'success',
};

const ENVIRONMENTS = ['dev', 'test', 'prod'];
const CAPACITY_SKUS = ['F2', 'F4', 'F8', 'F16', 'F32', 'F64', 'F128', 'F256'];
const REGIONS = ['westus2', 'eastus2', 'centralus', 'westeurope', 'northeurope', 'canadacentral'];

function formatDateTime(iso?: string): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface FormState {
  requestType: RequestType;
  displayName: string;
  environment: string;
  domain: string;
  capacitySku: string;
  region: string;
  targetCapacity: string;
  costCenter: string;
  justification: string;
}

const EMPTY_FORM: FormState = {
  requestType: 'Capacity',
  displayName: '',
  environment: 'dev',
  domain: '',
  capacitySku: 'F8',
  region: 'westus2',
  targetCapacity: '',
  costCenter: '',
  justification: '',
};

export function App() {
  const styles = useStyles();
  const [requests, setRequests] = useState<InfraRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<'backend' | 'seed'>('seed');
  const [err, setErr] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  // In a deployed Fabric app the session provides claims.sub; here the identity
  // is captured so the scaffold can stamp ownerSub / approverSub.
  const [identity, setIdentity] = useState('you@contoso.com');
  const [statusFilter, setStatusFilter] = useState<'all' | RequestStatus>(
    'all',
  );

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await listInfraRequests();
      setRequests(res.requests);
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
    const by = (s: RequestStatus) => requests.filter((r) => r.status === s).length;
    return {
      pending: by('Pending'),
      approved: by('Approved'),
      submitted: by('Submitted'),
      rejected: by('Rejected'),
    };
  }, [requests]);

  const visibleRequests = useMemo(
    () =>
      statusFilter === 'all'
        ? requests
        : requests.filter((r) => r.status === statusFilter),
    [requests, statusFilter],
  );

  const filterTile = (value: RequestStatus) => ({
    className: mergeClasses(
      styles.statCard,
      styles.statCardButton,
      statusFilter === value && styles.statCardActive,
    ),
    role: 'button' as const,
    tabIndex: 0,
    'aria-pressed': statusFilter === value,
    onClick: () => setStatusFilter((prev) => (prev === value ? 'all' : value)),
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        setStatusFilter((prev) => (prev === value ? 'all' : value));
      }
    },
  });

  const isCapacity = form.requestType === 'Capacity';
  const canSubmit =
    form.displayName.trim().length > 0 &&
    form.justification.trim().length > 0 &&
    (isCapacity ? !!form.capacitySku && !!form.region : form.targetCapacity.trim().length > 0);

  const onSubmit = useCallback(async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setErr(null);
    setNotice(null);
    try {
      const payload: NewInfraRequest = {
        requestType: form.requestType,
        displayName: form.displayName.trim(),
        environment: form.environment,
        justification: form.justification.trim(),
        domain: form.domain.trim() || undefined,
        costCenter: form.costCenter.trim() || undefined,
        ...(isCapacity
          ? { capacitySku: form.capacitySku, region: form.region }
          : { targetCapacity: form.targetCapacity.trim() }),
      };
      await createInfraRequest(payload, identity.trim() || 'unknown');
      setForm({ ...EMPTY_FORM, requestType: form.requestType });
      setNotice('Request submitted. It is now Pending approval.');
      await load();
    } catch (e) {
      setErr(String(e));
    } finally {
      setSubmitting(false);
    }
  }, [canSubmit, form, identity, isCapacity, load]);

  const onDecision = useCallback(
    async (id: string, decision: 'Approved' | 'Rejected') => {
      setErr(null);
      setNotice(null);
      try {
        await setRequestStatus(id, decision, identity.trim() || 'unknown');
        setNotice(
          decision === 'Approved'
            ? 'Approved. The provisioning workflow will open a GitHub issue on its next run.'
            : 'Request rejected.',
        );
        await load();
      } catch (e) {
        setErr(String(e));
      }
    },
    [identity, load],
  );

  const columns: TableColumnDefinition<InfraRequest>[] = useMemo(
    () => [
      createTableColumn<InfraRequest>({
        columnId: 'displayName',
        compare: (a, b) => a.displayName.localeCompare(b.displayName),
        renderHeaderCell: () => 'Request',
        renderCell: (item) => (
          <TableCellLayout
            media={item.requestType === 'Capacity' ? <DatabaseRegular /> : <CloudRegular />}
          >
            <div>
              <strong>{item.displayName}</strong>
              <Caption1 block>
                {item.requestType} · {item.environment}
                {item.domain ? ` · ${item.domain}` : ''}
              </Caption1>
            </div>
          </TableCellLayout>
        ),
      }),
      createTableColumn<InfraRequest>({
        columnId: 'spec',
        renderHeaderCell: () => 'Spec',
        renderCell: (item) => (
          <TableCellLayout>
            {item.requestType === 'Capacity'
              ? `${item.capacitySku ?? '—'} · ${item.region ?? '—'}`
              : item.targetCapacity ?? '—'}
          </TableCellLayout>
        ),
      }),
      createTableColumn<InfraRequest>({
        columnId: 'status',
        compare: (a, b) => a.status.localeCompare(b.status),
        renderHeaderCell: () => 'Status',
        renderCell: (item) => (
          <Badge appearance="filled" color={statusColor[item.status]}>
            {item.status}
          </Badge>
        ),
      }),
      createTableColumn<InfraRequest>({
        columnId: 'github',
        renderHeaderCell: () => 'GitHub',
        renderCell: (item) =>
          item.githubIssueUrl ? (
            <TableCellLayout>
              <Link href={item.githubIssueUrl} target="_blank">
                #{item.githubIssueNumber ?? 'issue'}
              </Link>
            </TableCellLayout>
          ) : (
            <TableCellLayout>—</TableCellLayout>
          ),
      }),
      createTableColumn<InfraRequest>({
        columnId: 'requestedBy',
        compare: (a, b) =>
          new Date(a.auditCreatedAt).getTime() -
          new Date(b.auditCreatedAt).getTime(),
        renderHeaderCell: () => 'Requested',
        renderCell: (item) => (
          <TableCellLayout>
            <div>
              {item.ownerSub}
              <Caption1 block>{formatDateTime(item.auditCreatedAt)}</Caption1>
            </div>
          </TableCellLayout>
        ),
      }),
      createTableColumn<InfraRequest>({
        columnId: 'actions',
        renderHeaderCell: () => 'Actions',
        renderCell: (item) =>
          item.status === 'Pending' ? (
            <div className={styles.rowActions}>
              <Tooltip content="Approve" relationship="label">
                <Button
                  size="small"
                  appearance="primary"
                  icon={<CheckmarkCircleRegular />}
                  onClick={() => void onDecision(item.id, 'Approved')}
                >
                  Approve
                </Button>
              </Tooltip>
              <Tooltip content="Reject" relationship="label">
                <Button
                  size="small"
                  icon={<DismissCircleRegular />}
                  onClick={() => void onDecision(item.id, 'Rejected')}
                >
                  Reject
                </Button>
              </Tooltip>
            </div>
          ) : (
            <Caption1>{item.approverSub ?? '—'}</Caption1>
          ),
      }),
    ],
    [onDecision, styles.rowActions],
  );

  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <span className={styles.headerIcon}>
          <RocketRegular />
        </span>
        <div className={styles.headerTitles}>
          <Title3>Infra Request</Title3>
          <Caption1>Microsoft Fabric · Capacity &amp; Workspace provisioning</Caption1>
        </div>
        <span className={styles.rayfinPill}>
          <SparkleRegular />
          Rayfin app
        </span>
        <div className={styles.headerSpacer} />
        <Field className={styles.identityField}>
          <Input
            value={identity}
            onChange={(_, d) => setIdentity(d.value)}
            placeholder="you@contoso.com"
            aria-label="Your identity"
          />
        </Field>
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

      <main className={styles.content}>
        <div className={styles.statsRow}>
          <Card {...filterTile('Pending')}>
            <Caption1>Pending</Caption1>
            <span className={styles.statValue}>{stats.pending}</span>
          </Card>
          <Card {...filterTile('Approved')}>
            <Caption1>Approved</Caption1>
            <span className={styles.statValue}>{stats.approved}</span>
          </Card>
          <Card {...filterTile('Submitted')}>
            <Caption1>Submitted to GitHub</Caption1>
            <span className={styles.statValue}>{stats.submitted}</span>
          </Card>
          <Card {...filterTile('Rejected')}>
            <Caption1>Rejected</Caption1>
            <span className={styles.statValue}>{stats.rejected}</span>
          </Card>
        </div>

        <Card className={styles.formCard}>
          <Title3>New infrastructure request</Title3>
          <div className={styles.formGrid}>
            <Field label="Request type" required>
              <Dropdown
                value={form.requestType}
                selectedOptions={[form.requestType]}
                onOptionSelect={(_, d) =>
                  setForm((f) => ({ ...f, requestType: d.optionValue as RequestType }))
                }
              >
                <Option value="Capacity">Capacity</Option>
                <Option value="Workspace">Workspace</Option>
              </Dropdown>
            </Field>

            <Field label={isCapacity ? 'Capacity name' : 'Workspace name'} required>
              <Input
                value={form.displayName}
                onChange={(_, d) => setForm((f) => ({ ...f, displayName: d.value }))}
                placeholder={isCapacity ? 'Contoso-Analytics-prod' : 'Contoso-Sales-dev'}
              />
            </Field>

            <Field label="Environment" required>
              <Dropdown
                value={form.environment}
                selectedOptions={[form.environment]}
                onOptionSelect={(_, d) =>
                  setForm((f) => ({ ...f, environment: d.optionValue as string }))
                }
              >
                {ENVIRONMENTS.map((e) => (
                  <Option key={e} value={e}>
                    {e}
                  </Option>
                ))}
              </Dropdown>
            </Field>

            <Field label="Governance domain">
              <Input
                value={form.domain}
                onChange={(_, d) => setForm((f) => ({ ...f, domain: d.value }))}
                placeholder="retail-sales"
              />
            </Field>

            {isCapacity ? (
              <>
                <Field label="Capacity SKU" required>
                  <Dropdown
                    value={form.capacitySku}
                    selectedOptions={[form.capacitySku]}
                    onOptionSelect={(_, d) =>
                      setForm((f) => ({ ...f, capacitySku: d.optionValue as string }))
                    }
                  >
                    {CAPACITY_SKUS.map((s) => (
                      <Option key={s} value={s}>
                        {s}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
                <Field label="Region" required>
                  <Dropdown
                    value={form.region}
                    selectedOptions={[form.region]}
                    onOptionSelect={(_, d) =>
                      setForm((f) => ({ ...f, region: d.optionValue as string }))
                    }
                  >
                    {REGIONS.map((r) => (
                      <Option key={r} value={r}>
                        {r}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
              </>
            ) : (
              <Field label="Target capacity" required>
                <Input
                  value={form.targetCapacity}
                  onChange={(_, d) => setForm((f) => ({ ...f, targetCapacity: d.value }))}
                  placeholder="Contoso-Shared-dev (F8)"
                />
              </Field>
            )}

            <Field label="Cost center">
              <Input
                value={form.costCenter}
                onChange={(_, d) => setForm((f) => ({ ...f, costCenter: d.value }))}
                placeholder="CC-4821"
              />
            </Field>
          </div>

          <Field label="Justification" required>
            <Textarea
              value={form.justification}
              onChange={(_, d) => setForm((f) => ({ ...f, justification: d.value }))}
              placeholder="Why is this capacity / workspace needed?"
              resize="vertical"
            />
          </Field>

          <div className={styles.formActions}>
            <Button
              appearance="primary"
              icon={<AddRegular />}
              disabled={!canSubmit || submitting}
              onClick={() => void onSubmit()}
            >
              {submitting ? 'Submitting…' : 'Submit request'}
            </Button>
            <Caption1>Submitted requests start as Pending and require approval.</Caption1>
          </div>
        </Card>

        {notice && (
          <Card className={styles.banner}>
            <Body1 style={{ color: tokens.colorPaletteGreenForeground1 }}>{notice}</Body1>
          </Card>
        )}
        {err && (
          <Card className={styles.banner}>
            <Body1 style={{ color: tokens.colorPaletteRedForeground1 }}>{err}</Body1>
          </Card>
        )}

        <Card className={styles.formCard}>
          <Toolbar aria-label="Request actions">
            <ToolbarButton
              appearance="primary"
              icon={<ArrowSyncRegular />}
              onClick={() => void load()}
            >
              Refresh
            </ToolbarButton>
            <ToolbarButton
              as="a"
              href="https://learn.microsoft.com/fabric/admin/capacity-settings"
              target="_blank"
            >
              Capacity docs
            </ToolbarButton>
          </Toolbar>
        </Card>

        <Card className={styles.gridCard}>
          {loading ? (
            <div className={styles.loading}>
              <Spinner label="Loading requests…" />
            </div>
          ) : (
            <DataGrid
              items={visibleRequests}
              columns={columns}
              getRowId={(item) => item.id}
              sortable
              defaultSortState={{
                sortColumn: 'requestedBy',
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
              <DataGridBody<InfraRequest>>
                {({ item, rowId }) => (
                  <DataGridRow<InfraRequest> key={rowId}>
                    {({ renderCell }) => <DataGridCell>{renderCell(item)}</DataGridCell>}
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
    </div>
  );
}
