# Backend Stack Catalog and Agent Selection Design

## Goal

Let a user choose the backend technology for a generated project, or use an
automatic recommendation, and make a curated catalog of backend languages,
frameworks, databases, and architecture methods available to the agent.
This describes the generated project's stack; it does not change LumicorePro's
own backend.

## Approved scope

- Add one canonical `registry/technology-stack-catalog.json` covering Node.js,
  Python, PHP, Java, Go, C#/.NET, and Ruby.
- Associate each language with compatible frameworks and ORMs:
  Express/NestJS/Fastify; FastAPI/Django/Flask; Laravel/Symfony/Slim;
  Spring Boot/Quarkus/Micronaut; Gin/Echo/Fiber; ASP.NET Core; and
  Rails/Sinatra, respectively.
- Include PostgreSQL, MySQL/MariaDB, SQLite, SQL Server, and MongoDB as
  database choices. Redis is cache/queue infrastructure, not a primary
  database choice.
- Include REST, GraphQL, and gRPC; modular monolith, microservices, and
  serverless architectures; JWT, OAuth2/OIDC, and session authentication;
  cache and queue options; and testing, observability, and deployment
  practices. Represent compatibility in catalog data so invalid combinations
  can be rejected rather than silently accepted.
- Provide an Auto default and manual language/framework/database controls in
  the generation UI, with less common stack details in an advanced panel.
  Backend-language selection is distinct from the existing UI/output
  localization language.
- Seed a SQLite `technology_catalog_index` idempotently from the JSON catalog.
  Expose catalog options through the AI-agent API and the existing Express
  proxy. Carry a validated `backend_stack` selection through generation and
  dry-run planning, and include the resolved stack in generation results.

## Behavior and compatibility

Auto uses the prompt and analyzed requirements to recommend a compatible
stack. Manual values override only the corresponding dimensions; unspecified
dimensions remain eligible for recommendation. Invalid IDs or incompatible
combinations return a client validation error and do not start generation.

This phase adds catalog and planning support only. It does not add Python, PHP,
Java, Go, .NET, or Ruby backend scaffolds. The existing project builder remains
Node.js/Express-based. Results must explicitly distinguish a catalog-only
selection from a scaffold the builder can actually generate; they must not
claim that a non-Node backend was generated. The existing domain-specific SQL
schema selector remains unchanged, and schemas are not claimed to be portable
across database engines.

## Data flow

1. The UI retrieves catalog options through the Express proxy to FastAPI.
2. A user selects Auto or a language and optional advanced values.
3. Express forwards only the structured stack object with the generation or
   dry-run request.
4. FastAPI validates catalog IDs and compatibility, passes the selection to
   the stack selector, and records the resolved stack in the plan/report.
5. SQLite stores the seeded catalog; existing run/report persistence stores
   the resolved stack with generation output.

## Verification and acceptance

- Re-running database initialization seeds or updates catalog records without
  duplicates and leaves unrelated registry rows intact.
- Catalog API returns the curated languages, choices, and compatibility data.
- Auto mode recommends a valid stack; manual values override the recommendation
  only for the supplied dimensions.
- Unknown IDs and incompatible language/framework/database combinations fail
  validation before generation starts.
- Dry-run and completed-generation reports show the selected stack and whether
  a native scaffold is available.
- With no backend-stack selection, current Node.js/Express generation behavior
  remains unchanged.
- Focused tests cover catalog seeding/API, selection/validation, and the
  existing default path. Frontend lint/build and relevant Python/Express tests
  verify integration.
- Agent documentation describes the catalog, selection fields, Auto behavior,
  and the current non-Node scaffold limitation.

## Out of scope

Native backend scaffolding for the newly listed languages; conversion of
existing SQL schema files between database engines; an exhaustive list of
every language, framework, vendor, or deployment provider; and changes to
LumicorePro's own runtime backend.
