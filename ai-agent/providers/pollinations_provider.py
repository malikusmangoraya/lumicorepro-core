"""Pollinations.ai provider — fully keyless, free, internet-run text & images.

Text:  POST https://text.pollinations.ai/openai (OpenAI-compatible chat payload)
       Free tier needs no API key; models include `openai-fast`, `openai` and
       community open-weight names (llamalight, mistral, ...)
Images: GET https://image.pollinations.ai/prompt/<prompt>?width&height&nologo
       Pure HTTP image generation — no key, used by agent.asset_gen.

The operator runs no local GPU stack, so every AI win must be reachable over
the internet — this provider is the zero-credential path for both text and
imagery, deliberately excluded from the local-runtime invariant.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

TEXT_BASE = os.getenv("POLLINATIONS_TEXT_BASE", "https://text.pollinations.ai")
IMAGE_BASE = os.getenv("POLLINATIONS_IMAGE_BASE", "https://image.pollinations.ai")
DEFAULT_TEXT_MODEL = os.getenv("POLLINATIONS_MODEL", "openai-fast")  # free tier


class PollinationsProvider(BaseAIProvider):
    """Keyless chat completion against Pollinations' OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: str = "",
        model_name: str = DEFAULT_TEXT_MODEL,
        timeout: int = 90,
        base_url: Optional[str] = None,
    ) -> None:
        # Pollinations needs no key; a POLLINATIONS_API_KEY (referrer tier) is optional.
        self.api_key = api_key or os.getenv("POLLINATIONS_API_KEY", "")
        self.base_url = (base_url or TEXT_BASE).rstrip("/")
        selected = model_name if model_name and model_name != DEFAULT_TEXT_MODEL \
            else (os.getenv("POLLINATIONS_TEXT_MODEL", "") or DEFAULT_TEXT_MODEL)
        super().__init__(self.api_key, selected, timeout)
        self.endpoint = f"{self.base_url}/openai"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        messages: list = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json={
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.2,
                "private": True,  # stay out of the public feed
            },
            timeout=self.timeout,
        )
        if response.status_code == 429:
            raise RuntimeError(f"Pollinations HTTP 429: {response.text[:200]}")
        if response.status_code != 200:
            raise RuntimeError(
                f"Pollinations HTTP {response.status_code}: {response.text[:300]}"
            )
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected Pollinations response shape") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Pollinations returned empty content")
        return content

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        context = "\n".join(
            f"--- FILE: {name} ---\n{content[:1500]}"
            for name, content in (context_files or {}).items()
        )
        return self._call_api(f"Context:\n{context}\n\nTask: {prompt}\nReturn code only.")

    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system = (
            "Analyze this software request and return only JSON with keys: "
            "website_type, industry, frontend, backend, database, features, style."
        )
        return safe_json_parse(self._call_api(prompt, system))

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
                "Review this project and return JSON {valid: boolean, suggestions: string[]}:\n"
                f"{json.dumps(project_summary, indent=2)[:2500]}"
            )
        )
        return result if result else {"valid": False, "suggestions": ["Invalid model response."]}

    def describe_image(self, image_url_or_b64: str, mime_type: str = "image/png",
                       prompt: str = "Describe this UI layout in detail.") -> str:
        """Pollinations 'openai' models accept image parts (vision-capable)."""
        stripped = str(image_url_or_b64).strip()
        if stripped.startswith(("http://", "https://", "data:")):
            source = {"url": stripped}
        else:
            source = {"url": f"data:{mime_type};base64,{stripped}"}
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json={"model": self.model_name,
                  "messages": [{"role": "user", "content": [{"type": "text", "text": prompt},
                                                           {"type": "image_url", "image_url": source}]}]},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Pollinations vision HTTP {response.status_code}: {response.text[:200]}")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected Pollinations vision response shape") from exc


def image_url(prompt: str, width: int = 1200, height: int = 630, seed: int = None) -> str:
    """Deterministic keyless image URL (fetch it to obtain the JPEG bytes)."""
    from urllib.parse import quote
    q = f"?width={int(width)}&height={int(height)}&nologo=true"
    if seed is not None:
        q += f"&seed={int(seed)}"
    return f"{IMAGE_BASE}/prompt/{quote(prompt)}{q}"
