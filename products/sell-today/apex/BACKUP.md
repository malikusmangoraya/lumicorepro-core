# Backup and restore

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
