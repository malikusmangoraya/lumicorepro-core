"""Deployment connector — turns a finished generated project into a live URL.

Supports two levels:
  1. Real deploy: when a platform token is configured (VERCEL_TOKEN, NETLIFY_AUTH_TOKEN,
     RAILWAY_TOKEN) we call the platform REST API and return a production URL.
  2. Guide mode: otherwise we return the generated deploy configs + the exact
     commands the user must run (works for Vercel/Netlify/Railway).
Every deployment is persisted to platform.db.deployments via AccountStore.
"""
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.logger import agent_logger

try:  # works both as `agent.deploy_engine` and as a direct script
    from agent.gh_token import clean_token, is_placeholder
    from agent.live_verify import expected_routes, verify_api_health, verify_site
except ImportError:
    from gh_token import clean_token, is_placeholder
    from live_verify import expected_routes, verify_api_health, verify_site


def _which_git() -> str:
    git = shutil.which("git")
    return git or ""

SUPPORTED_PLATFORMS: List[str] = ["vercel", "netlify", "railway", "github-pages"]

# Where a custom domain should point (DNS records to create)
DNS_TARGETS = {
    "vercel": {"type": "CNAME", "host": "@", "value": "cname.vercel-dns.com", "ttl": "Auto"},
    "netlify": {"type": "CNAME", "host": "www", "value": "your-site.netlify.app", "ttl": "Auto"},
    "railway": {"type": "CNAME", "host": "@", "value": "your-service.up.railway.app", "ttl": "Auto"},
    "vps": {"type": "A", "host": "@", "value": "YOUR_SERVER_IP", "ttl": "3600"},
}


def domain_guide(platform: str, domain: str) -> Dict[str, Any]:
    """Return the DNS records + platform steps needed to attach a custom domain.

    Platform must be one of vercel/netlify/railway/vps. Returns a ready-to-follow
    checklist so the client (or the owner) can complete DNS without hunting docs.
    """
    platform = (platform or "").strip().lower()
    domain = (domain or "").strip().lower().lstrip("www.")
    if not domain or not "." in domain:
        return {"status": "failed", "message": "A valid domain is required (e.g. mybrand.com)"}
    target = DNS_TARGETS.get("vps" if platform == "vps" else platform, DNS_TARGETS["vps"])

    steps = [
        f"1. Log in to your domain registrar/DNS provider (GoDaddy, Cloudflare, Namecheap, etc.).",
        f"2. Add a new record: type `{target['type']}`, host `{target['host']}`, value `{target['value']}` (TTL {target['ttl']}).",
        f"3. Add a secondary record for `www`: type `CNAME`, host `www`, value `{domain}`.",
    ]
    if platform == "vercel":
        steps += [
            "4. In Vercel → Project → Settings → Domains, click 'Add', enter the domain, and confirm.",
            "5. DNS propagation can take 5 minutes to 48 hours. Vercel validates automatically.",
        ]
    elif platform == "netlify":
        steps += [
            "4. In Netlify → Site → Domain management → Add custom domain, then set the www CNAME above to your *.netlify.app URL.",
            "5. Once verified, set your custom domain as primary.",
        ]
    elif platform == "railway":
        steps += [
            "4. In Railway → Settings → Networking → Custom domain, add your domain.",
            "5. Railway provisions an HTTPS cert automatically once DNS resolves.",
        ]
    else:
        steps += [
            "4. Point an A record at your VPS public IP (replace YOUR_SERVER_IP).",
            "5. On the server, add the virtual host block below, reload Nginx, and issue a Let's Encrypt cert.",
        ]

    nginx_block = ""
    if platform == "vps":
        nginx_block = f"""# /etc/nginx/sites-available/{domain.replace('.', '-')}
server {{
    listen 80;
    server_name {domain} www.{domain};

    root /var/www/{domain}/frontend/dist;
    index index.html;

    location /api/ {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}"""

    return {
        "status": "ok",
        "platform": platform,
        "domain": domain,
        "records": [{"type": target["type"], "host": target["host"], "value": target["value"], "ttl": target["ttl"]}],
        "steps": steps,
        "nginx_block": nginx_block,
    }


def add_domain(platform: str, domain: str, project_dir: Optional[str] = None) -> Dict[str, Any]:
    """Attach a custom domain via the platform API when a token exists, else guide.

    Currently automates Vercel (domains API). Netlify/Railway/VPS fall back to a
    precise DNS guide so the user never has to search for the steps.
    """
    platform = (platform or "").strip().lower()
    domain = (domain or "").strip().lower().lstrip("www.")
    guide = domain_guide(platform, domain)
    if guide.get("status") != "ok":
        return guide

    if platform == "vercel":
        token = os.getenv("VERCEL_TOKEN", "").strip()
        project = Path(project_dir).name if project_dir else ""
        if token and not token.startswith("your_"):
            try:
                req = urllib.request.Request(
                    "https://api.vercel.com/v10/projects/{}/domains".format(project),
                    method="POST",
                    data=json.dumps({"name": domain}),
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    payload = json.loads(resp.read().decode())
                return {
                    "status": "live",
                    "platform": platform,
                    "domain": domain,
                    "verification": payload,
                    "message": f"Domain {domain} added to project {project}. Finish in the Vercel dashboard if verification is pending.",
                }
            except Exception as exc:
                agent_logger.warning(f"Vercel add-domain failed: {exc}")
                return {**guide, "status": "guide", "message": f"API call failed ({exc}) — follow the DNS steps below."}
        return {**guide, "status": "guide", "message": "VERCEL_TOKEN not set — follow these steps to connect your domain manually."}

    return {
        **guide,
        "status": "guide",
        "message": f"Attach your domain by following the DNS steps below." if platform != "vps"
        else "Connect your domain to your VPS with the records and Nginx block below.",
    }


def _find_index(project_dir: str) -> Optional[str]:
    """Locate the built/index html to attach to a deploy payload."""
    candidates = [
        Path(project_dir) / "frontend" / "dist" / "index.html",
        Path(project_dir) / "frontend" / "public" / "index.html",
        Path(project_dir) / "index.html",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def _read_file(path: Optional[str], default: str = "") -> str:
    if not path:
        return default
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return default


def _vercel_inline_files(project_dir: str) -> List[Dict[str, str]]:
    """Collect a flat static subset of ``project_dir`` for the v13 inline API."""
    files: List[Dict[str, str]] = []
    base = Path(project_dir)
    limit, max_bytes = 40, 3 * 1024 * 1024
    for path in sorted(base.rglob("*")):
        if len(files) >= limit:
            break
        if not path.is_file() or path.stat().st_size > max_bytes // limit:
            continue
        if any(part in {".git", "node_modules", "__pycache__", ".venv"} for part in path.parts):
            continue
        rel = path.relative_to(base).as_posix()
        try:
            files.append({"file": rel, "data": path.read_text(encoding="utf-8")})
        except (UnicodeDecodeError, OSError):
            continue
    return files


def _vercel_deploy_root(project_dir: str) -> Path:
    """Best deployable directory for a generated project on Vercel.

    Priority: built frontend/dist (static, fastest) -> frontend (zero-config
    Vite build) -> raw project root.
    """
    base = Path(project_dir)
    # Source first: Vercel builds it remotely with the project's own lockfile.
    # Deploying a prebuilt dist inherits the project's stored build command and
    # then fails with "ENOENT package.json" (seen on nimbus-analytics-demo).
    if (base / "frontend" / "package.json").is_file():
        return base / "frontend"
    if (base / "frontend" / "dist" / "index.html").is_file():
        return base / "frontend" / "dist"
    return base


VERCEL_REWRITES = [{"source": "/((?!api/).*)", "destination": "/index.html"}]
VERCEL_ASSET_HEADERS = [
    {"source": "/assets/(.*)",
     "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
]


def _ensure_vercel_spa_config(workdir: Path) -> Optional[str]:
    """Write vercel.json when the project has none.

    Two shapes, because the same directory can be source or output:
      * source (has package.json): let Vercel run the Vite build,
      * prebuilt dist (only index.html): no build command — Vercel failed with
        ENOENT package.json when a build command was configured for a dist.

    A Vite SPA also needs a rewrite from every non-API path to index.html,
    otherwise the deployed site answers 404 for /features, /pricing, … while the
    homepage looks fine. Never overwrites an existing config.
    """
    config_path = workdir / "vercel.json"
    if config_path.is_file():
        return None
    config: Dict[str, Any] = {"rewrites": VERCEL_REWRITES, "headers": VERCEL_ASSET_HEADERS}
    if (workdir / "package.json").is_file():
        config = {
            "framework": "vite",
            "buildCommand": "npm run build",
            "outputDirectory": "dist",
            **config,
        }
    try:
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        ignore_path = workdir / ".vercelignore"
        if not ignore_path.is_file():
            # A 65 MB node_modules upload is not source. Vercel installs from the
            # lockfile; dist is rebuilt from source.
            ignore_path.write_text("node_modules\ndist\n.env*\n", encoding="utf-8")
        return str(config_path)
    except OSError as exc:
        agent_logger.warning(f"vercel deploy config could not be written in {workdir}: {exc}")
        return None


def _vercel_project_name(project_dir: str) -> str:
    """Stable Vercel project name (VERCEL_PROJECT_NAME overrides the folder)."""
    override = os.getenv("VERCEL_PROJECT_NAME", "").strip().lower()
    if override:
        cleaned = re.sub(r"[^a-z0-9-]+", "-", override).strip("-")
        if cleaned:
            return cleaned[:52]
    raw = Path(project_dir).name.lower()
    name = re.sub(r"[^a-z0-9-]+", "-", raw).strip("-")
    return (name or "lumicorepro-site")[:52]


def _vercel_probe(url: str, require_marker: bool = False) -> bool:
    """True when ``url`` serves a real page (200 + title + app shell).

    A bare 200 is not proof: the platform serves login walls and
    "deployment not found" pages as HTML. The marker check stays for shared
    domains that can hold unrelated content.
    """
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "lumicorepro-agent/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200 or "vercel.com/login" in resp.geturl():
                return False
            body = resp.read(120_000).decode("utf-8", "replace")
    except Exception:
        return False
    lowered = body.lower()
    if any(marker.lower() in lowered for marker in (
        "DEPLOYMENT_NOT_FOUND",
        "This deployment cannot be found",
        "Application error: a client-side exception",
    )):
        return False
    if "<title" not in lowered or 'id="root"' not in lowered and "id='root'" not in lowered \
            and 'id="app"' not in lowered and "id='app'" not in lowered:
        return False
    return "built-with-lumicorepro" in lowered if require_marker else True


def _vercel_cli() -> List[str]:
    """Vercel CLI command prefix: installed binary, else npx, else empty."""
    cli = shutil.which("vercel")
    if cli:
        return [cli]
    npx = shutil.which("npx")
    return [npx, "-y", "vercel@latest"] if npx else []


def _vercel_scope_args() -> List[str]:
    """Only pass --scope when the operator named a team; otherwise let the CLI
    use its own default so a generated project is not pinned to this machine."""
    slug = os.getenv("VERCEL_TEAM_SLUG", "").strip()
    return ["--scope", slug] if slug else []


def _run_vercel_env(cmd: List[str], workdir: Path, stdin: str = "",
                    secret: str = "") -> Dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=str(workdir), input=stdin, capture_output=True,
                              text=True, timeout=180, encoding="utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError) as exc:
        # TimeoutExpired echoes its argument list; a credential never travels
        # there, but a value we piped in through stdin can still surface.
        return {"ok": False, "message": _scrub_value(str(exc), secret)}
    tail = _scrub_value(((proc.stderr or "") + (proc.stdout or "")).strip()[-300:], secret)
    return {"ok": proc.returncode == 0, "exit": proc.returncode, "output": tail}


def _ensure_vercel_api_env(workdir: Path, api_url: str) -> Dict[str, Any]:
    """Put VITE_API_URL on the Vercel project before the build runs.

    The generated frontend is rebuilt by Vercel from source, so a VITE_API_URL
    exported only for the local ``npm run build`` never reaches the deployed
    bundle — the site looks live while every form posts to localhost:5000.
    """
    base = _vercel_cli()
    if not base:
        return {"ok": False, "skipped": True, "message": "vercel CLI unavailable"}
    _run_vercel_env([*base, "env", "rm", "VITE_API_URL", "production", "--yes",
                    *_vercel_scope_args()], workdir)
    added = _run_vercel_env([*base, "env", "add", "VITE_API_URL", "production",
                             *_vercel_scope_args()], workdir, stdin=api_url)
    if not added["ok"]:
        added["message"] = f"VITE_API_URL could not be set on the project: {added.get('output','')}"
    return added


def _ensure_vercel_link(workdir: Path, name: str) -> Dict[str, Any]:
    """Create + link the project so ``vercel env`` has a target before deploying."""
    base = _vercel_cli()
    if not base:
        return {"ok": False, "skipped": True, "message": "vercel CLI unavailable"}
    created = _run_vercel_env([*base, "project", "create", name, *_vercel_scope_args()], workdir)
    linked = _run_vercel_env([*base, "link", "--project", name, "--yes",
                              *_vercel_scope_args()], workdir)
    return {"ok": bool(linked["ok"]), "created": bool(created["ok"]),
            "output": linked.get("output", "")}


def _protection_is_off(output: str) -> bool:
    """``ssoProtection`` is gone only when the CLI says null or false."""
    return bool(re.search(r"""ssoProtection"?\s*[:=]\s*(null|false)""", output or "", re.I))


def open_project_for_public_demo(name: str, workdir: Path, token: str = "") -> Dict[str, Any]:
    """Turn off Vercel Authentication on a project the pipeline just created.

    A project made with ``vercel project create`` inherits the team's "Require
    Vercel Authentication for all deployments" default, which answers every
    ``*.vercel.app`` request with a login page instead of the API. Neither a
    health probe nor a client's demo can pass behind that wall, so hosting is
    not finished until the product is publicly reachable.
    """
    base = _vercel_cli()
    if not base or not name:
        return {"ok": False, "skipped": True, "status": "unknown",
                "message": "the vercel CLI is unavailable, so deployment protection is unchanged"}
    cmd = [*base, "project", "protection", "disable", name, "--sso", "--json",
           *_vercel_scope_args()]
    if token:
        cmd.append(f"--token={token}")
    run = _run_vercel_env(cmd, workdir)
    off = _protection_is_off(str(run.get("output", "")))
    return {
        "ok": bool(run.get("ok")) and off,
        "status": "public" if off else "protected",
        "project_name": name,
        "message": ("" if off else str(run.get("output", ""))[-300:] or
                    "the CLI did not confirm that deployment protection is off"),
    }


def _vercel_cli_deploy(project_dir: str, token: str, api_url: str = "") -> Optional[Dict[str, Any]]:
    """Deploy with the real Vercel CLI and verify the production URL.

    Honours an existing ``.vercel/project.json`` (a linked project) instead of
    forcing a derived name, waits for the build (the CLI is synchronous unless
    ``--no-wait`` is passed), then probes the live site with
    :func:`agent.live_verify.verify_site`. ``status: live`` is only returned
    when that verification passes; an existing-but-broken deployment is
    ``deployed-unverified`` with the evidence attached.
    """
    name = _vercel_project_name(project_dir)
    deploy_root = _vercel_deploy_root(project_dir)
    # deploy_root may be frontend/dist, while the link lives in frontend/ (or the
    # project root). The CLI only reads the link from its own cwd, so deploy from
    # the directory that actually holds .vercel/project.json.
    linked_root = next(
        (
            candidate
            for candidate in (deploy_root, deploy_root.parent, Path(project_dir))
            if (candidate / ".vercel" / "project.json").is_file()
        ),
        None,
    )
    linked = linked_root is not None
    workdir = linked_root or deploy_root
    _ensure_vercel_spa_config(workdir)
    api_env: Optional[Dict[str, Any]] = None
    if api_url:
        if not linked:
            api_env = _ensure_vercel_link(workdir, name)
            if api_env.get("ok"):
                linked = True
        if linked:
            api_env = {**(api_env or {}), **_ensure_vercel_api_env(workdir, api_url)}
        else:
            api_env = {**(api_env or {}),
                       "ok": False,
                       "message": "project could not be linked, so VITE_API_URL was not set"}
    cli = shutil.which("vercel")
    npx = shutil.which("npx")
    if cli:
        cmd = [cli, "deploy", ".", "--prod", "-y"]
    elif npx:
        cmd = [npx, "-y", "vercel@latest", "deploy", ".", "--prod", "-y"]
    else:
        return None
    if not linked:
        cmd.extend(["--project", name, "--create-if-missing"])
    if token:
        cmd.extend(["--token", token])
    try:
        proc = subprocess.run(
            cmd, cwd=str(workdir), capture_output=True, text=True,
            timeout=600, encoding="utf-8", errors="replace",
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": "failed", "message": f"vercel CLI failed: {exc}"}
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-600:]
        if "credentials" in tail.lower() or "not logged in" in tail.lower():
            return None
        return {"status": "failed", "message": tail or f"vercel CLI exited {proc.returncode}"}

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    urls = [u.rstrip(",;.)") for u in re.findall(r"https://[^\s\"']+\.vercel\.app", output)]
    urls = list(dict.fromkeys(urls))
    ids = re.findall(r"dpl_[A-Za-z0-9]+", output)
    deployment_id = ids[-1] if ids else ""
    if not urls:
        return {
            "status": "failed",
            "message": "vercel CLI exited 0 but printed no deployment URL",
            "deployment_id": deployment_id,
        }

    team_slug = os.getenv("VERCEL_TEAM_SLUG", "lumicorepro").strip() or "lumicorepro"
    scoped = re.compile(r"-\w+-" + re.escape(team_slug) + r"\.vercel\.app$")
    free = [u for u in urls if not scoped.search(u)]
    auto_team = [u for u in free if u.startswith(f"https://{name}-{team_slug}.vercel.app")]
    canonical = f"https://{name}.vercel.app"
    ordered = list(dict.fromkeys(auto_team + ([canonical] if canonical in urls else []) + free + urls))

    routes = expected_routes(project_dir)
    last_evidence: Optional[Dict[str, Any]] = None
    protection: Optional[Dict[str, Any]] = None
    for candidate in ordered[:4]:
        evidence = verify_site(candidate, routes=routes, timeout=45, poll_interval=2.0,
                               api_origin=api_url)
        last_evidence = evidence
        if evidence.get("verified"):
            return {
                "status": "live",
                "platform": "vercel",
                "url": evidence.get("url") or candidate,
                "project_name": name,
                "deployment_id": deployment_id,
                "api_env": api_env,
                "verification": evidence,
            }

    # Vercel Authentication answers with a login page, which no visitor or probe
    # can get past. It is a project setting, so turn it off and try the site once
    # more before reporting a deployment nobody can demo.
    failures = " ".join((last_evidence or {}).get("failures") or []).lower()
    if "login wall" in failures:
        protection = open_project_for_public_demo(name, workdir, token)
        evidence = verify_site(ordered[0], routes=routes, timeout=90, poll_interval=2.0,
                               api_origin=api_url)
        last_evidence = evidence
        if evidence.get("verified"):
            return {
                "status": "live",
                "platform": "vercel",
                "url": evidence.get("url") or ordered[0],
                "project_name": name,
                "deployment_id": deployment_id,
                "api_env": api_env,
                "protection": protection,
                "verification": evidence,
            }

    return {
        "status": "deployed-unverified",
        "platform": "vercel",
        "url": ordered[0],
        "project_name": name,
        "deployment_id": deployment_id,
        "api_env": api_env,
        "protection": protection,
        "verification": last_evidence,
        "message": "Deployment exists but the live URL did not pass verification",
    }


def _vercel_deploy(project_dir: str, api_url: str = "") -> Dict[str, Any]:
    """Deploy ``project_dir`` to Vercel.

    Order: CLI (logged-in, token-free preferred) -> CLI with token -> v13
    inline-files API (static fallback) -> guide mode. Ensures a *deployed*
    site, never an empty one.
    """
    token = os.getenv("VERCEL_TOKEN", "").strip()
    if token and not token.startswith("your_"):
        via_cli = _vercel_cli_deploy(project_dir, token, api_url)
        if via_cli is not None:
            return via_cli
    via_cli_free = _vercel_cli_deploy(project_dir, "", api_url)  # token-free, logged-in CLI
    if via_cli_free is not None:
        return via_cli_free
    if not token or token.startswith("your_"):
        return {"status": "guide", "message": "VERCEL_TOKEN not set and no logged-in CLI — guide mode"}
    try:
        files = _vercel_inline_files(str(_vercel_deploy_root(project_dir)))
        if not files:
            return {"status": "failed", "message": "Vercel: no deployable files found in project"}
        name = Path(project_dir).name
        req = urllib.request.Request(
            "https://api.vercel.com/v13/deployments",
            method="POST",
            data=json.dumps({"name": name, "target": "production", "files": files}),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
        url = payload.get("url") or ""
        if not url:
            return {"status": "failed", "platform": "vercel", "message": "Vercel API returned no URL"}
        live_url = url if url.startswith("http") else f"https://{url}"
        evidence = verify_site(live_url, routes=expected_routes(project_dir), timeout=60)
        return {
            "status": "live" if evidence.get("verified") else "deployed-unverified",
            "platform": "vercel",
            "url": evidence.get("url") or live_url,
            "deployment_id": payload.get("id") or payload.get("uid", ""),
            "verification": evidence,
        }
    except Exception as exc:
        agent_logger.warning(f"Vercel deploy failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _netlify_deploy(project_dir: str) -> Dict[str, Any]:
    """Deploy the built directory with the Netlify CLI, then verify it.

    The previous implementation POSTed a single index.html to the sites API:
    every JS/CSS asset 404'd on the live site while the connector reported
    "live". A site is a directory, so the deploy must be a directory.
    """
    token = os.getenv("NETLIFY_AUTH_TOKEN", "").strip()
    if not token or token.startswith("your_"):
        return {"status": "guide", "message": "NETLIFY_AUTH_TOKEN not set — guide mode"}
    cli = shutil.which("netlify")
    if not cli:
        return {"status": "guide", "message": "Netlify CLI not installed (npm i -g netlify-cli) — guide mode"}
    root = _vercel_deploy_root(project_dir)
    if not (root / "index.html").is_file() and not (root / "package.json").is_file():
        return {"status": "failed", "message": "No build output (dist/) or frontend/ to deploy"}
    site_id = os.getenv("NETLIFY_SITE_ID", "").strip()
    cmd = [cli, "deploy", "--prod", "--dir", str(root), "--auth", token, "--json"]
    if site_id:
        cmd.extend(["--site", site_id])
    try:
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=600)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": "failed", "message": f"netlify CLI failed: {exc}"}
    if proc.returncode != 0:
        return {"status": "failed", "message": (proc.stderr or proc.stdout).strip()[-600:]}
    url = ""
    try:
        payload = json.loads(proc.stdout[proc.stdout.index("{"):])
        url = payload.get("url") or payload.get("deploy_url") or ""
    except (ValueError, IndexError):
        match = re.search(r"https://[^\s\"]+\.netlify\.app", proc.stdout + proc.stderr)
        url = match.group(0) if match else ""
    if not url:
        return {"status": "deployed-unverified", "platform": "netlify",
                "message": "netlify CLI exited 0 but printed no URL"}
    evidence = verify_site(url, routes=expected_routes(project_dir), timeout=90)
    return {
        "status": "live" if evidence.get("verified") else "deployed-unverified",
        "platform": "netlify",
        "url": evidence.get("url") or url,
        "verification": evidence,
    }


def _railway_deploy(project_dir: str) -> Dict[str, Any]:
    token = os.getenv("RAILWAY_TOKEN", "").strip()
    if not token or token.startswith("your_"):
        return {"status": "guide", "message": "RAILWAY_TOKEN not set — guide mode"}
    cli = shutil.which("railway")
    if not cli:
        return {"status": "guide", "message": "Railway CLI not installed — guide mode"}
    try:
        result = subprocess.run(
            [cli, "up", "--detach"], cwd=project_dir,
            capture_output=True, text=True, timeout=300,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": "failed", "message": f"railway CLI failed: {exc}"}
    if result.returncode != 0:
        return {"status": "failed", "message": (result.stderr or result.stdout)[-600:]}
    url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if not url:
        return {
            "status": "deployed-unverified",
            "platform": "railway",
            "message": "railway up succeeded but RAILWAY_PUBLIC_DOMAIN is not set",
            "output": result.stdout[-1000:],
        }
    evidence = verify_site(url, routes=expected_routes(project_dir), timeout=120)
    return {
        "status": "live" if evidence.get("verified") else "deployed-unverified",
        "platform": "railway",
        "url": evidence.get("url") or url,
        "verification": evidence,
        "output": result.stdout[-1000:],
    }


def _github_pages_deploy(project_dir: str) -> Dict[str, Any]:
    """Free one-click deploy to GitHub Pages (100% free, no external token).

    Real path: needs GITHUB_TOKEN (classic `repo` scope) or `gh` authenticated;
    it creates/uses `{login}/{repo}` on the `gh-pages` branch and enables Pages.
    Guide path: otherwise returns exact commands + the generated workflow.
    """
    dist = Path(project_dir) / "frontend" / "dist"
    static_dist = Path(project_dir) / "dist"
    if (dist / "index.html").is_file():
        build_src = dist
    elif (static_dist / "index.html").is_file():
        build_src = static_dist
    else:
        return {"status": "failed", "message": "No built dist/ found for GitHub Pages."}

    token = clean_token(os.getenv("GITHUB_TOKEN", ""))
    repo = Path(project_dir).name.lower().replace("_", "-")

    if token and not is_placeholder(token):
        try:
            # 1) resolve the authenticated user login
            req = urllib.request.Request(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "lumicorepro-agent"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                login = json.loads(resp.read().decode()).get("login")
            if not login:
                return {"status": "failed", "message": "Could not resolve GitHub login from token."}

            # 2) create the repo if it does not exist yet
            check = urllib.request.Request(
                f"https://api.github.com/repos/{login}/{repo}",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "lumicorepro-agent"},
            )
            exists = True
            try:
                with urllib.request.urlopen(check, timeout=20):
                    pass
            except urllib.error.HTTPError as he:
                exists = he.code != 404
            if not exists:
                create = urllib.request.Request(
                    "https://api.github.com/user/repos",
                    method="POST",
                    data=json.dumps({
                        "name": repo,
                        "description": f"Live preview generated by LumicorePro Agent — {repo}",
                        "private": False,
                    }).encode(),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": "lumicorepro-agent",
                        "Content-Type": "application/json",
                    },
                )
                try:
                    with urllib.request.urlopen(create, timeout=30):
                        pass
                except urllib.error.HTTPError:
                    pass  # already created by a parallel call — continue
                exists = True

            # 3) push frontend/dist as the gh-pages branch
            git = _which_git()
            if not git:
                return {"status": "failed", "message": "git is required for GitHub Pages deploy."}
            tmpdir = Path(tempfile.mkdtemp(prefix="ghpages_"))
            try:
                shutil.copytree(str(build_src), str(tmpdir / "site"), dirs_exist_ok=True)
                remote_url = f"https://x-access-token:{token}@github.com/{login}/{repo}.git"
                for cmd in (
                    ["init", "-b", "gh-pages"],
                    ["add", "-A"],
                    ["-c", "user.email=agent@lumicorepro.app", "-c", "user.name=LumicorePro Agent",
                     "commit", "-m", "deploy(gh-pages): publish site"],
                    ["remote", "add", "origin", remote_url],
                    ["push", "-f", "origin", "gh-pages"],
                ):
                    run = subprocess.run([git] + cmd, cwd=str(tmpdir / "site"), capture_output=True,
                                         text=True, timeout=120)
                    if run.returncode != 0 and "nothing to commit" not in run.stdout:
                        return {"status": "failed", "message": (run.stderr or run.stdout)[-500:]}
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

            # 4) enable GitHub Pages on the gh-pages branch
            enable = urllib.request.Request(
                f"https://api.github.com/repos/{login}/{repo}/pages",
                method="POST",
                data=json.dumps({"source": {"branch": "gh-pages", "path": "/"}}).encode(),
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "lumicorepro-agent",
                    "Content-Type": "application/json",
                },
            )
            hot = ""
            try:
                with urllib.request.urlopen(enable, timeout=30) as resp:
                    payload = json.loads(resp.read().decode())
                    hot = (payload.get("html_url") or "").split("//")[-1]
            except urllib.error.HTTPError as he:
                if he.code == 409:
                    pass  # already enabled
                else:
                    agent_logger.warning(f"GitHub Pages enable HTTP {he.code}")
            live_url = f"https://{login}.github.io/{repo}/"
            evidence = verify_site(live_url, routes=["/"], timeout=150, poll_interval=5.0)
            return {
                "status": "live" if evidence.get("verified") else "deployed-unverified",
                "platform": "github-pages",
                "url": evidence.get("url") or live_url,
                "repo": f"{login}/{repo}",
                "hosted_on": hot or live_url,
                "verification": evidence,
            }
        except Exception as exc:
            agent_logger.warning(f"GitHub Pages deploy failed: {exc}")
            return {"status": "guide", "message": f"Auto-deploy failed ({exc}) — guide below still works.", "platform": "github-pages"}

    # Guide mode — best-effort exact commands (git only, no token needed)
    commands = [
        f"cd {dist}",
        "git init -b gh-pages",
        "git add -A",
        'git commit -m "deploy(gh-pages): publish site"',
        "gh repo create <your-user>/" + repo + " --public --push",
        "gh api -X POST repos/<your-user>/" + repo + "/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'",
    ]
    return {
        "status": "guide",
        "platform": "github-pages",
        "message": "Set GITHUB_TOKEN (repo scope) for one-click deploy, or run the commands below.",
        "commands": commands,
        "deploy_url": f"https://<your-user>.github.io/{repo}/",
    }


def _guide(project_dir: str, platform: str) -> Dict[str, Any]:
    """Return the deploy commands + config files that were generated for the project."""
    pdir = Path(project_dir)
    configs = {
        name: name
        for name in (
            "vercel.json",
            "netlify.toml",
            "railway.json",
            "render.yaml",
            "cloudrun.yaml",
            ".do/app.yaml",
            "aws/ecs-task-definition.json",
            ".github/workflows/deploy.yml",
            "frontend/Dockerfile",
            "backend/Dockerfile",
            "docker-compose.yml",
        )
        if (pdir / name).is_file()
    }
    commands: List[str] = []
    if platform == "vercel":
        commands = ["npm run build", "vercel --prod"]
    elif platform == "netlify":
        commands = ["npm run build", "netlify deploy --prod"]
    elif platform == "railway":
        commands = ["railway login", "railway up"]
    elif platform == "github-pages":
        commands = ["cd frontend/dist", "git init -b gh-pages", "git add -A",
                    'git commit -m "deploy(gh-pages)"',
                    "gh repo create <user>/<repo> --public --push",
                    "gh api -X POST repos/<user>/<repo>/pages -f 'source[branch]=gh-pages'"]
    return {
        "status": "guide",
        "platform": platform,
        "message": f"Deploy {platform} manually with the provided configs.",
        "commands": commands,
        "configs": list(configs.values()),
        "deploy_guide": _read_file(str(pdir / "DEPLOYMENT_GUIDE.md"))[:2000],
    }


def _store_deploy_gate(project_dir: str) -> Dict[str, Any]:
    """Pre-deploy readiness check on the same weighted store checklist.

    Default: report-only — the score rides along on the deploy result.
    Strict: env ``DEPLOY_GATE_STRICT=1`` blocks deploy when score < 90, so a
    half-finished project never reaches production."""
    out: Dict[str, Any] = {"store_gate": None, "blocked": False}
    try:
        from agent.extensions.store_gate import run_store_gate

        report = run_store_gate(project_dir, apply_fixes=False)
        score = float(report.get("score", 0.0))
        out["store_gate"] = {"score": score, "status": report.get("status")}
        strict = os.environ.get("DEPLOY_GATE_STRICT", "").strip().lower() in ("1", "true", "yes")
        if strict and score < 90.0:
            out["blocked"] = True
            out["message"] = f"DEPLOY_GATE_STRICT: store score {score} < 90"
        agent_logger.info(f"store gate: project={project_dir} score={score} blocked={out['blocked']}")
    except Exception as exc:  # noqa: BLE001 — a broken gate must not block shipping
        agent_logger.warning(f"store deploy gate skipped: {exc}")
    return out


def deploy_project(project_dir: str, platform: str = "vercel", api_url: str = "") -> Dict[str, Any]:
    """Deploy (or guide-deploy) a finished generated project.

    ``api_url`` is the hosted API the frontend was built against; on Vercel it is
    published as the project's ``VITE_API_URL`` before the build and required to
    appear in the deployed bundle during verification.
    """
    platform = (platform or "vercel").strip().lower()
    if platform not in SUPPORTED_PLATFORMS:
        return {"status": "failed", "message": f"Unsupported platform: {platform}", "platform": platform}
    if not project_dir or not os.path.isdir(str(project_dir)):
        return {"status": "failed", "message": "Project directory not found", "platform": platform}

    gate = _store_deploy_gate(project_dir)
    if gate.get("blocked"):
        return {
            "status": "blocked",
            "message": gate.get("message", "store gate below threshold"),
            "platform": platform,
            "store_gate": gate.get("store_gate"),
            "project_dir": project_dir,
        }

    if platform == "vercel":
        try:  # proof badge ships with every deployment (idempotent)
            from agent.extensions.built_with_badge import inject_built_with
            inject_built_with(str(project_dir))
        except Exception:
            agent_logger.warning("Built-with badge injection skipped", exc_info=True)
        result = _vercel_deploy(str(project_dir), api_url)
    elif platform == "netlify":
        result = _netlify_deploy(str(project_dir))
    elif platform == "github-pages":
        result = _github_pages_deploy(str(project_dir))
    else:
        result = _railway_deploy(str(project_dir))

    if result["status"] == "guide":
        result = {**_guide(str(project_dir), platform), **result}
    result["project_dir"] = str(project_dir)
    if gate.get("store_gate"):
        result["store_gate"] = gate["store_gate"]

    verification = result.get("verification")
    result["verified"] = bool(verification and verification.get("verified"))
    if result["status"] in {"live", "deployed-unverified"} and result.get("url"):
        if not verification:
            verification = verify_site(
                result["url"], routes=expected_routes(str(project_dir)), timeout=90
            )
            result["verification"] = verification
            result["verified"] = bool(verification.get("verified"))
            if result["verified"]:
                result["status"] = "live"
        result["live_audit"] = _live_audit(result["url"], str(project_dir))
        if result["verified"]:
            try:  # point the badge at the real URL for future rebuilds
                from agent.extensions.built_with_badge import update_live_link
                update_live_link(str(project_dir), result["url"])
            except Exception:
                pass
    try:
        report_path = Path(project_dir) / ".factory" / "deploy-report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        result["report_path"] = str(report_path)
    except OSError:
        pass
    return result


def _live_audit(url: str, project_dir: Optional[str] = None) -> Dict[str, Any]:
    """Post-deploy verification with evidence (bundle assets, routes, PSI)."""
    routes = expected_routes(project_dir) if project_dir else ["/"]
    audit: Dict[str, Any] = {"verification": verify_site(url, routes=routes, timeout=60)}
    try:
        from agent.free_web_tools import pagespeed_audit
    except ImportError:  # direct-script execution
        from free_web_tools import pagespeed_audit
    psi = pagespeed_audit(url)
    if psi.get("status") == "ok":
        audit["pagespeed"] = psi
    return audit


# --- Express API hosting ------------------------------------------------------
#
# Static hosts (Vercel/Netlify/Pages) serve the frontend only, so a generated
# project used to be reported as a full-stack delivery with its backend/ folder
# never uploaded anywhere. These functions host it as its own project and refuse
# `live` until the deployed health route proves Postgres answered.

API_HEALTH_PATH = "api/v1/health"
BACKEND_REQUIRED_ENV = ("NODE_ENV", "DATABASE_URL", "JWT_SECRET", "ENCRYPTION_KEY",
                        "BRAND_NAME", "APP_URL")
# Regenerated once per project and persisted, so a redeploy never rotates the
# key out from under tokens and encrypted columns already stored in the database.
BACKEND_SECRET_ENV = ("JWT_SECRET", "ENCRYPTION_KEY")
_BACKEND_VERCEL_CONFIG = {
    "version": 2,
    "functions": {"api/index.js": {"maxDuration": 60}},
    "rewrites": [{"source": "/(.*)", "destination": "/api/index.js"}],
}


def _backend_project_name(project_dir: str) -> str:
    """`<product>-api`: the frontend keeps the bare slug, the API gets its own."""
    override = os.getenv("VERCEL_BACKEND_PROJECT_NAME", "").strip().lower()
    if override:
        cleaned = re.sub(r"[^a-z0-9-]+", "-", override).strip("-")
        if cleaned:
            return cleaned[:52]
    path = Path(project_dir)
    slug = path.name
    if slug.lower() == "backend":
        slug = path.parent.name
    slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-") or "lumicorepro"
    return f"{slug[:46]}-api"


def read_env_file(path: Path) -> Dict[str, str]:
    """Parse a KEY=VALUE file. Values are CR-stripped: a Windows-authored .env
    otherwise appends \\r to every value handed to the platform."""
    values: Dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return values
    for line in text.splitlines():
        stripped = line.strip().replace("\r", "")
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if key.strip():
            values[key.strip()] = value
    return values


def _merge_env_file(path: Path, additions: Dict[str, str]) -> None:
    """Add or replace keys in an env file, leaving every other line untouched."""
    existing = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
    lines = existing.splitlines()
    remaining = dict(additions)
    for index, line in enumerate(lines):
        key, _, _value = line.strip().partition("=")
        if key.strip() in remaining:
            lines[index] = f"{key.strip()}={remaining.pop(key.strip())}"
    lines.extend(f"{key}={value}" for key, value in remaining.items())
    try:
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    except OSError as exc:
        agent_logger.warning(f"backend env file could not be persisted: {exc}")


def backend_runtime_env(backend_dir: str, database_url: str = "",
                        cors_origin: str = "") -> Dict[str, str]:
    """The environment the hosted API needs, with secrets generated once.

    Values come from ``backend/.env`` (the local, already-working config) and
    ``backend/.env.example`` (the declared contract); anything secret and absent
    is generated and written back, so the next deploy reuses it.
    """
    base = Path(backend_dir)
    local = read_env_file(base / ".env")
    example = read_env_file(base / ".env.example")
    env: Dict[str, str] = {"NODE_ENV": "production"}

    db = (database_url or local.get("DATABASE_URL", "")).strip()
    if db:
        env["DATABASE_URL"] = db.replace("\r", "")

    generated: Dict[str, str] = {}
    for key in BACKEND_SECRET_ENV:
        value = (local.get(key) or "").strip()
        if not value:
            value = secrets.token_hex(32)
            generated[key] = value
        env[key] = value

    for key in ("BRAND_NAME", "APP_URL"):
        value = (local.get(key) or example.get(key) or "").strip()
        if value:
            env[key] = value

    origin = (cors_origin or "").strip()
    if origin:
        env["CORS_ORIGIN"] = origin.rstrip("/")

    # The database belongs in the file, not only in the platform: the delivered
    # folder's own `npm run db:migrate` reads backend/.env, and a provisioned
    # database missing from it makes the migration runner talk to localhost.
    # CORS_ORIGIN is deliberately excluded — the production lock would otherwise
    # leave the local server refusing its own dev client.
    persisted = dict(generated)
    if db and local.get("DATABASE_URL", "").strip() != db:
        persisted["DATABASE_URL"] = db
    if persisted:
        _merge_env_file(base / ".env", persisted)
    return env


def _ensure_backend_serverless_config(backend_dir: Path) -> None:
    """Vercel needs a function entry + catch-all rewrite to run Express."""
    config_path = backend_dir / "vercel.json"
    if config_path.is_file():
        return
    config_path.write_text(json.dumps(_BACKEND_VERCEL_CONFIG, indent=2), encoding="utf-8")
    ignore = backend_dir / ".vercelignore"
    if not ignore.is_file():
        ignore.write_text("node_modules\n.env*\ntest\n", encoding="utf-8")


def publish_backend_env(workdir: Path, values: Dict[str, str], token: str = "") -> Dict[str, Any]:
    """Set every runtime variable on the Vercel project, names-only in evidence.

    ``vercel env add`` reads the value from stdin; passing it as an argument
    would put a credential in the process list and in any subprocess error text.
    """
    base = _vercel_cli()
    published: List[str] = []
    failed: List[str] = []
    for key, value in values.items():
        clean = (value or "").replace("\r", "")
        rm_cmd = [*base, "env", "rm", key, "production", "--yes", *_vercel_scope_args()]
        add_cmd = [*base, "env", "add", key, "production", *_vercel_scope_args()]
        if token:
            rm_cmd.append(f"--token={token}")
            add_cmd.append(f"--token={token}")
        _run_vercel_env(rm_cmd, workdir, secret=clean)
        added = _run_vercel_env(add_cmd, workdir, stdin=clean, secret=clean)
        if added["ok"]:
            published.append(key)
        else:
            failed.append(key)
    return {"ok": not failed, "published": published, "failed": failed,
            "message": "" if not failed else f"could not set: {', '.join(failed)}"}


_ALIAS_URL_RE = re.compile(r"Aliased[^\n]*?(https://[^\s\"']+?\.vercel\.app)", re.IGNORECASE)


def _api_url_order(output: str, urls: List[str], name: str) -> List[str]:
    """Stable production domains first, per-deployment URLs last.

    ``vercel deploy --prod`` prints both the deployment URL
    (``<name>-<hash>-<team>.vercel.app``, minted anew for every deploy) and, on
    the ``Aliased`` line, the project's own production domain. Baking the
    unstable one into the frontend means the next redeploy moves the API out from
    under a bundle that is already shipped, so the alias always wins. A bare
    ``https://<name>.vercel.app`` is used only when the CLI actually printed it:
    short project domains are global, and another tenant already owns some of
    them — pointing a client's form at one would post their data to a stranger.
    """
    ordered: List[str] = []
    aliased = _ALIAS_URL_RE.search(output or "")
    if aliased:
        ordered.append(aliased.group(1))
    canonical = f"https://{name}.vercel.app"
    if canonical in urls:
        ordered.append(canonical)
    ordered.extend(urls)
    return list(dict.fromkeys(u for u in ordered if u))


def _health_target(url: str) -> str:
    return urllib.parse.urljoin(url.rstrip("/") + "/", API_HEALTH_PATH)


def deploy_backend(project_dir: str, database_url: str = "", cors_origin: str = "") -> Dict[str, Any]:
    """Host ``<project>/backend`` as its own Vercel project and prove the API.

    Order matters: the database must exist before the API is deployed, because
    the serverless entry runs ``sequelize.sync()`` on the first request. ``live``
    is returned only when the hosted ``/api/v1/health`` answers with a payload
    that reports the database reachable — a CLI exit code, a URL string, or a
    health route that never queried Postgres is not evidence.

    No credential value ever appears in the returned evidence: only the names of
    the published variables, the URL, and the health payload.
    """
    backend_dir = Path(project_dir) / "backend"
    if not (backend_dir / "package.json").is_file():
        return {"status": "failed", "verified": False,
                "message": f"backend/package.json not found in {project_dir} — "
                           "this project has no Express API to host",
                "project_dir": str(project_dir)}

    local = read_env_file(backend_dir / ".env")
    db = (database_url or local.get("DATABASE_URL", "")).strip()
    if not db:
        return {
            "status": "blocked", "verified": False, "project_dir": str(project_dir),
            "message": "the API has no database to connect to: provision one (agent.db_provision) "
                       "and pass its connection string, or set FACTORY_DATABASE_TEMPLATE_URL in "
                       "ai-agent/.env (NEON_TEMPLATE_DATABASE_URL is still read) so the factory "
                       "can create it",
        }

    base = _vercel_cli()
    if not base:
        return {"status": "failed", "verified": False, "project_dir": str(project_dir),
                "message": "the vercel CLI is unavailable, so the API cannot be hosted"}

    token = os.getenv("VERCEL_TOKEN", "").strip()
    if token.startswith("your_"):
        token = ""

    name = _backend_project_name(str(project_dir))
    _ensure_backend_serverless_config(backend_dir)
    link = _ensure_vercel_link(backend_dir, name)
    protection = open_project_for_public_demo(name, backend_dir, token)
    env_result = publish_backend_env(
        backend_dir, backend_runtime_env(str(backend_dir), db, cors_origin), token
    )

    cmd = [*base, "deploy", ".", "--prod", "-y", *_vercel_scope_args()]
    if token:
        cmd.append(f"--token={token}")
    try:
        proc = subprocess.run(cmd, cwd=str(backend_dir), capture_output=True, text=True,
                              timeout=900, encoding="utf-8", errors="replace",
                              env=dict(os.environ, DATABASE_URL=db))
    except (subprocess.TimeoutExpired, OSError) as exc:
        # TimeoutExpired echoes its argument list, so the class name is all we keep.
        return {"status": "failed", "verified": False, "project_dir": str(project_dir),
                "message": f"the API deployment did not complete ({type(exc).__name__})",
                "project_name": name, "env": env_result}
    output = _scrub_value((proc.stdout or "") + "\n" + (proc.stderr or ""), db)

    if proc.returncode != 0:
        tail = output.strip()[-600:]
        lowered = tail.lower()
        status = "failed"
        message = tail or f"the vercel CLI exited {proc.returncode}"
        if "credentials" in lowered or "not logged in" in lowered:
            message = "the vercel CLI is not authenticated for this account: " + tail
        return {"status": status, "verified": False, "project_dir": str(project_dir),
                "project_name": name, "env": env_result, "message": message,
                "link": link}

    urls = list(dict.fromkeys(
        u.rstrip(",;.)") for u in re.findall(r"https://[^\s\"']+\.vercel\.app", output)
    ))
    candidates = _api_url_order(output, urls, name)
    deployment_id = (re.findall(r"dpl_[A-Za-z0-9]+", output) or [""])[-1]
    if not candidates:
        return {"status": "failed", "verified": False, "project_dir": str(project_dir),
                "project_name": name, "env": env_result, "deployment_id": deployment_id,
                "message": "the vercel CLI exited 0 but printed no API deployment URL",
                "output": output.strip()[-400:]}

    # The chosen URL is baked into the shipped bundle, so it must be the one that
    # actually serves this API: probe the stable domains before the per-deployment
    # URL and keep the first answer.
    probed: List[tuple] = []
    url = health_url = ""
    evidence: Dict[str, Any] = {}
    for candidate in candidates[:3]:
        target = _health_target(candidate)
        attempt = verify_api_health(target, timeout=45, poll_interval=4.0)
        if attempt.get("status") == "platform-page":
            protection = open_project_for_public_demo(name, backend_dir, token)
            attempt = verify_api_health(target, timeout=45, poll_interval=4.0)
        probed.append((candidate, target, attempt))
        if attempt.get("ok"):
            url, health_url, evidence = candidate, target, attempt
            break
    if not evidence.get("ok"):
        candidate, target, _first = probed[0]
        evidence = verify_api_health(target, timeout=150, poll_interval=4.0)
        url, health_url = candidate, target

    result: Dict[str, Any] = {
        "status": "live" if evidence.get("ok") else (
            "api-db-unreachable" if evidence.get("status") in {"db-disconnected", "db-not-proven"}
            else "deployed-protected" if evidence.get("status") == "platform-page"
            else "deployed-unverified"
        ),
        "verified": bool(evidence.get("ok")),
        "platform": "vercel",
        "url": url,
        "api_url": url,
        "health_url": health_url,
        "project_name": name,
        "deployment_id": deployment_id,
        "env": env_result,
        "link": link,
        "protection": protection,
        "candidates": [c for c, _, _ in probed],
        "verification": evidence,
        "project_dir": str(project_dir),
    }
    if not evidence.get("ok"):
        result["message"] = (evidence.get("failures") or ["the hosted API health check failed"])[0]

    try:
        report_path = backend_dir.parent / ".factory" / "backend-deploy-report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        result["report_path"] = str(report_path)
    except OSError:
        pass
    agent_logger.info(f"backend deploy: project={name} url={url} status={result['status']}")
    return result


def _scrub_value(text: str, secret: str) -> str:
    """Strip a credential from CLI output before it becomes report evidence."""
    if not secret or not text:
        return text
    cleaned = text.replace(secret, "[connection string]")
    for fragment in sorted({p for p in re.findall(r"://([^@]+)@", secret) if len(p) >= 4},
                           key=len, reverse=True):
        cleaned = cleaned.replace(fragment, "[credentials]")
    return cleaned


