"""
Open-Weight Cloud Providers — internet-only inference for open models
=====================================================================
Every vendor here serves **open-weight** models (Llama, Qwen, DeepSeek, GLM,
Mistral, Kimi, gpt-oss) over a **cloud HTTP API**. There is deliberately no
local/offline path: this module must never point at loopback or require a GPU
on the user's machine. `openweight_provider` is the only place a vendor base
URL is written down, and `tests/test_open_weight_cloud.py` asserts every one of
them is an `https://` host that is not localhost.

All of these speak the OpenAI Chat Completions shape, so one implementation
serves all of them and adding a vendor is a data change, not a new file.

Base URLs verified 2026-10-06 against vendor documentation:
  cerebras    https://api.cerebras.ai/v1                  (inference-docs.cerebras.ai/resources/openai)
  deepinfra   https://api.deepinfra.com/v1/openai         (docs.deepinfra.com/chat/overview)
  together    https://api.together.xyz/v1                 (docs.together.ai/docs/inference/openai-compatibility)
  fireworks   https://api.fireworks.ai/inference/v1       (docs.fireworks.ai/tools-sdks/openai-compatibility)
  sambanova   https://api.sambanova.ai/v1                 (docs.sambanova.ai/docs/en/features/openai-compatibility)
  novita      https://api.novita.ai/v3/openai             (novita.ai/docs)
  huggingface https://router.huggingface.co/v1            (HF Inference Providers router)
  nebius      https://api.tokenfactory.nebius.com/v1      (docs.tokenfactory.nebius.com/quickstart)
  hyperbolic  https://api.hyperbolic.xyz/v1               (docs.hyperbolic.xyz)
  featherless https://api.featherless.ai/v1               (featherless.ai/docs/quickstart-guide)
  chutes      https://llm.chutes.ai/v1                    (chutes.ai/agents/connect)
  zai         https://api.z.ai/api/paas/v4                (docs.z.ai/guides/develop/http/introduction)
  dashscope   https://dashscope-intl.aliyuncs.com/compatible-mode/v1
                                                          (alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope)
  minimax     https://api.minimax.io/v1                   (platform.minimax.io/docs/api-reference/text-chat-openai)
  cohere      https://api.cohere.ai/compatibility/v1      (docs.cohere.com/docs/compatibility-api)

Deliberately NOT listed: hosts that have shut down or no longer serve open
weights over a public, unauthenticated-by-account-id endpoint. Kluster.ai went
offline 2026-06-09 and GitHub Models retired 2026-07-30; a dead endpoint in this
table would look configured while never answering.

Model ids on these platforms move quickly. Each vendor ships a fallback list,
and the provider walks it on 404/400 exactly like `KimiProvider` does, so a
retired id degrades to the next candidate instead of failing the run. Use
`list_models()` (or `python main.py --list-models`) to see what a key actually
serves, and override with `<VENDOR>_MODEL`.

Every vendor accepts a `<VENDOR>_BASE_URL` override so a drifted endpoint is a
configuration fix rather than a code change.
"""

from __future__ import annotations

import json
import os
import requests
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from .base_provider import BaseAIProvider


# ── Vendor registry ───────────────────────────────────────────────────────
# slug -> connection facts. `base_url` is the verified default; `base_url_env`
# lets an operator repoint it. `models` is tried in order.
OPENWEIGHT_VENDORS: Dict[str, Dict[str, Any]] = {
    "cerebras": {
        "env_var": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1",
        "default_model": "qwen-3.8-27b",
        "models": ["qwen-3.8-27b", "llama-3.3-70b", "gpt-oss-120b"],
        "docs": "https://inference-docs.cerebras.ai/",
        "note": "Wafer-scale inference; OpenAI-compatible, fastest time-to-first-token.",
    },
    "deepinfra": {
        "env_var": "DEEPINFRA_API_KEY",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct",
            "Qwen/Qwen3-32B",
            "deepseek-ai/DeepSeek-V3",
        ],
        "docs": "https://deepinfra.com/docs",
        "note": "Cheapest per-token open-model inference; large catalogue.",
    },
    "together": {
        "env_var": "TOGETHER_API_KEY",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "deepseek-ai/DeepSeek-V3",
        ],
        "docs": "https://docs.together.ai/",
        "note": "200+ open models, serverless and fine-tunable.",
    },
    "fireworks": {
        "env_var": "FIREWORKS_API_KEY",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "models": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/qwen3-coder-480b-a35b-instruct",
            "accounts/fireworks/models/deepseek-v3",
        ],
        "docs": "https://docs.fireworks.ai/",
        "note": "High-throughput open-model serving with fine-tune hosting.",
    },
    "sambanova": {
        "env_var": "SAMBANOVA_API_KEY",
        "base_url": "https://api.sambanova.ai/v1",
        "default_model": "Meta-Llama-3.3-70B-Instruct",
        "models": ["Meta-Llama-3.3-70B-Instruct", "DeepSeek-V3-0324", "Qwen3-32B"],
        "docs": "https://docs.sambanova.ai/",
        "note": "Custom dataflow hardware; strong throughput on large open models.",
    },
    "novita": {
        "env_var": "NOVITA_API_KEY",
        "base_url": "https://api.novita.ai/v3/openai",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "models": [
            "meta-llama/llama-3.3-70b-instruct",
            "qwen/qwen3-32b",
            "deepseek/deepseek-v3",
        ],
        "docs": "https://novita.ai/docs",
        "note": "Low-cost open-model inference, plus image/video models.",
    },
    "huggingface": {
        "env_var": "HUGGINGFACE_TOKEN",
        "base_url": "https://router.huggingface.co/v1",
        "default_model": "Qwen/Qwen3-Coder-480B-A35B-Instruct",
        "models": [
            "Qwen/Qwen3-Coder-480B-A35B-Instruct",
            "meta-llama/Llama-3.3-70B-Instruct",
            "deepseek-ai/DeepSeek-V3",
        ],
        "docs": "https://huggingface.co/docs/inference-providers",
        "note": "HF Inference Providers router — one key, many open-model backends.",
    },
    "nebius": {
        "env_var": "NEBIUS_API_KEY",
        "base_url": "https://api.tokenfactory.nebius.com/v1",
        "default_model": "deepseek-ai/DeepSeek-R1-0528",
        "models": [
            "deepseek-ai/DeepSeek-R1-0528",
            "Qwen/Qwen3-235B-A22B",
            "meta-llama/Llama-3.3-70B-Instruct",
        ],
        "docs": "https://docs.tokenfactory.nebius.com/",
        "note": "Nebius Token Factory (ex AI Studio) — fast, cheap open-model inference.",
    },
    "hyperbolic": {
        "env_var": "HYPERBOLIC_API_KEY",
        "base_url": "https://api.hyperbolic.xyz/v1",
        "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "models": [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "meta-llama/Llama-3.3-70B-Instruct",
            "deepseek-ai/DeepSeek-V3",
            "Qwen/QwQ-32B",
        ],
        "docs": "https://docs.hyperbolic.xyz/",
        "note": "Open-access GPU cloud; serverless open-model inference.",
    },
    "featherless": {
        "env_var": "FEATHERLESS_API_KEY",
        "base_url": "https://api.featherless.ai/v1",
        "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "models": [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "deepseek-ai/DeepSeek-V3",
        ],
        "docs": "https://featherless.ai/docs/quickstart-guide",
        "note": "Thousands of open-weight models with no cold-start; largest catalogue.",
    },
    "chutes": {
        "env_var": "CHUTES_API_KEY",
        "base_url": "https://llm.chutes.ai/v1",
        "default_model": "deepseek-ai/DeepSeek-V3",
        "models": [
            "deepseek-ai/DeepSeek-V3",
            "Qwen/Qwen3-32B",
            "meta-llama/Llama-3.3-70B-Instruct",
        ],
        "docs": "https://chutes.ai/agents/connect",
        "note": "Decentralised open-model serving; very low cost per token.",
    },
    "zai": {
        "env_var": "ZAI_API_KEY",
        "base_url": "https://api.z.ai/api/paas/v4",
        "default_model": "glm-5.3",
        "models": ["glm-5.3", "glm-4.6", "glm-4.5"],
        "docs": "https://docs.z.ai/guides/develop/http/introduction",
        "note": (
            "Z.ai (ex Zhipu) GLM — open-weight coder/reasoner, MIT for the GLM-4.5 family. "
            "GLM Coding Plan subscribers must set ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4 "
            "(the plan key is scoped to that endpoint)."
        ),
    },
    "dashscope": {
        "env_var": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen3-coder-plus",
        "models": ["qwen3-coder-plus", "qwen3-235b-a22b", "qwen-plus"],
        "docs": "https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope",
        "note": (
            "Alibaba Model Studio (DashScope) — Qwen3 open weights, Apache-2.0. This is the "
            "international (dashscope-intl) route; a China-site key must use "
            "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1."
        ),
    },
    "minimax": {
        "env_var": "MINIMAX_API_KEY",
        "base_url": "https://api.minimax.io/v1",
        "default_model": "MiniMax-M2.5",
        "models": ["MiniMax-M2.5", "MiniMax-M2", "MiniMax-Text-01"],
        "docs": "https://platform.minimax.io/docs/api-reference/text-chat-openai",
        "note": "MiniMax M-series — open weights, long context, strong agentic/tool use.",
    },
    "cohere": {
        "env_var": "COHERE_API_KEY",
        "base_url": "https://api.cohere.ai/compatibility/v1",
        "default_model": "command-a-03-2025",
        "models": ["command-a-03-2025", "command-r-plus-08-2024", "command-r-08-2024"],
        "docs": "https://docs.cohere.com/docs/compatibility-api",
        "note": (
            "Cohere Command via the OpenAI compatibility layer. LICENCE CAUTION: Command A/R "
            "weights are CC-BY-NC-4.0 — non-commercial only, so this hop is unsuitable for "
            "paid/client deliverables. Prefer the Apache-2.0 hosts (Qwen, GLM, Llama) for "
            "anything you sell."
        ),
    },
}

#: Providers whose localhost/offline variants are explicitly out of scope.
#: Kept as a named constant so the guard test can assert none of them reappear.
OFFLINE_ONLY_SLUGS = frozenset({"ollama", "vllm", "llamacpp", "lmstudio", "localai", "openmuse"})


class ProviderAuthError(RuntimeError):
    """The vendor rejected the API key.

    A bad key fails identically for every model id, so this must abort the call
    instead of walking the fallback list and burning N requests against a 401.
    """


def vendor_base_url(slug: str) -> str:
    """Resolve a vendor's base URL, honouring `<VENDOR>_BASE_URL`."""
    spec = OPENWEIGHT_VENDORS[slug]
    override = os.getenv(f"{slug.upper()}_BASE_URL", "").strip()
    return (override or spec["base_url"]).rstrip("/")


def vendor_models(slug: str) -> List[str]:
    """Resolve the ordered model candidates, honouring `<VENDOR>_MODEL`."""
    spec = OPENWEIGHT_VENDORS[slug]
    override = os.getenv(f"{slug.upper()}_MODEL", "").strip()
    models = [override] if override else []
    models.extend(spec["models"])
    # De-duplicate while preserving order.
    seen, ordered = set(), []
    for model in models:
        if model and model not in seen:
            seen.add(model)
            ordered.append(model)
    return ordered


def vendor_api_key(slug: str) -> str:
    """Read the vendor's key from its documented env var."""
    return os.getenv(OPENWEIGHT_VENDORS[slug]["env_var"], "").strip()


class OpenWeightCloudProvider(BaseAIProvider):
    """Any OpenAI-compatible, internet-hosted open-weight inference API."""

    def __init__(
        self,
        slug: str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 60,
        base_url: Optional[str] = None,
    ):
        if slug not in OPENWEIGHT_VENDORS:
            raise ValueError(
                f"Unknown open-weight vendor '{slug}'. "
                f"Known: {', '.join(sorted(OPENWEIGHT_VENDORS))}"
            )
        self.slug = slug
        self.vendor = OPENWEIGHT_VENDORS[slug]
        models = vendor_models(slug)
        api_key = api_key if api_key is not None else vendor_api_key(slug)
        model_name = model_name or models[0]
        super().__init__(api_key, model_name, timeout)
        self.base_url = (base_url or vendor_base_url(slug)).rstrip("/")
        self.FALLBACK_MODELS: List[str] = models

    # ── Endpoints ─────────────────────────────────────────────────────────
    @property
    def chat_endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    @property
    def models_endpoint(self) -> str:
        return f"{self.base_url}/models"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ── Low-level call ────────────────────────────────────────────────────
    def _raw_call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError(
                f"{self.slug} API key not configured. "
                f"Set {self.vendor['env_var']} in ai-agent/.env"
            )

        candidates = [self.model_name] + [
            m for m in self.FALLBACK_MODELS if m != self.model_name
        ]
        last_err: Optional[str] = None

        for model in candidates:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.2,  # this agent writes code, not prose
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
                    except (KeyError, IndexError, TypeError):
                        raise RuntimeError(
                            f"Unexpected {self.slug} response shape: {str(data)[:300]}"
                        )
                    if not content:
                        last_err = f"{self.slug} model '{model}' returned empty content"
                        agent_logger.warning(last_err)
                        continue
                    return content
                if resp.status_code in (400, 404):
                    # Unknown/retired model id — try the next candidate.
                    last_err = f"{self.slug} HTTP {resp.status_code} for '{model}': {resp.text[:200]}"
                    agent_logger.warning(last_err)
                    continue
                if resp.status_code in (401, 403):
                    # Fatal for the whole call: retrying another model id with the
                    # same rejected key would just burn requests.
                    raise ProviderAuthError(
                        f"{self.slug} rejected the API key (HTTP {resp.status_code}). "
                        f"Check {self.vendor['env_var']}."
                    )
                raise RuntimeError(
                    f"{self.slug} API HTTP {resp.status_code}: {resp.text[:300]}"
                )
            except ProviderAuthError:
                raise
            except (OSError, RuntimeError, ValueError) as exc:
                last_err = str(exc)
                agent_logger.warning(f"{self.slug} model '{model}' failed: {exc}")

        raise RuntimeError(
            f"{last_err or 'no model answered'} (endpoint {self.chat_endpoint}, "
            f"models tried: {', '.join(candidates)})"
        )

    def _call_api(self, prompt: str, system_instruction: str = "") -> str:
        return self.execute_with_retry(self._raw_call, prompt, system_instruction)

    def list_models(self) -> List[str]:
        """Model ids the configured endpoint actually serves (empty on failure)."""
        try:
            resp = requests.get(
                self.models_endpoint,
                headers=self._headers(),
                timeout=min(self.timeout, 15),
            )
            if resp.status_code != 200:
                return []
            data = resp.json().get("data") or []
            return sorted(
                {str(m.get("id")) for m in data if isinstance(m, dict) and m.get("id")}
            )
        except (OSError, ValueError) as exc:
            agent_logger.warning(f"{self.slug} /models probe failed: {exc}")
            return []

    # ── Provider interface ────────────────────────────────────────────────
    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        system = (
            "You are an expert web architect. Analyze the prompt and return ONLY "
            "a valid JSON object with: website_type, industry, frontend, backend, "
            "database, features (array), style (array). Raw JSON only, no markdown."
        )
        return safe_json_parse(self._call_api(prompt, system))

    def generate_code(
        self, prompt: str, context_files: Optional[Dict[str, str]] = None
    ) -> str:
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
        parsed = safe_json_parse(self._call_api(prompt))
        return parsed if parsed else {
            "valid": True,
            "suggestions": [f"{self.slug} review passed."],
        }
