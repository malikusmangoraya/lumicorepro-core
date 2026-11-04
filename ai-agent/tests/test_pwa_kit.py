"""PWA kit and fullstack wiring contracts (Task 4).

The browser proof lives in `test_browser_qa.py`; these tests cover the emitted
assets, the offline queue source contract and the fullstack gating.
"""
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from agent.design_forge import build_design
from agent.fullstack_ultra_engine import FullStackUltraEngine
from agent.generation_contract import resolve_generation_contract
from agent.pwa_kit import pwa_files


BRAND = "Northstar"


def design():
    return build_design(BRAND, "saas", "#2563eb", "#0d9488")


def test_pwa_files_include_manifest_worker_offline_and_icons():
    files = pwa_files(BRAND, design())
    paths = set(files)
    assert "frontend/public/manifest.webmanifest" in paths
    assert "frontend/public/sw.js" in paths
    assert "frontend/public/offline.html" in paths
    assert "frontend/public/icons/icon-192.png" in paths
    assert "frontend/public/icons/icon-512.png" in paths
    assert isinstance(files["frontend/public/icons/icon-192.png"], bytes)
    worker = files["frontend/public/sw.js"]
    assert "network-first" in worker or "cache-first" in worker
    assert "api" not in worker.lower() or "no-store" in worker.lower()
    assert "VERSION" in worker
    manifest = json.loads(files["frontend/public/manifest.webmanifest"])
    assert manifest["display"] == "standalone"
    assert manifest["icons"][0]["sizes"] == "192x192"


def test_manifest_is_installable_and_uses_design_tokens():
    design_system = design()
    manifest = json.loads(
        pwa_files(BRAND, design_system)["frontend/public/manifest.webmanifest"])
    assert manifest["name"] == BRAND
    assert manifest["short_name"]
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["theme_color"] == design_system["primary"]
    assert manifest["background_color"] == design_system["slate"]["950"]
    assert [icon["sizes"] for icon in manifest["icons"]] == ["192x192", "512x512"]
    assert {icon["type"] for icon in manifest["icons"]} == {"image/png"}


def test_icons_are_deterministic_decodable_pngs():
    first = pwa_files(BRAND, design())
    second = pwa_files(BRAND, design())
    for relative, size in (
        ("frontend/public/icons/icon-192.png", (192, 192)),
        ("frontend/public/icons/icon-512.png", (512, 512)),
    ):
        payload = first[relative]
        assert isinstance(payload, bytes)
        assert payload == second[relative]
        with Image.open(BytesIO(payload)) as image:
            assert image.format == "PNG"
            assert image.size == size
            colors = image.convert("RGB").getcolors(maxcolors=1_000_000) or []
            assert len(colors) >= 3


def test_worker_is_versioned_and_never_caches_private_api_data():
    worker = pwa_files(BRAND, design())["frontend/public/sw.js"]
    assert "const VERSION" in worker
    assert "lumicore-" in worker
    assert "network-first" in worker
    assert "cache-first" in worker
    assert "/offline.html" in worker
    assert "/manifest.webmanifest" in worker
    assert "/icons/icon-192.png" in worker
    assert "/icons/icon-512.png" in worker
    assert "cache: 'no-store'" in worker or 'cache: "no-store"' in worker
    assert "caches.keys()" in worker
    assert "caches.delete" in worker
    # The API branch must run before the static cache-first branch.
    assert worker.index("/api/") < worker.index("cache-first")
    assert "request.method !== 'GET'" in worker


def test_offline_page_is_standalone_and_offers_retry():
    html = pwa_files(BRAND, design())["frontend/public/offline.html"]
    assert "<h1>You're offline</h1>" in html
    assert "location.reload()" in html
    assert "name=\"viewport\"" in html
    assert "http" not in html.lower().replace("http-equiv", "")


def test_web_app_queue_is_bounded_and_uses_the_client_record_id():
    files = pwa_files(BRAND, design(), web_app=True)
    queue = files["frontend/src/offlineQueue.js"]
    assert "lumicore-queue" in queue
    assert "'records'" in queue or '"records"' in queue
    assert "MAX_RECORDS = 50" in queue
    assert "export async function enqueue" in queue
    assert "export async function flush" in queue
    assert "export async function count" in queue
    assert "flushPromise" in queue
    assert "getToken" in queue and "Authorization" in queue

    records = files["frontend/src/pages/Records.jsx"]
    assert "crypto.randomUUID()" in records
    assert "enqueue(" in records
    assert "flush(" in records
    assert "data-queue-count" in records
    assert "Queued on this device" in records
    assert "window.addEventListener('online'" in records
    assert 'id="record-notice"' in records


def test_queue_rows_are_keyed_by_the_authenticated_user():
    queue = pwa_files(BRAND, design(), web_app=True)["frontend/src/offlineQueue.js"]
    assert "keyPath: ['owner', 'id']" in queue
    assert "DB_VERSION = 2" in queue
    assert "currentUserId" in queue
    assert "queueOwner" in queue
    assert "export async function clearQueue" in queue
    assert "delete([owner, id])" in queue
    assert "Sign in to queue records" in queue


def test_queue_retries_are_bounded_and_flush_at_boot():
    files = pwa_files(BRAND, design(), web_app=True)
    queue = files["frontend/src/offlineQueue.js"]
    banner = files["frontend/src/pwa.js"]
    assert "FLUSH_ATTEMPTS = 3" in queue
    assert "RETRY_DELAY_MS" in queue
    assert "drainWithRetry" in queue
    assert "Queue owner changed" in queue
    assert "if (navigator.onLine)" in banner
    assert "sync();" in banner
    assert "Sync pending." in banner
    assert "Syncing when the connection returns" not in banner
    assert "lumicore:signout" in banner


def test_website_pwa_does_not_emit_the_app_write_queue():
    files = pwa_files(BRAND, design())
    assert "frontend/src/offlineQueue.js" not in files
    assert "frontend/src/pages/Records.jsx" not in files
    # Update prompts are not app-specific: every PWA can activate a new worker.
    assert "frontend/src/pwaUpdate.js" in files


def test_worker_waits_for_the_explicit_update_prompt():
    worker = pwa_files(BRAND, design())["frontend/public/sw.js"]
    install = worker.split("addEventListener('install'", 1)[1].split(
        "addEventListener('message'", 1)[0]
    assert "skipWaiting" not in install
    assert "SKIP_WAITING" in worker
    assert "addEventListener('message'" in worker
    assert "GET_VERSION" in worker


def test_update_prompt_is_visible_accessible_and_reloads_after_activation():
    prompt = pwa_files(BRAND, design())["frontend/src/pwaUpdate.js"]
    assert "updatefound" in prompt
    assert "registration.waiting" in prompt
    assert "setAttribute('role', 'status')" in prompt
    assert "setAttribute('aria-live', 'polite')" in prompt
    assert "Reload to update" in prompt
    assert "postMessage({ type: 'SKIP_WAITING' })" in prompt
    assert "controllerchange" in prompt
    assert "window.location.reload()" in prompt
    assert "'serviceWorker' in navigator && import.meta.env.PROD" in prompt


def test_auth_exposes_the_subject_and_announces_sign_out():
    from agent.app_layouts import render_app_files

    auth = render_app_files(BRAND, "saas", design())["frontend/src/auth.js"]
    assert "export function currentUserId" in auth
    assert "payload.id || payload.sub" in auth
    assert "lumicore:signout" in auth
    assert "previousUserId" in auth


def pwa_contract():
    contract = resolve_generation_contract({
        "app": {"web": "web_app", "pwa": True, "mobile": None},
    })
    assert contract["app"]["pwa"] is True
    return contract


def test_fullstack_emits_pwa_assets_only_when_requested(tmp_path):
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt="Build a records web app", brand_name=BRAND,
        generation_contract=pwa_contract(),
    )
    assert result["success"] is True, result
    for relative in (
        "frontend/public/manifest.webmanifest",
        "frontend/public/sw.js",
        "frontend/public/offline.html",
        "frontend/public/icons/icon-192.png",
        "frontend/public/icons/icon-512.png",
    ):
        path = tmp_path / relative
        assert path.is_file() and path.stat().st_size > 0, relative
    main = (tmp_path / "frontend/src/main.jsx").read_text(encoding="utf-8")
    assert "import './pwaUpdate.js';" in main
    assert "import './pwa.js';" in main
    assert (tmp_path / "frontend/src/pwaUpdate.js").is_file()
    update = (tmp_path / "frontend/src/pwaUpdate.js").read_text(encoding="utf-8")
    assert "updatefound" in update and "SKIP_WAITING" in update
    assert (tmp_path / "frontend/src/offlineQueue.js").is_file()
    assert "manifest.webmanifest" in (
        tmp_path / "frontend/index.html").read_text(encoding="utf-8")
    app_contract = json.loads(
        (tmp_path / "app-contract.json").read_text(encoding="utf-8"))
    assert app_contract["pwa"] is True


def test_fullstack_without_pwa_request_writes_no_pwa_assets(tmp_path):
    contract = resolve_generation_contract({"prompt": "Build a records web app"})
    assert contract["app"]["pwa"] is False
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt="Build a records web app", brand_name=BRAND,
        generation_contract=contract,
    )
    assert result["success"] is True, result
    assert not (tmp_path / "frontend/public/sw.js").exists()
    assert not (tmp_path / "frontend/src/offlineQueue.js").exists()
    main = (tmp_path / "frontend/src/main.jsx").read_text(encoding="utf-8")
    assert "serviceWorker" not in main
    assert FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface="web_app") == []


def test_pwa_artifact_validation_requires_every_worker_asset(tmp_path):
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt="Build a records web app", brand_name=BRAND,
        generation_contract=pwa_contract(),
    )
    assert result["success"] is True, result
    assert FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface="web_app", pwa=True) == []
    (tmp_path / "frontend/public/sw.js").unlink()
    errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface="web_app", pwa=True)
    assert any("frontend/public/sw.js" in error for error in errors)
