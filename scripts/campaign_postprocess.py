#!/usr/bin/env python
"""Post-process a finished campaign: generate seller kits + a campaign report."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-agent"))

OUT = ROOT / "generated-projects"


def main():
    state = OUT / "campaign-results.json"
    data = json.loads(state.read_text(encoding="utf-8"))
    projects = data.get("projects", {})
    report_lines = [
        "# LumicorePro Build Campaign Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Id | Project | Features (pass/total) | Seller Kit | Live | Quality |",
        "|----|---------|----------------------|------------|------|---------|",
    ]
    for pid, info in projects.items():
        if info.get("status") != "complete":
            continue
        pdir = OUT / info["project_name"]
        seller_kit = info.get("seller_kit")
        if not seller_kit:
            try:
                from agent.extensions.marketing_kit import generate_marketing_kit
                kit = generate_marketing_kit(str(pdir))
                seller_kit = (kit or {}).get("zip_path") or (kit or {}).get("path")
            except Exception as exc:  # noqa: BLE001
                seller_kit = f"ERR: {exc}"
        live = "yes (github-pages)" if (pdir / ".github").exists() else "n/a"
        report_lines.append(
            f"| {pid} | {info['project_name']} | {info.get('checks_passed')}/{info.get('checks_total')} "
            f"| {seller_kit or 'MISSING'} | {live} | {info.get('score') or 'n/a'} |"
        )
        info["seller_kit"] = seller_kit
    data["summary"] = {
        "total": len(projects),
        "ok": sum(1 for r in projects.values() if r.get("status") == "complete"),
    }
    state.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "CAMPAIGN_REPORT.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print("CAMPAIGN_REPORT.md written; summary:", data["summary"])


if __name__ == "__main__":
    main()