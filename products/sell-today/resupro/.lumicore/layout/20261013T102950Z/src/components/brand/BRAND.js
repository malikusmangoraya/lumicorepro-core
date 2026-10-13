// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "ResuPro",
  initials: "RE",
  primary: "#be2c44",
  secondary: "#000000",
  accent: "#059669",
  displayFont: "Helvetica Neue",
  sansFont: "Helvetica Neue",
};

export default BRAND;
