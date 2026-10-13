"""Compose generated React pages from design DNA and niche-aware blocks."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .design_system_engine import get_design_catalog, normalize_niche
from .layout_recipes import get_niche_page, get_section_copy


_SAFE_CSS_TOKEN = re.compile(r"^[#a-zA-Z0-9(),.%\s+\-/'\"]+$")
_SAFE_FONT = re.compile(r"^[a-zA-Z0-9 ,\-]+$")
_SAFE_DIMENSION = re.compile(r"^\d+(?:\.\d+)?(?:px|rem|em|%|ch|vw|vh)$")
_NICHE_HERO_COPY = {
    "insurance": ("Claims, from intake to review", "Collect incident details, documents, and review steps in one clear workflow."),
    "real_estate": ("Find a place that fits", "Explore property details and arrange a conversation about what comes next."),
    "food": ("A table for good food", "Browse the menu and plan a visit with the people you are bringing."),
    "education": ("A clear path through the material", "Review the learning outline and decide where to begin."),
    "fitness": ("Training that fits your routine", "Compare available programs and ask about coaching."),
    "portfolio": ("Selected work, thoughtfully made", "Explore projects, the decisions behind them, and ways to collaborate."),
    "creative": ("Selected work, thoughtfully made", "Explore projects, the decisions behind them, and ways to collaborate."),
    "events": ("Make room for the next gathering", "Explore the programme and find the event details that matter to you."),
    "travel": ("A journey with room to discover", "Review the itinerary, places, and practical details before you go."),
    "ecommerce": ("Explore the collection", "Browse product details and compare the options available."),
    "electronics": ("Choose the right equipment", "Compare specifications and find the product details you need."),
    "automotive": ("Explore the available vehicles", "Review vehicle details and arrange a conversation or viewing."),
    "finance": ("Understand the service before deciding", "Review how the service works and which options are available."),
    "saas": ("A workspace for the work at hand", "See the product workflow and compare the available options."),
    "technology": ("A closer look at the platform", "Explore capabilities and technical details relevant to your team."),
    "healthcare": ("Care information in one place", "Review available services and find the right way to get in touch."),
    "hospitality": ("Plan a visit that feels considered", "Explore the experience and arrange the details of your visit."),
}


def _text(value: Any) -> str:
    return html.escape(str(value or ""), quote=False).replace("{", "&#123;").replace("}", "&#125;")


def _css_value(value: Any, fallback: str) -> str:
    candidate = str(value or "").strip()
    if not candidate or not _SAFE_CSS_TOKEN.fullmatch(candidate) or "url" in candidate.lower():
        return fallback
    return candidate


def _dimension(value: Any, fallback: str) -> str:
    candidate = str(value or "").strip()
    return candidate if _SAFE_DIMENSION.fullmatch(candidate) else fallback


def _font(value: Any, fallback: str) -> str:
    candidate = str(value or "").strip().replace("'", "").replace('"', "")
    return candidate if _SAFE_FONT.fullmatch(candidate) else fallback


def _spacing_values(tokens: Dict[str, Any]) -> List[str]:
    scale = tokens.get("spacing", {}).get("scale", [])
    values = []
    for item in scale:
        if isinstance(item, (int, float)) and item >= 0:
            values.append(f"{item:g}px")
        elif isinstance(item, str) and _SAFE_DIMENSION.fullmatch(item.strip()):
            values.append(item.strip())
    return values or ["4px", "8px", "12px", "16px", "24px", "32px", "48px", "64px", "96px"]


def _type_values(tokens: Dict[str, Any]) -> List[str]:
    scale = tokens.get("typography", {}).get("scale", [])
    values = []
    for item in scale:
        if isinstance(item, (int, float)) and item > 0:
            values.append(f"{item:g}px")
        elif isinstance(item, str) and _SAFE_DIMENSION.fullmatch(item.strip()):
            values.append(item.strip())
    return values or ["12px", "14px", "16px", "18px", "24px", "30px", "36px", "48px", "64px"]


def _render_css(design_dna: Dict[str, Any]) -> str:
    tokens = design_dna.get("tokens") or {}
    colors = tokens.get("colors") or {}
    typography = tokens.get("typography") or {}
    spacing = _spacing_values(tokens)
    type_scale = _type_values(tokens)
    radius = tokens.get("radius") or {}
    shadows = tokens.get("shadows") or {}
    layout_tokens = tokens.get("layout") or {}
    border_tokens = tokens.get("borders") or {}
    layout = design_dna.get("layout") or {}
    grid = str(layout.get("grid_system") or "editorial_2_column")
    container_width = _dimension(
        layout_tokens.get("container_max"),
        "72rem" if grid == "editorial_2_column" else "80rem",
    )
    hero_columns = _css_value(
        layout_tokens.get("hero_columns"),
        "minmax(0, 1fr) minmax(0, 0.82fr)" if grid == "editorial_2_column" else "repeat(12, minmax(0, 1fr))",
    )
    tablet_breakpoint = _dimension(layout_tokens.get("tablet_breakpoint"), "48rem")
    hero_copy_span = layout_tokens.get("hero_copy_span", 7)
    hero_visual_span = layout_tokens.get("hero_visual_span", 5)
    if not isinstance(hero_copy_span, int) or not isinstance(hero_visual_span, int):
        hero_copy_span, hero_visual_span = 7, 5
    declarations = {
        "--ds-color-canvas": _css_value(colors.get("canvas"), "#ffffff"),
        "--ds-color-surface": _css_value(colors.get("surface"), "#f8fafc"),
        "--ds-color-primary": _css_value(colors.get("primary"), "#111827"),
        "--ds-color-accent": _css_value(colors.get("accent"), "#0ea5e9"),
        "--ds-color-text": _css_value(colors.get("text"), "#111827"),
        "--ds-color-on-primary": _css_value(colors.get("text_on_primary"), "#ffffff"),
        "--ds-color-muted": _css_value(colors.get("muted"), "#64748b"),
        "--ds-color-border": _css_value(colors.get("border"), "#e2e8f0"),
        "--ds-font-display": _font(typography.get("display"), "Georgia"),
        "--ds-font-body": _font(typography.get("sans"), "system-ui"),
        "--ds-radius-card": _dimension(radius.get("card"), "8px"),
        "--ds-radius-control": _dimension(radius.get("button"), "4px"),
        "--ds-shadow-card": _css_value(shadows.get("card"), "none"),
        "--ds-container-max": container_width,
        "--ds-hero-columns": hero_columns,
        "--ds-sidebar-width": _dimension(layout_tokens.get("sidebar_width"), "18rem"),
        "--ds-card-min-width": _dimension(layout_tokens.get("card_min_width"), "18rem"),
        "--ds-border-width": _dimension(border_tokens.get("width"), "1px"),
        "--ds-leading-heading": _css_value(typography.get("line_height_heading"), "1.05"),
        "--ds-leading-body": _css_value(typography.get("line_height_body"), "1.6"),
        "--ds-heading-measure": _dimension(layout_tokens.get("heading_measure"), "14ch"),
        "--ds-body-measure": _dimension(layout_tokens.get("body_measure"), "62ch"),
        "--ds-section-measure": _dimension(layout_tokens.get("section_measure"), "48rem"),
        "--ds-hero-copy-span": str(hero_copy_span),
        "--ds-hero-visual-span": str(hero_visual_span),
        "--ds-page-min-height": _dimension(layout_tokens.get("page_min_height"), "100vh"),
        "--ds-weight-strong": str(typography.get("weight_strong", 700)) if isinstance(typography.get("weight_strong", 700), int) else "700",
        "--ds-motion-reduced-duration": _dimension(tokens.get("motion", {}).get("reduced_duration"), "0.01ms"),
    }
    for index, value in enumerate(spacing, 1):
        declarations[f"--ds-space-{index}"] = value
    for index, value in enumerate(type_scale, 1):
        declarations[f"--ds-type-{index}"] = value
    root = ":root {\n" + "\n".join(f"  {key}: {value};" for key, value in declarations.items()) + "\n}\n"
    rules = """
.ds-site { min-height: var(--ds-page-min-height); color: var(--ds-color-text); background: var(--ds-color-canvas); font-family: var(--ds-font-body), sans-serif; }
.ds-site[data-navigation="workspace_sidebar"] { display: grid; grid-template-columns: var(--ds-sidebar-width) minmax(0, 1fr); }
.ds-container { width: min(100% - var(--ds-space-5), var(--ds-container-max)); margin-inline: auto; }
.ds-header { border-bottom: var(--ds-border-width) solid var(--ds-color-border); background: var(--ds-color-canvas); }
.ds-nav { display: flex; align-items: center; justify-content: space-between; gap: var(--ds-space-4); padding-block: var(--ds-space-4); }
.ds-sidebar { position: sticky; top: 0; grid-column: 1; grid-row: 1 / span 3; align-self: start; min-height: 100vh; padding: var(--ds-space-5); border-right: var(--ds-border-width) solid var(--ds-color-border); background: var(--ds-color-surface); }
.ds-sidebar .ds-nav-links { align-items: stretch; flex-direction: column; margin-block: var(--ds-space-5); }
.ds-site[data-navigation="workspace_sidebar"] > main, .ds-site[data-navigation="workspace_sidebar"] > .ds-footer { grid-column: 2; }
.ds-site[data-scaffold="masonry_flow"] .ds-block-grid { display: block; columns: 22rem; column-gap: var(--ds-space-4); }
.ds-site[data-scaffold="masonry_flow"] .ds-block { break-inside: avoid; margin-bottom: var(--ds-space-4); }
.ds-site[data-scaffold="bento_showcase"] .ds-block-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.ds-site[data-scaffold="bento_showcase"] .ds-block:first-child { grid-column: span 2; grid-row: span 2; }
.ds-site[data-scaffold="magazine_spread"] .ds-section-heading { font-size: var(--ds-type-8); letter-spacing: -0.01em; }
.ds-site[data-scaffold="magazine_spread"] .ds-hero h1 { font-size: var(--ds-type-9); }
.ds-site[data-scaffold="dashboard_app"] .ds-section { padding-block: var(--ds-space-5); }
.ds-site[data-scaffold="dashboard_app"] .ds-block-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.ds-site[data-scaffold="dashboard_app"] .ds-header { position: sticky; top: 0; z-index: 20; }
.ds-site[data-scaffold="split_screen"] .ds-hero { min-height: 70vh; align-content: center; }
.ds-site[data-scaffold="narrow_single"] .ds-hero-copy { max-width: 40rem; }
.ds-site[data-scaffold="wide_immersive"] .ds-hero { min-height: 88vh; align-content: center; }
.ds-site[data-scaffold="overlapping_layers"] .ds-hero { padding-bottom: 0; }
.ds-site[data-scaffold="overlapping_layers"] .ds-hero-visual { transform: translateY(var(--ds-space-7)); box-shadow: var(--ds-shadow-card); }
.ds-site[data-scaffold="overlapping_layers"] .ds-section:first-of-type { padding-top: var(--ds-space-8); }
.ds-brand { color: var(--ds-color-text); font-family: var(--ds-font-display), serif; font-size: var(--ds-type-5); font-weight: 700; text-decoration: none; }
.ds-nav-links { display: flex; flex-wrap: wrap; align-items: center; gap: var(--ds-space-4); }
.ds-nav a, .ds-footer a { color: inherit; text-decoration: none; }
.ds-hero { display: grid; grid-template-columns: var(--ds-hero-columns); align-items: center; gap: var(--ds-space-7); padding-block: var(--ds-space-8); }
.ds-hero-copy { grid-column: auto; }
.ds-hero-copy { grid-column: span var(--ds-hero-copy-span); }
.ds-hero-visual { grid-column: span var(--ds-hero-visual-span); }
.ds-hero-visual { display: grid; align-content: center; gap: var(--ds-space-4); min-height: 100%; padding: var(--ds-space-6); border: var(--ds-border-width) solid var(--ds-color-border); border-radius: var(--ds-radius-card); background: var(--ds-color-surface); box-shadow: var(--ds-shadow-card); }
.ds-hero[data-hero="typographic"] { display: block; max-width: var(--ds-container-max); }
.ds-hero[data-hero="cinematic_media"], .ds-hero[data-hero="story_narrative"] { grid-template-columns: 1fr; }
.ds-hero[data-hero="search_led_catalog"] .ds-hero-visual, .ds-hero[data-hero="service_booking"] .ds-hero-visual { border-inline-start-width: var(--ds-space-2); }
.ds-hero h1 { max-width: var(--ds-heading-measure); margin: var(--ds-space-3) 0; font-family: var(--ds-font-display), serif; font-size: var(--ds-type-9); line-height: var(--ds-leading-heading); }
.ds-lede { max-width: var(--ds-body-measure); color: var(--ds-color-muted); font-size: var(--ds-type-5); line-height: var(--ds-leading-body); }
.ds-eyebrow { color: var(--ds-color-accent); font-size: var(--ds-type-2); font-weight: var(--ds-weight-strong); text-transform: uppercase; }
.ds-action { display: inline-flex; align-items: center; justify-content: center; margin-top: var(--ds-space-4); padding: var(--ds-space-3) var(--ds-space-5); border-radius: var(--ds-radius-control); background: var(--ds-color-primary); color: var(--ds-color-on-primary) !important; }
.ds-section { padding-block: var(--ds-space-7); }
.ds-section-heading { max-width: var(--ds-section-measure); margin-bottom: var(--ds-space-5); font-family: var(--ds-font-display), serif; font-size: var(--ds-type-7); }
.ds-block-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--ds-card-min-width)), 1fr)); gap: var(--ds-space-4); }
.ds-block { display: grid; align-content: start; gap: var(--ds-space-3); padding: var(--ds-space-5); border: var(--ds-border-width) solid var(--ds-color-border); border-radius: var(--ds-radius-card); background: var(--ds-color-surface); box-shadow: var(--ds-shadow-card); }
.ds-block h3 { margin: 0; font-family: var(--ds-font-display), serif; font-size: var(--ds-type-5); }
.ds-block p { margin: 0; color: var(--ds-color-muted); line-height: 1.6; }
.ds-footer { margin-top: var(--ds-space-8); padding-block: var(--ds-space-6); border-top: var(--ds-border-width) solid var(--ds-color-border); }
.ds-footer-content { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--ds-card-min-width)), 1fr)); gap: var(--ds-space-5); }
.ds-footer[data-footer="editorial_contact"] .ds-footer-content { grid-template-columns: 1fr auto; align-items: end; }
@media (max-width: 48rem) {
  .ds-nav { align-items: flex-start; flex-direction: column; }
  .ds-hero, .ds-hero[data-hero] { grid-template-columns: 1fr; }
    .ds-hero-copy, .ds-hero-visual { grid-column: auto; }
    .ds-site[data-navigation="workspace_sidebar"] { grid-template-columns: 1fr; }
    .ds-site[data-navigation="workspace_sidebar"] > main, .ds-site[data-navigation="workspace_sidebar"] > .ds-footer { grid-column: 1; }
    .ds-site[data-scaffold="bento_showcase"] .ds-block-grid, .ds-site[data-scaffold="dashboard_app"] .ds-block-grid { grid-template-columns: 1fr; }
    .ds-site[data-scaffold="bento_showcase"] .ds-block:first-child { grid-column: auto; grid-row: auto; }
    .ds-site[data-scaffold="overlapping_layers"] .ds-hero-visual { transform: none; }
    .ds-sidebar { position: relative; grid-row: auto; min-height: 0; border-right: 0; border-bottom: var(--ds-border-width) solid var(--ds-color-border); }
  .ds-hero h1 { font-size: var(--ds-type-7); }
  .ds-footer[data-footer="editorial_contact"] .ds-footer-content { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) { .ds-site *, .ds-site *::before, .ds-site *::after { scroll-behavior: auto !important; animation-duration: var(--ds-motion-reduced-duration) !important; transition-duration: var(--ds-motion-reduced-duration) !important; } }
"""
    return root + rules.replace("@media (max-width: 48rem)", f"@media (max-width: {tablet_breakpoint})", 1)


def _render_navigation(design_dna: Dict[str, Any], brand: str, section_ids: List[str]) -> str:
    pattern = design_dna["layout"]["navigation_pattern"]
    links = []
    for block_id in section_ids:
        if block_id == "hero":
            continue
        copy = get_section_copy(block_id)
        links.append(f'<a href="#{_text(block_id)}">{_text(copy["title"])}</a>')
    link_markup = "".join(links[:4])
    if pattern == "editorial_masthead":
        return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Main"><span className="ds-eyebrow">{_text(design_dna["niche"].replace("_", " "))}</span><a className="ds-brand" href="#top">{_text(brand)}</a><div className="ds-nav-links">{link_markup}</div></nav></header>'
    if pattern == "workspace_sidebar":
        return f'<aside className="ds-sidebar" data-navigation="{pattern}"><a className="ds-brand" href="#top">{_text(brand)}</a><nav aria-label="Workspace navigation"><div className="ds-nav-links">{link_markup}</div><a href="#contact_cta">Contact</a></nav></aside>'
    if pattern == "utility_dashboard":
        return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Workspace utilities"><a className="ds-brand" href="#top">{_text(brand)}</a><div className="ds-nav-links">{link_markup}</div><a href="#contact_cta">Workspace details</a></nav></header>'
    if pattern == "commerce_category_bar":
        return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Product categories"><a className="ds-brand" href="#top">{_text(brand)}</a><div className="ds-nav-links">{link_markup}</div></nav></header>'
    if pattern == "centered_brand":
        midpoint = (len(links) + 1) // 2
        left_links = "".join(links[:midpoint])
        right_links = "".join(links[midpoint:])
        return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Main"><div className="ds-nav-links">{left_links}</div><a className="ds-brand" href="#top">{_text(brand)}</a><div className="ds-nav-links">{right_links}</div></nav></header>'
    if pattern == "local_contact":
        return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Local services"><a className="ds-brand" href="#top">{_text(brand)}</a><div className="ds-nav-links">{link_markup}</div><a href="#contact_cta">Get in touch</a></nav></header>'
    if pattern == "immersive_overlay":
        return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Explore"><a className="ds-brand" href="#top">{_text(brand)}</a><details><summary>Explore</summary><div className="ds-nav-links">{link_markup}</div></details></nav></header>'
    return f'<header className="ds-header" data-navigation="{pattern}"><nav className="ds-container ds-nav" aria-label="Main"><a className="ds-brand" href="#top">{_text(brand)}</a><div className="ds-nav-links">{link_markup}</div></nav></header>'


def _render_hero(design_dna: Dict[str, Any], brand: str, spec: Dict[str, Any]) -> str:
    niche = design_dna["niche"]
    default_title, default_description = _NICHE_HERO_COPY.get(
        niche, ("A clearer way to move the work forward", "Explore the product and choose a useful next step.")
    )
    title = _text(spec.get("tagline") or spec.get("value_proposition") or default_title)
    description = _text(spec.get("product_summary") or spec.get("description") or default_description)
    hero = design_dna["layout"]["hero_archetype"]
    section_ids = design_dna["layout"]["pages"]["Home"]["section_order"]
    section_ids = [block_id for block_id in section_ids if block_id != "hero"]
    related = "".join(
        f'<li>{_text(get_section_copy(block_id)["title"])}</li>'
        for block_id in section_ids[:3]
    )
    visual = f'<aside className="ds-hero-visual" aria-label="{_text(brand)} workflow"><span className="ds-eyebrow">{_text(niche.replace("_", " "))}</span><ul>{related}</ul></aside>'
    if hero == "typographic":
        visual = ""
    elif hero == "editorial_image":
        visual = f'<aside className="ds-hero-visual" aria-label="Editorial overview"><p className="ds-eyebrow">{_text(brand)}</p><p className="ds-lede">{description}</p></aside>'
    elif hero == "cinematic_media":
        visual = f'<div className="ds-hero-visual" aria-label="{_text(brand)} introduction"><span className="ds-eyebrow">{_text(niche.replace("_", " "))}</span><p>{_text(brand)}</p></div>'
    elif hero in {"search_led_catalog", "map_local_discovery"}:
        visual = f'<aside className="ds-hero-visual"><h2>{_text(get_section_copy(section_ids[0] if section_ids else "contact_cta")["title"])}</h2><p>{description}</p><a className="ds-action" href="#{_text(section_ids[0] if section_ids else "contact_cta")}">Explore details</a></aside>'
    elif hero == "story_narrative":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">{_text(brand)}</span><p className="ds-lede">{description}</p></aside>'
    elif hero == "event_date":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">Programme</span><p>{_text(get_section_copy(section_ids[0] if section_ids else "event_schedule")["title"])}</p><p>{description}</p></aside>'
    elif hero == "service_booking":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">Next step</span><h2>{_text(get_section_copy(section_ids[0] if section_ids else "service_booking")["title"])}</h2><p>{description}</p></aside>'
    elif hero == "product_configurator":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">Product details</span><p>{_text(get_section_copy(section_ids[0] if section_ids else "product_catalog")["title"])}</p><p>{description}</p></aside>'
    elif hero == "split_product_preview":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">Product overview</span><ul>{related}</ul></aside>'
    elif hero == "dashboard_preview":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">Workflow preview</span><ol>{related}</ol></aside>'
    elif hero == "data_metrics":
        visual = f'<aside className="ds-hero-visual"><span className="ds-eyebrow">Process</span><ol>{related}</ol><p>{description}</p></aside>'
    return (
        f'<section id="top" className="ds-container ds-hero" data-hero="{hero}">'
        f'<div className="ds-hero-copy"><span className="ds-eyebrow">{_text(niche.replace("_", " "))}</span>'
        f'<h1>{title}</h1><p className="ds-lede">{description}</p>'
        f'<a className="ds-action" href="#contact_cta">Explore the next step</a></div>{visual}</section>'
    )


def _render_section(block_id: str, index: int) -> str:
    content = get_section_copy(block_id)
    label = _text(content["title"])
    description = _text(content["description"])
    extra = f'<a href="#contact_cta">Explore {label.lower()}</a>' if block_id not in {"contact_cta", "faq_answers"} else ""
    if block_id == "claims_queue":
        body = f'<div className="ds-queue"><span>{label}</span><span>Review details</span><span>Choose next action</span></div><p>{description}</p>'
    elif block_id == "claims_intake":
        body = f'<ol><li>Incident details</li><li>Supporting documents</li><li>Review submission</li></ol><p>{description}</p>'
    elif block_id == "course_curriculum":
        body = f'<ol><li>Foundations</li><li>Practice</li><li>Next steps</li></ol><p>{description}</p>'
    else:
        body = f'<p>{description}</p>'
    if block_id == "contact_cta":
        return f'<section id="{_text(block_id)}" className="ds-section"><div className="ds-container ds-contact"><span className="ds-eyebrow">Next step</span><h2>{label}</h2><p>{description}</p><a className="ds-action" href="/contact">Contact the team</a></div></section>'
    return f'<section id="{_text(block_id)}" className="ds-section" data-section-order="{index}"><div className="ds-container"><h2 className="ds-section-heading">{label}</h2><div className="ds-block-grid"><article className="ds-block" data-block="{_text(block_id)}">{body}{extra}</article></div></div></section>'


def _render_footer(design_dna: Dict[str, Any], brand: str) -> str:
    footer = design_dna["layout"].get("footer_type", "sitemap_columns")
    if footer == "editorial_contact":
        content = f'<div><a className="ds-brand" href="#top">{_text(brand)}</a><p>For project enquiries and questions.</p></div><a href="/contact">Contact</a>'
    else:
        content = f'<div><a className="ds-brand" href="#top">{_text(brand)}</a><p>{_text(design_dna["niche"].replace("_", " "))}</p></div><div><span>Explore</span><p><a href="#top">Home</a></p><p><a href="/contact">Contact</a></p></div>'
    return f'<footer className="ds-footer" data-footer="{_text(footer)}"><div className="ds-container ds-footer-content">{content}</div></footer>'


def _write_css(frontend_src: Path, design_dna: Dict[str, Any]) -> Path:
    target = frontend_src / "design-system.css"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render_css(design_dna), encoding="utf-8")
    return target


def _mount_niche_route(app_path: Path, page_name: str, route: str) -> bool:
    if not app_path.is_file():
        return False
    source = app_path.read_text(encoding="utf-8")
    if "<Routes" not in source or "</Routes>" not in source:
        return False
    import_line = f"import {page_name} from './pages/{page_name}.jsx';\n"
    route_line = f'<Route path="{route}" element={{<{page_name} />}} />'
    if route_line in source:
        return True
    source = import_line + source if import_line.strip() not in source else source
    source = source.replace("</Routes>", f"{route_line}</Routes>", 1)
    app_path.write_text(source, encoding="utf-8")
    return True


def _render_niche_page(page: Dict[str, Any], design_dna: Dict[str, Any], brand: str, spec: Dict[str, Any]) -> str:
    blocks = "".join(_render_section(block_id, index) for index, block_id in enumerate(page["blocks"]))
    heading = _text(spec.get("niche_page_title") or page["heading"])
    description = _text(page["description"])
    return (
        "import React from 'react';\nimport '../design-system.css';\n"
        f"export default function {page['name']}() {{ return (<div className=\"ds-site\" data-grid=\"{_text(design_dna['layout'].get('grid_system', 'editorial_2_column'))}\" data-navigation=\"{_text(design_dna['layout']['navigation_pattern'])}\" data-scaffold=\"{_text(design_dna['layout'].get('page_scaffold', 'standard_sections'))}\">"
        f"<header className=\"ds-header\"><nav className=\"ds-container ds-nav\" aria-label=\"Main\"><a className=\"ds-brand\" href=\"/\">{_text(brand)}</a></nav></header>"
        f"<main><section className=\"ds-container ds-section\"><span className=\"ds-eyebrow\">{_text(design_dna['niche'].replace('_', ' '))}</span><h1>{heading}</h1><p className=\"ds-lede\">{description}</p></section>{blocks}</main>"
        f"{_render_footer(design_dna, brand)}</div>); }}\n"
    )


def compose_project_pages(project_dir: Path, design_dna: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Write Home and niche-specific pages using the accepted design DNA."""
    project_dir = Path(project_dir).resolve()
    frontend_src = project_dir / "frontend" / "src"
    pages_dir = frontend_src / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    layout = design_dna.get("layout") or {}
    pages = layout.get("pages") or {}
    home = pages.get("Home") or {}
    section_order = list(home.get("section_order") or ["hero", "product_features", "contact_cta"])
    if section_order and section_order[0] == "hero":
        section_order = section_order[1:]
    hero = layout.get("hero_archetype") or "typographic"
    navigation = layout.get("navigation_pattern") or "minimal_top"
    scaffold = layout.get("page_scaffold") or "standard_sections"
    catalog = get_design_catalog()
    if hero not in {item["id"] for item in catalog["heroes"]}:
        raise ValueError(f"Unknown hero archetype in design DNA: {hero}")
    if navigation not in {item["id"] for item in catalog["navigation"]}:
        raise ValueError(f"Unknown navigation pattern in design DNA: {navigation}")
    if scaffold not in {item["id"] for item in catalog["scaffolds"]}:
        raise ValueError(f"Unknown page scaffold in design DNA: {scaffold}")
    valid_sections = {item["id"] for item in catalog["sections"]}
    unknown_sections = set(section_order) - valid_sections
    if unknown_sections:
        raise ValueError(f"Unknown section block(s) in design DNA: {', '.join(sorted(unknown_sections))}")

    niche = normalize_niche(design_dna.get("niche") or spec.get("industry"))
    normalized_dna = dict(design_dna, niche=niche)
    brand = str(spec.get("brand_title") or spec.get("project_name") or design_dna.get("project") or "Website")
    all_sections = ["hero", *section_order]
    nav = _render_navigation(normalized_dna, brand, all_sections)
    hero_markup = _render_hero(normalized_dna, brand, spec)
    section_markup = "".join(_render_section(block_id, index) for index, block_id in enumerate(section_order))
    footer = _render_footer(normalized_dna, brand)
    home_source = (
        "import React from 'react';\nimport '../design-system.css';\n"
        f"export default function Home() {{ return (<div className=\"ds-site\" data-grid=\"{_text(layout.get('grid_system', 'editorial_2_column'))}\" data-navigation=\"{_text(navigation)}\" data-scaffold=\"{_text(scaffold)}\">{nav}<main id=\"main-content\">{hero_markup}{section_markup}</main>{footer}</div>); }}\n"
    )
    home_path = pages_dir / "Home.jsx"
    home_path.write_text(home_source, encoding="utf-8")
    css_path = _write_css(frontend_src, normalized_dna)
    written_paths = [str(home_path), str(css_path)]
    niche_page = get_niche_page(niche)
    route_mounted = False
    if niche_page:
        niche_path = pages_dir / f"{niche_page['name']}.jsx"
        niche_path.write_text(_render_niche_page(niche_page, normalized_dna, brand, spec), encoding="utf-8")
        written_paths.append(str(niche_path))
        route_mounted = _mount_niche_route(
            frontend_src / "App.jsx", niche_page["name"], niche_page["path"]
        )
    return {
        "ok": True,
        "written_paths": written_paths,
        "structure": {
            "niche": niche,
            "hero": hero,
            "navigation": navigation,
            "scaffold": scaffold,
            "home_sections": all_sections,
            "niche_page": niche_page["name"] if niche_page else None,
            "niche_route_mounted": route_mounted,
            "fingerprint": (design_dna.get("fingerprint") or {}).get("value"),
        },
    }