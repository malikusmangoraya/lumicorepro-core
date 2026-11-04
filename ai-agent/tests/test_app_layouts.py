"""App-shell emitter contracts for the authenticated `web_app` surface."""
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from agent.app_layouts import app_route_expectations, render_app_files
from agent.design_forge import build_design


def files_for(brand="Northstar"):
    return render_app_files(
        brand, "saas", build_design(brand, "saas", "#2563eb", "#0d9488"))


def test_app_shell_routes_and_headings_are_independent():
    files = files_for()
    assert app_route_expectations("Northstar") == {
        "/login": {"heading": "Sign in"},
        "/register": {"heading": "Create your account"},
        "/dashboard": {"heading": "Your workspace"},
        "/records": {"heading": "All records"},
        "/settings": {"heading": "Account settings"},
    }
    assert "localStorage.getItem('token')" in files["frontend/src/auth.js"]
    assert "AuthGuard" in files["frontend/src/App.jsx"]


def test_app_shell_emits_exactly_the_authenticated_surface():
    files = files_for()
    assert set(files) == {
        "frontend/src/App.jsx",
        "frontend/src/components/AppShell.jsx",
        "frontend/src/auth.js",
        "frontend/src/pages/Login.jsx",
        "frontend/src/pages/Register.jsx",
        "frontend/src/pages/Dashboard.jsx",
        "frontend/src/pages/Records.jsx",
        "frontend/src/pages/Settings.jsx",
        "frontend/src/app.css",
    }
    app = files["frontend/src/App.jsx"]
    for route in ("/login", "/register", "/dashboard", "/records", "/settings"):
        assert f'path="{route}"' in app
    assert "Navigate" in app and "AuthGuard" in app
    assert 'to="/dashboard"' in app and 'to="/login"' in app
    # The marketing shell cannot leak into the app shell.
    assert "Features" not in app and "Pricing" not in app
    assert "GlassNavbar" not in app and "ModernFooter" not in app


def test_each_page_owns_its_headings_and_no_marketing_routes():
    files = files_for()
    expected = {
        "frontend/src/pages/Login.jsx": "<h1>Sign in</h1>",
        "frontend/src/pages/Register.jsx": "<h1>Create your account</h1>",
        "frontend/src/pages/Dashboard.jsx": "<h1>Your workspace</h1>",
        "frontend/src/pages/Records.jsx": "<h1>All records</h1>",
        "frontend/src/pages/Settings.jsx": "<h1>Account settings</h1>",
    }
    for relative, heading in expected.items():
        assert heading in files[relative]
    text = "\n".join(files.values()).lower()
    for banned in ("99.9", "uptime", "testimonial", "/features", "/pricing",
                   'href="#"', "lorem ipsum", "fake"):
        assert banned not in text


def test_auth_client_seeds_and_clears_the_production_token_key():
    auth = files_for()["frontend/src/auth.js"]
    assert "localStorage.getItem('token')" in auth
    assert "localStorage.setItem('token'" in auth
    assert "localStorage.removeItem('token')" in auth
    assert "Authorization: `Bearer ${" in auth
    assert "VITE_API_URL" in auth
    assert "http://localhost:5000/api/v1" in auth
    assert "export async function request(" in auth
    assert "export function signOut()" in auth
    # Plain objects must be serialized; FormData and string bodies stay untouched.
    assert "JSON.stringify(body)" in auth
    assert "body instanceof FormData" in auth


def test_records_page_uses_the_real_api_and_all_ui_states():
    records = files_for()["frontend/src/pages/Records.jsx"]
    for marker in (
        "request('/records')", "crypto.randomUUID()", "method: 'POST'",
        "method: 'PUT'", "method: 'DELETE'", 'type="search"',
        "statusFilter", "loading", "error", "Try again", "No records yet",
        "No records match", "aria-label",
    ):
        assert marker in records
    # A title and body come from the user; no fabricated demo rows.
    assert "title" in records and "body" in records
    assert "localhost" not in records


def test_dashboard_and_settings_only_show_real_session_data():
    files = files_for()
    dashboard = files["frontend/src/pages/Dashboard.jsx"]
    assert "request('/records')" in dashboard
    assert ".reduce(" in dashboard
    settings = files["frontend/src/pages/Settings.jsx"]
    assert "readOnly" in settings and "signOut" in settings
    assert "currentUser" in settings
    shell = files["frontend/src/components/AppShell.jsx"]
    assert "<main" in shell and "aria-label" in shell
    assert "signOut" in shell
    assert "Outlet" in shell


def test_brand_text_is_escaped_into_javascript_data():
    files = render_app_files(
        "</script><script>alert(1)</script>", "saas",
        build_design("Northstar", "saas", "#2563eb", "#0d9488"))
    joined = "\n".join(files.values())
    assert "</script><script>alert(1)</script>" not in joined
    assert "\\u003c/script\\u003e" in joined


def test_app_css_uses_design_tokens():
    design = build_design("Northstar", "saas", "#2563eb", "#0d9488")
    css = render_app_files("Northstar", "saas", design)["frontend/src/app.css"]
    assert design["primary"] in css
    assert design["accent"] in css
    assert design["slate"]["950"] in css
    assert "focus-visible" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


@pytest.fixture(scope="module")
def built_web_app(tmp_path_factory):
    """Generate and really build a `web_app`; a source marker cannot prove fetch()."""
    from agent.factory_pipeline import build_project
    from agent.fullstack_ultra_engine import FullStackUltraEngine
    from agent.generation_contract import resolve_generation_contract

    root = tmp_path_factory.mktemp("built-web-app")
    contract = resolve_generation_contract({"prompt": "Build a records web app"})
    assert contract["app"]["web"] == "web_app"
    result = FullStackUltraEngine().generate_project(
        str(root), prompt="Build a records web app", brand_name="Northstar",
        generation_contract=contract,
    )
    assert result["success"] is True, result
    build = build_project(str(root), install=True)
    assert build["ok"] is True, build
    return Path(build["dist"])


def test_built_web_app_login_posts_an_object_as_json(built_web_app):
    """Regression: fetch(object) sent `[object Object]`, so Express rejected logins."""
    from playwright.sync_api import sync_playwright

    from agent.extensions.browser_qa import CORS_HEADERS, _PreviewHandler

    def handler(*args, **kwargs):
        return _PreviewHandler(*args, roots=[str(built_web_app)], **kwargs)

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    login_requests = []
    try:
        with sync_playwright() as runtime:
            browser = runtime.chromium.launch(headless=True)
            try:
                context = browser.new_context(viewport={"width": 1280, "height": 900})
                page = context.new_page()

                def api(route):
                    request = route.request
                    if request.method == "OPTIONS":
                        route.fulfill(status=204, headers=CORS_HEADERS, body="")
                        return
                    headers = {**CORS_HEADERS, "content-type": "application/json"}
                    if request.url.endswith("/auth/login"):
                        login_requests.append(request.post_data_json)
                        route.fulfill(
                            status=200, headers=headers,
                            body=json.dumps({
                                "success": True, "token": "qa-token",
                                "user": {"email": "reader@example.test", "name": "Reader"},
                            }),
                        )
                        return
                    route.fulfill(status=404, headers=headers,
                                  body='{"success":false,"message":"No QA fixture"}')

                page.route("**/api/v1/**", api)
                page.goto(f"http://127.0.0.1:{server.server_port}/login",
                          wait_until="networkidle")
                page.get_by_label("Email").fill("reader@example.test")
                page.get_by_label("Password").fill("correct-horse-battery")
                page.get_by_role("button", name="Sign in").click()
                page.wait_for_url("**/dashboard")
                assert login_requests == [{
                    "email": "reader@example.test",
                    "password": "correct-horse-battery",
                }]
                assert page.get_by_role("heading", name="Your workspace").is_visible()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
