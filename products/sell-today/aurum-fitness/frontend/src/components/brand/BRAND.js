// Brand constants — the single source of truth for colour.
// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg
// all mirror these values. The canonical palette table lives in
// products/_audit/rebuild-css.cjs; re-check every source with
// `node products/_audit/verify-all.cjs`.
export const BRAND = {
  name: "Aurum Fitness",
  initials: "AF",
  primary: "#be882c",
  secondary: "#8b5cf6",
  accent: "#ec4899",
  displayFont: "Outfit",
  sansFont: "Inter",
};

export default BRAND;
