# UI_UX_DESIGN_TOKENS.md — LumicorePro UI/UX Architecture & Design System Tokens

> Source of truth: TRD #3 *UI/UX Architecture & Design System Design Tokens*.
> Every selector/class in generated code must use the predefined token system.
> Dark canvas is the default.

---

## Color Tokens

RGB triplets resolved via `rgb(var(--t-*) / <alpha-value>)` (enables every
Tailwind opacity modifier: `bg-primary/70`, `dark:bg-secondary`). `darkMode: 'class'`.

| Token | Dark (default, `2 6 23` canvas) | Light (`255 255 255` canvas) |
|-------|------------------------------|------------------------------|
| `--t-canvas` | `2 6 23` | `255 255 255` |
| `--t-canvas-text` | `248 250 252` | `15 23 42` |
| `--t-primary` | `34 211 238` | `14 165 233` |
| `--t-secondary` | `167 139 250` | `109 40 217` |
| `--t-accent` | `251 191 36` | `245 158 11` |
| `--t-muted` | `148 163 184` | `100 116 139` |
| `--t-glass-bg` | `15 23 42` | `255 255 255` |
| `--t-glass-border` | `255 255 255` | `255 255 255` |

Tailwind semantic color contract (when `tailwind.config.js` is absent it must be
written with exactly this mapping):

```js
colors: {
  canvas: 'rgb(var(--t-canvas) / <alpha-value>)',
  primary: 'rgb(var(--t-primary) / <alpha-value>)',
  secondary: 'rgb(var(--t-secondary) / <alpha-value>)',
  accent: 'rgb(var(--t-accent) / <alpha-value>)',
  muted: 'rgb(var(--t-muted) / <alpha-value>)',
},
```

## Glassmorphism

Canonical spec — exact classes, no deviation:

`backdrop-blur-md bg-white/70 dark:bg-slate-900/70 border border-white/10`

- Component form: `frontend/src/components/common/GlassCard.jsx`.
- Token utility form: `.glass-md` in `index.css`
  (`blur(12px)`, `rgb(var(--t-glass-bg) / 0.70)`, `rgb(var(--t-glass-border) / 0.10)`).

## Motion Profiles

`frontend/src/lib/motionPresets.js` — every animated wrapper reads from it:

| Key | Value |
|-----|-------|
| `DURATIONS.instant` | `80` ms |
| `DURATIONS.fast` | `140` ms |
| `DURATIONS.standard` | `240` ms |
| `DURATIONS.expressive` | `420` ms |
| `EASING` | `[0.22, 1, 0.36, 1]` |
| `PRESETS` | `fade`, `slide-up`, `scale` |

Wrapper: `frontend/src/components/motion/MotionWrapper.jsx` (framer-motion,
`useReducedMotion`).

## Theme Default

`frontend/src/lib/theme.js` applies `.dark` on `<html>` by default, honoring a
saved preference then `prefers-color-scheme`. Imported first in `App.jsx`.

## Conformance

| Check | Rule | Gate reference |
|-------|------|----------------|
| Semantic tokens | `--t-*` CSS block or token-mapped `tailwind.config.js` present | `design.checks.tokens` |
| Glassmorphism | `GlassCard.jsx` exact class string or `.glass-md` present | `design.checks.glass` |
| Motion | `motionPresets.js` `DURATIONS.standard=240` present | `design.checks.motion` |
| Theme | `theme.js` + App import present | `design.checks.theme` |
| No raw hex | **Hard violation** — no `#hex` color literals in `frontend/src/components/**` | `design.checks.raw_hex` |

**Hard rule:** raw hex literals (`#[0-9a-fA-F]{3,6,8}`) inside any generated
component are a design-token violation routed to self-healing. The ZIP archive is
not compiled while this check is red. Legacy palette utilities (slate/cyan/etc.)
are grandfathered and advisory-only; the token system is the canonical path for
new code.