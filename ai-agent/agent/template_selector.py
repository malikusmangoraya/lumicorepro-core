from typing import Dict, Any, Optional
from utils.logger import agent_logger
from .memory_retriever import MemoryRetriever

class TemplateSelector:
    """Selects the highest scoring matching frontend template from local library."""

    # Fallback templates by website type (point to real library dirs)
    FALLBACK_TEMPLATES = {
        "business": "src/templates/business",
        "ecommerce": "src/templates/ecommerce",
        "realestate": "src/templates/realestate",
        "restaurant": "src/templates/restaurant",
        "portfolio": "src/templates/portfolio",
        "education": "src/templates/education",
        "healthcare": "src/templates/healthcare",
        "fitness": "src/templates/fitness",
        "travel": "src/templates/travel",
        "creative": "src/templates/creative",
        "ai": "src/templates/ai",
        "dashboard": "src/templates/dashboard",
        "saas": "src/templates/business",
        "fintech": "src/templates/business",
        "social": "src/templates/business",
        "fashion": "src/templates/ecommerce",
        "crypto": "src/templates/business",
        "marketplace": "src/templates/marketplace",
        "music": "src/templates/business",
        "gaming": "src/templates/business",
        "logistics": "src/templates/business",
        "agriculture": "src/templates/business",
        "energy": "src/templates/business",
        "beauty": "src/templates/business",
        "furniture": "src/templates/business",
        "pet": "src/templates/business",
        "wedding": "src/templates/wedding",
        "religious": "src/templates/business",
        "government": "src/templates/business",
        "news": "src/templates/business",
        "events": "src/templates/business",
        "job": "src/templates/business",
        "photography": "src/templates/portfolio",
    }

    def __init__(self, memory_retriever: MemoryRetriever):
        self.retriever = memory_retriever

    def select_template(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Select best matching template for the requirement specification."""
        agent_logger.info("Searching local template library...")
        category = spec.get("website_type", "ecommerce")
        industry = spec.get("industry", "general")
        features = spec.get("features", [])

        templates = self.retriever.search_templates(category, industry, features)
        if templates:
            best_template = templates[0]
            self.retriever.bump_usage("template", best_template["name"])
            agent_logger.info(f"Selected Template: '{best_template['name']}' (Score: {best_template.get('score', 0)})")
            return best_template

        # Fallback to matching template type
        file_path = self.FALLBACK_TEMPLATES.get(category, "src/templates/business/corporate-template-01")
        agent_logger.warning(f"No perfect template found for '{category}'. Falling back to {file_path}")
        return {
            "name": f"Default {category.title()} Template",
            "type": "template",
            "category": category,
            "industry": industry,
            "file_path": file_path,
            "dependencies": ["react", "react-dom", "lucide-react"],
            "features": features
        }
