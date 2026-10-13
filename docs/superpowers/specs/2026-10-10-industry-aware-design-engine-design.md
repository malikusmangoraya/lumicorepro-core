# Industry-Aware Design Engine — Design Specification

## Status

Proposed for user review. This specification records the approved direction only; implementation and implementation planning are not authorized until the user approves this written spec.

## User intent and success

The user wants each newly generated website or project to have its own advanced UI/UX layout, tailored to its industry and brand. The agreed quality bar is **distinctive, usable, responsive, accessible, and fast**. The user approved both design-engine improvements and industry-specific layout families, delivered in phases. This first design is limited to new project generation; it does not authorize a bulk redesign of existing products.

Success means a generated site's actual page structure and visual system—not merely its color palette or descriptive manifest—reflect the project brief, industry, brand, and explicit user constraints, with design decisions reproducible and quality evidence honestly reported.

## Current system and constraints

The agent already contains a DesignDecisionEngine, DesignPlanner with page/section plans, DesignStyleEngine for visual tokens, ThemeMatrixEngine for template/style compatibility, design manifest and uniqueness support, portfolio-aware design selection, design lint/scoring/gate modules, and orchestrator integration. These modules have existing consumers and tests. Extend and connect these foundations; do not create a parallel selector or duplicate manifest system.

The current generator applies some style/theme decisions after page assembly, and the theme matrix explicitly documents that its style variants do not alter layout. The design planner has page and section recipes, but coverage and consumption need validation so selected recipes are materially reflected in generated pages. Existing-project iteration must preserve unrequested design decisions. Respect current user-specified style/reference constraints, the existing design token contract, and the existing design uniqueness spec. Do not disturb unrelated in-progress security changes.

## Scope

### In scope

- Audit current engine-to-builder data flow and identify where layout decisions are selected, persisted, and consumed.
- Establish one canonical, versioned layout-DNA/design-manifest contract, extending existing manifest and planning formats compatibly.
- Add a bounded catalog of distinct, industry-relevant layout families and section/page recipes to existing design modules.
- Resolve layout families deterministically from industry, brand personality, audience, brief, project seed, and user constraints.
- Pass selected layout decisions into page generation before markup is assembled so generated structure matches the selected recipe.
- Preserve portfolio uniqueness behavior: prefer meaningfully different compatible designs, but never override explicit requirements solely for novelty.
- Add honest quality validation for layout-family application, token use, accessibility/responsive intent, and available browser evidence.
- Deliver in phases: first architecture/data-flow and recipe coverage, then validate a representative subset of industries and expand catalog coverage based on testable results.

### Out of scope

- Redesigning every existing project or live product in this milestone.
- Replacing the current visual style catalog, React/Vite stack, or existing generation architecture.
- Adding third-party services, paid APIs, new external dependencies, or deployment changes.
- Claiming global uniqueness or guaranteed Lighthouse/WCAG scores without running those checks.
- Forcing animation, gradients, glassmorphism, 3D, or one layout style on every industry.
- Broad unrelated refactoring or altering ongoing tenant-isolation/security work.

## Proposed design

### 1. Canonical design DNA

Extend the existing design decision and manifest boundaries; there must be one authoritative decision for a generated project. Preserve current top-level manifest fields and legacy reads. New DNA should be versioned and include:

- project identity and stable design seed;
- detected/explicit industry, audience, brand archetype/personality, and provenance;
- selected visual style and semantic token references (reuse DesignStyleEngine);
- layout family, hero composition, navigation pattern, page recipes/section order, density, imagery treatment, interaction and motion profile;
- explicit user constraints and resolved conflicts (mobile and reduced-motion behavior included);
- portfolio uniqueness comparison/outcome and selection rationale;
- quality evidence states, distinguishing measured, failed, and not measured.

The canonical contract should be JSON-serializable, deterministic for identical normalized inputs, and backward-compatible with existing manifests and consumers.

### 2. Layout families and industry recipes

Add declarative, testable recipes rather than hard-coded per-customer pages. Recipes are selected from reusable layout families and composed with industry-specific page sections/data slots. Initial representative coverage should include at least: SaaS, ecommerce/marketplace, fintech, real estate, food/hospitality, portfolio/creative, healthcare, education, automotive, and events/entertainment. The exact initial family count is set during implementation planning after catalog audit; each family must differ in structural choices (e.g. hero composition, navigation, section rhythm, and content density), not just colors.

Industry recipes define appropriate page goals, primary journey/CTA, suitable page sections, trust needs, and avoidances. Brand playbooks tune typography, spacing, image treatment, surface and motion without erasing the industry journey. Layout variation must remain coherent with the brief and cannot introduce fake reviews, unsupported statistics, or fabricated trust claims.

### 3. Deterministic decision and generation flow

The intended flow is: brief/requirements → industry/audience/brand/reference analysis → layout-family and visual-style decisions → constraint resolution and uniqueness comparison → canonical plan/manifest → page builder consumes the decisions → quality validation and evidence. Decisions must reach the generator before page markup is assembled; post-build restyling alone is insufficient for layout differentiation.

Use the existing planner/orchestrator/design-decision/manifest integration points. Explicit user choices win. If an input is ambiguous or an optional playbook is unavailable, apply a documented deterministic fallback and record it rather than silently claiming a playbook was used. Existing-project iteration loads the existing manifest and preserves all unrequested design decisions.

### 4. Quality, accessibility, responsiveness, performance

- Layout tests assert materially distinct structures and correct industry-specific page composition.
- Semantic tokens are used for generated visual values; do not add raw style literals that violate the project token contract.
- Generated recipes specify semantic headings/landmarks, labelled controls, keyboard operation, visible focus, image alternatives, and reduced-motion-safe behavior.
- Responsive intent is verified at narrow mobile, tablet, laptop, and desktop widths (at minimum 375, 768, 1024, and 1440 CSS px); test overflow, clipping, navigation, hero collapse, and primary action visibility.
- Browser, performance, contrast, and accessibility results must report actual measurements. If tooling is unavailable, mark not measured; do not present a pass.
- Keep generated runtime lightweight: reuse current dependencies, avoid forcing 3D/heavy animation, and honor reduced-motion and mobile constraints.

### 5. Compatibility and safety

- Preserve existing APIs and manifest fields; legacy manifests remain readable.
- Keep DesignStyleEngine responsible for visual tokens and reuse ThemeMatrixEngine where its compatibility mapping remains relevant; avoid multiple authoritative style/layout decisions.
- Preserve deterministic behavior and current uniqueness behavior; explicit requirements take precedence over diversity.
- Scope generation changes to new projects. Do not rewrite existing product folders or manifests in bulk.
- Keep scope isolated from ongoing security/tenant-isolation edits; inspect status and only modify files required by the approved plan.

## Acceptance criteria

1. Given the same normalized prompt, project identity, and seed, the engine selects the same layout DNA; a different industry/brand can produce a materially different compatible structure.
2. Explicit layout/style/reference constraints take precedence over defaults and portfolio diversity; conflicts are recorded in provenance.
3. Representative industry recipes select relevant page sections and journeys; tests verify real generated structure, not manifest-only claims.
4. Generation consumes the chosen hero, navigation, section order, and visual tokens before page markup is assembled.
5. The canonical manifest records the decisions actually passed to generation, remains readable by existing consumers, and round-trips deterministically.
6. Existing project iteration preserves unrequested manifest decisions; prior generated projects are not modified.
7. Uniqueness checks prefer structurally different compatible candidates without forcing unrelated visual changes; unresolved collisions are reported honestly.
8. Tests cover unknown industry/brand fallback, missing optional playbook, legacy manifest, explicit constraints, token contract, and malformed/unavailable inputs.
9. Responsive/accessibility/performance evidence is reported truthfully; missing browser tooling cannot yield a pass.
10. Focused design/planner/orchestrator tests and the full AI-agent suite are run where dependencies permit; any blocked checks are reported.

## Phasing and handoff

- **Phase 1 — Audit and contract:** map current data flow; agree canonical DNA fields and migration/compatibility behavior; establish test fixtures.
- **Phase 2 — Recipes and integration:** implement declarative layout families and representative industry recipes, wire selected decisions into generation before markup assembly, persist through existing manifest boundary.
- **Phase 3 — Validation and coverage:** verify representative generated outputs, deterministic uniqueness, responsive/accessibility evidence, then expand recipe coverage using the same contract.

Detailed file-by-file tasks, exact test commands, and execution method belong in the implementation plan after the user approves this spec. No code changes are included in this design deliverable.
