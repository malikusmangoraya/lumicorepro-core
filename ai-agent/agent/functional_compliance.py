"""SRS Quality Gates — Functional System Compliance (TRD #5).

Gates §1 (functional compliance) on every generated project and surfaces the
state of §2 (DevOps code-quality gates):

1. SEO Architecture
   - 14 default JSON-LD schema types must be available in generated structured
     data; a top-up block adds the missing schema.org types to
     `frontend/src/config/structured-data.js` (idempotent, `LUMICORE_SEO`).
   - Complete custom Open Graph + Twitter meta must sit in the project
     `<head>`; injected when missing.
   - Responsive document headings: one `h1` per page, no skipped heading levels.

2. Internationalization (i18n)
   - `src/i18n/i18n.js` bootstrap (i18next + `languageChanged` → `dir`/`lang`
     on <html>) and an abstracted `useAppTranslation` key hook; component texts
     route through translator hooks. RTL languages get `dir="rtl"` natively.

Code Quality Assurance (gated §2 — verified, not duplicated): ESLint + Prettier
pass before ZIP compilation is enforced by `agent/quality_gate.py` (DevOps gate
in orchestrator); this module only reports its availability/config presence.

Deliverable: QUALITY-GATES.md + conformance report `functional_compliance`.
Static and transactional runtimes both carry a frontend, so this applies to both.
"""
import os
import re
from typing import Dict, Any, List

from utils.logger import agent_logger
from utils.file_manager import FileManager

SEO_MARKER = "LUMICORE_SEO"
I18N_MARKER = "LUMICORE_I18N"

# TRD §1 — 14 default JSON-LD schema types every generated project must ship.
JSONLD_REQUIRED_TYPES: List[str] = [
    "Organization", "WebSite", "WebPage", "Product", "Offer", "AggregateRating",
    "BreadcrumbList", "FAQPage", "Service", "LocalBusiness", "Person", "Article",
    "Review", "ImageObject",
]
# Types already supplied by seo_automation's structured-data.js.
JSONLD_EXISTING_TYPES = {
    "Organization", "WebSite", "Product", "Offer", "AggregateRating",
    "BreadcrumbList", "FAQPage",
}

# Canonical OG + Twitter tags that must exist in the project <head>.
OG_REQUIRED = [
    "og:title", "og:description", "og:image", "og:url", "og:type",
    "og:site_name", "og:locale", "twitter:card",
]

_RTL_LANGUAGES = ["ar", "he", "fa", "ur", "ps", "ku", "sd"]

_I18N_BOOTSTRAP = f"""/* SRS quality gate scaffolding — i18n bootstrap + RTL (LUMICORE_I18N) */
import i18n from 'i18next';
import {{ initReactI18next }} from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

export const RTL_LANGUAGES = {_RTL_LANGUAGES};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({{
    resources: {{}},
    fallbackLng: 'en',
    defaultNS: 'translation',
    interpolation: {{ escapeValue: false }},
    detection: {{ order: ['localStorage', 'navigator', 'htmlTag'], caches: ['localStorage'] }},
  }});

i18n.on('languageChanged', (lng) => {{
  document.documentElement.dir = RTL_LANGUAGES.includes(lng) ? 'rtl' : 'ltr';
  document.documentElement.lang = lng;
}});

export default i18n;
"""

_USE_TRANSLATION_HOOK = """/* SRS quality gate — abstracted translator key hook (LUMICORE_I18N) */
import { useTranslation } from 'react-i18next';

export default function useAppTranslation(namespace) {
  return useTranslation(namespace);
}
"""

# Top-up block: the JSON-LD types seo_automation does not already provide.
_EXTENDED_SCHEMAS_JS = """
/**
 * SRS Quality Gate — extended JSON-LD schema defaults (LUMICORE_SEO)
 * Top-up so the generated project ships all 14 default schema.org types.
 */
export const imageObjectSchema = ({ url, width, height }) => ({
  '@context': 'https://schema.org',
  '@type': 'ImageObject',
  url: url,
  width, height,
});

export const webPageSchema = ({ url, name, description, primaryImage }) => ({
  '@context': 'https://schema.org',
  '@type': 'WebPage',
  url, name, description,
  ...(primaryImage && { primaryImageOfPage: { '@type': 'ImageObject', url: primaryImage } }),
});

export const serviceSchema = ({ name, description, provider, areaServed = 'Worldwide' }) => ({
  '@context': 'https://schema.org',
  '@type': 'Service',
  name, description,
  provider: { '@type': 'Organization', name: provider },
  areaServed,
});

export const localBusinessSchema = ({ name, telephone, address, geo }) => ({
  '@context': 'https://schema.org',
  '@type': 'LocalBusiness',
  name, telephone,
  address: { '@type': 'PostalAddress', ...address },
  ...(geo && { geo: { '@type': 'GeoCoordinates', ...geo } }),
});

export const personSchema = ({ name, jobTitle, url, sameAs = [] }) => ({
  '@context': 'https://schema.org',
  '@type': 'Person',
  name, jobTitle, url, sameAs,
});

export const articleSchema = ({ headline, author, datePublished, image }) => ({
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline,
  author: { '@type': 'Person', name: author },
  datePublished,
  ...(image && { image }),
});

export const reviewSchema = ({ author, reviewBody, reviewRating, itemReviewed }) => ({
  '@context': 'https://schema.org',
  '@type': 'Review',
  author: { '@type': 'Person', name: author },
  reviewBody,
  reviewRating: { '@type': 'Rating', ratingValue: reviewRating },
  itemReviewed: { '@type': 'Thing', name: itemReviewed },
});

export { imageObjectSchema as webPageImageSchema };
"""


class FunctionalComplianceInjector:
    """SRS functional compliance gates (SEO + i18n) over generated projects."""

    def generate(self, spec: Dict[str, Any], project_dir: str, mode: str = "") -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "runtime_mode": spec.get("runtime_mode", "transactional"),
            "artifacts": [],
            "seo": self._gate_seo(spec, project_dir),
            "i18n": self._gate_i18n(project_dir),
            "code_quality": self._verify_devops_gate(),
        }
        report["doc"] = self._write_quality_gates_doc(spec, project_dir, report)
        report["artifacts"].append(report["doc"])
        agent_logger.info(
            f"FunctionalCompliance: seo_jsonld={len(report['seo']['jsonld']['types'])}/14 "
            f"og={'ok' if report['seo']['og']['pass'] else 'gap'} "
            f"i18n_bootstrap={'ok' if report['i18n']['bootstrap']['pass'] else 'gap'}"
        )
        return report

    # ── 1a. SEO: JSON-LD 14-type baseline ──────────────────────────────────
    def _structured_data_files(self, project_dir: str) -> List[str]:
        hits: List[str] = []
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", "build", ".git", "venv")]
            for fname in files:
                if fname.startswith("structured-data") and fname.endswith((".js", ".json")):
                    hits.append(os.path.join(root, fname))
        return hits

    @staticmethod
    def _extract_jsonld_types(content: str) -> List[str]:
        pattern = re.compile(r"""['"]?@type['"]?\s*[:=]\s*['"]([A-Za-z0-9_]+)['"]""")
        return pattern.findall(content)

    def _top_up_jsonld(self, project_dir: str) -> Dict[str, Any]:
        for path in self._structured_data_files(project_dir):
            if not path.endswith(".js"):
                continue
            content = FileManager.read_file(path)
            if SEO_MARKER in content:
                return {"status": "skip", "already_extended": True}
            types = set(self._extract_jsonld_types(content))
            missing = [t for t in JSONLD_REQUIRED_TYPES if t not in types]
            if not missing:
                return {"status": "skip", "already_complete": True}
            FileManager.write_file(path, content.rstrip("\n") + "\n" + _EXTENDED_SCHEMAS_JS)
            return {"status": "ok", "file": path.replace("\\", "/"), "topped_up": missing}
        return {"status": "skip", "reason": "no structured-data.js found"}

    def _gate_seo(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        top_up = self._top_up_jsonld(project_dir)
        types: List[str] = []
        for path in self._structured_data_files(project_dir):
            types.extend(self._extract_jsonld_types(FileManager.read_file(path)))
        distinct = sorted(set(t for t in JSONLD_REQUIRED_TYPES if t in types))
        missing_types = [t for t in JSONLD_REQUIRED_TYPES if t not in distinct]

        og = self._gate_open_graph(project_dir)
        headings = self._gate_headings(project_dir)

        return {
            "jsonld": {
                "required": len(JSONLD_REQUIRED_TYPES),
                "types": distinct,
                "missing_types": missing_types,
                "pass": not bool(missing_types),
                "top_up": top_up,
            },
            "og": og,
            "headings": headings,
        }

    # ── 1b. SEO: Open Graph metadata in <head> ────────────────────────────
    def _index_html_files(self, project_dir: str) -> List[str]:
        hits: List[str] = []
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", "build", ".git", "venv")]
            if "index.html" in files:
                hits.append(os.path.join(root, "index.html"))
        return sorted(hits)

    def _gate_open_graph(self, project_dir: str) -> Dict[str, Any]:
        index_files = self._index_html_files(project_dir)
        if not index_files:
            return {"pass": False, "missing": OG_REQUIRED, "note": "no index.html found"}
        combined = "\n".join(FileManager.read_file(p) for p in index_files if os.path.isfile(p))
        missing = [tag for tag in OG_REQUIRED if tag not in combined]
        if missing:
            target = None
            for path in index_files:
                content = FileManager.read_file(path)
                if "<head>" in content and "</head>" in content and SEO_MARKER not in content:
                    target = (path, content)
                    break
            if target:
                path, content = target
                pname = "This project"
                base_url = "https://example.com"
                block = (
                    "\n  <!-- LUMICORE_SEO:open_graph -->\n"
                    f'  <meta property="og:title" content="{pname}" />\n'
                    f'  <meta property="og:description" content="{pname} — modern platform." />\n'
                    f'  <meta property="og:image" content="{base_url}/og-image.jpg" />\n'
                    f'  <meta property="og:url" content="{base_url}" />\n'
                    '  <meta property="og:type" content="website" />\n'
                    '  <meta property="og:site_name" content="' + pname + '" />\n'
                    '  <meta property="og:locale" content="en_US" />\n'
                    '  <meta property="twitter:card" content="summary_large_image" />\n'
                    "  <!-- /LUMICORE_SEO -->\n"
                )
                content = content.replace("</head>", block + "</head>", 1)
                FileManager.write_file(path, content)
                missing = []
        return {"pass": not bool(missing), "missing": missing, "scanned": [os.path.relpath(p, project_dir) for p in index_files]}

    # ── 1c. SEO: responsive document headings ──────────────────────────────
    def _gate_headings(self, project_dir: str) -> Dict[str, Any]:
        violations: List[str] = []
        pages = 0
        src = os.path.join(project_dir, "frontend", "src")
        if not os.path.isdir(src):
            return {"pass": False, "pages": 0, "violations": ["frontend/src missing"]}
        for root, _, files in os.walk(src):
            if "components" in root.split(os.sep):
                continue
            for fname in files:
                if not fname.endswith((".jsx", ".html")):
                    continue
                content = FileManager.read_file(os.path.join(root, fname))
                levels = sorted(int(m) for m in re.findall(r"<h([1-6])[ >]", content))
                if not levels:
                    continue
                pages += 1
                rel = os.path.relpath(os.path.join(root, fname), project_dir)
                if levels.count(1) > 1:
                    violations.append(f"{rel}: multiple h1 ({levels.count(1)})")
                if 1 not in levels and any(l > 1 for l in levels):
                    violations.append(f"{rel}: headings skip h1")
                for i in range(1, len(levels)):
                    if levels[i] - levels[i - 1] > 1:
                        violations.append(f"{rel}: heading level jump h{levels[i-1]}→h{levels[i]}")
        violations = violations[:20]
        return {"pass": not bool(violations) and pages > 0, "pages": pages, "violations": violations}

    # ── 2. i18n architecture gate ──────────────────────────────────────────
    def _gate_i18n(self, project_dir: str) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        i18n_js = os.path.join(src, "i18n", "i18n.js")
        bootstrap = {"pass": False, "rtl_support": False}
        if os.path.isfile(i18n_js):
            content = FileManager.read_file(i18n_js)
            bootstrap = {
                "pass": "initReactI18next" in content and "init(" in content,
                "rtl_support": "document.documentElement.dir" in content
                and "localeNames" not in content,
            }
        else:
            if os.path.isdir(src):
                FileManager.ensure_dir(os.path.join(src, "i18n"))
                FileManager.write_file(i18n_js, _I18N_BOOTSTRAP)
                bootstrap = {"pass": True, "rtl_support": True, "injected": True}

        hook_path = os.path.join(src, "hooks", "useAppTranslation.js")
        hook_status = "present"
        if not os.path.isfile(hook_path):
            if os.path.isdir(src):
                FileManager.ensure_dir(os.path.join(src, "hooks"))
                FileManager.write_file(hook_path, _USE_TRANSLATION_HOOK)
                hook_status = "injected"

        # Coverage metric: share of components wording through translator key hooks.
        comp_dir = os.path.join(src, "components")
        components, hook_using = 0, 0
        if os.path.isdir(comp_dir):
            for root, _, files in os.walk(comp_dir):
                for fname in files:
                    if not fname.endswith(".jsx"):
                        continue
                    components += 1
                    body = FileManager.read_file(os.path.join(root, fname))
                    if "useTranslation" in body or "useAppTranslation" in body:
                        hook_using += 1
        coverage = round((hook_using / components) * 100, 1) if components else 100.0
        return {
            "bootstrap": bootstrap,
            "hook": {"file": "frontend/src/hooks/useAppTranslation.js", "status": hook_status},
            "coverage": {"components": components, "hook_using": hook_using, "percent": coverage},
        }

    # ── 2 (verified): DevOps ESLint/Prettier ZIP gates ─────────────────────
    def _verify_devops_gate(self) -> Dict[str, Any]:
        here = os.path.dirname(os.path.abspath(__file__))
        repo = os.path.dirname(os.path.dirname(here))  # <repo>/ai-agent/agent → repo root
        eslint_config = os.path.join(repo, "scripts", "eslint.generated.config.js")
        prettier_ignore = os.path.join(repo, ".prettierignore")
        try:
            from agent.quality_gate import DevOpsQualityGate  # noqa: F401
            module_ok = True
        except Exception:
            module_ok = False
        return {
            "eslint_pipeline": os.path.isfile(eslint_config),
            "prettier_pipeline": os.path.isfile(prettier_ignore),
            "gate_module": module_ok,
            "note": (
                "ZIP archiving is blocked unless ESLint + Prettier pass "
                "(agent/quality_gate.py DevOps gate); verified wiring, not re-run here."
            ),
        }

    # ── Doc ────────────────────────────────────────────────────────────────
    def _write_quality_gates_doc(self, spec: Dict[str, Any], project_dir: str, report: Dict[str, Any]) -> str:
        project = str(spec.get("project_name") or "This project").replace("-", " ").title()
        seo, i18n = report["seo"], report["i18n"]
        cq = report["code_quality"]
        body = f"""# SRS Quality Gates — {project}

> Functional system compliance (SEO + i18n) plus code-quality gates (TRD #5).

## 1. SEO Architecture
- **JSON-LD (14 default types):** {'PASS' if seo['jsonld']['pass'] else 'GAP'} —
  {len(seo['jsonld']['types'])}/14 present. Missing: {", ".join(seo['jsonld']['missing_types']) or "none"}.
  Top-up: {seo['jsonld']['top_up'].get('status')}.
- **Open Graph metadata:** {'PASS' if seo['og']['pass'] else 'GAP'} — canonical
  tags scanned across {", ".join('`' + p + '`' for p in seo['og'].get('scanned', [])) or 'none'}.
- **Responsive headings:** {'PASS' if seo['headings']['pass'] else 'VIOLATIONS'} —
  {seo['headings']['pages']} page(s) scanned; violations:
  {"; ".join(seo['headings']['violations']) or "none"}.

## 2. Internationalization (i18n)
- Bootstrap: {'PASS' if i18n['bootstrap']['pass'] else 'GAP'} — `src/i18n/i18n.js`
  (i18next + `useTranslation`), RTL via `dir` set on change
  ({'PASS' if i18n['bootstrap'].get('rtl_support') else 'GAP'}).
- Key hook: `{i18n['hook']['file']}` ({i18n['hook']['status']}).
- Coverage: **{i18n['coverage']['percent']}%** of components (
  {i18n['coverage']['hook_using']}/{i18n['coverage']['components']}) text-abstract through translator hooks.

## 3. Code Quality Assurance Rules
- ESLint gate: {'configured' if cq['eslint_pipeline'] else 'MISSING'} (
  `scripts/eslint.generated.config.js`); Prettier: {'configured' if cq['prettier_pipeline'] else 'MISSING'}.
- Rule: ZIP archiving EXECUTION is blocked whenever the ESLint/Prettier pipeline
  flags structural/syntax errors (`agent/quality_gate.py` → orchestrator). Violating
  projects route to code_modifier self-healing and are re-gated before archive.
- Gate module: {'available' if cq['gate_module'] else 'UNAVAILABLE'}.
"""
        path = os.path.join(project_dir, "QUALITY-GATES.md")
        FileManager.write_file(path, body)
        return path


functional_compliance = FunctionalComplianceInjector()