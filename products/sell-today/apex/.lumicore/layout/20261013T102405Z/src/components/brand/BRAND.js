// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "Apex Digital",
  initials: "AD",
  primary: "#0891b2",
  secondary: "#7c4dff",
  accent: "#7c4dff",
  displayFont: "Orbitron",
  sansFont: "Inter",
};

export default BRAND;
