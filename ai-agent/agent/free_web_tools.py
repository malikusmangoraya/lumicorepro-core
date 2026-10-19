"""Free internet-powered QA tools (no API key required by default).

Every helper talks straight to a free, keyless public endpoint and degrades
gracefully (returns ``{"status": "..."}`` dicts like the rest of the agent):

  * ``pagespeed_audit``  — Google PageSpeed Insights v5 (Lighthouse scores +
    core-web-vitals, mobile/desktop). Optional ``PAGESPEED_API_KEY`` removes
    the anonymous rate limit.
  * ``w3c_validate``     — W3C Nu HTML checker by URL or file content.
  * ``npm_latest``       — npm registry: latest published version per package
    (used to keep generated ``package.json`` deps fresh).
  * ``http_reachable``   — one-shot GET status check for a live URL.

Only stdlib ``urllib`` is used so the module loads instantly in every path the
agent runs from (CLI, FastAPI worker, tests).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional

USER_AGENT = "lumicorepro-agent/1.0 (+https://lumicorepro.local)"
PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
W3C_ENDPOINT = "https://validator.w3.org/nu/"
NPM_REGISTRY = "https://registry.npmjs.org"

_STRATEGIES = ("mobile", "desktop")


def _get_json(url: str, timeout: int, headers: Optional[Dict[str, str]] = None) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def pagespeed_audit(
    url: str,
    strategy: str = "mobile",
    categories: Optional[List[str]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Lighthouse-style audit of a live URL via the free Google PSI API.

    Returns category scores (0-100), core web vitals metrics and the top
    opportunities. Network/HTTP problems become ``{"status": "failed"}`` —
    callers must treat this as advisory, never fatal.
    """
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"status": "failed", "message": "A full http(s) URL is required"}
    strategy = strategy if strategy in _STRATEGIES else "mobile"
    categories = categories or ["performance", "accessibility", "best-practices", "seo"]
    params = {
        "url": url,
        "strategy": strategy,
        "category": tuple(categories),
    }
    key = os.getenv("PAGESPEED_API_KEY", "").strip()
    if key:
        params["key"] = key
    full = f"{PAGESPEED_ENDPOINT}?{urllib.parse.urlencode(params, doseq=True)}"
    try:
        report = _get_json(full, timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"status": "failed", "url": url, "strategy": strategy, "message": str(exc)}

    out: Dict[str, Any] = {"status": "ok", "url": url, "strategy": strategy}
    lr = report.get("lighthouseResult") or {}
    scores: Dict[str, Any] = {}
    for cat, info in (lr.get("categories") or {}).items():
        score = info.get("score")
        scores[cat] = round(score * 100) if isinstance(score, (int, float)) else None
    out["scores"] = scores

    metrics: Dict[str, Any] = {}
    for metric_id, m in (lr.get("audits") or {}).items():
        if metric_id in ("first-contentful-paint", "largest-contentful-paint", "cumulative-layout-shift",
                         "speed-index", "interactive", "total-blocking-time"):
            metrics[metric_id] = {
                "display": m.get("displayValue") or str(m.get("numericValue", "")),
                "value": m.get("numericValue"),
            }
    out["metrics"] = metrics

    opportunities = []
    for audit_id, a in (lr.get("audits") or {}).items():
        details = a.get("details") or {}
        save = details.get("overallSavingsMs") or 0
        if a.get("score") is not None and a["score"] < 0.9 and save > 100:
            opportunities.append({
                "id": audit_id,
                "title": a.get("title"),
                "savings_ms": round(save),
            })
    out["opportunities"] = sorted(opportunities, key=lambda o: -o["savings_ms"])[:5]
    return out


def w3c_validate(
    url: Optional[str] = None,
    content: Optional[str] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Validate HTML with the free W3C Nu checker (URL or string content)."""
    payload = {"url": url} if url else {"content": content}
    if not (payload.get("url") or payload.get("content")):
        return {"status": "failed", "message": "Provide url= or content="}
    ctype = ("application/json", "text/html; charset=utf-8")  # (accept, send)
    data = payload["content"].encode("utf-8") if payload.get("content") else None
    if data is None:
        full = f"{W3C_ENDPOINT}?{urllib.parse.urlencode({'out': 'json', 'doc': payload['url']})}"
        req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    else:
        req = urllib.request.Request(
            f"{W3C_ENDPOINT}?out=json",
            data=data,
            method="POST",
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "text/html; charset=utf-8",
                "Accept": "application/json",
            },
        )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            report = json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"status": "failed", "message": str(exc)}

    messages = report.get("messages") or []
    errors = [m for m in messages if m.get("type") == "error"]
    warnings = [m for m in messages if m.get("type") not in ("error",)]
    return {
        "status": "ok",
        "target": payload.get("url") or "<provided content>",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "first_errors": [
            {"line": m.get("lastLine"), "message": m.get("message", "")[:160]}
            for m in errors[:5]
        ],
    }


def npm_latest(packages: Iterable[str], timeout: int = 20) -> Dict[str, Any]:
    """Latest published version per package from the free npm registry."""
    names = [p.strip() for p in (packages or []) if p and p.strip()]
    if not names:
        return {"status": "failed", "message": "No package names given"}
    result: Dict[str, Any] = {"status": "ok", "versions": {}, "missing": []}
    for name in names:
        base = name.split("@")[1] if name.startswith("@") else name.split("@")[0]
        if not base:
            result["missing"].append(name)
            continue
        pkg_path = urllib.parse.quote(base, safe="@/")
        try:
            meta = _get_json(f"{NPM_REGISTRY}/{pkg_path}/latest", timeout)
            result["versions"][name] = meta.get("version")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
            result["missing"].append(name)
    if len(result["missing"]) == len(names):
        result["status"] = "failed"
    return result


def http_reachable(url: str, timeout: int = 15) -> Dict[str, Any]:
    """One-shot GET: does this live URL answer?"""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"status": "failed", "message": "A full http(s) URL is required"}
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": "ok", "url": url, "http": resp.status, "final_url": resp.geturl()}
    except urllib.error.HTTPError as exc:
        return {"status": "ok", "url": url, "http": exc.code, "final_url": url}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"status": "failed", "url": url, "message": str(exc)}
