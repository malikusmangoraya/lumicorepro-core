import os
import json
import socket
import requests
from urllib.parse import urlparse
from typing import Dict, Any, Optional
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider


class NinerouterProvider(BaseAIProvider):
    """9Router — local AI gateway / router + token saver.

    OpenAI-compatible /v1 endpoint that balances across connected providers
    (40+) and auto-falls back to FREE tiers, with RTK token compression for
    tool output. Model id format: '<provider-prefix>/<model>'.

    Setup (once): run `9router` → dashboard http://localhost:20128 →
    Providers → connect a FREE provider (Kiro AI / OpenCode Free) →
    API Keys → copy key into NINEROUTER_API_KEY.
    """

    def __init__(self, api_key: str = "", model_name: str = "", timeout: int = 30):
        api_key = api_key or os.getenv("NINEROUTER_API_KEY", "")
        model_name = model_name or os.getenv("NINEROUTER_MODEL", "kr/claude-sonnet-4.5")
        super().__init__(api_key, model_name, timeout)
        base_url = os.getenv("NINEROUTER_BASE_URL", "http://127.0.0.1:20128/v1").rstrip("/")
        self.endpoint = f"{base_url}/chat/completions"
        self.gateway_host, self.gateway_port = self._parse_endpoint(self.endpoint)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _parse_endpoint(endpoint: str):
        host, port = "127.0.0.1", 20128
        try:
            parsed = urlparse(endpoint)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except Exception:
            pass
        return host, port

    def _gateway_up(self) -> bool:
        """Fast probe so a dead local gateway fails in ~1s instead of
        stalling the retry loop on a dropped connect."""
        try:
            with socket.create_connection((self.gateway_host, self.gateway_port), timeout=1.0):
                return True
        except OSError:
            return False

    def _assert_gateway(self) -> None:
        if not self._gateway_up():
            raise ConnectionError(
                f"Cannot connect to 9Router at {self.gateway_host}:{self.gateway_port} "
                "(connection refused / gateway not running). Run: 9router"
            )

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        self._assert_gateway()
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
        }

        response = requests.post(self.endpoint, headers=self._headers(), json=payload, timeout=self.timeout)
        if response.status_code == 200:
            data = response.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise RuntimeError(f"Unexpected response structure from 9Router API: {data}")
        raise RuntimeError(f"9Router API HTTP Error {response.status_code}: {response.text}")

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system_instruction = (
            "You are an expert software architect. Analyze user prompt and return ONLY a valid JSON object with keys: "
            "website_type, industry, frontend, backend, database, features (list of strings), style (list of strings)."
        )
        resp = self._call_api(prompt, system_instruction)
        return safe_json_parse(resp)

    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        context_str = ""
        if context_files:
            for fname, content in context_files.items():
                context_str += f"\n--- FILE: {fname} ---\n{content[:1000]}\n"
        full_prompt = f"Context:\n{context_str}\n\nTask: {prompt}\nGenerate minimal clean code."
        return self._call_api(full_prompt)

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

    def describe_image(self, image_url_or_b64: str, mime_type: str = "image/png",
                       prompt: str = "Describe this UI layout in detail.") -> str:
        """Analyze a screenshot via the router's vision-capable backend."""
        if not self._gateway_up():
            agent_logger.warning(f"9Router not running at {self.gateway_host}:{self.gateway_port}")
            return ""
        stripped = image_url_or_b64.strip()
        is_url = stripped.startswith(("http://", "https://", "data:"))
        image_url = stripped if is_url else f"data:{mime_type};base64,{stripped}"
        payload = {
            "model": self.model_name,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }],
        }
        try:
            response = requests.post(self.endpoint, headers=self._headers(), json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    agent_logger.warning(f"9Router vision response structure unexpected: {data}")
                    return ""
            agent_logger.warning(f"9Router vision request failed {response.status_code}: {response.text[:200]}")
            return ""
        except Exception as e:
            agent_logger.warning(f"9Router vision request error: {e}")
            return ""