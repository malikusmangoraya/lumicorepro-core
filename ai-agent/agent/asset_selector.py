from typing import Dict, Any, List
from utils.logger import agent_logger
from .memory_retriever import MemoryRetriever

class AssetSelector:
    """Selects matching local images, icons, and animation CSS rules."""

    def __init__(self, memory_retriever: MemoryRetriever):
        self.retriever = memory_retriever

    def select_assets(self, spec: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Select images, icons, and animations based on industry and requirements."""
        agent_logger.info("Searching local asset library...")
        industry = spec.get("industry", "general")
        asset_types = ["image", "icon", "animation"]

        assets = self.retriever.search_assets(industry, asset_types)
        for group in assets.values():
            for asset in group:
                self.retriever.bump_usage("asset", asset.get("name") or "")

        agent_logger.info(
            f"Selected Assets: {len(assets.get('images', []))} images, "
            f"{len(assets.get('icons', []))} icons, "
            f"{len(assets.get('animations', []))} animations."
        )
        return assets
