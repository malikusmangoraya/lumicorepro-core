import sys
from pathlib import Path

import pytest

AI_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

from agent.generation_contract import resolve_generation_contract


def test_default_contract_is_postgresql_authenticated_fullstack():
    contract = resolve_generation_contract({"website_type": "portfolio"})

    assert contract == {
        "version": 1,
        "layout_mode": "enterprise",
        "database": "postgresql",
        "auth": True,
        "features": ["jwt_auth", "users", "contact"],
        "requirements": [],
    }


def test_explicit_static_contract_has_no_server_features():
    contract = resolve_generation_contract({"deployment_mode": "static-only"})

    assert contract["layout_mode"] == "client-static"
    assert contract["database"] is None
    assert contract["auth"] is False
    assert contract["features"] == []


def test_required_payment_feature_is_preserved_without_defaulting_other_payments():
    contract = resolve_generation_contract({"features": ["stripe_payments"]})

    assert "stripe_payments" in contract["features"]
    assert contract["requirements"] == ["stripe_payments"]
    assert "paypal_payments" not in contract["features"]


def test_invalid_features_are_normalized_without_crashing():
    contract = resolve_generation_contract({"features": 42})

    assert contract["features"] == ["jwt_auth", "users", "contact"]
    assert contract["requirements"] == []


def test_planner_carries_json_serializable_contract():
    import json

    from agent.planner import GenerationPlanner

    plan = GenerationPlanner().create_plan(
        spec={"project_name": "contract-check", "website_type": "business"},
        selected_template={},
        selected_components=[],
        selected_assets={},
        selected_backend={},
        selected_schemas=[],
    )

    assert plan["generation_contract"]["database"] == "postgresql"
    assert plan["generation_contract"]["auth"] is True
    assert json.loads(json.dumps(plan["generation_contract"]))["version"] == 1
