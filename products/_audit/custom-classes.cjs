/** Reports component class names that look custom (not Tailwind utilities) and are not
 *  defined in the product's index.css, so a rebuilt stylesheet cannot silently orphan one. */
const fs = require('fs');
const p = require('path');

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

const TAILWIND_LIKE =
  /^(?:[a-z-]+:)?(?:flex|grid|block|inline|hidden|relative|absolute|fixed|sticky|static|isolate|w-|h-|size-|min-|max-|p[xytblr]?-|m[xytblr]?-|gap-|space-|text-|bg-|border|rounded|shadow|font-|leading|tracking|opacity-|z-|top-|left-|right-|bottom-|inset-|translate|scale-|rotate|transition|duration|ease-|animate-|overflow|object-|cursor-|select-|pointer-|items-|justify-|self-|flex-|order-|col-|row-|aspect-|backdrop-|ring|outline|divide-|truncate|whitespace|break-|uppercase|lowercase|capitalize|italic|underline|line-|list-|align-|fill-|stroke-|will-change|content-|sr-only|not-sr-only|prose|container|mx-auto|auto-cols|auto-rows|basis-|shrink|grow|grid-cols|grid-rows|place-|columns|float|clear|table|isolate|mix-blend|filter|blur|brightness|contrast|drop-shadow|grayscale|hue-rotate|invert|saturate|sepia|origin-|perspective|rotate|skew|transform|accent-|appearance|caret-|resize|scroll-|snap-|touch-|but-|uppercase)/;

const walk = (dir, out = []) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const fp = p.join(dir, e.name);
    if (e.isDirectory()) walk(fp, out);
    else out.push(fp.split(p.sep).join('/'));
  }
  return out;
};

let totalMissing = 0;
for (const id of PRODUCTS) {
  const src = `products/${id}/frontend/src`;
  const css = fs.readFileSync(`${src}/index.css`, 'utf8');
  const defined = new Set([...css.matchAll(/\.([a-zA-Z][a-zA-Z0-9_-]*)/g)].map((m) => m[1]));
  const used = new Map();
  for (const f of walk(src)) {
    if (!/\.(jsx?|css)$/.test(f) || f.endsWith('/index.css')) continue;
    const text = fs.readFileSync(f, 'utf8');
    for (const m of text.matchAll(/className="([^"]+)"/g)) {
      for (const cls of m[1].split(/\s+/)) {
        if (!cls || /[{}$[\]]/.test(cls)) continue;
        if (TAILWIND_LIKE.test(cls)) continue;
        if (cls.includes('/') || cls.includes('.')) continue;
        used.set(cls, (used.get(cls) || 0) + 1);
      }
    }
  }
  const missing = [...used].filter(([c]) => !defined.has(c)).sort((a, b) => b[1] - a[1]);
  totalMissing += missing.length;
  console.log(
    `${id.padEnd(18)} undefined custom classes: ${missing.length}` +
      (missing.length ? ` → ${missing.slice(0, 8).map(([c, n]) => `${c}(${n})`).join(', ')}` : '')
  );
}
console.log(`\ntotal undefined custom classes across 11 products: ${totalMissing}`);
