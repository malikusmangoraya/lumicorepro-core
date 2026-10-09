#!/bin/bash
# install-docker-compose.sh
# Usage:
#   bash products/_audit/install-docker-compose.sh [--force]
#
# What it does for every product in products/
#   - writes products/<name>/docker-compose.yml
#   - writes products/<name>/docker-compose.override.yml.example
#   - writes products/<name>/.dockerignore
#
set -euo pipefail

ROOT="D:/lumicorepro-core"
TEMPLATE="$ROOT/products/_audit/docker-compose-template.yml"
PRODUCTS=(
  apex
  aurelia-estates
  aurum-fitness
  claimflow-ai
  flowpilot
  meridian-capital
  nuage-events
  prestige-studio
  resupro
  saffron-voyage
  studio-lumen
)

FORCE=0
if [[ " ${*} " =~ " --force " ]]; then
  FORCE=1
fi

die() {
  echo "ERROR: $*" >&2
  exit 1
}

for name in "${PRODUCTS[@]}"; do
  prod="$ROOT/products/$name"
  backend="$prod/backend"
  frontend="$prod/frontend"

  if [[ $FORCE -eq 0 && -f "$prod/docker-compose.yml" ]]; then
    echo "skip $name/docker-compose.yml already exists"
    continue
  fi

  echo "writing $name/docker-compose.yml"
  cp "$TEMPLATE" "$prod/docker-compose.yml"

  echo "writing $name/docker-compose.override.yml.example"
  cat > "$prod/docker-compose.override.yml.example" <<'OVERRIDE'
# docker-compose.override.yml.example
# Copy to docker-compose.override.yml for local development.
# This file is ignored by git in each product.

version: "3.9"

services:
  backend:
    build:
      target: dev
    environment:
      NODE_ENV: development
    ports:
      - "127.0.0.1:3000:3000"
    volumes:
      - ./backend:/app
      - /app/node_modules
      - ./backend/uploads:/app/uploads

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NODE_ENV: development
    ports:
      - "127.0.0.1:5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/dist
OVERRIDE

  echo "writing $name/.dockerignore"
  cat > "$prod/.dockerignore" <<'IGNORE'
node_modules
dist
build
coverage
.git
.venv
__pycache__
.pytest_cache
.env
.env.local
*.log
.DS_Store
frontend/node_modules
frontend/dist
IGNORE

  echo "done $name"
done

echo "all products processed"
