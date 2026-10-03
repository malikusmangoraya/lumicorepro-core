"""
Component Injection — rigid local-prebuilt-component mapping for generated projects.

LumicorePro ships a curated local component library (src/components/ui) plus
framer-motion wrappers. Instead of letting generated pages fall back to raw
semantic markup (e.g. <button>), every generator output is re-wired to the
pinned local components via the absolute `@/components/ui/*` alias.

The deterministic generator engines (Generation Matrix, Compliance Generator)
already emit library imports directly; this module provides:

* COMPONENT_LIBRARY — the single source of truth mapping a semantic need to a
  pinned local component + import string.
* inject_component_imports() — a conservative, idempotent post-generation
  sweep that upgrades *simple* raw <button> elements (no JSX-side-effect or
  expression attributes) in non-library generated files to the ButtonMotion
  wrapper with a pinned import. Complicated/dynamic markup is left untouched
  and is surfaced by the Enterprise Architect raw-interactive gate instead.
"""
import os
import re
from typing import Dict, List

# ── Pinned local component library (source of truth) ──────────────────────
# semantic action -> (component name, absolute import string)
COMPONENT_LIBRARY: Dict[str, tuple] = {
    "button": ("ButtonMotion", "@/components/ui/ButtonMotion"),
    "button_static": ("Button", "@/components/ui/Button"),
    "modal": ("Modal", "@/components/ui/Modal"),
    "card": ("Card", "@/components/ui/Card"),
    "badge": ("Badge", "@/components/ui/Badge"),
    "spinner": ("Spinner", "@/components/ui/Spinner"),
    "loading": ("Loading", "@/components/ui/Loading"),
    "progress": ("Progress", "@/components/ui/Progress"),
    "skeleton": ("Skeleton", "@/components/ui/Skeleton"),
    "tooltip": ("Tooltip", "@/components/ui/Tooltip"),
    "tabs": ("Tabs", "@/components/ui/Tabs"),
    "dropdown": ("Dropdown", "@/components/ui/Dropdown"),
    "accordion": ("Accordion", "@/components/ui/Accordion"),
    "alert": ("Alert", "@/components/ui/Alert"),
    "avatar": ("Avatar", "@/components/ui/Avatar"),
    "breadcrumb": ("Breadcrumb", "@/components/ui/Breadcrumb"),
    "divider": ("Divider", "@/components/ui/Divider"),
    "pagination": ("Pagination", "@/components/ui/Pagination"),
    "icon_button": ("IconButton", "@/components/ui/IconButton"),
    "empty": ("Empty", "@/components/ui/Empty"),
}

# Library-owned directories are copied, never rewritten by the sweep.
# NOTE: generated `layouts/` are NOT skipped — they carry raw semantic buttons
# that must be upgraded to ButtonMotion to pass the no-restricted-syntax gate.
_LIBRARY_DIRS = {
    "components/ui",
    "components/ui/",
    "components/motion",
    "components/forms",
    "components/icons",
    "components/common",
    "components/navigation",
    "components/Navbar.jsx",
    "components/Footer.jsx",
    "components/UniqueLogo.jsx",
}
_RAW_BUTTON_OPEN = re.compile(r"<button\b([^>]*)>")
_RAW_BUTTON_CLOSE = re.compile(r"</button\s*>")
_IMPORT_RE = re.compile(r"^\s*import\s.+$", re.M)


def _is_library_owned(rel_path: str) -> bool:
    norm = rel_path.replace(chr(92), "/")
    return any(d in norm for d in _LIBRARY_DIRS)


def _safe_button_attrs(attrs: str) -> bool:
    """Only auto-rewrite buttons whose attributes are plain (no JSX `=>`
    arrows, no nested `<`, no unbalanced braces). Complex handlers are left
    for the architect gate + self-healing loop."""
    if "=>" in attrs or "<" in attrs:
        return False
    return attrs.count("{") == attrs.count("}")


def inspect_raw_buttons(project_dir: str, src_root: str = "frontend/src") -> List[str]:
    """Return project-relative paths still containing raw <button> markup."""
    offenders: List[str] = []
    src = os.path.join(project_dir, src_root)
    if not os.path.isdir(src):
        return offenders
    for root, _, files in os.walk(src):
        if "node_modules" in root:
            continue
        for fname in files:
            if not fname.endswith((".jsx", ".tsx")):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, project_dir).replace("\\", "/")
            if _is_library_owned(rel):
                continue
            content = open(path, encoding="utf-8", errors="ignore").read()
            if _RAW_BUTTON_OPEN.search(content):
                offenders.append(rel)
    return offenders


def inject_component_imports(project_dir: str, src_root: str = "frontend/src") -> Dict:
    """Deterministic rigid-injection sweep over generated frontend sources.

    Upgrades simple raw <button> elements to the ButtonMotion wrapper with the
    pinned absolute import. Idempotent: files already referencing ButtonMotion
    are skipped. Returns a small report.
    """
    src = os.path.join(project_dir, src_root)
    report = {"files_upgraded": [], "buttons_swapped": 0, "skipped": 0}
    if not os.path.isdir(src):
        return report

    for root, _, files in os.walk(src):
        if "node_modules" in root:
            continue
        for fname in files:
            if not fname.endswith((".jsx", ".tsx")):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, project_dir).replace("\\", "/")
            if _is_library_owned(rel):
                continue
            with open(path, encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            if "ButtonMotion" in content or "<button" not in content:
                continue

            def _swap(match: re.Match) -> str:
                attrs = match.group(1)
                return f"<ButtonMotion{attrs}>" if _safe_button_attrs(attrs) else match.group(0)

            new_content = _RAW_BUTTON_OPEN.sub(_swap, content)
            # Only rewrite `</button>` closes when EVERY raw open was converted.
            # If any open tag survives (complex attrs like `onClick={() => ...}`
            # are intentionally skipped), rewriting the closes would leave an
            # unmatched `</ButtonMotion>` and corrupt the JSX — so skip the file
            # entirely instead and let the architect gate flag it.
            if new_content != content and _RAW_BUTTON_OPEN.search(new_content) is None:
                new_content = _RAW_BUTTON_CLOSE.sub("</ButtonMotion>", new_content)
                new_content = _ensure_import(new_content)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                swaps = len(_RAW_BUTTON_OPEN.findall(content)) - len(_RAW_BUTTON_OPEN.findall(new_content))
                report["buttons_swapped"] += max(swaps, 0)
                report["files_upgraded"].append(rel)
            else:
                report["skipped"] += 1
    return report


def _ensure_import(content: str) -> str:
    """Prepend the pinned ButtonMotion import when no import references it."""
    if re.search(r"import\s+ButtonMotion", content):
        return content
    return "import ButtonMotion from '@/components/ui/ButtonMotion';\n" + content


def library_prompt_note() -> str:
    """Instruction block appended to AI generation prompts so the provider
    emits pinned local-component imports instead of raw semantic markup."""
    lines = ["LocalComponentLibrary (absolute alias imports, prefer over raw HTML):",
             "  <button>        -> { component: ButtonMotion, import: \"@/components/ui/ButtonMotion\" }",
             "  <input>/<textarea>/<select> -> { component: Input/Textarea, import: \"@/components/ui/Input\" }",
             "RULE: Never emit raw semantic <button> elements. Always import the library wrapper."]
    return "\n".join(lines)