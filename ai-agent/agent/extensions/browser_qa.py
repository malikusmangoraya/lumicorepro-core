"""Fail-closed, built-output browser evidence for public route/viewport matrices.

Python Playwright is required for a verdict. CLI screenshots are partial evidence
only. Local and hosted evidence are persisted separately. A requested 3D scene is
proven from rendered canvas pixels and interaction-induced change, never markers.
"""
import hashlib
import io
import json
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote, unquote, urlsplit, urlunsplit


VIEWPORTS = ((375, 812), (768, 900), (1024, 900), (1440, 900), (1920, 1080))
MAX_DIAGNOSTICS = 20
MAX_FIXTURES = 100
REQUIRED_RESOURCES = {'document', 'script', 'stylesheet', 'image', 'font', 'media'}
FIXTURE_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}
CORS_HEADERS = {
    'access-control-allow-origin': '*',
    'access-control-allow-headers': 'authorization,content-type',
    'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    'cache-control': 'no-store',
}


def _safe_path(path):
    """Reject ambiguous/Windows paths before resolving anything on disk."""
    decoded = unquote(path, errors='strict')
    if (not decoded.startswith('/') or decoded.startswith('//')
            or any(c in decoded for c in ('\\', ':', '%', '?', '#'))
            or any(ord(c) < 32 or ord(c) == 127 for c in decoded)
            or any(part.startswith('.') for part in decoded.split('/') if part)):
        raise ValueError('Invalid path')
    return decoded


def _route(route):
    if not isinstance(route, str) or not route or len(route) > 2048:
        raise ValueError('Invalid route')
    parsed = urlsplit(route)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or '?' in route or '#' in route:
        raise ValueError('Invalid route')
    # Encoded aliases must not create duplicate requested matrix keys.
    if quote(_safe_path(route), safe='/@-._~') != route:
        raise ValueError('Noncanonical route')
    return route


def _viewport_key(viewport):
    if not isinstance(viewport, dict) or set(viewport) != {'width', 'height'}:
        raise ValueError('Invalid viewport')
    key = (viewport['width'], viewport['height'])
    if any(type(n) is not int or not 0 < n <= 10000 for n in key):
        raise ValueError('Invalid viewport')
    return key


def _auth_storage(auth):
    """Validate test-only localStorage storage; values are opaque strings."""
    if auth is None:
        return {}
    if not isinstance(auth, dict) or set(auth) - {'storage'}:
        raise ValueError('Invalid QA auth contract')
    storage = auth.get('storage', {})
    if not isinstance(storage, dict) or len(storage) > 20:
        raise ValueError('Invalid QA auth contract')
    normalized = {}
    for key, value in storage.items():
        if (not isinstance(key, str) or not 0 < len(key) <= 64
                or any(c in key for c in ('\x00', '\n', '\r'))
                or not isinstance(value, str) or len(value) > 4096):
            raise ValueError('Invalid QA auth contract')
        normalized[key] = value
    return normalized


def _fixtures(fixtures):
    """Validate bounded `METHOD /path` fixtures and serialize their bodies once."""
    if fixtures is None:
        return {}
    if not isinstance(fixtures, dict) or len(fixtures) > MAX_FIXTURES:
        raise ValueError('Invalid QA fixtures')
    normalized = {}
    for key, value in fixtures.items():
        if not isinstance(key, str) or len(key) > 1024:
            raise ValueError('Invalid QA fixture key')
        method, separator, path = key.partition(' ')
        method = method.upper()
        if (not separator or method not in FIXTURE_METHODS
                or not path.startswith('/') or len(path) > 1024
                or any(c.isspace() for c in path)
                or any(c in path for c in ('\\', '?', '#', '\x00'))
                or (method, path) in normalized):
            raise ValueError('Invalid QA fixture key')
        try:
            body = json.dumps(value, ensure_ascii=True, allow_nan=False)
        except (TypeError, ValueError):
            raise ValueError('Invalid QA fixture body') from None
        if len(body.encode('utf-8')) > 1024 * 1024:
            raise ValueError('QA fixture body is too large')
        normalized[(method, path)] = body
    return normalized


def _api_path(url):
    """Return the `/api/v1` suffix of a request URL, never the origin or query."""
    parsed = urlsplit(url)
    marker = '/api/v1'
    index = parsed.path.find(marker)
    if index < 0:
        return None
    suffix = parsed.path[index + len(marker):] or '/'
    if not suffix.startswith('/'):
        return None
    return suffix


def _png_evidence(path):
    """Verify signature, PNG structure and decoded pixels, not just file existence."""
    result = {'ok': False, 'path': str(path)}
    try:
        from PIL import Image
        path = Path(path)
        size = path.stat().st_size
        if not 0 < size <= 50 * 1024 * 1024:
            return result
        with path.open('rb') as stream:
            if stream.read(8) != b'\x89PNG\r\n\x1a\n':
                return result
        with Image.open(path) as image:
            width, height = image.size
            if image.format != 'PNG' or not 0 < width * height <= 50_000_000:
                return result
            image.verify()
        with Image.open(path) as image:
            image.load()
        result.update(ok=True, width=width, height=height, bytes=size)
    except Exception:
        # Filenames, decoder exceptions and image metadata may contain secrets.
        pass
    return result


def _captures_named_by(report):
    """PNG names the report cites, wherever they appear in it.

    Ownership comes from the report instead of a filename pattern, so a capture kind
    added later (scene, PWA, interaction) is kept by a run that measured it and pruned
    by a run that did not.
    """
    names = set()

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and node.lower().endswith('.png'):
            names.add(Path(node).name)

    walk(report)
    return names


def _canvas_evidence(png_bytes):
    """Decoded pixels, not attributes: size, variation and opaque coverage."""
    result = {'ok': False, 'width': 0, 'height': 0, 'colors': 0, 'deviation': 0.0,
              'coverage': 0.0}
    try:
        from PIL import Image, ImageStat
        with Image.open(io.BytesIO(png_bytes)) as image:
            image.load()
            rgba = image.convert('RGBA')
            width, height = rgba.size
            gray = rgba.convert('L')
            deviation = float(ImageStat.Stat(gray).stddev[0])
            alpha = rgba.getchannel('A')
            coverage = sum(alpha.histogram()[1:]) / float(width * height)
            render = rgba.convert('RGB')
            colors = render.getcolors(maxcolors=1_000_000) or []
        result.update(width=width, height=height, colors=len(colors),
                      deviation=round(deviation, 2), coverage=round(coverage, 3))
        result['ok'] = (width >= 100 and height >= 100 and deviation > 4.0
                        and coverage > 0.05 and len(colors) > 8)
    except Exception:
        pass
    return result


def _canvas_changed(first, second, *, minimum=0.002):
    """Fraction of pixels that visibly changed between two captures."""
    try:
        from PIL import Image, ImageChops
        with Image.open(io.BytesIO(first)) as a, Image.open(io.BytesIO(second)) as b:
            left, right = a.convert('RGBA'), b.convert('RGBA')
            if left.size != right.size:
                return 1.0
            mask = ImageChops.difference(left, right).convert('L').point(
                lambda value: 255 if value > 8 else 0)
            changed = sum(count for count, value in mask.getcolors(maxcolors=1_000_000)
                          if value == 255)
            return changed / float(left.width * left.height)
    except Exception:
        return 0.0


def evidence_passes(report):
    """Validate an exact unique matrix and readable captures, independent of status.

    Screenshot paths are absolute local evidence paths. Reports moved to another
    machine without their screenshots deliberately cannot satisfy this consumer.
    """
    try:
        if not isinstance(report, dict) or report.get('ok') is not True:
            return False
        if report.get('status') != 'passed' or report.get('failures') != []:
            return False
        routes = report['requested_routes']
        viewports = report['requested_viewports']
        results = report['results']
        if not all(isinstance(v, list) and v for v in (routes, viewports, results)):
            return False
        route_keys = [_route(r) for r in routes]
        viewport_keys = [_viewport_key(v) for v in viewports]
        if len(set(route_keys)) != len(routes) or len(set(viewport_keys)) != len(viewports):
            return False
        expected = {(r, *v) for r in route_keys for v in viewport_keys}
        seen = set()
        captures = set()
        for result in results:
            key = (_route(result['route']), *_viewport_key(result['requested_viewport']))
            if key in seen or key not in expected:
                return False
            seen.add(key)
            if (_viewport_key(result['actual_viewport']) != key[1:]
                    or result.get('ok') is not True or result.get('failures') != []):
                return False
            content = result['rendered_content']
            if any(content.get(k) is not True for k in ('ok', 'main_visible', 'heading_matched')):
                return False
            if any(result.get(k) != [] for k in ('console_errors', 'page_errors', 'network_errors')):
                return False
            overflow = result['overflow']
            if overflow.get('overflow') is not False or overflow.get('offenders') != []:
                return False
            shot = result['screenshot']
            if shot.get('ok') is not True or not isinstance(shot.get('path'), str):
                return False
            path = Path(shot['path'])
            if not path.is_absolute() or path.resolve() in captures:
                return False
            decoded = _png_evidence(path)
            # A capture that is not as wide as the requested viewport, or shorter
            # than it, cannot prove that width was actually rendered full-page.
            if (not decoded['ok'] or decoded['width'] != key[1]
                    or decoded['height'] < key[2]):
                return False
            captures.add(path.resolve())
            reduced = result['reduced_motion']
            if (reduced.get('ok') is not True or reduced.get('media_matches') is not True
                    or _viewport_key(reduced['actual_viewport']) != key[1:]
                    or reduced['overflow'].get('overflow') is not False
                    or reduced['overflow'].get('offenders') != []
                    or any(reduced['rendered_content'].get(k) is not True
                           for k in ('ok', 'main_visible', 'heading_matched'))):
                return False
        if report.get('requested_scene') is not None:
            scene = report.get('scene')
            if not isinstance(scene, dict) or scene.get('ok') is not True:
                return False
            if scene.get('state') != 'rendered' or scene.get('failures') != []:
                return False
            if not (scene.get('frames') or 0) >= 1 or not (scene.get('draw_calls') or 0) >= 1:
                return False
            if (scene.get('canvas') or {}).get('ok') is not True:
                return False
            if (scene.get('interaction') or {}).get('changed') is not True:
                return False
            if (scene.get('mobile_fallback') or {}).get('ok') is not True:
                return False
        if report.get('requested_pwa'):
            pwa = report.get('pwa')
            if not isinstance(pwa, dict) or pwa.get('ok') is not True:
                return False
            if pwa.get('failures') != [] or pwa.get('worker_controlled') is not True:
                return False
            if (not isinstance(pwa.get('offline_heading'), str)
                    or not pwa['offline_heading'].strip()
                    or pwa.get('online_recovered') is not True):
                return False
            queue = pwa.get('queue')
            if not isinstance(queue, dict):
                return False
            if queue.get('applicable') is not False:
                if queue.get('posts') != 1 or queue.get('cleared') is not True:
                    return False
                client_id = queue.get('client_id')
                if (not isinstance(client_id, str)
                        or queue.get('post_ids') != [client_id]):
                    return False
                # The real shipped queue must enforce its documented cap,
                # survive an unconfirmed flush, and never render success UI
                # before the server accepted the record.
                if queue.get('enqueued') != 1:
                    return False
                if queue.get('max_records') != 50 or queue.get('max_enforced') is not True:
                    return False
                if queue.get('retry_attempts') != 3 or queue.get('failed_flush_kept') is not True:
                    return False
                if queue.get('no_success_before_confirmation') is not True:
                    return False
        return seen == expected
    except (KeyError, TypeError, ValueError, AttributeError, OSError):
        return False


class _PreviewHandler(SimpleHTTPRequestHandler):
    """Serve one distribution, never sources, hidden files or directory listings."""

    def __init__(self, *args, roots=None, **kwargs):
        self._root = Path(roots[0]).resolve()
        super().__init__(*args, **kwargs)

    def send_head(self):
        try:
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc:
                raise ValueError('Invalid request path')
            path = _safe_path(parsed.path)
            candidate = (self._root / path.lstrip('/')).resolve()
            candidate.relative_to(self._root)
            if path == '/':
                candidate = self._root / 'index.html'
            elif candidate.is_dir():
                raise ValueError('Directory listing denied')
            elif not candidate.is_file() and '.' not in path.rsplit('/', 1)[-1]:
                candidate = self._root / 'index.html'
            candidate = candidate.resolve()
            candidate.relative_to(self._root)
            stream = candidate.open('rb')
        except (ValueError, OSError, UnicodeError):
            self.send_error(404, 'Not found')
            return None
        self.send_response(200)
        self.send_header('Content-type', self.guess_type(str(candidate)))
        self.send_header('Content-Length', str(candidate.stat().st_size))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        return stream

    def log_message(self, *args, **kwargs):
        pass


# No DOM strings/classes/attributes are returned: those may contain user payloads.
_DOM_EVIDENCE = r"""(heading) => {
  const visible = (el, checkClipping = false) => {
    if (!el || !el.getClientRects().length) return false;
    const r = el.getBoundingClientRect();
    let left = r.left, right = r.right, top = r.top, bottom = r.bottom;
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.display === 'none' || s.visibility !== 'visible' || Number(s.opacity) === 0
          || p.hidden || p.getAttribute('aria-hidden') === 'true') return false;
      // A clipped heading cannot independently prove visible page identity.
      if (checkClipping && (s.clipPath !== 'none' || s.clip !== 'auto')) return false;
      if (checkClipping && p !== el) {
        const pr = p.getBoundingClientRect();
        if (s.overflowX !== 'visible') { left = Math.max(left, pr.left); right = Math.min(right, pr.right); }
        if (s.overflowY !== 'visible') { top = Math.max(top, pr.top); bottom = Math.min(bottom, pr.bottom); }
      }
    }
    return right > left && bottom > top && (!checkClipping || (right > 0 && left < innerWidth));
  };
  const normalize = value => value.replace(/\s+/g, ' ').trim();
  const mains = [...document.querySelectorAll('main, [role="main"]')].filter(el => visible(el, true));
  const mainVisible = mains.some(el => normalize(el.innerText || '').length > 0);
  // Any heading inside main is page content. A hero may legitimately use a
  // <header> element inside main, so only the main container itself bounds it.
  const matched = typeof heading === 'string' && heading.trim().length > 0 && mains.some(main =>
    [...main.querySelectorAll('h1,h2,h3,h4,h5,h6,[role="heading"]')].some(el =>
      visible(el, true) && normalize(el.innerText || '') === normalize(heading)));
  // A visually hidden helper (clip rect 0 / inset 50%) cannot cause visible
  // overflow. Body-level clipping must NOT exempt real layout overflow.
  const fullyClipped = (el) => {
    const s = getComputedStyle(el);
    if (s.clipPath && s.clipPath !== 'none' && /inset\(\s*50%/.test(s.clipPath)) return true;
    if (s.clip && s.clip !== 'auto') {
      const match = s.clip.match(/rect\(([^)]+)\)/);
      if (match) {
        const values = match[1].split(/[ ,]+/).map(value => parseFloat(value));
        if (values.length === 4 && (values[0] >= values[2] || values[1] <= values[3])) {
          return true;
        }
      }
    }
    return false;
  };
  const width = window.innerWidth;
  const offenders = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el) || fullyClipped(el)) continue;
    const box = el.getBoundingClientRect();
    const r = {left: box.left, right: box.right};
    // Text can paint outside a correctly sized box without any wide child element.
    if (!['auto', 'scroll'].includes(getComputedStyle(el).overflowX)) {
      for (const node of el.childNodes) {
        if (node.nodeType !== Node.TEXT_NODE || !node.textContent.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(node);
        for (const rect of range.getClientRects()) {
          r.left = Math.min(r.left, rect.left); r.right = Math.max(r.right, rect.right);
        }
      }
    }
    if (r.right <= width + 1 && r.left >= -1) continue;
    let contained = false;
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const s = getComputedStyle(p), pr = p.getBoundingClientRect();
      if (['auto', 'scroll'].includes(s.overflowX) && pr.left >= -1 && pr.right <= width + 1) {
        contained = true; break;
      }
    }
    if (!contained && offenders.length < 8)
      offenders.push({tag: el.tagName, left: Math.round(r.left), right: Math.round(r.right)});
  }
  const nav = performance.getEntriesByType('navigation')[0];
  return {
    actual_viewport: {width, height: window.innerHeight},
    rendered_content: {ok: mainVisible && matched, main_visible: mainVisible,
                       heading_matched: matched},
    overflow: {overflow: offenders.length > 0, offenders},
    performance: {dom_ms: nav && nav.domContentLoadedEventEnd > 0
                  ? Math.round(nav.domContentLoadedEventEnd) : null, lcp_ms: null}
  };
}"""

_READINESS = """async () => {
  await Promise.race([document.fonts.ready, new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Fonts readiness timeout')), 2000))]);
  await Promise.race([new Promise(resolve => requestAnimationFrame(() =>
    requestAnimationFrame(resolve))), new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Layout readiness timeout')), 2000))]);
}"""

_TRIGGER_LAZY = """async () => {
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  const step = Math.max(240, Math.round(window.innerHeight * 0.8));
  const height = Math.max(document.documentElement.scrollHeight,
                          document.body ? document.body.scrollHeight : 0);
  for (let y = 0; y < height; y += step) {
    window.scrollTo(0, y);
    await pause(30);
  }
  window.scrollTo(0, 0);
  await pause(30);
}"""

_QUEUE_OPEN_JS = """const openQueue = () => new Promise((resolve, reject) => {
  const request = indexedDB.open('lumicore-queue', 2);
  request.onupgradeneeded = () => {
    const database = request.result;
    if (database.objectStoreNames.contains('records')) {
      database.deleteObjectStore('records');
    }
    database.createObjectStore('records', { keyPath: ['owner', 'id'] });
  };
  request.onsuccess = () => resolve(request.result);
  request.onerror = () => reject(request.error);
});"""

_QUEUE_ROWS_JS = """async () => {
  %s
  const database = await openQueue();
  return await new Promise((resolve, reject) => {
    const request = database
      .transaction('records', 'readonly')
      .objectStore('records')
      .getAll();
    request.onsuccess = () => resolve((request.result || []).map((record) => ({
      id: String(record.id || ''),
      owner: String(record.owner || ''),
    })));
    request.onerror = () => reject(request.error);
  });
}""" % _QUEUE_OPEN_JS

_QUEUE_CLEAR_JS = """async () => {
  %s
  const database = await openQueue();
  return await new Promise((resolve, reject) => {
    const transaction = database.transaction('records', 'readwrite');
    transaction.objectStore('records').clear();
    transaction.oncomplete = () => resolve(true);
    transaction.onerror = () => reject(transaction.error);
  });
}""" % _QUEUE_OPEN_JS

_QUEUE_SEED_JS = """async ({ owner, count }) => {
  %s
  const database = await openQueue();
  return await new Promise((resolve, reject) => {
    const transaction = database.transaction('records', 'readwrite');
    const store = transaction.objectStore('records');
    for (let index = 0; index < count; index += 1) {
      store.put({
        owner,
        id: crypto.randomUUID(),
        method: 'POST',
        title: `Seeded queued record ${index + 1}`,
        body: 'Seeded for the queue limit proof.',
        status: 'draft',
        queuedAt: Date.now(),
      });
    }
    transaction.oncomplete = () => resolve(true);
    transaction.onerror = () => reject(transaction.error);
  });
}""" % _QUEUE_OPEN_JS


class BrowserQA:
    def __init__(self, project_dir: str, base_url: Optional[str] = None, *,
                 route_expectations=None, viewports=None, scene_required=None,
                 auth_token: str = '', api_fixtures: Optional[dict] = None,
                 requested_pwa: Optional[bool] = None):
        if requested_pwa is not None and not isinstance(requested_pwa, bool):
            raise ValueError('Invalid PWA request')
        self.project_dir = Path(project_dir).resolve()
        self.base_url = base_url
        self.qa_dir = self.project_dir / 'qa'
        if base_url is not None:
            self.qa_dir /= 'live'
        self.route_expectations = route_expectations
        self.viewports = viewports
        self.scene_required = scene_required
        self.auth_token = auth_token
        self.api_fixtures = api_fixtures
        self.requested_pwa = requested_pwa
        self._auth_storage = {}
        self._api_fixtures = {}
        self._fixtures_declared = False
        self._app_surface = None
        self._app_pwa = False
        # Test-only counter: the next N queued POSTs fail so the proof can
        # observe bounded retry and unconfirmed writes. Never used live.
        self._pwa_fail_posts = 0

    def _seed_storage(self, context):
        if not self._auth_storage:
            return
        values = json.dumps(self._auth_storage, ensure_ascii=True)
        context.add_init_script(script=f"""(() => {{
  try {{
    const values = {values};
    for (const [key, value] of Object.entries(values)) localStorage.setItem(key, value);
  }} catch (error) {{
    // Storage can be unavailable on opaque origins; the route must then fail.
  }}
}})();""")

    def _fixture_handler(self, route, *, pwa_posts=None, pwa_failed_posts=None,
                         pwa_auth=None, post_delay=0.0):
        request = route.request
        if request.method == 'OPTIONS':
            route.fulfill(status=204, headers=CORS_HEADERS, body='')
            return
        path = _api_path(request.url)
        if (pwa_posts is not None and request.method.upper() == 'POST'
                and path == '/records'):
            try:
                payload = request.post_data_json
            except Exception:
                payload = None
            payload = payload if isinstance(payload, dict) else {}
            if pwa_auth is not None:
                pwa_auth.append(request.headers.get('authorization', ''))
            headers = {'content-type': 'application/json; charset=utf-8', **CORS_HEADERS}
            if self._pwa_fail_posts:
                self._pwa_fail_posts -= 1
                if pwa_failed_posts is not None:
                    pwa_failed_posts.append(payload)
                route.fulfill(status=503, headers=headers,
                              body='{"success":false,"message":"Server did not confirm"}')
                return
            pwa_posts.append(payload)
            if post_delay:
                time.sleep(post_delay)
        body = self._api_fixtures.get((request.method.upper(), path)) if path else None
        headers = {'content-type': 'application/json; charset=utf-8', **CORS_HEADERS}
        if body is None:
            # Unlisted API calls fail closed; local previews never reach a real API.
            route.fulfill(status=404, headers=headers,
                          body='{"success":false,"message":"No QA fixture"}')
            return
        route.fulfill(status=200, headers=headers, body=body)

    def _resolve_fixtures(self, contract=None):
        """Resolve explicit arguments over a local manifest; reject them live."""
        contract = contract if isinstance(contract, dict) else {}
        contract_auth = contract.get('auth')
        contract_fixtures = contract.get('fixtures')
        if self.base_url is not None and (self.auth_token or self.api_fixtures
                                          or contract_auth is not None
                                          or contract_fixtures is not None):
            raise ValueError('QA fixtures are local-only')
        storage = _auth_storage(contract_auth)
        fixtures = _fixtures(contract_fixtures)
        # A declared (even empty) fixture set or a seeded test token must install
        # the fail-closed handler; otherwise a local run could reach a real API.
        self._fixtures_declared = (contract_fixtures is not None
                                   or self.api_fixtures is not None)
        if self.auth_token:
            if (not isinstance(self.auth_token, str) or len(self.auth_token) > 4096
                    or '\x00' in self.auth_token):
                raise ValueError('Invalid QA auth token')
            storage['token'] = self.auth_token
        if self.api_fixtures is not None:
            fixtures = _fixtures(self.api_fixtures)
        self._auth_storage = storage
        self._api_fixtures = fixtures

    def _configure_context(self, context, *, pwa_posts=None, pwa_failed_posts=None,
                           pwa_auth=None, post_delay=0.0):
        self._seed_storage(context)
        if self._fixtures_declared or self._auth_storage:
            # Unlisted API calls are fulfilled with 404 by the handler, so a
            # local preview never reaches localhost:5000 or any other API.
            context.route(
                '**/api/v1/**',
                lambda route: self._fixture_handler(
                    route, pwa_posts=pwa_posts,
                    pwa_failed_posts=pwa_failed_posts,
                    pwa_auth=pwa_auth, post_delay=post_delay),
            )

    def _roots(self):
        for root in (self.project_dir / 'frontend' / 'dist', self.project_dir / 'dist'):
            if (root / 'index.html').is_file() and not any(
                p.is_symlink() for p in (root, root.parent, root / 'index.html')
            ):
                return [str(root)]
        return []

    def _serve(self):
        roots = self._roots()
        if not roots:
            raise ValueError('No build output')
        def handler(*args, **kwargs):
            return _PreviewHandler(*args, roots=roots, **kwargs)
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        try:
            thread.start()
        except Exception:
            server.server_close()
            raise
        self._server_thread = thread
        return '127.0.0.1', server.server_port, server

    def _python_playwright(self):
        try:
            from playwright.sync_api import sync_playwright
            return sync_playwright
        except ImportError:
            return None

    def _npx_playwright(self):
        return shutil.which('npx') or ''

    def _target(self):
        value = self.base_url
        if not isinstance(value, str) or any(c.isspace() for c in value):
            raise ValueError('Invalid live target')
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or '?' in value or '#' in value):
            raise ValueError('Invalid live target')
        parsed.port  # Validate the port without persisting the supplied value on error.
        path = _safe_path(parsed.path or '/')
        return urlunsplit((parsed.scheme, parsed.netloc, quote(path.rstrip('/'), safe='/@-._~'), '', ''))

    @staticmethod
    def _unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate contract key')
            result[key] = value
        return result

    def _app_contract(self):
        """Read the generated surface contract; absent files mean the legacy site."""
        path = self.project_dir / 'app-contract.json'
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding='utf-8'),
                              object_pairs_hook=self._unique_object)
        except (OSError, ValueError):
            raise ValueError('Invalid app contract') from None
        if (not isinstance(data, dict) or type(data.get('version')) is not int
                or data['version'] != 1 or data.get('web') not in ('website', 'web_app', 'none')
                or ('pwa' in data and not isinstance(data['pwa'], bool))):
            raise ValueError('Invalid app contract')
        return data

    def _app_web_surface(self):
        contract = self._app_contract()
        return contract['web'] if contract else None

    def _prepare(self, report):
        expectations = self.route_expectations
        scene = self.scene_required
        contract = None
        app_contract = self._app_contract()
        self._app_surface = app_contract['web'] if app_contract else None
        self._app_pwa = bool(app_contract.get('pwa')) if app_contract else False
        requested_pwa = (self.requested_pwa if self.requested_pwa is not None
                         else self._app_pwa)
        report['requested_pwa'] = bool(requested_pwa)
        if expectations is None:
            from agent.live_verify import expected_routes
            manifest = self.project_dir / 'qa-contract.json'
            expectations = {}
            if manifest.is_file():
                data = json.loads(manifest.read_text(encoding='utf-8'),
                                  object_pairs_hook=self._unique_object)
                if (not isinstance(data, dict) or type(data.get('version')) is not int
                        or data['version'] != 1):
                    raise ValueError('Invalid QA contract')
                contract = data
                expectations = data.get('routes')
                scene = data.get('scene', scene)
            if not isinstance(expectations, dict):
                raise ValueError('Invalid route expectations')
            if self._app_surface == 'web_app':
                # The app shell has no marketing inventory; its manifest is exact.
                routes = list(expectations)
            else:
                routes = list(dict.fromkeys(
                    expected_routes(str(self.project_dir)) + list(expectations)))
        else:
            if not isinstance(expectations, dict):
                raise ValueError('Invalid route expectations')
            routes = list(expectations)
        self._resolve_fixtures(contract)
        if scene is not None:
            from agent.generation_contract import SCENE_ARCHETYPES
            if (not isinstance(scene, dict) or scene.get('archetype') not in SCENE_ARCHETYPES):
                raise ValueError('Invalid scene contract')
            report['requested_scene'] = {'archetype': scene['archetype']}
        if not routes:
            raise ValueError('Empty routes')
        report['requested_routes'] = [_route(r) for r in routes]
        requested = VIEWPORTS if self.viewports is None else self.viewports
        if isinstance(requested, dict):
            requested = list(requested.values())
        normalized = []
        for item in requested:
            if isinstance(item, dict):
                viewport = dict(item)
            else:
                width, height = item
                viewport = {'width': width, 'height': height}
            _viewport_key(viewport)
            normalized.append(viewport)
        if not normalized or len({_viewport_key(v) for v in normalized}) != len(normalized):
            raise ValueError('Empty or duplicate viewports')
        report['requested_viewports'] = normalized
        return expectations

    @staticmethod
    def _sample(route, viewport):
        return {
            'route': route, 'requested_viewport': dict(viewport), 'actual_viewport': None,
            'rendered_content': {'ok': False, 'main_visible': False, 'heading_matched': False},
            'screenshot': {'ok': False, 'path': ''}, 'console_errors': [], 'page_errors': [],
            'network_errors': [], 'overflow': {'overflow': None, 'offenders': []},
            'performance': {'dom_ms': None, 'lcp_ms': None}, 'failures': [], 'ok': False,
        }

    def _shot_path(self, route, viewport):
        route_id = hashlib.sha256(route.encode()).hexdigest()[:16]
        return self.qa_dir / f'route-{route_id}-{viewport["width"]}x{viewport["height"]}.png'

    def run(self) -> Dict[str, Any]:
        report = {
            'ok': False, 'status': 'failed', 'requested_routes': [], 'requested_viewports': [],
            'results': [], 'failures': [], 'screenshots': {}, 'evidence': {},
            'requested_scene': None, 'scene': None,
            'requested_pwa': False, 'pwa': None,
            'report_path': str(self.qa_dir / 'qa-report.json'),
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        server = None
        try:
            self.qa_dir.mkdir(parents=True, exist_ok=True)
            target = self._target() if self.base_url is not None else None
            expectations = self._prepare(report)
            if target is None and not self._roots():
                report['failures'].append('No build output found to QA.')
            else:
                if target is None:
                    host, port, server = self._serve()
                    target = f'http://{host}:{port}'
                report['base_url'] = target
                runtime = self._python_playwright()
                if runtime is None:
                    if self._npx_playwright():
                        self._run_via_cli(target, report)
                    else:
                        report['status'] = 'not_measured'
                        report['failures'].append('Python Playwright unavailable; install Playwright and Chromium.')
                else:
                    self._run_full(runtime, target, expectations, report)
        except Exception as exc:
            report['failures'].append(f'QA setup failed ({type(exc).__name__}).')
            report['status'] = 'failed'
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
                self._server_thread.join(timeout=5)
        self._finish(report)
        return report

    def _run_full(self, runtime, target, expectations, report):
        launched = False
        try:
            with runtime() as playwright:
                browser = playwright.chromium.launch(headless=True)
                launched = True
                try:
                    for route in report['requested_routes']:
                        expectation = expectations.get(route)
                        heading = expectation.get('heading') if isinstance(expectation, dict) else None
                        if not isinstance(heading, str) or not heading.strip() or len(heading) > 500:
                            heading = None
                        for viewport in report['requested_viewports']:
                            report['results'].append(self._measure(browser, target, route, viewport, heading))
                    if report['requested_scene'] is not None:
                        report['scene'] = self._measure_scene(
                            browser, target, report['requested_viewports'])
                    if report['requested_pwa']:
                        report['pwa'] = self._measure_pwa(
                            browser, target, expectations)
                finally:
                    browser.close()
        except Exception as exc:
            report['failures'].append(f'Browser runtime failed ({type(exc).__name__}).')
            report['status'] = 'failed' if launched else 'not_measured'

    @staticmethod
    def _required(request, target):
        parsed = urlsplit(request.url)
        origin = urlsplit(target)
        return (request.resource_type in REQUIRED_RESOURCES or
                (request.resource_type in ('fetch', 'xhr') and
                 (parsed.scheme, parsed.netloc) == (origin.scheme, origin.netloc)))

    def _measure(self, browser, target, route, viewport, heading):
        sample = self._sample(route, viewport)
        context = None
        url = target.rstrip('/') + route
        ignored_network_urls = set()
        def record(kind, message):
            if len(sample[kind]) < MAX_DIAGNOSTICS:
                sample[kind].append(message)
        def network(request, status=None):
            if self._required(request, target):
                # Do not retain URLs, headers, bodies or error payloads. Even URL
                # paths can contain credentials; resource type/status suffice.
                record('network_errors', {'resource_type': request.resource_type, 'status': status})
            else:
                ignored_network_urls.add(request.url)
        def console(message):
            # Ignore native resource diagnostics only for an observed, out-of-scope
            # failed request. An app console.error with similar text still fails.
            native_ignored = (message.text.startswith('Failed to load resource:')
                              and message.location.get('url') in ignored_network_urls)
            if message.type == 'error' and not native_ignored:
                record('console_errors', 'Browser console error (message omitted).')
        try:
            context = browser.new_context(viewport=viewport, reduced_motion='no-preference')
            self._configure_context(context)
            page = context.new_page()
            page.set_default_timeout(5000)
            page.on('console', console)
            page.on('pageerror', lambda error: record('page_errors', 'Uncaught page error (message omitted).'))
            page.on('requestfailed', lambda request: network(request))
            page.on('response', lambda response: network(response.request, response.status)
                    if response.status >= 400 else None)
            try:
                response = page.goto(url, wait_until='domcontentloaded', timeout=15000)
                if response is None or response.status >= 400:
                    sample['failures'].append('navigation')
                if heading:
                    try:
                        page.wait_for_function(
                            f'(heading) => ({_DOM_EVIDENCE})(heading).rendered_content.ok',
                            arg=heading, timeout=2500,
                        )
                    except Exception:
                        sample['failures'].append('route_identity')
                try:
                    page.evaluate(_READINESS)
                except Exception:
                    # Fonts/layout readiness is a bounded wait, not a page defect.
                    # Required assets and console errors are measured separately.
                    pass
                # Below-fold lazy images are never requested until they approach
                # the viewport, so a full-page screenshot could certify a page
                # whose visible images 404. Trigger loading with bounded scroll.
                page.evaluate(_TRIGGER_LAZY)
                try:
                    page.wait_for_function(
                        '() => [...document.images].every(i => i.complete)', timeout=3000,
                    )
                except Exception:
                    record('network_errors', {'resource_type': 'image', 'status': 'load_timeout'})
                broken_images = page.evaluate(
                    '() => [...document.images].filter(i => i.complete && '
                    'i.currentSrc && i.naturalWidth === 0).length'
                )
                if broken_images:
                    record('network_errors', {'resource_type': 'image', 'status': 'decode_failed'})
                sample.update(page.evaluate(_DOM_EVIDENCE, heading))
                if page.url != url or (response and response.request.redirected_from):
                    sample['rendered_content']['ok'] = False
                if not sample['rendered_content']['ok']:
                    sample['failures'].append('route_identity')
                if sample['actual_viewport'] != viewport:
                    sample['failures'].append('viewport')
            except Exception as exc:
                sample['failures'].append(f'readiness ({type(exc).__name__})')
            path = self._shot_path(route, viewport)
            try:
                path.unlink(missing_ok=True)
                page.screenshot(path=str(path), full_page=True, type='png', timeout=10000)
                sample['screenshot'] = _png_evidence(path)
            except Exception:
                sample['screenshot'] = {'ok': False, 'path': str(path)}
            if not sample['screenshot']['ok']:
                sample['failures'].append('screenshot')
            # Reduced motion is measured from navigation in its own context.
            # Toggling emulate_media after load misses every branch a page takes
            # during initialization (review 2026-10-28). Not a scene/3D test.
            reduced_context = None
            try:
                reduced_context = browser.new_context(
                    viewport=viewport, reduced_motion='reduce')
                self._configure_context(reduced_context)
                reduced_page = reduced_context.new_page()
                reduced_page.set_default_timeout(5000)
                reduced_response = reduced_page.goto(
                    url, wait_until='domcontentloaded', timeout=15000)
                if reduced_response is None or reduced_response.status >= 400:
                    raise RuntimeError('navigation')
                try:
                    reduced_page.evaluate(_READINESS)
                except Exception:
                    pass
                reduced = reduced_page.evaluate(_DOM_EVIDENCE, heading)
                reduced['media_matches'] = reduced_page.evaluate(
                    '() => matchMedia("(prefers-reduced-motion: reduce)").matches'
                )
                reduced['ok'] = (reduced['media_matches'] and reduced['rendered_content']['ok']
                                 and reduced['actual_viewport'] == viewport
                                 and reduced['overflow']['overflow'] is False
                                 and reduced_page.url == url)
                sample['reduced_motion'] = reduced
                if not reduced['ok']:
                    sample['failures'].append('reduced_motion')
            except Exception as exc:
                sample['reduced_motion'] = {'ok': False,
                                            'error': type(exc).__name__}
                sample['failures'].append('reduced_motion')
            finally:
                if reduced_context is not None:
                    try:
                        reduced_context.close()
                    except Exception:
                        sample['failures'].append('context_cleanup')
        except Exception as exc:
            sample['failures'].append(f'capture ({type(exc).__name__})')
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    sample['failures'].append('context_cleanup')
        for key in ('console_errors', 'page_errors', 'network_errors'):
            if sample[key]:
                sample['failures'].append(key)
        if sample['overflow']['overflow'] is not False:
            sample['failures'].append('overflow')
        sample['failures'] = list(dict.fromkeys(sample['failures']))
        sample['ok'] = not sample['failures']
        return sample

    def _measure_scene(self, browser, target, viewports):
        """Desktop activation, rendered pixels, interaction change, mobile fallback."""
        widths = [viewport['width'] for viewport in viewports]
        width = 1440 if 1440 in widths else next(
            (value for value in widths if value >= 1024), max(widths))
        height = next((viewport['height'] for viewport in viewports
                       if viewport['width'] == width), 900)
        result = {
            'ok': False, 'route': '/', 'viewport': {'width': width, 'height': height},
            'state': None, 'frames': 0, 'draw_calls': 0, 'canvas': None,
            'interaction': None, 'mobile_fallback': None, 'failures': [],
        }
        context = None
        try:
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                reduced_motion='no-preference')
            page = context.new_page()
            page.set_default_timeout(5000)
            response = page.goto(target.rstrip('/') + '/', wait_until='domcontentloaded',
                                 timeout=15000)
            if response is None or response.status >= 400:
                result['failures'].append('scene_navigation')
            page.evaluate(_READINESS)
            section = page.locator('[data-scene-state]').first
            section.wait_for(state='attached', timeout=10000)
            enable = page.get_by_role('button', name='Enable 3D')
            if enable.count() == 0:
                result['failures'].append('scene_not_optional')
            else:
                enable.first.click()
            page.wait_for_function(
                "() => document.querySelector('[data-scene-state]')?.dataset.sceneState === 'rendered'",
                timeout=25000)
            section = page.locator('[data-scene-state]').first
            result['state'] = section.get_attribute('data-scene-state')
            result['frames'] = int(section.get_attribute('data-scene-frames') or 0)
            result['draw_calls'] = int(section.get_attribute('data-scene-draw-calls') or 0)
            canvas = page.locator('[data-scene-viewport] canvas').first
            canvas.wait_for(state='visible', timeout=10000)
            canvas.scroll_into_view_if_needed(timeout=5000)
            first = canvas.screenshot(type='png', timeout=10000)
            result['canvas'] = {**_canvas_evidence(first), 'bytes': len(first)}
            page.get_by_role('button', name='Rotate right').first.click()
            page.evaluate(
                '() => new Promise(resolve => requestAnimationFrame('
                '() => requestAnimationFrame(resolve)))')
            time.sleep(0.15)
            second = canvas.screenshot(type='png', timeout=10000)
            changed = _canvas_changed(first, second)
            result['interaction'] = {'changed': changed >= 0.002,
                                     'changed_fraction': round(changed, 4)}
            before_path = self.qa_dir / f'scene-{width}x{height}-rendered.png'
            after_path = self.qa_dir / f'scene-{width}x{height}-after-rotate.png'
            before_path.write_bytes(first)
            after_path.write_bytes(second)
            result['canvas']['path'] = str(before_path)
            result['interaction']['after_path'] = str(after_path)
        except Exception as exc:
            result['failures'].append(f'scene_activation ({type(exc).__name__})')
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    result['failures'].append('scene_context_cleanup')
        mobile_context = None
        try:
            mobile_context = browser.new_context(
                viewport={'width': 375, 'height': 812}, reduced_motion='no-preference')
            mobile = mobile_context.new_page()
            mobile.set_default_timeout(5000)
            mobile.goto(target.rstrip('/') + '/', wait_until='domcontentloaded', timeout=15000)
            mobile.evaluate(_READINESS)
            section = mobile.locator('[data-scene-state]').first
            section.wait_for(state='attached', timeout=10000)
            window = {
                'state': section.get_attribute('data-scene-state'),
                'canvas_count': mobile.locator('[data-scene-viewport] canvas').count(),
                'enable_visible': mobile.get_by_role('button', name='Enable 3D').is_visible(),
            }
            window['ok'] = (window['state'] in {'requested', 'fallback'}
                            and window['canvas_count'] == 0 and window['enable_visible'])
            result['mobile_fallback'] = window
        except Exception as exc:
            result['mobile_fallback'] = {'ok': False,
                                         'error': f'fallback ({type(exc).__name__})'}
        finally:
            if mobile_context is not None:
                try:
                    mobile_context.close()
                except Exception:
                    result['failures'].append('scene_context_cleanup')
        if result['state'] != 'rendered':
            result['failures'].append('scene_not_rendered')
        if result['frames'] < 1 or result['draw_calls'] < 1:
            result['failures'].append('scene_not_drawing')
        if not (result['canvas'] or {}).get('ok'):
            result['failures'].append('scene_blank_canvas')
        if not (result['interaction'] or {}).get('changed'):
            result['failures'].append('scene_interaction_not_visible')
        if not (result['mobile_fallback'] or {}).get('ok'):
            result['failures'].append('scene_mobile_fallback')
        result['failures'] = list(dict.fromkeys(result['failures']))
        result['ok'] = not result['failures']
        return result

    def _pwa_result(self, *, surface, route):
        return {
            'ok': False, 'status': 'not_measured', 'surface': surface, 'route': route,
            'worker_controlled': False, 'offline_heading': '',
            'online_recovered': False,
            'queue': {
                'applicable': surface != 'website',
                'enqueued': 0, 'client_id': '', 'posts': 0, 'post_ids': [],
                'cleared': False, 'ui_queued': False, 'ui_cleared': False,
                'max_records': 50, 'max_enforced': False, 'max_kept': 0,
                'retry_attempts': 0, 'failed_flush_kept': False,
                'no_success_before_confirmation': False, 'banner_copy': '',
            },
            'offline_screenshot': {'ok': False, 'path': ''},
            'failures': [],
        }

    def _pwa_not_measured(self, message, *, route=None):
        surface = self._app_surface or 'web_app'
        result = self._pwa_result(
            surface=surface,
            route=route or ('/dashboard' if surface == 'web_app' else '/'),
        )
        result['failures'] = [message]
        return result

    def _measure_pwa(self, browser, target, expectations):
        """Prove worker control, offline fallback, recovery and queue replay.

        The queue proof is deliberately local-only: it uses the seeded test token
        and bounded API fixtures. A live target reports `not_measured` instead of
        faking a backend, and any missing fixture fails closed.
        """
        if self.base_url is not None:
            # A hosted run has no proof fixtures. Return before opening a context
            # or navigating so live QA never adds a request or fakes a worker.
            return self._pwa_not_measured(
                'PWA proof requires a local fixture run; live QA never uses fixtures.')
        surface = self._app_surface or 'web_app'
        route = '/dashboard' if surface == 'web_app' else '/'
        if route not in expectations:
            route = next(iter(expectations), route)
        expectation = expectations.get(route)
        heading = expectation.get('heading') if isinstance(expectation, dict) else None
        if not isinstance(heading, str) or not heading.strip() or len(heading) > 500:
            heading = None
        if surface != 'website' and not (
                self._auth_storage and ('POST', '/records') in self._api_fixtures):
            return self._pwa_not_measured(
                'PWA queue proof requires local auth token and API fixtures.',
                route=route,
            )

        result = self._pwa_result(surface=surface, route=route)
        posts = []
        failed_posts = []
        online_errors = []
        offline_errors = []
        phase = {'offline': False}
        context = None

        def page_error(error):
            del error
            target_list = offline_errors if phase['offline'] else online_errors
            target_list.append('Uncaught page error (message omitted).')

        def heading_visible(value, timeout=6000):
            if not value:
                return True
            try:
                page.wait_for_function(
                    f'(heading) => ({_DOM_EVIDENCE})(heading).rendered_content.ok',
                    arg=value, timeout=timeout,
                )
                return True
            except Exception:
                return False

        try:
            context = browser.new_context(
                viewport={'width': 1440, 'height': 900},
                reduced_motion='no-preference',
            )
            self._configure_context(
                context,
                pwa_posts=posts if surface != 'website' else None,
                pwa_failed_posts=failed_posts if surface != 'website' else None,
                post_delay=0.35,
            )
            page = context.new_page()
            page.set_default_timeout(8000)
            page.on('pageerror', page_error)

            page.goto(target.rstrip('/') + route, wait_until='domcontentloaded',
                      timeout=15000)
            page.wait_for_function(
                "() => 'serviceWorker' in navigator"
                " && navigator.serviceWorker.ready.then(() => true)",
                timeout=15000,
            )
            page.reload(wait_until='domcontentloaded', timeout=15000)
            page.wait_for_function(
                '() => !!navigator.serviceWorker.controller', timeout=10000)
            result['worker_controlled'] = True
            if not heading_visible(heading):
                result['failures'].append('online_heading')

            # Offline reload must render the last-resort shell, not an error page.
            phase['offline'] = True
            context.set_offline(True)
            try:
                page.reload(wait_until='domcontentloaded', timeout=15000)
            except Exception:
                result['failures'].append('offline_reload')
            try:
                heading_node = page.locator('h1').first
                heading_node.wait_for(state='visible', timeout=5000)
                offline_heading = heading_node.inner_text(timeout=3000)
                result['offline_heading'] = offline_heading[:200]
                if 'offline' not in offline_heading.lower():
                    result['failures'].append('offline_heading')
            except Exception:
                result['failures'].append('offline_heading')
            shot_path = self.qa_dir / 'pwa-offline-1440x900.png'
            try:
                shot_path.unlink(missing_ok=True)
                page.screenshot(path=str(shot_path), full_page=True,
                                type='png', timeout=10000)
                result['offline_screenshot'] = _png_evidence(shot_path)
            except Exception:
                result['offline_screenshot'] = {'ok': False, 'path': str(shot_path)}
            if not result['offline_screenshot']['ok']:
                result['failures'].append('offline_screenshot')
            if offline_errors:
                result['failures'].append('offline_page_errors')
            phase['offline'] = False

            # Restoring connectivity must bring the authenticated content back.
            context.set_offline(False)
            try:
                page.reload(wait_until='domcontentloaded', timeout=15000)
            except Exception:
                result['failures'].append('online_reload')
            result['online_recovered'] = heading_visible(heading)
            if not result['online_recovered']:
                result['failures'].append('online_recovery')
            if online_errors:
                result['failures'].append('page_errors')

            if surface != 'website':
                self._pwa_queue_proof(context, page, target, posts, failed_posts,
                                      result)
        except Exception as exc:
            result['failures'].append(f'pwa_proof ({type(exc).__name__})')
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    result['failures'].append('pwa_context_cleanup')
        result['failures'] = list(dict.fromkeys(result['failures']))[:10]
        result['ok'] = not result['failures']
        result['status'] = 'passed' if result['ok'] else 'failed'
        return result

    def _pwa_queue_proof(self, context, page, target, posts, failed_posts, result):
        """Drive the shipped Records page and prove the queue contract.

        The proof uses the generated app's own `offlineQueue.js`, Records page
        and banner: the client UUID captured from IndexedDB must be the only
        successful POST, the 50-record cap must be enforced by the shipped
        `enqueue`, and a server that never confirms must never produce success
        UI. A three-attempt failed flush proves the bounded retry.
        """
        queue = result['queue']
        queue['applicable'] = True

        def rows():
            return page.evaluate(_QUEUE_ROWS_JS)

        def success_free():
            text = page.locator('main').inner_text().lower()
            return not any(word in text for word in (
                'saved', 'success', 'created successfully'))

        try:
            page.goto(target.rstrip('/') + '/records',
                      wait_until='domcontentloaded', timeout=15000)
            page.wait_for_selector('#record-title', state='visible', timeout=10000)
            page.wait_for_selector('#record-queue', state='attached', timeout=5000)
            page.wait_for_function('() => navigator.onLine === true', timeout=5000)
        except Exception:
            result['failures'].append('queue_navigation')
            return

        offline_no_success = False
        try:
            context.set_offline(True)
            page.wait_for_function('() => navigator.onLine === false', timeout=5000)
            page.locator('#record-title').fill('Offline proof record')
            page.locator('#record-body').fill('Created while the browser is offline.')
            page.get_by_role('button', name='Create record').click()
            page.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            queue['ui_queued'] = True
            notice = page.locator('#record-notice')
            notice.wait_for(state='visible', timeout=5000)
            notice_text = notice.inner_text().strip()
            main_text = page.locator('main').inner_text()
            offline_no_success = (
                'Queued on this device' in notice_text
                and success_free()
                # The queued record must not be presented as a saved record
                # before the server has seen it.
                and 'Offline proof record' not in main_text
                and not posts
            )
        except Exception:
            result['failures'].append('queue_ui')
            return

        try:
            queued_rows = rows()
        except Exception:
            queued_rows = []
        queue['enqueued'] = len(queued_rows)
        owner = ''
        if (len(queued_rows) == 1
                and isinstance(queued_rows[0].get('id'), str)
                and queued_rows[0]['id']):
            queue['client_id'] = queued_rows[0]['id']
            owner = str(queued_rows[0].get('owner') or '')
        else:
            result['failures'].append('queue_enqueue')

        try:
            context.set_offline(False)
            deadline = time.monotonic() + 15
            cleared = False
            while time.monotonic() < deadline:
                try:
                    remaining = len(rows())
                except Exception:
                    remaining = None
                if posts and remaining == 0:
                    cleared = True
                    break
                page.wait_for_timeout(100)
            page.wait_for_timeout(600)
            try:
                final_ids = [row['id'] for row in rows()]
            except Exception:
                final_ids = None
        except Exception:
            final_ids = None
        post_ids = [
            payload.get('id') for payload in posts
            if isinstance(payload, dict) and isinstance(payload.get('id'), str)
        ]
        queue['posts'] = len(posts)
        queue['post_ids'] = post_ids[:3]
        queue['cleared'] = final_ids == []
        queue['ui_cleared'] = False
        try:
            queue['ui_cleared'] = page.evaluate(
                "() => document.querySelector('#record-queue')?.dataset.queueCount"
            ) == '0'
        except Exception:
            pass
        if len(posts) != 1:
            result['failures'].append('queue_post_count')
        if not queue['client_id'] or post_ids != [queue['client_id']]:
            result['failures'].append('queue_client_id')
        if not queue['cleared']:
            result['failures'].append('queue_not_cleared')
        if not queue['ui_cleared']:
            result['failures'].append('queue_ui_clear')

        if owner:
            guarded = self._pwa_queue_limit_proof(context, page, owner, posts, queue)
        else:
            guarded = False
            result['failures'].append('queue_owner')
        unconfirmed = self._pwa_unconfirmed_flush_proof(
            context, page, failed_posts, queue)
        queue['no_success_before_confirmation'] = bool(
            offline_no_success and unconfirmed and queue['cleared'])
        if not queue['no_success_before_confirmation']:
            result['failures'].append('queue_success_ui')
        if not guarded:
            result['failures'].append('queue_limit')

    def _pwa_queue_limit_proof(self, context, page, owner, posts, queue):
        """The shipped enqueue must refuse the 51st record for one user."""
        try:
            context.set_offline(True)
            page.wait_for_function('() => navigator.onLine === false', timeout=5000)
            page.evaluate(_QUEUE_CLEAR_JS)
            page.evaluate(_QUEUE_SEED_JS, {'owner': owner, 'count': 50})
            page.locator('#record-title').fill('Queue limit record')
            page.locator('#record-body').fill('The fifty-first record must stay local only.')
            page.get_by_role('button', name='Create record').click()
            page.wait_for_function(
                "() => [...document.querySelectorAll('[role=\"alert\"]')].some("
                "element => /queue is full/i.test(element.textContent || ''))",
                timeout=8000,
            )
            page.wait_for_function(
                "() => !document.querySelector('.app-form button[type=\"submit\"]')?.disabled",
                timeout=5000,
            )
            remaining = page.evaluate(_QUEUE_ROWS_JS)
            queue['max_kept'] = len(remaining)
            queue['max_enforced'] = bool(
                len(remaining) == 50
                and all(str(row.get('owner') or '') == owner for row in remaining)
                and len(posts) == 1)
            page.evaluate(_QUEUE_CLEAR_JS)
            context.set_offline(False)
            page.wait_for_function('() => navigator.onLine === true', timeout=5000)
            page.wait_for_timeout(300)
            return queue['max_enforced']
        except Exception:
            return False

    def _pwa_unconfirmed_flush_proof(self, context, page, failed_posts, queue):
        """An unconfirmed flush retries three times, keeps the queue, no success UI."""
        try:
            context.set_offline(True)
            page.wait_for_function('() => navigator.onLine === false', timeout=5000)
            page.evaluate(_QUEUE_CLEAR_JS)
            page.locator('#record-title').fill('Unconfirmed record')
            page.locator('#record-body').fill('The server never accepted this write.')
            page.get_by_role('button', name='Create record').click()
            page.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            self._pwa_fail_posts = 3
            context.set_offline(False)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline and len(failed_posts) < 3:
                page.wait_for_timeout(150)
            # Let the final retry settle and the banner refresh.
            page.wait_for_timeout(500)
            remaining = page.evaluate(_QUEUE_ROWS_JS)
            queue['retry_attempts'] = len(failed_posts)
            queue['failed_flush_kept'] = len(remaining) == 1
            try:
                queue['banner_copy'] = page.locator(
                    '#pwa-connection-banner').inner_text().strip()[:200]
            except Exception:
                queue['banner_copy'] = ''
            body = page.locator('main').inner_text().lower()
            no_success = not any(word in body for word in (
                'saved', 'success', 'created successfully'))
            banner = queue['banner_copy'].lower()
            copy_matches = ('sync pending' in banner
                            and 'when the connection returns' not in banner)
            page.evaluate(_QUEUE_CLEAR_JS)
            return bool(queue['retry_attempts'] == 3
                        and queue['failed_flush_kept'] and no_success and copy_matches)
        except Exception:
            return False
        finally:
            self._pwa_fail_posts = 0

    def _run_via_cli(self, target, report):
        for route in report['requested_routes']:
            for viewport in report['requested_viewports']:
                sample = self._sample(route, viewport)
                path = self._shot_path(route, viewport)
                try:
                    path.unlink(missing_ok=True)
                    subprocess.run(
                        [self._npx_playwright(), '--no-install', 'playwright', 'screenshot',
                         '--full-page', '--viewport-size', f'{viewport["width"]},{viewport["height"]}',
                         target.rstrip('/') + route, str(path)],
                        cwd=str(self.project_dir), capture_output=True, timeout=60, check=True,
                    )
                    sample['screenshot'] = _png_evidence(path)
                except Exception:
                    pass
                sample['failures'] = ['CLI screenshot only; rendered evidence unmeasured.']
                report['results'].append(sample)
        captured = any(r['screenshot']['ok'] for r in report['results'])
        report['status'] = 'partial' if captured else 'not_measured'
        report['failures'].append('Python Playwright required for full browser evidence.')

    def _finish(self, report):
        for sample in report['results']:
            if sample['screenshot']['ok']:
                viewport = sample['requested_viewport']
                key = f'{sample["route"]}@{viewport["width"]}x{viewport["height"]}'
                report['screenshots'][key] = sample['screenshot']
            if sample['failures']:
                report['failures'].append({
                    'route': sample['route'], 'viewport': sample['requested_viewport'],
                    'failures': sample['failures'],
                })
        scene = report.get('scene')
        if report.get('requested_scene') is not None:
            if not isinstance(scene, dict) or not scene.get('ok'):
                failures = (scene or {}).get('failures') or ['scene proof incomplete']
                report['failures'].append({
                    'route': '/ (3D)', 'viewport': (scene or {}).get('viewport'),
                    'failures': failures,
                })
        if report.get('requested_pwa'):
            pwa = report.get('pwa')
            if not isinstance(pwa, dict) or pwa.get('ok') is not True:
                failures = (pwa or {}).get('failures') or ['PWA proof incomplete']
                report['failures'].append({
                    'route': f"{(pwa or {}).get('route') or '/dashboard'} (PWA)",
                    'viewport': {'width': 1440, 'height': 900},
                    'failures': failures[:10],
                })
        report['evidence'] = {
            'viewport_captures': len(report['screenshots']),
            'measured_samples': sum(r['actual_viewport'] is not None for r in report['results']),
            'lcp_ms': None,
        }
        owned = _captures_named_by(report)
        for path in sorted(p for p in self.qa_dir.glob('*.png') if p.name not in owned):
            try:
                path.unlink()
            except OSError as exc:
                report['failures'].append(
                    f'QA capture from an earlier run is still beside this report: '
                    f'{path.name} ({type(exc).__name__})'
                )
        if not report['failures']:
            report.update(ok=True, status='passed')
            if not evidence_passes(report):
                report['failures'].append('Incomplete or invalid browser evidence.')
                report.update(ok=False, status='failed')
        try:
            Path(report['report_path']).write_text(json.dumps(report, indent=2), encoding='utf-8')
        except OSError:
            report.update(ok=False, status='failed')
            report['failures'].append('Unable to persist QA report.')


def run_browser_qa(project_dir: str, base_url: Optional[str] = None, *,
                   route_expectations=None, viewports=None,
                   scene_required=None, auth_token: str = '',
                   api_fixtures: Optional[dict] = None,
                   requested_pwa: Optional[bool] = None) -> Dict[str, Any]:
    """Run public browser QA, optionally overriding independent headings/viewports.

    `auth_token` and `api_fixtures` are local-only test doubles for authenticated
    app shells. Live targets reject them so fixtures can never fake a backend.
    `requested_pwa` overrides the app contract; a requested PWA proof never
    silently disappears from the verdict.
    """
    return BrowserQA(project_dir, base_url, route_expectations=route_expectations,
                     viewports=viewports, scene_required=scene_required,
                     auth_token=auth_token, api_fixtures=api_fixtures,
                     requested_pwa=requested_pwa).run()
