import json
import sys
from pathlib import Path

AI_AGENT_DIR = Path(__file__).resolve().parent.parent
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

from agent.api_generator import APIGenerator
from agent.project_builder import ProjectBuilder


def generate_backend(tmp_path, features):
    target = tmp_path / "backend"
    plan = {
        "project_name": "generated-site",
        "layout_mode": "enterprise",
        "features": features,
        "spec": {
            "project_name": "generated-site",
            "website_type": "business",
            "industry": "general",
            "features": features,
        },
    }
    APIGenerator().generate_full_backend(target, plan)
    return target


def test_default_backend_uses_postgres_sequelize_and_excludes_unrequested_saas(tmp_path):
    backend = generate_backend(tmp_path, ["jwt_auth", "users", "contact"])
    package = json.loads((backend / "package.json").read_text(encoding="utf-8"))
    dependencies = package["dependencies"]

    assert "sequelize" in dependencies
    assert "pg" in dependencies
    assert "mongoose" not in dependencies
    assert "stripe" not in dependencies
    assert "passport" not in dependencies
    assert "redis" not in dependencies
    env_example = (backend / ".env.example").read_text(encoding="utf-8")
    assert "DATABASE_URL=postgresql://" in env_example
    assert "generated_site_db" in env_example
    assert not (backend / "routes" / "subscriptionRoutes.js").exists()
    assert not (backend / "routes" / "analyticsRoutes.js").exists()


def test_generated_auth_persists_accounts_and_uses_rotating_sessions(tmp_path):
    backend = generate_backend(tmp_path, ["jwt_auth", "users", "contact"])
    controller = (backend / "controllers" / "authController.js").read_text(encoding="utf-8")
    routes = (backend / "routes" / "authRoutes.js").read_text(encoding="utf-8")
    user_model = (backend / "models" / "User.js").read_text(encoding="utf-8")

    assert "User.findOne" in controller
    assert "bcrypt.hash" in controller
    assert "bcrypt.compare" in controller
    assert "expiresIn: '15m'" in controller
    assert "RefreshSession" in controller
    assert "httpOnly: true" in controller
    assert "router.post('/refresh'" in routes
    assert "router.post('/logout'" in routes
    assert "password_hash" in user_model


def test_generated_contact_form_persists_validated_submissions(tmp_path):
    backend = generate_backend(tmp_path, ["jwt_auth", "users", "contact"])
    controller_path = backend / "controllers" / "contactController.js"
    routes_path = backend / "routes" / "contactRoutes.js"

    assert controller_path.exists()
    assert routes_path.exists()
    assert "ContactSubmission.create" in controller_path.read_text(encoding="utf-8")
    assert "express-validator" in routes_path.read_text(encoding="utf-8")
    assert (backend / "models" / "ContactSubmission.js").exists()


def test_generated_backend_has_versioned_migrations_and_auth_tests(tmp_path):
    backend = generate_backend(tmp_path, ["jwt_auth", "users", "contact"])
    package = json.loads((backend / "package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["db:migrate"]
    migrations = list((backend / "migrations").glob("*.js"))
    assert migrations
    generated_tests = backend / "tests" / "auth.test.js"
    assert generated_tests.exists()
    test_source = generated_tests.read_text(encoding="utf-8")
    assert "rejects duplicate email" in test_source
    assert "rejects invalid credentials" in test_source
    server = (backend / "server.js").read_text(encoding="utf-8")
    assert "const authRoutes = require('./routes/authRoutes')" in server
    assert "userRoutes" not in server
    assert "await connectDB()" in server


def test_explicit_stripe_feature_generates_real_checkout_and_persistent_webhook(tmp_path):
    app = tmp_path / "frontend" / "src" / "App.jsx"
    app.parent.mkdir(parents=True)
    app.write_text(
        "import React from 'react';\n"
        "import { Routes, Route } from 'react-router-dom';\n"
        "export default function App() { return <Routes><Route path=\"/\" element={<main />} /></Routes>; }\n",
        encoding="utf-8",
    )
    backend = generate_backend(tmp_path, ["jwt_auth", "users", "contact", "stripe_payments"])
    package = json.loads((backend / "package.json").read_text(encoding="utf-8"))
    server = (backend / "server.js").read_text(encoding="utf-8")
    service = (backend / "services" / "stripeService.js").read_text(encoding="utf-8")
    route = (backend / "routes" / "stripeRoutes.js").read_text(encoding="utf-8")
    migration = (backend / "migrations" / "002_payment_events.js").read_text(encoding="utf-8")
    env = (backend / ".env.example").read_text(encoding="utf-8")
    button = (
        tmp_path / "frontend" / "src" / "components" / "ecommerce"
        / "GeneratedCheckoutButton.jsx"
    )

    assert "stripe" in package["dependencies"]
    assert "app.use('/api/payments', stripeRoutes)" in server
    assert "req.rawBody = Buffer.from(buffer)" in server
    assert "stripe.checkout.sessions.create" in service
    assert "constructEvent" in service
    assert "ON CONFLICT (event_id) DO NOTHING" in service
    assert "status = 'paid'" in service
    assert "getOrderStatus" in service
    assert "req.user.id" in route
    assert "STRIPE_PRICE_ID=" in env
    assert button.exists()
    app_source = app.read_text(encoding="utf-8")
    assert 'path="/checkout"' in app_source
    assert 'path="/payment/success"' in app_source


def test_explicit_static_project_does_not_generate_backend(tmp_path):
    target = tmp_path / "static-backend"
    APIGenerator().generate_full_backend(
        target,
        {
            "layout_mode": "client-static",
            "spec": {"layout_mode": "client-static", "features": []},
        },
    )

    assert not target.exists()


def test_fullstack_metadata_does_not_inject_competing_sqlite_or_fake_payments(tmp_path):
    project = tmp_path / "project"
    (project / "frontend" / "src").mkdir(parents=True)
    (project / "backend").mkdir()

    builder = ProjectBuilder()
    builder._generate_project_meta(
        project,
        {
            "project_name": "generated-site",
            "layout_mode": "enterprise",
            "spec": {"project_name": "generated-site", "features": ["jwt_auth", "users", "contact"]},
        },
    )

    assert not (project / "backend" / "prisma" / "schema.prisma").exists()
    assert not (project / "backend" / "src" / "controllers" / "demoController.js").exists()
    root_env = (project / ".env.example").read_text(encoding="utf-8")
    backend_env = (project / "backend" / ".env.example").read_text(encoding="utf-8")
    buyer_doc = (project / "BUYER_DOCUMENTATION.md").read_text(encoding="utf-8")
    seller_kit = (project / "SELLER_KIT.md").read_text(encoding="utf-8")
    assert "DATABASE_URL=postgresql://" in root_env
    assert "STRIPE_SECRET_KEY" not in root_env
    assert "STRIPE_SECRET_KEY" not in backend_env
    assert "paid_simulation" not in root_env
    assert "No payment provider is configured" in buyer_doc
    assert "/api/v1/lemonsqueezy/webhook" not in buyer_doc
    assert "lemon.js" not in seller_kit
    builder._generate_docker_setup(project, {"project_name": "generated-site"})
    compose = (project / "docker-compose.yml").read_text(encoding="utf-8")
    assert "./database/schema.sql" not in compose
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?" in compose


def test_payment_handoff_docs_match_explicit_stripe_feature(tmp_path):
    project = tmp_path / "stripe-docs"
    (project / "frontend" / "src").mkdir(parents=True)
    (project / "backend").mkdir()
    ProjectBuilder()._generate_project_meta(
        project,
        {
            "project_name": "stripe-docs",
            "layout_mode": "enterprise",
            "spec": {
                "project_name": "stripe-docs",
                "features": ["stripe_payments"],
            },
        },
    )

    buyer_doc = (project / "BUYER_DOCUMENTATION.md").read_text(encoding="utf-8")
    assert "STRIPE_PRICE_ID" in buyer_doc
    assert "verified Stripe webhook" in buyer_doc


def test_default_fallback_scaffold_never_claims_a_mock_payment_succeeded(tmp_path):
    from unittest.mock import patch

    with patch("agent.project_builder.GENERATED_PROJECTS_DIR", tmp_path):
        builder = ProjectBuilder()
        builder._resolve_template_path = lambda _template: tmp_path / "missing-template"
        project_dir = Path(
            builder.build_project(
                {
                    "project_name": "plain-business",
                    "template": {"file_path": "missing-template"},
                    "features": [],
                    "spec": {
                        "project_name": "plain-business",
                        "website_type": "business",
                        "features": [],
                    },
                }
            )
        )

    pricing = (
        project_dir / "frontend" / "src" / "components" / "ecommerce" / "PricingTable.jsx"
    ).read_text(encoding="utf-8")
    pricing = pricing.casefold()
    assert "Thank you for purchasing" not in pricing
    assert "openLemonSqueezyCheckout" not in pricing
    assert "Buy on Lemon Squeezy" not in pricing
    assert "lemon squeezy" not in pricing
    assert "$29" not in pricing
    assert "$79" not in pricing
    assert "$199" not in pricing
    assert 'to="/contact"' in pricing

    banner = (
        project_dir / "frontend" / "src" / "components" / "common" / "ContactBanner.jsx"
    ).read_text(encoding="utf-8").casefold()
    assert "lemon squeezy" not in banner
    assert "buy template" not in banner
    assert 'to="/contact"' in banner

    faq = (
        project_dir / "frontend" / "src" / "components" / "common" / "FAQAccordion.jsx"
    ).read_text(encoding="utf-8").casefold()
    assert "lemon squeezy" not in faq
    assert "money-back guarantee" not in faq

    testimonials = (
        project_dir / "frontend" / "src" / "components" / "common" / "TestimonialGrid.jsx"
    ).read_text(encoding="utf-8")
    assert "Sarah Jenkins" not in testimonials
    assert "10,000+ Teams" not in testimonials

    frontend_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (project_dir / "frontend" / "src").rglob("*")
        if path.is_file() and path.suffix in {".js", ".jsx", ".ts", ".tsx"}
    ).casefold()
    assert "lemon squeezy" not in frontend_sources
    assert "openlemon" not in frontend_sources
    assert "open-mock-checkout" not in frontend_sources
    assert "buy template" not in frontend_sources

    buyer_docs = (project_dir / "BUYER_DOCUMENTATION.md").read_text(encoding="utf-8")
    assert "Thank you for purchasing" not in buyer_docs
    assert "No payment provider is configured" in buyer_docs


def test_explicit_stripe_feature_links_pricing_to_secure_checkout(tmp_path):
    from unittest.mock import patch

    with patch("agent.project_builder.GENERATED_PROJECTS_DIR", tmp_path):
        builder = ProjectBuilder()
        builder._resolve_template_path = lambda _template: tmp_path / "missing-template"
        project_dir = Path(
            builder.build_project(
                {
                    "project_name": "paid-business",
                    "template": {"file_path": "missing-template"},
                    "features": ["stripe_payments"],
                    "spec": {
                        "project_name": "paid-business",
                        "website_type": "business",
                        "features": ["stripe_payments"],
                    },
                }
            )
        )

    pricing = (
        project_dir / "frontend" / "src" / "components" / "ecommerce" / "PricingTable.jsx"
    ).read_text(encoding="utf-8")
    assert 'to="/checkout"' in pricing
    assert "Continue to secure checkout" in pricing
    assert "Contact us to discuss options" not in pricing


def test_fullstack_docker_waits_for_database_and_backend_readiness(tmp_path):
    project = tmp_path / "docker-ready"
    (project / "frontend").mkdir(parents=True)
    (project / "backend").mkdir()
    builder = ProjectBuilder()
    builder._generate_docker_setup(project, {"project_name": "docker-ready"})

    compose = (project / "docker-compose.yml").read_text(encoding="utf-8")
    backend = (project / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "condition: service_healthy" in compose
    assert "backend:" in compose
    assert "frontend:" in compose
    assert "pg_isready" in compose
    assert "condition: service_healthy" in compose[compose.index("frontend:"):]
    nginx = (project / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "location /api/" in nginx
    assert "proxy_pass http://backend:5000/api/" in nginx
    assert 'CMD ["node", "server.js"]' in backend


def test_fullstack_environment_examples_have_safe_required_secret_placeholders(tmp_path):
    project = tmp_path / "docker-env"
    (project / "frontend").mkdir(parents=True)
    (project / "backend").mkdir()
    builder = ProjectBuilder()
    builder._generate_project_meta(
        project,
        {
            "project_name": "docker-env",
            "layout_mode": "enterprise",
            "spec": {
                "project_name": "docker-env",
                "features": ["jwt_auth", "users", "contact"],
            },
        },
    )

    root_env = (project / ".env.example").read_text(encoding="utf-8")
    assert "POSTGRES_PASSWORD=" in root_env
    assert "JWT_SECRET=" in root_env
    assert "your-super-secret" not in root_env.lower()


def test_payment_scaffolder_requires_explicit_payment_feature(tmp_path):
    import json
    from agent.extensions.checkout_stripe import CheckoutScaffolder

    project = tmp_path / "no-payment"
    project.mkdir()
    (project / "generation-report.json").write_text(
        json.dumps({"industry": "ecommerce", "features": ["catalog", "contact"]}),
        encoding="utf-8",
    )

    result = CheckoutScaffolder(str(project)).scaffold()
    assert result["status"] == "skipped"
    assert not (project / "backend" / "routes" / "stripeRoutes.js").exists()


def test_payment_webhook_fails_closed_and_is_idempotent(tmp_path):
    from agent.extensions.checkout_stripe import _SERVICE

    assert "verified: false" not in _SERVICE
    assert "payment_events" in _SERVICE
    assert "event.id" in _SERVICE
    assert "STRIPE_WEBHOOK_SECRET is required" in _SERVICE


def test_fullstack_readme_documents_database_setup_and_startup_migrations(tmp_path):
    from agent.project_mode_engine import ProjectModeEngine

    readme = ProjectModeEngine()._enterprise_readme(
        {
            "project_name": "documented",
            "website_type": "business",
            "features": ["jwt_auth", "users", "contact"],
        },
        [],
        [],
    )

    assert "npm run db:migrate" in readme
    assert "npm run dev" in readme
    assert "docker compose up --build" in readme
