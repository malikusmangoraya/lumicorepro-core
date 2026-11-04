import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import AGENT_DB_PATH, PROJECT_ROOT

CATALOG_PATH = Path(PROJECT_ROOT) / "registry" / "technology-stack-catalog.json"
REQUIRED_LANGUAGES = {
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
OPTION_GROUPS = {
    "frontend_frameworks",
    "admin_platforms",
    "hosting_providers",
    "testing_tools",
    "quality_tools",
    "ci_providers",
    "source_control_providers",
    "authentication_profiles",
    "authentication_libraries",
    "engineering_topics",
}
CAPABILITY_STATES = {"catalog_only_not_generated", "generated", "verified"}
COMPATIBILITY_STATES = {"compatible", "incompatible", "unknown"}
REQUIRED_SECTIONS = {
    "databases",
    "api_styles",
    "architectures",
    "authentication",
    "cache_options",
    "queue_options",
    "testing_options",
    "observability_options",
    "deployment_options",
}


def _validate_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(catalog, dict) or not catalog.get("version"):
        raise ValueError("Technology catalog must be an object with a version.")

    languages = catalog.get("languages")
    if not isinstance(languages, dict) or set(languages) != REQUIRED_LANGUAGES:
        raise ValueError("Technology catalog does not contain the supported language families.")

    database_ids = {
        item.get("id")
        for item in catalog.get("databases", [])
        if isinstance(item, dict)
    }
    if "redis" in database_ids:
        raise ValueError("Redis must be cataloged as cache/queue infrastructure, not a database.")
    database_types = {
        item.get("type")
        for item in catalog.get("databases", [])
        if isinstance(item, dict) and item.get("type")
    }
    orm_ids = set()

    for section in REQUIRED_SECTIONS:
        values = catalog.get(section)
        if not isinstance(values, list) or not values:
            raise ValueError(f"Technology catalog section '{section}' must be a non-empty list.")

    option_ids = {}
    for group in OPTION_GROUPS:
        options = catalog.get(group)
        if not isinstance(options, list) or not options:
            raise ValueError(f"Technology catalog group '{group}' must be a non-empty list.")
        ids = set()
        for option in options:
            if not isinstance(option, dict):
                raise ValueError(f"Invalid option in technology catalog group '{group}'.")
            option_id = option.get("id")
            if not isinstance(option_id, str) or not option_id.strip() or option_id in ids:
                raise ValueError(f"Invalid or duplicate option ID in group '{group}'.")
            if not isinstance(option.get("label"), str) or not option["label"].strip():
                raise ValueError(f"Option '{option_id}' in group '{group}' needs a label.")
            if not isinstance(option.get("category"), str) or not option["category"].strip():
                raise ValueError(f"Option '{option_id}' in group '{group}' needs a category.")
            capability_status = option.get("capability_status")
            if (
                not isinstance(capability_status, str)
                or capability_status not in CAPABILITY_STATES
            ):
                raise ValueError(f"Option '{option_id}' in group '{group}' has an invalid capability state.")
            compatibility = option.get("compatibility")
            if not isinstance(compatibility, list):
                raise ValueError(f"Option '{option_id}' in group '{group}' needs compatibility metadata.")
            ids.add(option_id)
        option_ids[group] = ids

    backend_framework_ids = {
        framework["id"]
        for language in languages.values()
        for framework in language.get("frameworks", [])
        if isinstance(framework, dict) and isinstance(framework.get("id"), str)
    }
    option_ids["backend_frameworks"] = backend_framework_ids
    option_ids["languages"] = set(languages)
    option_ids["databases"] = database_ids

    for language_id, language in languages.items():
        if language.get("id") != language_id or not language.get("label"):
            raise ValueError(f"Invalid technology language entry: {language_id}.")
        frameworks = language.get("frameworks")
        if not isinstance(frameworks, list) or not frameworks:
            raise ValueError(f"Language '{language_id}' must provide frameworks.")
        framework_ids = set()
        for framework in frameworks:
            framework_id = framework.get("id")
            compatible_databases = framework.get("databases")
            if not framework_id or framework_id in framework_ids or not framework.get("label"):
                raise ValueError(f"Invalid or duplicate framework in language '{language_id}'.")
            if not isinstance(compatible_databases, list) or not compatible_databases:
                raise ValueError(f"Framework '{framework_id}' must define compatible databases.")
            if not set(compatible_databases).issubset(database_ids):
                raise ValueError(f"Framework '{framework_id}' references an unknown database.")
            compatible_orms = framework.get("orms")
            if not isinstance(compatible_orms, list) or not compatible_orms:
                raise ValueError(f"Framework '{framework_id}' must define ORM options.")
            if "scaffold_supported" in framework and not isinstance(
                framework["scaffold_supported"], bool
            ):
                raise ValueError(f"Framework '{framework_id}' has an invalid scaffold status.")
            orm_ids.update(compatible_orms)
            framework_ids.add(framework_id)

    for group in OPTION_GROUPS:
        for option in catalog[group]:
            seen_relationships = set()
            for relationship in option["compatibility"]:
                if not isinstance(relationship, dict):
                    raise ValueError(f"Option '{option['id']}' has invalid compatibility metadata.")
                target_group = relationship.get("group")
                target_id = relationship.get("id")
                state = relationship.get("status")
                relationship_key = (target_group, target_id)
                if (
                    not isinstance(target_group, str)
                    or target_group not in option_ids
                    or not isinstance(target_id, str)
                    or target_id not in option_ids[target_group]
                    or not isinstance(state, str)
                    or state not in COMPATIBILITY_STATES
                    or relationship_key in seen_relationships
                ):
                    raise ValueError(f"Option '{option['id']}' has invalid compatibility metadata.")
                seen_relationships.add(relationship_key)

    orm_database_types = catalog.get("orm_database_types")
    if not isinstance(orm_database_types, dict) or set(orm_database_types) != orm_ids:
        raise ValueError("Technology catalog must define database compatibility for every ORM.")
    for orm_id, compatible_types in orm_database_types.items():
        if (
            not isinstance(compatible_types, list)
            or not compatible_types
            or not set(compatible_types).issubset(database_types)
        ):
            raise ValueError(f"ORM '{orm_id}' references an unknown database type.")

    return catalog


def load_catalog() -> Dict[str, Any]:
    """Load and validate the checked-in technology stack catalog."""
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load technology catalog at {CATALOG_PATH}.") from exc
    return _validate_catalog(catalog)


def seed_technology_catalog(cursor: sqlite3.Cursor, catalog: Optional[Dict[str, Any]] = None) -> None:
    """Create/update the single SQLite catalog row without touching other registry data."""
    catalog = _validate_catalog(catalog if catalog is not None else load_catalog())
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS technology_catalog_index (
            catalog_id INTEGER PRIMARY KEY CHECK (catalog_id = 1),
            version TEXT NOT NULL,
            catalog_json TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO technology_catalog_index (catalog_id, version, catalog_json, updated_at)
        VALUES (1, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(catalog_id) DO UPDATE SET
            version = excluded.version,
            catalog_json = excluded.catalog_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (catalog["version"], json.dumps(catalog, separators=(",", ":"), sort_keys=True)),
    )


def initialize_technology_catalog(db_path: Optional[str] = None) -> None:
    """Idempotently seed the catalog into an existing agent database."""
    path = Path(db_path or AGENT_DB_PATH)
    if not path.is_file():
        raise RuntimeError(f"Technology catalog database is not initialized: {path}")
    with sqlite3.connect(str(path)) as conn:
        seed_technology_catalog(conn.cursor())


def get_seeded_catalog(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Read the catalog from SQLite; fail clearly if initialization has not run."""
    path = Path(db_path or AGENT_DB_PATH)
    if not path.is_file():
        raise RuntimeError(f"Technology catalog database is not initialized: {path}")
    try:
        with sqlite3.connect(str(path)) as conn:
            row = conn.execute(
                "SELECT catalog_json FROM technology_catalog_index WHERE catalog_id = 1"
            ).fetchone()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Technology catalog database is not initialized: {path}") from exc
    if row is None:
        raise RuntimeError(f"Technology catalog is not initialized in database: {path}")
    try:
        catalog = json.loads(row[0])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Technology catalog data is invalid in database: {path}") from exc
    return _validate_catalog(catalog)
