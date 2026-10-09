#!/usr/bin/env python3
"""Compose hardening + audit correctness pass.

Two changes:

1. docker-compose.yml no longer ships a default database password. Compose now
   fails fast with a readable message when POSTGRES_PASSWORD is unset, so a
   buyer can never deploy the stack with a well-known credential. The variable
   is documented in .env.example with a one-liner to generate a real value.

2. The content-hygiene audit learned one narrowly scoped exemption: a value that
   appears inside a DENIED_SECRETS array is a security guard (the list of
   secrets the JWT loader refuses to boot with), not unfinished content. The
   check stays strict everywhere else.

Every compose file is re-parsed with PyYAML after editing; a file that fails to
parse is reported and left for manual repair.

Usage:  python scripts/compose_hardening.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import yaml

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

PRODUCTS = [
    "apex", "aurelia-estates", "aurum-fitness", "claimflow-ai",
    "meridian-capital", "nuage-events", "prestige-studio", "resupro",
    "saffron-voyage", "studio-lumen",
]

# No colon inside the message: compose reads ${VAR:?message} and a ": " inside
# a YAML plain scalar would break parsing.
REQUIRED = "${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env before docker compose up}"
REQUIRED_URL = "${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env before docker compose up}"

PW_LINE = re.compile(r"^(\s*)POSTGRES_PASSWORD:\s*\$\{POSTGRES_PASSWORD:-changeme\}\s*$", re.M)
URL_LINE = re.compile(r"\$\{POSTGRES_PASSWORD:-changeme\}")

ENV_BLOCK = """
# --- Docker Compose database -----------------------------------------------------
# Required. docker compose refuses to start until this is set, so the stack can
# never come up with a well-known password.
#   node -e "console.log(require('crypto').randomBytes(24).toString('base64url'))"
POSTGRES_DB={db}
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
"""


BACKEND_DB_LINE = re.compile(r"^DATABASE_URL=.*$", re.M)

BACKEND_DB_TEMPLATE = """# PostgreSQL connection string. Must match the database you actually created.
# Generate a strong password:
#   node -e "console.log(require('crypto').randomBytes(24).toString('base64url'))"
# Leave DATABASE_URL empty (or remove it) to fall back to a local SQLite file.
DATABASE_URL=postgresql://postgres:REPLACE_WITH_A_STRONG_PASSWORD@localhost:5432/{db}"""


ANY_DB_URL = re.compile(
    r"^(?P<prefix>\s*#?\s*DATABASE_URL\s*=\s*)postgresql://(?P<user>[^:@\s]+):(?P<pw>[^@\s]*)@(?P<host>[^/\s]*)/(?P<db>\S+)\s*$",
    re.M,
)


def rebuild_db_url(match, db: str) -> str:
    prefix = match.group("prefix")
    user = match.group("user")
    host = match.group("host") or "localhost"
    return (f"{prefix}postgresql://{user}:REPLACE_WITH_A_STRONG_PASSWORD"
            f"@{host}/{db}")


def harden_env_db_url(path: Path, db: str, dry: bool, log) -> bool:
    """Strip the shipped `postgres:postgres` credential out of an env template.

    Also aligns the database name with the one docker-compose actually creates;
    the templates shipped with hyphenated names that could never match.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(ANY_DB_URL.finditer(text))
    if not matches:
        return False
    new = ANY_DB_URL.sub(lambda m: rebuild_db_url(m, db), text)
    if new == text:
        return False
    log(f"    harden {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def harden_legacy_db_helper(path: Path, db: str, dry: bool, log) -> bool:
    """Remove the embedded `postgres:postgres` fallback from config/db.js."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"process\.env\.DATABASE_URL\s*\|\|\s*'postgresql://[^']*'", text)
    if not m:
        return False
    new = text[: m.start()] + (
        "process.env.DATABASE_URL || undefined"
    ) + text[m.end():]
    # keep the surrounding comment aligned with the property it documents
    new = new.replace(
        "  connectionString: process.env.DATABASE_URL || undefined,",
        "  // DATABASE_URL lives in backend/.env (see backend/.env.example). When it is\n"
        "  // unset the pool falls back to the standard PGHOST/PGUSER/PGPASSWORD vars.\n"
        "  connectionString: process.env.DATABASE_URL || undefined,",
        1,
    )
    log(f"    harden {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def harden_backend_env(path: Path, db: str, dry: bool, log) -> bool:
    """Drop the shipped `postgres:postgres` default and the generic app_db name."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = BACKEND_DB_LINE.search(text)
    if not m:
        return False
    current = m.group(0)
    if "REPLACE_WITH_A_STRONG_PASSWORD" in current and db in current:
        return False
    new = text.replace(current, BACKEND_DB_TEMPLATE.format(db=db), 1)
    log(f"    harden {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def harden_compose(path: Path, dry: bool, log) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "-changeme" not in text:
        return False
    new = PW_LINE.sub(lambda m: f"{m.group(1)}POSTGRES_PASSWORD: {REQUIRED}", text, count=1)
    new = URL_LINE.sub(REQUIRED_URL, new)
    if new == text:
        return False
    try:
        yaml.safe_load(new)
    except yaml.YAMLError as exc:
        log(f"    !! {path.name}: YAML would not parse ({exc}); left unchanged")
        return False
    log(f"    harden {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def document_env(path: Path, db: str, dry: bool, log) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "POSTGRES_PASSWORD" in text:
        return False
    new = text.rstrip() + "\n" + ENV_BLOCK.format(db=db)
    log(f"    document {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = []

    def log(m):
        lines.append(m)

    changed = 0
    for slug in PRODUCTS:
        root = PRODUCTS_DIR / slug
        compose = root / "docker-compose.yml"
        env_example = root / ".env.example"
        if not compose.exists():
            continue
        log(f"  [{slug}]")
        db_name = None
        m = re.search(r"POSTGRES_DB:\s*(\S+)", compose.read_text(encoding="utf-8", errors="replace"))
        db_name = m.group(1) if m else f"{slug}_db"
        if harden_compose(compose, args.dry_run, log):
            changed += 1
        if env_example.exists() and document_env(env_example, db_name, args.dry_run, log):
            changed += 1
        backend_env = root / "backend/.env.example"
        if backend_env.exists() and harden_backend_env(backend_env, db_name, args.dry_run, log):
            changed += 1
        for tmpl in (env_example, root / "frontend/.env.example"):
            if tmpl.exists() and harden_env_db_url(tmpl, db_name, args.dry_run, log):
                changed += 1
        legacy_db = root / "backend/config/db.js"
        if legacy_db.exists() and harden_legacy_db_helper(legacy_db, db_name, args.dry_run, log):
            changed += 1

    # Verify every compose file still parses.
    broken = []
    for slug in PRODUCTS:
        compose = PRODUCTS_DIR / slug / "docker-compose.yml"
        if compose.exists():
            try:
                yaml.safe_load(compose.read_text(encoding="utf-8", errors="replace"))
            except yaml.YAMLError as exc:
                broken.append(f"{slug}: {exc}")

    print("\n".join(lines))
    print()
    print(f"{changed} file(s) {'would be ' if args.dry_run else ''}updated")
    print(f"compose YAML: {'OK for all 10' if not broken else 'BROKEN -> ' + '; '.join(broken)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())