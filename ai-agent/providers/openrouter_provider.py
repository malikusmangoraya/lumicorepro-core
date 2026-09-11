import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter API Provider supporting model-rotation across free-tier models."""

    def __init__(self, api_key: str = None, model_name: str = "google/gemma-4-31b-it:free",
                 timeout: int = 30, model_names: List[str] = None):
        api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        super().__init__(api_key, model_name, timeout)
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        # Rotation list: [model_name, ...rest]. We always start with the first.
        self._model_names = list(model_names or []) or [model_name]
        if model_name not in self._model_names:
            self._model_names.insert(0, model_name)
        self._current_idx = 0  # always try preferred model first

    def _rotate_model(self, failed_model: str) -> Optional[str]:
        """Mark a model as unusable and return the next available model, or None."""
        try:
            idx = self._model_names.index(failed_model)
            self._model_names.pop(idx)
            if self._model_names:
                self.model_name = self._model_names[0]
                agent_logger.info(f"[OPENROUTER] Rotated → {self.model_name} ({len(self._model_names)} remaining)")
                return self.model_name
        except ValueError:
            pass
        return None

    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            raise ValueError("OpenRouter API key not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/lumicorepro-core",
            "X-Title": "LumicorePro Core AI Agent",
            "Content-Type": "application/json"
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        tried = []

        for model in list(self._model_names):
            tried.append(model)
            payload = {
                "model": model,
                "messages": messages,
            }
            try:
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    try:
                        content = data["choices"][0]["message"]["content"]
                        # persist working model
                        if model != self.model_name:
                            self.model_name = model
                        return content
                    except (KeyError, IndexError):
                        last_error = RuntimeError(f"Unexpected response structure: {data}")
                        continue
                elif response.status_code == 429:
                    raise RuntimeError(f"Rate limited by OpenRouter (429) on model '{model}'")
                else:
                    err_body = response.text[:150]
                    agent_logger.warning(f"[OPENROUTER] {model} HTTP {response.status_code}: {err_body}")
                    last_error = RuntimeError(f"OpenRouter HTTP {response.status_code}: {err_body}")
                    # 400/404/500 → rotate to next model
                    self._rotate_model(model)
                    continue
            except requests.exceptions.Timeout:
                agent_logger.warning(f"[OPENROUTER] {model} timed out, rotating")
                self._rotate_model(model)
                continue
            except RuntimeError:
                raise
            except Exception as e:
                last_error = e
                self._rotate_model(model)
                continue

        raise RuntimeError(
            f"All {len(tried)} OpenRouter models exhausted. Tried: {tried}. "
            f"Last error: {last_error}"
        )

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
        """Analyze a screenshot via an OpenRouter vision-capable model."""
        from config.settings import VISION_MODEL
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return ""
        stripped = image_url_or_b64.strip()
        is_url = stripped.startswith(("http://", "https://", "data:"))
        image_part = (
            {"type": "image_url", "image_url": {"url": stripped}}
            if is_url else {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{stripped}"},
            }
        )
        payload = {
            "model": VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": prompt}, image_part],
            }],
        }
        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/lumicorepro-core",
                    "X-Title": "LumicorePro Core AI Agent",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    agent_logger.warning(f"Vision response structure unexpected: {data}")
                    return ""
            agent_logger.warning(f"Vision request failed {response.status_code}: {response.text[:200]}")
            return ""
        except Exception as e:
            agent_logger.warning(f"Vision request error: {e}")
            return ""
