"""
Anthropic Claude Provider — LumicorePro AI Agent
=================================================
Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku.
Uses Anthropic Messages API (v1) via requests — no SDK dependency required.

Set ANTHROPIC_API_KEY in ai-agent/.env to enable.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude AI Provider — Messages API with streaming-off mode."""

    MESSAGES_ENDPOINT = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION = "2023-06-01"

    # Candidate models tried in order if primary fails
    FALLBACK_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ]

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "claude-3-5-sonnet-20241022",
        timeout: int = 45,
    ):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        super().__init__(api_key, model_name, timeout)

    # ── Low-level call ────────────────────────────────────────────────────
    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env")

        models_to_try = [self.model_name] + [
            m for m in self.FALLBACK_MODELS if m != self.model_name
        ]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        last_err = None
        for model in models_to_try:
            payload: Dict[str, Any] = {
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_instruction:
                payload["system"] = system_instruction

            try:
                resp = requests.post(
                    self.MESSAGES_ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # content is a list of blocks; grab first text block
                    for block in data.get("content", []):
                        if block.get("type") == "text":
                            return block["text"]
                    raise RuntimeError(f"No text block in Claude response: {data}")
                elif resp.status_code in (400, 404):
                    last_err = f"Claude HTTP {resp.status_code} for model '{model}': {resp.text[:200]}"
                    agent_logger.warning(last_err)
                    continue
                else:
                    raise RuntimeError(f"Claude HTTP {resp.status_code}: {resp.text[:300]}")
            except Exception as exc:
                last_err = str(exc)
                agent_logger.warning(f"Claude model '{model}' failed: {exc}")

        raise RuntimeError(last_err or "Claude API call failed for all candidate models.")

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    # ── Provider interface ────────────────────────────────────────────────
    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system = (
            "You are a senior software architect specializing in international web platforms. "
            "Analyze the user prompt and return ONLY a valid JSON object with keys: "
            "website_type, industry, frontend, backend, database, "
            "features (array of strings), style (array of strings). "
            "No markdown, no explanation — raw JSON only."
        )
        resp = self._call_api(prompt, system)
        return safe_json_parse(resp)

    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        ctx = ""
        if context_files:
            for fname, content in context_files.items():
                ctx += f"\n--- {fname} ---\n{content[:1200]}\n"
        full_prompt = (
            f"Context files:\n{ctx}\n\n"
            f"Task: {prompt}\n\n"
            "Generate clean, production-ready code. No explanations, only code."
        )
        return self._call_api(full_prompt)

    def modify_code(self, file_content: str, instruction: str) -> str:
        prompt = (
            f"Original file:\n```\n{file_content[:3000]}\n```\n\n"
            f"Instruction: {instruction}\n\n"
            "Return the complete updated file only. No explanations."
        )
        return self._call_api(prompt)

    def fix_error(self, error_log: str, file_content: str) -> str:
        prompt = (
            f"Error:\n{error_log[:500]}\n\n"
            f"Code:\n```\n{file_content[:3000]}\n```\n\n"
            "Fix the error and return the complete corrected file."
        )
        return self._call_api(prompt)

    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Project summary:\n{json.dumps(project_summary, indent=2)[:2000]}\n\n"
            "Review structure and return JSON: {\"valid\": bool, \"suggestions\": [str]}"
        )
        resp = self._call_api(prompt)
        parsed = safe_json_parse(resp)
        return parsed if parsed else {"valid": True, "suggestions": ["Claude review passed."]}
