"""Tests for the three-stage UI component graph.

Every test here is hermetic: no provider call, no network, no LangGraph. The
provider is always a stub and the registry is a fixture, so the suite is
deterministic on a machine with no API keys - which is the whole reason the
graph has a deterministic fallback path.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.ui_component_agent import (  # noqa: E402
    LANGGRAPH_AVAILABLE,
    NODE_SEQUENCE,
    emit_react_component,
    fallback_component,
    inject_ui_context,
    load_registry,
    render_layout_base,
    run_graph,
    strip_code_fence,
    validate_component,
)
from agent.ui_component_agent.context import ALLOWED_TOKENS, infer_categories  # noqa: E402
from agent.ui_component_agent.emit import (  # noqa: E402
    humanize_component_name,
    region_label,
)
from agent.ui_component_agent.layout import resolve_regions  # noqa: E402

REGISTRY = [
    {
        "name": "LoginForm",
        "category": "auth",
        "tags": ["login", "email", "password"],
        "description": "Login form with validation.",
        "file_path": "src/components/auth/LoginForm.jsx",
        "dependencies": ["lucide-react"],
        "features": ["email_login", "remember_me"],
    },
    {
        "name": "ProductCard",
        "category": "ecommerce",
        "tags": ["product", "price", "cart"],
        "description": "Product tile.",
        "file_path": "src/components/ecommerce/ProductCard.jsx",
        "dependencies": [],
        "features": ["add_to_cart"],
    },
    {
        "name": "RevenueCard",
        "category": "dashboard",
        "tags": ["kpi", "revenue", "metric"],
        "description": "KPI tile.",
        "file_path": "src/components/dashboard/RevenueCard.jsx",
        "dependencies": [],
        "features": ["sparkline"],
    },
]


class StubProvider:
    """Provider stub. Returns whatever `response` is set to."""

    def __init__(self, response="", raises=None):
        self.response = response
        self.raises = raises
        self.prompts = []

    def generate_code(self, prompt, *args, **kwargs):
        self.prompts.append(prompt)
        if self.raises:
            raise RuntimeError(self.raises)
        return self.response


class ExplodingProvider:
    def generate_code(self, prompt, *args, **kwargs):
        raise RuntimeError("provider exploded")


GOOD_JSX = """import React from 'react';

export default function PricingTable() {
  return (
    <main className="bg-[var(--t-bg)] text-[var(--t-text)]">
      <h1>Pricing</h1>
      <p>Three tiers.</p>
    </main>
  );
}
"""


# --------------------------------------------------------------------------
# Stage 1: UI library context
# --------------------------------------------------------------------------


class TestInjectUiContext:
    def test_infers_category_from_request(self):
        ctx = inject_ui_context("build me a login page", registry_path=None)
        assert "auth" in ctx["categories"]

    def test_explicit_categories_are_kept(self):
        cats = infer_categories("anything", explicit=["fintech"])
        assert "fintech" in cats

    def test_selects_matching_components_first(self, tmp_path):
        path = tmp_path / "components.json"
        path.write_text(__import__("json").dumps(REGISTRY), encoding="utf-8")
        ctx = inject_ui_context("ecommerce product listing page", registry_path=str(path))
        assert ctx["components"]
        assert ctx["components"][0]["name"] == "ProductCard"
        assert "ProductCard" in ctx["component_names"]

    def test_prompt_contains_library_contract(self, tmp_path):
        path = tmp_path / "components.json"
        path.write_text(__import__("json").dumps(REGISTRY), encoding="utf-8")
        ctx = inject_ui_context("login page", registry_path=str(path))
        assert "UI LIBRARY CONTEXT" in ctx["prompt"]
        assert "LoginForm" in ctx["prompt"]
        assert "--t-brand" in ctx["prompt"]

    def test_missing_registry_degrades_gracefully(self):
        ctx = inject_ui_context("login page", registry_path="/nope/missing.json")
        assert ctx["registry_size"] == 0
        assert ctx["components"] == []
        assert "none matched" in ctx["prompt"]

    def test_corrupt_registry_degrades_gracefully(self, tmp_path):
        path = tmp_path / "components.json"
        path.write_text("{not json", encoding="utf-8")
        assert load_registry(str(path)) == []

    def test_limit_is_respected(self, tmp_path):
        path = tmp_path / "components.json"
        path.write_text(__import__("json").dumps(REGISTRY), encoding="utf-8")
        ctx = inject_ui_context("login product cart kpi", registry_path=str(path), limit=2)
        assert len(ctx["components"]) <= 2

    def test_real_repo_registry_loads(self):
        """The shipped registry must be readable, or stage 1 is theatre."""
        ctx = inject_ui_context("a login page with email and password")
        assert ctx["registry_size"] > 0
        assert "LoginForm" in ctx["component_names"]


# --------------------------------------------------------------------------
# Stage 2: layout base
# --------------------------------------------------------------------------


class TestRenderLayoutBase:
    def test_explicit_layout_is_respected(self):
        out = render_layout_base(layout="dashboard")
        assert out["regions"][:2] == ["header", "nav"]
        assert "aside" in out["regions"]

    def test_auto_infers_from_request(self):
        assert "aside" in render_layout_base(layout="auto", request="admin analytics kpi")["regions"]
        assert "header" in render_layout_base(layout="auto", request="contact form")["regions"]

    def test_auto_falls_back_to_page(self):
        assert render_layout_base(layout="auto", request="zzz nonsense")["regions"][0] == "header"

    def test_wireframe_covers_every_region(self):
        out = render_layout_base(layout="landing")
        for region in out["regions"]:
            assert region in out["wireframe"]

    def test_region_spec_has_a11y_and_job(self):
        out = render_layout_base(layout="landing")
        for spec in out["region_spec"]:
            assert spec["a11y"]
            assert spec["job"]
            assert spec["weight"] > 0

    def test_max_regions_caps_output(self):
        assert len(render_layout_base(layout="landing", max_regions=3)["regions"]) == 3

    def test_guidance_forbids_raw_hex(self):
        assert "no raw hex" in render_layout_base(layout="page")["guidance"]

    def test_resolve_regions_never_returns_empty(self):
        assert resolve_regions("nonsense-layout", request="") != []


# --------------------------------------------------------------------------
# Stage 3: emit + validation
# --------------------------------------------------------------------------


class TestValidation:
    def test_good_jsx_passes(self):
        assert validate_component(GOOD_JSX, ALLOWED_TOKENS) == []

    def test_empty_output_rejected(self):
        assert validate_component("", ALLOWED_TOKENS) == ["empty output"]

    def test_missing_default_export_rejected(self):
        assert "missing `export default`" in validate_component("<main><h1>Hi</h1></main>")

    def test_raw_hex_rejected(self):
        code = GOOD_JSX.replace("var(--t-bg)", "#ff0000")
        assert any("raw hex" in p for p in validate_component(code, ALLOWED_TOKENS))

    def test_undeclared_token_rejected(self):
        code = GOOD_JSX.replace("var(--t-bg)", "var(--t-mystery)")
        assert any("undeclared token" in p for p in validate_component(code, ALLOWED_TOKENS))

    def test_two_h1_rejected(self):
        code = GOOD_JSX.replace("</main>", "<h1>Second</h1></main>")
        assert "more than one h1" in validate_component(code, ALLOWED_TOKENS)

    def test_missing_h1_rejected(self):
        code = "export default function X(){return <main><h2>Sub</h2></main>}"
        assert any("missing h1" in p for p in validate_component(code, ALLOWED_TOKENS))

    def test_unresolvable_alias_import_rejected(self):
        code = "import X from '@/components/ui/Button';\n" + GOOD_JSX
        assert any("will not resolve" in p for p in validate_component(code, ALLOWED_TOKENS))

    def test_unclosed_fence_rejected(self):
        assert any("fence" in p for p in validate_component(GOOD_JSX + "\n```", ALLOWED_TOKENS))

    def test_oversized_component_rejected(self):
        # Single line on purpose: a line cap alone would let this through.
        code = "export default function X(){return <main><h1>a</h1>" + "<p>x</p>" * 3000 + "</main>}"
        assert any("exceeds" in p for p in validate_component(code, ALLOWED_TOKENS))

    def test_many_lines_rejected(self):
        code = "export default function X(){\nreturn <main><h1>a</h1>\n" + "  <p>x</p>\n" * 500 + "</main>}"
        assert any("exceeds" in p for p in validate_component(code, ALLOWED_TOKENS))

    def test_long_but_legal_component_not_flagged_for_size(self):
        """Guard against a size false positive on a legitimately long component."""
        assert not any("exceeds" in p for p in validate_component(GOOD_JSX, ALLOWED_TOKENS))


class TestStripFence:
    def test_extracts_fenced_jsx(self):
        assert strip_code_fence("```jsx\nconst a = 1;\n```") == "const a = 1;"

    def test_passes_through_bare_code(self):
        assert strip_code_fence("const a = 1;") == "const a = 1;"

    def test_handles_empty(self):
        assert strip_code_fence("") == ""


class TestEmit:
    def test_provider_output_is_used_when_valid(self):
        provider = StubProvider(response=GOOD_JSX)
        region_spec = render_layout_base(layout="page")["region_spec"]
        out = emit_react_component("ctx", "lay", region_spec=region_spec, provider=provider)
        assert out["source"] == "provider"
        assert out["valid"] is True
        assert out["code"] == GOOD_JSX.strip()

    def test_fenced_provider_output_is_cleaned(self):
        provider = StubProvider(response="Here you go:\n```jsx\n%s\n```" % GOOD_JSX)
        out = emit_react_component("ctx", "lay", region_spec=[], provider=provider)
        assert out["source"] == "provider"
        assert "```" not in out["code"]

    def test_invalid_provider_output_falls_back(self):
        provider = StubProvider(response="I cannot help with that.")
        region_spec = render_layout_base(layout="page")["region_spec"]
        out = emit_react_component("ctx", "lay", region_spec=region_spec, provider=provider)
        assert out["source"] == "fallback"
        assert out["valid"] is True
        assert out["problems"]

    def test_provider_exception_falls_back(self):
        region_spec = render_layout_base(layout="page")["region_spec"]
        out = emit_react_component("ctx", "lay", region_spec=region_spec, provider=ExplodingProvider())
        assert out["source"] == "fallback"
        assert "provider exploded" in out["provider_error"]

    def test_no_provider_uses_fallback(self):
        out = emit_react_component("ctx", "lay", component_name="Card", region_spec=[])
        assert out["source"] == "fallback"
        assert "function Card()" in out["code"]

    def test_prompt_includes_context_and_layout(self):
        provider = StubProvider(response=GOOD_JSX)
        emit_react_component("MY-CONTEXT", "MY-LAYOUT", provider=provider)
        assert "MY-CONTEXT" in provider.prompts[0]
        assert "MY-LAYOUT" in provider.prompts[0]


class TestFallbackComponent:
    def test_exports_default(self):
        assert "export default" in fallback_component("Thing", [])

    def test_hero_carries_the_single_h1(self):
        spec = render_layout_base(layout="page")["region_spec"]
        code = fallback_component("Page", spec)
        assert code.count("<h1") == 1

    def test_layout_without_hero_still_has_one_h1(self):
        for layout in ("form", "single", "dashboard"):
            spec = render_layout_base(layout=layout)["region_spec"]
            code = fallback_component("Page", spec)
            assert code.count("<h1") == 1, layout
            assert validate_component(code, ALLOWED_TOKENS) == [], layout

    def test_every_preset_layout_produces_valid_component(self):
        from agent.ui_component_agent import LAYOUT_PRESETS

        for name in LAYOUT_PRESETS:
            spec = render_layout_base(layout=name)["region_spec"]
            code = fallback_component("Page", spec)
            assert validate_component(code, ALLOWED_TOKENS) == [], name

    def test_uses_landmark_elements(self):
        spec = render_layout_base(layout="landing")["region_spec"]
        code = fallback_component("Page", spec)
        for tag in ("<header", "<nav", "<main", "<aside", "<footer"):
            assert tag in code

    def test_never_emits_raw_hex(self):
        spec = render_layout_base(layout="page")["region_spec"]
        assert validate_component(fallback_component("Page", spec), ALLOWED_TOKENS) == []

    def test_sanitises_component_name(self):
        code = fallback_component("My Component!!", [])
        assert "function MyComponent" in code

    def test_empty_name_falls_back_to_default(self):
        assert "GeneratedComponent" in fallback_component("!!!", [])

    def test_duplicate_regions_collapse(self):
        spec = [
            {"name": "content", "job": "a", "weight": 10},
            {"name": "content", "job": "b", "weight": 10},
        ]
        assert fallback_component("X", spec).count("<main") == 1


# --------------------------------------------------------------------------
# Graph
# --------------------------------------------------------------------------


class TestRunGraph:
    def test_node_order_is_the_documented_pipeline(self):
        assert NODE_SEQUENCE == ["inject_ui_context", "render_layout_base", "emit_react_component"]

    def test_offline_run_is_valid(self):
        out = run_graph("a login page", component_name="LoginPage", provider_name="none")
        assert out["ok"] is True
        assert out["source"] == "fallback"
        assert out["code"]

    def test_trace_records_every_node(self):
        out = run_graph("pricing page", provider_name="none")
        assert [t["node"] for t in out["trace"]] == NODE_SEQUENCE

    def test_engine_reported(self):
        out = run_graph("a page", provider_name="none")
        assert out["engine"] == ("langgraph" if LANGGRAPH_AVAILABLE else "sequential")

    def test_context_and_layout_reach_the_result(self):
        out = run_graph("a login page", component_name="LoginPage", provider_name="none")
        assert "auth" in out["context"]["categories"]
        assert out["context"]["components"]
        assert out["layout"]["regions"]

    def test_stub_provider_is_used_end_to_end(self):
        provider = StubProvider(response=GOOD_JSX)
        out = run_graph("a pricing page", component_name="PricingTable", provider=provider)
        assert out["source"] == "provider"
        assert "PricingTable" in out["code"]

    def test_result_is_json_serialisable(self):
        import json

        json.dumps(run_graph("a page", provider_name="none"))


class TestHumanCopyInFallback:
    """The fallback emitter must never render the layout brief's `job` notes.

    Regression: the deterministic path used to put the internal design note
    ("identity + primary action", "the substance") straight into the <h1>/<h2>,
    so every offline-generated component shipped placeholder copy.
    """

    def test_humanize_component_name(self):
        assert humanize_component_name("PricingTable") == "Pricing Table"
        assert humanize_component_name("pricing_table") == "Pricing table"
        assert humanize_component_name("pricing-table") == "Pricing table"
        assert humanize_component_name("") == "Component"
        assert humanize_component_name(None) == "Component"

    def test_region_label_is_human(self):
        assert region_label("hero", 1) == "Overview"
        assert region_label("footer", 2) == "Footer"
        assert region_label("nav", 3) == "Sections"
        assert region_label("whatever", 4) == "Section 4"

    def test_fallback_never_contains_layout_brief_job_text(self):
        spec = render_layout_base(layout="page")["region_spec"]
        code = fallback_component("PricingTable", spec)
        for region in spec:
            job = str(region.get("job", "")).strip()
            if job:
                assert job not in code, f"layout brief leaked into copy: {job!r}"

    def test_fallback_h1_is_the_component_title(self):
        for layout in ("single", "section", "page", "dashboard", "form", "landing"):
            spec = render_layout_base(layout=layout)["region_spec"]
            code = fallback_component("OrderHistoryPanel", spec)
            assert "<h1" in code, layout
            assert "Order History Panel" in code, layout

    def test_fallback_still_validates(self):
        spec = render_layout_base(layout="page")["region_spec"]
        code = fallback_component("PricingTable", spec)
        assert validate_component(code) == []
