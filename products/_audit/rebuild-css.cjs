/**
 * rebuild-css.cjs — rebuild every product's src/index.css from one validated template.
 *
 * Why rebuild rather than patch: an earlier whole-file rewrite in this session cut
 * unbalanced regions out of nine of these stylesheets, and there is no committed revision to
 * restore them from. Every product shares the same template layers (buttons, section
 * headings, lumi-motion, hero-video, skip-link, scrollbars) and differs only in its palette,
 * its fonts and its own extra --t-* tokens, all three of which are carried over here. The
 * output is validated with postcss before the script reports success.
 */
const fs = require('fs');
const p = require('path');
const postcss = require('postcss');

const ROOT = 'products';
const PRODUCT_TOKENS = JSON.parse(fs.readFileSync(`${ROOT}/_audit/product-tokens.json`, 'utf8'));

const PALETTE = {
  apex: { canvas: '#f4f8ff', surface: '#ffffff', primary: '#0891b2', accent: '#7c4dff', heading: '#0b1b33', text: '#1f2937', muted: '#64748b', border: '#dbe4f0', footer: '#071a2b', displayFont: 'Orbitron', sansFont: 'Inter' },
  flowpilot: { canvas: '#f2faf6', surface: '#ffffff', primary: '#059669', accent: '#6366f1', heading: '#052e26', text: '#1f2937', muted: '#64748b', border: '#d6ece4', footer: '#052e26', displayFont: 'Space Grotesk', sansFont: 'Inter' },
  'aurelia-estates': { canvas: '#ffffff', surface: '#ffffff', primary: '#be2c2c', accent: '#821616', heading: '#5b3200', text: '#26292f', muted: '#be2c2c', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Inter', sansFont: 'Inter' },
  'aurum-fitness': { canvas: '#ffffff', surface: '#ffffff', primary: '#be882c', accent: '#ec4899', heading: '#be882c', text: '#26292f', muted: '#be882c', border: '#f0e2c8', footer: '#0e1116', displayFont: 'Outfit', sansFont: 'Inter' },
  'claimflow-ai': { canvas: '#f8fafc', surface: '#ffffff', primary: '#374151', accent: '#dc2626', heading: '#111827', text: '#26292f', muted: '#64748b', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Helvetica Neue', sansFont: 'Helvetica Neue' },
  'meridian-capital': { canvas: '#f8fafc', surface: '#ffffff', primary: '#be2c92', accent: '#be2c92', heading: '#be2c92', text: '#26292f', muted: '#be2c92', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Inter', sansFont: 'Inter' },
  'nuage-events': { canvas: '#f8fafc', surface: '#ffffff', primary: '#be2c4e', accent: '#82162f', heading: '#5b3200', text: '#26292f', muted: '#be2c4e', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Inter', sansFont: 'Inter' },
  'prestige-studio': { canvas: '#f8fafc', surface: '#ffffff', primary: '#be502c', accent: '#be502c', heading: '#be502c', text: '#26292f', muted: '#be502c', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Helvetica Neue', sansFont: 'Helvetica Neue' },
  resupro: { canvas: '#f8fafc', surface: '#ffffff', primary: '#be2c44', accent: '#059669', heading: '#be2c44', text: '#26292f', muted: '#be2c44', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Helvetica Neue', sansFont: 'Helvetica Neue' },
  'saffron-voyage': { canvas: '#f8fafc', surface: '#ffffff', primary: '#be702c', accent: '#f59e0b', heading: '#be702c', text: '#26292f', muted: '#be702c', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Inter', sansFont: 'Inter' },
  'studio-lumen': { canvas: '#ffffff', surface: '#ffffff', primary: '#ea580c', accent: '#16a34a', heading: '#451a03', text: '#26292f', muted: '#be692c', border: '#e2e8f0', footer: '#0e1116', displayFont: 'Outfit', sansFont: 'Inter' },
};

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

const PALETTE_KEYS = ['canvas', 'surface', 'primary', 'accent', 'heading', 'text', 'muted', 'border', 'footer'];
const hex2rgb = (hex) => [0, 2, 4].map((i) => parseInt(hex.slice(1 + i, 3 + i), 16)).join(' ');

/** The shared template. Every brand-specific value comes from `pal`. */
const TEMPLATE = (pal, extras) => `@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    background-color: var(--t-canvas);
    @apply antialiased;
    font-family: '${pal.sansFont}', system-ui, -apple-system, 'Segoe UI', sans-serif;
    color: var(--t-text);
  }
  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    font-family: '${pal.displayFont}', '${pal.sansFont}', system-ui, sans-serif;
    font-weight: 700;
    color: var(--t-heading);
  }
}

@layer components {
  .btn-primary {
    background-color: var(--t-primary);
    color: #ffffff;
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }
  .btn-primary:hover {
    opacity: 0.92;
    transform: translateY(-1px);
    box-shadow: 0 8px 20px color-mix(in srgb, var(--t-primary) 30%, transparent);
  }
  .btn-outline {
    border: 2px solid var(--t-heading);
    color: var(--t-heading);
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }
  .btn-outline:hover {
    background-color: var(--t-heading);
    color: #ffffff;
  }
  .skeleton-shimmer {
    background: linear-gradient(90deg, var(--t-border) 25%, var(--t-canvas) 50%, var(--t-border) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }
  .cls-reserve {
    content-visibility: auto;
    contain-intrinsic-size: 0 500px;
  }
  .glass-md {
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    background: color-mix(in srgb, var(--t-surface) 70%, transparent);
    border: 1px solid color-mix(in srgb, var(--t-border) 70%, transparent);
  }
  .card-panel {
    background: var(--t-surface);
    border: 1px solid var(--t-border);
    border-radius: 0.875rem;
    box-shadow: 0 6px 18px color-mix(in srgb, var(--t-heading) 10%, transparent);
  }
}

@layer utilities {
  .section-eyebrow {
    font-family: '${pal.sansFont}', system-ui, sans-serif;
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--t-primary);
    margin-bottom: 0.5rem;
    display: inline-block;
    position: relative;
    padding-left: 3rem;
  }
  .section-eyebrow::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    width: 2.5rem;
    height: 2px;
    background-color: var(--t-primary);
  }
  .section-heading {
    font-size: 2rem;
    font-weight: 800;
    color: var(--t-heading);
    line-height: 1.2;
  }
  .section-heading .accent {
    color: var(--t-primary);
  }
  .card-lift {
    transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
      box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .card-lift:hover {
    transform: translateY(-6px);
    box-shadow: var(--t-shadow-lift, 0 12px 32px rgba(0, 0, 0, 0.18));
  }
  .fluid-container {
    width: 100%;
    max-width: 1280px;
    margin-inline: auto;
    padding-inline: clamp(1rem, 5vw, 4rem);
  }
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

:root {
${FLUID_SCALE.map((l) => `  ${l}`).join('\n')}
${PALETTE_KEYS.map((k) => `  --t-${k}: ${pal[k]};`).join('\n')}
  --t-bg: #ffffff;${extras.length ? '\n\n  /* Product tokens carried over from the previous revision. */\n' + extras.map(([k, v]) => `  ${k}: ${v};`).join('\n') : ''}

${PALETTE_KEYS.filter((k) => /^#[0-9a-f]{6}$/i.test(pal[k])).map((k) => `  --t-${k}-rgb: ${hex2rgb(pal[k])};`).join('\n')}
}

::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: var(--t-canvas);
}
::-webkit-scrollbar-thumb {
  background: var(--t-muted);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--t-primary);
}

@media (max-width: 768px) {
  .section-heading {
    font-size: 1.5rem;
  }
}

.hero-aurora {
  background: linear-gradient(180deg, var(--t-surface) 0%, var(--t-border) 100%);
}

/* ===== lumi-motion (advanced animation layer) ===== */
/* Both reveal APIs are kept: utils/lumi-motion.js toggles .lumi-in, while the shared
   section components set data-reveal and toggle .revealed. */
[data-reveal] {
  opacity: 0;
  transform: translateY(24px);
  transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
[data-reveal].revealed {
  opacity: 1;
  transform: none;
}
.lumi-reveal {
  opacity: 0;
  transform: translate3d(0, var(--lumi-y, 28px), 0) scale(var(--lumi-s, 1));
  transition:
    opacity 0.72s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.72s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--lumi-d, 0ms);
}
.lumi-reveal[data-reveal='left'] { --lumi-y: 0px; transform: translate3d(-32px, 0, 0) scale(var(--lumi-s, 1)); }
.lumi-reveal[data-reveal='right'] { --lumi-y: 0px; transform: translate3d(32px, 0, 0) scale(var(--lumi-s, 1)); }
.lumi-reveal[data-reveal='scale'] { --lumi-y: 0px; --lumi-s: 0.94; }
.lumi-reveal.lumi-in {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
  will-change: auto;
}

/* Scroll progress */
.lumi-progress {
  position: fixed;
  inset: 0 auto auto 0;
  height: 3px;
  width: 100%;
  transform: scale3d(var(--lumi-progress, 0), 1, 1);
  transform-origin: 0 50%;
  background: linear-gradient(90deg, var(--t-primary), var(--t-accent));
  z-index: 9999;
  pointer-events: none;
  will-change: transform;
}

/* Counters */
.lumi-count { font-variant-numeric: tabular-nums; }

/* Magnetic + tilt targets */
.lumi-card {
  transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.34s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
.lumi-card:hover {
  transform: translate3d(0, -4px, 0);
  box-shadow: 0 18px 42px color-mix(in srgb, var(--t-heading) 18%, transparent);
}

/* Floating accents */
.lumi-float { animation: lumiFloat 7s ease-in-out infinite; }
@keyframes lumiFloat {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(0, -10px, 0); }
}

/* Loading shimmer */
.lumi-shimmer {
  background-image: linear-gradient(
    100deg,
    transparent 20%,
    color-mix(in srgb, var(--t-heading) 7%, transparent) 50%,
    transparent 80%
  );
  background-size: 220% 100%;
  animation: lumiShimmer 1.6s linear infinite;
}
@keyframes lumiShimmer {
  from { background-position: 180% 0; }
  to { background-position: -80% 0; }
}

/* Parallax backdrop */
.lumi-parallax { will-change: transform; }

@media (prefers-reduced-motion: reduce) {
  [data-reveal] { opacity: 1 !important; transform: none !important; transition: none !important; }
  .lumi-reveal { opacity: 1 !important; transform: none !important; transition: none !important; }
  .lumi-card, .lumi-float, .lumi-shimmer { animation: none !important; transition: none !important; }
  .lumi-progress { display: none !important; }
  .lumi-parallax { transform: none !important; }
}
/* ===== end lumi-motion ===== */

/* ===== hero-video (cinematic background layer) ===== */
.hero-video {
  position: relative;
  overflow: hidden;
  border-radius: 1rem;
  background: var(--t-heading);
  border: 1px solid var(--t-border);
  box-shadow: 0 24px 60px -24px color-mix(in srgb, var(--t-heading) 55%, transparent);
  isolation: isolate;
}
.hero-video-poster,
.hero-video-el {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.hero-video-poster {
  animation: hero-video-drift 22s ease-in-out infinite alternate;
}
@keyframes hero-video-drift {
  from { transform: scale(1); }
  to { transform: scale(1.07); }
}
.hero-video-el {
  opacity: 0;
  transition: opacity 900ms ease;
}
.hero-video.is-ready .hero-video-el { opacity: 1; }
.hero-video.is-ready .hero-video-poster { animation: none; }
.hero-video-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 46%, color-mix(in srgb, var(--t-heading) 62%, transparent) 100%);
  pointer-events: none;
}
.hero-video-caption {
  position: absolute;
  left: 1rem;
  bottom: 0.9rem;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin: 0;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #f8fafc;
  background: color-mix(in srgb, var(--t-heading) 55%, transparent);
  backdrop-filter: blur(6px);
}
.hero-video-caption::before {
  content: '';
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 999px;
  background: var(--t-accent);
}
@media (prefers-reduced-motion: reduce) {
  .hero-video-poster { animation: none !important; }
  .hero-video-el { transition: none !important; }
}
/* ===== end hero-video ===== */

/* ===== skip-link (keyboard access) ===== */
.skip-link {
  position: absolute;
  left: 1rem;
  top: -4rem;
  z-index: 100;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #f8fafc;
  background: var(--t-heading);
  text-decoration: none;
  transition: top 160ms ease;
}
.skip-link:focus-visible {
  top: 0.75rem;
  outline: 2px solid var(--t-primary);
  outline-offset: 2px;
}
/* ===== end skip-link ===== */
`;

const report = [];
for (const [id, pal] of Object.entries(PALETTE)) {
  const cssPath = `${ROOT}/${id}/frontend/src/index.css`;
  const extras = Object.entries(PRODUCT_TOKENS[id] || {});
  const css = TEMPLATE(pal, extras);

  // Validated before it is written: a stylesheet that cannot be parsed must never land.
  let roots = 0;
  try {
    const rootNode = postcss.parse(css);
    rootNode.walkRules((rule) => {
      if (rule.selector === ':root') roots++;
    });
  } catch (error) {
    report.push({ id, ok: false, error: `${error.reason} @${error.line}` });
    continue;
  }

  const declared = [...css.matchAll(/--t-([a-z-]+):/g)].map((m) => m[1]);
  const missing = PALETTE_KEYS.filter((k) => !declared.includes(k));
  const unused = PALETTE_KEYS.filter((k) => !css.includes(`var(--t-${k}`));
  fs.writeFileSync(cssPath, css.replace(/\n/g, '\r\n'));
  report.push({
    id,
    ok: roots === 1 && missing.length === 0,
    roots,
    missing,
    unused,
    bytes: css.length,
    primary: pal.primary,
    displayFont: pal.displayFont,
  });
}

console.log('product            | ok | rootRules | bytes | primary | displayFont');
console.log('-------------------|----|-----------|-------|---------|------------');
for (const r of report) {
  console.log(
    `${r.id.padEnd(18)} | ${r.ok ? 'ok' : 'NO'} | ${String(r.roots ?? '-').padStart(9)} | ${String(r.bytes ?? '-').padStart(5)} | ${r.primary ?? '-'} | ${r.displayFont ?? r.error}`
  );
}
const failed = report.filter((r) => !r.ok);
console.log(`\n${report.length - failed.length}/${report.length} stylesheets rebuilt and parsed`);
const unusedTokens = report.flatMap((r) => r.unused.map((k) => `${r.id}:--t-${k}`));
if (unusedTokens.length) console.log(`declared but never referenced: ${unusedTokens.join(', ')}`);
process.exitCode = failed.length ? 1 : 0;
