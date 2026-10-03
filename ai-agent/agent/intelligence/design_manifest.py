"""Design Memory / Manifest — LumicorePro Part 3.

Writes a machine-readable `design-manifest.json` into every generated
project and maintains a traceable `.artifacts/` chain
(01-business.json → 14-deployment.json) so later edits ("change the hero")
modify the existing design system instead of re-deriving it.

The manifest makes every design decision traceable for debugging and
iteration: design decision where -> stored artifact.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Canonical artifact chain (Part 3 §7)
_ARTIFACT_CHAIN = [
    "01-business", "02-audience", "03-brand", "04-reference",
    "05-playbook", "06-ux", "07-design", "08-architecture",
    "09-build", "10-designlint", "11-visual-score",
    "12-critic-review", "13-qa", "14-deployment",
]

_MANIFEST_SCHEMA = [
    "brand", "visual", "typography", "colors", "spacing",
    "components", "industry", "reference_sources", "constraints_resolved",
    "reproducibility", "created_at", "project",
]


class DesignManifestWriter:
    """Writes and reads design manifests + artifact chains."""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)

    # ------------------------------------------------------------------
    @property
    def manifest_path(self) -> Path:
        return self.project_dir / "design-manifest.json"

    @property
    def artifacts_dir(self) -> Path:
        return self.project_dir / ".artifacts"

    # ------------------------------------------------------------------
    def write_manifest(self, decision: Dict[str, Any],
                       extra: Optional[Dict[str, Any]] = None) -> Path:
        """Persist the design decision engine output as a manifest."""
        decision = decision or {}

        manifest: Dict[str, Any] = {}
        for key in _MANIFEST_SCHEMA:
            value = decision.get(key)
            if value is not None:
                manifest[key] = value

        manifest.setdefault("brand", {"archetype": "minimal",
                                      "personality": []})
        manifest.setdefault("visual", {})
        manifest.setdefault("typography", {})
        manifest.setdefault("colors", {"tokens": {}, "source":
                                       "design-tokens.json"})
        manifest.setdefault("spacing", {"scale": "token_based"})
        manifest.setdefault("components", {})
        manifest.setdefault("industry", "saas")
        manifest.setdefault("reference_sources", [])
        manifest.setdefault("constraints_resolved", {})
        manifest.setdefault("reproducibility", {})
        manifest["created_at"] = datetime.now(timezone.utc).isoformat()
        manifest["project"] = self.project_dir.name

        # Persist the full design decision (includes playbook/conversion)
        if decision.get("conversion") is not None:
            manifest["conversion"] = decision["conversion"]
        if decision.get("pages") is not None:
            manifest["pages"] = decision["pages"]
        if decision.get("avoid") is not None:
            manifest["avoid"] = decision["avoid"]
        if extra:
            manifest["qa_metadata"] = extra

        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")
        return self.manifest_path

    # ------------------------------------------------------------------
    def write_artifact(self, stage: str, payload: Dict[str, Any]) -> Path:
        """Write one `.artifacts/NN-name.json` stage file."""
        if stage not in _ARTIFACT_CHAIN:
            candidates = [s for s in _ARTIFACT_CHAIN
                          if s.endswith("-" + stage) or
                          s.startswith(stage)]
            if not candidates:
                # accept custom but keep numeric prefix ordering
                stage = stage
            else:
                stage = candidates[0]
        else:
            stage = stage

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        path = self.artifacts_dir / f"{stage}.json"
        payload.setdefault("_stage", stage)
        payload.setdefault("_written_at",
                           datetime.now(timezone.utc).isoformat())
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    def load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(
                self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def artifact_stages_present(self) -> Dict[str, bool]:
        present = {}
        if self.artifacts_dir.exists():
            for name in _ARTIFACT_CHAIN:
                present[name] = (self.artifacts_dir / f"{name}.json").exists()
        return present

    # ------------------------------------------------------------------
    def trace(self, stage_name: Optional[str] = None) -> Any:
        """Expose a stored stage payload for iteration/debugging."""
        if not self.artifacts_dir.exists():
            return None
        if stage_name:
            path = self.artifacts_dir / f"{stage_name}.json"
            if not path.exists():
                for cand in _ARTIFACT_CHAIN:
                    if stage_name in cand:
                        path = self.artifacts_dir / f"{cand}.json"
                        break
            if path.exists():
                try:
                    return json.loads(
                        path.read_text(encoding="utf-8"))
                except Exception:
                    return None
        return {name: self.trace(name) for name in _ARTIFACT_CHAIN
                if (self.artifacts_dir / f"{name}.json").exists()}


def ensure_design_memory(project_dir: str,
                         decision: Dict[str, Any],
                         stage_payloads: Optional[Dict[str, Dict[str, Any]]]
                         = None) -> Dict[str, str]:
    """One-call helper: write manifest + artifact chain for a project."""
    writer = DesignManifestWriter(project_dir)
    manifest = writer.write_manifest(decision)
    written: Dict[str, str] = {
        "manifest": str(manifest),
        "artifacts": [],
    }
    for stage, payload in (stage_payloads or {}).items():
        path = writer.write_artifact(stage, payload)
        written["artifacts"].append(str(path))
    return written


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sample = {
        "industry": "saas",
        "brand": {"archetype": "minimal", "personality": []},
        "visual": {"density": 0.4, "motion": 0.5, "3d": False},
        "typography": {"heading_style": "clean_sans",
                       "body_style": "modern_sans"},
        "colours_placeholder": True,
    }
    result = ensure_design_memory(
        target, sample,
        {"01-business": {"kind": "demo"}, "02-audience": {"kind": "demo"}})
    print(json.dumps(result, indent=1))