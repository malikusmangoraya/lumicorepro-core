# Complete Generated Websites — Design

## Purpose

Generated websites must be complete working applications rather than a polished
frontend beside mock backend features. Each newly generated website should
include a functioning backend, persistent database, authentication and
login/signup experience, working forms, Docker setup, and owner-facing setup
documentation. Payment processing must be production-shaped when the product
accepts payments, but must not be fabricated for sites that do not sell or
charge for anything.

This design refines
[AI Website Generation Standard](../../AI_WEBSITE_GENERATION_STANDARD.md):
the current user's explicit requirement overrides its earlier
scope-first suggestion that ordinary sites may omit the backend and database.

## Defaults and boundaries

- **New generated site:** full-stack by default; Express API, PostgreSQL
  persistence with versioned migrations, account registration/login, protected
  profile route, and real form persistence. Include frontend signup/login
  journeys that call those APIs.
- **Local development and handoff:** provide a working Docker Compose stack,
  valid environment examples, startup/health checks, migration and test
  commands, and documentation explaining setup and external configuration.
- **Authentication:** securely hash passwords, validate credentials, issue
  15-minute access tokens and rotating 7-day refresh tokens, keep refresh
  tokens in HttpOnly/Secure/SameSite cookies and persist only their hashes,
  enforce authorization on the server, and return safe error messages. Use
  bcrypt cost 12 or higher. No success-shaped registration or login stubs.
- **Forms:** persist submissions through validated API endpoints. Forms that
  send email may require SMTP configuration, clearly documented as an external
  prerequisite; without it, report an actionable failure rather than claiming
  a message was sent.
- **Payments:** add the existing Stripe checkout path when the specification
  includes purchases, subscriptions, or other money collection, unless the
  user selects a different supported provider. Checkout must use server-created
  intents/sessions, verified webhook signatures, idempotent payment state
  updates, and sandbox tests. Never store raw card details. Do not include a
  checkout on a site with no payment journey.
- **Existing-site upgrade:** preserve established architecture and behavior;
  add missing capabilities only when required by the explicit update or
  product journeys. Do not silently rebuild an existing frontend-only/static
  site as a different product.
- **Static exception for new sites:** only if the user explicitly requests a
  frontend-only/static site, omit backend/database/auth/Docker and record the
  user's opt-out and resulting limitations.
- **Credentials and live verification:** generated configuration must never
  contain real secrets. Without provider/database credentials or a reachable
  deployment environment, report exactly what code and local tests passed and
  mark live integration/deployment checks as blocked or not measured.

## Generation contract

1. The planner marks new sites `fullstack` by default and preserves an explicit
   `client-static` opt-out. It records required baseline features separately
   from optional business features; industry labels must not auto-add OAuth,
   MFA, subscriptions, analytics, or payments.
2. The backend generator creates executable auth, form, and data paths using
   the existing Express/Sequelize architecture and PostgreSQL default. Define
   a user model, required domain/form models, safe validation, authorization,
   migrations, and predictable server startup.
3. The frontend output includes usable login/signup forms, field validation,
   loading/error/success feedback, and API wiring. Protected UI reflects
   server-side auth and has usable unauthenticated behavior.
4. When payment is in scope, scaffold the existing provider integration
   without mock payment success. Store authoritative order/payment state in
   the database only after verified server-side provider events.
5. Docker Compose brings up the frontend, backend, and PostgreSQL with
   health/readiness dependencies and migrations. It must require secrets
   through environment configuration and never ship a working insecure
   default credential.
6. Generated docs describe architecture, environment setup, database
   migrations, auth/API behavior, forms, optional integrations, Docker, tests,
   deployment requirements, and known limitations. Documentation must match
   generated files and commands.
7. A generated-project completeness gate validates required artifacts and
   checks. Required-stack failures block a "complete" or release-ready result;
   a diagnostic archive may still be provided but must be labeled incomplete.
8. Reports distinguish scaffolded, locally verified, externally configured,
   release-ready, and deployed states. External secrets, sandbox accounts, or
   a live host are never assumed to exist.

## Acceptance criteria

- A new default project contains a working backend, PostgreSQL schema and
  repeatable migrations, signup/login/profile endpoints, a persistent form
  endpoint/model, frontend auth/forms, Docker Compose, setup/API documentation,
  and tests for successful and failed paths.
- Registration stores a password hash (not the password); duplicate/invalid
  registration and invalid login fail safely; protected profile access
  rejects missing/invalid credentials; logout/revocation invalidates refresh
  sessions and refresh tokens rotate.
- Form validation runs server-side, valid submissions persist, and DB errors
  do not become success responses.
- Docker configuration has no usable placeholder secret/password and services
  wait for database readiness and apply migrations before serving requests.
- A payment project contains the provider integration and durable payment
  state, rejects invalid webhook signatures, deduplicates event processing,
  and passes provider sandbox tests when credentials are available. Missing
  credentials block external/sandbox verification and are reported as such.
- A non-payment project has no unrequested checkout or payment provider
  secret requirement.
- A new site explicitly requested as static can be generated without backend,
  DB, auth, or Docker and documents that scope choice.
- Existing-site updates retain their architecture and change only the required
  surfaces.
- Tests, lint, builds, completeness checks, and docs validation report the real
  outcome; unmet required criteria block complete/release-ready status.

## Out of scope

- Requiring an actual production payment charge or live deployment during
  generation; those require owner credentials and an explicit deployment
  action.
- Mandating Redis, queues, analytics, OAuth, MFA, subscriptions, Kubernetes,
  or a cloud provider for every site.
- Replacing existing project modes, templates, or supported database choices
  wholesale; the implementation should reuse current generator conventions
  and migrate only the default contract needed to make output work.
