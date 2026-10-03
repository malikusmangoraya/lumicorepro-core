import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

class NvidiaProvider(BaseAIProvider):
    """NVIDIA NIM Free Tier Provider - free cloud API access.

    Models: DeepSeek V4.1 Flash, GLM 5.3, GLM 5.3 Flash, Kimi K3
    Endpoint: https://integrate.api.nvidia.com/v1
    Free tier: no credit card required
    """

    FREE_MODELS = [
        "deepseek-ai/deepseek-v4.1-flash",
        "z-ai/glm-5.3-flash",
        "z-ai/glm-5.3",
        "moonshotai/kimi-k3",
    ]

    def __init__(self, api_key: str = None, model_name: str = "deepseek-ai/deepseek-v4.1-flash", timeout: int = 30):
        api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        super().__init__(api_key, model_name, timeout)
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.endpoint = f"{self.base_url}/chat/completions"

    @staticmethod
    def _extract_text(data: Any, model: str) -> str:
        """Validate the chat-completion shape instead of masking drift as a model miss."""
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected NVIDIA response shape for model '{model}': {data!r}"[:500]) from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"Empty NVIDIA response for model '{model}'")
        return content

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        from config.providers import is_placeholder_key

        if not self.api_key or is_placeholder_key(self.api_key):
            raise ValueError("NVIDIA API key not configured. Set NVIDIA_API_KEY env var.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        last_err = None
        models_to_try = [self.model_name] + [m for m in self.FREE_MODELS if m != self.model_name]

        for model in models_to_try:
            payload["model"] = model
            try:
                resp = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                # Transport failures belong to router-level rotation, not to
                # another local retry against the same provider.
                raise RuntimeError(f"NVIDIA request failed for model '{model}': {exc}") from exc
            if resp.status_code in (401, 403):
                # Authentication will not succeed on another model or retry.
                raise RuntimeError(f"NVIDIA authentication failed for model '{model}': HTTP {resp.status_code}")
            if resp.status_code == 429:
                raise RuntimeError(f"NVIDIA rate limited for model '{model}': HTTP 429")
            if resp.status_code in (400, 404, 422):
                last_err = RuntimeError(f"NVIDIA rejected model '{model}': HTTP {resp.status_code}: {resp.text[:200]}")
                agent_logger.warning(last_err)
                continue
            if resp.status_code != 200:
                raise RuntimeError(f"NVIDIA HTTP {resp.status_code} for model '{model}': {resp.text[:200]}")
            try:
                data = resp.json()
            except ValueError as exc:
                raise RuntimeError(f"NVIDIA returned invalid JSON for model '{model}'") from exc
            return self._extract_text(data, model)

        raise last_err or Exception("All NVIDIA models failed")

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        # Router-level rotation owns retries across providers. Local retries here
        # would multiply one logical call across models and attempts.
        return self._raw_call(prompt, system_instruction)

    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system_instruction = (
            "You are an expert software architect. Analyze user prompt and return ONLY a valid JSON object with keys: "
            "website_type, industry, frontend, backend, database, features (list of strings), style (list of strings)."
        )
        resp = self._call_api(prompt, system_instruction)
        return safe_json_parse(resp)

    def modify_code(self, file_content: str, instruction: str) -> str:
        prompt = f"Original Code:\n{file_content}\n\nModification Instruction:\n{instruction}\n\nReturn complete updated file."
        return self._call_api(prompt)

    def fix_error(self, error_log: str, file_content: str) -> str:
        prompt = f"Error Log:\n{error_log}\n\nCode:\n{file_content}\n\nFix error and return updated code."
        return self._call_api(prompt)

    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"Project Summary:\n{json.dumps(project_summary, indent=2)}\nReview structure and return JSON with valid=true/false and suggestions list."
        resp = self._call_api(prompt)
        parsed = safe_json_parse(resp)
        return parsed if parsed else {"valid": True, "suggestions": ["Basic structure looks valid."]}

    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        context_str = ""
        if context_files:
            for fname, content in context_files.items():
                context_str += f"\n--- FILE: {fname} ---\n{content[:1000]}\n"
        full_prompt = f"Context:\n{context_str}\n\nTask: {prompt}\nGenerate minimal clean code."
        return self._call_api(full_prompt)

    def is_available(self) -> bool:
        try:
            from config.providers import is_placeholder_key

            return bool(self.api_key) and not is_placeholder_key(self.api_key)
        except Exception:
            return bool(self.api_key)
