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
import re
import shutil
import subprocess
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import agent_logger
from agent.live_verify import LOCAL_PATH_RE as _LOCAL_PATH_RE

DEFAULT_PLATFORM = "vercel"

# backend/ emitted by fullstack_ultra_engine mounts its health route here, so a
# delivery that names an API host proves it without the operator restating the path.
GENERATED_API_HEALTH_PATH = "api/v1/health"

_STOPWORDS = {
    "a", "an", "the", "build", "create", "make", "generate", "website", "site",
    "platform", "app", "application", "please", "need", "want", "for", "with",
}

_INDUSTRY_KEYWORDS = (
    ("fintech", "fintech"), ("bank", "fintech"), ("payment", "fintech"), ("invoice", "fintech"),
    ("ecommerce", "ecommerce"), ("e-commerce", "ecommerce"), ("shop", "ecommerce"), ("store", "ecommerce"),
    ("restaurant", "restaurant"), ("food", "restaurant"), ("cafe", "restaurant"),
    ("real estate", "real-estate"), ("property", "real-estate"),
    ("clinic", "healthcare"), ("health", "healthcare"), ("medical", "healthcare"),
    ("school", "education"), ("course", "education"), ("learning", "education"),
    ("travel", "travel"), ("booking", "hospitality"), ("hotel", "hospitality"),
    ("fitness", "sports"), ("gym", "sports"), ("sport", "sports"),
    ("game", "gaming"), ("gaming", "gaming"), ("esports", "gaming"),
    ("ai", "saas"), ("saas", "saas"), ("crm", "saas"), ("copilot", "saas"),
    ("agent", "saas"), ("automation", "saas"), ("analytics", "saas"),
)


def _emit(progress, stage: str, status: str, **detail) -> None:
    """Send one progress event without ever breaking the pipeline."""
    if not callable(progress):
        return
    try:
        progress({"stage": stage, "status": status, **detail})
    except Exception:  # noqa: BLE001 — a broken listener must not fail a delivery
        pass


def parse_delivery_prompt(prompt: str) -> Dict[str, Any]:
    """Turn one natural-language sentence into a generation + delivery plan.

    Understands: product name (quoted, ``named X`` or a leading brand token),
    industry keywords, deploy target keywords and an opt-out for the video.
    """
    text = " ".join(str(prompt or "").split())
    if len(text) < 8:
        raise ValueError("prompt is too short — describe the product you want")
    lower = text.lower()

    name = ""
    quoted = re.search(r'["\u201c]([A-Za-z][A-Za-z0-9&. -]{1,30})["\u201d]', text)
    named = re.search(r"(?:named|called|brand(?:ed)?)\s+([A-Z][A-Za-z0-9&.-]{1,30})", text)
    if quoted:
        name = quoted.group(1).strip()
    elif named:
        name = named.group(1).strip()
    else:
        # "Build CortexDesk, an AI copilot…" — the brand is the first token that
        # is neither an imperative verb nor a descriptor, so scan past them.
        generic = _STOPWORDS | {
            "ai", "ml", "saas", "web", "modern", "professional", "full", "stack",
            "landing", "page", "my", "your", "me", "us", "new", "clean", "for",
        }
        for token in [t.strip('"\'.,:;!?') for t in text.split()][:4]:
            if not token or token.lower() in generic:
                continue
            if re.match(r"^[A-Z][A-Za-z0-9&.-]{1,29}$", token):
                name = token
                break

    industry = next((label for needle, label in _INDUSTRY_KEYWORDS if needle in lower), "saas")
    if not name:
        name = f"{industry.replace('-', ' ').title()} Studio"

    tagline = re.split(r"(?<=[.!?])\s+", text)[0].strip()
    if len(tagline) > 140:
        tagline = tagline[:137].rstrip() + "..."
    if not tagline:
        tagline = f"{industry.replace('-', ' ').title()} platform"

    deploy = "vercel"
    if re.search(r"\b(no deploy|without deploy|local only|do not deploy)\b", lower):
        deploy = "none"
    elif "railway" in lower:
        deploy = "railway"
    elif "netlify" in lower:
        deploy = "netlify"
    elif "github pages" in lower:
        deploy = "github-pages"

    video = not re.search(r"\b(no video|without video|skip the video)\b", lower)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or industry
    return {
        "name": name,
        "tagline": tagline,
        "industry": industry,
        "slug": slug[:48],
        "deploy": deploy,
        "video": video,
        "prompt": text,
    }


def _unique_destination(root: Path, slug: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / slug
    suffix = 2
    while candidate.exists():
        candidate = root / f"{slug}-{suffix}"
        suffix += 1
    return candidate


def api_health_target(api_url: str, api_health: str = "") -> str:
    """Resolve the API health path against the API host, not the frontend host.

    Static hosts put the SPA and the Express service on different domains, so
    joining ``/api/v1/health`` to the deployed frontend URL probes a path that
    the SPA rewrites to ``index.html`` — an HTML page, not the API, and the old
    gate read its 200 as proof the backend was live.

    The health path is optional on purpose: ``backend/`` generated by this agent
    always serves ``api/v1/health``, so a run that only passes ``--factory-api-url``
    still proves the hosted database instead of blocking on a missing flag.
    """
    path = (api_health or "").strip().replace("\\", "/")
    if _LOCAL_PATH_RE.match(path):
        # Git Bash/MSYS rewrites a leading-slash argument (/api/v1/health) into
        # <msys-root>/api/v1/health before Python sees it, and urljoin reads the
        # "D:" as a scheme — the probe then hits a file path, never the API.
        # Dropping the mangled value falls back to the generated contract below.
        path = ""
    base = (api_url or "").strip()
    if not base.startswith(("http://", "https://")):
        return path.lstrip("/")  # no API host to resolve against; probe relative to the site
    if path.startswith(("http://", "https://")):
        return path
    parts = urllib.parse.urlsplit(base)
    if parts.path.rstrip("/").lower().endswith("health"):
        return base.rstrip("/")  # the caller already handed over the full health URL
    if not path:
        path = GENERATED_API_HEALTH_PATH
    return urllib.parse.urljoin(f"{parts.scheme}://{parts.netloc}/", path.lstrip("/"))


def deliver_from_prompt(
    prompt: str,
    *,
    dest_root: str = "generated-projects",
    platform: Optional[str] = None,
    video: Optional[bool] = None,
    api_url: str = "",
    api_health: str = "",
    progress=None,
    reuse_existing: bool = False,
) -> Dict[str, Any]:
    """One prompt → generated project → build/tests/QA/deploy/verify/video.

    ``reuse_existing`` regenerates into ``<dest_root>/<slug>`` in place (for
    shipping an update of the same product); the default never overwrites an
    existing directory and picks ``<slug>-2``, ``<slug>-3`` instead.
    """
    plan = parse_delivery_prompt(prompt)
    deploy = (platform or plan["deploy"]).strip().lower()
    want_video = plan["video"] if video is None else bool(video)

    health = provider_health()
    if not health["usable"]:
        _emit(progress, "generate", "blocked", provider=health["provider"], message=health["message"])
        return {
            "status": "failed",
            "verified": False,
            "message": f"generation provider unusable: {health['message']}",
            "provider": health,
            "plan": plan,
        }

    root = Path(dest_root).resolve()
    destination = (root / plan["slug"]) if reuse_existing else _unique_destination(root, plan["slug"])
    destination.mkdir(parents=True, exist_ok=True)

    _emit(progress, "generate", "running", name=plan["name"], industry=plan["industry"])
    from agent.fullstack_ultra_engine import FullStackUltraEngine
    from agent.generation_contract import resolve_generation_contract

    generated = FullStackUltraEngine().generate_project(
        str(destination),
        prompt=plan["prompt"],
        brand_name=plan["name"],
        industry=plan["industry"],
        generation_contract=resolve_generation_contract({}),
    )
    if not generated.get("success"):
        _emit(progress, "generate", "failed", errors=generated.get("errors"))
        return {
            "status": "failed",
            "verified": False,
            "message": "generation failed",
            "plan": plan,
            "destination": str(destination),
            "generation": generated,
        }
    _emit(progress, "generate", "done", files=generated.get("total_files"),
          elapsed_ms=generated.get("elapsed_ms"))

    result = run_factory(
        str(destination),
        deploy=deploy,
        video=want_video,
        name=plan["name"],
        tagline=plan["tagline"],
        api_url=api_url,
        api_health=api_health,
        progress=progress,
        generation_meta={
            "engine": "FullStackUltraEngine",
            "plan": plan,
            "files": generated.get("total_files"),
            "elapsed_ms": generated.get("elapsed_ms"),
            "destination": str(destination),
        },
    )
    result["plan"] = plan
    result["provider"] = health
    result["destination"] = str(destination)
    return result


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
    progress=None,
    generation_meta: Optional[Dict[str, Any]] = None,
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
    if generation_meta:
        report["generation"] = generation_meta

    # 1 — build -----------------------------------------------------------------
    if skip_build:
        dist = project / "frontend" / "dist"
        build = {"ok": (dist / "index.html").is_file(), "dist": str(dist), "skipped": True}
        if not build["ok"]:
            build["message"] = "--skip-build was set but no dist/index.html exists"
    else:
        _emit(progress, "build", "running")
        build = build_project(str(project), install=install, api_url=api_url)
    report["stages"]["build"] = build
    _emit(progress, "build", "done" if build.get("ok") else "failed",
          dist=build.get("dist"), message=build.get("message"))
    if not build.get("ok"):
        report.update(status="failed", message=build.get("message", "build failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 2 — backend tests ---------------------------------------------------------
    _emit(progress, "backend_tests", "running")
    backend = test_backend(str(project))
    report["stages"]["backend_tests"] = backend
    _emit(progress, "backend_tests", "done" if backend.get("ok") else "failed")
    if not backend.get("ok"):
        report.update(status="failed", message=backend.get("message", "backend tests failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 3 — QA --------------------------------------------------------------------
    _emit(progress, "qa", "running")
    qa = run_qa(str(project))
    report["stages"]["qa"] = qa
    _emit(progress, "qa", "done" if qa.get("ok") else "failed", detail=qa.get("status"))
    if not qa.get("ok") and not allow_qa_fail:
        report.update(status="failed", message=qa.get("message", "QA failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 4 — deploy + live verification -------------------------------------------
    backend_present = (project / "backend" / "package.json").is_file()
    deployment: Dict[str, Any] = {"status": "skipped", "verified": False}
    if platform != "none":
        from agent.deploy_engine import deploy_project

        _emit(progress, "deploy", "running", platform=platform)
        deployment = deploy_project(str(project), platform=platform, api_url=api_url)
        if deployment.get("verified") and backend_present:
            # The static hosts (Vercel/Netlify/Pages) only serve the frontend.
            # A full-stack claim needs the API host verified too, and the API
            # origin has to be the one the deployed bundle actually calls.
            health_target = api_health_target(api_url, api_health) if api_url else ""
            if not health_target:
                deployment = {
                    **deployment,
                    "verified": False,
                    "api_deployed": False,
                    "message": "Frontend is live, but the Express API is not deployed; "
                               "host backend/ (Railway/Render/Docker) and pass --factory-api-url",
                }
            else:
                from agent.live_verify import verify_site

                evidence = verify_site(
                    deployment["url"], api_health=health_target, timeout=60
                )
                deployment = {
                    **deployment,
                    "verification": evidence,
                    "verified": bool(evidence.get("verified")),
                    "api_deployed": bool((evidence.get("checks") or {}).get("api", {}).get("ok")),
                    "api_health_url": health_target,
                }
    report["stages"]["deploy"] = {
        key: deployment.get(key)
        for key in ("status", "url", "platform", "verified", "deployment_id", "message",
                    "verification", "api_deployed", "api_env", "api_health_url")
        if key in deployment
    }
    if platform == "none":
        _emit(progress, "deploy", "skipped")
    elif deployment.get("verified"):
        _emit(progress, "deploy", "done", url=deployment.get("url"), verified=True)
    elif deployment.get("status") == "live":
        # Frontend is up; the API half is unverified — say that, not "failed".
        _emit(progress, "deploy", "partial", url=deployment.get("url"), verified=False,
              message=deployment.get("message"))
    else:
        _emit(progress, "deploy", "failed", url=deployment.get("url"),
              message=deployment.get("message"))

    # 5 — demo video ------------------------------------------------------------
    if video:
        from agent.demo_video import generate_demo_video

        _emit(progress, "video", "running")
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
        _emit(progress, "video", "done" if video_result.get("verified") else "failed",
              duration_seconds=video_result.get("duration_seconds"),
              message=video_result.get("message"))

    failures = []
    if platform != "none" and not deployment.get("verified"):
        failures.append(f"deployment not verified ({deployment.get('status')}: {deployment.get('message', '')})")
    if video and not report["stages"].get("video", {}).get("verified"):
        failures.append("demo video not verified")
    if not qa.get("ok"):
        failures.append("QA failed (allowed by caller)")

    # `delivered` claims a hosted, verified product, so it requires a hosting
    # stage that actually passed. A local-only run reports `built`.
    if platform == "none" and not failures:
        report["status"] = "built"
        report["message"] = "every stage passed locally; no hosting was requested"
    else:
        report["status"] = "delivered" if not failures else "partial"
    report["failures"] = failures
    report["verified"] = report["status"] == "delivered"
    report["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    _emit(progress, "run", report["status"], verified=report["verified"], failures=failures,
          elapsed_ms=report["elapsed_ms"])
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


def provider_health(*, probe: bool = True) -> Dict[str, Any]:
    """Is the active generation provider actually able to serve a call?

    A placeholder key or a retired model id used to surface minutes into a
    generation run, leaving a half-written project on disk. Delivery checks
    this once, before it writes anything.
    """
    from config import providers

    name = providers.active_provider_name()
    try:
        status = providers.provider_status(name)
    except Exception:  # an unimportable provider is a hard block, not a crash
        return {"provider": name, "model": "", "usable": False, "key_present": False,
                "message": f"provider '{name}' could not be resolved"}

    health: Dict[str, Any] = {
        "provider": status["name"],
        "model": status["model"],
        "key_present": status["key_present"],
        "usable": bool(status["configured"]),
        "model_offered": None,
        "available_models": 0,
        "message": "" if status["configured"] else f"{status['env_var']} is missing or still a placeholder",
    }
    if not health["usable"] or not probe:
        return health

    probed = providers.probe_model(name)
    health["model_offered"] = probed.get("model_offered")
    health["available_models"] = probed.get("available_models", 0)
    if probed.get("probed") and probed.get("model_offered") is False:
        health["usable"] = False
        health["message"] = probed.get("reason", "")
        health["suggested_models"] = probed.get("suggested_models", [])
    elif not probed.get("probed"):
        health["message"] = probed.get("reason", "")
    return health


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
        "provider": provider_health(),
        "playwright_node": bool((Path(__file__).resolve().parents[2] / "node_modules" / "playwright" / "cli.js").is_file()),
    }
