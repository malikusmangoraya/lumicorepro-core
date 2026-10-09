# The Unique Project Playbook

**Audience:** anyone generating or hand-building a website with LumicorePro who
wants it to look *designed*, not generated.
**Scope:** the exact levers that make a project one-of-a-kind — brand identity,
layout, animation, content — plus the quality gates that judge them and the
file in this repo where each lever lives.
**Time:** ~15 minutes to read; keep it open as a reference afterwards.

---

## 1. What "unique" means here (and what it doesn't)

Unique ≠ different for its own sake. Two tests decide it:

1. **The cover test** — could a competitor swap their logo onto this page and
   nobody notice? If yes, the page is generic no matter how many effects it has.
2. **The inventory test** — name five specific decisions (palette, type
   pairing, layout device, motion signature, imagery treatment) that no other
   project in your fleet shares. Fewer than five = not unique.

Anti-generic rules (these are enforced, not aspirational — see DesignLint in §7):

- No gratuitous glassmorphism, gradient text, floating glow, particles, blur
  or parallax. Every decorative element must justify itself with hierarchy,
  storytelling, interaction, emotion or usability — or be removed.
- Never reuse one visual formula on every project.
- Clearer hierarchy, stronger brand and better UX beat more effects every time.

## 2. The pipeline in one screen

```
Prompt → Business Analysis → Audience → Brand → Reference intelligence
       → Industry playbook → UX/IA → Visual direction → Design system
       → design-manifest.json → Build → QA (DesignLint + critics)
       → Visual scoring → Self-heal → Deploy → Final report
```

The key idea: **uniqueness is decided before code, in the manifest.**
Everything downstream is the execution of a decision you can inspect and
change. Decisions are stored step by step in `.artifacts/01-business.json`
through `14-deployment`, so a later "change the hero" request is an edit, not
archaeology. The manifest writer is `ai-agent/agent/orchestrator.py`.

Reference inputs (Apple-style clarity, Aesop-style restraint, Stripe-style
UX…) are **decomposed into attributes**, never copied: typography rhythm,
spacing, navigation behaviour, image treatment, motion principles, content
density, CTA hierarchy, brand emotion — then synthesized into an original
system. Reference = inspiration attributes, not template extraction.

## 3. Design identity — the four foundations

### 3.1 Color

- **Semantic tokens only.** No raw hex in components. Brand colors live in
  `tailwind.config.js` and `src/styles/globals.css` as `--t-primary`,
  `--t-accent`, `--t-brand` style tokens; components consume the tokens.
- One brand hue + one accent, chosen against the industry's emotional
  baseline (the selection runs through `theme_matrix.py` and
  `design_intelligence.py`).
- **Dark mode is designed, not inverted** — every color is picked for both
  themes (`dark:` prefix is required on utility classes).

### 3.2 Typography

- **Max 2–3 families** (display + text, plus mono only for dev-tool brands).
- One deliberate scale (ratio-based), measure capped around 100 characters,
  `font-display: swap` so text never hides behind font loads.
- The type pairing is the strongest uniqueness lever per byte: two sites
  with the same palette but different type read as different brands.

### 3.3 Logo and brand marks

- **Never plain text.** Logos are dynamic vector SVGs (`UniqueLogo` /
  `BrandLogo`) built from a geometric symbol plus a dual-color gradient.
- One mark, one gradient recipe, reused everywhere (nav, footer, og:image,
  email) — consistency is scored (§7).

### 3.4 Imagery

- Real, curated, high-resolution photographs loaded through `LazyImage`
  with meaningful `alt`. No placeholders, no stock illustrations pretending
  to be product shots.
- A consistent treatment — crop ratio, duotone or none, border radius — is
  half of the style signature. Pick the treatment once; apply it everywhere.

## 4. Layout and anatomy — structure as a signature

### 4.1 The default long-form home

```
hero → proof strip → problem reframe → features → personas → stats
     → testimonial → pricing teaser → FAQ accordion → final CTA
```

This 10-part anatomy is what the fleet audit
(`scripts/audit_international_anatomy.py`) expects from generated homes.

**Uniqueness lever: reorder, merge or drop sections for the industry.** A
portfolio does not need a pricing teaser; a product launch can go
hero → live demo → proof → pricing. Structure is visible before color or
type is even noticed.

### 4.2 Layout devices — pick 1–2 per project, never all

| Device | Component / technique | Suits |
|---|---|---|
| Bento grid | `BentoGrid` | product ecosystems, dashboards |
| Editorial split | asymmetric 2-column + pull quotes | magazines, agencies, portfolios |
| Sticky scroll narrative | section stacking with `Reveal` | storytelling, case studies |
| Cinematic hero | `HeroCanvas` / `Scene3D` (lazy) | launches, 3D-first brands |
| Density-varied card grid | card sizes mixed on one grid | marketplaces, catalogs |

3D is **optional**: use it only when it improves understanding, emotion or
value. Otherwise video / editorial / typographic / UI-preview heroes win —
they are faster and often more distinctive. Always provide a mobile and
`prefers-reduced-motion` fallback; never ship a zero-height canvas.

### 4.3 Responsive intent, 320 → 1920 px

- Mobile is a redesign, not a shrink: the mobile hero must not eat the
  whole first screen, and the CTA must be visible without a long scroll.
- One spacing rhythm across breakpoints (spacing inconsistency is a
  DesignLint finding, DL004).
- Explicitly test 375 / 768 / 1024 / 1440 / 1920 — and reduced-motion.

## 5. Animation and motion — the motion signature

### 5.1 What you have

All motion components live in `src/components/motion/`:

`BentoGrid`, `BorderBeam`, `CyberGridCanvas`, `HeroCanvas`, `HeroSection`,
`HolographicCard`, `MagneticButton`, `ParticleField3D`, `Reveal`, `Scene3D`,
`SpotlightGrid`, `StaggerGroup`, `TextMorph`.

### 5.2 The rules that make motion feel designed

- **Animate `transform` and `opacity` only** (also the only properties that
  stay smooth under load); standard transitions are
  `transition-all duration-200`.
- **One motion vocabulary per project.** A site using Reveal + MagneticButton
  reads as intentional; a site using all thirteen components reads as a
  demo reel. Repeated, identical animation patterns across sections are a
  DesignLint failure (DL014).
- **Entrance choreography:** `StaggerGroup` for lists, `Reveal` for whole
  sections, `TextMorph` for one hero headline — not ten.
- **Restraint is scored** (motion carries 5% of the visual score with a
  restraint target of 8/10). Absence of gratuitous motion is a feature.
- **`prefers-reduced-motion` is mandatory.** `src/styles/globals.css`
  carries the media query; every effect must degrade to a static, readable
  layout. No flashing above 3 per second; carousels need manual controls.
- **The constraint resolver** is recorded in the manifest: desktop gets
  rich motion, mobile gets the simplified variant, reduced-motion users get
  minimal. Conflicting requirements (lots of animation vs. fast mobile) are
  resolved per context — never silently.

### 5.3 Motion anti-patterns

Scroll-jacked pages, parallax that costs frames, entrance animations that
delay content, motion that hides the CTA, canvas effects that block first
paint. If an animation delays LCP or shifts layout, it goes.

## 6. Choosing a direction — the registries

- **Style registry:** `ai-agent/agent/design_style.py` — every entry has an
  `id`, a `name`, a `dna` (what the style *is*) and `best_for` (which
  industries fit it). 30 ids are registered as of 2026-10-06, including
  `minimalism`, `glassmorphism`, `neo_brutalism`, `bento_grid`,
  `neumorphism`, `flat_design`, `claymorphism`, `skeuomorphism`,
  `corporate_memphis`, `editorial`, `swiss`, `aurora`, `organic`,
  `retro_futurism`, `maximalism`, `collage`, `vector`, `futuristic`,
  `handwritten`, `bohemian`, `graffiti`, `victorian`, `pixel_art`,
  `pop_art`, `surreal`, plus motion-forward ones like `animaster`
  (kinetic typography + magnetic buttons), `skipper` (spotlight grids +
  dark bento for devtools) and `vengeance` (cyber-brutalism for
  gaming/crypto). Examples: pick a `skipper` for an API platform and a
  `bohemian` editorial for a bakery and nothing overlaps.
- **Brand playbooks:** luxury, minimal, futuristic, editorial, playful,
  corporate, bold — each tunes typography, spacing, motion and imagery.
- **Industry playbooks:** ecommerce, marketplace, saas, automotive, food,
  fintech, portfolio, education, healthcare, real-estate, electronics,
  industrial, hospitality, entertainment, sports, fashion.
- Selection runs through `theme_matrix.py` and `design_vault.py`; a human
  can override it with the `design_style` parameter on
  `generate_website` / `POST /api/generate`.

## 7. The gates that judge uniqueness

### DesignLint (DL001–DL015)

Automated rules with severity (P1–P3): wide hero heading, low CTA contrast,
more than four identical cards, spacing inconsistency, too many rounded
containers, too many gradients, repeated decorative effects, broken heading
hierarchy, tall mobile hero, CTA below the fold, density too high, empty
section, placeholder copy, repeated animation pattern, brand differentiation
too low. Findings feed the self-healing loop — they are work items, not
decoration.

### Visual scoring (measurable, not taste)

```
Typography 15% + Composition 15% + Spacing 15% + Color 10% +
Imagery 10% + Hierarchy 10% + Consistency 10% + Brand fit 10% +
Motion 5% + Originality 10%                       = 100
```

Score bands: **Standard 80+**, **Premium 88+**, **Signature 92+**.

### Rules of evidence

- The builder never grades its own work; independent critics judge only
  real artifacts (screenshots, DOM, network timings, audit output).
- A pass badge requires the check to have actually run; otherwise the
  report says "not measured".
- After every fix, re-verify all five breakpoints plus reduced-motion and
  compare before/after evidence — a fix that breaks another viewport is
  itself a bug.

## 8. Content — the words are part of the design

- Brand voice is a manifest decision; copy is written for the persona, not
  the template. Placeholder or lorem copy is a DesignLint failure (DL013).
- Per-industry content (problem reframe, personas, pricing, FAQ) is
  hand-authored per brand in `scripts/brand_content.py` for the fleet and
  generated per prompt for single runs.
- **i18n, RTL and currency are design constraints, not translations:**
  German runs ~30% longer than English (test truncation), RTL flips every
  arrow and chevron and uses logical CSS properties, and currency formatting
  goes through `CurrencyContext` with real numbers.

## 9. Fast is part of unique — performance as a design constraint

A "premium" design that loads slowly reads as cheap. The budgets are
enforced:

| Gate | Command | Limit |
|---|---|---|
| Initial JS / CSS / largest chunk | `npm run size` | <200 KB / <50 KB / <300 KB gzip (targets: 150/30) |
| Core Web Vitals | `npm run test:perf` | Lighthouse 95+, LCP <1.5 s, **CLS <0.1 hard limit** |

Rules that keep a design fast: lazy-route pages with `React.lazy`,
lazy-load heavy canvases (Three.js, Lottie) behind idle or interaction,
`loading="lazy"` below the fold, window lists above 100 items, debounce
inputs 300 ms, and remember that naming a large lazily-reachable package in
`manualChunks` hoists it onto first paint — it defeats the lazy boundary.

Accessibility is non-negotiable inside any style: 4.5:1 text contrast
(DL002 fires on weak CTA contrast), visible focus, landmarks, labels, and
keyboard paths for every interaction.

## 10. Recipe: two same-industry projects that look unrelated

Differ on **five or more** of: hue + type pairing, layout device, motion
vocabulary, imagery treatment, section order, card geometry, hero
composition.

Example — two fintech sites in one fleet:

| Decision | Site A | Site B |
|---|---|---|
| Style | `swiss` — editorial light | `skipper` — dark bento |
| Palette | paper white, single ink accent | obsidian, one neon accent |
| Type | grotesk display + serif body | mono display + neutral sans |
| Layout | asymmetric editorial splits | spotlight bento grid |
| Motion | `Reveal` only, almost static | `BorderBeam` + `StaggerGroup` |
| Hero | typographic, no image | UI-preview card with beam |

Same industry, zero visual overlap — and both pass the same gates.

## 11. File map — where every lever lives

| Lever | File |
|---|---|
| Style registry (dna + best_for) | `ai-agent/agent/design_style.py` |
| Design intelligence / competitive benchmark | `ai-agent/agent/design_intelligence.py`, `competitive_benchmark.py` |
| Theme matrix / design vault | `ai-agent/agent/theme_matrix.py`, `design_vault.py` |
| Plan + manifest + memory | `ai-agent/agent/planner.py`, `orchestrator.py`, `memory_retriever.py`, `.artifacts/` |
| Scoring and gates | `ai-agent/agent/quality_gate.py`, `quality_gates.py`, `vision_pipeline.py` |
| Iteration / self-heal / restyle | `ai-agent/agent/iterate_engine.py`, `enterprise_repair.py`, `restyle_all.py` |
| Motion components | `src/components/motion/` |
| Design tokens | `tailwind.config.js`, `src/styles/globals.css` |
| Fleet anatomy audit | `scripts/audit_international_anatomy.py` |
| Bundle budget | `scripts/check-bundle-budget.mjs` |
| Sibling docs | `OPENSOURCE_ALTERNATIVES`, `WEBSITE_GENERATOR_COMPARISON`, `PRODUCT_MANUAL` |

## 12. Checklists

**Before build (manifest review)**

- [ ] Style id chosen with a stated `dna` reason, not "looked nice"
- [ ] Palette: brand + accent as tokens, dark theme designed, contrast ≥ 4.5:1
- [ ] Type: ≤ 3 families, scale fixed, `font-display: swap`
- [ ] Layout: 1–2 devices, section order fits the industry
- [ ] Motion: one vocabulary, reduced-motion fallback defined
- [ ] Imagery: treatment decided, real images, alt text plan
- [ ] Constraint resolver recorded (desktop / mobile / reduced-motion)

**Before declaring Signature (92+)**

- [ ] Cover test and inventory test both pass (§1)
- [ ] DesignLint: no P1 findings open
- [ ] All five breakpoints + reduced-motion verified with before/after evidence
- [ ] `npm run size` green; `npm run test:perf` green (CLS hard limit)
- [ ] A11y: contrast, focus, landmarks, keyboard paths audited
- [ ] Copy: no placeholders, i18n/RTL expansion checked
- [ ] Critics judged artifacts, not intentions

---

Next: [Product Manual](./PRODUCT_MANUAL.md) for operations ·
[Open-Source Alternatives](./OPENSOURCE_ALTERNATIVES.md) for what's wired in.
