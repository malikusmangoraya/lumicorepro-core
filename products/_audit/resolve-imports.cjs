/**
 * resolve-imports.cjs — the static equivalent of the bundler's UNRESOLVED_IMPORT check.
 *
 * A missing module is a hard build failure, and it can hide for a long time in a project
 * nobody builds. This walks every frontend, resolves each relative / `@/` import against the
 * filesystem (extension and directory-index aware) and prints what does not exist.
 *
 * Run: node products/_audit/resolve-imports.cjs
 */
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

const walk = (dir, out = []) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const fp = p.join(dir, e.name);
    if (e.isDirectory()) walk(fp, out);
    else out.push(fp.split(p.sep).join('/'));
  }
  return out;
};

const CANDIDATE_SUFFIXES = ['', '.js', '.jsx', '.mjs', '.ts', '.tsx', '.json', '/index.js', '/index.jsx', '/index.mjs'];

function resolves(basePath) {
  return CANDIDATE_SUFFIXES.some((suffix) => {
    const candidate = `${basePath}${suffix}`;
    try {
      return fs.statSync(candidate).isFile();
    } catch {
      return false;
    }
  });
}

const specifierRe = /(?:from\s*|import\s*\()\s*['"]([^'"]+)['"]/g;
const problems = [];

for (const id of PRODUCTS) {
  const src = `products/${id}/frontend/src`;
  const files = walk(src).filter((f) => /\.(jsx?|mjs)$/.test(f));
  const missing = new Map();
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    for (const m of text.matchAll(specifierRe)) {
      const spec = m[1];
      if (!spec.startsWith('.') && !spec.startsWith('@/')) continue;
      const base = spec.startsWith('@/')
        ? p.join(src, spec.slice(2))
        : p.normalize(p.join(p.dirname(file), spec));
      if (resolves(base)) continue;
      const shown = `${file.replace(`products/${id}/frontend/src/`, '')} → ${spec}`;
      missing.set(shown, (missing.get(shown) || 0) + 1);
    }
  }
  problems.push({ id, missing: [...missing.keys()] });
}

console.log('product            | unresolved imports');
console.log('-------------------|-------------------');
let total = 0;
for (const { id, missing } of problems) {
  total += missing.length;
  console.log(`${id.padEnd(18)} | ${missing.length}`);
  for (const m of missing) console.log(`   ${m}`);
}
console.log(`\ntotal unresolved local imports: ${total}`);
process.exitCode = total ? 1 : 0;
