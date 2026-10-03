"""UI Component Agent - a three-stage graph that outputs a React component.

    FastAPI / LangGraph Agent
        -> injects UI library context
        -> renders a layout base
        -> outputs a React component

LangGraph drives the graph when it is installed. When it is not, the identical
node sequence runs through a plain topological executor, so the pipeline has no
hard dependency on a graph library and stays usable offline and in CI.

MIT licensed and dependency-light on purpose: the only required package is
`requests` (already present for the provider layer).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from agent.ui_component_agent.context import (
    ALLOWED_TOKENS,
    inject_ui_context,
    load_registry,
)
from agent.ui_component_agent.emit import (
    emit_react_component,
    fallback_component,
    strip_code_fence,
    validate_component,
)
from agent.ui_component_agent.layout import (
    LAYOUT_PRESETS,
    REGION_CATALOGUE,
    render_layout_base,
    resolve_regions,
)

try:  # optional
    from langgraph.graph import END, START, StateGraph  # type: ignore

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when langgraph is absent
    LANGGRAPH_AVAILABLE = False


def _resolve_provider(provider_name: Optional[str] = None) -> Any:
    """Get a provider instance, or None when none is usable."""
    if os_env_offline():
        return None
    try:
        from config.providers import instantiate_provider, validate_provider_key

        name = provider_name
        if not name:
            from agent.ai_routing import get_router

            name = get_router().active_provider_name()
        if not name or not validate_provider_key(name, require_key=False):
            return None
        return instantiate_provider(name)
    except Exception:
        return None


def os_env_offline() -> bool:
    import os

    return os.getenv("AI_OFFLINE", "").strip().lower() in {"1", "true", "yes", "on"}


def _node_inject(state: Dict[str, Any]) -> Dict[str, Any]:
    ctx = inject_ui_context(
        request=state["request"],
        categories=state.get("categories"),
        limit=state.get("limit", 8),
        registry_path=state.get("registry_path"),
    )
    return {**state, "context": ctx}


def _node_layout(state: Dict[str, Any]) -> Dict[str, Any]:
    layout = render_layout_base(
        layout=state.get("layout", "auto"),
        request=state["request"],
        component_name=state.get("component_name", "GeneratedComponent"),
    )
    return {**state, "layout_base": layout}


def _node_emit(state: Dict[str, Any]) -> Dict[str, Any]:
    ctx = state["context"]
    layout = state["layout_base"]
    result = emit_react_component(
        context_prompt=ctx["prompt"],
        layout_prompt=layout["guidance"],
        component_name=state.get("component_name", "GeneratedComponent"),
        region_spec=layout["region_spec"],
        allowed_tokens=ctx.get("tokens", ALLOWED_TOKENS),
        provider=state.get("provider"),
    )
    return {**state, "result": result}


NODE_SEQUENCE: List[str] = ["inject_ui_context", "render_layout_base", "emit_react_component"]


def run_graph(
    request: str,
    component_name: str = "GeneratedComponent",
    layout: str = "auto",
    categories: Optional[List[str]] = None,
    provider_name: Optional[str] = None,
    provider: Any = None,
    limit: int = 8,
    registry_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the three stages and return the component plus a stage trace."""
    if provider is None and provider_name != "none":
        provider = _resolve_provider(provider_name)

    state: Dict[str, Any] = {
        "request": request,
        "component_name": component_name,
        "layout": layout,
        "categories": categories,
        "limit": limit,
        "registry_path": registry_path,
        "provider": provider,
    }

    engine = "langgraph" if LANGGRAPH_AVAILABLE else "sequential"
    trace: List[Dict[str, Any]] = []

    if LANGGRAPH_AVAILABLE:  # pragma: no cover - requires the optional dep
        graph = StateGraph(dict)
        graph.add_node("inject_ui_context", _node_inject)
        graph.add_node("render_layout_base", _node_layout)
        graph.add_node("emit_react_component", _node_emit)
        graph.add_edge(START, "inject_ui_context")
        graph.add_edge("inject_ui_context", "render_layout_base")
        graph.add_edge("render_layout_base", "emit_react_component")
        graph.add_edge("emit_react_component", END)
        final = graph.compile().invoke(state)
    else:
        for node, fn in (
            ("inject_ui_context", _node_inject),
            ("render_layout_base", _node_layout),
            ("emit_react_component", _node_emit),
        ):
            before = set(state)
            state = fn(state)
            trace.append({"node": node, "added": sorted(set(state) - before)})

    ctx = state["context"]
    layout_base = state["layout_base"]
    result = state["result"]
    return {
        "ok": bool(result.get("valid")),
        "engine": engine,
        "component_name": component_name,
        "code": result.get("code", ""),
        "source": result.get("source", "fallback"),
        "problems": result.get("problems", []),
        "provider_error": result.get("provider_error", ""),
        "context": {
            "categories": ctx["categories"],
            "components": ctx["component_names"],
            "registry_size": ctx["registry_size"],
        },
        "layout": {
            "regions": layout_base["regions"],
            "wireframe": layout_base["wireframe"],
        },
        "trace": trace,
        "nodes": NODE_SEQUENCE,
    }


__all__ = [
    "LANGGRAPH_AVAILABLE",
    "NODE_SEQUENCE",
    "run_graph",
    "inject_ui_context",
    "render_layout_base",
    "emit_react_component",
    "validate_component",
    "strip_code_fence",
    "fallback_component",
    "load_registry",
    "LAYOUT_PRESETS",
    "REGION_CATALOGUE",
    "ALLOWED_TOKENS",
]
