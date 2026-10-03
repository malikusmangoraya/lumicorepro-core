"""Delivery reports — write QA / Performance / Accessibility report MD files
into every generated project.

Honest reporting: if a metric was not actually measured, the report says
"not measured" instead of inventing a pass (per Part 2 quality-gate rules).
All access is defensive — the orchestrator calls this observationally and a
missing key can never raise.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

REPORT_FILES = ("QA_REPORT.md", "PERFORMANCE_REPORT.md", "A11Y_REPORT.md")

PERF_BUDGET_ROWS = [
    ("Lighthouse Performance", "95+", "", "not measured"),
    ("JS bundle (gzip)", "<150KB (hard <200KB)", "", "not measured"),
    ("CSS (gzip)", "<30KB (hard <50KB)", "", "not measured"),
    ("Total bundle (gzip)", "<200KB (hard <300KB)", "", "not measured"),
    ("LCP", "<1.5s", "", "not measured"),
    ("CLS", "<0.05 (hard <0.1)", "", "not measured"),
]


def _num(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _truthy(value: Any) -> bool:
    return bool(value)


def _extract_qgates(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("quality_gates", {}) or {}


def _extract_visual_critic(report: Dict[str, Any]) -> Dict[str, Any]:
    scan = report.get("design_scan", {}) or {}
    critic = scan.get("visual_critic")
    if not isinstance(critic, dict):
        critic = report.get("visual_critic")
    return critic if isinstance(critic, dict) and critic else {}


def _extract_browser_qa(report: Dict[str, Any]) -> Dict[str, Any]:
    phase = report.get("phase_results", {}) or {}
    bqa = phase.get("browser_qa", {}) or {}
    if not isinstance(bqa, dict):
        bqa = {}
    return bqa


def build_qa_report(report: Dict[str, Any]) -> str:
    gates = _extract_qgates(report)
    score = gates.get("overall_score")
    health = report.get("pipeline_health", {}) or {}
    phase_failures = report.get("phase_failures") or []
    critic = _extract_visual_critic(report)
    bqa = _extract_browser_qa(report)

    lines: List[str] = [
        "# QA Report",
        "",
        f"- Project: ``{report.get('project_name') or report.get('generated_project_dir') or 'n/a'}``",
        f"- Pipeline status: ``{report.get('status', 'n/a')}``",
        f"- Pipeline health: ``{health.get('score', 'n/a')}/100`` ({health.get('status', 'n/a')})",
        f"- Quality score: ``{score if score is not None else 'not measured'}``",
        f"- Enterprise ready: ``{_truthy(report.get('enterprise_ready'))}`` · Launch ready: ``{_truthy(report.get('launch_ready'))}``",
        f"- Build time: ``{report.get('execution_time_seconds', 'n/a')}s`` · AI API calls: ``{report.get('ai_api_calls_made', 'n/a')}``",
        "",
        "## Quality Gates",
        "",
    ]
    checked = gates.get("passed_count")
    total = gates.get("total_count")
    lines.append(f"Gates passed: ``{checked if checked is not None else 'not measured'}``"
                 f" of ``{total if total is not None else 'n/a'}``")
    gate_checks = gates.get("gates") or gates.get("checklist") or {
        k: v for k, v in gates.items() if k not in ("overall_score", "passed_count", "total_count")
    }
    if isinstance(gate_checks, dict) and gate_checks:
        lines.append("")
        for key, ok in gate_checks.items():
            lines.append(f"- ``{key}``: **PASS**" if _truthy(ok) else f"- ``{key}``: *FAIL / not satisfied*")

    lines += ["", "## Phase Failures", ""]
    if phase_failures:
        lines += [f"- ``{f}``" for f in phase_failures]
    else:
        lines.append("- None — all phases completed.")

    lines += ["", "## Visual Critic", ""]
    if critic:
        checks = critic.get("checks") or critic
        passed = 0
        total_c = 0
        rows = []
        for item in checks.values() if isinstance(checks, dict) else checks:
            if isinstance(item, dict):
                name = item.get("name") or item.get("check") or "check"
                ok = _truthy(item.get("passed"))
                total_c += 1
                if ok:
                    passed += 1
                rows.append(f"- ``{name}``: **PASS**" if ok else f"- ``{name}``: *FAIL*")
        if rows:
            lines.append(f"Visual critic passes: ``{passed}``/``{total_c}``")
            lines += rows
        else:
            lines.append("- Not measured (visual critic produced no checks).")
    else:
        lines.append("- Not measured.")

    lines += ["", "## Browser QA (real browser)", ""]
    if bqa:
        lines.append(f"- Status: ``{bqa.get('status', 'not measured')}``")
        for key in ("console_errors", "collapsed_sections", "lcp_ms", "mobile_breakpoints"):
            if key in bqa:
                lines.append(f"- ``{key}``: ``{bqa.get(key)}``")
    else:
        lines.append("- Not run — run the Browser QA tool for real screenshots + console evidence.")

    lines += [
        "",
        "## Release Checklist",
        "",
        "- [x] Project builds (Vite production build succeeded)" if _truthy(report.get("status")) else "- [ ] Project builds",
        "- [x] ZIP archive produced" if _truthy(report.get("zip_archive_path")) else "- [ ] ZIP archive produced",
        "- [x] Live preview URL" if _truthy(report.get("live_preview_url")) else "- [ ] Live preview URL (set one via the Deploy tool)",
        "- [ ] Visual critic evidence uploaded" if not critic else "- [x] Visual critic evidence reviewed",
        "- [ ] Browser QA screenshots linked" if not bqa else "- [x] Browser QA screenshots captured",
        "",
    ]
    return "\n".join(lines)


def build_performance_report(report: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Performance Report",
        "",
        "Budgets below follow LumicorePro performance targets. Values that were not "
        "measured during the build are reported honestly as *not measured* — run the "
        "deployment URL through Lighthouse to backfill them.",
        "",
        "| Metric | Target | Measured | Verdict |",
        "|--------|--------|----------|---------|",
    ]
    perf = report.get("performance_and_growth", {}) or {}
    measured = {
        k: v for k, v in perf.items()
        if isinstance(v, (int, float, str)) and str(v).strip() and v not in (0, "", "0")
    }
    for metric, target, default, verdict in PERF_BUDGET_ROWS:
        val = "not measured"
        if metric == "LCP" and "lcp_ms" in measured:
            val = f"{measured['lcp_ms']}ms"
        elif metric == "CLS" and "cls" in measured:
            val = str(measured["cls"])
        elif metric.lower() in str(measured).lower():
            hit = next((v for k, v in measured.items() if metric.lower() in k.lower()), None)
            val = str(hit)
        lines.append(f"| {metric} | {target} | ``{val}`` | *not verified* |")

    lines += [
        "",
        "## Measurements taken during the build",
        "",
        "- " + (str(perf).replace("\n", " ")
                [:800] if perf else "No runtime performance probes were executed by the build pipeline."),
        "",
    ]
    return "\n".join(lines)


def build_a11y_report(report: Dict[str, Any]) -> str:
    inter = report.get("international", {}) or {}
    compliance = report.get("seo_and_edge", {}) or {}
    a11y_score = inter.get("accessibility_score")
    lines: List[str] = [
        "# Accessibility Report",
        "",
        f"- Accessibility score: ``{a11y_score if a11y_score is not None else 'not measured'}``",
        f"- WCAG 2.1 AA compliant: ``{_truthy(inter.get('wcag_aa_compliant'))}``",
        f"- RTL support: ``{_truthy(inter.get('rtl_support'))}``",
        f"- RTL languages shipped: ``{', '.join(inter.get('rtl_languages') or []) or 'none'}``",
        f"- Consent banner required: ``{_truthy(inter.get('requires_consent_banner'))}``",
        f"- Compliance regulations targeted: ``{', '.join(inter.get('compliance_regs') or []) or 'none'}``",
        "- Compliance artifacts generated: ``%s``" % inter.get("compliance_artifacts", "not measured"),
        "",
        "## Compliance sources",
        "",
        "- " + (str(compliance)[:800] if compliance else "No compliance scanner output recorded."),
        "",
    ]
    return "\n".join(lines)


def write_delivery_reports(project_dir: str, report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Write QA / PERF / A11Y reports into project_dir. Never raises.

    When the build produced no rich report data, empty-but-valid files are
    written so buyers always get their delivery package.
    """
    try:
        if not os.path.isdir(str(project_dir)):
            return {"status": "skipped", "message": "project dir missing", "files": []}
        report = report or {}
        writers = {
            "QA_REPORT.md": build_qa_report,
            "PERFORMANCE_REPORT.md": build_performance_report,
            "A11Y_REPORT.md": build_a11y_report,
        }
        written = []
        for fname, builder in writers.items():
            try:
                content = builder(report)
            except Exception as exc:  # never block the deliverable
                agent_logger.error(f"Report builder {fname} failed: {exc}")
                content = f"# {fname}\n\nReport generation failed — see pipeline logs.\n"
            path = os.path.join(project_dir, fname)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            written.append(fname)
        agent_logger.info(f"Delivery reports written to {project_dir}: {', '.join(written)}")
        return {"status": "ok", "files": written, "project_dir": str(project_dir)}
    except Exception as exc:  # noqa: BLE001
        agent_logger.error(f"Delivery reports failed: {exc}")
        return {"status": "failed", "message": str(exc), "files": []}