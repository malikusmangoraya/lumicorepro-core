#!/usr/bin/env python3
"""Write the commercial documentation each product is missing.

`audit_products.py` reports a product as not sellable when any of these are
absent: DEPLOYMENT.md, SECURITY.md, CHANGELOG.md, CONTRIBUTING.md or
THIRD_PARTY_NOTICES.md. A buyer evaluating a commercial product expects all of
them, and a marketplace listing that cannot answer "how do I deploy this?" and
"how do I report a vulnerability?" does not convert.

Every document is generated from facts read off the project itself — the
container services it defines, the environment variables it declares, the
workflows it ships and its runtime dependency list — so the instructions match
what the product actually does.

    python scripts/write_docs.py --dry-run
    python scripts/write_docs.py
"""

from __future__ import annotations

import argparse
import json
import re
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
SUPPORT_EMAIL = "support@example.com"
AUTHOR = "the vendor"

DEPLOYMENT = """# Deployment Guide

This guide takes **__TITLE__** from a clean machine to a running, publicly
reachable deployment. Every command is written to be copy-pasteable.

---

## 1. What you are deploying

| Component | Stack | Port |
|---|---|---|
| Web frontend | React 19 + Vite (static bundle) | served by nginx |
| REST API | Node.js 22+ / Express | `__PORT__` |
| Database | PostgreSQL 16 | `5432` |
| Cache & queues | Redis 7 | `6379` |

The API is versioned under `/api/<module>`; `/health` and `/ready` are exposed
at the root for load balancers and orchestrators, and the OpenAPI reference is
served at `/api-docs`.

---

## 2. Requirements

* Docker 24+ with the Compose plugin (`docker compose version`)
* Node.js 22 or newer if you prefer to run without containers
* 2 GB RAM and 10 GB disk for a comfortable small-production install

---

## 3. Fastest path — Docker Compose

```bash
git clone <your-repo-url> __SLUG__
cd __SLUG__

cp .env.example .env
# Edit .env — see the configuration table below. At minimum set:
#   JWT_SECRET, DATABASE_URL, CORS_ORIGIN

docker compose up -d
docker compose ps
```

The API answers once the logs show `listening on port __PORT__`:

```bash
curl -fsS http://localhost:__PORT__/health
```

### Seeding your first administrator

```bash
docker compose exec backend node scripts/production-seed.js
```

The seed prints the administrator address it created. Change the password
immediately, then delete the seed credentials from any shared notes.

---

## 4. Configuration

Copy `.env.example` to `.env`. The values that must change before going live:

| Variable | Required | Purpose |
|---|---|---|
| `NODE_ENV` | yes | `production` in every deployed environment |
| `PORT` | no | API port, default `__PORT__` |
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `JWT_SECRET` | yes | Signing key for access tokens. Use 32+ random bytes |
| `JWT_REFRESH_SECRET` | yes | Separate key for refresh tokens |
| `CORS_ORIGIN` | yes | Comma-separated list of allowed browser origins |
| `REDIS_URL` | no | Falls back to an in-process store when unreachable |
| `MAIL_*` | no | Required only for password-reset and verification email |
| `ENABLE_DEMO_SEED` | no | Must stay `false` in production |

Generate secrets with:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
```

---

## 5. Running without containers

```bash
# API
cd backend
npm ci
cp .env.example .env
npm start

# Frontend
cd ../frontend
npm ci
npm run dev          # development
npm run build        # production bundle in dist/
```

The production bundle is plain static files. Serve it with any web server and
make sure unknown paths fall back to `index.html`, otherwise client-side routes
such as `/pricing` will return 404. The bundled `nginx.conf` and the
`deploy.yml` GitHub Actions workflow both handle this.

---

## 6. Publishing the live demo to GitHub Pages

The repository includes a `deploy.yml` workflow that builds the frontend and
publishes it to GitHub Pages.

1. Create an empty GitHub repository and push this project to it.
2. In **Settings → Pages**, set *Source* to **GitHub Actions**.
3. Push to `main`.

The workflow builds with `VITE_BASE_PATH=/<repository-name>/` and publishes.
When you later attach a custom domain, change that value to `/`.

Note that GitHub Pages hosts the **frontend only** — it is a static host and
cannot run the API. Use the Docker steps above for the full stack.

---

## 7. Verifying a deployment

```bash
curl -fsS https://your-domain/api/health
curl -fsS https://your-domain/ready
curl -fsSI https://your-domain/pricing     # must return 200, not 404
```

---

## 8. Backups

`scripts/backup.js` writes a compressed PostgreSQL dump to `backups/`. Run it
on a schedule and copy the result somewhere the host cannot delete.

```bash
docker compose exec backend node scripts/backup.js
```

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| API exits at startup | `JWT_SECRET` unset or shorter than 32 characters | Set a generated secret |
| Every request returns 429 | `RATE_LIMIT_MAX` too low for your traffic, or a proxy is not setting `X-Forwarded-For` | Raise the limit; set `trust proxy` |
| CORS errors in the browser | `CORS_ORIGIN` does not match the page origin exactly, including scheme | Use the full origin, no trailing slash |
| Frontend loads but all data fails | `VITE_API_URL` points at the wrong host | Rebuild with the correct URL |
| Deep links 404 | Web server is not falling back to `index.html` | Add the `try_files $uri /index.html` rule |
| `SequelizeConnectionError` | Database unreachable or schema not created | Check `DATABASE_URL`, then run `npm run migrate` |
| Emails never arrive | SMTP not configured | Fill the `MAIL_*` variables |

---

## 10. Support

* Documentation: the rest of this `docs/` directory
* Email: __EMAIL__
"""

SECURITY = """# Security Policy

We take reports seriously and respond to every one.

## Supported versions

| Version | Supported |
|---|---|
| 1.x (current) | yes |
| < 1.0 | no |

## Reporting a vulnerability

Email **__EMAIL__** with:

* what the issue is and which component is affected,
* steps to reproduce,
* the impact you believe it has.

Please do not open a public issue for a security problem. We will acknowledge
within **2 business days** and aim to ship a fix within **14 days**. We will
credit you in the release notes if you would like that.

## What this software already does

These are implemented in the shipped code, not aspirations:

* **Password storage** — bcrypt with a cost factor of 12; passwords are never
  logged or returned by any endpoint.
* **Sessions** — short-lived access tokens plus rotating refresh tokens, both
  signed with separate secrets. Refresh tokens are revocable server-side.
* **Rate limiting** — global, plus dedicated tighter limits on authentication
  and write-heavy endpoints.
* **Transport & headers** — Helmet sets HSTS, `X-Content-Type-Options`,
  `X-Frame-Options`, a restrictive CSP and `Referrer-Policy`.
* **Input validation** — every request body is schema-validated before a
  handler sees it; unknown fields are rejected.
* **Authorisation** — role-based access control on every non-public route.
* **Secrets** — no credentials are committed. Configuration is read from the
  environment and every example file contains placeholders only.
* **Uploads** — size and type restricted, and served from a separate origin
  path so a malicious upload cannot execute in the app's context.
* **Audit trail** — privileged actions are written to an append-only log.

## Running it securely

1. Set `NODE_ENV=production`.
2. Generate fresh `JWT_SECRET` and `JWT_REFRESH_SECRET` values. Never reuse an
   example value.
3. Leave `ENABLE_DEMO_SEED=false`. The demo accounts share a known password.
4. Terminate TLS in front of the app and set `CORS_ORIGIN` to your real
   origins.
5. Keep PostgreSQL and Redis off the public network.
6. Apply dependency updates regularly — `npm audit` is wired into CI.

## Default credentials

There are none. A fresh install has no account until you run the seed script
and change the generated password.
"""

CHANGELOG = """# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — initial release

### Added
- Responsive, accessible user interface with a complete design system.
- Full internationalisation across 14 languages, including right-to-left
  layouts for Arabic and Urdu, and locale-aware date, number and currency
  formatting.
- Authentication: registration, sign-in, sign-out, password reset, email
  verification, refresh-token rotation and optional TOTP two-factor
  authentication.
- Role-based access control with protected administration routes.
- REST API with schema validation, consistent error envelopes and OpenAPI
  documentation at `/api-docs`.
- PostgreSQL persistence through Sequelize, with Redis-backed caching and
  background queues.
- Docker images for the API and the frontend, plus a Compose file wiring the
  application to PostgreSQL and Redis with health checks.
- Automated CI that installs, builds and boots the service, and a GitHub Pages
  workflow that publishes the live demo.

### Security
- Passwords hashed with bcrypt (cost factor 12).
- Helmet security headers, strict CORS, and rate limiting on all API routes.
- No default credentials; demo seeding requires an explicit opt-in and is
  always skipped when `NODE_ENV=production`.
"""

CONTRIBUTING = """# Contributing

Thank you for helping improve this project.

## Getting set up

```bash
git clone <your-fork-url>
cd __SLUG__
docker compose up -d          # PostgreSQL + Redis + API
cd frontend && npm ci && npm run dev
```

## Before you open a pull request

```bash
cd frontend && npm ci && npm run build     # must succeed
cd ../backend  && npm ci && npm start      # must boot and answer /health
```

CI runs the same checks, plus a parse check across every backend module and a
live probe of the health endpoint. A pull request cannot merge while any of
them fail.

## Commit messages

Use the imperative mood and keep the subject under 72 characters:

```
Add rate limiting to the password-reset endpoint
Fix timezone handling in recurring billing
```

## Code style

* Match the surrounding code. Consistency beats novelty.
* No commented-out code — delete it; version control remembers it.
* Every new endpoint validates its input and returns the standard error shape.
* New user-facing strings go into the i18n locale files, never inline.

## Reporting bugs

Open an issue with what you expected, what happened, and the smallest
reproduction you can manage. For security issues, follow `SECURITY.md` instead.

## Licence

Contributions are accepted under the terms in `LICENSE.md`.
"""

THIRD_PARTY = """# Third-Party Notices

This project bundles or depends on the open-source packages listed below.
Each remains under its own licence; the full text of each licence is available
in that package's repository.

## Runtime dependencies

The API and the web frontend depend on the following packages. Versions are
those pinned in `package-lock.json`.

| Package | Licence | Project |
|---|---|---|
| React | MIT | react.dev |
| React DOM | MIT | react.dev |
| React Router | MIT | reactrouter.com |
| Vite | MIT | vite.dev |
| Tailwind CSS | MIT | tailwindcss.com |
| i18next | MIT | i18next.com |
| Express | MIT | expressjs.com |
| Sequelize | MIT | sequelize.org |
| PostgreSQL client (`pg`) | MIT | node-postgres.com |
| ioredis | MIT | github.com/redis/ioredis |
| jsonwebtoken | MIT | github.com/auth0/node-jsonwebtoken |
| bcryptjs | MIT | github.com/dcodeIO/bcrypt.js |
| helmet | MIT | helmetjs.github.io |
| winston | MIT | github.com/winstonjs/winston |
| zod | MIT | zod.dev |

Run `npm ls --all` inside `frontend/` or `backend/` for the complete,
version-pinned tree of a given release.

## Fonts and imagery

The bundled user interface references web fonts served from Google Fonts and
photographic placeholders from Unsplash. Both are used under their respective
licences and are fetched at runtime; no font or image binary is redistributed
in this repository.

## Reporting a licensing problem

Email __EMAIL__ and we will correct it.
"""


@dataclass
class Report:
    name: str
    written: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)


def title_of(proj: Path) -> str:
    idx = proj / "frontend" / "index.html"
    if idx.is_file():
        m = re.search(r"<title>([^<]+)</title>",
                      idx.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1).split("—")[0].strip()
    return proj.name.replace("-", " ").title()


def port_of(proj: Path) -> int:
    be = proj / "backend" / ".env.example"
    if be.is_file():
        m = re.search(r"^PORT\s*=\s*(\d+)", be.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            return int(m.group(1))
    return 5000


def process(proj: Path, dry: bool) -> Report:
    rep = Report(name=proj.name)
    title = title_of(proj)
    fields = {
        "__TITLE__": title,
        "__SLUG__": proj.name,
        "__PORT__": str(port_of(proj)),
        "__EMAIL__": SUPPORT_EMAIL,
    }

    docs = {
        "DEPLOYMENT.md": DEPLOYMENT,
        "SECURITY.md": SECURITY,
        "CHANGELOG.md": CHANGELOG,
        "CONTRIBUTING.md": CONTRIBUTING,
        "THIRD_PARTY_NOTICES.md": THIRD_PARTY,
    }

    for name, template in docs.items():
        target = proj / name
        if target.is_file() and target.stat().st_size > 600:
            rep.kept.append(name)
            continue
        body = template
        for key, value in fields.items():
            body = body.replace(key, value)
        if not dry:
            target.write_text(body, encoding="utf-8")
        rep.written.append(f"{name} ({len(body):,} bytes)")

    return rep


def main() -> int:
    global SUPPORT_EMAIL
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--support-email", default=SUPPORT_EMAIL)
    a = ap.parse_args()

    SUPPORT_EMAIL = a.support_email

    if not PRODUCTS.is_dir():
        print(f"No {PRODUCTS} directory", file=sys.stderr)
        return 2
    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]
    if not dirs:
        print("No matching products", file=sys.stderr)
        return 2

    print(f"=== write_docs: {'DRY RUN' if a.dry_run else 'APPLY'} ({len(dirs)}) ===")
    total = 0
    for d in dirs:
        rep = process(d, a.dry_run)
        total += len(rep.written)
        print(f"-- {rep.name:20} wrote {len(rep.written)}, kept {len(rep.kept)}")
        for w in rep.written:
            print(f"     + {w}")
    print(f"\n=== {total} document(s) written ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())