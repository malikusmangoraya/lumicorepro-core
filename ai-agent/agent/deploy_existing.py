"""Batch deploy the 7 existing generated projects to GitHub Pages."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_deploy import deploy

ROOT = Path(__file__).resolve().parents[2]
GP = ROOT / "generated-projects"

PROJECTS = [
    {
        "dir": GP / "generated-website",
        "repo": "nexa-marketplace",
        "name": "Nexa Market",
        "tagline": "Multi-vendor marketplace platform with AI recommendations, live tracking and multi-currency checkout.",
        "category": "Marketplace / SaaS",
        "features": [
            "Multi-vendor storefronts with live inventory sync",
            "AI-powered product recommendations",
            "Secure Stripe payments + multi-currency",
            "Order tracking with real-time notifications",
            "Vendor dashboard with analytics & payouts",
            "i18n (14 languages) + RTL support",
        ],
    },
    {
        "dir": GP / "generated-website-002",
        "repo": "verapay-fintech",
        "name": "VeraPay",
        "tagline": "Fintech payments & banking platform with budgeting, transfers and investment tracking.",
        "category": "Fintech / SaaS",
        "features": [
            "Digital wallet with instant transfers",
            "Budgeting & spend analytics dashboards",
            "Investment portfolio tracking",
            "Role-based access + audit logs",
            "Bank-grade JWT security with rate limiting",
            "Multi-currency + 14-language i18n",
        ],
    },
    {
        "dir": GP / "generated-website-003",
        "repo": "edulify-lms",
        "name": "Edulify LMS",
        "tagline": "EdTech learning management system with AI tutoring, course marketplace and adaptive learning.",
        "category": "EdTech / SaaS",
        "features": [
            "AI-powered personalized tutoring assistant",
            "Course marketplace with enrollments",
            "Adaptive learning paths & progress tracking",
            "Quiz engine with instant grading",
            "Instructor dashboard with analytics",
            "RTL + 14-language support",
        ],
    },
    {
        "dir": GP / "generated-website-004",
        "repo": "telecare-health",
        "name": "Telecare Health",
        "tagline": "Telemedicine platform connecting patients with doctors via video consults and AI triage.",
        "category": "HealthTech / SaaS",
        "features": [
            "Video consultations with live scheduling",
            "AI symptom triage assistant",
            "Digital health records (EHR)",
            "Prescription management",
            "HIPAA-aware access controls",
            "Multi-language patient portal",
        ],
    },
    {
        "dir": GP / "generated-website-005",
        "repo": "realspace-estate",
        "name": "RealSpace",
        "tagline": "Real estate platform with property listings, virtual tours, mortgage calculators and agent CRM.",
        "category": "Real Estate / SaaS",
        "features": [
            "Property listings with photo galleries",
            "Virtual tour embeds per property",
            "Mortgage & ROI calculators",
            "Agent CRM with lead management",
            "Interactive map-based search",
            "RTL + international listings",
        ],
    },
    {
        "dir": GP / "generated-website-006",
        "repo": "marketsphere",
        "name": "MarketSphere",
        "tagline": "Global marketplace for digital goods with instant delivery, reviews and seller analytics.",
        "category": "Marketplace / E-commerce",
        "features": [
            "Digital product storefronts",
            "Instant delivery + license keys",
            "Reviews, ratings & seller analytics",
            "Secure checkout with multi-currency",
            "Coupons, bundles & affiliate tracking",
            "i18n + RTL dashboards",
        ],
    },
    {
        "dir": GP / "generated-website-007",
        "repo": "storefront-pro",
        "name": "StoreFront Pro",
        "tagline": "Headless e-commerce storefront with live cart, real-time inventory and full admin control.",
        "category": "E-commerce / SaaS",
        "features": [
            "Headless catalog with GraphQL-ready API",
            "Live cart with optimistic updates",
            "Real-time inventory & stock alerts",
            "Full admin panel (products/orders/customers)",
            "SEO + JSON-LD product schema",
            "14-language i18n + RTL checkout",
        ],
    },
]


def main():
    results = []
    for p in PROJECTS:
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

    print("\n===== DEPLOYMENT SUMMARY =====")
    for repo, name, url in results:
        print(f"{name:20s} {repo:22s} {url}")


if __name__ == "__main__":
    main()