// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "Nuage Events",
  initials: "NE",
  primary: "#be2c4e",
  secondary: "#0ea5e9",
  accent: "#82162f",
  displayFont: "Inter",
  sansFont: "Inter",
};

export default BRAND;
