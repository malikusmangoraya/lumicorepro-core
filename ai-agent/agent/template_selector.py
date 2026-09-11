from typing import Dict, Any, Optional
from utils.logger import agent_logger
from .memory_retriever import MemoryRetriever

class TemplateSelector:
    """Selects the highest scoring matching frontend template from local library."""

    # Fallback templates by website type
    FALLBACK_TEMPLATES = {
        "business": "src/templates/business/corporate-template-01",
        "ecommerce": "src/templates/ecommerce/electronics/electronics-template-01",
        "realestate": "src/templates/realestate/property-template-01",
        "restaurant": "src/templates/restaurant/cafe-template-01",
        "portfolio": "src/templates/portfolio/personal-template-01",
        "education": "src/templates/education/lms-template-01",
        "healthcare": "src/templates/healthcare/medical-template-01",
        "fitness": "src/templates/fitness/gym-template-01",
        "travel": "src/templates/travel/agency-template-01",
        "creative": "src/templates/creative/studio-template-01",
        "saas": "src/templates/business/corporate-template-01",
        "dashboard": "src/templates/business/corporate-template-01",
        "fintech": "src/templates/business/corporate-template-01",
        "social": "src/templates/business/corporate-template-01",
        "fashion": "src/templates/ecommerce/electronics/electronics-template-01",
        "crypto": "src/templates/franchise-template-01",
        "marketplace": "src/templates/franchise-template-01",
        "music": "src/templates/franchise-template-01",
        "gaming": "src/templates/franchise-template-01",
        "logistics": "src/templates/franchise-template-01",
        "agriculture": "src/templates/franchise-template-01",
        "energy": "src/templates/franchise-template-01",
        "beauty": "src/templates/franchise-template-01",
        "furniture": "src/templates/franchise-template-01",
        "pet": "src/templates/franchise-template-01",
        "wedding": "src/templates/franchise-template-01",
        "religious": "src/templates/franchise-template-01",
        "government": "src/templates/franchise-template-01",
        "news": "src/templates/franchise-template-01",
        "events": "src/templates/franchise-template-01",
        "job": "src/templates/franchise-template-01",
        "photography": "src/templates/portfolio/personal-template-01",
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
