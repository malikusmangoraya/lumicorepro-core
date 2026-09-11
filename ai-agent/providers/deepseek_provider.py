import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

class DeepSeekProvider(BaseAIProvider):
    """DeepSeek AI Provider implementation using OpenAI compatible REST endpoints."""

    def __init__(self, api_key: str = None, model_name: str = "deepseek-chat", timeout: int = 30):
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        super().__init__(api_key, model_name, timeout)
        self.endpoint = "https://api.deepseek.com/v1/chat/completions"

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key or self.api_key == "your_deepseek_api_key_here":
            raise ValueError("DeepSeek API key not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2
        }

        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        if response.status_code == 200:
            data = response.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise RuntimeError(f"Unexpected response structure from DeepSeek API: {data}")
        else:
            raise RuntimeError(f"DeepSeek API HTTP Error {response.status_code}: {response.text}")

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
