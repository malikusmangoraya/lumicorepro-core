import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .logger import agent_logger

class PathTraversalError(Exception):
    """Raised when path traversal or unsafe file access is detected."""
    pass

class FileManager:
    """Utility class for managing project workspace files with path traversal protection, safe copy, directory management, and JSON read/write."""

    @staticmethod
    def resolve_safe_path(target_path: str, allowed_base: Optional[str] = None) -> Path:
        """Resolve path and verify it stays within allowed base directory to prevent path traversal."""
        resolved = Path(target_path).resolve()

        # Reject traversal syntax even when the caller forgot to provide a root.
        # This keeps the safe-path API secure by default.
        path_parts = str(target_path).replace("\\", "/").split("/")
        if ".." in path_parts:
            raise PathTraversalError(f"Access denied: Path '{target_path}' contains traversal segments.")

        if allowed_base:
            base_resolved = Path(allowed_base).resolve()
            try:
                resolved.relative_to(base_resolved)
            except ValueError:
                agent_logger.error(f"Path Traversal Blocked: Target '{resolved}' is outside allowed base '{base_resolved}'")
                raise PathTraversalError(f"Access denied: Path '{target_path}' escapes allowed root '{allowed_base}'.")

        return resolved

    @staticmethod
    def ensure_dir(dir_path: str, allowed_base: Optional[str] = None) -> Path:
        """Ensure that directory exists safely."""
        safe_path = FileManager.resolve_safe_path(dir_path, allowed_base)
        os.makedirs(safe_path, exist_ok=True)
        return safe_path

    @staticmethod
    def copy_file(src: str, dst: str, allowed_base: Optional[str] = None) -> bool:
        """Copy a file cleanly creating target parent directories if needed with path security checks."""
        try:
            safe_src = FileManager.resolve_safe_path(src)
            safe_dst = FileManager.resolve_safe_path(dst, allowed_base)

            if not safe_src.exists():
                agent_logger.warning(f"Source file does not exist: {safe_src}")
                return False

            os.makedirs(safe_dst.parent, exist_ok=True)
            shutil.copy2(safe_src, safe_dst)
            return True
        except Exception as e:
            agent_logger.error(f"Error copying file {src} to {dst}: {e}")
            return False

    @staticmethod
    def copy_directory(src_dir: str, dst_dir: str, ignore_patterns: List[str] = None, allowed_base: Optional[str] = None) -> bool:
        """Recursively copy directory contents to destination directory with security checks."""
        try:
            safe_src = FileManager.resolve_safe_path(src_dir)
            safe_dst = FileManager.resolve_safe_path(dst_dir, allowed_base)

            if not safe_src.exists():
                agent_logger.warning(f"Source directory does not exist: {safe_src}")
                return False

            os.makedirs(safe_dst, exist_ok=True)
            ignore_func = shutil.ignore_patterns(*ignore_patterns) if ignore_patterns else None

            for item in os.listdir(safe_src):
                s = safe_src / item
                d = safe_dst / item
                if s.is_dir():
                    if ignore_patterns and any(p in item for p in ignore_patterns):
                        continue
                    shutil.copytree(s, d, dirs_exist_ok=True, ignore=ignore_func)
                else:
                    shutil.copy2(s, d)
            return True
        except Exception as e:
            agent_logger.error(f"Error copying directory {src_dir} to {dst_dir}: {e}")
            return False

    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        """Read and parse JSON file safely."""
        try:
            safe_path = FileManager.resolve_safe_path(file_path)
            if not safe_path.exists():
                agent_logger.warning(f"JSON file not found: {safe_path}")
                return {}
            with open(safe_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            agent_logger.error(f"Failed to read JSON {file_path}: {e}")
            return {}

    @staticmethod
    def write_json(file_path: str, data: Any, indent: int = 2, allowed_base: Optional[str] = None) -> bool:
        """Write Python data structure as JSON file safely."""
        try:
            safe_path = FileManager.resolve_safe_path(file_path, allowed_base)
            os.makedirs(safe_path.parent, exist_ok=True)
            with open(safe_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            agent_logger.error(f"Failed to write JSON to {file_path}: {e}")
            return False

    @staticmethod
    def read_file(file_path: str) -> str:
        """Read text file contents safely."""
        try:
            safe_path = FileManager.resolve_safe_path(file_path)
            if not safe_path.exists():
                return ""
            with open(safe_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            agent_logger.error(f"Failed to read file {file_path}: {e}")
            return ""

    @staticmethod
    def write_file(file_path: str, content: str, allowed_base: Optional[str] = None) -> bool:
        """Write text file content safely."""
        try:
            safe_path = FileManager.resolve_safe_path(file_path, allowed_base)
            os.makedirs(safe_path.parent, exist_ok=True)
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            agent_logger.error(f"Failed to write file {file_path}: {e}")
            return False

    @staticmethod
    def create_zip_archive(src_dir: str, zip_output_base: str) -> str:
        """Package target project directory into a clean .zip archive file.

        Excludes `.git`, `node_modules`, `__pycache__`, `.pytest_cache`,
        `.venv`, and `screenshots` so the deliverable stays lean and buyer-ready.
        """
        try:
            safe_src = FileManager.resolve_safe_path(src_dir)
            excludes = {".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", "screenshots"}

            def _filter(directory: Path, names: List[str]) -> List[str]:
                ignored = []
                for name in names:
                    if name in excludes:
                        ignored.append(name)
                return ignored

            archive_path = shutil.make_archive(
                zip_output_base,
                "zip",
                root_dir=str(safe_src.parent),
                base_dir=str(safe_src.name),
                filter=_filter,
            )
            agent_logger.info(f"Successfully generated ZIP archive at: {archive_path}")
            return archive_path
        except Exception as e:
            agent_logger.error(f"Failed to create ZIP archive for {src_dir}: {e}")
            return ""


