/**
 * cache.mjs — the "stop re-reading everything" layer.
 *
 * The engine records a tiny signature per app (stage + size of the handful of
 * files the rules actually touch). A later run stats those few paths, and when
 * the signature and the rule fingerprint both match, the app is skipped without
 * opening a single source file.
 *
 * The manifest lives under node_modules/.cache so no .gitignore change is
 * needed and nothing lands in the repository.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export const CACHE_REL = path.join('node_modules', '.cache', 'lumi-upgrade', 'manifest.json');

export function hashOf(value) {
  return crypto.createHash('sha1').update(String(value)).digest('hex').slice(0, 16);
}

export function statSignature(absPath) {
  try {
    const stat = fs.statSync(absPath);
    return `${Math.round(stat.mtimeMs)}:${stat.size}`;
  } catch {
    return 'missing';
  }
}

export function loadCache(root) {
  const abs = path.join(root, CACHE_REL);
  try {
    const parsed = JSON.parse(fs.readFileSync(abs, 'utf8'));
    if (parsed && typeof parsed === 'object' && parsed.apps) return parsed;
  } catch {
    /* first run, or a corrupt manifest: start clean */
  }
  return { version: 1, apps: {} };
}

export function saveCache(root, cache) {
  const abs = path.join(root, CACHE_REL);
  try {
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, `${JSON.stringify(cache, null, 2)}\n`, 'utf8');
  } catch {
    /* the cache is an optimisation; a failure to persist it must not fail the run */
  }
}
