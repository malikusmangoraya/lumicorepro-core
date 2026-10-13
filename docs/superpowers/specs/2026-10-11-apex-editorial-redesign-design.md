# Apex Editorial Collector Showroom — Design Spec

## Purpose and approved brief

Redesign the existing Sell Today **Apex** automotive site into a complete, distinctive collector-car showroom before applying the approach to other products. The approved direction is **Editorial collector showroom**: warm ivory, graphite and restrained brass; magazine-like asymmetry; large vehicle photography; refined typography; premium but approachable. Reuse installed project dependencies and existing React, Tailwind, React Router, i18next and Lucide conventions; do not add a UI-library dependency.

## Scope

In scope: the Apex frontend only, including its brand mark, global navigation/footer shell, page/layout composition, reusable product-specific sections and components, responsive behavior, reduced-motion behavior, page copy/metadata, and meaningful customer-facing navigation and contact/inquiry interactions already supported by the project.

Out of scope: the AI agent design engine, all other ten Sell Today products, backend/API/payment behavior, production data, deployment, claims of real inventory/availability or third-party endorsements without evidence, and new external UI libraries. Preserve existing functionality and public routes unless a verified defect requires correction.

## Experience and information architecture

- Global shell: accessible skip link, sticky responsive navigation, unique Apex vector mark/wordmark, clear primary inquiry action, mobile navigation with keyboard-operable open/close behavior, and a multi-column footer with contact/navigation/legal links.
- Home: editorial hero with clear value proposition and two actions; curated inventory preview; transparent inspection/provenance process; ownership/concierge service; evidence-safe trust content; contact CTA.
- Inventory/services route(s): reuse existing public routes; present available catalog examples as clearly illustrative unless backed by actual inventory data. Include relevant attributes and direct inquiry links. Do not claim live search/filtering unless supported by real data and behavior.
- About: brand story and inspection standards, with no fabricated credentials.
- Contact: labeled form with validation, loading/success/error feedback and recovery, preserving the existing API behavior. If no backend endpoint exists, use honest mail/contact fallback rather than false submission success.
- Legal pages: retain existing privacy/terms content and routes; ensure they remain reachable.

## Visual system

- Palette: semantic tokens for warm paper/ivory canvas, elevated white surface, graphite text, muted warm-gray secondary text, restrained brass accent, and accessible status colors. Reuse the existing token mechanism where possible; no arbitrary per-component hex values.
- Typography: use the existing local/declared font stack; editorial display face paired with a highly legible body/UI face, no more than two families. Avoid remote font dependencies unless already used.
- Composition: asymmetric editorial hero, image-led vehicle features, varied section rhythms, simple borders, restrained square/low-radius surfaces; avoid repeated generic card grids and gratuitous glass/gradient/glow effects.
- Imagery: use existing locally available Apex vehicle imagery; verify paths and render. Meaningful images receive descriptive alt text; decorative images use empty alt. Do not invent asset rights or vehicle facts.
- Brand: create an original inline SVG geometric mark and lockup with accessible name/title, dual-tone brand colors, and no external logo dependency.
- Motion: purposeful short transitions only; respect `prefers-reduced-motion` and preserve functionality without animation.

## Components and interfaces

Use small, focused, product-specific components within the existing Apex frontend structure. Candidate units: `BrandMark`/`BrandLogo`, `Navbar`, `Footer`, `EditorialHero`, `VehicleFeature` or `VehicleCard`, `InspectionSteps`, `InquiryCTA`, and the existing contact form. Reuse shared components only where their semantics and visual behavior fit Apex; do not copy whole unrelated product pages. Keep existing route exports and React Router paths stable.

## Accessibility and responsive requirements

Semantic landmarks and heading order; skip link; visible focus; keyboard-operable navigation and forms; labels and actionable inline errors; meaningful link/button names; accessible mobile menu state; image alt text; no color-only meaning; adequate contrast; reduced-motion support. Design intentionally from 320px through 1920px, with explicit checks at 375, 768, 1024, 1440 and 1920px. No horizontal overflow, clipped text, hidden primary action, or collapsed hero.

## Acceptance criteria

1. Apex build succeeds and existing tests/smoke checks still pass; add focused tests for brand mark presence, route/navigation essentials, and honest contact behavior where test infrastructure permits.
2. Main route and existing public routes render; browser console has no fatal errors and local images load.
3. Distinct editorial visual hierarchy is present: warm paper/graphite/brass tokens, asymmetric image-led hero, varied section composition, and original SVG mark—not merely a recolor of the current generic page.
4. Navigation, mobile menu, primary CTAs, inventory inquiry links, and contact form give real, honest responses. No inert controls or fabricated success.
5. Responsive checks at 375/768/1024/1440/1920 and reduced-motion mode show no overflow/collapse; key journeys and keyboard behavior are verified in the browser.
6. Build and browser evidence are reported; any blocked checks, asset provenance, legal/content gaps, or backend limitations are explicitly listed. No deployment or production changes.

## Risks and constraints

Existing copy may imply inventory, press features, counts or inspection statistics that are not verifiable. Remove or qualify unsupported claims; present sample inventory as illustrative. Contact submission may depend on backend configuration; do not state a message was sent unless the existing endpoint confirms it. The shared checkout contains unrelated pre-existing modifications; only touch directly relevant Apex frontend files and new design documentation.
