/**
 * Read-only diagnostic: trace the entry chunk's STATIC import graph and report
 * which source modules pull which heavy third-party packages onto first paint.
 *
 * Uses dist/.vite/manifest.json (requires build.manifest: true).
 * Usage: node scripts/trace-critical-path.mjs [--why framer-motion]
 */
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const DIST = path.resolve(process.cwd(), 'dist');
const MANIFEST = path.join(DIST, '.vite', 'manifest.json');

const argv = process.argv.slice(2);
const whyIdx = argv.indexOf('--why');
const WHY = whyIdx !== -1 ? argv[whyIdx + 1] : null;

if (!fs.existsSync(MANIFEST)) {
  console.error('No dist/.vite/manifest.json - run `npm run build` first.');
  process.exit(1);
}

const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));

// The entry is the manifest key that isIsEntry
const entryKey = Object.keys(manifest).find((k) => manifest[k].isEntry);
if (!entryKey) {
  console.error('No isEntry chunk in manifest.');
  process.exit(1);
}

/** Walk static imports (not dynamic) from the entry. */
function staticGraph() {
  const seen = new Set();
  const parents = new Map();
  const stack = [entryKey];

  while (stack.length) {
    const key = stack.pop();
    if (seen.has(key)) continue;
    seen.add(key);

    const node = manifest[key];
    if (!node) continue;

    for (const imp of node.imports || []) {
      if (imp.startsWith('node_modules/')) continue; // dynamic only
      if (parents.has(imp)) continue;
      parents.set(imp, key);
      stack.push(imp);
    }
  }
  return { keys: seen, parents };
}

const { keys, parents } = staticGraph();

/** Chunks in the first-paint graph, with their on-disk gzip size. */
function gz(file) {
  const full = path.join(DIST, file);
  if (!fs.existsSync(full)) return 0;
  return zlib.gzipSync(fs.readFileSync(full), { level: 9 }).length;
}

const rows = [];
let total = 0;
for (const key of keys) {
  const node = manifest[key];
  if (!node) continue;
  const bytes = gz(node.file);
  total += bytes;
  rows.push({ name: node.name || key, file: node.file, kb: bytes / 1024 });
}
rows.sort((a, b) => b.kb - a.kb);

console.log(`\nENTRY: ${entryKey}  (${keys.size} static chunks, ${(total / 1024).toFixed(1)} KB gzip)\n`);
for (const r of rows) {
  console.log(`  ${r.kb.toFixed(1).padStart(8)} KB  ${r.file}`);
}

if (WHY) {
  console.log(`\n--- Why is "${WHY}" on the critical path? ---`);
  const target = Array.from(keys).find(
    (k) => (manifest[k]?.name || k).includes(WHY) || manifest[k]?.file?.includes(WHY),
  );
  if (!target) {
    console.log(`  "${WHY}" is NOT in the entry's static graph (it is lazy - good).`);
  } else {
    // Walk back to the entry printing the chain
    const chain = [target];
    let cur = target;
    while (parents.has(cur) && cur !== entryKey) {
      cur = parents.get(cur);
      chain.unshift(cur);
    }
    for (let i = 0; i < chain.length; i += 1) {
      const n = manifest[chain[i]];
      const arrow = i === 0 ? '' : '  <- ';
      console.log(`  ${arrow}${(n?.name || chain[i]).padEnd(28)} ${n?.file || ''}`);
    }
  }
}
