/**
 * engine.mjs — the upgrade engine.
 *
 * Responsibilities, in order: discover app targets, decide which ones the cache
 * lets us skip, run the rule set over the rest, and report only what changed.
 * Rules never touch the filesystem themselves; they return operations and the
 * engine performs them, which is what makes dry-run and diff-free idempotency
 * possible.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadCache, saveCache, hashOf, statSignature } from './cache.mjs';
import { appendBlock, insertBefore, readIfExists, writeFileEnsuringDir } from './util.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const DEFAULT_ROOTS = [path.join('products', 'sell-today'), 'products'];

export function listRules(rules) {
  return rules.map((rule) => ({
    id: rule.id,
    version: rule.version,
    title: rule.title,
    watch: rule.watch || [],
  }));
}

export function ruleFingerprint(rules) {
  return hashOf(rules.map((rule) => `${rule.id}@${rule.version}`).join('|'));
}

function isAppDir(dir) {
  return (
    fs.existsSync(path.join(dir, 'package.json')) && fs.existsSync(path.join(dir, 'src', 'main.jsx'))
  );
}

/** An app is `<root>/<slug>/frontend`, falling back to `<root>/<slug>`. */
export function discoverApps({ roots = [], apps = [] } = {}) {
  const searchRoots = roots.length ? roots : DEFAULT_ROOTS;
  const found = new Map();

  for (const relOrAbs of searchRoots) {
    const abs = path.isAbsolute(relOrAbs) ? relOrAbs : path.join(ROOT, relOrAbs);
    let entries;
    try {
      entries = fs.readdirSync(abs, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
      const base = path.join(abs, entry.name);
      const candidates = [path.join(base, 'frontend'), base];
      const dir = candidates.find(isAppDir);
      if (dir && !found.has(entry.name)) {
        found.set(entry.name, { id: entry.name, dir, srcDir: path.join(dir, 'src') });
      }
    }
  }

  const all = [...found.values()].sort((a, b) => a.id.localeCompare(b.id));
  if (!apps.length) return all;
  const wanted = new Set(apps);
  return all.filter((app) => wanted.has(app.id));
}

function createContext(app) {
  const reads = new Map();
  const notes = [];
  const abs = (rel) => path.join(app.dir, rel);
  return {
    app,
    notes,
    note(message) {
      notes.push(message);
    },
    has(rel) {
      return fs.existsSync(abs(rel));
    },
    get(rel) {
      if (!reads.has(rel)) reads.set(rel, readIfExists(abs(rel)));
      return reads.get(rel);
    },
    /** All files the rules declared interest in, for the cache signature. */
    statAll() {
      return reads;
    },
  };
}

function applyOp(app, op, options) {
  const target = path.join(app.dir, op.path);
  const current = readIfExists(target);

  if (op.kind === 'remove') {
    if (current === null) return { status: 'unchanged', path: op.path };
    if (!options.dryRun) fs.rmSync(target, { force: true });
    return { status: 'written', path: op.path };
  }

  if (current === op.content) return { status: 'unchanged', path: op.path };
  if (!options.dryRun) writeFileEnsuringDir(target, op.content);
  return { status: current === null ? 'created' : 'written', path: op.path };
}

/**
 * Run the configured rule set.
 * @returns {{ apps: object[], rules: object[], fingerprint: string, elapsedMs: number, totals: object }}
 */
export function runUpgrade({ rules, options = {} }) {
  const startedAt = process.hrtime.bigint();
  const fingerprint = ruleFingerprint(rules);
  const apps = discoverApps(options);
  const cache = loadCache(ROOT);
  const results = [];

  for (const app of apps) {
    const watch = [...new Set(rules.flatMap((rule) => rule.watch || []))].sort();
    const signature = watch.map((rel) => `${rel}=${statSignature(path.join(app.dir, rel))}`).join(';');
    const previous = cache.apps[app.id];

    if (
      !options.force &&
      previous &&
      previous.fingerprint === fingerprint &&
      previous.signature === signature &&
      previous.outcome !== 'error'
    ) {
      results.push({ id: app.id, outcome: 'skipped', cached: true, files: [], notes: [], ms: 0 });
      continue;
    }

    const appStart = process.hrtime.bigint();
    const ctx = createContext(app);
    const files = [];
    const notes = [];
    let outcome = 'updated';

    try {
      for (const rule of rules) {
        let ops = [];
        try {
          ops = rule.plan(ctx) || [];
        } catch (error) {
          notes.push(`${rule.id}: ${error.message}`);
          outcome = 'error';
          continue;
        }
        for (const op of ops) {
          if (op.kind === 'skip') {
            notes.push(`${rule.id}: ${op.note || 'not applicable'}`);
            continue;
          }
          const applied = applyOp(app, op, options);
          if (applied.status !== 'unchanged') files.push({ path: op.path, rule: rule.id, status: applied.status });
        }
      }
      notes.push(...ctx.notes);
      if (!files.length) outcome = notes.length ? 'review' : 'clean';
    } catch (error) {
      notes.push(error.message);
      outcome = 'error';
    }

    const ms = Number(process.hrtime.bigint() - appStart) / 1e6;
    results.push({ id: app.id, outcome, cached: false, files, notes, ms });

    // Re-stat after the writes: storing the pre-write signature would mismatch on
    // the next run for every file the rules just created or touched, which would
    // cost the cache hit exactly once per upgrade.
    const settled = watch
      .map((rel) => `${rel}=${statSignature(path.join(app.dir, rel))}`)
      .join(';');
    cache.apps[app.id] = { fingerprint, signature: settled, outcome, watched: watch };
  }

  if (!options.dryRun) saveCache(ROOT, cache);

  const totals = results.reduce(
    (acc, result) => {
      acc.apps += 1;
      acc.files += result.files.length;
      if (result.outcome === 'skipped') acc.skipped += 1;
      if (result.outcome === 'clean') acc.clean += 1;
      if (result.outcome === 'review') acc.review += 1;
      if (result.outcome === 'error') acc.errors += 1;
      return acc;
    },
    { apps: 0, files: 0, skipped: 0, clean: 0, review: 0, errors: 0 }
  );

  return {
    apps: results,
    rules: listRules(rules),
    fingerprint,
    elapsedMs: Number(process.hrtime.bigint() - startedAt) / 1e6,
    totals,
  };
}

export { appendBlock, insertBefore };
