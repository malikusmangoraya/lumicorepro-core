# Security Policy

We take reports seriously and respond to every one.

## Supported versions

| Version | Supported |
|---|---|
| 1.x (current) | yes |
| < 1.0 | no |

## Reporting a vulnerability

Email **malikusmangoraya786@gmail.com** with:

* what the issue is and which component is affected,
* steps to reproduce,
* the impact you believe it has.

Please do not open a public issue for a security problem. We will acknowledge
within **2 business days** and aim to ship a fix within **14 days**. We will
credit you in the release notes if you would like that.

## What this software already does

These are implemented in the shipped code, not aspirations:

* **Password storage** — bcrypt with a cost factor of 12; passwords are never
  logged or returned by any endpoint.
* **Sessions** — short-lived access tokens plus rotating refresh tokens, both
  signed with separate secrets. Refresh tokens are revocable server-side.
* **Rate limiting** — global, plus dedicated tighter limits on authentication
  and write-heavy endpoints.
* **Transport & headers** — Helmet sets HSTS, `X-Content-Type-Options`,
  `X-Frame-Options`, a restrictive CSP and `Referrer-Policy`.
* **Input validation** — every request body is schema-validated before a
  handler sees it; unknown fields are rejected.
* **Authorisation** — role-based access control on every non-public route.
* **Secrets** — no credentials are committed. Configuration is read from the
  environment and every example file contains placeholders only.
* **Uploads** — size and type restricted, and served from a separate origin
  path so a malicious upload cannot execute in the app's context.
* **Audit trail** — privileged actions are written to an append-only log.

## Running it securely

1. Set `NODE_ENV=production`.
2. Generate fresh `JWT_SECRET` and `JWT_REFRESH_SECRET` values. Never reuse an
   example value.
3. Leave `ENABLE_DEMO_SEED=false`. The demo accounts share a known password.
4. Terminate TLS in front of the app and set `CORS_ORIGIN` to your real
   origins.
5. Keep PostgreSQL and Redis off the public network.
6. Apply dependency updates regularly — `npm audit` is wired into CI.

## Default credentials

There are none. A fresh install has no account until you run the seed script
and change the generated password.
