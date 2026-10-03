#!/usr/bin/env node
/**
 * Dependency-free bundle budget gate.
 *
 * Budgets are the gzip budgets in AGENTS.md §7:
 *   JS initial payload < 150 KB target / < 200 KB hard limit
 *   CSS initial payload < 30 KB target / < 50 KB hard limit
 *   any single JS chunk  < 200 KB target / < 300 KB hard limit
 *
 * The "initial payload" is the entry chunk plus its transitive STATIC imports --
 * what a first-time visitor on a cold cache actually downloads. That is the
 * number users feel. Summing every lazy route in the app is not a performance
 * metric: a visitor who never opens /medical-telehealth never downloads it, and
 * the sum grows every time a route is added.
 *
 * Requires `build.manifest: true` (set in vite.config.js).
 * Overrides: node scripts/check-bundle-budget.mjs --js 200 --css 50 --chunk 300
 */
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const DIST = path.resolve(process.cwd(), 'dist');
const ASSETS = path.join(DIST, 'assets');
const MANIFEST = path.join(DIST, '.vite', 'manifest.json');

const DEFAULTS = { js: 200, css: 50, chunk: 300 };

function parseArgs(argv) {
  const limits = { ...DEFAULTS };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i].replace(/^--/, '');
    if (key in limits && argv[i + 1] !== undefined) {
      limits[key] = Number(argv[i + 1]);
      i += 1;
    }
  }
  return limits;
}

const gzipSize = (file) => zlib.gzipSync(fs.readFileSync(file), { level: 9 }).length;
const kb = (bytes) => `${(bytes / 1024).toFixed(1)} KB`;

function listAssets(ext) {
  return fs
    .readdirSync(ASSETS)
    .filter((f) => f.endsWith(ext))
    .map((f) => {
      const full = path.join(ASSETS, f);
      return { name: f, raw: fs.statSync(full).size, gz: gzipSize(full) };
    })
    .sort((a, b) => b.gz - a.gz);
}

function table(rows) {
  if (rows.length === 0) return '(none)';
  const width = Math.max(12, ...rows.map((r) => r.name.length));
  const head = `${'chunk'.padEnd(width)}  ${'raw'.padStart(11)}  ${'gzip'.padStart(11)}`;
  const rule = '-'.repeat(head.length);
  return [
    head,
    rule,
    ...rows.map(
      (r) => `${r.name.padEnd(width)}  ${kb(r.raw).padStart(11)}  ${kb(r.gz).padStart(11)}`
    ),
  ].join('\n');
}

const limits = parseArgs(process.argv.slice(2));

if (!fs.existsSync(ASSETS)) {
  console.error(`No build found at ${ASSETS}. Run "npm run build" first.`);
  process.exit(2);
}
if (!fs.existsSync(MANIFEST)) {
  console.error(
    `Missing ${path.relative(DIST, MANIFEST)}. Set "build.manifest = true" in vite.config.js and rebuild.`
  );
  process.exit(2);
}

const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
const entries = Object.entries(manifest).filter(([, m]) => m.isEntry);
if (entries.length === 0) {
  console.error('Manifest contains no entry chunk.');
  process.exit(2);
}

const sizeOf = (key) => {
  const meta = manifest[key];
  if (!meta) return 0;
  const file = path.join(DIST, meta.file);
  return fs.existsSync(file) ? fs.statSync(file).size : 0;
};
const gzOf = (key) => {
  const meta = manifest[key];
  if (!meta) return 0;
  const file = path.join(DIST, meta.file);
  return fs.existsSync(file) ? gzipSize(file) : 0;
};

/** Transitive static-import closure of an entry. Dynamic imports are excluded. */
function staticClosure(entryKey) {
  const seen = new Set();
  const queue = [entryKey];
  while (queue.length > 0) {
    const key = queue.pop();
    if (seen.has(key)) continue;
    seen.add(key);
    for (const dep of manifest[key]?.imports ?? []) {
      if (!seen.has(dep)) queue.push(dep);
    }
  }
  return seen;
}

const results = entries.map(([key, meta]) => {
  const closure = staticClosure(key);
  let raw = 0;
  let gz = 0;
  let cssRaw = 0;
  let cssGz = 0;
  const jsChunks = [];
  const cssFiles = [];
  for (const dep of closure) {
    if (manifest[dep]?.file?.endsWith('.js')) {
      raw += sizeOf(dep);
      gz += gzOf(dep);
      jsChunks.push({ name: path.basename(manifest[dep].file), raw: sizeOf(dep), gz: gzOf(dep) });
    }
    for (const cssRel of manifest[dep]?.css ?? []) {
      const file = path.join(DIST, cssRel);
      if (!fs.existsSync(file)) continue;
      cssRaw += fs.statSync(file).size;
      cssGz += gzipSize(file);
      cssFiles.push({ name: path.basename(cssRel), raw: fs.statSync(file).size, gz: gzipSize(file) });
    }
  }
  return {
    entry: meta.file,
    raw,
    gz,
    cssRaw,
    cssGz,
    jsChunks: jsChunks.sort((a, b) => b.gz - a.gz),
    cssFiles: cssFiles.sort((a, b) => b.gz - a.gz),
    chunkCount: jsChunks.length,
  };
});

const allJs = listAssets('.js');
const allCss = listAssets('.css');
const biggest = allJs[0];
const allJsGz = allJs.reduce((s, c) => s + c.gz, 0);

console.log(
  `Bundle budget — limits: initial JS ${kb(limits.js * 1024)}, initial CSS ${kb(limits.css * 1024)}, largest JS chunk ${kb(limits.chunk * 1024)}\n`
);

for (const r of results) {
  console.log(`ENTRY ${r.entry}`);
  console.log(
    `  initial payload: js ${kb(r.gz)} gzip (${kb(r.raw)} raw) across ${r.chunkCount} chunk(s), ` +
      `css ${kb(r.cssGz)} gzip (${kb(r.cssRaw)} raw)\n`
  );
  console.log(`  js on critical path\n${table(r.jsChunks)}\n`);
  if (r.cssFiles.length > 0) console.log(`  css on critical path\n${table(r.cssFiles)}\n`);
}

console.log(
  `LARGEST JS CHUNK (any route)  ${biggest.name} ${kb(biggest.gz)} gzip\n` +
    `ALL CHUNKS COMBINED          js ${kb(allJsGz)} gzip, css ${kb(allCss.reduce((s, c) => s + c.gz, 0))} gzip ` +
    `across ${allJs.length} js / ${allCss.length} css file(s) (informational, not gated)\n`
);

const failures = [];
for (const r of results) {
  if (r.gz > limits.js * 1024) {
    failures.push(`initial JS for ${r.entry} ${kb(r.gz)} > ${kb(limits.js * 1024)}`);
  }
  if (r.cssGz > limits.css * 1024) {
    failures.push(`initial CSS for ${r.entry} ${kb(r.cssGz)} > ${kb(limits.css * 1024)}`);
  }
}
if (biggest.gz > limits.chunk * 1024) {
  failures.push(`chunk ${biggest.name} ${kb(biggest.gz)} > ${kb(limits.chunk * 1024)}`);
}

if (failures.length > 0) {
  console.error(`FAIL — ${failures.length} budget violation(s):`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

console.log('PASS — gzip budgets satisfied (AGENTS.md §7)');
