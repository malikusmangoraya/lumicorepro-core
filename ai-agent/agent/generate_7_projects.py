"""Generate 7 new high-demand projects sequentially via the orchestrator."""
import io
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agent"))

os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agent.orchestrator import AgentOrchestrator  # noqa: E402

PROJECTS = [
    {
        "name": "ai-content-studio",
        "prompt": ("Build an AI-powered content studio SaaS: blog writer, social captions, "
                   "SEO meta generator, brand voice presets, team workspaces, and an AI chatbot. "
                   "Monetization via subscription plans and credits."),
        "spec": {
            "website_type": "saas",
            "industry": "ai",
            "features": ["hero", "pricing", "features", "dashboard", "contact", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
    {
        "name": "fooddelivery-express",
        "prompt": ("Build a food delivery platform: restaurant catalog, live order tracking, "
                   "courier dispatch, ratings, promo codes, and admin/vendor analytics. "
                   "i18n with RTL for MENA and multi-currency checkout."),
        "spec": {
            "website_type": "marketplace",
            "industry": "food",
            "features": ["hero", "catalog", "search", "cart", "dashboard", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
    {
        "name": "travelbook-pro",
        "prompt": ("Build a travel booking platform: hotel search, instant booking, trip dashboard, "
                   "packages, reviews, maps, and loyalty points. Admin panel with occupancy analytics "
                   "and partner payouts."),
        "spec": {
            "website_type": "marketplace",
            "industry": "travel",
            "features": ["hero", "catalog", "search", "booking", "dashboard", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
    {
        "name": "fitnesscoach-go",
        "prompt": ("Build a fitness & wellness SaaS: workout programs, progress tracking, wearable "
                   "sync, nutrition plans, live classes, coach bookings, and subscription monetization."),
        "spec": {
            "website_type": "saas",
            "industry": "health",
            "features": ["hero", "pricing", "features", "dashboard", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
    {
        "name": "jobboard-hirehub",
        "prompt": ("Build a job board & recruitment SaaS: job listings, resume builder, applicant "
                   "tracking, employer dashboards, filters, matching AI, and candidate pipelines."),
        "spec": {
            "website_type": "marketplace",
            "industry": "saas",
            "features": ["hero", "search", "catalog", "dashboard", "pricing", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
    {
        "name": "eventticket-live",
        "prompt": ("Build an event ticketing platform: event creation, seat maps, ticket tiers, "
                   "QR check-in, waitlists, analytics, sponsor areas, and instant payout for organizers."),
        "spec": {
            "website_type": "marketplace",
            "industry": "events",
            "features": ["hero", "catalog", "booking", "dashboard", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
    {
        "name": "cryptovault-pro",
        "prompt": ("Build a crypto portfolio & trading dashboard: multi-exchange sync, portfolio PnL, "
                   "price alerts, watchlists, DeFi staking tracking, tax reports, and institutional-grade "
                   "security with 2FA."),
        "spec": {
            "website_type": "saas",
            "industry": "fintech",
            "features": ["hero", "pricing", "features", "dashboard", "dark_mode"],
            "layout_mode": "enterprise",
        },
    },
]


def main():
    orchestrator = AgentOrchestrator()
    results = []
    for p in PROJECTS:
        name = p["name"]
        start = time.time()
        print(f"\n===== GENERATING {name} =====", flush=True)
        try:
            report = orchestrator.run(p["prompt"], interactive=False, extra_spec=p["spec"])
            dur = round(time.time() - start, 1)
            status = report.get("status", "?")
            project_dir = report.get("generated_project_dir", "")
            zip_path = report.get("zip_archive_path", "")
            quality = report.get("quality_gates", {}).get("overall_score", 0)
            live_url = report.get("live_preview_url", "")
            print(f"[{name}] status={status} quality={quality} time={dur}s zip={zip_path} live={live_url}", flush=True)
            results.append({"name": name, "status": status, "dir": project_dir, "zip": zip_path,
                            "quality": quality, "live_url": live_url, "time": dur})
        except Exception as e:  # noqa: BLE001
            dur = round(time.time() - start, 1)
            print(f"[{name}] FAILED after {dur}s: {e}", flush=True)
            results.append({"name": name, "status": "failed", "dir": "", "zip": "", "quality": 0,
                            "live_url": "", "time": dur, "error": str(e)})

    print("\n===== GENERATION SUMMARY =====", flush=True)
    for r in results:
        print(f"{r['name']:24s} {r['status']:10s} q={r.get('quality', 0)} t={r.get('time', 0)}s "
              f"dir={r.get('dir', '')} zip={r.get('zip', '')}", flush=True)

    out = ROOT / "generated-projects" / "_generation_report.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nReport: {out}", flush=True)


if __name__ == "__main__":
    main()