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


@pytest.mark.parametrize('prompt', ['Build an interactive 3D hero', 'WebGL experience',
                                   'three.js landing page'])
def test_explicit_3d_prompt_enables_scene_without_changing_defaults(prompt):
    result = resolve_generation_contract({'prompt': prompt})
    assert result.pop('scene') == {'archetype': 'floating_crystal'}
    assert result == resolve_generation_contract({})


def test_scene_request_normalizes_and_preserves_trusted_asset_input():
    import agent.generation_contract as contract

    source = {'archetype': ' PRODUCT_VIEWER ', 'model_path': 'D:/owner/model.glb'}
    assert hasattr(contract, 'resolve_scene_request')
    expected = {'archetype': 'product_viewer', 'model_path': 'D:/owner/model.glb'}
    assert contract.resolve_scene_request(scene=source) == expected
    assert resolve_generation_contract({'scene': source})['scene'] == expected
    assert source['archetype'] == ' PRODUCT_VIEWER '
    assert contract.resolve_scene_request('ordinary portfolio') is None


@pytest.mark.parametrize('prompt', [
    'A 3D hero for our SaaS product', '3D product launch page',
    'a WebGL experience for the product team',
])
def test_product_mention_alone_does_not_demand_a_supplied_model(prompt):
    result = resolve_generation_contract({'prompt': prompt})
    assert result['scene'] == {'archetype': 'floating_crystal'}


@pytest.mark.parametrize('spec', [
    {'prompt': '3D product showroom'}, {'prompt': 'model-viewer'},
    {'scene': {'archetype': 'product_viewer'}},
    {'scene': {'archetype': 'holographic_bento'}},
    {'scene': {'archetype': 'secret-unsupported-name'}},
    {'scene': {'archetype': 'floating_crystal', 'model_path': '/private/secret.glb'}},
    {'scene': {}}, {'scene': False}, {'scene': 'floating_crystal'},
])
def test_invalid_or_unavailable_scene_requests_fail_safely(spec):
    with pytest.raises(ValueError) as error:
        resolve_generation_contract(spec)
    assert 'secret' not in str(error.value)
    assert 'scene' in str(error.value).lower() or 'model' in str(error.value).lower()


@pytest.mark.parametrize("prompt,expected", [
    ("Build a records website", None),
    ("Build a landing page for records", None),
    ("Build a web app for records", {"web": "web_app", "pwa": False, "mobile": None}),
    ("Build an internal app dashboard", {"web": "web_app", "pwa": False, "mobile": None}),
    ("Build a records app", {"web": "none", "pwa": False,
        "mobile": {"platforms": ["android"], "verification": "apk_emulator"}}),
    ("Build a mobile app for records", {"web": "none", "pwa": False,
        "mobile": {"platforms": ["android"], "verification": "apk_emulator"}}),
    ("Build a records website and app", {"web": "website", "pwa": False,
        "mobile": {"platforms": ["android"], "verification": "apk_emulator"}}),
    ("Build a web app and a mobile app", {"web": "web_app", "pwa": False,
        "mobile": {"platforms": ["android"], "verification": "apk_emulator"}}),
    ("Build a records web app with PWA", {"web": "web_app", "pwa": True, "mobile": None}),
])
def test_prompt_decides_exactly_the_requested_surfaces(prompt, expected):
    contract = resolve_generation_contract({"prompt": prompt})
    assert contract.get("app") == expected


@pytest.mark.parametrize("prompt,expected_web", [
    ("Build a records website for web and mobile", "website"),
    ("Build a dashboard and mobile app", "web_app"),
])
def test_both_surface_phrases_never_drop_a_surface(prompt, expected_web):
    app = resolve_generation_contract({"prompt": prompt})["app"]
    assert app["web"] == expected_web
    assert app["mobile"] == {"platforms": ["android"], "verification": "apk_emulator"}


def test_bare_both_cue_requests_website_and_mobile():
    contract = resolve_generation_contract({"prompt": "Build both for records"})
    assert contract["app"] == {
        "web": "website",
        "pwa": False,
        "mobile": {"platforms": ["android"], "verification": "apk_emulator"},
    }


def test_pwa_without_a_web_surface_is_invalid():
    with pytest.raises(ValueError):
        resolve_generation_contract({"app": {"web": "none", "pwa": True}})


def test_unknown_surfaces_are_rejected_without_echoing_input():
    with pytest.raises(ValueError) as error:
        resolve_generation_contract({"app": {"web": "secret-value"}})
    assert "secret-value" not in str(error.value)


def test_non_boolean_pwa_is_rejected_without_echoing_input():
    with pytest.raises(ValueError) as error:
        resolve_generation_contract({"app": {"web": "website", "pwa": "secret-value"}})
    assert "secret-value" not in str(error.value)


def test_default_contract_has_no_app_block():
    assert "app" not in resolve_generation_contract({})
