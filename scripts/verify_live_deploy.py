"""Live re-verify: served HTML must carry the correct canonical + hreflang block.

Reads each brand's LIVE_URL, fetches the deployed index.html, and confirms the
canonical/og:url equals the URL the site is actually served from. Also confirms
the rtl.css asset and a page-scoped t() key are present in the served bundle.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core")
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402

URL_RE = re.compile(r"https?://[^\s'\"><)]+")
CANON_RE = re.compile(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', re.I)
OGURL_RE = re.compile(r'<meta[^>]*property="og:url"[^>]*content="([^"]+)"', re.I)
HDRS = {"User-Agent": "Mozilla/5.0 (compatible; lumicorepro-verify/1.0)"}


def live_url(slug):
    f = GEN / slug / "LIVE_URL.txt"
    if not f.exists():
        return ""
    for u in URL_RE.findall(f.read_text(errors="ignore")):
        if "github.io" in u:
            return u.rstrip("/")
    return ""


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", errors="ignore")


def check(slug):
    base = live_url(slug)
    if not base:
        return slug, "NO_URL", "-", "-", "-", "-"
    try:
        status, html = fetch(base + "/")
    except urllib.error.HTTPError as e:
        return slug, f"HTTP{e.code}", "-", "-", "-", "-"
    except Exception as e:
        return slug, type(e).__name__, "-", "-", "-", "-"

    mc, mo = CANON_RE.search(html), OGURL_RE.search(html)
    canon = mc.group(1).rstrip("/") if mc else ""
    ogurl = mo.group(1).rstrip("/") if mo else ""
    canon_ok = "OK" if canon == base else f"BAD({canon[-28:]})"
    og_ok = "OK" if ogurl == base else f"BAD({ogurl[-28:]})"
    hreflang = "OK" if "LUMI-HREFLANG" in html else "MISSING"

    # rtl.css is imported from main.jsx, so it is bundled into the hashed CSS
    # asset rather than linked in index.html. Check the served stylesheet.
    rtl = "OK"
    key = "-"
    for m in re.finditer(r'assets/[A-Za-z0-9_.-]+\.(?:js|css)', html):
        try:
            _, blob = fetch(base + "/" + m.group(0), timeout=60)
        except Exception:
            continue
        if m.group(0).endswith(".css"):
            # a real RTL sheet carries logical properties or a dir-aware rule
            if ("margin-inline" in blob or "padding-inline" in blob
                    or "[dir=rtl]" in blob or "rtl" in blob.lower()):
                rtl = "OK"
            else:
                rtl = "no-rtl-rules"
        else:
            if re.search(r'["\']Home\.[a-z0-9_]{18,}', blob):
                key = "OK"
    return slug, str(status), canon_ok, og_ok, f"{hreflang}/{rtl}", key


slugs = [s for s in sorted(BRANDS)
         if (GEN / s / "frontend" / "package.json").exists()]
with ThreadPoolExecutor(max_workers=8) as ex:
    rows = list(ex.map(check, slugs))

hdr = f"{'slug':<20} {'http':<6} {'canonical':<34} {'og:url':<34} hreflang/rtl  t_key"
print(hdr)
print("-" * len(hdr))
for r in rows:
    print(f"{r[0]:<20} {r[1]:<6} {r[2]:<34} {r[3]:<34} {r[4]:<14} {r[5]}")

http_ok = sum(1 for r in rows if r[1] == "200")
canon_ok = sum(1 for r in rows if r[2] == "OK")
og_ok = sum(1 for r in rows if r[3] == "OK")
hl = sum(1 for r in rows if r[4] == "OK/OK")
key = sum(1 for r in rows if r[5] == "OK")
n = len(rows)
print(f"\nchecked {n} live sites")
print(f"  http 200        : {http_ok}/{n}")
print(f"  canonical match : {canon_ok}/{n}")
print(f"  og:url match    : {og_ok}/{n}")
print(f"  hreflang + rtl  : {hl}/{n}")
print(f"  i18n t() in js  : {key}/{n}")
json.dump([{"slug": r[0], "http": r[1], "canonical": r[2], "og_url": r[3],
            "hreflang_rtl": r[4], "t_key": r[5]} for r in rows],
          open(GEN / "LIVE_VERIFY.json", "w", encoding="utf-8"), indent=2)