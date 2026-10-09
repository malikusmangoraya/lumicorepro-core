/**
 * lucide-imports.cjs — catches the class of build breaker a bundler reports as
 * MISSING_EXPORT: a named import that lucide-react does not actually export.
 *
 * The installed package in products/flowpilot/frontend/node_modules is the reference. Every
 * product pins the same lucide-react range, so a name missing there is missing everywhere.
 *
 * --fix replaces the known aliases with their current export (Spinner → LoaderCircle).
 *
 * Run: node products/_audit/lucide-imports.cjs [--fix]
 */
const fs = require('fs');
const p = require('path');

const REFERENCE = 'products/flowpilot/frontend/node_modules/lucide-react/dist/esm/lucide-react.mjs';
const FIX = process.argv.includes('--fix');

// Names these products import that the current lucide-react no longer exports. The brand
// marks (Chrome/Github/Facebook/Linkedin/Twitter) were removed from lucide entirely, so each
// maps to the closest available glyph — the button's visible label still names the brand.
const RENAMES = {
  Spinner: 'LoaderCircle',
  Chrome: 'Globe',
  Github: 'Code2',
  Facebook: 'Users',
  Linkedin: 'Briefcase',
  Twitter: 'AtSign',
};

if (!fs.existsSync(REFERENCE)) {
  console.error(`reference package not found: ${REFERENCE}`);
  process.exit(1);
}
const source = fs.readFileSync(REFERENCE, 'utf8');
const exported = new Set([...source.matchAll(/export\s*\{([^}]+)\}/g)].flatMap((m) => m[1].split(',').map((s) => s.trim().split(/\s+as\s+/).pop()).filter(Boolean)));
for (const m of source.matchAll(/export\s+(?:const|function|class)\s+([A-Za-z0-9_]+)/g)) exported.add(m[1]);

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

const walk = (dir, out = []) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const fp = p.join(dir, e.name);
    if (e.isDirectory()) walk(fp, out);
    else out.push(fp.split(p.sep).join('/'));
  }
  return out;
};

const importRe = /import\s*\{([^}]+)\}\s*from\s*['"]lucide-react['"];?/g;
let badFiles = 0;
let fixes = 0;
const problems = [];

for (const id of PRODUCTS) {
  const src = `products/${id}/frontend/src`;
  for (const file of walk(src)) {
    if (!/\.(jsx?|mjs)$/.test(file)) continue;
    let text = fs.readFileSync(file, 'utf8');
    let changed = false;
    for (const m of [...text.matchAll(importRe)]) {
      const names = m[1].split(',').map((s) => s.trim()).filter(Boolean);
      const missing = names.filter((n) => !exported.has(n));
      if (!missing.length) continue;
      badFiles++;
      const replaced = missing.map((n) => `${n}${RENAMES[n] ? ` → ${RENAMES[n]}` : ' (no known replacement)'}`);
      problems.push(`${file.replace('products/' + id + '/frontend/src/', `${id}:`)} — ${replaced.join(', ')}`);
      if (FIX) {
        const renamed = m[0].replace(/import\s*\{([^}]+)\}/, (_all, inner) => {
          const fixed = inner
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
            .map((n) => (RENAMES[n] ? RENAMES[n] : n));
          return `import { ${fixed.join(', ')} }`;
        });
        if (renamed !== m[0]) {
          text = text.replace(m[0], renamed);
          changed = true;
        }
      }
    }
    if (changed) {
      fs.writeFileSync(file, text);
      fixes++;
    }
  }
}

console.log(`lucide-react exports available: ${exported.size}`);
console.log(`files with a missing lucide export: ${badFiles}`);
for (const line of problems) console.log('  ' + line);
if (FIX) console.log(`\nfiles rewritten with current export names: ${fixes}`);
console.log(
  badFiles === 0
    ? '\nOK — every lucide-react import resolves'
    : FIX
      ? '\nRe-run without --fix to confirm'
      : '\nRun with --fix to rename the known aliases'
);
process.exitCode = badFiles && !FIX ? 1 : 0;

