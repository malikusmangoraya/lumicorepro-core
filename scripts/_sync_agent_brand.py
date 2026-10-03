"""Set the real unique palette into each agent's index.css lumi-shell block.

The scaffold used the #e0a33a default because agents' theme.js had no tokens.
This rewrites the block's --t-brand/brand-soft/accent-gold/accent-cyan to the
assigned AGENT_UNIQUE_PROGRESS palette (derived soft/accent from the brand hex).
"""
import colorsys
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
import restyle_unique_all as R  # noqa: E402

AGENTS = ["appointly-ai", "claimflow-ai", "clausecheck-ai", "insightpipe-ai",
          "leadscout-ai", "ledgerai", "onboarder-ai", "recruitiq-ai",
          "supportdesk-ai", "tablehost-ai"]


def palette_for_brand(hexc: str) -> dict:
    def _hex_rgb(hx):
        v = hx.lstrip("#")
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (x / 255.0 for x in _hex_rgb(hexc))
    h, _s, l = colorsys.rgb_to_hls(r, g, b)
    hd = h * 360.0
    return {
        "brand": hexc,
        "brand_soft": R.hsl_hex(hd, 0.34, 0.88),
        "accent": R.hsl_hex(hd, 0.55, 0.60),
        "accent_alt": R.hsl_hex(hd, 0.70, 0.30),
    }


def main() -> int:
    prog = {r["slug"]: r["brand"] for r in
            json.loads((GEN / "AGENT_UNIQUE_PROGRESS.json").read_text(encoding="utf-8"))}
    for slug in AGENTS:
        fe = GEN / slug / "frontend"
        cssp = fe / "src" / "index.css"
        t = cssp.read_text(encoding="utf-8", errors="ignore")
        pa = palette_for_brand(prog[slug])
        new = re.sub(r"--t-brand-soft\s*:\s*#[0-9a-fA-F]{6};",
                     "--t-brand-soft: %s;" % pa["brand_soft"], t)
        new = re.sub(r"--t-brand\s*:\s*#[0-9a-fA-F]{6};",
                     "--t-brand: %s;" % pa["brand"], new)
        new = re.sub(r"--t-accent-gold\s*:\s*#[0-9a-fA-F]{6};",
                     "--t-accent-gold: %s;" % pa["accent"], new)
        new = re.sub(r"--t-accent-cyan\s*:\s*#[0-9a-fA-F]{6};",
                     "--t-accent-cyan: %s;" % pa["accent_alt"], new)
        if new != t:
            cssp.write_text(new, encoding="utf-8")
            ok = "yes"
        else:
            # block may not exist -> append it
            blk = ("\n/* ===== lumi-shell-agent (7.13) ===== */\n:root {\n"
                   "  --t-brand: %s;\n  --t-brand-soft: %s;\n"
                   "  --t-accent-gold: %s;\n  --t-accent-cyan: %s;\n}\n"
                   % (pa["brand"], pa["brand_soft"], pa["accent"], pa["accent_alt"]))
            cssp.write_text(t.rstrip() + "\n" + blk, encoding="utf-8")
            ok = "appended"
        print("%-18s %s (%s)" % (slug, prog[slug], ok))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())