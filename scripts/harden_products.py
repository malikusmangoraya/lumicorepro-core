#!/usr/bin/env python3
"""Apply the verified cross-product fixes to every project in `products/`.

This script is idempotent: running it twice changes nothing the second time.
Every fix below corresponds to a finding that `audit_products.py` reports as a
FAIL with concrete file evidence, so the two scripts stay in lockstep.

    python scripts/harden_products.py --dry-run     # show the plan, touch nothing
    python scripts/harden_products.py               # apply
    python scripts/harden_products.py --only apex   # one product

Exit code is 1 if any fix failed, so CI can gate on it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

# The one redis client in the set that actually parses. `apex` carries the
# corrected module: the nine siblings had the `function getFallback()` keyword
# stripped, leaving a bare block with a top-level `return` — a fatal ESM
# SyntaxError, so those backends could never boot. Apex's copy also fixes a
# real bug the others still had: Node clamps setTimeout delays over ~24.8 days,
# which silently revived revoked 30-day refresh tokens in the in-memory fallback.
CANONICAL_REDIS = ROOT / "products/apex/backend/services/cache/redis.client.js"

SEQUELIZE_FROM = "^1.0.0"
SEQUELIZE_TO = "^6.37.5"

# Replaces the unguarded demo-credential seed. Identical in shape to the guarded
# version apex already ships, with two changes: no default password literal, and
# the seed additionally requires an explicit opt-in flag.
GUARDED_SEED = """// ── Demo / development accounts ──────────────────────────────────────────────
// SECURITY: these accounts use a fixed, publicly documented password, so they
// are never created in production. Seeding also requires an explicit opt-in
// (ENABLE_DEMO_SEED=true) so that simply running the app on a staging host can
// never expose an account whose password is in this repository.
const IS_PRODUCTION = process.env.NODE_ENV === 'production';
const DEMO_SEED_ENABLED = process.env.ENABLE_DEMO_SEED === 'true';
const DEMO_USER_PASSWORD = process.env.DEMO_USER_PASSWORD;

if (IS_PRODUCTION) {
  logger.warn('Production mode: skipping demo/admin seed — no fixed-credential accounts created.');
} else if (!DEMO_SEED_ENABLED) {
  logger.warn('Demo seed disabled. Set ENABLE_DEMO_SEED=true and DEMO_USER_PASSWORD to create local demo accounts.');
} else if (!DEMO_USER_PASSWORD) {
  logger.error('ENABLE_DEMO_SEED=true requires DEMO_USER_PASSWORD to be set; refusing to seed a known-password account.');
} else {
  (async () => {
    const hash = await bcrypt.hash(DEMO_USER_PASSWORD, 12);
    const demoUsers = [
      {
        id: 1,
        name: process.env.DEMO_USER_NAME || 'Demo User',
        email: (process.env.DEMO_USER_EMAIL || 'demo@lumicorepro.com').toLowerCase(),
        password: hash,
        role: 'user',
        avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
        isActive: true,
        twoFactorEnabled: false,
        preferences: { theme: 'dark', language: 'en' },
      },
      {
        id: 2,
        name: process.env.DEMO_ADMIN_NAME || 'Admin User',
        email: (process.env.DEMO_ADMIN_EMAIL || 'admin@lumicorepro.com').toLowerCase(),
        password: hash,
        role: 'admin',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
        isActive: true,
        twoFactorEnabled: false,
        preferences: { theme: 'dark', language: 'en' },
      },
    ];
    for (const u of demoUsers) {
      inMemoryUsers.set(u.email.toLowerCase(), {
        ...u,
        comparePassword: async function (cand) {
          return bcrypt.compare(cand, this.password);
        },
        save: async function () {
          return this;
        },
      });
    }
    logger.warn(
      `Seeded ${demoUsers.length} dev-only demo accounts (${demoUsers.map((u) => u.email).join(', ')}). ` +
        'These use a known password and must never exist in production.',
    );
  })().catch((err) => logger.error(`Demo user seed failed: ${err.message}`));
}
"""

# The onboarding playbook advertised a working admin password over HTTP.
PLAYBOOK_OLD = "'Log in as admin (admin@example.com / Password123!).',"
PLAYBOOK_NEW = "'Log in with the administrator account you created in step 1 (see SETUP_GUIDE.md).',"


@dataclass
class Fix:
    name: str
    ok: bool = True
    detail: str = ""
    skipped: bool = False


@dataclass
class ProductFixes:
    name: str
    fixes: list[Fix] = field(default_factory=list)

    def add(self, name, ok, detail="", skipped=False):
        self.fixes.append(Fix(name, ok, detail, skipped))

    @property
    def failed(self):
        return [f for f in self.fixes if not f.ok]


# --------------------------------------------------------------------------- #
# Individual fixes
# --------------------------------------------------------------------------- #
def _fails_to_parse(js_file: Path) -> bool:
    """True when Node's ESM parser rejects this file. This is the ground truth."""
    helper = ROOT / "scripts/js_parse_check.mjs"
    try:
        proc = subprocess.run(
            ["node", "--experimental-vm-modules", str(helper), str(js_file)],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return True  # cannot verify; assume broken rather than silently skip
    return proc.returncode != 0


def fix_redis_client(p: Path, dry: bool) -> Fix:
    """Restore the corrupted in-memory/Redis client."""
    target = p / "backend/services/cache/redis.client.js"
    if not target.is_file():
        return Fix("redis-client", True, "no such file — skipped", skipped=True)

    text = target.read_text(encoding="utf-8", errors="replace")
    if "function getFallback()" in text:
        return Fix("redis-client", True, "already correct", skipped=True)

    # Ground-truth check: does this file actually fail to parse?
    if not _fails_to_parse(target):
        return Fix("redis-client", False,
                   "file lacks getFallback() but still parses — unknown shape, left untouched")

    if not CANONICAL_REDIS.is_file():
        return Fix("redis-client", False, "canonical source is missing")
    canonical = CANONICAL_REDIS.read_text(encoding="utf-8", errors="replace")
    if dry:
        return Fix("redis-client", True, "would restore the canonical client")
    target.write_text(canonical, encoding="utf-8")
    return Fix("redis-client", True, "restored canonical client (fixes boot failure + 30-day refresh-token revival)")


def fix_sequelize(p: Path, dry: bool) -> Fix:
    """sequelize ^1.0.0 does not exist on npm; the real line is 6.x."""
    pj = p / "backend/package.json"
    if not pj.is_file():
        return Fix("sequelize", True, "no backend/package.json — skipped", skipped=True)
    raw = pj.read_text(encoding="utf-8")
    data = json.loads(raw)
    cur = data.get("dependencies", {}).get("sequelize")
    if cur is None:
        return Fix("sequelize", True, "sequelize not declared — skipped", skipped=True)
    if not cur.startswith("^1."):
        return Fix("sequelize", True, f"already {cur}", skipped=True)
    if dry:
        return Fix("sequelize", True, f"would pin {cur} -> {SEQUELIZE_TO}")
    data["dependencies"]["sequelize"] = SEQUELIZE_TO
    pj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return Fix("sequelize", True, f"{cur} -> {SEQUELIZE_TO}")


def fix_demo_seed(p: Path, dry: bool) -> Fix:
    """Guard the fixed-credential demo seed so it can never run in production."""
    f = p / "backend/routes/auth.routes.js"
    if not f.is_file():
        return Fix("demo-seed", True, "no auth.routes.js — skipped", skipped=True)
    text = f.read_text(encoding="utf-8", errors="replace")

    if "ENABLE_DEMO_SEED" in text:
        return Fix("demo-seed", True, "already guarded", skipped=True)

    lines = text.splitlines(keepends=True)
    start = end = None
    for i, ln in enumerate(lines):
        if "Seed default users for immediate out-of-the-box local testing" in ln:
            start = i
            break
    if start is None:
        return Fix("demo-seed", True, "no demo seed block found — skipped", skipped=True)
    for j in range(start, len(lines)):
        # Matches both `})();` and `})().catch(err => ...);`
        if lines[j].lstrip().startswith("})()"):
            end = j + 1
            break
    if end is None:
        return Fix("demo-seed", False, "could not find the end of the seed IIFE")

    if dry:
        return Fix("demo-seed", True,
                    f"would replace lines {start + 1}-{end} with the guarded version")

    original = text
    # Some copies close the guard's `else` block on the line AFTER the IIFE.
    # Try progressively longer spans and keep the first rewrite that parses,
    # so a differing block shape can never leave the file broken.
    for extra in (0, 1, 2):
        stop = end
        while stop < len(lines) and extra > 0:
            if lines[stop].strip() != "}":
                break
            stop += 1
            extra -= 1
        f.write_text("".join(lines[:start]) + GUARDED_SEED + "".join(lines[stop:]),
                     encoding="utf-8")
        if not _fails_to_parse(f):
            return Fix("demo-seed", True,
                       f"replaced lines {start + 1}-{stop} with a production-guarded, opt-in seed")

    f.write_text(original, encoding="utf-8")  # roll back rather than ship a broken file
    return Fix("demo-seed", False, "rewrite did not parse — original restored, left for manual review")


def fix_playbook_copy(p: Path, dry: bool) -> Fix:
    """Stop advertising a working admin password in an API response."""
    f = p / "backend/routes/playbook.routes.js"
    if not f.is_file():
        return Fix("playbook-copy", True, "no playbook.routes.js — skipped", skipped=True)
    text = f.read_text(encoding="utf-8", errors="replace")
    if PLAYBOOK_OLD not in text:
        return Fix("playbook-copy", True, "no credential in onboarding copy — skipped", skipped=True)
    if dry:
        return Fix("playbook-copy", True, "would remove the advertised password")
    f.write_text(text.replace(PLAYBOOK_OLD, PLAYBOOK_NEW), encoding="utf-8")
    return Fix("playbook-copy", True, "onboarding no longer advertises an admin password")


def fix_env_example(p: Path, dry: bool) -> Fix:
    """Document the new demo-seed opt-in variables."""
    f = p / "backend/.env.example"
    if not f.is_file():
        return Fix("env-example", False, "no backend/.env.example")
    text = f.read_text(encoding="utf-8", errors="replace")
    if "ENABLE_DEMO_SEED" in text:
        return Fix("env-example", True, "already documents the seed flags", skipped=True)
    block = """
# ── Demo accounts (local development only) ────────────────────────────────────
# Both flags are required before the fixed-credential demo users are created.
# The seed is ALWAYS skipped when NODE_ENV=production, regardless of these.
ENABLE_DEMO_SEED=false
DEMO_USER_PASSWORD=
DEMO_USER_EMAIL=demo@example.com
DEMO_ADMIN_EMAIL=admin@example.com
DEMO_USER_NAME=Demo User
DEMO_ADMIN_NAME=Admin User
"""
    if dry:
        return Fix("env-example", True, "would document the seed flags")
    f.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8")
    return Fix("env-example", True, "documented ENABLE_DEMO_SEED / DEMO_USER_PASSWORD")


def regenerate_backend_lockfile(p: Path, dry: bool) -> Fix:
    """CI runs `npm ci`, which needs a lockfile that matches package.json."""
    be = p / "backend"
    pj = be / "package.json"
    if not pj.is_file():
        return Fix("backend-lockfile", False, "no backend/package.json")
    if (be / "package-lock.json").is_file():
        return Fix("backend-lockfile", True, "lockfile already present", skipped=True)
    if dry:
        return Fix("backend-lockfile", True, "would run npm install --package-lock-only")
    # On Windows the npm entry point is npm.cmd, and subprocess will not resolve
    # the .cmd shim unless it is named explicitly.
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        return Fix("backend-lockfile", False, "npm executable not found on PATH")
    try:
        proc = subprocess.run(
            [npm, "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=str(be), capture_output=True, text=True, timeout=420, shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return Fix("backend-lockfile", False, f"npm failed: {exc}")
    if proc.returncode != 0 or not (be / "package-lock.json").is_file():
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
        return Fix("backend-lockfile", False, "npm install --package-lock-only failed: " + " | ".join(tail))
    return Fix("backend-lockfile", True, "generated backend/package-lock.json")


ALL_FIXES = [
    fix_redis_client,
    fix_sequelize,
    fix_demo_seed,
    fix_playbook_copy,
    fix_env_example,
    regenerate_backend_lockfile,
]


def harden(product: Path, dry: bool, with_lockfiles: bool) -> ProductFixes:
    pf = ProductFixes(name=product.name)
    for fn in ALL_FIXES:
        if fn is regenerate_backend_lockfile and not with_lockfiles:
            pf.add("backend-lockfile", True, "skipped (--no-lockfiles)", skipped=True)
            continue
        try:
            pf.fixes.append(fn(product, dry))
        except Exception as exc:  # a crashing fix is a failure, not a silent pass
            pf.add(getattr(fn, "__name__", str(fn)), False, f"raised {type(exc).__name__}: {exc}")
    return pf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="filter to one product")
    ap.add_argument("--no-lockfiles", action="store_true",
                    help="skip npm install --package-lock-only for backends")
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

    mode = "DRY RUN" if a.dry_run else "APPLY"
    print(f"=== harden_products: {mode} ({len(dirs)} product(s)) ===")

    all_pf = []
    for d in dirs:
        pf = harden(d, a.dry_run, not a.no_lockfiles)
        all_pf.append(pf)
        print(f"\n-- {pf.name}")
        for f in pf.fixes:
            mark = "skip" if f.skipped else ("ok  " if f.ok else "FAIL")
            print(f"   [{mark}] {f.name:<20} {f.detail}")

    total = sum(len(p.fixes) for p in all_pf)
    bad = sum(len(p.failed) for p in all_pf)
    print(f"\n=== {total} fix step(s), {bad} failure(s) ===")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())