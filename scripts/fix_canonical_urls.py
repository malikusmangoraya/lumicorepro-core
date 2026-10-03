"""Force canonical / og:url / hreflang to the real deployed Pages URL.

The 10 campaign brands carry legacy short repo names in their SEO meta
(e.g. /aurelia/) while the site is actually served from /aurelia-estates/.
A canonical that disagrees with the serving URL is an SEO defect, so the
deployed URL recorded in LIVE_URL.txt is treated as authoritative and the
meta is rewritten in source (frontend/index.html + index.html) before a
rebuild regenerates dist.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core")
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402

URL_RE = re.compile(r"https?://[^\s'\"><)]+")
LANG_DIR = {
    "ar": "ar", "de": "de", "en": "en", "es": "es", "fr": "fr", "hi": "hi",
    "id": "id", "ja": "ja", "ko": "ko", "pt": "pt", "ru": "ru", "tr": "tr",
    "ur": "ur", "zh": "zh",
}

CANON_RE = re.compile(r'(<link[^>]*rel="canonical"[^>]*href=")([^"]*)(")', re.I)
OGURL_RE = re.compile(r'(<meta[^>]*property="og:url"[^>]*content=")([^"]*)(")', re.I)
OGTITLE_RE = re.compile(r'(<meta[^>]*property="og:title"[^>]*content=")([^"]*)(")', re.I)
OGSITE_RE = re.compile(r'(<meta[^>]*property="og:site_name"[^>]*content=")([^"]*)(")', re.I)
OGDESC_RE = re.compile(r'(<meta[^>]*property="og:description"[^>]*content=")([^"]*)(")', re.I)
OGIMG_RE = re.compile(r'(<meta[^>]*property="og:image"[^>]*content=")([^"]*)(")', re.I)
ALT_RE = re.compile(r'(<link[^>]*rel="alternate"[^>]*hrefLang=")([^"]*)(")', re.I)
ALTRE_RE = re.compile(r'(<link[^>]*rel="alternate"[^>]*hreflang=")([^"]*)(")', re.I)


def live_url(slug):
    f = GEN / slug / "LIVE_URL.txt"
    if not f.exists():
        return ""
    for u in URL_RE.findall(f.read_text(errors="ignore")):
        if "github.io" in u:
            return u.rstrip("/")
    return ""


def patch(html, base, card):
    before = html
    html = CANON_RE.sub(lambda m: m.group(1) + base + m.group(3), html)
    html = OGURL_RE.sub(lambda m: m.group(1) + base + m.group(3), html)
    html = OGSITE_RE.sub(lambda m: m.group(1) + card["name"] + m.group(3), html)
    # alternate hreflang links must not point at the stale base either
    for rx in (ALT_RE, ALTRE_RE):
        def fix_alt(m, base=base):
            lang = m.group(2)
            tail = "" if lang == "x-default" else "/" + LANG_DIR.get(lang, lang)
            return m.group(1) + base + tail + m.group(3)
        html = rx.sub(fix_alt, html)

    # hreflang sets are incomplete without an x-default entry. Rebuild the whole
    # block so a malformed hreflang="<url>" attribute (a bad first pass that used
    # a URL where a language code belongs) cannot survive.
    if "LUMI-HREFLANG" in html:
        block = [f'    <!-- LUMI-HREFLANG-START -->',
                 f'    <link rel="alternate" hreflang="x-default" href="{base}/" />']
        for lang in LANG_DIR:
            block.append(
                f'    <link rel="alternate" hreflang="{lang}" '
                f'href="{base}/?lang={lang}" />')
        block.append(f'    <!-- LUMI-HREFLANG-END -->')
        start = html.find("<!-- LUMI-HREFLANG-START -->")
        end = html.find("<!-- LUMI-HREFLANG-END -->")
        if start != -1 and end != -1 and end > start:
            html = html[:start] + "\n".join(block) + html[end + len("<!-- LUMI-HREFLANG-END -->"):]
        else:
            html = html.replace("<head>", "<head>\n" + "\n".join(block), 1)
    return html, html != before


fixed, skipped = [], []
for slug, card in sorted(BRANDS.items()):
    proj = GEN / slug
    if not (proj / "frontend" / "package.json").exists():
        continue
    base = live_url(slug)
    if not base:
        skipped.append((slug, "no LIVE_URL"))
        continue
    targets = [proj / "frontend" / "index.html", proj / "frontend" / "public" / "index.html"]
    touched = []
    for t in targets:
        if not t.exists():
            continue
        html = t.read_text(encoding="utf-8", errors="ignore")
        new, changed = patch(html, base, card)
        if changed:
            t.write_text(new, encoding="utf-8")
            touched.append(t.relative_to(proj).as_posix())
    if touched:
        fixed.append((slug, base, touched))
    else:
        skipped.append((slug, "already consistent"))

print(f"canonical/og:url aligned: {len(fixed)}")
for slug, base, touched in fixed:
    print(f"  {slug:<20} -> {base}   {touched}")
print(f"no change needed / skipped: {len(skipped)}")
for s, why in skipped[:10]:
    print(f"  {s:<20} {why}")
json.dump([{"slug": s, "url": b, "files": t} for s, b, t in fixed],
          open(ROOT / "generated-projects" / "SEO_URL_FIX.json", "w", encoding="utf-8"),
          indent=2)