# Component Standards — LumicorePro Core

## 1. Core Component Rules
1. **One component per file** under the right category (`motion/`, `ui/`, `common/`, `forms/`, `templates/…`).
2. **Tailwind first** — Utility tokens (`primary`, `muted`, `border`, `card`, `background`) over hardcoded hex codes.
3. **Props contract** — Clear defaults: `variant`, `size`, `disabled`, `className`, event handlers.
4. **States** — default, hover, active, disabled, loading, focus, error where relevant.
5. **a11y** — Semantic HTML5 (`header`, `main`, `nav`, `footer`), `aria-*`, keyboard support, visible focus rings.
6. **Motion & Interaction** — Framer Motion & CSS keyframes, respect `prefers-reduced-motion`.
7. **React 19 & Vite** — Clean functional components, proper hooks usage, no broken lifecycle quirks.

---

## 2. Motion & Aesthetic Libraries (Animaster + Skipper UI + Vengeance UI)
| Library / Category | Components | Visual Characteristic |
|--------------------|------------|-----------------------|
| **Animaster Lib** | `TextMorph`, `TextShimmer`, `GlitchText`, `MagneticButton` | Kinetic typography, text morphing, magnetic spring pull, glowing gradient borders |
| **Skipper UI** | `SpotlightGrid`, `SpotlightCard`, `BorderBeam`, `BentoGrid` | Dark minimalist spotlight, cursor tracking illumination, moving border beams |
| **Vengeance UI** | `HolographicCard`, `CyberGridCanvas`, `TiltCard` | 3D perspective tilt, holographic specular sheen, neon cyber borders, particle repulsion |

---

## 3. Brand Identity & Header / Footer Architecture
- **Dynamic Brand Logo (`UniqueLogo`)**: Never use plain text for logos. Use `UniqueLogo` to render deterministic SVG vector marks (Quantum, Hexagon, Shield, Infinity, Vortex, Diamond, Neural, Nova) with brand dual-color gradients.
- **Professional Footer (`ModernFooter`)**: Never use a single plain line for footers. Every website must have a rich multi-column footer featuring:
  - Brand identity & unique SVG logo & mission statement
  - Live system status badge (`🟢 99.99% Operational`)
  - Categorized links (Product, Solutions, Resources, Company, Legal) with feature badges
  - Interactive newsletter subscription with instant validation
  - Bottom bar with Copyright, React 19 + Vite badge, Language/Currency selector, and Back to Top button.
- **Header & Navigation (`GlassNavbar` / `Navbar`)**: Glassmorphism backdrop blur, active link styling, Command Palette (`Cmd+K`) integration, responsive mobile drawer, and glowing CTA buttons.

---

## 4. Standard Variants & Sizes
- **Variants**: `primary` · `secondary` · `success` · `danger` · `warning` · `info` · `outline` · `ghost` · `glow`
- **Sizes**: `xs` · `sm` · `md` (default) · `lg` · `xl`
