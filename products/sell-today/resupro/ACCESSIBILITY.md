# Accessibility baseline

Implemented in the shipped UI:

- Skip-to-content link as the first focusable element.
- Semantic landmarks (`header`, `main`, `nav`, `footer`).
- Real labels on form fields, visible focus styles, dark mode.
- `prefers-reduced-motion` respected for motion content.

Not claimed: a formal WCAG 2.1 AA certification. Before each public
release, run an axe-core pass plus Lighthouse on Home, Login, Register,
Checkout (where present) and the product niche page, and record the
results in the release notes.
