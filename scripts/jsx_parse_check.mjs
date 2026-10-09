#!/usr/bin/env node
/**
 * JSX / JS syntax check for the products in products/.
 *
 * scripts/js_parse_check.mjs parses plain JavaScript only, so it cannot verify
 * the React components. This checker uses the @babel/parser that already ships
 * in backend/node_modules - nothing is installed - and parses every .js/.jsx
 * file under the given roots with the JSX plugin enabled.
 *
 * Usage:
 *   node scripts/jsx_parse_check.mjs                 # all products
 *   node scripts/jsx_parse_check.mjs products/apex   # one product
 *
 * Prints {"checked":N,"failed":N,"failures":[...]} and exits 1 on failure.
 */
import { createRequire } from 'node:module';
import { readdirSync, statSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve, extname } from 'node:path';

const repoRoot = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const require = createRequire(join(repoRoot, 'scripts', 'noop.cjs'));

let babelParser;
try {
  babelParser = require(join(repoRoot, 'backend', 'node_modules', '@babel', 'parser'));
} catch {
  console.error('FATAL: @babel/parser not found in backend/node_modules');
  process.exit(2);
}

const roots = process.argv.slice(2);
const targets = roots.length ? roots : ['products'];

const SKIP_DIRS = new Set(['node_modules', 'dist', '.git', 'build', 'coverage']);

function walk(dir, out) {
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return out;
  }
  for (const name of entries) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(dir, name);
    let st;
    try {
      st = statSync(full);
    } catch {
      continue;
    }
    if (st.isDirectory()) walk(full, out);
    else if (['.js', '.jsx', '.mjs', '.cjs'].includes(extname(full))) out.push(full);
  }
  return out;
}

const files = [];
for (const t of targets) {
  const abs = resolve(repoRoot, t);
  if (!existsSync(abs)) {
    console.error(`no such path: ${t}`);
    process.exit(2);
  }
  if (statSync(abs).isDirectory()) walk(abs, files);
  else files.push(abs);
}

const failures = [];
for (const file of files) {
  const code = readFileSync(file, 'utf8');
  try {
    babelParser.parse(code, {
      sourceType: 'unambiguous',
      allowReturnOutsideFunction: true,
      errorRecovery: false,
      plugins: ['jsx', 'classProperties', 'optionalChaining', 'nullishCoalescingOperator', 'dynamicImport', 'topLevelAwait'],
    });
  } catch (err) {
    failures.push({ file: file.replace(repoRoot + '\\', '').replace(repoRoot + '/', ''), message: err.message });
  }
}

console.log(JSON.stringify({ checked: files.length, failed: failures.length, failures }, null, 2));
process.exit(failures.length ? 1 : 0);