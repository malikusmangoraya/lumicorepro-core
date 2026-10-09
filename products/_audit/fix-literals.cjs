/**
 * fix-literals.cjs — two leftovers from the interrupted token pass:
 *
 *   1. aurelia-estates ended up with `var(--t-primary)` written into BRAND.js, its
 *      design-tokens.json palette and two Tailwind ramp steps. Brand constants are literals:
 *      a var() there cannot be read by a tool, a designer or a favicon build.
 *   2. every BRAND.js pointed readers at `products/_audit/unify-tokens.cjs`, which no longer
 *      exists. The header now names the tools that do.
 *
 * Run: node products/_audit/fix-literals.cjs
 */
const fs = require('fs');

const PRODUCTS = [
  'apex',
  'aurelia-estates',
  'aurum-fitness',
  'claimflow-ai',
  'flowpilot',
  'meridian-capital',
  'nuage-events',
  'prestige-studio',
  'resupro',
  'saffron-voyage',
  'studio-lumen',
];

const AURELIA = { primary: '#be2c2c', secondary: '#821616', accent: '#821616' };
const report = [];

for (const id of PRODUCTS) {
  const fe = `products/${id}/frontend`;
  const brandPath = `${fe}/src/components/brand/BRAND.js`;
  let brand = fs.readFileSync(brandPath, 'utf8');
  const before = brand;

  if (id === 'aurelia-estates') {
    brand = brand
      .replace(/(primary:\s*")[^"]*(")/, `$1${AURELIA.primary}$2`)
      .replace(/(secondary:\s*")[^"]*(")/, `$1${AURELIA.secondary}$2`)
      .replace(/(accent:\s*")[^"]*(")/, `$1${AURELIA.accent}$2`);
  }

  // One accurate header: drop the whole leading comment block, whatever earlier passes
  // appended to it, and write the canonical one in its place.
  const lines = brand.split(/\r?\n/);
  const firstCode = lines.findIndex((line) => line.trim() && !line.trim().startsWith('//'));
  brand = lines.slice(firstCode === -1 ? 0 : firstCode).join('\n');
  brand =
    [
      '// Brand constants — the single source of truth for colour.',
      '// src/index.css :root, tailwind.config.js, design-tokens.json and public/favicon.svg',
      '// all mirror these values. The canonical palette table lives in',
      '// products/_audit/rebuild-css.cjs; re-check every source with',
      '// `node products/_audit/verify-all.cjs`.',
    ].join('\n') +
    '\n' +
    brand;
  if (brand !== before) fs.writeFileSync(brandPath, brand.replace(/\n/g, '\r\n'));

  if (id === 'aurelia-estates') {
    const dtPath = `${fe}/design-tokens.json`;
    const dt = JSON.parse(fs.readFileSync(dtPath, 'utf8'));
    dt.palette = { ...dt.palette, primary: AURELIA.primary, secondary: AURELIA.secondary, accent: AURELIA.accent };
    if (dt.rendered_theme) {
      dt.rendered_theme.primary = AURELIA.primary;
      dt.rendered_theme.accent = AURELIA.accent;
    }
    fs.writeFileSync(dtPath, `${JSON.stringify(dt, null, 2)}\n`);

    const twPath = `${fe}/tailwind.config.js`;
    let tw = fs.readFileSync(twPath, 'utf8');
    const beforeTw = tw;
    tw = tw
      .replace(/(primary:\s*\{[^}]*?'350':\s*')[^']+(')/, `$1${AURELIA.primary}$2`)
      .replace(/(accent:\s*\{[^}]*?'350':\s*')[^']+(')/, `$1${AURELIA.accent}$2`);
    if (tw !== beforeTw) fs.writeFileSync(twPath, tw);
  }

  const finalBrand = fs.readFileSync(brandPath, 'utf8');
  const dt = JSON.parse(fs.readFileSync(`${fe}/design-tokens.json`, 'utf8'));
  const tw = fs.readFileSync(`${fe}/tailwind.config.js`, 'utf8');
  const css = fs.readFileSync(`${fe}/src/index.css`, 'utf8');
  const cssPrimary = (css.match(/--t-primary:\s*([^;]+)/) || [])[1]?.trim();
  const twRamp = (tw.match(/primary:\s*\{[^}]*?'350':\s*'([^']+)'/) || [])[1];
  const twVar = (tw.match(/--t-primary-rgb,\s*([\d\s]+)\)/) || [])[1]?.trim();

  report.push({
    id,
    brandPrimary: (finalBrand.match(/primary:\s*"([^"]*)"/) || [])[1],
    tokensPrimary: dt.palette?.primary,
    cssPrimary,
    tailwind: twRamp || twVar,
    headerOk: /verify-all\.cjs/.test(finalBrand) && !/unify-tokens/.test(finalBrand),
    // Only the brand constants and the palette are required to be literals. tailwind.config.js
    // legitimately maps its colours onto the CSS variables, which is a different thing.
    literalsOnly: ![finalBrand, JSON.stringify(dt.palette || {})].some((text) =>
      /var\(--t-(primary|accent|canvas|heading)/.test(text)
    ),
  });
}

console.log('product            | BRAND.js | design-tokens | index.css | tailwind | header ok | literals only');
console.log('-------------------|----------|---------------|-----------|----------|-----------|--------------');
for (const r of report) {
  console.log(
    `${r.id.padEnd(18)} | ${String(r.brandPrimary).padEnd(8)} | ${String(r.tokensPrimary).padEnd(13)} | ${String(r.cssPrimary).padEnd(13)} | ${String(r.tailwind).padEnd(8)} | ${r.headerOk ? '   ok    ' : '   NO    '} | ${r.literalsOnly ? 'ok' : 'NO'}`
  );
}
const failed = report.filter((r) => !r.headerOk || !r.literalsOnly);
console.log(`\n${report.length - failed.length}/${report.length} brand sources are literal and correctly documented`);
process.exitCode = failed.length ? 1 : 0;
