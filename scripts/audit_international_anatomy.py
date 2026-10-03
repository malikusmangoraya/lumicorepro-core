"""International anatomy audit — v7.10.

Read-only scanner. For every project (43) and every page in src/pages/ it
inventories how each section is BUILT and whether it meets the 2026
international landing-page anatomy, then writes a per-project + aggregate
report so the rebuild plan is evidence-based.

Outputs:
  generated-projects/INTERNATIONAL_ANATOMY_RAW.json
  generated-projects/INTERNATIONAL_ANATOMY_AUDIT.md
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

# ---- 2026 international anatomy markers (per page we accept any subset) ----
ANATOMY_RULES = {
    "hero":      { "names": ["hero", "section-hero"], "why": "One-second outcome headline + single primary CTA + trust signal" },
    "proof":     { "names": ["trust"], "why": "Logo strip or stats immediately below hero" },
    "features":  { "names": ["feature"], "why": "Benefit-first feature breakdown" },
    "stats":     { "names": ["stat"], "why": "Metric band" },
    "problem":   { "names": ["problem", "reframe"], "why": "Problem reframe (naming friction) " },
    "personas":  { "names": ["persona", "use-case", "use case", "who it", "ideal for"], "why": "Use-case / persona grid" },
    "pricing":   { "names": ["pricing", "plan", "tier"], "why": "Price honesty: visible tiers" },
    "comparison":{" names": ["comparison", "vs ", "side-by-side", "table"], "why": "Comparison table (optional)" },
    "testimonial":{ "names": ["testimonial", "review", "quote"], "why": "Social proof" },
    "faq":       { "names": ["faq", "accordion", "question"], "why": "Objection handling" },
    "cta":       { "names": ["cta", "get started", "book", "reserve", "shop", "start", "cta-band"], "why": "Final CTA, copy distinct from hero" },
    "newsletter":{ "names": ["subscribe", "newsletter", "stay updated"], "why": "Email capture" },
}
ANATOMY_RULES["comparison"]["names"] = ["comparison", "vs ", "side-by-side", "side by side", "difference, side by side"]
del ANATOMY_RULES["comparison"][" names"]  # typo guard

# generic / placeholder / anti-international content markers
BAD_MARKERS = {
    "lorem":  ["lorem", "ipsum"],
    "todo":   ["todo", "coming soon", "under construction", "placeholder", "tbd "],
    "generic_saas": ["fullstack engineering", "cloud infrastructure", "/lock", "maximize roi",
                     "streamline workflow", "boost productivity", "unlock the power", "seamless experience"],
    "generic_contact": ["get in touch", "let's get connected", "nice to meet you", "send us a message"],
    "hardcoded_gold":  ["#b8860b", "#8b4513", "#daa520"],
    "blue":    ["#2563eb", "#1e40af", "#3b82f6", "#0ea5e9", "bg-blue-", "text-blue-", "bg-sky-", "text-sky-", "bg-indigo-"],
}

SECTIONS_RE = re.compile(r"<section\b[^>]*>")
H_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.S)
MARKER_RE = re.compile(r'"(round|card|button|section|hero|grid|list|badge|pill|band)\([a-z-]+\)"', re.I)
CLASS_RE = re.compile(r'(?:class|className)="([^"]+)"')


def clean_txt(s: str) -> str:
    t = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", t).strip()


def page_scan(page: Path) -> dict:
    t = page.read_text(encoding="utf-8", errors="replace")
    low = t.lower()
    info = {
        "file": page.name,
        "lines": t.count("\n") + 1,
        "sections": len(SECTIONS_RE.findall(t)),
        "divs": t.count("<div"),
        "headings": [],
        "anatomy": {},
        "bad": {},
        "classes": {},
        "hardcoded_hexes": [],
    }
    for m in H_RE.finditer(t):
        info["headings"].append((int(m.group(1)), clean_txt(m.groups()[1])[:70]))
    for key, rule in ANATOMY_RULES.items():
        info["anatomy"][key] = any(n in low for n in rule["names"])
    for cls, markers in BAD_MARKERS.items():
        info["bad"][cls] = sum(low.count(m) for m in markers)
    for sel, pat in [("data-reveal", r"data-reveal"), ("card-lift", r"\bcard-lift\b"),
                     ("card-panel", r"\bcard-panel\b"), ("glass-md", r"\bglass-md\b"),
                     ("hero-aurora", r"\bhero-aurora\b"), ("section-eyebrow", r"\bsection-eyebrow\b"),
                     ("btn-primary", r"\bbtn-primary\b"), ("btn-outline", r"\bbtn-outline\b"),
                     ("fluid-container", r"\bfluid-container\b")]:
        info["classes"][sel] = len(re.findall(pat, t))
    info["hardcoded_hexes"] = list(dict.fromkeys(re.findall(r"#[0-9a-fA-F]{6}\b", t)))
    return info


def scan_project(slug: str) -> dict:
    pages_dir = PROJECTS / slug / "frontend" / "src" / "pages"
    pages = sorted(pages_dir.glob("*.jsx")) if pages_dir.exists() else []
    out = {"slug": slug, "pages": {}}
    for p in pages:
        out["pages"][p.stem] = page_scan(p)
    return out


def main():
    slugs = sys.argv[1:] or [
        d.name
        for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    raw = [scan_project(s) for s in slugs]
    (PROJECTS / "INTERNATIONAL_ANATOMY_RAW.json").write_text(
        json.dumps(raw, indent=1), encoding="utf-8")

    # ----- aggregate the markdown report -----
    lines = []
    lines.append("# International Anatomy Audit — v7.10 (read-only)")
    lines.append("")
    lines.append("How every project/page/section is BUILT, gated against the 2026 anatomy.")
    lines.append("")
    lines.append(f"Projects scanned: **{len(raw)}**")
    lines.append("")

    # anatomy legend rows
    order = ["hero", "proof", "features", "stats", "problem", "personas",
             "pricing", "comparison", "testimonial", "faq", "cta", "newsletter"]

    # summary table by project
    lines.append("## 1. Coverage matrix (anatomy sections present anywhere in project)")
    hdr = "| Project | " + " | ".join(a[:4].capitalize() if a != "newsletter" else "News" for a in order) + " | pages |"
    lines.append("|" + "_" * (hdr.count("|") - 1) + "|")
    lines.append(hdr)
    lines.append("|" + "|---|---|" * (len(order) + 1) + "|")
    for proj in raw:
        all_anat = {}
        for p in proj["pages"].values():
            for k in order:
                all_anat[k] = all_anat.get(k, False) or p["anatomy"][k]
        row = ["x" if all_anat.get(k) else "-" for k in order]
        lines.append(f"| {proj['slug']} | {' | '.join(row)} | {len(proj['pages'])} |")
    lines.append("")

    # aggregate bad markers
    lines.append("## 2. Anti-international content markers (totals across all projects)")
    agg = {c: 0 for c in BAD_MARKERS}
    agg_files = {c: 0 for c in BAD_MARKERS}
    for proj in raw:
        for p in proj["pages"].values():
            for c, n in p["bad"].items():
                if n:
                    agg[c] += n
                    agg_files[c] += 1
    for c in BAD_MARKERS:
        lines.append(f"- **{c}**: {agg[c]} hits across {agg_files[c]} page files")
    lines.append("")

    # hardcoded hex audit
    lines.append("## 3. Hardcoded hex colours still in page files")
    hex_counts = {}
    hex_files = {}
    for proj in raw:
        for p in proj["pages"].values():
            for hx in p["hardcoded_hexes"]:
                hex_counts[hx] = hex_counts.get(hx, 0) + 1
                hex_files.setdefault(hx, set()).add(f"{proj['slug']}/{p['file']}")
    for hx, n in sorted(hex_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{hx}` x{n}  — e.g. {snippet(list(hex_files[hx])[:3])}")
    lines.append("")

    # per-project per-page inventory + anatomy matrix
    lines.append("## 4. Per-project page inventory")
    for proj in raw:
        lines.append("")
        lines.append(f"### {proj['slug']} — {len(proj['pages'])} pages")
        lines.append("")
        lines.append("| Page | lines | <section> | h1/h2/h3 sample | anatomy missing |")
        lines.append("|---|---|---|---|---|")
        for name, p in proj["pages"].items():
            missing = ", ".join(k for k in order if not p["anatomy"][k]) or "none"
            heads = " / ".join(f"h{h}:{txt[:46]}" for h, txt in p["headings"][:3])
            lines.append(f"| {name} | {p['lines']} | {p['sections']} | {heads} | {missing} |")
        lines.append("")

    (PROJECTS / "INTERNATIONAL_ANATOMY_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"raw json + audit written: {PROJECTS / 'INTERNATIONAL_ANATOMY_AUDIT.md'}")


def snippet(items):
    return ", ".join(items) if len(items) <= 4 else ", ".join(items[:4]) + f" (+{len(items)-4} more)"


if __name__ == "__main__":
    main()