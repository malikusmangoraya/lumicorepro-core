"""Contract tests for the FastAPI server's hardening and its component endpoint.

Everything here was implemented by hand and previously only verified with live
HTTP probes, which means a refactor could quietly reopen `/docs` in production,
drop HSTS, or start relaying raw exception text to callers. These tests pin the
contracts instead.

`IS_PRODUCTION`, `EXPOSE_API_DOCS`, the `app` object, `TrustedHostMiddleware` and
`_AGENT_API_KEY` are all resolved at import time, so a runtime mode cannot be
exercised without re-importing `server`. The `reloaded_server` fixture does that
under a controlled environment and restores the module afterwards; reload costs
~0.2s, re-opens the existing (idempotent) sqlite stores, and re-registers routes
on a fresh app, so it is safe to repeat.

No test here touches the network, a real provider, or a listening socket: the UI
component graph is always forced down its deterministic offline path, and the
account store is a throwaway sqlite file under `tmp_path`.
"""

import contextlib
import importlib
import ipaddress
import os
import re
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as server_mod  # noqa: E402
from database.accounts_store import AccountStore  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.websockets import WebSocketDisconnect  # noqa: E402


# Only these keys change module-level state (app construction, security headers,
# TrustedHost, auth, rate limits). They are snapshotted and restored around
# every reload so no test can leak configuration into the next one.
_ENV_KEYS = (
    "APP_ENV",
    "NODE_ENV",
    "EXPOSE_API_DOCS",
    "AGENT_API_KEY",
    "ALLOWED_HOSTS",
    "RATE_LIMIT_REQUESTS",
    "AI_OFFLINE",
)

# A body the ui-component endpoint accepts, pinned to the offline path.
VALID_UI_BODY = {
    "request": "pricing page with 3 tiers",
    "component_name": "PricingTable",
    "layout": "page",
    "provider": "none",
}

# The internal region `job` notes from the layout catalogue. They are design
# metadata, and a regression once rendered "identity + primary action" as the
# visible header of the header region.
LEAKED_REGION_JOB = "identity + primary action"

# Words that must never appear in user-visible heading text.
INTERNAL_WORDS = ("job", "region", "layout", "primary action", "identity")

_HEADING_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.S | re.I)
_H1_RE = re.compile(r"<h1\b", re.I)

# A plausible internal failure: the kind of message that used to be relayed
# straight to the caller, with a path, a SQL fragment and a secret in it.
INTERNAL_SECRET = "hunter2"
INTERNAL_DETAIL = (
    "sqlite3.OperationalError: no such table: users | "
    "SELECT api_key FROM users WHERE email = 'x@example.com' | "
    "D:\\repo\\ai-agent\\database\\accounts_store.py line 126 | " + INTERNAL_SECRET
)

_ENVELOPE_KEYS = {"success", "status", "message", "data", "timestamp"}
_UI_DATA_KEYS = {
    "ok",
    "engine",
    "component_name",
    "code",
    "source",
    "problems",
    "provider_error",
    "context",
    "layout",
    "trace",
    "nodes",
}

# Text that must never survive into generated, shippable code.
DEBUG_MARKERS = ("data-testid", "console.log", "debugger", "TODO", "FIXME", "pytest")


@pytest.fixture
def reloaded_server():
    """Yield `server` re-imported under a controlled environment.

    Usage: ``with reloaded_server(APP_ENV="production") as srv:``. Any env key
    passed as ``None`` is removed, so "unset" is testable. The original
    environment and the original module state are restored on exit.
    """

    @contextlib.contextmanager
    def _reload(**env):
        saved = {key: os.environ.get(key) for key in _ENV_KEYS}
        # Belt and braces: the request body also pins `provider="none"`, so the
        # graph stays deterministic even if a key leaks in from the ambient env.
        env = {"AI_OFFLINE": "1", **env}
        try:
            for key, value in env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = str(value)
            yield importlib.reload(server_mod)
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(server_mod)

    return _reload


@pytest.fixture
def dev_server(reloaded_server, tmp_path):
    """Development-mode server with a throwaway account store and no rate limit.

    Auth is open in development by design, so the store is swapped rather than
    keyed. The limiter is raised to a non-binding value because `/api/accounts/*`
    counts per client IP for the whole process and would otherwise make these
    tests order-dependent.
    """
    with reloaded_server(AGENT_API_KEY="", RATE_LIMIT_REQUESTS="100000") as srv:
        original = srv._accounts
        srv._accounts = AccountStore(path=str(tmp_path / "platform.db"))
        try:
            yield srv, TestClient(srv.app)
        finally:
            srv._accounts = original


def _registered_user(client):
    """Create an account through the real endpoint and return its API key."""
    response = client.post(
        "/api/accounts/register",
        json={"email": "leak-probe@example.com", "display_name": "Leak Probe"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["api_key"]


def _assert_no_leak(payload, extra=()):
    """Nothing from the internal failure may appear anywhere in the payload."""
    blob = payload if isinstance(payload, str) else repr(payload)
    for secret in (INTERNAL_DETAIL, INTERNAL_SECRET, "Traceback", "accounts_store.py", "SELECT"):
        assert secret not in blob, "internal detail leaked: %r" % secret
    for secret in extra:
        assert secret not in blob, "internal detail leaked: %r" % secret


def test_client_completion_result_includes_workflow_roles_without_phase_log():
    report = {
        "project_name": "shop",
        "selected_resources": {
            "template": "storefront",
            "components": ["Header", "Catalog"],
            "backend": "Express",
            "trending_features": ["search"],
        },
        "quality_gates": {"overall_score": 91},
        "workflow_agents": {"qa_deployment": {"status": "ready"}},
        "phase_results": {"large": "not sent to the browser"},
    }

    result = server_mod._client_completion_result(report)

    assert result["project_name"] == "shop"
    assert result["workflow_agents"] == report["workflow_agents"]
    assert result["selected_resources"]["components"] == ["Header", "Catalog"]
    assert "phase_results" not in result


# --------------------------------------------------------------------------
# A. API docs gating
# --------------------------------------------------------------------------


class TestApiDocsGating:
    """`/docs` publishes the schema of every endpoint, so it is dev-only by default."""

    def test_production_disables_every_docs_route(self, reloaded_server):
        with reloaded_server(APP_ENV="production") as srv:
            assert srv.IS_PRODUCTION is True
            assert srv.EXPOSE_API_DOCS is False
            assert srv.app.docs_url is None
            assert srv.app.redoc_url is None
            assert srv.app.openapi_url is None
            client = TestClient(srv.app)
            for path in ("/docs", "/redoc", "/openapi.json"):
                assert client.get(path).status_code == 404, path

    def test_production_with_expose_api_docs_serves_docs(self, reloaded_server):
        with reloaded_server(APP_ENV="production", EXPOSE_API_DOCS="true") as srv:
            assert srv.IS_PRODUCTION is True
            assert srv.EXPOSE_API_DOCS is True
            client = TestClient(srv.app)
            assert client.get("/docs").status_code == 200
            assert client.get("/openapi.json").status_code == 200

    def test_production_docs_flag_is_case_insensitive(self, reloaded_server):
        with reloaded_server(APP_ENV="production", EXPOSE_API_DOCS="True") as srv:
            assert srv.EXPOSE_API_DOCS is True
            assert TestClient(srv.app).get("/docs").status_code == 200

    def test_development_serves_docs_and_openapi(self, reloaded_server):
        with reloaded_server(APP_ENV="development") as srv:
            assert srv.IS_PRODUCTION is False
            assert srv.EXPOSE_API_DOCS is True
            client = TestClient(srv.app)
            assert client.get("/docs").status_code == 200
            assert client.get("/openapi.json").status_code == 200

    def test_node_env_production_also_hides_docs(self, reloaded_server):
        with reloaded_server(APP_ENV=None, NODE_ENV="production") as srv:
            assert srv.IS_PRODUCTION is True
            assert TestClient(srv.app).get("/docs").status_code == 404

    @pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "Yes", "ON"])
    def test_truthy_spellings_all_enable_docs(self, reloaded_server, value):
        # AI_OFFLINE in agent/ui_component_agent already accepted 1|true|yes|on;
        # EXPOSE_API_DOCS only accepted the literal "true", so an operator who
        # wrote EXPOSE_API_DOCS=1 got no docs and no warning.
        with reloaded_server(APP_ENV="production", EXPOSE_API_DOCS=value) as srv:
            assert srv.EXPOSE_API_DOCS is True
            assert TestClient(srv.app).get("/docs").status_code == 200

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "maybe", "2"])
    def test_falsy_or_unrelated_values_do_not_enable_docs(self, reloaded_server, value):
        with reloaded_server(APP_ENV="production", EXPOSE_API_DOCS=value) as srv:
            assert srv.EXPOSE_API_DOCS is False
            assert TestClient(srv.app).get("/docs").status_code == 404


# --------------------------------------------------------------------------
# B. Production API-key auth (fail-secure)
# --------------------------------------------------------------------------

PROTECTED_PATHS = ("/api/runs", "/api/v1/ui-component")


class TestProductionApiKeyAuth:
    """An unset key in production must close the door, not swing it wide open."""

    @pytest.mark.parametrize("path", PROTECTED_PATHS)
    def test_missing_key_in_production_returns_503(self, reloaded_server, path):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY=None) as srv:
            assert srv._AGENT_API_KEY == ""
            client = TestClient(srv.app)
            if path == "/api/runs":
                response = client.get(path)
            else:
                response = client.post(path, json=VALID_UI_BODY)
            assert response.status_code == 503
            assert "not configured" in response.json()["detail"]

    def test_empty_key_in_production_is_treated_as_unset(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="   ") as srv:
            assert srv._AGENT_API_KEY == ""
            response = TestClient(srv.app).post("/api/v1/ui-component", json=VALID_UI_BODY)
            assert response.status_code == 503

    def test_production_503_does_not_serve_the_endpoint(self, reloaded_server):
        """The 503 must come from the guard, not from a failed handler run."""
        with reloaded_server(APP_ENV="production", AGENT_API_KEY=None) as srv:
            client = TestClient(srv.app)
            response = client.post("/api/v1/ui-component", json=VALID_UI_BODY)
            assert response.status_code == 503
            assert "code" not in response.json()
            assert "component_name" not in response.text

    def test_public_health_stays_reachable_in_production(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY=None) as srv:
            assert TestClient(srv.app).get("/health").status_code == 200

    def test_missing_key_header_is_rejected_when_key_is_set(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="s3cret") as srv:
            assert srv._AGENT_API_KEY == "s3cret"
            assert TestClient(srv.app).post("/api/v1/ui-component", json=VALID_UI_BODY).status_code == 401

    def test_wrong_key_is_rejected(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="s3cret") as srv:
            client = TestClient(srv.app)
            response = client.post(
                "/api/v1/ui-component", json=VALID_UI_BODY, headers={"X-API-KEY": "wrong"}
            )
            assert response.status_code == 401
            assert "code" not in response.json()

    def test_correct_key_is_accepted(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="s3cret") as srv:
            client = TestClient(srv.app)
            response = client.post(
                "/api/v1/ui-component", json=VALID_UI_BODY, headers={"X-API-KEY": "s3cret"}
            )
            assert response.status_code == 200, response.text
            assert response.json()["success"] is True

    def test_development_needs_no_key(self, reloaded_server):
        with reloaded_server(APP_ENV="development", AGENT_API_KEY=None) as srv:
            assert srv._AGENT_API_KEY == ""
            response = TestClient(srv.app).post("/api/v1/ui-component", json=VALID_UI_BODY)
            assert response.status_code == 200, response.text

    def test_key_set_in_development_is_still_enforced(self, reloaded_server):
        """Auth is optional in dev, not disabled."""
        with reloaded_server(APP_ENV="development", AGENT_API_KEY="s3cret") as srv:
            client = TestClient(srv.app)
            assert client.post("/api/v1/ui-component", json=VALID_UI_BODY).status_code == 401
            ok = client.post(
                "/api/v1/ui-component", json=VALID_UI_BODY, headers={"X-API-KEY": "s3cret"}
            )
            assert ok.status_code == 200


# --------------------------------------------------------------------------
# C. Security response headers
# --------------------------------------------------------------------------

REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "cross-origin-opener-policy": "same-origin",
}
HSTS = "strict-transport-security"


class TestSecurityHeaders:
    def test_health_sets_every_hardening_header(self, reloaded_server):
        with reloaded_server(APP_ENV="development") as srv:
            headers = TestClient(srv.app).get("/health").headers
            for name, value in REQUIRED_HEADERS.items():
                assert headers[name] == value, name

    def test_production_adds_hsts(self, reloaded_server):
        with reloaded_server(APP_ENV="production") as srv:
            headers = TestClient(srv.app).get("/health").headers
            assert HSTS in headers
            assert "max-age=" in headers[HSTS]
            for name, value in REQUIRED_HEADERS.items():
                assert headers[name] == value, name

    def test_development_omits_hsts(self, reloaded_server):
        with reloaded_server(APP_ENV="development") as srv:
            assert HSTS not in TestClient(srv.app).get("/health").headers

    def test_hsts_is_production_only_not_flag_dependent(self, reloaded_server):
        """`EXPOSE_API_DOCS` must not accidentally drive the header branch."""
        with reloaded_server(APP_ENV="production", EXPOSE_API_DOCS="true") as srv:
            assert HSTS in TestClient(srv.app).get("/docs").headers

    def test_headers_survive_a_401_from_a_protected_route(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="s3cret") as srv:
            response = TestClient(srv.app).post("/api/v1/ui-component", json=VALID_UI_BODY)
            assert response.status_code == 401
            for name, value in REQUIRED_HEADERS.items():
                assert response.headers[name] == value, name
            assert HSTS in response.headers

    def test_headers_survive_a_404(self, reloaded_server):
        with reloaded_server(APP_ENV="development") as srv:
            response = TestClient(srv.app).get("/definitely-not-a-route")
            assert response.status_code == 404
            for name, value in REQUIRED_HEADERS.items():
                assert response.headers[name] == value, name


# --------------------------------------------------------------------------
# D. TrustedHost
# --------------------------------------------------------------------------


class TestTrustedHost:
    def test_disallowed_host_is_rejected(self, reloaded_server):
        with reloaded_server(ALLOWED_HOSTS="localhost,127.0.0.1") as srv:
            assert srv._ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
            response = TestClient(srv.app).get("/health", headers={"Host": "evil.example.com"})
            assert response.status_code == 400

    def test_allowed_host_is_served(self, reloaded_server):
        with reloaded_server(ALLOWED_HOSTS="localhost,127.0.0.1") as srv:
            client = TestClient(srv.app)
            assert client.get("/health", headers={"Host": "localhost"}).status_code == 200
            assert client.get("/health", headers={"Host": "127.0.0.1"}).status_code == 200

    def test_wildcard_pattern_is_honoured(self, reloaded_server):
        with reloaded_server(ALLOWED_HOSTS="*.lumicore.app") as srv:
            client = TestClient(srv.app)
            assert client.get("/health", headers={"Host": "api.lumicore.app"}).status_code == 200
            assert client.get("/health", headers={"Host": "api.evil.app"}).status_code == 400

    def test_disabled_when_allowed_hosts_is_unset(self, reloaded_server):
        with reloaded_server(ALLOWED_HOSTS=None) as srv:
            assert srv._ALLOWED_HOSTS == []
            response = TestClient(srv.app).get("/health", headers={"Host": "anything.example.com"})
            assert response.status_code == 200


# --------------------------------------------------------------------------
# E. No internal detail leakage
# --------------------------------------------------------------------------


def _explode(*args, **kwargs):
    raise RuntimeError(INTERNAL_DETAIL)


class TestNoInternalDetailLeakage:
    def test_internal_error_helper_is_a_generic_500(self):
        exc = server_mod._internal_error(RuntimeError(INTERNAL_DETAIL), context="probe")
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 500
        assert exc.detail == "Internal server error"
        _assert_no_leak(exc.detail)

    def test_internal_error_helper_logs_the_real_cause(self, monkeypatch):
        recorded = []
        monkeypatch.setattr(
            server_mod.agent_logger,
            "exception",
            lambda msg, *a, **k: recorded.append(msg % a if a else msg),
            raising=False,
        )
        server_mod._internal_error(RuntimeError(INTERNAL_DETAIL), context="probe")
        assert recorded, "the real cause must still reach the server log"
        assert "probe" in recorded[0]
        assert INTERNAL_DETAIL in recorded[0]

    def test_provider_listing_failure_returns_generic_500(self, dev_server, monkeypatch):
        srv, client = dev_server
        monkeypatch.setattr("config.providers.describe_providers", _explode)
        response = client.get("/api/providers")
        assert response.status_code == 500
        _assert_no_leak(response.text)

    def test_ui_component_graph_failure_returns_generic_500(self, dev_server, monkeypatch):
        srv, client = dev_server
        monkeypatch.setattr("agent.ui_component_agent.run_graph", _explode)
        response = client.post("/api/v1/ui-component", json=VALID_UI_BODY)
        assert response.status_code == 500
        _assert_no_leak(response.text, extra=["no such table", "OperationalError"])
        assert "Internal server error" in response.text

    def test_duplicate_email_surfaces_the_store_message(self, dev_server):
        srv, client = dev_server
        assert _registered_user(client)
        response = client.post("/api/accounts/register", json={"email": "leak-probe@example.com"})
        assert response.status_code == 409
        assert response.json()["detail"] == "An account with that email already exists"

    def test_unknown_user_surfaces_the_store_message(self, dev_server, monkeypatch):
        """Deliberate UX: the store's ValueError text is a 409, not a 500."""
        srv, client = dev_server
        key = _registered_user(client)
        monkeypatch.setattr(srv._accounts, "get_user", lambda user_id: None, raising=False)
        response = client.post(
            "/api/accounts/projects",
            json={"project_name": "Acme", "website_type": "saas"},
            headers={"X-API-KEY": key},
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Unknown user"

    def test_non_positive_topup_surfaces_the_store_message(self, dev_server):
        srv, client = dev_server
        key = _registered_user(client)
        response = client.post(
            "/api/accounts/credits/topup", json={"amount": -5}, headers={"X-API-KEY": key}
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Amount must be positive"

    def test_blank_deployment_name_surfaces_the_store_message(self, dev_server):
        srv, client = dev_server
        key = _registered_user(client)
        response = client.post(
            "/api/accounts/deployments", json={"project_name": "   "}, headers={"X-API-KEY": key}
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "project_name is required"


# --------------------------------------------------------------------------
# F. POST /api/v1/ui-component
# --------------------------------------------------------------------------


@pytest.fixture
def generated(dev_server):
    """One successful offline generation, reused by the contract assertions."""
    srv, client = dev_server
    response = client.post("/api/v1/ui-component", json=VALID_UI_BODY)
    assert response.status_code == 200, response.text
    return response.json()


class TestUiComponentEndpoint:
    def test_response_envelope_matches_the_documented_shape(self, generated):
        assert set(generated) == _ENVELOPE_KEYS
        assert generated["success"] is True
        assert generated["status"] == "completed"
        assert generated["message"] == "React component generated"
        assert datetime.fromisoformat(generated["timestamp"])
        assert set(generated["data"]) == _UI_DATA_KEYS

    def test_generation_used_the_offline_path(self, generated):
        """Proof no provider was called: the deterministic fallback is the source."""
        assert generated["data"]["source"] == "fallback"
        assert generated["data"]["provider_error"] == ""
        assert generated["data"]["ok"] is True

    def test_problems_is_empty_on_success(self, generated):
        assert generated["data"]["problems"] == []

    def test_component_name_echoes_the_request(self, generated):
        """Regression: the response used to always carry the fallback name."""
        assert generated["data"]["component_name"] == "PricingTable"
        assert "PricingTable" in generated["data"]["code"]

    def test_page_has_exactly_one_h1(self, generated):
        code = generated["data"]["code"]
        assert _H1_RE.search(code)
        assert len(_H1_RE.findall(code)) == 1

    def test_h1_text_is_the_humanised_component_name(self, generated):
        code = generated["data"]["code"]
        headings = _HEADING_RE.findall(code)
        h1s = [text.strip() for text in headings if text]
        assert "Pricing Table" in h1s

    def test_visible_headings_hide_internal_layout_notes(self, generated):
        code = generated["data"]["code"]
        headings = [text.strip() for text in _HEADING_RE.findall(code)]
        assert headings
        for heading in headings:
            lowered = heading.lower()
            for word in INTERNAL_WORDS:
                assert word not in lowered, "internal note %r rendered as heading %r" % (word, heading)

    def test_region_job_note_never_reaches_the_code(self, generated):
        blob = generated["data"]["code"]
        assert LEAKED_REGION_JOB not in blob
        for word in ("identity + primary action", "wayfinding", "the substance"):
            assert word not in blob

    def test_non_hero_layout_still_has_one_humanised_h1(self, dev_server):
        """A dashboard has no hero, so the h1 is promoted - and must stay human."""
        srv, client = dev_server
        response = client.post(
            "/api/v1/ui-component",
            json={**VALID_UI_BODY, "layout": "dashboard", "component_name": "RevenueBoard"},
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["layout"]["regions"] == ["header", "nav", "content", "aside"]
        code = data["code"]
        assert len(_H1_RE.findall(code)) == 1
        headings = [text.strip() for text in _HEADING_RE.findall(code)]
        assert "Revenue Board" in headings
        for heading in headings:
            for word in INTERNAL_WORDS:
                assert word not in heading.lower(), heading

    def test_code_carries_no_debug_markers(self, generated):
        code = generated["data"]["code"]
        for marker in DEBUG_MARKERS:
            assert marker not in code, marker

    def test_code_uses_design_tokens_not_raw_hex(self, generated):
        assert "var(--t-" in generated["data"]["code"]
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", generated["data"]["code"])

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({}, id="missing-request"),
            pytest.param({"request": None}, id="null-request"),
            pytest.param({"request": "ab"}, id="below-min-length"),
            pytest.param({"request": "x" * 2001}, id="oversized-request"),
            pytest.param({"request": "pricing page", "limit": "many"}, id="limit-wrong-type"),
            pytest.param({"request": "pricing page", "limit": 0}, id="limit-below-min"),
            pytest.param({"request": "pricing page", "limit": 31}, id="limit-above-max"),
            pytest.param({"request": "pricing page", "categories": "auth"}, id="categories-not-a-list"),
            pytest.param({"request": "pricing page", "component_name": 7}, id="name-wrong-type"),
            pytest.param({"request": "pricing page", "layout": ["page"]}, id="layout-wrong-type"),
        ],
    )
    def test_malformed_body_is_4xx_not_500(self, dev_server, body):
        srv, client = dev_server
        response = client.post("/api/v1/ui-component", json=body)
        assert response.status_code == 422, response.text
        assert response.status_code < 500
        _assert_no_leak(response.text)

    def test_oversized_body_is_rejected_before_any_work(self, dev_server, monkeypatch):
        srv, client = dev_server
        called = []
        monkeypatch.setattr(
            "agent.ui_component_agent.run_graph", lambda **kw: called.append(kw) or {"ok": True}
        )
        response = client.post("/api/v1/ui-component", json={"request": "x" * 5000})
        assert response.status_code == 422
        assert called == []


# ---------------------------------------------------------------------------
# WebSocket handshake auth
# ---------------------------------------------------------------------------
# The event stream at /ws/generate/{run_id} used a hand-rolled key check that
# only ran `if _AGENT_API_KEY:`, so a production server started WITHOUT a key
# refused every HTTP endpoint with 503 but still accepted the WebSocket fully
# unauthenticated -- HTTP failed closed, the socket failed open. Both paths now
# share `_api_key_status`, which is what these tests pin.

RUN_ID = "ws-auth-probe-run"


class TestWebSocketAuth:
    def test_development_allows_connection_without_key(self, reloaded_server):
        with reloaded_server(APP_ENV="development", AGENT_API_KEY=None) as srv:
            with TestClient(srv.app).websocket_connect(f"/ws/generate/{RUN_ID}") as ws:
                # No run with this id exists, so the server answers with a
                # run-scoped error rather than refusing the handshake.
                assert ws.receive_json()["type"] == "error"

    def test_production_without_configured_key_refuses_handshake(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY=None) as srv:
            with pytest.raises(WebSocketDisconnect) as exc:
                with TestClient(srv.app).websocket_connect(f"/ws/generate/{RUN_ID}"):
                    pass
            assert exc.value.code == 1008

    def test_production_rejects_wrong_key(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="s" * 48) as srv:
            with pytest.raises(WebSocketDisconnect) as exc:
                with TestClient(srv.app).websocket_connect(
                    f"/ws/generate/{RUN_ID}", headers={"x-api-key": "wrong"}
                ):
                    pass
            assert exc.value.code == 1008

    def test_production_rejects_absent_key_header(self, reloaded_server):
        with reloaded_server(APP_ENV="production", AGENT_API_KEY="s" * 48) as srv:
            with pytest.raises(WebSocketDisconnect) as exc:
                with TestClient(srv.app).websocket_connect(f"/ws/generate/{RUN_ID}"):
                    pass
            assert exc.value.code == 1008

    def test_http_and_websocket_agree_when_key_unset_in_production(self, reloaded_server):
        """The two transports must fail the same way on a production misconfig."""
        with reloaded_server(APP_ENV="production", AGENT_API_KEY=None) as srv:
            client = TestClient(srv.app)
            assert client.get("/api/runs").status_code == 503
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect(f"/ws/generate/{RUN_ID}"):
                    pass
            assert exc.value.code == 1008


# --------------------------------------------------------------------------
# Design intelligence endpoints
# --------------------------------------------------------------------------


def _public_browser_dns(monkeypatch):
    """Resolve browser-test URLs to documentation/example public IPv4."""
    monkeypatch.setattr(
        server_mod,
        "_resolve_browser_host_ips",
        lambda host: [ipaddress.ip_address("93.184.215.14")],
    )


class TestDesignEndpoints:
    """The screenshot/browser routes must stay wired to the intelligence layer."""

    def test_screenshot_to_code_builds_a_plan_from_inputs(self, dev_server, monkeypatch):
        srv, client = dev_server
        seen = {}

        def fake_spec(sources, business_type=""):
            seen["sources"] = sources
            seen["business_type"] = business_type
            return {"status": "analyzed", "sections": ["hero", "pricing"]}

        plan_inputs = {
            "palette": {"primary": "#123456"},
            "design_tokens": {"heading_font": "Inter"},
            "reference_sections": ["hero", "pricing"],
            "reference_intelligence": {"measured": True},
        }
        monkeypatch.setattr(
            "agent.intelligence.screenshot_to_code.screenshot_to_design_spec_multi",
            fake_spec,
        )
        monkeypatch.setattr(
            "agent.intelligence.screenshot_to_code.to_plan_inputs",
            lambda spec: plan_inputs,
        )
        monkeypatch.setattr(
            "agent.intelligence.design_planner.create_design_plan",
            lambda **kwargs: {"plan": True, "received": kwargs},
        )

        response = client.post(
            "/api/screenshot-to-code",
            json={"sources": ["hero.png"], "business_type": "saas"},
        )

        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert seen == {"sources": ["hero.png"], "business_type": "saas"}
        assert payload["spec"]["status"] == "analyzed"
        assert payload["plan"]["received"]["reference_sections"] == ["hero", "pricing"]
        assert payload["plan"]["received"]["reference_intelligence"] == {"measured": True}

    def test_screenshot_to_code_rejects_an_empty_source_list(self, dev_server):
        srv, client = dev_server
        response = client.post("/api/screenshot-to-code", json={"sources": []})

        assert response.status_code == 422

    def test_failed_screenshot_specs_are_not_reported_as_success(
        self, dev_server, monkeypatch
    ):
        srv, client = dev_server
        monkeypatch.setattr(
            "agent.intelligence.screenshot_to_code.screenshot_to_design_spec_multi",
            lambda sources, business_type="": {"status": "failed", "failed_shots": sources},
        )
        monkeypatch.setattr(
            "agent.intelligence.screenshot_to_code.to_plan_inputs",
            lambda spec: {"failed_shots": spec["failed_shots"]},
        )

        response = client.post(
            "/api/screenshot-to-code", json={"sources": ["broken.png"]}
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["success"] is False
        assert payload["data"]["spec"]["failed_shots"] == ["broken.png"]
        assert "plan" not in payload["data"]

    def test_browser_audit_reports_every_section(self, dev_server, monkeypatch):
        srv, client = dev_server
        _public_browser_dns(monkeypatch)
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.deep_browser_audit",
            lambda url, session="lumi-qa": {"status": "measured", "url": url},
        )
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.responsive_check",
            lambda url, session="lumi-qa": {"status": "measured"},
        )
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.network_audit",
            lambda url, session="lumi-qa", allow_external=(): {"status": "measured"},
        )
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.performance_audit",
            lambda url, session="lumi-qa": {"status": "not_measured"},
        )
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.remediate_findings",
            lambda report: [{"priority": "P2"}],
        )

        response = client.post(
            "/api/browser/audit",
            json={"url": "https://www.example.com", "run_performance": True},
        )

        assert response.status_code == 200, response.text
        report = response.json()["data"]
        assert report["url"] == "https://www.example.com"
        assert report["deep_audit"]["status"] == "measured"
        assert report["responsive"]["status"] == "measured"
        assert report["network"]["status"] == "measured"
        assert report["performance"]["status"] == "not_measured"
        assert report["remediation"] == [{"priority": "P2"}]

    def test_browser_flow_does_not_report_failure_as_success(self, dev_server, monkeypatch):
        srv, client = dev_server
        _public_browser_dns(monkeypatch)
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.verify_flow",
            lambda url, steps, session="lumi-qa": {
                "status": "failed",
                "failed_at": 0,
            },
        )

        response = client.post(
            "/api/browser/flow",
            json={"url": "https://www.example.com", "steps": [{"action": "open"}]},
        )

        assert response.status_code == 200, response.text
        assert response.json()["success"] is False
        assert response.json()["data"]["failed_at"] == 0

    def test_browser_reference_and_diff_endpoints(self, dev_server, monkeypatch, tmp_path):
        srv, client = dev_server
        _public_browser_dns(monkeypatch)
        monkeypatch.setattr(server_mod, "GENERATED_PROJECTS_DIR", tmp_path)
        (tmp_path / "base.png").write_bytes(b"baseline")
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.capture_reference",
            lambda url, shots_dir, session="lumi-qa": {"status": "measured"},
        )
        monkeypatch.setattr(
            "agent.intelligence.browser_integration.visual_diff",
            lambda baseline, session="lumi-qa", url=None: {"status": "measured"},
        )

        reference = client.post(
            "/api/browser/reference",
            json={"url": "https://www.example.com", "shots_dir": "shots"},
        )
        diff = client.post("/api/browser/diff", json={"baseline": "base.png"})

        assert reference.status_code == 200, reference.text
        assert reference.json()["success"] is True
        assert diff.status_code == 200, diff.text
        assert diff.json()["success"] is True

    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",
            "http://127.0.0.1:5432/",
            "http://localhost:8000/",
            "http://db:5432/",
            "file:///etc/passwd",
            "ftp://www.example.com/site",
        ],
    )
    def test_browser_audit_rejects_ssrf_targets(self, dev_server, url):
        srv, client = dev_server
        response = client.post("/api/browser/audit", json={"url": url})

        assert response.status_code == 422, response.text

    def test_browser_audit_rejects_private_dns_answers(self, dev_server, monkeypatch):
        srv, client = dev_server
        monkeypatch.setattr(
            server_mod,
            "_resolve_browser_host_ips",
            lambda host: [ipaddress.ip_address("10.0.0.8")],
        )

        response = client.post(
            "/api/browser/audit", json={"url": "https://www.example.com"}
        )

        assert response.status_code == 422, response.text

    def test_browser_paths_stay_inside_generated_projects(
        self, dev_server, monkeypatch, tmp_path
    ):
        srv, client = dev_server
        _public_browser_dns(monkeypatch)
        monkeypatch.setattr(server_mod, "GENERATED_PROJECTS_DIR", tmp_path)
        outside = tmp_path.parent / "outside-generated-projects"

        traversal = client.post(
            "/api/browser/diff", json={"baseline": "../../outside.png"}
        )
        absolute = client.post(
            "/api/browser/reference",
            json={"url": "https://www.example.com", "shots_dir": str(outside)},
        )
        missing = client.post("/api/browser/diff", json={"baseline": "missing.png"})

        assert traversal.status_code == 422, traversal.text
        assert absolute.status_code == 422, absolute.text
        assert missing.status_code == 422, missing.text
        assert not outside.exists()
