import os
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from utils.logger import agent_logger

class BaseAIProvider(ABC):
    """Abstract Base Class for AI Providers with retries, timeouts, fallback chains, and structured logging."""

    def __init__(self, api_key: str, model_name: str, timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = 3
        self.backoff_factor = 1.5
        self.logs_dir = Path(__file__).resolve().parent.parent / "logs"
        self.jsonl_log_file = self.logs_dir / "provider_calls.jsonl"
        os.makedirs(self.logs_dir, exist_ok=True)

    def _log_provider_call(
        self,
        provider_name: str,
        prompt_snippet: str,
        latency_seconds: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Log structured provider call record to logs/provider_calls.jsonl."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "provider": provider_name,
            "model": self.model_name,
            "prompt_snippet": prompt_snippet[:100],
            "latency_seconds": round(latency_seconds, 3),
            "success": success,
            "error": error or ""
        }
        try:
            with open(self.jsonl_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            agent_logger.error(f"Failed writing to provider_calls.jsonl: {e}")

    @staticmethod
    def is_rate_limited(exception: Exception) -> bool:
        """Check if exception indicates a rate limit (429) response."""
        msg = str(exception).lower()
        return any(kw in msg for kw in ("429", "rate limit", "rate_limit", "too many requests",
                                         "quota exceeded", "requests per minute", "requests per day"))

    def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute API request function with 3-attempt exponential backoff retry.

        On rate-limit (429), immediately raises so the caller can rotate providers.
        """
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                if result:
                    self._log_provider_call(
                        self.__class__.__name__,
                        str(args[0]) if args else "",
                        latency,
                        success=True
                    )
                    return result
                else:
                    raise RuntimeError("Empty response received from AI provider")
            except Exception as e:
                latency = time.time() - start_time
                last_exception = e
                self._log_provider_call(
                    self.__class__.__name__,
                    str(args[0]) if args else "",
                    latency,
                    success=False,
                    error=str(e)
                )

                # Rate limit — don't retry, let caller rotate to next provider
                if self.is_rate_limited(e):
                    agent_logger.warning(
                        f"Provider {self.__class__.__name__} rate limited (attempt {attempt}/{self.max_retries}). "
                        "Signaling rotation."
                    )
                    raise

                agent_logger.warning(
                    f"Provider call attempt {attempt}/{self.max_retries} failed ({e}). Retrying..."
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff_factor ** attempt)

        raise last_exception or RuntimeError("Max retries exceeded for AI Provider call")

    @abstractmethod
    def analyze_requirement(self, prompt: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_code(self, prompt: str, context_files: Optional[Dict[str, str]] = None) -> str:
        pass

    @abstractmethod
    def modify_code(self, file_content: str, instruction: str) -> str:
        pass

    @abstractmethod
    def fix_error(self, error_log: str, file_content: str) -> str:
        pass

    @abstractmethod
    def validate_project(self, project_summary: Dict[str, Any]) -> Dict[str, Any]:
        pass

    # ── Vision (optional) ─────────────────────────────────────────────────
    def describe_image(self, image_url_or_b64: str, mime_type: str = "image/png",
                       prompt: str = "Describe this UI layout in detail.") -> str:
        """Vision-capable providers override this to analyze a screenshot.

        Default implementation returns an empty string so the VisionPipeline can
        degrade to deterministic heuristics when no vision-capable key exists.
        """
        return ""
