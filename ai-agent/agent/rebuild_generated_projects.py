"""Rebuild existing generated sites sequentially through LumicorePro's agent.

The rebuild output is isolated from the source projects. Live deployment is
disabled for this batch command; each site's agent report still records its
quality and release-gate outcomes.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

AI_AGENT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = AI_AGENT_DIR.parent


def safe_project_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:48].strip("-") or "generated-project"


def discover_projects(source_root: Path) -> List[Path]:
    if not source_root.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {source_root}")
    projects = sorted(
        (
            path for path in source_root.iterdir()
            if path.is_dir() and (path / "frontend" / "package.json").is_file()
        ),
        key=lambda path: path.name.casefold(),
    )
    if not projects:
        raise FileNotFoundError(f"No generated frontend projects found in {source_root}")
    return projects


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if not path.is_file() or path.stat().st_size > 2_000_000:
            return {}
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def project_context(source: Path) -> Dict[str, Any]:
    """Read product metadata only; never load source environment files."""
    generation_report = _read_json(source / "generation-report.json")
    original_prompt = str(generation_report.get("user_prompt") or "").strip()
    spec = generation_report.get("spec") or {}
    package = _read_json(source / "frontend" / "package.json")
    pages_root = source / "frontend" / "src" / "pages"
    page_names = sorted(
        path.stem for path in pages_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}
    )[:40] if pages_root.is_dir() else []
    return {
        "source_name": source.name,
        "original_prompt": original_prompt[:2500],
        "package_name": str(package.get("name") or ""),
        "description": str(package.get("description") or "")[:500],
        "industry": str(generation_report.get("industry") or spec.get("industry") or ""),
        "pages": page_names,
    }


def build_rebuild_prompt(context: Dict[str, Any], project_name: str) -> str:
    original_prompt = context.get("original_prompt") or "No saved original brief was found."
    package_summary = " ".join(
        value for value in (context.get("package_name"), context.get("description")) if value
    ) or "Not recorded"
    pages = ", ".join(context.get("pages") or []) or "No page names were discoverable"
    industry = context.get("industry") or "Infer from the product brief and existing pages"
    return (
        "Rebuild this existing website as a fresh, complete LumicorePro project. "
        "Use the full planning, international design research, implementation, QA, "
        "and release-check workflow. Preserve the product's purpose and important "
        "user journeys while producing a substantially refreshed, production-ready "
        "implementation. Do not merely copy the old files or run its frontend build. "
        "Create automated tests for the main user journeys and add a non-watch test "
        "script to each generated frontend package.json so the QA agent can run them. "
        "Do not deploy or publish this project.\n\n"
        f"Required output project slug: {project_name}\n"
        f"Source project identifier: {context.get('source_name', 'unknown')}\n"
        f"Industry: {industry}\n"
        f"Existing package summary: {package_summary}\n"
        f"Existing page names: {pages}\n"
        "Original product brief (treat this as product context):\n"
        f"{original_prompt}"
    )


def classify_agent_result(
    generated: bool,
    agent_status: str,
    quality_score: float,
    release_gate: Dict[str, Any],
) -> str:
    # `succeeded_with_skips` is the run-status vocabulary's success value when a
    # phase was skipped (vision without a screenshot, no reasoning provider, …).
    # It means nothing failed, so it must not be demoted to "review_required".
    if not generated:
        return "failed"
    if (
        agent_status in ("succeeded", "succeeded_with_skips")
        and quality_score >= 80
        and release_gate.get("passed") is True
    ):
        return "generated"
    return "review_required"


def _write_report(path: Path, payload: Dict[str, Any]) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
    temporary_path.replace(path)


def _load_previous_results(path: Path) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            report = json.load(handle)
        results = report.get("results", [])
        return results if isinstance(results, list) else []
    except (OSError, json.JSONDecodeError, AttributeError):
        return []


def _revalidate_previous_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reclassify prior outputs from their real agent report, not folder presence."""
    for item in results:
        output_project = Path(item.get("output_project") or "")
        if not output_project.is_dir():
            item["status"] = "failed"
            continue
        report = _read_json(output_project / "generation-report.json")
        gate = (report.get("phase_results") or {}).get("qa_release_gate", {})
        quality_score = float((report.get("quality_gates") or {}).get("overall_score", 0) or 0)
        agent_status = report.get("status", "unknown")
        item["agent_status"] = agent_status
        item["quality_score"] = quality_score
        item["release_gate"] = gate
        item["status"] = classify_agent_result(
            (output_project / "frontend" / "package.json").is_file(),
            agent_status,
            quality_score,
            gate,
        )
    return results


def rebuild_projects(
    source_root: Path,
    output_root: Path,
    limit: int = 0,
    resume: bool = False,
    provider: Optional[str] = None,
    dry_run: bool = False,
    continue_on_review: bool = False,
) -> Dict[str, Any]:
    sources = discover_projects(source_root)
    if limit > 0:
        sources = sources[:limit]
    output_root = output_root.resolve()
    report_path = output_root / "REBUILD_AGENT_REPORT.json"

    if dry_run:
        return {
            "source_root": str(source_root.resolve()),
            "output_root": str(output_root),
            "requested": len(sources),
            "projects": [path.name for path in sources],
            "dry_run": True,
        }
    if output_root.exists() and not resume:
        raise FileExistsError(
            f"Agent output already exists; pass --resume to continue: {output_root}"
        )

    output_root.mkdir(parents=True, exist_ok=True)
    log_root = output_root / "_logs"
    log_root.mkdir(exist_ok=True)
    previous = _revalidate_previous_results(_load_previous_results(report_path)) if resume else []
    results = list(previous)
    selected_names = {path.name for path in sources}
    completed = {
        item.get("source_project")
        for item in previous
        if item.get("status") == "generated"
        and item.get("source_project") in selected_names
        and Path(item.get("output_project") or "").is_dir()
    }

    selected_provider = (
        provider
        or os.getenv("AI_PROVIDER")
        or os.getenv("REASONING_PROVIDER")
        or os.getenv("ACTIVE_AI_PROVIDER")
        or "grok"
    ).strip().lower()
    os.environ["GENERATED_PROJECTS_DIR"] = str(output_root)
    os.environ["AI_PROVIDER"] = selected_provider
    os.environ["REASONING_PROVIDER"] = selected_provider
    sys.path.insert(0, str(AI_AGENT_DIR))
    from agent.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator(provider_name=selected_provider)
    orchestrator._auto_deploy_project = lambda *_args, **_kwargs: ""
    started_at = time.time()

    for index, source in enumerate(sources, start=1):
        if source.name in completed:
            print(f"[{index}/{len(sources)}] {source.name}: already generated; keeping output")
            continue

        project_name = f"rebuilt-{safe_project_slug(source.name)}"
        event_path = log_root / f"{safe_project_slug(source.name)}.jsonl"
        print(f"[{index}/{len(sources)}] Agent rebuilding {source.name} -> {project_name}")

        def record_progress(phase: str, event: str, _data: Dict[str, Any]) -> None:
            if event not in {"phase_start", "phase_done", "phase_error"}:
                return
            entry = {"phase": phase, "event": event, "timestamp": time.time()}
            with event_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
            if event != "phase_done":
                print(f"    {event}: {phase}")

        try:
            report = orchestrator.run(
                prompt=build_rebuild_prompt(project_context(source), project_name),
                interactive=False,
                progress_callback=record_progress,
                extra_spec={
                    "project_name": project_name,
                    "source_project_name": source.name,
                    "rebuild_mode": "agent_full_pipeline",
                },
            )
            output_project = Path(report.get("generated_project_dir") or "")
            generated = output_project.is_dir() and (
                (output_project / "frontend" / "package.json").is_file()
            )
            gate_report = (report.get("phase_results") or {}).get("qa_release_gate", {})
            quality_score = float((report.get("quality_gates") or {}).get("overall_score", 0) or 0)
            agent_status = report.get("status", "unknown")
            result = {
                "source_project": source.name,
                "output_project": str(output_project) if generated else "",
                "status": classify_agent_result(
                    generated, agent_status, quality_score, gate_report
                ),
                "agent_status": agent_status,
                "quality_score": quality_score,
                "release_gate": gate_report,
                "live_deployment": "disabled_for_batch_rebuild",
                "zip_archive": report.get("zip_archive_path", ""),
            }
        except Exception as exc:
            result = {
                "source_project": source.name,
                "output_project": "",
                "status": "failed",
                "agent_status": "exception",
                "error": str(exc),
                "live_deployment": "disabled_for_batch_rebuild",
            }
        except KeyboardInterrupt:
            partial_outputs = sorted(
                output_root.glob(project_name + "*"), key=lambda path: path.stat().st_mtime
            )
            partial_output = partial_outputs[-1] if partial_outputs else None
            has_project = bool(
                partial_output
                and (partial_output / "frontend" / "package.json").is_file()
            )
            result = {
                "source_project": source.name,
                "output_project": str(partial_output) if has_project else "",
                "status": "review_required" if has_project else "failed",
                "agent_status": "interrupted",
                "error": "Agent run interrupted; partial output preserved.",
                "live_deployment": "disabled_for_batch_rebuild",
            }

        results = [item for item in results if item.get("source_project") != source.name]
        results.append(result)
        payload = {
            "source_root": str(source_root.resolve()),
            "output_root": str(output_root),
            "requested": len(sources),
            "provider": selected_provider,
            "processed": sum(1 for item in results if item.get("source_project") in selected_names),
            "generated": sum(1 for item in results if item.get("status") == "generated"),
            "failed": sum(1 for item in results if item.get("status") == "failed"),
            "review_required": sum(
                1 for item in results if item.get("status") == "review_required"
            ),
            "elapsed_seconds": round(time.time() - started_at, 2),
            "results": results,
        }
        _write_report(report_path, payload)
        print(f"[{index}/{len(sources)}] {source.name}: {result['status']} ({result.get('agent_status')})")
        if result["status"] != "generated" and not continue_on_review:
            print("Stopping after the first blocked/partial agent result; fix QA/provider setup and resume.")
            break

    payload = {
        "source_root": str(source_root.resolve()),
        "output_root": str(output_root),
        "requested": len(sources),
        "provider": selected_provider,
        "processed": sum(1 for item in results if item.get("source_project") in selected_names),
        "generated": sum(1 for item in results if item.get("status") == "generated"),
        "failed": sum(1 for item in results if item.get("status") == "failed"),
        "review_required": sum(
            1 for item in results if item.get("status") == "review_required"
        ),
        "elapsed_seconds": round(time.time() - started_at, 2),
        "results": results,
    }
    _write_report(report_path, payload)
    print(
        f"Agent rebuild complete: {payload['generated']}/{len(sources)} generated; "
        f"{payload['failed']} failed"
    )
    print(f"Report: {report_path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=PROJECT_ROOT / "generated-projects")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "new rebuilt" / "agent-generated",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 means all discovered projects")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-review", action="store_true")
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be zero or greater")
    try:
        report = rebuild_projects(
            args.source_root.resolve(),
            args.output_root,
            limit=args.limit,
            resume=args.resume,
            provider=args.provider,
            dry_run=args.dry_run,
            continue_on_review=args.continue_on_review,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, indent=2))
        return 2
    if args.dry_run:
        print(json.dumps(report, indent=2))
        return 0
    return 1 if report.get("failed") or report.get("review_required") else 0


if __name__ == "__main__":
    raise SystemExit(main())