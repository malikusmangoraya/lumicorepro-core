#!/usr/bin/env python
"""LumicorePro Build Campaign: 10 trending luxury full-stack projects.

Runs the AgentOrchestrator for each brief (real provider chain, real npm builds),
verifies feature completeness, packages each marketing/seller kit and writes a
single campaign report. Resume-safe: completed projects are skipped.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-agent"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("campaign")

BRIEFS = [
    {
        "id": "campaign-01",
        "slug": "aurelia-estates",
        "brand": "Aurelia Estates",
        "prompt": (
            "Build a luxury international real-estate platform showcasing exclusive villas and penthouses in "
            "Dubai, Paris and Miami. Brand: 'Aurelia Estates' - refined minimal with editorial typography. "
            "Audience: global HNWI investors and expats. Full features: user auth (register/login/reset, JWT), "
            "Stripe payment for viewings and holding deposits, hero with cinematic listing imagery, property "
            "listing grid with filters and bookmarking, agent concierge booking, i18n (English, Arabic, Spanish) "
            "with RTL support, multi-currency (USD, EUR, AED, SAR), WhatsApp float, GDPR consent, cookies "
            "policy, privacy and terms pages, SEO meta + OG + JSON-LD + sitemap, dark luxury theme. "
            "React 19 + Vite + Tailwind, Express + MySQL, structure identical to LumicorePro. "
            "Everything real and production-ready."
        ),
    },
    {
        "id": "campaign-02",
        "slug": "maison-noir",
        "brand": "Maison Noir",
        "prompt": (
            "Build a high-end fashion e-commerce store 'Maison Noir' for designer ready-to-wear with exclusive "
            "drops and a sizing concierge. Audience: international fashion-forward shoppers, GCC and EU. Full "
            "features: auth (register/login/one-time-code, JWT), Stripe checkout with order confirmation, "
            "editorial hero with lookbook, product catalog with filters, size guide, cart and wishlist "
            "(optimistic), i18n (English, Arabic, French) with RTL, multi-currency (USD, EUR, GBP, AED), seo "
            "og json-ld sitemap, privacy/terms/returns, cookie consent, dark theme, motion micro-interactions. "
            "React 19 + Vite + Tailwind, Express + MySQL. Real and production-ready."
        ),
    },
    {
        "id": "campaign-03",
        "slug": "ember-salt",
        "brand": "Ember & Salt",
        "prompt": (
            "Build a luxury fine-dining restaurant site 'Ember & Salt' with reservations, private dining and "
            "premium takeout. Audience: destination diners in London, Dubai and NYC. Features: auth (register/"
            "login, JWT), Stripe payments for reservation deposits and gift cards, cinematic hero with chef "
            "storytelling, menu with dietary flags, chef's table booking, i18n (English, Arabic, Spanish) RTL, "
            "multi-currency (USD, GBP, EUR, AED), reservation management dashboard, GDPR, privacy/terms, hours "
            "block with world clock, map embed, SEO. React 19 + Vite + Tailwind, Express + MySQL. Real."
        ),
    },
    {
        "id": "campaign-04",
        "slug": "saffron-voyage",
        "brand": "Saffron Voyage",
        "prompt": (
            "Build a luxury travel concierge platform 'Saffron Voyage' for private island villas, chartered "
            "yachts and bespoke itineraries. Audience: high-net-worth travelers. Features: auth (JWT), Stripe "
            "checkout for trip deposits and full bookings, immersive hero with video-like reveal, trip builder "
            "with dates and guests, destination cards, itinerary builder, i18n (English, Arabic, French) RTL, "
            "multi-currency (USD, EUR, AED), compliance pages, SEO + OG + JSON-LD, WhatsApp float, dark luxury "
            "theme. React 19 + Vite + Tailwind, Express + MySQL. Real and production-ready."
        ),
    },
    {
        "id": "campaign-05",
        "slug": "prestige-studio",
        "brand": "Prestige",
        "prompt": (
            "Build a luxury SaaS platform 'Prestige' - AI content studio for luxury brands with campaigns, "
            "brand voice, multi-channel publishing. Audience: global marketing agencies and brand teams. "
            "Features: auth (register/login/2FA-code, JWT+refresh), Stripe subscription billing with tiers and "
            "credits, hero with product mockup, dashboard with analytics and revenue cards, workspace pages, "
            "i18n (English, Spanish, Arabic) RTL, multi-currency (USD, EUR, GBP), privacy/terms, GDPR, SEO, "
            "modern glass-cinematic dark theme. React 19 + Vite + Tailwind, Express + MySQL. Real."
        ),
    },
    {
        "id": "campaign-06",
        "slug": "meridian-capital",
        "brand": "Meridian Capital",
        "prompt": (
            "Build a luxury wealth-management fintech dashboard 'Meridian Capital' with portfolio analytics, "
            "market watch and private banking concierge. Audience: accredited investors globally. Features: "
            "auth with 2FA, JWT, Stripe for advisory billing, dark luxury fintech UI with revenue cards and "
            "charts, portfolio dashboard, watchlists, i18n (English, Arabic, German) RTL, multi-currency (USD, "
            "EUR, AED), compliance (privacy, terms, risk disclaimer), SEO, real-time widget states. React 19 + "
            "Vite + Tailwind, Express + MySQL. Real."
        ),
    },
    {
        "id": "campaign-07",
        "slug": "voltus-atelier",
        "brand": "Voltus Atelier",
        "prompt": (
            "Build a luxury electric vehicle showroom 'Voltus Atelier' for a premium EV brand with a car "
            "configurator and test-drive booking. Audience: affluent car enthusiasts in EU, USA, GCC. Features: "
            "auth (register/login, JWT), Stripe payments for reservations, cinematic hero with 3D-feel car "
            "visuals, configurator with trims/colors/wheels and price update, model lineup, test-drive booking, "
            "i18n (English, Arabic, German) RTL, multi-currency (USD, EUR, AED), trade-in form, privacy/terms, "
            "SEO, dark automotive theme. React 19 + Vite + Tailwind, Express + MySQL. Real."
        ),
    },
    {
        "id": "campaign-08",
        "slug": "aurum-fitness",
        "brand": "Aurum Fitness",
        "prompt": (
            "Build a premium wellness and fitness membership platform 'Aurum Fitness' with elite coaching, "
            "virtual classes and nutrition plans. Audience: health-conscious professionals worldwide. Features: "
            "auth (register/login/one-time-code, JWT), Stripe subscription payments, hero with athlete imagery, "
            "class schedule, coach profiles and booking, nutrition plans, membership tiers with pricing toggle, "
            "progress dashboard, i18n (English, Arabic, Spanish) RTL, multi-currency (USD, EUR, AED), privacy/"
            "terms, cookie consent, SEO, clean premium light+dark theme. React 19 + Vite + Tailwind, Express + "
            "MySQL. Real."
        ),
    },
    {
        "id": "campaign-09",
        "slug": "studio-lumen",
        "brand": "Studio Lumen",
        "prompt": (
            "Build a luxury interior-design studio portfolio 'Studio Lumen' with immersive project galleries "
            "and complimentary consultation booking. Audience: homeowners, architects and developers in North "
            "America, Europe and GCC. Features: auth (JWT), Stripe payments for design retainers, editorial "
            "hero with featured projects, project case studies, services, team, consultation booking flow, "
            "before/after showcase, i18n (English, Arabic, French) RTL, multi-currency (USD, EUR, AED), "
            "privacy/terms, SEO + OG + JSON-LD, map embed, WhatsApp float, sophisticated minimal themed design. "
            "React 19 + Vite + Tailwind, Express + MySQL. Real."
        ),
    },
    {
        "id": "campaign-10",
        "slug": "nuage-events",
        "brand": "Nuage Events",
        "prompt": (
            "Build a luxury wedding and event planning platform 'Nuage Events' for destination weddings across "
            "Lake Como, Bali and Santorini with a curated vendor marketplace. Audience: couples and event "
            "professionals globally. Features: auth (register/login, JWT), Stripe payments for planning "
            "packages and deposits, romantic cinematic hero, packages with pricing toggle, vendor directory "
            "with filters, events gallery, inquiry and booking forms, i18n (English, Arabic, Spanish) RTL, "
            "multi-currency (USD, EUR, AED), privacy/terms, cookie consent, SEO, elegant serif + soft palette "
            "design. React 19 + Vite + Tailwind, Express + MySQL. Real and production-ready."
        ),
    },
]

REQUIRED_FILES = [
    ("auth", ["login", "register"]),
    ("payment", ["stripe"]),
    ("i18n", ["i18n"]),
    ("compliance", ["privacy", "terms"]),
    ("seo", ["sitemap", "og", "json-ld"]),
]


def verify_project(project_dir: Path) -> dict:
    """Objective feature checks across the generated project."""
    report = {}
    files = [p.name.lower() for p in project_dir.rglob("*") if p.is_file()]

    def has_any(tokens, names):
        return any(any(t in n for t in tokens) for n in names)

    report["auth"] = has_any(["login", "register"], files)
    report["payment"] = any("stripe" in f for f in files) or has_any(["checkout"], files)
    report["hero"] = has_any(["hero"], files)
    report["i18n"] = any("i18n" in f or f.endswith((".json")) and "en" in f for f in files)
    report["rtl"] = any(f == "rtl.css" or "rtl" in f for f in files)
    report["currency"] = has_any(["currency"], files)
    report["compliance"] = has_any(["privacy"], files) and has_any(["terms"], files)
    report["seo"] = has_any(["sitemap"], files) or has_any(["og"], files) or has_any(["json-ld", "seo"], files)
    for root in (project_dir, project_dir / "frontend", project_dir / "public"):
        if root.exists():
            report["index_html"] = report.get("index_html") or (root / "index.html").exists() or bool(root.rglob("index.html"))
            break
    report["package_json"] = (project_dir / "frontend" / "package.json").exists() or (project_dir / "package.json").exists()
    report["dist"] = (project_dir / "frontend" / "dist").exists() or (project_dir / "dist").exists()
    return report


def build_one(brief: dict, out_root: Path, progress_log: Path):
    from agent.orchestrator import AgentOrchestrator

    def cb(phase, event, meta):
        with progress_log.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {brief['id']} | {phase} | {event}\n")
        log.info("%s | %s | %s", brief["id"], phase, event)

    orch = AgentOrchestrator()
    res = orch.run(
        brief["prompt"],
        interactive=False,
        progress_callback=cb,
        extra_spec={
            "project_name": brief.get("slug", brief["id"]),
            "project_name_human": brief.get("brand", ""),
            "brand_name": brief.get("brand", ""),
            "company_name": brief.get("brand", ""),
        },
    )
    with progress_log.open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {brief['id']} | DONE | {json.dumps({k: v for k, v in res.items() if k in ('project_name','project_path','quality','score','design_score','status')})}\n")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="build only first N briefs (0 = all)")
    ap.add_argument("--ids", default="", help="comma-separated brief ids to build")
    ap.add_argument("--offline", action="store_true", help="force offline provider (no AI)")
    args = ap.parse_args()

    out_root = ROOT / "generated-projects"
    out_root.mkdir(exist_ok=True)
    state_file = out_root / "campaign-results.json"
    log_file = out_root / "campaign-progress.log"

    briefs = BRIEFS
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",") if x.strip()}
        briefs = [b for b in briefs if b["id"] in wanted]
    elif args.limit:
        briefs = briefs[: args.limit]

    results = {}
    if state_file.exists():
        results = json.loads(state_file.read_text(encoding="utf-8"))

    log.info("CAMPAIGN START: %d brief(s), offline=%s", len(briefs), args.offline)
    for brief in briefs:
        if results.get(brief["id"], {}).get("status") == "complete":
            log.info("skip %s (already complete)", brief["id"])
            continue
        started = time.time()
        try:
            res = build_one(brief, out_root, log_file)
            name = res.get("project_name", brief["id"])
            pdir = out_root / name
            checks = verify_project(pdir)
            seller_kit = None
            try:
                from agent.extensions.marketing_kit import generate_marketing_kit
                kit = generate_marketing_kit(str(pdir))
                if isinstance(kit, dict):
                    seller_kit = kit.get("zip_path") or kit.get("path")
            except Exception as exc:  # noqa: BLE001 - optional
                log.warning("%s seller kit failed: %s", brief["id"], exc)
            results[brief["id"]] = {
                "status": "complete",
                "project_name": name,
                "prompt": brief["prompt"][:120],
                "features": checks,
                "checks_passed": sum(1 for v in checks.values() if v),
                "checks_total": len(checks),
                "seller_kit": seller_kit,
                "elapsed_s": round(time.time() - started),
                "score": res.get("score") or res.get("quality") or res.get("design_score"),
            }
            state_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info("%s DONE in %ds | project=%s | checks %s/%s", brief["id"], results[brief["id"]]["elapsed_s"], name, results[brief["id"]]["checks_passed"], len(checks))
        except Exception as exc:  # noqa: BLE001 - keep campaign alive
            results[brief["id"]] = {"status": "error", "error": repr(exc), "elapsed_s": round(time.time() - started)}
            state_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log.error("%s FAILED: %s", brief["id"], exc)

    summary = {"total": len(results), "ok": sum(1 for r in results.values() if r.get("status") == "complete")}
    state_file.write_text(json.dumps({"summary": summary, "projects": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("CAMPAIGN SUMMARY: %s", summary)
    print("CAMPAIGN RESULT:", json.dumps(summary))


if __name__ == "__main__":
    main()