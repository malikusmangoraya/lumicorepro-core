"""Replace blue-family rgba() literals in src CSS with project brand."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restyle_unique_all as R

GEN = Path(__file__).resolve().parent.parent / "generated-projects"
PAT = re.compile(
    r"rgba\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\s*,(\s*[0-9.]+\s*)\)", re.I
)


def is_blue(r, g, b):
    return b >= 45 and b - min(r, g) >= 28 and b - max(r, g) >= 20


def hex_to_rgb(hx):
    v = hx.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def main() -> int:
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    fixed = 0
    found = {}
    for idx, proj in enumerate(projects):
        pal = R.palette_for(idx)
        br = hex_to_rgb(pal["brand"] if pal["brand"].startswith("#") else "#" + pal["brand"])
        for f in (proj / "frontend" / "src").rglob("*.css"):
            t = f.read_text(encoding="utf-8", errors="replace")

            def _rep(m):
                r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
                a = m.group(4).strip()
                if is_blue(r, g, b):
                    return "rgba(%d, %d, %d, %s)" % (br[0], br[1], br[2], a)
                return m.group(0)

            new = PAT.sub(_rep, t)
            for m in PAT.finditer(t):
                r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if is_blue(r, g, b):
                    found.setdefault((r, g, b), set()).add(proj.name)
                    fixed += 1
            if new != t:
                f.write_text(new, encoding="utf-8")
    print("blue rgba replacements:", fixed)
    for k, v in sorted(found.items(), key=lambda x: -len(x[1])):
        print(k, "in", len(v), "projects:", sorted(v)[:4])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())