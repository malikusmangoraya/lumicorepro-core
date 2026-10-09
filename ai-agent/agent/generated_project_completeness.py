"""Deterministic release checks for generated website artifacts."""
from pathlib import Path
from typing import Any, Dict, List


_PAYMENT_FEATURES = {
    "payments",
    "stripe_payments",
    "paypal_payments",
    "checkout",
    "subscriptions",
}


def _features(spec: Dict[str, Any]) -> set[str]:
    values = spec.get("features") or []
    if isinstance(values, str):
        values = [values]
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _check(name: str, path: Path, required: bool = True, tokens: tuple[str, ...] = ()) -> Dict[str, Any]:
    exists = path.is_file()
    content = path.read_text(encoding="utf-8", errors="replace") if exists and tokens else ""
    passed = exists and all(token.lower() in content.lower() for token in tokens)
    return {
        "name": name,
        "path": path.as_posix(),
        "required": required,
        "passed": passed,
    }


def evaluate_generated_project(project_dir: str | Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Check the required generated artifacts for the selected delivery mode."""
    root = Path(project_dir)
    mode = str(spec.get("layout_mode") or "enterprise").lower()
    static = mode in {"client-static", "static", "static-only"}
    required_checks: List[Dict[str, Any]] = [
        _check("setup_documentation", root / "README.md", tokens=("npm install", "npm run")),
        _check("frontend_package", root / "frontend" / "package.json", tokens=("build",)),
        _check("frontend_entry", root / "frontend" / "index.html"),
        _check(
            "frontend_application",
            root / "frontend" / "src" / "App.jsx",
            tokens=(
                ()
                if static
                else ('path="/login"', 'path="/register"', 'path="/contact"')
            ),
        ),
    ]
    if not static:
        required_checks.extend(
            [
                _check(
                    "backend_server",
                    root / "backend" / "server.js",
                    tokens=("authRoutes", "contactRoutes", "connectDB"),
                ),
                _check(
                    "backend_package",
                    root / "backend" / "package.json",
                    tokens=("db:migrate",),
                ),
                _check(
                    "auth_routes",
                    root / "backend" / "routes" / "authRoutes.js",
                    tokens=("register", "login", "refresh"),
                ),
                _check(
                    "auth_persistence",
                    root / "backend" / "controllers" / "authController.js",
                    tokens=("bcrypt.hash", "bcrypt.compare"),
                ),
                _check(
                    "contact_routes",
                    root / "backend" / "routes" / "contactRoutes.js",
                    tokens=("contact",),
                ),
                _check(
                    "contact_persistence",
                    root / "backend" / "controllers" / "contactController.js",
                    tokens=("ContactSubmission.create",),
                ),
                _check(
                    "database_configuration",
                    root / "backend" / "config" / "database.js",
                    tokens=("new Sequelize", "runMigrations"),
                ),
                _check(
                    "database_migrations",
                    root / "backend" / "migrations" / "001_create_core_tables.js",
                    tokens=("users", "contact_submissions"),
                ),
                _check(
                    "docker_compose",
                    root / "docker-compose.yml",
                    tokens=("db:", "backend:", "frontend:", "condition: service_healthy", "DB_PASSWORD:"),
                ),
                _check("safe_environment_example", root / ".env.example", tokens=("JWT_SECRET=", "POSTGRES_PASSWORD=")),
                _check("login_page", root / "frontend" / "src" / "pages" / "GeneratedLogin.jsx"),
                _check("registration_page", root / "frontend" / "src" / "pages" / "GeneratedRegister.jsx"),
                _check(
                    "persisted_contact_form",
                    root / "frontend" / "src" / "components" / "forms" / "GeneratedContactForm.jsx",
                ),
            ]
        )

    features = _features(spec)
    payment_requested = bool(features & _PAYMENT_FEATURES)
    payment_checks: List[Dict[str, Any]] = []
    if payment_requested:
        payment_checks = [
            _check("payment_routes", root / "backend" / "routes" / "stripeRoutes.js"),
            _check(
                "payment_webhook_security",
                root / "backend" / "services" / "stripeService.js",
                tokens=("constructEvent", "payment_events", "event.id"),
            ),
            _check(
                "payment_event_migration",
                root / "backend" / "migrations" / "002_payment_events.js",
                tokens=("payment_events",),
            ),
            _check(
                "payment_checkout_ui",
                root / "frontend" / "src" / "components" / "ecommerce" / "GeneratedCheckoutButton.jsx",
            ),
            _check(
                "checkout_route",
                root / "frontend" / "src" / "App.jsx",
                tokens=('path="/checkout"', 'path="/payment/success"'),
            ),
            _check(
                "payment_confirmation_page",
                root / "frontend" / "src" / "pages" / "GeneratedPaymentSuccess.jsx",
                tokens=("orders/", "status === 'paid'"),
            ),
        ]

    all_checks = required_checks + payment_checks
    blockers = [check["name"] for check in all_checks if not check["passed"]]
    return {
        "status": "complete" if not blockers else "incomplete",
        "mode": "client-static" if static else "enterprise",
        "payment_required": payment_requested,
        "required_checks": required_checks,
        "payment_checks": payment_checks,
        "blockers": blockers,
    }
