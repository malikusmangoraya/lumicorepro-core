"""GitHub Sync Service — Repository creation, commit, branch, and PR workflow.
============================================================================
Uses the GitHub REST API (v3) to:
  1. Create/fork a repository for the user
  2. Initialize with a default branch
  3. Commit generated project files into a dedicated branch (e.g. lumicore/feature-v1)
  4. Create a Pull Request with AI-generated summary

Requires: GITHUB_TOKEN or GITHUB_APP_TOKEN environment variable.
Docs: https://docs.github.com/en/rest
"""
import json
import os
import base64
import hashlib
import urllib.request
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.logger import agent_logger


GITHUB_API = "https://api.github.com"


class GitHubSyncError(Exception):
    """Raised when GitHub API operations fail."""
    pass


class GitHubService:
    """Manages GitHub repository operations for generated projects."""

    VENDOR_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".pytest_cache"}

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_APP_TOKEN") or ""
        self.enabled = bool(self.token and not self.token.startswith("your_"))

    def _request(self, method: str, path: str, data: Optional[dict] = None,
                 accept: str = "application/vnd.github+json") -> Any:
        """Make an authenticated request to the GitHub API."""
        if not self.enabled:
            raise GitHubSyncError("GitHub token not configured (set GITHUB_TOKEN)")

        url = f"{GITHUB_API}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(
            url, method=method, data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": accept,
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode()
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode() if exc.fp else str(exc)
            raise GitHubSyncError(f"GitHub API {exc.code}: {error_body}")

    def get_authenticated_user(self) -> Dict[str, Any]:
        """Get the authenticated user's info."""
        return self._request("GET", "/user")

    def create_repository(self, name: str, description: str = "", private: bool = True,
                           auto_init: bool = True) -> Dict[str, Any]:
        """Create a new repository under the authenticated user."""
        slug = name.lower().replace(" ", "-").replace("_", "-")[:63]
        payload = {
            "name": slug,
            "description": description[:512],
            "private": private,
            "auto_init": auto_init,
            "gitignore_template": "Node",
            "license_template": "mit",
        }
        result = self._request("POST", "/user/repos", payload)
        agent_logger.info(f"GitHub repo created: {result.get('full_name')} ({'private' if private else 'public'})")
        return {
            "repo_id": result.get("id"),
            "full_name": result.get("full_name"),
            "clone_url": result.get("clone_url"),
            "html_url": result.get("html_url"),
            "default_branch": result.get("default_branch"),
        }

    def create_branch(self, owner: str, repo: str, branch_name: str,
                       base_branch: str = "main") -> Dict[str, Any]:
        """Create a new branch from the base branch."""
        # Get the base branch SHA
        base = self._request("GET", f"/repos/{owner}/{repo}/branches/{base_branch}")
        sha = base.get("commit", {}).get("sha")
        if not sha:
            raise GitHubSyncError(f"Could not find base branch: {base_branch}")

        # Create ref
        payload = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        result = self._request("POST", f"/repos/{owner}/{repo}/git/refs", payload)
        agent_logger.info(f"Branch created: {branch_name} from {base_branch}")
        return {
            "branch_name": branch_name,
            "ref": result.get("ref"),
            "sha": result.get("object", {}).get("sha"),
        }

    def list_files_recursive(self, directory: str, prefix: str = "") -> List[Dict[str, Any]]:
        """List all files in a directory for commit."""
        files = []
        for entry in sorted(Path(directory).iterdir()):
            if entry.name in self.VENDOR_DIRS:
                continue
            rel = f"{prefix}/{entry.name}" if prefix else entry.name
            if entry.is_dir():
                files.extend(self._list_files_recursive(entry, rel))
            elif entry.is_file():
                size = entry.stat().st_size
                if size > 1_000_000:  # Skip files > 1MB
                    continue
                try:
                    content = entry.read_text(encoding="utf-8", errors="replace")
                    files.append({"path": rel, "content": content, "size": size})
                except Exception:
                    pass
        return files

    def _list_files_recursive(self, directory: Path, prefix: str) -> List[Dict[str, Any]]:
        files = []
        for entry in sorted(directory.iterdir()):
            if entry.name in self.VENDOR_DIRS:
                continue
            rel = f"{prefix}/{entry.name}"
            if entry.is_dir():
                files.extend(self._list_files_recursive(entry, rel))
            elif entry.is_file():
                size = entry.stat().st_size
                if size > 1_000_000:
                    continue
                try:
                    content = entry.read_text(encoding="utf-8", errors="replace")
                    files.append({"path": rel, "content": content, "size": size})
                except Exception:
                    pass
        return files

    def commit_files(self, owner: str, repo: str, branch: str,
                      files: List[Dict[str, Any]], message: str) -> Dict[str, Any]:
        """Commit all files to a branch using the Git tree API."""
        # Get latest commit SHA on branch
        branch_info = self._request("GET", f"/repos/{owner}/{repo}/branches/{branch}")
        base_sha = branch_info.get("commit", {}).get("sha")
        if not base_sha:
            raise GitHubSyncError(f"Could not find branch: {branch}")

        # Create blobs for each file
        tree_items = []
        for f in files:
            blob = self._request("POST", f"/repos/{owner}/{repo}/git/blobs", {
                "content": f["content"],
                "encoding": "utf-8",
            })
            tree_items.append({
                "path": f["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob.get("sha"),
            })

        # Create tree
        tree = self._request("POST", f"/repos/{owner}/{repo}/git/trees", {
            "base_tree": base_sha,
            "tree": tree_items,
        })

        # Create commit
        commit = self._request("POST", f"/repos/{owner}/{repo}/git/commits", {
            "message": message,
            "tree": tree.get("sha"),
            "parents": [base_sha],
        })

        # Update branch ref
        self._request("PATCH", f"/repos/{owner}/{repo}/git/refs/heads/{branch}", {
            "sha": commit.get("sha"),
        })

        agent_logger.info(f"Committed {len(files)} files to {branch}: {commit.get('sha', '')[:8]}")
        return {
            "commit_sha": commit.get("sha"),
            "commit_url": commit.get("html_url"),
            "files_count": len(files),
            "message": message,
        }

    def create_pull_request(self, owner: str, repo: str, branch: str,
                             title: str, body: str = "",
                             base: str = "main") -> Dict[str, Any]:
        """Create a Pull Request from the branch to base."""
        payload = {
            "title": title,
            "body": body,
            "head": branch,
            "base": base,
            "maintainer_can_modify": True,
        }
        result = self._request("POST", f"/repos/{owner}/{repo}/pulls", payload)
        agent_logger.info(f"PR created: #{result.get('number')} — {result.get('html_url')}")
        return {
            "pr_number": result.get("number"),
            "pr_url": result.get("html_url"),
            "title": result.get("title"),
            "state": result.get("state"),
            "diff_url": result.get("diff_url"),
        }

    def sync_project(self, project_dir: str, repo_name: str,
                      description: str = "", private: bool = True,
                      branch_name: str = "lumicore/feature-v1",
                      commit_message: str = "feat: initial LumicorePro generation",
                      pr_title: str = "",
                      pr_body: str = "") -> Dict[str, Any]:
        """Full sync: create repo → branch → commit files → create PR."""
        user = self.get_authenticated_user()
        owner = user.get("login", "")

        # Step 1: Create repo
        repo = self.create_repository(repo_name, description, private)
        repo_full = repo["full_name"]

        # Step 2: Create branch
        branch = self.create_branch(owner, repo_full.split("/")[1], branch_name,
                                     repo.get("default_branch", "main"))

        # Step 3: Collect files
        files = self.list_files_recursive(project_dir)
        agent_logger.info(f"Collected {len(files)} files for commit")

        # Step 4: Commit
        commit = self.commit_files(owner, repo_full.split("/")[1], branch_name,
                                    files, commit_message)

        # Step 5: Create PR
        pr = self.create_pull_request(
            owner, repo_full.split("/")[1], branch_name,
            title=pr_title or f"LumicorePro: {repo_name}",
            body=pr_body or f"Auto-generated by LumicorePro AI Engine.\n\n**Files:** {len(files)}\n**Commit:** {commit.get('commit_sha', '')[:8]}",
        )

        return {
            "repo": repo,
            "branch": branch,
            "commit": commit,
            "pr": pr,
            "status": "synced",
        }


def generate_pr_summary(project_dir: str) -> str:
    """Generate an AI-friendly PR summary from the project structure."""
    summary_parts = ["## LumicorePro Generated Project\n"]
    tree = []
    for entry in sorted(Path(project_dir).iterdir()):
        if entry.name in {"node_modules", ".git", "dist", "build"}:
            continue
        if entry.is_dir():
            tree.append(f"- 📁 `{entry.name}/`")
        else:
            tree.append(f"- 📄 `{entry.name}`")

    summary_parts.append("### Project Structure\n")
    summary_parts.extend(tree[:30])
    if len(tree) > 30:
        summary_parts.append(f"- ... and {len(tree) - 30} more items")

    summary_parts.append("\n### Tech Stack")
    summary_parts.append("- React 19 + Vite + Tailwind CSS 3")
    summary_parts.append("- Node.js + Express.js backend")
    summary_parts.append("- PostgreSQL database")

    summary_parts.append("\n### Quick Start")
    summary_parts.append("```bash\nnpm install\nnpm run dev\n```")

    return "\n".join(summary_parts)
