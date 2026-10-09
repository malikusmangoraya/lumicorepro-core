# Security Options — what to enable per product before publish

Created: 2026-10-10

This is a checklist + short note file. Use it when preparing any of the eleven products for
production. Each item is a security option that can be enabled, verified, or hardened. Not every
option is mandatory for every product; mark the ones that apply.

## 1. Environment and secrets
- [ ] `.env` is local only and not shipped in public assets, source control, or build output
- [ ] `.env.example` lists every required key with placeholder values
- [ ] No real keys, passwords, or tokens are committed
- [ ] Platform secrets live in the hosting/panel secrets store when available, not in repo files
- [ ] Per-product secrets are rotated when staff or providers change

## 2. Authentication and sessions
- [ ] JWT access tokens are short-lived
- [ ] Refresh tokens are longer-lived but still rotated or scoped
- [ ] Password hashing is strong (current target is bcrypt cost 12 or equivalent)
- [ ] Login/signup/reset flows validate inputs on both frontend and backend
- [ ] Account takeover paths (reset, email change, token replay) are reviewed per product
- [ ] Admin/console routes are protected and not publicly reachable

## 3. CORS and origin policy
- [ ] CORS is restricted to expected origins
- [ ] Wildcard CORS is not used for authenticated endpoints
- [ ] Cookies are scoped to the correct origin and path
- [ ] Backend trusts only expected frontend origins for mutations

## 4. Rate limiting and abuse control
- [ ] Auth endpoints are rate limited
- [ ] Payment/webhook endpoints are rate limited or protected against repeated abuse
- [ ] AI-agent or heavy compute endpoints are capped when present
- [ ] Failed login or repeated invalid submission paths are limited

## 5. Input validation and injection safety
- [ ] All user inputs are validated before use
- [ ] SQL queries are parameterized, not built from raw strings
- [ ] Search, filters, and sorting inputs are sanitized where needed
- [ ] File paths and identifiers are not taken directly from user input without checks

## 6. File uploads
- [ ] Upload size limits are enforced
- [ ] Allowed MIME types are restricted
- [ ] Uploaded filenames are normalized or rewritten
- [ ] Uploads are stored outside executable paths where possible
- [ ] Malicious file content is not trusted after upload

## 7. Payment and webhooks
- [ ] Webhook signatures are verified before processing
- [ ] Webhook handlers are idempotent where needed
- [ ] Webhook failures are logged and not silently swallowed
- [ ] Payment state changes go through backend-controlled flows
- [ ] No card or raw payment data is collected in the browser frontend

## 8. Errors and logging
- [ ] Stack traces are not exposed to users in production
- [ ] Generic, user-safe error messages are shown for failures
- [ ] Detailed errors are logged server-side only
- [ ] Logs do not contain secrets, tokens, or full payment payloads unless necessary

## 9. Cookie and client-side privacy
- [ ] Cookie consent is presented where required
- [ ] Cookie names and scopes are product-specific
- [ ] Tracking/consent model matches the product’s region and privacy posture
- [ ] Local-only preferences are kept in localStorage only when appropriate

## 10. Transport and hosting
- [ ] Production uses HTTPS
- [ ] Service worker and asset caching strategy does not cache private responses improperly
- [ ] Public static assets do not leak env vars or internal paths
- [ ] Debug/development endpoints are not exposed publicly

## 11. Product-specific notes
Use this section when a product needs a security note that differs from the defaults above.

### apex
- Payment webhooks and configurable gateway mode are already present.
- Confirm CORS and webhook signature settings before publish.

### aurelia-estates
- Confirm cookie scopes, rate limits, and upload rules if file uploads are used.

### aurum-fitness
- Confirm auth rate limits and admin route protection if administrative features are present.

### claimflow-ai
- AI/claims processing endpoints should have usage limits and input validation review.

### flowpilot
- Confirm webhook/provider config and secrets handling before publish.

### meridian-capital
- Financial product posture: review CORS, rate limits, and admin/auth exposure carefully.

### nuage-events
- Review upload, seat/booking, and webhook flows if those features are enabled.

### prestige-studio
- Review portfolio/media uploads and any public submission paths.

### resupro
- Review auth and any resume/file handling paths if present.

### saffron-voyage
- Review booking/payment and travel-data handling paths if enabled.

### studio-lumen
- Review media/gallery upload and public-facing submission paths if present.

## 12. Optional hardening
These are optional improvements, not baseline requirements.
- [ ] Security headers review (for example, HSTS, X-Content-Type-Options, Content-Security-Policy where applicable)
- [ ] CSRF protection review on state-changing endpoints
- [ ] Dependency audit before publish
- [ ] Backend dependency audit and update review
- [ ] Pen-test or internal security review for high-risk products

## Final note
“Security option” here means a setting, review, or guard that can be enabled or verified. It does not
mean every product must enable every item before it can run locally. Decide per product which items
are required for its publish target.
