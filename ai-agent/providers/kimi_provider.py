"""
Kimi (Moonshot AI) Provider — LumicorePro AI Agent
=================================================
OpenAI-compatible Chat Completions API from Moonshot AI.

Model IDs currently served by the API (verified 2026-09):
  - ``kimi-k2.7-code``            coding-first, best fit for this agent (default)
  - ``kimi-k2.7-code-highspeed``  same weights, latency-tuned
  - ``kimi-k2.6``                 general purpose, 256K context
  - ``kimi-k3``                   flagship, thinking always on
Retired (do NOT ship new integrations): ``kimi-latest`` (discontinued
2026-01-28) and the original ``kimi-k2`` series (discontinued 2026-05-25).

The K2 family is open-weight, so ``KIMI_BASE_URL`` can point at a self-hosted
vLLM/SGLang deployment (the compliant path for data-residency/GDPR rules, since
the hosted API processes requests in China).

Set KIMI_API_KEY (or MOONSHOT_API_KEY) in ai-agent/.env to enable.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

INTERNATIONAL_BASE = "https://api.moonshot.ai/v1"
CHINA_BASE = "https://api.moonshot.cn/v1"


class KimiProvider(BaseAIProvider):
    """Moonshot AI (Kimi) Provider — Chat Completions API."""

    DEFAULT_BASE = INTERNATIONAL_BASE

    # Ordered by fit for this agent: coding first, then general, then flagship.
    FALLBACK_MODELS: List[str] = [
        "kimi-k2.7-code",
        "kimi-k2.7-code-highspeed",
        "kimi-k2.6",
        "kimi-k3",
    ]

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "kimi-k2.7-code",
        timeout: int = 60,
        base_url: str = None,
    ):
        api_key = api_key or os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY", "")
        super().__init__(api_key, model_name, timeout)
        self.base_url = (base_url or os.getenv("KIMI_BASE_URL") or self.DEFAULT_BASE).rstrip("/")

    @property
    def chat_endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _models_endpoint(self) -> str:
        return f"{self.base_url}/models"

    # ── Low-level call ────────────────────────────────────────────────────
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if self.api_key.startswith("your_"):
            raise ValueError("Kimi API key not configured. Set KIMI_API_KEY in .env")

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
                "max_tokens": 8192,
                "temperature": 0.2,  # low temp: this agent writes code, not prose
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
                        raise RuntimeError(f"Unexpected Kimi response shape: {data}")
                    if not content:
                        # Thinking-mode models can return reasoning only; retry the
                        # next model rather than handing an empty string upward.
                        last_err = f"Kimi model '{model}' returned empty content"
                        agent_logger.warning(last_err)
                        continue
                    return content
                if resp.status_code in (400, 404):
                    # Unknown/retired model id — try the next candidate.
                    last_err = f"Kimi HTTP {resp.status_code} for '{model}': {resp.text[:200]}"
                    agent_logger.warning(last_err)
                    continue
                raise RuntimeError(f"Kimi API HTTP {resp.status_code}: {resp.text[:300]}")
            # RequestException subclasses OSError; catching OSError also covers a bare
            # socket-level failure from a mock/self-hosted runtime.
            except (OSError, RuntimeError, ValueError) as exc:
                last_err = str(exc)
                agent_logger.warning(f"Kimi model '{model}' failed: {exc}")

        raise RuntimeError(
            f"{last_err or 'no model answered'} (endpoint {self.chat_endpoint}, "
            f"models tried: {', '.join(models_to_try)})"
        )

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def list_models(self) -> List[str]:
        """Return the model ids the configured endpoint actually serves.

        Used by the doctor command so a configured-but-dead model id is reported
        as a configuration problem instead of surfacing as a mid-run failure.
        """
        try:
            resp = requests.get(self._models_endpoint(), headers=self._headers(), timeout=min(self.timeout, 15))
            if resp.status_code != 200:
                return []
            data = resp.json().get("data") or []
            return sorted({str(m.get("id")) for m in data if isinstance(m, dict) and m.get("id")})
        except OSError as exc:
            agent_logger.warning(f"Kimi /models probe failed: {exc}")
            return []

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
            "Return clean, production-ready code only. No explanations, no prose."
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
        return parsed if parsed else {"valid": True, "suggestions": ["Kimi review passed."]}
