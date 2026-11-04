# Expanded Technology Catalog and Agent Guidance

## Goal

Extend the existing project-generation technology catalog to include the
frameworks, admin platforms, hosting/deployment providers, testing tools,
authentication patterns, and advanced engineering topics in the user's
reference. Make these choices available to the generation agent as curated,
compatible selection metadata and contextual guidance without claiming that
catalog inclusion implements the selected technology.

## User intent and constraints

- The catalog and agent guidance should cover every technology and topic named
  in the supplied reference.
- The user selected catalog/guidance only; native scaffolds or deployment
  automation for every listed option are not in scope.
- Retain the existing backend-stack selection and Node.js/Express default.
- Distinguish selection/recommendation from implementation in plans, dry runs,
  and generation reports.
- Avoid treating changing vendor pricing, free-tier limits, availability, or
  acceptable-use rules as fixed facts.

## Catalog coverage

The canonical catalog remains `registry/technology-stack-catalog.json`. It is
expanded with typed capability groups so unlike concepts cannot be confused:

### Application frameworks

- Full-stack/frontend frameworks: the existing React + Vite baseline, Next.js,
  SvelteKit, Nuxt, Astro, TanStack Start, React Router Framework, Qwik City,
  and SolidStart.
- Backend frameworks include all existing options plus Hono and AdonisJS for
  JavaScript/TypeScript; API Platform for PHP; Litestar for Python; Axum and
  Actix Web for Rust; Chi for Go; and Phoenix for Elixir. Rust, Elixir, and
  Kotlin are added as backend language families where named by the reference;
  Micronaut is associated with both Java and Kotlin. Existing Symfony,
  Quarkus, Micronaut, NestJS, Fastify, and other catalog entries remain.
- Framework metadata identifies its language/runtime, role, compatible
  companion technologies where known, and current generator capability.

### Admin and content platforms

Include Payload CMS, Strapi, Directus, Appsmith, and Budibase. Record their
role (CMS, database-backed admin, or internal-tools platform) and known
integration constraints, such as Payload's Next.js relationship.

### Hosting and deployment

- Frontend: Cloudflare Pages, Netlify, Vercel, and GitHub Pages.
- Backend/API: Cloudflare Workers, Render, Vercel Functions, Firebase, and
  Docker-based self-hosting.
- Database/backend services: Supabase, MongoDB Atlas, and Firebase.
- Automation/version control: GitHub and GitHub Actions.

Provider records contain a provider name, capability category, relevant
official documentation or pricing URL when available, and compatibility
metadata. They do not promise current free-plan availability or encode
time-sensitive quotas/prices. The agent must direct users to verify current
provider terms before choosing a real production deployment.

### Testing and quality tools

Include the reference's tools by purpose and runtime compatibility:

- Frontend: Vitest, React Testing Library, Jest, Playwright, Cypress, and
  Lighthouse.
- API/backend: Bruno, Postman, Supertest, pytest, PHPUnit, JUnit, xUnit, and
  curl.
- Performance/security/dependency checks: k6, OWASP ZAP, `npm audit`,
  `composer audit`, `pip-audit`, GitHub Dependabot, and Chrome DevTools.
- CI: GitHub Actions, with pipeline stages such as lint, tests, build, and
  deployment gates represented as guidance rather than executable workflows.

### Authentication and engineering guidance

Keep authentication concepts distinct: browser cookies are a transport
mechanism; sessions are server-side login state; JWT is a token format; OAuth
2.0 is delegated authorization; and OIDC adds authentication/identity.
Guidance covers cookie `HttpOnly`, `Secure`, `SameSite=Strict|Lax|None`,
`Max-Age`, `Expires`, `Path`, and `Domain`; cross-site `None` requires `Secure`.
It covers Express session access/save/regenerate/destroy, persistent stores,
expiry, rotation, concurrent sessions, revocation, logout invalidation, and
the warning against production `MemoryStore`. PHP references include
`session_start`, `$_SESSION`, `session_regenerate_id`, `session_unset`,
`session_destroy`, `setcookie`, `session_name`, and `session_status`.

OAuth/OIDC guidance distinguishes `client_id`, exact `redirect_uri`,
authorization-code flow, scopes, `state`, PKCE challenge/verifier, access and
refresh tokens, OIDC ID tokens and `nonce`, expiry, revocation, and validation
of issuer/audience/signature. It includes Auth.js, Better Auth, Passport.js,
Laravel Socialite, Spring Security OAuth2 Client, ASP.NET Core OIDC handlers,
and Django `allauth` as ecosystem references. Cookie-authenticated cross-origin
requests explain credentials mode, exact CORS origins (never `*` with
credentials), `SameSite`, and CSRF protection. These are guidance, not claims
that the libraries or flows have been wired into the generator.

The agent's engineering checklist also covers password security, RBAC/ABAC,
CSRF/XSS, SQL injection, input validation, rate limiting, uploads, email,
webhooks, queues, caching, transactions, search, real-time transports,
observability, i18n/timezones/currency, accessibility, SEO, backup/restore,
architecture, and scalability. Guidance must retain safe defaults:
parameterized database access, server-boundary validation/authorization,
least-privilege CORS, CSRF defenses for cookie-authenticated flows, secret
redaction, and explicit error handling.

## Selection and compatibility model

Keep `backend_stack` stable, including its current language, framework,
database, ORM, API, architecture, auth, and operational option fields. Add an
optional namespaced `technology_choices` object with these optional fields:
`frontend_framework`, `admin_platform`, `frontend_host`, `backend_host`,
`database_host`, `source_control_provider`, `testing_tools` (list),
`quality_tools` (list), `ci_provider`, and `authentication_profile`.
List-valued tool choices are validated as catalog IDs, deduplicated while
retaining catalog order, and normalized deterministically.

Each catalog option declares a capability category and known compatibility
constraints, along with one capability state: `catalog_only_not_generated`,
`generated`, or `verified`. Validation rejects unknown IDs and combinations explicitly
marked incompatible before a generation run is created. Auto mode recommends
only combinations explicitly marked compatible; manual selections whose
compatibility is unknown remain selectable but carry an `unverified`
compatibility status and a clear warning. The agent must never silently treat
unknown compatibility as supported. Manual values override only their own
dimensions. Missing optional dimensions remain recommendable.

Existing API paths and response fields remain compatible. Catalog API responses
are additive. Generation, streaming, and dry-run accept the optional choices
object. The resolved choices are carried through planning and appear in
generation reports alongside the existing `backend_stack` result.

## Capability reporting and non-goals

Catalog inclusion does not create source code, integrations, CI workflows,
hosting configuration, accounts, or deployments. Report capability per
selected option as supported/generated only when an existing generation path
actually produces and verifies that artifact. Otherwise use a clear
catalog-only/not-generated status. In particular, do not claim native
scaffolding for newly cataloged frameworks or providers.

Out of scope:

- Implementing every framework's project scaffold or translating projects
  between runtimes.
- Creating/configuring hosting accounts, provider resources, CI workflows, or
  deploying generated projects.
- Verifying or promising third-party free plans, pricing, quotas, uptime, or
  current feature availability.
- Implementing every authentication/security feature merely because it is
  listed as guidance.
- Changing LumicorePro's own runtime stack.

## User experience

The existing Auto/manual selector remains recognizable. Selecting Auto clears
manual overrides; selecting Manual exposes controls for the optional groups.
Manual choices are
grouped into progressive-disclosure panels for application framework,
backend, admin/CMS, hosting, testing/quality, and authentication profile.
Options are filtered when compatibility metadata is available. Loading and
catalog errors remain explicit. Selection labels and result/report notices
differentiate recommendations, catalog-only selections, generated artifacts,
and verified artifacts. `generated` is used only when the output contains that
artifact, and `verified` only after an applicable check confirms it.

Provider plan/limit facts are not presented as static guarantees. Official
provider links may be shown for independent verification; the interface should
not imply that a listed provider is currently free or production-suitable.

## Security and failure handling

- Validate all new selection fields at the FastAPI trust boundary before run
  creation, credit reservation, or background task scheduling.
- Validate and forward request bodies through the Express proxy without
  accepting unknown catalog IDs.
- Never return a success-shaped result for incompatible or unavailable catalog
  data.
- Preserve existing error envelope/status conventions and avoid exposing stack
  traces or secrets.
- Treat provider links and catalog descriptions as data, not executable
  content.

## Acceptance criteria

1. The catalog contains every framework, platform, hosting/provider, testing
   tool, auth reference, and engineering topic named in the supplied text, in
   correctly typed categories.
2. Catalog validation checks unique IDs, required categories, known references,
   and declared compatibility relationships.
3. Existing `backend_stack` clients and the default Node.js/Express resolution
   continue to work without supplying `technology_choices`.
4. Auto and manual choices resolve deterministically; invalid IDs and
   incompatible selections fail before any generation work starts.
5. UI/API/planner/dry-run/report carry new selections consistently and state
   when each selected capability is catalog-only versus generated/verified.
6. No provider quota, price, free-plan, or production-availability claim is
   presented as a durable guarantee.
7. Unit and integration tests cover catalog structure, compatibility,
   malformed input, Auto/manual selection, API round-trips, report honesty, and
   backward compatibility.
8. Relevant frontend lint/build and focused AI-agent/Express/frontend tests
   pass. Existing unrelated full-suite failures are reported, not masked.

## Verification plan

- Unit-test catalog schema integrity, duplicate IDs, compatibility edges, and
  all required entries from the reference.
- Test resolver behavior for manual partial choices and Auto recommendations.
- Assert API validation occurs before run/credit/task side effects for invalid
  choices, including generation, stream, and dry-run routes.
- Test Express forwarding and UI loading/error/selection/report behavior.
- Run targeted Python, Express, and frontend suites, changed-file lint, build,
  and bundle budget checks.
- Inspect final diff for unrelated changes and confirm `git diff --check`.
