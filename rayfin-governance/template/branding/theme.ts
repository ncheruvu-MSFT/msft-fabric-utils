import {
  BrandVariants,
  Theme,
  createLightTheme,
  createDarkTheme,
} from '@fluentui/react-components';

/**
 * Rayfin Governance — shared brand ramp.
 *
 * Fluent v9 requires a 16-stop brand ramp. This teal ramp is aligned with the
 * Microsoft Fabric data-plane. To re-brand for a customer, replace the hex
 * values below (keep all 16 stops) or generate a new ramp with the Fluent
 * Theme Designer: https://react.fluentui.dev/?path=/docs/theme-theme-designer--docs
 */
export const governanceBrand: BrandVariants = {
  10: '#02110F',
  20: '#04211C',
  30: '#062E27',
  40: '#073B31',
  50: '#08493C',
  60: '#0A5747',
  70: '#0B6553',
  80: '#0D745F',
  90: '#11836B',
  100: '#1A9177',
  110: '#2E9F85',
  120: '#48AD94',
  130: '#67BBA4',
  140: '#89C8B6',
  150: '#ADD6C9',
  160: '#D3E8E0',
};

export const governanceLightTheme: Theme = {
  ...createLightTheme(governanceBrand),
};

export const governanceDarkTheme: Theme = {
  ...createDarkTheme(governanceBrand),
};

/** Premium diagonal header gradient built from the brand ramp. */
export const HEADER_GRADIENT =
  `linear-gradient(135deg, ${governanceBrand[70]} 0%, ${governanceBrand[90]} 45%, ${governanceBrand[110]} 100%)`;
