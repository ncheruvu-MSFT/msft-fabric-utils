import {
  Badge,
  Caption1,
  Title3,
  Tooltip,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  CloudRegular,
  PlugDisconnectedRegular,
  SparkleRegular,
} from '@fluentui/react-icons';
import { ReactNode } from 'react';
import { HEADER_GRADIENT } from './theme';

/**
 * Rayfin Governance branding kit.
 *
 * Drop this file (and ./theme.ts) into any Rayfin app's `src/` folder to get a
 * consistent, premium Fluent v9 look plus the "Rayfin app" badge that signals
 * the app is built on Microsoft Fabric Apps (Rayfin).
 *
 * Usage in App.tsx:
 *
 *   import { useBrandStyles, AppHeader } from './branding';
 *   const brand = useBrandStyles();
 *   ...
 *   <div className={brand.root}>
 *     <AppHeader icon={<BookDatabaseRegular />} title="Glossary"
 *                subtitle="Microsoft Fabric · Data governance" source={source} />
 *     ...stat cards use brand.statCard / brand.statValue, grids use brand.gridCard...
 *   </div>
 */
export const useBrandStyles = makeStyles({
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
});

/** The "Rayfin app" badge — a pill that labels the app as built on Fabric Apps. */
export function RayfinPill() {
  const brand = useBrandStyles();
  return (
    <Tooltip
      content="Built with Rayfin on Microsoft Fabric Apps"
      relationship="label"
    >
      <span className={brand.rayfinPill}>
        <SparkleRegular />
        Rayfin app
      </span>
    </Tooltip>
  );
}

/** Live-backend vs seed-data indicator shown on the right of the header. */
export function SourceBadge({ source }: { source: 'backend' | 'seed' }) {
  return (
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
  );
}

export interface AppHeaderProps {
  icon: ReactNode;
  title: string;
  subtitle: string;
  /** Optional data-source indicator. Omit to hide the badge. */
  source?: 'backend' | 'seed';
  /** Optional extra header content (e.g. an identity field), rendered before the badges. */
  children?: ReactNode;
}

/** Premium branded app header with the Rayfin pill baked in. */
export function AppHeader({ icon, title, subtitle, source, children }: AppHeaderProps) {
  const brand = useBrandStyles();
  return (
    <header className={brand.header}>
      <span className={brand.headerIcon}>{icon}</span>
      <div className={brand.headerTitles}>
        <Title3>{title}</Title3>
        <Caption1>{subtitle}</Caption1>
      </div>
      <RayfinPill />
      <div className={brand.headerSpacer} />
      {children}
      {source ? <SourceBadge source={source} /> : null}
    </header>
  );
}

/** Small stat card used in the KPI row. */
export function StatCard({ label, value }: { label: string; value: ReactNode }) {
  const brand = useBrandStyles();
  return (
    <div className={brand.statCard}>
      <Caption1>{label}</Caption1>
      <span className={brand.statValue}>{value}</span>
    </div>
  );
}
