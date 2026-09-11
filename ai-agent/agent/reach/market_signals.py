"""Market signal research via the Agent Reach router (Reddit + Twitter/X).

During full generation (orchestrator Phase 1) the market analyzer triggers
Agent Reach queries targeting the communities where the target audience
complains and asks for features. Raw snippets are classified into Pydantic-
validated complaint / preferred-feature / design-topic buckets and handed to
the planner engine as a `MarketSignalReport`.

Every subprocess effort runs through `process.run_cli`
(asyncio.create_subprocess_exec); a headless server without login-backed
channels degrades to an empty-but-consistent report.
"""
import re
import threading
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger
from agent.reach.models import ChannelStatus, MarketSignalReport, ReachFragment, utc_iso
from agent.reach.process import in_worker_loop
from agent.reach.router import AgentReachRouter, infos_for_channel

_DEFAULT_SUBREDDIS = {
    "saas": ["r/saas", "r/SaaS", "r/webdev"],
    "ecommerce": ["r/ecommerce", "r/Shopify", "r/smallbusiness"],
    "ecommerce_shop": ["r/ecommerce", "r/shopify"],
    "restaurant": ["r/restaurantowners", "r/KitchenConfidential"],
    "realestate": ["r/RealEstate", "r/realtors"],
    "healthcare": ["r/healthcare", "r/medicine"],
    "fitness": ["r/fitness30plus", "r/crossfit"],
    "education": ["r/Teachers", "r/edtech"],
    "travel": ["r/travel", "r/TravelHacks"],
    "fintech": ["r/fintech", "r/personalfinance"],
    "crypto": ["r/CryptoCurrency", "r/Bitcoin"],
    "startup": ["r/startups", "r/Entrepreneur"],
    "dashboard": ["r/ProductManagement", "r/SaaS"],
    "lawfirm": ["r/LawFirm"],
    "event": ["r/EventPlanning"],
    "general": ["r/webdev", "r/marketing"],
}

_COMPLAINT_LEXICON = [
    "slow", "broken", "bug", "error", "crash", "unusable", "confusing",
    "hard to use", "difficult", "hate", "worst", "expensive", "paywall",
    "checkout fail", "nothing works", "waste", "annoying", "ugly", "refund",
]

_PREFERENCE_LEXICON = [
    "dark mode", "search", "filter", "mobile app", "cart", "wishlist",
    "chat", "live chat", "whatsapp", "payment", "checkout", "review",
    "rating", "notification", "search bar", "fast load", "category",
    "multi vendor", "wish supports",
]

_DESIGN_LEXICON = [
    "clean", "modern", "theme", "dark mode", "accessibility", "responsive",
    "animation", "font", "layout", "mobile-first", "color", "minimal",
    "loading speed", "seo", "bounce", "landing",
]

_RISK_LEXICON = ["bug", "crash", "broken", "slow", "compliance", "privacy", "pci", "gdpr"]

_router: Optional[AgentReachRouter] = None
_router_lock = threading.Lock()


def _get_router() -> AgentReachRouter:
    global _router
    if _router is None:
        with _router_lock:
            if _router is None:
                _router = AgentReachRouter(probe=True)
    return _router


def subreddits_for(website_type: str, industry: str) -> List[str]:
    """Pick community subreddits for a website type/industry, with fallbacks."""
    for key in (website_type, industry, "general"):
        subs = _DEFAULT_SUBREDDIS.get(str(key).lower())
        if subs:
            return subs
    return _DEFAULT_SUBREDDIS["general"]


def build_signal_query(spec: Dict[str, Any]) -> str:
    """Build a search query from spec keywords/intent."""
    tokens: List[str] = []
    for key in ("keywords",):
        value = spec.get(key)
        if isinstance(value, list):
            tokens.extend(str(t) for t in value[:5])
        elif isinstance(value, str) and value.strip():
            tokens.append(value.strip())
    tokens.append(str(spec.get("website_type", "ecommerce")))
    tokens.append(str(spec.get("industry", "general")))
    seen: List[str] = []
    for token in tokens:
        token = token.strip()
        if token and token not in seen:
            seen.append(token)
    return " ".join(seen[:8])


def classify_signal(text: str) -> Dict[str, List[str]]:
    """Bucket a raw fragment into complaints, preferred features and design topics."""
    lower = (text or "").lower()
    complaints = [kw for kw in _COMPLAINT_LEXICON if kw in lower]
    preferred = [kw for kw in _PREFERENCE_LEXICON if kw in lower]
    design = [kw for kw in _DESIGN_LEXICON if kw in lower]
    return {
        "complaints": complaints,
        "preferred_features": preferred,
        "design_topics": design,
    }


def _summarize(results: List[Any]) -> Dict[str, Any]:
    """Aggregate channel results into a MarketSignalReport payload."""
    fragments: List[ReachFragment] = []
    complaints: List[str] = []
    preferred: List[str] = []
    design_topics: List[str] = []
    risk_flags: List[str] = []
    channels_available: Dict[str, bool] = {}
    reasons: List[str] = []

    for res in results:
        if res is None:
            continue
        channels_available[res.channel] = res.available
        if not res.available:
            if res.reason:
                reasons.append(f"{res.channel}: {res.reason}")
            continue
        for rec in res.records:
            snippet = rec.get("snippet") or rec.get("title") or ""
            if len(snippet.strip()) < 30:
                continue
            fragments.append(
                ReachFragment(
                    platform=res.channel,
                    title=rec.get("title") or "",
                    url=rec.get("url") or "",
                    snippet=snippet[:600],
                    score=float(rec.get("score") or 0),
                    reference_id=str(rec.get("query") or ""),
                )
            )
            klass = classify_signal(snippet)
            for item in klass["complaints"]:
                if item not in complaints:
                    complaints.append(item)
            for item in klass["preferred_features"]:
                if item not in preferred:
                    preferred.append(item)
            for item in klass["design_topics"]:
                if item not in design_topics:
                    design_topics.append(item)
            flag = _extract_risk(snippet)
            if flag and flag not in risk_flags:
                risk_flags.append(flag)

    ok = bool(fragments)
    reason = "; ".join(reasons[:2]) if reasons else ("" if ok else infos_for_channel("reddit"))
    return {
        "ok": ok,
        "reason": reason,
        "fragments": fragments,
        "complaints": complaints,
        "preferred_features": preferred,
        "design_topics": design_topics,
        "risk_flags": risk_flags,
        "channels_available": channels_available,
    }


def _extract_risk(text: str) -> Optional[str]:
    lower = (text or "").lower()
    for flag in _RISK_LEXICON:
        if flag in lower:
            return f"risk:{flag}"
    return None


async def collect_market_signals(spec: Dict[str, Any]) -> MarketSignalReport:
    """Query Agent Reach (Reddit + Twitter/X) and return a validated report."""
    import asyncio

    router = _get_router()
    website_type = str(spec.get("website_type", "ecommerce"))
    industry = str(spec.get("industry", "general"))
    query = build_signal_query(spec)
    subs = subreddits_for(website_type, industry)

    sub_tasks = []
    for sub in subs[:2]:
        sub_tasks.append(router.search("reddit", query, num=5, subreddit=sub))
    sub_tasks.append(router.search("twitter", query, num=8))

    results = list(await asyncio.gather(*sub_tasks, return_exceptions=True))
    results = [r for r in results if not isinstance(r, Exception)]

    summary = _summarize(results)
    report = MarketSignalReport(
        website_type=website_type,
        industry=industry,
        ok=summary["ok"],
        reason=summary["reason"],
        generated_at=utc_iso(),
        channels_available=summary["channels_available"],
        fragments=summary["fragments"],
        complaints=summary["complaints"],
        preferred_features=summary["preferred_features"],
        design_topics=summary["design_topics"],
        risk_flags=summary["risk_flags"],
    )
    return report


def market_signals_sync(spec: Dict[str, Any], timeout: float = 25.0) -> Dict[str, Any]:
    """Synchronous entry point for the sync orchestrator (worker-thread safe).

    Never blocks the core FastAPI loop: when a loop is already running in this
    thread it returns an empty report immediately.
    """
    import asyncio

    def _factory():
        return asyncio.wait_for(collect_market_signals(spec), timeout=timeout)

    result = in_worker_loop(_factory)
    if result is None:
        return {
            "ok": False,
            "reason": "event-loop-thread: search deferred to a running loop",
            "website_type": str(spec.get("website_type", "ecommerce")),
            "industry": str(spec.get("industry", "general")),
            "fragments": [],
            "complaints": [],
            "preferred_features": [],
            "design_topics": [],
            "risk_flags": [],
            "channels_available": {},
        }
    return result.to_dict() if hasattr(result, "to_dict") else {}