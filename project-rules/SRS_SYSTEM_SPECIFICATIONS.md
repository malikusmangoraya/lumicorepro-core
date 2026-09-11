# SRS_SYSTEM_SPECIFICATIONS.md — LumicorePro System Requirements Specification & Quality Gates

> Source of truth: TRD #5 *SRS Quality Gates*.
> Systemic semantic SEO compliance, i18n/RTL architecture, and the linter/formatter
> gates that must clear before the ZIP archive is compiled.

---

## SEO Architecture

### JSON-LD — 14 default schema.org types
Every generated project must ship **14 distinct** `@type` values
(`frontend/src/config/structured-data.js`, `LUMICORE_SEO`):

`Organization`, `WebSite`, `WebPage`, `Product`, `Offer`, `AggregateRating`,
`BreadcrumbList`, `FAQPage`, `Service`, `LocalBusiness`, `Person`, `Article`,
`Review`, `ImageObject`.

`seo_automation` supplies 7 (Organization, WebSite, Product, Offer,
AggregateRating, BreadcrumbList, FAQPage); the remaining 7 are topped up by the
quality gate (`WebPage`, `Service`, `LocalBusiness`, `Person`, `Article`,
`Review`, `ImageObject`).

### Open Graph / Twitter
`<head>` must carry: `og:title`, `og:description`, `og:image`, `og:url`,
`og:type`, `og:site_name`, `og:locale`, `twitter:card`.

### Responsive heading hierarchy
Generated pages must expose exactly one `h1` and no missing `h1` beneath deeper
headings or `h1 → h3+` level jumps. `components/` is excluded from this scan.

## Internationalization

- Bootstrap `frontend/src/i18n/i18n.js` (`LUMICORE_I18N`): i18next +
  `initReactI18next` + `LanguageDetector`; `fallbackLng: 'en'`.
- **RTL:** `RTL_LANGUAGES = ["ar","he","fa","ur","ps","ku","sd"]`; on
  `languageChanged` set `document.documentElement.dir`.
- Translator key hook: `frontend/src/hooks/useAppTranslation.js`
  (`useTranslation` abstraction).
- **Coverage gate:** ≥ 100% of `frontend/src/components/**` must route strings
  through `useTranslation`/`useAppTranslation` (counted, reported; advisory).

## Code Quality Assurance (linter/formatter gates)

- **Prettier** pass with `.prettierignore`-scoped formatting.
- **ESLint** flat config (`scripts/eslint.generated.config.js`).
- Both must exit `0` **before the ZIP archive is compiled**; ESLint errors block
  archiving and route the project back to `code_modifier` self-healing.
- Verified wiring (not duplicated) by the functional compliance gate.

## Conformance

| Check | Gate reference |
|-------|----------------|
| 14 JSON-LD types present | `srs.checks.jsonld` |
| OG + twitter meta in `<head>` | `srs.checks.open_graph` |
| Heading hierarchy clean | `srs.checks.headings` |
| i18n bootstrap + RTL + hook | `srs.checks.i18n_rtl` |
| Linter/formatter gate wired | `srs.checks.devops` |

**Hard rule:** JSON-LD gaps, missing OG meta, heading violations, or absent i18n
bootstrap in a generated file are SRS violations routed to self-healing; the ZIP
archive is not compiled while this check is red.