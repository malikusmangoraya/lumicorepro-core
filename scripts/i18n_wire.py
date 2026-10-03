"""Phase B - wire page copy to t() and publish translations into locale JSON.

For each page component:
  1. read the translation cache
  2. add a `pages` namespace to every locale JSON containing the translated
     strings, keyed by a stable hash-free slug derived from the page + text
  3. replace each source string in JSX text / string literals with
     t('<page>.<key>', '<original>')

The English original is always passed as the i18next default so a missing
translation degrades to English rather than blanking the UI.

Idempotent: a string already wrapped in t() is left alone.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"
CACHE = PROJECTS / "I18N_TRANSLATION_CACHE.json"
TARGETS = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt", "ru", "tr", "ur", "zh"]


def slugify_key(s: str) -> str:
    k = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return k[:60] or "s"


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def jsx_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def process_project(slug: str, cache: dict, dry: bool = False) -> dict:
    fe = PROJECTS / slug / "frontend"
    src = fe / "src"
    pages_dir = src / "pages"
    loc_dir = src / "i18n" / "locales"
    if not pages_dir.exists() or not loc_dir.exists():
        return {"pages": 0, "wired": 0, "keys": 0}

    # 1) build key map for this project
    keymap: dict = {}
    pages_namespace: dict = {}
    for f in sorted(pages_dir.glob("*.jsx")):
        page = f.stem
        text = f.read_text(encoding="utf-8", errors="ignore")
        from i18n_extract_strings import extract_file
        for kind, s in extract_file(f):
            if s not in cache:
                continue
            k = f"{page}.{slugify_key(s)}"
            # dedupe collisions
            n = 1
            base = k
            while k in pages_namespace:
                n += 1
                k = f"{base}_{n}"
            pages_namespace[k] = cache[s]
            keymap.setdefault(f, {})[s] = k

    if not pages_namespace:
        return {"pages": 0, "wired": 0, "keys": 0}

    wired = 0
    # 2) wire each file
    for f, mapping in keymap.items():
        text = f.read_text(encoding="utf-8", errors="ignore")
        orig = text
        for s, k in mapping.items():
            if s not in text:
                continue
            # already inside a t() call? skip
            if re.search(r"t\(\s*['\"]" + re.escape(s[:20]), text):
                continue
            esc = jsx_escape(s)
            # JSX text node:  >text<   ->  >{t('key', 'text')}<
            text = re.sub(r">" + re.escape(esc) + r"<",
                          lambda m: ">{t('" + k + "', '" + esc + "')}<", text)
            # string literal:  'text'  ->  t('key', 'text')
            text = re.sub(r"'" + re.escape(esc) + r"'",
                          lambda m: "t('" + k + "', '" + esc + "')", text)
            wired += 1
        if text != orig and not dry:
            f.write_text(text, encoding="utf-8")

    # 3) publish pages namespace into every locale
    if not dry:
        for lg in ["en"] + TARGETS:
            f = loc_dir / f"{lg}.json"
            if not f.exists():
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            ns = data.setdefault("pages", {})
            for k, entry in pages_namespace.items():
                val = entry.get(lg)
                if val:
                    ns[k] = val
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"pages": len(keymap), "wired": wired, "keys": len(pages_namespace)}


def main():
    cache = load_cache()
    slugs = sys.argv[1:] or [d.name for d in sorted(PROJECTS.iterdir())
                             if (d / "frontend" / "package.json").exists()]
    dry = "--dry" in slugs
    if dry:
        slugs = [s for s in slugs if s != "--dry"]
    total_wired = 0
    touched = 0
    for slug in slugs:
        r = process_project(slug, cache, dry=dry)
        if r["wired"]:
            touched += 1
            total_wired += r["wired"]
            print(f"{slug}: wired {r['wired']} strings ({r['keys']} keys)")
    print(f"\ntotal wired: {total_wired} across {touched} projects (dry={dry})")


if __name__ == "__main__":
    main()