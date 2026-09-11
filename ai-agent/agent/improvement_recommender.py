from typing import Dict, Any, List
from utils.logger import agent_logger


class ImprovementRecommender:
    """Phase 8 — ROI-ranked improvement recommendations calibrated to
    international market standards (2025-2026).
    Covers performance, security, SEO, conversion, retention, legal, DevOps, and growth.
    """

    # ── Full international improvement catalog (25 items) ─────────────────
    IMPROVEMENT_CATALOG = [
        # Performance
        {"id": "perf_images_webp",      "title": "Optimize images: WebP + lazy loading + AVIF fallback",  "roi": 96, "effort_hours": 2,  "category": "performance", "international_priority": True},
        {"id": "perf_code_split",       "title": "Route-based code splitting + dynamic imports",            "roi": 88, "effort_hours": 3,  "category": "performance", "international_priority": True},
        {"id": "perf_core_web_vitals",  "title": "Optimize Core Web Vitals (LCP < 2.5s, CLS < 0.1, FID < 100ms)", "roi": 93, "effort_hours": 4, "category": "performance", "international_priority": True},
        {"id": "perf_cdn",              "title": "Deploy static assets to CDN (Cloudflare / Vercel Edge)",  "roi": 90, "effort_hours": 2,  "category": "performance", "international_priority": True},
        # SEO
        {"id": "seo_structured_data",   "title": "Add JSON-LD structured data (Product, Organization, FAQ, Review schema)", "roi": 85, "effort_hours": 3, "category": "seo", "international_priority": True},
        {"id": "seo_sitemap_robots",    "title": "Generate sitemap.xml + robots.txt + canonical URLs",     "roi": 80, "effort_hours": 1,  "category": "seo", "international_priority": True},
        {"id": "seo_hreflang",          "title": "Add hreflang tags for multilingual/multi-region support", "roi": 78, "effort_hours": 2,  "category": "seo", "international_priority": True},
        {"id": "seo_meta_og",           "title": "Complete Open Graph + Twitter Card meta tags per page",   "roi": 76, "effort_hours": 2,  "category": "seo", "international_priority": True},
        # Security
        {"id": "sec_audit_owasp",       "title": "Run OWASP Top 10 security audit",                        "roi": 92, "effort_hours": 4,  "category": "security", "international_priority": True},
        {"id": "sec_2fa",               "title": "Add two-factor authentication (TOTP + SMS)",              "roi": 82, "effort_hours": 6,  "category": "security", "international_priority": False},
        {"id": "sec_rate_limit",        "title": "Implement API rate limiting + DDoS protection headers",   "roi": 88, "effort_hours": 2,  "category": "security", "international_priority": True},
        # Conversion
        {"id": "conv_social_proof",     "title": "Add live social proof notifications (recent purchases/signups)", "roi": 91, "effort_hours": 4, "category": "conversion", "international_priority": True},
        {"id": "conv_whatsapp",         "title": "Add WhatsApp floating chat button (3-5x better than contact forms)", "roi": 94, "effort_hours": 1, "category": "conversion", "international_priority": True},
        {"id": "conv_exit_intent",      "title": "Exit-intent popup with lead magnet or discount offer",   "roi": 87, "effort_hours": 3,  "category": "conversion", "international_priority": True},
        {"id": "conv_countdown",        "title": "Add urgency countdown timer for limited-time offers",     "roi": 86, "effort_hours": 2,  "category": "conversion", "international_priority": False},
        # PWA & Mobile
        {"id": "pwa_install",           "title": "Progressive Web App (offline, install prompt, push notifications)", "roi": 91, "effort_hours": 4, "category": "pwa", "international_priority": True},
        {"id": "mobile_ux",             "title": "Audit and improve mobile UX (tap targets, font sizes, viewport)", "roi": 89, "effort_hours": 3, "category": "performance", "international_priority": True},
        # Payments
        {"id": "pay_stripe",            "title": "Integrate Stripe Payments (cards, Apple Pay, Google Pay)", "roi": 95, "effort_hours": 6, "category": "conversion", "international_priority": True},
        {"id": "pay_paypal",            "title": "Add PayPal checkout option (40% of users prefer PayPal)", "roi": 82, "effort_hours": 4,  "category": "conversion", "international_priority": False},
        # Legal / Compliance
        {"id": "legal_gdpr_cookie",     "title": "GDPR/CCPA compliant cookie consent banner",               "roi": 83, "effort_hours": 2,  "category": "legal", "international_priority": True},
        {"id": "legal_privacy_policy",  "title": "Add Privacy Policy + Terms of Service pages",             "roi": 75, "effort_hours": 2,  "category": "legal", "international_priority": True},
        # Growth
        {"id": "growth_newsletter",     "title": "Email newsletter integration (Mailchimp/Klaviyo)",        "roi": 81, "effort_hours": 3,  "category": "growth", "international_priority": True},
        {"id": "growth_ab_testing",     "title": "A/B testing setup (Google Optimize / Posthog)",           "roi": 84, "effort_hours": 5,  "category": "growth", "international_priority": False},
        # DevOps / Monitoring
        {"id": "ops_monitoring",        "title": "Set up error monitoring with Sentry + uptime alerts",     "roi": 82, "effort_hours": 2,  "category": "ops", "international_priority": True},
        {"id": "ops_cicd",              "title": "Add GitHub Actions CI/CD pipeline for automated deploys",  "roi": 87, "effort_hours": 3,  "category": "ops", "international_priority": True},
    ]

    def recommend(
        self,
        spec: Dict[str, Any],
        quality_report: Dict[str, Any],
        validation_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate prioritized improvement recommendations for international market."""
        agent_logger.info("Phase 8: Generating international ROI-ranked improvement recommendations...")

        existing = set(spec.get("features", [])) | set(spec.get("trending_features", []))
        website_type = spec.get("website_type", "ecommerce")
        industry = spec.get("industry", "general")
        recommendations: List[Dict[str, Any]] = []

        gates = quality_report.get("gates", {})
        perf_passed = gates.get("performance", {}).get("passed", False)
        sec_passed  = gates.get("security", {}).get("passed", False)

        for item in self.IMPROVEMENT_CATALOG:
            include = False
            reason = ""

            # Performance gate failures
            if not perf_passed and item["category"] == "performance":
                include = True
                reason = "Performance gate not fully passed"

            # Security gate failures
            if not sec_passed and item["category"] == "security":
                include = True
                reason = "Security gate needs improvement"

            # Always include international priorities for non-local deployments
            if item.get("international_priority") and item["id"] not in existing:
                include = True
                reason = reason or "International market requirement"

            # Missing high-ROI features
            if item["roi"] >= 88 and item["id"] not in existing:
                include = True
                reason = reason or f"High ROI opportunity ({item['roi']})"

            # Industry-specific
            ecommerce_pay = website_type in ("ecommerce",) and item["id"] in ("pay_stripe", "pay_paypal")
            if ecommerce_pay:
                include = True
                reason = "E-commerce payment gateway required"

            # Validation warnings → monitoring
            if len(validation_report.get("warnings", [])) > 5 and item["category"] == "ops":
                include = True
                reason = "Multiple validation warnings detected"

            if include:
                roi_effort = round(item["roi"] / max(item["effort_hours"], 1), 2)
                recommendations.append({**item, "reason": reason, "roi_effort_ratio": roi_effort})

        # Deduplicate and sort by ROI/effort ratio
        seen = set()
        unique = []
        for r in recommendations:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique.append(r)
        unique.sort(key=lambda x: x["roi_effort_ratio"], reverse=True)
        top = unique[:10]

        result = {
            "total_recommendations": len(top),
            "recommendations": top,
            "estimated_total_hours": sum(r["effort_hours"] for r in top),
            "priority_order": [r["id"] for r in top],
            "international_compliance": {
                "gdpr_ready": any(r["id"] == "legal_gdpr_cookie" for r in top),
                "pwa_ready":  any(r["id"] == "pwa_install" for r in top),
                "seo_ready":  any(r["id"].startswith("seo_") for r in top),
            },
        }
        agent_logger.info(f"Generated {len(top)} improvement recommendations (international profile).")
        return result
