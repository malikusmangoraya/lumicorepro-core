# Deployment Guide

This is the **canonical** deployment procedure for LumicorePro: **Docker Compose on
a single VPS, with nginx serving the static React build and terminating TLS.**

Everything below describes that topology. The Kubernetes manifests in `k8s/` are a
secondary target for the same application — they are documented in `k8s/README.md`,
are not exercised by CI, and are not what this guide deploys.

For day-2 operations (health checks, backup/restore, rollback, AI-agent outages)
see **[RUNBOOK.md](./RUNBOOK.md)**.

---

## 1. Topology

```
                        :80 / :443
   Internet ─────────────────────────▶ nginx            (edge: TLS, routing, headers)
                                        │
                          "/" ──────────┤
                                        ▼
                                  frontend            (nginx, static dist/, :8080)
                          "/api/*" ─────┐
                          "/uploads/*"  │
                          "/socket.io/*"│
                          "/api-docs"   ▼
                                  backend             (Express + Sequelize, :5000)
                                        │
                                        ├──▶ db       (PostgreSQL 16, internal)
                                        ├──▶ redis    (Redis 7, internal, password)
                                        └──▶ ai-agent (FastAPI, :8000, internal)
```

Only `nginx` publishes host ports. `db`, `redis`, `backend` and `ai-agent` are
reachable only on the `lumicorepro-network` bridge. Postgres and Redis additionally
bind to `127.0.0.1` so `psql`/`redis-cli` work over an SSH tunnel.

The frontend and the API share **one origin** (`PUBLIC_ORIGIN`). The SPA calls
`{PUBLIC_ORIGIN}/api`, nginx routes that prefix to the backend, and the browser
therefore sees a same-origin request: no CORS preflight for the normal path, and
cookies/`Authorization` headers behave normally.

---

## 2. Prerequisites

| Requirement | Notes |
|-------------|-------|
| Docker Engine 24+ | `docker --version` |
| Docker Compose v2.20+ | `docker compose version` (the plugin, not `docker-compose` v1) |
| A DNS A/AAAA record | pointing `SERVER_NAME` (and `www.` if used) at the VPS |
| Ports 80 and 443 open | 80 is needed for the ACME challenge even if you redirect to HTTPS |
| ~4 GB RAM, 2 vCPU, 40 GB disk | backend 512 MB + frontend small + Postgres + Redis + agent up to 1 GB |
| git, openssl | for clone and secret generation |

---

## 3. Environment variables

```bash
git clone <repository-url> /srv/lumicorepro
cd /srv/lumicorepro
cp .env.production.example .env.production
$EDITOR .env.production
```

`.env.production` is gitignored. Never commit it and never bake its values into an
image.

### Required (`docker compose` refuses to start without them)

| Variable | Purpose |
|----------|---------|
| `SERVER_NAME` | TLS host name; becomes nginx `server_name` and the certbot `live/<name>` path |
| `PUBLIC_ORIGIN` | Full public origin, e.g. `https://example.com`. Used for `FRONTEND_URL`, `CORS_ORIGIN` and as the frontend build arg |
| `POSTGRES_PASSWORD` | Database password. Also baked into the volume on first init — see § 8 |
| `REDIS_PASSWORD` | Redis runs with `--requirepass`; there is no passwordless mode |
| `JWT_SECRET` | ≥ 32 chars. `openssl rand -hex 48` |
| `JWT_REFRESH_SECRET` | ≥ 32 chars, **different** from `JWT_SECRET` |
| `GHCR_OWNER` | Lowercase GitHub owner that publishes the images |

### Recommended

| Variable | Default | Why change it |
|----------|---------|---------------|
| `IMAGE_TAG` | `latest` | Pin to a commit SHA for a reproducible deploy and a one-command rollback |
| `CORS_ORIGIN` | `PUBLIC_ORIGIN` | Only needed if other origins call the API |
| `ACTIVE_AI_PROVIDER` + one provider key | `grok`, none set | Without a key the agent starts but cannot generate |
| `SENTRY_DSN` | empty | Error tracking |
| `SMTP_*`, `FROM_EMAIL` | empty | Transactional email |
| `STRIPE_*` | empty | Payments |

### `VITE_API_URL` — read this before changing it

Vite inlines `VITE_*` variables at **build** time. `docker-compose.prod.yml` passes
`VITE_API_URL=${PUBLIC_ORIGIN}` into the image build, which is correct for this
topology: the SPA calls the same origin it is served from, and nginx proxies
`/api` to the backend.

Consequences:

* Changing `PUBLIC_ORIGIN` requires **rebuilding** the frontend image
  (`docker compose -f docker-compose.prod.yml build frontend`), not just a restart.
* Setting `VITE_API_URL` to a *different* origin (e.g. `https://api.example.com`)
  makes every API call cross-origin, so that origin must also be in `CORS_ORIGIN`.
  The Compose topology does not require it.
* A runtime-configurable value would need a new mechanism (an `env.js` served by
  nginx and read in `src/services/api.js`). That is a source change in `src/**`
  and is deliberately **not** part of this deployment path.

### AI agent authentication

`AGENT_API_KEY` is **empty by default and should stay empty** in the Compose
topology. The agent refuses unauthenticated access when the variable is set, but
`backend/routes/ai.routes.js` calls the agent without an `X-API-Key` header, so
enabling it breaks every AI request with 401/503.

The agent is instead protected by network isolation: it has no published port and
only `backend` can reach `ai-agent:8000`. Making the key usable requires a
backend source change (forward the header in `callAgent()`); that is outside this
runbook's scope and is tracked as a known gap.

---

## 4. TLS certificates

The stack cannot start on `:443` without certificates — this is intentional. Silent
HTTP fallback would make "TLS enabled" untrue.

```bash
# 1. DNS must already resolve to this host and ports 80/443 must be free.
mkdir -p ssl/certs ssl/www

# 2. First issuance with the standalone plugin (nothing else may hold :80 yet).
docker run --rm -p 80:80 \
  -v "$PWD/ssl/certs:/etc/letsencrypt" \
  -v "$PWD/ssl/www:/var/www/certbot" \
  certbot/certbot certonly --standalone \
  -d "$SERVER_NAME" -d "www.$SERVER_NAME" \
  --email admin@example.com --agree-tos --no-eff-email
```

Renewal is handled by the `certbot` service in `docker-compose.prod.yml`, which
runs `certbot renew --webroot -w /var/www/certbot` every 12 hours. nginx serves
`/.well-known/acme-challenge/` from that same volume, so no downtime is needed.

After a renewal, reload nginx to pick up the new certificate:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec nginx nginx -s reload
```

Verify:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec certbot certbot certificates
echo | openssl s_client -connect "$SERVER_NAME:443" -servername "$SERVER_NAME" 2>/dev/null \
  | openssl x509 -noout -subject -dates
```

Certificates live in `ssl/certs` on the host and are mounted read-only into nginx.
Back that directory up — reissuing is possible but rate-limited by Let's Encrypt.

---

## 5. First deploy

```bash
cd /srv/lumicorepro
docker compose -f docker-compose.prod.yml --env-file .env.production pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
docker compose -f docker-compose.prod.yml --env-file .env.production ps
```

On a machine without registry access, build locally instead of pulling:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Now provision the database (§ 6) before expecting the app to serve anything —
`/api/health` answers before the schema exists, but every data endpoint will fail.

---

## 6. Migrations and the base schema

> **Known gap, stated plainly.** This repository does not contain a single
> canonical base schema that recreates the production database from scratch.
> The running schema is created by the Sequelize models in `backend/models/`,
> and `backend/config/database.js` only calls `sequelize.sync()` when
> `NODE_ENV=development` — so in production nothing creates tables
> automatically. `database/migrations/*.sql` are **additive** scripts written
> against an existing database (they reference `users`), and
> `database/schemas/*.sql` are reference schemas used by the AI agent when it
> generates customer projects; they are **not** the schema of this application.
>
> The previous `docker-compose.prod.yml` mounted `./database/schema.sql` into
> `docker-entrypoint-initdb.d/`. That file does not exist, so Docker created an
> empty *directory* with that name and the database was initialised empty while
> the mount looked like a working init step. The mount is gone. Do not re-add a
> mount for a file that is not in the repository.

### Option A — provision from an existing database (recommended)

Promote a working database (staging, or a developer database created with
`npm run dev` from `backend/`) into production:

```bash
# On the SOURCE machine:
pg_dump --format=custom --no-owner --no-privileges "$SOURCE_DATABASE_URL" > base.pg.dump

# Copy base.pg.dump to the VPS, then:
docker compose -f docker-compose.prod.yml --env-file .env.production \
  cp base.pg.dump db:/tmp/base.pg.dump
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec db pg_restore --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --no-owner --no-privileges --exit-on-error /tmp/base.pg.dump
```

Then apply the migrations that post-date that dump (§ below).

### Option B — seed a fresh database from the models

Run the backend once in development mode against the production database so
`sequelize.sync()` creates the tables, then immediately switch back to
`NODE_ENV=production`:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  run --rm -e NODE_ENV=development backend node -e "import('./config/database.js').then(m => m.default.sync())"
```

`sync()` without `{ alter: true }` only creates missing tables; it will not
modify or drop existing ones. **Verify the result** (§ 7) before serving traffic —
if any model fails to sync, fix it rather than shipping a partial schema.

### Applying migrations

Migrations are additive and idempotent (`IF NOT EXISTS` / `ADD COLUMN IF NOT
EXISTS`), so re-running them is safe. There is no migration-runner script in the
repository; apply them in lexical order:

```bash
for f in database/migrations/*.sql; do
  case "$f" in *.down.sql) continue;; esac
  echo "--- $f"
  docker compose -f docker-compose.prod.yml --env-file .env.production \
    exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$f"
done

# Supporting indexes (idempotent; also available as `npm run db:indexes` in backend/)
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  < database/schemas/indexes.sql
```

`database/schemas/indexes.sql` is the one schema file that *is* meant for this
application; it is the `backend/scripts/apply-indexes.js` target.

CI runs the same migrations against a throwaway Postgres (job
`db-migration-check` in `.github/workflows/ci.yml`) to prove they parse, apply
twice without error, and that the `.down.sql` rollbacks execute. That validates
the SQL, **not** that your production schema matches the models.

---

## 7. Verification

Run these on the VPS after every deploy. Full checklist: `RUNBOOK.md` § "Is the
deploy healthy?".

```bash
# 1. Every service is up and healthy
docker compose -f docker-compose.prod.yml --env-file .env.production ps
#    Expect: db/redis "healthy", backend "healthy", ai-agent "healthy",
#            nginx/frontend/certbot "running"

# 2. Edge answers over TLS
curl -fsS "https://$SERVER_NAME/health"                 # -> OK
curl -fsSI "https://$SERVER_NAME/" | head -n 1          # -> HTTP/2 200

# 3. HTTP redirects to HTTPS
curl -sI "http://$SERVER_NAME/" | grep -i '^location'   # -> https://…

# 4. Security headers are present on the document response
curl -fsSI "https://$SERVER_NAME/" \
  | grep -iE 'content-security-policy|strict-transport-security|x-content-type-options'
#    HSTS must be present; CSP must not contain 'unsafe-eval'.

# 5. API is reachable through the edge and the database is connected
curl -fsS "https://$SERVER_NAME/api/health"
curl -fsS "https://$SERVER_NAME/api/health/detailed"

# 6. SPA deep links are served by the fallback, not 404
curl -fsS -o /dev/null -w '%{http_code}\n' "https://$SERVER_NAME/login"   # -> 200

# 7. Hashed assets are cached immutably
asset=$(curl -fsS "https://$SERVER_NAME/" | grep -o '/assets/[^"]*\.js' | head -n1)
curl -fsSI "https://$SERVER_NAME$asset" | grep -i cache-control
#    -> public, max-age=31536000, immutable

# 8. AI agent is up (internal network only)
docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec backend node -e "fetch('http://ai-agent:8000/health').then(r=>r.text()).then(console.log)"
```

A failed step is a failed deploy. Do not proceed to "it's probably fine" — see
`RUNBOOK.md` § Rollback.

---

## 8. Releases and rollback

Releases are tag-driven. `.github/workflows/deploy.yml` runs on a `v*.*.*` tag:

1. **verify** — re-runs lint, unit tests, build and bundle budget against the
   tagged commit, so a tag on a red commit cannot publish.
2. **build-images** — builds both images, pushes them to GHCR tagged with the
   version, `major.minor`, `latest` **and the commit SHA**.
3. **deploy** — only if `VPS_HOST`, `VPS_USER` and `VPS_SSH_KEY` repository
   secrets exist: it SSHes in and runs `docker compose pull && up -d` with
   `IMAGE_TAG` set to the commit SHA, then probes `/api/health` for 30 s. If
   those secrets are absent the job is **skipped** and a summary explains the
   exact manual commands. It never reports a deploy it did not perform.

To cut a release:

```bash
git tag v1.2.3 && git push origin v1.2.3
```

If the deploy job was skipped, deploy by hand on the VPS:

```bash
cd /srv/lumicorepro
export IMAGE_TAG=<commit-sha-from-the-workflow-summary>
docker compose -f docker-compose.prod.yml --env-file .env.production pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --remove-orphans
curl -fsS "https://$SERVER_NAME/api/health"
```

**Rollback** is the same procedure with the previous `IMAGE_TAG`:

```bash
export IMAGE_TAG=<previous-sha>
docker compose -f docker-compose.prod.yml --env-file .env.production pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --remove-orphans
```

Because images are tagged by SHA, this is deterministic. If a release also
changed the database schema, restoring from a pre-release dump may be required —
see `RUNBOOK.md` § Rollback for the decision tree.

---

## 9. Local development (not production)

For a developer machine, `docker-compose.yml` runs the same topology with these
differences: `DEMO_MODE=true`, a self-signed certificate, host ports bound to
`127.0.0.1`, and a default Redis password so a fresh clone starts with only the
JWT secrets set.

```bash
cp .env.example .env          # set JWT_SECRET, JWT_REFRESH_SECRET
bash scripts/dev-certs.sh     # self-signed cert for the local edge
docker compose up -d
# https://localhost            (self-signed warning is expected)
```

Most development does not need containers at all: `npm run dev:full` runs Vite on
`:5173` with a proxy to the backend on `:5000`.

---

## 10. Assumptions and placeholders in this repository

Nothing here invents a credential or a host name. Where a real value is required,
the file says so and uses an obvious placeholder:

| Placeholder | Where | What you must supply |
|-------------|-------|----------------------|
| `example.com` | `.env.production.example`, `nginx/ssl/README.md` | Your real domain (`SERVER_NAME`, `PUBLIC_ORIGIN`) |
| `admin@example.com` | `nginx/ssl/README.md`, § 4 above | The Let's Encrypt contact address |
| `noreply@example.com` | `.env.production.example` (`FROM_EMAIL`) | Your sending address |
| `ghcr.io/<owner>/…` | `docker-compose.prod.yml` (`GHCR_OWNER`) | GitHub owner publishing the images |
| `lumicorepro.com` | `k8s/configmap.yaml`, `k8s/ingress.yaml`, `nginx/security-headers.conf` (`connect-src`) | Your domain — these are the *secondary* k8s/edge defaults and must be updated if you use them |
| `1.0.0` | `k8s/*-deployment.yaml` | A real released image tag or commit SHA |
| `REPLACE_ME` | `k8s/secret.example.yaml` | Real secrets, created with `kubectl create secret` |
| `redis_dev_password` | `docker-compose.yml` | Nothing — local-only fallback, and the port is not published |

Two values are baked into `nginx/security-headers.conf` and must be edited if your
domain differs: the CSP `connect-src` entry `https://api.lumicorepro.com` (only
needed if you use a separate API origin) and the HSTS `preload` directive (drop
`preload` if any subdomain is not HTTPS-ready).

---

## 11. Known gaps

These are real and are not hidden behind a passing check:

1. **No canonical base schema** (§ 6). The first production database must be
   provisioned from an existing database or by a one-off `sequelize.sync()`.
2. **No AI-agent authentication in the Compose path** (§ 3). Network isolation
   only; `AGENT_API_KEY` cannot be enabled without a backend source change.
3. **Brotli is not enabled.** The stock nginx images do not include the
   `ngx_brotli` module, so `brotli on` would make nginx fail to start. gzip is
   configured; brotli needs a custom nginx build.
4. **`PUBLIC_ORIGIN` changes require a frontend rebuild** (§ 3).
5. **The CSP does not whitelist an analytics vendor.** `index.html` loads no
   analytics script and `VITE_ENABLE_ANALYTICS` defaults to false. Enabling
   Plausible or GA4 requires extending `script-src` (and `connect-src` for GA4) in
   `nginx/security-headers.conf`, or the script is blocked.
6. **`frontend` and `ai-agent` have no `deploy.resources` reservations in dev**
   and no memory limit in either file for `frontend` — a runaway static container
   is unlikely, but it is unconstrained.
7. **The local `nginx.conf` uses `server_name _`** with a self-signed certificate,
   so SNI/Host routing is not exercised until you deploy with the prod config.
