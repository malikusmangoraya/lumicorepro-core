// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "Meridian Capital",
  initials: "MC",
  primary: "#be2c92",
  secondary: "#64748b",
  accent: "#be2c92",
  displayFont: "Inter",
  sansFont: "Inter",
};

export default BRAND;
