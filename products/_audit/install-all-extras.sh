#!/bin/bash
# install-all-extras.sh
# Usage:
#   bash products/_audit/install-all-extras.sh [--force]
#
# Installs to every product in products/:
#   - docker-compose.yml
#   - docker-compose.override.yml.example
#   - .dockerignore
#   - backend/webhook-registry.json
#   - backend/models/WebhookEvent.js
#   - backend/middleware/webhook-errors.js
#   - backend/utils/webhook-logger.js
#   - backend/routes/healthcheck.js
#   - backend/healthcheck.js
#
# Prints a short per-product summary when done.
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

ensure_dir() {
  mkdir -p "$1"
}

failed=()
for name in "${PRODUCTS[@]}"; do
  prod="$ROOT/products/$name"
  backend="$prod/backend"
  models="$backend/models"
  middleware="$backend/middleware"
  utils="$backend/utils"
  routes="$backend/routes"

  ensure_dir "$backend"
  ensure_dir "$models"
  ensure_dir "$middleware"
  ensure_dir "$utils"
  ensure_dir "$routes"

  # ---- docker-compose files ----

  if [[ $FORCE -eq 0 && -f "$prod/docker-compose.yml" ]]; then
    echo "skip $name/docker-compose.yml already exists"
  else
    echo "writing $name/docker-compose.yml"
    if [[ ! -f "$TEMPLATE" ]]; then
      failed+=("$name: docker-compose template missing at $TEMPLATE")
      continue
    fi
    cp "$TEMPLATE" "$prod/docker-compose.yml"
  fi

  if [[ $FORCE -eq 0 && -f "$prod/docker-compose.override.yml.example" ]]; then
    echo "skip $name/docker-compose.override.yml.example already exists"
  else
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
  fi

  if [[ $FORCE -eq 0 && -f "$prod/.dockerignore" ]]; then
    echo "skip $name/.dockerignore already exists"
  else
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
  fi

  # ---- webhook extras ----

  if [[ $FORCE -eq 0 && -f "$backend/webhook-registry.json" ]]; then
    echo "skip $name/backend/webhook-registry.json already exists"
  else
    echo "writing $name/backend/webhook-registry.json"
    cat > "$backend/webhook-registry.json" <<'JSON'
{
  "version": "1.0.0",
  "provider": "payments",
  "routes": {
    "verify": "POST /api/payments/webhook",
    "health": "GET /api/health"
  },
  "retries": {
    "maxAttempts": 5,
    "backoffMs": 1000
  }
}
JSON
  fi

  if [[ $FORCE -eq 0 && -f "$models/WebhookEvent.js" ]]; then
    echo "skip $name/models/WebhookEvent.js already exists"
  else
    echo "writing $name/models/WebhookEvent.js"
    cat > "$models/WebhookEvent.js" <<'MODEL'
"use strict";

const { Model, DataTypes } = require("sequelize");

class WebhookEvent extends Model {
  static init(sequelize) {
    return super.init(
      {
        id: {
          type: DataTypes.INTEGER,
          primaryKey: true,
          autoIncrement: true,
        },
        event_id: {
          type: DataTypes.STRING,
          allowNull: false,
          unique: true,
        },
        event_type: {
          type: DataTypes.STRING,
          allowNull: false,
        },
        gateway: {
          type: DataTypes.STRING,
          allowNull: false,
        },
        payload: {
          type: DataTypes.JSONB,
          allowNull: true,
        },
        status: {
          type: DataTypes.ENUM("pending", "processed", "failed"),
          defaultValue: "pending",
        },
        response_code: {
          type: DataTypes.INTEGER,
        },
        error_message: {
          type: DataTypes.TEXT,
        },
      },
      {
        sequelize,
        modelName: "WebhookEvent",
        tableName: "webhook_events",
        timestamps: true,
      }
    );
  }
}

module.exports = WebhookEvent;
MODEL
  fi

  if [[ $FORCE -eq 0 && -f "$middleware/webhook-errors.js" ]]; then
    echo "skip $name/middleware/webhook-errors.js already exists"
  else
    echo "writing $name/middleware/webhook-errors.js"
    cat > "$middleware/webhook-errors.js" <<'MIDDLEWARE'
"use strict";

/**
 * webhookErrors middleware
 * Wraps webhook route handlers to convert thrown errors into non-user-facing
 * responses and log structured context.
 */
function webhookErrors(logger) {
  return (req, res, next) => {
    try {
      next();
    } catch (err) {
      logger.error("webhook handler error", {
        eventId: req.headers["x-event-id"] || "unknown",
        eventType: req.headers["x-event-name"] || "unknown",
        error: err.message,
      });
      res.status(500).json({ success: false, error: "webhook processing failed" });
    }
  };
}

module.exports = webhookErrors;
MIDDLEWARE
  fi

  if [[ $FORCE -eq 0 && -f "$utils/webhook-logger.js" ]]; then
    echo "skip $name/utils/webhook-logger.js already exists"
  else
    echo "writing $name/utils/webhook-logger.js"
    cat > "$utils/webhook-logger.js" <<'UTIL'
"use strict";

const pino = require("pino");

let logger = null;

function getLogger() {
  if (logger) return logger;
  logger = pino({
    level: process.env.LOG_LEVEL || "info",
    base: {
      provider: "payments-webhook",
    },
  });
  return logger;
}

module.exports = { getLogger };
UTIL
  fi

  if [[ $FORCE -eq 0 && -f "$routes/healthcheck.js" ]]; then
    echo "skip $name/routes/healthcheck.js already exists"
  else
    echo "writing $name/routes/healthcheck.js"
    cat > "$routes/healthcheck.js" <<'ROUTE'
"use strict";

const express = require("express");

const router = express.Router();

router.get("/health", (req, res) => {
  res.json({
    success: true,
    status: "ok",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

module.exports = router;
ROUTE
  fi

  if [[ $FORCE -eq 0 && -f "$backend/healthcheck.js" ]]; then
    echo "skip $name/backend/healthcheck.js already exists"
  else
    echo "writing $name/backend/healthcheck.js"
    cat > "$backend/healthcheck.js" <<'HC'
"use strict";

const http = require("http");

function startHealthServer(port) {
  const srv = http.createServer((req, res) => {
    if (req.url === "/health" && req.method === "GET") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        success: true,
        status: "ok",
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
      }));
    } else {
      res.writeHead(404);
      res.end();
    }
  });

  srv.listen(port, () => {
    console.log(`healthcheck listening on :${port}`);
  });

  return srv;
}

module.exports = { startHealthServer };
HC
  fi
done

if [[ ${#failed[@]} -gt 0 ]]; then
  echo "some products failed to install extras:"
  for line in "${failed[@]}"; do
    echo "  $line"
  done
  exit 1
fi

echo "all products processed"
