"""Optional client adapter for a locally hosted FreeLLMAPI router."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider


class FreeLLMAPIProvider(BaseAIProvider):
    """Call a FreeLLMAPI router over its OpenAI-compatible chat endpoint.

    The local unified-key is optional when the router is configured without
    authentication. Upstream provider credentials and quotas remain managed by
    the router and are not supplied or inferred by this adapter.
    """

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "auto",
        timeout: int = 60,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("FREELLMAPI_API_KEY", "")
        self.base_url = (
            base_url or os.getenv("FREELLMAPI_BASE_URL", "http://127.0.0.1:3001/v1")
        ).rstrip("/")
        selected_model = model_name or "auto"
        super().__init__(self.api_key, selected_model, timeout)
        self.endpoint = f"{self.base_url}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json={"model": self.model_name, "messages": messages, "temperature": 0.2},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"FreeLLMAPI HTTP {response.status_code}: {response.text[:300]}"
            )
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected FreeLLMAPI response shape") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("FreeLLMAPI returned empty content")
        return content

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system = (
            "Analyze this software request and return only JSON with keys: "
            "website_type, industry, frontend, backend, database, features, style."
        )
        return safe_json_parse(self._call_api(prompt, system))

    def generate_code(
        self, prompt: str, context_files: Optional[Dict[str, str]] = None
    ) -> str:
        context = "\n".join(
            f"--- FILE: {name} ---\n{content[:1500]}"
            for name, content in (context_files or {}).items()
        )
        return self._call_api(f"Context:\n{context}\n\nTask: {prompt}\nReturn code only.")

    def modify_code(self, file_content: str, instruction: str) -> str:
        return self._call_api(
            f"File:\n```\n{file_content[:4000]}\n```\n\n"
            f"Instruction: {instruction}\nReturn the complete updated file only."
        )

    def fix_error(self, error_log: str, file_content: str) -> str:
        return self._call_api(
            f"Error:\n{error_log[:1000]}\n\nCode:\n```\n{file_content[:4000]}\n```\n"
            "Return the complete corrected file only."
        )

    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        result = safe_json_parse(
            self._call_api(
                f"Review this project and return JSON {{valid: boolean, suggestions: string[]}}:\n"
                f"{json.dumps(project_summary, indent=2)[:2500]}"
            )
        )
        return result if result else {"valid": False, "suggestions": ["Invalid model response."]}
