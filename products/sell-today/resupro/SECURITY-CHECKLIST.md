# Security Checklist — resupro

Prepared: 2026-09-13

Built into this codebase by default (verified by the generation pipeline):

- [x] Express `helmet` middleware — security headers (CSP, HSTS, X-Frame-Options)
- [x] Content-Security-Policy header configured in production (helmet CSP)
- [x] HTTPS enforced in production (HSTS via helmet; Nginx TLS config generated)
- [x] Passwords hashed with bcrypt (12+ rounds)
- [x] JWT access tokens (15 min) + refresh tokens (7 day) with rotation
- [x] Rate limiting on auth and AI endpoints (express-rate-limit)
- [x] Parameterized queries / ORM — SQL injection blocked by design (Sequelize)
- [x] Input validation on every route (express-validator / Pydantic)
- [x] CORS whitelist restricted to configured origins
- [x] Upload validation — MIME type and size limits enforced
- [x] .env only for secrets; .env.example committed, real .env gitignored
- [x] Generator-side static gate: eval/exec/shell/child_process rejected
- [x] No stack traces leaked to clients — generic 500 responses

Must review before launch (requires your environment/secret decisions):

- [ ] Run `npm audit` (or `pip-audit`) in `/frontend` and `/backend` after install; update vulnerable ranges
- [ ] Pin production dependencies and enable Dependabot/Renovate
- [ ] Rotate all published secrets before first deploy
- [ ] Add Web Application Firewall (WAF) rules in front of the origin once domain is live
- [ ] Enable per-route CSRF protection for cookie-authenticated mutation endpoints
- [ ] Ship a signed Subresource-Integrity (SRI) hash for external CDN scripts

> This checklist is machine-generated. A penetration test and legal review are recommended before handling sensitive user data.
