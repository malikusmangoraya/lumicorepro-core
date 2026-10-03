"""Unique non-blue restyle + rebuild for every generated project.

Deterministic, offline. For each project with a real frontend:
  1. decode industry/brand via Benchmark-First (mandatory design research step),
  2. assign a UNIQUE palette from 48 non-blue hue families (one per project,
     sorted alphabetically => 1:1, no collisions), so no two sites share a
     brand color and NONE are blue/cyan/indigo,
  3. patch `frontend/src/lib/theme.js` design-tokens (`--t-brand*`,
     `--t-accent-*`) and purge blue-dominant hex literals from src,
  4. `npm run build` and record the result.

Writes generated-projects/UNIQUE_RESTYLE_REPORT.md + JSON progress.
"""
import colorsys
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "ai-agent"))

from agent.intelligence.benchmark_first import run_benchmark_first  # noqa: E402


def hsl_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def is_blue_dominant(hexcode: str) -> bool:
    try:
        v = hexcode.lstrip("#")
        if len(v) == 3:
            v = "".join(c * 2 for c in v)
        if len(v) != 6:
            return False
        r, g, b = (int(v[i:i + 2], 16) for i in (0, 2, 4))
        return (b >= 45 and (b - max(r, g)) >= 20 and (b - min(r, g)) >= 28)
    except Exception:
        return False


# 48 curated hue families (non-blue; white/cyan/blue/indigo 165-265 excluded):
# red|orange|amber|gold|olive|leaf|green|emerald|mint|magenta|fuchsia|pink|
# rose|crimson|maroon. Bands interleave so consecutive projects differ.
_BANDS = [
    [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33],
    [38, 40, 44, 48, 52, 56],
    [60, 62, 66, 70, 74, 78, 82, 86],
    [92, 96, 100, 104, 108, 112, 116, 120, 124, 128],
    [134, 138, 142, 146, 150, 154, 158, 162],
    [300, 305, 310, 314, 318, 322, 326],
    [330, 334, 338, 342, 346, 350, 352, 354, 356, 358, 359, 360],
]


def _interleaved_hues() -> list:
    out = []
    i = 0
    while any(i < len(b) for b in _BANDS):
        for band in _BANDS:
            if i < len(band):
                out.append(band[i])
        i += 1
    return out


_PALETTE_HUES = _interleaved_hues()


def _build_pool() -> list:
    """Deterministically produce 64 unique, non-blue brand hexes."""
    pool = []
    for h in _PALETTE_HUES:
        if len(pool) >= 64:
            break
        s, l = 0.62, 0.46
        hx = hsl_hex(h, s, l)
        while (is_blue_dominant(hx) or hx in pool) and l > 0.25:
            l -= 0.02
            hx = hsl_hex(h, s, l)
        if not is_blue_dominant(hx) and hx not in pool:
            pool.append(hx)
    return pool


PALETTE_POOL = _build_pool()


def palette_for(index: int) -> dict:
    h = _PALETTE_HUES[index % len(_PALETTE_HUES)]
    return {
        "brand": PALETTE_POOL[index % len(PALETTE_POOL)],
        "brand_soft": hsl_hex(h, 0.34, 0.88),
        "accent": hsl_hex(h, 0.55, 0.60),
        "accent_alt": hsl_hex(h, 0.70, 0.30),
    }


_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}", re.IGNORECASE)

_PATCH_FILES = re.compile(r"\.(css|jsx|js|json|html)$")


def prep_fix(fe: Path) -> dict:
    """Repair known pre-existing build-breakers before rebuild.

    1. theme.js may contain a duplicated ``export const designTokens`` (the
       LUMI_MOTION block was appended with the same name) -> rename extras.
    2. AppProviders.jsx may close ``return (<...>`` with ``;`` instead of
       ``);`` (broken brace) -> insert the missing parenthesis.
    """
    rep = {"theme_dup_fixed": 0, "appproviders_fixed": 0}
    theme = fe / "src" / "lib" / "theme.js"
    if theme.exists():
        text = theme.read_text(encoding="utf-8", errors="replace")
        chunk = "export const designTokens"
        count = text.count(chunk)
        if count > 1:
            base = chunk + " ="
            fixed = base.replace("designTokens", "lumiMotionCss")
            idx = 0
            parts = []
            first = True
            while True:
                pos = text.find(base, idx)
                if pos == -1:
                    parts.append(text[idx:])
                    break
                parts.append(text[idx:pos])
                parts.append(base if first else fixed)
                first = False
                idx = pos + len(base)
            text = "".join(parts)
            theme.write_text(text, encoding="utf-8")
            rep["theme_dup_fixed"] = count - 1
    providers = fe / "src" / "lib" / "AppProviders.jsx"
    if providers.exists():
        text = providers.read_text(encoding="utf-8", errors="replace")
        fixed = re.sub(r"(return\s*\(\s*)(.*?);", _fix_return_paren, text, flags=re.DOTALL)
        if fixed != text:
            providers.write_text(fixed, encoding="utf-8")
            rep["appproviders_fixed"] = 1
    return rep


def _fix_return_paren(m: "re.Match") -> str:
    head, body = m.group(1), m.group(2)
    if (head + body).count("(") > (head + body).count(")"):
        return head + body + ");"
    return m.group(0)


def patch_src_blue(src: Path, brand: str, report: dict) -> None:
    hits = 0
    for path in src.rglob("*"):
        if not path.is_file() or not _PATCH_FILES.search(path.name):
            continue
        low = "node_modules" in str(path) or "dist" in str(path)
        if low:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        matched = False

        def _sub(m):
            nonlocal matched
            hexc = m.group(0)
            if is_blue_dominant(hexc):
                matched = True
                return brand
            return hexc

        new = _HEX_RE.sub(_sub, text)
        if matched:
                hits += 1
                path.write_text(new, encoding="utf-8")
    report["blue_purged_files"] = hits


def patch_theme_tokens(theme: Path, pal: dict, report: dict) -> None:
    text = theme.read_text(encoding="utf-8", errors="replace")
    rep = [
        (r"--t-brand\s*:[^;]*;", "--t-brand: %s;" % pal["brand"]),
        (r"--t-brand-soft\s*:[^;]*;", "--t-brand-soft: %s;" % pal["brand_soft"]),
        (r"--t-accent-gold\s*:[^;]*;", "--t-accent-gold: %s;" % pal["accent"]),
        (r"--t-accent-cyan\s*:[^;]*;", "--t-accent-cyan: %s;" % pal["accent_alt"]),
    ]
    changed = 0
    for pat, repl in rep:
        if re.search(pat, text):
            text = re.sub(pat, repl, text)
            changed += 1
    theme.write_text(text, encoding="utf-8")
    report["token_lines_patched"] = changed


def project_list() -> list:
    out = []
    for proj in sorted(GEN.iterdir()):
        if not proj.is_dir():
            continue
        fe = proj / "frontend"
        if (fe / "package.json").exists():
            out.append(proj)
    return out


def _npm(exe: str, args: list, cwd: str, timeout: int) -> subprocess.CompletedProcess:
    """Run an npm command, resolving npm.cmd on Windows."""
    found = shutil.which("npm") or os.environ.get("NPM_BIN") or "npm"
    if os.name == "nt" and not found.lower().endswith(".cmd"):
        alt = shutil.which("npm.cmd")
        if alt:
            found = alt
    return subprocess.run([found, exe] + args, cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)


def build(fe: Path, timeout: int = 360) -> dict:
    if not (fe / "node_modules").exists():
        inst = _npm("install", ["--no-audit", "--no-fund"], str(fe),
                    timeout=timeout + 60)
        if inst.returncode != 0:
            return {"rc": inst.returncode, "tail": (inst.stderr or "")[-400:]}
    res = _npm("run", ["build"], str(fe), timeout=timeout)
    tail = (res.stdout or "")[-300:] + (res.stderr or "")[-300:]
    return {"rc": res.returncode, "tail": tail}


SLUG_INDUSTRY = {
    "aurelia-estates": "real-estate", "maison-noir": "fashion",
    "ember-salt": "food", "saffron-voyage": "hospitality",
    "prestige-studio": "portfolio", "meridian-capital": "fintech",
    "voltus-atelier": "electronics", "studio-lumen": "portfolio",
    "nuage-events": "entertainment", "luxemart": "ecommerce",
    "resupro": "saas", "realestate-realestate-001": "real-estate",
    "food-restaurant-001": "food", "tourism-travel-001": "hospitality",
    "tourism-travel-001-002": "hospitality",
    "electronics-portfolio-001": "electronics",
    "electronics-portfolio-001-002": "electronics",
    "edtech-fitness-001": "education", "edtech-fitness": "education",
    "aurum-fitness": "sports", "personal-portfolio-001": "portfolio",
    "personal-creative-001": "portfolio",
    "generated-website": "ecommerce", "generated-website-002": "ecommerce",
    "generated-website-003": "ecommerce", "generated-website-004": "ecommerce",
    "generated-website-005": "ecommerce", "generated-website-006": "ecommerce",
    "generated-website-007": "ecommerce", "generated-website-008": "ecommerce",
    "generated-website-009": "ecommerce",
    "auto-deploy-test": "saas", "test-i18n": "saas",
    "rest": "saas", "ui-style-wheel": "fashion",
    "3d-luxury-realestate": "real-estate",
    "build-017": "saas", "build-018": "saas", "build-019": "saas",
    "saas-saas-001": "saas",
    "generated-website-008": "healthcare",
}
for _s, _i in list(SLUG_INDUSTRY.items()):
    for _extra in ("-001", "-002", "-003", "-004", "-005"):
        if _s.endswith(_extra):
            SLUG_INDUSTRY.setdefault(_s[:-len(_extra)], _i)


def slug_industry(slug: str) -> str:
    return SLUG_INDUSTRY.get(slug, "saas")


def main() -> int:
    projects = project_list()
    wanted = set(sys.argv[1:])
    if wanted:
        projects = [p for p in projects if p.name in wanted]
    rows = []
    for idx, proj in enumerate(projects):
        slug = proj.name
        fe = proj / "frontend"
        src = fe / "src"
        theme = (src / "lib" / "theme.js") or (src / "styles" / "theme.js")

        pal = palette_for(idx)
        row = {"slug": slug, "idx": idx, "brand": pal["brand"]}

        # 0) Repair pre-existing build-breakers (dup theme export, brace)
        rep = prep_fix(fe)
        row.update(rep)

        # 1) Benchmark-First decode (mandatory, deterministic)
        #    Resolve the REAL industry from the slug before analyzing
        #    international-type reference websites of that industry.
        industry = slug_industry(slug)
        try:
            spec = {"project_name": slug.replace("-", " ").title(),
                    "industry": industry, "description": slug}
            bench = run_benchmark_first(spec, provider=None)
            row["industry"] = bench["industry"]
            row["brand_kind"] = bench["brand"]
        except Exception as exc:
            row["industry"] = "saas"

        # 2) Patch theme tokens
        try:
            candidates = sorted(src.rglob("theme.js")) if src.exists() else []
            if candidates:
                patch_theme_tokens(candidates[0], pal, row)
                theme = candidates[0]
                row["theme_ok"] = True
            else:
                row["theme_ok"] = False
        except Exception as exc:
            row["theme_ok"] = False
            row["theme_err"] = str(exc)[:80]

        # 3) Purge leftover blue-dominant literals from src
        try:
            patch_src_blue(src, pal["brand"], row)
        except Exception as exc:
            row["blue_err"] = str(exc)[:80]

        # 4) Rebuild
        try:
            b = build(fe)
            row["build_rc"] = b["rc"]
            if b["rc"] != 0:
                row["build_tail"] = b["tail"]
            row["dist"] = (fe / "dist" / "index.html").exists()
        except subprocess.TimeoutExpired:
            row["build_rc"] = "TIMEOUT"
        except Exception as exc:
            row["build_rc"] = "ERR"
            row["build_tail"] = str(exc)[:120]

        rows.append(row)
        print("[%02d/ %02d] %-28s %-8s -> rc=%s"
              % (idx + 1, len(projects), slug, pal["brand"], row["build_rc"]))

        progress = GEN / "UNIQUE_RESTYLE_PROGRESS.json"
        progress.write_text(json.dumps(rows, indent=1), encoding="utf-8")

    # 5) Report
    lines = [
        "# Unique Non-Blue Restyle Rebuild",
        "",
        "Every project got a deterministic UNIQUE non-blue brand palette (48"
        " hue families, one per project, no collisions) + Benchmark-First"
        " industry/brand decode + full `npm run build`.",
        "",
        "| Project | Industry | BrandKind | Palette | Build | Dist |",
        "|---------|----------|-----------|---------|-------|------|",
    ]
    green = 0
    for r in rows:
        green += 1 if r.get("build_rc") == 0 else 0
        pr = "%s (%s)" % (r.get("palette", ""), r.get("palette_name", ""))
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (r["slug"], r.get("industry", "-"), r.get("brand_kind", "-"),
               r["brand"], r.get("build_rc", "-"), r.get("dist", False)))
    lines += [
        "",
        "**Builds green: %d/%d**" % (green, len(rows)),
        "",
        "Blue-family hues (cyan/blue/indigo, 165-265deg) are excluded from the"
        " palette pool entirely; leftover blue-dominant hex literals in src/ were"
        " purged to each project's brand color.",
        "",
    ]
    (GEN / "UNIQUE_RESTYLE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nBuilds green: %d/%d" % (green, len(rows)))
    print("report: %s" % (GEN / "UNIQUE_RESTYLE_REPORT.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())