# AI Website Generation Standard

**Audience:** LumicorePro's website-generation agent and the people reviewing
its output.
**Applies to:** new websites, generated applications, and upgrades to existing
websites.
**Purpose:** turn a request into a coherent, distinctive, usable, secure, and
verifiably working deliverable without adding infrastructure or features the
request does not need.

This is the agent's top-level delivery contract. Use it with the detailed
[Website Build Playbook](./WEBSITE_BUILD_PLAYBOOK.md) and
[Unique Project Playbook](./UNIQUE_PROJECT_PLAYBOOK.md). This standard owns
scope selection, priorities, and truthful completion claims; those playbooks
provide deeper implementation references. Where older prompt text or a
checklist conflicts with this standard, follow the user's request, the
existing project's architecture, and this standard—in that order.

## 1. Non-negotiable principles

1. **Build the requested product, not a generic showcase.** Understand the
   audience, primary user journey, business outcome, content, and constraints
   before choosing features or design.
2. **Default new websites to complete full-stack delivery.** Include a
   functioning backend, persistent database, authentication with signup/login,
   validated forms, Docker setup, tests, and accurate setup documentation.
   Only an explicit static-only request opts out. Payments are required when
   the product accepts money; do not invent checkout for a site that does not.
3. **Preserve existing behavior on upgrades.** Inspect the current code,
   instructions, tests, dependencies, routes, and deployment setup first.
   Make the smallest complete change and retain the established architecture.
4. **Design before implementation.** Record the information architecture,
   visual direction, brand decisions, responsive behavior, and essential
   states before building the main interface.
5. **Complete working journeys.** Visible controls must work; forms must
   validate and report outcomes; async surfaces must explain loading, empty,
   success, and error states. Do not disguise missing integrations with
   success-shaped mocks.
6. **Verify the delivered artifact.** Run the relevant checks and report
   evidence, failures, and unmeasured items. Never equate code generation
   with verification, release readiness, or deployment.
7. **Be original and lawful.** Use references to understand attributes such
   as hierarchy, typography, composition, and motion—not to copy a site's
   text, identity, source, or distinctive artwork. Use assets with appropriate
   rights and attribution.

## 2. Intake and project mode

Before work, extract the following from the request and repository:

- Product purpose, audience/personas, industry, and primary user journey.
- Required routes, features, content, integrations, and measurable outcomes.
- Existing brand assets, design system, code conventions, and user changes.
- Target devices, browsers, locales, accessibility needs, hosting, and
  operational constraints.
- What must remain unchanged, what is explicitly out of scope, and what
  cannot be verified in the current environment.

Select one project mode and record the reason. New websites use full-stack by
default; website type alone does not remove backend, database, auth, forms, or
Docker:

| Mode | Use when | Include |
|---|---|---|
| Full-stack website/application (default) | Any new generated website unless the user explicitly opts out | Frontend, backend, PostgreSQL persistence/migrations, signup/login, persisted validated forms, Docker, tests, and setup docs |
| Static/content site (explicit opt-out) | The user explicitly requests frontend-only/static output | Frontend, accessible interactions, SEO, static deploy path, and a recorded explanation that backend, database, authentication, persisted forms, and Docker were excluded |
| Upgrade | A working codebase already exists | Requested delta, compatibility review, focused tests, and regression checks; retain its established stack |

Do not infer payments, subscriptions, admin dashboards, multi-tenancy, or
analytics merely from an industry label. Include checkout only when the product
accepts money. If a material requirement is genuinely ambiguous and cannot be
resolved from the request or project, identify the assumption before committing
to an irreversible design. Do not invent credentials, live services, legal
claims, or real business facts.

## 3. Brand and visual design

Create an intentional design system instead of applying a preset indiscriminately:

- Define brand personality, audience fit, positioning, and a short visual
  rationale. For upgrades, preserve recognizable brand decisions unless asked
  to change them.
- Choose a restrained palette with semantic tokens, readable contrast, and
  deliberate light/dark behavior where themes are in scope.
- Establish a legible type scale and a small, compatible font set. Avoid
  loading multiple copies or blocking first paint on remote fonts.
- Design an original logo/mark that fits the brand and works at small sizes,
  in monochrome, and on light/dark surfaces. Do not use an arbitrary gradient
  wordmark as a substitute for brand identity.
- Use high-quality, relevant imagery with documented licensing/attribution
  where required. Optimize dimensions and format, provide useful alternative
  text, and lazy-load non-critical images. Do not ship broken links,
  misleading stock, fabricated product imagery, or placeholder assets as if
  they were real.
- Give each project a recognizable visual signature through a few deliberate
  decisions—such as composition, typography, imagery treatment, or section
  rhythm—rather than a pile of effects or a copied competitor layout.
- Write credible, specific content for the actual product and audience.
  Remove lorem ipsum, generic filler, unsupported claims, and dead-end CTAs.

Use the [Unique Project Playbook](./UNIQUE_PROJECT_PLAYBOOK.md) for the
manifest, identity, design lint, visual scoring, and reference-analysis detail.

## 4. UX, responsive behavior, accessibility, and motion

- Map requested routes and user journeys before building. Navigation labels,
  active states, back behavior, and mobile navigation must be predictable.
- Use semantic landmarks, heading hierarchy, associated form labels, visible
  focus, keyboard operation, useful error messages, and accessible names for
  icon-only controls. Target WCAG 2.2 AA; report any known exceptions.
- Treat mobile as a designed layout, not a compressed desktop view. Check
  narrow phones through wide desktop, content wrapping, touch targets, menus,
  tables, and forms. Avoid horizontal overflow and hidden primary actions.
- Provide loading, empty, success, failure, disabled, and retry states where
  the feature needs them. Preserve user input after recoverable failures.
- Motion must clarify state, hierarchy, or brand character. Keep it short,
  purposeful, and non-blocking; prefer transform/opacity. Respect
  `prefers-reduced-motion`, avoid scroll-jacking and flashing, and provide a
  static/mobile fallback for canvas or 3D effects.
- Do not use dark mode, a sidebar dashboard, animation, or 3D merely because
  a template or prompt lists it as an available option.

## 5. Frontend implementation

- Follow the repository's framework, versions, folder structure, components,
  tokens, lint rules, and state-management conventions. Do not introduce a
  second architecture for an existing feature.
- Keep components focused and reusable where that improves clarity; avoid
  needless abstractions and oversized single-file pages.
- Use URL state for shareable navigation/filter state, local state for local
  interactions, and the existing server-state solution for remote data.
- Validate forms at the user interface for usability and again at the trusted
  server boundary when a backend exists.
- Handle network failures explicitly. Never expose stack traces, credentials,
  or internal service details to users.
- Use route-level lazy loading and defer heavy libraries/assets when the
  project's build setup supports it and the change benefits real users.
- Keep metadata, titles, canonical URLs, social previews, structured data,
  and sitemap/robots behavior appropriate to the actual site.

### Default account and contact journeys

Unless the user explicitly chooses static-only output, generated full-stack
websites include database-backed signup, login, and a validated contact form.
The generated frontend must call the generated API; it must never show a
successful submission before the server confirms it.

- Register/login return a short-lived access token; the rotating refresh token
  is stored only as a hash on the server and travels in an HttpOnly cookie.
- The frontend API client sends cookies, refreshes access tokens once after an
  eligible `401`, and avoids retry loops on authentication endpoints.
- Generated auth and contact pages expose associated labels, inline validation,
  pending/disabled controls, and accessible error and success announcements.
- Preserve an existing contact page's design where possible while replacing
  demo-only submission behavior with the persisted contact API.
- PostgreSQL migrations are the source of truth for generated database state.
  Never report auth or form functionality complete when an API/database path
  is missing, unwired, or only simulated.

## 6. Backend, data, and integrations — only when in scope

When server-side behavior is needed:

- Define API boundaries, request/response shapes, validation, authorization,
  safe error codes/messages, and rate limits appropriate to the endpoint.
- Enforce authentication and authorization on the server for every protected
  operation. Client-side hiding is not access control.
- Validate and normalize untrusted input; use parameterized queries or the
  established ORM. Prevent injection, XSS, CSRF, SSRF, insecure direct object
  access, and unsafe file handling as applicable.
- Keep secrets in environment configuration, commit only safe examples, and
  fail clearly when required configuration is missing. Never embed secrets in
  frontend bundles, prompts, screenshots, logs, or generated documentation.
- For a generated full-stack default, use persistent PostgreSQL storage; add
  other databases only when the existing project or request requires them.
  Include Docker Compose for the frontend, backend, and database, with health
  checks and migration-driven startup. Define schema constraints, ownership,
  indexes for real query patterns, migrations, seed strategy, retention and
  deletion behavior, backups, and restore expectations.
- Make external integrations explicit about sandbox/live mode, required
  configuration, failure states, timeouts, retries, and idempotency where
  relevant. A mock is acceptable only when clearly labeled as a demo/test
  mode and never represented as a completed real transaction.
- Generate payments only when the spec explicitly requires accepting money.
  For Stripe Checkout, use server-configured Price IDs, authenticated checkout
  session creation, persisted orders, raw-body signature verification,
  idempotent persisted webhook events, and an authenticated order-status
  endpoint. Never accept an authoritative amount from the browser or mark an
  order paid from a redirect/client response. Keep provider credentials blank
  in examples and identify sandbox/live setup as external configuration.
- Include local setup, Compose, migration, test/build, API journey, environment,
  conditional payment, and external-setup instructions in generated docs.

## 7. CI/CD, deployment, and operations — scope appropriately

- For a static prototype or local-only deliverable, document its actual run
  and build commands; do not fabricate a deployment pipeline.
- Add CI when the project has a repository/team workflow or the user requests
  it. At minimum, run the relevant install, lint, test, and build checks.
- Add containers, infrastructure-as-code, deployment workflows, monitoring,
  backups, and rollback guidance when the target environment or product needs
  them. Docker Compose remains part of the full-stack default. Keep
  environment-specific values configurable and secrets out of committed files.
- Document supported runtime versions, setup, environment variables, data
  migrations, test commands, build commands, deployment prerequisites, and
  known limitations. Do not claim a provider integration or deployment works
  unless it was actually exercised.

## 8. Verification and release claims

Choose checks based on changed surfaces. Prefer the project's existing
commands and tests; add focused tests for new behavior and failure paths.

| Surface | Minimum relevant evidence |
|---|---|
| UI/layout | Production build; route and interaction checks; responsive and keyboard review |
| Forms/API | Valid, invalid, unauthenticated, unauthorized, and service-failure paths as applicable |
| Database | Migration/schema validation and tests for constraints/queries changed |
| Auth/payment | Server-side authorization probes; sandbox end-to-end checks for payment changes |
| Performance/assets | Bundle check or measured browser metrics when configured; no invented Lighthouse score |
| Deployment | Confirmed artifact/configuration, then a real deployment and live critical-path check if deployment is claimed |
| Upgrade | Focused tests plus relevant regression checks for affected dependencies/routes/features |

Use these statuses precisely:

- **Generated:** files were produced; quality checks may remain incomplete.
- **Verified:** the stated commands/checks ran and passed; list the actual
  commands and scope.
- **Release-ready:** required release gates for the target have passed; say
  what was not measured or remains conditional.
- **Deployed:** a real environment accepted the release and the live URL and
  critical path were checked.

A failed gate remains a failure even if a diagnostic ZIP or preview exists.
Bounded self-healing may retry actionable failures, but must stop at a
reasonable limit, retain the original evidence, and never convert an
unresolved failure into a pass. Distinguish **failed**, **blocked**,
**skipped**, and **not measured**.

Before deployment, run output guardrails and a deterministic artifact
completeness check. A full-stack release requires auth/contact journeys,
backend and migrations, Docker Compose, and setup documentation. A static
opt-out is checked only against its declared frontend scope. Payment artifacts
are gated only when the user explicitly requests payment features. A ZIP may
still be produced for diagnosis, but must be labelled `diagnostic_incomplete`
and cannot enable deployment.

## 9. Final handoff

Report, in plain language:

1. What changed and which user journeys/features are complete.
2. Files or architecture added, and any assumptions that affect behavior.
3. Checks actually run and their exact outcomes.
4. Generated/verified/release-ready/deployed status—do not combine them.
5. Remaining failures, skipped checks, unmeasured items, and external setup
   the owner must provide.

## Generation checklist

- [ ] Request, project mode, user journeys, constraints, and existing changes reviewed.
- [ ] Stack and infrastructure justified by the requirements.
- [ ] Design direction and content fit the brand and audience.
- [ ] Routes and controls work; responsive, keyboard, and reduced-motion behavior checked.
- [ ] Loading/empty/error/success states and validation are present where needed.
- [ ] Server-side security, data handling, integrations, and secrets are handled where in scope.
- [ ] Relevant tests, lint, build, and browser checks ran; evidence is recorded.
- [ ] Documentation matches the actual setup and deployment state.
- [ ] Final status and limitations are truthful.
