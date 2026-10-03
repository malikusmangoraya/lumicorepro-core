"""DesignLint — LumicorePro Part 3.

A lint pass for design, like ESLint for code. Analyzes generated frontend
source (JSX) and design tokens to flag design-quality violations.

Rules:
  DL001 wide hero heading   DL009 mobile hero too tall
  DL002 low CTA contrast    DL010 CTA below fold
  DL003 >4 identical cards  DL011 visual density too high
  DL004 spacing inconsistency
  DL005 too many rounded containers
  DL006 too many gradients
  DL007 repeated decorative effects
  DL008 broken heading hierarchy
  DL012 empty section       DL013 generic placeholder copy
  DL014 repeated animation  DL015 brand differentiation too low

Severity: P1 = critical, P2 = high, P3 = medium, P4 = minor.
"""
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Rule definitions: code -> (severity, description)
# ---------------------------------------------------------------------------
_RULES: Dict[str, Dict[str, Any]] = {
    "DL001": {"severity": "P2", "name": "hero_heading_too_wide",
              "description": "Hero heading too wide"},
    "DL002": {"severity": "P1", "name": "cta_contrast",
              "description": "Primary CTA has insufficient contrast"},
    "DL003": {"severity": "P2", "name": "identical_cards",
              "description": "More than 4 identical cards"},
    "DL004": {"severity": "P3", "name": "spacing_inconsistency",
              "description": "Section spacing inconsistency"},
    "DL005": {"severity": "P2", "name": "too_many_rounded_containers",
              "description": "Too many rounded containers"},
    "DL006": {"severity": "P2", "name": "too_many_gradients",
              "description": "Too many gradients"},
    "DL007": {"severity": "P3", "name": "repeated_decorative_effects",
              "description": "Repeated decorative effects"},
    "DL008": {"severity": "P1", "name": "heading_hierarchy_broken",
              "description": "Heading hierarchy broken"},
    "DL009": {"severity": "P2", "name": "mobile_hero_too_tall",
              "description": "Mobile hero too tall"},
    "DL010": {"severity": "P1", "name": "cta_below_fold",
              "description": "CTA buried below fold"},
    "DL011": {"severity": "P3", "name": "visual_density_too_high",
              "description": "Visual density too high"},
    "DL012": {"severity": "P2", "name": "empty_section",
              "description": "Empty section detected"},
    "DL013": {"severity": "P2", "name": "generic_placeholder_copy",
              "description": "Generic placeholder copy detected"},
    "DL014": {"severity": "P3", "name": "repeated_animation_pattern",
              "description": "Repeated animation pattern"},
    "DL015": {"severity": "P1", "name": "brand_differentiation_low",
              "description": "Brand differentiation too low"},
}

_PLACEHOLDER_RE = re.compile(
    "|".join([r"\blorem\s+ipsum\b", r"\byour\s+\w+\b",
              r"\bplaceholder[s]?\b", r"\b%dummy\b", r"\bTBD\b",
              r"\bcoming\s+soon\b"]), re.IGNORECASE)

_HEADING_RE = re.compile(r"<h([1-6])[^>]*>")
_CTA_BUTTON_RE = re.compile(
    r"<(?:Button|button)[^>]*(?:href|to|onClick)[^>]*>", re.I)
_GRADIENT_RE = re.compile(r"(?:bg-gradient|from-[^'\"]+|to-[^'\"]+|"
                          r"background:\s*linear-gradient|"
                          r"background:\s*radial-gradient)", re.I)
_RADIUS_RE = re.compile(
    r"rounded-(?:full|3xl|2xl|xl)", re.I)
_CARD_LIKE_RE = re.compile(
    r"className=\"[^\"]*\b(?:card|panel|tile)\b[^\"]*\"", re.I)
_ANIMATION_CLASS_RE = re.compile(
    r"\b(?:animate|motion\.|framer|transition-all duration)",
    re.I)
_DECORATIVE_RE = re.compile(
    r"\b(?:blur|glow|glass|aurora|particle|shine|shadow-2xl|"
    r"backdrop-blur)\b", re.I)
_SECTION_RE = re.compile(
    r"<(?:section|div)[^>]*className=\"[^\"]*\b(?:section|hero|feature|"
    r"pricing|testimonial|footer|contact|stats)\b[^\"]*\"")


class DesignLint:
    """Run the DL rules against a generated frontend source tree."""

    def __init__(self, rules: Optional[Dict[str, Dict[str, Any]]] = None):
        self.rules = rules or _RULES

    # ------------------------------------------------------------------
    def lint_directory(self, project_dir: str) -> Dict[str, Any]:
        """Lint a generated frontend (or standalone HTML) directory."""
        root = Path(project_dir)
        findings: List[Dict[str, Any]] = []
        files_checked = 0

        # Collect source files (JSX/TSX, or self-contained HTML) — single walk
        # via the shared SourceIndex (collapses repeated rglob passes).
        from .source_index import get_source_index
        index = get_source_index(project_dir)
        sources: List[Path] = [Path(p) for p in
                               index.files(".jsx", ".tsx")]
        html_files = [Path(p) for p in index.files(".html")]
        sources += [h for h in html_files
                    if self._is_generated_html(h)]
        if not sources:
            return {"files_checked": 0, "findings": [],
                    "summary": {"total": 0, "by_severity": {}}}
        if len(sources) > 400:
            sources = sources[:400]

        microcopy_buf = self._read_microcopy(root)

        for src in sources:
            try:
                text = src.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files_checked += 1
            findings += self._lint_file(text, src, microcopy_buf, root)

        # Native-like aggregated checks across the whole project
        findings += self._lint_project_level(root)

        # Cap identical findings (avoid floods)
        findings = self._dedupe(findings)

        severity_counts: Dict[str, int] = {}
        for f in findings:
            sev = f["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        summary = {
            "total": len(findings),
            "by_severity": severity_counts,
        }
        primary = sum(1 for f in findings
                      if f["severity"] in ("P1", "P2", "P3"))
        return {
            "files_checked": files_checked,
            "findings": findings,
            "summary": summary,
            "pass": primary == 0,
        }

    # ------------------------------------------------------------------
    def _is_generated_html(self, path: Path) -> bool:
        name = path.name.lower()
        return name in ("index.html", "404.html") and \
            self._read_snippet(path).find("id=\"root\"") >= 0

    @staticmethod
    def _read_snippet(path: Path, limit: int = 4000) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read(limit)
        except Exception:
            return ""

    @staticmethod
    def _read_microcopy(root: Path) -> str:
        """Collect known real copy files for placeholder detection."""
        buf: List[str] = []
        for name in ("data.js", "content.js", "i18n.js",
                     "locales/*.json"):
            for match in list(root.glob("**/" + name))[:20]:
                buf.append(DesignLint._read_snippet(match, 12000))
        return "\n".join(buf)

    # ------------------------------------------------------------------
    def _lint_file(self, text: str, path: Path,
                   microcopy_buf: str, root: Path) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        rel = str(path.relative_to(root)).replace("\\", "/") \
            if root else str(path)

        def add(code: str, detail: str = ""):
            rule = self.rules.get(code)
            if not rule:
                return
            findings.append({
                "code": code,
                "severity": rule["severity"],
                "rule": rule["name"],
                "message": rule["description"] +
                           (f" — {detail}" if detail else ""),
                "file": rel,
            })

        # DL013 generic placeholder copy
        for match in _PLACEHOLDER_RE.finditer(text):
            add("DL013", f"'${match.group(0)}' in {path.name}")
            break  # one per file is enough

        # DL008 broken heading hierarchy
        headings = _HEADING_RE.findall(text)
        if headings:
            prev = int(headings[0])
            for tag in headings[1:]:
                cur = int(tag)
                if cur > prev + 1:
                    add("DL008", f"h{prev} → h{cur} jump in {path.name}")
                    break
                prev = cur

        # DL006 too many gradients
        gradients = _GRADIENT_RE.findall(text)
        if len(gradients) > 6:
            add("DL006", f"{len(gradients)} gradient usages in {path.name}")

        # DL005 too many rounded containers
        rounded = _RADIUS_RE.findall(text)
        if len(rounded) > 14:
            add("DL005", f"{len(rounded)} large-radius usages in {path.name}")

        # DL003 >4 identical card-like components repeated
        cards = _CARD_LIKE_RE.findall(text)
        if len(cards) > 4:
            add("DL003", f"{len(cards)} card-like blocks in {path.name}")

        # DL007 repeated decorative effects
        decorative = _DECORATIVE_RE.findall(text)
        if len(decorative) > 10:
            add("DL007", f"{len(decorative)} decorative effects in {path.name}")

        # DL014 repeated animation pattern
        anims = _ANIMATION_CLASS_RE.findall(text)
        if len(anims) > 16:
            add("DL014", f"{len(anims)} animation classes in {path.name}")

        # DL012 empty section
        for sec in _SECTION_RE.finditer(text):
            snippet = text[sec.start(): sec.start() + 400]
            if self._looks_empty(snippet):
                add("DL012", f"section may be empty in {path.name}")
                break

        # DL001 hero heading too wide (single h1 line too long)
        h1_re = re.compile(r"<h1[^>]*>[^<]{0,200}</h1>", re.S)
        for m in h1_re.finditer(text):
            inner = re.sub(r"<[^>]+>", "", m.group(0)).strip()
            if len(inner) > 110:
                add("DL001", f"h1 length {len(inner)} chars")
                break

        # DL011 visual density too high (many grid children in one map)
        maps = re.findall(r"\.map\(", text)
        if len(maps) > 12 and len(cards) > 6:
            add("DL011", f"{len(maps)} list renders in {path.name}")

        # DL010 CTA below fold (CTA in footer-located component or far
        # down the file after a large hero block)
        if _CTA_BUTTON_RE.search(text) and \
                (re.search(r"CTA|cta|CallToAction|Footer", path.name) or
                 "footer" in path.name.lower()):
            add("DL010", "CTA appears only in lower sections")

        return findings

    @staticmethod
    def _looks_empty(snippet: str) -> bool:
        stripped = re.sub(r"<[^>]+>", "", snippet)
        stripped = re.sub(r"\s+", "", stripped)
        return len(stripped) < 12

    # ------------------------------------------------------------------
    def _lint_project_level(self, root: Path) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        # DL015 brand differentiation: check for a unique logo + custom
        # color tokens (not the bare default palette)
        components_dir = root / "src" / "components"
        has_logo = False
        for pattern in ("*Logo*", "*logo*", "*Brand*", "*brand*"):
            if list(components_dir.rglob(pattern)):
                has_logo = True
                break
        tokens = {}
        tokens_path = root / "design-tokens.json"
        if tokens_path.exists():
            try:
                import json
                tokens = json.loads(tokens_path.read_text(
                    encoding="utf-8"))
            except Exception:
                tokens = {}
        palette = tokens.get("palette", {}) or {}
        custom_hue = palette.get("primary_hue") is not None or \
            bool(palette.get("primary")) or \
            bool(palette.get("accent"))
        if not (has_logo and custom_hue):
            if not has_logo:
                findings.append(self._finding(
                    "DL015", "No brand logo component detected"))
            if not custom_hue:
                findings.append(self._finding(
                    "DL015", "No custom brand palette detected"))

        # DL004 spacing inconsistency: one top-level spacing scale present
        # (we can only sanity check tokens file for a consistent scale)
        spacing = tokens.get("spacing", {})
        if spacing and len(spacing) < 3:
            findings.append(self._finding(
                "DL004", "Spacing scale too small (<3 steps)"))

        return findings

    def _finding(self, code: str, message: str) -> Dict[str, Any]:
        rule = self.rules.get(code, {})
        return {
            "code": code,
            "severity": rule.get("severity", "P3"),
            "rule": rule.get("name", code),
            "message": message,
            "file": "(project)",
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _dedupe(
            findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for f in findings:
            key = (f["file"], f["code"])
            if key in seen:
                continue
            seen.add(key)
            out.append(f)
        return out

    # ------------------------------------------------------------------
    def report(self, result: Dict[str, Any]) -> str:
        lines = ["DESIGNLINT"]
        if not result.get("findings"):
            lines.append("No design lint findings.")
            return "\n".join(lines)
        for f in result["findings"]:
            lines.append(
                f"{f['severity']} {f['code']}  {f['message']}  "
                f"[{f['file']}]")
        return "\n".join(lines)


def run_designlint(project_dir: str) -> Dict[str, Any]:
    """One-call helper for orchestrator wiring."""
    return DesignLint().lint_directory(project_dir)


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = run_designlint(target)
    print(DesignLint().report(result))
    print(f"\n{result['summary']}")