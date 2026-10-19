"""Retrofit missing backend/ and database/ layers into older generated projects.

Builds 020-063 were generated before enterprise mode became the default and
shipped as client-only static sites. This batch command mounts the canonical
backend-library scaffold (Express + Sequelize, PostgreSQL/MySQL ready) and the
database reference artifacts into each project that lacks them — the same mount
step the current enterprise layout pipeline performs, minus anything that would
rewrite the existing static frontend or overwrite project documentation.

Dry-run by default; pass --apply to write. Idempotent: projects that already
have backend/ + database/ are skipped untouched.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AI_AGENT_DIR = Path(__file__).resolve().parents[1] / "ai-agent"
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))
if str(AI_AGENT_DIR / "agent") not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR / "agent"))

PROJECT_ROOT = AI_AGENT_DIR.parent
GENERATED = PROJECT_ROOT / "generated-projects"

DB_README = """# Database

This project ships a versioned Sequelize schema (PostgreSQL/MySQL ready). The
backend adopts `backend/migrations/` as the canonical schema and applies them
automatically before the API begins listening. Run them manually with
`npm run db:migrate` from `backend/` when needed.

Any SQL files in `reference/` are planning inputs only; they are not applied
automatically. Incorporate required tables into versioned backend migrations
before relying on them.
"""


def find_projects_missing_backend(root: Path) -> list[Path]:
    targets = []
    if not root.is_dir():
        return targets
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if path.name in {"build", "create"} and not (path / "frontend" / "package.json").is_file():
            continue  # scratch dirs without a frontend
        project = path if (path / "frontend" / "src").is_dir() or (path / "frontend" / "package.json").is_file() else None
        if not project:
            continue
        backend = project / "backend"
        database = project / "database"
        if not (backend.is_dir() and (backend / "server.js").is_file()) or not database.is_dir():
            targets.append(project)
    return targets


def retrofit(project: Path, engine) -> dict:
    import agent.project_mode_engine as pme
    from utils.file_manager import FileManager

    copy_dirs = pme.BACKEND_COPY_DIRS
    copy_files = pme.BACKEND_COPY_FILES
    exclude_dirs = pme.BACKEND_EXCLUDE_DIRS

    spec = {
        "project_name": project.name,
        "website_type": "fullstack",
        "features": ["jwt_auth", "users", "contact"],
    }
    backend_dir = project / "backend"
    backend_dir.mkdir(exist_ok=True)

    # 1) ecommerce-base scaffold → backend/ (fresh layer, idempotent).
    ecommerce_base = PROJECT_ROOT / "backend-library" / "ecommerce-base"
    if ecommerce_base.is_dir():
        FileManager.copy_directory(
            str(ecommerce_base), str(backend_dir),
            ignore_patterns=["node_modules", ".git", "coverage", "logs"],
        )

    # 2) Canonical master-express overlay (dirs + files, no secrets).
    canonical = PROJECT_ROOT / "backend"
    mounted = 0
    if canonical.is_dir():
        for sub in copy_dirs:
            src = canonical / sub
            if src.is_dir():
                FileManager.copy_directory(
                    str(src), str(backend_dir / sub),
                    ignore_patterns=list(exclude_dirs),
                )
                mounted += 1
        for fname in copy_files:
            src = canonical / fname
            if src.is_file():
                FileManager.copy_file(str(src), str(backend_dir / fname))
                mounted += 1
    # 3) Blueprint completeness files (additive only).
    blueprint = engine._ensure_backend_blueprint_files(str(backend_dir))

    # 4) Hygiene: strip env secrets; write Postgres-ready env template.
    for env_file in (".env", ".env.production", ".env.staging"):
        env_path = backend_dir / env_file
        if env_path.is_file():
            try:
                env_path.unlink()
            except OSError:
                pass
    FileManager.write_file(
        str(backend_dir / ".env.example"),
        engine._enterprise_env_example(spec["project_name"]),
    )

    # 5) Nginx gateway + frontend axios service wiring.
    engine._write_nginx_gateway(str(project))
    frontend_package = project / "frontend" / "package.json"
    if frontend_package.is_file():
        data = json.loads(FileManager.read_file(str(frontend_package)))
        deps = data.setdefault("dependencies", {})
        if "axios" not in deps and "axios" not in data.get("devDependencies", {}):
            deps["axios"] = "^1.7.9"
            FileManager.write_json(str(frontend_package), data)

    services_dir = project / "frontend" / "src" / "services"
    services_dir.mkdir(parents=True, exist_ok=True)
    FileManager.write_file(str(services_dir / "apiConfig.js"), engine._api_config_js())
    FileManager.write_file(str(services_dir / "api.js"), engine._api_js())

    # 6) database/ artifacts: README + reference SQL schemas.
    db_dir = project / "database"
    schemas_dir = PROJECT_ROOT / "database" / "schemas"
    reference = db_dir / "reference"
    reference.mkdir(parents=True, exist_ok=True)
    if schemas_dir.is_dir():
        for sql in sorted(schemas_dir.glob("*.sql")):
            FileManager.write_file(str(reference / sql.name), FileManager.read_file(str(sql)))
    FileManager.write_file(str(db_dir / "schemas" / ".keep"), "")
    FileManager.write_file(str(db_dir / "README.md"), DB_README)

    return {
        "project": project.name,
        "backend_mounted_dirs": mounted,
        "blueprint_files": blueprint,
        "database_reference_files": len(list(reference.glob('*.sql'))),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(GENERATED), help="generated-projects root")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = parser.parse_args(argv)

    from agent.project_mode_engine import ProjectModeEngine
    import agent.project_mode_engine as pme

    engine = ProjectModeEngine()
    copy_dirs = pme.BACKEND_COPY_DIRS
    copy_files = pme.BACKEND_COPY_FILES
    exclude_dirs = pme.BACKEND_EXCLUDE_DIRS
    targets = find_projects_missing_backend(Path(args.root))
    print(f"Projects missing backend/database: {len(targets)}")
    for path in targets:
        print(f"  - {path.name}")
    if not args.apply:
        print("DRY-RUN only. Pass --apply to mount backend + database layers.")
        return 0

    results = []
    for path in targets:
        try:
            results.append(retrofit(path, engine))
            print(f"  retrofitted {path.name}")
        except Exception as exc:  # noqa: BLE001 — batch must continue
            print(f"  FAILED {path.name}: {exc}")
            results.append({"project": path.name, "error": str(exc)})

    report = PROJECT_ROOT / "generated-projects" / "RETROFIT_REPORT.json"
    report.write_text(json.dumps({"retrofitted": results}, indent=2), encoding="utf-8")
    print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
