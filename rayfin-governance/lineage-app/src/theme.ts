import {
  BrandVariants,
  Theme,
  createLightTheme,
  createDarkTheme,
} from '@fluentui/react-components';

// Lineage-aligned brand ramp (indigo/blue accent) to visually distinguish the
// lineage graph app from the teal governance apps, while staying inside the
// Microsoft Fabric data-plane look. 16-stop ramp required by Fluent v9.
export const lineageBrand: BrandVariants = {
  10: '#020B14',
  20: '#031A2B',
  30: '#04263F',
  40: '#053253',
  50: '#063F67',
  60: '#074C7C',
  70: '#085A91',
  80: '#0A68A6',
  90: '#1276BB',
  100: '#2884C7',
  110: '#4592D0',
  120: '#62A0D9',
  130: '#80AFE1',
  140: '#9FBEEA',
  150: '#BFCFF2',
  160: '#DFE7F9',
};

export const lineageLightTheme: Theme = {
  ...createLightTheme(lineageBrand),
};

export const lineageDarkTheme: Theme = {
  ...createDarkTheme(lineageBrand),
};

/** Premium diagonal header gradient built from the lineage brand ramp. */
export const HEADER_GRADIENT =
  `linear-gradient(135deg, ${lineageBrand[70]} 0%, ${lineageBrand[90]} 45%, ${lineageBrand[110]} 100%)`;
