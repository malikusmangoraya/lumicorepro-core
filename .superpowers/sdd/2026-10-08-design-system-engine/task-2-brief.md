# Task 2 Brief — Tokenized Page Composer

**Plan:** `docs/superpowers/plans/2026-10-08-design-system-engine.md`
**Consumes:** Task 1 DNA has `tokens.colors`, typography, spacing, radius, shadows, motion; `layout.navigation_pattern`, `hero_archetype`, `pages.Home.section_order`, grid/card/footer/density; selection and fingerprint.
**Produces:** `get_layout_catalog()` and `compose_project_pages(project_dir, design_dna, spec)` that write token-driven Home + applicable niche page(s), shared navigation and footer, plus structural evidence. ProjectBuilder invokes it only when a generation plan contains `design_dna`.

## Required checks

- Catalog exposes at least 12 hero, 8 navigation, and 10 niche-aware section choices.
- Same DNA produces stable structure; hero/navigation/section order changes actual markup, not only metadata.
- Niche content and page output are bound to the selected niche and brief data, safely escaped, with no fabricated metrics, customers, testimonials, or press logos.
- Generated blocks contain no literal color values or hardcoded pixel sizing; styling uses semantic CSS custom properties emitted from DNA.
- Existing project-builder plans without DNA keep their legacy output.

## TDD

Write tests in `ai-agent/tests/test_design_page_composer.py` and add a focused `ProjectBuilder` regression. Run the new composer test before implementation, then implement `layout_recipes.py`, `page_composer.py`, and the guarded builder integration. Verify with composer + relevant builder/backend tests. Commit only Task 2-owned files as `feat(design): compose pages from tokenized niche recipes`.
