// Thin data client for the lineage-app frontend.
//
// In a deployed Fabric app the Rayfin backend exposes a GraphQL endpoint at
// `${VITE_RAYFIN_API_URL}/api/graphql`. This client posts GraphQL there when an
// API URL is configured, and otherwise returns local seed data so the UI builds
// and runs without the preview backend.
//
// The entity contract lives in `rayfin/data/lineage_edge.ts`. These rows mirror
// the `LineageEdge` shape emitted by the Python harvesters in
// `fabric-lineage-graph/common/schema.py`.

export type ProcessCategory =
  | 'ADF'
  | 'T-SQL'
  | 'Power BI'
  | 'Spark'
  | 'Pipeline'
  | 'Dataflow'
  | 'Other';

export interface LineageEdge {
  id: string;
  sourceQname: string;
  sourceType: string;
  targetQname: string;
  targetType: string;
  processName: string;
  processType: string;
  artifactRef: string;
  harvestedAt: string;
}

const API_URL = import.meta.env.VITE_RAYFIN_API_URL;

/** Map a raw process_type to a friendly category used for grouping + colour. */
export function categorize(processType: string): ProcessCategory {
  const p = processType.toLowerCase();
  if (p.startsWith('adf')) return 'ADF';
  if (p.startsWith('tsql')) return 'T-SQL';
  if (p.startsWith('pbi')) return 'Power BI';
  if (p.startsWith('spark')) return 'Spark';
  if (p.startsWith('dataflow')) return 'Dataflow';
  if (p.includes('pipeline')) return 'Pipeline';
  return 'Other';
}

/** Short, human-friendly name for a qualified name (last path segment). */
export function shortName(qname: string): string {
  const trimmed = qname.replace(/\/+$/, '');
  const seg = trimmed.split(/[/:]/).filter(Boolean).pop();
  return seg ?? qname;
}

const SEED: LineageEdge[] = [
  {
    id: '1',
    sourceQname: 'mssql://prod-sql/sales/dbo/Customers',
    sourceType: 'azure_sql_table',
    targetQname: 'fabric://lakehouse/silver/customers',
    targetType: 'fabric_lakehouse_table',
    processName: 'adf:CopyCustomers',
    processType: 'adf_copy',
    artifactRef: 'adf/pipelines/ingest_sales.json',
    harvestedAt: '2026-06-14T02:10:00Z',
  },
  {
    id: '2',
    sourceQname: 'mssql://prod-sql/sales/dbo/Orders',
    sourceType: 'azure_sql_table',
    targetQname: 'fabric://lakehouse/silver/orders',
    targetType: 'fabric_lakehouse_table',
    processName: 'adf:CopyOrders',
    processType: 'adf_copy',
    artifactRef: 'adf/pipelines/ingest_sales.json',
    harvestedAt: '2026-06-14T02:11:00Z',
  },
  {
    id: '3',
    sourceQname: 'fabric://lakehouse/silver/customers',
    sourceType: 'fabric_lakehouse_table',
    targetQname: 'fabric://lakehouse/gold/dim_customer',
    targetType: 'fabric_lakehouse_table',
    processName: 'spark:build_dim_customer',
    processType: 'spark_write',
    artifactRef: 'notebooks/build_gold.ipynb',
    harvestedAt: '2026-06-14T03:05:00Z',
  },
  {
    id: '4',
    sourceQname: 'fabric://lakehouse/silver/orders',
    sourceType: 'fabric_lakehouse_table',
    targetQname: 'fabric://warehouse/gold/fact_sales',
    targetType: 'fabric_warehouse_table',
    processName: 'tsql:proc_load_fact_sales',
    processType: 'tsql_insert',
    artifactRef: 'warehouse/procs/load_fact_sales.sql',
    harvestedAt: '2026-06-14T03:20:00Z',
  },
  {
    id: '5',
    sourceQname: 'fabric://lakehouse/gold/dim_customer',
    sourceType: 'fabric_lakehouse_table',
    targetQname: 'powerbi://dataset/Sales Analytics',
    targetType: 'powerbi_dataset',
    processName: 'pbi:m:DimCustomer',
    processType: 'pbi_m_step',
    artifactRef: 'powerbi/Sales Analytics.pbix',
    harvestedAt: '2026-06-14T04:02:00Z',
  },
  {
    id: '6',
    sourceQname: 'fabric://warehouse/gold/fact_sales',
    sourceType: 'fabric_warehouse_table',
    targetQname: 'powerbi://dataset/Sales Analytics',
    targetType: 'powerbi_dataset',
    processName: 'pbi:m:FactSales',
    processType: 'pbi_m_step',
    artifactRef: 'powerbi/Sales Analytics.pbix',
    harvestedAt: '2026-06-14T04:03:00Z',
  },
  {
    id: '7',
    sourceQname: 'powerbi://dataset/Sales Analytics',
    sourceType: 'powerbi_dataset',
    targetQname: 'powerbi://report/Exec Sales Dashboard',
    targetType: 'powerbi_report',
    processName: 'pbi:Net Revenue',
    processType: 'pbi_dax_measure',
    artifactRef: 'powerbi/Exec Sales Dashboard.pbix',
    harvestedAt: '2026-06-14T04:10:00Z',
  },
  {
    id: '8',
    sourceQname: 'fabric://dataflow/Clean Telemetry',
    sourceType: 'fabric_dataflow_gen2',
    targetQname: 'fabric://lakehouse/silver/clickstream',
    targetType: 'fabric_lakehouse_table',
    processName: 'df2:CleanEvents',
    processType: 'dataflow_gen2_step',
    artifactRef: 'dataflows/Clean Telemetry.json',
    harvestedAt: '2026-06-14T02:40:00Z',
  },
];

const LIST_QUERY = `
  query LineageEdges {
    lineageEdges {
      id
      sourceQname
      sourceType
      targetQname
      targetType
      processName
      processType
      artifactRef
      harvestedAt
    }
  }
`;

export interface DataClientResult {
  edges: LineageEdge[];
  source: 'backend' | 'seed';
}

export async function listEdges(): Promise<DataClientResult> {
  if (!API_URL) {
    return { edges: SEED, source: 'seed' };
  }
  // When a backend URL is configured we try it first, but fall back to the
  // seed examples if it is unreachable (e.g. the static page lacks the auth /
  // CORS context for the Rayfin data-plane). This keeps the summary populated
  // instead of surfacing a "Failed to fetch" error.
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
      data?: { lineageEdges?: LineageEdge[] };
      errors?: unknown;
    };
    if (json.errors) {
      throw new Error(JSON.stringify(json.errors));
    }
    const edges = json.data?.lineageEdges ?? [];
    // An empty backend (freshly provisioned schema) still shows the examples so
    // the dashboard is not blank.
    if (edges.length === 0) {
      return { edges: SEED, source: 'seed' };
    }
    return { edges, source: 'backend' };
  } catch {
    return { edges: SEED, source: 'seed' };
  }
}
