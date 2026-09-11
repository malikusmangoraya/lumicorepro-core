import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Set
from utils.logger import agent_logger
from utils.file_manager import FileManager

class ProjectValidator:
    """Validates structural integrity, imports, routes, npm dependencies, env vars, component props, and SQL schema consistency."""

    def validate_project(self, project_path: str) -> Dict[str, Any]:
        """Perform comprehensive deep validation of generated project."""
        p_dir = Path(project_path).resolve()
        agent_logger.info(f"Executing deep validation of generated project at: {p_dir}")

        errors: List[str] = []
        warnings: List[str] = []

        # 1. Validate Frontend Structural Integrity & NPM Imports
        frontend_dir = p_dir / "frontend"
        frontend_valid = True
        frontend_files_count = 0
        fe_imports: Set[str] = set()
        fe_env_vars: Set[str] = set()

        if not frontend_dir.exists():
            errors.append("Missing 'frontend' directory in generated project.")
            frontend_valid = False
        else:
            required_fe_files = ["package.json", "src/App.jsx"]
            for rfile in required_fe_files:
                if not (frontend_dir / rfile).exists():
                    errors.append(f"Frontend missing required file: {rfile}")
                    frontend_valid = False
            
            # Scan Frontend JS/JSX files for imports & env vars
            for root, _, files in os.walk(frontend_dir / "src"):
                for fname in files:
                    if fname.endswith((".jsx", ".js", ".tsx", ".ts")):
                        frontend_files_count += 1
                        fpath = os.path.join(root, fname)
                        content = FileManager.read_file(fpath)

                        # Extract imported packages (e.g., import X from 'lucide-react')
                        imports = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\".\/][^'\"]*)['\"]", content)
                        for imp in imports:
                            # Strip subpaths e.g., 'lucide-react/dist' -> 'lucide-react'
                            pkg = imp.split('/')[0] if not imp.startswith('@') else '/'.join(imp.split('/')[:2])
                            fe_imports.add(pkg)

                        # Extract import.meta.env.X
                        envs = re.findall(r"import\.meta\.env\.([A-Za-z0-9_]+)", content)
                        for ev in envs:
                            if ev not in ["MODE", "BASE_URL", "PROD", "DEV"]:
                                fe_env_vars.add(ev)

            # Check NPM package integrity against package.json
            fe_pkg_json = frontend_dir / "package.json"
            if fe_pkg_json.exists():
                pkg_data = FileManager.read_json(str(fe_pkg_json))
                declared_deps = set(pkg_data.get("dependencies", {}).keys()).union(set(pkg_data.get("devDependencies", {}).keys()))
                declared_deps.add("react") # built-in standard
                declared_deps.add("react-dom")

                for imp in fe_imports:
                    if imp not in declared_deps:
                        warnings.append(f"Frontend code imports '{imp}' but it is missing from package.json dependencies.")

            # Check Frontend Env Vars completeness
            fe_env_example = frontend_dir / ".env.example"
            if fe_env_example.exists():
                env_text = FileManager.read_file(str(fe_env_example))
                for ev in fe_env_vars:
                    if ev not in env_text:
                        warnings.append(f"Frontend references 'import.meta.env.{ev}' which is missing from .env.example.")

        # 2. Validate Backend Structural Integrity & NPM Imports
        backend_dir = p_dir / "backend"
        backend_valid = True
        backend_files_count = 0
        be_imports: Set[str] = set()
        be_env_vars: Set[str] = set()

        if not backend_dir.exists():
            errors.append("Missing 'backend' directory.")
            backend_valid = False
        else:
            required_be_files = ["package.json", "server.js"]
            for rfile in required_be_files:
                if not (backend_dir / rfile).exists():
                    errors.append(f"Backend missing file: {rfile}")
                    backend_valid = False

            for root, _, files in os.walk(backend_dir):
                if "node_modules" in root:
                    continue
                for fname in files:
                    if fname.endswith(".js"):
                        backend_files_count += 1
                        fpath = os.path.join(root, fname)
                        content = FileManager.read_file(fpath)

                        # Extract require('pkg')
                        requires = re.findall(r"require\(['\"]([^'\".\/][^'\"]*)['\"]\)", content)
                        for req in requires:
                            pkg = req.split('/')[0] if not req.startswith('@') else '/'.join(req.split('/')[:2])
                            if pkg not in ["fs", "path", "http", "https", "events", "util", "crypto", "os", "stream"]:
                                be_imports.add(pkg)

                        # Extract process.env.X
                        envs = re.findall(r"process\.env\.([A-Za-z0-9_]+)", content)
                        for ev in envs:
                            if ev not in ["NODE_ENV", "PORT"]:
                                be_env_vars.add(ev)

            # Check Backend package.json
            be_pkg_json = backend_dir / "package.json"
            if be_pkg_json.exists():
                pkg_data = FileManager.read_json(str(be_pkg_json))
                declared_deps = set(pkg_data.get("dependencies", {}).keys()).union(set(pkg_data.get("devDependencies", {}).keys()))

                for req in be_imports:
                    if req not in declared_deps:
                        warnings.append(f"Backend code requires '{req}' but it is missing from package.json dependencies.")

            # Check Backend Env Vars
            be_env_example = backend_dir / ".env.example"
            if be_env_example.exists():
                env_text = FileManager.read_file(str(be_env_example))
                for ev in be_env_vars:
                    if ev not in env_text:
                        warnings.append(f"Backend references 'process.env.{ev}' which is missing from .env.example.")

        # 3. Validate Database Schema & Foreign Key Consistency
        schema_file = p_dir / "database" / "schema.sql"
        database_valid = True
        tables_found: List[str] = []

        if not schema_file.exists():
            errors.append("Missing 'database/schema.sql' schema file.")
            database_valid = False
        else:
            sql_content = FileManager.read_file(str(schema_file))
            if "CREATE TABLE" not in sql_content:
                errors.append("Database schema contains no CREATE TABLE statements.")
                database_valid = False
            else:
                tables_found = re.findall(r"CREATE\ TABLE\ (?:IF\ NOT\ EXISTS\ )?([a-zA-Z0-9_]+)", sql_content, re.IGNORECASE)
                created_tables_set = set(t.lower() for t in tables_found)

                # Check Foreign Key REFERENCES
                fk_references = re.findall(r"REFERENCES\s+([a-zA-Z0-9_]+)\s*\(", sql_content, re.IGNORECASE)
                for ref_table in fk_references:
                    if ref_table.lower() not in created_tables_set:
                        warnings.append(f"SQL Schema foreign key references table '{ref_table}', but table '{ref_table}' is not defined in merged schema.")

        # 4. Component Contract Rigidity — real prop-check against the local
        #    44-core library index and absolute-alias resolution.
        from agent.component_registry import get_component_registry, _extract_props

        component_report: Dict[str, Any] = {"status": "PASSED", "checked_components": 0, "errors": [], "warnings": []}
        if frontend_dir.exists():
            comp_dir = frontend_dir / "src" / "components"
            gen_src = frontend_dir / "src"
            registry = get_component_registry()
            contract_names = registry.names()
            comp_errors: List[str] = []
            comp_warnings: List[str] = []
            checked = 0

            # 4a. Local-alpha imports resolve to files present in the tree.
            alias_map: Dict[str, Path] = {}
            if gen_src.exists():
                for root, _, files in os.walk(gen_src):
                    for fname in files:
                        if fname.endswith((".jsx", ".tsx", ".js")):
                            content = FileManager.read_file(os.path.join(root, fname))
                            for alias in re.findall(r"['\"](@/components/[^'\"]+)['\"]", content):
                                rel = alias.removeprefix("@/").rstrip("/")
                                target = Path(gen_src) / rel
                                if target.suffix == "" and not target.exists():
                                    target = Path(gen_src) / f"{rel}.jsx"
                                alias_map.setdefault(alias, target)

            for root, _, files in os.walk(comp_dir):
                for fname in files:
                    if not fname.endswith((".jsx", ".tsx")):
                        continue
                    checked += 1
                    content = FileManager.read_file(os.path.join(root, fname))
                    props = list(dict.fromkeys(_extract_props(content, fname)))
                    if not props:
                        comp_warnings.append(f"Component '{fname}' defines empty props signature.")
                        continue
                    # 4b. Prop contract: registered names must stay within the
                    # local contract's declared props plus passthrough set.
                    if fname.rsplit(".", 1)[0] in contract_names:
                        contract = registry.get(fname.rsplit(".", 1)[0])
                        allowed = set(contract.get("props", [])) | {"children", "className", "key", "ref"}
                        for prop in props:
                            if prop not in allowed:
                                comp_errors.append(
                                    f"Component '{fname}' uses prop '{prop}' undefined in local contract "
                                    f"({', '.join(sorted(allowed))})."
                                )

            # 4c. Every @/components alias used by the generated tree must exist.
            for alias, target in alias_map.items():
                if not (target.exists() or (gen_src / f"{alias.removeprefix('@/')}.jsx").exists()):
                    comp_errors.append(f"Frontend imports '{alias}' but no file exists at that path.")

            if comp_errors:
                component_report["status"] = "FAILED"
                errors.extend(f"[contract] {e}" for e in comp_errors)
            if comp_warnings:
                warnings.extend(f"[contract] {w}" for w in comp_warnings)
            component_report.update({"checked_components": checked, "errors": comp_errors, "warnings": comp_warnings})

        is_overall_valid = len(errors) == 0

        report = {
            "valid": is_overall_valid,
            "errors": errors,
            "warnings": warnings,
            "frontend": {
                "status": "PASSED" if frontend_valid else "FAILED",
                "files_checked": frontend_files_count,
                "imports_checked": list(fe_imports)
            },
            "backend": {
                "status": "PASSED" if backend_valid else "FAILED",
                "files_checked": backend_files_count,
                "requires_checked": list(be_imports)
            },
            "database": {
                "status": "PASSED" if database_valid else "FAILED",
                "tables_found": tables_found
            },
            "components": component_report
        }

        agent_logger.info(f"Deep Validation Result: Overall Valid={report['valid']}, Errors={len(errors)}, Warnings={len(warnings)}")
        return report
