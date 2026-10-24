"""Deterministic release checks for generated website artifacts."""
import json
import re
from pathlib import Path
from typing import Any

from .generation_contract import resolve_generation_contract

_PAYMENT_FEATURES = {
    "payments",
    "stripe_payments",
    "paypal_payments",
    "checkout",
    "subscriptions",
}
_SECRET_NAMES = {"JWT_SECRET", "POSTGRES_PASSWORD", "DB_PASSWORD"}
_PLACEHOLDERS = {"", "changeme", "change-me", "your-secret", "replace-me", "example"}


def _check(name: str, path: Path, required: bool = True, tokens: tuple[str, ...] = ()) -> dict[str, Any]:
    exists = path.is_file()
    content = path.read_text(encoding="utf-8", errors="replace") if exists and tokens else ""
    passed = exists and all(token.lower() in content.lower() for token in tokens)
    reason = "artifact_present" if passed else "artifact_missing" if not exists else "required_content_missing"
    if exists and path.name == "package.json":
        try:
            package = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            passed = False
            reason = "invalid_json"
        else:
            if passed and path.parent.name == "frontend":
                scripts = package.get("scripts") if isinstance(package, dict) else None
                if not isinstance(scripts, dict) or not isinstance(scripts.get("build"), str) or not scripts["build"].strip():
                    passed = False
                    reason = "required_content_missing"
    return {"name": name, "path": path.as_posix(), "required": required, "passed": passed, "status": "passed" if passed else "failed", "reason": reason}


def _first_present(root: Path, patterns: tuple[str, ...]) -> Path | None:
    """Return the first existing file for a set of layout-agnostic globs."""
    for pattern in patterns:
        for candidate in sorted(root.glob(pattern)):
            if candidate.is_file():
                return candidate
    return None


def _check_any(
    name: str,
    root: Path,
    patterns: tuple[str, ...],
    required: bool = True,
    token_groups: tuple[tuple[str, ...], ...] = (),
) -> dict[str, Any]:
    """Check a capability by any conventional filename, not one scaffold name.

    ``token_groups`` are alternatives: a file passes if every token in at least
    one group is present. This allows equivalent scaffolds (``auth.routes.js``
    vs ``authRoutes.js``) without weakening the content requirement.
    """
    path = _first_present(root, patterns)
    if path is None:
        expected = root / patterns[0] if patterns else root
        return {
            "name": name,
            "path": expected.as_posix(),
            "required": required,
            "passed": False,
            "status": "failed",
            "reason": "artifact_missing",
        }
    content = path.read_text(encoding="utf-8", errors="replace") if token_groups else ""
    passed = True
    if token_groups:
        passed = any(
            all(token.lower() in content.lower() for token in group)
            for group in token_groups
        )
    return {
        "name": name,
        "path": path.as_posix(),
        "required": required,
        "passed": passed,
        "status": "passed" if passed else "failed",
        "reason": "artifact_present" if passed else "required_content_missing",
    }


def _safe_environment_example(root: Path) -> dict[str, Any]:
    path = root / ".env.example"
    check = _check("safe_environment_example", path, tokens=("JWT_SECRET=", "POSTGRES_PASSWORD="))
    if check["passed"]:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.match(r"\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", line)
            if match and match.group(1) in _SECRET_NAMES:
                value = match.group(2).strip().strip("'\"")
                is_template = (
                    value.lower() in _PLACEHOLDERS
                    or value.startswith("${") and value.endswith("}")
                    or value.startswith("#")
                )
                if not is_template:
                    check.update(passed=False, status="failed", reason="secret_value_present")
                    break
    return check


def evaluate_generated_project(project_dir: str | Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Check required generated artifacts for the contract-resolved delivery mode."""
    root = Path(project_dir)
    contract = resolve_generation_contract(spec)
    static = contract["layout_mode"] == "client-static"
    checks = [
        _check("setup_documentation", root / "README.md", tokens=("npm install", "npm run")),
        _check("license", root / "LICENSE.md"),
        _check("frontend_package", root / "frontend/package.json", tokens=("build",)),
        _check("frontend_entry", root / "frontend/index.html"),
        _check("frontend_application", root / "frontend/src/App.jsx", tokens=() if static else ('path="/login"', 'path="/register"', 'path="/contact"')),
    ]
    if not static:
        checks.extend([
            _check_any(
                "backend_server", root, ("backend/server.js",),
                token_groups=(
                    ("authRoutes", "contactRoutes", "connectDB"),
                    ("express", "routes", "sequelize"),
                ),
            ),
            _check_any(
                "backend_package", root, ("backend/package.json",),
                token_groups=(("db:migrate",), ("migrate",), ("sequelize",)),
            ),
            _check_any(
                "auth_routes", root,
                ("backend/routes/authRoutes.js", "backend/routes/*auth*.js"),
                token_groups=(("register", "login", "refresh"), ("register", "login")),
            ),
            _check_any(
                "auth_persistence", root,
                (
                    "backend/controllers/authController.js",
                    "backend/controllers/*auth*.js",
                    "backend/routes/*auth*.js",
                    "backend/services/*auth*.js",
                ),
                token_groups=(("bcrypt.hash", "bcrypt.compare"), ("bcrypt", "hash")),
            ),
            _check_any(
                "contact_routes", root,
                ("backend/routes/contactRoutes.js", "backend/routes/*contact*.js"),
                token_groups=(("contact",),),
            ),
            _check_any(
                "contact_persistence", root,
                ("backend/controllers/contactController.js", "backend/controllers/*contact*.js"),
                token_groups=(("ContactSubmission.create",), ("contact", "create")),
            ),
            _check_any(
                "database_configuration", root,
                (
                    "backend/config/database.js",
                    "backend/config/*.js",
                    "backend/models/index.js",
                ),
                token_groups=(
                    ("new Sequelize", "runMigrations", "postgres"),
                    ("Sequelize", "DATABASE_URL"),
                ),
            ),
            _check_any(
                "database_migrations", root,
                (
                    "backend/migrations/001_create_core_tables.js",
                    "backend/migrations/*.js",
                ),
                token_groups=(("users", "contact_submissions"), ("users",)),
            ),
            _check_any(
                "docker_compose", root,
                ("docker-compose.yml", "docker-compose.yaml", "compose.yml"),
                token_groups=(
                    ("db:", "backend:", "frontend:", "condition: service_healthy", "DB_PASSWORD:"),
                    ("services:", "db:", "backend:", "frontend:"),
                    ("db:", "backend:", "frontend:"),
                ),
            ),
            _safe_environment_example(root),
            _check_any(
                "login_page", root,
                (
                    "frontend/src/pages/GeneratedLogin.jsx",
                    "frontend/src/pages/*Login*.jsx",
                ),
            ),
            _check_any(
                "registration_page", root,
                (
                    "frontend/src/pages/GeneratedRegister.jsx",
                    "frontend/src/pages/*Register*.jsx",
                    "frontend/src/pages/*Signup*.jsx",
                ),
            ),
            _check_any(
                "persisted_contact_form", root,
                (
                    "frontend/src/components/forms/GeneratedContactForm.jsx",
                    "frontend/src/components/forms/*Contact*.jsx",
                    "frontend/src/components/*Contact*.jsx",
                    "frontend/src/pages/*Contact*.jsx",
                ),
                token_groups=(
                    ("api.post", "contact"),
                    ("axios", "contact"),
                    ("fetch", "contact"),
                    ("contact", "submit"),
                ),
            ),
        ])

    payment_requested = bool(set(contract["features"]) & _PAYMENT_FEATURES)
    payment_checks = []
    if payment_requested:
        payment_checks = [
            _check("payment_routes", root / "backend/routes/stripeRoutes.js"),
            _check("payment_webhook_security", root / "backend/services/stripeService.js", tokens=("constructEvent", "payment_events", "event.id")),
            _check("payment_event_migration", root / "backend/migrations/002_payment_events.js", tokens=("payment_events",)),
            _check("payment_checkout_ui", root / "frontend/src/components/ecommerce/GeneratedCheckoutButton.jsx"),
            _check("checkout_route", root / "frontend/src/App.jsx", tokens=('path="/checkout"', 'path="/payment/success"')),
            _check("payment_confirmation_page", root / "frontend/src/pages/GeneratedPaymentSuccess.jsx", tokens=("orders/", "status === 'paid'")),
        ]

    if static:
        checks.extend(
            {
                "name": name,
                "status": "not_applicable",
                "passed": True,
                "required": False,
                "reason": "client_static_contract",
            }
            for name in ("backend_server", "backend_package", "database_migrations", "docker_compose")
        )
    required_checks = [check for check in checks if check["required"]]
    blockers = [check["name"] for check in required_checks + payment_checks if not check["passed"]]
    optional_checks = [
        {
            "name": "frontend_build",
            "path": "frontend/package.json",
            "required": False,
            "status": "not_run",
            "passed": False,
            "reason": "build_not_executed",
        },
    ]
    if not static:
        optional_checks.append(
            {
                "name": "backend_tests",
                "path": "backend/package.json",
                "required": False,
                "status": "not_run",
                "passed": False,
                "reason": "tests_not_executed",
            }
        )
    return {
        # Artifact presence is not behavioural proof. ``status`` is kept for
        # backward compatibility; ``release_ready`` deliberately stays False
        # until the DevOps gate has executed build and test verification.
        "status": "complete" if not blockers else "incomplete",
        "artifact_status": "complete" if not blockers else "incomplete",
        "release_ready": False,
        "verified": False,
        "verification": {
            "build": {
                "status": "not_run",
                "passed": False,
                "reason": "build_not_executed",
            },
            "tests": {
                "status": "not_applicable" if static else "not_run",
                "passed": False,
                "reason": "no_backend_in_static_mode" if static else "tests_not_executed",
            },
        },
        "mode": contract["layout_mode"],
        "contract_version": contract["version"],
        "payment_required": payment_requested,
        "checks": checks + payment_checks + optional_checks,
        "required_checks": required_checks,
        "payment_checks": payment_checks,
        "blockers": blockers,
    }
