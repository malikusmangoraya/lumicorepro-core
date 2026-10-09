# Design System & Design Tokens — resupro

> Semantic, token-driven UI contract (TRD #3). Raw hex in components is barred —
> always reference the semantic mapping below.

## 1. Semantic Color Mapping

| Token       | Light (`:root`)       | Dark (`.dark` default) | Role                     |
| ----------- | --------------------- | ---------------------- | ------------------------ |
| `primary`   | rgb(14 165 233)       | rgb(34 211 238)        | brand primary action     |
| `secondary` | rgb(109 40 217)       | rgb(167 139 250)       | complementary action     |
| `accent`    | rgb(245 158 11)       | rgb(251 191 36)        | highlights / callouts    |
| `muted`     | rgb(100 116 139)      | rgb(148 163 184)       | secondary text, disabled |
| `canvas`    | `#ffffff`             | `#020617` (slate-950)  | page background          |
| text        | `#0f172a` (slate-900) | `#f8fafc` (slate-50)   | default foreground       |

- Canvas archetypes: **dark default** (`bg-canvas` → slate-950 / text slate-50),
  light alternative (white / slate-900). Toggled by `src/lib/theme.js` `.dark`
  class (honors saved preference + OS scheme).
- Usage: `bg-primary`, `text-secondary`, `border-accent`, opacity modifiers work
  e.g. `bg-primary/70`, `dark:bg-primary`. Tokens live in `tailwind.config.js`
  (`rgb(var(--t-*) / <alpha-value>)`) and `src/index.css` (`--t-*` variables).

## 2. Glassmorphism Spec

- Token utility: `.glass-md` == `backdrop-blur-md` + `bg-white/70`
  (`dark:` `bg-slate-900/70`) + `border border-white/10`.
- React component: `GlassCard` (`src/components/common/GlassCard.jsx`) implements
  the exact class combo. Use for premium containers (cards, modals, nav bars).

## 3. Motion Profiles (cohesive durations)

`src/lib/motionPresets.js` — every transition reads from the frozen `DURATIONS`
metric table (instant 80ms / fast 140ms / standard 240ms / expressive 420ms)
plus the shared `EASING` cubic-bezier(0.22, 1, 0.36, 1):

| Profile    | Duration | Easing                         |
| ---------- | -------- | ------------------------------ |
| instant    | 80ms     | cubic-bezier(0.22, 1, 0.36, 1) |
| fast       | 140ms    | cubic-bezier(0.22, 1, 0.36, 1) |
| standard   | 240ms    | cubic-bezier(0.22, 1, 0.36, 1) |
| expressive | 420ms    | cubic-bezier(0.22, 1, 0.36, 1) |

Wrapper: `MotionWrapper` (`src/components/motion/MotionWrapper.jsx`) with
variants `fade` / `slide-up` / `scale`; respects `prefers-reduced-motion`.

## Conformance

- Raw hex scan (components): 7 violation(s) —
  FIX: move colors into tokens.
- Tailwind config: ok.
- Token CSS: ok.
- Glass spec: ok.
- Motion profiles: ok.
- Dark default theme: ok.
