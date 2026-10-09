"""Niche page recipes backed by the selector's single layout catalog."""

from typing import Any, Dict, Optional

from .design_system_engine import get_design_catalog


_NICHE_PAGES = {
    "insurance": {
        "name": "Claims",
        "path": "/claims",
        "blocks": ["claims_intake", "claims_queue", "coverage_review"],
        "heading": "Claims, from intake to review",
        "description": "Collect incident details, supporting documents, and review steps in one clear workflow.",
    },
    "real_estate": {
        "name": "Listings",
        "path": "/listings",
        "blocks": ["property_listings", "service_booking"],
        "heading": "Find a place that fits",
        "description": "Explore property details and arrange a conversation about the next step.",
    },
    "food": {
        "name": "Menu",
        "path": "/menu",
        "blocks": ["menu_reservations", "service_booking"],
        "heading": "A table for good food",
        "description": "Browse the menu and plan a visit with the people you are bringing.",
    },
    "education": {
        "name": "Courses",
        "path": "/courses",
        "blocks": ["course_curriculum", "event_schedule"],
        "heading": "A clear path through the material",
        "description": "Review the course outline and decide where to begin.",
    },
    "fitness": {
        "name": "Programs",
        "path": "/programs",
        "blocks": ["fitness_program", "service_booking"],
        "heading": "Choose a program that fits your routine",
        "description": "Compare available training formats and ask about coaching.",
    },
    "portfolio": {
        "name": "Work",
        "path": "/work",
        "blocks": ["portfolio_cases", "product_features"],
        "heading": "Selected work and the thinking behind it",
        "description": "Explore projects, the decisions behind them, and ways to collaborate.",
    },
    "creative": {
        "name": "Work",
        "path": "/work",
        "blocks": ["portfolio_cases", "product_features"],
        "heading": "Selected work and the thinking behind it",
        "description": "Explore projects, the decisions behind them, and ways to collaborate.",
    },
    "events": {
        "name": "Events",
        "path": "/events",
        "blocks": ["event_schedule", "product_catalog"],
        "heading": "Make room for the next gathering",
        "description": "Explore the programme and find the event details that matter to you.",
    },
    "travel": {
        "name": "Itineraries",
        "path": "/itineraries",
        "blocks": ["travel_itinerary", "product_catalog"],
        "heading": "A journey with room to discover",
        "description": "Review the itinerary, places, and practical details before you go.",
    },
    "ecommerce": {
        "name": "Catalog",
        "path": "/catalog",
        "blocks": ["product_catalog", "pricing_options"],
        "heading": "Explore the collection",
        "description": "Browse product details and compare the options available.",
    },
    "electronics": {
        "name": "Products",
        "path": "/products",
        "blocks": ["product_catalog", "product_features"],
        "heading": "Choose the right equipment",
        "description": "Compare specifications and find the product details you need.",
    },
    "automotive": {
        "name": "Inventory",
        "path": "/inventory",
        "blocks": ["product_catalog", "service_booking"],
        "heading": "Explore the available vehicles",
        "description": "Review vehicle details and arrange a conversation or viewing.",
    },
    "travel": {
        "name": "Itineraries",
        "path": "/itineraries",
        "blocks": ["travel_itinerary", "product_catalog"],
        "heading": "A journey with room to discover",
        "description": "Review the itinerary, places, and practical details before you go.",
    },
    "finance": {
        "name": "Services",
        "path": "/services",
        "blocks": ["product_features", "pricing_options"],
        "heading": "Understand the service before deciding",
        "description": "Review how the service works and which options are available.",
    },
    "saas": {
        "name": "Workspace",
        "path": "/workspace",
        "blocks": ["product_features", "pricing_options"],
        "heading": "A workspace for the work at hand",
        "description": "See the product workflow and compare the available plans.",
    },
    "technology": {
        "name": "Platform",
        "path": "/platform",
        "blocks": ["product_features", "faq_answers"],
        "heading": "A closer look at the platform",
        "description": "Explore the capabilities and technical details relevant to your team.",
    },
    "healthcare": {
        "name": "Care",
        "path": "/care",
        "blocks": ["service_booking", "faq_answers"],
        "heading": "Care information in one place",
        "description": "Review available services and find the right way to get in touch.",
    },
    "hospitality": {
        "name": "Visit",
        "path": "/visit",
        "blocks": ["service_booking", "menu_reservations"],
        "heading": "Plan a visit that feels considered",
        "description": "Explore the experience and arrange the details of your visit.",
    },
}

_SECTION_COPY = {
    "product_catalog": ("Product details", "Explore available items and review the details before choosing."),
    "service_booking": ("Arrange a conversation", "Choose a convenient next step to discuss the service."),
    "property_listings": ("Property details", "Review the spaces, locations, and details relevant to your search."),
    "menu_reservations": ("Menu and reservations", "Browse menu information and make a plan for your visit."),
    "course_curriculum": ("Course outline", "See how the material is organized before you begin."),
    "fitness_program": ("Training programs", "Compare training formats and find a routine that suits you."),
    "claims_queue": ("Review queue", "Keep submitted claims and the next review action together."),
    "claims_intake": ("Claim intake", "Collect incident details and supporting documents in a guided flow."),
    "coverage_review": ("Coverage review", "Bring policy information and submitted details into the review."),
    "portfolio_cases": ("Selected work", "Review project context, decisions, and delivered work."),
    "event_schedule": ("Programme", "Explore programme details and plan which sessions to attend."),
    "travel_itinerary": ("Itinerary", "Review places, travel details, and practical information for the journey."),
    "product_features": ("How it works", "Explore the parts of the product that support the requested workflow."),
    "pricing_options": ("Available options", "Compare the available options and choose what fits your needs."),
    "faq_answers": ("Common questions", "Find clear answers about the product and its next steps."),
    "contact_cta": ("Talk through the details", "Share what you are looking for and decide on a useful next step."),
}


def get_layout_catalog() -> Dict[str, Any]:
    """Return layout archetypes, niche blocks, and page-specific block recipes."""
    catalog = get_design_catalog()
    catalog["niche_pages"] = {key: dict(value) for key, value in _NICHE_PAGES.items()}
    catalog["section_copy"] = dict(_SECTION_COPY)
    return catalog


def get_niche_page(niche: str) -> Optional[Dict[str, Any]]:
    recipe = _NICHE_PAGES.get(niche)
    return dict(recipe) if recipe else None


def get_section_copy(block_id: str) -> Dict[str, str]:
    title, description = _SECTION_COPY.get(block_id, ("Details", "Explore the details relevant to your needs."))
    return {"title": title, "description": description}