import { useMemo, useRef, useState } from 'react';
import {
  Badge,
  Body1,
  Button,
  Caption1,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  AddCircleRegular,
  SubtractCircleRegular,
  TargetRegular,
} from '@fluentui/react-icons';
import {
  ASSET_TYPE_LABEL,
  AssetType,
  ColumnGraph,
  GraphAsset,
  traceColumn,
} from './columnLineage';

// ---- layout constants -------------------------------------------------------
const LEVEL_GAP = 260;
const ASSET_W = 184;
const HEADER_H = 34;
const ROW_H = 24;
const ASSET_PAD_Y = 26;
const MARGIN_X = 40;
const MARGIN_Y = 32;

// ---- colours per medallion layer (dark-theme friendly) ----------------------
const LAYER_COLOR: Record<AssetType, { fill: string; stroke: string; head: string }> = {
  source: { fill: '#0d1b3e', stroke: '#1565C0', head: '#1b2c5a' },
  bronze: { fill: '#2e1d0d', stroke: '#B26A00', head: '#4a3318' },
  silver: { fill: '#1a1f29', stroke: '#78909C', head: '#2c333f' },
  gold: { fill: '#2e2a0d', stroke: '#C9A227', head: '#4a4318' },
  semantic: { fill: '#1a0d2e', stroke: '#7B1FA2', head: '#2f1a4a' },
  report: { fill: '#0d2e1a', stroke: '#2E7D32', head: '#18402a' },
};

interface PositionedColumn {
  key: string;
  name: string;
  x: number; // left edge of asset
  yMid: number;
  inX: number; // left anchor
  outX: number; // right anchor
}

interface PositionedAsset extends GraphAsset {
  x: number;
  y: number;
  h: number;
}

interface Layout {
  assets: PositionedAsset[];
  columns: Map<string, PositionedColumn>;
  width: number;
  height: number;
}

function computeLayout(graph: ColumnGraph): Layout {
  const byLevel = new Map<number, GraphAsset[]>();
  for (const a of graph.assets) {
    if (!byLevel.has(a.level)) byLevel.set(a.level, []);
    byLevel.get(a.level)!.push(a);
  }

  const assets: PositionedAsset[] = [];
  const columns = new Map<string, PositionedColumn>();
  let maxHeight = 0;

  for (let lv = 0; lv < graph.levels; lv++) {
    const group = (byLevel.get(lv) ?? []).slice().sort((a, b) => a.id.localeCompare(b.id));
    const x = MARGIN_X + lv * LEVEL_GAP;
    let y = MARGIN_Y;
    for (const a of group) {
      const h = HEADER_H + a.columns.length * ROW_H + 8;
      const pa: PositionedAsset = { ...a, x, y, h };
      assets.push(pa);
      a.columns.forEach((c, i) => {
        const yMid = y + HEADER_H + i * ROW_H + ROW_H / 2;
        columns.set(c.key, {
          key: c.key,
          name: c.name,
          x,
          yMid,
          inX: x,
          outX: x + ASSET_W,
        });
      });
      y += h + ASSET_PAD_Y;
    }
    maxHeight = Math.max(maxHeight, y);
  }

  const width = MARGIN_X * 2 + graph.levels * LEVEL_GAP;
  const height = maxHeight + MARGIN_Y;
  return { assets, columns, width, height };
}

function edgePath(sx: number, sy: number, tx: number, ty: number): string {
  const dx = Math.max(40, (tx - sx) / 2);
  return `M ${sx},${sy} C ${sx + dx},${sy} ${tx - dx},${ty} ${tx},${ty}`;
}

const useStyles = makeStyles({
  wrap: { display: 'flex', flexDirection: 'column', ...shorthands.gap('8px') },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
    flexWrap: 'wrap',
  },
  spacer: { flexGrow: 1 },
  legend: { display: 'flex', alignItems: 'center', ...shorthands.gap('10px'), flexWrap: 'wrap' },
  legendItem: { display: 'flex', alignItems: 'center', ...shorthands.gap('4px') },
  swatch: { width: '12px', height: '12px', ...shorthands.borderRadius('3px') },
  canvas: {
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: '#16213e',
    ...shorthands.overflow('auto'),
    maxHeight: '70vh',
    cursor: 'grab',
  },
  hint: { color: tokens.colorNeutralForeground3 },
});

export interface LineageGraphProps {
  graph: ColumnGraph;
}

export function LineageGraph({ graph }: LineageGraphProps) {
  const styles = useStyles();
  const layout = useMemo(() => computeLayout(graph), [graph]);
  const [selected, setSelected] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const scrollRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null);

  const trace = useMemo(
    () => (selected ? traceColumn(graph, selected) : null),
    [graph, selected],
  );

  const onColumnClick = (key: string) => {
    setSelected((cur) => (cur === key ? null : key));
  };

  const onMouseDown = (e: React.MouseEvent) => {
    const el = scrollRef.current;
    if (!el) return;
    drag.current = { x: e.clientX, y: e.clientY, left: el.scrollLeft, top: el.scrollTop };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    const el = scrollRef.current;
    if (!el || !drag.current) return;
    el.scrollLeft = drag.current.left - (e.clientX - drag.current.x);
    el.scrollTop = drag.current.top - (e.clientY - drag.current.y);
  };
  const endDrag = () => {
    drag.current = null;
  };

  const selCol = selected ? graph.columnIndex.get(selected) : undefined;
  const selAsset = selCol ? layout.assets.find((a) => a.id === selCol.asset) : undefined;

  return (
    <div className={styles.wrap}>
      <div className={styles.toolbar}>
        <Button
          size="small"
          icon={<SubtractCircleRegular />}
          onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))}
        >
          Zoom out
        </Button>
        <Text>{Math.round(zoom * 100)}%</Text>
        <Button
          size="small"
          icon={<AddCircleRegular />}
          onClick={() => setZoom((z) => Math.min(2, +(z + 0.1).toFixed(2)))}
        >
          Zoom in
        </Button>
        {selected && (
          <Button size="small" icon={<TargetRegular />} onClick={() => setSelected(null)}>
            Clear selection
          </Button>
        )}
        <div className={styles.spacer} />
        <div className={styles.legend}>
          {(Object.keys(LAYER_COLOR) as AssetType[]).map((t) => (
            <span key={t} className={styles.legendItem}>
              <span
                className={styles.swatch}
                style={{ backgroundColor: LAYER_COLOR[t].stroke }}
              />
              <Caption1>{ASSET_TYPE_LABEL[t]}</Caption1>
            </span>
          ))}
        </div>
      </div>

      {selected && trace ? (
        <Body1>
          <Badge appearance="filled" color="brand">
            {selCol?.name}
          </Badge>{' '}
          in <strong>{selAsset?.label}</strong> — {trace.upstream} upstream and{' '}
          {trace.downstream} downstream columns across {trace.edges.size} hops.
        </Body1>
      ) : (
        <Caption1 className={styles.hint}>
          {graph.levels} levels · {graph.assets.length} assets ·{' '}
          {graph.edges.length} column edges. Click any column to trace its lineage;
          drag to pan, zoom with the buttons.
        </Caption1>
      )}

      <div
        ref={scrollRef}
        className={styles.canvas}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={endDrag}
        onMouseLeave={endDrag}
      >
        <svg
          width={layout.width * zoom}
          height={layout.height * zoom}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="img"
          aria-label="Column-level lineage graph"
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#5a6b8c" />
            </marker>
            <marker
              id="arrowHot"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="8"
              markerHeight="8"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#4cc2ff" />
            </marker>
          </defs>

          {/* edges */}
          {graph.edges.map((e) => {
            const s = layout.columns.get(e.from);
            const t = layout.columns.get(e.to);
            if (!s || !t) return null;
            const hot = trace?.edges.has(e.id) ?? false;
            const dim = selected != null && !hot;
            return (
              <path
                key={e.id}
                d={edgePath(s.outX, s.yMid, t.inX, t.yMid)}
                fill="none"
                stroke={hot ? '#4cc2ff' : '#3c4a66'}
                strokeWidth={hot ? 2.4 : 1.2}
                opacity={dim ? 0.12 : 1}
                markerEnd={hot ? 'url(#arrowHot)' : 'url(#arrow)'}
              />
            );
          })}

          {/* assets + columns */}
          {layout.assets.map((a) => {
            const c = LAYER_COLOR[a.type];
            return (
              <g key={a.id}>
                <rect
                  x={a.x}
                  y={a.y}
                  width={ASSET_W}
                  height={a.h}
                  rx={8}
                  fill={c.fill}
                  stroke={c.stroke}
                  strokeWidth={1.4}
                />
                <rect
                  x={a.x}
                  y={a.y}
                  width={ASSET_W}
                  height={HEADER_H}
                  rx={8}
                  fill={c.head}
                />
                <text
                  x={a.x + 10}
                  y={a.y + 15}
                  fill="#FFFFFF"
                  fontSize="11"
                  fontWeight="600"
                >
                  {a.label.length > 26 ? a.label.slice(0, 25) + '…' : a.label}
                </text>
                <text x={a.x + 10} y={a.y + 27} fill={c.stroke} fontSize="9">
                  {ASSET_TYPE_LABEL[a.type]} · L{a.level}
                </text>
                {a.columns.map((col, i) => {
                  const y = a.y + HEADER_H + i * ROW_H;
                  const inPath = trace?.columns.has(col.key) ?? false;
                  const isSel = col.key === selected;
                  const dim = selected != null && !inPath;
                  return (
                    <g
                      key={col.key}
                      onClick={(ev) => {
                        ev.stopPropagation();
                        onColumnClick(col.key);
                      }}
                      style={{ cursor: 'pointer' }}
                      opacity={dim ? 0.25 : 1}
                    >
                      <rect
                        x={a.x + 4}
                        y={y + 2}
                        width={ASSET_W - 8}
                        height={ROW_H - 4}
                        rx={4}
                        fill={isSel ? '#4cc2ff' : inPath ? '#1f3a52' : '#ffffff08'}
                        stroke={inPath && !isSel ? '#4cc2ff' : 'transparent'}
                        strokeWidth={1}
                      />
                      <circle cx={a.x + 4} cy={y + ROW_H / 2} r={2.5} fill={c.stroke} />
                      <circle
                        cx={a.x + ASSET_W - 4}
                        cy={y + ROW_H / 2}
                        r={2.5}
                        fill={c.stroke}
                      />
                      <text
                        x={a.x + 14}
                        y={y + ROW_H / 2 + 3.5}
                        fill={isSel ? '#0b1020' : '#d6def0'}
                        fontSize="10.5"
                        fontWeight={isSel ? 700 : 400}
                      >
                        {col.name}
                      </text>
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
