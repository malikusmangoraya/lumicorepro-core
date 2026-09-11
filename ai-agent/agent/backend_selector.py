from typing import Dict, Any, Optional
from utils.logger import agent_logger
from .memory_retriever import MemoryRetriever

class BackendSelector:
    """Selects matching Express.js backend base and configures required modules."""

    def __init__(self, memory_retriever: MemoryRetriever):
        self.retriever = memory_retriever

    def select_backend(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find best matching backend and active modules for specification."""
        agent_logger.info("Searching backend library...")
        category = spec.get("website_type", "ecommerce")
        industry = spec.get("industry", "general")
        features = spec.get("features", [])

        backend = self.retriever.search_backend(category, features)
        if backend:
            self.retriever.bump_usage("backend", backend["name"])
            agent_logger.info(f"Selected Backend Base: '{backend['name']}' with modules: {backend.get('modules', [])}")
            return backend

        # Better fallback based on website type
        ec_backend = self.retriever.search_backend("ecommerce", features)
        if ec_backend:
            self.retriever.bump_usage("backend", ec_backend["name"])
            agent_logger.warning(f"No backend for '{category}'. Falling back to E-Commerce Base.")
            return ec_backend

        agent_logger.warning("No custom backend base matched. Defaulting to E-Commerce Base.")
        return {
            "name": "E-Commerce Modular Base API",
            "type": "backend",
            "category": "ecommerce",
            "file_path": "backend-library/ecommerce-base",
            "modules": ["auth", "products", "cart", "orders"],
            "dependencies": ["express", "cors", "dotenv", "pg"]
        }
