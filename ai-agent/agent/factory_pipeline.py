"""Website Factory — one pipeline from generated project to delivered product.

Stages, each with evidence and a hard gate:

  1. ``build``      npm install (if needed) + npm run build; the frontend must
                    produce ``frontend/dist/index.html``.
  2. ``backend``    the generated backend test suite must pass (``npm test``).
  3. ``qa``         browser QA on the built site (console errors, overflow,
                    screenshots at four widths).
  4. ``deploy``     deploy_engine (Vercel/Netlify/Railway/GitHub Pages) and the
                    live URL must pass :func:`agent.live_verify.verify_site`.
  5. ``video``      demo_video builds and ffprobe-verifies the ~2-minute tour.

``status: "delivered"`` is returned only when every requested stage passed.
Anything else is ``failed`` or ``partial`` with the failing evidence attached.
Reports land in ``<project>/.factory/report.json`` and ``report.md``.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import agent_logger

DEFAULT_PLATFORM = "vercel"


def _run(cmd, cwd: Path, timeout: int = 900, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    started = time.perf_counter()
    merged_env = {**os.environ, **(env or {})}
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=merged_env,
        )
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-1500:],
            "stderr_tail": (proc.stderr or "")[-1500:],
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": -1, "stderr_tail": f"timed out after {timeout}s",
                "elapsed_ms": int((time.perf_counter() - started) * 1000)}
    except OSError as exc:
        return {"ok": False, "code": -1, "stderr_tail": str(exc),
                "elapsed_ms": int((time.perf_counter() - started) * 1000)}


def _npm() -> str:
    if os.name == "nt":
        return shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"
    return shutil.which("npm") or "npm"


def build_project(project_dir: str, *, install: bool = True, api_url: str = "",
                  timeout: int = 900) -> Dict[str, Any]:
    """Build the generated frontend and return the dist path + command evidence.

    ``api_url`` is injected as ``VITE_API_URL`` for the build. Without it the
    generated pages fall back to ``http://localhost:5000`` and every deployed
    form calls the visitor's own machine.
    """
    root = Path(project_dir)
    frontend = root / "frontend"
    if not (frontend / "package.json").is_file():
        # A standalone static project may already be built at the root.
        if (root / "dist" / "index.html").is_file():
            return {"ok": True, "dist": str(root / "dist"), "skipped": "no frontend/package.json"}
        return {"ok": False, "message": "No frontend/package.json and no prebuilt dist/"}

    steps: Dict[str, Any] = {}
    if install and not (frontend / "node_modules").is_dir():
        steps["install"] = _run([_npm(), "install", "--no-audit", "--no-fund"], frontend, timeout=timeout)
        if not steps["install"]["ok"]:
            return {"ok": False, "dist": "", "steps": steps,
                    "message": "npm install failed", "stderr": steps["install"]["stderr_tail"]}

    package_json = json.loads((frontend / "package.json").read_text(encoding="utf-8"))
    if "build" not in (package_json.get("scripts") or {}):
        return {"ok": False, "dist": "", "steps": steps, "message": "frontend package has no build script"}
    build_env = {"VITE_API_URL": api_url} if api_url else None
    steps["build"] = _run([_npm(), "run", "build"], frontend, timeout=timeout, env=build_env)
    steps["build"]["api_url"] = api_url or ""
    dist = frontend / "dist"
    if not steps["build"]["ok"]:
        return {"ok": False, "dist": str(dist), "steps": steps, "message": "npm run build failed",
                "stderr": steps["build"]["stderr_tail"]}
    if not (dist / "index.html").is_file():
        return {"ok": False, "dist": str(dist), "steps": steps,
                "message": "build finished but dist/index.html is missing"}
    return {"ok": True, "dist": str(dist), "steps": steps}


def test_backend(project_dir: str, timeout: int = 300) -> Dict[str, Any]:
    """Run the generated backend tests. A project without tests is a failure here,
    because a deploy gate that cannot see tests is not a gate."""
    backend = Path(project_dir) / "backend"
    if not (backend / "package.json").is_file():
        return {"ok": True, "skipped": "no backend"}
    package = json.loads((backend / "package.json").read_text(encoding="utf-8"))
    if "test" not in (package.get("scripts") or {}):
        return {"ok": False, "message": "backend package.json has no test script"}
    result = _run([_npm(), "test"], backend, timeout=timeout)
    return {**result, "command": "npm test", "cwd": str(backend)}


def run_qa(project_dir: str) -> Dict[str, Any]:
    result = {"ok": False, "message": "QA not run"}
    try:
        from agent.extensions.browser_qa import run_browser_qa

        qa = run_browser_qa(str(project_dir))
        result = {
            "ok": qa.get("status") == "passed",
            "status": qa.get("status"),
            "results": qa.get("results") or qa.get("viewports") or qa,
            "message": "" if qa.get("status") == "passed" else "browser QA did not pass",
        }
    except Exception as exc:  # noqa: BLE001 — QA failure is reported, not hidden
        result = {"ok": False, "message": f"browser QA crashed: {exc}"}
    return result


def run_factory(
    project_dir: str,
    *,
    deploy: str = DEFAULT_PLATFORM,
    video: bool = True,
    name: str = "",
    tagline: str = "",
    skip_build: bool = False,
    install: bool = True,
    allow_qa_fail: bool = False,
    video_target: float = 120.0,
    out_dir: str = "",
    api_url: str = "",
    api_health: str = "",
) -> Dict[str, Any]:
    """Run build → backend tests → QA → deploy → live verify → demo video."""
    started = time.perf_counter()
    project = Path(project_dir).resolve()
    if not project.is_dir():
        return {"status": "failed", "message": "Project directory not found", "project_dir": str(project_dir)}

    platform = (deploy or "none").strip().lower()
    if platform in {"", "none", "off"}:
        platform = "none"
    report_dir = Path(out_dir) if out_dir else project / ".factory"
    report_dir.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {
        "status": "running",
        "verified": False,
        "project_dir": str(project),
        "platform": platform,
        "requested_video": bool(video),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stages": {},
    }

    # 1 — build -----------------------------------------------------------------
    if skip_build:
        dist = project / "frontend" / "dist"
        build = {"ok": (dist / "index.html").is_file(), "dist": str(dist), "skipped": True}
        if not build["ok"]:
            build["message"] = "--skip-build was set but no dist/index.html exists"
    else:
        build = build_project(str(project), install=install, api_url=api_url)
    report["stages"]["build"] = build
    if not build.get("ok"):
        report.update(status="failed", message=build.get("message", "build failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 2 — backend tests ---------------------------------------------------------
    backend = test_backend(str(project))
    report["stages"]["backend_tests"] = backend
    if not backend.get("ok"):
        report.update(status="failed", message=backend.get("message", "backend tests failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 3 — QA --------------------------------------------------------------------
    qa = run_qa(str(project))
    report["stages"]["qa"] = qa
    if not qa.get("ok") and not allow_qa_fail:
        report.update(status="failed", message=qa.get("message", "QA failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 4 — deploy + live verification -------------------------------------------
    backend_present = (project / "backend" / "package.json").is_file()
    deployment: Dict[str, Any] = {"status": "skipped", "verified": False}
    if platform != "none":
        from agent.deploy_engine import deploy_project

        deployment = deploy_project(str(project), platform=platform)
        if deployment.get("verified") and backend_present:
            # The static hosts (Vercel/Netlify/Pages) only serve the frontend.
            # A full-stack claim needs the API host verified too.
            if not api_health:
                deployment = {
                    **deployment,
                    "verified": False,
                    "api_deployed": False,
                    "message": "Frontend is live, but the Express API is not deployed; "
                               "host backend/ (Railway/Render/Docker) and pass api_health",
                }
            else:
                from agent.live_verify import verify_site

                evidence = verify_site(
                    deployment["url"], api_health=api_health, timeout=60
                )
                deployment = {
                    **deployment,
                    "verification": evidence,
                    "verified": bool(evidence.get("verified")),
                    "api_deployed": bool((evidence.get("checks") or {}).get("api", {}).get("ok")),
                }
    report["stages"]["deploy"] = {
        key: deployment.get(key)
        for key in ("status", "url", "platform", "verified", "deployment_id", "message",
                    "verification", "api_deployed")
        if key in deployment
    }

    # 5 — demo video ------------------------------------------------------------
    if video:
        from agent.demo_video import generate_demo_video

        live_url = deployment.get("url", "") if deployment.get("verified") else ""
        video_result = generate_demo_video(
            str(project), name=name, tagline=tagline, live_url=live_url,
            target_seconds=video_target,
            out_path=str(report_dir / "demo.mp4"),
        )
        report["stages"]["video"] = {
            key: video_result.get(key)
            for key in ("status", "verified", "video", "subtitles", "duration_seconds",
                        "resolution", "warnings", "failures", "missing", "message")
            if key in video_result
        }

    failures = []
    if platform != "none" and not deployment.get("verified"):
        failures.append(f"deployment not verified ({deployment.get('status')}: {deployment.get('message', '')})")
    if video and not report["stages"].get("video", {}).get("verified"):
        failures.append("demo video not verified")
    if not qa.get("ok"):
        failures.append("QA failed (allowed by caller)")

    report["status"] = "delivered" if not failures else "partial"
    report["failures"] = failures
    report["verified"] = not failures
    report["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return _write_report(project, report_dir, report)


def _write_report(project: Path, report_dir: Path, report: Dict[str, Any]) -> Dict[str, Any]:
    report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json_path = report_dir / "report.json"
    md_path = report_dir / "report.md"
    report["report_json"] = str(json_path)
    report["report_md"] = str(md_path)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Delivery report",
        "",
        f"- **Project:** `{project.name}`",
        f"- **Status:** `{report['status']}`",
        f"- **Verified:** {'yes' if report.get('verified') else 'no'}",
        f"- **Elapsed:** {report.get('elapsed_ms', 0)} ms",
        "",
    ]
    for stage_name, stage in (report.get("stages") or {}).items():
        ok = stage.get("ok", stage.get("verified", stage.get("status") in {"live", "skipped"}))
        lines.append(f"## {stage_name} — {'PASS' if ok else 'FAIL/UNVERIFIED'}")
        for key in ("url", "status", "duration_seconds", "resolution", "message", "dist"):
            if stage.get(key):
                lines.append(f"- {key}: `{stage[key]}`")
        for warning in stage.get("warnings") or []:
            lines.append(f"- warning: {warning}")
        lines.append("")
    for failure in report.get("failures") or []:
        lines.append(f"- failure: {failure}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def preflight() -> Dict[str, Any]:
    """What this machine can actually run — used by the API status endpoint."""
    from agent.demo_video import detect_toolchain

    vercel = shutil.which("vercel")
    npx = shutil.which("npx")
    return {
        "node": shutil.which("node") or "",
        "npm": _npm(),
        "vercel_cli": vercel or "",
        "npx": npx or "",
        "video": detect_toolchain(),
        "playwright_node": bool((Path(__file__).resolve().parents[2] / "node_modules" / "playwright" / "cli.js").is_file()),
    }
