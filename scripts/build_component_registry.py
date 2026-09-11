"""Build the canonical component-contract registry artifact.

Scans the monorepo's local `src/components/**/*.jsx` library and materializes a
deterministic JSON index (absolute alias paths + prop contracts) used by the AI
agent's validator as the rigidity base for Pillar 2 enforcement.

Usage:
    python scripts/build_component_registry.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-agent"))

from agent.component_registry import build_registry_index  # noqa: E402

if __name__ == "__main__":
    payload = build_registry_index(str(ROOT / "registry" / "component-contracts.json"))
    print(f"Indexed {payload['count']} components -> {payload['categories']}")
    sys.exit(0)