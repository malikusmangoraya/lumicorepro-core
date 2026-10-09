"""Canonical GitHub token handling for every deploy/publish path.

Why this module exists
----------------------
The repo read ``GITHUB_TOKEN`` from several places (root ``.env``,
``ai-agent/.env``, the process environment, the Windows Credential Manager) and
each consumer parsed it slightly differently. Two defects followed:

1. **Quote characters survived parsing.** ``setx GITHUB_TOKEN "ghp_..."`` and
   hand-edited ``.env`` lines leave literal ``"`` / ``'`` in the value. Only
   ``.strip()`` was applied, so a perfectly valid token was sent as
   ``"ghp_..."`` and GitHub answered ``401 Bad credentials`` — the failure
   looks exactly like an expired token.
2. **Placeholders looked like real tokens.** ``deploy_engine`` guarded with
   ``startswith("your_")``; other call sites had no guard at all.

``clean_token`` normalizes once, ``load_token`` resolves in a documented order,
and ``validate_token`` proves a token works before any deploy is attempted, so
a stale token fails fast with an actionable message instead of halfway through
a 59-project sweep.
"""
from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_API = "https://api.github.com/user"

# Classic PAT: ghp_ + 36. Fine-grained: github_pat_ + 22+.
TOKEN_RE = re.compile(r"^(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})$")

_PLACEHOLDER_MARKERS = ("your_", "your-token", "changeme", "placeholder", "xxx", "<", ">")


def clean_token(raw: str | None) -> str:
    """Normalize a raw token: drop whitespace AND surrounding quote characters.

    ``'ghp_abc'`` and ``"ghp_abc"`` both become ``ghp_abc``. Unbalanced quotes
    are stripped too, since a trailing quote from a copy/paste is just as fatal.
    """
    if not raw:
        return ""
    value = str(raw).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    else:
        value = value.strip("\"'").strip()
    return value


def is_placeholder(token: str | None) -> bool:
    """True for empty values and the usual 'fill me in' placeholders."""
    value = clean_token(token)
    if not value:
        return True
    low = value.lower()
    return any(marker in low for marker in _PLACEHOLDER_MARKERS)


def looks_like_token(token: str | None) -> bool:
    """Shape check only — does NOT prove the token works. See validate_token."""
    return bool(TOKEN_RE.match(clean_token(token)))


def token_from_env_files(paths) -> str:
    """First non-placeholder ``GITHUB_TOKEN`` found in the given .env files."""
    for candidate in paths or ():
        if not candidate:
            continue
        path = Path(candidate)
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("GITHUB_TOKEN="):
                value = clean_token(line.split("=", 1)[1])
                if value and not is_placeholder(value):
                    return value
    return ""


def load_token(env_files=(), env_var: str = "GITHUB_TOKEN") -> str:
    """Resolve a token: process env first, then the given .env files.

    Explicit .env files win over a stale process environment variable, matching
    ``scripts/deploy_all_pages.py`` so every entry point agrees on one answer.
    """
    for path in env_files or ():
        if not path:
            continue
        path = Path(path)
        if path.exists():
            value = token_from_env_files([path])
            if value:
                return value
    from_env = clean_token(os.getenv(env_var, ""))
    if from_env and not is_placeholder(from_env):
        return from_env
    return ""


def validate_token(token: str | None, timeout: int = 15) -> tuple[bool, str]:
    """Prove a token against the live API. Returns ``(ok, detail)``.

    ``detail`` is the authenticated login on success, otherwise a short reason
    such as ``401 Bad credentials``. Never raises — callers treat network
    failure as "cannot prove", not "invalid".
    """
    value = clean_token(token)
    if not value:
        return False, "no token found"
    if is_placeholder(value):
        return False, "token is a placeholder"
    request = urllib.request.Request(
        GITHUB_API,
        headers={
            "Authorization": f"Bearer {value}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "lumicorepro-core",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            import json

            payload = json.loads(response.read().decode("utf-8", errors="ignore") or "{}")
            return True, str(payload.get("login") or "authenticated")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, f"{exc.code} Bad credentials — token revoked or expired"
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # network/DNS/TLS: unprovable, not invalid
        return False, f"could not verify ({type(exc).__name__})"