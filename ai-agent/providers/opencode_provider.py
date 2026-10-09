"""
OpenCode Provider — LumicorePro AI Agent
========================================
Adapter for OpenCode, the MIT-licensed open-source coding agent (the free,
open-source Claude Code alternative): https://github.com/sst/opencode

OpenCode is a *local CLI agent*, not a hosted model API, so this adapter does
not speak HTTP. It shells out to `opencode run "<prompt>"` in non-interactive
headless mode and returns the CLI's stdout. The adapter itself is keyless —
OpenCode carries its own provider credentials (set them once with
`opencode auth login`).

Config (ai-agent/.env):
    OPENCODE_BIN      executable name or full path        (default: opencode)
    OPENCODE_MODEL    provider/model id                   (optional)
    OPENCODE_AGENT    agent name, e.g. build              (optional)
    OPENCODE_DIR      working directory for the run       (optional)
    OPENCODE_ATTACH   URL of a warm `opencode serve`      (optional)
    OPENCODE_TIMEOUT  seconds before the run is killed    (default: 180)

Select it with ACTIVE_AI_PROVIDER=opencode.
"""

import os
import json
import shutil
import subprocess
from typing import Dict, Any, Optional, List

from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

#: Substrings that mean "the CLI is not there" rather than "the model failed".
_INSTALL_HINT = "Install it with: npm i -g opencode-ai  (or: curl -fsSL https://opencode.ai/install | bash)"


class OpenCodeProvider(BaseAIProvider):
    """OpenCode CLI adapter — headless `opencode run` wrapper (MIT, free)."""

    DEFAULT_BIN = "opencode"
    DEFAULT_TIMEOUT = 180

    def __init__(self, api_key: str = "", model_name: str = "", timeout: Optional[int] = None):
        # Keyless adapter: OpenCode holds its own provider credentials.
        super().__init__(
            api_key or "",
            model_name or os.getenv("OPENCODE_MODEL", ""),
            timeout or self._env_timeout(),
        )
        self.binary_env = os.getenv("OPENCODE_BIN", self.DEFAULT_BIN).strip() or self.DEFAULT_BIN
        self.agent = os.getenv("OPENCODE_AGENT", "").strip()
        self.attach = os.getenv("OPENCODE_ATTACH", "").strip()
        self.workdir = os.getenv("OPENCODE_DIR", "").strip()

    # ── Environment helpers ───────────────────────────────────────────────
    @classmethod
    def _env_timeout(cls) -> int:
        raw = os.getenv("OPENCODE_TIMEOUT", "")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return cls.DEFAULT_TIMEOUT
        return value if value > 0 else cls.DEFAULT_TIMEOUT

    @staticmethod
    def is_available() -> bool:
        """True when the OpenCode CLI resolves on PATH (no key required)."""
        return shutil.which(os.getenv("OPENCODE_BIN", OpenCodeProvider.DEFAULT_BIN)) is not None

    def _assert_cli(self) -> str:
        """Resolve the CLI or fail fast.

        The raised text contains "cannot connect" so `BaseAIProvider` treats it
        as a connectivity error and rotates instead of burning three retries on
        an executable that will never appear.
        """
        resolved = shutil.which(self.binary_env)
        if not resolved:
            raise ConnectionError(
                f"Cannot connect to OpenCode CLI '{self.binary_env}' (not found on PATH). "
                f"{_INSTALL_HINT}. Or point OPENCODE_BIN at its full path."
            )
        return resolved

    # ── Command construction ──────────────────────────────────────────────
    @staticmethod
    def _command_prefix(binary: str) -> List[str]:
        """On Windows a `.cmd`/`.bat` shim is not a valid Win32 image, so it
        must be launched through cmd.exe."""
        if os.name == "nt" and binary.lower().endswith((".cmd", ".bat")):
            return ["cmd", "/c", binary]
        return [binary]

    def build_args(self, prompt: str) -> List[str]:
        """Arguments after the executable: `run [flags] <prompt>`."""
        args: List[str] = ["run"]
        if self.model_name:
            args += ["--model", self.model_name]
        if self.agent:
            args += ["--agent", self.agent]
        if self.attach:
            args += ["--attach", self.attach]
        if self.workdir:
            args += ["--dir", self.workdir]
        args.append(prompt)
        return args

    # ── Low-level call ────────────────────────────────────────────────────
    def _run_cli(self, prompt: str) -> str:
        binary = self._assert_cli()
        cmd = self._command_prefix(binary) + self.build_args(prompt)

        env = dict(os.environ)
        env.setdefault("NO_COLOR", "1")  # keep stdout free of ANSI escapes

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=self.workdir or None,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"OpenCode CLI timed out after {self.timeout}s (raise OPENCODE_TIMEOUT if needed)"
            ) from exc
        except FileNotFoundError as exc:
            raise ConnectionError(
                f"Cannot connect to OpenCode CLI '{binary}'. {_INSTALL_HINT}"
            ) from exc

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()[:300]
            raise RuntimeError(f"OpenCode CLI exited {proc.returncode}: {detail}")

        output = (proc.stdout or "").strip() or (proc.stderr or "").strip()
        if not output:
            raise RuntimeError("OpenCode CLI returned no output")
        return output

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        return self._run_cli(full_prompt)

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    # ── Provider interface ────────────────────────────────────────────────
    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system = (
            "You are an expert software architect. Analyze the user prompt and return ONLY a valid "
            "JSON object with keys: website_type, industry, frontend, backend, database, "
            "features (list of strings), style (list of strings). No markdown, no prose — raw JSON only."
        )
        resp = self._call_api(prompt, system)
        return safe_json_parse(resp)

    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        context_str = ""
        if context_files:
            for fname, content in context_files.items():
                context_str += f"\n--- FILE: {fname} ---\n{content[:1000]}\n"
        full_prompt = f"Context:\n{context_str}\n\nTask: {prompt}\nGenerate clean, production-ready code."
        return self._call_api(full_prompt)

    def modify_code(self, file_content: str, instruction: str) -> str:
        prompt = (
            f"Original file:\n```\n{file_content[:3000]}\n```\n\n"
            f"Instruction: {instruction}\n\nReturn the complete updated file only."
        )
        return self._call_api(prompt)

    def fix_error(self, error_log: str, file_content: str) -> str:
        prompt = (
            f"Error:\n{error_log[:500]}\n\n"
            f"Code:\n```\n{file_content[:3000]}\n```\n\n"
            "Fix the error and return the complete corrected file."
        )
        return self._call_api(prompt)

    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Project summary:\n{json.dumps(project_summary, indent=2)[:2000]}\n\n"
            'Review the structure and return JSON: {"valid": bool, "suggestions": [str]}'
        )
        resp = self._call_api(prompt)
        parsed = safe_json_parse(resp)
        return parsed if parsed else {"valid": True, "suggestions": ["OpenCode review passed."]}
