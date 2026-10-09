#!/bin/bash
# install-webhook-extras.sh
# Usage:
#   bash products/_audit/install-webhook-extras.sh [--force]
#
# Adds baseline webhook infrastructure to every product backend:
#   - backend/webhook-registry.json
#   - backend/models/WebhookEvent.js
#   - backend/middleware/webhook-errors.js
#   - backend/utils/webhook-logger.js
#   - backend/routes/healthcheck.js
#   - backend/healthcheck.js
#   - notes in products/CHANGELOG_WEBHOOK_EVENTS.md
#
set -euo pipefail

ROOT="D:/lumicorepro-core"
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

cat > /tmp/webhook-registry.json <<'JSON'
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

  if [[ $FORCE -eq 0 && -f "$backend/webhook-registry.json" ]]; then
    echo "skip $name/webhook-registry.json exists"
  else
    echo "writing $name/webhook-registry.json"
    cp /tmp/webhook-registry.json "$backend/webhook-registry.json"
  fi

  if [[ $FORCE -eq 0 && -f "$models/WebhookEvent.js" ]]; then
    echo "skip $name/models/WebhookEvent.js exists"
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
    echo "skip $name/middleware/webhook-errors.js exists"
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
    echo "skip $name/utils/webhook-logger.js exists"
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
    echo "skip $name/routes/healthcheck.js exists"
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
    echo "skip $name/healthcheck.js exists"
  else
    echo "writing $name/healthcheck.js"
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

  echo "done $name webhook extras"
done

echo "all products processed for webhook extras"
