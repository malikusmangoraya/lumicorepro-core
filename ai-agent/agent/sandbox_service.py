"""Sandbox Service — Serves generated project files for WebContainer mounting.

Provides the project as a mountable file tree for StackBlitz WebContainers,
enabling live npm install + npm run dev execution in the browser.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.logger import agent_logger


class SandboxService:
    """Serves project files in WebContainer-compatible format."""

    VENDOR_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".pytest_cache"}

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        if not self.project_dir.is_dir():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

    def to_mount_tree(self, max_file_size: int = 512_000) -> Dict[str, Any]:
        """Convert project directory to a nested dict for WebContainer mountFiles.

        Returns a dict like:
            {
              "package.json": {"file": {"contents": "..."}},
              "src": {
                "directory": {
                  "App.jsx": {"file": {"contents": "..."}},
                  ...
                }
              }
            }
        """
        tree: Dict[str, Any] = {}
        self._walk(self.project_dir, tree, max_file_size)
        return tree

    def _walk(self, directory: Path, tree: Dict[str, Any], max_size: int) -> None:
        for entry in sorted(directory.iterdir()):
            if entry.name in self.VENDOR_DIRS:
                continue
            if entry.is_dir():
                subtree: Dict[str, Any] = {}
                self._walk(entry, subtree, max_size)
                tree[entry.name] = {"directory": subtree}
            elif entry.is_file():
                size = entry.stat().st_size
                if size > max_size:
                    tree[entry.name] = {"file": {"contents": f"/* skipped — {size} bytes > {max_size} limit */"}}
                    continue
                try:
                    contents = entry.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    contents = f"/* binary file — {size} bytes */"
                tree[entry.name] = {"file": {"contents": contents}}

    def get_package_json(self) -> Optional[Dict[str, Any]]:
        """Read the root package.json for dependency installation."""
        pkg_path = self.project_dir / "package.json"
        if pkg_path.is_file():
            try:
                return json.loads(pkg_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def get_start_command(self) -> str:
        """Determine the dev start command from package.json scripts."""
        pkg = self.get_package_json()
        if not pkg:
            return "npm run dev"
        scripts = pkg.get("scripts", {})
        if "dev" in scripts:
            return "npm run dev"
        if "start" in scripts:
            return "npm start"
        if "serve" in scripts:
            return "npm run serve"
        return "npm run dev"

    def get_dependencies(self) -> Dict[str, str]:
        """Extract all dependencies + devDependencies."""
        pkg = self.get_package_json()
        if not pkg:
            return {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        return deps

    def get_file_list(self, max_file_size: int = 256_000) -> List[Dict[str, Any]]:
        """List all files with metadata for the file tree UI."""
        files = []
        self._list_walk(self.project_dir, "", files, max_file_size)
        return files

    def _list_walk(self, directory: Path, prefix: str, files: List[Dict], max_size: int) -> None:
        for entry in sorted(directory.iterdir()):
            rel = f"{prefix}/{entry.name}" if prefix else entry.name
            if entry.name in self.VENDOR_DIRS:
                continue
            if entry.is_dir():
                files.append({"path": rel, "type": "directory"})
                self._list_walk(entry, rel, files, max_size)
            elif entry.is_file():
                size = entry.stat().st_size
                try:
                    content = entry.read_text(encoding="utf-8", errors="replace") if size <= max_size else ""
                except Exception:
                    content = ""
                files.append({
                    "path": rel,
                    "type": "file",
                    "size": size,
                    "contents": content if size <= max_size else None,
                })

    def get_env_template(self) -> Dict[str, str]:
        """Extract .env.example as key-value pairs for the sandbox."""
        env_path = self.project_dir / ".env.example"
        if not env_path.is_file():
            return {}
        env = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip("'\"")
        return env


def get_sandbox_payload(project_dir: str) -> Dict[str, Any]:
    """Build the full sandbox payload for the frontend."""
    svc = SandboxService(project_dir)
    return {
        "mount_tree": svc.to_mount_tree(),
        "package_json": svc.get_package_json(),
        "start_command": svc.get_start_command(),
        "dependencies": svc.get_dependencies(),
        "file_list": svc.get_file_list(),
        "env_template": svc.get_env_template(),
    }
