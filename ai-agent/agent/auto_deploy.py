"""
Auto-deploy script (robust v2): push a generated project to GitHub and enable
a live preview via GitHub Pages.

Robustness improvements vs v1:
  - Static preview served from repo ROOT with `.nojekyll` (no Jekyll build step).
  - Pages config updated via PUT (update existing) with POST fallback (new).
  - Polls `/pages/builds` until the build is `built`, then verifies HTTP 200.
  - No dependency on Actions workflow or /docs path quirks.
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
OWNER = "malikusmangoraya"


def load_token() -> str:
    candidates = [ENV_FILE, Path(__file__).resolve().parents[1] / ".env"]
    for env in candidates:
        if env and env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    if token:
                        return token
    return os.getenv("GITHUB_TOKEN", "")


def gh_request(method: str, url: str, token: str, body: dict | None = None) -> dict | list:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"message": raw[:500]}
        parsed["status_code"] = e.code
        return {"__error__": parsed}
    except Exception as e:  # noqa: BLE001
        return {"__error__": {"message": str(e)}}


def repo_exists(repo_name: str, token: str) -> bool:
    res = gh_request("GET", f"https://api.github.com/repos/{OWNER}/{repo_name}", token)
    return isinstance(res, dict) and "__error__" not in res


def create_repo(repo_name: str, token: str, description: str) -> bool:
    res = gh_request(
        "POST", "https://api.github.com/user/repos", token,
        body={
            "name": repo_name,
            "description": description,
            "private": False,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": True,
        },
    )
    if "__error__" in res:
        code = res["__error__"].get("status_code")
        if code == 422:
            return repo_exists(repo_name, token)
        return False
    print(f"  repo created: https://github.com/{OWNER}/{repo_name}")
    return True


def _git(cwd: Path, *args: str) -> bool:
    try:
        sub = ["git", "-C", str(cwd)] + list(args)
        import subprocess
        subprocess.run(sub, check=True, capture_output=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  git {' '.join(args[:2])} failed: {e.stderr.decode() if e.stderr else e}")
        return False


def push_all(project_dir: Path, repo_name: str, token: str) -> bool:
    remote = f"https://x-access-token:{token}@github.com/{OWNER}/{repo_name}.git"
    ok = True
    ok &= _git(project_dir, "init") or True
    _git(project_dir, "config", "user.name", "LumicorePro")
    _git(project_dir, "config", "user.email", "bot@lumicorepro.com")
    _git(project_dir, "add", "-A")
    _git(project_dir, "commit", "-m", "feat: marketplace-ready project", "--allow-empty")
    _git(project_dir, "branch", "-M", "main")
    _git(project_dir, "remote", "remove", "origin")
    ok &= _git(project_dir, "remote", "add", "origin", remote)
    ok &= _git(project_dir, "push", "-u", "origin", "main", "--force")
    if ok:
        print("  source pushed to main (root preview + .nojekyll)")
    return ok


def preview_file(name: str, tagline: str, category: str, features: list[str]) -> str:
    feats = "".join(
        f'<div class="p-4 rounded-xl bg-white/5 border border-white/10 flex items-start gap-3">'
        f'<svg class="w-5 h-5 text-teal-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" '
        f'viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>'
        f'<span class="text-slate-200 text-sm">{f}</span></div>'
        for f in features
    )
    return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{name} — Live Preview</title>
<meta name="description" content="{tagline}" />
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {{ darkMode: 'class', theme: {{ extend: {{ fontFamily: {{ display: ['Inter','ui-sans-serif','system-ui'] }} }} }} }};
</script>
<style>
  body {{ font-family: 'Inter', ui-sans-serif, system-ui; }}
  .gradient-text {{ background: linear-gradient(135deg,#2dd4bf,#22d3ee,#818cf8); -webkit-background-clip: text; background-clip: text; color: transparent; }}
</style>
</head>
<body class="bg-slate-950 min-h-screen text-slate-100 antialiased">
  <header class="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
    <a href="/" class="flex items-center gap-2.5">
      <span class="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-blue-500 grid place-items-center">
        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
      </span>
      <span class="font-bold text-lg tracking-tight">{name}</span>
    </a>
    <div class="flex items-center gap-2 text-xs">
      <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
      <span class="text-emerald-400 font-medium">Live Preview</span>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-6">
    <section class="text-center py-20">
      <span class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-400/10 border border-teal-400/20 text-teal-300 text-xs mb-6">
        {category} · Marketplace Ready
      </span>
      <h1 class="font-display text-5xl sm:text-6xl font-black tracking-tight leading-[1.05] mb-6">
        {name}<br/><span class="gradient-text">Full-Stack, Production-Ready</span>
      </h1>
      <p class="max-w-2xl mx-auto text-slate-400 text-lg mb-8">{tagline}</p>
      <div class="flex flex-wrap justify-center gap-3">
        <a href="https://github.com/{OWNER}/{name.lower().replace(' ','-')}" target="_blank"
           class="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-400 to-blue-500 text-white font-semibold hover:opacity-90 transition">View on GitHub</a>
        <a href="https://github.com/{OWNER}/{name.lower().replace(' ','-')}/archive/refs/heads/main.zip"
           class="px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-200 font-semibold hover:bg-white/10 transition">Download Source</a>
      </div>
      <div class="mt-12 grid grid-cols-3 max-w-md mx-auto gap-4 text-center">
        <div><div class="text-2xl font-black">React 19</div><div class="text-xs text-slate-500 mt-1">Frontend</div></div>
        <div><div class="text-2xl font-black">Express</div><div class="text-xs text-slate-500 mt-1">Backend</div></div>
        <div><div class="text-2xl font-black">MySQL</div><div class="text-xs text-slate-500 mt-1">Database</div></div>
      </div>
    </section>

    <section class="grid sm:grid-cols-2 gap-4 pb-20">
      {feats}
    </section>
  </main>

  <footer class="border-t border-white/5">
    <div class="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
      <span>© 2026 {name}. All rights reserved.</span>
      <span>Generated with LumicorePro Core</span>
    </div>
  </footer>
</body>
</html>"""


def configure_pages(repo_name: str, token: str) -> str:
    """Set Pages source to main root. Returns the pages site URL."""
    base = f"https://api.github.com/repos/{OWNER}/{repo_name}"
    body = {"source": {"branch": "main", "path": "/"}}
    # Try PUT (update) first
    res = gh_request("PUT", f"{base}/pages", token, body=body)
    if "__error__" in res and res["__error__"].get("status_code") == 404:
        # new pages: POST
        res = gh_request("POST", f"{base}/pages", token, body=body)
    if "__error__" in res:
        code = res["__error__"].get("status_code")
        # 409 = already configured → fetch existing
        if code == 409:
            got = gh_request("GET", f"{base}/pages", token)
            return got.get("html_url") or f"https://{OWNER}.github.io/{repo_name}/"
        print(f"  configure_pages issue (code={code}): {res['__error__'].get('message','')[:100]}")
    return f"https://{OWNER}.github.io/{repo_name}/"


def wait_for_pages(repo_name: str, token: str, url: str, max_wait: int = 240) -> bool:
    """Poll pages builds until built, then verify HTTP 200."""
    base = f"https://api.github.com/repos/{OWNER}/{repo_name}"
    deadline = time.time() + max_wait
    while time.time() < deadline:
        builds = gh_request("GET", f"{base}/pages/builds", token)
        if isinstance(builds, list) and builds:
            latest = builds[0]
            status = latest.get("status")
            if status == "built":
                # give CDN a moment
                time.sleep(5)
                if _http_ok(url):
                    return True
        elif isinstance(builds, dict) and "__error__" in builds:
            # Pages may not have any build recorded yet — verify URL anyway
            time.sleep(5)
            if _http_ok(url):
                return True
        time.sleep(10)
    return _http_ok(url)


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def deploy(project_dir: Path, repo_name: str, name: str, tagline: str,
           category: str, features: list[str]) -> str:
    print(f"=== Deploying {name} -> {repo_name} ===")
    token = load_token()
    if not token:
        print("  NO GITHUB_TOKEN — aborting deploy.")
        return ""

    if not repo_exists(repo_name, token):
        if not create_repo(repo_name, token, tagline):
            return ""

    # Write root-level static preview + .nojekyll (disable Jekyll)
    html = preview_file(name, tagline, category, features)
    (project_dir / "index.html").write_text(html, encoding="utf-8")
    (project_dir / ".nojekyll").write_text("", encoding="utf-8")
    # Keep docs/index.html for anyone browsing the repo
    docs = project_dir / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(html, encoding="utf-8")
    (docs / ".nojekyll").write_text("", encoding="utf-8")

    if not push_all(project_dir, repo_name, token):
        print("  source push failed")
        return ""

    url = configure_pages(repo_name, token)
    built = wait_for_pages(repo_name, token, url)
    print(f"  LIVE PREVIEW: {url} {'(verified 200)' if built else '(build pending — check shortly)'}")

    (project_dir / "LIVE_PREVIEW_URL.txt").write_text(url + "\n", encoding="utf-8")
    (project_dir.parent / f"{repo_name}_LIVE_URL.txt").write_text(url + "\n", encoding="utf-8")
    return url


if __name__ == "__main__":
    pass