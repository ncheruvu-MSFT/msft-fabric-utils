// Column-level lineage graph model for the lineage-app.
//
// The table-level edges in `dataClient.ts` answer "which asset feeds which".
// This module models the *column*-level lineage underneath that: every column
// of every asset, and the column->column transforms that connect them across
// many layers (source -> bronze -> silver -> gold -> semantic -> report).
//
// Assets are assigned to a level via longest-path leveling so the graph renders
// as clean left-to-right layers. `traceColumn` walks the edges upstream and
// downstream from a clicked column so the UI can highlight the full journey.

export type AssetType =
  | 'source'
  | 'bronze'
  | 'silver'
  | 'gold'
  | 'semantic'
  | 'report';

interface AssetMeta {
  label: string;
  type: AssetType;
}

interface RawColEdge {
  from: string; // "assetId::Column"
  to: string; // "assetId::Column"
  transform: string;
}

const ASSET_META: Record<string, AssetMeta> = {
  src_orders: { label: 'Orders · Azure SQL', type: 'source' },
  src_customers: { label: 'Customers · Azure SQL', type: 'source' },
  bronze_orders: { label: 'bronze.orders_raw', type: 'bronze' },
  bronze_customers: { label: 'bronze.customers_raw', type: 'bronze' },
  silver_stage: { label: 'silver.orders_stage', type: 'silver' },
  silver_clean: { label: 'silver.orders_clean', type: 'silver' },
  silver_typed: { label: 'silver.orders_typed', type: 'silver' },
  silver_valid: { label: 'silver.orders_valid', type: 'silver' },
  silver_cust_clean: { label: 'silver.customers_clean', type: 'silver' },
  silver_cust_dedup: { label: 'silver.customers_dedup', type: 'silver' },
  silver_enriched: { label: 'silver.orders_enriched', type: 'silver' },
  gold_fact: { label: 'gold.fact_sales', type: 'gold' },
  gold_secured: { label: 'gold.fact_sales_secured', type: 'gold' },
  gold_agg: { label: 'gold.agg_sales_region', type: 'gold' },
  semantic_sales: { label: 'Sales · semantic model', type: 'semantic' },
  semantic_measures: { label: 'Sales measures', type: 'semantic' },
  report_exec: { label: 'Exec Sales report', type: 'report' },
  report_kpi: { label: 'Revenue KPI tile', type: 'report' },
};

const RAW_EDGES: RawColEdge[] = [
  // ---- Amount -> GrossAmount -> NetAmount -> Total Revenue ------------------
  { from: 'src_orders::Amount', to: 'bronze_orders::Amount', transform: 'copy' },
  { from: 'bronze_orders::Amount', to: 'silver_stage::Amount', transform: 'ingest' },
  { from: 'silver_stage::Amount', to: 'silver_clean::Amount', transform: 'trim' },
  { from: 'silver_clean::Amount', to: 'silver_typed::AmountDec', transform: 'cast decimal(18,2)' },
  { from: 'silver_typed::AmountDec', to: 'silver_valid::AmountDec', transform: 'filter > 0' },
  { from: 'silver_valid::AmountDec', to: 'silver_enriched::GrossAmount', transform: 'rename' },
  { from: 'silver_enriched::GrossAmount', to: 'gold_fact::GrossAmount', transform: 'load' },
  { from: 'gold_fact::GrossAmount', to: 'gold_fact::NetAmount', transform: 'Gross × (1 − Discount)' },
  { from: 'gold_fact::Discount', to: 'gold_fact::NetAmount', transform: 'Gross × (1 − Discount)' },
  { from: 'gold_fact::NetAmount', to: 'gold_secured::NetAmount', transform: 'RLS view' },
  { from: 'gold_secured::NetAmount', to: 'gold_agg::TotalNet', transform: 'SUM by region' },
  { from: 'gold_agg::TotalNet', to: 'semantic_sales::NetAmount', transform: 'import' },
  { from: 'semantic_sales::NetAmount', to: 'semantic_measures::TotalRevenue', transform: 'SUM(NetAmount)' },
  { from: 'semantic_measures::TotalRevenue', to: 'report_exec::RevenueByRegion', transform: 'column chart' },
  { from: 'report_exec::RevenueByRegion', to: 'report_kpi::RevenueKPI', transform: 'KPI card' },

  // ---- Discount path -------------------------------------------------------
  { from: 'src_orders::Discount', to: 'bronze_orders::Discount', transform: 'copy' },
  { from: 'bronze_orders::Discount', to: 'silver_stage::Discount', transform: 'ingest' },
  { from: 'silver_stage::Discount', to: 'silver_typed::DiscountDec', transform: 'cast decimal(5,4)' },
  { from: 'silver_typed::DiscountDec', to: 'silver_valid::DiscountDec', transform: 'default 0' },
  { from: 'silver_valid::DiscountDec', to: 'silver_enriched::Discount', transform: 'passthrough' },
  { from: 'silver_enriched::Discount', to: 'gold_fact::Discount', transform: 'load' },

  // ---- Quantity -> Total Units --------------------------------------------
  { from: 'src_orders::Qty', to: 'bronze_orders::Qty', transform: 'copy' },
  { from: 'bronze_orders::Qty', to: 'silver_stage::Qty', transform: 'ingest' },
  { from: 'silver_stage::Qty', to: 'silver_typed::QtyInt', transform: 'cast int' },
  { from: 'silver_typed::QtyInt', to: 'silver_valid::QtyInt', transform: 'filter >= 0' },
  { from: 'silver_valid::QtyInt', to: 'silver_enriched::Qty', transform: 'passthrough' },
  { from: 'silver_enriched::Qty', to: 'gold_fact::Qty', transform: 'load' },
  { from: 'gold_fact::Qty', to: 'gold_secured::Qty', transform: 'RLS view' },
  { from: 'gold_secured::Qty', to: 'gold_agg::TotalQty', transform: 'SUM by region' },
  { from: 'gold_agg::TotalQty', to: 'semantic_sales::Qty', transform: 'import' },
  { from: 'semantic_sales::Qty', to: 'semantic_measures::TotalUnits', transform: 'SUM(Qty)' },
  { from: 'semantic_measures::TotalUnits', to: 'report_exec::UnitsByRegion', transform: 'column chart' },

  // ---- CustomerId join keys (orders side) ---------------------------------
  { from: 'src_orders::CustomerId', to: 'bronze_orders::CustomerId', transform: 'copy' },
  { from: 'bronze_orders::CustomerId', to: 'silver_stage::CustomerId', transform: 'ingest' },
  { from: 'silver_stage::CustomerId', to: 'silver_clean::CustomerId', transform: 'trim' },
  { from: 'silver_clean::CustomerId', to: 'silver_typed::CustomerId', transform: 'cast int' },
  { from: 'silver_typed::CustomerId', to: 'silver_valid::CustomerId', transform: 'not null' },
  { from: 'silver_valid::CustomerId', to: 'silver_enriched::CustomerId', transform: 'join key' },

  // ---- Region path (customers side) ---------------------------------------
  { from: 'src_customers::CustomerId', to: 'bronze_customers::CustomerId', transform: 'copy' },
  { from: 'bronze_customers::CustomerId', to: 'silver_cust_clean::CustomerId', transform: 'ingest' },
  { from: 'silver_cust_clean::CustomerId', to: 'silver_cust_dedup::CustomerId', transform: 'dedupe' },
  { from: 'silver_cust_dedup::CustomerId', to: 'silver_enriched::CustomerId', transform: 'join key' },
  { from: 'src_customers::Region', to: 'bronze_customers::Region', transform: 'copy' },
  { from: 'bronze_customers::Region', to: 'silver_cust_clean::Region', transform: 'upper()' },
  { from: 'silver_cust_clean::Region', to: 'silver_cust_dedup::Region', transform: 'dedupe' },
  { from: 'silver_cust_dedup::Region', to: 'silver_enriched::Region', transform: 'join → enrich' },
  { from: 'silver_enriched::Region', to: 'gold_fact::Region', transform: 'load' },
  { from: 'gold_fact::Region', to: 'gold_secured::Region', transform: 'RLS view' },
  { from: 'gold_secured::Region', to: 'gold_agg::Region', transform: 'GROUP BY' },
  { from: 'gold_agg::Region', to: 'semantic_sales::Region', transform: 'import' },
  { from: 'semantic_sales::Region', to: 'report_exec::RevenueByRegion', transform: 'axis' },
];

export interface GraphColumn {
  key: string; // assetId::Column
  asset: string;
  name: string;
}

export interface GraphAsset {
  id: string;
  label: string;
  type: AssetType;
  level: number;
  columns: GraphColumn[];
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  transform: string;
}

export interface ColumnGraph {
  assets: GraphAsset[];
  edges: GraphEdge[];
  levels: number;
  columnIndex: Map<string, GraphColumn>;
}

function colName(key: string): string {
  return key.split('::')[1] ?? key;
}
function assetId(key: string): string {
  return key.split('::')[0] ?? key;
}

/** Longest-path leveling: level(asset) = max(level(pred)) + 1. */
function assignLevels(
  assetIds: string[],
  edges: GraphEdge[],
): Map<string, number> {
  const preds = new Map<string, Set<string>>();
  const succs = new Map<string, Set<string>>();
  for (const id of assetIds) {
    preds.set(id, new Set());
    succs.set(id, new Set());
  }
  for (const e of edges) {
    const a = assetId(e.from);
    const b = assetId(e.to);
    if (a === b) continue;
    preds.get(b)!.add(a);
    succs.get(a)!.add(b);
  }
  const level = new Map<string, number>();
  // Kahn-style longest path.
  const indeg = new Map<string, number>();
  for (const id of assetIds) indeg.set(id, preds.get(id)!.size);
  const queue = assetIds.filter((id) => indeg.get(id) === 0);
  for (const id of queue) level.set(id, 0);
  while (queue.length) {
    const id = queue.shift()!;
    const lv = level.get(id) ?? 0;
    for (const next of succs.get(id)!) {
      level.set(next, Math.max(level.get(next) ?? 0, lv + 1));
      indeg.set(next, (indeg.get(next) ?? 0) - 1);
      if (indeg.get(next) === 0) queue.push(next);
    }
  }
  for (const id of assetIds) if (!level.has(id)) level.set(id, 0);
  return level;
}

let cachedGraph: ColumnGraph | null = null;

/** Shape produced by `harvesters.scan_repo --app-export` on the Python side. */
export interface ScannedColumnGraph {
  assets: Record<string, { label: string; type: string }>;
  edges: { from: string; to: string; transform: string }[];
}

const VALID_TYPES: AssetType[] = [
  'source', 'bronze', 'silver', 'gold', 'semantic', 'report',
];

function coerceType(t: string): AssetType {
  return (VALID_TYPES as string[]).includes(t) ? (t as AssetType) : 'source';
}

/**
 * Build the column graph. With no argument it returns the bundled demo graph
 * (cached). Pass a `ScannedColumnGraph` (from the repo scanner) to render real
 * column lineage harvested from notebooks / SQL / Python code.
 */
export function buildColumnGraph(scanned?: ScannedColumnGraph): ColumnGraph {
  if (!scanned && cachedGraph) return cachedGraph;

  const rawEdges: RawColEdge[] = scanned
    ? scanned.edges.map((e) => ({ from: e.from, to: e.to, transform: e.transform }))
    : RAW_EDGES;
  const assetMeta: Record<string, AssetMeta> = scanned
    ? Object.fromEntries(
        Object.entries(scanned.assets).map(([id, m]) => [
          id,
          { label: m.label, type: coerceType(m.type) },
        ]),
      )
    : ASSET_META;

  const edges: GraphEdge[] = rawEdges.map((e, i) => ({
    id: `ce${i}`,
    from: e.from,
    to: e.to,
    transform: e.transform,
  }));

  // Collect columns per asset, preserving first-seen order.
  const assetCols = new Map<string, string[]>();
  const seen = new Set<string>();
  const addCol = (key: string) => {
    const aid = assetId(key);
    if (!assetCols.has(aid)) assetCols.set(aid, []);
    if (!seen.has(key)) {
      seen.add(key);
      assetCols.get(aid)!.push(key);
    }
  };
  for (const e of edges) {
    addCol(e.from);
    addCol(e.to);
  }

  const assetIds = [...assetCols.keys()];
  const levels = assignLevels(assetIds, edges);

  const columnIndex = new Map<string, GraphColumn>();
  const assets: GraphAsset[] = assetIds.map((id) => {
    const columns = assetCols.get(id)!.map((key) => {
      const col: GraphColumn = { key, asset: id, name: colName(key) };
      columnIndex.set(key, col);
      return col;
    });
    const meta = assetMeta[id] ?? { label: id, type: 'source' as AssetType };
    return { id, label: meta.label, type: meta.type, level: levels.get(id) ?? 0, columns };
  });

  const maxLevel = Math.max(...assets.map((a) => a.level), 0);
  const graph: ColumnGraph = { assets, edges, levels: maxLevel + 1, columnIndex };
  if (!scanned) cachedGraph = graph;
  return graph;
}

/**
 * Try to load a scanned column graph exported by the repo scanner (served from
 * the app's `public/column_edges.json`, or the Rayfin backend when configured).
 * Falls back to the bundled demo graph so the view is never empty.
 */
export async function loadColumnGraph(): Promise<{
  graph: ColumnGraph;
  source: 'scanned' | 'demo';
}> {
  const apiUrl = import.meta.env.VITE_RAYFIN_API_URL as string | undefined;
  const candidates = [
    apiUrl ? `${apiUrl}/column_edges.json` : null,
    `${import.meta.env.BASE_URL ?? '/'}column_edges.json`,
  ].filter(Boolean) as string[];

  for (const url of candidates) {
    try {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) continue;
      const data = (await res.json()) as ScannedColumnGraph;
      if (data?.edges?.length) {
        return { graph: buildColumnGraph(data), source: 'scanned' };
      }
    } catch {
      // try next candidate
    }
  }
  return { graph: buildColumnGraph(), source: 'demo' };
}

export interface TraceResult {
  columns: Set<string>;
  edges: Set<string>;
  upstream: number;
  downstream: number;
}

/** Walk all upstream and downstream column edges from `start`. */
export function traceColumn(graph: ColumnGraph, start: string): TraceResult {
  const fwd = new Map<string, GraphEdge[]>();
  const bwd = new Map<string, GraphEdge[]>();
  for (const e of graph.edges) {
    (fwd.get(e.from) ?? fwd.set(e.from, []).get(e.from)!).push(e);
    (bwd.get(e.to) ?? bwd.set(e.to, []).get(e.to)!).push(e);
  }
  const columns = new Set<string>([start]);
  const edges = new Set<string>();

  const walk = (
    adj: Map<string, GraphEdge[]>,
    pick: (e: GraphEdge) => string,
  ): number => {
    let count = 0;
    const stack = [start];
    const visited = new Set<string>([start]);
    while (stack.length) {
      const node = stack.pop()!;
      for (const e of adj.get(node) ?? []) {
        edges.add(e.id);
        const next = pick(e);
        if (!columns.has(next)) count += 1;
        columns.add(next);
        if (!visited.has(next)) {
          visited.add(next);
          stack.push(next);
        }
      }
    }
    return count;
  };

  const downstream = walk(fwd, (e) => e.to);
  const upstream = walk(bwd, (e) => e.from);
  return { columns, edges, upstream, downstream };
}

export const ASSET_TYPE_LABEL: Record<AssetType, string> = {
  source: 'Source',
  bronze: 'Bronze',
  silver: 'Silver',
  gold: 'Gold',
  semantic: 'Semantic',
  report: 'Report',
};
