from typing import Dict, Any, List
from utils.logger import agent_logger

class TechStackSelector:
    """Phase 3: Optimal technology stack selection based on requirements and scale."""

    STACK_PROFILES = {
        "ecommerce": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "icons": "lucide-react"},
            "backend": {"runtime": "node", "framework": "express", "auth": "jwt+bcrypt"},
            "database": {"engine": "postgresql", "orm": "raw-sql", "cache": "optional-redis"},
            "payments": "stripe",
            "deployment": ["vercel", "railway", "render"],
        },
        "saas": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "charts": "recharts"},
            "backend": {"runtime": "node", "framework": "express", "auth": "jwt+bcrypt"},
            "database": {"engine": "postgresql", "orm": "raw-sql", "cache": "redis-recommended"},
            "payments": "stripe-subscriptions",
            "deployment": ["vercel", "aws", "gcp"],
        },
        "dashboard": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "charts": "recharts"},
            "backend": {"runtime": "node", "framework": "express", "auth": "jwt+bcrypt"},
            "database": {"engine": "postgresql", "orm": "raw-sql"},
            "deployment": ["vercel", "aws"],
        },
        "business": {
            "frontend": {"framework": "react", "bundler": "vite", "styling": "tailwindcss", "animation": "css-transitions"},
            "backend": {"runtime": "node", "framework": "express", "auth": "optional-jwt"},
            "database": {"engine": "postgresql", "orm": "raw-sql"},
            "deployment": ["vercel", "netlify"],
        },
    }

    SCALE_OVERRIDES = {
        "high_traffic": {"cache": "redis-required", "cdn": "cloudflare", "rate_limit": "strict"},
        "enterprise": {"monitoring": "datadog", "logging": "structured-json", "audit": "required"},
    }

    def select(
        self,
        spec: Dict[str, Any],
        selected_backend: Dict[str, Any],
        selected_schemas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Select and document optimal tech stack for the project."""
        agent_logger.info("Phase 3: Selecting optimal technology stack...")

        website_type = spec.get("website_type", "ecommerce")
        profile = self.STACK_PROFILES.get(website_type, self.STACK_PROFILES["ecommerce"])

        features = spec.get("features", [])
        scale_hints = []
        if "payments" in features or "checkout" in features:
            scale_hints.append("payment_processing")
        if "admin" in features or "dashboard" in features:
            scale_hints.append("enterprise")

        stack = {
            "frontend": profile["frontend"],
            "backend": {
                **profile["backend"],
                "selected_module": selected_backend.get("name") if selected_backend else "master-express-backend",
                "module_path": selected_backend.get("file_path") if selected_backend else None,
            },
            "database": {
                **profile["database"],
                "schemas": [s.get("name") for s in selected_schemas],
                "schema_count": len(selected_schemas),
            },
            "payments": profile.get("payments"),
            "deployment_targets": profile.get("deployment", []),
            "scale_considerations": scale_hints,
            "rationale": self._build_rationale(spec, profile),
        }

        agent_logger.info(f"Tech stack selected: React+Vite frontend, {stack['backend']['selected_module']} backend.")
        return stack

    def _build_rationale(self, spec: Dict[str, Any], profile: Dict[str, Any]) -> str:
        wtype = spec.get("website_type", "project")
        return (
            f"React + Vite chosen for {wtype} due to component reuse from the shared UI library, "
            f"fast HMR, and {profile['database']['engine']} compatibility for structured data."
        )
