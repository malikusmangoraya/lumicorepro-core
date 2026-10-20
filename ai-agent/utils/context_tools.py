"""Context tooling for the agent: Headroom compression + Crawl4AI reference mining.

Both capabilities ship as *optional* runtime extras — the agent works without
them (this module degrades to plain passthroughs / urllib fallbacks), so they
never become a hard dependency of the pipeline. Enable explicitly:

  * ``HEADROOM_ENABLED=1``  — compress injected context before LLM calls
    (typical 20-60% fewer tokens for repetitive tool output; runs locally,
    nothing is uploaded).
  * ``REFERENCE_CRAWLER=1`` — prefer Crawl4AI for Reference Intelligence
    mining (LLM-ready markdown, boilerplate-stripped). When unset or missing,
    a stdlib urllib fallback fetches raw HTML and strips scripts/styles.

Nothing in this module raises on a missing/failed backend: utility failures
must never break a generation run.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

USER_AGENT = "lumicorepro-agent/1.0"
_CACHE_DIR = Path("database") / "reference_cache"
_STRIP = re.compile(r"<(script|style|noscript|svg)\b[^>]*>.*?</\1\s*>", re.I | re.S)


def headroom_enabled() -> bool:
    return os.getenv("HEADROOM_ENABLED", "").strip() == "1"


def compress_context(text: str, max_chars: Optional[int] = None) -> str:
    """Compress long injected context with Headroom when explicitly enabled.

    Passthrough on: env not set, import failure, or any runtime error — callers
    can treat the return as "best-effort, always usable text".
    """
    if not headroom_enabled() or not text or len(text) < 500:
        return context_lint(text, max_chars)
    try:
        from headroom import compress

        result = compress([{"role": "user", "content": text}])
        messages = getattr(result, "messages", None) or []
        out = messages[0].get("content", "") if isinstance(messages, list) and messages else ""
        if not out or len(out) > len(text):  # no savings → original
            out = text
        return context_lint(out, max_chars)
    except Exception:
        return context_lint(text, max_chars)


def context_lint(text: Optional[str], max_chars: Optional[int] = None) -> str:
    """Normalize whitespace + hard-truncate so injected context stays sane."""
    if not text:
        return ""
    cleaned = "\n".join(line.rstrip() for line in text.splitlines())
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if max_chars and len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars - 120] + "\n… [context truncated]"
    return cleaned


def _urllib_fallback(url: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    html = _STRIP.sub(" ", html)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"[ \t]{2,}", " ", html)
    return re.sub(r"\n{3,}", "\n\n", html).strip()


def reference_markdown(url: str, focus: Optional[str] = None, timeout: int = 60) -> Dict[str, Any]:
    """Mine a live reference page into LLM-ready markdown (Reference Intelligence).

    Tries Crawl4AI (PruningFilter + optional BM25 focus), falls back to urllib.
    Successful results are cached on disk so repeated runs skip the network.
    """
    url = (url or "").strip()
    if not url.startswith(("http://", "https://", "file://")):
        return {"status": "failed", "url": url, "message": "A valid URL is required"}

    cache_key = hashlib.sha1(f"{url}|{focus or ''}".encode()).hexdigest()[:16]
    cache_path = _CACHE_DIR / f"{cache_key}.json"
    try:
        if cache_path.is_file():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if time.time() - cached.get("mined_at", 0) < 7 * 86400:
                return {**cached, "cached": True}
    except Exception:
        pass

    out = {"status": "failed", "url": url}
    if os.getenv("REFERENCE_CRAWLER", "").strip() != "0":
        try:
            import asyncio

            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=timeout * 1000,
                exclude_external_images=True,
            )

            async def _run() -> Any:
                async with AsyncWebCrawler(headless=True) as crawler:
                    return await crawler.arun(url=url, config=config)

            res = asyncio.run(_run())
            md = ""
            mk = getattr(res, "markdown", None)
            if mk is not None:
                md = getattr(mk, "fit_markdown", "") or getattr(mk, "raw_markdown", "") or ""
            if md.strip():
                out = {
                    "status": "ok",
                    "url": url,
                    "title": (getattr(res, "metadata", None) or {}).get("title", ""),
                    "markdown": md,
                    "source": "crawl4ai",
                    "mined_at": time.time(),
                }
        except Exception as exc:  # pragma: no cover - exercised in live smoke
            out["crawl4ai_note"] = str(exc)[:200]

    if out["status"] != "ok":
        try:
            html_text = _urllib_fallback(url, timeout)
            if html_text:
                out = {
                    "status": "ok",
                    "url": url,
                    "title": "",
                    "markdown": html_text,
                    "source": "urllib-fallback",
                    "mined_at": time.time(),
                }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            out["message"] = str(exc)[:200]
    if out["status"] == "ok" and not out["markdown"].strip():
        out = {"status": "failed", "url": url, "message": "Empty extraction"}

    if out["status"] == "ok":
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return out
