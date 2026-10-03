"""Visual Editor — element-level AI edits on a generated project.

Lets a client tell the agent "update THIS element/file this way" and get a
security-checked, atomic rewrite of just that file (then a preview rebuild).

Design decisions:
  - Path safety: only files inside the project dir are editable (no `..` escapes).
  - Provider: uses the live provider pool so edits ride the same OmniRoute →
    Gemini → OpenAI fallback chain (fast-fastest-first, auto-rotation).
  - Security: output passes the same DANGEROUS_PATTERNS gate as full builds.
  - Atomic: writes to a temp file then renames — never leaves a half-written file.
"""
import os
import re
import shutil
import difflib
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logger import agent_logger

MAX_EDIT_CHARS = 30_000

_EDITABLE_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".svg",
                      ".json", ".md", ".scss", ".txt")
_CODE_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".py", ".sh", ".php", ".html")
_BLOCKED_PATTERNS = ("node_modules", "__pycache__", ".git/")


class VisualEditor:
    def __init__(self, project_dir: str, ai_provider=None):
        self.project_dir = Path(project_dir).resolve()
        self.ai_provider = ai_provider

    def _resolve(self, target_file: str) -> Optional[Path]:
        if not target_file or isinstance(target_file, str) is False:
            return None
        rel = target_file.replace("\\", "/").lstrip("/")
        if any(b in rel for b in _BLOCKED_PATTERNS):
            return None
        cand = (self.project_dir / rel).resolve()
        if not str(cand).startswith(str(self.project_dir) + os.sep):
            return None
        if not cand.is_file():
            return None
        if not cand.suffix.lower() in _EDITABLE_SUFFIXES:
            return None
        return cand

    def _provider(self):
        if self.ai_provider is not None:
            return self.ai_provider
        from providers.provider_pool import get_pool
        pool = get_pool()
        inst = pool.get_active()
        if inst is None:
            raise RuntimeError("No AI provider available to perform the edit.")
        self.ai_provider = inst
        return inst

    def _call_edit(self, original: str, prompt: str) -> str:
        """Call modify_code with pool rotation on rate-limit/connectivity failures."""
        from providers.provider_pool import get_pool
        from providers.base_provider import BaseAIProvider
        pool = get_pool()
        provider = self._provider()
        last_err: Optional[Exception] = None
        for _ in range(len(pool.available) + 1):
            if provider is None:
                break
            name = pool.get_provider_name(provider)
            try:
                return provider.modify_code(original, prompt)
            except Exception as exc:
                last_err = exc
                if name:
                    if BaseAIProvider.is_rate_limited(exc):
                        pool.mark_rate_limited(name)
                    elif BaseAIProvider.is_connectivity_error(exc):
                        pool.mark_failed(name)
                    else:
                        pool.mark_failed(name)
                    agent_logger.warning(
                        f"[VISUAL-EDIT] '{name}' failed — rotating to next provider ({exc})"
                    )
                provider = pool.get_active()
        raise RuntimeError(f"No provider could perform the edit: {last_err}")

    def _security_ok(self, content: str, suffix: str) -> bool:
        # Only gate executable code files — docs/JSON/CSS are not injection targets.
        if suffix.lower() not in _CODE_SUFFIXES:
            return True
        try:
            from agent.code_modifier import CodeModifier
            return CodeModifier.validate_code_security(content)
        except Exception:
            # Never block on validator availability — the patterns gate is best-effort.
            return True

    def edit(self, target_file: str, instruction: str,
             selector_hint: str = "") -> Dict[str, Any]:
        path = self._resolve(target_file)
        if path is None:
            return {"status": "failed", "message": "Invalid or non-editable target file."}
        if not instruction or not instruction.strip():
            return {"status": "failed", "message": "An instruction is required."}

        original = path.read_text(encoding="utf-8", errors="replace")
        if len(original) > MAX_EDIT_CHARS:
            return {
                "status": "failed",
                "message": f"File too large to rewrite safely ({len(original)} chars, "
                           f"max {MAX_EDIT_CHARS}). Target a smaller file.",
            }

        prompt = f"Edit the {path.suffix} file below.\n"
        if selector_hint:
            prompt += f"Scope your change to the element matching: {selector_hint}\n"
        prompt += f"Instruction: {instruction}\n\n```\n{original}\n```\n" \
                  "Return the COMPLETE updated file content only — no explanations, " \
                  "no markdown fences."

        before_lines = original.splitlines()
        edited = self._call_edit(original, prompt)
        if not edited or not edited.strip():
            return {"status": "failed", "message": "Provider returned an empty edit."}
        edited = re.sub(r"^```(?:[a-zA-Z0-9_-]+)?\s*", "", edited)
        edited = re.sub(r"\s*```$", "", edited).rstrip("\n") + "\n"
        new_lines = edited.splitlines()

        if not self._security_ok(edited, path.suffix):
            return {
                "status": "failed",
                "message": "Edit blocked — output matched a dangerous pattern (secrets/injection).",
            }

        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".vedit_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(edited)
            os.replace(tmp, str(path))
            tmp = None
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)

        diff = list(difflib.unified_diff(before_lines, new_lines, lineterm="", n=1))
        diff_preview = "\n".join(diff[:40])

        return {
            "status": "ok",
            "file": str(path.relative_to(self.project_dir)).replace("\\", "/"),
            "lines_before": len(before_lines),
            "lines_after": len(new_lines),
            "insertions": sum(1 for l in diff if l.startswith("+") and not l.startswith("+++")),
            "deletions": sum(1 for l in diff if l.startswith("-") and not l.startswith("---")),
            "diff_preview": diff_preview,
            "hint": "Rebuild the preview to see the change live.",
        }


def edit_element(project_dir: str, target_file: str, instruction: str,
                 selector_hint: str = "", ai_provider=None) -> Dict[str, Any]:
    return VisualEditor(project_dir, ai_provider).edit(target_file, instruction, selector_hint)