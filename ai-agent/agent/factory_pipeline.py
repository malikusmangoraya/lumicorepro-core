"""Factory delivery pipeline for legacy websites and contract-selected app surfaces.

Stages, each with evidence and a hard gate:

  Web requests build, run backend tests and browser QA, then deploy/verify the
  frontend. App-only requests skip those web stages but retain backend/API/DB
  proof; requested mobile apps additionally export, build an APK and verify on
  an emulator. Requested PWA evidence is gated separately from browser QA.

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
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import agent_logger
from agent import native_binary_repair as nbr
from agent.live_verify import LOCAL_PATH_RE as _LOCAL_PATH_RE


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_app_contract(project_dir: str) -> Optional[Dict[str, Any]]:
    """Read the generated delivery surfaces, or return ``None`` for legacy sites."""
    path = Path(project_dir) / "app-contract.json"
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError("Invalid app contract: expected a regular file")
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("Invalid app contract: file is not valid JSON") from None

    if not isinstance(contract, dict):
        raise ValueError("Invalid app contract: expected a JSON object")
    if not {"version", "web", "pwa", "mobile"}.issubset(contract):
        raise ValueError(
            "Invalid app contract: version, web, pwa and mobile are all required"
        )
    if type(contract.get("version")) is not int or contract.get("version") != 1:
        raise ValueError("Invalid app contract: unsupported or missing version")
    web = contract.get("web")
    pwa = contract.get("pwa")
    mobile = contract.get("mobile")
    if not isinstance(web, str) or web not in {"website", "web_app", "none"}:
        raise ValueError("Invalid app contract: unsupported web surface")
    if not isinstance(pwa, bool) or (pwa and web == "none"):
        raise ValueError("Invalid app contract: PWA requires a web surface")

    normalized_mobile = None
    if mobile is not None:
        if not isinstance(mobile, dict):
            raise ValueError("Invalid app contract: mobile surface must be an object")
        if not {"platforms", "verification"}.issubset(mobile):
            raise ValueError("Invalid app contract: incomplete mobile surface")
        platforms = mobile["platforms"]
        verification = mobile["verification"]
        if (not isinstance(platforms, list) or not platforms
                or any(not isinstance(platform, str) or platform not in {"android", "ios"}
                       for platform in platforms)
                or len(set(platforms)) != len(platforms)):
            raise ValueError("Invalid app contract: unsupported mobile platforms")
        if not isinstance(verification, str) or verification not in {"apk_emulator", "none"}:
            raise ValueError("Invalid app contract: unsupported mobile verification")
        normalized_mobile = {"platforms": platforms, "verification": verification}
    if web == "none" and normalized_mobile is None:
        raise ValueError(
            "Invalid app contract: at least one client surface (web or mobile) "
            "must be requested"
        )
    return {"web": web, "pwa": pwa, "mobile": normalized_mobile}


DEFAULT_PLATFORM = "vercel"

# The mobile stages consume the path-shaped toolchain() contract; a readiness
# report would silently degrade to booleans, so name the gaps for the handoff.
_TOOLCHAIN_PATH_KEYS = (
    "java_home", "sdk", "adb", "emulator", "avd", "avd_home", "maestro", "gradle_home",
    "cmake",
)
_TOOLCHAIN_LABELS = {
    "java_home": "JDK 17",
    "sdk": "Android SDK",
    "adb": "adb",
    "emulator": "Android emulator",
    "avd": "AVD image",
    "avd_home": "AVD home",
    "maestro": "Maestro",
    "gradle_home": "Gradle home",
    "cmake": "CMake with a long-path-aware ninja",
}

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


def _emulator_fixture_api_url(base_url: str) -> str:
    """Translate the host-only loopback fixture to Android's emulator gateway."""
    parsed = urllib.parse.urlsplit(base_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or not parsed.port
        or parsed.path not in ("", "/")
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("fixture API must bind to an ephemeral 127.0.0.1 port")
    return f"http://10.0.2.2:{parsed.port}/api/v1"


def _probe_mobile_fixture_api(base_url: str) -> Dict[str, Any]:
    """Prove the app-runs fixture is serving on its loopback port before APK build."""
    parsed = urllib.parse.urlsplit(base_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or not parsed.port
        or parsed.path not in ("", "/")
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return {
            "ok": False,
            "status": "failed",
            "message": "fixture API health probe requires a loopback origin",
        }
    health_url = f"{base_url.rstrip('/')}/api/v1/health"
    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            payload = json.loads(response.read())
            data = payload.get("data") if isinstance(payload, dict) else None
            valid = (
                response.status == 200
                and isinstance(payload, dict)
                and payload.get("success") is True
                and isinstance(data, dict)
                and data.get("fixture") is True
                and data.get("status") == "ok"
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": "failed",
            "url": health_url,
            "message": f"fixture API health probe failed ({type(exc).__name__})",
        }
    if not valid:
        return {
            "ok": False,
            "status": "failed",
            "url": health_url,
            "message": "fixture API returned invalid health evidence",
        }
    return {
        "ok": True,
        "status": "passed",
        "url": health_url,
        "body": {"status": "ok", "fixture": True},
    }


def _backend_env_value(backend_dir: Path, key: str) -> str:
    """Read one value from the generated backend's own .env (never echoed)."""
    try:
        from agent.deploy_engine import read_env_file
        return read_env_file(backend_dir / ".env").get(key, "").strip()
    except Exception:  # noqa: BLE001 — an unreadable local file is simply "absent"
        return ""


def _apply_schema(evidence: Dict[str, Any], database_url: str, project: Path, progress=None) -> str:
    """Migrate the database that was just created, and fold the result into the
    stage evidence. Returns the URL to deploy against, or "" when the schema is
    not there — an API booted against an empty database is not a product.

    A missing runner is only a warning: an existing repository may keep its
    migrations elsewhere, and the live probes (health proves the database, the
    contact write and the CRUD journey need real tables) cover what this step
    would have proven. An *error* from the project's own runner is never waived.
    """
    from agent.db_provision import _scrub, run_migrations

    _emit(progress, "database", "running", step="schema", database=evidence.get("database"))
    migrations = run_migrations(project / "backend", database_url)
    summary = {key: migrations[key] for key in ("ok", "status", "applied", "names", "message")
               if key in migrations}
    # The runner scrubs its own messages, and this is the stage that holds the
    # credential, so the URL is stripped again on the way into the report.
    if summary.get("message"):
        summary["message"] = _scrub(str(summary["message"]), database_url)
    evidence["migrations"] = summary
    if migrations.get("status") == "missing":
        evidence.setdefault("warnings", []).append(summary.get("message", ""))
        _emit(progress, "database", "done", schema="absent", message=summary.get("message"))
        return database_url
    if migrations.get("ok"):
        _emit(progress, "database", "done", schema=migrations.get("status"),
              applied=migrations.get("applied"))
        return database_url
    evidence["ok"] = False
    evidence["status"] = "schema-incomplete"
    evidence["message"] = (f"database {evidence.get('database', '')} exists but its schema did not "
                           f"apply ({migrations.get('status')}: {summary.get('message', '')})")
    _emit(progress, "database", "schema-incomplete", message=evidence["message"])
    return ""


def _host_database(project: Path, progress=None):
    """Create the project's own Postgres database, migrate it, hand back its URL.

    Returns ``(evidence, connection_string)``. The connection string is kept out
    of ``evidence`` on purpose: evidence goes into report.json, and a Neon
    credential in a report is a credential in a git tree.
    """
    from agent.db_provision import (database_url_for, missing_credential_message,
                                    provision_database, redact, template_url)

    _emit(progress, "database", "running", project=project.name)
    template = template_url()
    fallback = _backend_env_value(project / "backend", "DATABASE_URL")
    if not template and fallback:
        evidence = {"ok": True, "status": "reused", "host": redact(fallback)["host"],
                    "database": (urllib.parse.urlsplit(fallback).path or "").lstrip("/"),
                    "message": "provisioned from the connection string already configured in backend/.env"}
        return evidence, _apply_schema(evidence, fallback, project, progress)
    if not template:
        evidence = {"ok": False, "status": "blocked",
                    "message": missing_credential_message() + ", or put a DATABASE_URL "
                               "in the project's backend/.env"}
        _emit(progress, "database", "blocked", message=evidence["message"])
        return evidence, ""

    result = provision_database(project.name, template, backend_dir=project / "backend")
    if not result.get("ok"):
        _emit(progress, "database", result.get("status", "failed"),
              database=result.get("database"), message=result.get("message"))
        return result, ""
    evidence = {key: result[key] for key in ("ok", "status", "database", "host", "message")
                if key in result}
    _emit(progress, "database", "done", provisioned=result.get("status"),
          database=result.get("database"), host=result.get("host"))
    return evidence, _apply_schema(evidence, database_url_for(template, result["database"]),
                                   project, progress)


def _host_api(project: Path, database_url: str, progress=None) -> Dict[str, Any]:
    """Deploy backend/ as its own hosted project — the half that used to be manual."""
    from agent.deploy_engine import deploy_backend

    _emit(progress, "api", "running", project=project.name)
    result = deploy_backend(str(project), database_url=database_url)
    evidence = {key: result[key] for key in
                ("status", "url", "health_url", "project_name", "deployment_id", "message",
                 "env", "verified") if key in result}
    if result.get("status") == "live":
        _emit(progress, "api", "done", url=result.get("url"))
    else:
        _emit(progress, "api", "failed" if result.get("status") in {"failed", "blocked"} else "partial",
              url=result.get("url"), message=evidence.get("message"))
    return evidence


def _lock_api_cors(project: Path, database_url: str, frontend_url: str, progress=None) -> Dict[str, Any]:
    """Republish the API with the real site origin, so CORS is not left on ``*``.

    The frontend URL is only known after the frontend deployment, which is why
    the API is published twice: first so the bundle can be built and verified
    against a live origin, then once more locked to that origin.
    """
    from agent.deploy_engine import deploy_backend

    _emit(progress, "api", "running", step="cors-lock", origin=frontend_url)
    result = deploy_backend(str(project), database_url=database_url, cors_origin=frontend_url)
    return {key: result[key] for key in ("status", "url", "health_url", "message", "env")
            if key in result}


_PROOF_LABELS = {
    "health": "the hosted API never proved its database is reachable",
    "write": "the hosted contact form never wrote a real row",
    "surface": "the hosted API never answered the client journey its own routes promise",
    "feed": "the hosted change feed never pushed an event to an open dashboard",
}


def _not_proven(reason: str) -> Dict[str, Any]:
    """A proof that never ran is a failure, not a blank — it must read as one."""
    return {"ok": False, "status": "not-probed", "failures": [reason]}


def _prove_api(api_url: str, health_target: str, progress=None) -> Dict[str, Any]:
    """Prove the hosted API is a product, not a process that happens to boot.

    Four separate claims, each with its own evidence: the health endpoint reaches
    Postgres, the contact form stores a row, every generated endpoint answers a
    real client journey (register, list, create, read, update, delete) with the
    tenant checks that go with it, and the change feed pushes an event while a
    dashboard is listening. A 200 from `/health` proves none of those.
    """
    from agent.live_verify import (
        verify_api_health,
        verify_api_surface,
        verify_contact_write,
        verify_realtime_feed,
    )

    _emit(progress, "handshake", "running", api=api_url)
    health = verify_api_health(health_target, timeout=120) if health_target else {
        "ok": False, "status": "target-invalid", "failures": ["no health target"]}
    write = verify_contact_write(api_url, timeout=60) if health.get("ok") else _not_proven(
        "the contact form was not probed because the API health check failed")
    surface = verify_api_surface(api_url, timeout=90) if write.get("ok") else _not_proven(
        "the endpoint surface was not probed because the contact form did not write")
    feed = verify_realtime_feed(api_url, str(surface.get("token") or ""), timeout=45,
                                event_timeout=10.0) if surface.get("ok") else _not_proven(
        "the live feed was not probed because the endpoint surface check failed")

    stages = [("health", health), ("write", write), ("surface", surface), ("feed", feed)]
    failing = [pair for pair in stages if not pair[1].get("ok")]
    evidence = {
        "ok": not failing,
        "status": "verified" if not failing else failing[0][1].get("status"),
        "health": {key: health.get(key) for key in ("ok", "status", "url", "body")},
        "write": {key: write.get(key) for key in ("ok", "status", "url", "id")},
        # `token` is a live session credential: it is read for the feed call above
        # and deliberately never copied into the evidence the report is built from.
        "surface": {key: surface.get(key) for key in
                    ("ok", "status", "url", "proven", "leftovers")},
        "feed": {key: feed.get(key) for key in
                 ("ok", "status", "events", "latency_ms", "id", "leftovers")},
        "failures": [str(f) for _, stage in stages for f in (stage.get("failures") or [])],
    }
    _emit(progress, "handshake", "done" if evidence["ok"] else "failed",
          proof=evidence["status"], failures=evidence["failures"])
    return evidence


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
    scene: Optional[Dict[str, Any]] = None,
    app: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """One prompt → generated project → build/tests/QA/deploy/verify/video.

    ``reuse_existing`` regenerates into ``<dest_root>/<slug>`` in place (for
    shipping an update of the same product); the default never overwrites an
    existing directory and picks ``<slug>-2``, ``<slug>-3`` instead.
    ``app`` names the requested surfaces; when omitted the prompt decides and
    a plain website request keeps the existing lane (no ``app`` block).
    """
    plan = parse_delivery_prompt(prompt)
    deploy = (platform or plan["deploy"]).strip().lower()
    want_video = plan["video"] if video is None else bool(video)
    from agent.generation_contract import resolve_app_request, resolve_generation_contract

    # Surface validation is pure and must precede the provider gate: an invalid
    # app request must not call a provider or create the destination directory.
    try:
        resolve_app_request({"prompt": prompt, "app": app})
    except ValueError as exc:
        message = f"Invalid app request: {exc}"
        _emit(progress, "generate", "failed", message=message)
        return {"status": "failed", "verified": False, "message": message, "plan": plan}

    try:
        contract = resolve_generation_contract({"prompt": prompt, "scene": scene, "app": app})
    except ValueError:
        message = ("Invalid 3D request: choose a supported scene and supply a valid local "
                   "GLB/GLTF model for product_viewer.")
        _emit(progress, "generate", "failed", message=message)
        return {"status": "failed", "verified": False, "message": message, "plan": plan}

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

    generated = FullStackUltraEngine().generate_project(
        str(destination),
        prompt=plan["prompt"],
        brand_name=plan["name"],
        industry=plan["industry"],
        generation_contract=contract,
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

    package_json = json.loads((frontend / "package.json").read_text(encoding="utf-8"))
    modules = frontend / "node_modules"
    missing = [name for name in (package_json.get("dependencies") or {})
               if not (modules / name.replace("/", os.sep)).exists()]
    steps: Dict[str, Any] = {}
    # An existing node_modules is not proof the manifest is installed: reuse after
    # adding a scene leaves three/@react-three missing and the build fails.
    if install and (not modules.is_dir() or missing):
        steps["install"] = _run([_npm(), "install", "--no-audit", "--no-fund"], frontend, timeout=timeout)
        steps["install"]["missing_before"] = missing[:20]
        if not steps["install"]["ok"]:
            return {"ok": False, "dist": "", "steps": steps,
                    "message": "npm install failed", "stderr": steps["install"]["stderr_tail"]}

    if "build" not in (package_json.get("scripts") or {}):
        return {"ok": False, "dist": "", "steps": steps, "message": "frontend package has no build script"}
    build_env = {"VITE_API_URL": api_url} if api_url else None
    steps["build"] = _run([_npm(), "run", "build"], frontend, timeout=timeout, env=build_env)
    steps["build"]["api_url"] = api_url or ""
    repairs: list = []
    used: list = []
    while not steps["build"]["ok"] and len(repairs) < nbr.MAX_SWAP_ATTEMPTS:
        fix = nbr.repair(frontend, steps["build"]["stderr_tail"], repo_root=_repo_root(), exclude=used)
        if not fix["repaired"]:
            break
        used.append(Path(fix["source"]))
        repairs.append(fix)
        agent_logger.warning("build: native binary blocked by Windows policy — restored %s and retrying",
                             fix["blocked_path"])
        steps["build"] = _run([_npm(), "run", "build"], frontend, timeout=timeout, env=build_env)
        steps["build"]["api_url"] = api_url or ""
    dist = frontend / "dist"
    notes = [f"Windows App Control refused {fix['blocked_path']} v{fix['blocked_version']} from a "
             f"fresh install; restored the copy this machine already accepts (v{fix['source_version']}) "
             f"and re-ran the build — a machine policy, not a defect in the generated project."
             for fix in repairs]
    extra = {"warnings": notes} if notes else {}
    if not steps["build"]["ok"]:
        return {"ok": False, "dist": str(dist), "steps": steps, "message": "npm run build failed",
                "stderr": steps["build"]["stderr_tail"], "environment_repairs": repairs, **extra}
    if not (dist / "index.html").is_file():
        return {"ok": False, "dist": str(dist), "steps": steps,
                "message": "build finished but dist/index.html is missing",
                "environment_repairs": repairs, **extra}
    return {"ok": True, "dist": str(dist), "steps": steps, "environment_repairs": repairs, **extra}


def _backend_test_files(backend: Path) -> list:
    """Test files the project itself owns — a dependency's suite is not evidence."""
    found = []
    for pattern in ("test/**/*.test.js", "tests/**/*.test.js", "__tests__/**/*.test.js", "*.test.js"):
        found.extend(path for path in backend.glob(pattern) if "node_modules" not in path.parts)
    return found


def test_backend(project_dir: str, timeout: int = 300) -> Dict[str, Any]:
    """Run the generated backend tests. A project without tests is a failure here,
    because a deploy gate that cannot see tests is not a gate."""
    backend = Path(project_dir) / "backend"
    if not (backend / "package.json").is_file():
        return {"ok": True, "skipped": "no backend"}
    package = json.loads((backend / "package.json").read_text(encoding="utf-8"))
    if "test" not in (package.get("scripts") or {}):
        return {"ok": False, "message": "backend package.json has no test script"}
    if not _backend_test_files(backend):
        return {"ok": False, "message": "backend has no test files, so `npm test` would prove nothing"}

    steps: Dict[str, Any] = {}
    if not (backend / "node_modules").is_dir():
        # Nothing that imports sequelize can run without these, and the Neon runner shells
        # out to node in this directory — an uninstalled backend silently tests nothing.
        steps["install"] = _run([_npm(), "install", "--no-audit", "--no-fund"], backend,
                                timeout=max(timeout, 900))
        if not steps["install"]["ok"]:
            return {"ok": False, "steps": steps, "cwd": str(backend),
                    "message": "npm install failed in backend/, so its tests cannot run",
                    "stderr": steps["install"]["stderr_tail"]}

    result = _run([_npm(), "test"], backend, timeout=timeout)
    return {**result, "command": "npm test", "cwd": str(backend), "steps": steps}


def run_qa(project_dir: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    try:
        from agent.extensions.browser_qa import evidence_passes, run_browser_qa

        qa = run_browser_qa(str(project_dir), base_url=base_url)
        passed = evidence_passes(qa)
        failures = list(qa.get("failures") or [])[:20]
        return {
            "ok": passed,
            "status": qa.get("status") if passed else "failed",
            "measurement_status": qa.get("status"),
            "results": qa.get("results") or [],
            "failures": failures,
            "report_path": qa.get("report_path"),
            "evidence": qa.get("evidence") or {},
            "scene": qa.get("scene"),
            "pwa": qa.get("pwa"),
            "requested_pwa": qa.get("requested_pwa", False),
            "message": "" if passed else "browser QA did not pass: " +
                       ("; ".join(str(f) for f in failures[:3]) or "incomplete evidence"),
        }
    except Exception as exc:
        return {"ok": False, "status": "failed",
                "message": f"browser QA crashed ({type(exc).__name__})"}


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
    """Run only the contract-requested surfaces, with backend and delivery gates."""
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
    try:
        app_contract = read_app_contract(str(project))
    except ValueError as exc:
        report.update(status="failed", message=str(exc), failures=[str(exc)])
        return _write_report(project, report_dir, report)

    web_surface = app_contract.get("web", "website") if app_contract else "website"
    web_requested = web_surface != "none"
    pwa_requested = bool(app_contract and app_contract.get("pwa"))
    mobile_request = app_contract.get("mobile") if app_contract else None
    report["requested_surfaces"] = {
        "web": web_surface,
        "pwa": pwa_requested,
        "mobile": mobile_request,
    }
    report["mobile_tier"] = "not_requested" if not mobile_request else "not_run"
    skipped_surfaces = {}
    if not web_requested:
        skipped_surfaces.update({
            "web_build": "web surface is none in app-contract.json",
            "browser_qa": "web surface is none in app-contract.json",
            "frontend_deploy": "web surface is none in app-contract.json",
        })
    if not pwa_requested:
        skipped_surfaces["pwa"] = "PWA was not requested"
    if not mobile_request:
        skipped_surfaces["mobile"] = "mobile was not requested"
    report["skipped_surfaces"] = skipped_surfaces

    def mark_unrun_surfaces(reason: str) -> None:
        if pwa_requested and "pwa" not in report["stages"]:
            report["stages"]["pwa"] = {"status": "skipped", "reason": reason}
            skipped_surfaces["pwa"] = reason
        if mobile_request:
            for stage in ("mobile_export", "mobile_apk", "mobile_emulator"):
                report["stages"].setdefault(
                    stage, {"status": "skipped", "reason": reason}
                )
            skipped_surfaces["mobile"] = reason

    # 1 — build -----------------------------------------------------------------
    build = {}
    if web_requested:
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
            mark_unrun_surfaces("web build failed")
            report.update(status="failed", message=build.get("message", "build failed"),
                          elapsed_ms=int((time.perf_counter() - started) * 1000))
            return _write_report(project, report_dir, report)
    else:
        _emit(progress, "build", "skipped", reason=skipped_surfaces["web_build"])

    # 2 — backend tests ---------------------------------------------------------
    _emit(progress, "backend_tests", "running")
    backend = test_backend(str(project))
    report["stages"]["backend_tests"] = backend
    _emit(progress, "backend_tests", "done" if backend.get("ok") else "failed")
    if not backend.get("ok"):
        mark_unrun_surfaces("backend tests failed")
        report.update(status="failed", message=backend.get("message", "backend tests failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 3 — QA --------------------------------------------------------------------
    qa = {"ok": True, "status": "skipped", "reason": skipped_surfaces.get("browser_qa", "")}
    if web_requested:
        _emit(progress, "qa", "running")
        qa = run_qa(str(project))
        report["stages"]["qa"] = qa
        _emit(progress, "qa", "done" if qa.get("ok") else "failed", detail=qa.get("status"))
    else:
        _emit(progress, "qa", "skipped", reason=skipped_surfaces["browser_qa"])

    if pwa_requested:
        pwa = qa.get("pwa")
        if not isinstance(pwa, dict):
            pwa = {"ok": False, "status": "not-proven",
                   "message": "requested PWA evidence is missing"}
        else:
            pwa = dict(pwa)
            pwa.setdefault("status", "passed" if pwa.get("ok") is True else "failed")
        report["stages"]["pwa"] = pwa
        _emit(progress, "pwa", "done" if pwa.get("ok") is True else "failed",
              message=pwa.get("message"))

    if web_requested and not qa.get("ok") and not allow_qa_fail:
        mark_unrun_surfaces("browser QA failed")
        report.update(status="failed", message=qa.get("message", "QA failed"),
                      elapsed_ms=int((time.perf_counter() - started) * 1000))
        return _write_report(project, report_dir, report)

    # 4 — full-stack hosting: database → API → frontend --------------------------
    backend_present = (project / "backend" / "package.json").is_file()
    database_stage: Dict[str, Any] = {"status": "skipped", "reason": "this project has no backend/"}
    api_stage: Dict[str, Any] = {"status": "skipped", "reason": "this project has no backend/"}
    handshake: Dict[str, Any] = {"status": "skipped", "reason": "no hosted API to prove"}
    database_url = ""
    auto_host = platform != "none" and backend_present and not api_url
    if auto_host:
        database_stage, database_url = _host_database(project, progress)
        if database_url:
            api_stage = _host_api(project, database_url, progress)
            if api_stage.get("url"):
                api_url = api_stage["url"]
        else:
            api_stage = {"status": "blocked",
                         "message": database_stage.get("message", "no database, so no API host")}

    baked = str((((build.get("steps") or {}).get("build") or {}).get("api_url")) or "")
    if web_requested and api_url and api_url != baked:
        # Stage 1 built before the API origin existed. Hosts that publish the local dist
        # (Netlify, Pages, Railway) would ship a bundle still calling localhost, so the
        # frontend is rebuilt against the origin it is about to be deployed with.
        _emit(progress, "build", "running", api_url=api_url, reason="baking the hosted API origin")
        build = build_project(str(project), install=False, api_url=api_url)
        report["stages"]["build"] = build
        _emit(progress, "build", "done" if build.get("ok") else "failed",
              dist=build.get("dist"), message=build.get("message"))
        if not build.get("ok"):
            mark_unrun_surfaces("rebuild with the hosted API origin failed")
            report.update(status="failed",
                          message="rebuild with the hosted API origin failed: "
                                  + str(build.get("message", "")),
                          elapsed_ms=int((time.perf_counter() - started) * 1000))
            return _write_report(project, report_dir, report)

    deployment: Dict[str, Any] = {"status": "skipped", "verified": False}
    if platform != "none" and web_requested:
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
                               "the factory hosts it with deploy_backend() once a database "
                               "server is configured (FACTORY_DATABASE_TEMPLATE_URL, or the "
                               "legacy NEON_TEMPLATE_DATABASE_URL), or pass --factory-api-url "
                               "for an API hosted elsewhere",
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

    if (web_requested and auto_host and database_url and api_stage.get("url")
            and deployment.get("url") and api_health_target(api_url, api_health)):
        # The site now has a real origin, so lock the API to it and prove the
        # whole path end to end: health, then an actual form submission.
        api_stage["cors"] = _lock_api_cors(project, database_url, deployment["url"], progress)
        locked = str(api_stage["cors"].get("url") or "")
        if locked and locked.rstrip("/") != api_url.rstrip("/"):
            # The bundle already shipped calling `api_url`. If the CORS pass found a
            # different production domain, the shipped origin is stale and the client's
            # forms would post somewhere else — say so instead of delivering it.
            api_stage["cors"]["drift"] = f"locked to {locked}, bundle calls {api_url}"
        handshake = _prove_api(api_url, api_health_target(api_url, api_health), progress)
    elif api_url and backend_present:
        handshake = _prove_api(api_url, api_health_target(api_url, api_health), progress)

    if api_url and backend_present and handshake.get("ok") is True \
            and api_stage.get("status") == "skipped":
        api_stage = {
            "status": "live",
            "url": api_url,
            "health_url": api_health_target(api_url, api_health),
            "verified": True,
            "source": "provided",
        }
    report["stages"]["database"] = database_stage
    report["stages"]["api"] = api_stage
    report["stages"]["handshake"] = handshake
    hosted_database = bool(
        database_url
        and database_stage.get("status") in {"created", "reused"}
        and database_stage.get("ok") is not False
    )
    hosted_api = bool(
        api_stage.get("status") == "live"
        and api_stage.get("verified") is not False
        and api_stage.get("url")
    )
    full_stack_verified = bool(hosted_database and hosted_api and handshake.get("ok") is True)
    if not web_requested:
        deployment = {
            "status": "api-only",
            "url": api_url or api_stage.get("url", ""),
            "verified": full_stack_verified,
            "api_deployed": hosted_api,
            "reason": "web surface is none in app-contract.json",
        }
    report["stages"]["deploy"] = {
        key: deployment.get(key)
        for key in ("status", "url", "platform", "verified", "deployment_id", "message",
                    "verification", "api_deployed", "api_env", "api_health_url", "reason")
        if key in deployment
    }
    if deployment.get("status") == "api-only":
        _emit(progress, "deploy", "done" if deployment.get("verified") else "partial",
              url=deployment.get("url"), verified=deployment.get("verified"),
              reason=deployment.get("reason"))
    elif platform == "none":
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

    live_qa = {"ok": False, "status": "skipped", "reason": "no hosted frontend"}
    if web_requested and platform != "none" and deployment.get("url"):
        _emit(progress, "live_qa", "running")
        live_qa = run_qa(str(project), base_url=deployment["url"])
        _emit(progress, "live_qa", "done" if live_qa.get("ok") else "failed",
              detail=live_qa.get("status"), message=live_qa.get("message"))
    if web_requested:
        report["stages"]["live_qa"] = live_qa

    mobile_failures = []
    if mobile_request:
        from agent import mobile_verify

        _emit(progress, "mobile_export", "running")
        try:
            mobile_export = mobile_verify.export_mobile(str(project))
        except Exception as exc:
            mobile_export = {
                "ok": False,
                "status": "failed",
                "message": f"mobile export raised {type(exc).__name__}",
            }
        if not isinstance(mobile_export, dict):
            mobile_export = {
                "ok": False,
                "status": "failed",
                "message": "mobile export returned invalid evidence",
            }
        report["stages"]["mobile_export"] = mobile_export
        _emit(progress, "mobile_export", "done" if mobile_export.get("ok") else "failed",
              message=mobile_export.get("message"))
        if mobile_export.get("ok") is not True:
            export_error = mobile_export.get("message") or mobile_export.get("status")
            mobile_failures.append(
                f"mobile export failed ({export_error})"
            )

        verification = mobile_request.get("verification", "apk_emulator")
        if verification == "none":
            report["mobile_tier"] = "not_verified"
            report["stages"]["mobile_apk"] = {
                "status": "skipped",
                "reason": "mobile.verification is none",
            }
            report["stages"]["mobile_emulator"] = {
                "status": "skipped",
                "reason": "mobile.verification is none",
            }
            skipped_surfaces["mobile_verification"] = "mobile.verification is none"
            mobile_failures.append(
                "mobile verification was not requested; this run cannot be delivered"
            )
        elif mobile_export.get("ok") is not True:
            report["stages"]["mobile_apk"] = {
                "status": "skipped",
                "reason": "mobile export did not pass",
            }
            report["stages"]["mobile_emulator"] = {
                "status": "skipped",
                "reason": "mobile export did not pass",
            }
            report["mobile_tier"] = "failed"
        elif mobile_export.get("ok") is True:
            platforms = mobile_request.get("platforms", []) or []
            unsupported_platforms = [
                platform_name for platform_name in platforms
                if platform_name != "android"
            ]
            if unsupported_platforms:
                report["stages"]["mobile_ios"] = {
                    "status": "not_measured",
                    "platforms": unsupported_platforms,
                    "reason": (
                        "iOS export is checked, but signing, store submission, and "
                        "iOS device verification are not delivered by this pipeline"
                    ),
                }
            no_android = "android" not in platforms
            toolchain = {"ready": False, "missing": []}
            if not no_android:
                try:
                    from agent.android_toolchain import toolchain as resolve_toolchain

                    resolved = resolve_toolchain()
                except Exception as exc:
                    resolved = {
                        "ready": False,
                        "missing": [f"toolchain check raised {type(exc).__name__}"],
                    }
                if isinstance(resolved, dict):
                    toolchain = resolved
                else:
                    toolchain = {
                        "ready": False,
                        "missing": ["invalid toolchain evidence"],
                    }

            if no_android or not toolchain.get("ready"):
                if no_android:
                    message = (
                        "no Android target was requested, so APK and emulator "
                        "verification have nothing to build or install"
                    )
                else:
                    detail = ", ".join(
                        str(item) for item in toolchain.get("missing") or []
                    ) or ", ".join(
                        _TOOLCHAIN_LABELS[name]
                        for name in _TOOLCHAIN_PATH_KEYS
                        if not toolchain.get(name)
                    )
                    message = "Android toolchain is not ready" + (
                        f": {detail}" if detail else ""
                    )
                    # A named gap is the only way a blocked delivery turns into a
                    # fixed machine, so the remedy rides along with the label.
                    remedy = str(toolchain.get("cmake_gap") or "").strip()
                    if remedy:
                        message += f" ({remedy})"
                report["stages"]["mobile_apk"] = {
                    "ok": False,
                    "status": "blocked",
                    "message": message,
                    "toolchain": toolchain,
                }
                report["stages"]["mobile_emulator"] = {
                    "status": "skipped",
                    "reason": message,
                }
                report["mobile_tier"] = "blocked"
                skipped_surfaces["mobile_verification"] = message
                mobile_failures.append(message)
            else:
                tier = "full_stack" if full_stack_verified else "app_runs"
                mobile_api_url = api_url or api_stage.get("url", "")
                fixture_server = None
                if tier == "app_runs":
                    try:
                        from agent.mobile_fixture_api import start_fixture_api

                        fixture_server, fixture_base_url = start_fixture_api(port=0)
                        mobile_api_url = _emulator_fixture_api_url(fixture_base_url)
                        fixture_health = _probe_mobile_fixture_api(fixture_base_url)
                        health_path = report_dir / "mobile" / "health.json"
                        if fixture_health.get("ok"):
                            health_path.parent.mkdir(parents=True, exist_ok=True)
                            health_path.write_text(
                                json.dumps({
                                    "status": "ok",
                                    "fixture": True,
                                    "url": fixture_health["url"],
                                }, indent=2) + "\n",
                                encoding="utf-8",
                            )
                            fixture_health["report_path"] = str(health_path)
                        report["stages"]["mobile_fixture_api"] = fixture_health
                        if fixture_health.get("ok") is not True:
                            mobile_api_url = ""
                            report["mobile_tier"] = "blocked"
                            mobile_failures.append(
                                fixture_health.get("message", "fixture API health check failed")
                            )
                        elif not health_path.is_file():
                            mobile_api_url = ""
                            report["stages"]["mobile_fixture_api"] = {
                                **fixture_health,
                                "ok": False,
                                "status": "failed",
                                "message": "fixture API health evidence was not persisted",
                            }
                            report["mobile_tier"] = "blocked"
                            mobile_failures.append(
                                report["stages"]["mobile_fixture_api"]["message"]
                            )
                    except OSError as exc:
                        mobile_api_url = ""
                        report["stages"]["mobile_fixture_api"] = {
                            "ok": False,
                            "status": "failed",
                            "message": f"fixture API health evidence failed ({type(exc).__name__})",
                        }
                        report["mobile_tier"] = "blocked"
                        mobile_failures.append(
                            report["stages"]["mobile_fixture_api"]["message"]
                        )
                    except Exception as exc:
                        mobile_api_url = ""
                        report["stages"]["mobile_apk"] = {
                            "ok": False,
                            "status": "blocked",
                            "message": f"fixture API failed to start ({type(exc).__name__})",
                        }
                        report["stages"]["mobile_emulator"] = {
                            "status": "skipped",
                            "reason": "fixture API was unavailable",
                        }
                        report["mobile_tier"] = "blocked"
                        mobile_failures.append(report["stages"]["mobile_apk"]["message"])

                if tier == "app_runs" and not mobile_api_url:
                    fixture_failure = (
                        report.get("stages", {}).get("mobile_fixture_api") or {}
                    ).get("message", "fixture API was unavailable")
                    report["stages"].setdefault("mobile_apk", {
                        "ok": False,
                        "status": "blocked",
                        "message": fixture_failure,
                    })
                    report["stages"].setdefault("mobile_emulator", {
                        "status": "skipped",
                        "reason": fixture_failure,
                    })

                if mobile_api_url:
                    apk_result = {}
                    try:
                        apk_result = mobile_verify.build_apk(
                            str(project),
                            toolchain,
                            api_url=mobile_api_url,
                            evidence_dir=str(report_dir / "mobile"),
                        )
                    except Exception as exc:
                        apk_result = {
                            "ok": False,
                            "status": "failed",
                            "message": f"APK build raised {type(exc).__name__}",
                        }
                    if not isinstance(apk_result, dict):
                        apk_result = {
                            "ok": False,
                            "status": "failed",
                            "message": "APK build returned invalid evidence",
                        }
                    report["stages"]["mobile_apk"] = apk_result
                    _emit(progress, "mobile_apk",
                          "done" if apk_result.get("ok") is True and apk_result.get("apk")
                          else ("failed" if apk_result.get("ok") is True
                                else apk_result.get("status", "failed")),
                          message=apk_result.get("message") or (
                              "APK build returned no APK path"
                              if apk_result.get("ok") is True and not apk_result.get("apk")
                              else None
                          ))
                    if apk_result.get("ok") is not True:
                        mobile_failures.append(
                            "mobile APK build failed "
                            f"({apk_result.get('message') or apk_result.get('status')})"
                        )
                        report["stages"]["mobile_emulator"] = {
                            "status": "skipped",
                            "reason": "mobile APK build did not pass",
                        }
                        report["mobile_tier"] = "failed"
                    elif not apk_result.get("apk"):
                        apk_result["ok"] = False
                        apk_result["status"] = "failed"
                        apk_result["message"] = "APK build returned no APK path"
                        mobile_failures.append(apk_result["message"])
                        report["stages"]["mobile_apk"] = apk_result
                        report["stages"]["mobile_emulator"] = {
                            "status": "skipped",
                            "reason": "APK build returned no APK path",
                        }
                        report["mobile_tier"] = "failed"
                    else:
                        try:
                            emulator = mobile_verify.verify_emulator(
                                str(project),
                                apk_result.get("apk", ""),
                                toolchain=toolchain,
                                api_url=mobile_api_url,
                                tier=tier,
                                evidence_dir=str(report_dir / "mobile"),
                            )
                        except Exception as exc:
                            emulator = {
                                "ok": False,
                                "status": "failed",
                                "message": (
                                    "mobile emulator verification raised "
                                    f"{type(exc).__name__}"
                                ),
                            }
                        if not isinstance(emulator, dict):
                            emulator = {
                                "ok": False,
                                "status": "failed",
                                "message": "mobile emulator returned invalid evidence",
                            }
                        else:
                            emulator = dict(emulator)
                        reported_tier = emulator.get("tier")
                        emulator["tier"] = tier
                        if emulator.get("ok") is True and reported_tier != tier:
                            if reported_tier:
                                emulator["reported_tier"] = reported_tier
                            emulator["ok"] = False
                            emulator["message"] = (
                                f"emulator reported tier "
                                f"{reported_tier or 'missing'}, expected {tier}"
                            )
                        report["stages"]["mobile_emulator"] = emulator
                        _emit(progress, "mobile_emulator",
                              "done" if emulator.get("ok") is True else "failed",
                              tier=tier, message=emulator.get("message"))
                        if emulator.get("ok") is not True:
                            mobile_failures.append(
                                "mobile emulator verification failed "
                                f"({emulator.get('message') or emulator.get('status')})"
                            )
                            report["mobile_tier"] = "app_runs" if tier == "app_runs" else "failed"
                        else:
                            report["mobile_tier"] = tier
                            if tier != "full_stack":
                                mobile_failures.append(
                                    "mobile verification only proved app_runs against a fixture API"
                                )
                try:
                    if fixture_server is not None:
                        fixture_server.shutdown()
                except Exception as exc:
                    mobile_failures.append(
                        f"fixture API shutdown failed ({type(exc).__name__})"
                    )
                finally:
                    if fixture_server is not None:
                        try:
                            fixture_server.server_close()
                        except Exception as exc:
                            mobile_failures.append(
                                f"fixture API close failed ({type(exc).__name__})"
                            )

    # 5 — demo video ------------------------------------------------------------
    if video and not web_requested:
        # A mobile-app delivery has no public page to film; recording the API host
        # would produce a "demo" of a health endpoint and nothing else.
        report["stages"]["video"] = {
            "status": "skipped",
            "verified": False,
            "reason": "no web surface to film; app-contract.json requests mobile only",
        }
        skipped_surfaces["video"] = "no web surface to film"
        _emit(progress, "video", "skipped",
              reason="app-contract.json requests no web surface")
    elif video:
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
    if not web_requested and platform == "none":
        failures.append("API-only app delivery has no hosted API, database, or frontend")
    if backend_present and platform != "none":
        # A client demo needs all three tiers live: a page that loads but cannot
        # save is not a product, and that is exactly what used to be shipped.
        if auto_host:
            if database_stage.get("status") == "schema-incomplete":
                # The database exists and the API could still boot against an
                # empty schema — which is exactly the "live" claim that used to be
                # printed while every form 500'd on a missing table.
                failures.append("the product's own migrations never applied, so its database "
                                f"has no schema ({database_stage.get('message', '')})")
            elif database_stage.get("status") in {"blocked", "failed"}:
                failures.append(f"database not provisioned ({database_stage.get('status')}: "
                                f"{database_stage.get('message', '')})")
            if api_stage.get("status") != "live":
                hint = ("" if api_stage.get("status") != "deployed-protected" else
                        " — the API answers with a Vercel login page; the automatic "
                        "`vercel project protection disable --sso` did not take effect, so turn "
                        "Deployment Protection off for "
                        f"`{api_stage.get('project_name', 'the API project')}` in the Vercel "
                        "dashboard")
                failures.append(f"API not live ({api_stage.get('status')}: "
                                f"{api_stage.get('message', '')}){hint}")
            elif api_stage.get("cors", {}).get("drift"):
                failures.append("the API moved to a different domain after the bundle was "
                                f"built ({api_stage['cors']['drift']})")
        elif not deployment.get("api_deployed"):
            failures.append("the API origin the deployed frontend calls did not pass its health check")
        if not handshake.get("ok"):
            # Name the proof that failed, not just "the API is broken": a database
            # that cannot be reached, a route that 500s, a missing tenant check and
            # a dead change feed are four different things for someone to fix.
            first_failed = next(
                (key for key in ("health", "write", "surface", "feed")
                 if not (handshake.get(key) or {}).get("ok")), "health")
            failures.append(
                f"{_PROOF_LABELS[first_failed]} ({(handshake.get(first_failed) or {}).get('status')}: "
                f"{'; '.join(str(f) for f in handshake.get('failures') or [])})")
    if pwa_requested and report["stages"].get("pwa", {}).get("ok") is not True:
        pwa = report["stages"].get("pwa") or {}
        detail = "; ".join(str(item) for item in (pwa.get("failures") or [])[:3])
        failures.append("PWA verification failed: " +
                        (detail or pwa.get("message") or "incomplete PWA evidence"))
    failures.extend(mobile_failures)
    # An app-only run records `video` as skipped, so this gate must not read that
    # skip as a failure — otherwise every mobile delivery caps at `partial`.
    if video and web_requested and not report["stages"].get("video", {}).get("verified"):
        failures.append("demo video not verified")
    if web_requested and not qa.get("ok"):
        failures.append("QA failed (allowed by caller)")
    if web_requested and platform != "none" and not live_qa.get("ok"):
        detail = "; ".join(str(item) for item in (live_qa.get("failures") or [])[:3])
        failures.append("live browser QA failed: " +
                        (detail or live_qa.get("message") or "no complete hosted evidence"))

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


def _handoff_lines(report: Dict[str, Any]) -> list:
    """The client-facing block: every URL, plus what was never proven.

    A delivery report is handed to a buyer, so it names the live frontend, the
    live API, the health endpoint to paste into a browser, the database the
    product owns, and the demo file. Anything the run could not prove is listed
    explicitly instead of being silently omitted.
    """
    stages = report.get("stages") or {}
    deploy = stages.get("deploy") or {}
    api = stages.get("api") or {}
    database = stages.get("database") or {}
    handshake = stages.get("handshake") or {}
    video = stages.get("video") or {}
    mobile_apk = stages.get("mobile_apk") or {}
    mobile_emulator = stages.get("mobile_emulator") or {}
    surfaces = report.get("requested_surfaces") or {}

    lines = ["## Client handoff", ""]
    rows = [
        ("Frontend (live)", deploy.get("url") if surfaces.get("web") != "none" else None),
        ("API (live)", api.get("url") or deploy.get("api_health_url")),
        ("API health", api.get("health_url")),
        ("Database", f"{database.get('database', '')}@{database.get('host', '')}"
                     if database.get("database") else None),
        ("Demo video", video.get("video")),
        ("Local browser evidence", (stages.get("qa") or {}).get("report_path")),
        ("Hosted browser evidence", (stages.get("live_qa") or {}).get("report_path")),
    ]
    for label, value in rows:
        if value:
            lines.append(f"- **{label}:** `{value}`")
    if surfaces:
        mobile = surfaces.get("mobile")
        requested_mobile = (", ".join(mobile.get("platforms") or [])
                            if isinstance(mobile, dict) else "not requested")
        lines.append(
            f"- **Requested surfaces:** web `{surfaces.get('web', 'website')}`, "
            f"PWA `{'yes' if surfaces.get('pwa') else 'no'}`, mobile `{requested_mobile}`"
        )
    if mobile_apk.get("apk"):
        lines.append(f"- **APK:** `{mobile_apk['apk']}`")
    if mobile_apk.get("sha256"):
        lines.append(f"- **APK SHA-256:** `{mobile_apk['sha256']}`")
    if report.get("mobile_tier") not in (None, "", "not_requested"):
        lines.append(f"- **Mobile verification tier:** `{report['mobile_tier']}`")
    maestro = mobile_emulator.get("maestro")
    if isinstance(maestro, dict) and maestro:
        flow_results = sorted(
            f"{name} {'passed' if (result or {}).get('ok') is True else 'failed'}"
            for name, result in maestro.items()
            if isinstance(result, dict)
        )
        overall = ("passed" if flow_results and all(
            (result or {}).get("ok") is True
            for result in maestro.values() if isinstance(result, dict)
        ) else "failed")
        lines.append(f"- **Maestro result:** `{overall}` ({'; '.join(flow_results)})")
    elif isinstance(maestro, dict):
        lines.append("- **Maestro result:** `no flow evidence produced`")
    elif maestro is not None:
        lines.append(f"- **Maestro result:** `{maestro}`")
    test_account = mobile_emulator.get("test_account")
    if test_account:
        if mobile_emulator.get("tier") == "full_stack":
            lines.append(
                f"- **Test account:** `{test_account}` signed up against the live API. "
                "Its password was never written to this report, so reset it in the app "
                "before signing in; delete the rows it created if you want an empty table."
            )
        else:
            lines.append(
                f"- **Test account:** `{test_account}` signed up against a throwaway "
                "fixture API that this run shut down; it proves the app runs, not the "
                "hosted backend."
            )
    elif surfaces.get("mobile"):
        lines.append("- **Test account:** use app-owner supplied credentials; credentials are not "
                     "stored in this report")
    migrations = database.get("migrations") or {}
    if migrations.get("status") == "applied":
        lines.append(f"- **Schema:** {migrations.get('applied')} migration(s) applied "
                     f"({', '.join(migrations.get('names') or [])}) before the API was deployed")
    elif migrations.get("status") == "uptodate":
        lines.append("- **Schema:** at the head — every migration was already recorded, so "
                     "nothing was re-applied")
    elif migrations.get("status") == "missing":
        lines.append("- **Schema:** this project keeps no `backend/migrations/run.js`, so its "
                     "tables are proven by the live journey below rather than by a migration run")
    if api.get("env", {}).get("published"):
        lines.append(f"- **API runtime variables set:** {', '.join(api['env']['published'])} "
                     "(values are stored on the hosting platform, never in this report)")
    if handshake.get("write", {}).get("id"):
        lines.append(f"- **Form round-trip:** a real inquiry was stored "
                     f"(row `{handshake['write']['id']}`) — delete it before the demo if you "
                     "want an empty inbox")
    surface = handshake.get("surface") or {}
    if surface.get("proven"):
        lines.append(f"- **API surface:** {' → '.join(surface['proven'])} — each answered over "
                     "the live origin, and a second account was proved unable to read the "
                     "first one's rows")
    feed = handshake.get("feed") or {}
    if feed.get("status") == "verified":
        # A sub-millisecond push rounds to 0, and `if latency` then dropped the
        # line entirely — the proof exists, the report just refused to say so.
        latency = int(feed.get("latency_ms") or 0)
        took = f"{latency} ms" if latency else "under 1 ms"
        lines.append(f"- **Live updates:** a write reached an open dashboard in {took} "
                     f"(frames seen: {', '.join(feed.get('events') or [])})")
    scene = (stages.get("live_qa") or {}).get("scene") or {}
    if scene.get("ok"):
        lines.append(
            f"- **3D scene:** rendered in the hosted browser "
            f"({scene.get('frames', 0)} frames, {scene.get('draw_calls', 0)} draw calls; "
            "canvas pixels changed after a rotate action; mobile stayed static until activated)")
    stray = list(surface.get("leftovers") or []) + list(feed.get("leftovers") or [])
    if stray:
        lines.append(f"- **Clean-up owed:** the run could not remove its own probe rows "
                     f"({', '.join(f'`{i}`' for i in stray)}) — delete them before the demo")
    lines.append("- **Secrets:** the signing/encryption keys live in `backend/.env` and on the "
                 "hosting platform. Rotate them if either is shared.")

    not_proven = [f for f in report.get("failures") or []]
    for name in ("qa", "live_qa"):
        stage = stages.get(name) or {}
        if stage.get("status") not in {None, "skipped"} and stage.get("ok") is not True:
            not_proven.extend(f"{name}: {failure}" for failure in (
                stage.get("failures") or [stage.get("message") or "incomplete browser evidence"]
            )[:5])
    if not report.get("verified"):
        not_proven.append("Hosted delivery was not verified.")
    skipped = [name for name, stage in stages.items()
               if stage.get("status") in {"skipped", "blocked"} and name != "video"]
    unmeasured = [name for name, stage in stages.items()
                  if stage.get("status") == "not_measured"]
    skipped_surfaces = report.get("skipped_surfaces") or {}
    lines.append("")
    lines.append("## Not proven")
    if not not_proven and not skipped and not unmeasured and not skipped_surfaces:
        lines.append("Nothing — every stage above was verified against the live deployment.")
    else:
        for failure in not_proven:
            lines.append(f"- not proven: {failure}")
        for name in skipped:
            stage = stages.get(name) or {}
            reason = stage.get("reason") or stage.get("message") or ""
            lines.append(f"- skipped stage: `{name}` ({reason})")
        for name in unmeasured:
            stage = stages.get(name) or {}
            lines.append(f"- not measured: `{name}` "
                         f"({stage.get('reason') or 'this pipeline never measured it'})")
        for surface, reason in skipped_surfaces.items():
            lines.append(f"- skipped surface: `{surface}` ({reason})")
    lines.append("")
    return lines


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
        status = stage.get("status")
        # `skipped` used to fall into the same bucket as `live`, so a stage that
        # proved nothing printed as a pass in the report a buyer reads.
        if status in {"skipped", "not_requested", "not_measured"}:
            verdict = status.upper().replace("_", " ")
        elif status == "api-only":
            verdict = "PASS" if stage.get("verified") is True else "FAIL/UNVERIFIED"
        else:
            ok = stage.get("ok", stage.get("verified", status == "live"))
            verdict = "PASS" if ok else "FAIL/UNVERIFIED"
        lines.append(f"## {stage_name} — {verdict}")
        for key in ("url", "status", "duration_seconds", "resolution", "message", "dist",
                    "database", "host", "health_url", "report_path", "reason"):
            if stage.get(key):
                lines.append(f"- {key}: `{stage[key]}`")
        for failure in (stage.get("failures") or [])[:5]:
            lines.append(f"- failure: {failure}")
        for warning in stage.get("warnings") or []:
            lines.append(f"- warning: {warning}")
        lines.append("")
    for failure in report.get("failures") or []:
        lines.append(f"- failure: {failure}")
    lines.append("")
    lines.extend(_handoff_lines(report))
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
