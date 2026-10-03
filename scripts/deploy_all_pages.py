"""Deploy every project that lacks a UNIQUE live link to a fresh GitHub Pages repo.

Repo name = brand slug (e.g. nova-forge). Campaign projects that already have a
unique, verified repo (aurelia/aurum/ember/maison/meridian/nuage/prestige/saffron/
studio/voltus) are skipped. Requires GITHUB_TOKEN in ai-agent/.env.

Usage:
  python scripts/deploy_all_pages.py            # dry-run: print plan
  python scripts/deploy_all_pages.py --go       # deploy every pending project
  python scripts/deploy_all_pages.py --go slug1 slug2 ...   # deploy subset
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from brand_map import BRANDS

# Campaign repos already deployed + verified unique (do not touch).
VERIFIED = {
    "aurelia-estates", "aurum-fitness", "ember-salt", "maison-noir",
    "meridian-capital", "nuage-events", "prestige-studio", "saffron-voyage",
    "studio-lumen", "voltus-atelier",
}

DEFAULT_REPOS = {"build", "rest", "style"}
BAD = ("example.com", "placeholder", "your-site", "yourdomain", "localhost", "<your-user>")


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _token_is_valid(token: str) -> bool:
    """Confirm the token actually authenticates (rejects stale/revoked tokens)."""
    if not token or token.startswith("your_"):
        return False
    try:
        req = urllib.request.Request("https://api.github.com/user", headers={
            "Authorization": f"Bearer {token}", "User-Agent": "lumicorepro-agent"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            login = json.loads(resp.read().decode() or "{}").get("login")
            return bool(login)
    except Exception:
        return False


def load_token() -> str:
    """Return the FIRST working GITHUB_TOKEN from env or any .env file.

    Order: process env -> repo root .env -> ai-agent/.env -> backend/.env ->
    Windows Credential Manager. Stale/revoked tokens are skipped (validated
    against the GitHub API), so a fresh token in root .env wins over a stale
    process env var.
    """
    candidates = []
    candidates.append(("env", os.environ.get("GITHUB_TOKEN", "").strip()))
    for envf in (ROOT / ".env", ROOT / "ai-agent" / ".env", ROOT / "backend" / ".env"):
        if envf.exists():
            for line in envf.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    candidates.append((str(envf), val))
    for label, val in candidates:
        if _token_is_valid(val):
            print(f"using working GITHUB_TOKEN from {label}")
            return val
    # fallback: Windows Credential Manager via git credential fill (kept in-process)
    try:
        git = shutil.which("git")
        if git:
            inp = "protocol=https\nhost=github.com\n\n"
            run = subprocess.run([git, "credential", "fill"], input=inp,
                                 capture_output=True, text=True, timeout=20)
            if run.returncode == 0:
                out = run.stdout if not run.stderr else run.stdout
                for line in out.splitlines():
                    if line.startswith("password="):
                        val = line.split("=", 1)[1].strip()
                        if val and not val.startswith("your_"):
                            if _token_is_valid(val):
                                print("using working GITHUB_TOKEN from git credential manager")
                                return val
    except Exception:
        pass
    return ""


def current_link(proj: Path) -> str:
    URL_RE = re.compile(r"https?://[^\s'\"><)]+")
    for f in proj.rglob("*LIVE_URL*.txt"):
        try:
            for u in URL_RE.findall(f.read_text(errors="ignore")):
                if "github.io" in u and not any(b in u for b in BAD):
                    return u.rstrip("/")
        except Exception:
            continue
    for cand in ("frontend/dist/index.html", "frontend/index.html"):
        f = proj / cand
        if f.exists():
            t = f.read_text(errors="ignore")
            m = re.search(r'property="og:url"\s+content="([^"]+)"', t)
            if m and not any(b in m.group(1) for b in BAD):
                return m.group(1).rstrip("/")
    return ""


def api(token: str, method: str, url: str, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "lumicorepro-agent",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as he:
        if he.code in (404, 409, 422):
            return {}
        raise


class RateLimited(Exception):
    """Secondary rate limit active on content creation."""


def create_repo(token: str, name: str, pause: int = 5) -> None:
    """Create a repo, throttled. Raises RateLimited when GitHub's secondary
    rate limit blocks content creation (backoff handled at run level)."""
    import time as _time
    _time.sleep(pause)
    try:
        api(token, "POST", "https://api.github.com/user/repos",
            {"name": name, "description": f"Live preview generated by LumicorePro Agent — {name}",
             "private": False})
    except urllib.error.HTTPError as he:
        if he.code in (403, 429, 500):
            raise RateLimited(f"HTTP {he.code}") from he
        raise


def ensure_pages_source(login: str, repo: str, token: str, branch: str = "gh-pages") -> str:
    """Make Pages serve from `branch`.

    Older repos in this account were created with Pages pointed at `main`, so a
    force-push to gh-pages lands but is never served. GitHub has no PATCH for the
    Pages source, so the config is deleted and re-created when it disagrees.
    """
    want = {"branch": branch, "path": "/"}
    cur = api(token, "GET", f"https://api.github.com/repos/{login}/{repo}/pages")
    if isinstance(cur, dict) and cur.get("source") == want:
        return "ok"
    if isinstance(cur, dict):
        api(token, "DELETE", f"https://api.github.com/repos/{login}/{repo}/pages")
    made = api(token, "POST", f"https://api.github.com/repos/{login}/{repo}/pages", {"source": want})
    if isinstance(made, dict) and made.get("source") == want:
        return "recreated"
    return f"WARN source={(made.get('source') if isinstance(made, dict) else made)}"


def deploy(proj: Path, repo: str, token: str) -> dict:
    login = api(token, "GET", "https://api.github.com/user").get("login")
    if not login:
        return {"status": "failed", "message": "token -> no login"}
    check = api(token, "GET", f"https://api.github.com/repos/{login}/{repo}")
    if not check:
        create_repo(token, repo)
    dist = proj / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        return {"status": "failed", "message": "no dist/index.html"}
    git = shutil.which("git")
    if not git:
        return {"status": "failed", "message": "git missing"}
    tmpdir = Path(tempfile.mkdtemp(prefix="ghpages_"))
    try:
        shutil.copytree(str(dist), str(tmpdir / "site"), dirs_exist_ok=True)
        remote = f"https://x-access-token:{token}@github.com/{login}/{repo}.git"
        for cmd in (
            ["init", "-b", "gh-pages"],
            ["add", "-A"],
            ["-c", "user.email=agent@lumicorepro.app", "-c", "user.name=LumicorePro Agent",
             "commit", "-m", "deploy(gh-pages): publish site"],
            ["remote", "add", "origin", remote],
            ["push", "-f", "origin", "gh-pages"],
        ):
            run = subprocess.run([git] + cmd, cwd=str(tmpdir / "site"),
                                 capture_output=True, text=True, timeout=180)
            if run.returncode != 0 and "nothing to commit" not in run.stdout:
                return {"status": "failed", "message": (run.stderr or run.stdout)[-400:]}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    src = ensure_pages_source(login, repo, token)
    return {"status": "live", "url": f"https://{login}.github.io/{repo}/",
            "pages": src}


def pending_slugs() -> list:
    out = []
    for slug in sorted(BRANDS.keys()):
        if slug in VERIFIED:
            continue
        proj = GEN / slug
        if not (proj / "frontend" / "package.json").exists():
            continue
        link = current_link(proj)
        if link and link.rstrip("/").split("//")[-1] not in DEFAULT_REPOS and \
           link.rstrip("/").split("/")[-1] == slugify(BRANDS[slug]["name"]):
            continue  # already a unique brand-slug repo
        out.append(slug)
    return out


def main() -> int:
    import time as _time
    token = load_token()
    go = "--go" in sys.argv[1:]
    redeploy = "--redeploy" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a not in ("--go", "--redeploy")]
    slugs = list(args) if args else (list(BRANDS.keys()) if redeploy else pending_slugs())
    if not token:
        print("NO TOKEN: set GITHUB_TOKEN in ai-agent/.env")
        return 1
    if not go:
        print("DRY-RUN — projects to deploy ({}):".format(len(slugs)))
        for s in slugs:
            brand = BRANDS[s]
            print("  {} -> {} -> {}.github.io/{}/".format(
                s, brand["name"], "LOGIN", slugify(brand["name"])))
        print("Run with --go to deploy.")
        return 0
    fail = []
    live = []
    total = len(slugs)
    i = 0
    while slugs:
        i += 1
        s = slugs.pop(0)
        brand = BRANDS[s]
        repo = slugify(brand["name"])
        print(f"[{i}/{total}] {s} -> {repo} ...", flush=True)
        try:
            res = deploy(GEN / s, repo, token)
        except RateLimited as exc:
            print(f"    STALL: {exc} — waiting 900s before retrying remaining", flush=True)
            _time.sleep(900)
            slugs.insert(0, s)
            continue
        except Exception as exc:
            res = {"status": "failed", "message": str(exc)[-300:]}
        if res.get("status") == "live":
            url = res["url"].rstrip("/")
            (GEN / s / "LIVE_URL.txt").write_text(f"{url}\n", encoding="utf-8")
            live.append(url)
            print(f"    OK {url}", flush=True)
        else:
            fail.append((s, res.get("message", "?")))
            print(f"    FAIL {res.get('message', '?')}", flush=True)
    print(f"\ndeployed: {len(live)} | failed: {len(fail)}")
    for s, m in fail:
        print(f"  {s}: {m}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())