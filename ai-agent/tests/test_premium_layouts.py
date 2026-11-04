"""Public-emitter contracts; generated browser journeys can be run explicitly."""
import importlib
import importlib.util
import json
import os
import re
import threading
from copy import deepcopy
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from agent.design_forge import build_design


CASES = [
    ("Evergreen", "saas", "hero-split", ("capabilities", "workflow", "principles")),
    ("Northstar", "legal", "hero-editorial", ("principles", "capabilities", "workflow")),
    ("Meridian", "gaming", "hero-kinetic", ("workflow", "principles", "capabilities")),
    ("Ledger", "finance", "hero-precision", ("workflow", "capabilities", "principles")),
]


def emitter():
    assert importlib.util.find_spec("agent.premium_layouts"), "public-layout emitter is missing"
    return importlib.import_module("agent.premium_layouts")


def render(brand="Evergreen", industry="saas", **kwargs):
    return emitter().render_public_files(
        brand, industry, build_design(brand, industry, "#2563eb", "#0d9488"), **kwargs,
    )


def test_public_files_match_generator_paths_without_overwriting_auth_or_dashboard():
    files = render()
    assert set(files) == {
        "frontend/src/App.jsx",
        "frontend/src/components/common/GlassNavbar.jsx",
        "frontend/src/components/common/ModernFooter.jsx",
        "frontend/src/pages/Home.jsx",
        "frontend/src/pages/Features.jsx",
        "frontend/src/pages/Pricing.jsx",
        "frontend/src/pages/About.jsx",
        "frontend/src/pages/Contact.jsx",
        "frontend/public/assets/workflow.svg",
    }
    app = files["frontend/src/App.jsx"]
    for page in ("Home", "Features", "Pricing", "About", "Contact", "Login", "Register", "Dashboard"):
        assert f"lazy(() => import('./pages/{page}.jsx'))" in app
    assert "useLocation()" in app
    assert "window.location.pathname" not in app
    assert 'id="main-content"' in app
    assert 'href="#main-content"' in app
    assert "!isAuthRoute" in app


@pytest.mark.parametrize("brand,industry,hero,order", CASES)
def test_compositions_emit_different_semantic_hero_structures_and_order(brand, industry, hero, order):
    home = render(brand, industry)["frontend/src/pages/Home.jsx"]
    assert f'className="{hero}"' in home
    assert [key for key in re.findall(r'<section id="([a-z-]+)"', home)] == list(order)
    hero_markup = home.split('id="' + order[0] + '"')[0]
    if industry == "saas":
        assert "<figure" in hero_markup and "<figcaption" in hero_markup
    elif industry == "legal":
        assert "<aside" in hero_markup and "<blockquote" not in hero_markup
    elif industry == "gaming":
        assert "<ol" in hero_markup
    else:
        assert "<dl" in hero_markup and "<dt" in hero_markup


def test_route_expectations_are_independent_stable_public_headings():
    assert emitter().route_expectations("Evergreen") == {
        "/": {"heading": "Evergreen"},
        "/features": {"heading": "What you can do"},
        "/pricing": {"heading": "Choose your next step"},
        "/about": {"heading": "Built for your work"},
        "/contact": {"heading": "Let's talk"},
        "/login": {"heading": "Sign in"},
        "/register": {"heading": "Create your account"},
    }
    for page, heading in [("Features", "What you can do"), ("Pricing", "Choose your next step"),
                          ("About", "Built for your work"), ("Contact", "Let's talk")]:
        assert re.search(r'<h1[^>]*>' + re.escape(heading) + r'</h1>', render()[f"frontend/src/pages/{page}.jsx"])


def test_brand_and_industry_are_serialized_as_data_not_jsx_or_template_code():
    brand = '\"</script><img src=x onerror=alert(1)>{x} ${alert(2)} & __INDUSTRY__\u2028'
    industry = "</div><script>alert('x')</script>"
    files = render(brand, industry)
    home = files["frontend/src/pages/Home.jsx"]
    encoded = re.search(r"const BRAND = (.*);", home).group(1)
    assert json.loads(encoded) == brand
    assert "<script>" not in "\n".join(files.values())
    assert "<img src=x" not in "\n".join(files.values())
    assert '<h1 className="hero-brand">{BRAND}</h1>' in home
    assert "dangerouslySetInnerHTML" not in "\n".join(files.values())


def test_emission_is_repeatable_and_does_not_mutate_design():
    design = build_design("Evergreen", "saas", "#2563eb", "#0d9488")
    original = deepcopy(design)
    first = emitter().render_public_files("Evergreen", "saas", design)
    assert first == emitter().render_public_files("Evergreen", "saas", design)
    assert design == original


def test_only_explicit_scene_emission_imports_the_scene():
    ordinary = "\n".join(render().values())
    assert "Modern3DScene" not in ordinary
    assert "@react-three" not in ordinary and "from 'three'" not in ordinary
    enabled = render(scene_enabled=True)["frontend/src/pages/Home.jsx"]
    assert "lazy(() => import('../components/motion/Modern3DScene.jsx'))" in enabled
    assert "<Modern3DScene" in enabled and "<Suspense" in enabled


def test_public_defaults_omit_unsupported_claims_and_dead_controls():
    text = "\n".join(render().values()).lower()
    for claim in ('href="#"', "99.9", "certified", "testimonials", "uptime", "prorated",
                  "free trial", "credit card", "hello@", "currency", "autoplay", "$29", "sla"):
        assert claim not in text
    destinations = re.findall(r'(?:to|href)="([^"]+)"', text)
    assert set(destinations) <= {"/", "/features", "/pricing", "/about", "/contact", "/login",
                                 "/register", "/dashboard", "#main-content"}
    assert "/register" in destinations and "/contact" in destinations


def test_mobile_nav_supports_keyboard_state_and_close_on_navigation():
    nav = render()["frontend/src/components/common/GlassNavbar.jsx"]
    for contract in ("aria-expanded={mobileOpen}", 'aria-controls="public-navigation"',
                     'id="public-navigation"', "event.key === 'Escape'", "toggleRef.current?.focus()",
                     "useLocation()", "setMobileOpen(false)", "[location]", "aria-label="):
        assert contract in nav


def test_contact_preserves_post_contract_and_validation_with_truthful_retry():
    contact = render()["frontend/src/pages/Contact.jsx"]
    for contract in ("VITE_API_URL", "fetch(`${API}/contact`", "method: 'POST'", "JSON.stringify(payload)",
                     "120", "254", "5000", "< 10", "EMAIL_RE.test", "json.success !== true",
                     "Try again", "Message received", "Send another message", "role=\"alert\"",
                     "aria-describedby", "aria-invalid", "autoComplete", "disabled={status === 'sending'}"):
        assert contract in contact
    assert "one business day" not in contact
    assert "error.message" not in contact
    assert "json.message" not in contact
    assert "json.errors" in contact


def test_workflow_asset_is_local_original_static_svg():
    files = render()
    asset = files["frontend/public/assets/workflow.svg"]
    assert '<svg' in asset and 'viewBox="0 0 640 480"' in asset
    assert '<script' not in asset and '<image' not in asset and '<animate' not in asset
    assert '${import.meta.env.BASE_URL}assets/workflow.svg' in files["frontend/src/pages/Home.jsx"]


@pytest.fixture(scope="module")
def rendered_browser():
    """Opt-in real built fixture; absent runtime/build fails when requested.

    PREMIUM_LAYOUT_BROWSER_ROOT points to a generated representative project.
    This suite exercises emitter output, not live database or delivery proofs.
    """
    root_value = os.environ.get("PREMIUM_LAYOUT_BROWSER_ROOT")
    if not root_value:
        pytest.skip("Set PREMIUM_LAYOUT_BROWSER_ROOT to run generated UI browser acceptance")
    root = Path(root_value).resolve()
    dist = root / "frontend" / "dist"
    assert (dist / "index.html").is_file(), "A real production build is required"
    from playwright.sync_api import sync_playwright

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if not Path(path).suffix:
                self.path = "/index.html"
            super().do_GET()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(dist)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as runtime:
            browser = runtime.chromium.launch()
            try:
                yield browser, f"http://127.0.0.1:{server.server_port}", root
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("width", [375, 768, 1024, 1440, 1920])
@pytest.mark.parametrize("motion", ["no-preference", "reduce"])
def test_generated_public_routes_render_without_overflow_or_runtime_errors(rendered_browser, width, motion):
    browser, origin, root = rendered_browser
    from playwright.sync_api import expect
    context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion=motion)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("requestfailed", lambda request: errors.append(request.url))
    page.route("https://fonts.googleapis.com/**", lambda route: route.fulfill(body="", content_type="text/css"))
    brand = os.environ.get("PREMIUM_LAYOUT_BROWSER_BRAND", "Evergreen")
    headings = {"/": brand, "/features": "What you can do", "/pricing": "Choose your next step",
                "/about": "Built for your work", "/contact": "Let's talk", "/login": "Sign in",
                "/register": "Create your account"}
    try:
        for path, heading in headings.items():
            page.goto(origin + path)
            expect(page.locator("main").get_by_role("heading", name=heading, exact=True)).to_be_visible()
            assert page.evaluate("window.innerWidth") == width
            offenders = page.evaluate("""() => [...document.querySelectorAll('main *, header *, footer *')]
              .filter(el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
                return r.width && r.height && s.visibility !== 'hidden' && s.display !== 'none'
                  && (r.left < -1 || r.right > innerWidth + 1); }).map(el => el.outerHTML.slice(0, 180))""")
            assert not offenders, (path, width, offenders)
            if path in ("/login", "/register"):
                expect(page.locator(".public-header")).to_have_count(0)
                expect(page.locator(".public-footer")).to_have_count(0)
            if path == "/":
                for image in page.locator("main img").all():
                    assert image.evaluate("el => el.complete && el.naturalWidth > 0")
                evidence = root / "emitter-evidence"
                evidence.mkdir(exist_ok=True)
                page.screenshot(path=str(evidence / f"home-{width}-{motion}.png"), full_page=True)
        assert not errors
    finally:
        context.close()


def test_generated_mobile_keyboard_navigation_and_auth_shell_updates(rendered_browser):
    browser, origin, _ = rendered_browser
    from playwright.sync_api import expect
    context = browser.new_context(viewport={"width": 375, "height": 900})
    page = context.new_page()
    page.route("https://fonts.googleapis.com/**", lambda route: route.fulfill(body="", content_type="text/css"))
    try:
        page.goto(origin)
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
        page.keyboard.press("Enter")
        expect(page.locator("main")).to_be_focused()
        toggle = page.locator(".menu-toggle")
        expect(toggle).to_have_accessible_name("Open navigation")
        toggle.focus()
        page.keyboard.press("Enter")
        expect(toggle).to_have_attribute("aria-expanded", "true")
        expect(toggle).to_have_accessible_name("Close navigation")
        page.keyboard.press("Tab")
        expect(page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Features")).to_be_focused()
        page.keyboard.press("Escape")
        expect(toggle).to_be_focused()
        expect(toggle).to_have_attribute("aria-expanded", "false")
        expect(toggle).to_have_accessible_name("Open navigation")
        page.keyboard.press("Enter")
        page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Contact").click()
        expect(page.get_by_role("heading", name="Let's talk", exact=True)).to_be_visible()
        expect(toggle).to_have_attribute("aria-expanded", "false")
        toggle.click()
        page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Sign in").click()
        expect(page.get_by_role("heading", name="Sign in", exact=True)).to_be_visible()
        expect(page.locator(".public-header")).to_have_count(0)
        page.get_by_role("link", name="Back to home").click()
        expect(page.locator(".public-header")).to_be_visible()
    finally:
        context.close()


def test_generated_contact_invalid_error_retry_success_and_malformed_response(rendered_browser):
    browser, origin, _ = rendered_browser
    from playwright.sync_api import expect
    context = browser.new_context(viewport={"width": 375, "height": 900})
    page = context.new_page()
    page.route("https://fonts.googleapis.com/**", lambda route: route.fulfill(body="", content_type="text/css"))
    calls = []
    reply = {"status": 500, "body": {"success": False, "message": "private internal trace"}}

    def contact(route):
        if route.request.method == "OPTIONS":
            route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*",
                          "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST"})
            return
        calls.append(route.request.post_data_json)
        route.fulfill(status=reply["status"], content_type="application/json",
                      headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(reply["body"]))

    page.route("**/api/v1/contact", contact)
    try:
        page.goto(origin + "/contact")
        page.get_by_role("button", name="Send message", exact=True).click()
        expect(page.get_by_label("Your name")).to_be_focused()
        assert not calls
        expect(page.get_by_label("Email", exact=True)).to_have_attribute("aria-invalid", "true")
        page.get_by_label("Your name").fill("  Reader  ")
        page.get_by_label("Email", exact=True).fill("reader@example.test")
        page.get_by_label("How can we help?").fill("  Please explain the record workflow.  ")
        page.get_by_role("button", name="Send message", exact=True).click()
        expect(page.get_by_role("button", name="Try again")).to_be_visible()
        assert calls == [{"name": "Reader", "email": "reader@example.test", "message": "Please explain the record workflow."}]
        expect(page.get_by_label("Your name")).to_have_value("  Reader  ")
        expect(page.get_by_text("private internal trace")).to_have_count(0)
        reply.update(status=200, body={})
        page.get_by_role("button", name="Try again").click()
        expect(page.get_by_role("button", name="Try again")).to_be_enabled()
        expect(page.get_by_role("heading", name="Message received")).to_have_count(0)
        reply.update(status=422, body={"success": False, "errors": {"email": "internal detail"}})
        page.get_by_role("button", name="Try again").click()
        expect(page.get_by_label("Email", exact=True)).to_have_attribute("aria-invalid", "true")
        reply.update(status=201, body={"success": True, "data": {"id": "saved-record"}})
        page.get_by_role("button", name="Try again").click()
        expect(page.get_by_role("heading", name="Message received")).to_be_visible()
        page.get_by_role("button", name="Send another message").click()
        expect(page.get_by_label("Your name")).to_have_value("")
    finally:
        context.close()
