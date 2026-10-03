"""Replace leftover 6 and 8-digit blue hexes in CSS with the project brand."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restyle_unique_all as R

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"

# 6-digit blue-ish hexes
BLUE6 = {
    "#2563eb", "#22d3ee", "#0891b2", "#06b6d4", "#3b82f6",
    "#0ea5e9", "#0d9488", "#14b8a6", "#60a5fa", "#93c5fd",
    "#38bdf8", "#7dd3fc", "#bae6fd", "#e0f2fe", "#0284c7",
    "#67e8f9", "#a5f3fc", "#cffafe", "#e0f7fa",
}
# 8-digit blue-ish (with alpha): #RRGGBBAA
BLUE8_RE = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})")

BLUE8_PREFIXES = {"2563eb", "22d3ee", "0891b2", "06b6d4", "3b82f6",
                  "0ea5e9", "0d9488", "14b8a6", "60a5fa", "93c5fd",
                  "38bdf8", "7dd3fc", "bae6fd", "e0f2fe", "0284c7",
                  "67e8f9", "a5f3fc", "cffafe", "e0f7fa"}


def main() -> int:
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    fixed = 0
    for idx, proj in enumerate(projects):
        pal = R.palette_for(idx)
        br = pal["brand"]  # e.g. "#be882c"
        brg = br.lower()
        br8 = brg[1:]  # without #
        ac = pal["accent"].lower()
        ac8 = ac[1:]
        for f in proj.rglob("*"):
            if f.suffix != ".css":
                continue
            if "node_modules" in str(f) or "dist" in str(f):
                continue
            t = f.read_text(encoding="utf-8", errors="replace")
            new = t
            # 6-digit
            for hx in BLUE6:
                if hx in new:
                    new = new.replace(hx, brg)
                    fixed += 1
            # 8-digit
            def _rep8(m):
                digits, alpha = m.group(1), m.group(2)
                if digits in BLUE8_PREFIXES:
                    return "#" + (br8 if digits in ("2563eb", "3b82f6", "06b6d4") else ac8) + alpha
                return m.group(0)
            new = BLUE8_RE.sub(_rep8, new)
            fixed += len(BLUE8_RE.findall(t)) - len(BLUE8_RE.findall(new)) if new != t else 0
            if new != t:
                f.write_text(new, encoding="utf-8")
    print("blue hex (6+8 digit) replacements:", fixed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
