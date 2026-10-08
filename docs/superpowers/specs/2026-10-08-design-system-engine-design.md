# Design System Engine Design

## Status

Design proposed for review. No implementation changes are authorized until this
specification is approved.

## Problem

LumicorePro already has named visual styles, design tokens, design planning,
page recipes, and portfolio signatures. However, template selection and page
assembly still reuse a small set of fixed structures. Style application can
change colors and visual treatment without ensuring that navigation, hero
composition, section order, content, and density fit the requested product.

The existing manifest writer, orchestrator, planner, builder, style engine,
uniqueness module, tests, and generated projects have uncommitted workspace
changes. Implementation must preserve those changes and avoid rewriting the
existing 11 curated products.

## Goals

- Produce one canonical `design-manifest.json` for each newly generated project.
- Make both visual tokens and layout DNA drive the generated markup.
- Provide at least 12 hero archetypes, 8 navigation patterns, and 10 niche-aware
  page blocks, selected deterministically with niche fit and project seed.
- Persist portfolio fingerprints in SQLite and change the selected recipe when
  its hero, navigation, and section order are too similar to prior designs.
- Bind generated copy to brief/niche data and reject generic phrases,
  cross-niche leakage, and unsupported statistics, logos, or testimonials.
- Add evidence-based quality gates, at most three layout attempts, responsive
  screenshots at mobile/tablet/desktop, and a `design-preview` CLI command.
- Preserve existing CLI behavior, old design manifests, current products, and
  legacy layout modes.

## Non-goals

- Rebuilding or restyling existing generated products.
- Replacing the current 20-style prompt catalog or the larger runtime style
  catalog.
- Requiring an external AI provider for deterministic layout selection.
- Treating unavailable browser tooling as a successful screenshot or a11y pass.
- Adding new runtime services, databases for generated apps, or paid APIs.

## Proposed Architecture

Use a deterministic, recipe-based engine integrated with the existing design
decision and generation pipeline. Keep `DesignStyleEngine` responsible for
visual style/tokens and extend the current portfolio-uniqueness concepts rather
than maintaining a competing design selector. The new engine resolves a
versioned DNA object before page generation; builders consume that object to
compose real page blocks rather than merely recording a plan.

### Canonical DNA manifest

Add a versioned `design_dna` object to each project manifest while preserving
legacy top-level keys. Its required fields are:

- `version`, `project`, `seed`, `niche`, `audience`, `tone`.
- `tokens`: semantic color roles, display/body/optional mono fonts, type scale,
  spacing scale, radius, shadows, and motion preferences including reduced
  motion behavior.
- `layout`: navigation pattern, hero archetype, page recipes/section order,
  grid system, card treatment, footer type, and density.
- `content_sources`: brief/niche-pack provenance and explicit allowed claims,
  logos, and testimonials.
- `fingerprint`: stable hash plus normalized dimensions used for comparison.
- `selection`: deterministic candidate choices, niche-fit weights, retries,
  and any explicit user constraints.

`DesignManifestWriter` remains the persistence boundary. Reading older
manifests must continue to work; missing DNA is treated as a legacy manifest,
not an error. The canonical DNA is written once before code generation and
final QA metadata may be appended without recomputing the selected design.

### Layout archetypes and composable blocks

Create a declarative library with at least these 12 hero families: typographic,
editorial image, split product preview, cinematic media, search-led catalog,
product configurator, dashboard preview, service booking, map/local discovery,
story-led narrative, event/date-led, and data/metrics-led.

Create at least 8 navigation patterns: minimal top, editorial masthead,
commerce category bar, product workspace sidebar, centered brand navigation,
utility-first dashboard header, local-business contact nav, and immersive
overlay navigation.

Create niche-aware section blocks (at least 10), including product/catalog,
service booking, property listing, menu/reservation, course curriculum,
fitness program, claims/work queue, portfolio/case study, event schedule, and
travel itinerary. Each recipe is a list of named blocks and data bindings;
pages are composed from these blocks, not copied from one fixed Home template.

All generated block styling must consume semantic design tokens. Validators
must flag literal colors and hardcoded layout dimensions in block markup/styles;
content-derived values such as image URLs and accessibility labels are not style
tokens and remain allowed.

### Deterministic selection and portfolio registry

Selection uses a stable hash of normalized brief, niche, project name, and
explicit seed. Niche-fit weights restrict or prioritize valid hero, navigation,
and block candidates. Explicit user constraints take precedence; unconstrained
dimensions vary deterministically.

Add an isolated SQLite portfolio registry under the agent database directory,
with a versioned table for project name, fingerprint, normalized DNA dimensions,
and creation time. Use parameterized SQL, a busy timeout/WAL, and safe
`CREATE TABLE IF NOT EXISTS` initialization. Never modify existing registry
rows or product folders during preview/generation. Use existing manifest
fingerprints as a read-only compatibility fallback when the registry has no
history.

Similarity compares the requested collision keys: hero, navigation, and Home
section order. If the threshold is exceeded, deterministically try alternative
archetypes, up to three complete layout candidates total. Save the accepted
candidate and comparison evidence to the manifest and SQLite. If all
candidates collide, retain the best-scoring candidate but mark uniqueness as
failed; do not report it as unique.

### Content binding and anti-fabrication

Create or reuse a niche pack containing allowed terminology, features, and
content slots. Bind headline, CTA, feature, and section copy only to supplied
brief details or that pack. Maintain a banned generic phrase list, but do not
rely on phrase matching alone: identify claims, stats, logos, and testimonials
as evidence-backed content entries. Unsupported entries fail validation and
must be omitted or replaced with neutral, non-claim copy. Cross-niche terms
outside the selected niche and shared neutral vocabulary fail the leakage
check. No fabricated customer names, press marks, ratings, or outcome numbers.

### Quality gates and responsive evidence

Run the following before release status can pass:

1. DNA schema and uniqueness threshold check.
2. Token-usage scan of generated design blocks.
3. Contrast checks for semantic foreground/background token pairs, plus
   existing accessibility checks.
4. Browser screenshots and layout checks at 375x812, 768x1024, and 1440x900.
5. Content provenance, banned phrase, and cross-niche leakage checks.

An actionable layout failure can trigger another candidate, up to three total.
Do not retry for unavailable tooling, and do not convert missing measurements to
passes. If browser/screenshot tooling is unavailable, report `not_measured` and
keep release readiness blocked when screenshots are required. Preserve each
attempt's findings and report the final candidate and reason.

### CLI

Add a `design-preview` command that accepts a prompt/niche, sample count `N`,
and optional seed; it must not generate project files or mutate the registry.
Print each sampled DNA signature and a pairwise diversity matrix for hero,
navigation, and section order, plus a summary collision rate. Preserve current
flag-based CLI invocations; malformed counts and empty prompts return a useful
nonzero error.

## Integration and Compatibility

- Resolve DNA after requirement analysis and before the builder generates
  pages; pass it through the existing plan/spec boundary.
- Update generation so Home and applicable niche pages are actually composed
  from selected block recipes. Do not stop at writing a richer manifest.
- Keep the existing style catalog and palette overrides compatible; translate
  their values into semantic tokens rather than duplicating color selection.
- Preserve current explicit style/layout/reference constraints.
- Preserve current `design-manifest.json` fields and compatibility with legacy
  manifests and `design_uniqueness.py` consumers.
- Scope all generation changes to newly generated projects. Do not write into
  `products/`, `generated-projects/`, or existing live-project directories.

## Verification and Acceptance Criteria

- Unit tests prove stable selection for the same brief/seed, niche-weighted
  choices, explicit-constraint precedence, and a changed candidate after a
  collision, including the three-candidate limit.
- Tests prove SQLite inserts, duplicate handling, legacy-manifest fallback,
  and preview read-only behavior.
- Tests prove generated layouts reflect selected hero/navigation/section order
  and design blocks use tokens rather than literal style values.
- Tests reject banned generic phrases, cross-niche leakage, and unsupported
  stats/logos/testimonials while allowing brief-backed claims.
- Tests verify missing browser tooling yields `not_measured`/blocked, not pass;
  available browser QA captures all three configured viewports.
- CLI tests verify sample count, diversity matrix output, deterministic seed,
  invalid input, and no filesystem/registry mutation.
- Existing focused design/orchestrator/builder tests pass, followed by the
  complete `ai-agent/tests` suite. Run an isolated generation smoke test and
  confirm hashes/status of all 11 curated products remain unchanged.
- Report exact tests, screenshots actually captured, gates not measured, files
  changed, and whether the result is generated, verified, or release-ready.

## Implementation Boundaries

Expected implementation areas include the design intelligence package,
manifest writer, SQLite registry, project builder/orchestrator integration,
CLI, and focused tests. Exact file-level task breakdown belongs in the
implementation plan after this specification is approved.