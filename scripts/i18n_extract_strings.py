"""Extract user-visible strings from a project's page components.

Only picks text that a visitor actually reads:
  * JSX text nodes           >Some headline<
  * string literals in arrays/objects that are rendered
Skips imports, className strings, style values, keys, and anything with
JSX inside (those are handled by their own leaves).
"""
import re
import sys
from pathlib import Path

ROOT = Path(r'D:\lumicorepro-core')
PROJECTS = ROOT / "generated-projects"

SKIP_ATTRS = re.compile(r'\b(className|class|href|to|src|style|id|type|name|key|'
                        r'placeholder|variant|size|icon|role|target|rel|htmlFor|'
                        r'autoComplete|autoFocus|inputMode)\s*=')
JSX_TEXT = re.compile(r">([^<>{}\n][^<>{}]*?)<", re.S)
STRING_LIT = re.compile(r"(?<![\w])'([^'\n]{4,200})'(?![\w])")


def looks_like_code(s: str) -> bool:
    t = s.strip()
    if not t:
        return True
    if "/" in t and " " not in t:
        return True
    if t.startswith(("$", "#", "var(", "rgb", "hsl", "url(")):
        return True
    if re.match(r"^[a-z-]+(\s+[a-z0-9:\[\].%_-]+)*$", t) and " " not in t:
        return True
    if t.endswith((".js", ".css", ".svg", ".png", ".jpg", ".webp")):
        return True
    if t.count("-") >= 2 and " " not in t:
        return True
    if t in {"text", "button", "submit", "email", "password", "checkbox", "radio"}:
        return True
    return False


def extract_file(path: Path) -> list:
    t = path.read_text(encoding="utf-8", errors="ignore")
    out = []

    # JSX text nodes
    for m in JSX_TEXT.finditer(t):
        s = m.group(1)
        if looks_like_code(s):
            continue
        if len(s.strip()) < 3:
            continue
        out.append(("jsx", s.strip()))

    # string literals that look like prose (sentence case + space)
    for m in STRING_LIT.finditer(t):
        s = m.group(1)
        if looks_like_code(s):
            continue
        # prose heuristic: contains a space and starts uppercase, or is a CTA
        if " " in s and (s[0].isupper() or s.lower() in {"subscribe", "contact us"}):
            out.append(("lit", s.strip()))

    # dedupe preserving order
    seen, res = set(), []
    for kind, s in out:
        if s in seen:
            continue
        seen.add(s)
        res.append((kind, s))
    return res


def main():
    slug = sys.argv[1]
    src = PROJECTS / slug / "frontend" / "src" / "pages"
    total = 0
    for f in sorted(src.glob("*.jsx")):
        items = extract_file(f)
        if not items:
            continue
        total += len(items)
        print(f"\n=== {f.name} ({len(items)} strings)")
        for kind, s in items:
            print(f"  [{kind}] {s[:100]}")
    print(f"\nTOTAL unique-ish strings in {slug}: {total}")


if __name__ == "__main__":
    main()