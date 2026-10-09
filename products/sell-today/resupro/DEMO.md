# Demo accounts and sample data

The hosted GitHub Pages preview is frontend-only and has no API, so the
Login page shows where demo access would appear, not working credentials.

For a local full-stack demo:

1. `cp backend/.env.example backend/.env`
2. Set `ENABLE_DEMO_SEED=true` and a strong `DEMO_USER_PASSWORD`.
3. `npm ci && npm run migrate && npm run dev` (backend), `npm ci && npm run dev` (frontend).
4. Sign in with `DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD`.

`NODE_ENV=production` always skips the seed, even if the flags are set.

Sample catalogue data lives in `backend/scripts/seed*.js`.
