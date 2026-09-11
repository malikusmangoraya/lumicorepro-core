import json
from pathlib import Path
from typing import Dict, Any, List
from utils.logger import agent_logger
from config.settings import REGISTRY_DIR

class TrendingFeaturesInjector:
    """Phase 4: Auto-inject 5-7 trending market-leading features."""

    MIN_FEATURES = 5
    MAX_FEATURES = 7

    def __init__(self):
        self._registry: List[Dict[str, Any]] = []
        registry_path = REGISTRY_DIR / "trending-features.json"
        if registry_path.exists():
            with open(registry_path, "r", encoding="utf-8") as f:
                self._registry = json.load(f)

    def inject(self, spec: Dict[str, Any], market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Select and inject trending features into the requirement spec."""
        agent_logger.info("Phase 4: Injecting trending market-leading features...")

        website_type = spec.get("website_type", "ecommerce")
        industry = spec.get("industry", "general")
        existing_features = set(spec.get("features", []))

        scored: List[tuple] = []
        for feat in self._registry:
            tags = feat.get("tags", [])
            if website_type in tags or industry in tags or "general" in tags:
                score = feat.get("roi_score", 50)
                if feat["id"] not in existing_features:
                    scored.append((score, feat))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [f for _, f in scored[: self.MAX_FEATURES]]

        if len(selected) < self.MIN_FEATURES:
            for feat in self._registry:
                if feat not in selected and len(selected) < self.MIN_FEATURES:
                    selected.append(feat)

        injected_ids = [f["id"] for f in selected]
        injected_components = []
        for f in selected:
            injected_components.extend(f.get("components", []))

        for feat_id in injected_ids:
            existing_features.add(feat_id)

        spec["features"] = list(existing_features)
        spec["trending_features"] = injected_ids

        result = {
            "injected_count": len(selected),
            "features": selected,
            "feature_ids": injected_ids,
            "required_components": list(set(injected_components)),
            "market_alignment": market_analysis.get("market_trends", [])[:3],
        }

        agent_logger.info(f"Injected {len(selected)} trending features: {', '.join(injected_ids)}")
        return result
