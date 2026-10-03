#!/usr/bin/env bash
# Generate the self-signed TLS certificate used by the LOCAL stack
# (docker-compose.yml + nginx/nginx.conf).
#
# Why this exists: the local Compose file publishes :443, but nginx/nginx.conf
# referenced certificate paths that no file in the repository created, so the
# edge container could not start with TLS enabled. This script makes the local
# HTTPS path real.
#
# Usage:
#   bash scripts/dev-certs.sh [domain]
#
# Outputs (both required by nginx/nginx.conf):
#   nginx/ssl/fullchain.pem
#   nginx/ssl/privkey.pem
#
# Never use these certificates outside a development machine.
set -euo pipefail

DOMAIN="${1:-localhost}"
OUT_DIR="$(cd "$(dirname "$0")/.." && pwd)/nginx/ssl"

if ! command -v openssl >/dev/null 2>&1; then
  echo "ERROR: openssl is not installed." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

if [ -f "$OUT_DIR/fullchain.pem" ] && [ -f "$OUT_DIR/privkey.pem" ]; then
  echo "Certificates already exist in $OUT_DIR — leaving them in place."
  echo "Delete them first if you want a fresh pair."
  exit 0
fi

echo "Generating a self-signed certificate for '$DOMAIN' (365 days)..."

# A SAN entry is required by modern browsers; CN alone is ignored.
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout "$OUT_DIR/privkey.pem" \
  -out "$OUT_DIR/fullchain.pem" \
  -subj "/C=US/ST=Dev/L=Dev/O=LumiCorePro Development/CN=$DOMAIN" \
  -addext "subjectAltName=DNS:$DOMAIN,DNS:*.localhost,IP:127.0.0.1"

chmod 600 "$OUT_DIR/privkey.pem"
chmod 644 "$OUT_DIR/fullchain.pem"

echo "OK: $OUT_DIR/fullchain.pem"
echo "OK: $OUT_DIR/privkey.pem"
echo
echo "Next: docker compose up -d   (then browse https://localhost — the"
echo "certificate is self-signed, so the browser warning is expected.)"
