# LumicorePro System Prompt — Quality Standards Reference

**Version:** 2.1  
**Scope:** All generated projects must meet these standards

---

## Performance Standards

| Metric | Minimum | Target |
|--------|---------|--------|
| Lighthouse Performance | 90 | 95+ |
| Lighthouse Accessibility | 85 | 90+ |
| Lighthouse Best Practices | 85 | 90+ |
| Lighthouse SEO | 85 | 90+ |
| First Contentful Paint | <2s | <1.2s |
| Time to Interactive | <4s | <2.5s |
| Animation FPS | 30 | 60 |

**Implementation:**
- Vite for bundling with code splitting
- Tailwind CSS (no runtime CSS-in-JS overhead)
- `transform-gpu` for animated elements
- Lazy load images below fold
- WebP format preferred

---

## Security Standards

| Requirement | Implementation |
|-------------|----------------|
| HTTP headers | Helmet.js with CSP |
| Rate limiting | 100 req/15min general, 20 req/15min auth |
| CORS | Whitelist origins only |
| Input sanitization | Strip script tags, javascript: URLs |
| Authentication | JWT (15min access) + bcrypt (12 rounds) |
| Secrets | Never commit `.env`, use `.env.example` |
| SQL | Parameterized queries only |
| HTTPS | Required in production |

**File:** `backend-library/shared/middleware/security.js`

---

## Feature Standards

Every ecommerce project must include:

- [ ] Product catalog with grid + details
- [ ] Shopping cart + checkout flow
- [ ] User authentication (register/login)
- [ ] Search with filters
- [ ] Reviews/ratings display
- [ ] 5+ trending features from registry
- [ ] Responsive mobile layout
- [ ] Dark/light theme support

Every SaaS project must include:

- [ ] Pricing table
- [ ] Feature comparison grid
- [ ] User dashboard with metrics
- [ ] Authentication + subscription flow
- [ ] Analytics charts

---

## Asset Standards

| Rule | Detail |
|------|--------|
| Real images only | `.jpg`, `.png`, `.webp`, `.svg` from `src/assets/` |
| No AI-generated | Reject filenames matching `ai-generated`, `placeholder`, `dummy` |
| Max file size | 5MB per image |
| Min dimensions | 100×100px |
| Icons | Lucide React with visible labels in navigation |

**File:** `src/utils/imageValidator.js`

---

## Animation Standards

- Duration: 150–300ms for UI transitions
- Easing: `ease-out` for entrances, `ease-in` for exits
- Use CSS transforms (translate, scale, opacity) — never animate width/height
- Respect `prefers-reduced-motion`
- Badge animations: subtle bounce, max 2s cycle

---

## Code Quality Standards

| Rule | Detail |
|------|--------|
| No TODO stubs | Deliver complete, working code |
| Consistent naming | PascalCase components, camelCase functions |
| Barrel exports | `index.js` in each component category |
| API responses | `{ success, status, message, data, timestamp }` |
| Error handling | Centralized Express error handler |
| Validation | Frontend form validators + backend input validation |
| Dependencies | All imports declared in package.json |

---

## Database Standards

| Rule | Detail |
|------|--------|
| Engine | PostgreSQL |
| Naming | snake_case tables and columns |
| Foreign keys | All references validated |
| Indexes | On frequently queried columns |
| Migrations | Schema in `database/schema.sql` |
| Required tables | Validated via schemaValidator |

**File:** `src/utils/schemaValidator.js`

---

## Differentiation Standards

Each project must have **3-5 unique features** beyond basic template:

1. At least 3 from trending features registry
2. Industry-specific implicit features (specs for electronics, size guide for fashion)
3. Premium design system injection (Tailwind tokens, glow effects)
4. Competitive positioning documented in generation report

---

## Accessibility Standards

- All interactive elements keyboard accessible
- Icons paired with text labels in navigation
- Color contrast ratio ≥ 4.5:1
- Form inputs have associated labels
- Focus indicators visible
- ARIA labels on icon-only buttons

---

## Deployment Standards

Generated projects include `INSTRUCTIONS.md` with:

1. Environment setup (`.env` from `.env.example`)
2. Database migration steps
3. Frontend: `npm install && npm run dev`
4. Backend: `npm install && npm start`
5. Production build: `npm run build`
6. Recommended hosting (Vercel + Railway)

---

## Validation Checklist

Before marking `enterprise_ready: true`:

- [ ] `validation_results.valid === true`
- [ ] `quality_gates.overall_score >= 80`
- [ ] `quality_gates.gates.features.passed === true`
- [ ] `quality_gates.gates.assets.passed === true`
- [ ] `quality_gates.gates.differentiation.passed === true`
- [ ] `competitive_benchmark.launch_ready === true`
