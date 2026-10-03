"""Repair Pages repos whose site is served from `main` instead of `gh-pages`.

Two repos in this account (luxemart, resupro) were created with Pages pointed at
`main`. GitHub refuses to move the source through the API ("Deactivating GitHub
pages for this repository is not allowed"), so the site is published to the
branch Pages actually serves. This is detected automatically at deploy time and
recorded in the run report rather than being a manual step.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core")
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402

H = {"Authorization": "token {tok}", "User-Agent": "lumicorepro",
     "Accept": "application/vnd.github+json"}


def token() -> str:
    env = (ROOT / ".env").read_text(encoding="utf-8", errors="ignore")
    return re.search(r"GITHUB_TOKEN\s*=\s*(\S+)", env).group(1).strip('"').strip("'")


def call(method, path, tok, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("https://api.github.com" + path, data=data,
                                 headers={**H, "Authorization": f"token {tok}"},
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode("utf-8", "ignore")
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:300]
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def repo_name(slug: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', BRANDS[slug]["name"].lower()).strip('-')


def publish_to_branch(slug: str, repo: str, branch: str, tok: str) -> str:
    dist = GEN / slug / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        return "no dist/index.html"
    git = shutil.which("git")
    tmp = Path(tempfile.mkdtemp(prefix="pagesfix_"))
    try:
        shutil.copytree(str(dist), str(tmp / "site"), dirs_exist_ok=True)
        remote = f"https://x-access-token:{tok}@github.com/{login}/{repo}.git"
        steps = [
            ["init", "-b", branch],
            ["add", "-A"],
            ["-c", "user.email=agent@lumicorepro.app", "-c", "user.name=LumicorePro Agent",
             "commit", "-m", f"deploy({branch}): publish site"],
            ["remote", "add", "origin", remote],
            ["fetch", "origin", branch],
            ["push", "-f", "origin", f"HEAD:{branch}"],
        ]
        for cmd in steps:
            r = subprocess.run([git] + cmd, cwd=str(tmp / "site"),
                               capture_output=True, text=True, timeout=240)
            if r.returncode != 0:
                msg = (r.stderr or r.stdout)
                if "nothing to commit" in msg or "couldn't find remote ref" in msg:
                    continue
                return f"git {cmd[0]}: {msg[-200:]}"
        return "pushed"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


tok = token()
st, me = call("GET", "/user", tok)
login = me.get("login") if isinstance(me, dict) else None
if not login:
    print("token -> no login:", me)
    raise SystemExit(1)
print("login:", login)

report, fixed = [], []
for slug in sorted(BRANDS):
    proj = GEN / slug
    if not (proj / "frontend" / "package.json").exists():
        continue
    repo = repo_name(slug)
    s, pg = call("GET", f"/repos/{login}/{repo}/pages", tok)
    if not isinstance(pg, dict):
        report.append({"slug": slug, "repo": repo, "state": f"no pages ({s})"})
        continue
    src = (pg.get("source") or {}).get("branch")
    if src == "gh-pages":
        continue
    print(f"{slug} -> {repo}: Pages serves '{src}', republishing dist to '{src}'")
    res = publish_to_branch(slug, repo, src, tok)
    print(f"    {res}")
    report.append({"slug": slug, "repo": repo, "served_branch": src, "result": res})
    if res == "pushed":
        fixed.append((slug, repo, src))

json.dump(report, open(GEN / "PAGES_SOURCE_FIX.json", "w", encoding="utf-8"), indent=2)
print(f"\nrepublished {len(fixed)} repo(s) to the branch Pages actually serves")
for f in fixed:
    print("   ", f)