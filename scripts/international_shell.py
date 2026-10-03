"""International design-system shell fixer — v7.10.

Fixes per-project foundation so generated pages render as designed:
  1. tailwind.config.js  -> add token color slots (canvas/surface/heading/muted/footer/brand)
  2. src/index.css        -> dedupe repeated lumi-motion blocks, add `.card-lift`,
                            append token-based foundation overrides (buttons, headings,
                            eyebrows) so no hardcoded gold/red survives.

Idempotent (marker-guarded). Usage: python scripts/international_shell.py [slug ...]
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

SHELL_MARK = "/* ===== international-shell ===== */"
SHELL_END = "/* ===== end international-shell ===== */"

TAILWIND_COLOR_INJECT = """        brand: 'var(--t-brand)',
        canvas: 'var(--t-canvas)',
        surface: 'var(--t-surface)',
        heading: 'var(--t-heading)',
        muted: 'var(--t-muted)',
        footer: 'var(--t-footer)',"""

CSS_OVERRIDES = ("\n"
    "/* ===== international-shell ===== */\n"
    ".card-lift {\n"
    "  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);\n"
    "}\n"
    ".card-lift:hover {\n"
    "  transform: translateY(-6px);\n"
    "  box-shadow: var(--t-shadow-lift, 0 12px 32px rgba(0, 0, 0, 0.18));\n"
    "}\n"
    ".btn-primary {\n"
    "  background-color: var(--t-primary);\n"
    "  color: #ffffff;\n"
    "  border: none;\n"
    "  box-shadow: 0 8px 24px -8px var(--t-primary);\n"
    "}\n"
    ".btn-primary:hover {\n"
    "  background-color: var(--t-accent, var(--t-primary));\n"
    "  transform: translateY(-2px);\n"
    "  box-shadow: 0 14px 32px -10px var(--t-primary);\n"
    "}\n"
    ".btn-outline {\n"
    "  border: 2px solid var(--t-primary);\n"
    "  color: var(--t-primary);\n"
    "  background-color: transparent;\n"
    "}\n"
    ".btn-outline:hover {\n"
    "  background-color: var(--t-primary);\n"
    "  border-color: var(--t-primary);\n"
    "  color: #ffffff;\n"
    "}\n"
    ".section-eyebrow {\n"
    "  color: var(--t-primary);\n"
    "  padding-left: 3rem;\n"
    "}\n"
    ".section-eyebrow::before {\n"
    "  background-color: var(--t-primary);\n"
    "  width: 2.5rem;\n"
    "}\n"
    ".section-heading {\n"
    "  color: var(--t-heading);\n"
    "}\n"
    ".section-heading .accent {\n"
    "  color: var(--t-primary);\n"
    "}\n"
    "/* ===== end international-shell ===== */\n")


def fix_tailwind(css_dir: Path) -> bool:
    cfg = css_dir / "tailwind.config.js"
    if not cfg.exists():
        return False
    t = cfg.read_text(encoding="utf-8", errors="replace")
    if "canvas: 'var(--t-canvas)'" in t:
        return True  # already injected
    m = re.search(r"(\s*colors\s*:\s*\{)", t)
    if not m:
        return False
    insert_at = m.end(1)
    t = t[:insert_at] + "\n" + TAILWIND_COLOR_INJECT + t[insert_at:]
    cfg.write_text(t, encoding="utf-8")
    return True


def fix_css(css_file: Path) -> bool:
    if not css_file.exists():
        return False
    t = css_file.read_text(encoding="utf-8", errors="replace")

    # 1. collapse repeated lumi-motion blocks to the first one
    pat = re.compile(
        r"/\* ===== lumi-motion \(premium animation layer\) ===== \*/.*?/\* ===== end lumi-motion ===== \*/",
        re.S,
    )
    blocks = pat.findall(t)
    if len(blocks) > 1:
        t = t.replace("".join(blocks), blocks[0])

    # 2. append foundation overrides once
    if SHELL_MARK not in t:
        if not t.endswith("\n"):
            t += "\n"
        t += CSS_OVERRIDES
        css_file.write_text(t, encoding="utf-8")
    return True


def fix(root: str) -> dict:
    front = PROJECTS / root / "frontend"
    status = {"tailwind": False, "css": False}
    if (front / "tailwind.config.js").exists():
        status["tailwind"] = fix_tailwind(front)
    css_path = front / "src" / "index.css"
    if css_path.exists():
        status["css"] = fix_css(css_path)
    return status


def main():
    slugs = sys.argv[1:] or [
        d.name
        for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    ok = fail = 0
    for s in slugs:
        st = fix(s)
        if st["tailwind"] and st["css"]:
            ok += 1
        else:
            fail += 1
            print(f"  WARN {s}: {st}")
    print(f"international-shell: {ok} ok, {fail} warn/absent")


if __name__ == "__main__":
    main()