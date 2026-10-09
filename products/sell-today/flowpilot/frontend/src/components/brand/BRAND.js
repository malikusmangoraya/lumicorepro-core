// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "FlowPilot",
  initials: "FL",
  primary: "#059669",
  secondary: "#6366f1",
  accent: "#6366f1",
  displayFont: "Space Grotesk",
  sansFont: "Inter",
};

export default BRAND;
