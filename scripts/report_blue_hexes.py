"""Report blue-family colour literals found in each built dist."""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core")
GEN = ROOT / "generated-projects"

# blue-family hexes (3 or 8 digit) as used by the delivery gate
BLUE = re.compile(
    r"#(?:0[0-9a-f]{2}|1[0-9a-f]{2}|2[0-9a-f]{2}|3[0-9a-f]{2}|4[0-9a-f]{2}"
    r"|5[0-6][0-9a-f])[0-9a-f]{0,6}\b", re.I)
# reduce false positives: only flag hues that actually read blue
def is_blue(h):
    h = h.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    if len(h) == 8:
        h = h[:6]
    if len(h) != 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return b > r + 18 and b >= g + 10

ASSETS = (".css", ".js", ".html", ".svg", ".json")
hits, total = {}, Counter()
for d in sorted(GEN.iterdir()):
    dist = d / "frontend" / "dist"
    if not dist.is_dir():
        continue
    found = Counter()
    for f in dist.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in ASSETS:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in BLUE.findall(txt):
            if is_blue(m):
                found[m.lower()] += 1
    if found:
        hits[d.name] = found
        total.update(found)

print(f"dists with blue literals: {len(hits)}")
for slug, c in list(hits.items())[:30]:
    print(f"  {slug:<24} {dict(c.most_common(5))}")
print("\nmost common blue hexes:")
for hx, n in total.most_common(15):
    print(f"  {hx} x{n}")