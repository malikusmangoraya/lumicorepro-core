"""Buyer-facing README renderer for generated / sellable projects."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

REQUIRED_HEADING_GROUPS = (
    ("getting started", "quick start", "quick installation"),
    ("features", "what is included", "highlights"),
    ("license",),
    ("environment", "environment variables", "prerequisites"),
)


def _humanize(value: Any) -> str:
    words = str(value or "").replace("_", " ").replace("-", " ").split()
    return " ".join(w[:1].upper() + w[1:] for w in words) or str(value or "")


def _feature_lines(spec: Dict[str, Any]) -> List[str]:
    raw = list(spec.get("features") or []) + list(spec.get("trending_features") or [])
    out: List[str] = []
    seen = set()
    for item in raw:
        if isinstance(item, dict):
            value = item.get("name") or item.get("title") or item.get("id") or ""
        else:
            value = str(item or "")
        key = value.lower().strip()
        if value and key not in seen:
            seen.add(key)
            out.append(_humanize(value))
    if out:
        return out
    return [
        "Responsive, mobile-first interface with dark mode",
        "Professional branding, navigation, and multi-column footer",
        "International ready: i18n, RTL, and multi-currency display",
        "SEO, PWA, and accessibility (WCAG 2.1 AA) baselines",
        "Secure, validated API (when full-stack) with documented env vars",
    ]


def _tech_rows(spec: Dict[str, Any]) -> List[Tuple[str, str]]:
    stack = spec.get("tech_stack") or {}
    rows: List[Tuple[str, str]] = []
    for layer in ("frontend", "backend", "database"):
        value = stack.get(layer) if isinstance(stack, dict) else None
        if not value:
            value = spec.get(layer)
        if isinstance(value, dict):
            bits = [
                _humanize(value[k])
                for k in ("framework", "bundler", "styling", "engine", "runtime", "auth")
                if value.get(k)
            ]
            label = ", ".join(dict.fromkeys(bits)) or _humanize(layer)
        elif value:
            label = _humanize(value)
        else:
            continue
        rows.append((_humanize(layer), label))
    if rows:
        return rows
    return [
        ("Frontend", "React 19 + Vite + Tailwind CSS"),
        ("Backend", "Node.js + Express"),
        ("Database", "PostgreSQL"),
    ]


def _env_rows(mode: str) -> List[Tuple[str, str, str]]:
    if mode == "static":
        return [
            ("VITE_FORMSPREE_ENDPOINT", "Formspree form URL", "https://formspree.io/f/xxxx"),
            ("VITE_CONTACT_WEBHOOK_URL", "Optional webhook for contact forms", ""),
        ]
    return [
        ("PORT", "API port", "5000"),
        ("DATABASE_URL", "PostgreSQL or MySQL connection string", "postgres://user:pass@localhost:5432/app"),
        ("JWT_SECRET", "Random 64-character secret", "replace_with_a_random_64_character_secret"),
        ("CORS_ORIGIN", "Allowed frontend origin", "http://localhost:5173"),
        ("VITE_API_URL", "Frontend API base URL", "http://localhost:5000"),
        ("REDIS_URL", "Redis for queues (enterprise)", "redis://localhost:6379"),
    ]


def generate_marketplace_readme(
    spec: Dict[str, Any],
    mode: str = "fullstack",
    extra_sections: Optional[str] = None,
) -> str:
    """Render a complete buyer README: details + how to start."""
    raw_name = spec.get("project_name") or spec.get("name") or "Project"
    name = str(raw_name).replace("-", " ").title()
    wtype = _humanize(spec.get("website_type") or spec.get("industry") or "web product")
    description = (
        spec.get("description")
        or spec.get("tagline")
        or spec.get("summary")
        or spec.get("original_prompt")
        or f"Production-ready {wtype} you can deploy and sell on international marketplaces."
    )
    features = _feature_lines(spec)
    tech = _tech_rows(spec)
    env_rows = _env_rows(mode)

    parts: List[str] = [
        f"# {name}",
        "",
        str(description).strip(),
        "",
        f"**Type:** {wtype}  |  **Audience:** agencies, founders, and digital-product buyers  |  **Quality bar:** marketplace / ThemeForest grade",
        "",
        "## Features",
        "",
    ]
    parts.extend(f"- {line}" for line in features)
    parts.extend(
        [
            "",
            "## Tech Stack",
            "",
            "| Layer | Technology |",
            "|-------|------------|",
        ]
    )
    parts.extend(f"| {layer} | {tech_name} |" for layer, tech_name in tech)
    parts.extend(
        [
            "",
            "## Prerequisites",
            "",
            "- Node.js 18+ (20 LTS recommended)",
            "- npm 9+",
        ]
    )
    if mode != "static":
        parts.extend(
            [
                "- PostgreSQL 14+ (or MySQL 8 if you switch dialect)",
                "- Redis 6+ when using background jobs",
            ]
        )
    parts.extend(["", "## Getting Started", ""])

    if mode == "static":
        parts.extend(
            [
                "```bash",
                "cd frontend",
                "cp ../.env.example .env   # or copy frontend/.env.example",
                "npm install",
                "npm run dev               # http://localhost:5173",
                "```",
                "",
                "Production build:",
                "",
                "```bash",
                "cd frontend",
                "npm run build",
                "npm run preview",
                "```",
                "",
                "Deploy: import the repo on **Vercel** or **Netlify** (root directory `frontend`). See copy-paste deploy steps below if this README includes Vercel/Netlify sections.",
            ]
        )
    else:
        parts.extend(
            [
                "```bash",
                "# 1. Backend",
                "cd backend",
                "cp .env.example .env      # set DATABASE_URL and JWT_SECRET",
                "npm install",
                "npm run dev               # http://localhost:5000",
                "",
                "# 2. Frontend (new terminal)",
                "cd frontend",
                "cp .env.example .env      # set VITE_API_URL=http://localhost:5000",
                "npm install",
                "npm run dev               # http://localhost:5173",
                "```",
                "",
                "Optional Docker:",
                "",
                "```bash",
                "docker compose up --build",
                "```",
            ]
        )

    parts.extend(
        [
            "",
            "## Environment Variables",
            "",
            "Copy `.env.example` to `.env`. Never commit `.env`.",
            "",
            "| Variable | Purpose | Example |",
            "|----------|---------|---------|",
        ]
    )
    parts.extend(f"| `{key}` | {purpose} | `{example}` |" for key, purpose, example in env_rows)
    parts.extend(
        [
            "",
            "## Project Structure",
            "",
            "```",
            "├── README.md                 # This file — details and start guide",
            "├── LICENSE.md                # End-user license",
            "├── .env.example              # Safe env template",
            "├── frontend/                 # React 19 + Vite + Tailwind",
            "├── screenshots/              # Marketplace preview images",
        ]
    )
    if mode != "static":
        parts.extend(
            [
                "├── backend/                  # Express API",
                "├── database/                 # SQL schema",
                "├── docker-compose.yml",
                "├── INSTRUCTIONS.md           # Extended install and deploy",
                "└── DEPLOYMENT_CHECKLIST.md",
            ]
        )
    else:
        parts.append("└── vercel.json / netlify.toml")
    parts.extend(
        [
            "```",
            "",
            "## Scripts",
            "",
            "| Command | Where | Action |",
            "|---------|-------|--------|",
            "| `npm run dev` | frontend / backend | Local development |",
            "| `npm run build` | frontend | Production bundle |",
            "| `npm run lint` | frontend | ESLint |",
            "| `npm test` | where present | Unit tests |",
            "",
            "## International",
            "",
            "- UI copy in English; extra locales under `frontend/src/i18n` when generated",
            "- RTL-ready layout tokens",
            "- Currency display via Intl (USD, EUR, GBP, PKR, INR, AED, SAR)",
            "- Privacy / Terms pages and cookie consent for EU buyers",
            "",
            "## Troubleshooting",
            "",
            "- **Blank page / 5173 refused:** run `npm install` inside `frontend`, then `npm run dev`.",
            "- **API CORS / 401:** confirm `CORS_ORIGIN` and `VITE_API_URL` match the running backend.",
            "- **Database errors:** create the database, apply `database/schema.sql`, restart the API.",
            "- **Env not applied:** Vite inlines `VITE_*` at build time — rebuild after changing `.env`.",
            "",
            "## Screenshots",
            "",
            "Place desktop and mobile previews in `screenshots/` before listing on Gumroad, Lemon Squeezy, or ThemeForest.",
            "",
            "## License",
            "",
            "Paid end-user license. You may deploy and customize for client work. You may not resell this source as a competing template without a reseller license. See `LICENSE.md` and `LICENSE-SEAL.md`.",
            "",
        ]
    )
    if extra_sections:
        parts.append(extra_sections.rstrip())
        parts.append("")
    return "\n".join(parts)


def readme_has_required_sections(text: str) -> List[str]:
    """Return names of missing required heading groups."""
    lowered = (text or "").lower()
    missing: List[str] = []
    for group in REQUIRED_HEADING_GROUPS:
        if not any(heading in lowered for heading in group):
            missing.append(group[0])
    return missing


def iter_env_example_paths(root) -> Iterable:
    from pathlib import Path

    p = Path(root)
    for rel in (".env.example", "frontend/.env.example", "backend/.env.example"):
        yield p / rel
