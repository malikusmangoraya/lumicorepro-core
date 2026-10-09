#!/usr/bin/env python3
"""Boot each product's API and prove that signup and login actually work.

This is the end-to-end check that matters most for selling: the product is only
worth anything if a buyer can install it, register an account and sign in.

For every project in `products/` this script:

  1. installs backend dependencies if they are missing,
  2. starts `node server.js` on a free port,
  3. waits for `GET /health`,
  4. `POST /api/auth/register` with a unique email,
  5. `POST /api/auth/login` with the same credentials,
  6. reports exactly which step failed, then shuts the server down.

    python scripts/verify_backend.py --only aurelia-estates
    python scripts/verify_backend.py --install     # allow npm install
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"
NPM = "npm.cmd" if os.name == "nt" else "npm"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def http(url: str, payload: dict | None = None, method: str = "GET", timeout: int = 20):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(4000).decode("utf-8", "replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read(4000).decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


@dataclass
class Result:
    name: str
    health: str = "not attempted"
    register: str = "not attempted"
    login: str = "not attempted"
    authorised: str = "not attempted"
    mounted: int = 0
    ok: bool = False
    log: list[str] = field(default_factory=list)


def run_project(p: Path, allow_install: bool, timeout: int) -> Result:
    r = Result(name=p.name)
    be = p / "backend"
    if not be.is_dir():
        r.health = "no backend directory"
        return r

    if not (be / "node_modules").is_dir():
        if not allow_install:
            r.health = "dependencies not installed (re-run with --install)"
            return r
        try:
            subprocess.run([NPM, "install", "--no-audit", "--no-fund"],
                           cwd=str(be), capture_output=True, text=True, timeout=900)
        except Exception as e:
            r.health = f"npm install failed: {e}"
            return r

    port = free_port()
    # No DATABASE_URL on purpose: config/database.js then falls back to the
    # sqlite dialect and creates ./database.sqlite, so the check runs against a
    # real database with no external service. Leaving DATABASE_URL as an empty
    # string would exercise a different code path than a buyer's first run.
    env = {
        **os.environ,
        "NODE_ENV": "development",
        "PORT": str(port),
        # Access and refresh tokens are signed with separate secrets; both are
        # required or login fails while minting the refresh token.
        "JWT_SECRET": "verification-access-secret-verification-access",
        "JWT_REFRESH_SECRET": "verification-refresh-secret-verification",
        "ENABLE_DEMO_SEED": "true",
        "DEMO_USER_PASSWORD": "VerifyOnly!123",
        "REDIS_DISABLED": "true",
        "AI_AGENT_URL": "http://127.0.0.1:9",  # never reachable; must not block boot
    }
    env.pop("DATABASE_URL", None)
    proc = subprocess.Popen([ "node", "server.js"], cwd=str(be), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        # 1. health
        deadline = time.time() + 45
        up = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            code, body = http(f"{base}/health", timeout=4)
            if code == 200:
                up = True
                r.health = "200 OK"
                try:
                    r.mounted = json.loads(body).get("status") == "OK" and 1 or 1
                except Exception:
                    pass
                break
            time.sleep(1)
        if not up:
            r.health = "server did not answer /health within 45s"
            return r

        # 2. register — a unique address per run so repeat runs still pass
        email = f"verify-{int(time.time())}@example.com"
        password = "VerifyOnly!123"
        code, body = http(f"{base}/api/auth/register", {
            "name": "Verification User", "email": email, "password": password,
        }, method="POST")
        r.register = f"{code} {body[:110]}"

        # 3. login
        code2, body2 = http(f"{base}/api/auth/login", {
            "email": email, "password": password,
        }, method="POST")
        r.login = f"{code2} {body2[:110]}"

        # 4. the access token must actually authorise a protected route
        token = ""
        try:
            token = json.loads(body2).get("token", "")
        except Exception:
            pass
        if token:
            req = urllib.request.Request(f"{base}/api/auth/profile")
            req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    r.authorised = f"{resp.status} OK on /api/auth/profile"
            except urllib.error.HTTPError as e:
                r.authorised = f"{e.code} on /api/auth/profile"
            except Exception as e:
                r.authorised = f"error: {e}"
        else:
            r.authorised = "no token returned by login"

        # Registration correctly answers 201 Created; login answers 200 OK. Requiring
# exactly 200 for registration would report a working endpoint as broken.
        r.ok = (code in (200, 201) and code2 == 200 and "200" in r.authorised)
    finally:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
        for line in (out or "").splitlines():
            if "mounted" in line or "failed to mount" in line:
                r.log.append(line.strip())
        # The sqlite fallback writes database.sqlite next to the server; it is a
        # runtime artefact and must never be left in a deliverable.
        sqlite = be / "database.sqlite"
        if sqlite.exists():
            try:
                sqlite.unlink()
            except OSError:
                pass
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only")
    ap.add_argument("--install", action="store_true", help="allow npm install")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    if not PRODUCTS.is_dir():
        print(f"No {PRODUCTS} directory", file=sys.stderr)
        return 2
    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]
    if not dirs:
        print("No matching products", file=sys.stderr)
        return 2

    print(f"=== verify_backend ({len(dirs)} project(s)) ===")
    results = []
    for d in dirs:
        res = run_project(d, a.install, a.timeout)
        results.append(res)
        flag = "PASS" if res.ok else "FAIL"
        print(f"[{flag}] {res.name}")
        print(f"     health   : {res.health}")
        print(f"     register : {res.register}")
        print(f"     login    : {res.login}")
        print(f"     bearer   : {res.authorised}")
        for line in res.log[:3]:
            print(f"     log      : {line[:150]}")

    good = sum(1 for r in results if r.ok)
    print(f"\n=== {good}/{len(results)} projects serve a working signup + login ===")
    return 0 if good == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())