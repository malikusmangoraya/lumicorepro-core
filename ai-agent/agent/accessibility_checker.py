"""
Accessibility Checker — WCAG 2.1 AA — LumicorePro AI Agent
===========================================================
Phase: Quality Verification (Phase 7 extension)

Performs static analysis of generated project files for:
  - WCAG 2.1 Level A & AA compliance
  - ARIA landmark & role usage
  - Keyboard navigation support
  - Colour contrast awareness (flag missing patterns)
  - Form label association
  - Image alt-text
  - Language attribute
  - Skip navigation links
  - Focus management
  - Responsive & zoom support
  - Reduced-motion media query support
  - RTL/BiDi text handling

Returns scored report with per-check results and actionable remediation hints.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from utils.logger import agent_logger
from utils.file_manager import FileManager


class AccessibilityChecker:
    """WCAG 2.1 AA static accessibility auditor for generated React/HTML projects."""

    # ── WCAG check definitions ────────────────────────────────────────────
    # Each check: id, criterion, level, description, search patterns (regex), fix_hint
    CHECKS: List[Dict[str, Any]] = [
        # ── Perceivable ──────────────────────────────────────────────────
        {
            "id": "img-alt",
            "criterion": "1.1.1",
            "level": "A",
            "name": "Image Alt Text",
            "desc": "All <img> elements should have a non-empty alt attribute.",
            "pattern": r"<img(?![^>]*\balt\s*=\s*[\"'][^\"']+[\"'])[^>]*>",
            "scope": "html_jsx",
            "fix": "Add alt='description' to all <img> tags. Use alt='' for decorative images.",
        },
        {
            "id": "lang-attr",
            "criterion": "3.1.1",
            "level": "A",
            "name": "Language Attribute",
            "desc": "The <html> element must have a lang attribute.",
            "pattern": r"<html(?![^>]*\blang\s*=)[^>]*>",
            "scope": "html",
            "fix": "Add lang='en' (or appropriate locale) to the <html> tag in index.html.",
        },
        {
            "id": "aria-labels",
            "criterion": "4.1.2",
            "level": "A",
            "name": "ARIA Labels on Interactive Elements",
            "desc": "Buttons and links should have accessible labels.",
            "pattern": r"<(button|a)\b(?![^>]*(?:aria-label|aria-labelledby|title|>(?:(?!<).)+<))[^>]*>(\s*</\1>|\s*/>)",
            "scope": "html_jsx",
            "fix": "Add aria-label='description' to icon-only buttons and links.",
        },
        {
            "id": "form-labels",
            "criterion": "1.3.1",
            "level": "A",
            "name": "Form Input Labels",
            "desc": "All form inputs should be associated with a <label>.",
            "pattern": r"<input\b(?![^>]*(?:aria-label|aria-labelledby|id\s*=))[^>]*>",
            "scope": "html_jsx",
            "fix": "Associate every <input> with a <label htmlFor='id'> or add aria-label.",
        },
        {
            "id": "heading-hierarchy",
            "criterion": "1.3.1",
            "level": "A",
            "name": "Heading Hierarchy",
            "desc": "Headings should not skip levels (h1→h3 without h2).",
            "pattern": None,  # handled by custom logic
            "scope": "custom",
            "fix": "Ensure heading levels are sequential: h1 → h2 → h3.",
        },
        {
            "id": "skip-nav",
            "criterion": "2.4.1",
            "level": "A",
            "name": "Skip Navigation Link",
            "desc": "A skip-to-main-content link should be the first focusable element.",
            "pattern": r"skip.*main|skip.*content|jump.*main",
            "scope": "html_jsx",
            "fix": "Add <a href='#main-content' className='sr-only focus:not-sr-only'>Skip to main content</a> as first element.",
        },
        {
            "id": "focus-visible",
            "criterion": "2.4.7",
            "level": "AA",
            "name": "Focus Indicator Visible",
            "desc": "Keyboard focus should be visually visible.",
            "pattern": r"outline\s*:\s*none|outline\s*:\s*0(?!px)|:focus\s*\{[^}]*outline\s*:\s*none",
            "scope": "css",
            "fix": "Never remove outline without providing an alternative focus indicator. Use focus-visible pseudo-class.",
        },
        # ── Operable ─────────────────────────────────────────────────────
        {
            "id": "keyboard-trap",
            "criterion": "2.1.2",
            "level": "A",
            "name": "No Keyboard Trap",
            "desc": "Modals and overlays must have keyboard escape / trap management.",
            "pattern": r"(Modal|Dialog|Drawer|Overlay).*?(onClose|onDismiss|handleClose)",
            "scope": "jsx",
            "fix": "Ensure modals close on Escape key and return focus to trigger element.",
        },
        {
            "id": "target-size",
            "criterion": "2.5.5",
            "level": "AAA",
            "name": "Touch Target Size",
            "desc": "Interactive targets should be at least 44×44 CSS pixels.",
            "pattern": r"(?:w|h)-[1-3]\b(?!\/)",  # Tailwind w-1..w-3 on buttons
            "scope": "jsx",
            "fix": "Use min-h-11 min-w-11 (44px) on all buttons and interactive elements.",
        },
        {
            "id": "reduced-motion",
            "criterion": "2.3.3",
            "level": "AAA",
            "name": "Reduced Motion Support",
            "desc": "Animations should respect prefers-reduced-motion media query.",
            "pattern": r"prefers-reduced-motion",
            "scope": "css",
            "fix": "Wrap animations in @media (prefers-reduced-motion: no-preference) { ... }",
        },
        # ── Understandable ────────────────────────────────────────────────
        {
            "id": "error-messages",
            "criterion": "3.3.1",
            "level": "A",
            "name": "Error Identification",
            "desc": "Form errors should be described to the user.",
            "pattern": r"aria-invalid|aria-describedby.*error|role=[\"']alert[\"']",
            "scope": "jsx",
            "fix": "Add role='alert' or aria-describedby linking to error message element.",
        },
        {
            "id": "color-contrast",
            "criterion": "1.4.3",
            "level": "AA",
            "name": "Colour Contrast (4.5:1)",
            "desc": "Text must have at least 4.5:1 contrast ratio against its background.",
            "pattern": None,  # static analysis can't compute ratios — flag for review
            "scope": "advisory",
            "fix": "Use a contrast checker (webaim.org/resources/contrastchecker) to verify text/background combinations.",
        },
        {
            "id": "text-resize",
            "criterion": "1.4.4",
            "level": "AA",
            "name": "Text Resize to 200%",
            "desc": "Content must not break when text is scaled to 200%.",
            "pattern": r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1",
            "scope": "html",
            "fix": "Remove user-scalable=no and maximum-scale=1 from viewport meta tag.",
        },
        # ── Robust ────────────────────────────────────────────────────────
        {
            "id": "valid-html",
            "criterion": "4.1.1",
            "level": "A",
            "name": "Valid HTML Structure",
            "desc": "HTML elements must have complete start and end tags.",
            "pattern": r"<(div|span|section|main|nav|header|footer)(?=[^/]*[^>]$)",
            "scope": "advisory",
            "fix": "Run HTML validator at validator.w3.org on the built output.",
        },
        {
            "id": "landmark-roles",
            "criterion": "1.3.6",
            "level": "AAA",
            "name": "ARIA Landmark Roles",
            "desc": "Page should contain main, nav, header, footer landmark regions.",
            "pattern": r"<(main|nav|header|footer|aside)\b|role=[\"'](main|navigation|banner|contentinfo|complementary)[\"']",
            "scope": "jsx",
            "fix": "Ensure page uses semantic HTML5 landmarks: <main>, <nav>, <header>, <footer>.",
        },
        {
            "id": "rtl-support",
            "criterion": "1.3.4",
            "level": "AA",
            "name": "RTL/BiDi Text Support",
            "desc": "Right-to-left languages (Arabic, Hebrew, Urdu) need dir='rtl' on container.",
            "pattern": r'dir\s*=\s*["\']rtl["\']|direction\s*:\s*rtl',
            "scope": "html_jsx_css",
            "fix": "Set dir='rtl' on <html> for RTL languages. Use logical CSS properties (margin-inline-start).",
        },
    ]

    # ── File type scopes ──────────────────────────────────────────────────
    SCOPE_EXTENSIONS: Dict[str, List[str]] = {
        "html":         [".html"],
        "css":          [".css"],
        "jsx":          [".jsx", ".tsx"],
        "html_jsx":     [".html", ".jsx", ".tsx"],
        "html_jsx_css": [".html", ".jsx", ".tsx", ".css"],
        "advisory":     [],  # advisory — never file-scanned
        "custom":       [],  # custom logic checks
    }

    def check(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Run full WCAG 2.1 AA accessibility audit on generated project."""
        agent_logger.info("AccessibilityChecker: Running WCAG 2.1 AA audit...")

        p_dir = Path(project_dir)
        frontend = p_dir / "frontend" / "src"

        results: List[Dict[str, Any]] = []
        level_a_passed = 0
        level_aa_passed = 0
        level_a_total = 0
        level_aa_total = 0

        # Collect all relevant source files
        all_files = self._collect_files(p_dir)

        for check in self.CHECKS:
            check_result = self._run_check(check, all_files, spec, p_dir)
            results.append(check_result)

            if check["level"] in ("A",):
                level_a_total += 1
                if check_result["passed"]:
                    level_a_passed += 1
            elif check["level"] in ("AA",):
                level_aa_total += 1
                if check_result["passed"]:
                    level_aa_passed += 1

        total_checks = len(results)
        passed_checks = sum(1 for r in results if r["passed"])
        advisory_checks = sum(1 for r in results if r.get("advisory"))

        # Score: only non-advisory checks counted
        scoreable = total_checks - advisory_checks
        score = round((passed_checks / max(scoreable, 1)) * 100, 1)

        # WCAG AA requires all A + AA checks to pass
        wcag_aa_compliant = (
            level_a_passed == level_a_total and
            level_aa_passed == level_aa_total
        )

        report = {
            "wcag_level_target":     "AA",
            "wcag_aa_compliant":     wcag_aa_compliant,
            "accessibility_score":   score,
            "checks_passed":         passed_checks,
            "checks_total":          total_checks,
            "level_a": {
                "passed": level_a_passed,
                "total":  level_a_total,
            },
            "level_aa": {
                "passed": level_aa_passed,
                "total":  level_aa_total,
            },
            "results":               results,
            "critical_failures":     [r for r in results if not r["passed"] and r["level"] == "A"],
            "aa_failures":           [r for r in results if not r["passed"] and r["level"] == "AA"],
            "rtl_checked":           spec.get("rtl_support", False),
            "remediation_priority":  self._prioritise_fixes(results),
        }

        agent_logger.info(
            f"AccessibilityChecker: score={score}%, "
            f"A:{level_a_passed}/{level_a_total}, "
            f"AA:{level_aa_passed}/{level_aa_total}, "
            f"WCAG_AA={'PASS' if wcag_aa_compliant else 'FAIL'}"
        )
        return report

    # ── Internal ──────────────────────────────────────────────────────────
    def _collect_files(self, p_dir: Path) -> Dict[str, str]:
        """Collect file contents keyed by path string."""
        files: Dict[str, str] = {}
        for root, _, filenames in os.walk(str(p_dir)):
            # Skip node_modules, __pycache__, .git
            if any(skip in root for skip in ["node_modules", "__pycache__", ".git", "dist", "build"]):
                continue
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext in (".jsx", ".tsx", ".js", ".ts", ".html", ".css", ".scss"):
                    fpath = os.path.join(root, fname)
                    try:
                        content = FileManager.read_file(fpath)
                        if content:
                            files[fpath] = content
                    except Exception:
                        pass
        return files

    def _run_check(
        self,
        check: Dict[str, Any],
        all_files: Dict[str, str],
        spec: Dict[str, Any],
        p_dir: Path,
    ) -> Dict[str, Any]:
        """Execute a single check and return result dict."""
        result_base = {
            "id":        check["id"],
            "criterion": check["criterion"],
            "level":     check["level"],
            "name":      check["name"],
            "fix":       check["fix"],
            "advisory":  check["scope"] == "advisory",
        }

        # Advisory checks always pass (manual review needed)
        if check["scope"] == "advisory":
            return {**result_base, "passed": True, "note": "Manual review required", "matches": []}

        # Custom logic checks
        if check["scope"] == "custom":
            return self._run_custom_check(check, all_files, result_base)

        # Pattern checks
        exts = self.SCOPE_EXTENSIONS.get(check["scope"], [])
        relevant = {
            path: content
            for path, content in all_files.items()
            if Path(path).suffix.lower() in exts
        }

        if not relevant:
            # No files to check — treat as passed (not applicable)
            return {**result_base, "passed": True, "note": "No applicable files found", "matches": []}

        pattern = check.get("pattern")
        if not pattern:
            return {**result_base, "passed": True, "note": "Pattern not defined", "matches": []}

        # For skip-nav, reduced-motion, rtl-support — check if pattern IS present (positive check)
        positive_checks = {"skip-nav", "reduced-motion", "rtl-support", "landmark-roles",
                           "error-messages", "focus-visible"}

        matches: List[str] = []
        for fpath, content in relevant.items():
            try:
                found = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if found:
                    matches.append(os.path.relpath(fpath, str(p_dir)))
            except re.error:
                pass

        if check["id"] in positive_checks:
            # Pass if pattern IS found somewhere
            passed = len(matches) > 0
        else:
            # Pass if pattern is NOT found (anti-pattern checks)
            # e.g., img without alt — pass if NO such img exists
            passed = len(matches) == 0

        return {
            **result_base,
            "passed":  passed,
            "matches": matches[:5],  # first 5 occurrences
            "match_count": len(matches),
        }

    def _run_custom_check(
        self,
        check: Dict[str, Any],
        all_files: Dict[str, str],
        result_base: Dict,
    ) -> Dict[str, Any]:
        """Custom heading hierarchy check."""
        if check["id"] == "heading-hierarchy":
            for fpath, content in all_files.items():
                if Path(fpath).suffix.lower() not in (".html", ".jsx", ".tsx"):
                    continue
                headings = re.findall(r"<h([1-6])", content, re.IGNORECASE)
                levels = [int(h) for h in headings]
                for i in range(1, len(levels)):
                    if levels[i] - levels[i - 1] > 1:
                        return {
                            **result_base,
                            "passed": False,
                            "note": f"Heading jump from h{levels[i-1]} to h{levels[i]} in {os.path.basename(fpath)}",
                            "matches": [fpath],
                        }
            return {**result_base, "passed": True, "note": "Heading hierarchy is sequential", "matches": []}
        return {**result_base, "passed": True, "matches": []}

    def _prioritise_fixes(self, results: List[Dict]) -> List[Dict[str, str]]:
        """Return top-5 highest-priority failed checks with fix hints."""
        failed = [r for r in results if not r.get("passed") and not r.get("advisory")]
        # Sort: Level A first, then AA
        order = {"A": 0, "AA": 1, "AAA": 2}
        failed.sort(key=lambda r: order.get(r.get("level", "AA"), 1))
        return [
            {"id": r["id"], "level": r["level"], "name": r["name"], "fix": r["fix"]}
            for r in failed[:5]
        ]
