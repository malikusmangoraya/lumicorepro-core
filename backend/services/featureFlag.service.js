/**
 * Feature flags — gradual rollouts and kill-switches.
 *
 * Flags live in Postgres with an in-memory cache (60s TTL) so reads never hit
 * the DB per request. Rollout is a stable hash of (flag key + user id), so a
 * user deterministically lands in or out of the cohort across processes and
 * restarts. Unknown flags are OFF (fail-closed).
 */
import crypto from 'crypto';
import FeatureFlag from '../models/FeatureFlag.js';
import logger from '../utils/logger.js';

const CACHE_TTL_MS = 60_000;
let cache = { at: 0, flags: new Map() };

export function clearFlagCache() {
  cache = { at: 0, flags: new Map() };
}

async function loadFlags() {
  if (Date.now() - cache.at < CACHE_TTL_MS && cache.flags.size) return cache.flags;
  try {
    const rows = await FeatureFlag.findAll({ raw: true });
    cache = { at: Date.now(), flags: new Map(rows.map((r) => [r.key, r])) };
  } catch (err) {
    logger.warn(`Feature flags unavailable, failing closed: ${err.message}`);
    cache = { at: Date.now(), flags: new Map() };
  }
  return cache.flags;
}

export function rolloutBucket(flagKey, userId) {
  const digest = crypto
    .createHash('sha256')
    .update(`${flagKey}:${userId ?? 'anon'}`)
    .digest('hex');
  return parseInt(digest.slice(0, 8), 16) % 100;
}

export async function isEnabled(flagKey, userId = null) {
  const flags = await loadFlags();
  const flag = flags.get(flagKey);
  if (!flag || !flag.enabled) return false;
  const rollout = Math.max(0, Math.min(100, Number(flag.rollout ?? 100)));
  if (rollout >= 100) return true;
  if (rollout <= 0 || userId == null) return false;
  return rolloutBucket(flagKey, userId) < rollout;
}
