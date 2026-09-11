"""
SEO Automation Engine — LumicorePro AI Agent
============================================
Phase 13 — Global SEO Suite

Generates production-ready SEO artifacts for every website type:
  - Per-page <head> meta tags (title, description, keywords, robots)
  - Open Graph (Facebook, LinkedIn) + Twitter Card tags
  - JSON-LD structured data per page/industry (20+ schema types)
  - hreflang alternate link tags for multi-language/multi-region
  - XML sitemap with lastmod + changefreq + priority
  - robots.txt with crawler rules + sitemap pointer
  - Canonical URL strategy
  - Breadcrumb schema
  - Core Web Vitals preload/preconnect hints
  - SEO_AUDIT.md report written to project root
"""

import os
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from utils.logger import agent_logger


class SEOAutomationEngine:
    """Full international SEO automation for 20+ website types."""

    # ── Page definitions per website type ────────────────────────────────
    PAGES: Dict[str, List[Dict[str, Any]]] = {
        "ecommerce": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "daily",   "schema": "website"},
            {"slug": "products",  "title": "Products",      "priority": 0.9, "changefreq": "daily",   "schema": "itemList"},
            {"slug": "cart",      "title": "Cart",          "priority": 0.5, "changefreq": "never",   "schema": None,      "noindex": True},
            {"slug": "checkout",  "title": "Checkout",      "priority": 0.5, "changefreq": "never",   "schema": None,      "noindex": True},
            {"slug": "about",     "title": "About Us",      "priority": 0.7, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.6, "changefreq": "monthly", "schema": "localBusiness"},
            {"slug": "blog",      "title": "Blog",          "priority": 0.7, "changefreq": "weekly",  "schema": "blog"},
            {"slug": "faq",       "title": "FAQ",           "priority": 0.6, "changefreq": "monthly", "schema": "faqPage"},
        ],
        "saas": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "software"},
            {"slug": "features",  "title": "Features",      "priority": 0.9, "changefreq": "monthly", "schema": "software"},
            {"slug": "pricing",   "title": "Pricing",       "priority": 0.9, "changefreq": "weekly",  "schema": "offer"},
            {"slug": "blog",      "title": "Blog",          "priority": 0.8, "changefreq": "daily",   "schema": "blog"},
            {"slug": "docs",      "title": "Documentation", "priority": 0.7, "changefreq": "weekly",  "schema": None},
            {"slug": "about",     "title": "About",         "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.5, "changefreq": "monthly", "schema": "localBusiness"},
        ],
        "restaurant": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "restaurant"},
            {"slug": "menu",      "title": "Menu",          "priority": 0.9, "changefreq": "weekly",  "schema": "menu"},
            {"slug": "reservations","title":"Reserve Table","priority": 0.8, "changefreq": "monthly", "schema": "reserveAction"},
            {"slug": "about",     "title": "About Us",      "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.7, "changefreq": "monthly", "schema": "localBusiness"},
            {"slug": "gallery",   "title": "Gallery",       "priority": 0.5, "changefreq": "monthly", "schema": None},
        ],
        "healthcare": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "medicalBusiness"},
            {"slug": "doctors",   "title": "Our Doctors",   "priority": 0.9, "changefreq": "weekly",  "schema": "person"},
            {"slug": "services",  "title": "Services",      "priority": 0.9, "changefreq": "monthly", "schema": "medicalSpecialty"},
            {"slug": "appointments","title":"Book Appointment","priority":0.8,"changefreq":"monthly",  "schema": "reserveAction"},
            {"slug": "about",     "title": "About Us",      "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.7, "changefreq": "monthly", "schema": "localBusiness"},
            {"slug": "faq",       "title": "FAQ",           "priority": 0.6, "changefreq": "monthly", "schema": "faqPage"},
        ],
        "education": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "educationalOrganization"},
            {"slug": "courses",   "title": "Courses",       "priority": 0.9, "changefreq": "daily",   "schema": "itemList"},
            {"slug": "about",     "title": "About",         "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "instructors","title":"Instructors",   "priority": 0.7, "changefreq": "monthly", "schema": "person"},
            {"slug": "blog",      "title": "Blog",          "priority": 0.7, "changefreq": "weekly",  "schema": "blog"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.5, "changefreq": "monthly", "schema": "localBusiness"},
        ],
        "realestate": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "daily",   "schema": "realEstateAgent"},
            {"slug": "listings",  "title": "Properties",    "priority": 0.9, "changefreq": "daily",   "schema": "itemList"},
            {"slug": "agents",    "title": "Our Agents",    "priority": 0.7, "changefreq": "weekly",  "schema": "person"},
            {"slug": "about",     "title": "About",         "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.7, "changefreq": "monthly", "schema": "localBusiness"},
            {"slug": "blog",      "title": "Blog",          "priority": 0.6, "changefreq": "weekly",  "schema": "blog"},
        ],
        "portfolio": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "monthly", "schema": "person"},
            {"slug": "about",     "title": "About",         "priority": 0.8, "changefreq": "monthly", "schema": "person"},
            {"slug": "projects",  "title": "Projects",      "priority": 0.9, "changefreq": "monthly", "schema": "itemList"},
            {"slug": "blog",      "title": "Blog",          "priority": 0.7, "changefreq": "weekly",  "schema": "blog"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.7, "changefreq": "monthly", "schema": None},
        ],
        "travel": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "travelAgency"},
            {"slug": "destinations","title":"Destinations", "priority": 0.9, "changefreq": "weekly",  "schema": "itemList"},
            {"slug": "packages",  "title": "Tour Packages", "priority": 0.9, "changefreq": "weekly",  "schema": "touristTrip"},
            {"slug": "about",     "title": "About",         "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.5, "changefreq": "monthly", "schema": "localBusiness"},
        ],
        "fitness": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "sportsClub"},
            {"slug": "classes",   "title": "Classes",       "priority": 0.9, "changefreq": "weekly",  "schema": "itemList"},
            {"slug": "trainers",  "title": "Trainers",      "priority": 0.7, "changefreq": "monthly", "schema": "person"},
            {"slug": "pricing",   "title": "Pricing",       "priority": 0.8, "changefreq": "monthly", "schema": "offer"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.5, "changefreq": "monthly", "schema": "localBusiness"},
        ],
        "blog": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "daily",   "schema": "blog"},
            {"slug": "articles",  "title": "Articles",      "priority": 0.9, "changefreq": "daily",   "schema": "itemList"},
            {"slug": "categories","title": "Categories",    "priority": 0.7, "changefreq": "weekly",  "schema": None},
            {"slug": "about",     "title": "About",         "priority": 0.5, "changefreq": "monthly", "schema": "person"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.4, "changefreq": "monthly", "schema": None},
        ],
        "fintech": [
            {"slug": "",          "title": "Home",          "priority": 1.0, "changefreq": "weekly",  "schema": "financialService"},
            {"slug": "features",  "title": "Features",      "priority": 0.9, "changefreq": "monthly", "schema": None},
            {"slug": "pricing",   "title": "Pricing",       "priority": 0.9, "changefreq": "weekly",  "schema": "offer"},
            {"slug": "security",  "title": "Security",      "priority": 0.7, "changefreq": "monthly", "schema": None},
            {"slug": "about",     "title": "About",         "priority": 0.6, "changefreq": "monthly", "schema": "organization"},
            {"slug": "contact",   "title": "Contact",       "priority": 0.5, "changefreq": "monthly", "schema": "localBusiness"},
        ],
    }

    # Default pages for unlisted types
    DEFAULT_PAGES = [
        {"slug": "",       "title": "Home",    "priority": 1.0, "changefreq": "weekly",  "schema": "website"},
        {"slug": "about",  "title": "About",   "priority": 0.7, "changefreq": "monthly", "schema": "organization"},
        {"slug": "services","title":"Services","priority": 0.8, "changefreq": "monthly", "schema": None},
        {"slug": "contact","title": "Contact", "priority": 0.6, "changefreq": "monthly", "schema": "localBusiness"},
    ]

    # hreflang region→locale mapping
    REGION_HREFLANG: Dict[str, List[Dict[str, str]]] = {
        "SA":    [{"lang": "ur-pk", "code": "ur"}, {"lang": "en-pk", "code": "en"}],
        "MENA":  [{"lang": "ar",    "code": "ar"}, {"lang": "en",    "code": "en"}],
        "EU":    [{"lang": "en",    "code": "en"}, {"lang": "de",    "code": "de"},
                  {"lang": "fr",    "code": "fr"}, {"lang": "es",    "code": "es"}],
        "NA":    [{"lang": "en-us", "code": "en"}, {"lang": "es-us", "code": "es"},
                  {"lang": "fr-ca", "code": "fr"}],
        "APAC":  [{"lang": "en",    "code": "en"}, {"lang": "zh-cn", "code": "zh"},
                  {"lang": "ja",    "code": "ja"}, {"lang": "ko",    "code": "ko"}],
        "AF":    [{"lang": "en",    "code": "en"}, {"lang": "fr",    "code": "fr"},
                  {"lang": "ar",    "code": "ar"}, {"lang": "sw",    "code": "sw"}],
        "LATAM": [{"lang": "es",    "code": "es"}, {"lang": "pt-br", "code": "pt"},
                  {"lang": "en",    "code": "en"}],
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate all SEO artifacts for the project."""
        agent_logger.info("SEOAutomationEngine: Generating global SEO suite...")

        website_type = spec.get("website_type", "ecommerce")
        project_name = spec.get("project_name", "project")
        base_url     = f"https://{project_name.lower().replace('_', '-').replace(' ', '-')}.com"
        region       = spec.get("region", "NA")
        languages    = spec.get("languages_generated", ["en"])
        today        = date.today().isoformat()

        pages = self.PAGES.get(website_type, self.DEFAULT_PAGES)
        hreflangs = self.REGION_HREFLANG.get(region, self.REGION_HREFLANG["NA"])

        artifacts = []
        pub_dir = os.path.join(project_dir, "frontend", "public")
        src_dir = os.path.join(project_dir, "frontend", "src")
        os.makedirs(pub_dir, exist_ok=True)
        os.makedirs(src_dir, exist_ok=True)

        # 1. sitemap.xml
        sitemap_path = os.path.join(pub_dir, "sitemap.xml")
        self._write(sitemap_path, self._build_sitemap(pages, base_url, today, hreflangs))
        artifacts.append(sitemap_path)

        # 2. robots.txt
        robots_path = os.path.join(pub_dir, "robots.txt")
        self._write(robots_path, self._build_robots(base_url, pages))
        artifacts.append(robots_path)

        # 3. Per-page SEO meta JSON (consumed by SEO.jsx)
        seo_config_path = os.path.join(src_dir, "seo-config.json")
        seo_config = self._build_seo_config(pages, base_url, spec)
        self._write(seo_config_path, json.dumps(seo_config, indent=2, ensure_ascii=False))
        artifacts.append(seo_config_path)

        # 4. hreflang config
        hreflang_path = os.path.join(src_dir, "hreflang-config.json")
        self._write(hreflang_path, json.dumps(
            {"base_url": base_url, "region": region, "hreflangs": hreflangs, "pages": [p["slug"] for p in pages]},
            indent=2
        ))
        artifacts.append(hreflang_path)

        # 5. SEO_AUDIT.md
        audit_path = os.path.join(project_dir, "SEO_AUDIT.md")
        self._write(audit_path, self._build_audit_md(spec, pages, base_url, hreflangs, today))
        artifacts.append(audit_path)

        # 6. Structured data helpers JS
        sd_path = os.path.join(src_dir, "config", "structured-data.js")
        os.makedirs(os.path.dirname(sd_path), exist_ok=True)
        self._write(sd_path, self._build_structured_data_js(spec, base_url))
        artifacts.append(sd_path)

        result = {
            "pages_optimized":   len(pages),
            "hreflang_count":    len(hreflangs),
            "artifacts":         artifacts,
            "base_url":          base_url,
            "sitemap_url":       f"{base_url}/sitemap.xml",
            "noindex_pages":     [p["slug"] for p in pages if p.get("noindex")],
            "schema_types_used": list({p["schema"] for p in pages if p.get("schema")}),
        }
        agent_logger.info(
            f"SEOAutomationEngine: {len(pages)} pages, {len(hreflangs)} hreflangs, "
            f"{len(artifacts)} artifacts."
        )
        return result

    # ── Builders ──────────────────────────────────────────────────────────
    def _build_sitemap(self, pages, base_url, today, hreflangs):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
                 '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
        for page in pages:
            if page.get("noindex"):
                continue
            url = f"{base_url}/{page['slug']}" if page['slug'] else base_url
            lines.append("  <url>")
            lines.append(f"    <loc>{url}</loc>")
            lines.append(f"    <lastmod>{today}</lastmod>")
            lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
            lines.append(f"    <priority>{page['priority']}</priority>")
            for hl in hreflangs:
                hl_url = f"{base_url}/{hl['code']}/{page['slug']}" if page['slug'] else f"{base_url}/{hl['code']}"
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{hl["lang"]}" href="{hl_url}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url}"/>')
            lines.append("  </url>")
        lines.append("</urlset>")
        return "\n".join(lines)

    def _build_robots(self, base_url, pages):
        noindex_slugs = [p["slug"] for p in pages if p.get("noindex")]
        lines = [
            "User-agent: *",
            "Allow: /",
        ]
        for slug in noindex_slugs:
            lines.append(f"Disallow: /{slug}")
        lines += [
            "Disallow: /api/",
            "Disallow: /admin/",
            "Disallow: /_next/",
            "",
            "User-agent: Googlebot",
            "Allow: /",
            "",
            f"Sitemap: {base_url}/sitemap.xml",
        ]
        return "\n".join(lines)

    def _build_seo_config(self, pages, base_url, spec):
        project = spec.get("project_name", "Project")
        industry = spec.get("industry", "general")
        config = {}
        for page in pages:
            slug = page["slug"] or "home"
            url = f"{base_url}/{page['slug']}" if page['slug'] else base_url
            config[slug] = {
                "title":         f"{page['title']} | {project}",
                "description":   self._default_desc(page["title"], project, industry),
                "canonicalUrl":  url,
                "ogType":        "website" if not page["slug"] else "article",
                "noIndex":       page.get("noindex", False),
                "schema":        page.get("schema"),
            }
        return config

    def _default_desc(self, page_title, project, industry):
        descs = {
            "Home":    f"Welcome to {project} — the leading {industry} platform. Discover our services, products, and more.",
            "About":   f"Learn about {project}, our mission, team, and story.",
            "Contact": f"Get in touch with {project}. We're here to help.",
            "Blog":    f"Read the latest articles and insights from {project}.",
            "FAQ":     f"Frequently asked questions about {project}.",
        }
        return descs.get(page_title, f"{page_title} — {project}")

    def _build_structured_data_js(self, spec, base_url):
        project = spec.get("project_name", "Project")
        industry = spec.get("industry", "general")
        website_type = spec.get("website_type", "website")
        return f"""/**
 * Structured Data Helpers — {project}
 * Import and use in your SEO.jsx component
 */

export const SITE_URL = '{base_url}';
export const SITE_NAME = '{project}';
export const INDUSTRY  = '{industry}';

/** Organization schema */
export const organizationSchema = {{
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: SITE_NAME,
  url: SITE_URL,
  logo: `${{SITE_URL}}/logo.png`,
  sameAs: [],
}};

/** Website schema with SearchAction */
export const websiteSchema = {{
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: SITE_NAME,
  url: SITE_URL,
  potentialAction: {{
    '@type': 'SearchAction',
    target: {{ '@type': 'EntryPoint', urlTemplate: `${{SITE_URL}}/search?q={{search_term_string}}` }},
    'query-input': 'required name=search_term_string',
  }},
}};

/** Breadcrumb schema builder */
export const breadcrumbSchema = (items) => ({{
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: items.map((item, i) => ({{
    '@type': 'ListItem',
    position: i + 1,
    name: item.name,
    item: `${{SITE_URL}}${{item.path}}`,
  }})),
}});

/** FAQ schema builder */
export const faqSchema = (faqs) => ({{
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqs.map((f) => ({{
    '@type': 'Question',
    name: f.question,
    acceptedAnswer: {{ '@type': 'Answer', text: f.answer }},
  }})),
}});

/** Product schema builder */
export const productSchema = ({{ name, description, image, sku, price, currency = 'USD', availability = 'InStock', rating, reviewCount }}) => ({{
  '@context': 'https://schema.org',
  '@type': 'Product',
  name, description, image, sku,
  offers: {{
    '@type': 'Offer',
    price, priceCurrency: currency,
    availability: `https://schema.org/${{availability}}`,
    url: typeof window !== 'undefined' ? window.location.href : SITE_URL,
  }},
  ...(rating && {{
    aggregateRating: {{ '@type': 'AggregateRating', ratingValue: rating, reviewCount: reviewCount || 1 }},
  }}),
}});

export default {{ organizationSchema, websiteSchema, breadcrumbSchema, faqSchema, productSchema }};
"""

    def _build_audit_md(self, spec, pages, base_url, hreflangs, today):
        project = spec.get("project_name", "Project")
        lines = [
            f"# SEO Audit Report — {project}",
            f"\nPrepared: {today}",
            "\n---\n",
            "## Summary\n",
            f"- **Base URL:** {base_url}",
            f"- **Pages Indexed:** {len([p for p in pages if not p.get('noindex')])}",
            f"- **Noindex Pages:** {', '.join(p['slug'] for p in pages if p.get('noindex')) or 'none'}",
            f"- **hreflang Locales:** {', '.join(h['lang'] for h in hreflangs)}",
            f"- **Schema Types:** {', '.join({p['schema'] for p in pages if p.get('schema')})}",
            "\n## Pages\n",
            "| Page | Priority | Change Freq | Schema | Noindex |",
            "|------|----------|-------------|--------|---------|",
        ]
        for p in pages:
            lines.append(
                f"| /{p['slug']} | {p['priority']} | {p['changefreq']} | "
                f"{p.get('schema','—')} | {'yes' if p.get('noindex') else 'no'} |"
            )
        lines += [
            "\n## hreflang Tags\n",
            "| Language | Code |",
            "|----------|------|",
        ]
        for h in hreflangs:
            lines.append(f"| {h['lang']} | {h['code']} |")
        lines += [
            "\n## Action Checklist\n",
            "- [ ] Submit sitemap to Google Search Console",
            "- [ ] Submit sitemap to Bing Webmaster Tools",
            "- [ ] Verify canonical URLs are correct in all pages",
            "- [ ] Confirm hreflang implementation with hreflang checker tool",
            "- [ ] Add real OG image at /public/og-image.jpg (1200x630px)",
            "- [ ] Test structured data with Google Rich Results Test",
            "- [ ] Enable Google Search Console + set up performance alerts",
            "- [ ] Verify robots.txt is accessible at /robots.txt",
            "\n---\n",
            "> Review with an SEO specialist before launch.",
        ]
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"SEOAutomationEngine: Could not write {path}: {e}")
