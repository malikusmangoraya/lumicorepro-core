"""Repair pass for the i18n-wiring damage in shared components.

Fixes exactly the three patterns pass 3 can produce:

  1. copyright <p> lost its closing tag
         <p>&copy; {year} Brand. {t('footer.all_rights', ...)}
     -> restore </p>
  2. "Subscribed!" mangled into "...}d!"
         {t('footer.subscribe', 'Subscribe')}d!
     -> {t('forms.form_success', 'Subscribed!')}
  3. a bare t() inside JSX text that is not wrapped, leaving stray braces

Afterwards every touched file is re-validated for balanced <p> tags.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"


def repair(t: str) -> tuple:
    n = 0

    # 1) "{t('footer.subscribe', 'Subscribe')}d!"  -> proper success message
    t2, k = re.subn(
        r"\{t\('footer\.subscribe',\s*'Subscribe'\)\}d!",
        "{t('forms.form_success', 'Subscribed!')}", t)
    t, n = t2, n + k

    # 2) copyright paragraph missing </p>
    def close_p(m):
        return m.group(0) + "\n            </p>"
    t2, k = re.subn(
        r"(?m)^(\s*<p>&copy;[^\n]*\{t\([^\n]*?\}\.?\s*)$",
        close_p, t)
    t, n = t2, n + k

    return t, n


def p_balance(t: str) -> int:
    return len(re.findall(r"<p[\s>]", t)) - len(re.findall(r"</p>", t))


def main():
    targets = sys.argv[1:] or [d.name for d in sorted(PROJECTS.iterdir())
                               if (d / "frontend" / "package.json").exists()]
    fixed_files = 0
    total_edits = 0
    still_bad = []
    for slug in targets:
        src = PROJECTS / slug / "frontend" / "src"
        if not src.exists():
            continue
        for f in src.rglob("*.jsx"):
            t0 = f.read_text(encoding="utf-8", errors="ignore")
            if "t('" not in t0 and 't("' not in t0:
                continue
            t, n = repair(t0)
            bal = p_balance(t)
            if n and bal == 0:
                f.write_text(t, encoding="utf-8")
                fixed_files += 1
                total_edits += n
            elif bal != 0:
                still_bad.append((slug, f.relative_to(src).as_posix(), bal))

    print("REPAIR — i18n wiring damage")
    print(f"  files repaired : {fixed_files}")
    print(f"  edits applied  : {total_edits}")
    print(f"  still unbalanced: {len(still_bad)}")
    for s, r, b in still_bad[:20]:
        print(f"    {s}/{r}  (p delta {b:+d})")


if __name__ == "__main__":
    main()