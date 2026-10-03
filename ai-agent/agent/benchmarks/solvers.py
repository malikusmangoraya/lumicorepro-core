"""Solvers: how the agent actually attempts a bug fix.

Three implementations, all behind one interface so the harness can measure the
agent, a scripted reference, or the empty baseline under identical conditions:

  * `NoOpSolver`     — changes nothing; proves the grader does not pass broken code
  * `ScriptedSolver` — replays a known patch; used by tests and by patch-replay audits
  * `AiPatchSolver`  — the real thing: provider pool → unified diff → apply → retry
                       with the real apply/parse error fed back (same self-correct
                       philosophy as `SELF_CORRECT_ENABLED` in the website pipeline)
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

from .context import ContextBundle
from .snapshots import GitResult
from .workspace import TaskWorkspace

try:  # reuse the website pipeline's diff sanitiser instead of duplicating it
    from agent.code_modifier import strip_diff_fence  # type: ignore
except Exception:  # pragma: no cover - fallback keeps the harness self-contained

    def strip_diff_fence(raw: str) -> str:  # type: ignore[misc]
        raw = (raw or "").strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        raw = raw.strip()
        if not raw.startswith("diff --git") and not raw.startswith("---"):
            first = raw.find("diff --git")
            if first >= 0:
                raw = raw[first:]
        return raw


DIFF_CONTRACT = """
Return ONE unified diff that fixes the issue. Rules:
- Start the diff with `diff --git` or `---`; no prose, no explanation, no markdown
  fences around the whole answer except a single ```diff block.
- Touch only files that exist in the context; minimal change, no refactors.
- Do not modify or add tests; the grader supplies its own.
- Include correct hunk line counts (`@@ -a,b +c,d @@`) or `git apply` will reject it.
- If a file must be created, use `new file mode` with `--- /dev/null`.
""".strip()


@dataclass
class SolveResult:
    """Outcome of one solve attempt (possibly several model rounds)."""

    patch: str = ""
    attempts: int = 0
    applied: bool = False
    declined: bool = False
    solver: str = ""
    provider: str = ""
    notes: List[str] = field(default_factory=list)
    error: str = ""
    transcript: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver": self.solver,
            "provider": self.provider,
            "attempts": self.attempts,
            "applied": self.applied,
            "declined": self.declined,
            "patch_bytes": len(self.patch.encode("utf-8", errors="replace")),
            "notes": self.notes,
            "error": self.error,
        }


class Solver(ABC):
    """Attempts to fix a task inside a workspace."""

    name = "solver"

    @abstractmethod
    def solve(
        self,
        task: Any,
        workspace: TaskWorkspace,
        bundle: ContextBundle,
        feedback: Optional[str] = None,
    ) -> SolveResult:
        """Mutate `workspace` with a candidate fix."""


class NoOpSolver(Solver):
    """Baseline: the repository is left exactly as shipped."""

    name = "noop"

    def solve(self, task, workspace, bundle, feedback=None) -> SolveResult:
        return SolveResult(solver=self.name, declined=True, notes=["baseline: no changes applied"])


class ScriptedSolver(Solver):
    """Apply a caller-supplied patch (reference replay, or a fixture in tests)."""

    name = "scripted"

    def __init__(self, patch: str = ""):
        self.patch = patch

    def solve(self, task, workspace, bundle, feedback=None) -> SolveResult:
        if not self.patch:
            return SolveResult(
                solver=self.name,
                declined=True,
                notes=["no scripted patch supplied"],
            )
        result: GitResult = workspace.apply_patch(self.patch)
        return SolveResult(
            patch=self.patch,
            attempts=1,
            applied=result.ok,
            solver=self.name,
            notes=[f"apply rc={result.returncode}", (result.stderr or result.stdout).strip()[:400]],
            error="" if result.ok else (result.stderr or "apply failed").strip()[:400],
        )


class AiPatchSolver(Solver):
    """Ask the configured provider pool for a diff; apply it; retry on failure."""

    name = "ai-patch"

    def __init__(
        self,
        provider: Any = None,
        max_attempts: int = 3,
        max_context_chars: int = 28_000,
        context_files: Optional[Dict[str, str]] = None,
    ):
        self._provider = provider
        self.max_attempts = max(1, int(max_attempts))
        self.max_context_chars = max_context_chars
        self.context_files = context_files

    def provider(self) -> Any:
        if self._provider is not None:
            return self._provider
        try:
            # Fixing a real bug in a real repo is a repair job: route it to a
            # reasoning-tier model instead of the pool's generic active one.
            from agent.ai_routing import route

            inst, name, tier = route("repair", is_repair=True)
            if inst is not None:
                agent_logger.info(f"[BENCH] solver routed to tier={tier} provider={name}")
                return inst
            from providers.provider_pool import get_pool

            return get_pool().get_active()
        except Exception as exc:
            agent_logger.warning(f"[BENCH] Provider pool unavailable: {exc}")
            return None

    def _build_prompt(self, task, bundle: ContextBundle, feedback: Optional[str]) -> str:
        parts = [
            "You are fixing a real bug in a real open-source Python repository.",
            "",
            bundle.text[: self.max_context_chars],
            "",
            DIFF_CONTRACT,
        ]
        if feedback:
            parts += ["", "## Previous attempt failed", feedback[:4000]]
        return "\n".join(parts)

    def solve(self, task, workspace, bundle, feedback=None) -> SolveResult:
        provider = self.provider()
        if provider is None:
            return SolveResult(
                solver=self.name,
                error="provider_unavailable: no active AI provider (set ACTIVE_AI_PROVIDER + key)",
                notes=["no provider in pool; nothing attempted"],
            )

        result = SolveResult(solver=self.name)
        current_feedback = feedback

        for attempt in range(1, self.max_attempts + 1):
            result.attempts = attempt
            # Rebuilt every round: the retry must carry the previous failure back.
            prompt = self._build_prompt(task, bundle, current_feedback)
            try:
                raw = provider.generate_code(prompt, self.context_files) if self.context_files else provider.generate_code(prompt)
            except Exception as exc:
                result.error = f"provider_error: {exc}"
                result.notes.append(f"attempt {attempt}: provider raised {type(exc).__name__}")
                continue

            raw_text = raw if isinstance(raw, str) else str(raw or "")
            result.transcript.append(raw_text[:2000])
            patch = strip_diff_fence(raw_text)
            if not patch.strip() or "@@" not in patch:
                result.notes.append(f"attempt {attempt}: reply contained no unified diff")
                current_feedback = (
                    "Your previous answer contained no unified diff. Reply with a single "
                    "```diff block using `diff --git` headers and `@@` hunk ranges."
                )
                continue

            applied: GitResult = workspace.apply_patch(patch)
            if applied.ok:
                result.patch = workspace.capture_patch()
                result.applied = True
                result.provider = self._provider_name(provider)
                result.notes.append(f"attempt {attempt}: patch applied cleanly")
                return result

            fallback_msg = (applied.stderr or applied.stdout or "git apply rejected the diff").strip()
            result.notes.append(f"attempt {attempt}: apply failed rc={applied.returncode}")
            current_feedback = (
                f"`git apply` rejected your diff (rc={applied.returncode}):\n"
                f"{fallback_msg[:1500]}\n\nEmit a corrected unified diff with accurate hunk headers."
            )
            agent_logger.info(f"[BENCH] {task.id} attempt {attempt} apply failed: {fallback_msg[:200]}")

        result.error = result.error or "patch_never_applied"
        return result

    @staticmethod
    def _provider_name(provider: Any) -> str:
        for attr in ("model_name", "name", "provider_name"):
            value = getattr(provider, attr, None)
            if value:
                return str(value)
        return type(provider).__name__
