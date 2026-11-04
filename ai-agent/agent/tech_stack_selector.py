import re
from typing import Dict, Any, List, Optional

from utils.logger import agent_logger
from .technology_catalog import load_catalog


SELECTION_KEYS = {
    "language",
    "framework",
    "database",
    "orm",
    "api_style",
    "architecture",
    "authentication",
    "cache",
    "queue",
    "testing",
    "observability",
    "deployment",
}


def _option_ids(catalog: Dict[str, Any], section: str) -> set:
    return {item["id"] for item in catalog[section]}


def _orm_supports_database(catalog: Dict[str, Any], orm: str, database: str) -> bool:
    database_type = next(
        (item["type"] for item in catalog["databases"] if item["id"] == database),
        None,
    )
    return database_type in catalog["orm_database_types"].get(orm, [])


def validate_backend_stack(selection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize explicit selection fields and reject unknown catalog identifiers."""
    if selection is None:
        return {"mode": "auto"}
    if not isinstance(selection, dict):
        raise ValueError("backend_stack must be an object.")

    unknown_fields = set(selection) - SELECTION_KEYS - {"mode"}
    if unknown_fields:
        raise ValueError(f"Unknown backend_stack field: {sorted(unknown_fields)[0]}.")

    mode = selection.get("mode", "auto")
    if not isinstance(mode, str) or mode not in {"auto", "manual"}:
        raise ValueError("backend_stack.mode must be 'auto' or 'manual'.")
    normalized = {"mode": mode}
    for key in SELECTION_KEYS:
        value = selection.get(key)
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"backend_stack.{key} must be a non-empty catalog ID.")
            normalized[key] = value.strip().lower()

    catalog = load_catalog()
    languages = catalog["languages"]
    language = normalized.get("language")
    framework = normalized.get("framework")
    framework_owners = {
        item["id"]: (language_id, item)
        for language_id, language_entry in languages.items()
        for item in language_entry["frameworks"]
    }
    if language and language not in languages:
        raise ValueError(f"Unknown backend_stack.language: {language}.")
    if framework and framework not in framework_owners:
        raise ValueError(f"Unknown backend_stack.framework: {framework}.")
    if language and framework and framework_owners[framework][0] != language:
        raise ValueError(
            f"backend_stack.framework '{framework}' is not compatible with language '{language}'."
        )

    selected_framework = framework_owners.get(framework, (None, None))[1]
    if selected_framework is None and language:
        selected_framework = languages[language]["frameworks"][0]
    database_ids = {item["id"] for item in catalog["databases"]}
    database = normalized.get("database")
    if database and database not in database_ids:
        raise ValueError(f"Unknown backend_stack.database: {database}.")
    if database and selected_framework and database not in selected_framework["databases"]:
        language_id = language or framework_owners[framework][0]
        if not any(
            database in item["databases"] for item in languages[language_id]["frameworks"]
        ) or framework:
            raise ValueError(
                f"backend_stack.database '{database}' is not compatible with framework "
                f"'{selected_framework['id']}'."
            )

    option_fields = {
        "orm": None,
        "api_style": "api_styles",
        "architecture": "architectures",
        "authentication": "authentication",
        "cache": "cache_options",
        "queue": "queue_options",
        "testing": "testing_options",
        "observability": "observability_options",
        "deployment": "deployment_options",
    }
    for field, section in option_fields.items():
        value = normalized.get(field)
        if not value:
            continue
        if field == "orm":
            if framework:
                compatible = selected_framework["orms"]
            elif language:
                compatible = [
                    orm
                    for entry in languages[language]["frameworks"]
                    for orm in entry["orms"]
                ]
            else:
                compatible = [
                    orm
                    for entry in framework_owners.values()
                    for orm in entry[1]["orms"]
                ]
            if value not in compatible:
                raise ValueError(f"Unknown or incompatible backend_stack.orm: {value}.")
            if database and not _orm_supports_database(catalog, value, database):
                raise ValueError(
                    f"backend_stack.orm '{value}' is not compatible with database '{database}'."
                )
        elif value not in _option_ids(catalog, section):
            raise ValueError(f"Unknown backend_stack.{field}: {value}.")
    return normalized


def _prompt_text(spec: Dict[str, Any]) -> str:
    values = [
        spec.get(key, "")
        for key in ("prompt", "description", "requirements", "website_type", "industry")
    ]
    features = spec.get("features", [])
    if isinstance(features, (list, tuple, set)):
        values.extend(features)
    return " ".join(str(value) for value in values).lower()


def _mentions(text: str, *terms: str) -> bool:
    return any(re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) for term in terms)


def _recommend_language(spec: Dict[str, Any]) -> str:
    text = _prompt_text(spec)
    recommendations = (
        ("python", ("python", "fastapi", "django", "flask")),
        ("php", ("php", "laravel", "symfony")),
        ("java", ("java", "spring boot", "quarkus", "micronaut")),
        ("go", ("golang", "gin", "echo", "fiber")),
        ("dotnet", (".net", "dotnet", "c#", "asp.net")),
        ("ruby", ("ruby", "rails", "sinatra")),
        ("nodejs", ("node.js", "nodejs", "express", "nestjs", "fastify")),
    )
    for language, terms in recommendations:
        if _mentions(text, *terms):
            return language
    return "nodejs"


def _recommend_item(spec: Dict[str, Any], options: List[Dict[str, Any]], default: str) -> str:
    text = _prompt_text(spec)
    for option in options:
        identifier = option["id"].replace("-", " ")
        label = option["label"].lower()
        if _mentions(text, identifier, label):
            return option["id"]
    return default


def resolve_backend_stack(
    spec: Dict[str, Any],
    selection: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Recommend a compatible stack, applying explicit selection dimensions."""
    catalog = load_catalog()
    normalized = validate_backend_stack(selection)
    language_catalog = catalog["languages"]
    framework_owners = {
        framework["id"]: language_id
        for language_id, language in language_catalog.items()
        for framework in language["frameworks"]
    }

    language = normalized.get("language")
    framework = normalized.get("framework")
    database = normalized.get("database")
    orm = normalized.get("orm")
    if framework and framework not in framework_owners:
        raise ValueError(f"Unknown backend_stack.framework: {framework}.")
    if language and language not in language_catalog:
        raise ValueError(f"Unknown backend_stack.language: {language}.")
    if framework and language and framework_owners[framework] != language:
        raise ValueError(
            f"backend_stack.framework '{framework}' is not compatible with language '{language}'."
        )
    if framework and not language:
        language = framework_owners[framework]
    if not language and orm:
        compatible_pairs = [
            (language_id, entry)
            for language_id, language_entry in language_catalog.items()
            for entry in language_entry["frameworks"]
            if orm in entry["orms"]
            and (
                not database
                or database in entry["databases"]
                and _orm_supports_database(catalog, orm, database)
            )
        ]
        if not compatible_pairs:
            raise ValueError(
                f"backend_stack.orm '{orm}' has no framework compatible with the selected database."
            )
        language, framework_entry = compatible_pairs[0]
        framework = framework_entry["id"]
    if not language:
        language = _recommend_language(spec)

    language_entry = language_catalog[language]
    frameworks = language_entry["frameworks"]
    known_databases = {entry["id"] for entry in catalog["databases"]}
    if database and database not in known_databases:
        raise ValueError(f"Unknown backend_stack.database: {database}.")

    if framework:
        framework_entry = next(entry for entry in frameworks if entry["id"] == framework)
    else:
        compatible_frameworks = [
            entry
            for entry in frameworks
            if (not database or database in entry["databases"])
            and (not orm or orm in entry["orms"])
            and (not orm or not database or _orm_supports_database(catalog, orm, database))
        ]
        if not compatible_frameworks:
            raise ValueError(
                f"backend_stack.framework has no option compatible with database '{database}' "
                f"and ORM '{orm}'."
            )
        recommended_framework = _recommend_item(
            spec, compatible_frameworks, compatible_frameworks[0]["id"]
        )
        framework_entry = next(
            entry for entry in compatible_frameworks if entry["id"] == recommended_framework
        )

    if not database:
        compatible_databases = [
            entry
            for entry in catalog["databases"]
            if entry["id"] in framework_entry["databases"]
            and (not orm or _orm_supports_database(catalog, orm, entry["id"]))
        ]
        if not compatible_databases:
            raise ValueError(
                f"backend_stack.orm '{orm}' has no compatible database for framework "
                f"'{framework_entry['id']}'."
            )
        database = _recommend_item(
            spec,
            compatible_databases,
            "postgresql"
            if any(entry["id"] == "postgresql" for entry in compatible_databases)
            else compatible_databases[0]["id"],
        )
    if database not in framework_entry["databases"]:
        raise ValueError(
            f"backend_stack.database '{database}' is not compatible with framework "
            f"'{framework_entry['id']}'."
        )
    if orm and not _orm_supports_database(catalog, orm, database):
        raise ValueError(
            f"backend_stack.orm '{orm}' is not compatible with database '{database}'."
        )
    if orm and orm not in framework_entry["orms"]:
        raise ValueError(
            f"backend_stack.orm '{orm}' is not compatible with framework '{framework_entry['id']}'."
        )
    if not orm:
        orm = next(
            (
                candidate
                for candidate in framework_entry["orms"]
                if _orm_supports_database(catalog, candidate, database)
            ),
            None,
        )
        if not orm:
            raise ValueError(
                f"Framework '{framework_entry['id']}' has no ORM compatible with database "
                f"'{database}'."
            )

    option_fields = {
        "api_style": ("api_styles", "rest"),
        "architecture": ("architectures", "modular-monolith"),
        "authentication": ("authentication", "jwt"),
        "cache": ("cache_options", "none"),
        "queue": ("queue_options", "none"),
        "testing": ("testing_options", "unit-integration"),
        "observability": ("observability_options", "structured-logging"),
        "deployment": ("deployment_options", "docker"),
    }
    resolved_options = {}
    for field, (section, default) in option_fields.items():
        value = normalized.get(field)
        valid_ids = _option_ids(catalog, section)
        if value and value not in valid_ids:
            raise ValueError(f"Unknown backend_stack.{field}: {value}.")
        resolved_options[field] = value or _recommend_item(spec, catalog[section], default)

    scaffold_supported = bool(
        language == "nodejs" and framework_entry["id"] == "express"
    )
    return {
        "mode": normalized["mode"],
        "language": language,
        "framework": framework_entry["id"],
        "database": database,
        "orm": orm,
        **resolved_options,
        "scaffold_supported": scaffold_supported,
        "scaffold_status": (
            "generated" if scaffold_supported else "catalog_only_not_generated"
        ),
    }

class TechStackSelector:
    """Phase 3: Optimal technology stack selection based on requirements and scale."""

    STACK_PROFILES = {
        "ecommerce": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "icons": "lucide-react"},
            "backend": {"runtime": "node", "framework": "express", "auth": "jwt+bcrypt"},
            "database": {"engine": "postgresql", "orm": "raw-sql", "cache": "optional-redis"},
            "payments": "stripe",
            "deployment": ["vercel", "railway", "render"],
        },
        "saas": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "charts": "recharts"},
            "backend": {"runtime": "node", "framework": "express", "auth": "jwt+bcrypt"},
            "database": {"engine": "postgresql", "orm": "raw-sql", "cache": "redis-recommended"},
            "payments": "stripe-subscriptions",
            "deployment": ["vercel", "aws", "gcp"],
        },
        "dashboard": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "charts": "recharts"},
            "backend": {"runtime": "node", "framework": "express", "auth": "jwt+bcrypt"},
            "database": {"engine": "postgresql", "orm": "raw-sql"},
            "deployment": ["vercel", "aws"],
        },
        "business": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "animation": "css-transitions"},
            "backend": {"runtime": "node", "framework": "express", "auth": "optional-jwt"},
            "database": {"engine": "postgresql", "orm": "raw-sql"},
            "deployment": ["vercel", "netlify"],
        },
    }

    SCALE_OVERRIDES = {
        "high_traffic": {"cache": "redis-required", "cdn": "cloudflare", "rate_limit": "strict"},
        "enterprise": {"monitoring": "datadog", "logging": "structured-json", "audit": "required"},
    }

    def select(
        self,
        spec: Dict[str, Any],
        selected_backend: Dict[str, Any],
        selected_schemas: List[Dict[str, Any]],
        backend_stack: Optional[Dict[str, Any]] = None,
        technology_choices: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Select and document optimal tech stack for the project."""
        agent_logger.info("Phase 3: Selecting optimal technology stack...")

        website_type = spec.get("website_type", "ecommerce")
        profile = self.STACK_PROFILES.get(website_type, self.STACK_PROFILES["ecommerce"])

        features = spec.get("features", [])
        resolved_backend_stack = resolve_backend_stack(spec, backend_stack)
        from agent.technology_choices import (
            format_technology_guidance,
            resolve_technology_choices,
        )

        selected_choices = (
            technology_choices
            if technology_choices is not None
            else spec.get("technology_choices")
        )
        resolved_choices = resolve_technology_choices(
            spec,
            selected_choices,
            mode="manual" if selected_choices else "auto",
        )
        technology_guidance = (
            format_technology_guidance(resolved_choices)
            if resolved_choices["resolved_options"]
            else ""
        )
        if technology_guidance:
            spec["technology_guidance"] = technology_guidance
        scale_hints = []
        if "payments" in features or "checkout" in features:
            scale_hints.append("payment_processing")
        if "admin" in features or "dashboard" in features:
            scale_hints.append("enterprise")

        stack = {
            "frontend": profile["frontend"],
            "backend": {
                **profile["backend"],
                "selected_module": selected_backend.get("name") if selected_backend else "master-express-backend",
                "module_path": selected_backend.get("file_path") if selected_backend else None,
            },
            "database": {
                **profile["database"],
                "schemas": [s.get("name") for s in selected_schemas],
                "schema_count": len(selected_schemas),
            },
            "payments": profile.get("payments"),
            "deployment_targets": profile.get("deployment", []),
            "scale_considerations": scale_hints,
            "rationale": self._build_rationale(spec, profile),
            "backend_stack": resolved_backend_stack,
            "technology_choices": resolved_choices,
            "technology_guidance": technology_guidance,
        }

        agent_logger.info(f"Tech stack selected: React+Vite frontend, {stack['backend']['selected_module']} backend.")
        return stack

    def _build_rationale(self, spec: Dict[str, Any], profile: Dict[str, Any]) -> str:
        wtype = spec.get("website_type", "project")
        return (
            f"React + Vite chosen for {wtype} due to component reuse from the shared UI library, "
            f"fast HMR, and {profile['database']['engine']} compatibility for structured data."
        )
