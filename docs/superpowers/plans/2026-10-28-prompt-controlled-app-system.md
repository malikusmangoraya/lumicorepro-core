# Prompt-Controlled App System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build exactly the surfaces a prompt asks for — web only, mobile app only, or both — with optional PWA, one shared backend, and real APK/emulator proof for mobile.

**Architecture:** A normalized `app` contract drives every stage. `FullStackUltraEngine` emits website, web-app shell, backend and/or `mobile/` according to that contract; `factory_pipeline` runs only the matching build/QA/deploy/mobile stages and fails closed. Expo SDK 58 (React Native 0.88) is the mobile stack; Android verification uses a pinned SDK 35 toolchain, Gradle debug APK and Maestro flows.

**Tech Stack:** Python 3, pytest, Node 24/npm 11, React 19 + Vite 6 + Tailwind 3, Express + Sequelize + PostgreSQL, Expo SDK 58 + Expo Router + TypeScript, Android SDK 35 + Gradle + Maestro, Playwright/Chromium.

**Spec:** `docs/superpowers/specs/2026-10-28-universal-app-system-design.md`

## Global Constraints

- Work only in `D:/lumicorepro-core-premium-delivery` on `feature/premium-delivery-gates`; never modify the original `D:/lumicorepro-core` checkout.
- No commit, push, external deployment, store submission or live payment unless the user explicitly authorizes it. The existing worktree may already be dirty; leave prior work intact.
- **Prompt decides surfaces.** Website prompt → website only. App/mobile prompt → `backend/` + `mobile/`, no `frontend/`. “Web and app” → stated web surface + mobile. Never add a surface that was not requested.
- PWA only when the prompt says PWA/installable/offline or `--deliver-pwa` is passed; `pwa: true` with `web: "none"` is invalid.
- One shared backend for every selected surface; do not create a second API.
- Mobile delivery requires a debug APK built, installed and launched on the emulator. Missing toolchain/API/DB is `blocked` or `partial`, never `delivered`.
- iOS project files may be generated; iOS simulator/device proof is `not_measured` on Windows.
- Never put tokens, passwords, local model paths or private data in reports, bundles, logs or screenshots.
- No automatic toolchain install during delivery. `--android-toolchain install` requires `--accept-licenses`.
- Run focused tests only during iteration. Real emulator/APK tests are opt-in and fail (not skip silently) when requested without a toolchain.
- Use `py` (not `python`) on this machine. Run pytest through:
  `py -c "import os,sys; os.chdir(r'D:\lumicorepro-core-premium-delivery\ai-agent'); sys.path.insert(0,os.getcwd()); import pytest; sys.exit(pytest.main([...]))"`
- Each task ends with a green focused test run and a checkpoint note; no commit step is permitted.

## File Structure

- `ai-agent/agent/generation_contract.py` — surface normalization and prompt routing.
- `ai-agent/agent/app_layouts.py` (new) — authenticated web-app shell emitter.
- `ai-agent/agent/pwa_kit.py` (new) — manifest, service worker, offline page, PWA icons.
- `ai-agent/agent/mobile_app_engine.py` (new) — Expo project emitter.
- `ai-agent/agent/android_toolchain.py` (new) — toolchain check/install.
- `ai-agent/agent/mobile_verify.py` (new) — export, APK build, emulator, Maestro.
- `ai-agent/agent/mobile_fixture_api.py` (new) — loopback fixture API for `app_runs`.
- `ai-agent/agent/fullstack_ultra_engine.py` — surface branches, mobile stage, `app-contract.json`, artifact contracts.
- `ai-agent/agent/production_spec_kit.py` — backend-only mode (skip frontend writes).
- `ai-agent/agent/factory_pipeline.py` — conditional stages, mobile evidence, delivery rules.
- `ai-agent/agent/extensions/browser_qa.py` — app-shell fixtures and PWA proof.
- `ai-agent/main.py`, `ai-agent/server.py` — CLI/API surface fields (no local paths).
- `ai-agent/tests/` — one focused test module per new unit plus factory acceptance tests.
- `AGENTS.md`, `CHANGELOG.md`, `docs/FACTORY.md` — permanent rules and evidence.

---

### Task 1: Surface contract and prompt routing

**Files:**
- Modify: `ai-agent/agent/generation_contract.py`
- Test: `ai-agent/tests/test_generation_contract.py`
- Modify: `ai-agent/agent/factory_pipeline.py` (`deliver_from_prompt` signature/early validation)
- Modify: `ai-agent/main.py` (deliver flags)
- Modify: `ai-agent/server.py` (`FactoryDeliverRequest`)
- Test: `ai-agent/tests/test_factory_prompt.py`

**Interfaces:**
- Produces: `resolve_app_request(spec: dict) -> dict | None` returning `{"web": "website"|"web_app"|"none", "pwa": bool, "mobile": {"platforms": list[str], "verification": "apk_emulator"|"none"} | None}`.
- Produces: `resolve_generation_contract(spec)` includes `"app"` only when a surface is requested.
- Produces: `deliver_from_prompt(..., app: dict | None = None)`.

- [ ] **Step 1: Write the failing routing tests**

```python
import pytest
from agent.generation_contract import resolve_generation_contract

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

def test_pwa_without_a_web_surface_is_invalid():
    with pytest.raises(ValueError):
        resolve_generation_contract({"app": {"web": "none", "pwa": True}})

def test_unknown_surfaces_are_rejected_without_echoing_input():
    with pytest.raises(ValueError) as error:
        resolve_generation_contract({"app": {"web": "secret-value"}})
    assert "secret-value" not in str(error.value)

def test_default_contract_has_no_app_block():
    assert "app" not in resolve_generation_contract({})
```

- [ ] **Step 2: Run the red test**

Run: `py -c "import os,sys; os.chdir(r'D:\lumicorepro-core-premium-delivery\ai-agent'); sys.path.insert(0,os.getcwd()); import pytest; sys.exit(pytest.main(['tests/test_generation_contract.py','-q','-p','no:randomly','--tb=short']))"`
Expected: FAIL on missing `app` routing.

- [ ] **Step 3: Implement normalization**

```python
APP_WEB_SURFACES = ("website", "web_app", "none")
APP_MOBILE_PLATFORMS = ("android", "ios")
APP_VERIFICATIONS = ("apk_emulator", "none")

def resolve_app_request(spec):
    raw = spec.get("app")
    prompt = str(spec.get("prompt") or "")
    if raw is None:
        raw = _app_from_prompt(prompt)
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) - {"web", "pwa", "mobile"}:
        raise ValueError("App request must contain web, pwa or mobile.")
    web = str(raw.get("web") or "none").strip().lower()
    if web not in APP_WEB_SURFACES:
        raise ValueError("Unsupported web surface.")
    pwa = bool(raw.get("pwa", False))
    if pwa and web == "none":
        raise ValueError("PWA requires a web surface.")
    mobile = raw.get("mobile")
    if mobile is not None:
        if not isinstance(mobile, dict) or set(mobile) - {"platforms", "verification"}:
            raise ValueError("Invalid mobile surface.")
        platforms = mobile.get("platforms") or ["android"]
        if not isinstance(platforms, list) or not platforms or set(platforms) - set(APP_MOBILE_PLATFORMS):
            raise ValueError("Unsupported mobile platform.")
        verification = str(mobile.get("verification") or "apk_emulator").lower()
        if verification not in APP_VERIFICATIONS:
            raise ValueError("Unsupported mobile verification.")
        mobile = {"platforms": platforms, "verification": verification}
    if web == "none" and mobile is None:
        raise ValueError("An app request needs a web or mobile surface.")
    return {"web": web, "pwa": pwa, "mobile": mobile}

def _app_from_prompt(prompt):
    text = prompt.lower()
    mobile_intent = bool(re.search(
        r"\b(mobile app|android app|ios app|react native|mobile application)\b", text))
    # “website and app” has a standalone app word; “web app”, “internal app”
    # and “admin app” are web surfaces, not mobile requests.
    if re.search(
        r"(?<!web )(?<!internal )(?<!admin )(?<!management )\bapp\b", text
    ):
        mobile_intent = True
    web_intent = bool(re.search(
        r"\b(website|web site|landing page|storefront|web app|internal app|"
        r"admin dashboard|management system|web)\b", text))
    if not mobile_intent and not web_intent:
        return None
    web = "none"
    if web_intent:
        web = "web_app" if re.search(
            r"\b(web app|internal app|admin dashboard|management system)\b", text
        ) else "website"
    pwa = bool(re.search(r"\b(pwa|installable|offline app)\b", text))
    mobile = ({"platforms": ["android"], "verification": "apk_emulator"}
              if mobile_intent else None)
    return {"web": web, "pwa": pwa, "mobile": mobile}
```

Add `app = resolve_app_request(normalized_spec)` at the end of `resolve_generation_contract`; `if app is not None: contract["app"] = app`.

- [ ] **Step 4: Wire explicit input and CLI**

In `deliver_from_prompt(..., app=None)`:
```python
contract = resolve_generation_contract({"prompt": prompt, "scene": scene, "app": app})
```
mapping `ValueError` to a sanitized failed result before `provider_health()`.

In `main.py` add:
```python
parser.add_argument("--deliver-web", choices=("website", "web-app", "none"))
parser.add_argument("--deliver-mobile", choices=("android", "none"))
parser.add_argument("--deliver-pwa", action="store_true")
parser.add_argument("--deliver-mobile-verify", choices=("apk-emulator", "none"),
                    default="apk-emulator")
```
Build:
```python
app = None
if args.deliver_web or args.deliver_mobile or args.deliver_pwa:
    if args.deliver_pwa and not args.deliver_web:
        parser.error("--deliver-pwa requires --deliver-web website|web-app")
    app = {
        "web": (args.deliver_web or "none").replace("web-app", "web_app"),
        "pwa": args.deliver_pwa,
        "mobile": ({"platforms": ["android"],
                    "verification": args.deliver_mobile_verify.replace("-", "_")}
                   if args.deliver_mobile == "android" else None),
    }
```
Pass `app=app` to `deliver_from_prompt`.

In `server.py`, `FactoryDeliverRequest` gains:
```python
app: Optional[Dict[str, Any]] = Field(
    default=None,
    description="Surfaces: {'web':'website|web_app|none','pwa':bool,"
                "'mobile':{'platforms':['android'],'verification':'apk_emulator'}}")
```
The server passes it to `deliver_from_prompt`; no filesystem fields.

- [ ] **Step 5: Add factory tests**

```python
def test_app_surfaces_reach_the_generation_contract(self):
    seen = []
    def generate(destination, **kwargs):
        seen.append(kwargs["generation_contract"]["app"])
        return {"success": True, "total_files": 1}
    with tempfile.TemporaryDirectory() as tmp, \
         patch("agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project",
               side_effect=generate), \
         patch.object(factory, "run_factory", return_value={"status": "built"}):
        factory.deliver_from_prompt("Build a records app", dest_root=tmp,
                                    platform="none", video=False)
    self.assertEqual(seen[0]["web"], "none")
    self.assertEqual(seen[0]["mobile"]["platforms"], ["android"])

def test_pwa_without_web_surface_fails_before_provider_or_files(self):
    with tempfile.TemporaryDirectory() as tmp, \
         patch.object(factory, "provider_health") as health:
        result = factory.deliver_from_prompt(
            "Build a records app", dest_root=tmp,
            app={"web": "none", "pwa": True})
        self.assertEqual(result["status"], "failed")
        self.assertEqual(list(Path(tmp).iterdir()), [])
        health.assert_not_called()
```

- [ ] **Step 6: Run green and checkpoint**

Run the contract + factory prompt suites. Record exact pass counts in the plan execution record. Do not commit.

---

### Task 2: Idempotent record creation for offline queues

**Files:**
- Modify: `ai-agent/agent/production_spec_kit.py` (`_RECORDS_JS`, backend test template)
- Test: `ai-agent/tests/test_production_spec_kit.py`
- Test: `ai-agent/tests/test_premium_generation.py` (generated backend test wiring)
- Create generated file: `backend/utils/recordIdentity.js`
- Create generated test: `backend/test/record-identity.test.js`

**Interfaces:**
- `POST /api/v1/records` accepts `{id?, title, body?, status?}`; UUID v4 `id` is idempotent per user.
- Helper `isUuidV4(value)` and `duplicateRecordId(existing, userId)` exported from `recordIdentity.js`.

- [ ] **Step 1: Write failing template and Node tests**

```python
def test_records_route_is_idempotent_for_a_client_uuid(tmp_path):
    project = tmp_path / "project"
    (project / "backend").mkdir(parents=True)
    result = apply_production_spec(str(project), brand="North")
    assert result["status"] == "ok"
    route = (project / "backend/routes/records.routes.js").read_text()
    assert "isUuidV4" in route
    assert "duplicateRecordId" in route
    assert "findByPk(clientId)" in route
    assert "status(409)" in route
    assert "status(200)" in route
    helper = (project / "backend/utils/recordIdentity.js").read_text()
    assert "module.exports = { isUuidV4, duplicateRecordId };" in helper
    test_file = (project / "backend/test/record-identity.test.js").read_text()
    assert "node:test" in test_file
```

Node helper test content must assert:
```js
test('accepts canonical v4 uuids only', () => {
  assert.equal(isUuidV4('123e4567-e89b-42d3-a456-426614174000'), true);
  assert.equal(isUuidV4('123e4567-e89b-12d3-a456-426614174000'), false);
  assert.equal(isUuidV4('not-a-uuid'), false);
});
test('same user can retry the same id; another user cannot', () => {
  assert.equal(duplicateRecordId({ userId: 7 }, 7), 'retry');
  assert.equal(duplicateRecordId({ userId: 8 }, 7), 'conflict');
  assert.equal(duplicateRecordId(null, 7), 'create');
});
```

- [ ] **Step 2: Run red**

Run the focused production-spec test. Expected: FAIL because the helper and route branches do not exist.

- [ ] **Step 3: Implement the generated helper and route**

`recordIdentity.js`:
```js
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
function isUuidV4(value) { return typeof value === 'string' && UUID_V4.test(value); }
function duplicateRecordId(existing, userId) {
  if (!existing) return 'create';
  return String(existing.userId) === String(userId) ? 'retry' : 'conflict';
}
module.exports = { isUuidV4, duplicateRecordId };
```

Route POST:
```js
const clientId = req.body.id ? String(req.body.id) : null;
if (clientId && !isUuidV4(clientId)) {
  return res.status(422).json({ success: false, message: 'Invalid record id' });
}
if (clientId) {
  const existing = await Record.findByPk(clientId);
  const decision = duplicateRecordId(existing, req.user.id);
  if (decision === 'retry') return res.status(200).json({ success: true, data: existing });
  if (decision === 'conflict') {
    return res.status(409).json({ success: false, message: 'Id unavailable' });
  }
}
const record = await Record.create({ id: clientId || undefined, title, body, status,
  userId: req.user.id });
notify(String(req.user.id), { type: 'record:changed', id: String(record.id) });
return res.status(201).json({ success: true, data: record });
```
Preserve existing validation, sanitisation and tenant scope.

- [ ] **Step 4: Run green**

Run `tests/test_production_spec_kit.py`, `tests/test_premium_generation.py` and the generated backend test via the generator’s `test_backend`. Expected: all pass, including `record-identity.test.js`.

- [ ] **Step 5: Checkpoint**

Record the pass counts. Do not commit.

---

### Task 3: Web-app shell (`web_app` surface)

**Files:**
- Create: `ai-agent/agent/app_layouts.py`
- Modify: `ai-agent/agent/fullstack_ultra_engine.py` (surface branch, app contract, artifacts)
- Modify: `ai-agent/agent/extensions/browser_qa.py` (fixture auth/token for app routes)
- Test: `ai-agent/tests/test_app_layouts.py`
- Test: `ai-agent/tests/test_premium_generation.py`
- Test: `ai-agent/tests/test_browser_qa.py`

**Interfaces:**
- `render_app_files(brand: str, industry: str, design: dict) -> dict[str, str]` with `frontend/...` keys.
- `app_route_expectations(brand) -> dict[str, dict[str, str]]` returning the 5 app routes.
- BrowserQA accepts `auth_token: str = ""` and `api_fixtures: dict | None`; when present it seeds `localStorage.token` and fulfils `**/api/v1/**` deterministically.

- [ ] **Step 1: Write failing emitter tests**

```python
from agent.design_forge import build_design
from agent.app_layouts import render_app_files, app_route_expectations

def test_app_shell_routes_and_headings_are_independent():
    files = render_app_files("Northstar", "saas",
                             build_design("Northstar", "saas", "#2563eb", "#0d9488"))
    assert app_route_expectations("Northstar") == {
        "/login": {"heading": "Sign in"},
        "/register": {"heading": "Create your account"},
        "/dashboard": {"heading": "Your workspace"},
        "/records": {"heading": "All records"},
        "/settings": {"heading": "Account settings"},
    }
    assert "localStorage.getItem('token')" in files["frontend/src/auth.js"]
    assert "AuthGuard" in files["frontend/src/App.jsx"]

def test_app_shell_has_no_fake_metrics_or_marketing_routes():
    text = "\n".join(render_app_files(
        "Northstar", "saas", build_design("Northstar", "saas", "#2563eb", "#0d9488")
    ).values()).lower()
    for banned in ("99.9", "uptime", "testimonial", "/features", "/pricing", "href=\"#\""):
        assert banned not in text
```

- [ ] **Step 2: Run red**

Expected: `ModuleNotFoundError: agent.app_layouts`.

- [ ] **Step 3: Implement the emitter**

Emit exactly:

```
frontend/src/App.jsx
frontend/src/components/AppShell.jsx
frontend/src/auth.js
frontend/src/pages/Login.jsx
frontend/src/pages/Register.jsx
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Records.jsx
frontend/src/pages/Settings.jsx
frontend/src/app.css
```

Requirements:
- `App.jsx` routes `/login`, `/register`, `/dashboard`, `/records`, `/settings`;
  `/` redirects by token; unknown paths → login.
- Auth guard reads `localStorage.getItem('token')`, redirects to `/login`.
- `auth.js` exports `API` (`VITE_API_URL` or `http://localhost:5000/api/v1`),
  `request(path, options)` with `Authorization: Bearer`, and `signOut()`.
- Dashboard computes totals from `GET /records`; no invented numbers.
- Records page has search, status filter, create/edit/delete, loading/empty/error/
  retry states; uses `crypto.randomUUID()` when creating offline.
- Settings shows stored user email/name (read-only) and sign out.
- All copy is truthful; design tokens from `design_forge`; focus-visible and
  labeled controls.

- [ ] **Step 4: Integrate into the generator**

In `generate_project`, branch on `contract.get("app", {}).get("web")`:
- `"website"` or absent → existing `_build_frontend_files`.
- `"web_app"` → build package/vite/tailwind/index/main, then
  `fmap.update(render_app_files(...))`, `qa-contract.json` from
  `app_route_expectations(brand)`.
- `"none"` → skip all frontend files.
Write `app-contract.json`:
```json
{"version": 1, "web": "website", "pwa": false, "mobile": null}
```
Artifacts validator takes `web_surface` and requires app-shell markers only for
`web_app` (App routes, token guard, records fetch); for `none` it must not require
any frontend file.

- [ ] **Step 5: Add browser fixture support**

`qa-contract.json` may carry:
```json
{"auth": {"storage": {"token": "qa-token"}},
 "fixtures": {
   "GET /records": {"success": true, "data": [{"id": "r1", "title": "First record", "status": "draft"}]}
 }}
```
BrowserQA `_measure` seeds `localStorage` before navigation and fulfils matching
`**/api/v1/**` requests. Fixtures are test-only and never written to the app.
Add a real Chromium test:
```python
def test_app_shell_authenticated_routes_render_with_fixtures(tmp_path):
    build(tmp_path)  # dist with App shell
    result = browser_qa.run_browser_qa(
        str(tmp_path),
        route_expectations=app_route_expectations("Northstar"),
        viewports=SMALL,
        auth_token="qa-token",
        api_fixtures={"GET /records": {"success": True, "data": []}},
    )
    assert result["ok"] is True, result
```

- [ ] **Step 6: Run green and checkpoint**

Run `tests/test_app_layouts.py`, `tests/test_premium_generation.py`,
`tests/test_browser_qa.py`. Build one generated web_app and inspect the dist
routes with Playwright before claiming success. Do not commit.

---

### Task 4: PWA kit and offline proof

**Files:**
- Create: `ai-agent/agent/pwa_kit.py`
- Modify: `ai-agent/agent/fullstack_ultra_engine.py`
- Modify: `ai-agent/agent/extensions/browser_qa.py`
- Test: `ai-agent/tests/test_pwa_kit.py`
- Test: `ai-agent/tests/test_browser_qa.py`

**Interfaces:**
- `pwa_files(brand: str, design: dict) -> dict[str, bytes | str]` keyed under `frontend/`.
- Browser report gains `pwa: {ok, worker_controlled, offline_heading, online_recovered, queue: {...}, failures}`; `evidence_passes` requires it when `requested_pwa` is set.

- [ ] **Step 1: Write failing tests**

```python
from agent.pwa_kit import pwa_files

def test_pwa_files_include_manifest_worker_offline_and_icons():
    files = pwa_files("Northstar", build_design("Northstar", "saas", "#2563eb", "#0d9488"))
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
```

- [ ] **Step 2: Run red**

Expected: module missing.

- [ ] **Step 3: Implement the kit**

- Manifest: name, short_name, start_url `/`, scope `/`, display standalone,
  theme/background from `design`, 192/512 icons.
- Icons: Pillow-generated PNGs with brand background and mark/initials; deterministic.
- `sw.js`: cache version derived from brand + design hue; precache `/`, `/index.html`,
  `/offline.html`, manifest, icons; navigation network-first with offline fallback;
  GET static assets cache-first; `/api/` always network-only (`cache: 'no-store'`);
  activate deletes old caches.
- `offline.html`: standalone styled page, `<h1>You're offline</h1>`, retry button.
- Register the worker in production from `main.jsx`:
  `if ('serviceWorker' in navigator && import.meta.env.PROD) ...`.
- App-shell queue: `frontend/src/offlineQueue.js` using IndexedDB database
  `lumicore-queue`, object store `records`, max 50; `enqueue`, `flush`, `count`.
  Create uses `crypto.randomUUID()`; update uses the record id.
- Fullstack adds `pwa_files` only when contract `app.pwa` is true; validator
  requires the five PWA files.

- [ ] **Step 4: Add the browser PWA proof**

At the end of the normal matrix, when `requested_pwa`:
1. New context at 1440×900 with API fixtures.
2. Navigate `/dashboard`; wait `navigator.serviceWorker.ready`, reload.
3. `context.set_offline(True)`; `page.reload()`; require offline heading and no
   uncaught errors.
4. Online; reload; require authenticated content.
5. Queue: offline, create a record through the UI with fixtures delaying the POST,
   assert queued count; online; assert exactly one POST with the same UUID; queue
   clears.
6. Report `pwa`; fail the stage on any miss.

- [ ] **Step 5: Run green and real build**

Run `tests/test_pwa_kit.py` and `tests/test_browser_qa.py`. Build a PWA-enabled
web_app and run the real PWA proof; inspect offline screenshot. Do not commit.

---

### Task 5: Mobile Expo generator and surface integration

**Files:**
- Create: `ai-agent/agent/mobile_app_engine.py`
- Modify: `ai-agent/agent/fullstack_ultra_engine.py`
- Modify: `ai-agent/agent/production_spec_kit.py` (skip frontend writes when absent)
- Test: `ai-agent/tests/test_mobile_app_engine.py`
- Test: `ai-agent/tests/test_premium_generation.py`

**Interfaces:**
- `generate_mobile_app(project_dir, brand, industry, design, app, *, api_base="") -> {"success": bool, "files": list[str], "errors": list[str], "mobile": dict}`.
- Generated root: `mobile/`; app contract persisted in `app-contract.json`.

- [ ] **Step 1: Capture exact Expo versions**

Run:
```bash
cd generated-projects/premium-verification
npx create-expo-app@latest app-reference --template blank-typescript --yes
cd app-reference && node -e "const p=require('./package.json');console.log(JSON.stringify({dependencies:p.dependencies,devDependencies:p.devDependencies},null,2))"
```
Record the exact versions in `MOBILE_DEPENDENCIES` in `mobile_app_engine.py`.
Baseline from npm at plan time: Expo `~58.0.20`, React Native `0.88.1`,
expo-router `~58.0.27`, expo-secure-store `~58.0.2`, async-storage `3.1.1`,
react-native-sse `1.2.1`. Remove the scratch project afterwards.

- [ ] **Step 2: Write failing generator tests**

```python
def test_mobile_project_has_auth_records_feed_and_offline_queue(tmp_path):
    design = build_design("Northstar", "saas", "#2563eb", "#0d9488")
    result = generate_mobile_app(
        str(tmp_path), "Northstar", "saas", design,
        {"web": "none", "pwa": False, "mobile": {"platforms": ["android"],
         "verification": "apk_emulator"}},
        api_base="https://api.example.test/api/v1",
    )
    assert result["success"] is True, result
    files = set(result["files"])
    for relative in (
        "mobile/app.json", "mobile/package.json", "mobile/tsconfig.json",
        "mobile/app/_layout.tsx", "mobile/app/(auth)/sign-in.tsx",
        "mobile/app/(auth)/register.tsx", "mobile/app/(tabs)/_layout.tsx",
        "mobile/app/(tabs)/index.tsx", "mobile/app/(tabs)/records.tsx",
        "mobile/app/(tabs)/settings.tsx", "mobile/app/record/[id].tsx",
        "mobile/app/record/new.tsx", "mobile/src/api/client.ts",
        "mobile/src/auth/AuthContext.tsx", "mobile/src/realtime/useRecordFeed.ts",
        "mobile/src/offline/queue.ts", "mobile/src/theme.ts",
        "mobile/.maestro/smoke.yaml", "mobile/.maestro/records.yaml",
    ):
        assert relative in files
    package = json.loads((tmp_path / "mobile/package.json").read_text())
    assert package["dependencies"]["expo"].startswith("~58")
    assert "expo-router" in package["dependencies"]
    assert "react-native-sse" in package["dependencies"]
    assert "@react-native-async-storage/async-storage" in package["dependencies"]
    app = json.loads((tmp_path / "mobile/app.json").read_text())
    assert app["expo"]["android"]["package"] == "com.lumicore.northstar"
    assert "api.example.test" in (tmp_path / "mobile/src/api/client.ts").read_text()

def test_mobile_release_requires_https():
    with pytest.raises(ValueError):
        generate_mobile_app(".", "North", "saas", design,
                            {"web": "none", "mobile": {"platforms": ["android"],
                             "verification": "apk_emulator"}},
                            api_base="http://api.example.test")
```

- [ ] **Step 3: Run red**

Expected: module missing.

- [ ] **Step 4: Implement the emitter**

Emit every file in the spec §7 list with:
- `expo-secure-store` token storage and 401 sign-out.
- `react-native-sse` feed with 15 s polling fallback and foreground resume via
  `AppState`.
- Offline queue `AsyncStorage`, max 50, sequential flush, client UUID, no success
  before server confirmation.
- Theme from `design`; icons/splash generated with Pillow (1024×1024,
  1024×1024, 1284×2778) under `mobile/assets/`.
- `app.json` package id `com.lumicore.<slug>`; orientation portrait; scheme slug.
- Maestro flows with exact assertions from spec §7.4.
- README: start commands, API base, emulator `10.0.2.2`, no secrets.
- Reject non-HTTPS `api_base` unless host is `10.0.2.2`/`localhost`.

- [ ] **Step 5: Integrate the generation stage**

In `generate_project`:
- Determine `app = contract.get("app")`.
- `web == "none"` → do not call `_build_frontend_files`; do not create
  `frontend/`.
- After `file_write` succeeds and before AI kit, when `app.mobile`:
  `stage = "mobile_generate"`; call `generate_mobile_app(dest, ...)`; on failure
  raise so `failed_stage == "mobile_generate"`; extend `generation_steps`.
- Write `app-contract.json` with the normalized app block (no secrets).
- Make `apply_production_spec` skip all frontend sections when
  `frontend/src` is absent; backend sections still run.
- Artifacts validator accepts `web_surface` and `mobile`:
  - web none: no frontend requirement; `backend/` + `app-contract.json` required.
  - mobile: mobile files + package dependencies + Maestro files required.

- [ ] **Step 6: Add generation tests**

```python
def test_app_only_generation_has_no_frontend_and_a_mobile_app(tmp_path):
    contract = resolve_generation_contract({"prompt": "Build a records app"})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt="Build a records app", brand_name="Northstar",
        generation_contract=contract)
    assert result["success"] is True, result
    assert not (tmp_path / "frontend").exists()
    assert (tmp_path / "mobile/package.json").is_file()
    assert (tmp_path / "mobile/.maestro/records.yaml").is_file()
    assert (tmp_path / "backend/routes/records.routes.js").is_file()
    contract_file = json.loads((tmp_path / "app-contract.json").read_text())
    assert contract_file["web"] == "none"
    assert contract_file["mobile"]["verification"] == "apk_emulator"

def test_web_and_app_generation_has_both_surfaces(tmp_path):
    contract = resolve_generation_contract({"prompt": "Build a website and app"})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt="Build a website and app", brand_name="Northstar",
        generation_contract=contract)
    assert result["success"] is True, result
    assert (tmp_path / "frontend/src/App.jsx").is_file()
    assert (tmp_path / "mobile/package.json").is_file()
```

- [ ] **Step 7: Run green and checkpoint**

Run mobile engine + generation suites. Do not commit.

---

### Task 6: Android toolchain check/install

**Files:**
- Create: `ai-agent/agent/android_toolchain.py`
- Modify: `ai-agent/main.py` (`--android-toolchain`)
- Test: `ai-agent/tests/test_android_toolchain.py`

**Interfaces:**
- `check_environment(*, root=None, env=None) -> {ready, java17, java_home, sdk, adb, emulator, avd, maestro, gradle_home, disk_free_gb, missing}`.
- `install_toolchain(root="D:/android-sdk", *, accept_licenses=False, progress=None) -> dict`.
- `toolchain(env=None) -> {ready, java_home, sdk, adb, emulator, avd, maestro, gradle_home}` used by mobile verification.
- Constants for JDK/SDK/AVD/Maestro/Gradle paths and Android 35 packages.

- [ ] **Step 1: Write failing check tests**

```python
def test_check_reports_every_missing_piece(monkeypatch, tmp_path):
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("JAVA_HOME", raising=False)
    report = android_toolchain.check_environment(root=str(tmp_path / "sdk"),
                                                 env={})
    assert report["ready"] is False
    assert report["missing"]
    assert "java17" in report["missing"]
    assert "sdk" in report["missing"]
    assert "emulator" in report["missing"]

def test_install_refuses_without_license_flag(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(android_toolchain, "_download", lambda *a, **k: called.append("download"))
    result = android_toolchain.install_toolchain(str(tmp_path), accept_licenses=False)
    assert result["ok"] is False
    assert "accept" in result["error"].lower()
    assert called == []
```

- [ ] **Step 2: Run red**

Expected: module missing.

- [ ] **Step 3: Implement**

- `check_environment`: resolve `ANDROID_HOME` or `D:/android-sdk`; JDK 17 check via
  `bin/java.exe -version`; adb/emulator/sdkmanager files; AVD via
  `emulator -list-avds`; Maestro path; disk free via `shutil.disk_usage`.
- `install_toolchain`: disk ≥14 GB, `accept_licenses` required, official URLs only,
  ZIP integrity, `sdkmanager --sdk_root=<root> --licenses` and packages, AVD
  `lumicore_api35`, Maestro extract, `emulator -accel-check`; returns report and
  writes `ai-agent/.env.android` with paths (no secrets).
- Downloads/commands go through injectable helpers `_download`, `_run` for tests.
- CLI `--android-toolchain check|install`; install without `--accept-licenses`
  exits non-zero with instructions.

- [ ] **Step 4: Run green and real check**

Run tests, then `py ai-agent/main.py --android-toolchain check --factory-json`.
The background bootstrap may still be running; check must report the truth.

- [ ] **Step 5: Checkpoint**

Do not commit.

---

### Task 7: Mobile export, APK and emulator verification

**Files:**
- Create: `ai-agent/agent/mobile_verify.py`
- Create: `ai-agent/agent/mobile_fixture_api.py`
- Test: `ai-agent/tests/test_mobile_verify.py`
- Test: `ai-agent/tests/test_mobile_fixture_api.py`

**Interfaces:**
- `export_mobile(project_dir, *, run=_run, timeout=1800) -> {ok, status, steps, errors}`.
- `build_apk(project_dir, toolchain, *, run=_run, timeout=3600) -> {ok, status, apk, sha256, package, min_sdk, errors}`.
- `verify_emulator(project_dir, apk, *, toolchain, api_url="", tier="app_runs", run=_run, evidence_dir="") -> {ok, tier, booted, installed, launched, logcat_clean, maestro, screenshots, failures}`.
- Fixture API `start_fixture_api(port=0) -> (server, base_url)` with `/api/v1/health`, `/auth/register`, `/auth/login`, `/records`, `/events`.

- [ ] **Step 1: Write failing export/APK tests**

```python
def test_export_runs_expo_export_and_typescript(tmp_path):
    calls = []
    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        return {"ok": True, "code": 0, "stdout_tail": "", "stderr_tail": "", "elapsed_ms": 1}
    (tmp_path / "mobile").mkdir()
    report = mobile_verify.export_mobile(str(tmp_path), run=run)
    assert report["ok"] is True
    assert any("expo" in part and "export" in " ".join(cmd) for cmd in calls)
    assert any("tsc" in " ".join(cmd) for cmd in calls)

def test_apk_missing_output_fails(tmp_path):
    def run(cmd, cwd, timeout=900, env=None):
        return {"ok": True, "code": 0, "stdout_tail": "", "stderr_tail": "", "elapsed_ms": 1}
    report = mobile_verify.build_apk(str(tmp_path), {"java_home": "x", "sdk": "y",
                                                     "ready": True}, run=run)
    assert report["ok"] is False
    assert "APK" in report["message"]

def test_emulator_requires_a_real_package_launch(tmp_path):
    calls = []
    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if "logcat" in cmd:
            return {"ok": True, "code": 0, "stdout_tail": "FATAL EXCEPTION: main",
                    "stderr_tail": "", "elapsed_ms": 1}
        return {"ok": True, "code": 0, "stdout_tail": "ok", "stderr_tail": "", "elapsed_ms": 1}
    report = mobile_verify.verify_emulator(
        str(tmp_path), str(tmp_path / "app-debug.apk"),
        toolchain={"ready": True, "adb": "adb", "emulator": "emulator",
                   "avd": "lumicore_api35", "maestro": "maestro"},
        run=run, evidence_dir=str(tmp_path / "evidence"))
    assert report["ok"] is False
    assert report["logcat_clean"] is False
```

- [ ] **Step 2: Run red**

Expected: modules missing.

- [ ] **Step 3: Implement export and APK build**

- `export_mobile`: run `npm install` in `mobile/` only when dependencies are
  missing (same manifest check as `build_project`), `npx expo export --platform
  all` (fallback to three separate exports only if the installed CLI rejects
  `all`), `npx tsc --noEmit`; require
  `mobile/dist` bundles; capture bounded tails; never install anything system-level.
- `build_apk`: check toolchain `ready`; env `JAVA_HOME`, `ANDROID_HOME`,
  `ANDROID_SDK_ROOT`, `GRADLE_USER_HOME`; `npx expo prebuild --platform android
  --no-install`; `gradlew.bat assembleDebug`; verify APK path, SHA-256, and
  `aapt dump badging` package/minSdk; bounded output.

- [ ] **Step 4: Implement emulator verification**

- Start emulator headless: `-avd <avd> -no-window -no-audio -no-snapshot
  -gpu swiftshader_indirect -accel auto`; poll `adb shell getprop
  sys.boot_completed` up to 240 s.
- `adb install -r`; `adb shell am start -n <package>/.MainActivity`; wait 5 s.
- `adb logcat -d -v brief`; fail on `FATAL EXCEPTION`, `ANR in`, package crash.
- API tier: `full_stack` requires `api_url`; the Maestro register→create→list
  journey proves the app can reach the hosted API (no `adb shell curl` assumption).
  `app_runs` starts the fixture API on loopback and builds the APK with the
  emulator origin `http://10.0.2.2:<port>/api/v1`.
- Run Maestro:
  `maestro test .maestro/smoke.yaml` and `records.yaml` with env email/password;
  require zero failures; copy screenshots and result JSON into evidence.
- Evidence: `apk.json`, `emulator.json`, `maestro/`, `health.json`; never include
  tokens/passwords.

- [ ] **Step 5: Implement the fixture API**

Loopback-only HTTP server:
- `POST /api/v1/auth/register` and `/login` → token + user.
- `GET/POST /api/v1/records`, `GET/PUT/DELETE /api/v1/records/:id`.
- `GET /api/v1/events` → SSE ready frame.
- In-memory only, per-run, max 100 records; labeled test-only in the report.
- Tests use `http.client` against a real ephemeral port.

- [ ] **Step 6: Run green**

Run both suites. Real emulator test is opt-in:
`SCENE_BROWSER_TEST`-style env `MOBILE_EMULATOR_TEST=1` must fail, not skip, when
requested without toolchain.

- [ ] **Step 7: Checkpoint**

Do not commit.

---

### Task 8: Factory conditional stages and delivery rules

**Files:**
- Modify: `ai-agent/agent/factory_pipeline.py`
- Test: `ai-agent/tests/test_factory_pipeline.py`
- Test: `ai-agent/tests/test_app_delivery.py` (new)

**Interfaces:**
- `read_app_contract(project_dir) -> {"web","pwa","mobile"} | None`; missing file
  means legacy website.
- `run_factory` stages exactly the requested surfaces; report gains
  `stages.pwa`, `stages.mobile_export`, `stages.mobile_apk`,
  `stages.mobile_emulator`, `mobile_tier`.

- [ ] **Step 1: Write failing surface-stage tests**

```python
def _app_only_project(tmp_path):
    project = tmp_path / "app"
    (project / "backend").mkdir(parents=True)
    (project / "backend/package.json").write_text("{}", encoding="utf-8")
    (project / "backend/server.js").write_text("", encoding="utf-8")
    (project / "app-contract.json").write_text(json.dumps({
        "version": 1, "web": "none", "pwa": False,
        "mobile": {"platforms": ["android"], "verification": "apk_emulator"},
    }), encoding="utf-8")
    return project

def test_app_only_skips_web_build_qa_and_frontend_deploy(tmp_path):
    project = _app_only_project(tmp_path)
    with patch.object(factory, "build_project", side_effect=AssertionError("web build")), \
         patch.object(factory, "run_qa", side_effect=AssertionError("web qa")), \
         patch.object(factory, "test_backend", return_value={"ok": True}), \
         patch.object(factory, "_host_database", return_value=({"status": "created"}, "postgres://x")), \
         patch.object(factory, "_host_api", return_value={"status": "live", "url": "https://api.test"}), \
         patch.object(factory, "_prove_api", return_value={"ok": True}), \
         patch("agent.mobile_verify.export_mobile", return_value={"ok": True}), \
         patch("agent.mobile_verify.build_apk", return_value={"ok": True, "apk": "a.apk"}), \
         patch("agent.mobile_verify.verify_emulator",
               return_value={"ok": True, "tier": "full_stack"}):
        result = factory.run_factory(str(project), video=False, deploy="vercel",
                                     api_url="", api_health="")
    self.assertNotIn("build", result["stages"])
    self.assertNotIn("qa", result["stages"])
    self.assertIn("mobile_emulator", result["stages"])
    self.assertEqual(result["status"], "delivered", result.get("failures"))

def test_missing_toolchain_blocks_mobile_delivery(tmp_path):
    project = _app_only_project(tmp_path)
    with patch.object(factory, "test_backend", return_value={"ok": True}), \
         patch("agent.mobile_verify.export_mobile", return_value={"ok": True}), \
         patch("agent.mobile_verify.build_apk", return_value={
             "ok": False, "status": "blocked", "message": "Android toolchain missing"}):
        result = factory.run_factory(str(project), video=False, deploy="none")
    self.assertEqual(result["status"], "partial")
    self.assertTrue(any("toolchain" in f.lower() for f in result["failures"]))
```

- [ ] **Step 2: Run red**

Expected: `run_factory` still builds a frontend / has no mobile stages.

- [ ] **Step 3: Implement conditional stages**

- At start, `app = read_app_contract(project_dir)`; `web = app.get("web", "website")`;
  `mobile = app.get("mobile")`; `pwa = bool(app.get("pwa"))`.
- `web != "none"`: existing build → backend tests → qa → optional pwa → deploy →
  live_qa.
- `web == "none"`: backend tests → database/api/handshake; no build/qa/deploy
  frontend; `deployment = {"status": "api-only", "url": api_url,
  "verified": bool(api live and handshake)}`.
- `mobile`: after API/handshake, run export → apk → emulator; failures append and
  status becomes `partial`/`failed`; missing toolchain `blocked`.
- `mobile.verification == "none"`: run export only; `mobile_tier = "not_verified"`;
  final status at most `partial`.
- `pwa` requested but web none → contract validation already rejects.
- Keep all existing database/auth/tenant/realtime/video blockers.
- Handoff: list web URL (if any), API, DB, browser evidence, APK hash/path, mobile
  tier, Maestro result, test account note; list skipped surfaces with reasons.
- `_write_report` stage list handles `api-only` as verified only when evidence says so.

- [ ] **Step 4: Add gate tests**

- app-only with web build patched to explode: pass.
- web+app runs both web and mobile stages in order.
- mobile export failure blocks delivery.
- mobile emulator failure blocks delivery.
- PWA failure blocks delivery when requested.
- no app-contract file keeps legacy behavior (existing suites).
- mobile verification none cannot be `delivered`.

- [ ] **Step 5: Run green**

Run factory + app delivery suites. Do not commit.

---

### Task 9: Real representatives, evidence and documentation

**Files:**
- Modify: `AGENTS.md`, `CHANGELOG.md`, `docs/FACTORY.md`
- Add evidence under `generated-projects/premium-verification/`
- Test: focused suites plus opt-in real browser/mobile runs

- [ ] **Step 1: Generate and verify web-only**

Use a normal website prompt. Build, run browser QA, confirm 7 routes × 5 widths.
This proves the default lane is unchanged.

- [ ] **Step 2: Generate and verify web-app + PWA**

Generate `web_app` with PWA, build, run browser QA and the PWA offline/queue
proof. Capture screenshots of login, dashboard, records and offline page. Record
`qa/qa-report.json`.

- [ ] **Step 3: Generate and verify web + app**

Generate “website and app”. Build the web surface and run QA; run
`expo export` and TypeScript; build the debug APK; boot `lumicore_api35`, install,
launch, scan logcat and run Maestro. If a hosted API+DB is available, use
`full_stack`; otherwise record the labeled `app_runs` tier and do **not** claim
`delivered`.

- [ ] **Step 4: Generate and verify app-only**

Confirm no `frontend/` exists. Run backend tests, export/APK/emulator. Confirm the
report has no web URL and no browser QA stage. Delivery only with `full_stack`.

- [ ] **Step 5: Negative fixtures**

- Mobile prompt with toolchain missing → `blocked`, no APK path.
- Web+app with mobile export error → `partial`/`failed`.
- PWA requested with broken worker → PWA stage fails.
- App-only with no API/DB → cannot be `delivered`.
- Website prompt never generates `mobile/`; app-only never generates `frontend/`.

- [ ] **Step 6: Documentation and permanent rules**

- `AGENTS.md`: surface routing table, app-only stage rules, idempotent record id,
  APK/emulator fail-closed rules, no automatic toolchain install, iOS limitation.
- `CHANGELOG.md`: new version row with exact evidence and honest limitations.
- `docs/FACTORY.md`: modes, CLI examples, toolchain install, mobile evidence,
  verification tiers, failure statuses.
- Update `docs/MIGRATION_EXIT_PATH.md` only if it claims a mobile scaffold that now
  exists (do not claim iOS/store support).

- [ ] **Step 7: Full affected verification**

Run all affected suites (contract, app layouts, PWA, mobile engine, toolchain,
mobile verify, factory, premium generation, browser QA, existing fullstack/schema/
spec). Real Chromium and emulator runs as required by the selected representatives.
Record pass counts and failures. Do not run unrelated repository suites unless
requested.

- [ ] **Step 8: Independent review**

Package the production diff and review it. Fix confirmed Critical/Important issues,
rerun covering tests, then request a scoped re-review. Do not commit or deploy.

## Execution record

- Task 1: pending
- Task 2: pending
- Task 3: pending
- Task 4: pending
- Task 5: pending
- Task 6: pending (background toolchain bootstrap started 2026-10-28)
- Task 7: pending
- Task 8: pending
- Task 9: pending

Ruling: no commit steps are permitted because the user has not authorized a commit
in this slice. Each checkpoint requires a green focused suite and a written record.

Ruling: browser QA for authenticated app routes uses bounded API fixtures and a
test token; it proves rendering, states and PWA behavior, not the real backend. The
real backend remains proven by the factory handshake and the mobile `full_stack`
journey.

Ruling: app-only builds skip the web pipeline entirely; `delivered` requires a
verified API+DB and a `full_stack` mobile journey. A fixture-API run is `app_runs`
and can never be reported as full-stack.
