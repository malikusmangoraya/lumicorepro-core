# LumicorePro — Themes & Templates Library Engine

The template library is now a **Template × Design-Style matrix**: every template
has multiple ready "looks" built by a token-driven theming engine, without
hand-designing each combination.

```
Template (35) × compatible Design Styles = 292 theme variants (formalised)
```

## How a variant is produced

A template's **layout/structure stays identical**; only `design-tokens.json`
(colours, radius, shadows, typography, spacing) is swapped via the
`DesignStyleEngine`. So the Neo-Brutalism restyle of "Restaurant Landing"
looks entirely different from its Minimalism twin — with zero layout rebuild.

```
registry/templates.json ─┐
  compatible_styles      ├─► ThemeMatrixEngine ─► variant (template::style)
DesignStyleEngine.STYLES ┘        │
                                  ├─► quality_gate()  (WCAG contrast, breakpoints, budgets)
                                  ├─► preview_manifest (previews/{tpl}/{style}.png)
                                  └─► package_template (.lctemplate pack)
```

## Part 1 — Theme matrix

`ai-agent/agent/theme_matrix.py` — `ThemeMatrixEngine`.
- `build_matrix()` → flat list of `{template_id, style_id, variant_id, preview, …}`.
- `project_variant(spec, template)` → the active combo for a generated project.
- Deterministic; read-only over the source library.

## Part 2 — Template metadata schema

Every entry in `registry/templates.json` now carries:
`id, category, compatible_styles, sections_used, conversion_optimized,
quality_score, complexity, industries_secondary, preview_screenshot, last_updated`.

Backfill: `scripts/backfill_template_metadata.py`.

## Part 3 — Coverage (countable gains)

| Area | Before | Now |
|---|---|---|
| Templates (registry) | 27 | **35** |
| Categories | 16 | **24** (added agency, gym, podcast, newsletter, marketplace, insurance, automotive, wedding) |
| Section library | 183 (12×15) | **223** (12 existing cats + 8 new × 5 = 40 new) |
| Theme variants | 0 formalised | **292** (35×compatible styles) |

Section scaffolds live in `src/templates/<category>/<Section>/` and mirror the
existing per-category section-library pattern (TemplateShell + token-driven
UI kit + lucide icons + `@/utils/images`).

## Part 4 — Quality gate per variant

`quality_gate(template, style)`:
- **Contrast (WCAG AA ≥ 4.5)** — exact static sRGB colour-math on text-on-bg and
  text-on-card; flags styles like dark cyberpunk / neo-brutalism that risk fails.
- **Responsive breakpoints** — mobile/tablet/laptop/wide coverage metadata.
- **Lighthouse budget** — declared contract (>90 desktop / >80 mobile); the actual
  headless-browser run is wired as a pipeline hook (needs a built app).
- Visual-regression snapshot is left as a hook for the same reason.

## Part 5 — Auto-preview generation

`scripts/generate_previews.py`:
- `--mode verify` (default, no browser): checks the `previews/{tpl}/{style}.png`
  contract and reports present/missing — CI/offline safe.
- `--mode live --base http://localhost:4173`: headless Chromium captures real
  screenshots into `previews/` for a self-hosted "browse before you generate"
  gallery (Framer/Webflow-style, fully self-hosted).

## Part 6 — Extensibility (.lctemplate)

`scripts/package_template.py [--id X | --all]` bundles a template + its style
packs into a portable `*.lctemplate` zip (manifest + template metadata + README).
Power users/agencies can create and share packs without touching core code —
WordPress-theme spirit for LumicorePro's code-output model.

## API

- `GET /api/themes` — matrix summary + full variant list (`by_category`,
  `variants_by_style`, `matrix`).
- `GET /api/themes/variants?variant_id={template}::{style}` — variant detail +
  quality gate.

## Orchestrator

Phase 6 (code generation) records `phase_6_theme_matrix` — the active
`theme_variant`, total variant count, quality gate, and preview manifest —
surfaced in the top-level report as `theme_variant`.
