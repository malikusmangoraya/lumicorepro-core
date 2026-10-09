/**
 * motionPresets — cohesive transition metrics (TRD #3 motion profiles).
 * Frozen duration/easing tokens; every animated wrapper reads from here so
 * transition states stay consistent across the product.
 */
export const DURATIONS = {
  instant: 80,
  fast: 140,
  standard: 240,
  expressive: 420,
};

export const EASING = [0.22, 1, 0.36, 1];

export const PRESETS = {
  fade: { hidden: { opacity: 0 }, show: { opacity: 1 } },
  'slide-up': { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } },
  scale: { hidden: { opacity: 0, scale: 0.96 }, show: { opacity: 1, scale: 1 } },
};

export default { DURATIONS, EASING, PRESETS };
