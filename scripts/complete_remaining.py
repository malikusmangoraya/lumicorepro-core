"""Finish the remaining catalogue hardening across all 11 products.

Applies: Sentry wiring in server.js, backend/scripts/backup.js + npm script,
honest demo-access banner text, and Tier-3 docs (SUPPORT, ROADMAP, DEMO,
BACKUP, ACCESSIBILITY). Idempotent: skips anything already applied.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core\products")
SUPPORT_EMAIL = "malikusmangoraya786@gmail.com"

SENTRY_INIT = """  try {
    const monitoring = await import('./utils/monitoring.js');
    if (monitoring && monitoring.initSentry) await monitoring.initSentry(app);
  } catch (err) {
    console.warn(`[server] monitoring disabled: ${err.message}`);
  }

"""

SENTRY_ERROR = """  try {
    const monitoring = await import('./utils/monitoring.js');
    if (monitoring && monitoring.attachSentryErrorHandler) await monitoring.attachSentryErrorHandler(app);
  } catch (err) {
    console.warn(`[server] monitoring error handler disabled: ${err.message}`);
  }
"""

BACKUP_JS = """'use strict';
/**
 * Write a compressed PostgreSQL dump to backend/backups/.
 *
 * Usage:
 *   node scripts/backup.js
 *   docker compose exec backend node scripts/backup.js
 *
 * Requires DATABASE_URL with a postgresql:// connection string and a
 * pg_dump binary in PATH. Never prints the connection string.
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function main() {
  const url = process.env.DATABASE_URL || '';
  if (!url.startsWith('postgresql://') && !url.startsWith('postgres://')) {
    console.error('[backup] DATABASE_URL must be a postgresql:// connection string.');
    process.exit(2);
  }
  const dir = path.join(__dirname, '..', 'backups');
  fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const out = path.join(dir, `backup-${stamp}.dump`);
  const r = spawnSync('pg_dump', ['--format=custom', '--file', out, url], { stdio: 'inherit' });
  if (r.status !== 0) {
    console.error('[backup] pg_dump failed. Is PostgreSQL client installed and DATABASE_URL reachable?');
    process.exit(r.status || 1);
  }
  console.log(`[backup] wrote ${out}`);
  console.log('[backup] restore with: pg_restore --clean --if-exists -d "$DATABASE_URL" <file>');
}

if (require.main === module) main();
module.exports = { main };
"""

OLD_BANNER = "Email: demo@example.com \u00b7 Password: demo1234"
NEW_BANNER = ("Demo accounts are seeded only when ENABLE_DEMO_SEED=true and "
              "DEMO_USER_PASSWORD is set (see backend/.env.example). "
              "Seeding is always disabled in production.")

SUPPORT_MD = """# Support and update policy

Support contact: {email}

- Standard licence: 1 year of updates, community support by email.
- Agency licence: unlimited client deployments, priority email support.
- Security fixes are released for the supported line for 12 months after
  each archive date. After that, upgrade to the current archive.
- Before reporting, run `npm run build` (frontend) and `npm test` (backend)
  and include the failing output plus `node --version`.
""".format(email=SUPPORT_EMAIL)

ROADMAP_MD = """# Roadmap

Committed, in order:

1. Keep dependencies current via Dependabot (weekly npm + actions).
2. Extend automated coverage beyond auth/operational endpoints to payments
   and each product's niche flow.
3. Accessibility: per-release axe-core + Lighthouse pass on Home, Login,
   Register, Checkout and the niche page.
4. Migrations stay additive; never edit an applied migration, add a new one.

Non-goals: hidden pricing, fake reviews, dark patterns, placeholder copy.
"""

DEMO_MD = """# Demo accounts and sample data

The hosted GitHub Pages preview is frontend-only and has no API, so the
Login page shows where demo access would appear, not working credentials.

For a local full-stack demo:

1. `cp backend/.env.example backend/.env`
2. Set `ENABLE_DEMO_SEED=true` and a strong `DEMO_USER_PASSWORD`.
3. `npm ci && npm run migrate && npm run dev` (backend), `npm ci && npm run dev` (frontend).
4. Sign in with `DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD`.

`NODE_ENV=production` always skips the seed, even if the flags are set.

Sample catalogue data lives in `backend/scripts/seed*.js`.
"""

BACKUP_MD = """# Backup and restore

`backend/scripts/backup.js` writes a compressed PostgreSQL dump to
`backend/backups/`. Run it on a schedule and copy the result off the host.

```bash
npm run backup
# or inside the backend container:
docker compose exec backend node scripts/backup.js
```

Restore:

```bash
pg_restore --clean --if-exists -d "$DATABASE_URL" backend/backups/<file>.dump
```

Keep at least daily backups and test a restore before you need one.
"""

A11Y_MD = """# Accessibility baseline

Implemented in the shipped UI:

- Skip-to-content link as the first focusable element.
- Semantic landmarks (`header`, `main`, `nav`, `footer`).
- Real labels on form fields, visible focus styles, dark mode.
- `prefers-reduced-motion` respected for motion content.

Not claimed: a formal WCAG 2.1 AA certification. Before each public
release, run an axe-core pass plus Lighthouse on Home, Login, Register,
Checkout (where present) and the product niche page, and record the
results in the release notes.
"""


def patch_server(path: Path) -> str:
    t = path.read_text(encoding="utf-8")
    if "initSentry" not in t:
        anchor = "  const mounted = await mountRoutes();\n"
        if anchor not in t:
            return "no-mount-anchor"
        t = t.replace(anchor, SENTRY_INIT + anchor, 1)
    if "attachSentryErrorHandler" not in t:
        anchor2 = "  app.use(notFound);\n  app.use(errorHandler);"
        if anchor2 not in t:
            return "no-error-anchor"
        t = t.replace(anchor2, SENTRY_ERROR + anchor2, 1)
    path.write_text(t, encoding="utf-8")
    return "ok"


def ensure_docs(prod: Path) -> list[str]:
    made = []
    docs = {
        "SUPPORT.md": SUPPORT_MD,
        "ROADMAP.md": ROADMAP_MD,
        "DEMO.md": DEMO_MD,
        "BACKUP.md": BACKUP_MD,
        "ACCESSIBILITY.md": A11Y_MD,
    }
    for name, content in docs.items():
        p = prod / name
        if not p.is_file():
            p.write_text(content, encoding="utf-8")
            made.append(name)
    return made


def main() -> int:
    for prod in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        be = prod / "backend"
        if not be.is_dir():
            continue
        srv = be / "server.js"
        res = patch_server(srv) if srv.is_file() else "no-server"
        bkp = be / "scripts" / "backup.js"
        if not bkp.is_file():
            bkp.parent.mkdir(parents=True, exist_ok=True)
            bkp.write_text(BACKUP_JS, encoding="utf-8")
            res += "+backup"
        pkgp = be / "package.json"
        pkg = json.loads(pkgp.read_text(encoding="utf-8"))
        if pkg.get("scripts", {}).get("backup") != "node scripts/backup.js":
            pkg.setdefault("scripts", {})["backup"] = "node scripts/backup.js"
            pkgp.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            res += "+backup-script"
        login = prod / "frontend" / "src" / "pages" / "Login.jsx"
        banner = "same"
        if login.is_file():
            t = login.read_text(encoding="utf-8")
            if OLD_BANNER in t:
                login.write_text(t.replace(OLD_BANNER, NEW_BANNER, 1), encoding="utf-8")
                banner = "fixed"
        docs = ensure_docs(prod)
        print(f"{prod.name:<18} server={res} banner={banner} docs+={len(docs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
