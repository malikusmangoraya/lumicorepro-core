# Deployment Guide

This guide takes **Apex Digital** from a clean machine to a running, publicly
reachable deployment. Every command is written to be copy-pasteable.

---

## 1. What you are deploying

| Component | Stack | Port |
|---|---|---|
| Web frontend | React 19 + Vite (static bundle) | served by nginx |
| REST API | Node.js 22+ / Express | `5000` |
| Database | PostgreSQL 16 | `5432` |
| Cache & queues | Redis 7 | `6379` |

The API is versioned under `/api/<module>`; `/health` and `/ready` are exposed
at the root for load balancers and orchestrators, and the OpenAPI reference is
served at `/api-docs`.

---

## 2. Requirements

* Docker 24+ with the Compose plugin (`docker compose version`)
* Node.js 22 or newer if you prefer to run without containers
* 2 GB RAM and 10 GB disk for a comfortable small-production install

---

## 3. Fastest path — Docker Compose

```bash
git clone <your-repo-url> apex
cd apex

cp .env.example .env
# Edit .env — see the configuration table below. At minimum set:
#   JWT_SECRET, DATABASE_URL, CORS_ORIGIN

docker compose up -d
docker compose ps
```

The API answers once the logs show `listening on port 5000`:

```bash
curl -fsS http://localhost:5000/health
```

### Seeding your first administrator

```bash
docker compose exec backend node scripts/production-seed.js
```

The seed prints the administrator address it created. Change the password
immediately, then delete the seed credentials from any shared notes.

---

## 4. Configuration

Copy `.env.example` to `.env`. The values that must change before going live:

| Variable | Required | Purpose |
|---|---|---|
| `NODE_ENV` | yes | `production` in every deployed environment |
| `PORT` | no | API port, default `5000` |
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `JWT_SECRET` | yes | Signing key for access tokens. Use 32+ random bytes |
| `JWT_REFRESH_SECRET` | yes | Separate key for refresh tokens |
| `CORS_ORIGIN` | yes | Comma-separated list of allowed browser origins |
| `REDIS_URL` | no | Falls back to an in-process store when unreachable |
| `MAIL_*` | no | Required only for password-reset and verification email |
| `ENABLE_DEMO_SEED` | no | Must stay `false` in production |

Generate secrets with:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
```

---

## 5. Running without containers

```bash
# API
cd backend
npm ci
cp .env.example .env
npm start

# Frontend
cd ../frontend
npm ci
npm run dev          # development
npm run build        # production bundle in dist/
```

The production bundle is plain static files. Serve it with any web server and
make sure unknown paths fall back to `index.html`, otherwise client-side routes
such as `/pricing` will return 404. The bundled `nginx.conf` and the
`deploy.yml` GitHub Actions workflow both handle this.

---

## 6. Publishing the live demo to GitHub Pages

The repository includes a `deploy.yml` workflow that builds the frontend and
publishes it to GitHub Pages.

1. Create an empty GitHub repository and push this project to it.
2. In **Settings → Pages**, set *Source* to **GitHub Actions**.
3. Push to `main`.

The workflow builds with `VITE_BASE_PATH=/<repository-name>/` and publishes.
When you later attach a custom domain, change that value to `/`.

Note that GitHub Pages hosts the **frontend only** — it is a static host and
cannot run the API. Use the Docker steps above for the full stack.

---

## 7. Verifying a deployment

```bash
curl -fsS https://your-domain/api/health
curl -fsS https://your-domain/ready
curl -fsSI https://your-domain/pricing     # must return 200, not 404
```

---

## 8. Backups

`scripts/backup.js` writes a compressed PostgreSQL dump to `backups/`. Run it
on a schedule and copy the result somewhere the host cannot delete.

```bash
docker compose exec backend node scripts/backup.js
```

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| API exits at startup | `JWT_SECRET` unset or shorter than 32 characters | Set a generated secret |
| Every request returns 429 | `RATE_LIMIT_MAX` too low for your traffic, or a proxy is not setting `X-Forwarded-For` | Raise the limit; set `trust proxy` |
| CORS errors in the browser | `CORS_ORIGIN` does not match the page origin exactly, including scheme | Use the full origin, no trailing slash |
| Frontend loads but all data fails | `VITE_API_URL` points at the wrong host | Rebuild with the correct URL |
| Deep links 404 | Web server is not falling back to `index.html` | Add the `try_files $uri /index.html` rule |
| `SequelizeConnectionError` | Database unreachable or schema not created | Check `DATABASE_URL`, then run `npm run migrate` |
| Emails never arrive | SMTP not configured | Fill the `MAIL_*` variables |

---

## 10. Support

* Documentation: the rest of this `docs/` directory
* Email: malikusmangoraya786@gmail.com
