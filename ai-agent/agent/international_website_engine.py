"""International Website Inspector & Replicator Engine
=====================================================
Analyzes any international website URL, domain, or reference brand (e.g. Stripe,
Apple, Linear, Airbnb, Nike, Vercel, etc.) and synthesizes a production-grade
matching website specification with all sections, pages, icons, color tokens,
and high-res imagery adhering to top-tier global standards.
"""

import os
import re
import json
import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger


class _DOMSemanticExtractor(HTMLParser):
    """Resilient HTML parser extracting semantic structure, headings, links, and content."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_tags: Dict[str, str] = {}
        self.headings: List[Dict[str, str]] = []
        self.nav_links: List[str] = []
        self.buttons: List[str] = []
        self.paragraphs: List[str] = []
        self.image_alts: List[str] = []
        self.section_classes: List[str] = []

        self._current_tag = ""
        self._current_text = []
        self._in_title = False
        self._in_nav = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        self._current_tag = tag

        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attr_dict.get("name") or attr_dict.get("property")
            content = attr_dict.get("content")
            if name and content:
                self.meta_tags[name.lower()] = content
        elif tag == "nav":
            self._in_nav = True
        elif tag in ("section", "div"):
            cls = attr_dict.get("class", "")
            if cls:
                self.section_classes.append(cls)
        elif tag == "img":
            alt = attr_dict.get("alt", "")
            if alt:
                self.image_alts.append(alt)

    def handle_endtag(self, tag: str):
        text = "".join(self._current_text).strip()
        if tag == "title":
            self._in_title = False
            self.title = text
        elif tag == "nav":
            self._in_nav = False
        elif tag in ("h1", "h2", "h3", "h4"):
            if text:
                self.headings.append({"level": tag, "text": text})
        elif tag == "a" and (self._in_nav or len(text) < 30):
            if text and len(text) > 1:
                self.nav_links.append(text)
        elif tag == "button":
            if text:
                self.buttons.append(text)
        elif tag == "p":
            if len(text) > 20:
                self.paragraphs.append(text)

        self._current_text = []
        self._current_tag = ""

    def handle_data(self, data: str):
        if data.strip():
            self._current_text.append(data)


class InternationalWebsiteEngine:
    """Inspects live websites or reference intelligence profiles, extracting
    layout tokens, copy hierarchy, sections, pages, icons, and imagery.
    """

    # Reference intelligence profiles for industry benchmarks
    REFERENCE_PROFILES: Dict[str, Dict[str, Any]] = {
        "stripe.com": {
            "brand": "Stripe",
            "industry": "fintech",
            "tagline": "Financial infrastructure for the internet",
            "description": "Millions of businesses of all sizes use Stripe online and in person to accept payments, send payouts, and manage their businesses online.",
            "color_palette": {
                "primary": "#635bff",
                "accent": "#00d4ff",
                "surface": "#0a2540",
                "background": "#ffffff",
                "text": "#0a2540",
            },
            "typography": "neogrotesque",
            "sections": [
                {"type": "hero", "title": "Financial infrastructure for the internet", "cta": "Start now"},
                {"type": "logo_cloud", "title": "Powering the world's most innovative teams"},
                {"type": "bento_grid", "title": "A fully integrated suite of financial products"},
                {"type": "interactive_terminal", "title": "Designed for developers"},
                {"type": "stats", "metrics": ["500M+ API requests/day", "99.999% uptime", "135+ currencies"]},
                {"type": "comparison", "title": "Why high-growth companies choose Stripe"},
                {"type": "modern_footer", "categories": ["Products", "Developers", "Company", "Resources"]},
            ],
            "pages": ["Home", "Products", "Solutions", "Developers", "Pricing", "About", "Contact"],
            "icons": ["CreditCard", "ShieldCheck", "Zap", "Globe", "Code", "BarChart3", "Lock", "ArrowRight"],
            "imagery_theme": "modern fintech payment cards abstract 3d glass",
        },
        "apple.com": {
            "brand": "Apple",
            "industry": "consumer-tech",
            "tagline": "Innovation and precision engineering",
            "description": "Discover the innovative world of Apple. Shop iPhone, iPad, Apple Watch, Mac, and Apple TV, plus explore accessories and entertainment.",
            "color_palette": {
                "primary": "#0071e3",
                "accent": "#2997ff",
                "surface": "#1d1d1f",
                "background": "#000000",
                "text": "#f5f5f7",
            },
            "typography": "clean-minimal",
            "sections": [
                {"type": "hero", "title": "Titanium. So strong. So light. So Pro.", "cta": "Buy Now"},
                {"type": "product_showcase", "title": "Explore the full lineup"},
                {"type": "interactive_3d", "title": "Precision engineered from inside out"},
                {"type": "bento_grid", "title": "Next-generation capabilities"},
                {"type": "modern_footer", "categories": ["Shop and Learn", "Account", "Entertainment", "Apple Values"]},
            ],
            "pages": ["Home", "Store", "Mac", "iPad", "iPhone", "Watch", "Vision", "Support"],
            "icons": ["Sparkles", "Cpu", "BatteryCharging", "Camera", "Smartphone", "Monitor", "Headphones"],
            "imagery_theme": "sleek minimalist titanium technology hardware",
        },
        "linear.app": {
            "brand": "Linear",
            "industry": "saas",
            "tagline": "Linear is a better way to build products",
            "description": "Meet the new standard for modern software development. Streamline issues, sprints, and product roadmaps.",
            "color_palette": {
                "primary": "#5e6ad2",
                "accent": "#8a99ad",
                "surface": "#121316",
                "background": "#08090a",
                "text": "#f7f8f8",
            },
            "typography": "editorial-sans",
            "sections": [
                {"type": "hero", "title": "Linear is a better way to build products", "cta": "Get started"},
                {"type": "product_preview", "title": "Issue tracking you'll actually enjoy using"},
                {"type": "bento_grid", "title": "Engineered for speed and focus"},
                {"type": "keyboard_shortcuts", "title": "Keyboard-first workflow"},
                {"type": "testimonials", "title": "Loved by the world's best product teams"},
                {"type": "modern_footer", "categories": ["Product", "Features", "Company", "Community"]},
            ],
            "pages": ["Home", "Features", "Method", "Customers", "Changelog", "Pricing", "Contact"],
            "icons": ["CheckCircle2", "Zap", "Layers", "GitBranch", "Command", "Sliders", "Search"],
            "imagery_theme": "dark mode software ui bento mockup sleek",
        },
        "airbnb.com": {
            "brand": "Airbnb",
            "industry": "travel",
            "tagline": "Find spaces that inspire your journey",
            "description": "Book unique homes, vacation rentals, and experiences all around the globe.",
            "color_palette": {
                "primary": "#ff385c",
                "accent": "#e00b41",
                "surface": "#ffffff",
                "background": "#ffffff",
                "text": "#222222",
            },
            "typography": "friendly-sans",
            "sections": [
                {"type": "hero_search", "title": "Anywhere - Any week - Add guests", "cta": "Search"},
                {"type": "category_filter", "title": "Top-rated destinations worldwide"},
                {"type": "grid_listings", "title": "Stay at top-tier homes"},
                {"type": "host_cta", "title": "Airbnb it easily"},
                {"type": "modern_footer", "categories": ["Support", "Community", "Hosting", "Airbnb"]},
            ],
            "pages": ["Home", "Stays", "Experiences", "Become a Host", "Wishlists", "Help"],
            "icons": ["MapPin", "Calendar", "Users", "Search", "Heart", "Star", "Compass"],
            "imagery_theme": "luxurious architectural villas nature travel photography",
        },
    }

    # Curated Unsplash HD images mapped to industries
    CURATED_IMAGERY: Dict[str, List[str]] = {
        "fintech": [
            "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1618042164219-62c820f10723?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1400&q=80",
        ],
        "saas": [
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1400&q=80",
        ],
        "consumer-tech": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?auto=format&fit=crop&w=1400&q=80",
        ],
        "ecommerce": [
            "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1400&q=80",
        ],
        "travel": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1400&q=80",
            "https://images.unsplash.com/photo-1502784444187-359ac186c5bb?auto=format&fit=crop&w=1400&q=80",
        ],
    }

    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def inspect_url(self, target: str) -> Dict[str, Any]:
        """Inspects target URL or domain. Falls back to reference profile if offline."""
        clean_target = target.strip().lower()
        if clean_target.startswith("http://") or clean_target.startswith("https://"):
            url = clean_target
            domain = urllib.parse.urlparse(clean_target).netloc.replace("www.", "")
        else:
            domain = clean_target.replace("www.", "")
            url = f"https://{domain}"

        # Check pre-indexed reference intelligence profiles
        for ref_domain, profile in self.REFERENCE_PROFILES.items():
            if ref_domain in domain or domain in ref_domain:
                agent_logger.info(f"Loaded reference intelligence profile for {domain}")
                return {
                    "source": "reference_profile",
                    "domain": domain,
                    "status": "success",
                    "data": profile,
                }

        # Attempt live inspection
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                return self._parse_html(raw_html, domain, url)
        except Exception as exc:
            agent_logger.warning(f"Live inspection failed for {url}: {exc}. Synthesizing from domain.")
            return self._synthesize_from_domain(domain)

    def _parse_html(self, html_text: str, domain: str, url: str) -> Dict[str, Any]:
        """Parses raw HTML extracting sections, headings, CTAs, and metadata."""
        parser = _DOMSemanticExtractor()
        try:
            parser.feed(html_text)
        except Exception as err:
            agent_logger.warning(f"HTML parse warning: {err}")

        # Extract title and brand
        title = parser.title or parser.meta_tags.get("og:title", domain.capitalize())
        brand = title.split("-")[0].split("|")[0].split(":")[0].strip() or domain.capitalize()
        description = parser.meta_tags.get("description") or parser.meta_tags.get("og:description", f"Modern high-performance web experience for {brand}.")

        # Detect industry keywords
        content_sample = f"{title} {description} {' '.join([h['text'] for h in parser.headings])}".lower()
        industry = "saas"
        if any(k in content_sample for k in ["payment", "bank", "invest", "finance", "crypto", "wallet"]):
            industry = "fintech"
        elif any(k in content_sample for k in ["shop", "store", "cart", "product", "cloth", "fashion", "order"]):
            industry = "ecommerce"
        elif any(k in content_sample for k in ["flight", "hotel", "travel", "vacation", "trip", "booking"]):
            industry = "travel"
        elif any(k in content_sample for k in ["device", "phone", "hardware", "screen", "gadget", "chip"]):
            industry = "consumer-tech"

        # Color extraction from hex occurrences
        hex_matches = re.findall(r"#[0-9a-fA-F]{6}", html_text)
        primary_color = hex_matches[0] if hex_matches else "#2563eb"
        surface_color = "#0f172a" if "dark" in html_text.lower() else "#ffffff"

        sections = []
        # Hero Section
        h1_text = next((h["text"] for h in parser.headings if h["level"] == "h1"), title)
        cta_text = parser.buttons[0] if parser.buttons else "Get Started"
        sections.append({"type": "hero", "title": h1_text, "cta": cta_text})

        # Feature / Bento grid sections from H2s
        h2_headings = [h["text"] for h in parser.headings if h["level"] == "h2"][:6]
        if h2_headings:
            sections.append({"type": "bento_grid", "title": "Core Features & Architecture", "items": h2_headings})

        # Testimonials / Trust
        sections.append({"type": "testimonials", "title": f"Trusted by leading global enterprises"})
        sections.append({"type": "comparison", "title": f"Why choose {brand} over legacy alternatives"})
        sections.append({"type": "modern_footer", "categories": ["Products", "Platform", "Resources", "Company"]})

        pages = ["Home", "Features", "Pricing", "About", "Contact"]
        if parser.nav_links:
            clean_links = [l.strip() for l in parser.nav_links if 3 <= len(l.strip()) <= 18][:6]
            if clean_links:
                pages = list(dict.fromkeys(["Home"] + clean_links))

        return {
            "source": "live_inspection",
            "domain": domain,
            "status": "success",
            "data": {
                "brand": brand,
                "industry": industry,
                "tagline": title,
                "description": description,
                "color_palette": {
                    "primary": primary_color,
                    "accent": "#38bdf8",
                    "surface": surface_color,
                    "background": surface_color,
                    "text": "#0f172a" if surface_color == "#ffffff" else "#f8fafc",
                },
                "typography": "neogrotesque",
                "sections": sections,
                "pages": pages,
                "icons": ["Sparkles", "ShieldCheck", "Zap", "Globe", "CheckCircle2", "ArrowRight", "Layers", "BarChart3"],
                "imagery_theme": f"modern {industry} high tech minimal",
            },
        }

    def _synthesize_from_domain(self, domain: str) -> Dict[str, Any]:
        """Synthesizes an international-grade spec directly from brand name or domain."""
        brand = domain.split(".")[0].capitalize()
        industry = "saas"
        if any(k in domain for k in ["pay", "coin", "bank", "fund", "money", "wallet", "fintech", "crypto", "billing"]):
            industry = "fintech"
        elif any(k in domain for k in ["shop", "store", "market", "wear", "cart", "commerce"]):
            industry = "ecommerce"
        elif any(k in domain for k in ["travel", "stay", "tour", "fly", "trip"]):
            industry = "travel"

        return {
            "source": "domain_synthesizer",
            "domain": domain,
            "status": "success",
            "data": {
                "brand": brand,
                "industry": industry,
                "tagline": f"Next-Generation Platform for {brand}",
                "description": f"Engineered for speed, precision, and global scale with enterprise reliability.",
                "color_palette": {
                    "primary": "#3b82f6",
                    "accent": "#6366f1",
                    "surface": "#090d16",
                    "background": "#030712",
                    "text": "#f9fafb",
                },
                "typography": "editorial-sans",
                "sections": [
                    {"type": "hero", "title": f"The intelligent platform for {brand}", "cta": "Explore Now"},
                    {"type": "bento_grid", "title": "Engineered for maximum velocity"},
                    {"type": "comparison", "title": f"The {brand} Advantage"},
                    {"type": "pricing", "title": "Transparent, scalable pricing"},
                    {"type": "modern_footer", "categories": ["Solutions", "Developers", "Resources", "Legal"]},
                ],
                "pages": ["Home", "Features", "Pricing", "About", "Contact"],
                "icons": ["Zap", "ShieldCheck", "Globe", "Cpu", "CheckCircle2", "ArrowRight", "Layers"],
                "imagery_theme": f"sleek modern {industry} technology architecture",
            },
        }

    def replicate_website_spec(self, target: str, brand_override: Optional[str] = None) -> Dict[str, Any]:
        """Extracts and synthesizes a complete React 19 + Tailwind project blueprint
        matching the target international website standard.
        """
        inspection = self.inspect_url(target)
        spec = inspection.get("data", {})
        if brand_override:
            spec["brand"] = brand_override

        industry = spec.get("industry", "saas")
        images = self.CURATED_IMAGERY.get(industry, self.CURATED_IMAGERY["saas"])

        spec["resolved_images"] = {
            "hero_bg": images[0],
            "feature_1": images[1],
            "feature_2": images[2],
            "banner": images[3],
        }
        spec["international_ready"] = True
        spec["target_source"] = target

        return {
            "success": True,
            "target": target,
            "brand": spec["brand"],
            "industry": industry,
            "spec": spec,
            "instructions": "Mount using GlassNavbar, HeroSection, BentoGrid, ComparisonTable, and ModernFooter.",
        }
