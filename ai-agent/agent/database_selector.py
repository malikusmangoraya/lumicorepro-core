from typing import Dict, Any, List
from utils.logger import agent_logger
from .memory_retriever import MemoryRetriever

class DatabaseSelector:
    """Selects and consolidates PostgreSQL database schemas from database/schemas/."""

    def __init__(self, memory_retriever: MemoryRetriever):
        self.retriever = memory_retriever

    def select_schemas(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select database SQL schema files matching requirement specification."""
        agent_logger.info("Searching database schemas...")
        features = spec.get("features", [])
        industry = spec.get("industry", "general")

        matched_schemas = self.retriever.search_database_schemas(features, industry)
        agent_logger.info(f"Selected {len(matched_schemas)} Database Schemas: {[s['name'] for s in matched_schemas]}")
        return matched_schemas
