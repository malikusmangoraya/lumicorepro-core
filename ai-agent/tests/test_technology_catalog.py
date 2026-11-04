import copy
import json
import importlib
import sqlite3
import sys
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = AGENT_DIR.parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))


def test_catalog_contains_supported_languages_and_frameworks():
    catalog_path = PROJECT_ROOT / "registry" / "technology-stack-catalog.json"
    assert catalog_path.is_file()

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert set(catalog["languages"]) == {
        "nodejs",
        "python",
        "php",
        "java",
        "go",
        "dotnet",
        "ruby",
        "rust",
        "elixir",
        "kotlin",
    }
    assert {item["id"] for item in catalog["languages"]["python"]["frameworks"]} == {
        "fastapi",
        "django",
        "flask",
        "litestar",
    }
    assert {item["id"] for item in catalog["languages"]["java"]["frameworks"]} == {
        "spring-boot",
        "quarkus",
        "micronaut",
    }


def test_catalog_contains_database_and_advanced_method_options():
    catalog_path = PROJECT_ROOT / "registry" / "technology-stack-catalog.json"
    assert catalog_path.is_file()

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert {
        "postgresql",
        "mysql",
        "mariadb",
        "sqlite",
        "sql-server",
        "mongodb",
    }.issubset({item["id"] for item in catalog["databases"]})
    assert "rest" in {item["id"] for item in catalog["api_styles"]}
    assert "graphql" in {item["id"] for item in catalog["api_styles"]}
    assert "grpc" in {item["id"] for item in catalog["api_styles"]}
    assert "modular-monolith" in {item["id"] for item in catalog["architectures"]}
    assert "microservices" in {item["id"] for item in catalog["architectures"]}
    assert "serverless" in {item["id"] for item in catalog["architectures"]}
    assert "redis" not in {item["id"] for item in catalog["databases"]}
    assert "redis" in {item["id"] for item in catalog["cache_options"]}
    assert catalog["orm_database_types"]["pymongo"] == ["document"]
    assert catalog["orm_database_types"]["sqlalchemy"] == ["relational"]


def test_expanded_catalog_contains_reference_inventory():
    from agent.technology_catalog import load_catalog

    catalog = load_catalog()
    frontend_ids = {item["id"] for item in catalog["frontend_frameworks"]}
    assert {
        "react-vite",
        "nextjs",
        "sveltekit",
        "nuxt",
        "astro",
        "tanstack-start",
        "react-router-framework",
        "qwik-city",
        "solidstart",
    } <= frontend_ids

    framework_ids = {
        framework["id"]
        for language in catalog["languages"].values()
        for framework in language["frameworks"]
    }
    assert {
        "hono",
        "adonisjs",
        "api-platform",
        "litestar",
        "axum",
        "actix-web",
        "chi",
        "phoenix",
    } <= framework_ids
    assert {
        "payload",
        "strapi",
        "directus",
        "appsmith",
        "budibase",
    } <= {item["id"] for item in catalog["admin_platforms"]}
    assert {
        "cloudflare-pages",
        "netlify",
        "vercel",
        "github-pages",
        "cloudflare-workers",
        "render",
        "vercel-functions",
        "firebase",
        "docker-self-hosted",
        "supabase",
        "mongodb-atlas",
    } <= {item["id"] for item in catalog["hosting_providers"]}
    assert {"github"} <= {item["id"] for item in catalog["source_control_providers"]}
    assert {"github-actions"} <= {item["id"] for item in catalog["ci_providers"]}

    testing_ids = {item["id"] for item in catalog["testing_tools"]}
    assert {
        "vitest",
        "react-testing-library",
        "jest",
        "playwright",
        "cypress",
        "lighthouse",
        "bruno",
        "postman",
        "supertest",
        "pytest",
        "phpunit",
        "junit",
        "xunit",
        "curl",
    } <= testing_ids
    assert {
        "k6",
        "owasp-zap",
        "npm-audit",
        "composer-audit",
        "pip-audit",
        "dependabot",
        "chrome-devtools",
    } <= {item["id"] for item in catalog["quality_tools"]}
    assert {
        "secure-cookie-session",
        "jwt",
        "oauth2-oidc",
        "social-login",
    } <= {item["id"] for item in catalog["authentication_profiles"]}
    assert {
        "authjs",
        "better-auth",
        "passportjs",
        "laravel-socialite",
        "spring-security-oauth2-client",
        "aspnet-oidc",
        "django-allauth",
    } <= {item["id"] for item in catalog["authentication_libraries"]}
    assert {
        "password-security",
        "rbac-abac",
        "csrf-xss",
        "sql-injection",
        "input-validation",
        "rate-limiting",
        "file-uploads",
        "email",
        "webhooks",
        "background-queues",
        "caching",
        "database-transactions",
        "search",
        "real-time-systems",
        "observability",
        "internationalization",
        "accessibility",
        "seo",
        "backups",
        "architecture",
        "scalability",
    } <= {item["id"] for item in catalog["engineering_topics"]}

    provider_ids = {item["id"] for item in catalog["hosting_providers"]}
    assert "free_tier_limits" not in provider_ids
    assert all("quota" not in item and "price" not in item for item in catalog["hosting_providers"])


def test_catalog_rejects_duplicate_option_ids():
    from agent.technology_catalog import _validate_catalog, load_catalog

    catalog = copy.deepcopy(load_catalog())
    catalog["admin_platforms"].append(copy.deepcopy(catalog["admin_platforms"][0]))

    with pytest.raises(ValueError, match="duplicate"):
        _validate_catalog(catalog)


def test_catalog_rejects_missing_required_group():
    from agent.technology_catalog import _validate_catalog, load_catalog

    catalog = copy.deepcopy(load_catalog())
    del catalog["frontend_frameworks"]

    with pytest.raises(ValueError, match="frontend_frameworks"):
        _validate_catalog(catalog)


def test_catalog_rejects_unknown_compatibility_target():
    from agent.technology_catalog import _validate_catalog, load_catalog

    catalog = copy.deepcopy(load_catalog())
    catalog["frontend_frameworks"][0]["compatibility"] = [
        {"group": "hosting_providers", "id": "unknown-host", "status": "compatible"}
    ]

    with pytest.raises(ValueError, match="compatibility"):
        _validate_catalog(catalog)


def test_catalog_rejects_invalid_compatibility_state():
    from agent.technology_catalog import _validate_catalog, load_catalog

    catalog = copy.deepcopy(load_catalog())
    catalog["frontend_frameworks"][0]["compatibility"] = [
        {"group": "hosting_providers", "id": "cloudflare-pages", "status": "maybe"}
    ]

    with pytest.raises(ValueError, match="compatibility"):
        _validate_catalog(catalog)


@pytest.mark.parametrize(
    "selection",
    [
        [],
        {"frontend_framework": []},
        {"frontend_framework": ""},
        {"testing_tools": "playwright"},
        {"testing_tools": ["playwright", 3]},
        {"unknown_field": "anything"},
        {"frontend_framework": "not-in-catalog"},
    ],
)
def test_validate_technology_choices_rejects_malformed_fields(selection):
    from agent.technology_choices import validate_technology_choices

    with pytest.raises(ValueError):
        validate_technology_choices(selection)


def test_resolve_technology_choices_matches_only_compatible_prompt_choices():
    from agent.technology_choices import resolve_technology_choices

    resolved = resolve_technology_choices(
        {"prompt": "Create a React + Vite site and deploy it to Netlify."}
    )

    assert resolved["choices"] == {
        "frontend_framework": "react-vite",
        "frontend_host": "netlify",
    }
    assert not resolved["warnings"]
    assert all(
        item["compatibility_status"] == "compatible"
        for item in resolved["resolved_options"]
    )

    unknown_pair = resolve_technology_choices(
        {"prompt": "Create a Next.js website and host it on Netlify."}
    )
    assert unknown_pair["choices"] == {"frontend_framework": "nextjs"}


def test_manual_unknown_compatibility_returns_unverified_warning():
    from agent.technology_choices import resolve_technology_choices

    resolved = resolve_technology_choices(
        {},
        {"frontend_framework": "nextjs", "frontend_host": "netlify"},
        mode="manual",
    )

    assert resolved["choices"] == {
        "frontend_framework": "nextjs",
        "frontend_host": "netlify",
    }
    assert any(
        item["compatibility_status"] == "unverified"
        for item in resolved["resolved_options"]
    )
    assert any("unverified" in warning.lower() for warning in resolved["warnings"])


def test_tool_choices_deduplicate_in_catalog_order():
    from agent.technology_choices import validate_technology_choices

    choices = validate_technology_choices(
        {"testing_tools": ["playwright", "vitest", "playwright"]}
    )

    assert choices == {"testing_tools": ["vitest", "playwright"]}

def test_firebase_is_valid_for_backend_and_database_host_choices():
    from agent.technology_choices import validate_technology_choices

    assert validate_technology_choices(
        {"backend_host": "firebase", "database_host": "firebase"}
    ) == {"backend_host": "firebase", "database_host": "firebase"}


def test_manual_choices_override_auto_recommendations():
    from agent.technology_choices import resolve_technology_choices

    resolved = resolve_technology_choices(
        {"prompt": "Create a Next.js website."},
        {"frontend_framework": "react-vite"},
        mode="manual",
    )

    assert resolved["choices"]["frontend_framework"] == "react-vite"


def test_explicitly_incompatible_manual_choices_are_rejected(monkeypatch):
    from agent import technology_choices
    from agent.technology_catalog import load_catalog

    catalog = copy.deepcopy(load_catalog())
    nextjs = next(item for item in catalog["frontend_frameworks"] if item["id"] == "nextjs")
    nextjs["compatibility"] = [
        {"group": "hosting_providers", "id": "netlify", "status": "incompatible"}
    ]
    monkeypatch.setattr(technology_choices, "load_catalog", lambda: catalog)

    with pytest.raises(ValueError, match="incompatible"):
        technology_choices.resolve_technology_choices(
            {},
            {"frontend_framework": "nextjs", "frontend_host": "netlify"},
            mode="manual",
        )


def test_omitted_technology_choices_preserve_legacy_defaults():
    from agent.tech_stack_selector import TechStackSelector

    selector = TechStackSelector()
    default_stack = selector.select({}, {}, [])
    omitted_stack = selector.select({}, {}, [], technology_choices=None)

    assert omitted_stack["backend_stack"] == default_stack["backend_stack"]
    assert omitted_stack["technology_choices"]["choices"] == {}


def test_selected_technology_choices_reach_plan_and_agent_guidance():
    from agent.planner import GenerationPlanner
    from agent.tech_stack_selector import TechStackSelector

    spec = {"prompt": "Build a Next.js site, deploy on Netlify, use secure sessions."}
    tech_stack = TechStackSelector().select(
        spec,
        {},
        [],
        technology_choices={
            "frontend_framework": "nextjs",
            "frontend_host": "netlify",
            "authentication_profile": "secure-cookie-session",
        },
    )
    plan = GenerationPlanner().create_plan(
        {"project_name": "technology-guidance"},
        {},
        [],
        {"images": [], "icons": [], "animations": []},
        {},
        [],
        tech_stack,
    )

    assert plan["technology_choices"]["choices"] == {
        "frontend_framework": "nextjs",
        "frontend_host": "netlify",
        "authentication_profile": "secure-cookie-session",
    }
    assert plan["technology_guidance"] == tech_stack["technology_guidance"]
    assert "SameSite=None requires Secure" in plan["technology_guidance"]
    assert "compatibility=unverified" in plan["technology_guidance"]


def test_catalog_loader_returns_canonical_catalog():
    from agent.technology_catalog import load_catalog

    catalog = load_catalog()

    assert catalog["version"]
    assert catalog["languages"]["nodejs"]["scaffold_supported"] is True
    assert catalog["languages"]["python"]["scaffold_supported"] is False


def test_seed_is_idempotent_and_preserves_unrelated_rows(tmp_path):
    from agent.technology_catalog import get_seeded_catalog, load_catalog, seed_technology_catalog

    db_path = tmp_path / "catalog.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE unrelated (value TEXT NOT NULL)")
    conn.execute("INSERT INTO unrelated (value) VALUES ('preserve-me')")
    cursor = conn.cursor()
    catalog = load_catalog()

    seed_technology_catalog(cursor, catalog)
    seed_technology_catalog(cursor, catalog)
    conn.commit()

    assert conn.execute("SELECT COUNT(*) FROM technology_catalog_index").fetchone()[0] == 1
    assert conn.execute("SELECT value FROM unrelated").fetchone()[0] == "preserve-me"
    conn.close()
    assert get_seeded_catalog(db_path) == catalog


def test_database_initialization_seeds_catalog_without_overwriting_other_rows(tmp_path):
    from database.init_db import init_database

    db_path = tmp_path / "agent.db"
    init_database(db_path=str(db_path))
    init_database(db_path=str(db_path))

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT catalog_json FROM technology_catalog_index WHERE catalog_id = 1"
    ).fetchone()
    assert row is not None
    assert len(json.loads(row[0])["languages"]) == 10
    conn.close()


def test_existing_database_can_be_migrated_to_include_catalog(tmp_path):
    from agent.technology_catalog import get_seeded_catalog, initialize_technology_catalog

    db_path = tmp_path / "legacy-agent.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE legacy_data (value TEXT NOT NULL)")
        conn.execute("INSERT INTO legacy_data (value) VALUES ('keep') ")

    initialize_technology_catalog(str(db_path))

    assert get_seeded_catalog(str(db_path))["languages"]["php"]["label"] == "PHP"
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT value FROM legacy_data").fetchone()[0] == "keep"


def test_catalog_read_reports_uninitialized_database(tmp_path):
    from agent.technology_catalog import get_seeded_catalog

    with pytest.raises(RuntimeError, match="not initialized"):
        get_seeded_catalog(tmp_path / "missing.db")


def _stack_resolver():
    selector = importlib.import_module("agent.tech_stack_selector")
    resolver = getattr(selector, "resolve_backend_stack", None)
    assert callable(resolver), "tech_stack_selector.resolve_backend_stack must be implemented"
    return resolver


def test_auto_preserves_existing_node_express_default():
    resolved = _stack_resolver()({"website_type": "ecommerce", "prompt": "Build a store"})

    assert (resolved["language"], resolved["framework"]) == ("nodejs", "express")
    assert resolved["database"] == "postgresql"
    assert resolved["scaffold_supported"] is True
    assert resolved["scaffold_status"] == "generated"


def test_auto_recommends_language_and_framework_named_in_prompt():
    resolved = _stack_resolver()(
        {"website_type": "saas", "prompt": "Build a Python API with FastAPI"}
    )

    assert (resolved["language"], resolved["framework"]) == ("python", "fastapi")
    assert resolved["scaffold_supported"] is False
    assert resolved["scaffold_status"] == "catalog_only_not_generated"


@pytest.mark.parametrize(
    ("language", "framework"),
    [
        ("nodejs", "express"),
        ("python", "fastapi"),
        ("php", "laravel"),
        ("java", "spring-boot"),
        ("go", "gin"),
        ("dotnet", "aspnet-core"),
        ("ruby", "rails"),
    ],
)
def test_manual_language_selection_uses_compatible_default_framework(language, framework):
    resolved = _stack_resolver()({}, {"mode": "manual", "language": language})

    assert (resolved["language"], resolved["framework"]) == (language, framework)
    assert resolved["database"] in {"postgresql", "mysql", "mariadb", "sqlite", "sql-server", "mongodb"}


def test_partial_manual_selection_overrides_database_and_keeps_recommendations():
    resolved = _stack_resolver()(
        {"website_type": "business", "prompt": "Company portal"},
        {"mode": "auto", "language": "java", "database": "mysql"},
    )

    assert resolved["language"] == "java"
    assert resolved["framework"] == "spring-boot"
    assert resolved["database"] == "mysql"


def test_rejects_framework_database_incompatible_combination():
    with pytest.raises(ValueError, match="database"):
        _stack_resolver()(
            {},
            {"mode": "manual", "language": "python", "framework": "django", "database": "mongodb"},
        )

def test_rejects_orm_incompatible_with_selected_database():
    with pytest.raises(ValueError, match="orm.*database"):
        _stack_resolver()(
            {},
            {
                "mode": "manual",
                "language": "python",
                "framework": "fastapi",
                "database": "postgresql",
                "orm": "pymongo",
            },
        )


def test_recommends_database_compatible_orm_and_database_for_manual_orm():
    resolved = _stack_resolver()(
        {},
        {
            "mode": "manual",
            "language": "python",
            "framework": "fastapi",
            "orm": "pymongo",
        },
    )

    assert resolved["database"] == "mongodb"
    assert resolved["orm"] == "pymongo"


def test_rejects_unknown_language_or_framework_ids():
    with pytest.raises(ValueError, match="language"):
        _stack_resolver()({}, {"mode": "manual", "language": "swift"})
    with pytest.raises(ValueError, match="framework"):
        _stack_resolver()({}, {"mode": "manual", "language": "python", "framework": "express"})


def test_only_node_express_reports_generated_scaffold():
    resolved = _stack_resolver()(
        {}, {"mode": "manual", "language": "nodejs", "framework": "nestjs"}
    )

    assert resolved["scaffold_supported"] is False
    assert resolved["scaffold_status"] == "catalog_only_not_generated"


def test_tech_stack_selector_includes_resolved_backend_stack():
    from agent.tech_stack_selector import TechStackSelector

    stack = TechStackSelector().select(
        {"website_type": "business"},
        {"name": "Express Base", "file_path": "backend-library/master-express-backend"},
        [],
        {"mode": "manual", "language": "python"},
    )

    assert stack["backend_stack"]["language"] == "python"
    assert stack["backend_stack"]["scaffold_status"] == "catalog_only_not_generated"


def test_planner_persists_resolved_backend_stack():
    from agent.planner import GenerationPlanner

    resolved_stack = {
        "language": "python",
        "framework": "fastapi",
        "database": "postgresql",
        "scaffold_supported": False,
        "scaffold_status": "catalog_only_not_generated",
    }
    plan = GenerationPlanner().create_plan(
        {"project_name": "stack-test", "website_type": "business"},
        {},
        [],
        {"images": [], "icons": [], "animations": []},
        {"name": "Express Base"},
        [],
        {"backend_stack": resolved_stack},
    )

    assert plan["backend_stack"] == resolved_stack
    assert plan["tech_stack"]["backend_stack"] == resolved_stack
