"""Design Gate — LumicorePro Part 3.

Pre-deployment gate: 8 design-quality metrics each must be >= 85, else
REDESIGN_REQUIRED (and the agent may redesign the affected area, not just
patch).

Metrics:
  Brand clarity, Visual hierarchy, Typography, Spacing, Originality,
  CTA clarity, Mobile design, Interaction quality.
"""
import json
import os
from typing import Any, Dict, List, Optional

_THRESHOLD = 85.0

# Maps upstream 10-metric score keys onto the Design Gate metrics
_METRIC_SOURCE = {
    "brand_clarity": "brand_fit",
    "visual_hierarchy": "hierarchy",
    "typography": "typography",
    "spacing": "spacing",
    "originality": "originality",
    "cta_clarity": "cta_focus",
    "mobile_design": "composition",
    "interaction_quality": "motion",
}

_GATE_METRICS = [
    "brand_clarity", "visual_hierarchy", "typography", "spacing",
    "originality", "cta_clarity", "mobile_design", "interaction_quality",
]


class DesignGate:
    """Evaluates the 8-metric design gate before deployment."""

    def __init__(self, threshold: float = _THRESHOLD):
        self.threshold = threshold

    # ------------------------------------------------------------------
    def evaluate(self, score_result: Dict[str, Any],
                 design_decision: Optional[Dict[str, Any]] = None
                 ) -> Dict[str, Any]:
        """Evaluate the gate from the automated design score metrics."""
        metrics10 = score_result.get("metrics", {})
        if not metrics10:
            metrics10 = self._derive_fallback(design_decision)

        gate: Dict[str, float] = {}
        evidence: Dict[str, str] = {}
        for gate_metric in _GATE_METRICS:
            source_key = _METRIC_SOURCE[gate_metric]
            raw = metrics10.get(source_key, self.threshold)
            # cta_focus lives on a 0-1 scale in some paths
            if source_key == "cta_focus" and raw <= 1.0:
                raw = raw * 100.0
            gate[gate_metric] = round(max(0.0, min(100.0, raw)), 1)
            evidence[gate_metric] = f"source:{source_key}={metrics10.get(source_key)}"

        failing = [
            m for m in _GATE_METRICS
            if gate.get(m, 0) < self.threshold
        ]
        passed = not failing

        return {
            "threshold": self.threshold,
            "metrics": gate,
            "evidence": evidence,
            "failing": failing,
            "passed": passed,
            "decision": "APPROVED" if passed else "REDESIGN_REQUIRED",
            "recommendations": self._recommendations(failing),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _derive_fallback(
            decision: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Heuristic fallback when no automated score is available."""
        decision = decision or {}
        default: Dict[str, float] = {}
        lux = 0.6 if decision.get("brand") == "luxury" else 0.0
        visual = decision.get("visual", {}) or {}
        density = visual.get("density", 0.4)
        default["brand_fit"] = 95.0 if decision.get("brand") else 70.0
        default["hierarchy"] = 90.0 - 10 * decision.get("avoid", [])
        default["typography"] = 90.0 + 5 * lux
        default["spacing"] = 90.0 - 15 * max(0.0, density - 0.6)
        default["originality"] = 88.0
        default["cta_focus"] = 90.0
        default["composition"] = 90.0
        default["motion"] = 88.0
        return default

    # ------------------------------------------------------------------
    @staticmethod
    def _recommendations(failing: List[str]) -> List[Dict[str, str]]:
        advice = {
            "brand_clarity": "Sharpen the brand voice; ensure logo, color "
                             "and messaging carry the brand alone.",
            "visual_hierarchy": "Give each section one clear focal point; "
                                "fix heading scale jumps.",
            "typography": "Match type sizes to hierarchy; remove font soup; "
                          "check measure and pairing.",
            "spacing": "Apply the token spacing scale consistently across "
                       "sections.",
            "originality": "Replace generic/lorem copy and repeated "
                           "component formulas with brand-specific design.",
            "cta_clarity": "Make the primary CTA visually dominant and "
                           "above the fold.",
            "mobile_design": "Recompose the design for mobile viewports; "
                             "hero must not be excessively tall.",
            "interaction_quality": "Balance motion so it feels deliberate "
                                   "rather than excessive or missing.",
        }
        return [{"metric": m, "advice": advice.get(m, "")} for m in failing]


def evaluate_design_gate(score_result: Dict[str, Any],
                         design_decision: Optional[Dict[str, Any]] = None
                         ) -> Dict[str, Any]:
    """One-call helper for orchestrator wiring."""
    return DesignGate().evaluate(score_result, design_decision)


if __name__ == "__main__":
    import sys
    sample = {
        "metrics": {
            "brand_fit": 90, "hierarchy": 82, "typography": 88,
            "spacing": 90, "originality": 95, "cta_focus": 88,
            "composition": 84, "motion": 80,
        }
    }
    if len(sys.argv) > 1:
        try:
            sample = json.loads(sys.argv[1])
        except Exception:
            pass
    result = evaluate_design_gate(sample)
    print(json.dumps(result, indent=1))