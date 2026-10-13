import sys
from pathlib import Path

AI_AGENT_DIR = Path(__file__).resolve().parent.parent
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

from agent.generated_project_completeness import evaluate_generated_project
from agent.project_builder import ProjectBuilder


def make_fullstack_project(root: Path) -> Path:
    files = {
        "README.md": "# Setup\nnpm install\nnpm run dev\n",
        "LICENSE.md": "Project license",
        "docker-compose.yml": "db: backend: frontend: condition: service_healthy DB_PASSWORD: postgres:16",
        "frontend/package.json": '{"scripts":{"build":"vite build"}}',
        "frontend/index.html": "<div id='root'></div>",
        "frontend/src/App.jsx": '<Route path="/login" /><Route path="/register" /><Route path="/contact" />',
        "frontend/src/pages/GeneratedLogin.jsx": "login",
        "frontend/src/pages/GeneratedRegister.jsx": "register",
        "frontend/src/components/forms/GeneratedContactForm.jsx": "api.post('/contact'",
        "backend/server.js": "authRoutes contactRoutes connectDB",
        "backend/package.json": '{"scripts":{"db:migrate":"node migrations/run.js"}}',
        "backend/routes/authRoutes.js": "register login refresh",
        "backend/routes/contactRoutes.js": "contact",
        "backend/controllers/authController.js": "bcrypt.hash bcrypt.compare",
        "backend/controllers/contactController.js": "ContactSubmission.create",
        "backend/config/database.js": "new Sequelize runMigrations dialect: 'postgres'",
        "backend/migrations/001_create_core_tables.js": "users contact_submissions",
        ".env.example": "JWT_SECRET=\nPOSTGRES_PASSWORD=\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def test_fullstack_project_passes_required_artifact_checks(tmp_path):
    result = evaluate_generated_project(
        make_fullstack_project(tmp_path / "complete"),
        {"layout_mode": "enterprise", "features": ["jwt_auth", "users", "contact"]},
    )

    assert result["status"] == "complete"
    assert result["blockers"] == []
    assert result["payment_checks"] == []
    assert all(check["status"] == "passed" for check in result["required_checks"])


def test_missing_artifacts_block_fullstack_completion(tmp_path):
    root = make_fullstack_project(tmp_path / "incomplete")
    (root / "backend/routes/authRoutes.js").unlink()
    (root / "backend/migrations/001_create_core_tables.js").unlink()
    (root / "docker-compose.yml").unlink()
    (root / "README.md").unlink()
    (root / "LICENSE.md").unlink()

    result = evaluate_generated_project(root, {"layout_mode": "enterprise"})

    assert result["status"] == "incomplete"
    assert {"auth_routes", "database_migrations", "docker_compose", "setup_documentation", "license"} <= set(result["blockers"])
    assert all("reason" in check for check in result["required_checks"])


def test_static_project_only_checks_explicitly_scoped_artifacts(tmp_path):
    root = tmp_path / "static"
    for relative, content in {
        "README.md": "# Static site\nnpm install\nnpm run build\n",
        "LICENSE.md": "License",
        "frontend/package.json": '{"scripts":{"build":"vite build"}}',
        "frontend/index.html": "<div id='root'></div>",
        "frontend/src/App.jsx": "export default function App() {}",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    result = evaluate_generated_project(root, {"layout_mode": "client-static", "features": []})

    assert result["status"] == "complete"
    assert not any("backend" in check["name"] for check in result["required_checks"])
    assert result["payment_checks"] == []
    backend_checks = [check for check in result["checks"] if check["name"].startswith("backend") or check["name"] in {"database_migrations", "docker_compose"}]
    assert backend_checks
    assert all(check["status"] == "not_applicable" for check in backend_checks)


def test_default_fallback_scaffold_includes_core_feature_modules(tmp_path):
    from unittest.mock import patch

    with patch("agent.project_builder.GENERATED_PROJECTS_DIR", tmp_path):
        builder = ProjectBuilder()
        builder._resolve_template_path = lambda _template: tmp_path / "missing-template"
        project_dir = Path(builder.build_project({
            "project_name": "plain-business",
            "template": {"file_path": "missing-template"},
            "features": [],
            "spec": {"project_name": "plain-business", "website_type": "business", "features": []},
        }))

    assert (project_dir / "frontend/src/features/auth").is_dir()
    assert (project_dir / "frontend/src/features/dashboard").is_dir()
    assert (project_dir / "frontend/src/features/profile").is_dir()
    assert (project_dir / "frontend/src/features/payments").is_dir()
    assert (project_dir / "frontend/src/lib/paymentProvider.js").exists()


def test_payment_requirements_are_checked_only_when_explicit(tmp_path):
    root = make_fullstack_project(tmp_path / "payment")
    missing = evaluate_generated_project(root, {"layout_mode": "enterprise", "features": ["stripe_payments"]})
    (root / "backend/routes/stripeRoutes.js").write_text("webhook route", encoding="utf-8")
    (root / "backend/services/stripeService.js").parent.mkdir(parents=True, exist_ok=True)
    (root / "backend/services/stripeService.js").write_text("constructEvent PaymentEvent event.id", encoding="utf-8")
    (root / "backend/migrations/002_payment_events.js").write_text("CREATE payment_events", encoding="utf-8")
    button = root / "frontend/src/components/ecommerce/GeneratedCheckoutButton.jsx"
    button.parent.mkdir(parents=True, exist_ok=True)
    button.write_text("POST /api/payments/checkout-session", encoding="utf-8")
    success_page = root / "frontend/src/pages/GeneratedPaymentSuccess.jsx"
    success_page.parent.mkdir(parents=True, exist_ok=True)
    success_page.write_text("orders/ status === 'paid'", encoding="utf-8")
    (root / "frontend/src/App.jsx").write_text(
        '<Route path="/login" /><Route path="/register" /><Route path="/contact" />'
        '<Route path="/checkout" /><Route path="/payment/success" />', encoding="utf-8"
    )
    ready = evaluate_generated_project(root, {"layout_mode": "enterprise", "features": ["stripe_payments"]})
    no_payment = evaluate_generated_project(root, {"layout_mode": "enterprise", "features": ["catalog"]})

    assert "payment_routes" in missing["blockers"]
    assert ready["payment_checks"][0]["passed"]
    assert no_payment["payment_checks"] == []


def test_real_secret_in_env_example_blocks_readiness(tmp_path):
    root = make_fullstack_project(tmp_path / "secret")
    (root / ".env.example").write_text("JWT_SECRET=actual-secret-value-that-is-not-empty\nPOSTGRES_PASSWORD=unsafe\n")

    result = evaluate_generated_project(root, {"layout_mode": "enterprise"})

    assert result["status"] == "incomplete"
    assert "safe_environment_example" in result["blockers"]


def test_exported_secret_values_block_but_template_values_are_safe(tmp_path):
    root = make_fullstack_project(tmp_path / "exported-secret")
    env_file = root / ".env.example"
    env_file.write_text("export JWT_SECRET='real-secret-value'\nPOSTGRES_PASSWORD=${DB_PASSWORD:?required}\n")

    unsafe = evaluate_generated_project(root, {"layout_mode": "enterprise"})
    env_file.write_text("JWT_SECRET=\nPOSTGRES_PASSWORD=${DB_PASSWORD:?required}\n")
    safe = evaluate_generated_project(root, {"layout_mode": "enterprise"})

    assert "safe_environment_example" in unsafe["blockers"]
    assert "safe_environment_example" not in safe["blockers"]


def test_optional_checks_report_not_run_instead_of_fabricated_pass(tmp_path):
    result = evaluate_generated_project(make_fullstack_project(tmp_path / "checks"), {"layout_mode": "enterprise"})

    build = next(check for check in result["checks"] if check["name"] == "frontend_build")
    assert build["status"] == "not_run"
    assert build["passed"] is False


def test_malformed_package_json_blocks_generated_project_completion(tmp_path):
    root = make_fullstack_project(tmp_path / "malformed-package")
    (root / "frontend/package.json").write_text("{broken json", encoding="utf-8")

    result = evaluate_generated_project(root, {"layout_mode": "enterprise"})

    package_check = next(check for check in result["checks"] if check["name"] == "frontend_package")
    assert result["status"] == "incomplete"
    assert "frontend_package" in result["blockers"]
    assert package_check["reason"] == "invalid_json"


def test_valid_json_package_without_build_script_is_not_complete(tmp_path):
    root = make_fullstack_project(tmp_path / "package-no-build")
    (root / "frontend/package.json").write_text('{"scripts":{"test":"vitest"}}', encoding="utf-8")

    result = evaluate_generated_project(root, {"layout_mode": "enterprise"})

    package_check = next(check for check in result["checks"] if check["name"] == "frontend_package")
    assert result["status"] == "incomplete"
    assert "frontend_package" in result["blockers"]
    assert package_check["reason"] == "required_content_missing"
