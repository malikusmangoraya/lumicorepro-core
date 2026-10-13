# International Layout Policy for Generation and Updates

**Status:** Draft for user review; implementation is not authorized until this spec is approved.

## Intent and success

The user wants the website agent to try internationally competitive, industry-appropriate layouts for both newly generated sites and requested updates to existing websites. User-approved policy: international-quality layout is the default, but an explicit request to preserve the existing layout/design takes precedence. Apex's current automotive dealer layout is intentional and must remain in place; this policy does not authorize reverting it to its previous generic SaaS layout.

Success means generation and update flows both consult the existing design engine and user intent; updates preserve a site's existing design decisions unless redesign is explicitly requested; international layout quality is a preference implemented through existing design-system/layout machinery, not a promise of measured compliance without evidence.

## Existing system and boundaries

The AI agent already has layout recipes and page composition, design style resolution, requirements/planning, iteration and orchestrator paths. Extend those current pathways rather than creating a parallel selector. Existing worktree has unrelated and ongoing edits; avoid clobbering them and limit changes to the eventual approved plan.

The generator must distinguish a deliberate design update from a content/bug/feature update. For a normal update, inspect and retain current layout structure, tokens and manifest choices where available. If no design manifest exists, infer from the existing project files and preserve the recognizable layout. For new generation, resolve an international-quality, industry-and-brand-appropriate design through existing layout recipes. In all paths, explicit user instructions and product requirements win over defaults.

## Policy

1. **New generation:** select and apply a distinctive, internationally competitive layout that matches industry, brand, audience, content, accessibility and responsive requirements. Consume structural choices during page composition, not just post-build color restyling.
2. **Existing-site updates:** inspect existing pages/design manifest before proposing or making changes. Keep existing layout and design-system choices for changes that do not request redesign. For a redesign request, try a compatible international-quality layout while preserving specified content, functionality, brand identity and constraints.
3. **Explicit preservation:** requests such as “keep the current layout,” “only update content,” or “do not redesign” prohibit layout replacement. State any conflict rather than silently changing layout.
4. **International quality is not a single template:** use the existing industry/brand system to select appropriate hierarchy, navigation, section composition and responsive behavior. Do not impose one global visual formula, gratuitous effects, fake testimonials/metrics, or unsupported claims.
5. **Evidence:** report only checks actually run. Browser, accessibility, responsive, performance or visual scores unavailable in the runtime are “not measured,” not passed.
6. **Apex exception/context:** retain the current Apex Motor Collective automotive layout as intentional; only change it if the user explicitly requests a redesign.

## Integration design

Use the existing orchestrator/planner and project-iteration entry points to pass a small normalized design intent (for example, `preserve_existing`, `international_default`, or `redesign_requested`) alongside current project context. Reuse existing `DesignSystemEngine`, page recipes/composer, manifest/memory and iteration modules. Exact interface names and file-by-file wiring are for the implementation plan after spec approval.

During an update, load any existing manifest and preserve all decisions not explicitly targeted. If manifest is missing, inspect available source/styles and record the inferred-preservation fallback. During new generation, feed resolved layout family, hero, navigation and section composition into page assembly. Keep old request formats working with a safe default: generation uses international-default selection; updates preserve existing layout unless the request explicitly asks for redesign.

## Acceptance criteria

- New generation without a layout preference selects an industry/brand-compatible layout through the existing design engine and uses it during page markup composition.
- An ordinary existing-project update preserves existing layout and tokens, including when an existing manifest is present.
- An ordinary update of a project without a manifest preserves its recognizable structure based on source inspection and records the inferred fallback.
- Explicit redesign requests activate layout selection; explicit keep-layout requests preserve it even when international-default policy exists.
- Explicit choices are not overridden by diversity/novelty logic; conflicting requirements are surfaced.
- Old API/request callers remain compatible and safely follow the policy defaults.
- Tests cover generation default, update default, explicit redesign, explicit preserve, legacy/missing manifest, existing manifest retention, and deterministic recipe resolution.
- Quality reports distinguish measured evidence from not-measured checks; no unsupported score claims are introduced.
- Apex's current automotive homepage is not reverted or modified as part of the agent-policy change.

## Out of scope

Bulk redesign of existing products, changing Apex's current layout, adding a new design system in parallel, external services/dependencies, deployment, and claiming that “international” guarantees a particular award, WCAG certification or performance score.

## Phasing

1. Audit the generation/update call graph and identify existing design-intent/manifest fields.
2. Wire the policy into existing generation and update flows with backward-compatible defaults.
3. Add focused policy tests and verify representative output structure; run relevant AI-agent suites.

Detailed exact files, interfaces and commands belong in the implementation plan after approval of this written spec.