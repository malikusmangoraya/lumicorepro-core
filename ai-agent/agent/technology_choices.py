"""Validate technology choices and provide catalog-grounded generation guidance."""

from typing import Any, Dict, Optional, Tuple

from agent.technology_catalog import load_catalog

CHOICE_GROUPS = {
    "frontend_framework": ("frontend_frameworks", None),
    "admin_platform": ("admin_platforms", None),
    "frontend_host": ("hosting_providers", "frontend_host"),
    "backend_host": ("hosting_providers", ("backend_host", "backend_and_database_host")),
    "database_host": ("hosting_providers", ("database_host", "backend_and_database_host")),
    "source_control_provider": ("source_control_providers", None),
    "testing_tools": ("testing_tools", None),
    "quality_tools": ("quality_tools", None),
    "ci_provider": ("ci_providers", None),
    "authentication_profile": ("authentication_profiles", None),
}
LIST_FIELDS = {"testing_tools", "quality_tools"}
CAPABILITY_STATES = {"catalog_only_not_generated", "generated", "verified"}
PROMPT_ALIASES = {
    "react-vite": ("react", "vite"),
    "nextjs": ("next.js", "nextjs"),
    "sveltekit": ("svelte kit",),
    "tanstack-start": ("tanstack start",),
    "react-router-framework": ("react router",),
    "qwik-city": ("qwik city",),
    "solidstart": ("solid start",),
    "payload": ("payload cms",),
    "github-pages": ("github pages",),
    "cloudflare-pages": ("cloudflare pages",),
    "cloudflare-workers": ("cloudflare workers",),
    "vercel-functions": ("vercel functions",),
    "react-testing-library": ("testing library",),
}


def validate_technology_choices(
    selection: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Validate IDs and return list-valued choices in canonical catalog order."""
    if selection is None:
        return {}
    if not isinstance(selection, dict):
        raise ValueError("technology_choices must be an object.")

    unknown_fields = set(selection) - set(CHOICE_GROUPS)
    if unknown_fields:
        raise ValueError(
            f"Unknown technology_choices field: {sorted(unknown_fields)[0]}."
        )

    catalog = load_catalog()
    normalized = {}
    for field, value in selection.items():
        group, category = CHOICE_GROUPS[field]
        options = catalog[group]
        if category:
            categories = category if isinstance(category, tuple) else (category,)
            options = [option for option in options if option["category"] in categories]
        known_ids = {option["id"] for option in options}
        if field in LIST_FIELDS:
            if not isinstance(value, list):
                raise ValueError(f"technology_choices.{field} must be a list.")
            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(
                    f"technology_choices.{field} must contain non-empty catalog IDs."
                )
            unknown = set(value) - known_ids
            if unknown:
                raise ValueError(
                    f"Unknown technology_choices.{field}: {sorted(unknown)[0]}."
                )
            chosen = set(value)
            normalized[field] = [
                option["id"] for option in options if option["id"] in chosen
            ]
        else:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"technology_choices.{field} must be a non-empty catalog ID."
                )
            if value not in known_ids:
                raise ValueError(f"Unknown technology_choices.{field}: {value}.")
            normalized[field] = value
    return normalized


def _option_by_id(catalog: Dict[str, Any], field: str, option_id: str) -> Dict[str, Any]:
    group, category = CHOICE_GROUPS[field]
    for option in catalog[group]:
        if option["id"] == option_id and (
            category is None
            or option["category"] in (category if isinstance(category, tuple) else (category,))
        ):
            return option
    raise ValueError(f"Unknown technology_choices.{field}: {option_id}.")


def _match_prompt_choice(
    catalog: Dict[str, Any], field: str, prompt: str
) -> Optional[str]:
    group, category = CHOICE_GROUPS[field]
    options = catalog[group]
    if category:
        categories = category if isinstance(category, tuple) else (category,)
        options = [option for option in options if option["category"] in categories]
    matches = []
    for option in options:
        terms = {
            option["id"].replace("-", " "),
            option["label"],
            *PROMPT_ALIASES.get(option["id"], ()),
        }
        if any(term.casefold() in prompt for term in terms if term):
            matches.append(option)
    if field in LIST_FIELDS:
        if matches:
            matched = {option["id"] for option in matches}
            return [
                option["id"] for option in options if option["id"] in matched
            ]
        return None
    if not matches:
        return None
    return max(matches, key=lambda option: len(option["label"]))["id"]


def _relationship_status(
    left: Dict[str, Any], right: Dict[str, Any], left_group: str, right_group: str
) -> Optional[str]:
    matches = []
    for source, target_group, target_id in (
        (left, right_group, right["id"]),
        (right, left_group, left["id"]),
    ):
        for relationship in source.get("compatibility", []):
            if relationship["group"] == target_group and relationship["id"] == target_id:
                matches.append(relationship["status"])
    if not matches:
        return None
    if len(set(matches)) > 1:
        raise ValueError("Technology catalog has conflicting compatibility metadata.")
    return matches[0]


def _framework_host_compatibility(
    catalog: Dict[str, Any], choices: Dict[str, Any], manual_fields: set
) -> Tuple[Optional[str], Optional[str]]:
    framework_id = choices.get("frontend_framework")
    host_id = choices.get("frontend_host")
    if not framework_id or not host_id:
        return None, None
    framework = _option_by_id(catalog, "frontend_framework", framework_id)
    host = _option_by_id(catalog, "frontend_host", host_id)
    status = _relationship_status(
        framework, host, "frontend_frameworks", "hosting_providers"
    )
    if status == "incompatible":
        raise ValueError(
            f"Technology choices '{framework_id}' and '{host_id}' are incompatible."
        )
    if status == "compatible":
        return status, None
    if "frontend_framework" in manual_fields or "frontend_host" in manual_fields:
        return "unverified", (
            f"Compatibility between {framework['label']} and {host['label']} "
            "is unverified; confirm framework adapter and deployment requirements."
        )
    return "unknown", None


def resolve_technology_choices(
    spec: Dict[str, Any],
    selection: Optional[Dict[str, Any]] = None,
    mode: str = "auto",
) -> Dict[str, Any]:
    """Resolve prompt recommendations and manual overrides against catalog metadata."""
    if mode not in {"auto", "manual"}:
        raise ValueError("technology_choices mode must be 'auto' or 'manual'.")
    if not isinstance(spec, dict):
        raise ValueError("Technology choice spec must be an object.")
    normalized = validate_technology_choices(selection)
    catalog = load_catalog()
    prompt = " ".join(
        str(spec.get(key, "")) for key in ("prompt", "description", "project_description")
    ).casefold()

    choices: Dict[str, Any] = {}
    for field in CHOICE_GROUPS:
        match = _match_prompt_choice(catalog, field, prompt)
        if match:
            choices[field] = match
    manual_fields = set(normalized)
    choices.update(normalized)

    warnings = []
    if "frontend_framework" in choices and "frontend_host" in choices:
        status, warning = _framework_host_compatibility(
            catalog, choices, manual_fields
        )
        if status in {"unknown", "unverified"}:
            if status == "unknown":
                choices.pop("frontend_host", None)
            elif warning:
                warnings = [warning]

    resolved_options = []
    for field, value in choices.items():
        group, _ = CHOICE_GROUPS[field]
        selected_ids = value if field in LIST_FIELDS else [value]
        for option_id in selected_ids:
            option = _option_by_id(catalog, field, option_id)
            compatibility_status = "not_applicable"
            if field in {"frontend_framework", "frontend_host"}:
                pair_status, pair_warning = _framework_host_compatibility(
                    catalog, choices, manual_fields
                )
                if pair_status:
                    compatibility_status = pair_status
                if pair_warning and pair_warning not in warnings:
                    warnings.append(pair_warning)
            resolved_options.append(
                {
                    "field": field,
                    "group": group,
                    "id": option["id"],
                    "label": option["label"],
                    "category": option["category"],
                    "capability_status": option.get(
                        "capability_status", "catalog_only_not_generated"
                    ),
                    "compatibility_status": compatibility_status,
                }
            )

    return {
        "mode": mode,
        "choices": choices,
        "resolved_options": resolved_options,
        "warnings": warnings,
    }


def format_technology_guidance(resolved: Dict[str, Any]) -> str:
    """Format safe, catalog-backed choices with consistent implementation caveats."""
    if not isinstance(resolved, dict) or not isinstance(
        resolved.get("resolved_options", []), list
    ):
        raise ValueError("Resolved technology choices are invalid.")

    lines = [
        "Technology selection guidance:",
        "Catalog selection is not implementation: do not claim code, integration,",
        "CI, hosting configuration, or deployment was generated unless the run",
        "actually created and verified that artifact.",
    ]
    for option in resolved.get("resolved_options", []):
        if not isinstance(option, dict) or option.get("capability_status") not in CAPABILITY_STATES:
            raise ValueError("Resolved technology option metadata is invalid.")
        lines.append(
            f"- {option.get('field')}: {option.get('label')} "
            f"[{option['capability_status']}; "
            f"compatibility={option.get('compatibility_status', 'unknown')}]."
        )
    for warning in resolved.get("warnings", []):
        if not isinstance(warning, str):
            raise ValueError("Technology choice warnings must be strings.")
        lines.append(f"Warning: {warning}")

    lines.extend(
        [
            "Security and engineering defaults:",
            "- Hash passwords with a current, deliberately configured password-hashing algorithm; "
            "enforce authorization server-side with least privilege and RBAC/ABAC as required.",
            "- Validate inputs at trusted boundaries; use parameterized database access; protect "
            "against CSRF and XSS; rate-limit sensitive routes; validate upload type and size; "
            "redact secrets; surface errors without exposing stack traces.",
            "- For cookies, set HttpOnly, Secure, and an intentional SameSite policy; "
            "SameSite=None requires Secure. Set narrowly scoped Path/Domain and deliberate "
            "Max-Age/Expires.",
            "- Sessions are server-side state; rotate IDs after authentication and privilege "
            "changes, expire and revoke sessions, invalidate on logout, and use a persistent "
            "production store (not Express MemoryStore). Express session APIs include "
            "regenerate, save, and destroy; PHP references include session_start, $_SESSION, "
            "session_regenerate_id, session_unset, session_destroy, setcookie, session_name, "
            "and session_status.",
            "- OAuth 2.0 delegated authorization is distinct from OIDC authentication. Prefer "
            "authorization code with PKCE; validate exact redirect_uri, state, issuer, audience, "
            "signature, expiry, and scopes. OIDC ID tokens require nonce validation; handle "
            "access/refresh-token storage, rotation, expiry, and revocation safely.",
            "- Credentialed cross-origin cookies require an exact CORS origin (never *), "
            "credentials enabled on both sides, a compatible SameSite policy, and CSRF defenses.",
            "- Consider transactional data changes, queues, caching, search, webhooks, email, "
            "real-time behavior, observability, localization/timezones/currency, accessibility, "
            "SEO, backup/restore, architecture, and scalability against the product requirements.",
            "- Verify current provider documentation, availability, pricing, quotas, and terms "
            "before deployment; catalog entries do not establish current vendor capabilities.",
        ]
    )
    return "\n".join(lines)
