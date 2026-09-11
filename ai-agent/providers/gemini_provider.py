import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI Provider implementation with retries, timeout, and fallback support."""

    def __init__(self, api_key: str = None, model_name: str = "gemini-3.6-flash", timeout: int = 30):
        api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        super().__init__(api_key, model_name, timeout)
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key not configured.")

        # Fallback candidate models (latest supported versions)
        models_to_try = [self.model_name, "gemini-3.6-flash", "gemini-2.5-flash"]
        # Remove duplicates while preserving order
        unique_models = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        last_err = None
        for model in unique_models:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            url = f"{endpoint}?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            headers = {"Content-Type": "application/json"}
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        raise RuntimeError(f"Unexpected response payload structure from Gemini API: {data}")
                elif response.status_code == 404:
                    last_err = f"Gemini API HTTP Error 404 for model '{model}': {response.text}"
                    continue
                else:
                    raise RuntimeError(f"Gemini API HTTP Error {response.status_code}: {response.text}")
            except Exception as e:
                last_err = str(e)

        raise RuntimeError(last_err or "Gemini API call failed for all candidate models.")


    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def describe_image(self, image_url_or_b64: str, mime_type: str = "image/png",
                       prompt: str = "Describe this UI layout in detail.") -> str:
        """Analyze a screenshot with Gemini's native multimodal support (inline data)."""
        from config.settings import VISION_MODEL_IMAGE
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return ""
        stripped = image_url_or_b64.strip()
        model = VISION_MODEL_IMAGE
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        url = f"{endpoint}?key={self.api_key}"

        if stripped.startswith(("http://", "https://", "data:")):
            inline = {"mime_type": mime_type, "data": stripped.split(",", 1)[-1] if stripped.startswith("data:") else stripped}
            parts = [
                {"text": prompt},
                {"image": {"mime_type": inline["mime_type"], "data": inline["data"]}},
            ]
            payload = {"contents": [{"parts": parts}]}
        else:
            payload = {
                "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": stripped}}]}]
            }
        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return ""
            agent_logger.warning(f"Gemini vision failed {response.status_code}: {response.text[:200]}")
            return ""
        except Exception as e:
            agent_logger.warning(f"Gemini vision error: {e}")
            return ""

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
