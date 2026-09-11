"""Component Registry Rigidity — prop-contract verification for the local component set.

Pillar 2 enforcement layer. Builds a canonical index over the monorepo's LOCAL
component library (`src/components/**/*.jsx`) keyed by absolute path alias
(`@/components/<rel>`), extracts prop signatures (variant/size + defaults) and
verifies generated projects:

  1. Unknown-component imports            -> error (breaks the clone build).
  2. Prop-contract drift (unknown prop     -> warning (flexible, hard-linted by
     used on a registered component)          the variant/size subset).
  3. Generic markup where a local          -> warning (drives the model toward
     component exists (<button>/<img>          the component library).

`component_contract_snippet()` is the machine-readable contract injected into
generation/heal instructions so outputs map to the local library, not generic
markup.
"""
import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import PROJECT_ROOT
from utils.logger import agent_logger

COMPONENTS_ROOT = PROJECT_ROOT / "src" / "components"

_PROPS_PATTERN = re.compile(
    r"(?s)\bconst\s+\w+\s*=\s*(?:React\.)?(?:forwardRef|memo|lazy)\s*\(\s*\(\s*\{([\s\S]*?)\}(?:\s*,\s*\w+)?\s*\)\s*=>"
)
_ARROW_PROPS_PATTERN = re.compile(
    r"(?s)\bconst\s+\w+\s*=\s*\(\s*\{([\s\S]*?)\}\s*\)\s*=>"
)
_FUNC_PROPS_PATTERN = re.compile(r"(?s)\bfunction\s+\w+\s*\(\s*\{([\s\S]*?)\}\s*\)")
_DEFAULT_EXPORT_PATTERN = re.compile(r"(?m)\bexport\s+default\s+(?:function\s+|class\s+)?(\w+)")
_VARIANT_MAP_PATTERN = re.compile(r"(?s)\bconst\s+variants\s*=\s*\{([^}]*)\}")
_SIZE_MAP_PATTERN = re.compile(r"(?s)\bconst\s+sizes\s*=\s*\{([^}]*)\}")
_ALIAS_IMPORT_PATTERN = re.compile(r"""(?:from|require)\s*\(?\s*['"](@/components/[^'"]+)['"]""")
_JSX_TAG_PATTERN = re.compile(r"<([A-Z][A-Za-z0-9_]*\b)")
_GENERIC_MARKUP_PATTERNS = {
    "button": ("Button", "ButtonMotion"),
    "img": ("LazyImage",),
    "select": ("Select",),
    "textarea": ("Textarea",),
}


def _clean_props(raw: str) -> List[str]:
    props: List[str] = []
    for segment in raw.split(","):
        segment = segment.strip()
        if not segment or segment == "..." or segment.startswith("..."):
            continue
        token = segment.split("=")[0].split(":")[0].strip()
        token = token.strip()
        if token and re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", token):
            props.append(token)
    return list(dict.fromkeys(props))


def _extract_props(text: str, name: str) -> List[str]:
    """Extract destructured prop names for the exact component signature.

    Matches are anchored to the component's own name so inner helper components
    (e.g. ``NavItem`` inside ``GlassNavbar``) never contaminate the contract.
    """
    named_patterns = (
        re.compile(
            rf"(?s)\bconst\s+{re.escape(name)}\s*=\s*(?:React\.)?(?:forwardRef|memo|lazy)\s*"
            rf"\(\s*\(\s*\{{([\s\S]*?)\}}(?:\s*,\s*\w+)?\s*\)\s*=>"
        ),
        re.compile(rf"(?s)\bfunction\s+{re.escape(name)}\s*\(\s*\{{([\s\S]*?)\}}\s*\)"),
        re.compile(rf"(?s)\bconst\s+{re.escape(name)}\s*=\s*\(\s*\{{([\s\S]*?)\}}\s*\)\s*=>"),
    )
    for pattern in named_patterns:
        match = pattern.search(text)
        if match and match.group(1).strip():
            return _clean_props(match.group(1))

    # Prop-less signatures (hooks-based, class, or no-arg) must not inherit
    # props from unrelated inner components/functions further down the file.
    no_arg_patterns = (
        re.compile(rf"(?s)\bfunction\s+{re.escape(name)}\s*\(\)"),
        re.compile(rf"(?s)\bconst\s+{re.escape(name)}\s*=\s*\(\)\s*=>"),
        re.compile(rf"(?s)\bclass\s+{re.escape(name)}\s+extends"),
        re.compile(rf"(?s)\bconst\s+{re.escape(name)}\s*=\s*(?:React\.)?(?:forwardRef|memo|lazy)\s*\(\s*\(\)"),
    )
    if any(p.search(text) for p in no_arg_patterns):
        return []

    # Fallback: full-file scan (anonymous export-default + memo(({...}) =>)).
    candidates: List[str] = []
    for pattern in (_PROPS_PATTERN, _ARROW_PROPS_PATTERN, _FUNC_PROPS_PATTERN):
        for match in pattern.finditer(text):
            candidate = match.group(1)
            if candidate.strip():
                candidates.append(candidate)
    if not candidates:
        return []
    prefer_spread = [c for c in candidates if "..." in c]
    pool = prefer_spread or candidates
    return _clean_props(max(pool, key=lambda c: c.count(",")))


def _map_keys_simple(text: str, pattern: re.Pattern) -> List[str]:
    match = pattern.search(text)
    if not match:
        return []
    keys = []
    for line in match.group(1).split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        key = stripped.split(":")[0].strip()
        if key and re.match(r"^[A-Za-z0-9_]+$", key):
            keys.append(key)
    return keys


def _component_props(name: str, text: str) -> Dict[str, Any]:
    e = _extract_props(text, name)
    return {
        "name": name,
        "props": e,
        "has_variant": "variant" in e,
        "has_size": "size" in e,
        "variant_values": _map_keys_simple(text, _VARIANT_MAP_PATTERN),
        "size_values": _map_keys_simple(text, _SIZE_MAP_PATTERN),
    }


class ComponentRegistry:
    """Canonical index over the local component library."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or COMPONENTS_ROOT)
        self._index: Dict[str, Dict[str, Any]] = {}
        self._by_alias: Dict[str, Dict[str, Any]] = {}
        self._build()

    def _build(self) -> None:
        if not self.root.is_dir():
            agent_logger.warning(f"Component library not found at {self.root}")
            return
        for jsx in sorted(self.root.rglob("*.jsx")):
            rel = jsx.relative_to(self.root).as_posix()
            parts = rel.split("/")
            category = parts[0] if len(parts) > 1 else "common"
            text = jsx.read_text(encoding="utf-8", errors="replace")
            export = _DEFAULT_EXPORT_PATTERN.search(text)
            name = export.group(1) if export else jsx.stem
            contract = _component_props(name, text)
            contract.update(
                {
                    "relative_path": rel,
                    "alias": f"@/components/{rel}",
                    "category": category,
                    "file": str(jsx),
                }
            )
            self._index[name] = contract
            self._by_alias[contract["alias"]] = contract
        agent_logger.debug(f"Component registry indexed {len(self._index)} local components")

    # ── Lookup ─────────────────────────────────────────────────────────────
    def names(self) -> List[str]:
        return sorted(self._index)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self._index.get(name)

    def by_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        return self._by_alias.get(alias)

    def count(self) -> int:
        return len(self._index)

    def categories(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for contract in self._index.values():
            counts[contract["category"]] = counts.get(contract["category"], 0) + 1
        return counts

    # ── Prompt contract snippet (Pillar 2 rigid mapping) ───────────────────
    def contract_snippet(self, max_lines: int = 120) -> str:
        lines = [
            "COMPONENT CONTRACT (absolute alias paths; use local components, "
            "NEVER generic markup when one exists):",
        ]
        for name in self.names():
            contract = self._index[name]
            props = ", ".join(contract["props"]) if contract["props"] else "(n/a)"
            if contract["has_variant"]:
                props += " | variant=" + "|".join(contract["variant_values"] or ["primary", "secondary", "outline", "ghost"])
            if contract["has_size"]:
                props += " | size=" + "|".join(contract["size_values"] or ["xs", "sm", "md", "lg", "xl"])
            lines.append(f"- {contract['alias']} # props: {props}")
        return "\n".join(lines[:max_lines])

    # ── Generated-project verification ─────────────────────────────────────
    def verify_generated_components(self, project_dir: str) -> Dict[str, Any]:
        """Cross-check a generated frontend tree against the local contract index."""
        errors: List[str] = []
        warnings: List[str] = []
        unknown_imports: List[str] = []
        prop_contract_warnings: List[str] = []
        generic_markup_warnings: List[str] = []
        checked_files = 0

        frontend = Path(project_dir).resolve() / "frontend" / "src"
        if not frontend.is_dir():
            return {
                "checked_files": 0,
                "errors": ["frontend/src missing — cannot verify component contracts"],
                "warnings": [],
                "unknown_imports": [],
                "prop_contract_warnings": [],
                "generic_markup_warnings": [],
            }

        for root, _, files in os.walk(frontend):
            for fname in files:
                if not fname.endswith((".jsx", ".js")):
                    continue
                checked_files += 1
                fpath = os.path.join(root, fname)
                text = Path(fpath).read_text(encoding="utf-8", errors="replace")
                rel_file = os.path.relpath(fpath, frontend)

                for alias in _ALIAS_IMPORT_PATTERN.findall(text):
                    if not self.by_alias(alias):
                        unknown_imports.append(f"{rel_file} -> {alias}")

                # Prop-contract drift on registered components used in JSX.
                for tag in _JSX_TAG_PATTERN.findall(text):
                    contract = self.get(tag)
                    if not contract or not contract["props"]:
                        continue
                    for match in re.finditer(
                        re.escape(tag) + r"\s+(_?[a-zA-Z][A-Za-z0-9_-]*)\s*=", text
                    ):
                        prop = match.group(1)
                        if prop not in contract["props"] and prop not in ("key", "ref", "data-testid"):
                            prop_contract_warnings.append(
                                f"{rel_file}: <{tag} prop='{prop}' not declared in contract"
                            )

                # Generic markup rule — flag raw tags when a local component exists.
                for tag, candidate_names in _GENERIC_MARKUP_PATTERNS.items():
                    if re.search(rf"<{tag}\b", text) and any(self.get(c) for c in candidate_names):
                        generic_markup_warnings.append(
                            f"{rel_file}: raw <{tag}> while local components exist "
                            f"({', '.join(f'@{c}' for c in candidate_names)})"
                        )

        for entry in unknown_imports:
            errors.append(entry)
        for entry in prop_contract_warnings:
            warnings.append(entry)
        for entry in generic_markup_warnings:
            warnings.append(entry)

        return {
            "checked_files": checked_files,
            "errors": list(dict.fromkeys(errors)),
            "warnings": list(dict.fromkeys(warnings)),
            "unknown_imports": list(dict.fromkeys(unknown_imports)),
            "prop_contract_warnings": list(dict.fromkeys(prop_contract_warnings)),
            "generic_markup_warnings": list(dict.fromkeys(generic_markup_warnings)),
            "registered_components": len(self._index),
        }

    def to_index_json(self) -> List[Dict[str, Any]]:
        return [self._index[name] for name in self.names()]


_REGISTRY: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """Process-wide singleton registry (read-only after first build)."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ComponentRegistry()
    return _REGISTRY


def component_contract_snippet() -> str:
    return get_component_registry().contract_snippet()


def build_registry_index(output_path: Optional[str] = None) -> Dict[str, Any]:
    """Materialize the canonical index as a JSON artifact (absolute-alias map)."""
    registry = get_component_registry()
    payload = {
        "generated_by": "ai-agent.agent.component_registry",
        "count": registry.count(),
        "categories": registry.categories(),
        "components": registry.to_index_json(),
    }
    target = Path(output_path) if output_path else PROJECT_ROOT / "registry" / "component-contracts.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    agent_logger.info(f"Component contract registry written: {target} ({registry.count()} components)")
    return payload