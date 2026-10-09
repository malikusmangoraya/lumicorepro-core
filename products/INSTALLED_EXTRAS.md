# Installed Extras — what gets added to every product and why

Last updated: 2026-10-10

This file records the extra files the `products/_audit/install-all-extras.sh` script adds across
all eleven products. It exists so the extras stay traceable and anyone can tell which file is default
copy and which file is product-specific.

## What gets installed everywhere

### Docker/deploy extras

- `docker-compose.yml`
  - postgres + redis + backend + frontend
  - default production compose shape for the product
- `docker-compose.override.yml.example`
  - local development override example
  - copied by hand when a developer wants local compose
- `.dockerignore`
  - keeps node_modules, dist, .env, logs, git out of build context

### Webhook/backend extras

- `backend/webhook-registry.json`
  - small registry describing the webhook route shape and retry policy
  - default placeholder, not a substitute for actual route wiring
- `backend/models/WebhookEvent.js`
  - Sequelize model for webhook event ledger
  - default shape; products with their own webhook events can extend this
- `backend/middleware/webhook-errors.js`
  - error wrapper for webhook handlers
  - returns safe response shape and logs structured context
- `backend/utils/webhook-logger.js`
  - pino logger factory for webhook code
  - default logger shape
- `backend/routes/healthcheck.js`
  - `/api/health` GET endpoint
  - default healthcheck route
- `backend/healthcheck.js`
  - standalone http healthcheck server factory
  - only used if the product explicitly starts it

## What this is not

- It does not run DB migrations automatically.
- It does not seed any data.
- It does not create real webhook provider credentials.
- It does not replace whatever webhook routing a product already has.
- It does not override product-specific services or models.
- It does not guarantee that `pino` is installed in a product yet.

## Files created by this extras pass

- `products/_audit/install-all-extras.sh`
- `products/_audit/docker-compose-template.yml`
- `products/INSTALLED_EXTRAS.md`

Run:
```bash
bash products/_audit/install-all-extras.sh
```

After that, the eleven products should each have the three docker-compose files and the six webhook
files listed above, unless a file already existed and was skipped.

## Notes for future changes

- If a file here should become product-specific, copy it out of the shared installer and edit it
  per product instead of changing the shared script.
- If a new default file is needed everywhere, add it here and to the installer script.
