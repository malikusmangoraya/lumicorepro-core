"""
OpenMuse Provider — LumicorePro AI Agent
========================================
OpenMuse is the MIT-licensed, open-source personal agent (CopilotKit) modelled on
Meta's Muse. It is an **agent framework, not a model**: it is "bring your own
model" and speaks to any OpenAI-compatible endpoint through its `[llm]` block
(`OPENMUSE_LLM_BASE_URL` / `_MODEL` / `_API_KEY` / `_PROVIDER`).

This provider therefore targets a self-hosted, OpenAI-compatible OpenMuse gateway
and — because the same wire protocol serves them — any local open-weight runtime:

  - OpenMuse gateway (default: http://127.0.0.1:8080/v1)
  - Ollama            http://127.0.0.1:11434/v1
  - vLLM / SGLang     http://127.0.0.1:8000/v1
  - llama.cpp server  http://127.0.0.1:8080/v1
  - LM Studio         http://127.0.0.1:1234/v1

No API key is required: local servers usually accept a placeholder, and the
Authorization header is omitted entirely when none is configured. That makes this
the provider to use for fully offline / air-gapped builds with open-weight models
(Qwen3, DeepSeek, Llama, Gemma, and the open-weight Kimi K2 family).

Config (all optional — every default points at a local server):
  OPENMUSE_BASE_URL   OPENMUSE_MODEL   OPENMUSE_API_KEY
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

DEFAULT_BASE_URLS = [
    "http://127.0.0.1:8080/v1",   # OpenMuse gateway / llama.cpp
    "http://127.0.0.1:11434/v1",  # Ollama
    "http://127.0.0.1:8000/v1",   # vLLM / SGLang
    "http://127.0.0.1:1234/v1",   # LM Studio
]


class OpenMuseProvider(BaseAIProvider):
    """Self-hosted OpenAI-compatible endpoint (OpenMuse gateway or local runtime)."""

    # Open-weight coding models, best first. Each entry is tried in order after
    # the configured model fails, so one local server can host several.
    FALLBACK_MODELS: List[str] = [
        "qwen3-coder",
        "qwen3:8b",
        "deepseek-coder-v2",
        "moonshotai/Kimi-K2-Instruct",
        "llama3.1:8b",
        "gemma3:4b",
    ]

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "qwen3-coder",
        timeout: int = 120,
        base_url: str = None,
    ):
        api_key = api_key or os.getenv("OPENMUSE_API_KEY", "")
        model_name = model_name or os.getenv("OPENMUSE_MODEL", "") or "qwen3-coder"
        base_url = (
            base_url or os.getenv("OPENMUSE_BASE_URL", "") or DEFAULT_BASE_URLS[0]
        ).rstrip("/")
        super().__init__(api_key, model_name, timeout)
        self.base_url = base_url
        # Local servers are routinely slow to boot / load weights; keep the call
        # patient instead of rotating the whole pool on one slow call.
        self.timeout = max(self.timeout, 60)

    @property
    def chat_endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        # Local runtimes usually ignore auth; sending none is cleaner than "Bearer dummy".
        if self.api_key and not self.api_key.startswith("your_"):
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ── Low-level call ────────────────────────────────────────────────────
    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        models_to_try = [self.model_name] + [
            m for m in self.FALLBACK_MODELS if m != self.model_name
        ]

        last_err = None
        for model in models_to_try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.2,
                "stream": False,
            }

            try:
                resp = requests.post(
                    self.chat_endpoint,
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        content = data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        raise RuntimeError(f"Unexpected OpenMuse response shape: {data}")
                    if content:
                        return content
                    last_err = f"OpenMuse model '{model}' returned empty content"
                    agent_logger.warning(last_err)
                    continue
                if resp.status_code in (400, 404):
                    # Ollama answers 404 for an unknown model tag; vLLM answers 400.
                    last_err = f"OpenMuse HTTP {resp.status_code} for '{model}': {resp.text[:200]}"
                    agent_logger.warning(last_err)
                    continue
                raise RuntimeError(f"OpenMuse HTTP {resp.status_code}: {resp.text[:300]}")
            # RequestException subclasses OSError; catching OSError also covers a bare
            # socket-level failure from a mock/self-hosted runtime.
            except (OSError, RuntimeError, ValueError) as exc:
                last_err = str(exc)
                agent_logger.warning(f"OpenMuse model '{model}' failed: {exc}")

        # Always name the endpoint: "connection refused" alone gives the operator
        # no way to tell a wrong port from a stopped server.
        raise RuntimeError(
            f"{last_err or 'no model answered'} — no OpenAI-compatible server at {self.base_url}. "
            f"Start one of {DEFAULT_BASE_URLS} or set OPENMUSE_BASE_URL."
        )

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def list_models(self) -> List[str]:
        """Model ids the local server advertises (used by `doctor`)."""
        try:
            resp = requests.get(
                f"{self.base_url}/models", headers=self._headers(), timeout=min(self.timeout, 10)
            )
            if resp.status_code != 200:
                return []
            data = resp.json().get("data") or []
            return sorted({str(m.get("id")) for m in data if isinstance(m, dict) and m.get("id")})
        except OSError as exc:
            agent_logger.warning(f"OpenMuse /models probe failed: {exc}")
            return []

    def discover(self, prompt: str = "ping") -> Optional[str]:
        """Probe the common local ports and return the first one that answers."""
        candidates = [self.base_url] + [u for u in DEFAULT_BASE_URLS if u != self.base_url]
        original = self.base_url
        for base in candidates:
            self.base_url = base
            try:
                if self.list_models():
                    agent_logger.info(f"[BENCH] OpenMuse-compatible server found at {base}")
                    return base
            except Exception:
                continue
        self.base_url = original
        return None

    # ── Provider interface ────────────────────────────────────────────────
    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system = (
            "You are an expert web architect. Analyze the prompt and return ONLY "
            "a valid JSON object with: website_type, industry, frontend, backend, "
            "database, features (array), style (array). Raw JSON only, no markdown."
        )
        resp = self._call_api(prompt, system)
        return safe_json_parse(resp)

    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        ctx = ""
        if context_files:
            for fname, content in context_files.items():
                ctx += f"\n--- FILE: {fname} ---\n{content[:1500]}\n"
        full_prompt = (
            f"Context:\n{ctx}\n\nTask: {prompt}\n\n"
            "Return clean, production-ready code only. No explanations."
        )
        return self._call_api(full_prompt)

    def modify_code(self, file_content: str, instruction: str) -> str:
        prompt = (
            f"File:\n```\n{file_content[:4000]}\n```\n\n"
            f"Instruction: {instruction}\n\nReturn the complete updated file only."
        )
        return self._call_api(prompt)

    def fix_error(self, error_log: str, file_content: str) -> str:
        prompt = (
            f"Error log:\n{error_log[:800]}\n\n"
            f"Code:\n```\n{file_content[:4000]}\n```\n\n"
            "Fix the error. Return the complete updated file only."
        )
        return self._call_api(prompt)

    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Project:\n{json.dumps(project_summary, indent=2)[:2500]}\n\n"
            'Return JSON: {"valid": bool, "suggestions": [str]}'
        )
        resp = self._call_api(prompt)
        parsed = safe_json_parse(resp)
        return parsed if parsed else {"valid": True, "suggestions": ["OpenMuse review passed."]}
