import json
import re
from typing import Dict, Any, List, Tuple
from utils.logger import agent_logger
from utils.helpers import extract_keywords, safe_json_parse, slugify


class RequirementAnalyzer:
    """Phase 2 — Analyzes prompts in English, Urdu, Roman-Urdu, Arabic, and mixed languages.
    Detects conflicts/vagueness, infers implicit sub-features, detects color/style hints,
    RTL language needs, and builds fully structured requirement specs for 20+ industry verticals.
    """

    # ── Urdu / Roman-Urdu / Arabic → English mappings ────────────────────
    URDU_KEYWORD_MAP = {
        # Food & Restaurant
        "khana": "food", "khane ki dukan": "restaurant", "biryani": "food",
        "restaurant wala": "restaurant", "cafe": "cafe", "nashta": "food",
        "menu": "menu", "order": "order", "delivery": "delivery", "karachi food": "food",
        "dhabba": "restaurant", "tikka": "food", "kabab": "food",
        # Real Estate
        "makan": "house", "ghar": "house", "plot": "property", "zameen": "property",
        "kiraya": "rent", "makaan": "house", "flat": "apartment", "villa": "villa",
        "property wala": "realestate", "ghar dhondna": "realestate", "kiraye ka": "rent",
        "jagah": "property", "imarat": "building",
        # Healthcare / Medical
        "doctor": "doctor", "hospital": "hospital", "clinic": "clinic", "ilaj": "medical",
        "mareez": "patient", "dawai": "medicine", "sehat": "health", "bemari": "disease",
        "tabib": "doctor", "nuskha": "prescription", "ilaaj": "healthcare",
        "dawa": "pharmacy", "lab test": "healthcare",
        # Education
        "school": "education", "college": "education", "university": "education",
        "parhai": "education", "course": "course", "taleem": "education", "tutor": "tutor",
        "online parhai": "lms", "seekhna": "learning", "class": "education",
        "kitab": "education", "ustaz": "teacher", "student": "education",
        # Fitness / Gym
        "gym": "gym", "exercise": "fitness", "workout": "fitness", "fitnes": "fitness",
        "warzish": "fitness", "trainer": "trainer", "kushti": "fitness",
        "body building": "fitness", "yoga": "fitness",
        # Travel
        "safar": "travel", "tour": "travel", "tourism": "travel", "ticket": "travel",
        "hotel": "hotel", "package": "package", "ghoomna": "travel", "sair": "travel",
        "destination": "travel", "visa": "travel", "booking": "booking",
        # E-Commerce / Shop
        "dukan": "shop", "khareed": "shop", "sell": "ecommerce", "online shop": "ecommerce",
        "products": "products", "cart": "cart", "wishlist": "wishlist",
        "payment": "payment", "bikna": "ecommerce", "bechna": "ecommerce",
        # Portfolio
        "portfolio": "portfolio", "apna kaam": "portfolio", "mera kaam": "portfolio",
        "developer": "portfolio", "meri website": "portfolio", "apna brand": "portfolio",
        # Creative
        "design": "creative", "agency": "agency", "branding": "creative",
        "logo": "branding", "studio": "creative", "dijain": "creative",
        # Business / Corporate
        "company": "business", "business": "business", "corporate": "corporate",
        "service": "services", "office": "business", "startup": "startup",
        # Blog / News
        "blog": "blog", "articles": "blog", "news": "blog", "likhai": "blog",
        "magazine": "blog", "akhbar": "news", "content": "blog",
        # Events
        "event": "event", "conference": "conference", "seminar": "event",
        "program": "event", "taqreeb": "event", "mehfil": "event",
        # Nonprofit / NGO
        "ngo": "nonprofit", "charity": "nonprofit", "donation": "nonprofit",
        "madad": "nonprofit", "khidmat": "nonprofit", "waqf": "nonprofit",
        # Law / Legal
        "lawyer": "lawfirm", "attorney": "lawfirm", "legal": "lawfirm",
        "advocate": "lawfirm", "case": "lawfirm", "court": "lawfirm",
        # SaaS / Dashboard
        "dashboard": "dashboard", "admin": "dashboard", "saas": "saas",
        "analytics": "analytics", "panel": "dashboard", "software": "saas",
        # Fintech / Finance
        "bank": "fintech", "finance": "fintech", "loan": "fintech", "qarz": "fintech",
        "investment": "fintech", "stock": "fintech", "crypto": "crypto",
        "bitcoin": "crypto", "wallet": "fintech", "payment gateway": "fintech",
        # Arabic keywords
        "مطعم": "restaurant", "طبيب": "healthcare", "عقار": "realestate",
        "تعليم": "education", "سفر": "travel", "تسوق": "ecommerce",
        "أعمال": "business", "مدونة": "blog",
    }

    # ── Industry implicit features (20+ verticals) ────────────────────────
    INDUSTRY_IMPLICIT_FEATURES = {
        "electronics":  ["specs", "discount_badge", "ratings", "search_autocomplete", "shipping_info", "price_filter", "wishlist", "comparison"],
        "fashion":      ["size_guide", "color_selector", "discount_badge", "ratings", "wishlist", "outfit_builder"],
        "food":         ["delivery_time", "cuisine_filter", "ratings", "order_tracking", "loyalty_points", "promo_code"],
        "restaurant":   ["menu_categories", "cart", "delivery_tracking", "ratings", "reservation", "qr_menu", "whatsapp_float"],
        "realestate":   ["property_search", "map_view", "filters", "virtual_tour", "mortgage_calculator", "contact_agent", "whatsapp_float"],
        "medical":      ["doctor_search", "appointment_booking", "ratings", "video_consult", "e_prescription"],
        "healthcare":   ["doctor_search", "appointment_booking", "ratings", "video_consult", "e_prescription", "lab_tests", "whatsapp_float"],
        "gym":          ["class_schedule", "membership_plans", "trainer_profiles", "booking", "nutrition_guide", "countdown_timer"],
        "fitness":      ["class_schedule", "membership_plans", "trainer_profiles", "progress_tracker", "bmi_calculator"],
        "edtech":       ["course_catalog", "video_player", "certificates", "progress_tracking", "instructor_rating", "newsletter_signup"],
        "education":    ["course_catalog", "video_lessons", "certificates", "progress_tracking", "quiz", "newsletter_signup"],
        "tourism":      ["destination_gallery", "package_search", "booking", "ratings", "itinerary", "currency_converter"],
        "travel":       ["destination_gallery", "package_filter", "booking", "reviews", "currency_converter", "newsletter_signup"],
        "personal":     ["project_grid", "skills_chart", "experience_timeline", "contact_form", "testimonials", "social_share"],
        "creative":     ["portfolio_grid", "case_studies", "team_section", "services_page", "client_logos", "social_share"],
        "corporate":    ["hero_section", "services", "team", "testimonials", "contact_form", "newsletter_signup"],
        "saas":         ["pricing_table", "feature_grid", "testimonial_slider", "auth_flow", "metrics", "pwa_support", "i18n_multilingual"],
        "dashboard":    ["recent_orders", "revenue_card", "data_table", "date_filter", "sidebar_nav", "analytics_dashboard"],
        "blog":         ["article_grid", "category_filter", "search", "newsletter_signup", "social_share", "seo_meta_tags", "rss_feed"],
        "nonprofit":    ["donation_form", "impact_stats", "cause_cards", "volunteer_signup", "newsletter_signup", "social_proof"],
        "event":        ["countdown_timer", "speaker_profiles", "session_agenda", "ticket_tiers", "map_embed", "newsletter_signup"],
        "lawfirm":      ["practice_areas", "attorney_profiles", "case_results", "consultation_booking", "trust_badges", "live_chat"],
        "fintech":      ["pricing_table", "security_badges", "auth_flow", "dashboard", "transaction_history", "analytics"],
        "crypto":       ["wallet_connect", "token_stats", "roadmap", "whitepaper", "community_links", "countdown_timer"],
        "startup":      ["hero_section", "pricing_table", "testimonials", "newsletter_signup", "pwa_support", "social_proof"],
        "agency":       ["portfolio_grid", "services", "team", "testimonials", "contact_form", "client_logos"],
        "general":      ["hero_section", "contact_form", "responsive_design", "social_share"],
    }

    # ── Website type detection rules (ordered by specificity) ─────────────
    TYPE_RULES = {
        "restaurant":  ["restaurant", "cafe", "food", "menu", "biryani", "dine", "dining", "delivery food", "khana", "eatery", "dhabba", "tikka"],
        "realestate":  ["real estate", "property", "house", "estate", "makan", "ghar", "plot", "zameen", "apartment", "villa", "listing", "rent"],
        "healthcare":  ["medical", "clinic", "hospital", "doctor", "healthcare", "ilaj", "sehat", "patient", "prescription", "pharmacy"],
        "fitness":     ["gym", "fitness", "workout", "exercise", "trainer", "warzish", "fitnes", "classes", "membership", "yoga", "body building"],
        "education":   ["course", "lms", "education", "learning", "school", "college", "university", "parhai", "seekhna", "online class", "e-learning"],
        "travel":      ["travel", "tourism", "tour", "vacation", "safar", "ticket", "hotel booking", "destination", "package", "ghoomna"],
        "portfolio":   ["portfolio", "personal site", "my work", "apna kaam", "developer portfolio", "designer portfolio", "resume site"],
        "creative":    ["creative", "studio", "agency", "branding", "design agency", "motion", "dijain agency"],
        "blog":        ["blog", "articles", "news", "magazine", "news site", "akhbar", "content site", "likhai", "media"],
        "nonprofit":   ["ngo", "nonprofit", "charity", "donation", "madad", "khidmat", "waqf", "volunteer", "cause"],
        "event":       ["event", "conference", "seminar", "program", "taqreeb", "mehfil", "summit", "meetup", "expo"],
        "lawfirm":     ["law firm", "lawyer", "attorney", "legal", "advocate", "case", "court", "legal services"],
        "fintech":     ["fintech", "finance", "bank", "loan", "investment", "payment gateway", "qarz"],
        "crypto":      ["crypto", "bitcoin", "blockchain", "token", "nft", "defi", "web3", "wallet"],
        "saas":        ["saas", "software", "platform", "api", "startup", "tool", "app"],
        "dashboard":   ["dashboard", "admin", "analytics", "panel", "monitor", "metrics", "management system"],
        "ecommerce":   ["store", "cart", "shop", "ecommerce", "buy", "sell", "dukan", "products", "marketplace"],
        "business":    ["landing", "portfolio", "agency", "blog", "corporate", "business", "company", "service"],
    }

    # ── Industry detection rules ──────────────────────────────────────────
    INDUSTRY_RULES = {
        "electronics":  ["electronics", "gadgets", "tech", "laptop", "mobile", "phone", "computer", "gaming"],
        "fashion":      ["fashion", "clothing", "apparel", "dress", "shirt", "shoes", "kapray", "clothes"],
        "food":         ["food", "restaurant", "cafe", "dish", "khana", "biryani", "cuisine"],
        "realestate":   ["real estate", "property", "house", "listings", "makan", "ghar", "zameen"],
        "personal":     ["portfolio", "personal", "brand", "resume", "developer", "designer"],
        "edtech":       ["education", "lms", "course", "learning", "school", "e-learning"],
        "education":    ["course", "learn", "university", "college", "tutor", "class"],
        "medical":      ["medical", "healthcare", "clinic", "doctor", "hospital", "health"],
        "healthcare":   ["health", "medical", "doctor", "clinic", "wellbeing", "pharmacy"],
        "gym":          ["fitness", "gym", "workout", "trainer", "classes", "yoga"],
        "fitness":      ["gym", "fitness", "health", "exercise", "sport", "body"],
        "tourism":      ["travel", "tourism", "tour", "destination", "safar"],
        "travel":       ["travel", "tour", "vacation", "holiday", "booking", "flight"],
        "corporate":    ["business", "corporate", "company", "services", "b2b"],
        "creative":     ["creative", "studio", "agency", "design", "branding"],
        "saas":         ["saas", "software", "platform", "api", "startup"],
        "blog":         ["blog", "news", "magazine", "articles", "media", "content"],
        "nonprofit":    ["ngo", "nonprofit", "charity", "donation", "cause", "volunteer"],
        "event":        ["event", "conference", "seminar", "summit", "meetup", "expo"],
        "legal":        ["law", "legal", "lawyer", "attorney", "advocate"],
        "fintech":      ["finance", "bank", "loan", "investment", "fintech", "payment"],
        "crypto":       ["crypto", "bitcoin", "blockchain", "nft", "web3", "token"],
        "general":      [],
    }

    # ── Color/style hints ─────────────────────────────────────────────────
    COLOR_HINTS_MAP = {
        "red": "#ef4444", "lal": "#ef4444",
        "blue": "#3b82f6", "neela": "#3b82f6",
        "green": "#22c55e", "hara": "#22c55e",
        "purple": "#a855f7", "baingani": "#a855f7",
        "orange": "#f97316", "narangi": "#f97316",
        "yellow": "#eab308", "zard": "#eab308",
        "pink": "#ec4899", "gulabi": "#ec4899",
        "cyan": "#06b6d4", "teal": "#0d9488",
        "black": "#0f172a", "kala": "#0f172a",
        "white": "#ffffff", "safed": "#ffffff",
        "gold": "#f59e0b", "sona": "#f59e0b",
        "dark": "dark_theme", "andhera": "dark_theme",
        "light": "light_theme", "ujala": "light_theme",
    }

    # ── RTL languages ─────────────────────────────────────────────────────
    RTL_SIGNALS = ["arabic", "urdu", "rtl", "right to left", "arab", "عربي", "اردو", "arabi"]

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Analyze prompt (any language) → structured requirements dict."""
        agent_logger.info("Analyzing requirements (multilingual NLP engine v2)...")

        # Pre-process: translate Urdu/Roman-Urdu/Arabic tokens
        normalized_prompt = self._normalize_multilingual(prompt)
        is_ambiguous, reason, options = self.check_ambiguity(normalized_prompt)

        spec = None
        analysis_source = "local_rules"
        if self.ai_provider:
            try:
                # Spec extraction is a classification job, not a reasoning job:
                # route it to the fast tier (cheapest adequate model) so it does
                # not sit in front of a strong model on the critical path.
                from agent.ai_routing import prefer

                provider, provider_name, tier = prefer(
                    "analyze", prompt, explicit=self.ai_provider
                ) or (self.ai_provider, "explicit", "pinned")
                agent_logger.info(f"[ROUTER] analyze_requirement -> tier={tier} provider={provider_name}")
                ai_result = provider.analyze_requirement(prompt)
                if ai_result and isinstance(ai_result, dict) and "website_type" in ai_result:
                    agent_logger.info("AI Provider analysis succeeded.")
                    spec = ai_result
                    # Provenance for the run record: the spec was NOT derived by
                    # the local rules, so the report may claim a model answered.
                    analysis_source = "ai_provider"
            except Exception as e:
                agent_logger.warning(f"AI analysis failed: {e}. Using local NLP.")

        if not spec:
            spec = self._local_rule_analysis(normalized_prompt, original_prompt=prompt)
        spec["analysis_source"] = analysis_source

        self._infer_implicit_features(spec)
        self._detect_color_hints(spec, prompt)
        self._detect_region(spec, prompt)
        self._detect_rtl(spec, prompt)
        self._detect_pwa_signals(spec, prompt)

        spec["is_ambiguous"] = is_ambiguous
        spec["ambiguity_reason"] = reason
        spec["clarifying_options"] = options
        spec["original_prompt"] = prompt
        # Always resolve a human brand name for the repo/project (ResuPro → resupro).
        if not spec.get("project_name") or "001" in str(spec.get("project_name", "")):
            spec["project_name"] = self._generate_project_name(spec, prompt)
        return spec

    def _normalize_multilingual(self, prompt: str) -> str:
        """Translate Urdu/Roman-Urdu/Arabic keywords to English equivalents."""
        result = prompt.lower()
        # Sort by length descending so longer phrases match first
        for kw, en in sorted(self.URDU_KEYWORD_MAP.items(), key=lambda x: -len(x[0])):
            result = result.replace(kw, en)
        return result

    # ── International market/region colors (culture-aware color combos) ───
    # Kept OUT of pro_design so the analyzer can also feed AI providers.
    REGION_SIGNALS = {
        'gcc':          ['uae', 'dubai', 'saudi', 'qatar', 'kuwait', 'bahrain', 'oman', 'kharab', 'middle east',
                         'gulf', 'khaliji', 'khaleej', 'مطعم'],
        'south-asia':   ['pakistan', 'pakistani', 'india', 'indian', 'bangladesh', 'bangladeshi', 'lahore',
                         'islamabad', 'karachi', 'main land', 'deli', 'amritsar', 'south asia', 'desi', 'hindi'],
        'east-asia':    ['china', 'chinese', 'japan', 'japanese', 'korea', 'korean', 'singapore', 'tokyo',
                         'shanghai', 'seoul', 'hong kong', 'taiwan'],
        'europe':       ['europe', 'european', 'uk', 'london', 'paris', 'berlin', 'france', 'germany',
                         'italy', 'spain', 'switzerland', 'sweden', 'denmark', 'norway', 'nordic'],
        'north-america': ['usa', 'united states', 'america', 'canada', 'new york', 'los angeles', 'san francisco'],
        'latam':        ['brazil', 'mexico', 'argentina', 'colombia', 'chile', 'peru', 'latam', 'latin america',
                         'spain market', 'uruguay'],
        'africa':       ['nigeria', 'kenya', 'egypt', 'south africa', 'ghana', 'africa', 'morocco', 'tunisia',
                         'algiers'],
        'default':      [],
    }

    def _detect_region(self, spec: Dict[str, Any], prompt: str) -> None:
        """Detect the target international market so the palette can follow it."""
        p = prompt.lower()
        for region, signals in self.REGION_SIGNALS.items():
            if region == 'default':
                continue
            if any(sig in p for sig in signals):
                spec['target_region'] = region
                agent_logger.info(f"Target region detected: {region}")
                return
        spec['target_region'] = 'default'

    def _detect_color_hints(self, spec: Dict[str, Any], prompt: str) -> None:
        """Extract color and theme preferences from prompt."""
        p = prompt.lower()
        detected_colors = []
        theme = "dark"  # default dark theme

        for kw, val in self.COLOR_HINTS_MAP.items():
            if kw in p:
                if val == "dark_theme":
                    theme = "dark"
                elif val == "light_theme":
                    theme = "light"
                else:
                    detected_colors.append(val)

        if detected_colors:
            spec["primary_color_hint"] = detected_colors[0]
        spec["preferred_theme"] = theme
        if detected_colors:
            spec["color_palette_hints"] = detected_colors[:3]

    def _detect_rtl(self, spec: Dict[str, Any], prompt: str) -> None:
        """Detect if the project needs RTL (right-to-left) language support."""
        p = prompt.lower()
        needs_rtl = any(signal in p for signal in self.RTL_SIGNALS)
        # Also detect if prompt itself contains Arabic/Urdu unicode characters
        has_arabic_script = bool(re.search(r'[\u0600-\u06FF\u0750-\u077F]', prompt))
        spec["rtl_support"] = needs_rtl or has_arabic_script
        if needs_rtl or has_arabic_script:
            spec["language_direction"] = "rtl"
            if "i18n_multilingual" not in spec.get("features", []):
                spec.setdefault("features", []).append("i18n_multilingual")
            agent_logger.info("RTL language support detected — injecting i18n feature.")

    def _detect_pwa_signals(self, spec: Dict[str, Any], prompt: str) -> None:
        """Detect if project should be a PWA."""
        p = prompt.lower()
        pwa_signals = ["pwa", "app", "mobile app", "offline", "install", "phone app", "smartphone", "mobile"]
        if any(s in p for s in pwa_signals):
            if "pwa_support" not in spec.get("features", []):
                spec.setdefault("features", []).append("pwa_support")

    def check_ambiguity(self, prompt: str) -> Tuple[bool, str, List[str]]:
        """Detect vague (<4 words) or highly conflicting domain signals."""
        prompt_lower = prompt.lower().strip()
        keywords = extract_keywords(prompt_lower)

        if len(keywords) < 2 and len(prompt_lower.split()) < 4:
            return (
                True,
                "Prompt is too vague. Please add more details.",
                [
                    "(a) E-commerce store (products, cart, checkout, payments)",
                    "(b) Restaurant website (menu, online ordering, delivery tracking)",
                    "(c) Healthcare portal (doctors, appointments, video consultation)",
                    "(d) SaaS platform (pricing, dashboard, subscriptions)",
                    "(e) Blog / Online magazine (articles, categories, newsletter)",
                    "(f) Event / Conference (tickets, speakers, countdown)",
                ]
            )

        type_signals = {
            "e-commerce storefront":    ["store", "cart", "shop", "ecommerce", "buy", "shopping cart"],
            "restaurant/food portal":   ["restaurant", "food", "menu", "biryani"],
            "medical/healthcare":       ["hospital", "medical", "clinic", "doctor", "patient"],
            "education/lms platform":   ["course", "lms", "education", "learning"],
            "travel portal":            ["travel", "tour", "tourism", "vacation"],
            "blog/media portal":        ["blog", "article", "articles", "news", "magazine"],
            "real estate portal":       ["real estate", "property", "house", "makan"],
            "fintech/crypto portal":    ["crypto", "bitcoin", "wallet", "banking", "finance"],
        }
        detected_types = [label for label, signals in type_signals.items() if any(w in prompt_lower for w in signals)]

        if len(detected_types) >= 3 or (len(detected_types) == 2 and any(t in detected_types for t in ["medical/healthcare", "restaurant/food portal"]) and "e-commerce storefront" in detected_types and "hospital" in prompt_lower):
            return (
                True,
                f"Conflicting domain signals: {', '.join(detected_types[:3])}.",
                [f"Option {i+1}: Build a focused {dt}" for i, dt in enumerate(detected_types[:3])]
            )
        return (False, "", [])

    def _infer_implicit_features(self, spec: Dict[str, Any]) -> None:
        """Auto-inject implicit industry sub-features."""
        features = set(spec.get("features", []))
        for key in [spec.get("industry", "general"), spec.get("website_type", "ecommerce")]:
            for imp in self.INDUSTRY_IMPLICIT_FEATURES.get(key, []):
                features.add(imp)

        # Always inject international essentials
        features.update({
            "cookie_consent",
            "social_share",
            "i18n_multilingual",
            "seo_meta_tags",
            "responsive_design",
            "accessibility_wcag",
            "security_hardening",
            "animation_system",
        })
        if spec.get("website_type") not in {"portfolio", "blog"}:
            features.add("whatsapp_float")
        spec["features"] = list(features)

    def _local_rule_analysis(self, prompt: str, original_prompt: str = "") -> Dict[str, Any]:
        """Enhanced local rule-based NLP parser (20+ industries, multilingual)."""
        prompt_lower = prompt.lower()
        keywords = extract_keywords(prompt_lower)

        # Detect website_type — score every rule; ties broken by rule order, so
        # SaaS/platform words (resume *builder*, tool, app) beat incidental page
        # names like "blog" in the page list. This stops "blog pricing page"
        # from classifying a SaaS product as a blog.
        website_type = "ecommerce"
        best_score = 0
        for wtype, signals in self.TYPE_RULES.items():
            score = sum(1 for s in signals if s in prompt_lower) + (
                3 if wtype == "saas" and any(w in prompt_lower for w in ("builder", "tool ", " tool", "app ", "platform", "software")) else 0
            )
            if score > best_score:
                best_score = score
                website_type = wtype

        # Detect industry
        industry = "general"
        for ind, kws in self.INDUSTRY_RULES.items():
            if kws and any(kw in prompt_lower for kw in kws):
                industry = ind
                break

        # Detect explicit features
        possible_features = [
            "authentication", "login", "register", "products", "categories",
            "cart", "wishlist", "checkout", "payments", "reviews", "admin",
            "dashboard", "search", "filters", "animations", "responsive",
            "ratings", "booking", "map", "gallery", "blog", "newsletter",
            "dark_mode", "multilingual", "seo", "notifications", "chat",
            "pwa", "stripe", "paypal", "whatsapp",
        ]
        detected_features = []
        for feat in possible_features:
            if feat in prompt_lower or any(feat in kw for kw in keywords):
                normalized = "authentication" if feat in ["login", "register"] else feat
                if normalized not in detected_features:
                    detected_features.append(normalized)

        # Type-specific baseline features
        type_defaults = {
            "ecommerce":  ["products", "cart", "checkout"],
            "restaurant": ["menu_categories", "cart", "reservation"],
            "realestate": ["property_search", "filters", "whatsapp_float"],
            "healthcare": ["doctor_search", "appointment_booking"],
            "fitness":    ["class_schedule", "membership_plans"],
            "education":  ["course_catalog", "enrollment"],
            "travel":     ["destination_gallery", "booking"],
            "portfolio":  ["project_grid", "contact_form"],
            "creative":   ["portfolio_grid", "services_page"],
            "blog":       ["article_grid", "newsletter_signup"],
            "nonprofit":  ["donation_form", "impact_stats"],
            "event":      ["countdown_timer", "ticket_tiers"],
            "lawfirm":    ["practice_areas", "consultation_booking"],
            "fintech":    ["pricing_table", "dashboard"],
            "crypto":     ["token_stats", "wallet_connect"],
            "saas":       ["pricing_table", "auth_flow", "dashboard"],
        }
        for default_feat in type_defaults.get(website_type, ["hero_section", "contact_form"]):
            if default_feat not in detected_features:
                detected_features.append(default_feat)

        # Detect category count
        categories_count = 10
        match = re.search(r"(\d+)\s+(product\s+)?categories", prompt_lower)
        if match:
            categories_count = int(match.group(1))

        # Detect styles
        styles = ["modern", "responsive"]
        if "animat" in prompt_lower or "motion" in prompt_lower:
            styles.append("animated")
        if "dark" in prompt_lower or "andhera" in prompt_lower:
            styles.append("dark_mode")
        if "minimal" in prompt_lower or "sada" in prompt_lower:
            styles.append("minimal")
        if "3d" in prompt_lower:
            styles.append("3d_effects")
        if "luxury" in prompt_lower or "premium" in prompt_lower:
            styles.append("premium")

        # Detect language
        has_urdu = any(kw in original_prompt.lower() for kw in self.URDU_KEYWORD_MAP)
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', original_prompt))
        detected_language = "urdu_bilingual" if has_urdu else ("arabic" if has_arabic else "english")

        result = {
            "project_name":           "",
            "website_type":           website_type,
            "industry":               industry,
            "frontend":               "react",
            "backend":                "node-express",
            "database":               "postgresql",
            "features":               detected_features,
            "style":                  styles,
            "product_categories_count": categories_count,
            "original_prompt":        original_prompt or prompt,
            "language_detected":      detected_language,
            "rtl_support":            False,
            "preferred_theme":        "dark",
        }
        self._detect_ui_style(result, original_prompt or prompt)
        result["project_name"] = self._generate_project_name(result, original_prompt or prompt)
        agent_logger.info(
            f"NLP Spec: type={result['website_type']}, industry={result['industry']}, "
            f"features={len(result['features'])}, lang={result['language_detected']}, "
            f"rtl={result['rtl_support']}"
        )
        return result

    UI_STYLE_SIGNALS = {
        "minimalist":    ["minimal", "minimalist", "sada", "clean", "studio", "simple ui", "apple", "klar", "suthra"],
        "glassmorphism": ["glass", "glassmorphism", "frosted", "blur", "translucent", "backdrop-blur", "sheesha"],
        "neobrutalism":  ["neo-brutal", "neobrutalism", "brutalist", "neo-brutalist", "brutalism", "gumroad", "borders"],
        "bento":         ["bento", "bento grid", "grid layout", "card grid", "vibes"],
        "neumorphism":   ["neumorph", "neumorphism", "soft ui", "soft-ui", "soft button", "nsm"],
        "flat":          ["flat", "flat design", "material", "material ui", "google", "2d"],
        "claymorphism":  ["clay", "claymorphism", "3d clay", "clay ui", "bubble"],
        "skeuomorphism": ["skeuomorph", "skeuomorphism", "realistic", "leather", "metallic", "vintage", "texture"],
        "dark":          ["cyberpunk", "neon", "dark ui", "dark mode", "noir", "terminal", "hacker", "cyber"],
    }

    def _detect_ui_style(self, spec: Dict[str, Any], prompt: str) -> None:
        """Detect a named UI design system (minimal/glass/neo-brutalism/bento/neumorphism/
        flat/clay/skeuomorphism/dark-cyberpunk) from the prompt."""
        p = prompt.lower()
        matched = []
        for style, signals in self.UI_STYLE_SIGNALS.items():
            if any(sig in p for sig in signals):
                matched.append(style)
        # Highest-specificity first; dark/cyberpunk wins on explicit request
        order = ["dark", "glassmorphism", "neobrutalism", "bento", "neumorphism",
                 "claymorphism", "skeuomorphism", "flat", "minimalist"]
        for style in order:
            if style in matched:
                spec["ui_style"] = style
                if style not in spec.get("style", []):
                    spec.setdefault("style", []).append(style)
                agent_logger.info(f"UI style detected: {style}")
                return
        spec["ui_style"] = "glassmorphism"  # enterprise default

    def _generate_project_name(self, spec: Dict[str, Any], prompt: str = "") -> str:
        brand = self._extract_brand_name(prompt or spec.get("original_prompt", ""))
        if brand:
            return slugify(brand)
        ind = spec.get("industry", "custom")
        wtype = spec.get("website_type", "site")
        return slugify(f"{ind}-{wtype}-001")

    def _extract_brand_name(self, prompt: str) -> str:
        """Extract a human brand/product name from the prompt (ResuPro, Verapay, ...)."""
        import re as _re
        if not prompt:
            return ""
        p = prompt.strip()
        # 1) Explicit "named/called/brand X" hints
        for m in _re.finditer(r"(?:named|called|brand(?: name)?|for the (?:brand|company)|app)\s+[:\-]?\s*([A-Z][A-Za-z0-9]*)", p):
            cand = m.group(1)
            if len(cand) >= 3:
                return cand
        # 2) PascalCase/CamelCase compound tokens (ResuPro, PayFlow, NexaMart)
        for m in _re.finditer(r"\b[A-Z][a-z0-9]*[A-Z][A-Za-z0-9]*\b", p):
            cand = m.group(0)
            if len(cand) >= 3 and cand[0].isupper():
                return cand
        # 3) Single capitalized word (sidekick, verapay, ...)
        for m in _re.finditer(r"\b[A-Z][a-z]{2,}\b", p):
            first = m.group(0)
            if first.lower() not in {"the", "for", "and", "with", "new", "your", "buy", "pro", "ai", "app", "get", "how", "why"}:
                return first
        return ""
