// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "Aurelia Estates",
  initials: "AE",
  primary: "#be2c2c",
  secondary: "#821616",
  accent: "#821616",
  displayFont: "Inter",
  sansFont: "Inter",
};

export default BRAND;
