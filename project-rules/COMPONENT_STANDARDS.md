# Component Standards — LumicorePro Core

## Rules (simple & professional)

1. **One component per file** under the right category (`ui/`, `forms/`, `templates/…`).
2. **Tailwind first** — CSS modules only for rare complex cases.
3. **Design tokens** — use `primary`, `muted`, `border`, never hardcode brand colors.
4. **Props** — clear defaults: `variant`, `size`, `disabled`, `className`, event handlers.
5. **States** — default, hover, active, disabled, loading, focus, error where relevant.
6. **a11y** — `aria-*`, keyboard support, visible focus rings.
7. **Motion** — `transition-all duration-200`, respect `prefers-reduced-motion`.
8. **Docs** — short JSDoc with usage example on public components.

## Variants

`primary` · `secondary` · `success` · `danger` · `warning` · `info` · `outline` · `ghost`

## Sizes

`xs` · `sm` · `md` (default) · `lg` · `xl`
