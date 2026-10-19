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
except ImportError:
    from gh_token import clean_token, is_placeholder


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


def _vercel_cli_deploy(project_dir: str, token: str) -> Optional[Dict[str, Any]]:
    """Deploy with the real Vercel CLI when available (handles any framework)."""
    cli = shutil.which("vercel")
    cmd = None
    if cli:
        cmd = [cli, "--prod", "--yes", f"--token={token}"]
    elif _which_git() or shutil.which("npx"):  # npx covers vercel on demand
        npx = shutil.which("npx")
        if npx:
            cmd = [npx, "-y", "vercel@latest", "--prod", "--yes", f"--token={token}"]
    if not cmd:
        return None
    env = {**os.environ, "VERCEL_ORG_ID": os.getenv("VERCEL_ORG_ID", ""), "VERCEL_PROJECT_ID": os.getenv("VERCEL_PROJECT_ID", "")}
    try:
        proc = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=420,
            env=env,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": "failed", "message": f"vercel CLI failed: {exc}"}
    if proc.returncode != 0:
        return {"status": "failed", "message": (proc.stderr or proc.stdout or "").strip()[-400:]}
    url = ""
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("https://") and ".vercel.app" in line:
            url = line.split()[0]
    return {"status": "live", "platform": "vercel", "url": url, "deployment_id": ""}


def _vercel_deploy(project_dir: str) -> Dict[str, Any]:
    """Deploy ``project_dir`` to Vercel.

    Order: CLI (real upload, any framework) -> v13 inline-files API (static
    fallback) -> guide mode. Ensures a *deployed* site, never an empty one.
    """
    token = os.getenv("VERCEL_TOKEN", "").strip()
    if not token or token.startswith("your_"):
        return {"status": "guide", "message": "VERCEL_TOKEN not set — guide mode"}
    via_cli = _vercel_cli_deploy(project_dir, token)
    if via_cli is not None:
        return via_cli
    try:
        files = _vercel_inline_files(project_dir)
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
        return {
            "status": "live" if url else "failed",
            "platform": "vercel",
            "url": f"https://{url}" if url and not url.startswith("http") else url,
            "deployment_id": payload.get("id") or payload.get("uid", ""),
        }
    except Exception as exc:
        agent_logger.warning(f"Vercel deploy failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _netlify_deploy(project_dir: str) -> Dict[str, Any]:
    token = os.getenv("NETLIFY_AUTH_TOKEN", "").strip()
    if not token or token.startswith("your_"):
        return {"status": "guide", "message": "NETLIFY_AUTH_TOKEN not set — guide mode"}
    index = _find_index(project_dir)
    data = _read_file(index)
    if not data:
        return {"status": "failed", "message": "No built index.html found for deploy"}
    try:
        req = urllib.request.Request(
            "https://api.netlify.com/api/v1/sites",
            method="POST",
            data=data.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/html",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        return {
            "status": "live",
            "platform": "netlify",
            "url": payload.get("url") or "",
            "deployment_id": payload.get("id"),
        }
    except Exception as exc:
        agent_logger.warning(f"Netlify deploy failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _railway_deploy(project_dir: str) -> Dict[str, Any]:
    token = os.getenv("RAILWAY_TOKEN", "").strip()
    if not token or token.startswith("your_"):
        return {"status": "guide", "message": "RAILWAY_TOKEN not set — guide mode"}
    try:
        result = subprocess.run(
            ["railway", "up", "--detach"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return {
                "status": "live",
                "platform": "railway",
                "url": os.getenv("RAILWAY_PUBLIC_DOMAIN", ""),
                "deployment_id": "",
                "output": result.stdout[-1000:],
            }
        return {"status": "failed", "message": (result.stderr or result.stdout)[-500:]}
    except Exception as exc:
        agent_logger.warning(f"Railway deploy failed: {exc}")
        return {"status": "failed", "message": str(exc)}


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
            return {
                "status": "live",
                "platform": "github-pages",
                "url": f"https://{login}.github.io/{repo}/",
                "repo": f"{login}/{repo}",
                "hosted_on": hot or f"https://{login}.github.io/{repo}/",
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


def deploy_project(project_dir: str, platform: str = "vercel") -> Dict[str, Any]:
    """Deploy (or guide-deploy) a finished generated project."""
    platform = (platform or "vercel").strip().lower()
    if platform not in SUPPORTED_PLATFORMS:
        return {"status": "failed", "message": f"Unsupported platform: {platform}", "platform": platform}
    if not project_dir or not os.path.isdir(str(project_dir)):
        return {"status": "failed", "message": "Project directory not found", "platform": platform}

    if platform == "vercel":
        result = _vercel_deploy(str(project_dir))
    elif platform == "netlify":
        result = _netlify_deploy(str(project_dir))
    elif platform == "github-pages":
        result = _github_pages_deploy(str(project_dir))
    else:
        result = _railway_deploy(str(project_dir))

    if result["status"] == "guide":
        result = {**_guide(str(project_dir), platform), **result}
    result["project_dir"] = str(project_dir)

    if result["status"] == "live" and result.get("url"):
        result["live_audit"] = _live_audit(result["url"])
    return result


def _live_audit(url: str) -> Dict[str, Any]:
    """Post-deploy verification with the free keyless tools (PSI + reachability).

    Advisory only — a failed audit never flips ``status`` to failed, but the
    scores travel with the deployment so the QA gate can report honestly.
    """
    try:
        from agent.free_web_tools import http_reachable, pagespeed_audit
    except ImportError:  # direct-script execution
        from free_web_tools import http_reachable, pagespeed_audit
    audit = {"reachability": http_reachable(url)}
    psi = pagespeed_audit(url)
    if psi.get("status") == "ok":
        audit["pagespeed"] = psi
    return audit