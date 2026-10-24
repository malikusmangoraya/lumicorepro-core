import { describe, it, expect } from '@jest/globals';
import path from 'path';
import nodeModule from 'node:module';
import { promises as fs } from 'fs';
import { pathToFileURL, fileURLToPath } from 'url';

/**
 * Module resolution smoke gate.
 *
 * A static `import` of a package that is not in package.json aborts the whole
 * backend at boot, and no route test can see it if nothing imports that module
 * in the test graph — that is how `@socket.io/redis-adapter` shipped unwired
 * while its own suite could not even load. This walks every backend module and
 * fails on any unresolved dependency.
 */

const BACKEND_ROOT = path.resolve(fileURLToPath(import.meta.url), '../../..');
const SCAN_DIRS = ['services', 'routes', 'middleware', 'models', 'utils', 'config'];

// Modules that bind a port, open a pool, or start consumers on import are
// covered by their own suites; this gate only parses their import graph.
const SIDE_EFFECT_MODULES = new Set([
  'server.js',
  'workers/worker.js',
  'config/database.js',
]);

const PACKAGE_JSON = JSON.parse(
  await fs.readFile(path.join(BACKEND_ROOT, 'package.json'), 'utf8'),
);
const DECLARED = new Set([
  ...Object.keys(PACKAGE_JSON.dependencies || {}),
  ...Object.keys(PACKAGE_JSON.devDependencies || {}),
]);

const NODE_BUILTINS = new Set([
  ...nodeModule.builtinModules,
  ...nodeModule.builtinModules.map((m) => `node:${m}`),
]);

const STATIC_IMPORT = /(?:^|\n)\s*(?:import|export)[^;'"]*?from\s*['"]([^'"]+)['"]/g;
const BARE_IMPORT = /(?:^|\n)\s*import\s+['"]([^'"]+)['"]/g;
const DYNAMIC_IMPORT = /\bimport\(\s*['"]([^'"]+)['"]\s*\)/g;

function specifiersOf(source) {
  const found = new Set();
  for (const pattern of [STATIC_IMPORT, BARE_IMPORT, DYNAMIC_IMPORT]) {
    const regex = new RegExp(pattern.source, pattern.flags);
    let match;
    while ((match = regex.exec(source)) !== null) found.add(match[1]);
  }
  return [...found];
}

function packageNameOf(specifier) {
  if (specifier.startsWith('.') || specifier.startsWith('/') || specifier.startsWith('#')) {
    return null;
  }
  const bare = specifier.replace(/^node:/, '');
  const parts = bare.split('/');
  return bare.startsWith('@') ? `${parts[0]}/${parts[1]}` : parts[0];
}

async function listModules() {
  const files = [];
  for (const dir of SCAN_DIRS) {
    const absolute = path.join(BACKEND_ROOT, dir);
    const exists = await fs.stat(absolute).then(() => true).catch(() => false);
    if (!exists) continue;
    const entries = await fs.readdir(absolute, { recursive: true, withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isFile() || !entry.name.endsWith('.js')) continue;
      const parent = entry.parentPath || entry.path;
      if (!String(parent).startsWith(absolute)) continue;
      const full = path.join(parent, entry.name);
      const rel = path.relative(BACKEND_ROOT, full).split(path.sep).join('/');
      files.push({ rel, full });
    }
  }
  return files.sort((a, b) => a.rel.localeCompare(b.rel));
}

async function readSources(modules) {
  const out = [];
  for (const { rel, full } of modules) {
    out.push({ rel, full, source: await fs.readFile(full, 'utf8') });
  }
  return out;
}

const modules = await listModules();
const sources = await readSources(modules);

describe('backend module graph', () => {
  it('finds the modules to scan', () => {
    expect(modules.length).toBeGreaterThan(40);
  });

  it('imports only packages declared in package.json', () => {
    const undeclared = [];
    for (const { rel, source } of sources) {
      for (const specifier of specifiersOf(source)) {
        const pkg = packageNameOf(specifier);
        if (!pkg) continue;
        if (NODE_BUILTINS.has(pkg) || NODE_BUILTINS.has(specifier) || DECLARED.has(pkg)) continue;
        undeclared.push(`${rel} -> ${specifier}`);
      }
    }
    expect(undeclared).toEqual([]);
  });

  it('resolves every relative import to a real file', async () => {
    const missing = [];
    for (const { rel, full, source } of sources) {
      for (const specifier of specifiersOf(source)) {
        if (!specifier.startsWith('.')) continue;
        const target = path.resolve(path.dirname(full), specifier);
        const exists = await fs.stat(target).then(() => true).catch(() => false);
        if (!exists) missing.push(`${rel} -> ${specifier}`);
      }
    }
    expect(missing).toEqual([]);
    // One fs.stat per relative specifier across the whole tree: under a parallel
    // worker pool that comfortably passes 5 s, so it gets its own budget.
  }, 30000);

  it('loads every side-effect-free module without an unresolved dependency', async () => {
    const failures = [];
    for (const { rel, full } of modules) {
      if (SIDE_EFFECT_MODULES.has(rel)) continue;
      try {
        await import(pathToFileURL(full).href);
      } catch (err) {
        const message = String(err?.message || err);
        if (/Cannot find module|ERR_MODULE_NOT_FOUND|Cannot find package/.test(message)) {
          failures.push(`${rel}: ${message.split('\n')[0]}`);
        }
      }
    }
    expect(failures).toEqual([]);
  }, 120000);

  it('declares the socket scaling adapter the service imports', () => {
    expect(DECLARED.has('@socket.io/redis-adapter')).toBe(true);
  });
});
