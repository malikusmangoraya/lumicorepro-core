"""Pydantic-validated payload objects for the Agent Reach integration.

The planner engine and self-healing hooks consume these payloads after the raw
CLI fragments have been classified, so the pipeline works on validated
structures instead of untrusted shell output. When pydantic is unavailable the
payloads degrade to lightweight plain objects with the same `to_dict()` contract.
"""
import datetime as _dt
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except Exception:  # pragma: no cover - degraded environments only
    BaseModel = None
    Field = None
    PYDANTIC_AVAILABLE = False


class ChannelKind(str, Enum):
    """Agent Reach channels used by the LumicorePro agent."""

    GITHUB = "github"
    REDDIT = "reddit"
    TWITTER = "twitter"
    EXA = "exa"
    WEB = "web"


class _Model:
    """Compatibility base so payloads mirror pydantic's `to_dict()` contract."""

    def to_dict(self) -> Dict[str, Any]:
        return dict(getattr(self, "__dict__", {}))


if PYDANTIC_AVAILABLE:
    _Base = BaseModel
else:  # pragma: no cover
    _Base = _Model


class ReachFragment(_Base):
    """A single classified fragment returned by a channel search."""

    platform: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    score: float = 0.0
    reference_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        if PYDANTIC_AVAILABLE:
            return self.model_dump(mode="json")
        return dict(self.__dict__)


class ChannelStatus(_Base):
    """Health + routing status for one Agent Reach channel (from doctor)."""

    channel: str
    label: str = ""
    available: bool = False
    active_backend: Optional[str] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        if PYDANTIC_AVAILABLE:
            return self.model_dump(mode="json")
        return dict(self.__dict__)


class MarketSignalReport(_Base):
    """Pydantic-validated social/market signal payload for the planner engine."""

    website_type: str
    industry: str = "general"
    ok: bool = False
    reason: str = ""
    generated_at: Optional[str] = None
    channels_available: Dict[str, bool] = Field(default_factory=dict)
    fragments: List[ReachFragment] = Field(default_factory=list)
    complaints: List[str] = Field(default_factory=list)
    preferred_features: List[str] = Field(default_factory=list)
    design_topics: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        if PYDANTIC_AVAILABLE:
            return self.model_dump(mode="json")
        return {
            "website_type": self.website_type,
            "industry": self.industry,
            "ok": self.ok,
            "reason": self.reason,
            "generated_at": self.generated_at,
            "channels_available": self.channels_available,
            "fragments": [f.to_dict() for f in self.fragments],
            "complaints": self.complaints,
            "preferred_features": self.preferred_features,
            "design_topics": self.design_topics,
            "risk_flags": self.risk_flags,
        }


class GithubRecoveryPatch(_Base):
    """A verified community patch surfaced by the Agent Reach GitHub channel."""

    error_signature: str
    title: str
    url: str
    repo: str = ""
    language: str = "JavaScript"
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        if PYDANTIC_AVAILABLE:
            return self.model_dump(mode="json")
        return dict(self.__dict__)


class RecoveryBundle(_Base):
    """Payload consumed by quality_gates.py and code_modifier.py exception hooks."""

    applied: bool = False
    context: str = ""
    query: str = ""
    patches: List[GithubRecoveryPatch] = Field(default_factory=list)
    patch_title: Optional[str] = None
    patch_url: Optional[str] = None
    reference: str = ""

    def to_dict(self) -> Dict[str, Any]:
        if PYDANTIC_AVAILABLE:
            return self.model_dump(mode="json")
        return {
            "applied": self.applied,
            "context": self.context,
            "query": self.query,
            "patches": [p.to_dict() for p in self.patches],
            "patch_title": self.patch_title,
            "patch_url": self.patch_url,
            "reference": self.reference,
        }


def utc_iso() -> str:
    """ISO-8601 timestamp (UTC) for report freshness metadata."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")