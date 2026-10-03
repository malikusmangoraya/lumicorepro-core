"""Benchmark-First re-audit across all generated projects (deterministic).

For every real project under generated-projects/ (one that ships a frontend),
derive a spec from its name + directory, run the mandatory Benchmark-First
decode, and record: industry/brand detection, playbook load, international
peer set, and the resulting design decision (hero/motion/cta/3d).

This is a fast, offline, deterministic pass (no npm builds). Writes
generated-projects/BENCHMARK_FIRST_AUDIT.md.
"""
import json
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "ai-agent"))

from agent.intelligence.benchmark_first import run_benchmark_first  # noqa: E402
from agent.intelligence.design_decision_engine import decide_design  # noqa: E402

# Explicit industry hints for known campaign slugs (deterministic mapping).
INDUSTRY_HINTS = {
    "aurelia-estates": "real estate luxury property",
    "maison-noir": "fashion luxury boutique",
    "ember-salt": "food restaurant fine dining",
    "saffron-voyage": "hospitality tourism travel",
    "prestige-studio": "portfolio creative agency",
    "meridian-capital": "fintech investment banking",
    "voltus-atelier": "electronics premium devices",
    "aurum-fitness": "sports fitness gym",
    "studio-lumen": "portfolio design studio",
    "nuage-events": "entertainment events",
    "luxemart": "ecommerce luxury store",
    "resupro": "saas resume builder",
    "food-restaurant-001": "food restaurant",
    "tourism-travel-001": "hospitality tourism travel",
    "electronics-portfolio-001": "electronics portfolio",
    "edtech-fitness-001": "education fitness",
    "realestate-realestate-001": "real estate property",
}


def _spec_for(proj: Path) -> dict:
    slug = proj.name
    industry = INDUSTRY_HINTS.get(slug)
    if not industry:
        # heuristic from slug tokens
        if re.search(r"shop|store|mart|commerce", slug):
            industry = "ecommerce"
        elif re.search(r"estate|realty|property", slug):
            industry = "real-estate"
        elif re.search(r"food|restaurant|cafe", slug):
            industry = "food"
        elif re.search(r"travel|tourism|hotel", slug):
            industry = "hospitality"
        elif re.search(r"fintech|pay|bank|capital", slug):
            industry = "fintech"
        elif re.search(r"health|clinic|care", slug):
            industry = "healthcare"
        elif re.search(r"fitness|sport|gym", slug):
            industry = "sports"
        elif re.search(r"portfolio|studio|creative", slug):
            industry = "portfolio"
        elif re.search(r"saas|app|平台|platform|dashboard", slug):
            industry = "saas"
        else:
            industry = "saas"
    return {
        "project_name": slug.replace("-", " ").title(),
        "industry": industry,
        "description": f"{slug.replace('-', ' ')} generated website",
    }


def _has_frontend(proj: Path) -> bool:
    return (proj / "frontend" / "package.json").exists() or \
           (proj / "src" / "App.jsx").exists()


def _build_state(proj: Path) -> str:
    fe = proj / "frontend"
    dist = (fe / "dist" / "index.html")
    if dist.exists():
        return "dist"
    if fe.exists():
        return "no-dist"
    return "no-frontend"


def main() -> int:
    if not GEN.exists():
        print("no generated-projects dir")
        return 1

    rows = []
    for proj in sorted(p for p in GEN.iterdir() if p.is_dir()):
        if not _has_frontend(proj):
            continue
        try:
            spec = _spec_for(proj)
            report = run_benchmark_first(spec, provider=None)
            decision = decide_design(
                spec,
                reference_analysis=report["reference_spec"]["reference_intelligence"],
            )
            rows.append({
                "slug": proj.name,
                "industry": report["industry"],
                "brand": report["brand"],
                "playbook": report["playbook_loaded"],
                "peers": len(report["benchmark_peers"]),
                "hero": decision.get("hero"),
                "motion": decision.get("motion"),
                "cta": decision.get("cta_style"),
                "3d": decision.get("3d"),
                "source": report["source"],
                "build": _build_state(proj),
            })
        except Exception as exc:
            rows.append({"slug": proj.name, "error": str(exc)[:120]})

    lines = [
        "# Benchmark-First Re-Audit",
        "",
        f"Projects audited: {len(rows)}  |  Deterministic decode (no builds this pass)",
        "",
        "| Project | Industry | Brand | Playbook | Peers | Hero | Motion | CTA | 3D | Source | Build |",
        "|---------|----------|-------|----------|-------|------|--------|-----|----|--------|-------|",
    ]
    ok = 0
    for r in rows:
        if r.get("error"):
            lines.append(f"| {r['slug']} | ERROR | - | - | - | - | - | - | - | - | - |")
            continue
        ok += 1 if r["playbook"] and r["peers"] else 0
        lines.append(
            f"| {r['slug']} | {r['industry']} | {r['brand']} | "
            f"{'YES' if r['playbook'] else 'NO'} | {r['peers']} | {r['hero']} | "
            f"{r['motion']} | {r['cta']} | {r['3d']} | {r['source']} | {r['build']} |"
        )
    lines += [
        "",
        f"Benchmark-First populated (playbook + peers): {ok}/{len(rows)}",
        "",
        "> Full per-project `npm run build` verification is scheduled for the next",
        "> session; this pass verifies the mandatory deterministic design decode.",
        "",
    ]
    out = GEN / "BENCHMARK_FIRST_AUDIT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:6]))
    print(f"...\nBenchmark-First populated: {ok}/{len(rows)}")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
