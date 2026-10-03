"""Scorecard: JSON + Markdown reporting with no invented metrics.

Anything the harness could not measure is emitted as `not_measured` with a
reason, so a report can never look better than the evidence supports.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .runner import TaskRun

RESOLVED = "resolved"
STATUS_NOT_MEASURED = "not_measured"


def _pct(numerator: int, denominator: int) -> Optional[float]:
    return round(numerator / denominator * 100, 2) if denominator else None


def build_report(
    runs: List[TaskRun],
    dataset_stats: Optional[Dict[str, Any]] = None,
    solver: str = "unknown",
    command: str = "",
) -> Dict[str, Any]:
    total = len(runs)
    resolved = [r for r in runs if r.resolved]
    errored = [r for r in runs if r.status.startswith("error")]
    measured = [r for r in runs if r.status in (RESOLVED, "unresolved")]

    by_repo: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        bucket = by_repo.setdefault(
            run.repo, {"total": 0, "resolved": 0, "errors": 0, "statuses": {}}
        )
        bucket["total"] += 1
        if run.resolved:
            bucket["resolved"] += 1
        if run.status.startswith("error"):
            bucket["errors"] += 1
        bucket["statuses"][run.status] = bucket["statuses"].get(run.status, 0) + 1
    for bucket in by_repo.values():
        bucket["resolve_rate"] = _pct(bucket["resolved"], bucket["total"])

    error_reasons: Dict[str, int] = {}
    for run in errored:
        key = run.status.split(":", 1)[-1] if ":" in run.status else run.status
        error_reasons[key] = error_reasons.get(key, 0) + 1

    leakage = [r for r in runs if r.leakage]
    leaked_fraction = len(leakage) / total if total else None

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "command": command,
        "solver": solver,
        "totals": {
            "tasks": total,
            "resolved": len(resolved),
            "unresolved": len([r for r in measured if not r.resolved]),
            "errors": len(errored),
            "measured": len(measured),
            "resolve_rate": _pct(len(resolved), total),
            "resolve_rate_of_measured": _pct(len(resolved), len(measured)),
            "unmeasured": total - len(measured),
            "error_reasons": error_reasons,
            "total_seconds": round(sum(r.seconds for r in runs), 1),
            "avg_seconds": round(sum(r.seconds for r in runs) / total, 2) if total else None,
        },
        "integrity": {
            "tasks_with_reference_leakage": len(leakage),
            "leakage_free": not leakage,
            "patch_bytes_total": sum(r.patch_bytes for r in runs),
        },
        "by_repo": by_repo,
        "dataset": dataset_stats or {},
        "runs": [r.to_dict() for r in runs],
    }


def _fmt_pct(value: Optional[float]) -> str:
    return f"{value:.2f}%" if value is not None else STATUS_NOT_MEASURED


def render_markdown(report: Dict[str, Any], top: int = 30) -> str:
    totals = report["totals"]
    lines = [
        "# Public-Development Benchmark Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Solver: `{report['solver']}`",
        f"- Command: `{report['command'] or 'n/a'}`",
        "",
        "## Headline",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Tasks attempted | {totals['tasks']} |",
        f"| Resolved | {totals['resolved']} |",
        f"| Unresolved (measured) | {totals['unresolved']} |",
        f"| Harness errors | {totals['errors']} |",
        f"| Unmeasured | {totals['unmeasured']} |",
        f"| Resolve rate (all tasks) | {_fmt_pct(totals['resolve_rate'])} |",
        f"| Resolve rate (measured only) | {_fmt_pct(totals['resolve_rate_of_measured'])} |",
        f"| Avg seconds / task | {totals['avg_seconds'] if totals['avg_seconds'] is not None else STATUS_NOT_MEASURED} |",
        "",
        "## Integrity",
        "",
        f"- Reference-solution leakage: {'NONE (clean)' if report['integrity']['leakage_free'] else 'DETECTED'}",
        f"- Total candidate patch bytes: {report['integrity']['patch_bytes_total']}",
        "",
    ]
    if totals["error_reasons"]:
        lines += ["## Harness errors", "", "| Reason | Count |", "| --- | --- |"]
        lines += [f"| {reason} | {count} |" for reason, count in sorted(totals["error_reasons"].items())]
        lines.append("")

    if report["by_repo"]:
        lines += ["## Per repository", "", "| Repo | Resolved | Total | Resolve rate | Errors |", "| --- | --- | --- | --- | --- |"]
        for repo, bucket in sorted(report["by_repo"].items(), key=lambda kv: -(kv[1]["resolve_rate"] or -1)):
            lines.append(
                f"| {repo} | {bucket['resolved']} | {bucket['total']} | {_fmt_pct(bucket['resolve_rate'])} | {bucket['errors']} |"
            )
        lines.append("")

    lines += ["## Task detail", "", "| Task | Repo | Status | Resolved | Detail |", "| --- | --- | --- | --- | --- |"]
    for run in report["runs"][:top]:
        detail = (run["detail"] or "").replace("|", "\\|")[:90]
        lines.append(f"| {run['task_id']} | {run['repo']} | {run['status']} | {'yes' if run['resolved'] else 'no'} | {detail} |")
    if len(report["runs"]) > top:
        lines.append(f"| ... | ... | {len(report['runs']) - top} more in the JSON report | | |")
    lines.append("")
    return "\n".join(lines)


def write_report(report: Dict[str, Any], out_dir: Path, basename: str = "benchmark-report") -> Dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{basename}.json"
    md_path = out_dir / f"{basename}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def load_report(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarise(report: Dict[str, Any]) -> str:
    totals = report.get("totals", {})
    return (
        f"{totals.get('resolved', 0)}/{totals.get('tasks', 0)} resolved "
        f"({_fmt_pct(totals.get('resolve_rate'))}), "
        f"{totals.get('errors', 0)} harness error(s), "
        f"{totals.get('unmeasured', 0)} unmeasured"
    )
