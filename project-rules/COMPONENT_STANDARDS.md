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
- **Professional Footer (`ModernFooter`)**: Use a composed multi-column footer featuring:
  - Brand identity, unique SVG logo and truthful mission statement.
  - Categorized links to implemented routes; no dead `#` links or invented legal pages.
  - Newsletter, social, language/currency and status controls only when functional and supported by owner-supplied evidence.
  - Copyright and a working Back to Top action; never fabricated uptime, certification, testimonials, prices or payment claims.
- **Header & Navigation (`GlassNavbar` / `Navbar`)**: Use design-system tokens, active link styling and real CTA destinations. Mobile navigation needs labeled controls, `aria-expanded`/`aria-controls`, Escape close with focus return, and close-on-navigation. Add a command palette only when implemented.
- **Authentication routes**: Login, registration, password-reset, and other identity-flow screens use a focused auth layout; do not render marketing navigation, promotional banners, or the marketing footer on these routes. Keep auth-specific branding and required navigation links within the auth form/layout.

---

## 4. Standard Variants & Sizes
- **Variants**: `primary` · `secondary` · `success` · `danger` · `warning` · `info` · `outline` · `ghost` · `glow`
- **Sizes**: `xs` · `sm` · `md` (default) · `lg` · `xl`
