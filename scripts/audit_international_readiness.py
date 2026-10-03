"""International readiness audit — BEFORE state for the comparison table.

Measures what AGENTS.md section 10 (i18n + RTL + CURRENCY) and section 17
(international delivery) actually require, per project, from real files.

Dimensions checked per project:
  i18n      - src/i18n wired + locales shipped + t() usage in pages
  locales   - how many locale JSON files exist
  rtl       - dir="rtl" handling / rtl.css / logical CSS properties
  currency  - CurrencyContext + Intl.NumberFormat + selector UI
  legal     - privacy + terms pages (compliance)
  consent   - GDPR consent banner
  seo       - hreflang alternates + og:locale
  headers   - Vary/Accept-Language or lang attribute on <html>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

CHECKS = {
    # key -> (label, list of (relative glob, regex))   globs are relative to frontend/
    "i18n_import": ("i18n imported in main", [("src/main.jsx", r"import\s+['\"].*i18n")]),
    "i18n_file": ("i18n config exists", [("src/i18n/index.js", r"i18n|resources")]),
    "t_usage": ("t() used in pages", [("src/pages/*.jsx", r"\bt\(\s*['\"]")]),
    "locale_files": ("locale JSON count", None),
    "dir_rtl": ("dir=rtl handled", [("src/i18n/index.js", r"dir\s*=\s*['\"]rtl|setAttribute\(\s*['\"]dir"),
                                    ("src/**/*.jsx", r"dir=\{\s*dir|dir\s*=\s*['\"]rtl")]),
    "logical_css": ("logical CSS props", [("src/**/*.css", r"margin-inline|padding-inline|inset-inline")]),
    "rtl_css": ("rtl.css present", [("src/styles/rtl.css", r".")]),
    "currency_ctx": ("CurrencyContext", [("src/context/CurrencyContext.jsx", r"createContext|CurrencyProvider")]),
    "intl_number": ("Intl.NumberFormat", [("src/**/*.jsx", r"Intl\.NumberFormat")]),
    "currency_sel": ("CurrencySelector UI", [("src/components/**/*.jsx", r"CurrencySelector")]),
    "lang_sel": ("LanguageSelector UI", [("src/components/**/*.jsx", r"LanguageSelector")]),
    "privacy": ("privacy page", [("src/pages/Privacy*.jsx", r".")]),
    "terms": ("terms page", [("src/pages/Terms*.jsx", r".")]),
    "gdpr": ("GDPR consent", [("src/**/*.jsx", r"gdpr|consent|cookieConsent")]),
    "hreflang": ("hreflang alternates", [("index.html", r"hreflang")]),
    "og_locale": ("og:locale", [("index.html", r"og:locale")]),
}


def project_slugs():
    return [d.name for d in sorted(PROJECTS.iterdir()) if (d / "frontend" / "package.json").exists()]


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def scan(slug: str) -> dict:
    base = PROJECTS / slug / "frontend"
    res = {"slug": slug}
    for key, (label, pats) in CHECKS.items():
        if key == "locale_files":
            loc = base / "src" / "i18n" / "locales"
            n = len(list(loc.glob("*.json"))) if loc.exists() else 0
            res[key] = {"ok": n > 0, "label": label, "value": n}
            continue
        hits = 0
        for rel, pat in pats or []:
            for f in base.glob(rel):
                if re.search(pat, read(f)):
                    hits += 1
        res[key] = {"ok": hits > 0, "label": label, "value": hits}
    score = sum(1 for k in CHECKS if res[k]["ok"])
    res["score"] = score
    res["total"] = len(CHECKS)
    return res


def main():
    slugs = sys.argv[1:] or project_slugs()
    rows = [scan(s) for s in slugs]
    out = {
        "projects": len(rows),
        "dimensions": {k: v[0] for k, v in CHECKS.items()},
        "rows": rows,
        "aggregate": {
            k: {"pass": sum(1 for r in rows if r[k]["ok"]), "of": len(rows)}
            for k in CHECKS
        },
    }
    p = PROJECTS / "INTERNATIONAL_READINESS.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(f"scanned {len(rows)} projects -> {p}")
    print()
    print(f"{'DIMENSION':<24} {'PASS':>6}  {'COVERAGE':>9}")
    for k, v in out["aggregate"].items():
        pct = 100.0 * v["pass"] / v["of"]
        bar = "#" * int(pct / 5)
        print(f"{k:<24} {v['pass']:>4}/{v['of']:<3} {pct:>6.1f}%  {bar}")
    full = sum(1 for r in rows if r["score"] == r["total"])
    print()
    print(f"fully international ({full}/{len(rows)})")


if __name__ == "__main__":
    main()