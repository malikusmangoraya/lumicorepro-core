# LumicorePro Core — Complete System Master Prompt

**Version:** 2.0  
**Status:** Production-ready Enterprise Blueprint  
**Scope:** Frontend (React 19 + Vite 8 + Tailwind CSS + Motion) · Backend (Node + Express + MySQL/Redis) · AI Agent Engine

---

## 1. System Architecture

```
End User → React 19 Frontend → Axios Interceptors → Express Backend → MySQL / Redis
                                  ↘ Fast Python AI Agent / Stripe / WebSockets
```

---

## 2. Frontend Design & UI/UX Standards

| Category | Rules & Requirements |
|----------|----------------------|
| **Branding & Logos** | **Never plain text.** Always generate a unique vector SVG logo (`UniqueLogo` / `BrandLogo`) with geometric symbols (Quantum, Hexagon, Shield, Infinity, Vortex, Diamond, Neural, Nova) and dual-tone gradients. |
| **Footers** | **Never a single plain line.** Always build a rich 4-5 column professional footer (`ModernFooter`) with brand story, live system status (`🟢 99.99% Operational`), newsletter signup with instant validation, categorized sitemap with badges, social links, and legal/copyright bottom bar. |
| **Headers & Navigation** | Sticky / Floating glassmorphism navbar (`GlassNavbar` / `Navbar`), responsive mobile menu drawer, active link indicators, Command Palette (`Cmd+K`), and glowing CTA buttons. |
| **Icons** | Real icons from `lucide-react`. Always paired with visible text or accessible `aria-label`. Standard size `h-4 w-4` or `h-5 w-5`. |
| **Images** | High-resolution photography via `ImageService` / Unsplash category matching. Wrapped in `LazyImage` or responsive containers with `alt` text, `object-cover`, and rounded radii. |
| **Motion UI** | Inspired by **AnimasterLib**, **SkipperUI**, and **VengeanceUI**: Bento Grids, Spotlight cursor illumination, 3D holographic tilt, animated border beams, text morphing, and magnetic buttons. |

---

## 3. Backend & Security Specifications

- **Input Validation & Sanitization**: Strict schema validation with Joi/Yup. Parameterized SQL queries only (no string concatenation).
- **Authentication**: JWT with secure rotation (15m access token, 7d refresh token in httpOnly cookie). Bcrypt hashing (12+ rounds).
- **Secrets & Config**: All keys loaded via `.env`. No hardcoded secrets.
- **Security Headers**: Helmet, strict CORS whitelist, Content-Security-Policy (CSP), rate limiting on `/api/auth` and `/api/ai`.
- **API Response Format**:
  ```json
  { "success": true, "status": 200, "message": "...", "data": {}, "timestamp": "2026-09-12T20:00:00Z" }
  ```

---

## 4. Production Readiness

- **Build Integrity**: Zero ESLint / compile errors. React 19 clean functional components and hook rules.
- **SEO & Meta**: Automated JSON-LD structured schemas, OpenGraph social cards, dynamic page titles and descriptions.
- **Internationalization & Currency**: Multi-language (`i18next`), RTL support, and multi-currency switching (`CurrencyContext`).
- **Containerization**: Dockerfile and Docker Compose production profiles.
- **Marketplace README**: Root `README.md` must include product details, Getting Started commands, env vars, deploy, troubleshooting, and license — sellable on Gumroad / Lemon Squeezy / ThemeForest without extra writing.
- **Pro UI only**: UniqueLogo, GlassNavbar, ModernFooter, dark mode, real assets. Hobby/demo UI is a failed delivery.
- **Zero defects**: No TODO stubs, no placeholder images, no committed secrets, no known lint/build errors.
