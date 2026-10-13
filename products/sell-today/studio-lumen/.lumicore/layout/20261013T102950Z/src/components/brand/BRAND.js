// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "Studio Lumen",
  initials: "SL",
  primary: "#ea580c",
  secondary: "#8b5cf6",
  accent: "#16a34a",
  displayFont: "Outfit",
  sansFont: "Inter",
};

export default BRAND;
