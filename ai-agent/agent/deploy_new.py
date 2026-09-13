"""Deploy the 7 newly generated projects to GitHub Pages."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_deploy import deploy

ROOT = Path(__file__).resolve().parents[2]
GP = ROOT / "generated-projects"

PROJECTS = [
    {
        "dir": GP / "generated-website-008",
        "repo": "ai-content-studio",
        "name": "AI Content Studio",
        "tagline": "AI-powered content SaaS: blog writer, captions, SEO meta, brand voice presets, workspaces.",
        "category": "AI / SaaS",
        "features": [
            "AI blog writer with 30+ tone presets",
            "Social caption & hashtag generator",
            "SEO meta + schema generator",
            "Brand voice profiles per workspace",
            "Content calendar with team roles",
            "Credit-based subscription billing",
        ],
    },
    {
        "dir": GP / "food-restaurant-001",
        "repo": "fooddelivery-express",
        "name": "Foodley",
        "tagline": "Food delivery platform: restaurant catalog, live order tracking, courier dispatch and analytics.",
        "category": "FoodTech / Marketplace",
        "features": [
            "Restaurant catalog with live menus",
            "Real-time order tracking map",
            "Courier dispatch & batching",
            "Ratings, reviews & promo codes",
            "Vendor + admin analytics dashboards",
            "RTL + multi-currency (MENA ready)",
        ],
    },
    {
        "dir": GP / "tourism-travel-001",
        "repo": "travelbook-pro",
        "name": "TravelBook",
        "tagline": "Travel booking platform: hotel search, instant booking, packages, reviews, maps and loyalty.",
        "category": "Travel / Marketplace",
        "features": [
            "Hotel & package search engine",
            "Instant booking with inventory lock",
            "Trip dashboard & e-tickets",
            "Guest reviews with photos",
            "Loyalty points & referral coins",
            "Partner payout automation",
        ],
    },
    {
        "dir": GP / "edtech-fitness-001",
        "repo": "fitnesscoach-go",
        "name": "FitCoach GO",
        "tagline": "Fitness wellness SaaS: workout programs, progress tracking, nutrition, live classes and bookings.",
        "category": "Health / SaaS",
        "features": [
            "Personalized workout programs",
            "Wearable & step integration",
            "Nutrition plans with macro logs",
            "Live & recorded class library",
            "Coach scheduling & 1:1 sessions",
            "Subscription + membership tiers",
        ],
    },
    {
        "dir": GP / "realestate-realestate-001",
        "repo": "jobboard-hirehub",
        "name": "HireHub",
        "tagline": "Job board & recruitment SaaS: listings, resume builder, ATS, AI matching and candidate pipelines.",
        "category": "HR / SaaS",
        "features": [
            "Job listings with smart filters",
            "Resume builder & career pages",
            "Applicant tracking (ATS) kanban",
            "AI candidate-job matching",
            "Employer dashboards with billing",
            "Role-based recruiting workflows",
        ],
    },
    {
        "dir": GP / "tourism-travel-001-002",
        "repo": "eventticket-live",
        "name": "EventTix",
        "tagline": "Event ticketing platform: events, seat maps, ticket tiers, QR check-in, waitlists and analytics.",
        "category": "Events / Marketplace",
        "features": [
            "Event studio with seat maps",
            "Tiered ticketing & promo codes",
            "QR check-in via mobile",
            "Waitlist & resale marketplace",
            "Organizer payout automation",
            "Live attendance analytics",
        ],
    },
    {
        "dir": GP / "personal-portfolio-001",
        "repo": "cryptovault-pro",
        "name": "CryptoVault",
        "tagline": "Crypto portfolio & trading dashboard: multi-exchange sync, PnL, alerts, watchlists and tax reports.",
        "category": "Fintech / Crypto",
        "features": [
            "Multi-exchange portfolio sync",
            "Real-time PnL and performance",
            "Price alerts & smart watchlists",
            "DeFi staking tracking",
            "Tax report generation (CSV)",
            "2FA + institutional-grade security",
        ],
    },
]


def main():
    results = []
    for p in PROJECTS:
        if not p["dir"].exists():
            print(f"SKIP {p['repo']}: project dir missing")
            results.append((p["repo"], p["name"], "SKIPPED"))
            continue
        try:
            url = deploy(
                project_dir=p["dir"],
                repo_name=p["repo"],
                name=p["name"],
                tagline=p["tagline"],
                category=p["category"],
                features=p["features"],
            )
            results.append((p["repo"], p["name"], url))
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {p['repo']}: {e}")
            results.append((p["repo"], p["name"], ""))

    print("\n===== NEW PROJECT DEPLOYMENT SUMMARY =====")
    for repo, name, url in results:
        print(f"{name:18s} {repo:24s} {url}")


if __name__ == "__main__":
    main()