# Runbook

Day-2 operations for the canonical deployment: **Docker Compose on a single VPS**
(see [DEPLOYMENT.md](./DEPLOYMENT.md) for the topology and first-deploy procedure).

Every command below assumes:

```bash
cd /srv/lumicorepro
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.production"
```

All commands are run from the repository root on the VPS. `$SERVER_NAME` is the
value from `.env.production`.

---

## 1. Is the deploy healthy?

Run in order. Each step states what a healthy answer looks like; stop at the first
failure and use the section it points to.

### 1.1 Containers

```bash
$COMPOSE ps
```

| Service | Expected |
|---------|----------|
| `db` | `Up … (healthy)` |
| `redis` | `Up … (healthy)` |
| `backend` | `Up … (healthy)` |
| `ai-agent` | `Up … (healthy)` — `(health: starting)` for the first ~60 s is normal |
| `nginx`, `frontend`, `certbot` | `Up …` |

A container in `Restarting` is a real failure, not a warm-up. Get its logs first
(§ 1.6) — a crash loop overwrites the interesting output within seconds.

### 1.2 The site answers over TLS

```bash
curl -fsS  "https://$SERVER_NAME/health"                 # -> OK
curl -fsSI "https://$SERVER_NAME/" | head -n 1           # -> HTTP/2 200
curl -sI   "http://$SERVER_NAME/"  | grep -i '^location' # -> https://…
```

### 1.3 The API and its dependencies

```bash
curl -fsS "https://$SERVER_NAME/api/health"
curl -fsS "https://$SERVER_NAME/api/health/detailed"
```

`/api/health/detailed` reports the database and Redis connection state. If it
reports the DB as down while `db` is healthy, check `DATABASE_URL` in
`.env.production` against the credentials the volume was initialised with (§ 6).

### 1.4 Security headers and caching

```bash
# HSTS + CSP must be present on the document response
curl -fsSI "https://$SERVER_NAME/" \
  | grep -iE 'content-security-policy|strict-transport-security'

# A hashed asset must be immutable-cached
asset=$(curl -fsS "https://$SERVER_NAME/" | grep -o '/assets/[^"]*\.js' | head -n1)
curl -fsSI "https://$SERVER_NAME$asset" | grep -i cache-control
```

Headers are added per-`location`; if the document has them but an asset does not,
the header include is missing from that location in `nginx/nginx.conf`.

### 1.5 SPA deep links and the API prefix

```bash
for p in / /login /dashboard /api/health; do
  printf '%-14s %s\n' "$p" "$(curl -fsS -o /dev/null -w '%{http_code}' "https://$SERVER_NAME$p")"
done
```

Expect `200` for all four. A `404` on `/login` means the SPA fallback is broken.
A `200` on `/api/health` that returns HTML means nginx is routing `/api` to the
frontend instead of the backend.

### 1.6 Logs

```bash
$COMPOSE logs --tail=200 backend          # API errors
$COMPOSE logs --tail=200 nginx            # routing / TLS / upstream errors
$COMPOSE logs --tail=200 ai-agent         # generation pipeline
$COMPOSE logs --tail=100 db               # Postgres
$COMPOSE logs --tail=100 certbot          # renewal
```

Follow one service live with `$COMPOSE logs -f backend`.

### 1.7 Resource pressure

```bash
docker stats --no-stream
df -h /var/lib/docker          # a full disk is the most common silent outage
docker system df               # reclaimable images / build cache
```

A full disk stops Postgres writes and then the whole stack. Reclaim with
`docker image prune -a --filter "until=168h"` — **not** `docker system prune -a
--volumes`, which deletes the database volume.

### 1.8 Verify the WebSocket

Notifications are delivered over Socket.IO through the edge. With more than one
backend replica (Kubernetes only — Compose runs one), sticky sessions are
required. To check:

```bash
$COMPOSE exec backend node -e "
const { io } = require('socket.io-client');
const s = io('http://127.0.0.1:5000', { transports: ['websocket'] });
s.on('connect', () => { console.log('connected', s.id); s.close(); process.exit(0); });
s.on('connect_error', (e) => { console.error('failed', e.message); process.exit(1); });
setTimeout(() => { console.error('timeout'); process.exit(1); }, 10000);
"
```

Then repeat through the public origin from your own machine:
`wss://$SERVER_NAME/socket.io/`. A connection that succeeds directly but fails
through nginx points at the `/socket.io/` location or the upgrade headers.

### 1.9 Certificate expiry

```bash
echo | openssl s_client -connect "$SERVER_NAME:443" -servername "$SERVER_NAME" 2>/dev/null \
  | openssl x509 -noout -enddate
$COMPOSE exec certbot certbot certificates
```

Renewal runs automatically every 12 h. After a renewal, reload nginx:

```bash
$COMPOSE exec nginx nginx -s reload
```

Alert on **< 14 days** remaining: that means renewal has been failing for weeks.

---

## 2. Backup and restore

### 2.1 What is backed up, and how

| Data | Mechanism | Where |
|------|-----------|-------|
| PostgreSQL | `.github/workflows/backup.yml` (nightly 03:10 UTC) runs `scripts/backup-db.sh`, then **restores the dump into a scratch database** and verifies it | GitHub Actions artifact, 14-day retention |
| Uploaded files | `backend_uploads` Docker volume | Only in the volume; **not** in the CI artifact unless `ARTIFACTS_DIR` points at it |
| AI agent state | `agent_state` + `agent_projects` volumes (SQLite + generated sites) | Only in the volumes |
| TLS certificates | `./ssl/certs` (host directory) | Host filesystem |

> The CI artifact is a **verification copy**, not a retention strategy. There is no
> off-site backup configured in this repository. Set one up (object storage,
> `restic`, or `pgBackRest`) before you rely on this for recovery. Until then,
> recovery depends on the volumes on the VPS itself.

### 2.2 Manual backup (VPS)

```bash
STAMP="$(date -u +%Y%m%d_%H%M%S)"
mkdir -p backups

# Database
$COMPOSE exec -T db pg_dump --format=custom --no-owner --no-privileges \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "backups/db-$STAMP.pg.dump"
sha256sum "backups/db-$STAMP.pg.dump" > "backups/db-$STAMP.pg.dump.sha256"

# Uploads volume
docker run --rm -v lumicorepro-uploads:/data:ro -v "$PWD/backups:/backup" alpine \
  tar -czf "/backup/uploads-$STAMP.tar.gz" -C /data .

# AI agent state + generated projects
docker run --rm -v lumicorepro-agent-state:/data:ro -v "$PWD/backups:/backup" alpine \
  tar -czf "/backup/agent-state-$STAMP.tar.gz" -C /data .
docker run --rm -v lumicorepro-agent-projects:/data:ro -v "$PWD/backups:/backup" alpine \
  tar -czf "/backup/agent-projects-$STAMP.tar.gz" -C /data .

# TLS certificates
tar -czf "backups/certs-$STAMP.tar.gz" -C ssl certs
```

Then copy `backups/` off the machine. A backup that only exists on the server it
backs up is not a backup.

### 2.3 Restore verification — do this monthly, and after any restore

Never assume a dump is good. Verify it against a **scratch database**, never the
live one.

```bash
DUMP=backups/db-YYYYMMDD_HHMMSS.pg.dump

# 0. Integrity
sha256sum -c "$DUMP.sha256"

# 1. Scratch database inside the running Postgres container
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS restorecheck;" -c "CREATE DATABASE restorecheck;"

# 2. Restore
$COMPOSE exec -T db pg_restore \
  --username "$POSTGRES_USER" --dbname restorecheck \
  --no-owner --no-privileges --exit-on-error < "$DUMP"

# 3. It answers a query
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d restorecheck -c "SELECT 1;"

# 4. The schema came back
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d restorecheck -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

# 5. The DATA came back — the check that actually matters
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d restorecheck -tAc \
  "SELECT count(*) FROM users;"

# 6. Per-table sanity (informational)
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d restorecheck -c \
  "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 15;"

# 7. Clean up
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE restorecheck;"
```

Pass criteria: step 3 returns `1`; step 4 is ≥ 1; **step 5 is ≥ 1**. A restored
schema with zero users means the dump captured an empty database — a backup that
would restore a working, empty application.

The nightly workflow performs exactly these checks (steps 1–5) and fails the run
if any of them fail. If that job is red, **last night's backup is not valid**.
If the job has not run at all (no `DATABASE_URL` secret configured), there is no
automated verification and this manual procedure is the only evidence.

### 2.4 Full restore (disaster recovery)

This destroys current data. Confirm you have the right dump and that the app is
stopped or in maintenance.

```bash
$COMPOSE stop backend ai-agent          # stop writers, keep db/redis/nginx

# Safety net: snapshot the current (broken) database before overwriting it
$COMPOSE exec -T db pg_dump --format=custom -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  > "backups/pre-restore-$(date -u +%Y%m%d_%H%M%S).pg.dump"

$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" \
  -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

$COMPOSE exec -T db pg_restore \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --no-owner --no-privileges --exit-on-error < "$DUMP"

# Uploads / agent state, if restoring those too
docker run --rm -v lumicorepro-uploads:/data -v "$PWD/backups:/backup" alpine \
  sh -c 'rm -rf /data/* && tar -xzf /backup/uploads-YYYYMMDD_HHMMSS.tar.gz -C /data'

$COMPOSE start backend ai-agent

# Re-run § 1, and § 6 for migrations that post-date the dump
```

**Point-in-time note.** A nightly logical dump loses up to 24 h of writes. If that
is unacceptable, enable WAL archiving (`archive_mode`, `archive_command`, plus
`pgBackRest` or `wal-g`) — not configured here.

---

## 3. Rollback

### 3.1 Decide which rollback you need

| Symptom | Rollback |
|---------|----------|
| New release misbehaves; schema unchanged | § 3.2 — redeploy the previous image tag. Fast, no data loss. |
| New release included a migration that is not backward compatible | § 3.2 first, then § 3.3 if the old code cannot read the new schema. |
| Data corrupted by the release | § 3.2 to stop the bleeding, then § 2.4 (full restore) — accepts data loss back to the dump. |
| Only one service is broken | § 3.2 with that service only, using the same `IMAGE_TAG` mechanism. |

### 3.2 Roll back the images

Images are pushed tagged with the commit SHA as well as the version, so a rollback
is deterministic:

```bash
# Find the previous good tag: git tags, or the Release workflow summaries
git tag --sort=-creatordate | head

cd /srv/lumicorepro
export IMAGE_TAG=<previous-commit-sha-or-version>

$COMPOSE pull
$COMPOSE up -d --remove-orphans
$COMPOSE ps
curl -fsS "https://$SERVER_NAME/api/health"
```

Then re-run § 1.3 and § 1.4. If `IMAGE_TAG` was `latest` in
`.env.production`, set it permanently to a concrete tag — a floating `latest`
makes the next rollback guesswork.

### 3.3 Roll back a migration

`database/migrations/` ships `.down.sql` files alongside the forward migrations:

```bash
$COMPOSE exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  < database/migrations/002__add_plans_and_credits.down.sql
```

Read the file first: it drops tables and columns, so **it destroys the data in
them**. `002__add_plans_and_credits.down.sql` drops `subscriptions` and `plans`
and removes the Stripe columns from `users`. Take a dump (§ 2.2) before running it.

CI executes every `.down.sql` against a throwaway database
(`db-migration-check` job), so the SQL is known to run — but only against the
schema those migrations created, never against your production data.

### 3.4 Roll back the frontend only

The frontend is a static bundle baked into an image, so rolling back the frontend
is `IMAGE_TAG=<old-sha> $COMPOSE up -d frontend nginx`. Users with the page open
keep the old bundle until they reload; `index.html` is served `no-cache` and
hashed assets are immutable, so there is no stale-asset window.

---

## 4. The AI agent is offline

### 4.1 Symptoms

* Generation, chat and vision requests fail with a generic
  *"The AI agent is unavailable or returned an error. Please retry."*
  (the backend deliberately never relays the upstream error text).
* `$COMPOSE ps` shows `ai-agent` as `Restarting`, `Exited`, or `(unhealthy)`.
* Backend logs contain `AI agent request failed` and `AI Agent unavailable at
  http://ai-agent:8000`.

Everything else — auth, catalogue, orders, payments, the SPA — keeps working. The
agent is not on the critical path for those.

### 4.2 Triage

```bash
# 1. Is the container even up?
$COMPOSE ps ai-agent
$COMPOSE logs --tail=200 ai-agent

# 2. Does it answer from inside the network?
$COMPOSE exec backend node -e \
  "fetch('http://ai-agent:8000/health').then(r=>r.text()).then(console.log).catch(e=>console.error('UNREACHABLE',e.message))"

# 3. Did configuration change?
grep -E 'AGENT_API_KEY|ALLOWED_HOSTS|CORS_ORIGINS|ACTIVE_AI_PROVIDER' .env.production
grep -cE '^[A-Z_]*API_KEY=.+' .env.production      # at least one key must be non-empty
```

### 4.3 Common causes

| Cause | Evidence | Fix |
|-------|----------|-----|
| No provider API key set | Logs: provider selection failures at startup | Set `ACTIVE_AI_PROVIDER` and at least one of `GROK_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` / `OPENROUTER_API_KEY`, then `$COMPOSE up -d ai-agent` |
| Provider quota exhausted / key revoked | Logs: HTTP 401/429 from the provider | Rotate the key, or switch `ACTIVE_AI_PROVIDER` to a provider with quota |
| `AGENT_API_KEY` set by mistake | Logs: `AGENT_API_KEY is not set` **or** 401 with `x-api-key` errors; § 3 of DEPLOYMENT.md | Unset it — the Express passthrough does not send an API key. Network isolation is the intended control |
| `ALLOWED_HOSTS` missing the in-cluster name | Logs: 400 `Invalid host header` | Include `ai-agent,127.0.0.1,localhost` |
| Out of memory (heavy generation) | <span v-pre>`docker inspect lumicorepro-ai-agent --format '{{.State.OOMKilled}}'`</span> → `true` | Raise the `ai-agent` memory limit, or leave `AI_AGENT_INSTALL_HEAVY_ML=false` so torch/chromadb are not loaded |
| State volume unwritable | Logs: `unable to open database file` | `docker compose … exec -u 0 ai-agent chown -R 10001:10001 /app/database` |
| Slow first start | `(health: starting)` for > 2 min | `start_period` is 60 s; a cold model load can exceed it. Check logs before restarting |

### 4.4 Degradation policy (what users see)

* The backend already degrades: `backend/routes/ai.routes.js` returns a generic
  502/503 for upstream failure, so no stack traces or filesystem paths leak.
* If the outage will last, disable the AI surfaces in the UI or put a banner up.
  There is no feature flag for this in the repository — it is a product decision.
* Do **not** set `DEMO_MODE=true` in production to "work around" an agent outage.
  It changes application behaviour well beyond AI routes.

### 4.5 Recovery confirmation

```bash
$COMPOSE exec backend node -e \
  "fetch('http://ai-agent:8000/health').then(r=>r.json()).then(j=>console.log(j)).catch(e=>console.error(e.message))"
$COMPOSE logs --tail=50 ai-agent
```

Then run one real generation through the UI and watch
`$COMPOSE logs -f ai-agent` for the pipeline phases.

### 4.6 Scale the AI agent

**Do not run more than one replica.** The agent keeps run state in-process
(pipeline store, telemetry, in-memory run registry) and persists to SQLite on a
`ReadWriteOnce` volume. Two replicas would serve inconsistent results for the same
`run_id` and race on the SQLite file. Scaling it means externalising that state
first (Postgres/Redis for run state, object storage for generated projects) —
that is a code change, not a Compose change.

Vertical scaling is supported: raise `deploy.resources.limits.memory` for
`ai-agent` in `docker-compose.prod.yml`.

---

## 5. Routine operations

### 5.1 Deploy a new release

See DEPLOYMENT.md § 8. Short version: tag, let the workflow publish, then
`$COMPOSE pull && $COMPOSE up -d --remove-orphans` with `IMAGE_TAG` pinned.

### 5.2 Apply migrations

See DEPLOYMENT.md § 6. Always take a dump first (§ 2.2).

### 5.3 Restart a service

```bash
$COMPOSE restart backend          # one service
$COMPOSE up -d --force-recreate backend
$COMPOSE exec nginx nginx -s reload     # config/cert reload, no drop
```

### 5.4 Rotate secrets

`JWT_SECRET` / `JWT_REFRESH_SECRET`:

```bash
# 1. New values
$EDITOR .env.production
# 2. Recreate the consumers (this logs everyone out — expected)
$COMPOSE up -d --force-recreate backend
```

Rotating `JWT_SECRET` invalidates every issued token, so all sessions end. Do it
during a quiet window.

`POSTGRES_PASSWORD`: the container is initialised with `POSTGRES_PASSWORD` **only
on first start of an empty volume**. Editing `.env.production` afterwards changes
what the backend tries to use but not the database's actual password. Rotate it in
the database as well:

```bash
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres \
  -c "ALTER USER $POSTGRES_USER WITH PASSWORD 'NEW_PASSWORD';"
# then update .env.production and:
$COMPOSE up -d --force-recreate backend
```

`REDIS_PASSWORD`: update `.env.production`, then
`$COMPOSE up -d --force-recreate redis backend`.

Uploads and generated projects are not affected by any of these.

### 5.5 Inspect the AI agent's persisted state

```bash
$COMPOSE exec ai-agent python - <<'PY'
import sqlite3, os
p = "/app/database/agent.db"
print("exists:", os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else "-")
con = sqlite3.connect(p)
for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    n = con.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
    print(f"{name}: {n}")
PY
```

---

## 6. Incident checklist

Copy this into the incident channel and fill it in as you go.

```
[ ] 1. Impact: what is broken, for whom, since when?
[ ] 2. Is the site up?            curl -fsSI "https://$SERVER_NAME/" | head -n1
[ ] 3. Containers:                $COMPOSE ps
[ ] 4. Logs (last 200 lines):     backend / nginx / db / ai-agent
[ ] 5. Disk:                      df -h /var/lib/docker
[ ] 6. Last change:               git log -1 --format='%h %ci %s' ; git describe --tags
[ ] 7. Decide: roll back (§ 3) or fix forward
[ ] 8. If data is involved:       dump the CURRENT state before any restore (§ 2.4)
[ ] 9. After the fix:             re-run § 1 in full
[ ] 10. Write down the cause and the fix in the issue
```

Rule: **never restore over the live database without first dumping its current
state.** Even a corrupted database is evidence, and often recoverable.

---

## 7. What still needs a real runtime check

These are documented but have not been executed in this environment (no Docker
available where these files were written). Verify them on the first real deploy:

1. `docker compose -f docker-compose.prod.yml config` parses (env interpolation,
   anchors) with a filled-in `.env.production`.
2. Both Dockerfiles build: `Dockerfile.frontend` (two-stage, port 8080,
   non-root) and `ai-agent/Dockerfile` (repo-root context).
3. `nginx -t` passes for `nginx/nginx.conf` **and** for `nginx/nginx.prod.conf`
   **after** envsubst substitution of `${SERVER_NAME}`.
4. The envsubst template mechanism produces a valid `/etc/nginx/nginx.conf` and
   leaves `$host` / `$uri` untouched.
5. The AI agent reaches a provider (a real generation succeeds end to end).
6. `$COMPOSE exec ai-agent python -m pytest tests -q` inside the built image.
7. Socket.IO connects through the edge (§ 1.8).
8. certbot's first issuance and one renewal cycle (§ 1.9).
