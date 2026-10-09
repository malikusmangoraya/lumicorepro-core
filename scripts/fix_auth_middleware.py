#!/usr/bin/env python3
"""Write the missing authentication middleware into every product.

`backend/middleware/auth.js` shipped as a 29-line CommonJS file exporting only
`protect` and `adminOnly`. Every route module imports it as an ES module and
also expects `authorize`, `generateToken` and `registerInMemoryStore`:

    import { protect, generateToken, registerInMemoryStore } from '../middleware/auth.js';
    import { protect, authorize } from '../middleware/auth.js';

Those three names are defined nowhere in the codebase. Because Node resolves a
named import at load time, every route that imports them throws immediately —
so the entire login and signup system, and every route using role checks, was
dead on arrival. This is the single defect that made the products unsellable.

This writes a complete ES module that provides all five exports:

  protect                    verify the bearer token and hydrate req.user
  authorize(...roles)        require one of the listed roles (403 otherwise)
  adminOnly                  shorthand for authorize('admin')
  generateToken(user)        sign a short-lived access token
  registerInMemoryStore(map) register the offline fallback user store

    python scripts/fix_auth_middleware.py --dry-run
    python scripts/fix_auth_middleware.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

MODULE = '''import jwt from 'jsonwebtoken';
// `utils/jwtSecret.js` is CommonJS. A default import always resolves for an
// interop module, unlike named imports which depend on static analysis.
import jwtSecretModule from '../utils/jwtSecret.js';

/**
 * Authentication and authorisation middleware.
 *
 * Exports:
 *   protect                     verify the bearer token, hydrate `req.user`
 *   optionalProtect             attach `req.user` when a token is present, never reject
 *   authorize(...roles)         require one of the listed roles
 *   adminOnly                   shorthand for authorize('admin')
 *   generateToken(user)         sign a short-lived access token
 *   registerInMemoryStore(map)  register the offline fallback user store
 */

const { jwtSecret } = jwtSecretModule;

const TOKEN_TTL = process.env.JWT_EXPIRES_IN || '15m';
const ALGORITHM = 'HS256';

/**
 * When no database is reachable the auth routes fall back to an in-memory Map
 * keyed by lower-cased email address. The routes register it here so `protect`
 * can hydrate a full user record from a token that only carries an id.
 */
let memoryStore = null;

/**
 * Register the fallback user store.
 * @param {Map<string, object>} store keyed by lower-cased email address
 */
export function registerInMemoryStore(store) {
  if (!(store instanceof Map)) {
    throw new TypeError('registerInMemoryStore expects a Map of users');
  }
  memoryStore = store;
  return store;
}

/** True when a fallback store has been registered and holds this user. */
function lookupMemoryUser(id) {
  if (!memoryStore || id === undefined || id === null) return null;
  for (const user of memoryStore.values()) {
    if (String(user.id) === String(id)) return user;
  }
  return null;
}

/**
 * Sign an access token.
 *
 * Accepts either a user id or a user object; when given an object the role is
 * carried in the payload so `authorize` can make a decision without a database
 * round trip on every request.
 *
 * @param {number|string|{id:*, role?:string}} user
 * @param {object} [extra] additional claims
 */
export function generateToken(user, extra = {}) {
  const isObject = user !== null && typeof user === 'object';
  const id = isObject ? user.id : user;
  const role = isObject ? user.role : undefined;
  const payload = { id, ...(role ? { role } : {}), ...extra };
  return jwt.sign(payload, jwtSecret, { expiresIn: TOKEN_TTL, algorithm: ALGORITHM });
}

function readBearerToken(req) {
  const header = req.headers?.authorization || '';
  if (!header.startsWith('Bearer ')) return null;
  const token = header.slice(7).trim();
  return token || null;
}

/**
 * Verify the access token on the request.
 *
 * On success `req.user` holds the token payload, enriched with the full record
 * when the in-memory fallback store knows the id.
 */
export async function protect(req, res, next) {
  const token = readBearerToken(req);
  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Not authorized, no token provided',
    });
  }

  let decoded;
  try {
    decoded = jwt.verify(token, jwtSecret, { algorithms: [ALGORITHM] });
  } catch (err) {
    const message = err.name === 'TokenExpiredError'
      ? 'Not authorized, token expired'
      : 'Not authorized, token failed';
    return res.status(401).json({ success: false, message });
  }

  const full = lookupMemoryUser(decoded.id);
  req.user = full ? { ...decoded, ...full, password: undefined } : decoded;
  return next();
}

/**
 * Restrict a route to the given roles.
 *
 * Must be used after `protect`, which is what populates `req.user`.
 *
 * @param {...string} roles
 */
export function authorize(...roles) {
  const allowed = roles.flat().filter(Boolean);
  return function authorizeMiddleware(req, res, next) {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Not authorized, no token provided',
      });
    }
    if (allowed.length === 0) return next();
    if (!allowed.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        message: 'Forbidden: insufficient permissions',
      });
    }
    return next();
  };
}

/** Shorthand for `authorize('admin')`. */
export const adminOnly = authorize('admin');

/**
 * Attach the caller when a valid token is present, but never reject.
 *
 * Used by endpoints that render a different experience for signed-in users
 * (a dashboard link in the nav, for example) and must stay reachable by
 * anonymous visitors. An invalid or absent token simply leaves `req.user`
 * undefined and the request continues.
 */
export async function optionalProtect(req, res, next) {
  const token = readBearerToken(req);
  if (!token) return next();
  try {
    const decoded = jwt.verify(token, jwtSecret, { algorithms: [ALGORITHM] });
    const full = lookupMemoryUser(decoded.id);
    req.user = full ? { ...decoded, ...full, password: undefined } : decoded;
  } catch {
    // An unusable token is treated as no token at all.
  }
  return next();
}

export default {
  protect,
  optionalProtect,
  authorize,
  adminOnly,
  generateToken,
  registerInMemoryStore,
};
'''

REQUIRED_EXPORTS = ("protect", "optionalProtect", "authorize", "adminOnly",
                    "generateToken", "registerInMemoryStore")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    if not PRODUCTS.is_dir():
        print(f"No {PRODUCTS} directory", file=sys.stderr)
        return 2
    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]
    if not dirs:
        print("No matching products", file=sys.stderr)
        return 2

    print(f"=== fix_auth_middleware: {'DRY RUN' if a.dry_run else 'APPLY'} ({len(dirs)}) ===")
    failures = 0
    for d in dirs:
        target = d / "backend" / "middleware" / "auth.js"
        if not target.parent.is_dir():
            print(f"-- {d.name:20} no backend/middleware — skipped")
            continue

        current = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
        missing = [e for e in REQUIRED_EXPORTS
                   if not re.search(rf"export\s+(?:async\s+)?(?:function|const)\s+{e}\b", current)]
        if not missing:
            print(f"-- {d.name:20} already complete — skipped")
            continue

        if a.dry_run:
            print(f"-- {d.name:20} would add: {', '.join(missing)}")
            continue

        target.write_text(MODULE, encoding="utf-8")

        proc = subprocess.run(
            ["node", "--experimental-vm-modules",
             str(ROOT / "scripts" / "js_parse_check.mjs"), str(target)],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            print(f"-- {d.name:20} [FAIL] new module does not parse")
            print(proc.stdout[:400])
            failures += 1
            continue

        print(f"-- {d.name:20} [ok] wrote complete auth middleware "
              f"(was missing {', '.join(missing)})")

    print(f"\n=== {failures} failure(s) ===")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())