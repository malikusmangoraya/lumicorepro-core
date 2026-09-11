# LumiCorePro — Backup & Restore

## Backup (automatic, free)

A GitHub Actions workflow (`.github/workflows/backup.yml`) runs **daily at
03:10 UTC** and produces a `pg_dump` of your database plus user uploads.

Steps to activate:

1. Add a repo secret `DATABASE_URL` pointing to your production database.
   (GitHub → Settings → Secrets and variables → Actions.)
2. Run the workflow: Actions → **Database Backup** → **Run workflow**
   (or wait for the scheduled run).
3. Artifacts for each run are stored on GitHub for **14 days** (free).
   For longer retention, download the `.tar.gz` and store it anywhere —
   Google Drive / Dropbox / a second repo.

## Manual backup

```bash
DATABASE_URL="postgres://user:pass@host:5432/db" \
ARTIFACTS_DIR="./uploads" \
./scripts/backup-db.sh
```

Produces `backups/lumicorepro-<timestamp>.tar.gz` containing:
- `db.pg.dump` — compressed PostgreSQL custom-format dump
- `db.sql` — portable plain-SQL dump (can re-import anywhere)
- `artifacts.tar.gz` — uploaded user content (when present)

Retention: last 7 archives are kept, older are removed.

## Restore

### Option 1 — plain SQL (`db.sql`), new/existing Postgres:

```bash
psql "$DATABASE_URL" -f db.sql
```

### Option 2 — custom-format dump (more reliable, restores in original schema):

```bash
pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" db.pg.dump
```

### Option 3 — from a GitHub Actions artifact:

1. Download and extract the artifact (`.tar.gz`).
2. `tar -xzf lumicorepro-<stamp>.tar.gz`
3. Verify integrity: `sha256sum -c lumicorepro-<stamp>.tar.gz.sha256`
4. Restore with Option 1 or 2.

### After restore

- The backend auto-syncs schema (`sequelize.sync({ alter: false })`).
- Re-run `npm run seed` only if you want fresh demo data
  (it clears existing data — be careful in production).
- Restart the backend worker (`npm run worker`) so cron jobs/queues refresh.

## Restoring ONLY user uploads

```bash
tar -xzf artifacts.tar.gz
# copy the ./uploads output into your deployed upload dir
```

## Verify your backup works

Do a monthly restore test into a scratch Postgres:

```bash
# create scratch db
createdb lumicorepro_restore_test
DATABASE_URL="postgres://user:pass@localhost:5432/lumicorepro_restore_test" \
  pg_restore --clean --no-owner -d lumicorepro_restore_test db.pg.dump
psql lumicorepro_restore_test -c "select count(*) from \"Users\";"
```