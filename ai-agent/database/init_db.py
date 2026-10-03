import os
import sqlite3
import json
import sys
from pathlib import Path

# Add parent directory to sys.path so imports work
current_dir = Path(__file__).resolve().parent
ai_agent_dir = current_dir.parent
if str(ai_agent_dir) not in sys.path:
    sys.path.insert(0, str(ai_agent_dir))

from config.settings import AGENT_DB_PATH, REGISTRY_DIR, PROJECT_ROOT
from utils.logger import agent_logger
from utils.file_manager import FileManager

def init_database() -> None:
    """Initialize agent.db SQLite database tables and populate from registry JSON files."""
    agent_logger.info(f"Initializing SQLite Agent Database at: {AGENT_DB_PATH}")
    os.makedirs(os.path.dirname(AGENT_DB_PATH), exist_ok=True)

    conn = sqlite3.connect(AGENT_DB_PATH)
    cursor = conn.cursor()

    # Enable WAL mode and busy timeout for concurrent access robustness
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")

    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS templates_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            industry TEXT NOT NULL,
            tags TEXT NOT NULL,
            description TEXT,
            file_path TEXT NOT NULL,
            dependencies TEXT,
            compatible_categories TEXT,
            features TEXT,
            rating REAL DEFAULT 5.0,
            usage_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS components_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT NOT NULL,
            description TEXT,
            file_path TEXT NOT NULL,
            dependencies TEXT,
            compatible_categories TEXT,
            features TEXT,
            usage_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS assets_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            industry TEXT NOT NULL,
            tags TEXT NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            usage_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS backend_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT NOT NULL,
            description TEXT,
            file_path TEXT NOT NULL,
            modules TEXT,
            dependencies TEXT,
            usage_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS database_schemas_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            file_path TEXT NOT NULL,
            tables TEXT,
            features TEXT
        );

        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            query TEXT NOT NULL,
            result_summary TEXT,
            matches_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            template_used TEXT,
            status TEXT NOT NULL,
            report_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_hash TEXT UNIQUE NOT NULL,
            provider TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Migrate pre-existing databases that predate adaptive-usage columns.
    _ensure_column(cursor, "templates_index", "usage_count", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "components_index", "usage_count", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "assets_index", "usage_count", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "backend_index", "usage_count", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "search_history", "session_id", "TEXT")

    # Seed data from registry files
    _seed_templates(cursor)
    _seed_components(cursor)
    _seed_assets(cursor)
    _seed_backend(cursor)
    _seed_schemas(cursor)

    conn.commit()
    conn.close()
    agent_logger.info("Agent Database successfully initialized and seeded.")

def _ensure_column(cursor, table: str, column: str, ddl: str) -> None:
    """Idempotently add a column to an existing table when missing."""
    try:
        cols = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            agent_logger.info(f"Migrated {table}: added {column}")
    except Exception as exc:  # pragma: no cover
        agent_logger.warning(f"Migration skipped for {table}.{column}: {exc}")

def _is_valid_template_root(fp: str, project_root: Path) -> bool:
    """A template path is valid when it is either a real Vite project root
    (package.json + index.html) or a real library template folder containing at
    least one .jsx section. This keeps broken/stale paths out while still seeding
    the 100+ UI template sections that the project builder actually assembles.
    """
    try:
        base = project_root / fp
    except (TypeError, OSError):
        return False
    if not base.is_dir():
        return False
    if (base / "package.json").exists() and (base / "index.html").exists():
        return True
    return any(base.rglob("*.jsx"))


def _seed_templates(cursor):
    path = REGISTRY_DIR / "templates.json"
    data = FileManager.read_json(str(path))
    if not isinstance(data, list):
        data = []
    # Remove stale templates whose files are gone so broken section-level copies
    # never recur in memory or the theme matrix.
    cursor.execute("SELECT id, file_path FROM templates_index")
    for row_id, fp in cursor.fetchall():
        if not fp:
            continue
        if not _is_valid_template_root(fp, PROJECT_ROOT):
            cursor.execute("DELETE FROM templates_index WHERE id = ?", (row_id,))
    for item in data:
        fp = item.get("file_path")
        if not fp:
            continue
        if not _is_valid_template_root(fp, PROJECT_ROOT):
            continue
        cursor.execute("""
            INSERT OR REPLACE INTO templates_index 
            (name, type, category, industry, tags, description, file_path, dependencies, compatible_categories, features, rating, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("name"),
            item.get("type", "template"),
            item.get("category", "general"),
            item.get("industry", "general"),
            ",".join(item.get("tags", [])),
            item.get("description", ""),
            item.get("file_path", ""),
            ",".join(item.get("dependencies", [])),
            ",".join(item.get("compatible_categories", [])),
            ",".join(item.get("features", [])),
            item.get("rating", 5.0),
            item.get("usage_count", 0)
        ))

def _seed_components(cursor):
    path = REGISTRY_DIR / "components.json"
    data = FileManager.read_json(str(path))
    if not isinstance(data, list):
        return
    # Drop stale rows whose files were removed so memory reflects the real
    # library (keeps component search free of ghost references).
    cursor.execute("SELECT name, file_path FROM components_index")
    for row_name, fp in cursor.fetchall():
        if fp and not (Path(PROJECT_ROOT) / fp).exists():
            cursor.execute("DELETE FROM components_index WHERE name = ?", (row_name,))
    for item in data:
        if not isinstance(item, dict) or not item.get("file_path"):
            continue
        if not (Path(PROJECT_ROOT) / item["file_path"]).exists():
            continue
        cursor.execute("""
            INSERT OR REPLACE INTO components_index 
            (name, type, category, tags, description, file_path, dependencies, compatible_categories, features, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("name"),
            item.get("type", "component"),
            item.get("category", "general"),
            ",".join(item.get("tags", [])),
            item.get("description", ""),
            item.get("file_path", ""),
            ",".join(item.get("dependencies", [])),
            ",".join(item.get("compatible_categories", [])),
            ",".join(item.get("features", [])),
            item.get("usage_count", 0)
        ))

def _seed_assets(cursor):
    for filename in ["icons.json", "images.json", "animations.json"]:
        path = REGISTRY_DIR / filename
        data = FileManager.read_json(str(path))
        if not isinstance(data, list):
            continue
        for item in data:
            cursor.execute("""
                INSERT OR REPLACE INTO assets_index 
                (name, type, category, industry, tags, file_path, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("name"),
                item.get("type", "asset"),
                item.get("category", "general"),
                item.get("industry", "general"),
                ",".join(item.get("tags", [])),
                item.get("file_path", ""),
                item.get("usage_count", 0)
            ))

def _seed_backend(cursor):
    path = REGISTRY_DIR / "backend-modules.json"
    data = FileManager.read_json(str(path))
    if not isinstance(data, list):
        return
    for item in data:
        cursor.execute("""
            INSERT OR REPLACE INTO backend_index 
            (name, type, category, tags, description, file_path, modules, dependencies, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("name"),
            item.get("type", "backend"),
            item.get("category", "general"),
            ",".join(item.get("tags", [])),
            item.get("description", ""),
            item.get("file_path", ""),
            ",".join(item.get("modules", [])),
            ",".join(item.get("dependencies", [])),
            item.get("usage_count", 0)
        ))

def _seed_schemas(cursor):
    schemas = [
        {"name": "E-Commerce Master Schema", "type": "schema", "category": "ecommerce", "file_path": "database/schemas/ecommerce.sql", "tables": ["carts", "cart_items", "wishlists", "orders", "order_items"], "features": ["cart", "wishlist", "checkout", "orders"]},
        {"name": "Electronics Products Schema", "type": "schema", "category": "electronics", "file_path": "database/schemas/electronics.sql", "tables": ["categories", "products"], "features": ["products", "categories", "specs"]},
        {"name": "Users & Auth Schema", "type": "schema", "category": "auth", "file_path": "database/schemas/users.sql", "tables": ["users", "addresses"], "features": ["authentication", "user_profile"]},
        {"name": "SaaS Subscription Schema", "type": "schema", "category": "saas", "file_path": "database/schemas/saas.sql", "tables": ["subscriptions", "plans", "usages"], "features": ["subscription", "billing", "plan"]},
        {"name": "Automotive / Car Dealership Schema", "type": "schema", "category": "automotive", "file_path": "database/schemas/automotive.sql", "tables": ["vehicle_brands", "vehicle_models", "test_drive_bookings", "sales_leads", "promotions", "user_favorites"], "features": ["vehicle inventory", "test drive booking", "sales leads", "car dealership", "automotive", "favorites"]},
    ]
    # Drop stale rows whose SQL file no longer exists on disk so the schema
    # index only ever advertises real, consumable DDL.
    for item in schemas:
        s_path = Path(PROJECT_ROOT) / item["file_path"]
        if not s_path.exists():
            continue
        cursor.execute("""
            INSERT OR REPLACE INTO database_schemas_index 
            (name, type, category, file_path, tables, features)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item.get("name"),
            item.get("type", "schema"),
            item.get("category", "general"),
            item.get("file_path", ""),
            ",".join(item.get("tables", [])),
            ",".join(item.get("features", []))
        ))
    cursor.execute("SELECT id, file_path FROM database_schemas_index")
    stale_ids = [row[0] for row in cursor.fetchall()
                 if row[1] and not (Path(PROJECT_ROOT) / row[1]).exists()]
    for sid in stale_ids:
        cursor.execute("DELETE FROM database_schemas_index WHERE id = ?", (sid,))

if __name__ == "__main__":
    init_database()
