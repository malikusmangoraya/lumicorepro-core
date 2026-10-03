"""Production DevOps & Code Quality Gatekeeper.

Intercepts generated projects (`generated-projects/{project_id}`) after the
ProjectBuilder export step and runs format, lint, declared test scripts, and
optional build verification before release:

    1. Subprocess layer  -> spawns a Node.js background process (npm/npx) via
                           this Python shell/subprocess execution handler.
    2. Prettier rule     -> Prettier pass scoped to the generated project with an
                           explicit `--ignore-path .prettierignore` (the repo
                           `.gitignore` excludes `generated-projects/`, and Prettier
                           reads `.gitignore` even when `.prettierignore` exists, so
                           the literal `npm run format -- <path>` would be a no-op).
    3. ESLint rule       -> dedicated flat config, `--config scripts/eslint.generated.config.js`
                           (the repo root config globalIgnores `generated-projects`,
                           so a naive `npm run lint -- <path>` would silently skip files).
    4. Test runner       -> each declared npm test script runs with CI=1; missing or
                           failing test suites block deployment.
    5. Release checks    -> failed format, lint, tests, or enabled build verification
                           block deployment; diagnostic ZIP creation remains separate.
"""
import os
import re
import json
import shutil
import asyncio
import inspect
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from config.settings import PROJECT_ROOT
from utils.logger import agent_logger


class GateNotAvailableError(Exception):
    """Raised when required Node.js tooling (npm/npx) is unavailable."""


@dataclass
class CommandResult:
    """Result of a subprocess invocation."""

    command: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_secs: float = 0.0

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


# Source extensions the quality gate cares about (same scope as the repo toolchain).
PRETTIER_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".json")
LINT_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx")
VENDOR_DIR_NAMES = {
    "node_modules", "dist", "build", ".git", "venv", ".pytest_cache",
    "__pycache__", ".history", "coverage",
}


def _resolve_tool(name: str) -> Optional[str]:
    """Locate an executable, preferring the .cmd shim on Windows."""
    candidates = [name]
    if os.name == "nt":
        candidates += [f"{name}.cmd", f"{name}.exe"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _posix(path: str) -> str:
    return path.replace("\\", "/")


class DevOpsQualityGate:
    """Enforces formatting, lint, tests, and optional build checks for generated projects."""

    def __init__(
        self,
        repo_root: Optional[str] = None,
        max_heal_attempts: int = 2,
        command_timeout: int = 240,
        require_node: bool = True,
        verify_build: Optional[bool] = None,
        self_correct_enabled: Optional[bool] = None,
        self_correct_max_rounds: int = 3,
    ):
        self.repo_root = str(repo_root or PROJECT_ROOT)
        self.eslint_config = str(
            Path(self.repo_root) / "scripts" / "eslint.generated.config.js"
        )
        self.max_heal_attempts = max(0, int(max_heal_attempts))
        self.command_timeout = int(command_timeout)
        self.verify_build_enabled = bool(verify_build) if verify_build is not None else (
            os.getenv("QUALITY_GATE_VERIFY_BUILD", "0").strip().lower() in ("1", "true", "yes")
        )
        # Self-correction (Lovable/Bolt-style): loop real compiler/lint error
        # output back to the reasoning model until the build exits 0. This forces
        # `npm run build` verification even when QUALITY_GATE_VERIFY_BUILD is off.
        self.self_correct_enabled = bool(self_correct_enabled) if self_correct_enabled is not None else (
            os.getenv("SELF_CORRECT_ENABLED", "1").strip().lower() in ("1", "true", "yes")
        )
        if self.self_correct_enabled:
            self.verify_build_enabled = True
        self.self_correct_max_rounds = max(1, int(self_correct_max_rounds))
        self.npm = _resolve_tool("npm")
        self.npx = _resolve_tool("npx")
        if require_node and not self.npm:
            raise GateNotAvailableError(
                "npm executable not found on PATH; cannot run the DevOps quality gate."
            )

    # ── Async Subprocess layer ────────────────────────────────────────────────
    async def run_command(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """Execute a Node.js/npm background process asynchronously and capture its exit code."""
        cwd = cwd or self.repo_root
        command_line = " ".join(args)
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        start = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd,
                env=process_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.command_timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return CommandResult(
                    command=command_line,
                    returncode=124,
                    stdout="",
                    stderr="Command timed out",
                    timed_out=True,
                    duration_secs=round(time.time() - start, 3),
                )
            return CommandResult(
                command=command_line,
                returncode=process.returncode or 0,
                stdout=(stdout or b"").decode("utf-8", errors="replace").strip(),
                stderr=(stderr or b"").decode("utf-8", errors="replace").strip(),
                duration_secs=round(time.time() - start, 3),
            )
        except Exception as exc:
            return CommandResult(
                command=command_line,
                returncode=1,
                stdout="",
                stderr=str(exc),
                duration_secs=round(time.time() - start, 3),
            )

    # ── Tooling ──────────────────────────────────────────────────────────────
    def _source_files(self, project_dir: str, extensions: Tuple[str, ...]) -> List[str]:
        """Discover generated source files to check, excluding vendor dirs."""
        files: List[str] = []
        root = Path(project_dir)
        if not root.is_dir():
            return files
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            parts = set(path.parts)
            if parts & VENDOR_DIR_NAMES:
                continue
            if path.suffix.lower() in extensions:
                files.append(str(path))
        return sorted(files)

    def _lint_targets(self, project_dir: str) -> List[str]:
        return self._source_files(project_dir, LINT_EXTENSIONS)

    # ── Steps ────────────────────────────────────────────────────────────────
    async def format_project(self, project_dir: str, targets: Optional[List[str]] = None) -> CommandResult:
        """Prettier pass over the generated project.

        NOTE: `npm run format -- ./generated-projects/{id}` is a silent no-op
        here — Prettier reads `.gitignore` even when `.prettierignore` exists,
        and the repo `.gitignore` excludes `generated-projects/`. To genuinely
        enforce the format rule the gate invokes Prettier with an explicit
        `--ignore-path` (which replaces the gitignore fallback), so the generated
        source is reformatted before the ZIP serializer gate.

        When `targets` is given (only files touched by self-healing), Prettier
        rewrites exactly those files instead of the whole tree — the fast lane.
        """
        ignore_path = _posix(os.path.relpath(os.path.join(self.repo_root, ".prettierignore"), self.repo_root))
        npx_bin = self.npx or "npx"
        if targets:
            relative_targets = []
            for t in targets:
                absp = os.path.abspath(t)
                if absp.startswith(os.path.abspath(project_dir)):
                    rel = _posix(os.path.relpath(absp, self.repo_root))
                    if rel not in relative_targets:
                        relative_targets.append(rel)
            if not relative_targets:
                return CommandResult(
                    command="prettier (empty targets)",
                    returncode=0,
                    stdout="No files to format.",
                    stderr="",
                )
            return await self.run_command(
                [npx_bin, "prettier", "--write", "--ignore-path", ignore_path, *relative_targets],
                cwd=self.repo_root,
            )
        rel = _posix(os.path.relpath(project_dir, self.repo_root))
        return await self.run_command(
            [npx_bin, "prettier", "--write", "--ignore-path", ignore_path, "--", rel],
            cwd=self.repo_root,
        )

    async def lint_project(self, project_dir: str, targets: Optional[List[str]] = None) -> CommandResult:
        """ESLint pass with a dedicated config so generated files are truly checked.

        On Windows, expanding every file to its own argv entry blows past the
        ~32k command-line limit for backend-bearing projects ('The command line
        is too long.'). Passing the project directory as a single target lets
        ESLint resolve/expand the file set internally while the shared flat
        config still applies its `files`/`ignores` globs.

        When `targets` is given (only files touched by self-correction), lint
        exactly those files fast instead of re-scanning the whole tree.
        """
        if targets:
            relative_targets = []
            for t in targets:
                absp = os.path.abspath(t)
                if absp.startswith(os.path.abspath(project_dir)):
                    rel = _posix(os.path.relpath(absp, self.repo_root))
                    if rel not in relative_targets:
                        relative_targets.append(rel)
            if not relative_targets:
                return CommandResult(
                    command="eslint (empty targets)",
                    returncode=0,
                    stdout="No lintable files found.",
                    stderr="",
                )
            npx_bin = self.npx or "npx"
            return await self.run_command(
                [
                    npx_bin, "eslint",
                    "--no-config-lookup",
                    "--config", _posix(os.path.relpath(self.eslint_config, self.repo_root)),
                    *relative_targets,
                ],
                cwd=self.repo_root,
            )
        relative_dirs: List[str] = []
        for cand in (project_dir, os.path.join(project_dir, "frontend")):
            if os.path.isdir(cand):
                rel = _posix(os.path.relpath(cand, self.repo_root))
                if rel not in relative_dirs:
                    relative_dirs.append(rel)
        if not relative_dirs:
            return CommandResult(
                command=f"eslint ({project_dir})",
                returncode=0,
                stdout="No lintable files found.",
                stderr="",
            )
        npx_bin = self.npx or "npx"
        return await self.run_command(
            [
                npx_bin, "eslint",
                "--no-config-lookup",
                "--config", _posix(os.path.relpath(self.eslint_config, self.repo_root)),
                *relative_dirs,
            ],
            cwd=self.repo_root,
        )

    @staticmethod
    def lint_offenders(lint: CommandResult, project_dir: str) -> List[str]:
        """Extract unique relative file paths that ESLint flagged."""
        offenders: List[str] = []
        if not lint.stderr and not lint.stdout:
            return offenders
        combined = f"{lint.stdout}\n{lint.stderr}"
        for line in combined.splitlines():
            match = re.match(r"([^\s:]+?\.(?:js|jsx|ts|tsx))\s*:", line)
            if not match:
                continue
            path = _posix(match.group(1))
            if path.startswith(_posix(project_dir)) or path.startswith("generated-projects/"):
                if path not in offenders:
                    offenders.append(path)
        return offenders

    # ── Build verification (opt-in: QUALITY_GATE_VERIFY_BUILD=1) ─────────────
    def _package_roots(self, project_dir: str) -> List[str]:
        """Locate package.json roots (project root, frontend/, backend/)."""
        roots: List[str] = []
        for cand in (
            project_dir,
            os.path.join(project_dir, "frontend"),
            os.path.join(project_dir, "backend"),
        ):
            if os.path.isfile(os.path.join(cand, "package.json")):
                roots.append(cand)
        return roots

    @staticmethod
    def _has_build_script(root: str) -> bool:
        try:
            with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
                pkg = json.load(fh)
            scripts = pkg.get("scripts") or {}
            return bool(scripts.get("build"))
        except (OSError, ValueError):
            return False

    @staticmethod
    def _has_test_script(root: str) -> bool:
        try:
            with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
                pkg = json.load(fh)
            scripts = pkg.get("scripts") or {}
            return bool(scripts.get("test"))
        except (OSError, ValueError):
            return False

    async def run_tests(self, project_dir: str) -> Dict[str, Any]:
        """Run each declared package test script non-interactively in CI mode."""
        npm_bin = self.npm or "npm"
        suites: List[Dict[str, Any]] = []
        for root in self._package_roots(project_dir):
            if not self._has_test_script(root):
                continue
            rel = _posix(os.path.relpath(root, project_dir))
            result = await self.run_command(
                [npm_bin, "test"],
                cwd=root,
                env={"CI": "1", "FORCE_COLOR": "0"},
            )
            suites.append({
                "stack": rel,
                "command": result.command,
                "exit_code": result.returncode,
                "timed_out": result.timed_out,
                "duration_secs": result.duration_secs,
                "passed": result.ok,
                "output": self._tail(result),
            })
        configured = bool(suites)
        passed = configured and all(suite["passed"] for suite in suites)
        return {
            "configured": configured,
            "passed": passed,
            "status": "passed" if passed else "failed" if configured else "not_configured",
            "suites": suites,
        }

    async def verify_build(self, project_dir: str) -> Dict[str, Any]:
        """Install deps + run `npm run build` per package root (npm, not npx)."""
        npm_bin = self.npm or "npm"
        builds: List[Dict[str, Any]] = []
        for root in self._package_roots(project_dir):
            rel = _posix(os.path.relpath(root, self.repo_root))
            entry: Dict[str, Any] = {"stack": rel}
            install = await self.run_command(
                [npm_bin, "install", "--no-audit", "--no-fund", "--prefer-offline"],
                cwd=root,
            )
            entry["install_exit"] = install.returncode
            if self._has_build_script(root):
                build = await self.run_command([npm_bin, "run", "build"], cwd=root)
                entry["build_exit"] = build.returncode
                entry["build_command"] = build.command
                entry["output"] = self._tail(build)
                entry["ok"] = install.ok and build.ok
            else:
                entry["build_exit"] = None
                entry["output"] = self._tail(install)
                entry["ok"] = install.ok
            agent_logger.info(
                f"[QUALITY GATE] build verify {rel}: install={install.returncode} "
                f"build={entry['build_exit']} -> {'ok' if entry['ok'] else 'FAIL'}"
            )
            builds.append(entry)
        ok = all(b["ok"] for b in builds) if builds else True
        return {"ok": ok, "builds": builds, "verified": bool(builds)}

    # ── Orchestrated gate with self-healing loop ─────────────────────────────
    async def run_gate(
        self,
        project_dir: str,
        self_heal: Optional[Callable[[str, List[str]], Any]] = None,
        error_fixer: Optional[Callable[[str, str, int], Any]] = None,
        checkpoint: Optional[Callable[[], None]] = None,
    ) -> Dict[str, Any]:
        """Run format + lint + build verification, looping compiler errors back
        to the AI via ``error_fixer`` until every step exits 0.

        `error_fixer(project_dir, error_blob, round_idx)` is the isolated
        self-correction hook: it receives the REAL terminal output and returns a
        unified-diff fix. `self_heal(project_dir, offenders)` remains the
        offline/legacy fallback. ``checkpoint`` is a cooperative cancellation
        hook invoked between subprocess steps.

        ZIP compilation is only permitted when the final report has `passed=True`.
        """
        project_dir = str(Path(project_dir).resolve())
        if not os.path.isdir(project_dir):
            return {
                "available": bool(self.npm),
                "passed": False,
                "status": "blocked",
                "error": f"Project directory not found: {project_dir}",
                "attempts": 0,
                "format": None,
                "lint": None,
                "build_verify": {"enabled": self.verify_build_enabled, "verified": False, "ok": False, "builds": []},
                "self_heal_rounds": [],
                "self_correction": [],
                "lint_files": [],
                "github_recovery": {},
                "note": "ZIP compilation blocked by DevOps quality gate.",
            }

        fmt_result: Optional[CommandResult] = None
        lint_result: Optional[CommandResult] = None
        build_result: Optional[Dict[str, Any]] = None
        test_result: Optional[Dict[str, Any]] = None
        heal_rounds: List[Dict[str, Any]] = []
        self_correction: List[Dict[str, Any]] = []
        last_recovery: Dict[str, Any] = {}
        attempt = 0
        # Retry fast-lane keeps the offender set from the previous round so the
        # next lint/format pass scans ONLY the touched files (95s -> seconds).
        active_targets: Optional[List[str]] = None
        # AI self-correction gets its own budget; the offline self-heal loop keeps
        # the legacy bound so existing deployments behave unchanged.
        max_attempts = (
            self.self_correct_max_rounds if error_fixer is not None
            else self.max_heal_attempts
        )

        while True:
            if checkpoint is not None:
                checkpoint()
            agent_logger.info(f"[QUALITY GATE] format+lint attempt {attempt + 1} for {_posix(project_dir)}")
            fmt_result = await self.format_project(project_dir, targets=active_targets)
            lint_result = await self.lint_project(project_dir, targets=active_targets)
            passed = fmt_result.ok and lint_result.ok
            test_result = None
            if passed:
                test_result = await self.run_tests(project_dir)
                passed = bool(test_result.get("passed"))
                if not test_result.get("configured"):
                    break
            if passed and self.verify_build_enabled:
                build_result = await self.verify_build(project_dir)
                passed = build_result.get("ok", False)

            if passed or attempt >= max_attempts:
                break

            offenders = self.lint_offenders(lint_result, project_dir)
            error_blob = self._failure_blob(
                fmt_result, lint_result, build_result, test_result
            )
            agent_logger.warning(
                f"[QUALITY GATE] attempt {attempt + 1} failed "
                f"(format={fmt_result.returncode}, lint={lint_result.returncode}, "
                f"build={'fail' if build_result and not build_result.get('ok') else 'n/a'}); "
                f"feeding error output to self-correction loop."
            )
            heal_rounds.append(
                {
                    "attempt": attempt + 1,
                    "offending_files": offenders,
                    "format_exit": fmt_result.returncode,
                    "lint_exit": lint_result.returncode,
                    "build_exit": (build_result or {}).get("builds", [{}])[0].get("build_exit")
                    if build_result and build_result.get("builds") else None,
                }
            )
            # Agent Reach GitHub self-healing: when node/ESLint surfaces React 19
            # or Vite 8 breaking errors, fetch verified community patches.
            recovery = await self._github_recovery_for(lint_result, fmt_result)
            if recovery:
                last_recovery = recovery
                heal_rounds[-1]["github_recovery"] = recovery
            # Fast lane — prettier is deterministic (`--write` already ran):
            # a pure formatting failure is repaired locally, and semantic
            # (lint/build) errors alone consume the expensive AI self-correction
            # round. This avoids an LLM round-trip for auto-fixable formatting.
            semantic_failure = (
                not lint_result.ok
                or not (build_result or {}).get("ok", True)
                or bool(test_result and not test_result.get("passed"))
            )
            if not fmt_result.ok:
                try:
                    fmt_retry = await self.format_project(
                        project_dir, targets=[os.path.abspath(f) for f in offenders] or None)
                except Exception as exc:
                    agent_logger.warning(f"[QUALITY GATE] targeted prettier replay failed: {exc}")
            # Preferred path: AI feedback loop (compiler output → diff fix).
            if error_fixer is not None and semantic_failure:
                try:
                    fix = error_fixer(project_dir, error_blob, attempt)
                    self_correction.append(
                        {
                            "attempt": attempt + 1,
                            "error_chars": len(error_blob),
                            "feedback": fix,
                        }
                    )
                except Exception as exc:
                    agent_logger.error(f"[QUALITY GATE] error_fixer raised: {exc}")
                    self_correction.append({"attempt": attempt + 1, "raised": str(exc)})
            elif self_heal is not None:
                try:
                    if inspect.iscoroutinefunction(self_heal):
                        await self_heal(project_dir, offenders)
                    else:
                        self_heal(project_dir, offenders)
                except Exception as exc:  # never let healing break the loop
                    agent_logger.error(f"[QUALITY GATE] self-healing step raised: {exc}")
            # Next round touches ONLY the offenders fixed this round.
            if offenders:
                active_targets = [os.path.abspath(f) for f in offenders]
            attempt += 1

        status = "passed" if passed else "blocked"
        agent_logger.info(f"[QUALITY GATE] {status} for {_posix(project_dir)}")

        return {
            "available": bool(self.npm),
            "passed": passed,
            "status": status,
            "attempts": attempt + 1,
            "maximum_attempts": max_attempts + 1,
            "format": {
                "command": fmt_result.command,
                "exit_code": fmt_result.returncode,
                "timed_out": fmt_result.timed_out,
                "duration_secs": fmt_result.duration_secs,
                "output": self._tail(fmt_result),
            },
            "lint": {
                "command": lint_result.command,
                "exit_code": lint_result.returncode,
                "timed_out": lint_result.timed_out,
                "duration_secs": lint_result.duration_secs,
                "files_checked": len(self._lint_targets(project_dir)),
                "output": self._tail(lint_result),
            },
            "tests": test_result or {
                "configured": False,
                "passed": False,
                "status": "not_run",
                "suites": [],
            },
            "build_verify": {
                "enabled": self.verify_build_enabled,
                "verified": bool(build_result and build_result.get("verified")),
                "ok": bool(build_result and build_result.get("ok")),
                "builds": (build_result or {}).get("builds", []),
            },
            "self_heal_rounds": heal_rounds,
            "self_correction": self_correction,
            "lint_files": self.lint_offenders(lint_result, project_dir),
            "github_recovery": last_recovery,
            "note": (
                "Release checks passed (format + lint + tests + enabled build verification)."
                if passed
                else "Quality gate FAILED — release deployment blocked; diagnostic ZIP may still be created."
            ),
        }

    @staticmethod
    def _failure_blob(
        fmt_result: Optional[CommandResult],
        lint_result: Optional[CommandResult],
        build_result: Optional[Dict[str, Any]],
        test_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Assemble the REAL terminal output the AI fixer needs to see."""
        parts = []
        if build_result and build_result.get("builds"):
            for b in build_result["builds"]:
                _out = b.get("output") or ""
                if _out:
                    parts.append(f"[build:{b.get('stack')} exit={b.get('build_exit')}]\n{_out[:3000]}")
        if test_result:
            for suite in test_result.get("suites") or []:
                _out = suite.get("output") or ""
                if _out:
                    parts.append(
                        f"[test:{suite.get('stack')} exit={suite.get('exit_code')}]\n{_out[:3000]}"
                    )
        if lint_result and (lint_result.stdout or lint_result.stderr):
            parts.append(f"[eslint exit={lint_result.returncode}]\n{DevOpsQualityGate._tail(lint_result, max_chars=3000)}")
        if fmt_result and (fmt_result.stdout or fmt_result.stderr):
            parts.append(f"[prettier exit={fmt_result.returncode}]\n{DevOpsQualityGate._tail(fmt_result, max_chars=1500)}")
        return "\n\n".join(p for p in parts if p) or "No error output captured."

    @staticmethod
    def _tail(result: CommandResult, max_chars: int = 2000) -> str:
        output = f"{result.stdout}\n{result.stderr}".strip()
        if len(output) > max_chars:
            output = output[-max_chars:]
        return output

    async def _github_recovery_for(
        self,
        lint_result: CommandResult,
        fmt_result: Optional[CommandResult],
    ) -> Dict[str, Any]:
        """Async hook: fetch Agent Reach GitHub patches for React 19 / Vite 8 lint output.

        Uses ONLY the async subprocess layer (never a blocking system call) and
        never raises — on any failure it returns an empty dict so the gate's
        self-healing loop is unaffected.
        """
        blob = self._tail(lint_result)
        if fmt_result:
            blob = f"{blob}\n{self._tail(fmt_result)}"
        if not blob.strip():
            return {}
        from agent.reach.github_recovery import github_recovery_from_error, has_react19_vite_marker

        if not has_react19_vite_marker(blob):
            return {}
        try:
            return await github_recovery_from_error(blob, context="react19-vite-lint")
        except Exception as exc:
            agent_logger.warning(f"[QUALITY GATE] Agent Reach GitHub recovery skipped: {exc}")
            return {}


async def run_quality_gate(
    project_dir: str,
    self_heal: Optional[Callable[[str, List[str]], Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Drop-in helper: execute the DevOps quality gate on a generated project."""
    gate = DevOpsQualityGate(**kwargs)
    return await gate.run_gate(project_dir, self_heal=self_heal)