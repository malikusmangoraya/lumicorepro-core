# SRS Quality Gates — Resupro

> Functional system compliance (SEO + i18n) plus code-quality gates (TRD #5).

## 1. SEO Architecture

- **JSON-LD (14 default types):** GAP —
  1/14 present. Missing: WebSite, WebPage, Product, Offer, AggregateRating, BreadcrumbList, FAQPage, Service, LocalBusiness, Person, Article, Review, ImageObject.
  Top-up: skip.
- **Open Graph metadata:** GAP — canonical
  tags scanned across none.
- **Responsive headings:** VIOLATIONS —
  0 page(s) scanned; violations:
  none.

## 2. Internationalization (i18n)

- Bootstrap: PASS — `src/i18n/i18n.js`
  (i18next + `useTranslation`), RTL via `dir` set on change
  (PASS).
- Key hook: `frontend/src/hooks/useAppTranslation.js` (injected).
- Coverage: **2.0%** of components (
  1/51) text-abstract through translator hooks.

## 3. Code Quality Assurance Rules

- ESLint gate: configured (
  `scripts/eslint.generated.config.js`); Prettier: configured.
- Rule: ZIP archiving EXECUTION is blocked whenever the ESLint/Prettier pipeline
  flags structural/syntax errors (`agent/quality_gate.py` → orchestrator). Violating
  projects route to code_modifier self-healing and are re-gated before archive.
- Gate module: available.
