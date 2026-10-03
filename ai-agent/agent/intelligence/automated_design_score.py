"""Automated Design Scoring — LumicorePro Part 3.

Computes the 10-metric visual quality score (total 100) from DesignLint
findings + project artifacts, feeding the Part 2 weighted quality score
(Visual Quality = 20% weight).

Metrics (weights):
  Typography 15%  Composition 15%  Spacing 15%  Color 10%  Imagery 10%
  Hierarchy 10%   Consistency 10%  Brand Fit 10%  Motion 5%   Originality 10%

Scores are evidence-based: derived from DesignLint findings, token files,
and project structure — never guessed.
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Severity penalty when a lint finding maps to a metric
_SEVERITY_PENALTY = {"P1": 12, "P2": 7, "P3": 4, "P4": 2}

# DL code -> affected metric(s) and per-metric impact basis
_DL_TO_METRIC: Dict[str, List[str]] = {
    "DL001": ["typography", "composition"],
    "DL002": ["color"],
    "DL003": ["composition", "originality"],
    "DL004": ["spacing"],
    "DL005": ["composition"],
    "DL006": ["color", "originality"],
    "DL007": ["originality", "motion"],
    "DL008": ["typography", "hierarchy"],
    "DL009": ["composition"],
    "DL010": ["hierarchy"],
    "DL011": ["spacing", "composition"],
    "DL012": ["composition"],
    "DL013": ["originality"],
    "DL014": ["motion", "originality"],
    "DL015": ["brand_fit", "originality"],
}


class AutomatedDesignScore:
    """Compute the 10-metric visual score from artifacts + lint output."""

    _W = {
        "typography": 15, "composition": 15, "spacing": 15, "color": 10,
        "imagery": 10, "hierarchy": 10, "consistency": 10,
        "brand_fit": 10, "motion": 5, "originality": 10,
    }

    def __init__(self, benchmark_targets: Optional[Dict[str, float]] = None):
        # Target scores from Part 3 §8 Visual Benchmarking
        self.targets = benchmark_targets or {
            "typography": 90, "composition": 85, "spacing": 80,
            "color": 80, "imagery": 90, "hierarchy": 85,
            "consistency": 80, "brand_fit": 90, "motion": 80,
            "originality": 90,
        }

    # ------------------------------------------------------------------
    def score(self, project_dir: str,
              lint_result: Optional[Dict[str, Any]] = None,
              decision: Optional[Dict[str, Any]] = None
              ) -> Dict[str, Any]:
        root = Path(project_dir)
        lint_result = lint_result or self._run_lint(root)

        # Start each metric at 95 to allow meaningful deductions
        metrics = {k: 95.0 for k in self._W}

        # Apply lint penalties (capped so one very templated file set
        # cannot drive a metric to zero)
        penalty_acc: Dict[str, float] = {k: 0.0 for k in self._W}
        for finding in lint_result.get("findings", []):
            code = finding.get("code", "")
            sev = finding.get("severity", "P3")
            affected = _DL_TO_METRIC.get(code, [])
            pen = _SEVERITY_PENALTY.get(sev, 2)
            for metric in affected:
                penalty_acc[metric] = min(
                    45.0, penalty_acc[metric] + pen)
                metrics[metric] = 95.0 - penalty_acc[metric]

        # Structural positives (evidence from project)
        self._apply_tokens_bonus(root, metrics)
        self._apply_assets_bonus(root, metrics)
        self._apply_brand_bonus(root, metrics, decision)
        self._apply_motion_bonus(root, metrics)

        # Clamp to 0-100
        for k in metrics:
            metrics[k] = round(min(100.0, max(0.0, metrics[k])), 1)

        total = round(sum(metrics[k] * (w / 100.0)
                          for k, w in self._W.items()), 1)

        gap = {
            m: round(max(0.0, self.targets.get(m, 80) / 10.0 -
                         metrics[m] / 10.0), 1)
            for m in self._W
        }
        weakest = min(self._W, key=lambda m: metrics[m])

        return {
            "visual_quality_score": total,
            "metrics": metrics,
            "weights": self._W,
            "targets": {k: v / 10.0 for k, v in self.targets.items()},
            "gap_to_target": gap,
            "weakest_metric": weakest,
            "benchmark_passed": all(
                metrics[m] / 10.0 >= self.targets[m] / 10.0 for m in self._W),
            "lint": {
                "total_findings": lint_result.get("summary", {}).get(
                    "total", 0),
                "severity": lint_result.get("summary", {}).get(
                    "by_severity", {}),
                "pass": lint_result.get("pass", False),
            },
            "evidence_basis": self._evidence_summary(root, lint_result),
        }

    # ------------------------------------------------------------------
    def grade(self, score: float) -> str:
        if score >= 92:
            return "SIGNATURE"
        if score >= 88:
            return "PREMIUM"
        if score >= 80:
            return "STANDARD"
        return "BELOW_STANDARD"

    def _run_lint(self, root: Path) -> Dict[str, Any]:
        try:
            from .design_lint import DesignLint
            return DesignLint().lint_directory(str(root))
        except Exception:
            return {"findings": [], "summary": {"total": 0,
                    "by_severity": {}}, "pass": True}

    # ------------------------------------------------------------------
    @staticmethod
    def _tokens_payload(root: Path) -> Dict[str, Any]:
        path = root / "design-tokens.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _apply_tokens_bonus(self, root: Path,
                            metrics: Dict[str, float]) -> None:
        tokens = self._tokens_payload(root)
        if not tokens:
            metrics["color"] -= 10
            metrics["spacing"] -= 8
            return
        palette = tokens.get("palette", {}) or {}
        spacing = tokens.get("spacing", {}) or {}
        typo = tokens.get("typography", {}) or {}
        if any(palette.get(k) for k in
               ("primary", "accent", "primary_hsl", "accent_hsl")):
            metrics["color"] = min(100, metrics["color"] + 2)
        if len(spacing) >= 4:
            metrics["spacing"] = min(100, metrics["spacing"] + 2)
        if any(typo.get(k) for k in ("scale", "font_display", "h1")):
            metrics["typography"] = min(100, metrics["typography"] + 2)

    def _apply_assets_bonus(self, root: Path,
                            metrics: Dict[str, float]) -> None:
        # Single shared walk: image counts come from the SourceIndex instead
        # of three separate rglob passes over the whole tree.
        from .source_index import get_source_index
        index = get_source_index(str(root))
        image_lists = index.files(".png", ".webp", ".jpg")
        image_count = sum(1 for p in image_lists
                          if "/public/assets/" in
                          str(Path(p)).replace("\\", "/"))
        metrics["imagery"] = min(
            100, metrics["imagery"] +
            (6 if image_count >= 6 else 2 if image_count >= 3 else 0))

    def _apply_brand_bonus(self, root: Path,
                           metrics: Dict[str, float],
                           decision: Optional[Dict[str, Any]]) -> None:
        # Brand candidates from the shared index — single walk (was 3×rglob)
        # since Logo/Brand/logo files are always child paths of a source dir.
        from .source_index import get_source_index
        index = get_source_index(str(root))
        source_paths = index.files(".jsx", ".tsx")
        brand_files = [p for p in source_paths
                       if "/src/" in str(Path(p)).replace("\\", "/")
                       and any(tok in Path(p).name
                               for tok in ("Logo", "Brand", "logo"))]
        if brand_files:
            metrics["brand_fit"] = min(100, metrics["brand_fit"] + 4)
            metrics["originality"] = min(100, metrics["originality"] + 3)
        else:
            metrics["brand_fit"] -= 8
            metrics["originality"] -= 5
        if decision and decision.get("reference_hints"):
            metrics["originality"] = min(
                100, metrics["originality"] +
                (4 if len(decision["reference_hints"]) <= 3 else 0))
        avoid_list = decision.get("avoid") if decision else []
        if avoid_list:
            metrics["consistency"] = min(100, metrics["consistency"] + 2)

    def _apply_motion_bonus(self, root: Path,
                            metrics: Dict[str, float]) -> None:
        # Motion pattern scan over the shared source index (was 2×rglob).
        from .source_index import get_source_index
        index = get_source_index(str(root))
        sources = [Path(p) for p in
                   index.files(".jsx", ".tsx")][:160]
        count = 0
        for src in sources:
            try:
                count += len(re.findall(
                    r"\b(?:animate-|motion\.|framer-motion|transition-all)",
                    src.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                pass
        if count > 0 and count < 200:
            metrics["motion"] = min(95, metrics["motion"] + 1)
        elif count == 0:
            metrics["motion"] -= 4  # no motion at all = flat UX

    def _evidence_summary(self, root: Path,
                          lint_result: Dict[str, Any]) -> List[str]:
        evidence = [
            f"lint findings: {lint_result.get('summary', {}).get('total', 0)}",
            f"tokens: {'present' if self._tokens_payload(root) else 'missing'}",
            f"assets: {self._count_assets(root)}",
            f"brand: {self._count_brand(root)}",
        ]
        return evidence

    @staticmethod
    def _count_assets(root: Path) -> int:
        from .source_index import get_source_index
        index = get_source_index(str(root))
        rel_assets = sum(1 for p in index.files(".png", ".webp", ".jpg")
                         if "/public/assets/" in
                         str(Path(p)).replace("\\", "/"))
        return rel_assets

    @staticmethod
    def _count_brand(root: Path) -> int:
        from .source_index import get_source_index
        index = get_source_index(str(root))
        brands = [p for p in index.files(".jsx", ".tsx")
                  if "/src/" in str(Path(p)).replace("\\", "/")
                  and any(tok in Path(p).name
                          for tok in ("Logo", "Brand", "logo"))]
        return len(brands)


def score_design(project_dir: str,
                 lint_result: Optional[Dict[str, Any]] = None,
                 decision: Optional[Dict[str, Any]] = None
                 ) -> Dict[str, Any]:
    """One-call helper for orchestrator wiring."""
    return AutomatedDesignScore().score(project_dir, lint_result, decision)


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = score_design(target)
    print(json.dumps(result, indent=1))