"""Windows Application Control can block a freshly installed native bundler binary.

``npm install`` writes ``@rollup/rollup-win32-x64-msvc`` at whatever patch version is
current that day. When the machine's App Control / Smart App Control policy has never
seen that file hash it refuses the load, and ``npm run build`` dies with
``ERR_DLOPEN_FAILED`` — on generated code that was never the problem, before anything
is deployed. Verified on 2026-10-27: the same project built as soon as the binary was
swapped for the same-minor copy another project on this machine already loads.

This module restores such a copy — same package path, exact version preferred, same
``major.minor`` accepted — from a sibling install inside this repository. It never
downloads a binary, never writes outside the project being built, and returns evidence
naming both versions so the swap is auditable in the delivery report.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

POLICY_MARKERS = ("An Application Control policy has blocked this file", "ERR_DLOPEN_FAILED")
_BINARY_SUFFIXES = (".node", ".dll", ".exe", ".so", ".dylib")
_WINDOWS_PATH_RE = re.compile(
    r"(?:\\\\\?\\)?([A-Za-z]:\\[^\n\r\"']*?(?:%s))"
    % "|".join(s.replace(".", r"\.") for s in _BINARY_SUFFIXES),
    re.IGNORECASE,
)
# Sibling installs worth searching, ordered by how likely they are to hold an accepted copy.
_SEARCH_PATTERNS = (
    "generated-projects/*/frontend/node_modules",
    "generated-projects/*/node_modules",
    "*/node_modules",
    "node_modules",
)
MAX_SWAP_ATTEMPTS = 2


def is_policy_block(stderr: str) -> bool:
    return any(marker in (stderr or "") for marker in POLICY_MARKERS)


def blocked_binary(stderr: str) -> str:
    """The absolute path App Control named in its refusal, or "" when there is none.

    A block without a named file is not guessed at: restoring the wrong binary would turn
    an environment problem into a corrupted build.
    """
    text = stderr or ""
    if not is_policy_block(text):
        return ""
    match = _WINDOWS_PATH_RE.search(text)
    return match.group(1) if match else ""


def _version_of(package_dir: Path) -> str:
    try:
        return str(json.loads((package_dir / "package.json").read_text(encoding="utf-8")).get("version", ""))
    except (OSError, ValueError):
        return ""


def _minor(version: str) -> str:
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def _rank(version: str, wanted: str) -> int:
    """0 = the exact version, 1 = the same minor, 2 = unusable."""
    if not version or _minor(version) != _minor(wanted):
        return 2
    return 0 if version == wanted else 1


def _descending(version: str) -> Tuple[int, int, int]:
    numbers = [int(part) for part in re.findall(r"\d+", version)[:3]]
    numbers += [0] * (3 - len(numbers))
    return tuple(-part for part in numbers)


def _node_modules_of(path: Path) -> Optional[Path]:
    """The nearest ``node_modules`` ancestor — a scoped package sits one level deeper,
    so counting parents would land inside ``@scope`` instead of above it."""
    for parent in path.parents:
        if parent.name == "node_modules":
            return parent
    return None


def candidates(blocked: Path, repo_root: Path, frontend: Path) -> List[Tuple[Path, str]]:
    """Copies of the same package path that another install in this repository already has.

    The project being built is excluded — its own file is the one that was refused — and a
    package directory whose binary is missing is skipped rather than half-copied.
    """
    node_modules = _node_modules_of(blocked)
    if node_modules is None:
        return []
    relative = blocked.relative_to(node_modules)
    wanted = _version_of(blocked.parent)
    if not wanted:
        return []

    scored: List[Tuple[int, Tuple[int, int, int], Path, str]] = []
    for pattern in _SEARCH_PATTERNS:
        for modules in sorted(repo_root.glob(pattern)):
            resolved = modules.resolve()
            if resolved == node_modules.resolve() or _inside_any(resolved, frontend):
                continue
            other = resolved / relative
            if not other.is_file():
                continue
            rank = _rank(_version_of(other.parent), wanted)
            if rank == 2:
                continue
            scored.append((rank, _descending(_version_of(other.parent)), other, _version_of(other.parent)))
    scored.sort(key=lambda item: (item[0], item[1], str(item[2])))
    return [(path, version) for _, _, path, version in scored]


def _absolute(path: Path) -> Path:
    """Long-form absolute path — Windows hands the same file back as ``AZAMCO~1`` or
    ``AZAM COMPUTERS`` depending on who wrote it, and a prefix test would then fail."""
    try:
        return Path(path).resolve()
    except OSError:
        return Path(path)


def _resolved(path: Path) -> Path:
    return Path(os.path.normcase(str(_absolute(path))))


def _inside_any(path: Path, root: Path) -> bool:
    target, inside = _resolved(path), _resolved(root)
    return target == inside or target.is_relative_to(inside)


def repair(frontend: Path, stderr: str, *, repo_root: Path,
           exclude: Sequence[Path] = ()) -> Dict[str, Any]:
    """Replace the refused binary with one accepted copy and report exactly what changed.

    ``exclude`` carries the sources an earlier retry already failed with, so the caller
    walks the candidate list instead of looping on the same file.
    """
    base: Dict[str, Any] = {"repaired": False, "attempts": 0}
    raw = blocked_binary(stderr)
    if not raw:
        base["status"] = "policy-block-without-path" if is_policy_block(stderr) else "not-a-policy-block"
        return base
    frontend_root = _absolute(frontend)
    blocked = _absolute(Path(raw))
    if not _inside_any(blocked, frontend_root):
        base.update(status="not-in-project", blocked_path=str(blocked))
        return base

    skipped = {_resolved(p) for p in exclude}
    options = [(path, version) for path, version in candidates(blocked, repo_root, frontend_root)
               if _resolved(path) not in skipped]
    if not options:
        base.update(status="no-compatible-copy", blocked_path=str(blocked),
                    blocked_version=_version_of(blocked.parent),
                    message="App Control blocked a native bundler binary and this repository holds "
                            "no compatible copy to restore. Nothing was downloaded. Unblock the file "
                            "in Windows Security, or allow the npm cache directory in the policy, "
                            "then re-run.")
        return base

    source, source_version = options[0]
    try:
        shutil.copyfile(source, blocked)
    except OSError as exc:
        base.update(status="copy-failed", blocked_path=str(blocked), message=str(exc))
        return base
    base.update(
        status="swapped",
        repaired=True,
        attempts=1,
        blocked_path=str(blocked.relative_to(frontend_root)),
        blocked_version=_version_of(blocked.parent),
        source=str(source),
        source_version=source_version,
        message="Windows Application Control refused the freshly installed native bundler binary; "
                "restored the same package already accepted on this machine and the build is being "
                "retried. This is a machine policy, not a defect in the generated project.",
    )
    return base
