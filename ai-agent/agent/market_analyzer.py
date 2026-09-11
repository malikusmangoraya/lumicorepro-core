import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import agent_logger
from config.settings import REGISTRY_DIR


class MarketAnalyzer:
    """Phase 1 — Market research, competitor benchmarking, trend analysis, and ROI
    opportunity scoring for 26 industry verticals including Pakistani market context.
    Covers global + PK competitors, mobile-first metrics, and international growth rates.
    """

    INDUSTRY_BENCHMARKS = {
        # ── E-Commerce ──────────────────────────────────────────────────
        "electronics": {
            "competitors": ["Daraz.pk", "iShopping.pk", "Homeshopping.pk", "Amazon", "Best Buy"],
            "trends": ["AI product recommendations", "AR/3D product preview", "Same-day delivery", "EMI financing", "Voice search"],
            "conversion_drivers": ["spec_comparison", "reviews", "price_alerts", "emi_plans", "free_returns"],
            "target_lighthouse": 95, "avg_conversion": "2.8%", "mobile_share": "72%",
            "pk_growth": "+35% YoY", "global_market_size": "$5.8T",
            "roi_opportunities": ["ai_chat_assistant", "pwa_install", "whatsapp_float"],
        },
        "fashion": {
            "competitors": ["Khaadi.com", "Bonanza Satrangi", "ASOS", "Zara", "H&M"],
            "trends": ["Virtual try-on", "Sustainable fashion", "Size AI", "Social commerce", "Live shopping"],
            "conversion_drivers": ["size_guide", "outfit_builder", "free_returns", "wishlist", "style_ai"],
            "target_lighthouse": 93, "avg_conversion": "3.2%", "mobile_share": "78%",
            "pk_growth": "+40% YoY", "global_market_size": "$1.7T",
            "roi_opportunities": ["instagram_shopping", "loyalty_rewards", "exit_intent_popup"],
        },
        # ── Food & Restaurant ────────────────────────────────────────────
        "food": {
            "competitors": ["Foodpanda.pk", "Cheetay.pk", "Careem Food", "Talabat", "Uber Eats"],
            "trends": ["Real-time order tracking", "Ghost kitchens", "Group ordering", "Subscription meals"],
            "conversion_drivers": ["delivery_time", "cuisine_filter", "ratings", "order_tracking", "loyalty_points"],
            "target_lighthouse": 92, "avg_conversion": "4.5%", "mobile_share": "85%",
            "pk_growth": "+48% YoY", "global_market_size": "$900B",
            "roi_opportunities": ["whatsapp_float", "loyalty_rewards", "pwa_install"],
        },
        "restaurant": {
            "competitors": ["Foodpanda.pk", "Cheetay.pk", "Eat.pk", "local chains"],
            "trends": ["QR code menus", "Self-ordering kiosks", "Pre-order with time slots", "Allergy filters"],
            "conversion_drivers": ["delivery_time", "reviews", "menu_photos", "loyalty_cards", "promo_codes"],
            "target_lighthouse": 91, "avg_conversion": "5.0%", "mobile_share": "88%",
            "pk_growth": "+48% YoY", "global_market_size": "$900B",
            "roi_opportunities": ["whatsapp_float", "online_ordering", "reservation_system"],
        },
        # ── Real Estate ──────────────────────────────────────────────────
        "realestate": {
            "competitors": ["Zameen.com", "Graana.com", "Lamudi.pk", "Bayut.com", "Zillow"],
            "trends": ["3D virtual tours", "AI price prediction", "WhatsApp lead capture", "Map-first search"],
            "conversion_drivers": ["verified_listings", "virtual_tours", "easy_contact", "emi_calculator", "area_comparison"],
            "target_lighthouse": 93, "avg_conversion": "1.8%", "mobile_share": "65%",
            "pk_growth": "+22% YoY", "global_market_size": "$326T",
            "roi_opportunities": ["whatsapp_float", "mortgage_calculator", "virtual_tour"],
        },
        # ── Healthcare ───────────────────────────────────────────────────
        "medical": {
            "competitors": ["Oladoc.com", "Marham.pk", "Shifa4U", "DoctorHere.pk", "Zocdoc"],
            "trends": ["Telemedicine", "AI symptom checker", "Digital prescriptions", "Home lab tests"],
            "conversion_drivers": ["verified_doctors", "ratings", "availability", "video_consult", "instant_booking"],
            "target_lighthouse": 94, "avg_conversion": "6.2%", "mobile_share": "80%",
            "pk_growth": "+60% YoY", "global_market_size": "$11.9T",
            "roi_opportunities": ["whatsapp_float", "appointment_reminders", "health_packages"],
        },
        "healthcare": {
            "competitors": ["Oladoc.com", "Marham.pk", "Shifa4U", "DoctorHere.pk", "Practo"],
            "trends": ["Telemedicine", "AI symptom checker", "Digital prescriptions", "Wearables integration"],
            "conversion_drivers": ["verified_doctors", "ratings", "availability", "video_consult", "instant_booking"],
            "target_lighthouse": 94, "avg_conversion": "6.2%", "mobile_share": "80%",
            "pk_growth": "+60% YoY", "global_market_size": "$11.9T",
            "roi_opportunities": ["whatsapp_float", "pwa_install", "appointment_reminders"],
        },
        # ── Fitness ──────────────────────────────────────────────────────
        "gym": {
            "competitors": ["Shapes Gym PK", "Fitness First", "Gold's Gym PK", "ClassPass"],
            "trends": ["AI workout plans", "Wearable sync", "Live stream classes", "Nutrition tracking"],
            "conversion_drivers": ["free_trial", "class_schedule", "trainer_profiles", "flexible_plans"],
            "target_lighthouse": 92, "avg_conversion": "7.0%", "mobile_share": "75%",
            "pk_growth": "+30% YoY", "global_market_size": "$96B",
            "roi_opportunities": ["countdown_timer", "loyalty_rewards", "pwa_install"],
        },
        "fitness": {
            "competitors": ["Shapes Gym PK", "Fitness First", "Gold's Gym", "ClassPass", "Mindbody"],
            "trends": ["AI personal training", "Wearables integration", "Live stream classes", "Nutrition AI"],
            "conversion_drivers": ["free_trial", "class_schedule", "trainer_profiles", "flexible_plans"],
            "target_lighthouse": 92, "avg_conversion": "7.0%", "mobile_share": "75%",
            "pk_growth": "+30% YoY", "global_market_size": "$96B",
            "roi_opportunities": ["video_hero", "countdown_timer", "newsletter_signup"],
        },
        # ── Education ────────────────────────────────────────────────────
        "edtech": {
            "competitors": ["Coursera", "Udemy", "DigiSkills.pk", "NAVTTC", "Coursemology"],
            "trends": ["AI tutoring", "Micro-credentials", "Live cohort learning", "Job placement"],
            "conversion_drivers": ["free_preview", "instructor_rating", "certificate", "job_outcomes"],
            "target_lighthouse": 93, "avg_conversion": "4.2%", "mobile_share": "70%",
            "pk_growth": "+65% YoY", "global_market_size": "$400B",
            "roi_opportunities": ["pwa_install", "newsletter_signup", "certificate_download"],
        },
        "education": {
            "competitors": ["Coursera", "Udemy", "DigiSkills.pk", "edX", "Khan Academy"],
            "trends": ["AI tutoring", "Micro-credentials", "Live cohort learning", "Gamification"],
            "conversion_drivers": ["free_preview", "instructor_rating", "certificate", "job_outcomes"],
            "target_lighthouse": 93, "avg_conversion": "4.2%", "mobile_share": "70%",
            "pk_growth": "+65% YoY", "global_market_size": "$400B",
            "roi_opportunities": ["referral_program", "pwa_install", "live_chat"],
        },
        # ── Travel ───────────────────────────────────────────────────────
        "tourism": {
            "competitors": ["TravelPak.com", "Bookme.pk", "GoTrip.pk", "Airbnb", "Booking.com"],
            "trends": ["AI itinerary builder", "Domestic tourism", "Immersive content", "Group tours"],
            "conversion_drivers": ["early_bird_discount", "flexible_booking", "verified_guides", "photo_gallery"],
            "target_lighthouse": 92, "avg_conversion": "3.5%", "mobile_share": "76%",
            "pk_growth": "+18% YoY", "global_market_size": "$9.5T",
            "roi_opportunities": ["video_hero", "newsletter_signup", "whatsapp_float"],
        },
        "travel": {
            "competitors": ["TravelPak.com", "Bookme.pk", "GoTrip.pk", "Airbnb", "TripAdvisor"],
            "trends": ["AI itinerary builder", "Sustainable travel", "Staycation packages", "Visa assistance"],
            "conversion_drivers": ["early_bird", "flexible_cancellation", "reviews", "price_match"],
            "target_lighthouse": 92, "avg_conversion": "3.5%", "mobile_share": "76%",
            "pk_growth": "+18% YoY", "global_market_size": "$9.5T",
            "roi_opportunities": ["countdown_timer", "video_hero", "newsletter_signup"],
        },
        # ── Portfolio & Creative ─────────────────────────────────────────
        "personal": {
            "competitors": ["Behance", "Dribbble", "GitHub Pages", "LinkedIn"],
            "trends": ["Interactive 3D portfolio", "AI project descriptions", "GitHub integration"],
            "conversion_drivers": ["project_quality", "contact_form", "testimonials", "social_proof"],
            "target_lighthouse": 96, "avg_conversion": "8.0%", "mobile_share": "60%",
            "pk_growth": "+25% YoY", "global_market_size": "$500B freelance",
            "roi_opportunities": ["social_share", "newsletter_signup", "pwa_install"],
        },
        "creative": {
            "competitors": ["Behance", "Dribbble", "99designs", "Toptal", "Upwork"],
            "trends": ["Motion portfolios", "AI-assisted design", "Brand story videos", "Case study depth"],
            "conversion_drivers": ["portfolio_quality", "case_studies", "client_logos", "awards"],
            "target_lighthouse": 94, "avg_conversion": "5.5%", "mobile_share": "65%",
            "pk_growth": "+28% YoY", "global_market_size": "$500B freelance",
            "roi_opportunities": ["video_hero", "social_proof", "live_chat"],
        },
        # ── SaaS & Dashboard ─────────────────────────────────────────────
        "saas": {
            "competitors": ["Stripe", "Notion", "Linear", "Vercel", "Supabase"],
            "trends": ["Usage-based pricing", "AI copilots", "Self-serve onboarding", "Integrations marketplace"],
            "conversion_drivers": ["free_trial", "demo_cta", "case_studies", "pricing_transparency"],
            "target_lighthouse": 96, "avg_conversion": "4.5%", "mobile_share": "42%",
            "pk_growth": "+55% YoY", "global_market_size": "$197B",
            "roi_opportunities": ["pwa_install", "i18n_multilingual", "exit_intent_popup"],
        },
        "dashboard": {
            "competitors": ["Retool", "Metabase", "Grafana", "Power BI"],
            "trends": ["Real-time WebSocket", "AI insights", "Natural language queries"],
            "conversion_drivers": ["performance", "customization", "integrations", "api_access"],
            "target_lighthouse": 95, "avg_conversion": "N/A", "mobile_share": "30%",
            "pk_growth": "+40% YoY", "global_market_size": "$197B",
            "roi_opportunities": ["analytics_dashboard", "live_chat", "pwa_install"],
        },
        # ── Business & Corporate ─────────────────────────────────────────
        "corporate": {
            "competitors": ["Industry leaders", "Clutch top agencies", "local competitors"],
            "trends": ["ESG reporting", "AI chatbot", "Interactive annual reports", "Video backgrounds"],
            "conversion_drivers": ["trust_signals", "client_logos", "team_profiles", "case_studies"],
            "target_lighthouse": 93, "avg_conversion": "5.0%", "mobile_share": "55%",
            "pk_growth": "+20% YoY", "global_market_size": "$500B+ services",
            "roi_opportunities": ["whatsapp_float", "newsletter_signup", "live_chat"],
        },
        # ── Blog & Media ─────────────────────────────────────────────────
        "blog": {
            "competitors": ["Medium", "Substack", "Ghost", "WordPress.com", "Hashnode"],
            "trends": ["AI-assisted writing", "Newsletter monetization", "Podcast integration", "Membership walls"],
            "conversion_drivers": ["content_quality", "newsletter_signup", "social_share", "seo_ranking"],
            "target_lighthouse": 92, "avg_conversion": "3.0%", "mobile_share": "82%",
            "pk_growth": "+15% YoY", "global_market_size": "$600B+ digital media",
            "roi_opportunities": ["newsletter_signup", "pwa_install", "social_share"],
        },
        "media": {
            "competitors": ["Dawn.com", "ARY Digital", "Geo.tv", "The News"],
            "trends": ["Video-first content", "Breaking news push", "Live blogs", "Dark mode"],
            "conversion_drivers": ["content_freshness", "push_notifications", "newsletter", "social_share"],
            "target_lighthouse": 88, "avg_conversion": "2.5%", "mobile_share": "85%",
            "pk_growth": "+20% YoY", "global_market_size": "$600B+ digital media",
            "roi_opportunities": ["pwa_install", "push_notifications", "newsletter_signup"],
        },
        # ── Nonprofit / NGO ──────────────────────────────────────────────
        "nonprofit": {
            "competitors": ["Edhi Foundation", "Akhuwat", "Shaukat Khanum", "GoFundMe", "GlobalGiving"],
            "trends": ["Recurring micro-donations", "Impact transparency", "Volunteer apps", "Social fundraising"],
            "conversion_drivers": ["impact_stats", "trust_badges", "donor_recognition", "easy_donate"],
            "target_lighthouse": 92, "avg_conversion": "4.0%", "mobile_share": "73%",
            "pk_growth": "+10% YoY", "global_market_size": "$2.8T annual giving",
            "roi_opportunities": ["newsletter_signup", "social_share", "whatsapp_float"],
        },
        # ── Events ───────────────────────────────────────────────────────
        "events": {
            "competitors": ["Eventbrite", "Hopin", "Cvent", "Eventify.pk", "Bookme.pk"],
            "trends": ["Hybrid events", "NFT tickets", "AI matchmaking", "On-demand replays"],
            "conversion_drivers": ["countdown_timer", "early_bird", "speaker_lineup", "social_proof"],
            "target_lighthouse": 93, "avg_conversion": "6.0%", "mobile_share": "76%",
            "pk_growth": "+20% YoY", "global_market_size": "$1.5T",
            "roi_opportunities": ["countdown_timer", "newsletter_signup", "video_hero"],
        },
        "event": {
            "competitors": ["Eventbrite", "Hopin", "Cvent", "Eventify.pk"],
            "trends": ["Hybrid events", "NFT tickets", "Live streaming", "On-demand replays"],
            "conversion_drivers": ["countdown_timer", "early_bird_pricing", "speaker_lineup", "venue_info"],
            "target_lighthouse": 93, "avg_conversion": "6.0%", "mobile_share": "76%",
            "pk_growth": "+20% YoY", "global_market_size": "$1.5T",
            "roi_opportunities": ["countdown_timer", "video_hero", "newsletter_signup"],
        },
        # ── Law & Professional Services ──────────────────────────────────
        "legal": {
            "competitors": ["FindLaw", "Avvo", "LegalZoom", "PakLaw.pk"],
            "trends": ["Online consultations", "AI legal research", "Document automation", "Virtual law offices"],
            "conversion_drivers": ["trust_signals", "case_results", "free_consultation", "credentials"],
            "target_lighthouse": 93, "avg_conversion": "5.0%", "mobile_share": "58%",
            "pk_growth": "+12% YoY", "global_market_size": "$849B",
            "roi_opportunities": ["live_chat", "newsletter_signup", "testimonial_carousel"],
        },
        "lawfirm": {
            "competitors": ["FindLaw", "Avvo", "LegalZoom", "local firms"],
            "trends": ["Online consultations", "AI legal research", "Virtual offices"],
            "conversion_drivers": ["trust_signals", "case_results", "free_consultation", "credentials"],
            "target_lighthouse": 93, "avg_conversion": "5.0%", "mobile_share": "58%",
            "pk_growth": "+12% YoY", "global_market_size": "$849B",
            "roi_opportunities": ["live_chat", "cookie_consent", "testimonial_carousel"],
        },
        # ── Fintech ──────────────────────────────────────────────────────
        "fintech": {
            "competitors": ["JazzCash", "Easypaisa", "HBL Konnect", "Stripe", "Payoneer"],
            "trends": ["Open banking", "Buy Now Pay Later", "Crypto payments", "AI fraud detection"],
            "conversion_drivers": ["trust_seals", "instant_transfer", "zero_fees_promo", "regulatory_compliance"],
            "target_lighthouse": 96, "avg_conversion": "3.5%", "mobile_share": "88%",
            "pk_growth": "+70% YoY", "global_market_size": "$324B",
            "roi_opportunities": ["pwa_install", "push_notifications", "i18n_multilingual"],
        },
        # ── SaaS Startup ─────────────────────────────────────────────────
        "startup": {
            "competitors": ["Y Combinator portco", "ProductHunt launches", "local tech startups"],
            "trends": ["Product-led growth", "Freemium", "AI features", "Community-led"],
            "conversion_drivers": ["free_tier", "quick_setup", "integration_ecosystem", "social_proof"],
            "target_lighthouse": 95, "avg_conversion": "5.0%", "mobile_share": "55%",
            "pk_growth": "+55% YoY", "global_market_size": "$3T+ startup ecosystem",
            "roi_opportunities": ["exit_intent_popup", "newsletter_signup", "referral_program"],
        },
        # ── Crypto / Web3 ────────────────────────────────────────────────
        "crypto": {
            "competitors": ["Binance", "Coinbase", "PancakeSwap", "OpenSea"],
            "trends": ["DeFi 2.0", "Real-world assets tokenization", "AI trading bots", "Zero-knowledge proofs"],
            "conversion_drivers": ["security_audits", "tokenomics_clarity", "roadmap_transparency", "community_size"],
            "target_lighthouse": 92, "avg_conversion": "4.0%", "mobile_share": "68%",
            "pk_growth": "+80% YoY", "global_market_size": "$2.5T market cap",
            "roi_opportunities": ["countdown_timer", "social_proof", "newsletter_signup"],
        },
        # ── General fallback ─────────────────────────────────────────────
        "general": {
            "competitors": ["Industry leaders in segment"],
            "trends": ["Mobile-first", "Dark mode", "AI features", "PWA", "Performance optimization"],
            "conversion_drivers": ["clear_cta", "trust_signals", "fast_load", "social_proof", "mobile_ux"],
            "target_lighthouse": 92, "avg_conversion": "3.0%", "mobile_share": "65%",
            "pk_growth": "+25% YoY", "global_market_size": "varies",
            "roi_opportunities": ["whatsapp_float", "pwa_install", "newsletter_signup"],
        },
    }

    WEBSITE_TYPE_MARKET = {
        "ecommerce":   {"market_size": "large",      "avg_conversion": "2.5-3.5%",  "mobile_share": "72%", "pk_growth": "+35% YoY"},
        "saas":        {"market_size": "growing",     "avg_conversion": "3-7%",      "mobile_share": "40%", "pk_growth": "+55% YoY"},
        "business":    {"market_size": "medium",      "avg_conversion": "5-10%",     "mobile_share": "55%", "pk_growth": "+20% YoY"},
        "dashboard":   {"market_size": "enterprise",  "avg_conversion": "N/A",       "mobile_share": "30%", "pk_growth": "+40% YoY"},
        "restaurant":  {"market_size": "large",       "avg_conversion": "4-6%",      "mobile_share": "85%", "pk_growth": "+48% YoY"},
        "realestate":  {"market_size": "large",       "avg_conversion": "1.5-2.5%",  "mobile_share": "65%", "pk_growth": "+22% YoY"},
        "healthcare":  {"market_size": "growing",     "avg_conversion": "5-8%",      "mobile_share": "78%", "pk_growth": "+60% YoY"},
        "fitness":     {"market_size": "medium",      "avg_conversion": "6-9%",      "mobile_share": "75%", "pk_growth": "+30% YoY"},
        "education":   {"market_size": "large",       "avg_conversion": "3-5%",      "mobile_share": "70%", "pk_growth": "+65% YoY"},
        "travel":      {"market_size": "medium",      "avg_conversion": "2-4%",      "mobile_share": "76%", "pk_growth": "+18% YoY"},
        "portfolio":   {"market_size": "niche",       "avg_conversion": "6-12%",     "mobile_share": "60%", "pk_growth": "+25% YoY"},
        "creative":    {"market_size": "niche",       "avg_conversion": "4-7%",      "mobile_share": "62%", "pk_growth": "+28% YoY"},
        "blog":        {"market_size": "medium",      "avg_conversion": "2-5%",      "mobile_share": "82%", "pk_growth": "+15% YoY"},
        "nonprofit":   {"market_size": "large",       "avg_conversion": "3-6%",      "mobile_share": "73%", "pk_growth": "+10% YoY"},
        "event":       {"market_size": "large",       "avg_conversion": "5-8%",      "mobile_share": "76%", "pk_growth": "+20% YoY"},
        "lawfirm":     {"market_size": "medium",      "avg_conversion": "4-7%",      "mobile_share": "58%", "pk_growth": "+12% YoY"},
        "fintech":     {"market_size": "explosive",   "avg_conversion": "2-5%",      "mobile_share": "88%", "pk_growth": "+70% YoY"},
        "crypto":      {"market_size": "volatile",    "avg_conversion": "3-6%",      "mobile_share": "68%", "pk_growth": "+80% YoY"},
        "startup":     {"market_size": "growing",     "avg_conversion": "4-8%",      "mobile_share": "55%", "pk_growth": "+55% YoY"},
    }

    def analyze(self, spec: Dict[str, Any], social_signals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run comprehensive market analysis for 26+ industry verticals.

        When an Agent Reach `social_signals` payload (see
        `agent.reach.market_signals.collect_market_signals`) is supplied the
        live Reddit/Twitter X signals are merged into the trend and
        differentiation sections, keeping the reported market intelligence
        grounded in current community sentiment.
        """
        agent_logger.info("Phase 1: Running enhanced international market analysis...")

        industry     = spec.get("industry", "general")
        website_type = spec.get("website_type", "ecommerce")

        # Try industry first, then website_type, then general
        benchmark = (
            self.INDUSTRY_BENCHMARKS.get(industry) or
            self.INDUSTRY_BENCHMARKS.get(website_type) or
            self.INDUSTRY_BENCHMARKS["general"]
        )
        market_profile = (
            self.WEBSITE_TYPE_MARKET.get(website_type) or
            self.WEBSITE_TYPE_MARKET.get(industry) or
            {"market_size": "medium", "avg_conversion": "3%", "mobile_share": "65%", "pk_growth": "+20% YoY"}
        )

        analysis = {
            "industry":                  industry,
            "website_type":              website_type,
            "competitors":               benchmark["competitors"],
            "market_trends":             benchmark["trends"],
            "conversion_drivers":        benchmark["conversion_drivers"],
            "target_lighthouse_score":   benchmark["target_lighthouse"],
            "market_profile":            market_profile,
            "pk_market_growth":          benchmark.get("pk_growth", "N/A"),
            "global_market_size":        benchmark.get("global_market_size", "N/A"),
            "roi_opportunities":         benchmark.get("roi_opportunities", []),
            "differentiation_opportunities": self._identify_gaps(spec, benchmark),
            "recommended_positioning":   self._build_positioning(spec, benchmark),
            "mobile_priority":           float(str(benchmark.get("mobile_share", "50%")).replace("%", "")) >= 70,
            "whatsapp_market":           industry in ["restaurant", "realestate", "healthcare", "retail", "general"] or
                                          float(str(benchmark.get("mobile_share", "50%")).replace("%", "")) >= 75,
        }

        agent_logger.info(
            f"Market analysis complete: {len(analysis['competitors'])} competitors, "
            f"{len(analysis['market_trends'])} trends, "
            f"PK growth: {analysis['pk_market_growth']}, "
            f"global market: {analysis['global_market_size']}"
        )
        if social_signals:
            analysis["live_trend_signals"] = social_signals
            self._merge_social_signals(analysis, social_signals)
        return analysis

    def _merge_social_signals(self, analysis: Dict[str, Any], social_signals: Dict[str, Any]) -> None:
        """Fold Agent Reach social signals into market_trends + differentiation."""
        if not isinstance(social_signals, dict):
            return
        fragments = social_signals.get("fragments") or []
        preferred = social_signals.get("preferred_features") or []
        complaints = social_signals.get("complaints") or []
        channels_available = social_signals.get("channels_available") or {}
        platforms = sorted({str(f.get("platform")) for f in fragments if isinstance(f, dict)})

        existing_trends = list(analysis.get("market_trends") or [])
        for item in (preferred[:3] + complaints[:3]):
            label = f"Live community signal: {item}"
            if label not in existing_trends:
                existing_trends.append(label)
        analysis["market_trends"] = existing_trends[:12]

        differentiation = list(analysis.get("differentiation_opportunities") or [])
        for item in (preferred[:2] + complaints[:2]):
            label = f"Address community-reported need: {item}"
            if label not in differentiation:
                differentiation.append(label)
        analysis["differentiation_opportunities"] = differentiation[:7]

        if platforms:
            analysis["live_signal_sources"] = {
                "platforms": platforms,
                "channels_available": {k: bool(v) for k, v in channels_available.items()},
            }

    async def research_social_signals(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Async entry point: query Agent Reach (Reddit + Twitter/X) for this spec."""
        from agent.reach.market_signals import collect_market_signals

        report = await collect_market_signals(spec)
        return report.to_dict() if hasattr(report, "to_dict") else {}

    def _identify_gaps(self, spec: Dict[str, Any], benchmark: Dict[str, Any]) -> List[str]:
        features = set(spec.get("features", []))
        gaps = []
        for driver in benchmark["conversion_drivers"]:
            normalized = driver.replace(" ", "_").lower()
            if normalized not in features and driver not in features:
                gaps.append(f"Missing high-ROI driver: {driver}")
        for opp in benchmark.get("roi_opportunities", [])[:3]:
            gaps.append(f"Growth opportunity: {opp}")
        return gaps[:7]

    def _build_positioning(self, spec: Dict[str, Any], benchmark: Dict[str, Any]) -> str:
        industry  = spec.get("industry", "general")
        wtype     = spec.get("website_type", "website")
        features  = spec.get("features", [])
        pk_growth = benchmark.get("pk_growth", "")

        base = f"Premium {industry} {wtype} platform"
        extras = []
        if "authentication" in features:
            extras.append("personalised user experience")
        if "whatsapp_float" in features or benchmark.get("whatsapp_market"):
            extras.append("WhatsApp-first conversion (3-5x vs forms)")
        if "pwa_support" in features:
            extras.append("PWA-ready for mobile-first audience")
        if "i18n_multilingual" in features:
            extras.append("multilingual for international markets")
        if pk_growth:
            extras.append(f"positioned for {pk_growth} market growth")

        if extras:
            base += " with " + ", ".join(extras[:3])
        return base + "."
