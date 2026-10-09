/**
 * repair-tokens.cjs — one valid `:root` per product, built from an explicit palette table.
 *
 * Self-contained on purpose: it never derives a colour from the file it is repairing, so an
 * interrupted earlier run can always be converged back to a good state. It
 *   1. collects the product's own non-palette tokens (--t-brand, --t-glass-*, --t-shadow-*),
 *   2. deletes every :root block and any orphaned declaration run left outside a rule,
 *   3. writes one :root block: fluid scale + palette + product tokens + rgb companions,
 *   4. de-hardcodes template hexes in the class layers so the UI follows the palette.
 *
 * Run: node products/_audit/repair-tokens.cjs
 */
const fs = require('fs');
const p = require('path');

const ROOT = 'products';

const FLUID_SCALE = [
  '--fluid-space-0: clamp(0rem, 0vw, 0rem);',
  '--fluid-space-1: clamp(0.25rem, 0.5vw + 0.125rem, 0.5rem);',
  '--fluid-space-2: clamp(0.5rem, 1vw + 0.25rem, 1rem);',
  '--fluid-space-3: clamp(1rem, 2vw + 0.5rem, 1.5rem);',
  '--fluid-space-4: clamp(1.5rem, 3vw + 0.75rem, 2rem);',
  '--fluid-space-5: clamp(2rem, 4vw + 1rem, 3rem);',
  '--fluid-space-6: clamp(3rem, 5vw + 1.5rem, 4rem);',
  '--fluid-space-7: clamp(4rem, 6vw + 2rem, 5rem);',
  '--fluid-space-8: clamp(5rem, 8vw + 2.5rem, 7rem);',
];

/**
 * Canonical palette per product.
 * apex and flowpilot were re-pointed at their own brand hues because they rendered the
 * identical generic purple/cream theme. The other nine carry the palette that was already
 * rendering on disk, recovered after the 2026-10-08 partial write dropped two of them.
 */
const PALETTE = {
  apex: {
    canvas: '#f4f8ff',
    surface: '#ffffff',
    primary: '#0891b2',
    accent: '#7c4dff',
    heading: '#0b1b33',
    text: '#1f2937',
    muted: '#64748b',
    border: '#dbe4f0',
    footer: '#071a2b',
    displayFont: 'Orbitron',
    sansFont: 'Inter',
  },
  flowpilot: {
    canvas: '#f2faf6',
    surface: '#ffffff',
    primary: '#059669',
    accent: '#6366f1',
    heading: '#052e26',
    text: '#1f2937',
    muted: '#64748b',
    border: '#d6ece4',
    footer: '#052e26',
    displayFont: 'Space Grotesk',
    sansFont: 'Inter',
  },
  'aurelia-estates': {
    canvas: '#ffffff',
    surface: '#ffffff',
    primary: '#be2c2c',
    accent: '#821616',
    heading: '#5b3200',
    text: '#26292f',
    muted: '#be2c2c',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Inter',
    sansFont: 'Inter',
  },
  'aurum-fitness': {
    canvas: '#ffffff',
    surface: '#ffffff',
    primary: '#be882c',
    accent: '#ec4899',
    heading: '#be882c',
    text: '#26292f',
    muted: '#be882c',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Outfit',
    sansFont: 'Inter',
  },
  'claimflow-ai': {
    canvas: '#f8fafc',
    surface: '#ffffff',
    primary: '#374151',
    accent: '#dc2626',
    heading: '#111827',
    text: '#26292f',
    muted: '#64748b',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Helvetica Neue',
    sansFont: 'Helvetica Neue',
  },
  'meridian-capital': {
    canvas: '#f8fafc',
    surface: '#ffffff',
    primary: '#be2c92',
    accent: '#be2c92',
    heading: '#be2c92',
    text: '#26292f',
    muted: '#be2c92',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Inter',
    sansFont: 'Inter',
  },
  'nuage-events': {
    canvas: '#f8fafc',
    surface: '#ffffff',
    primary: '#be2c4e',
    accent: '#82162f',
    heading: '#5b3200',
    text: '#26292f',
    muted: '#be2c4e',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Inter',
    sansFont: 'Inter',
  },
  'prestige-studio': {
    canvas: '#f8fafc',
    surface: '#ffffff',
    primary: '#be502c',
    accent: '#be502c',
    heading: '#be502c',
    text: '#26292f',
    muted: '#be502c',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Helvetica Neue',
    sansFont: 'Helvetica Neue',
  },
  resupro: {
    canvas: '#f8fafc',
    surface: '#ffffff',
    primary: '#be2c44',
    accent: '#059669',
    heading: '#be2c44',
    text: '#26292f',
    muted: '#be2c44',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Helvetica Neue',
    sansFont: 'Helvetica Neue',
  },
  'saffron-voyage': {
    canvas: '#f8fafc',
    surface: '#ffffff',
    primary: '#be702c',
    accent: '#f59e0b',
    heading: '#be702c',
    text: '#26292f',
    muted: '#be702c',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Inter',
    sansFont: 'Inter',
  },
  'studio-lumen': {
    canvas: '#ffffff',
    surface: '#ffffff',
    primary: '#ea580c',
    accent: '#16a34a',
    heading: '#451a03',
    text: '#26292f',
    muted: '#be692c',
    border: '#e2e8f0',
    footer: '#0e1116',
    displayFont: 'Outfit',
    sansFont: 'Inter',
  },
};

// Template-generation defaults still pinned inside the class layers of the older products.
const LEGACY_HEX_TO_VAR = {
  '#7c3aed': 'var(--t-primary)',
  '#ec4899': 'var(--t-accent)',
  '#2e1065': 'var(--t-heading)',
  '#f7f3ea': 'var(--t-canvas)',
};

const hex2rgb = (hex) => [0, 2, 4].map((i) => parseInt(hex.slice(1 + i, 3 + i), 16)).join(' ');

const ROOT_MARK = '/*__LUMI_ROOT__*/';

/** Replaces the first `:root` block with a marker and deletes any later ones. */
const takeRootBlocks = (css) => {
  const at = css.indexOf(':root');
  if (at === -1) return { css, marked: false };
  const braceOpen = css.indexOf('{', at);
  const closeRe = /\r?\n\}/g;
  closeRe.lastIndex = braceOpen;
  const m = closeRe.exec(css);
  if (!m) throw new Error('unterminated :root block');
  const end = braceOpen + m.index + m[0].length;
  let out = css.slice(0, at) + ROOT_MARK + css.slice(end);
  // Any further :root block is a duplicate of the palette and is dropped outright.
  let next = out.indexOf(':root');
  while (next !== -1) {
    const open = out.indexOf('{', next);
    closeRe.lastIndex = open;
    const m2 = closeRe.exec(out);
    if (!m2) break;
    out = out.slice(0, next) + out.slice(open + m2.index + m2[0].length);
    next = out.indexOf(':root');
  }
  return { css: out, marked: true };
};

/** Drops declaration-like lines that sit outside any rule (brace depth 0). */
const stripOrphanDeclarations = (css) => {
  const lines = css.split(/\r?\n/);
  let depth = 0;
  const kept = [];
  let dropped = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    const isDecl = /^--[a-z0-9-]+:\s*.+;$/i.test(trimmed);
    if (depth === 0 && isDecl) {
      dropped++;
      continue;
    }
    kept.push(line);
    // Brace counting ignores braces inside comments and quoted strings well enough here:
    // these stylesheets contain none in those positions.
    if (!trimmed.startsWith('/*') && !trimmed.startsWith('*')) {
      depth += (line.match(/\{/g) || []).length;
      depth -= (line.match(/\}/g) || []).length;
      if (depth < 0) depth = 0;
    }
  }
  return { css: kept.join('\n'), dropped };
};

const report = [];
for (const [id, pal] of Object.entries(PALETTE)) {
  const cssPath = `${ROOT}/${id}/frontend/src/index.css`;
  let css = fs.readFileSync(cssPath, 'utf8');
  const eol = css.includes('\r\n') ? '\r\n' : '\n';

  /* 1. Collect the product's own tokens from anywhere in the file. */
  const extras = new Map();
  for (const line of css.split(/\r?\n/)) {
    const m = /^\s*(--t-[a-z0-9-]+):\s*(.+);\s*$/.exec(line);
    if (!m) continue;
    const base = m[1].replace(/^--t-/, '').replace(/-rgb$/, '');
    if (Object.prototype.hasOwnProperty.call(pal, base)) continue;
    if (/^--t-[a-z0-9-]+-rgb$/.test(m[1])) continue;
    if (m[1] === '--t-bg') continue; // emitted explicitly
    extras.set(m[1], m[2]);
  }

  /* 2. Collapse the :root blocks to a marker, then drop declarations left outside a rule. */
  const taken = takeRootBlocks(css);
  css = taken.css;
  const stripped = stripOrphanDeclarations(css.replace(/\r\n/g, '\n'));
  css = stripped.css;

  /* 3. De-hardcode template hexes in the class layers, never inside a token declaration. */
  // Ordered so the most meaningful token wins when a product reuses one hex for two roles
  // (aurum-fitness renders its primary and its heading in the same gold).
  const paletteVars = {
    ...LEGACY_HEX_TO_VAR,
    [pal.canvas]: 'var(--t-canvas)',
    [pal.accent]: 'var(--t-accent)',
    [pal.heading]: 'var(--t-heading)',
    [pal.primary]: 'var(--t-primary)',
  };
  css = css
    .split('\n')
    .map((line) => {
      if (/^\s*--t-/.test(line)) return line;
      let out = line;
      for (const [hex, token] of Object.entries(paletteVars)) {
        if (hex === pal.surface || hex === '#ffffff') continue; // white stays literal
        out = out.replace(new RegExp(hex, 'gi'), token);
      }
      return out;
    })
    .join('\n');

  /* 4. Build the single canonical block. */
  const tokenLines = Object.entries(pal)
    .filter(([, v]) => /^#[0-9a-f]{6}$/i.test(v))
    .map(([k, v]) => `  --t-${k}: ${v};`);
  const rgbLines = Object.entries(pal)
    .filter(([, v]) => /^#[0-9a-f]{6}$/i.test(v))
    .map(([k, v]) => `  --t-${k}-rgb: ${hex2rgb(v)};`);
  const extraLines = [...extras].map(([k, v]) => `  ${k}: ${v};`);
  const block = [
    ':root {',
    ...FLUID_SCALE.map((l) => `  ${l}`),
    ...tokenLines,
    '  --t-bg: #ffffff;',
    ...(extraLines.length ? ['', '  /* product tokens */', ...extraLines] : []),
    '',
    ...rgbLines,
    '}',
  ].join('\n');

  // The block goes back exactly where the first :root was; a product that never had one
  // gets it just above the scrollbar rules, or at the end.
  if (css.includes(ROOT_MARK)) {
    css = css.replace(ROOT_MARK, `${block}\n`);
  } else {
    const lines = css.split('\n');
    const scroll = lines.findIndex((l) => l.includes('::-webkit-scrollbar'));
    lines.splice(scroll === -1 ? lines.length : scroll, 0, block, '');
    css = lines.join('\n');
  }
  css = css.replace(/\n{4,}/g, '\n\n\n').replace(/\s+$/, '\n');
  if (eol === '\r\n') css = css.replace(/\n/g, '\r\n');
  fs.writeFileSync(cssPath, css);

  report.push({
    id,
    primary: pal.primary,
    canvas: pal.canvas,
    orphans_removed: stripped.dropped,
    product_tokens: [...extras.keys()],
  });
}

console.log('product            | primary | canvas  | orphans removed | product tokens kept');
console.log('-------------------|---------|---------|-----------------|--------------------');
for (const r of report) {
  console.log(
    `${r.id.padEnd(18)} | ${r.primary} | ${r.canvas} | ${String(r.orphans_removed).padStart(15)} | ${r.product_tokens.length}` +
      (r.product_tokens.length ? ` (${r.product_tokens.slice(0, 4).join(', ')}${r.product_tokens.length > 4 ? ', …' : ''})` : '')
  );
}
console.log(`\ndistinct identities: ${new Set(report.map((r) => `${r.primary}|${r.canvas}`)).size} / ${report.length}`);
