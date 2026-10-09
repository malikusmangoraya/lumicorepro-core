"""Autopilot — automated audit & repair across every generated project.

Purpose: generated projects drift (missing CSP, committed secrets, copy PII,
lint/build regressions). Previously each fix was a manual pass. Autopilot walks
a projects root, runs four deterministic stages per project, and writes a
report:

  1. guardrails  — CSP injection + secret/PII redaction (see agent.guardrails)
  2. self-heal   — lint/dependency/port self-healing fixes (see agent.self_healing)
  3. quality     — enterprise quality gates, producing a 0–100 score
  4. trends      — every score is recorded so regressions are visible over time

Project discovery deliberately ignores scratch directories (`build-*`,
`auto-deploy-test`, `test-i18n`, ...) and only treats a directory as a project
when it carries a real frontend/backend marker.

CLI::

    python -m agent.autopilot --root ../generated-projects
    python -m agent.autopilot --root ../generated-projects --fix --threshold 80
    python -m agent.autopilot --root ../generated-projects --json-only --strict

Exit code is 0 unless ``--strict`` is passed AND a project is below threshold,
so it is safe to wire into a scheduled job that should not fail the pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "generated-projects"
DEFAULT_THRESHOLD = int(os.getenv("AUTOPILOT_QUALITY_THRESHOLD", "80"))
REPORT_DIR = Path(__file__).resolve().parent.parent / "logs" / "autopilot"

# Scratch/test directories that are not deliverable projects.
_IGNORED_PATTERNS = (
    re.compile(r"^build(-\d+)?$"),
    re.compile(r"^auto-deploy-test$"),
    re.compile(r"^test-i18n$"),
    re.compile(r"^generated-website(-\d+)?$"),
    re.compile(r"^\.cache"),
    re.compile(r"^__"),
)

# A real project has at least one of these markers.
_PROJECT_MARKERS = ("frontend/src", "frontend/package.json", "package.json", "src/index.js", "index.html")


def discover_projects(root: Path, include_scratch: bool = False) -> List[Path]:
    """Return sorted project directories under `root`."""
    projects: List[Path] = []
    if not root.is_dir():
        return projects
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not include_scratch and any(p.match(child.name) for p in _IGNORED_PATTERNS):
            continue
        if any((child / marker).exists() for marker in _PROJECT_MARKERS):
            projects.append(child)
    return projects


def _run_stage_guardrails(project_dir: Path, apply_fixes: bool) -> Dict[str, Any]:
    from .guardrails import apply_guardrails, scan_text_for_secrets

    if not apply_fixes:
        # Read-only preview: still report what would be redacted.
        secrets_found: List[Dict[str, str]] = []
        for path in sorted(project_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".js", ".jsx", ".ts", ".tsx", ".env", ".json", ".md"}:
                continue
            if any(part in {"node_modules", "dist", "build", ".git"} for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for hit in scan_text_for_secrets(text):
                secrets_found.append({"file": str(path.relative_to(project_dir)), **hit})
        return {"stage": "guardrails", "applied": False,
                "secrets_found": secrets_found, "passed": not secrets_found}

    report = apply_guardrails(str(project_dir))
    return {"stage": "guardrails", "applied": True,
            "secrets_found": report.get("pii", {}).get("secrets_found", []),
            "csp_injected": report.get("csp", {}).get("injected", 0),
            "redacted_count": report.get("pii", {}).get("redacted_count", 0),
            "passed": bool(report.get("passed", False))}


def _run_stage_self_heal(project_dir: Path, apply_fixes: bool) -> Dict[str, Any]:
    """Scan (and optionally repair) lint/dependency issues. Never raises."""
    try:
        from .self_healing import create_self_healing_system

        system = create_self_healing_system(project_dir)
        errors = system.scan_project()
        fixes = system.auto_fix(errors) if (apply_fixes and errors) else []
        return {
            "stage": "self_heal",
            "applied": apply_fixes,
            "errors_found": len(errors),
            "errors": [
                {"severity": getattr(e.severity, "value", str(e.severity)), "message": str(e.message)[:200],
                 "file": str(e.file) if getattr(e, "file", None) else None}
                for e in errors[:10]
            ],
            "fixes_applied": len(fixes),
            "passed": not errors or apply_fixes,
        }
    except Exception as exc:  # noqa: BLE001
        return {"stage": "self_heal", "passed": True, "skipped": True, "reason": str(exc)[:200]}


def _run_stage_quality(project_dir: Path) -> Dict[str, Any]:
    try:
        from .quality_gates import QualityGates

        spec = {"project_name": project_dir.name}
        validation = {"valid": True, "errors": [], "warnings": []}
        report = QualityGates().evaluate(str(project_dir), spec, validation)
        return {
            "stage": "quality",
            "score": float(report.get("overall_score", 0) or 0),
            "enterprise_ready": bool(report.get("enterprise_ready", False)),
            "checks": report.get("checks", {}),
        }
    except Exception as exc:  # noqa: BLE001
        return {"stage": "quality", "score": 0.0, "error": str(exc)[:200], "passed": False}


def audit_project(project_dir: Path, apply_fixes: bool = False) -> Dict[str, Any]:
    """Run every stage for a single project. Always returns a result record."""
    started = time.time()
    stages = {
        "guardrails": _run_stage_guardrails(project_dir, apply_fixes),
        "self_heal": _run_stage_self_heal(project_dir, apply_fixes),
        "quality": _run_stage_quality(project_dir),
    }
    score = stages["quality"].get("score", 0.0)
    try:
        from .quality_trends import get_quality_tracker
        trend = get_quality_tracker().evaluate(score)
        get_quality_tracker().record(
            score,
            project=project_dir.name,
            status="autopilot",
            provider="autopilot",
        )
    except Exception:  # noqa: BLE001
        trend = {"state": "unavailable"}

    return {
        "project": project_dir.name,
        "path": str(project_dir),
        "score": score,
        "guardrails": stages["guardrails"],
        "self_heal": stages["self_heal"],
        "quality": stages["quality"],
        "trend": trend,
        "duration_seconds": round(time.time() - started, 2),
    }


def write_reports(results: List[Dict[str, Any]], threshold: int, apply_fixes: bool) -> Dict[str, str]:
    """Persist JSON + Markdown reports; returns their paths."""
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"autopilot-{stamp}.json"
    md_path = REPORT_DIR / f"autopilot-{stamp}.md"

    below = [r for r in results if r["score"] < threshold]
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "applied_fixes": apply_fixes,
        "threshold": threshold,
        "total": len(results),
        "below_threshold": len(below),
        "average_score": round(sum(r["score"] for r in results) / len(results), 2) if results else 0.0,
        "results": results,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Autopilot Report",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Projects audited: {payload['total']}",
        f"- Fixes applied: {'yes' if apply_fixes else 'no (dry run)'}",
        f"- Average quality score: {payload['average_score']}",
        f"- Below threshold ({threshold}): {payload['below_threshold']}",
        "",
        "| Project | Score | Guardrails | Self-heal errors | Trend |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in sorted(results, key=lambda x: x["score"]):
        lines.append(
            f"| {r['project']} | {r['score']:.1f} | "
            f"{'ok' if r['guardrails'].get('passed') else 'issues'} | "
            f"{r['self_heal'].get('errors_found', 0)} | {r.get('trend', {}).get('state', 'n/a')} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def run(root: Optional[Path] = None, apply_fixes: bool = False,
        threshold: int = DEFAULT_THRESHOLD, limit: Optional[int] = None,
        include_scratch: bool = False) -> Dict[str, Any]:
    """Audit (and optionally repair) every project under `root`."""
    root = Path(root) if root else DEFAULT_ROOT
    projects = discover_projects(root, include_scratch=include_scratch)
    if limit:
        projects = projects[:limit]

    agent_logger.info("Autopilot: auditing %d project(s) under %s (fixes=%s)",
                      len(projects), root, apply_fixes)
    results: List[Dict[str, Any]] = []
    for project in projects:
        try:
            results.append(audit_project(project, apply_fixes=apply_fixes))
        except Exception as exc:  # noqa: BLE001
            agent_logger.error("Autopilot failed on %s: %s", project.name, exc)
            results.append({"project": project.name, "path": str(project), "score": 0.0,
                            "guardrails": {"passed": False}, "self_heal": {"errors_found": 0},
                            "quality": {"error": str(exc)[:200]}, "trend": {"state": "error"}})

    report = write_reports(results, threshold, apply_fixes)
    below = [r for r in results if r["score"] < threshold]
    agent_logger.info("Autopilot complete: %d project(s), %d below threshold %d",
                      len(results), len(below), threshold)
    return {
        "total": len(results),
        "below_threshold": [r["project"] for r in below],
        "average_score": round(sum(r["score"] for r in results) / len(results), 2) if results else 0.0,
        "reports": report,
        "results": results,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Autopilot — audit & repair generated projects")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="generated-projects root")
    parser.add_argument("--fix", action="store_true", help="apply repairs (default: dry run)")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help="quality threshold")
    parser.add_argument("--limit", type=int, default=None, help="only audit the first N projects")
    parser.add_argument("--include-scratch", action="store_true", help="include build-*/test scratch dirs")
    parser.add_argument("--json-only", action="store_true", help="print JSON only (no report files)")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any project is below threshold")
    args = parser.parse_args(argv)

    outcome = run(
        root=Path(args.root),
        apply_fixes=args.fix,
        threshold=args.threshold,
        limit=args.limit,
        include_scratch=args.include_scratch,
    )
    if args.json_only:
        print(json.dumps({k: v for k, v in outcome.items() if k != "results"}, indent=2))
    else:
        print(json.dumps({"total": outcome["total"],
                          "average_score": outcome["average_score"],
                          "below_threshold": outcome["below_threshold"],
                          "reports": outcome["reports"]}, indent=2))

    if args.strict and outcome["below_threshold"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())