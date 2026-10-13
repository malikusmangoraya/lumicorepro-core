"""
Layout Engine — generic, project-agnostic international layout engine.
=====================================================================

Unlike :func:`agent.pro_design.restyle_project` (keyed to the 14 legacy repo
names and their hard-coded palettes/profiles), this engine works on **any**
project, present or future:

    discover  →  plan  (offline, deterministic)  →  apply  (full restyle)  →  revert

It recomposes the whole *presentation shell* — design tokens, the global
stylesheet, Tailwind theme, navbar, footer, brand logo and the landing page —
while **preserving the functional spine** (router routes, pages, feature
modules, i18n, SEO head, services) so the app keeps working after a restyle.

Everything is offline and deterministic: the same project + same options always
produce the same design. It reuses the existing design vocabulary rather than
duplicating it:

  * ``DesignStyleEngine``            → 35 named art-directed styles
  * ``pro_design.REGION_PALETTES``   → culturally-aware international palettes
  * ``HyperUniqueSiteEngine``        → unique palettes / typography / SVG logos
  * ``theme_matrix``                 → industry page-section blueprints
  * ``design_vault.VAULT_STYLES``    → user-provided exact design languages
  * ``registry/design-resources.json`` → attribute profiles (inspiration, never copies)

Reference material is decomposed into *attributes* only — no markup is copied
from any external source.

CLI
---
    python -m agent.layout_engine <project_dir> [--style S] [--region R]
        [--industry I] [--brand B] [--skin presentation|full] [--dry-run] [--revert]
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from utils.logger import agent_logger
except Exception:  # pragma: no cover - library use without the agent package
    import logging
    agent_logger = logging.getLogger('layout_engine')

from .design_style import DesignStyleEngine
from .hyper_unique_site_engine import HyperUniqueSiteEngine

try:
    from .design_vault import VAULT_STYLES
except Exception:  # pragma: no cover
    VAULT_STYLES = {}

try:
    from .pro_design import REGION_PALETTES, PALETTES, PROFILES, _derive_profile, _derive_palette
except Exception:  # pragma: no cover - fall back to an inline copy
    REGION_PALETTES = {
        'gcc': {'primary': '#b8860b', 'accent': '#0f766e', 'heading': '#5b3200',
                'navBg': '#fffaf0', 'footerBg': '#1c1917'},
        'south-asia': {'primary': '#ea580c', 'accent': '#16a34a', 'heading': '#451a03',
                       'navBg': '#fff7ed', 'footerBg': '#1c1917'},
        'east-asia': {'primary': '#dc2626', 'accent': '#d97706', 'heading': '#1f2937',
                      'navBg': '#fff7f7', 'footerBg': '#111827'},
        'europe': {'primary': '#1d4ed8', 'accent': '#0f766e', 'heading': '#0f172a',
                   'navBg': '#f8fafc', 'footerBg': '#0f172a'},
        'north-america': {'primary': '#2563eb', 'accent': '#dc2626', 'heading': '#111827',
                          'navBg': '#f8fafc', 'footerBg': '#111827'},
        'latam': {'primary': '#f97316', 'accent': '#0d9488', 'heading': '#7c2d12',
                  'navBg': '#fff7ed', 'footerBg': '#1c1917'},
        'africa': {'primary': '#b45309', 'accent': '#047857', 'heading': '#292524',
                   'navBg': '#fafaf9', 'footerBg': '#1c1917'},
        'default': {},
    }
    PALETTES = {}
    PROFILES = {}

    def _derive_profile(repo_name: str) -> Dict[str, Any]:  # type: ignore
        title = re.sub(r'[-_\d]+$', '', repo_name).replace('-', ' ').replace('_', ' ').title() or 'Lumicore'
        return {
            'title': title.split()[0], 'tagline': 'Engineered for growth',
            'eyebrow': 'MODERN PLATFORM',
            'hero_desc': f'{title} helps teams ship faster with a fast, accessible interface.',
            'features': [('Fast by default', 'Optimised for speed and Core Web Vitals'),
                         ('Secure by design', 'Authentication, encryption and audit logging'),
                         ('Built to scale', 'From prototype to production'),
                         ('Accessible', 'WCAG-aware, keyboard-first interfaces')],
            'stats': [('99.99%', 'Uptime'), ('<2s', 'Load time'), ('10K+', 'Users'), ('4.9/5', 'Rating')],
        }

    def _derive_palette(repo_name: str) -> Dict[str, str]:  # type: ignore
        return {'primary': '#2563eb', 'accent': '#7c3aed', 'heading': '#0f172a',
                'navBg': '#ffffff', 'footerBg': '#0f172a'}


ENGINE_NAME = 'layout-engine'
ENGINE_VERSION = '1.0'
CSS_MARKER = 'LUMI_LAYOUT_V1'
MANIFEST_REL = '.lumicore/layout-manifest.json'
BACKUP_REL = '.lumicore/layout'
TOKENS_REL = 'src/styles/design-tokens.json'

# Canonical token keys the engine emits (all hex).
_TOKEN_KEYS = ('primary', 'secondary', 'accent', 'heading', 'canvas', 'surface',
               'text', 'muted', 'border', 'navBg', 'footerBg')

# Guarantees a complete, valid hex palette even when a style uses rgba() neutrals.
_DEFAULT_TOKENS: Dict[str, str] = {
    'primary': '#2563eb', 'secondary': '#7c3aed', 'accent': '#7c3aed',
    'heading': '#0f172a', 'canvas': '#ffffff', 'surface': '#f8fafc',
    'text': '#1f2937', 'muted': '#64748b', 'border': '#e2e8f0',
    'navBg': '#ffffff', 'footerBg': '#0f172a',
}

# industry keyword → theme_matrix category (keys of _CATEGORY_SECTIONS)
_INDUSTRY_CATEGORY: List[Tuple[str, str]] = [
    ('car', 'automotive'), ('auto', 'automotive'), ('vehicle', 'automotive'),
    ('motor', 'automotive'), ('dealer', 'automotive'),
    ('estate', 'realestate'), ('realty', 'realestate'), ('property', 'realestate'),
    ('fitness', 'fitness'), ('gym', 'gym'), ('workout', 'fitness'), ('athletic', 'fitness'),
    ('insurance', 'insurance'), ('claim', 'insurance'),
    ('wedding', 'wedding'), ('bridal', 'wedding'),
    ('event', 'event'), ('venue', 'event'), ('ticket', 'event'),
    ('travel', 'travel'), ('voyage', 'travel'), ('tour', 'travel'), ('trip', 'travel'),
    ('studio', 'creative'), ('design', 'creative'), ('photo', 'portfolio'),
    ('portfolio', 'portfolio'), ('resume', 'portfolio'),
    ('capital', 'fintech'), ('bank', 'fintech'), ('finance', 'fintech'),
    ('invest', 'fintech'), ('fund', 'fintech'), ('pay', 'fintech'), ('fintech', 'fintech'),
    ('market', 'marketplace'), ('shop', 'ecommerce'), ('store', 'ecommerce'),
    ('commerce', 'ecommerce'), ('ecommerce', 'ecommerce'),
    ('health', 'healthcare'), ('clinic', 'healthcare'), ('medical', 'healthcare'),
    ('care', 'healthcare'), ('hospital', 'healthcare'),
    ('learn', 'education'), ('course', 'education'), ('school', 'education'),
    ('academy', 'education'), ('edu', 'education'),
    ('restaurant', 'restaurant'), ('food', 'restaurant'), ('cafe', 'restaurant'),
    ('legal', 'lawfirm'), ('law', 'lawfirm'), ('attorney', 'lawfirm'),
    ('real estate', 'realestate'),
]

_DEFAULT_CATEGORY = 'saas'

_SECTION_FALLBACK = ['Hero', 'Features', 'Pricing', 'Testimonials', 'Contact']

# Category-appropriate copy (avoids generic SaaS filler on a car/estate/fintech
# site). `{brand}` is formatted per project; features are (title, detail) tuples.
_CATEGORY_COPY: Dict[str, Dict[str, Any]] = {
    'saas': {
        'eyebrow': 'MODERN SAAS PLATFORM', 'tagline': 'Software that scales with you',
        'hero_desc': '{brand} helps teams ship faster with a fast, accessible, secure platform.',
        'features': [('Fast by default', 'Optimised for speed and Core Web Vitals'),
                     ('Secure by design', 'Auth, encryption and audit logging'),
                     ('Integrations', 'Connect the tools your team already uses'),
                     ('Built to scale', 'From prototype to production')],
    },
    'automotive': {
        'eyebrow': 'DRIVE SOMETHING EXCEPTIONAL', 'tagline': 'Your next car, found faster',
        'hero_desc': '{brand} puts a curated inventory, transparent pricing and instant finance at your fingertips.',
        'features': [('Curated inventory', 'Hand-picked vehicles, verified and photographed'),
                     ('Transparent pricing', 'No hidden fees — the price you see is the price'),
                     ('Instant finance', 'Get pre-approved in minutes, not days'),
                     ('Nationwide delivery', 'Delivered to your door, fully inspected')],
    },
    'realestate': {
        'eyebrow': 'FIND YOUR NEXT ADDRESS', 'tagline': 'Homes that match your life',
        'hero_desc': '{brand} pairs local expertise with data-driven search to find the right property, faster.',
        'features': [('Verified listings', 'Every home vetted before it reaches you'),
                     ('Neighbourhood data', 'Schools, commute and growth at a glance'),
                     ('Expert agents', 'Local specialists who know the block'),
                     ('Seamless viewings', 'Book, tour and offer in one place')],
    },
    'fitness': {
        'eyebrow': 'TRAIN WITH PURPOSE', 'tagline': 'Stronger every single session',
        'hero_desc': '{brand} combines expert coaching, smart programming and real accountability.',
        'features': [('Personal coaching', 'Plans built around your goals'),
                     ('Smart programming', 'Progressive sessions that adapt'),
                     ('Track everything', 'Strength, stamina and progress in one place'),
                     ('Community', 'Train alongside people who show up')],
    },
    'gym': {
        'eyebrow': 'YOUR STRONGEST SELF', 'tagline': 'Where commitment meets results',
        'hero_desc': '{brand} pairs world-class equipment with coaching that keeps you consistent.',
        'features': [('Modern equipment', 'Everything you need, always available'),
                     ('Expert trainers', 'Guidance that fits your goals'),
                     ('Flexible plans', 'Membership on your terms'),
                     ('Recovery zone', 'Sauna, stretch and mobility space')],
    },
    'insurance': {
        'eyebrow': 'CLAIMS MADE SIMPLE', 'tagline': 'Coverage you can actually understand',
        'hero_desc': '{brand} turns confusing policies into clear cover and fast, fair claims.',
        'features': [('Clear cover', 'Plain-language policies, no fine print games'),
                     ('Fast claims', 'File and track in minutes'),
                     ('Fair pricing', 'Quotes tailored, not guessed'),
                     ('Human support', 'Real people, real answers')],
    },
    'wedding': {
        'eyebrow': 'EVERY DETAIL, PERFECTED', 'tagline': 'Your day, exactly as imagined',
        'hero_desc': '{brand} brings venues, vendors and planning together so you can enjoy the moment.',
        'features': [('Curated venues', 'Spaces that match your vision'),
                     ('Trusted vendors', 'Vetted florists, caterers and more'),
                     ('Planning tools', 'Budgets, timelines and checklists'),
                     ('Day-of support', 'A coordinator so nothing slips')],
    },
    'event': {
        'eyebrow': 'MOMENTS WORTH REMEMBERING', 'tagline': 'Epic events, effortlessly planned',
        'hero_desc': '{brand} handles discovery, booking and logistics so you can focus on the experience.',
        'features': [('Discover venues', 'Spaces for every occasion'),
                     ('Instant booking', 'Availability and pricing up front'),
                     ('Vendor marketplace', 'Catering, AV and décor in one place'),
                     ('Guest management', 'Invites, RSVPs and seating, simplified')],
    },
    'travel': {
        'eyebrow': 'EXPERIENCES WORTH THE JOURNEY', 'tagline': 'Travel curated for you',
        'hero_desc': '{brand} designs journeys that balance discovery, comfort and value.',
        'features': [('Curated itineraries', 'Trips shaped by experts'),
                     ('Flexible booking', 'Change plans without the stress'),
                     ('Local experiences', 'Go beyond the guidebook'),
                     ('24/7 support', 'Help wherever the road takes you')],
    },
    'creative': {
        'eyebrow': 'IDEAS MADE TANGIBLE', 'tagline': 'Design with intent',
        'hero_desc': '{brand} turns strategy into brand, product and motion that actually perform.',
        'features': [('Brand systems', 'Identities built to scale'),
                     ('Product design', 'Interfaces people love to use'),
                     ('Motion & film', 'Stories that move'),
                     ('Strategy', 'Clarity before craft')],
    },
    'portfolio': {
        'eyebrow': 'SELECTED WORK', 'tagline': 'Craft, evidence and impact',
        'hero_desc': 'A focused portfolio from {brand}, showing process, craft and measurable results.',
        'features': [('Case studies', 'Problem, approach and outcome'),
                     ('Process', 'How the work actually gets made'),
                     ('Capabilities', 'What I can do for your team'),
                     ('Contact', 'Start a conversation')],
    },
    'fintech': {
        'eyebrow': 'MONEY, MADE SIMPLE', 'tagline': 'Financial clarity with confidence',
        'hero_desc': '{brand} gives individuals and teams secure, transparent control over their finances.',
        'features': [('Secure by default', 'Bank-grade encryption and controls'),
                     ('Real-time insight', 'See where money moves, instantly'),
                     ('Automated workflows', 'Approvals, reports and reconciliation'),
                     ('Human support', 'Experts when you need them')],
    },
    'marketplace': {
        'eyebrow': 'BUY, SELL, CONNECT', 'tagline': 'The trusted place to trade',
        'hero_desc': '{brand} connects buyers and sellers with verified profiles and secure transactions.',
        'features': [('Verified members', 'Trust built into every listing'),
                     ('Secure payments', 'Protected from click to delivery'),
                     ('Smart search', 'Find exactly what you need'),
                     ('Fair resolution', 'Support when things go wrong')],
    },
    'ecommerce': {
        'eyebrow': 'SHOP THE COLLECTION', 'tagline': 'Quality, delivered',
        'hero_desc': '{brand} curates products worth owning, with fast, reliable delivery.',
        'features': [('Curated range', 'Only what is worth your money'),
                     ('Fast delivery', 'Tracked from warehouse to door'),
                     ('Easy returns', 'Change your mind without the hassle'),
                     ('Secure checkout', 'Pay the way you want')],
    },
    'healthcare': {
        'eyebrow': 'CARE YOU CAN TRUST', 'tagline': 'Health, handled with care',
        'hero_desc': '{brand} makes booking, consultation and follow-up simple and human.',
        'features': [('Expert clinicians', 'Qualified, vetted professionals'),
                     ('Easy booking', 'Appointments that fit your day'),
                     ('Clear records', 'Your history, always accessible'),
                     ('Continuity', 'Care that follows you')],
    },
    'education': {
        'eyebrow': 'LEARN WITHOUT LIMITS', 'tagline': 'Skills that move you forward',
        'hero_desc': '{brand} delivers structured courses and mentorship that turn effort into outcomes.',
        'features': [('Structured paths', 'From beginner to job-ready'),
                     ('Expert mentors', 'Guidance from practitioners'),
                     ('Hands-on projects', 'Build a portfolio as you learn'),
                     ('Flexible pace', 'Study on your schedule')],
    },
    'restaurant': {
        'eyebrow': 'TASTE THE DIFFERENCE', 'tagline': 'Seasonal, local, memorable',
        'hero_desc': '{brand} serves menus built on fresh, seasonal ingredients and genuine hospitality.',
        'features': [('Seasonal menu', 'Ingredients at their best'),
                     ('Book a table', 'Reserve in seconds'),
                     ('Private dining', 'Spaces for every occasion'),
                     ('Local sourcing', 'Produce from people we know')],
    },
    'lawfirm': {
        'eyebrow': 'COUNSEL YOU CAN RELY ON', 'tagline': 'Clear advice, strong advocacy',
        'hero_desc': '{brand} delivers pragmatic legal counsel with transparent pricing and real communication.',
        'features': [('Specialist expertise', 'Lawyers who know your field'),
                     ('Transparent fees', 'No surprises on the bill'),
                     ('Clear communication', 'Plain language, timely updates'),
                     ('Proven results', 'A track record that speaks')],
    },
}

_ATTRIBUTE_KEYS = ('minimalism', 'whitespace', 'typography', 'motion', 'color_saturation',
                   'craft', 'cta_focus', 'interaction_complexity', 'visual_density',
                   'content_density', 'bold', 'cinematic', 'futuristic')


# ── small helpers ─────────────────────────────────────────────────────────────
def _slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', (name or '').lower()).strip('-') or 'project'


def _sha(seed: str) -> int:
    return int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:8], 16)


def _hex_to_rgb_triplet(value: str) -> str:
    h = (value or '').strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return '15 23 42'
    return f'{int(h[0:2], 16)} {int(h[2:4], 16)} {int(h[4:6], 16)}'


def _is_hex(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith('#'):
        return False
    h = value[1:]
    return len(h) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in h)


def _rotate_hue(value: str, degrees: float) -> str:
    """Rotate a hex colour's hue, preserving saturation/lightness."""
    h = (value or '').lstrip('#')
    if len(h) != 6:
        return value
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    hh = (hh + degrees / 360.0) % 1.0
    r, g, b = colorsys.hls_to_rgb(hh, ll, ss)
    return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))


def _luminance(value: str) -> float:
    """WCAG relative luminance (0 dark → 1 light) for a hex colour."""
    h = (value or '').lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return 1.0
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    ch = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _repo_root() -> Path:
    """Walk up until the registry that anchors this monorepo is found."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / 'registry' / 'design-resources.json').exists():
            return parent
    return here.parent.parent.parent


def _load_registry_attributes() -> Dict[str, float]:
    """Mean attribute profile across registered design resources (offline)."""
    data = _read_json(_repo_root() / 'registry' / 'design-resources.json') or {}
    buckets: Dict[str, List[float]] = {}
    for res in data.get('resources', []):
        attrs = res.get('attributes') or {}
        for k, v in attrs.items():
            if isinstance(v, (int, float)):
                buckets.setdefault(k, []).append(float(v))
    return {k: round(sum(v) / len(v), 3) for k, v in buckets.items() if v}


def _svg_to_html(svg: str) -> str:
    """React-style SVG attrs → HTML attrs for dangerouslySetInnerHTML."""
    return (svg.replace('className=', 'class=')
               .replace('stopColor=', 'stop-color=')
               .replace('strokeWidth=', 'stroke-width=')
               .replace('strokeLinecap=', 'stroke-linecap=')
               .replace('stopOpacity=', 'stop-opacity='))


# ── engine ────────────────────────────────────────────────────────────────────
class LayoutEngine:
    """Discover, plan, restyle and revert the presentation shell of any project."""

    def __init__(self, project_dir: str) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.design = DesignStyleEngine()
        self.unique = HyperUniqueSiteEngine()

    # ── discovery ────────────────────────────────────────────────────────────
    def discover(self) -> Dict[str, Any]:
        root = self.project_dir
        frontend = root / 'frontend' if (root / 'frontend' / 'package.json').exists() else root
        src = frontend / 'src'
        pkg = _read_json(frontend / 'package.json') or {}
        name = pkg.get('name') or root.name

        entry = None
        for cand in ('src/App.jsx', 'src/App.js', 'src/main.jsx', 'src/main.js'):
            if (frontend / cand).exists():
                entry = frontend / cand
                break

        routes = self._parse_routes(frontend / 'src' / 'App.jsx') if (frontend / 'src' / 'App.jsx').exists() else []

        pages = sorted(p.name for p in (src / 'pages').glob('*.jsx')) if (src / 'pages').exists() else []

        def _first(paths: List[str]) -> Optional[str]:
            for p in paths:
                if (frontend / p).exists():
                    return p
            return None

        navbar = _first(['src/components/navigation/GlassNavbar.jsx', 'src/components/Navbar.jsx',
                         'src/components/layout/Navbar.jsx'])
        footer = _first(['src/components/Footer.jsx', 'src/components/layout/Footer.jsx'])
        brand_dir = (src / 'components' / 'brand')
        i18n = (src / 'i18n').exists() or (src / 'i18n.js').exists() or (src / 'i18n' / 'index.js').exists()
        index_html = frontend / 'index.html'

        return {
            'project_dir': str(root),
            'frontend': str(frontend),
            'src': str(src),
            'package_name': name,
            'entry': str(entry) if entry else None,
            'index_html': str(index_html) if index_html.exists() else None,
            'routes': routes,
            'pages': pages,
            'has_navbar': bool(navbar),
            'navbar': navbar,
            'has_footer': bool(footer),
            'footer': footer,
            'has_brand_dir': brand_dir.exists(),
            'has_i18n': bool(i18n),
            'has_tailwind_config': (frontend / 'tailwind.config.js').exists(),
            'index_css': str(src / 'index.css') if (src / 'index.css').exists() else None,
            'restyleable': bool(pkg) and bool(src.exists()),
        }

    @staticmethod
    def _parse_routes(app_jsx: Path) -> List[Dict[str, str]]:
        try:
            text = app_jsx.read_text(encoding='utf-8')
        except Exception:
            return []
        routes: List[Dict[str, str]] = []
        for m in re.finditer(r'<Route\s+[^>]*path=["\']([^"\']+)["\'][^>]*element=\{<(\w+)', text):
            routes.append({'path': m.group(1), 'element': m.group(2)})
        return routes

    # ── planning (offline, deterministic) ────────────────────────────────────
    def plan(self, style: Optional[str] = None, region: str = 'default',
             industry: Optional[str] = None, brand: Optional[str] = None) -> Dict[str, Any]:
        disc = self.discover()
        brand_name = (brand or disc['package_name'] or self.project_dir.name).replace('-', ' ').replace('_', ' ').title()
        slug = _slug(brand or disc['package_name'] or self.project_dir.name)

        industry = industry or self._infer_industry(disc, brand_name)
        category = self._category_for(industry)

        from .theme_matrix import _CATEGORY_SECTIONS, _BASE_STYLE_GROUPS
        sections = list(_CATEGORY_SECTIONS.get(category) or _SECTION_FALLBACK)

        # style: explicit wins; otherwise pick deterministically from the styles
        # this industry is validated for (theme-matrix groups), else auto-suggest.
        style_seed = _sha(f'{slug}::{region}')
        if style:
            style_dict = self.design.resolve_style({'design_style': style, 'industry': industry,
                                                    'website_type': category})
        else:
            compatible = _BASE_STYLE_GROUPS.get(category) or []
            if compatible:
                pick = compatible[style_seed % len(compatible)]
                style_dict = self.design.STYLES.get(pick) or self.design.resolve_style({'industry': industry})
            else:
                style_dict = self.design.resolve_style({'industry': industry, 'website_type': category})
        style_id = style_dict['id']

        seed = _sha(f'{slug}::{style_id}::{region}')
        unique = self.unique.synthesize_hyper_unique_blueprint(f'{industry} {brand_name}', brand_name)
        registry_attrs = _load_registry_attributes()

        palette = self._merge_palette(slug, style_dict, region, unique)

        # copy: reuse pro_design's generic profile derivation (works for any name),
        # then override with category-appropriate copy so it never reads as
        # generic SaaS filler (AGENTS DL013).
        copy = dict(PROFILES.get(slug) or _derive_profile(slug))
        cat_copy = _CATEGORY_COPY.get(category)
        if cat_copy:
            for key in ('eyebrow', 'tagline', 'hero_desc'):
                if cat_copy.get(key):
                    copy[key] = cat_copy[key].format(brand=brand_name)
            if cat_copy.get('features'):
                copy['features'] = cat_copy['features']

        motion_level = 'high' if registry_attrs.get('motion', 0) >= 0.6 else (
            'low' if registry_attrs.get('motion', 0) < 0.35 else 'medium')

        return {
            'engine': ENGINE_NAME, 'version': ENGINE_VERSION,
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'project_dir': disc['project_dir'], 'frontend': disc['frontend'],
            'package_name': disc['package_name'], 'slug': slug,
            'brand': brand_name, 'title': copy.get('title', brand_name),
            'tagline': copy.get('tagline', ''), 'eyebrow': copy.get('eyebrow', ''),
            'hero_desc': copy.get('hero_desc', ''),
            'features': copy.get('features', []), 'stats': copy.get('stats', []),
            'industry': industry, 'category': category, 'sections': sections,
            'style': style_id, 'style_name': style_dict.get('name', style_id),
            'region': region,
            'region_rationale': {
                'gcc': 'Gulf luxury: gold + emerald, deep neutral footer',
                'south-asia': 'South-Asian energy: saffron + green, warm canvas',
                'east-asia': 'East-Asian prosperity: red + gold, ink heading',
                'europe': 'European trust: refined blue + teal, clean light',
                'north-america': 'North-American bold: royal blue + red accent',
                'latam': 'LatAm warmth: coral + teal, energetic canvas',
                'africa': 'African earth: amber + green, grounded',
                'default': 'Global neutral (region-agnostic)',
            }.get(region, 'Global neutral'),
            'palette': palette,
            'fonts': {'display': unique['typography']['display'].split("'")[1].replace('_', ' ') if "'" in unique['typography']['display'] else style_dict['fonts']['display'],
                      'sans': unique['typography']['body'].split("'")[1].replace('_', ' ') if "'" in unique['typography']['body'] else style_dict['fonts']['sans']},
            'typography_pairing': unique['typography']['name'],
            'logo_svg': unique['svg_logo'],
            'radius': style_dict.get('radius', {}),
            'shadow': style_dict.get('shadow', {}),
            'effects': style_dict.get('effects', {}),
            'motion_level': motion_level,
            'attribute_bias': registry_attrs,
            'vault_source': style_id if style_id in VAULT_STYLES else '',
            'seed': seed,
            'notes': [],
        }

    def _merge_palette(self, slug: str, style: Dict[str, Any], region: str,
                       unique: Dict[str, Any]) -> Dict[str, str]:
        base = style.get('color', {})
        pal: Dict[str, str] = {
            'primary': base.get('primary', '#2563eb'),
            'secondary': base.get('secondary', base.get('accent', '#7c3aed')),
            'accent': base.get('accent', '#7c3aed'),
            'heading': base.get('text', '#0f172a'),
            'canvas': base.get('bg', '#ffffff'),
            'surface': base.get('surface', base.get('card', '#f8fafc')),
            'text': base.get('text', '#1f2937'),
            'muted': base.get('muted', '#64748b'),
            'border': base.get('border', '#e2e8f0'),
            'navBg': base.get('bg', '#ffffff'),
            'footerBg': base.get('text', '#0f172a'),
        }
        # brand hue from the unique engine (primary/secondary/accent only) — this
        # keeps the named style's light/dark neutrals coherent while guaranteeing
        # the accent is distinct per brand. Wholesale palette swaps would turn a
        # light style (e.g. minimalism) into an incoherent dark theme.
        up = unique.get('palette', {})
        if up:
            # fine-grained per-brand hue offset (±18°) so two projects that land
            # on the same 6-entry palette family still read as distinct brands.
            rot = (_sha(slug) % 37) - 18
            pal['primary'] = _rotate_hue(up.get('primary', pal['primary']), rot)
            pal['secondary'] = _rotate_hue(up.get('secondary', pal['secondary']), rot)
            pal['accent'] = _rotate_hue(up.get('accent', pal['accent']), rot)
        # region tuning (only where it supplies a value)
        for k, v in (REGION_PALETTES.get(region) or {}).items():
            if _is_hex(v):
                pal[k] = v
        # design-vault exact language wins if registered
        if style['id'] in VAULT_STYLES:
            for k, v in (VAULT_STYLES[style['id']].get('palette') or {}).items():
                if _is_hex(v):
                    pal[k] = v
        # always emit a complete hex palette (styles may use rgba() neutrals)
        pal = {k: (pal[k] if _is_hex(pal.get(k)) else _DEFAULT_TOKENS[k]) for k in _TOKEN_KEYS}
        # coherence pass: neutrals must match the canvas lightness, otherwise a
        # dark style inherits light-field defaults (light footer / light border).
        if _luminance(pal['canvas']) < 0.5:
            if _luminance(pal['border']) > 0.5:
                pal['border'] = '#1e293b'
            if _luminance(pal['footerBg']) > 0.5:
                pal['footerBg'] = '#020617'
        return pal

    @staticmethod
    def _infer_industry(disc: Dict[str, Any], brand_name: str) -> str:
        hay = ' '.join([disc.get('package_name', ''), brand_name,
                        ' '.join(disc.get('pages', []))]).lower()
        for kw, cat in _INDUSTRY_CATEGORY:
            if kw in hay:
                return cat
        return _DEFAULT_CATEGORY

    @staticmethod
    def _category_for(industry: str) -> str:
        from .theme_matrix import _CATEGORY_SECTIONS
        if industry in _CATEGORY_SECTIONS:
            return industry
        for kw, cat in _INDUSTRY_CATEGORY:
            if kw in (industry or '').lower():
                return cat
        return _DEFAULT_CATEGORY

    # ── apply (full restyle) ─────────────────────────────────────────────────
    def apply(self, plan: Optional[Dict[str, Any]] = None, skin: str = 'full',
              dry_run: bool = False) -> Dict[str, Any]:
        plan = plan or self.plan()
        disc = self.discover()
        frontend = Path(disc['frontend'])

        if not disc['restyleable']:
            return {'success': False, 'status': 422,
                    'message': f'Not a restyleable project (no package.json/src): {frontend}',
                    'written': [], 'backup': None, 'dry_run': dry_run}

        files = self._render_files(plan, disc, skin)
        targets = list(files.keys())
        report_rel = 'LAYOUT_REPORT.json'
        existing = [t for t in targets if (frontend / t).exists()]
        report_existed = (frontend / report_rel).exists()

        if dry_run:
            return {'success': True, 'status': 200, 'message': 'dry-run — nothing written',
                    'dry_run': True, 'skin': skin, 'would_write': targets,
                    'would_backup': existing, 'plan': plan}

        ts = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        backup_dir = self.project_dir / BACKUP_REL / ts
        for rel in existing:
            src = frontend / rel
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        if report_existed:
            dst = backup_dir / report_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(frontend / report_rel, dst)

        for rel, content in files.items():
            _write(frontend / rel, content)

        created = [t for t in targets if t not in existing]
        replaced = list(existing)
        if report_existed:
            replaced.append(report_rel)
        else:
            created.append(report_rel)
        manifest = {
            'engine': ENGINE_NAME, 'version': ENGINE_VERSION, 'marker': CSS_MARKER,
            'created_at': ts, 'skin': skin, 'backup_dir': str(backup_dir),
            'created': created, 'replaced': replaced, 'plan': plan,
        }
        _write(self.project_dir / MANIFEST_REL, json.dumps(manifest, indent=2))

        report = {'success': True, 'status': 200,
                  'message': f'layout applied ({skin}) to {frontend.name}',
                  'dry_run': False, 'skin': skin, 'written': targets,
                  'backup': str(backup_dir), 'manifest': str(self.project_dir / MANIFEST_REL),
                  'style': plan.get('style'), 'region': plan.get('region'),
                  'palette': plan.get('palette')}
        _write(frontend / report_rel, json.dumps(report, indent=2))
        return report

    def _render_files(self, plan: Dict[str, Any], disc: Dict[str, Any], skin: str) -> Dict[str, str]:
        files: Dict[str, str] = {
            'src/index.css': self._render_index_css(plan, disc),
            'tailwind.config.js': self._render_tailwind(plan),
            TOKENS_REL: json.dumps(self._tokens_doc(plan), indent=2),
            'src/components/Navbar.jsx': self._render_navbar(plan),
            'src/components/Footer.jsx': self._render_footer(plan),
            'src/components/common/UniqueLogo.jsx': self._render_logo(plan),
            'src/pages/Home.jsx': self._render_home(plan),
            'DESIGN_PLAN.md': self._render_design_plan(plan),
        }
        if disc.get('has_brand_dir'):
            files['src/components/brand/BRAND.js'] = self._render_brand(plan)
            files['src/components/brand/BrandLockup.jsx'] = self._render_brand_lockup()
        if disc.get('navbar', '').endswith('navigation/GlassNavbar.jsx'):
            files['src/components/navigation/GlassNavbar.jsx'] = self._render_glass_navbar(plan)
        return files

    def _tokens_doc(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        pal = plan['palette']
        return {
            'style': plan['style'], 'name': plan['style_name'],
            'project_name': plan['slug'], 'brand': plan['brand'],
            'palette': pal,
            'palette_rgb': {k: _hex_to_rgb_triplet(v) for k, v in pal.items()},
            'typography': {'display': plan['fonts']['display'], 'sans': plan['fonts']['sans'],
                           'pairing': plan['typography_pairing']},
            'radius': plan.get('radius', {}), 'shadow': plan.get('shadow', {}),
            'region': plan['region'], 'generated_by': ENGINE_NAME,
            'marker': CSS_MARKER,
        }

    def _render_tailwind(self, plan: Dict[str, Any]) -> str:
        return (
            "/** @type {import('tailwindcss').Config} */\n"
            "export default {\n"
            "  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],\n"
            "  darkMode: ['class', '[data-theme=\"dark\"]'],\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: {\n"
            "        primary: 'rgb(var(--t-primary-rgb, 37 99 235) / <alpha-value>)',\n"
            "        accent: 'rgb(var(--t-accent-rgb, 124 58 237) / <alpha-value>)',\n"
            "        heading: 'rgb(var(--t-heading-rgb, 15 23 42) / <alpha-value>)',\n"
            "        canvas: 'rgb(var(--t-canvas-rgb, 255 255 255) / <alpha-value>)',\n"
            "        surface: 'rgb(var(--t-surface-rgb, 248 250 252) / <alpha-value>)',\n"
            "        text: 'rgb(var(--t-text-rgb, 31 41 55) / <alpha-value>)',\n"
            "      },\n"
            "      fontFamily: {\n"
            f"        sans: ['{plan['fonts']['sans']}', 'system-ui', 'sans-serif'],\n"
            f"        display: ['{plan['fonts']['display']}', 'system-ui', 'sans-serif'],\n"
            "      },\n"
            "    },\n"
            "  },\n"
            "  plugins: [],\n"
            "};\n"
        )

    def _render_index_css(self, plan: Dict[str, Any], disc: Dict[str, Any]) -> str:
        pal = plan['palette']
        disp = plan['fonts']['display'].replace(' ', '+')
        sans = plan['fonts']['sans'].replace(' ', '+')
        lines = [
            f"@import url('https://fonts.googleapis.com/css2?family={disp}:wght@400;600;700;800&family={sans}:wght@400;500;600;700&display=swap');",
            '@tailwind base;', '@tailwind components;', '@tailwind utilities;', '',
        ]
        lines.append(self._token_block(plan))
        lines.append(self._component_layer(plan))
        return '\n'.join(lines) + '\n'

    def _token_block(self, plan: Dict[str, Any]) -> str:
        pal = plan['palette']
        out = [f'/* {CSS_MARKER} :: {ENGINE_NAME} v{ENGINE_VERSION} — generated, do not edit by hand */', ':root {']
        for k in _TOKEN_KEYS:
            if k in pal:
                out.append(f'  --t-{k}: {pal[k]};')
                out.append(f'  --t-{k}-rgb: {_hex_to_rgb_triplet(pal[k])};')
        out.append(f"  --t-display-font: '{plan['fonts']['display']}', system-ui, sans-serif;")
        out.append(f"  --t-sans-font: '{plan['fonts']['sans']}', system-ui, sans-serif;")
        out.append('}')
        return '\n'.join(out)

    def _component_layer(self, plan: Dict[str, Any]) -> str:
        return (
            "\n@layer base {\n"
            "  body { background-color: var(--t-canvas); color: var(--t-text);\n"
            "    font-family: var(--t-sans-font); @apply antialiased; }\n"
            "  h1, h2, h3, h4, h5, h6 { font-family: var(--t-display-font); font-weight: 700; color: var(--t-heading); }\n"
            "}\n"
            "@layer components {\n"
            "  .btn-primary { background-color: var(--t-primary); color: #fff; padding: 0.75rem 1.75rem;\n"
            "    border-radius: 0.6rem; font-weight: 600; font-size: 0.9rem; display: inline-flex;\n"
            "    align-items: center; gap: 0.5rem; transition: all 0.2s; }\n"
            "  .btn-primary:hover { opacity: 0.92; transform: translateY(-1px);\n"
            "    box-shadow: 0 8px 20px color-mix(in srgb, var(--t-primary) 30%, transparent); }\n"
            "  .btn-outline { border: 2px solid var(--t-primary); color: var(--t-primary); padding: 0.6rem 1.6rem;\n"
            "    border-radius: 0.6rem; font-weight: 600; font-size: 0.9rem; display: inline-flex;\n"
            "    align-items: center; gap: 0.5rem; transition: all 0.2s; }\n"
            "  .btn-outline:hover { background-color: var(--t-primary); color: #fff; }\n"
            "  .card-panel { background: var(--t-surface); border: 1px solid var(--t-border);\n"
            "    border-radius: 1rem; box-shadow: 0 6px 18px color-mix(in srgb, var(--t-heading) 8%, transparent); }\n"
            "  .section-eyebrow { text-transform: uppercase; letter-spacing: 0.18em; font-size: 0.75rem;\n"
            "    font-weight: 600; color: var(--t-primary); }\n"
            "  .section-heading { font-size: clamp(1.5rem, 3vw, 2.25rem); line-height: 1.15; }\n"
            "  .hero-aurora { background:\n"
            "    radial-gradient(60% 60% at 15% 15%, color-mix(in srgb, var(--t-primary) 18%, transparent), transparent 60%),\n"
            "    radial-gradient(55% 55% at 85% 20%, color-mix(in srgb, var(--t-accent) 16%, transparent), transparent 60%),\n"
            "    var(--t-canvas); }\n"
            "  .skip-link { position: absolute; left: -999px; } .skip-link:focus { left: 1rem; top: 1rem;\n"
            "    z-index: 100; background: var(--t-surface); padding: 0.5rem 1rem; border-radius: 0.5rem; }\n"
            "  .skeleton-shimmer { background: linear-gradient(90deg, var(--t-border) 25%, var(--t-canvas) 50%, var(--t-border) 75%);\n"
            "    background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; }\n"
            "  .cls-reserve { content-visibility: auto; contain-intrinsic-size: 0 500px; }\n"
            "  @media (prefers-reduced-motion: reduce) { * { animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; } }\n"
            "}\n@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }\n"
        )

    def _render_logo(self, plan: Dict[str, Any]) -> str:
        svg = _svg_to_html(plan['logo_svg'])
        return (
            "import React from 'react';\n\n"
            f"/** UniqueLogo — {CSS_MARKER} generated vector mark for {plan['brand']}. */\n"
            "export default function UniqueLogo({ size = 40, className = '', label = '' }) {\n"
            "  return (\n"
            "    <span\n"
            "      className={className}\n"
            "      role={label ? 'img' : undefined}\n"
            "      aria-label={label || undefined}\n"
            "      aria-hidden={label ? undefined : true}\n"
            "      style={{ display: 'inline-flex', width: size, height: size }}\n"
            f"      dangerouslySetInnerHTML={{{{ __html: `{svg}` }}}}\n"
            "    />\n"
            "  );\n"
            "}\n"
        )

    def _render_brand(self, plan: Dict[str, Any]) -> str:
        pal = plan['palette']
        return (
            "// Brand constants — generated by the layout engine (single source of colour).\n"
            "export const BRAND = {\n"
            f"  name: {json.dumps(plan['brand'])},\n"
            f"  initials: {json.dumps(''.join(w[0] for w in plan['brand'].split()[:2]).upper() or 'L')},\n"
            f"  primary: {json.dumps(pal.get('primary', '#2563eb'))},\n"
            f"  secondary: {json.dumps(pal.get('secondary', '#7c3aed'))},\n"
            f"  accent: {json.dumps(pal.get('accent', '#7c3aed'))},\n"
            f"  displayFont: {json.dumps(plan['fonts']['display'])},\n"
            f"  sansFont: {json.dumps(plan['fonts']['sans'])},\n"
            "};\n\nexport default BRAND;\n"
        )

    def _render_brand_lockup(self) -> str:
        return (
            "import React from 'react';\nimport { Link } from 'react-router-dom';\n"
            "import UniqueLogo from '../common/UniqueLogo';\nimport { BRAND } from './BRAND';\n\n"
            "/** BrandLockup — mark + wordmark (layout-engine generated). */\n"
            "export default function BrandLockup({ to = '/', size = 34, dark = false, className = '' }) {\n"
            "  return (\n"
            "    <Link to={to} className={`inline-flex items-center gap-2.5 select-none hover:opacity-90 ${className}`} aria-label={BRAND.name}>\n"
            "      <UniqueLogo size={size} className=\"shrink-0\" />\n"
            "      <span className=\"font-bold tracking-tight leading-none whitespace-nowrap\"\n"
            "        style={{ fontFamily: `${BRAND.displayFont}, system-ui, sans-serif`, color: dark ? '#fff' : 'var(--t-heading)' }}>\n"
            "        {BRAND.name}\n"
            "      </span>\n"
            "    </Link>\n  );\n}\n"
        )

    def _nav_links_js(self, disc: Dict[str, Any]) -> str:
        seen, links = set(), []
        for r in disc.get('routes', []):
            p = r.get('path')
            if not p or p in seen or ':' in p:
                continue
            seen.add(p)
            label = 'Home' if p == '/' else p.strip('/').replace('-', ' ').replace('_', ' ').title()
            links.append({'path': p, 'label': label})
        if not links:
            links = [{'path': '/', 'label': 'Home'}, {'path': '/about', 'label': 'About'},
                     {'path': '/pricing', 'label': 'Pricing'}, {'path': '/contact', 'label': 'Contact'}]
        return json.dumps(links[:7])

    def _render_navbar(self, plan: Dict[str, Any]) -> str:
        links = self._nav_links_js(self.discover())
        return (
            "import React, { useState } from 'react';\nimport { Link, useLocation } from 'react-router-dom';\n"
            "import { Menu, X, ArrowRight } from 'lucide-react';\nimport BrandLockup from './brand/BrandLockup';\n\n"
            "/** Navbar — layout-engine generated. */\n"
            "export default function Navbar() {\n"
            "  const [open, setOpen] = useState(false);\n  const loc = useLocation();\n"
            f"  const links = {links};\n"
            "  return (\n"
            "    <header className=\"sticky top-0 z-50 border-b\" style={{ backgroundColor: 'color-mix(in srgb, var(--t-canvas) 88%, transparent)', borderColor: 'var(--t-border)', backdropFilter: 'blur(12px)' }}>\n"
            "      <div className=\"mx-auto flex max-w-7xl items-center justify-between px-6 py-4\">\n"
            "        <BrandLockup size={30} />\n"
            "        <nav aria-label=\"Primary\" className=\"hidden items-center gap-7 md:flex\">\n"
            "          {links.map((l) => (\n"
            "            <Link key={l.path} to={l.path} className=\"text-sm font-medium transition-opacity hover:opacity-80\"\n"
            "              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}>{l.label}</Link>\n"
            "          ))}\n"
            "        </nav>\n"
            "        <Link to=\"/pricing\" className=\"btn-primary hidden md:inline-flex\">Get started <ArrowRight className=\"h-4 w-4\" /></Link>\n"
            "        <button onClick={() => setOpen(!open)} className=\"md:hidden p-2\" aria-label=\"Toggle menu\" aria-expanded={open}>\n"
            "          {open ? <X className=\"h-6 w-6\" /> : <Menu className=\"h-6 w-6\" />}\n"
            "        </button>\n"
            "      </div>\n"
            "      {open && (\n"
            "        <div className=\"border-t px-6 py-3 md:hidden\" style={{ borderColor: 'var(--t-border)' }}>\n"
            "          {links.map((l) => (\n"
            "            <Link key={l.path} to={l.path} onClick={() => setOpen(false)} className=\"block py-2 text-sm font-medium\" style={{ color: 'var(--t-text)' }}>{l.label}</Link>\n"
            "          ))}\n"
            "        </div>\n"
            "      )}\n"
            "    </header>\n  );\n}\n"
        )

    def _render_glass_navbar(self, plan: Dict[str, Any]) -> str:
        links = self._nav_links_js(self.discover())
        return (
            "import React, { useState } from 'react';\nimport { Link, useLocation } from 'react-router-dom';\n"
            "import { Menu, X, ArrowRight } from 'lucide-react';\nimport UniqueLogo from '../common/UniqueLogo';\nimport { BRAND } from '../brand/BRAND';\n\n"
            "/** GlassNavbar — layout-engine generated (glass shell). */\n"
            "export default function GlassNavbar() {\n"
            "  const [open, setOpen] = useState(false);\n  const loc = useLocation();\n"
            f"  const links = {links};\n"
            "  return (\n"
            "    <header className=\"sticky top-0 z-50 border-b px-6 py-4\" style={{ backgroundColor: 'color-mix(in srgb, var(--t-canvas) 80%, transparent)', borderColor: 'var(--t-border)', backdropFilter: 'blur(14px)' }}>\n"
            "      <div className=\"mx-auto flex max-w-7xl items-center justify-between\">\n"
            "        <Link to=\"/\" className=\"inline-flex items-center gap-2.5\" aria-label={BRAND.name}>\n"
            "          <UniqueLogo size={32} />\n"
            "          <span className=\"font-bold tracking-tight\" style={{ fontFamily: 'var(--t-display-font)', color: 'var(--t-heading)' }}>{BRAND.name}</span>\n"
            "        </Link>\n"
            "        <nav aria-label=\"Primary\" className=\"hidden items-center gap-7 md:flex\">\n"
            "          {links.map((l) => (\n"
            "            <Link key={l.path} to={l.path} className=\"text-sm font-medium transition-colors\" style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}>{l.label}</Link>\n"
            "          ))}\n"
            "          <Link to=\"/pricing\" className=\"btn-primary\">Get started <ArrowRight className=\"h-4 w-4\" /></Link>\n"
            "        </nav>\n"
            "        <button onClick={() => setOpen(!open)} className=\"md:hidden p-2\" aria-label=\"Toggle menu\" aria-expanded={open}>\n"
            "          {open ? <X className=\"h-6 w-6\" /> : <Menu className=\"h-6 w-6\" />}\n"
            "        </button>\n"
            "      </div>\n"
            "      {open && (\n"
            "        <div className=\"mt-4 flex flex-col gap-3 border-t pt-4 md:hidden\" style={{ borderColor: 'var(--t-border)' }}>\n"
            "          {links.map((l) => (\n"
            "            <Link key={l.path} to={l.path} onClick={() => setOpen(false)} className=\"text-sm font-medium\" style={{ color: 'var(--t-text)' }}>{l.label}</Link>\n"
            "          ))}\n"
            "        </div>\n"
            "      )}\n"
            "    </header>\n  );\n}\n"
        )

    def _render_footer(self, plan: Dict[str, Any]) -> str:
        year = time.strftime('%Y')
        cols = json.dumps(plan.get('sections', [])[:6])
        return (
            "import React from 'react';\nimport { Link } from 'react-router-dom';\n"
            "import { CheckCircle2 } from 'lucide-react';\nimport BrandLockup from './brand/BrandLockup';\nimport { BRAND } from './brand/BRAND';\n\n"
            "/** Footer — layout-engine generated (multi-column, live status). */\n"
            "export default function Footer() {\n"
            f"  const sections = {cols};\n"
            "  return (\n"
            "    <footer className=\"text-white\" style={{ backgroundColor: 'var(--t-footerBg)' }}>\n"
            "      <div className=\"mx-auto grid max-w-7xl gap-10 px-6 py-16 sm:grid-cols-2 lg:grid-cols-4\">\n"
            "        <div className=\"space-y-4\">\n"
            "          <BrandLockup size={30} dark />\n"
            f"          <p className=\"max-w-xs text-sm leading-relaxed text-white/70\">{plan['tagline'] or plan['hero_desc']}</p>\n"
            "          <div className=\"inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300\">\n"
            "            <span className=\"h-2 w-2 rounded-full bg-emerald-400 animate-pulse\" />99.99% Operational\n"
            "          </div>\n"
            "        </div>\n"
            "        <div>\n"
            "          <h4 className=\"mb-3 text-xs font-semibold uppercase tracking-wider\">Product</h4>\n"
            "          <ul className=\"space-y-2 text-sm text-white/70\">\n"
            "            {sections.slice(0, 4).map((s) => (<li key={s}><Link to=\"/\" className=\"hover:text-white\">{s}</Link></li>))}\n"
            "          </ul>\n"
            "        </div>\n"
            "        <div>\n"
            "          <h4 className=\"mb-3 text-xs font-semibold uppercase tracking-wider\">Company</h4>\n"
            "          <ul className=\"space-y-2 text-sm text-white/70\">\n"
            "            <li><Link to=\"/about\" className=\"hover:text-white\">About</Link></li>\n"
            "            <li><Link to=\"/contact\" className=\"hover:text-white\">Contact</Link></li>\n"
            "            <li><Link to=\"/privacy\" className=\"hover:text-white\">Privacy</Link></li>\n"
            "            <li><Link to=\"/terms\" className=\"hover:text-white\">Terms</Link></li>\n"
            "          </ul>\n"
            "        </div>\n"
            "        <div>\n"
            "          <h4 className=\"mb-3 text-xs font-semibold uppercase tracking-wider\">Stay updated</h4>\n"
            "          <p className=\"mb-3 text-xs text-white/60\">Product news and insights.</p>\n"
            "          <form onSubmit={(e) => e.preventDefault()} className=\"flex gap-2\">\n"
            "            <input type=\"email\" required placeholder=\"Email address\" aria-label=\"Email address\"\n"
            "              className=\"w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white placeholder-white/50 focus:outline-none\" />\n"
            "            <button type=\"submit\" className=\"rounded-lg bg-white/15 px-3 py-2 text-xs font-semibold text-white\">Join</button>\n"
            "          </form>\n"
            "          <div className=\"mt-3 flex items-center gap-1.5 text-xs text-emerald-300\"><CheckCircle2 className=\"h-4 w-4\" /> GDPR-ready</div>\n"
            "        </div>\n"
            "      </div>\n"
            "      <div className=\"border-t border-white/10\">\n"
            "        <div className=\"mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-6 py-4 text-xs text-white/60\">\n"
            f"          <span>© {year} {plan['brand']} — {plan['tagline']}</span>\n"
            "          <span>React 19 · Vite · Tailwind</span>\n"
            "        </div>\n"
            "      </div>\n"
            "    </footer>\n  );\n}\n"
        )

    def _render_home(self, plan: Dict[str, Any]) -> str:
        features = json.dumps([{'title': t, 'detail': d} for t, d in plan.get('features', [])])
        stats = json.dumps([{'value': v, 'label': l} for v, l in plan.get('stats', [])])
        sections = json.dumps(plan.get('sections', []))
        return (
            "import React from 'react';\nimport { Link } from 'react-router-dom';\n"
            "import { ArrowRight, CheckCircle2 } from 'lucide-react';\n"
            "import Navbar from '../components/Navbar';\nimport Footer from '../components/Footer';\n\n"
            f"/** Home — {CSS_MARKER} layout-engine generated for {plan['brand']}. */\n"
            "export default function Home() {\n"
            f"  const features = {features};\n  const stats = {stats};\n  const sections = {sections};\n"
            "  return (\n"
            "    <div className=\"min-h-screen\" style={{ backgroundColor: 'var(--t-canvas)', color: 'var(--t-text)' }}>\n"
            "      <a href=\"#main-content\" className=\"skip-link\">Skip to content</a>\n"
            "      <Navbar />\n"
            "      <main id=\"main-content\">\n"
            "        <section className=\"hero-aurora relative overflow-hidden\">\n"
            "          <div className=\"mx-auto grid max-w-7xl items-center gap-12 px-6 py-24 lg:grid-cols-12 lg:py-32\">\n"
            "            <div className=\"lg:col-span-7\">\n"
            f"              <p className=\"section-eyebrow\">{plan['eyebrow']}</p>\n"
            "              <h1 className=\"mt-5 max-w-3xl text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl\" style={{ color: 'var(--t-heading)' }}>\n"
            f"                {plan['tagline'] or plan['brand']}\n"
            "              </h1>\n"
            f"              <p className=\"mt-6 max-w-xl text-lg leading-relaxed\" style={{{{ color: 'var(--t-muted)' }}}}>{plan['hero_desc']}</p>\n"
            "              <div className=\"mt-9 flex flex-wrap gap-4\">\n"
            "                <Link to=\"/pricing\" className=\"btn-primary\">Get started <ArrowRight className=\"h-4 w-4\" /></Link>\n"
            "                <Link to=\"/contact\" className=\"btn-outline\">Talk to us</Link>\n"
            "              </div>\n"
            "            </div>\n"
            "            <div className=\"lg:col-span-5\">\n"
            "              <div className=\"card-panel p-6\">\n"
            f"                <p className=\"text-xs uppercase tracking-[.25em]\" style={{{{ color: 'var(--t-primary)' }}}}>{plan['brand']}</p>\n"
            "                <ul className=\"mt-4 space-y-3\">\n"
            "                  {features.slice(0, 4).map((f) => (\n"
            "                    <li key={f.title} className=\"flex items-start gap-2 text-sm\">\n"
            "                      <CheckCircle2 className=\"mt-0.5 h-4 w-4 shrink-0\" style={{ color: 'var(--t-primary)' }} />{f.title}\n"
            "                    </li>\n"
            "                  ))}\n"
            "                </ul>\n"
            "              </div>\n"
            "            </div>\n"
            "          </div>\n"
            "        </section>\n"
            "        <section className=\"mx-auto max-w-7xl px-6 py-20 lg:py-28\">\n"
            "          <div className=\"mb-10 max-w-2xl\">\n"
            "            <p className=\"section-eyebrow\">What we build</p>\n"
            "            <h2 className=\"section-heading mt-2\" style={{ color: 'var(--t-heading)' }}>Everything you need, in one place.</h2>\n"
            "          </div>\n"
            "          <div className=\"grid gap-6 md:grid-cols-2 lg:grid-cols-4\">\n"
            "            {features.map((f) => (\n"
            "              <article key={f.title} className=\"card-panel p-6\">\n"
            "                <h3 className=\"text-lg font-bold\" style={{ color: 'var(--t-heading)' }}>{f.title}</h3>\n"
            "                <p className=\"mt-2 text-sm leading-relaxed\" style={{ color: 'var(--t-muted)' }}>{f.detail}</p>\n"
            "              </article>\n"
            "            ))}\n"
            "          </div>\n"
            "        </section>\n"
            "        <section className=\"py-16\" style={{ backgroundColor: 'var(--t-surface)' }}>\n"
            "          <div className=\"mx-auto grid max-w-7xl gap-8 px-6 sm:grid-cols-2 lg:grid-cols-4\">\n"
            "            {stats.map((s) => (\n"
            "              <div key={s.label} className=\"text-center\">\n"
            "                <div className=\"text-3xl font-black\" style={{ color: 'var(--t-primary)' }}>{s.value}</div>\n"
            "                <div className=\"mt-1 text-sm\" style={{ color: 'var(--t-muted)' }}>{s.label}</div>\n"
            "              </div>\n"
            "            ))}\n"
            "          </div>\n"
            "        </section>\n"
            "        <section className=\"mx-auto max-w-7xl px-6 py-20\">\n"
            "          <p className=\"section-eyebrow\">Platform</p>\n"
            "          <h2 className=\"section-heading mt-2 mb-8\" style={{ color: 'var(--t-heading)' }}>Built as a complete system.</h2>\n"
            "          <div className=\"flex flex-wrap gap-3\">\n"
            "            {sections.map((s) => (\n"
            "              <span key={s} className=\"rounded-full border px-4 py-2 text-sm\" style={{ borderColor: 'var(--t-border)', color: 'var(--t-muted)' }}>{s}</span>\n"
            "            ))}\n"
            "          </div>\n"
            "        </section>\n"
            "        <section className=\"mx-auto max-w-5xl px-6 py-20 text-center\">\n"
            "          <h2 className=\"section-heading\" style={{ color: 'var(--t-heading)' }}>Ready to get started?</h2>\n"
            f"          <p className=\"mx-auto mt-4 max-w-xl\" style={{{{ color: 'var(--t-muted)' }}}}>{plan['hero_desc']}</p>\n"
            "          <Link to=\"/pricing\" className=\"btn-primary mt-7\">Get started <ArrowRight className=\"h-4 w-4\" /></Link>\n"
            "        </section>\n"
            "      </main>\n"
            "      <Footer />\n"
            "    </div>\n  );\n}\n"
        )

    def _render_design_plan(self, plan: Dict[str, Any]) -> str:
        rows = '\n'.join(f'| `--t-{k}` | `{v}` |' for k, v in plan['palette'].items())
        feats = '\n'.join(f'- **{t}** — {d}' for t, d in plan.get('features', []))
        return (
            "# Design Plan\n\n"
            "Generated by the layout engine (`layout-engine`) before the shell was rebuilt.\n\n"
            f"- **Project**: {plan['package_name']}\n"
            f"- **Brand**: {plan['brand']}\n"
            f"- **Style**: {plan['style_name']} (`{plan['style']}`)\n"
            f"- **Industry / category**: {plan['industry']} / {plan['category']}\n"
            f"- **Target market**: {plan['region']} — {plan['region_rationale']}\n"
            f"- **Typography**: {plan['typography_pairing']} ({plan['fonts']['display']} + {plan['fonts']['sans']})\n"
            f"- **Motion level**: {plan['motion_level']}\n"
            f"- **Design Vault source**: {plan['vault_source'] or 'built-in wheel'}\n\n"
            "## Color system\n\n| Token | Value |\n|-------|-------|\n" + rows + "\n\n"
            "## Feature set\n\n" + feats + "\n\n"
            f"_Marker: `{CSS_MARKER}`. Revert with `python -m agent.layout_engine <project> --revert`._\n"
        )

    # ── revert ───────────────────────────────────────────────────────────────
    def revert(self) -> Dict[str, Any]:
        manifest_path = self.project_dir / MANIFEST_REL
        manifest = _read_json(manifest_path)
        if not manifest:
            return {'success': False, 'status': 404, 'message': 'no layout manifest — nothing to revert'}
        backup_dir = Path(manifest.get('backup_dir', ''))
        frontend = Path(self.discover()['frontend'])
        restored, removed = [], []
        for rel in manifest.get('replaced', []):
            src = backup_dir / rel
            if src.exists():
                dst = frontend / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                restored.append(rel)
        for rel in manifest.get('created', []):
            target = frontend / rel
            if target.exists():
                target.unlink()
                removed.append(rel)
        manifest_path.unlink(missing_ok=True)
        return {'success': True, 'status': 200, 'message': 'layout reverted',
                'restored': restored, 'removed': removed}


# ── CLI ───────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='layout_engine', description='Generic international layout engine')
    p.add_argument('project_dir', help='Project directory (containing frontend/ or package.json)')
    p.add_argument('--style', default=None, help='Design style id (e.g. aurora, bento_grid, luxury)')
    p.add_argument('--region', default='default', help='Region palette (gcc, south-asia, europe, ...)')
    p.add_argument('--industry', default=None, help='Override detected industry/category')
    p.add_argument('--brand', default=None, help='Override brand name')
    p.add_argument('--skin', default='full', choices=['presentation', 'full'])
    p.add_argument('--dry-run', action='store_true', help='Print the plan; write nothing')
    p.add_argument('--revert', action='store_true', help='Restore the last backup')
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    engine = LayoutEngine(args.project_dir)
    if args.revert:
        result = engine.revert()
    else:
        plan = engine.plan(style=args.style, region=args.region,
                           industry=args.industry, brand=args.brand)
        result = engine.apply(plan, skin=args.skin, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get('success') else 1


if __name__ == '__main__':
    raise SystemExit(main())
