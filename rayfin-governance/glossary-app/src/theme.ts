import {
  BrandVariants,
  Theme,
  createLightTheme,
  createDarkTheme,
} from '@fluentui/react-components';

// Fabric-aligned brand ramp (teal accent consistent with the Microsoft Fabric
// data-plane). Generated to satisfy Fluent v9's 16-stop brand ramp contract.
export const fabricBrand: BrandVariants = {
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

export const fabricLightTheme: Theme = {
  ...createLightTheme(fabricBrand),
};

export const fabricDarkTheme: Theme = {
  ...createDarkTheme(fabricBrand),
};

/** Premium diagonal header gradient built from the Fabric brand ramp. */
export const HEADER_GRADIENT =
  `linear-gradient(135deg, ${fabricBrand[70]} 0%, ${fabricBrand[90]} 45%, ${fabricBrand[110]} 100%)`;
