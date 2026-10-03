# Security Policy

LumicorePro Core — React 19 + Vite frontend, Express + PostgreSQL + Redis backend,
Python FastAPI AI agent.

---

## Supported versions

This project is developed on a single long-lived branch (`master`) and released as
annotated `v*.*.*` tags. Security fixes are applied **only to the most recent
release series**. There is no LTS line and no back-porting to older releases.

| Version | Supported | Notes |
|---------|-----------|-------|
| Latest `v1.x` release tag | ✅ | Receives security fixes |
| `master` (unreleased head) | ✅ | Fixes land here first, then are tagged |
| Any older `v*` tag | ❌ | Upgrade to the latest release |
| Pre-release / `-rc` builds | ⚠️ | Fixes are applied at the maintainers' discretion |
| Forks and downstream distributions | ❌ | Supported by whoever distributes them |

### Supported runtime

Security fixes are validated against these minimums. Older runtimes are not tested.

| Component | Supported |
|-----------|-----------|
| Node.js (frontend build + backend) | **20.x** (CI uses 20; 18 is end-of-life and not tested) |
| Python (AI agent) | **3.11.x** |
| PostgreSQL | **16.x** (the Compose file pins `postgres:16-alpine`) |
| Redis | **7.x** |
| Docker Engine / Compose | Engine 24+, Compose **v2.20+** (the v2 plugin, not `docker-compose` v1) |
| Browsers (frontend) | Current Chrome, Edge, Firefox, Safari; `es2020` build target |

The package version in the root `package.json` is not the release version — use
`git describe --tags` (or the GitHub Releases page) to identify a release.

---

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use one of these private channels:

1. **GitHub private vulnerability reporting** — open the repository's **Security**
   tab and choose **Report a vulnerability**. This is the preferred channel: it
   keeps the discussion private and produces a tracked advisory.
2. If that is unavailable, contact the maintainers through the repository's
   organisation profile and ask for a private channel before disclosing details.

Please include, as far as you can:

* the affected component (frontend / backend / AI agent / deployment assets) and
  release tag or commit SHA;
* a description of the impact — what an attacker gains;
* reproduction steps or a proof of concept (a minimal request, script or diff is
  far more useful than a description alone);
* whether the issue is already public anywhere;
* any suggested remediation, if you have one.

**Do not include real credentials, personal data or live customer data in a
report.** Redact tokens, keys and personal records; a placeholder is enough to
demonstrate the issue.

### What to expect

| Stage | Target |
|-------|--------|
| Acknowledgement of your report | within **3 business days** |
| Initial triage and severity assessment | within **7 business days** |
| Status update | at least every **14 days** while a fix is in progress |
| Fix for Critical / High severity | target **30 days** from triage |
| Fix for Medium / Low severity | next scheduled release |
| Coordinated public disclosure | **90 days** after triage, or earlier by agreement |

These are targets from a small maintainer team, not contractual guarantees. If a
deadline slips you will be told why rather than left waiting.

We will credit reporters in the advisory and release notes unless you ask us not
to. If you would prefer to publish your own write-up, tell us and we will
coordinate the date.

### Safe harbour

We will not pursue or support legal action against anyone who:

* researches, tests or reports a vulnerability in good faith under this policy;
* does not access, modify or exfiltrate data belonging to anyone else — use your
  own account and your own test data;
* does not degrade or disrupt the service for other users (no DoS, no spam, no
  automated high-volume scanning);
* does not use social engineering, physical intrusion or third-party services
  against the maintainers;
* gives us reasonable time to fix the issue before publishing.

If you are unsure whether your testing crosses a line, ask first via the private
reporting channel. Activity that stays within this policy is authorised; we will
make that clear to any third party that asks.

---

## Scope

### In scope

* Frontend application code (`src/**`) — XSS, auth/session handling, client-side
  injection, unsafe `dangerouslySetInnerHTML`, PII leakage.
* Backend API (`backend/**`) — authentication and authorisation bypass, IDOR /
  broken object-level authorisation, SQL injection, SSRF, command injection,
  insecure file upload, secret exposure, rate-limit bypass, payment-webhook
  signature verification.
* AI agent (`ai-agent/**`) — path traversal in generated output, prompt-injection
  paths that reach the filesystem or execution, unauthenticated access to
  expensive endpoints, secret leakage through API responses.
* Deployment assets (`Dockerfile*`, `docker-compose*.yml`, `nginx/**`, `k8s/**`,
  `.github/workflows/**`) — misconfiguration that weakens production security
  (TLS, headers, exposed ports, permissive CORS, privilege escalation in images,
  CI secrets exposure, supply-chain risk in the release path).

### Out of scope

* **Automated scanner output with no demonstrated impact.** A bare `npm audit` /
  Dependabot finding is a dependency-update task, not a vulnerability report. It
  becomes in scope when you show the affected code path is reachable and what it
  achieves.
* **The committed example/template files.** `.env.example`,
  `.env.production.example`, `k8s/secret.example.yaml` and CI placeholder values
  are documentation, not credentials. (`k8s/secret.yaml` intentionally contains
  no Secret object at all; see its header.)
* Findings that require an already-compromised host, an attacker-controlled
  browser extension, physical access, or a rooted device.
* Self-XSS, clickjacking on pages with no sensitive action, tabnabbing,
  autocomplete/`autofill` attributes, and missing headers on non-production
  configurations.
* Denial of service through sheer volume, and reports produced by load testing
  without prior agreement.
* Third-party services and providers: hosting, the AI model providers
  (Gemini/OpenAI/DeepSeek/Groq/OpenRouter/Mistral/Anthropic), Stripe, PayPal and
  other payment gateways, SMTP, and GitHub. Report those to the provider.
* The `backend-library/`, `k8s/`, and generated-project trees as *deployed*
  systems — they are secondary or generated artefacts. Configuration weaknesses in
  `k8s/**` are in scope (see above).

---

## Security controls in this repository

Useful context when assessing a finding — several controls already exist, so a
report should explain why they do not apply.

* **Authentication** — JWT access/refresh with distinct secrets, both validated
  at boot and required to be ≥ 32 characters in production
  (`backend/config/database.js`, `backend/middleware/security.js`). Passwords are
  hashed with bcrypt cost 12+. Optional 2FA and OAuth (Google/GitHub).
* **Authorisation** — role-based middleware plus per-route ownership checks;
  multi-tenancy via an organisation header (`x-org-id`).
* **Headers** — Helmet on the backend; `Content-Security-Policy` (no
  `unsafe-inline`/`unsafe-eval` for scripts), HSTS, `X-Content-Type-Options`,
  `Referrer-Policy`, `Cross-Origin-Opener-Policy` and `Permissions-Policy` at the
  nginx edge. See `nginx/security-headers.conf`.
* **Rate limiting** — Redis-backed per-route limits (stricter on `/api/auth`),
  plus nginx edge zones and an in-process limiter in the AI agent.
* **Uploads** — MIME and size validation, 10 MB cap, non-guessable filenames;
  uploaded SVGs are served with `Content-Security-Policy: default-src 'none';
  sandbox` and `nosniff` to prevent stored XSS.
* **Errors** — never relay upstream/stack details to clients; structured server
  logging instead (`backend/middleware/errorHandler.js`).
* **Containers** — all images run as non-root with dropped capabilities where the
  manifest controls it; only nginx publishes host ports in production.
* **Secrets in git** — `gitleaks` runs on full history for every pull request, and
  `npm audit --audit-level=high` runs for the frontend and backend
  (`.github/workflows/ci.yml`). No secret is committed anywhere in this repository.
* **Release path** — a `v*.*.*` tag re-runs the full merge gate before any image is
  pushed, and images are always tagged with the commit SHA as well as the version.

Deployment-specific guidance lives in
[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md); operational procedures (backup
verification, rollback, AI-agent outage) live in
[docs/RUNBOOK.md](./docs/RUNBOOK.md).

### Known security gaps

Stated here rather than left for a reporter to rediscover:

1. **The AI agent has no application-level authentication in the Compose path.**
   `backend/routes/ai.routes.js` calls the agent without an `X-API-Key` header, so
   setting `AGENT_API_KEY` breaks every AI request. The agent is protected by
   network isolation instead: it publishes no host port and only `backend` can
   reach `ai-agent:8000`. Wiring the key through is a tracked, unfinished change.
2. **No off-site backup is configured.** See `docs/RUNBOOK.md` § Backup — this is
   an availability risk, not a confidentiality one.
3. **Frontend test coverage is very low** (see `AGENTS.md` § 6), so regressions in
   client-side logic — including security-relevant logic — are less likely to be
   caught by CI than in the backend.
4. **The Kubernetes manifests are a secondary, unverified target.** They are kept
   consistent with the application but have not been applied to a live cluster.
   `k8s/README.md` lists the gaps.
