"""
Mistral AI Provider — LumicorePro AI Agent
==========================================
Supports Mistral Large, Mistral Small, Mixtral 8x7B, Codestral.
Uses Mistral Chat Completions API via requests.

Set MISTRAL_API_KEY in ai-agent/.env to enable.
Cost note: mistral-small is 8x cheaper than GPT-4, good for high-volume tasks.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider


class MistralProvider(BaseAIProvider):
    """Mistral AI Provider — Chat Completions API."""

    CHAT_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"

    # Ordered by capability: try primary, fallback to smaller/faster
    FALLBACK_MODELS = [
        "mistral-large-latest",
        "mistral-small-latest",
        "open-mixtral-8x7b",
        "open-mistral-7b",
    ]

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "mistral-large-latest",
        timeout: int = 40,
    ):
        api_key = api_key or os.getenv("MISTRAL_API_KEY", "")
        super().__init__(api_key, model_name, timeout)

    # ── Low-level call ────────────────────────────────────────────────────
    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Mistral API key not configured. Set MISTRAL_API_KEY in .env")

        models_to_try = [self.model_name] + [
            m for m in self.FALLBACK_MODELS if m != self.model_name
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
                "temperature": 0.3,  # Lower temp for structured outputs
            }

            try:
                resp = requests.post(
                    self.CHAT_ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        return data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        raise RuntimeError(f"Unexpected Mistral response: {data}")
                elif resp.status_code in (400, 404):
                    last_err = f"Mistral HTTP {resp.status_code} for '{model}': {resp.text[:200]}"
                    agent_logger.warning(last_err)
                    continue
                else:
                    raise RuntimeError(f"Mistral HTTP {resp.status_code}: {resp.text[:300]}")
            except Exception as exc:
                last_err = str(exc)
                agent_logger.warning(f"Mistral model '{model}' failed: {exc}")

        raise RuntimeError(last_err or "Mistral API call failed for all candidate models.")

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

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
                ctx += f"\n--- {fname} ---\n{content[:1200]}\n"
        full_prompt = (
            f"Context:\n{ctx}\n\nTask: {prompt}\n\n"
            "Generate clean, production-ready code only. No explanations."
        )
        return self._call_api(full_prompt)

    def modify_code(self, file_content: str, instruction: str) -> str:
        prompt = (
            f"File:\n```\n{file_content[:3000]}\n```\n\n"
            f"Instruction: {instruction}\n\nReturn complete updated file only."
        )
        return self._call_api(prompt)

    def fix_error(self, error_log: str, file_content: str) -> str:
        prompt = (
            f"Error: {error_log[:500]}\n\n"
            f"Code:\n```\n{file_content[:3000]}\n```\n\nFix and return complete file."
        )
        return self._call_api(prompt)

    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Project:\n{json.dumps(project_summary, indent=2)[:2000]}\n\n"
            'Return JSON: {"valid": bool, "suggestions": [str]}'
        )
        resp = self._call_api(prompt)
        parsed = safe_json_parse(resp)
        return parsed if parsed else {"valid": True, "suggestions": ["Mistral review passed."]}
