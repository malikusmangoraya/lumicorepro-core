"""Pass 1 — global international fixes for every generated project.

  * src/styles/rtl.css          (real RTL layer, logical properties)
  * import it from main.jsx
  * hreflang alternates + x-default for every shipped locale
  * canonical / og:url / og:image -> the project's REAL deployed Pages URL

Idempotent: safe to re-run.
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"
RTL_SRC = Path(__file__).resolve().parent / "_rtl_stylesheet.css"

HREFLANG_LABEL = {
    "en": "English", "ar": "Arabic", "de": "German", "es": "Spanish",
    "fr": "French", "hi": "Hindi", "id": "Indonesian", "ja": "Japanese",
    "ko": "Korean", "pt": "Portuguese", "ru": "Russian", "tr": "Turkish",
    "ur": "Urdu", "zh": "Chinese",
}


def slugs():
    return [d.name for d in sorted(PROJECTS.iterdir()) if (d / "frontend" / "package.json").exists()]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def write(p: Path, t: str):
    p.write_text(t, encoding="utf-8")


def live_url(slug: str) -> str:
    """Project's real deployed Pages URL from LIVE_URL.txt / dist og:url."""
    proj = PROJECTS / slug
    url_re = re.compile(r"https?://[^\s'\"><)]+")
    for f in proj.rglob("LIVE_URL.txt"):
        try:
            for u in url_re.findall(read(f)):
                if "github.io" in u:
                    return u.rstrip("/")
        except Exception:
            pass
    for cand in ("frontend/dist/index.html", "frontend/index.html"):
        f = proj / cand
        if f.exists():
            m = re.search(r'property="og:url"\s+content="([^"]+)"', read(f))
            if m and "github.io" in m.group(1):
                return m.group(1).rstrip("/")
    return ""


def patch_rtl(slug: str) -> list:
    """Install rtl.css and make sure it is imported."""
    done = []
    fe = PROJECTS / slug / "frontend"
    styles = fe / "src" / "styles"
    styles.mkdir(parents=True, exist_ok=True)
    rtl = styles / "rtl.css"
    body = RTL_SRC.read_text(encoding="utf-8")
    if not rtl.exists() or rtl.read_text(encoding="utf-8", errors="ignore") != body:
        write(rtl, body)
        done.append("rtl.css")

    main = fe / "src" / "main.jsx"
    if main.exists():
        t = read(main)
        imports = list(re.finditer(r"^import .*?;$", t, re.M))
        # ensure i18n bootstrap runs before the app renders
        if not re.search(r"^import\s+['\"]\./i18n['\"]", t, re.M) and \
           not re.search(r"^import\s+['\"].*/i18n['\"]", t, re.M):
            if imports:
                pos = imports[0].start()
                t = t[:pos] + "import './i18n';\n" + t[pos:]
                done.append("i18n-import")
        # rtl.css import
        if "styles/rtl.css" not in t:
            imports = list(re.finditer(r"^import .*?;$", t, re.M))
            if imports:
                pos = imports[-1].end()
                t = t[:pos] + "\nimport './styles/rtl.css';" + t[pos:]
                done.append("main-import")
        if done:
            write(main, t)
    return done


def rewrite_seo_html(t: str, base_url: str, langs: list | None = None) -> str:
    """Pure HTML transform: point every SEO identity field at `base_url`.

    Single source of truth for the campaign SEO contract, shared by
    patch_seo() and scripts/fix_campaign_seo.py so the generator and the
    repair tool can never drift apart.

    Fixes (all three were broken on every deployed campaign site):
      - og:image pointed at a truncated repo slug  -> 404
      - twitter:image pointed at an invented <brand>.com domain -> 404
      - JSON-LD @id/url/logo used that same invented domain, contradicting
        og:url/canonical so the entity had no resolvable identity
    """
    # Strip any previously injected block so this stays idempotent. Both the
    # leading and trailing run of whitespace have to go: leaving either behind
    # means every pass grows the document by one blank line before the block.
    t = re.sub(r"\s*<!--\s*LUMI-HREFLANG-START\s*-->.*?<!--\s*LUMI-HREFLANG-END\s*-->\s*", "\n    ", t, flags=re.S)

    if base_url:
        t = re.sub(r'(<link\s+rel="canonical"\s+href=")[^"]*(")',
                   lambda m: m.group(1) + base_url + "/\"", t)
        t = re.sub(r'(<meta\s+property="og:url"\s+content=")[^"]*(")',
                   lambda m: m.group(1) + base_url + "/\"", t)
        t = re.sub(r'(<meta\s+property="og:image"\s+content=")[^"]*(")',
                   lambda m: m.group(1) + base_url + "/og-image.svg\"", t)
        # twitter:image was left pointing at the invented custom domain
        # (e.g. https://brand.com/og-image.svg) while og:image moved to the
        # real Pages URL — X/Twitter previews were silently 404.
        t = re.sub(r'(<meta\s+name="twitter:image"\s+content=")[^"]*(")',
                   lambda m: m.group(1) + base_url + "/og-image.svg\"", t)
        t = re.sub(r'(<meta\s+property="og:locale"\s+content=")[^"]*(")',
                   lambda m: m.group(1) + "en_US\"", t)

        # JSON-LD must describe the URL that is actually served. Scoped to the
        # ld+json block and to @id/url keys only, so genuine third-party links
        # (fonts, Stripe, analytics) and inline <script> payloads are never
        # touched.
        #
        # Each value is rewritten as a whole, not by substituting just the
        # origin: the original regex consumed scheme+host only, so a second run
        # turned /ember-salt/#website into /ember-salt/ember-salt/#website.
        # Keeping the original path suffix, and returning already-correct
        # values unchanged, makes repeated runs converge.
        _defect = re.compile(r'("(?:@id|url)"\s*:\s*")(https?://[^"]*)(")')

        def _jsonld_value(m):
            head, value, tail = m.groups()
            if value.rstrip("/") == base_url.rstrip("/") or value.startswith(base_url + "/"):
                return m.group(0)
            _, _, rest = value.partition("://")[2].partition("/")
            suffix = ("/" + rest) if rest else ""
            return head + base_url + suffix + tail

        def _fix_jsonld_block(block_match):
            return _defect.sub(_jsonld_value, block_match.group(0))

        t = re.sub(
            r'<script type="application/ld\+json">.*?</script>',
            _fix_jsonld_block,
            t,
            flags=re.S,
        )

    if langs:
        rows = [
            f'    <link rel="alternate" hreflang="{lg}" href="{base_url}/?lang={lg}" />'
            for lg in langs
        ]
        rows.append(f'    <link rel="alternate" hreflang="x-default" href="{base_url}/" />')
        block = ("\n    <!-- LUMI-HREFLANG-START -->\n" + "\n".join(rows)
                 + "\n    <!-- LUMI-HREFLANG-END -->")
        # place right after <html ...> head opening, before <title>. The
        # replacement consumes any whitespace immediately before <title> so a
        # re-run cannot accumulate a blank line ahead of the block.
        t = (re.sub(r"\s*<title>", block + "\n    <title>", t, count=1)
             if "<title>" in t else block + t)

    return t


def patch_seo(slug: str, base_url: str, langs: list) -> list:
    """hreflang alternates + correct canonical/og for the real deploy URL."""
    done = []
    for cand in ("frontend/index.html", "frontend/dist/index.html"):
        f = PROJECTS / slug / cand
        if not f.exists():
            continue
        orig = read(f)
        t = rewrite_seo_html(orig, base_url, langs)
        if t != orig:
            write(f, t)
            done.append(cand.split("/")[-2] + "/" + cand.split("/")[-1])
    return done


def main():
    targets = sys.argv[1:] or slugs()
    stats = {"rtl_css": 0, "main_import": 0, "seo": 0, "no_url": [], "no_lang": []}
    for slug in targets:
        fe = PROJECTS / slug / "frontend"
        loc = fe / "src" / "i18n" / "locales"
        langs = sorted(p.stem for p in loc.glob("*.json")) if loc.exists() else []
        if not langs:
            stats["no_lang"].append(slug)

        res = patch_rtl(slug)
        if "rtl.css" in res:
            stats["rtl_css"] += 1
        if "main-import" in res:
            stats["main_import"] += 1

        url = live_url(slug)
        if not url:
            stats["no_url"].append(slug)
        else:
            if patch_seo(slug, url, langs):
                stats["seo"] += 1

    print("PASS 1 — global international fixes")
    print(f"  rtl.css written      : {stats['rtl_css']}")
    print(f"  main.jsx import added: {stats['main_import']}")
    print(f"  SEO/hreflang patched : {stats['seo']}")
    print(f"  no live url          : {len(stats['no_url'])} {stats['no_url'][:6]}")
    print(f"  no locales           : {len(stats['no_lang'])} {stats['no_lang'][:6]}")


if __name__ == "__main__":
    main()