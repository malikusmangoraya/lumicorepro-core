# Brand Guidelines — Apex Digital

The complete identity kit for this product. Everything here is generated from
`frontend/design-tokens.json`, so the logo, the favicon, the PWA icons and the
social share image are all the same artwork in different sizes.

## Logo

| Asset | Path | Use |
|---|---|---|
| Vector mark (app icon) | `frontend/public/favicon.svg` | browser tab, bookmarks |
| Multi-resolution icon | `frontend/public/favicon.ico` | legacy favicon requests |
| PWA icons | `frontend/public/icons/icon-*.png` | installable app, splash screens |
| Maskable icon | `frontend/public/icons/icon-maskable-512x512.png` | Android adaptive icons |
| iOS icon | `frontend/public/apple-touch-icon.png` | iOS home screen |
| Share image | `frontend/public/og-image.png` / `.svg` | link previews |

In React, import the mark instead of inlining an image:

```jsx
import { BrandMark } from './components/brand/BrandMark';
import BrandLockup from './components/brand/BrandLockup';

<BrandMark size={40} />
<BrandLockup size={34} />
```

Brand constants live in `frontend/src/components/brand/BRAND.js`
(`BRAND.name`, `BRAND.initials`, `BRAND.primary`, `BRAND.secondary`,
`BRAND.accent`). Changing a colour there and in `design-tokens.json` updates
every surface at once.

## Colour

| Role | Value |
|---|---|
| Primary | `#00e5ff` |
| Secondary | `#7c4dff` |
| Accent | `#00b0ff` |
| Surface | `#070913` |
| Text on surface | `#e0f2fe` |

The mark is a gradient tile from primary to secondary carrying
A layered summit peak with summit orb and base rail. Ink flips to dark automatically when the gradient is pale, and the
knockout tone is derived from the gradient itself, so the mark stays legible on
any palette you choose. The wordmark beside it is set in
Orbitron; the monogram **AD** is kept in
`BRAND.initials` for favicons and anywhere a single pair of letters is needed.

## Typography

- Display: **Orbitron**
- Sans / body: **Inter**

## Clear space and minimum size

Keep clear space equal to the monogram height on all sides. Never render the
mark below 16 px, and never recolour, rotate, outline or add effects to it —
use the maskable variant for adaptive-icon crops and let the browser handle
the rest.

## Live demo

https://malikusmangoraya.github.io/apex-digital

The demo is served from a GitHub Pages **project subpath**, which is why every
asset path in `manifest.json` is relative. If you move the product to a custom
domain, update `LIVE_URL.txt`, `frontend/index.html` (canonical, hreflang,
og:*, twitter:*, JSON-LD), `frontend/public/robots.txt` and
`frontend/public/sitemap.xml` in one pass.
