"""Assign UNIQUE non-blue palettes to the 10 AI-agent products and rebuild.

Deterministic and subset-independent for the fixed 10-agent set:
  - candidate hexes built from hue families + lightness sweep (never blue)
  - the 59 already-delivered brand hexes (UNIQUE_RESTYLE_PROGRESS.json) are EXCLUDED
    so the frozen 59 stay byte-stable and unrepeatable
  - agents are processed in sorted-slug order, each taking the next unused candidate

Patches theme tokens (--t-brand*, --t-accent-*) like restyle_unique_all, purges
blue-dominant hex literals from src, then npm run build. Logo scripts read the
patched tokens, so running this first keeps every artifact on-brand.
"""
import colorsys
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
import restyle_unique_all as R  # noqa: E402 (reuse hsl_hex/is_blue_dominant/patch fns)

AGENTS = [
    "appointly-ai", "claimflow-ai", "clausecheck-ai", "insightpipe-ai",
    "leadscout-ai", "ledgerai", "onboarder-ai", "recruitiq-ai",
    "supportdesk-ai", "tablehost-ai",
]

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}", re.IGNORECASE)
PATCH_FILES = re.compile(r"\.(css|jsx|js|json|html)$")


def build_candidates() -> list:
    """Deterministic non-blue candidate hexes (ordered, no dups)."""
    pool = list(R.PALETTE_POOL)
    for l in (0.30, 0.54, 0.40, 0.50):
        for h in R._PALETTE_HUES:
            hx = R.hsl_hex(h, 0.62, l)
            if hx not in pool and not R.is_blue_dominant(hx):
                pool.append(hx)
    for h in R._PALETTE_HUES:
        for s in (0.55, 0.65):
            for l in (0.48, 0.44):
                hx = R.hsl_hex(h, s, l)
                if hx not in pool and not R.is_blue_dominant(hx):
                    pool.append(hx)
    return pool


def used_colors() -> set:
    fp = GEN / "UNIQUE_RESTYLE_PROGRESS.json"
    out = set()
    if fp.exists():
        try:
            rows = json.loads(fp.read_text(encoding="utf-8"))
            for r in rows:
                if isinstance(r, dict) and r.get("brand"):
                    out.add(str(r["brand"]).lower())
        except Exception:
            pass
    return out


def agent_palettes() -> dict:
    cands = [c for c in build_candidates() if c.lower() not in used_colors()]
    cands = [c for c in cands if not R.is_blue_dominant(c)]
    out = {}
    for slug in sorted(AGENTS):
        if not cands:
            raise RuntimeError("insufficient unique candidate colors")
        hexc = cands.pop(0)
        # recover hue for soft/accent/alt from the hex
        r, g, b = (int(hexc[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        h, _s, l = colorsys.rgb_to_hls(r, g, b)
        hd = h * 360.0
        out[slug] = {
            "brand": hexc,
            "brand_soft": R.hsl_hex(hd, 0.34, 0.88),
            "accent": R.hsl_hex(hd, 0.55, 0.60),
            "accent_alt": R.hsl_hex(hd, 0.70, 0.30),
        }
    return out


def patch_src_blue(src, brand) -> int:
    hits = 0
    for path in src.rglob("*"):
        if not path.is_file() or not PATCH_FILES.search(path.name):
            continue
        if "node_modules" in str(path) or "dist" in str(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        matched = [False]

        def _sub(m):
            hexc = m.group(0)
            if R.is_blue_dominant(hexc):
                matched[0] = True
                return brand
            return hexc

        new = HEX_RE.sub(_sub, text)
        if matched[0]:
            hits += 1
            path.write_text(new, encoding="utf-8")
    return hits


def npm(exe, args, cwd, timeout):
    found = "npm.cmd" if sys.platform.startswith("win") else "npm"
    return subprocess.run([found, exe] + args, cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)


def main() -> int:
    pals = agent_palettes()
    rows = []
    for slug in AGENTS:
        fe = GEN / slug / "frontend"
        src = fe / "src"
        pal = pals[slug]
        rep = R.prep_fix(fe)
        try:
            cands = sorted(src.rglob("theme.js")) if src.exists() else []
            if cands:
                R.patch_theme_tokens(cands[0], pal, rep)
            else:
                rep["theme_ok"] = False
        except Exception as exc:
            rep["theme_err"] = str(exc)[:80]
        try:
            rep["blue_purged_files"] = patch_src_blue(src, pal["brand"])
        except Exception as exc:
            rep["blue_err"] = str(exc)[:80]
        if not (fe / "node_modules").exists():
            inst = npm("install", ["--no-audit", "--no-fund"], str(fe), 420)
            if inst.returncode != 0:
                rep["build_rc"] = inst.returncode
                rep["build_tail"] = (inst.stderr or "")[-400:]
                rows.append({"slug": slug, "brand": pal["brand"], **rep,
                             "dist": (fe / "dist" / "index.html").exists()})
                continue
        res = npm("run", ["build"], str(fe), 360)
        rep["build_rc"] = res.returncode
        if res.returncode != 0:
            rep["build_tail"] = (res.stdout or "")[-300:] + (res.stderr or "")[-300:]
        rep["dist"] = (fe / "dist" / "index.html").exists()
        rows.append({"slug": slug, "brand": pal["brand"], **rep})
        print("[%02d] %-18s %s rc=%s dist=%s" % (
            len(rows), slug, pal["brand"], rep["build_rc"], rep["dist"]))
        (GEN / "AGENT_UNIQUE_PROGRESS.json").write_text(
            json.dumps(rows, indent=1), encoding="utf-8")
    gp = sum(1 for r in rows if r.get("build_rc") == 0)
    (GEN / "AGENT_UNIQUE_REPORT.md").write_text(
        "\n".join([
            "# AI-Agent Unique Restyle Rebuild", "",
            "New unique non-blue palettes for the 10 agent products. The 59",
            "delivered brands are excluded (their colors/file bytes stay frozen).", "",
            "| Project | Palette | Build | Dist |",
            "|---------|---------|-------|------|",
        ] + [
            "| %s | %s | %s | %s |" % (r["slug"], r["brand"], r.get("build_rc"),
                                       r.get("dist"))
            for r in rows
        ] + ["", "**Builds green: %d/%d**" % (gp, len(rows)), ""]),
        encoding="utf-8")
    print("\nBuilds green: %d/10  report: %s" % (gp, GEN / "AGENT_UNIQUE_REPORT.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())