"""Fix the same redis.client.js and license.js bugs in all generated projects."""
import glob
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

# --- redis.client.js fix ---
REDIS_OLD = """function getFallback() {
  if (!fallback) {
    fallback = {
      __memory: true,
      isMemory: true,
      async get(k) { return memoryStore.get(k) ?? null; },
      async set(k, v, mode, ttl) {
        memoryStore.set(k, v);
        if (mode === 'EX' && ttl) {
          setTimeout(() => memoryStore.delete(k), ttl * 1000);
        }
        return 'OK';
      },
      async del(...keys) { keys.forEach((k) => memoryStore.delete(k)); return keys.length; },
      async incrby(k, n) { const next = (Number(memoryStore.get(k)) || 0) + n; memoryStore.set(k, String(next)); return next; },
      async expire() { return 1; },
      async ttl() { return -1; },
      async exists(...keys) { return keys.some((k) => memoryStore.has(k)) ? 1 : 0; },
      async keys(p = '*') {
        const re = new RegExp('^' + p.replace(/\\*/g, '.*') + '$');
        return [...memoryStore.keys()].filter((k) => re.test(k));
      },
      async sadd(key, member) {
        const list = memoryStore.get(key) ? memoryStore.get(key).split(',') : [];
        if (!list.includes(member)) list.push(member);
        memoryStore.set(key, list.join(','));
        return 1;
      },
      async smembers(key) {
        const raw = memoryStore.get(key);
        return raw ? raw.split(',').filter(Boolean) : [];
      },
      async srem(key, ...members) {
        const list = memoryStore.get(key) ? memoryStore.get(key).split(',') : [];
        const before = list.length;
        const next = list.filter((m) => !members.includes(m));
        memoryStore.set(key, next.join(','));
        return before - next.length;
      },
      async quit() { memoryStore.clear(); return 'OK'; },
    };
  }
  return fallback;
}"""

REDIS_NEW = """const MAX_TIMER_MS = 2 ** 31 - 1;

const readEntry = (k) => {
  const entry = memoryStore.get(k);
  if (entry === undefined) return undefined;
  const { value, expiresAt } = entry && entry.__expired !== undefined
    ? entry
    : { value: entry, expiresAt: 0 };
  if (expiresAt && Date.now() >= expiresAt) {
    memoryStore.delete(k);
    return undefined;
  }
  return value;
};

const writeEntry = (k, value, ttlSeconds) => {
  const expiresAt = ttlSeconds ? Date.now() + ttlSeconds * 1000 : 0;
  memoryStore.set(k, { __expired: true, value, expiresAt });
  if (expiresAt) {
    const delay = expiresAt - Date.now();
    if (delay <= MAX_TIMER_MS) {
      setTimeout(() => {
        if (readEntry(k) === undefined) memoryStore.delete(k);
      }, delay);
    }
  }
  return 'OK';
};

function getFallback() {
  if (!fallback) {
    fallback = {
      __memory: true,
      isMemory: true,
      async get(k) { const v = readEntry(k); return v === undefined ? null : v; },
      async set(k, v, mode, ttl) {
        return writeEntry(k, v, mode === 'EX' ? Number(ttl) : 0);
      },
      async del(...keys) {
        let n = 0;
        for (const k of keys) if (memoryStore.delete(k)) n += 1;
        return n;
      },
      async incrby(k, n) {
        const next = (Number(readEntry(k)) || 0) + n;
        writeEntry(k, String(next), 0);
        return next;
      },
      async expire(k, ttl) { writeEntry(k, readEntry(k) ?? '', Number(ttl)); return 1; },
      async ttl(k) {
        const entry = memoryStore.get(k);
        if (!entry || !entry.__expired) return -1;
        if (!entry.expiresAt) return -1;
        return Math.max(0, Math.ceil((entry.expiresAt - Date.now()) / 1000));
      },
      async exists(...keys) { return keys.some((k) => readEntry(k) !== undefined) ? 1 : 0; },
      async keys(p = '*') {
        const re = new RegExp('^' + p.replace(/\\*/g, '.*') + '$');
        return [...memoryStore.keys()].filter((k) => re.test(k) && readEntry(k) !== undefined);
      },
      async sadd(key, member) {
        const list = (readEntry(key) || '').split(',').filter(Boolean);
        if (!list.includes(member)) list.push(member);
        writeEntry(key, list.join(','), 0);
        return 1;
      },
      async smembers(key) {
        const raw = readEntry(key);
        return raw ? raw.split(',').filter(Boolean) : [];
      },
      async srem(key, ...members) {
        const list = (readEntry(key) || '').split(',').filter(Boolean);
        const before = list.length;
        const next = list.filter((m) => !members.includes(m));
        writeEntry(key, next.join(','), 0);
        return before - next.length;
      },
      async quit() { memoryStore.clear(); return 'OK'; },
    };
  }
  return fallback;
}"""

# --- license.js fix ---
LICENSE_OLD = """/** Parse a license code (accepts any dash/space grouping) into payload parts or null. */
export function parseCode(code) {
  const raw = String(code || '').trim();
  const m = raw.match(/^LMC-?([A-Za-z2-7]+)$/i);
  if (!m) return null;
  return decodePayload(m[1]);
}"""

LICENSE_NEW = """/** Parse a license code (accepts any dash/space grouping) into payload parts or null. */
export function parseCode(code) {
  const body = normalizeCode(code).replace(/^LMC-/, '');
  if (!body || !/^[A-Z2-7]+$/.test(body)) return null;
  return decodePayload(body);
}"""

redis_fixed = 0
license_fixed = 0
errors = []

for proj_dir in sorted(PROJECTS.iterdir()):
    if not proj_dir.is_dir():
        continue
    # redis
    rpath = proj_dir / "backend" / "services" / "cache" / "redis.client.js"
    if rpath.exists():
        src = rpath.read_text(encoding="utf-8")
        if "MAX_TIMER_MS" not in src:
            # Try exact match first
            if REDIS_OLD in src:
                src = src.replace(REDIS_OLD, REDIS_NEW)
                rpath.write_text(src, encoding="utf-8")
                redis_fixed += 1
            else:
                # Try regex-based replacement of the getFallback function
                pattern = r"function getFallback\(\) \{[\s\S]*?\n\}"
                if re.search(pattern, src):
                    # Insert MAX_TIMER_MS and readEntry/writeEntry before getFallback
                    insert_before = "function getFallback()"
                    helpers = REDIS_NEW.split("function getFallback()")[0]
                    rest = "function getFallback()" + REDIS_NEW.split("function getFallback()")[1]
                    src = src.replace(insert_before, helpers)
                    src = re.sub(pattern, rest, src, count=1)
                    rpath.write_text(src, encoding="utf-8")
                    redis_fixed += 1
                else:
                    errors.append(f"redis: {proj_dir.name} - no match")
    # license
    lpath = proj_dir / "backend" / "utils" / "license.js"
    if lpath.exists():
        src = lpath.read_text(encoding="utf-8")
        if "normalizeCode(code).replace" not in src:
            if LICENSE_OLD in src:
                src = src.replace(LICENSE_OLD, LICENSE_NEW)
                lpath.write_text(src, encoding="utf-8")
                license_fixed += 1
            else:
                errors.append(f"license: {proj_dir.name} - no match")

print(f"redis.client.js fixed: {redis_fixed}")
print(f"license.js fixed: {license_fixed}")
if errors:
    print(f"errors ({len(errors)}):")
    for e in errors[:20]:
        print(f"  {e}")
