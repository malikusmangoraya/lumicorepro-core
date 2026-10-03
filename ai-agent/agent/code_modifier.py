import re
import os
from typing import Dict, Any, List, Optional
from utils.logger import agent_logger
from utils.file_manager import FileManager
from .component_injection import library_prompt_note


class SecurityViolationError(Exception):
    """Raised when generated code violates security policies."""
    pass


DIFF_PROMPT = """Work as a senior full-stack engineer. Apply this change:

TASK: {task}

You have the WHOLE project structure already (see PROJECT TREE). Only touch files
you actually need. NEVER rewrite the full file — return a precise git-style
Unified Diff.

FORMAT — return ONLY this, nothing else (no prose, no markdown fences):

```
diff --git a/path/to/file.jsx b/path/to/file.jsx
--- a/path/to/file.jsx
+++ b/path/to/file.jsx
@@ -start,count +start,count @@
 unchanged-context-line
-removed-line
+added-line
```

Rules:
- One `diff --git` block per file, hunks ordered top-to-bottom with exact original line offsets.
- Include 1-2 context lines around each change so the patch applies cleanly.
- Tailwind utility classes only; use the project's existing design tokens, not hardcoded hex.
- For new files: `--- /dev/null` + `new file mode 100644`.
- NO comments explaining the diff; NO markdown code fences; NO JSON wrapper.

PROJECT TREE + KEY FILE CONTENT:
{context}
""".strip()


def build_diff_prompt(task: str, vfs_context: str) -> str:
    return DIFF_PROMPT.format(task=task, context=vfs_context[:15000])


_FENCE_BLOCK_RE = re.compile(r"```[a-zA-Z0-9_+-]*[ \t]*\r?\n(.*?)```", re.DOTALL)


def strip_diff_fence(raw: str) -> str:
    """Remove markdown code fences and surrounding prose from a model reply.

    Models wrap replies in a fence *and* like to prefix a sentence ("Here is the
    updated file:"), so a naive ``startswith("```")`` check leaves the fence and
    the prose in the payload. When that payload is written straight to a source
    file it produces a file that cannot compile. Extract the fenced block from
    anywhere in the reply, preferring one that actually looks like a diff.
    """
    raw = raw.strip()
    if not raw:
        return raw

    blocks = [b.strip() for b in _FENCE_BLOCK_RE.findall(raw)]
    if blocks:
        diffish = [
            b
            for b in blocks
            if b.startswith("diff --git") or b.startswith("---") or "diff --git" in b
        ]
        raw = (diffish or blocks)[0]
    else:
        raw = re.sub(r"^\s*```[a-zA-Z0-9_+-]*[ \t]*\r?\n?", "", raw)
        raw = re.sub(r"\r?\n?\s*```\s*$", "", raw)

    raw = raw.strip()
    if not raw.startswith("diff --git") and not raw.startswith("---"):
        first = raw.find("diff --git")
        if first >= 0:
            raw = raw[first:]
    raw = raw.strip()
    # A unified diff is only valid when its last line is newline-terminated;
    # `git apply` rejects the whole patch with "corrupt patch at <stdin>:N"
    # otherwise. Same reasoning for a full source file written back out.
    if raw and not raw.endswith("\n"):
        raw += "\n"
    return raw


def has_code_fence(text: str) -> bool:
    """True when `text` still carries markdown fence markers (i.e. stripping failed)."""
    return "```" in (text or "")


class CodeModifier:
    """Modifies source code files safely with security validation and full-page generation."""

    DANGEROUS_PATTERNS = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bchild_process\b",
        r"\bsubprocess\b",
        r"\bos\.system\b",
        r"\bexecSync\b",
        r"\bspawnSync\b",
        r"\bshell_exec\b",
        r"\bprocess\.exit\b",
        r"\bfs\.unlink\b",
        r"\bfs\.rmdir\b",
        r"\bfs\.rmSync\b",
        r"\brmdirSync\b",
        r"__import__",
    ]

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    async def generate_full_page(self, project_dir: str, spec: Dict[str, Any],
                                  template_info: Dict[str, Any], components: List[Dict[str, Any]],
                                  target_file: str = "frontend/src/pages/LandingPage.jsx") -> bool:
        """
        Generate a complete React page component by combining template structure,
        component imports, and AI-driven customisation based on spec and plan.
        """
        agent_logger.info(f"Generating full AI-driven page: {target_file}")
        if not self.ai_provider:
            agent_logger.warning("No AI provider available for page generation, using template.")
            return True

        prompt = self._build_page_generation_prompt(spec, template_info, components)
        try:
            new_content = self.ai_provider.generate_code(prompt)
            if new_content and len(new_content.strip()) > 50:
                violations = self.validate_code_security(new_content)
                if violations:
                    agent_logger.error(f"Security violations in page generation: {violations}")
                    raise SecurityViolationError("; ".join(violations))
                if self.validate_syntax_balance(new_content):
                    target_path = FileManager.resolve_safe_path(
                        os.path.join(project_dir, target_file), project_dir
                    )
                    os.makedirs(target_path.parent, exist_ok=True)
                    return FileManager.write_file(str(target_path), new_content, project_dir)
            return False
        except Exception as e:
            agent_logger.warning(f"AI page generation failed: {e}")
            self._fire_github_recovery(str(e))
            return False

    def _fire_github_recovery(self, error_text: str) -> None:
        """Bind this exception hook to the Agent Reach GitHub channel (non-blocking)."""
        try:
            from agent.reach.github_recovery import fire_github_recovery

            fire_github_recovery(error_text, context="code-modifier-hook")
        except Exception:
            pass

    def _build_page_generation_prompt(self, spec, template_info, components):
        """Build a prompt for generating a full React page from context."""
        wtype = spec.get("website_type", "ecommerce")
        features = spec.get("features", [])
        component_names = [c["name"] for c in components]
        return f"""
Generate a complete React functional component (JSX) for a {wtype} landing page.
Include imports, components, and TailwindCSS classes. Do NOT use external CSS files.
Features: {", ".join(features)}
Available components: {", ".join(component_names)}

{library_prompt_note()}

Output ONLY the JSX code. Ensure proper import statements at the top.
        """.strip()


    @classmethod
    def validate_code_security(cls, code: str) -> List[str]:
        """Scan generated code for dangerous functions, execution primitives, and dangerous FS calls."""
        violations = []
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                violations.append(f"Forbidden security pattern detected: '{pattern}'")
        return violations

    @classmethod
    def validate_syntax_balance(cls, code: str) -> bool:
        """Check for balanced braces, brackets, and parentheses in JS/JSX code snippets."""
        stack = []
        matching = {')': '(', '}': '{', ']': '['}
        in_string = False
        string_char = ''
        escaped = False

        for char in code:
            if escaped:
                escaped = False
                continue

            if char == '\\':
                escaped = True
                continue

            if in_string:
                if char == string_char:
                    in_string = False
                continue

            if char in ('"', "'", '`'):
                in_string = True
                string_char = char
                continue

            if char in ('(', '{', '['):
                stack.append(char)
            elif char in (')', '}', ']'):
                if not stack or stack[-1] != matching[char]:
                    return False
                stack.pop()

        return len(stack) == 0 and not in_string

    def update_imports(self, file_path: str, new_imports: List[str]) -> bool:
        """Inject new import statements cleanly into a React/JS file."""
        content = FileManager.read_file(file_path)
        if not content:
            return False

        existing_lines = content.split("\n")
        last_import_index = 0
        for idx, line in enumerate(existing_lines):
            if line.strip().startswith("import "):
                last_import_index = idx

        for imp in new_imports:
            if imp not in content:
                existing_lines.insert(last_import_index + 1, imp)
                last_import_index += 1

        updated_content = "\n".join(existing_lines)
        return FileManager.write_file(file_path, updated_content)

    def _recovery_hint(self) -> Optional[str]:
        """Community-verified React 19 / Vite recovery reference (cache-only)."""
        try:
            from agent.reach.github_recovery import cached_github_recovery
            rec = cached_github_recovery()
        except Exception:
            return None
        if rec and rec.get("applied") and rec.get("patch_title"):
            return f"Community-verified fix reference: {rec.get('patch_title')} ({rec.get('patch_url')})"
        return None

    def _contract_instruction(self) -> str:
        """Component-contract preamble so heal/generation maps to the local library."""
        try:
            from agent.component_registry import component_contract_snippet
            return component_contract_snippet()
        except Exception:
            return ""

    def patch_file(self, file_path: str, instruction: str) -> bool:
        """Patch a file using AI provider if available, or append safe fallback code."""
        agent_logger.info(f"Patching file safely: {file_path}")
        contract = self._contract_instruction()
        if contract:
            instruction = f"{instruction}\n\n{contract}"
        hint = self._recovery_hint()
        if hint:
            instruction = f"{instruction}\n{hint}"
        content = FileManager.read_file(file_path)

        if self.ai_provider:
            try:
                # A patch/repair is the one call where a wrong answer costs a
                # whole build loop, so route it to a reasoning-tier model
                # instead of whatever the pool happens to be pointing at.
                # An explicit AI_PROVIDER/REASONING_PROVIDER still wins.
                from agent.ai_routing import offline, prefer

                if offline():
                    # AI_OFFLINE: fall through to the deterministic safe patch.
                    raise RuntimeError("AI_OFFLINE=1: provider calls disabled")
                provider, provider_name, tier = prefer(
                    "repair", f"{content}\n{instruction}", is_repair=True, explicit=self.ai_provider
                ) or (self.ai_provider, "explicit", "pinned")
                agent_logger.info(f"[ROUTER] patch_file -> tier={tier} provider={provider_name}")
                new_content, call_err = self._call_with_rotation(provider, "modify_code", content, instruction)
                if call_err is not None:
                    raise call_err
                if new_content and len(new_content.strip()) > 10:
                    # Security Audit & Syntax Sanity Validation
                    violations = self.validate_code_security(new_content)
                    if violations:
                        agent_logger.error(f"Security violations in AI response for {file_path}: {violations}")
                        raise SecurityViolationError("; ".join(violations))

                    if not self.validate_syntax_balance(new_content):
                        agent_logger.warning(f"Syntax imbalance detected in generated JS for {file_path}. Falling back to original.")
                        return False

                    return FileManager.write_file(file_path, new_content)
            except Exception as e:
                agent_logger.warning(f"AI code modification failed or rejected: {e}. Applying safe patch.")
                self._fire_github_recovery(str(e))

        # Safe fallback patch — never inject AI instruction text or review
        # comments into delivered source. Normalize the file and move on so the
        # gate can re-validate with truly clean code.
        if file_path.lower().endswith(".json"):
            body = content.strip() or "{}"
            try:
                import json as _json
                _json.loads(body)
                normalized = body + "\n"
            except Exception:
                normalized = "{}"
            return FileManager.write_file(file_path, normalized)
        normalized = "\n".join(line.rstrip() for line in content.split("\n")).rstrip() + "\n"
        return FileManager.write_file(file_path, normalized)

    def _call_with_rotation(self, provider, method_name, *args):
        """Call a provider method; on connectivity failure or an empty/short
        reply, rotate to the next live provider once and retry.

        Returns (result, None) on success or (None, exception) once retried.
        """
        from providers.base_provider import BaseAIProvider

        def _attempt(p):
            result = getattr(p, method_name)(*args)
            if isinstance(result, str) and len(result.strip()) <= 10:
                if result.strip():
                    raise ConnectionError("empty provider reply")
                return "", ConnectionError("empty provider reply")
            return result, None

        try:
            result, _err = _attempt(provider)
            return result, None
        except Exception as exc:
            if BaseAIProvider.is_connectivity_error(exc):
                try:
                    from config.providers import get_reasoning_provider
                    fresh = get_reasoning_provider()
                    if fresh is not None and fresh is not provider:
                        agent_logger.info(f"Provider rotation in code-modifier: {provider.__class__.__name__} -> {fresh.__class__.__name__}")
                        return _attempt(fresh)
                except Exception as rotate_err:
                    agent_logger.warning(f"Provider rotation failed: {rotate_err}")
            return None, exc

    # ── Revision apply: multi-change batch patch ──────────────────────────────
    def apply_revision(self, project_dir: str, changes: List[str], provider=None) -> Dict[str, Any]:
        """Apply a list of client revision changes to a generated project.

        Combines all changes into a single task, then uses VFS batch patching
        for efficiency. Returns a summary of what was patched.
        """
        if not changes:
            return {"status": "skipped", "reason": "no_changes"}

        combined_task = (
            "Apply these client revision requests to the website. "
            "Make each change precisely — do not rewrite entire files unless necessary.\n\n"
            "CHANGE REQUESTS:\n"
            + "\n".join(f"{i+1}. {c}" for i, c in enumerate(changes))
        )

        result = self.apply_ai_diff_batch(project_dir, combined_task, provider=provider)

        # Patch individual page files if AI identified specific files
        patched_files = result.get("patched_files", [])

        return {
            "status": result.get("status", "unknown"),
            "changes_applied": len(changes),
            "patched_files": patched_files,
            "diff_preview": result.get("diff", "")[:500] if result.get("diff") else "",
            "errors": result.get("errors", []),
        }

    # ── VFS batch patching (single diff across 50+ files, no per-file text swap) ──
    def apply_ai_diff_batch(
        self,
        project_dir: str,
        task: str,
        provider=None,
        max_context_files: int = None,
    ) -> Dict[str, Any]:
        """One-shot VFS diff patch: build project tree → ask model for a unified
        diff → apply hunks in-memory → persist changed files safely.

        This is the 50+ file path: the model returns a patch (tiny), the local
        Python applies it, so the context window and token budget never grow with
        the number of files.
        """
        from config.settings import AI_MAX_CONTEXT_FILES
        from agent.vfs import ProjectVFS, UnifiedDiffError

        max_context_files = max_context_files or AI_MAX_CONTEXT_FILES
        provider = provider or self.ai_provider
        if provider is None:
            return {"status": "skipped", "reason": "no_ai_provider"}

        vfs = ProjectVFS(project_dir).load()
        if not vfs.files():
            return {"status": "error", "reason": "no_files_in_project"}

        prompt = build_diff_prompt(task, vfs.to_prompt_context(max_files=max_context_files))
        raw_diff, call_err = self._call_with_rotation(provider, "generate_code", prompt)
        if call_err is not None:
            raise call_err
        if not raw_diff or len(raw_diff.strip()) < 40:
            return {"status": "error", "reason": "empty_model_reply"}

        diff_text = strip_diff_fence(raw_diff)
        violations = ProjectVFS.security_violations(diff_text)
        if violations:
            agent_logger.error(f"VFS diff rejected (security): {violations}")
            raise SecurityViolationError("; ".join(violations))

        try:
            report = vfs.apply_unified_diff(diff_text)
        except UnifiedDiffError as exc:
            agent_logger.warning(f"VFS diff parse failed: {exc}")
            return {"status": "error", "reason": str(exc), "diff_excerpt": diff_text[:500]}

        files_changed = report["applied_files"]
        if files_changed:
            written = vfs.persist()
            agent_logger.info(
                f"VFS diff applied: {len(files_changed)} file(s), {report['hunks']} hunks -> {written}"
            )
        return {
            "status": "applied" if files_changed else "no_changes",
            "files_changed": files_changed,
            "hunks": report["hunks"],
            "errors": report["errors"],
        }

    # ── Self-correction loop (isolated compiler feedback → diff fix → rebuild) ──
    def fix_from_errors(
        self,
        project_dir: str,
        error_blob: str,
        round_idx: int = 0,
        provider=None,
    ) -> Dict[str, Any]:
        """Send the actual build/lint failure output back to the reasoning model
        and have it return a unified diff that fixes ONLY those errors."""
        from config.providers import get_reasoning_provider
        provider = provider or self.ai_provider or get_reasoning_provider()
        if provider is None:
            return {"status": "skipped", "reason": "no_ai_provider"}

        task = (
            "This code failed compilation/lint with the errors below. "
            "Fix the specific imports, syntax, or class names exactly where the "
            "errors point. Do NOT restructure or rename working code.\n\n"
            f"ERROR LOG (attempt {round_idx + 1}):\n{error_blob[:4000]}\n\n"
            "Return ONLY a unified diff that resolves these errors."
        )
        return self.apply_ai_diff_batch(
            project_dir, task, provider=provider,
        )

    def self_heal_project(self, project_dir: str, offending_files: List[str]) -> int:
        """Best-effort self-healing pass on files flagged by the quality gate.

        Prefers the VFS batch-diff path (ONE AI call for ALL offending files)
        when an AI provider is available — this eliminates the old serial
        per-file AI round trip. Falls back to per-file `patch_file`, then to the
        offline deterministic repair. The quality gate re-runs format + lint
        after this pass to confirm recovery. Returns the number of files healed.
        """
        healed = 0
        seen: set = set()
        resolved: List[str] = []
        for rel_path in offending_files or []:
            candidate = rel_path if os.path.isabs(rel_path) else os.path.join(project_dir, rel_path)
            candidate = os.path.abspath(candidate)
            key = candidate.replace(os.sep, "/")
            if key in seen:
                continue
            seen.add(key)
            try:
                candidate = FileManager.resolve_safe_path(candidate, project_dir)
            except Exception as exc:
                agent_logger.warning(f"Self-heal skipped (unsafe path) {candidate}: {exc}")
                continue
            candidate = str(candidate)
            if os.path.exists(candidate):
                resolved.append(candidate)

        if not resolved:
            return 0

        # Preferred: one batched AI diff across all offending files.
        batch: Dict[str, Any] = {}
        if self.ai_provider:
            try:
                task = (
                    "Fix syntax, ESLint and formatting issues in the flagged "
                    "files below so they parse and lint cleanly. Fix the "
                    "specific problems only — do NOT restructure working code "
                    "or rewrite files wholesale.\n\n"
                    "FLAGGED FILES:\n"
                    + "\n".join(
                        os.path.relpath(f, project_dir).replace("\\", "/")
                        for f in resolved
                    )
                )
                result = self.apply_ai_diff_batch(project_dir, task)
                if result and isinstance(result, dict):
                    batch = result
                if batch.get("status") in ("applied", "no_changes"):
                    count = len(batch.get("files_changed") or [])
                    healed += count
                    agent_logger.info(
                        f"Self-heal batched AI diff: {count} file(s) changed "
                        f"({len(resolved)} flagged)"
                    )
            except Exception as exc:
                agent_logger.warning(f"Self-heal batched AI diff failed: {exc}. Falling back to per-file patch.")

            # Only per-file patch the files the batch diff did NOT touch.
            patched = set(batch.get("files_changed") or [])
        else:
            patched = set()

        for candidate in resolved:
            rel_key = os.path.relpath(candidate, project_dir).replace("\\", "/")
            if rel_key in patched or candidate.replace(os.sep, "/") in patched:
                continue
            if self.ai_provider:
                try:
                    ok = self.patch_file(
                        candidate,
                        "Fix syntax and lint issues (ESLint/Prettier) so this file parses cleanly.",
                    )
                except Exception as exc:
                    agent_logger.warning(f"Self-heal AI patch failed for {candidate}: {exc}")
                    ok = False
                if ok:
                    candidate_content = FileManager.read_file(candidate) or ""
                    if self.validate_syntax_balance(candidate_content):
                        healed += 1
                continue

            if self._repair_best_effort(candidate):
                healed += 1

        # Component-injection rigidity: rewrite raw <button> markup to the local
        # ButtonMotion wrapper so ComponentLibrary violations recover offline too.
        try:
            from agent.component_injection import inject_component_imports
            report = inject_component_imports(project_dir)
            healed += int(report.get("rewritten", 0))
        except Exception as exc:
            agent_logger.warning(f"Component-injection sweep skipped during self-heal: {exc}")

        agent_logger.info(f"Self-healing pass complete: healed {healed}/{len(offending_files or [])} file(s).")
        return healed

    @staticmethod
    def _repair_best_effort(file_path: str) -> bool:
        """Offline deterministic repair: strip trailing whitespace and normalize EOF."""
        content = FileManager.read_file(file_path)
        if not content:
            return False
        cleaned = "\n".join(line.rstrip() for line in content.split("\n")).rstrip() + "\n"
        if cleaned == content:
            return True
        return FileManager.write_file(file_path, cleaned)
