#!/usr/bin/env python3
"""OFFLINE per-zip brand-content ground truth: open every delivery zip, read its
dist/index.html, and report whether the served <title>/<h1>/<body> actually
carry THIS brand's name. No network, no deployer import — pure zip internals.
"""
import json, re, zipfile
from pathlib import Path

CORE = Path(r"D:\lumicorepro-core")
delivery = CORE / "delivery"

# Expected brand display-name per canonical repo, derived the SAME way the
# deployer builds LIVE links: repo stem -> title case words.
def brand_from_stem(stem: str) -> str:
    return " ".join(w.capitalize() for w in stem.replace("_", "-").split("-") if w)

rows = []
for z in sorted(delivery.glob("*.zip")):
    slug = z.stem
    brand = brand_from_stem(slug)
    title = h1 = body = ""
    try:
        with zipfile.ZipFile(z) as zf:
            cands = [n for n in zf.namelist() if re.match(r"^(?:dist|frontend/dist)/index\.html$", n)]
            for n in cands[:1]:
                body = zf.read(n).decode("utf-8", errors="ignore")
    except Exception:
        pass
    tm = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    title = re.sub(r"<[^>]+>", "", tm.group(1)).strip() if tm else ""
    hm = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.I | re.S)
    h1 = re.sub(r"<[^>]+>", "", hm.group(1)).strip() if hm else ""
    b = brand.lower()
    t_ok = b in title.lower()
    b_ok = b in body.lower()
    # generic "Build" marker = deployer never touched this Home
    generic = bool(re.search(r"\bBuild\b", body)) and not b_ok
    rows.append((slug, brand, title, h1, t_ok, b_ok, generic))

matched = [r for r in rows if (r[4] or r[5]) and not r[6]]
found_title_only = [r for r in rows if (r[4] or r[5])]

print(f"zips: {len(rows)} | brand-matched (title or body): {len(matched)} | any brand-name at all: {len(found_title_only)}")
print("=" * 110)
for slug, brand, title, h1, t_ok, b_ok, generic in sorted(rows, key=lambda r: (not (r[4] or r[5]), r[0])):
    verdict = "MATCH" if (t_ok or b_ok) and not generic else ("GENERIC-Build" if generic else "unnamed")
    print(f"{verdict:<14}  {slug:<32} title={title[:55]!r}  h1={h1[:40]!r}")

(CORE / "delivery" / "_BRAND_CONTENT_AUDIT.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("-> delivery/_BRAND_CONTENT_AUDIT.json")
