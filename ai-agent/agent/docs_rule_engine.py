"""Docs-as-rule-engine.

Turns ``LUMIRULE(...)`` markers in the canonical ``project-rules/`` specs into a
checked-in ``spec-lockfile.json`` that the Enterprise Architect gate enforces on
every generated project tree.

Marker syntax (single line in a canonical spec, markdown source of truth):

    LUMIRULE(scope=<scope>, id=<rule-id>, mode=required|optional)

``mode=required`` rules are gate-blocking when the generated tree opts into
their scope; ``optional`` rules are advisory only. Rules whose id has no
registered verifier are treated as advisory (forward compatible with specs that
are not yet enforceable).

Verifiers are registered in ``VERIFIERS`` keyed by rule id. Each verifier
receives the generated ``project_dir`` and returns
``(passed, detail, files, applies)``.
"""
import hashlib
import json
import os
import re
from typing import Any, Dict, List, Tuple

from agent.schema_contract_injection import MODEL_BASELINE

LOCKFILE_NAME = "spec-lockfile.json"
LOCKFILE_VERSION = 1

_RULE_RE = re.compile(
    r"LUMIRULE\(\s*scope=(?P<scope>[a-z0-9_-]+)\s*,"
    r"\s*id=(?P<id>[a-z0-9_-]+)\s*,"
    r"\s*mode=(?P<mode>required|optional)\s*\)"
)

SPEC_NAMES = [
    "PRD_MASTER_TEMPLATE.md",
    "TRD_ENGINEERING_STANDARDS.md",
    "UI_UX_DESIGN_TOKENS.md",
    "BACKEND_SCHEMA_SPEC.md",
    "SRS_SYSTEM_SPECIFICATIONS.md",
]


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _rel(project_dir: str, path: str) -> str:
    project_dir = os.path.abspath(project_dir)
    path = os.path.abspath(path)
    try:
        common = os.path.commonpath([project_dir, path])
    except ValueError:
        return path
    if common == project_dir:
        return os.path.relpath(path, project_dir).replace(os.sep, "/")
    return path


# ── Rule extraction ─────────────────────────────────────────────────────────
def extract_rules(rules_dir: str, spec_names: List[str] = None) -> List[Dict[str, str]]:
    """Scrape ``LUMIRULE`` markers from the canonical specs."""
    spec_names = spec_names or SPEC_NAMES
    rules: List[Dict[str, str]] = []
    for name in spec_names:
        path = os.path.join(rules_dir, name)
        for lineno, line in enumerate(_read(path).splitlines(), 1):
            match = _RULE_RE.search(line)
            if not match:
                continue
            rules.append(
                {
                    "scope": match.group("scope"),
                    "id": match.group("id"),
                    "mode": match.group("mode"),
                    "source": name,
                    "line": lineno,
                }
            )
    return rules


def _content_hash(rules_dir: str, spec_names: List[str]) -> str:
    digest = hashlib.sha256()
    for name in spec_names:
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(_read(os.path.join(rules_dir, name)).encode("utf-8"))
    return digest.hexdigest()


# ── Lockfile build / load ───────────────────────────────────────────────────
def build_lockfile(rules_dir: str, spec_names: List[str] = None) -> Dict[str, Any]:
    """Return a fresh lockfile, rebuilding ``spec-lockfile.json`` only when the
    source specs changed (content-hash guarded, so the checked-in file stays
    stable across runs)."""
    spec_names = spec_names or SPEC_NAMES
    lock_path = os.path.join(rules_dir, LOCKFILE_NAME)
    rules = extract_rules(rules_dir, spec_names)
    content_hash = _content_hash(rules_dir, spec_names)

    existing = load_lockfile(rules_dir)
    if (
        existing
        and existing.get("version") == LOCKFILE_VERSION
        and existing.get("contentHash") == content_hash
    ):
        existing["rules"] = rules
        return existing

    lockfile = {
        "version": LOCKFILE_VERSION,
        "generator": "docs-as-rule-engine",
        "contentHash": content_hash,
        "generatedAt": None,
        "source_files": list(spec_names),
        "model_baseline": list(MODEL_BASELINE),
        "rules": rules,
    }
    try:
        json.dump(lockfile, open(lock_path, "w", encoding="utf-8"), indent=2, sort_keys=True)
        lockfile["generatedAt"] = None
    except OSError:
        pass
    return lockfile


def load_lockfile(rules_dir: str) -> Dict[str, Any]:
    path = os.path.join(rules_dir, LOCKFILE_NAME)
    if not os.path.isfile(path):
        return None
    try:
        return json.loads(_read(path))
    except ValueError:
        return None


# ── Verifiers (registered by rule id) ───────────────────────────────────────
def _backend(project_dir: str) -> str:
    return os.path.join(project_dir, "backend")


def _scan_backend_middleware(project_dir: str, needle: str) -> List[str]:
    hits: List[str] = []
    mw_dir = os.path.join(_backend(project_dir), "middleware")
    if not os.path.isdir(mw_dir):
        return hits
    for fname in os.listdir(mw_dir):
        if not fname.endswith(".js"):
            continue
        path = os.path.join(mw_dir, fname)
        if needle in _read(path):
            hits.append(_rel(project_dir, path))
    return hits


def _verify_multitenancy(project_dir: str) -> Tuple[bool, str, List[str], bool]:
    """Opt-in consistency rule. Applies only when the generated backend carries
    multi-tenant scaffolding (``org_id`` or an ``Organization`` model)."""
    models_dir = os.path.join(_backend(project_dir), "models")
    index_path = os.path.join(models_dir, "index.js")
    index_content = _read(index_path)
    has_org_id = "org_id" in index_content
    has_org_model = os.path.isfile(os.path.join(models_dir, "Organization.js"))

    if not (has_org_id or has_org_model):
        return True, "multi-tenant not opted in (no org_id/Organization)", [], False

    files: List[str] = []
    problems: List[str] = []
    if not (has_org_id or "Organization" in index_content):
        problems.append("tenant resources lack org_id FK wiriing")
        files.append(_rel(project_dir, index_path))
    middleware = _scan_backend_middleware(project_dir, "requireOrg")
    if not middleware:
        problems.append("no requireOrg middleware (x-org-id / current_org_id gate)")
        files.append(os.path.join("backend", "middleware"))
    if has_org_model and not os.path.isfile(os.path.join(models_dir, "Membership.js")):
        problems.append("Organization without Membership model")
        files.append(_rel(project_dir, os.path.join(models_dir, "Organization.js")))
    passed = not problems
    return passed, ("multi-tenant scaffold consistent" if passed else "; ".join(problems)), files or [os.path.join("backend", "models", "index.js")], True


def _verify_rbac(project_dir: str) -> Tuple[bool, str, List[str], bool]:
    """Opt-in consistency rule for Role/Permission based access control."""
    models_dir = os.path.join(_backend(project_dir), "models")
    index_path = os.path.join(models_dir, "index.js")
    index_content = _read(index_path)
    has_role = os.path.isfile(os.path.join(models_dir, "Role.js"))
    has_permission = os.path.isfile(os.path.join(models_dir, "Permission.js"))
    has_join = "role_permissions" in index_content

    if not (has_role or has_permission or has_join):
        return True, "RBAC not opted in (no Role/Permission)", [], False

    problems: List[str] = []
    files: List[str] = []
    if not (has_role and has_permission):
        problems.append("Role/Permission models required together")
        files.append(os.path.join("backend", "models"))
    if not has_join:
        problems.append("role_permissions join missing from models/index.js")
        files.append(_rel(project_dir, index_path))
    middleware = _scan_backend_middleware(project_dir, "requirePermission")
    if not middleware:
        problems.append("no requirePermission middleware")
        files.append(os.path.join("backend", "middleware"))
    passed = not problems
    return passed, ("RBAC scaffold consistent" if passed else "; ".join(problems)), files or [os.path.join("backend", "models", "Role.js")], True


VERIFIERS = {
    "multitenancy": _verify_multitenancy,
    "rbac": _verify_rbac,
}


# ── Enforcement ─────────────────────────────────────────────────────────────
def verify_rules(project_dir: str, lockfile: Dict[str, Any], transactional: bool = True) -> List[Dict[str, Any]]:
    """Run every lockfile rule against a generated tree. Returns per-rule
    verdicts (``pass`` always True when ``applies`` is False)."""
    results: List[Dict[str, Any]] = []
    scope = "schema"
    rules = [r for r in lockfile.get("rules", []) if r.get("scope") == scope] or lockfile.get("rules", [])
    for rule in rules:
        if rule.get("mode") == "optional":
            results.append(
                {
                    "id": rule["id"],
                    "mode": rule.get("mode"),
                    "pass": True,
                    "detail": "advisory (optional rule)",
                    "files": [],
                    "applies": False,
                }
            )
            continue
        verifier = VERIFIERS.get(rule["id"])
        if verifier is None:
            results.append(
                {
                    "id": rule["id"],
                    "mode": rule.get("mode"),
                    "pass": True,
                    "detail": "no verifier registered — advisory",
                    "files": [],
                    "applies": False,
                }
            )
            continue
        if not transactional:
            results.append(
                {
                    "id": rule["id"],
                    "mode": rule.get("mode"),
                    "pass": True,
                    "detail": "not applicable (static runtime)",
                    "files": [],
                    "applies": False,
                }
            )
            continue
        passed, detail, files, applies = verifier(project_dir)
        results.append(
            {
                "id": rule["id"],
                "mode": rule.get("mode"),
                "pass": passed,
                "detail": detail,
                "files": files,
                "applies": applies,
            }
        )
    return results