"""Discovery audit v1 - scan all generated project dirs and report state.

Read-only. Produces generated-projects/STATE_AUDIT.md + STATE_AUDIT.json
with per-project: industry/brand (from brand_map), pages, routes, backend
presence, dist presence, blue/gold hex scan, i18n, comparison marker,
placeholder scan, PLAN presence, logo presence.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GP = os.path.join(ROOT, "generated-projects")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

try:
    from brand_map import BRANDS
except Exception:  # pragma: no cover
    BRANDS = {}

BLUE_HEX = re.compile(
    r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})"
)
BLUE_RE = re.compile(
    r"#(?:0?0?2?(?:1e1e4|256|3b82|60a5|0ea5|06b6|38bd|0d94|0284|0369|1d4e|1e40|1e3a|1725|0f17|3b76|4f7f|6ba1|7eb1|93c|bae|dbe|eff|e0f2|f0f9|bfd|2563)"
    r"|0?1?[0-9a-fA-F]2[0-9a-fA-F]{5}2[0-9a-fA-F]{4})",
    re.IGNORECASE | re.VERBOSE,
)
GOLD_RE = re.compile(r"#(?:f59e|fbbf|fcd3|fde6|d977|b453|ac4|a162|d4a|caa6|f6e2|f7f0|fce7|fffb|ffed|d9a9|c98f|a97c|eab3|d4af|f1c4|ecc0)", re.IGNORECASE)

PLACEHOLDER_RE = re.compile(
    r"(TODO|FIXME|Lorem|ipsum|lorem|Dummy|dummy|placeholder-logo|Your Brand|YourLogo|BrandName|pending image|PLACEHOLDER|coming soon x)",
    re.IGNORECASE,
)

SKIP_DIRS = {"node_modules", "dist", "build", ".git", "venv", "__pycache__", ".pytest_cache", "coverage"}


def collect_files(dirpath, exts, maxdepth=8):
    out = []
    base = len(dirpath.split(os.sep))
    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        depth = len(root.split(os.sep)) - base
        if depth > maxdepth:
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(exts):
                out.append(os.path.join(root, f))
    return out


def scan_project(name):
    pdir = os.path.join(GP, name)
    frontend = os.path.join(pdir, "frontend")
    src = os.path.join(frontend, "src")
    info = {
        "dir": name,
        "has_frontend": os.path.isdir(frontend),
        "has_backend": os.path.isdir(os.path.join(pdir, "backend")),
        "has_database": os.path.isdir(os.path.join(pdir, "database")),
        "dist": os.path.isdir(os.path.join(frontend, "dist")),
        "pages": [],
        "routes": None,
        "backend_server": os.path.isfile(os.path.join(pdir, "backend", "server.js"))
        if os.path.isdir(os.path.join(pdir, "backend")) else False,
        "blue_files": 0,
        "gold_files": 0,
        "placeholders": 0,
        "i18n": os.path.isdir(os.path.join(src, "i18n")) if os.path.isfile(os.path.join(src, "main.jsx")) or os.path.isdir(src) else False,
        "comparison": False,
        "has_plan": False,
        "has_logo": False,
        "brand_content_key": None,
    }
    try:
        info["brand"] = BRANDS.get(name, {}).get("name", None)
        info["industry"] = BRANDS.get(name, {}).get("industry", None)
    except Exception:
        pass

    # pages
    pages_dir = os.path.join(src, "pages")
    if os.path.isdir(pages_dir):
        info["pages"] = sorted(
            f[:-4] for f in os.listdir(pages_dir)
            if f.endswith((".jsx", ".tsx"))
        )
    # routes from App.jsx
    appjsx = None
    for cand in ("App.jsx", "App.tsx"):
        p = os.path.join(src, cand)
        if os.path.isfile(p):
            appjsx = p
            break
    if appjsx:
        with open(appjsx, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        info["routes"] = len(re.findall(r"<Route\b", content))
        info["lazy_routes"] = "lazy(" in content
    # comparison marker lives in generated Home.jsx
    home = os.path.join(src, "pages", "Home.jsx")
    if os.path.isfile(home):
        with open(home, "r", encoding="utf-8", errors="ignore") as fh:
            hc = fh.read()
        info["comparison"] = "side-by-side" in hc or "The difference" in hc or "render_compare" in hc

    # scans
    if os.path.isdir(src):
        theme_like = []
        for ext in (".jsx", ".js", ".css", ".json"):
            for f in collect_files(src, (ext,), maxdepth=5):
                low = f.lower()
                if any(k in low for k in ("theme", "design-token", "globals", "index.css", "tailwind")):
                    theme_like.append(f)
        for f in theme_like:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    c = fh.read()
                if BLUE_RE.search(c):
                    info["blue_files"] += 1
                if GOLD_RE.search(c):
                    info["gold_files"] += 1
            except Exception:
                pass
        # placeholders across pages + home
        ph_scan = []
        for f in (os.path.join(src, "pages") and [os.path.join(src, "pages")] or []):
            if os.path.isdir(f):
                ph_scan = collect_files(f, (".jsx", ".tsx"), maxdepth=2)
        home = os.path.join(src, "pages", "Home.jsx")
        if os.path.isfile(home):
            ph_scan.append(home)
        for f in ph_scan:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    c = fh.read()
                info["placeholders"] += len(PLACEHOLDER_RE.findall(c))
            except Exception:
                pass

    # logo
    pub = os.path.join(frontend, "public")
    if os.path.isfile(os.path.join(pub, "logo.svg")):
        info["has_logo"] = True
    info["has_plan"] = os.path.isfile(os.path.join(pdir, "PLAN.md"))
    return info


def main():
    dirs = sorted(
        d for d in os.listdir(GP)
        if os.path.isdir(os.path.join(GP, d)) and not d.startswith(".")
    )
    results = []
    for d in dirs:
        try:
            results.append(scan_project(d))
        except Exception as exc:  # pragma: no cover
            results.append({"dir": d, "error": str(exc)})
    # stats
    total = len(results)
    backend = sum(1 for r in results if r.get("has_backend"))
    dist = sum(1 for r in results if r.get("dist"))
    with_routes = sum(1 for r in results if r.get("routes"))
    with_pages = sum(1 for r in results if r.get("pages"))
    plan = sum(1 for r in results if r.get("has_plan"))
    logo = sum(1 for r in results if r.get("has_logo"))
    blue = sum(1 for r in results if r.get("blue_files"))
    gold = sum(1 for r in results if r.get("gold_files"))
    i18n = sum(1 for r in results if r.get("i18n"))
    comp = sum(1 for r in results if r.get("comparison"))
    placeholders = sum(r.get("placeholders", 0) for r in results)

    lines = ["# STATE AUDIT v1 — All Generated Projects", ""]
    lines.append(f"> total={total} backend={backend} dist={dist} with_routes={with_routes} "
                 f"with_pages={with_pages} i18n={i18n} comparison={comp} plan={plan} "
                 f"logo={logo} blue_files_present={blue} gold_files_present={gold} placeholders={placeholders}")
    lines.append("")
    lines.append("| dir | industry | brand | pages | routes | backend | dist | i18n | comp | plan | logo | blue | gold | ph |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['dir']} | ERROR: {r['error']} |")
            continue
        lines.append(
            "| {dir} | {ind} | {brand} | {pages} | {routes} | {be} | {dist} | {i18n} | {comp} | {plan} | {logo} | {blue} | {gold} | {ph} |".format(
                dir=r["dir"], ind=r.get("industry") or "-", brand=(r.get("brand") or "-"),
                pages=r["pages"].__len__() if r["pages"] else 0,
                routes=r["routes"] or 0, be="Y" if r["has_backend"] else "-",
                dist="Y" if r["dist"] else "-", i18n="Y" if r["i18n"] else "-",
                comp="Y" if r["comparison"] else "-", plan="Y" if r["has_plan"] else "-",
                logo="Y" if r["has_logo"] else "-", blue=r["blue_files"],
                gold=r["gold_files"], ph=r["placeholders"],
            )
        )
    md_path = os.path.join(GP, "STATE_AUDIT.md")
    json_path = os.path.join(GP, "STATE_AUDIT.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"done: {md_path}, {json_path}")
    print("\n".join(lines[:2]))


if __name__ == "__main__":
    main()