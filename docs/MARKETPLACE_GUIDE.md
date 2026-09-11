# Marketplace Guide — Selling LumicorePro-Generated Projects (Free Tier Only)

> Companion to `scripts/sell_ready_zip.py` and `scripts/generate_readme.py`.
> Everything here works on the free tier of each platform — no paid plans required.

## 0. Prepare the sell-ready bundle

Before listing anywhere, build the distribution ZIP:

```bash
python scripts/sell_ready_zip.py path/to/generated-project
```

This produces `{project-name}-sell-ready.zip` containing the full source plus:

| Artifact | Purpose |
|----------|---------|
| `LICENSE.md` | End-customer license (usage rights + warranty) |
| `LICENSE-SEAL.md` | Origin proof (generator seal) |
| `README.md` | Auto-generated marketing README |
| `screenshots/` | Drop desktop/mobile previews here |
| `demo-data/` | Drop sample content here |

Regenerate the README on its own with:

```bash
python scripts/generate_readme.py path/to/project         # reads spec.json / generation-report.json
python scripts/generate_readme.py path/to/spec.json --out README.md
```

Capture 3-5 real screenshots (homepage, a key feature, mobile view) in
`webp`/`png` under 5 MB, and place them in `screenshots/` before re-zipping.
Every marketplace below wants at least one strong image — it is the #1
conversion factor.

---

## 1. Gumroad — free to list, commission on sale

**Cost to list: $0.** Gumroad has no monthly plan; you pay only when you sell.

### Fees (2026)
- Direct sales (your own link/storefront): **10% + $0.50** per transaction.
- Discover marketplace sales (buyers find you via Gumroad search): **flat 30%**,
  includes processing.
- Payment processing (on top): Stripe ~2.9% + $0.30, PayPal/Venmo ~3.49% + $0.49.
- High-volume discount: once monthly paid sales pass **$20,000**, new direct
  sales drop to **5% + $0.50** automatically.

### How to list (free tier)
1. Create an account at gumroad.com (email/password, no card required to start).
2. Go to **Products → New Product**.
3. Upload **Content** → file picker → choose `{project-name}-sell-ready.zip`.
4. Price it — for a full code project recommend **$19–$79** depending on depth.
   Optionally enable **Pay what you want** with a minimum.
5. Set a thumbnail, a one-line tagline, and paste the auto-generated README
   description into **Rich text / description**.
6. Fill in **Cover** and leave "Discover" (marketplace) **on** — it is free
   exposure; you just pay the higher 30% fee on those sales.
7. Connect a payout method (bank card) — required once you make a sale.

### Free-tier tips
- Price the ZIP well above the fee floor: a $5 product loses ~21% to fees, a
  $50 product only ~13%.
- Add a discount code (e.g. `LAUNCH20`) from **Discounts** — free of charge.
- Gumroad embeds a sales/analytics dashboard in the free tier; use it instead
  of paying for external analytics.
- License note: your `LICENSE.md` says "paid end-user license" — surface that
  in the product description so buyers know redistribution is restricted.

---

## 2. GitHub — repository listing (free)

A public GitHub repo doubles as the project's permanent home, changelog, and
portfolio proof. GitHub Free includes unlimited public repositories.

### Free-tier limits to respect
- Unlimited **public** repos with full features; unlimited private repos but
  with a reduced feature set.
- **GitHub Pages** for public repos only on the free personal plan.
- GitHub Actions: **2,000 minutes/month** included; unlimited minutes for
  public repos on standard runners.
- GitHub Packages: **500 MB** storage.
- Releases can host binary attachments (e.g. the sell-ready ZIP) — practical
  download storage at no cost under soft limits.

### How to list (free)
1. Create a public repo with **README** + **LICENSE** (pick a template or use
   your `LICENSE.md`). Use `{project-name}` as the repo name.
2. Commit the full source (respect `.gitignore` for `node_modules/`, `dist/`,
   `vendor/`).
3. Add a screenshot preview to the README:
   ```markdown
   <p align="center"><img src="screenshots/dashboard.png" width="800"></p>
   ```
4. Attach the sell-ready ZIP to a **Release** (Releases → Create release →
   tag `v1.0.0` → attach the zip). Buyers can download direct from the release
   page with no hosting cost.
5. Pin the repo on your profile (**Customize your pins**) so it shows as a
   portfolio item.
6. (Optional, free) Publish a one-page marketing site via **GitHub Pages**
   (Settings → Pages → deploy from `main`), pointing visitors to the Gumroad
   link and the release ZIP.

### Free-tier tips
- Keep the README buyer-facing: the auto-generated README already includes
  Features / Tech Stack / Setup / License — add a "Buy license" badge linking
  to Gumroad at the top.
- Enable **Releases** RSS/webhooks so project updates auto-notify watchers.
- Do NOT enable paid plans or private Pages — everything above is free.

---

## 3. Product Hunt — submission guide (free)

Product Hunt is a discovery launchpad, not a store. Posting is **free** — you
pay nothing regardless of upvotes; paid plans only add analytics. Goal: get
developers to your Gumroad link / GitHub repo.

### Free-tier prerequisites
- A free account with a **verified email**.
- One strong **launch image** (1200×900 / 900×1200 recommended).
- A **first comment** drafted (this is where you tell the story). Hunters
  judge products within minutes.

### How to submit (free)
1. Sign in → **Add product** → paste your project name, tagline
   (≤60 chars), and URL (point to the GitHub repo or live demo).
2. Upload the launch gallery image + optional video (free tier allows
   images; videos via YouTube embed).
3. Fill the description — paste the "Features" section from the auto-generated
   README. Keep it benefit-led ("Launch a polished storefront in minutes"),
   not technical.
4. Pick **Topics/Tags** — always add `Developer Tools`, plus `Website`,
   `Productivity`, or `Artificial Intelligence` to match the project.
5. Choose a **launch day** — Tuesday/Wednesday/Thursday perform best.
6. Publish per Product Hunt's schedule (submissions open daily; your launch
   goes live on the chosen day). Free tier supports one active launch slot —
   no paid boosts needed.
7. **On launch day**: post your maker comment, reply to every comment within
   the first hours (this drives the algorithm), and share the launch link
   on X/LinkedIn. Optionally add the launch to your **Topics** feed.

### Free-tier tips
- Launch a **live demo / GitHub Pages site** the same day; hunters click
  through more than they buy.
- Reply fast and thank every commenter — early engagement decides ranking.
- Do NOT buy "Featured" placement or ads on day one; free organic ranking via
  early interaction is usually enough to discover real traffic.

---

## 4. Cross-platform checklist

- [ ] `scripts/sell_ready_zip.py` run — ZIP has LICENSE + README + screenshots
- [ ] `screenshots/` has real webp/png previews (no placeholders)
- [ ] `README.md` regenerated from the final spec
- [ ] GitHub public repo live, release ZIP attached, Pages site (optional)
- [ ] Gumroad product published with ZIP + pricing + Discover enabled
- [ ] Product Hunt product scheduled with image, tags, and maker comment
- [ ] Every mention links Gumroad (sell) and GitHub (show) — never host the
      paid ZIP as a raw public download in the repo

## 5. License reminder

- The sellable ZIP ships `LICENSE.md` (end-user rights) + `LICENSE-SEAL.md`
  (origin proof). Buyers get usage rights, not the right to resell the source.
- Public GitHub repo: keep `LICENSE.md` visible, but do NOT expose the
  sell-ready ZIP as a free raw download in the repo tree — point to Gumroad.
- GitHub releases can hold the ZIP for purchasers; if you make the release
  public, buyers have no reason to pay. Prefer private release drafts or the
  Gumroad-hosted ZIP for the paid artifact.