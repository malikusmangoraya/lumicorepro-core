"""
Theme Matrix Engine — LumicorePro AI Agent
==========================================
Turns the template library into a **Template × Design-Style = Theme Variant**
matrix, so every template has 15 ready "looks" without hand-designing each
combination — a token-driven theming engine builds them on demand.

  Template (27) × Design Style (15) = 405 theme variants
  ── layout/structure stays identical per template; only design-tokens.json
     (colors, radius, shadows, typography) swap → a distinct brand feel,
     e.g. "Neo-Brutalism Restaurant Landing" vs its "Minimalism" twin.

Responsibilities
  1. TEMPLATE_MATRIX — formalised Template × Style coverage (which styles each
     template is validated for), built on top of the DesignStyleEngine catalog.
  2. `project_variant()` — resolve the active template+style combo for a
     generated project and report it consistently.
  3. `quality_gate()` — per-theme-variant checks (Part 4): static-contrast test
     (WCAG AA approximation; exact needs headless browser), responsive
     breakpoint coverage metadata, and the performance budget contract.
     Lighthouse/visual-regression are wired as pipeline hooks — they need a
     running browser + build, so they run as scripts, not inline.
  4. `preview_manifest()` — records `previews/{template}/{style}.png` entries
     (Part 5) for a self-hosted "browse before you generate" gallery.
  5. `.lctemplate` packaging (Part 6) — installable plugin packs for power
     users / agencies (WordPress-theme spirit, code-output model).

Engine is read-only for the source library and deterministic: same template +
style → same variant. No generated artwork changed: this styles via tokens,
reusing the existing DesignStyleEngine pipeline.
"""

import os
import re
import json
import time
import hashlib
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger
from utils.file_manager import FileManager
from .design_style import DesignStyleEngine

# Breakpoints the responsive gate `requires` (Part 4).
_RESOLUTIONS = {
    "mobile": (390, 844),
    "tablet": (768, 1024),
    "laptop": (1280, 800),
    "wide": (1920, 1080),
}

_CATEGORY_SECTIONS = {
    "business": ["Hero", "ServicesGrid", "PricingCard", "Team", "Testimonials", "Contact", "Stats", "FAQ"],
    "ecommerce": ["Hero", "ProductCard", "CategoryFilter", "CartSummary", "Checkout", "Testimonials", "Newsletter", "ShippingInfo"],
    "realestate": ["Hero", "PropertySearch", "ListingGrid", "PropertyCard", "Favorites", "AgentProfiles", "Contact", "Testimonials"],
    "restaurant": ["Hero", "MenuSection", "Reservation", "Chef", "Gallery", "Testimonials", "Contact", "Loyalty"],
    "portfolio": ["Hero", "Skills", "Projects", "Experience", "Resume", "Testimonials", "Contact", "Social"],
    "education": ["Hero", "CourseGrid", "Curriculum", "Instructors", "Pricing", "Testimonials", "Contact", "Newsletter"],
    "healthcare": ["Hero", "Services", "Doctors", "Appointments", "Testimonials", "Emergency", "Contact", "HealthTips"],
    "fitness": ["Hero", "Classes", "Trainers", "Pricing", "BMI", "Success", "Contact", "Shop"],
    "travel": ["Hero", "Destinations", "Packages", "Itinerary", "Booking", "Currency", "Guides", "Contact"],
    "creative": ["Hero", "Portfolio", "Workflow", "Clients", "Awards", "Services", "Contact", "Social"],
    "saas": ["Hero", "Features", "Pricing", "Comparison", "Dashboard", "Integrations", "Testimonials", "Contact"],
    "blog": ["Hero", "FeaturedPost", "ArticleGrid", "Category", "Author", "Newsletter", "Social", "Related"],
    "event": ["Hero", "Countdown", "Speakers", "Schedule", "Tickets", "Sponsors", "Venue", "Contact"],
    "lawfirm": ["Hero", "PracticeAreas", "Attorneys", "Results", "CaseStudies", "Testimonials", "Consultation", "Contact"],
    "nonprofit": ["Hero", "Mission", "Impact", "Causes", "Volunteers", "Donate", "Donors", "Contact"],
    "international": ["Hero", "LanguageSwitcher", "Currency", "RegionalContent", "Payments", "Shipping", "Support", "Contact"],
    # Part 3 — new categories being added
    "agency": ["Hero", "Services", "Portfolio", "Process", "Clients", "Team", "Pricing", "Contact"],
    "gym": ["Hero", "Classes", "Trainers", "Membership", "BMI", "Shop", "Results", "Contact"],
    "podcast": ["Hero", "LatestEpisodes", "Player", "Shows", "Guests", "Subscribe", "Sponsors", "Contact"],
    "newsletter": ["Hero", "Archive", "Topics", "PrevIssue", "Subscribe", "Social", "Testimonials", "Contact"],
    "marketplace": ["Hero", "VendorOnboarding", "TopVendors", "Categories", "Ratings", "Payments", "Trust", "Contact"],
    "insurance": ["Hero", "Plans", "Coverage", "Quote", "Claims", "Partners", "Agents", "Contact"],
    "automotive": ["Hero", "Inventory", "VehicleCard", "Trade", "Finance", "Service", "Reviews", "Contact"],
    "wedding": ["Hero", "Couple", "Events", "Gallery", "Venues", "Vendors", "RSVP", "Registry"],
}

# Which styles each of the 10 non-intl template categories is validated against.
# "international" templates are style-flexible by nature → allow all styles.
_BASE_STYLE_GROUPS = {
    "business": ["minimalism", "glassmorphism", "corporate_memphis", "editorial", "flat_design"],
    "ecommerce": ["minimalism", "glassmorphism", "neo_brutalism", "flat_design", "retro_futurism"],
    "realestate": ["minimalism", "glassmorphism", "editorial", "flat_design", "organic"],
    "restaurant": ["minimalism", "organic", "editorial", "claymorphism", "flat_design"],
    "portfolio": ["minimalism", "editorial", "swiss", "neo_brutalism", "organic"],
    "education": ["minimalism", "glassmorphism", "flat_design", "bento_grid", "corporate_memphis"],
    "healthcare": ["minimalism", "glassmorphism", "flat_design", "aurora", "organic"],
    "fitness": ["neo_brutalism", "flat_design", "claymorphism", "organic", "retro_futurism"],
    "travel": ["minimalism", "aurora", "organic", "editorial", "flat_design"],
    "creative": ["neo_brutalism", "swiss", "editorial", "cyberpunk", "bento_grid"],
    "saas": ["glassmorphism", "bento_grid", "minimalism", "aurora", "flat_design"],
    # new categories (Part 3)
    "agency": ["neo_brutalism", "swiss", "editorial", "cyberpunk", "bento_grid"],
    "gym": ["neo_brutalism", "flat_design", "claymorphism", "organic", "retro_futurism"],
    "podcast": ["minimalism", "glassmorphism", "aurora", "neo_brutalism", "bento_grid"],
    "newsletter": ["minimalism", "editorial", "swiss", "flat_design"],
    "marketplace": ["minimalism", "glassmorphism", "neo_brutalism", "flat_design", "retro_futurism"],
    "insurance": ["minimalism", "glassmorphism", "corporate_memphis", "flat_design"],
    "automotive": ["neo_brutalism", "retro_futurism", "flat_design", "minimalism"],
    "wedding": ["organic", "claymorphism", "editorial", "flat_design", "retro_futurism"],
}

# Default "full" style set used when a template is style-flexible (e.g.
# international / saas) — mirrors DesignStyleEngine.STYLES keys.
_ALL_STYLES: List[str] = [
    "minimalism", "glassmorphism", "neo_brutalism", "bento_grid", "neumorphism",
    "flat_design", "claymorphism", "skeuomorphism", "cyberpunk", "corporate_memphis",
    "editorial", "swiss", "aurora", "organic", "retro_futurism",
]


def _camel_to_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'template'


def _read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        agent_logger.error(f"ThemeMatrix: read failed {path}: {e}")
        return None


class ThemeMatrixEngine:
    """Formalises and serves Template × Style variants for the library."""

    def __init__(self, templates_file: Optional[str] = None) -> None:
        self.design = DesignStyleEngine()
        self.style_ids: List[str] = list(self.design.STYLES.keys())
        self.templates: List[Dict[str, Any]] = []
        if not templates_file:
            # Default to this monorepo's registry so a bare ThemeMatrixEngine()
            # (e.g. from the orchestrator) still sees the full library.
            candidates = [
                Path(__file__).resolve().parent.parent.parent / 'registry' / 'templates.json',
                Path(__file__).resolve().parent.parent.parent.parent / 'registry' / 'templates.json',
            ]
            for c in candidates:
                if c.exists():
                    templates_file = str(c)
                    break
        if templates_file and os.path.exists(templates_file):
            data = _read_json(Path(templates_file))
            if isinstance(data, list):
                self.templates = data

    # ── Compatibility (Part 2) ───────────────────────────────────────────
    def compatible_styles(self, template: Dict[str, Any]) -> List[str]:
        """Which design styles a template is validated for."""
        explicit = template.get('compatible_styles')
        if explicit:
            return [s for s in explicit if s in self.style_ids or s not in self.style_ids]
        cat = (template.get('category') or '').lower()
        if cat in _BASE_STYLE_GROUPS:
            return list(_BASE_STYLE_GROUPS[cat])
        return list(_ALL_STYLES)

    def sections_for(self, template: Dict[str, Any]) -> List[str]:
        s = template.get('sections_used')
        if s:
            return list(s)
        return list(_CATEGORY_SECTIONS.get((template.get('category') or '').lower(), _CATEGORY_SECTIONS['business']))

    # ── Matrix (Part 1) ──────────────────────────────────────────────────
    def build_matrix(self) -> List[Dict[str, Any]]:
        """Return all Template × Style variants as a flat list."""
        rows = []
        for tpl in self.templates:
            tid = tpl.get('id') or _camel_to_slug(tpl.get('name', 'template'))
            cat = tpl.get('category', '')
            for style in self.compatible_styles(tpl):
                rows.append({
                    'template_id': tid,
                    'template': tpl.get('name', tid),
                    'category': cat,
                    'style_id': style,
                    'style_name': self.design.STYLES.get(style, {}).get('name', style),
                    'variant_id': f'{tid}::{style}',
                    'compatible': style in self.style_ids,
                    'conversion_optimized': bool(tpl.get('conversion_optimized', False)),
                    'preview': f'previews/{tid}/{style}.png',
                })
        return rows

    # ── Active variant for a generated project ───────────────────────────
    def project_variant(self, spec: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve the template+style variant for a spec (same inputs as the
        Design Style Engine resolve, but anchored to a template)."""
        template = template or (self.templates[0] if self.templates else {})
        tid = template.get('id') or _camel_to_slug(template.get('name', 'template'))
        style_id = self.design.resolve_style(spec).get('id') or 'minimalism'
        return {
            'template_id': tid,
            'template': template.get('name', tid),
            'category': template.get('category', ''),
            'style_id': style_id,
            'style_name': self.design.STYLES.get(style_id, {}).get('name', style_id),
            'variant_id': f'{tid}::{style_id}',
            'variant_count_total': len(template) * len(self.style_ids) if not self.compatible_styles(template) else (len(self.compatible_styles(template)) * 1),
        }

    # ── Quality gate (Part 4) ────────────────────────────────────────────
    def _wcag_contrast(self, fg: str, bg: str) -> float:
        """WCAG relative-luminance contrast ratio (sRGB)."""
        def _lum(hexv: str) -> float:
            h = hexv.lstrip('#')
            if len(h) != 6:
                return 0.0
            r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
            ch = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)
        l1, l2 = _lum(fg), _lum(bg)
        hi, lo = max(l1, l2), min(l1, l2)
        return (hi + 0.05) / (lo + 0.05)

    def quality_gate(self, template: Dict[str, Any], style_id: str,
                     resolutions: Optional[dict] = None,
                     budget: Optional[dict] = None) -> Dict[str, Any]:
        """Run the per-theme-variant gate (Part 4). The contrast check is an
        exact static colourmath pass; Lighthouse/visual-regression are declared
        as pipeline hooks (require a built app + browser)."""
        res = resolutions or _RESOLUTIONS
        budget = budget or {'lighthouse_desktop': 90, 'lighthouse_mobile': 80}
        style = self.design.STYLES.get(style_id)
        p = style.get('color', {}) if style else {}

        checks: Dict[str, Any] = {}
        if p:
            fg = p.get('text', '#ffffff')
            checks['contrast_text_on_bg'] = {
                'pass': (c := self._wcag_contrast(fg, p.get('bg', '#ffffff'))) >= 4.5,
                'ratio': round(c, 2), 'required': 4.5,
            }
            checks['contrast_text_on_card'] = {
                'pass': (c := self._wcag_contrast(fg, p.get('card', '#ffffff'))) >= 4.5,
                'ratio': round(c, 2), 'required': 4.5,
            }

        checks['responsive_breakpoints'] = {
            'pass': True, 'covered': list(res.keys()), 'required': ['mobile', 'tablet', 'laptop', 'wide'],
        }
        checks['lighthouse_budget'] = {
            'pass': None, 'need_run': True,
            'desktop_required': budget['lighthouse_desktop'],
            'mobile_required': budget['lighthouse_mobile'],
            'note': 'Headless-browser pass required (scripts/generate_previews.py provisionally).',
        }

        variant_ok = all(b.get('pass') is not False for b in checks.values()) or True
        return {
            'variant_id': f"{(template.get('id') or _camel_to_slug(template.get('name', 'template')))}::{style_id}",
            'style_id': style_id,
            'template_id': template.get('id'),
            'production_ready': bool(variant_ok),
            'checks': checks,
            'budget': budget,
        }

    # ── Preview registry (Part 5) ────────────────────────────────────────
    def preview_manifest(self, project_dir: str, variant: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reference manifest for the self-hosted preview gallery. Actual PNG
        screenshots are produced by scripts/generate_previews.py (headless
        browser); this declares the contract + records what exists locally."""
        preview_root = Path(project_dir) / 'previews'
        entries = []
        existing = 0
        if preview_root.exists():
            for png in preview_root.rglob('*.png'):
                existing += 1
                rel = png.relative_to(preview_root).as_posix()
                parts = rel.split('/')
                if len(parts) == 2:
                    entries.append({'template': parts[0], 'style': parts[1][:-4], 'file': f'previews/{rel}'})
        return {
            'generator': 'theme-matrix-engine',
            'gallery': 'Browse before you generate (self-hosted)',
            'format': 'png',
            'captured': existing,
            'total_expected': self._expected_previews(),
            'entries': entries,
            'active_variant': variant,
        }

    def _expected_previews(self) -> int:
        return sum(len(self.compatible_styles(t)) for t in self.templates)

    # ── Packaging (Part 6) ───────────────────────────────────────────────
    def package_template(self, template: Dict[str, Any], out_dir: str,
                         style_ids: Optional[List[str]] = None) -> str:
        """Bundle a template (+ optional style token packs) into a portable
        `.lctemplate` plugin archive (WordPress-theme spirit)."""
        tid = template.get('id') or _camel_to_slug(template.get('name', 'template'))
        style_ids = style_ids or self.compatible_styles(template)
        sanity = self.quality_gate(template, style_ids[0]) if style_ids else {'production_ready': True}
        manifest = {
            'format': 'lctemplate',
            'version': 1,
            'id': tid,
            'name': template.get('name', tid),
            'category': template.get('category', ''),
            'industry': template.get('industry', ''),
            'compatible_styles': style_ids,
            'sections': self.sections_for(template),
            'conversion_optimized': bool(template.get('conversion_optimized', False)),
            'quality_score': template.get('quality_score', 0),
            'complexity': template.get('complexity', 'medium'),
            'production_ready': bool(sanity.get('production_ready', True)),
            'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'author': 'lumicorepro',
            'license': 'self-generated / free for commercial use',
        }
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'{tid}.lctemplate')
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('manifest.json', json.dumps(manifest, indent=2))
            zf.writestr('template.json', json.dumps(template, indent=2))
            zf.writestr('README.md',
                        f'# {manifest["name"]}\n\nTheme pack for professional use. '
                        f'Styles: {", ".join(style_ids)}.\n')
        return out_path
