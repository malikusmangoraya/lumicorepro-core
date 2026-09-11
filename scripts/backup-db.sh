#!/usr/bin/env bash
# LumiCorePro — PostgreSQL backup + artifacts pack (free-tier friendly).
# Produces a compressed .tar.gz in ./backups with:
#   - pg_dump SQL dump of the database (or JSON via pg_dump --format=custom)
#   - uploaded user-generated content + project artifacts
# Retention: keeps last 7 dumps (older files removed).
#
# Usage:
#   DATABASE_URL="postgres://user:pass@host:5432/db" \
#   ARTIFACTS_DIR="./uploads" \
#   BACKUP_ROOT="./backups" \
#   ./scripts/backup-db.sh
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-./backups}"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-./uploads}"
KEEP_DUMPS="${KEEP_DUMPS:-7}"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is required" >&2
  exit 1
fi

mkdir -p "$BACKUP_ROOT"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
DEST="$BACKUP_ROOT/lumicorepro-$STAMP"
mkdir -p "$DEST"

# 1) Logical dump (custom format)
pg_dump --format=custom --no-owner --no-privileges \
  "$DATABASE_URL" > "$DEST/db.pg.dump"
echo "OK: db dump -> $DEST/db.pg.dump"

# 2) Also a portable SQL copy
pg_dump --format=plain --no-owner --no-privileges \
  "$DATABASE_URL" > "$DEST/db.sql"
echo "OK: plain SQL -> $DEST/db.sql"

# 3) User artifacts (uploads, generated projects)
if [ -d "$ARTIFACTS_DIR" ] && [ -n "$(ls -A "$ARTIFACTS_DIR" 2>/dev/null || true)" ]; then
  tar -czf "$DEST/artifacts.tar.gz" -C "$(dirname "$ARTIFACTS_DIR")" "$(basename "$ARTIFACTS_DIR")"
  echo "OK: artifacts -> $DEST/artifacts.tar.gz"
else
  echo "SKIP: no artifacts in $ARTIFACTS_DIR"
fi

# 4) Compress + checksum
tar -czf "$DEST.tar.gz" -C "$BACKUP_ROOT" "$(basename "$DEST")"
sha256sum "$DEST.tar.gz" > "$DEST.tar.gz.sha256"
rm -rf "$DEST"

# 5) Retention: keep the newest N archives
ls -1t "$BACKUP_ROOT"/lumicorepro-*.tar.gz 2>/dev/null | tail -n +$((KEEP_DUMPS + 1)) | xargs -r rm -f

echo "DONE: $DEST.tar.gz ($(du -h "$DEST.tar.gz" | cut -f1))"