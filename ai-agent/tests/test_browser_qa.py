"""Fail-closed browser evidence regressions (real Chromium tests never skip)."""
import base64
import copy
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import threading
import time
import zlib
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.app_layouts import app_route_expectations
from agent.extensions import browser_qa
from agent.fullstack_ultra_engine import FullStackUltraEngine
from agent.generation_contract import resolve_generation_contract


def test_no_build_cannot_pass(tmp_path, monkeypatch):
    (tmp_path / 'index.html').write_text('<main><h1>Home</h1></main>')
    # Runtime absence must not obscure the more fundamental missing-build failure.
    monkeypatch.setattr(browser_qa.BrowserQA, '_python_playwright', lambda self: None)
    monkeypatch.setattr(browser_qa.BrowserQA, '_npx_playwright', lambda self: '')
    result = browser_qa.BrowserQA(str(tmp_path)).run()
    assert result.get('ok') is False
    assert result['status'] == 'failed'


CLEAN = '''<!doctype html><html><head><meta name="viewport"
content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"></head>
<body><header>Navigation</header><main><h1>Home</h1><p>Usable page content.</p></main>
<script>if(location.pathname.endsWith('/features'))
document.querySelector('h1').textContent='Features';</script></body></html>'''
SMALL = [{'width': 375, 'height': 812}]


def build(tmp_path, html=CLEAN):
    dist = tmp_path / 'dist'
    dist.mkdir(exist_ok=True)
    (dist / 'index.html').write_text(html, encoding='utf-8')
    return tmp_path


def png(path):
    def chunk(kind, data):
        return (struct.pack('!I', len(data)) + kind + data
                + struct.pack('!I', zlib.crc32(kind + data)))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('!2I5B', 1, 1, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
                     + chunk(b'IEND', b''))


def good_report(tmp_path):
    shot = tmp_path / 'proof.png'
    from PIL import Image
    Image.new('RGB', (375, 812), 'white').save(shot)
    vp = {'width': 375, 'height': 812}
    return {
        'ok': True, 'status': 'passed', 'requested_routes': ['/'],
        'requested_viewports': [vp], 'failures': [],
        'results': [{
            'route': '/', 'requested_viewport': vp.copy(), 'actual_viewport': vp.copy(),
            'ok': True, 'failures': [],
            'rendered_content': {'ok': True, 'main_visible': True, 'heading_matched': True},
            'screenshot': {'ok': True, 'path': str(shot)},
            'console_errors': [], 'page_errors': [], 'network_errors': [],
            'overflow': {'overflow': False, 'offenders': []},
            'reduced_motion': {
                'ok': True, 'media_matches': True, 'actual_viewport': vp.copy(),
                'rendered_content': {'ok': True, 'main_visible': True, 'heading_matched': True},
                'overflow': {'overflow': False, 'offenders': []},
            },
        }],
    }


def test_consumer_accepts_complete_readable_evidence(tmp_path):
    assert browser_qa.evidence_passes(good_report(tmp_path))


@pytest.mark.parametrize('damage', [
    'missing', 'duplicate', 'extra', 'empty_routes', 'empty_viewports', 'duplicate_routes',
    'duplicate_viewports', 'wrong_viewport', 'false_result', 'identity', 'screenshot',
    'unreadable', 'signature_only', 'console', 'page', 'network', 'overflow', 'failure',
    'status_only', 'missing_errors', 'zero_viewport', 'boolean_viewport',
    'missing_reduced_motion', 'wrong_screenshot_width',
])
def test_consumer_rejects_forged_or_incomplete_evidence(tmp_path, damage):
    report = good_report(tmp_path)
    sample = report['results'][0]
    if damage == 'missing':
        report['results'] = []
    elif damage in ('duplicate', 'extra'):
        report['results'].append(copy.deepcopy(sample))
        if damage == 'extra':
            report['results'][-1]['route'] = '/other'
    elif damage.startswith('empty_'):
        report['requested_' + damage[6:]] = []
    elif damage.startswith('duplicate_'):
        key = 'requested_' + damage[10:]
        report[key] *= 2
    elif damage == 'wrong_viewport':
        sample['actual_viewport']['width'] = 1440
    elif damage == 'false_result':
        sample['ok'] = False
    elif damage == 'identity':
        sample['rendered_content']['heading_matched'] = False
    elif damage == 'screenshot':
        sample['screenshot']['ok'] = False
    elif damage == 'unreadable':
        Path(sample['screenshot']['path']).unlink()
    elif damage == 'signature_only':
        Path(sample['screenshot']['path']).write_bytes(b'\x89PNG\r\n\x1a\n')
    elif damage in ('console', 'page', 'network'):
        sample[damage + '_errors'] = ['error']
    elif damage == 'overflow':
        sample['overflow']['overflow'] = True
    elif damage == 'failure':
        sample['failures'] = ['failed']
    elif damage == 'status_only':
        report = {'ok': True, 'status': 'passed'}
    elif damage == 'missing_errors':
        del sample['page_errors']
    elif damage in ('zero_viewport', 'boolean_viewport'):
        report['requested_viewports'][0]['width'] = 0 if damage == 'zero_viewport' else True
    elif damage == 'missing_reduced_motion':
        report['results'][0].pop('reduced_motion')
    elif damage == 'wrong_screenshot_width':
        wide = tmp_path / 'wide.png'
        wide.write_bytes(Path(sample['screenshot']['path']).read_bytes())
        from PIL import Image
        with Image.open(wide) as image:
            larger = image.resize((image.width + 100, image.height))
            larger.save(wide)
        sample['screenshot']['path'] = str(wide)
    assert not browser_qa.evidence_passes(report)


@contextmanager
def preview(project):
    qa = browser_qa.BrowserQA(str(project))
    host, port, server = qa._serve()
    try:
        yield host, port
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize('path,status', [
    ('/', 200), ('/features', 200), ('/features?token=private', 200),
    ('/app.js?v=1', 200), ('/missing.js', 404), ('/missing.png', 404),
    ('/.env', 404), ('/%2eenv', 404), ('/../outside.txt', 404),
    ('/%2e%2e/outside.txt', 404), ('/%2e%2e%5coutside.txt', 404),
    ('/C:/outside.txt', 404), ('/assets/', 404),
])
def test_preview_only_serves_safe_built_files(tmp_path, path, status):
    build(tmp_path)
    (tmp_path / 'dist' / 'app.js').write_text('window.built=true')
    (tmp_path / 'dist' / '.env').write_text('PRIVATE')
    (tmp_path / 'outside.txt').write_text('PRIVATE')
    (tmp_path / 'dist' / 'assets').mkdir()
    with preview(tmp_path) as (host, port):
        conn = HTTPConnection(host, port, timeout=3)
        conn.request('GET', path)
        response = conn.getresponse()
        assert response.status == status
        assert b'PRIVATE' not in response.read()
        conn.close()


@pytest.mark.parametrize('target', [
    'file:///secret', 'ftp://localhost', '//localhost', 'https://user:pass@example.test',
    'https://example.test/app?token=secret', 'https://example.test/#secret',
    'http://', 'https://example.test/../private', 'https://example.test/%2e%2e/private',
])
def test_invalid_live_target_fails_without_local_fallback(tmp_path, monkeypatch, target):
    def forbidden(*args):
        pytest.fail('Invalid live URL must not start a local server')
    monkeypatch.setattr(browser_qa.BrowserQA, '_serve', forbidden)
    result = browser_qa.run_browser_qa(str(tmp_path), target)
    assert result['ok'] is False
    assert result['status'] == 'failed'
    assert 'secret' not in json.dumps(result)
    assert 'user:pass' not in json.dumps(result)


def test_missing_runtime_is_unmeasured_and_persisted(tmp_path, monkeypatch):
    build(tmp_path)
    monkeypatch.setattr(browser_qa.BrowserQA, '_python_playwright', lambda self: None)
    monkeypatch.setattr(browser_qa.BrowserQA, '_npx_playwright', lambda self: '')
    result = browser_qa.BrowserQA(str(tmp_path)).run()
    assert result['ok'] is False
    assert result['status'] == 'not_measured'
    assert not browser_qa.evidence_passes(result)
    assert json.loads(Path(result['report_path']).read_text()) == result


def test_cli_capture_is_only_partial(tmp_path, monkeypatch):
    build(tmp_path)
    monkeypatch.setattr(browser_qa.BrowserQA, '_python_playwright', lambda self: None)
    monkeypatch.setattr(browser_qa.BrowserQA, '_npx_playwright', lambda self: 'npx')
    def capture(args, **kwargs):
        png(Path(args[-1]))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(browser_qa.subprocess, 'run', capture)
    result = browser_qa.run_browser_qa(str(tmp_path), route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert result['status'] == 'partial'
    assert result['screenshots']
    assert not browser_qa.evidence_passes(result)


def test_launch_failure_closes_server_and_runtime(tmp_path, monkeypatch):
    build(tmp_path)
    stopped = []
    servers = []
    real_serve = browser_qa.BrowserQA._serve
    def serve(self):
        result = real_serve(self)
        servers.append(result[2])
        return result
    @contextmanager
    def runtime():
        def launch(**kwargs):
            raise RuntimeError('token=launch-secret')
        try:
            yield SimpleNamespace(chromium=SimpleNamespace(launch=launch))
        finally:
            stopped.append(True)
    monkeypatch.setattr(browser_qa.BrowserQA, '_serve', serve)
    monkeypatch.setattr(browser_qa.BrowserQA, '_python_playwright', lambda self: runtime)
    result = browser_qa.BrowserQA(str(tmp_path)).run()
    assert result['ok'] is False
    assert result['status'] == 'not_measured'
    assert stopped
    assert servers[0].socket.fileno() == -1
    assert 'launch-secret' not in json.dumps(result)


def test_real_clean_matrix_has_actual_viewports_and_null_lcp(tmp_path):
    build(tmp_path)
    result = browser_qa.run_browser_qa(str(tmp_path), route_expectations={
        '/': {'heading': 'Home'}, '/features': {'heading': 'Features'},
    })
    assert result['ok'] is True, result
    assert browser_qa.evidence_passes(result)
    assert result['status'] == 'passed'
    assert len(result['results']) == 10
    assert {r['actual_viewport']['width'] for r in result['results']} == {
        375, 768, 1024, 1440, 1920,
    }
    assert all(r['actual_viewport'] == r['requested_viewport'] for r in result['results'])
    assert len(set(s['path'] for s in result['screenshots'].values())) == 10
    assert result['evidence']['lcp_ms'] is None
    assert all(r['performance']['lcp_ms'] is None for r in result['results'])
    assert result['report_path'] == str(tmp_path / 'qa' / 'qa-report.json')


@pytest.mark.parametrize('html,heading,expected_failure', [
    ('<main><h1>Home</h1></main>', 'Pricing', 'route_identity'),
    ('<main></main>', 'Home', 'route_identity'),
    ('<header><h1>Home</h1></header><main>Different content</main>', 'Home', 'route_identity'),
    ('<main><h1 hidden>Home</h1></main>', 'Home', 'route_identity'),
    ('<main><h1>Home</h1></main>', None, 'route_identity'),
    (CLEAN + '<script>console.error("token=console-secret")</script>', 'Home', 'console_errors'),
    (CLEAN + '<script>throw Error("password=page-secret")</script>', 'Home', 'page_errors'),
    (CLEAN + '<script src="/missing.js?token=asset-secret"></script>', 'Home', 'network_errors'),
    (CLEAN + '<img src="/missing.png">', 'Home', 'network_errors'),
    (CLEAN + '<style>body{overflow-x:hidden}@media(max-width:400px){'
     'main{width:700px}}</style>', 'Home', 'overflow'),
    (CLEAN + '<script>if(location.pathname!=="/login")location.replace("/login")</script>',
     'Home', 'route_identity'),
])
def test_real_broken_pages_fail(tmp_path, html, heading, expected_failure):
    build(tmp_path, html)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': heading}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert result['status'] == 'failed', result
    assert expected_failure in result['results'][0]['failures']
    assert not browser_qa.evidence_passes(result)
    text = json.dumps(result)
    assert all(secret not in text for secret in ('console-secret', 'page-secret', 'asset-secret'))


def test_real_hero_header_inside_main_proves_page_identity(tmp_path):
    build(tmp_path, '<main><header><h1>Home</h1><p>Hero content.</p></header>'
                   '<section><h2>Details</h2></section></main>')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is True, result
    assert result['results'][0]['rendered_content']['heading_matched'] is True


def test_real_contained_scroller_and_hidden_elements_are_not_overflow(tmp_path):
    build(tmp_path, CLEAN + '''<div style="overflow-x:auto;width:100%">
      <div style="width:900px">Intentionally scrollable content</div></div>
      <div style="display:none;width:9999px">Hidden</div>
      <div style="visibility:hidden;position:absolute;left:-500px">Hidden</div>
      <span style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;
        overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">
        Screen-reader label</span>
      <span style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;
        overflow:hidden;clip-path:inset(50%)">Offscreen label</span>''')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is True, result
    assert result['results'][0]['overflow']['offenders'] == []


def test_real_reduced_motion_is_measured_from_navigation(tmp_path):
    build(tmp_path, CLEAN + '''<script>
      if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.querySelector('main').remove();
      }
    </script>''')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert 'reduced_motion' in result['results'][0]['failures']


def test_real_below_fold_lazy_asset_is_required(tmp_path):
    build(tmp_path, CLEAN + '<div style="height:3000px"></div>'
                            '<img src="/missing.png" loading="lazy" alt="Proof">')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert 'network_errors' in result['results'][0]['failures']


def test_real_screenshot_exception_fails_and_closes_context(tmp_path, monkeypatch):
    from playwright.sync_api import Page, BrowserContext
    build(tmp_path)
    closed = []
    close = BrowserContext.close
    def fail(*args, **kwargs):
        raise RuntimeError('cookie=session-secret')
    def track(self, *args, **kwargs):
        closed.append(True)
        return close(self, *args, **kwargs)
    monkeypatch.setattr(Page, 'screenshot', fail)
    monkeypatch.setattr(BrowserContext, 'close', track)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert result['status'] == 'failed'
    assert 'screenshot' in result['results'][0]['failures']
    assert closed
    assert 'session-secret' not in json.dumps(result)


def test_real_live_prefix_uses_remote_only_and_preserves_local_report(tmp_path, monkeypatch):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            html = CLEAN.replace('Home', 'Hosted')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    (tmp_path / 'qa').mkdir()
    local_report = tmp_path / 'qa' / 'qa-report.json'
    local_report.write_text('local-evidence')
    def forbidden(*args):
        pytest.fail('Live QA must not start local preview')
    monkeypatch.setattr(browser_qa.BrowserQA, '_serve', forbidden)
    try:
        result = browser_qa.run_browser_qa(
            str(tmp_path), f'http://127.0.0.1:{server.server_port}/app',
            route_expectations={'/': {'heading': 'Hosted'}, '/features': {'heading': 'Features'}},
            viewports=SMALL,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result['ok'] is True, result
    assert '/app/' in requests and '/app/features' in requests
    assert '/index.html' not in requests and '/features' not in requests
    assert result['report_path'] == str(tmp_path / 'qa' / 'live' / 'qa-report.json')
    assert local_report.read_text() == 'local-evidence'


def test_manifest_routes_union_inventory_and_missing_expectation_fails(tmp_path):
    build(tmp_path)
    pages = tmp_path / 'src' / 'pages'
    pages.mkdir(parents=True)
    (pages / 'Pricing.jsx').write_text('export default function Pricing() {}')
    (tmp_path / 'qa-contract.json').write_text(json.dumps({
        'version': 1, 'routes': {'/': {'heading': 'Home'}, '/features': {'heading': 'Features'}},
        'scene': {'archetype': 'floating_crystal'},
    }))
    result = browser_qa.run_browser_qa(str(tmp_path), viewports=SMALL)
    assert set(result['requested_routes']) == {'/', '/features', '/pricing'}
    assert result['ok'] is False
    pricing = next(r for r in result['results'] if r['route'] == '/pricing')
    assert 'route_identity' in pricing['failures']


@pytest.mark.parametrize('viewports', [[], [(0, 812)], [(True, 812)], [(375, 812), (375, 812)]])
def test_invalid_viewport_requests_cannot_pass(tmp_path, viewports):
    build(tmp_path)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=viewports)
    assert result['ok'] is False
    assert result['status'] == 'failed'


def test_consumer_rejects_reused_screenshot_for_different_samples(tmp_path):
    report = good_report(tmp_path)
    report['requested_routes'].append('/features')
    second = copy.deepcopy(report['results'][0])
    second['route'] = '/features'
    report['results'].append(second)
    assert not browser_qa.evidence_passes(report)


def test_consumer_rejects_contradictory_reduced_motion_evidence(tmp_path):
    report = good_report(tmp_path)
    report['results'][0]['reduced_motion'] = {'ok': False}
    assert not browser_qa.evidence_passes(report)


@pytest.mark.parametrize('css', [
    'main{overflow:hidden;width:100px}h1{transform:translateX(200px)}',
    'h1{clip-path:inset(100%)}',
    'h1{position:absolute;clip:rect(0,0,0,0)}',
])
def test_real_clipped_heading_cannot_prove_identity(tmp_path, css):
    build(tmp_path, CLEAN + f'<style>{css}</style>')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert 'route_identity' in result['results'][0]['failures']


def test_real_long_text_overflow_is_detected_even_with_body_clipping(tmp_path):
    html = CLEAN + '<style>body{overflow-x:hidden}p{white-space:nowrap}</style>'
    html = html.replace('Usable page content.', 'UnbrokenLongWord' * 30)
    build(tmp_path, html)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert 'overflow' in result['results'][0]['failures']


@pytest.mark.parametrize('broken', [False, True])
def test_real_reduced_motion_is_measured_independently(tmp_path, broken):
    html = CLEAN
    if broken:
        html += '<style>@media(prefers-reduced-motion:reduce){main{display:none}}</style>'
    build(tmp_path, html)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is not broken, result
    reduced = result['results'][0]['reduced_motion']
    assert reduced['ok'] is not broken
    assert reduced['actual_viewport'] == {'width': 375, 'height': 812}
    assert reduced['rendered_content']['ok'] is not broken


def scene_html(draw_body):
    return CLEAN + '''<section data-scene-state="requested" data-scene-frames="0"
  data-scene-draw-calls="0"><h2>Interactive 3D</h2>
  <button data-scene-enable>Enable 3D</button>
  <div data-scene-viewport></div>
  <button>Rotate right</button></section>
<script>
  const section = document.querySelector('[data-scene-state]');
  const viewport = document.querySelector('[data-scene-viewport]');
  let canvas = null;
  let ctx = null;
  let angle = 0;
  function ensureCanvas() {
    if (canvas) return;
    canvas = document.createElement('canvas');
    canvas.width = 600; canvas.height = 360;
    viewport.appendChild(canvas);
    ctx = canvas.getContext('2d');
  }
  function draw() {
    ensureCanvas();
    __DRAW__
    section.dataset.sceneFrames = '3';
    section.dataset.sceneDrawCalls = '5';
    section.dataset.sceneState = 'rendered';
  }
  document.querySelector('[data-scene-enable]').addEventListener('click', draw);
  document.querySelectorAll('button')[1].addEventListener('click', () => {
    angle += 0.6;
    draw();
  });
</script>'''.replace('__DRAW__', draw_body)


DRAW = '''ctx.fillStyle = '#0b1020'; ctx.fillRect(0, 0, 600, 360);
    ctx.fillStyle = '#34d399'; ctx.fillRect(40, 40, 180, 120);
    ctx.fillStyle = '#818cf8'; ctx.beginPath(); ctx.arc(430, 110, 60, 0, 6.28); ctx.fill();
    ctx.strokeStyle = '#fbbf24'; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(40, 300); ctx.lineTo(560, 300); ctx.stroke();
    ctx.save(); ctx.translate(300, 210); ctx.rotate(angle);
    ctx.fillStyle = '#f472b6'; ctx.fillRect(-90, -50, 180, 100); ctx.restore();'''
SCENE = scene_html(DRAW)


def scene_project(tmp_path, html=SCENE):
    build(tmp_path, html)
    (tmp_path / 'qa-contract.json').write_text(json.dumps({
        'version': 1, 'routes': {'/': {'heading': 'Home'}},
        'scene': {'archetype': 'cyber_grid'},
    }), encoding='utf-8')


def test_real_scene_proof_requires_rendered_pixels_and_interaction(tmp_path):
    scene_project(tmp_path)
    result = browser_qa.run_browser_qa(
        str(tmp_path), viewports=[{'width': 1440, 'height': 900}])
    assert result['ok'] is True, result['scene']
    assert browser_qa.evidence_passes(result)
    scene = result['scene']
    assert scene['canvas']['ok'] and scene['canvas']['deviation'] > 4
    assert Path(scene['canvas']['path']).is_file()
    assert Path(scene['interaction']['after_path']).is_file()
    assert scene['frames'] >= 1 and scene['draw_calls'] >= 1
    assert scene['interaction']['changed'] is True
    assert scene['mobile_fallback'] == {
        'state': 'requested', 'canvas_count': 0, 'enable_visible': True, 'ok': True,
    }


def test_real_blank_scene_cannot_pass(tmp_path):
    blank = scene_html('ctx.clearRect(0, 0, 600, 360);')
    scene_project(tmp_path, blank)
    result = browser_qa.run_browser_qa(
        str(tmp_path), viewports=[{'width': 1440, 'height': 900}])
    assert result['ok'] is False
    assert 'scene_blank_canvas' in result['scene']['failures']
    assert not browser_qa.evidence_passes(result)


def test_real_static_scene_without_interaction_change_cannot_pass(tmp_path):
    static = SCENE.replace("    angle += 0.6;\n    draw();\n", "    draw();\n")
    scene_project(tmp_path, static)
    result = browser_qa.run_browser_qa(
        str(tmp_path), viewports=[{'width': 1440, 'height': 900}])
    assert result['ok'] is False
    assert 'scene_interaction_not_visible' in result['scene']['failures']


def test_real_wrong_actual_viewport_blocks_pass(tmp_path, monkeypatch):
    from playwright.sync_api import Browser
    build(tmp_path)
    original = Browser.new_context
    def wrong_width(self, **kwargs):
        kwargs['viewport'] = {'width': 1440, 'height': 900}
        return original(self, **kwargs)
    monkeypatch.setattr(Browser, 'new_context', wrong_width)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert 'viewport' in result['results'][0]['failures']
    assert result['results'][0]['actual_viewport']['width'] == 1440


def test_real_corrupt_image_with_success_http_status_fails(tmp_path):
    build(tmp_path, CLEAN + '<img src="/corrupt.png">')
    (tmp_path / 'dist' / 'corrupt.png').write_text('not an image')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert result['results'][0]['network_errors']


@pytest.mark.parametrize('resource,should_fail', [
    ('fetch("https://telemetry.invalid/events?token=private").catch(()=>{})', False),
    ('fetch("/api/data?token=private").catch(()=>{})', True),
    ('const s=document.createElement("script");s.src="https://cdn.invalid/app.js";'
     'document.head.appendChild(s)', True),
])
def test_real_network_errors_are_required_resource_scoped(tmp_path, monkeypatch, resource, should_fail):
    from playwright.sync_api import Browser
    build(tmp_path, CLEAN + f'<script>{resource}</script>')
    original = Browser.new_context
    def intercepted(self, **kwargs):
        context = original(self, **kwargs)
        for pattern in ('https://telemetry.invalid/**', 'https://cdn.invalid/**', '**/api/data?*'):
            context.route(pattern, lambda route: route.fulfill(
                status=503, headers={'access-control-allow-origin': '*'}, body='payload-secret',
            ))
        return context
    monkeypatch.setattr(Browser, 'new_context', intercepted)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is not should_fail, result
    assert bool(result['results'][0]['network_errors']) is should_fail
    assert 'private' not in json.dumps(result) and 'payload-secret' not in json.dumps(result)


def test_real_diagnostics_are_bounded_and_drop_payloads(tmp_path):
    build(tmp_path, CLEAN + '''<script>for(let i=0;i<100;i++)console.error(
    'Authorization: Bearer opaque-secret', {cookie:'session-secret', body:'payload-secret'},
    'https://user:password@host.test/path?token=query-secret#fragment-secret');</script>''')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    errors = result['results'][0]['console_errors']
    assert 1 <= len(errors) <= 20
    assert all(len(message) <= 500 for message in errors)
    persisted = Path(result['report_path']).read_text()
    assert all(secret not in persisted for secret in (
        'opaque-secret', 'session-secret', 'payload-secret', 'query-secret', 'fragment-secret',
        'user:password',
    ))


def test_real_normal_completion_releases_preview_socket(tmp_path, monkeypatch):
    build(tmp_path)
    servers = []
    original = browser_qa.BrowserQA._serve
    def capture(self):
        result = original(self)
        servers.append(result[2])
        return result
    monkeypatch.setattr(browser_qa.BrowserQA, '_serve', capture)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is True, result
    assert servers[0].socket.fileno() == -1
    with socket.socket() as probe:
        assert probe.connect_ex(servers[0].server_address) != 0


@pytest.mark.parametrize('source', [
    '{"version":1,"routes":{"/":{"heading":"Wrong"},"/":{"heading":"Home"}}}',
    '{"version":true,"routes":{"/":{"heading":"Home"}}}',
    '{"version":2,"routes":{"/":{"heading":"Home"}}}',
    'not-json',
])
def test_invalid_manifest_cannot_prove_route_matrix(tmp_path, source):
    build(tmp_path)
    (tmp_path / 'qa-contract.json').write_text(source)
    result = browser_qa.run_browser_qa(str(tmp_path), viewports=SMALL)
    assert result['ok'] is False
    assert result['status'] == 'failed'


def test_real_console_resource_lookalike_is_not_ignored(tmp_path):
    build(tmp_path, CLEAN + '<script>console.error("Failed to load resource: app failure")</script>')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert result['results'][0]['console_errors']


def test_real_errors_do_not_leak_between_route_samples(tmp_path):
    build(tmp_path, CLEAN + '''<script>if(location.pathname==='/'){
      console.error('Home-only error'); fetch('/missing.json').catch(()=>{});
    }</script>''')
    result = browser_qa.run_browser_qa(str(tmp_path), route_expectations={
        '/': {'heading': 'Home'}, '/features': {'heading': 'Features'},
    }, viewports=SMALL)
    home, features = result['results']
    assert result['ok'] is False and home['ok'] is False
    assert features['ok'] is True
    assert features['console_errors'] == features['network_errors'] == []


@pytest.mark.parametrize('mode', ['corrupt', 'missing'])
def test_real_screenshot_must_be_fresh_and_readable(tmp_path, monkeypatch, mode):
    from playwright.sync_api import Page
    build(tmp_path)
    qa = browser_qa.BrowserQA(str(tmp_path), route_expectations={'/': {'heading': 'Home'}},
                               viewports=SMALL)
    qa.qa_dir.mkdir(parents=True)
    path = qa._shot_path('/', SMALL[0])
    png(path)  # Stale evidence from a previous run must not rescue this capture.
    def broken(self, **kwargs):
        if mode == 'corrupt':
            Path(kwargs['path']).write_bytes(b'\x89PNG\r\n\x1a\n')
        return b''
    monkeypatch.setattr(Page, 'screenshot', broken)
    result = qa.run()
    assert result['ok'] is False
    assert 'screenshot' in result['results'][0]['failures']


def test_real_full_page_capture_includes_below_fold_content(tmp_path):
    build(tmp_path, CLEAN + '<section style="height:1800px">Below the fold</section>')
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is True, result
    assert result['results'][0]['screenshot']['height'] > 1800


def test_real_request_failure_and_late_heading_are_observed(tmp_path, monkeypatch):
    from playwright.sync_api import Browser
    build(tmp_path, CLEAN.replace('<h1>Home</h1>', '<h1>Loading</h1>') + '''<script>
    setTimeout(()=>document.querySelector('h1').textContent='Home', 150);
    fetch('/api/failure').catch(()=>{});</script>''')
    original = Browser.new_context
    def intercepted(self, **kwargs):
        context = original(self, **kwargs)
        context.route('**/api/failure', lambda route: route.abort('failed'))
        return context
    monkeypatch.setattr(Browser, 'new_context', intercepted)
    result = browser_qa.run_browser_qa(str(tmp_path),
                                      route_expectations={'/': {'heading': 'Home'}},
                                      viewports=SMALL)
    assert result['ok'] is False
    assert result['results'][0]['rendered_content']['ok'] is True
    assert result['results'][0]['network_errors']


APP_SHELL = '''<!doctype html><html><head><meta name="viewport"
content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"></head>
<body><header>Workspace navigation</header><main><h1 id="title">Sign in</h1>
<p>Authenticated content loaded from the QA fixture.</p></main>
<script>
const titles = {
  '/login': 'Sign in', '/register': 'Create your account',
  '/dashboard': 'Your workspace', '/records': 'All records',
  '/settings': 'Account settings',
};
const path = location.pathname;
const title = document.getElementById('title');
let token = null;
try { token = localStorage.getItem('token'); } catch (error) { token = null; }
const appRoute = !['/login', '/register'].includes(path);
if (appRoute && token !== 'qa-token') {
  title.textContent = 'Sign in';
} else if (path === '/dashboard' || path === '/records') {
  title.textContent = 'Loading';
  fetch('http://localhost:5000/api/v1/records', {
    headers: { Authorization: 'Bearer ' + token },
  }).then((response) => response.json()).then((json) => {
    if (!json || json.success !== true || !Array.isArray(json.data) || !json.data.length) {
      title.textContent = 'Fixture missing';
      return;
    }
    title.textContent = titles[path];
  }).catch(() => { title.textContent = 'Fixture missing'; });
} else {
  title.textContent = titles[path] || 'Sign in';
}
</script></body></html>'''

AUTH_FIXTURE = {'GET /records': {
    'success': True,
    'data': [{'id': 'r1', 'title': 'First record', 'status': 'draft'}],
}}


def build_app_shell(tmp_path):
    return build(tmp_path, APP_SHELL)


def test_app_shell_authenticated_routes_render_with_fixtures(tmp_path):
    build_app_shell(tmp_path)
    result = browser_qa.run_browser_qa(
        str(tmp_path),
        route_expectations=app_route_expectations('Northstar'),
        viewports=SMALL,
        auth_token='qa-token',
        api_fixtures=AUTH_FIXTURE,
    )
    assert result['ok'] is True, result
    assert len(result['results']) == 5
    text = json.dumps(result)
    assert 'qa-token' not in text and 'First record' not in text


def test_app_shell_without_the_qa_token_cannot_pass(tmp_path):
    build_app_shell(tmp_path)
    missing_token = browser_qa.run_browser_qa(
        str(tmp_path),
        route_expectations={'/dashboard': {'heading': 'Your workspace'}},
        viewports=SMALL,
        api_fixtures=AUTH_FIXTURE,
    )
    assert missing_token['ok'] is False


API_STATUS = '''<!doctype html><html><head><meta name="viewport"
content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"></head>
<body><main><h1 id="title">Waiting</h1></main>
<script>
fetch('http://localhost:5000/api/v1/records').then((response) => {
  document.getElementById('title').textContent =
    response.status === 404 ? 'API unavailable' : 'Unexpected response';
}).catch(() => { document.getElementById('title').textContent = 'Connection refused'; });
</script></body></html>'''


@pytest.mark.parametrize('options', [
    {'auth_token': 'qa-token'},
    {'api_fixtures': {}},
])
def test_local_qa_without_a_matching_fixture_returns_404_not_a_real_api(tmp_path, options):
    """A seeded token or declared fixture set must fail closed, not reach localhost:5000."""
    build(tmp_path, API_STATUS)
    result = browser_qa.run_browser_qa(
        str(tmp_path),
        route_expectations={'/': {'heading': 'API unavailable'}},
        viewports=SMALL,
        **options,
    )
    assert result['ok'] is True, result


def test_live_qa_rejects_explicit_fixtures_without_faking_the_backend(tmp_path):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(CLEAN.encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = browser_qa.run_browser_qa(
            str(tmp_path), f'http://127.0.0.1:{server.server_port}',
            route_expectations={'/': {'heading': 'Home'}},
            viewports=SMALL, auth_token='qa-token', api_fixtures=AUTH_FIXTURE,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result['ok'] is False
    assert result['status'] == 'failed'
    assert requests == []
    assert 'qa-token' not in json.dumps(result)


def test_live_qa_rejects_contract_declared_fixtures(tmp_path):
    build(tmp_path)
    (tmp_path / 'qa-contract.json').write_text(json.dumps({
        'version': 1, 'routes': {'/': {'heading': 'Home'}},
        'auth': {'storage': {'token': 'contract-secret'}},
        'fixtures': AUTH_FIXTURE,
    }))
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(CLEAN.encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = browser_qa.run_browser_qa(
            str(tmp_path), f'http://127.0.0.1:{server.server_port}', viewports=SMALL)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result['ok'] is False
    assert result['status'] == 'failed'
    assert requests == []
    assert 'contract-secret' not in json.dumps(result)


def test_local_manifest_auth_and_fixtures_are_applied(tmp_path):
    build_app_shell(tmp_path)
    (tmp_path / 'app-contract.json').write_text(json.dumps({
        'version': 1, 'web': 'web_app', 'pwa': False, 'mobile': None,
    }))
    (tmp_path / 'qa-contract.json').write_text(json.dumps({
        'version': 1,
        'routes': app_route_expectations('Northstar'),
        'auth': {'storage': {'token': 'qa-token'}},
        'fixtures': AUTH_FIXTURE,
    }))
    result = browser_qa.run_browser_qa(str(tmp_path), viewports=SMALL)
    assert result['ok'] is True, result
    assert result['requested_routes'] == [
        '/login', '/register', '/dashboard', '/records', '/settings']
    assert 'qa-token' not in json.dumps(result)


@pytest.mark.parametrize('fixtures', [
    {'GET': {'success': True}},
    {'FETCH /records': {'success': True}},
    {'GET records': {'success': True}},
    {1: {'success': True}},
    ['GET /records'],
])
def test_invalid_fixture_contracts_fail_closed(tmp_path, fixtures):
    build_app_shell(tmp_path)
    result = browser_qa.run_browser_qa(
        str(tmp_path), route_expectations={'/login': {'heading': 'Sign in'}},
        viewports=SMALL, auth_token='qa-token', api_fixtures=fixtures)
    assert result['ok'] is False
    assert result['status'] == 'failed'


PWA_FIXTURES = {
    'GET /records': {
        'success': True,
        'data': [{'id': 'r1', 'title': 'First record', 'status': 'draft'}],
    },
    'POST /records': {
        'success': True,
        'data': {'id': 'r2', 'title': 'Queued record', 'status': 'draft'},
    },
}

ACTIVE_WORKER_VERSION = """async () => {
  const worker = navigator.serviceWorker.controller;
  if (!worker) return '';
  return await new Promise((resolve) => {
    const channel = new MessageChannel();
    const timer = setTimeout(() => resolve(''), 3000);
    channel.port1.onmessage = (event) => {
      clearTimeout(timer);
      resolve(String((event.data && event.data.version) || ''));
    };
    worker.postMessage({ type: 'GET_VERSION' }, [channel.port2]);
  });
}"""


def qa_jwt(user_id):
    def encode(payload):
        raw = json.dumps(payload, separators=(',', ':')).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()

    header = encode({'alg': 'HS256', 'typ': 'JWT'})
    claims = encode({'id': user_id, 'email': f'{user_id}@example.test'})
    return f'{header}.{claims}.signature'


def set_session(page, user_id):
    page.evaluate(
        "({ token, user }) => {"
        " localStorage.setItem('token', token);"
        " localStorage.setItem('user', user);"
        "}",
        {
            'token': qa_jwt(user_id),
            'user': json.dumps({
                'id': user_id, 'name': user_id, 'email': f'{user_id}@example.test',
            }),
        },
    )


def wait_for(page, predicate, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        page.wait_for_timeout(100)
    return predicate()


@pytest.fixture(scope='session')
def real_pwa_project(tmp_path_factory):
    """Generate and build the real PWA `web_app`; no hand-written fixture app."""
    root = tmp_path_factory.mktemp('real-pwa-app')
    contract = resolve_generation_contract({
        'app': {'web': 'web_app', 'pwa': True, 'mobile': None},
    })
    result = FullStackUltraEngine().generate_project(
        str(root), prompt='Build a records web app', brand_name='Northstar',
        generation_contract=contract)
    assert result['success'] is True, result
    frontend = root / 'frontend'
    npm = shutil.which('npm') or 'npm'
    for args in (['install', '--no-audit', '--no-fund', '--prefer-offline'],
                 ['run', 'build']):
        completed = subprocess.run(
            [npm, *args], cwd=str(frontend), capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=600, shell=False,
            env={**os.environ, 'CI': '1'})
        assert completed.returncode == 0, (
            completed.stdout[-3000:], completed.stderr[-3000:])
    assert (frontend / 'dist' / 'index.html').is_file()
    assert (frontend / 'dist' / 'sw.js').is_file()
    assert (frontend / 'src' / 'offlineQueue.js').is_file()
    assert (frontend / 'src' / 'pwa.js').is_file()
    return root


def serve_pwa(project, *, auth_token='', api_fixtures=None):
    qa = browser_qa.BrowserQA(
        str(project), auth_token=auth_token, api_fixtures=api_fixtures)
    qa._resolve_fixtures(None)
    host, port, server = qa._serve()
    return qa, f'http://{host}:{port}', server


def test_real_generated_pwa_proof_controls_worker_offline_and_queue(real_pwa_project):
    result = browser_qa.run_browser_qa(
        str(real_pwa_project),
        route_expectations=app_route_expectations('Northstar'),
        viewports=SMALL,
        auth_token=qa_jwt('user-a'),
        api_fixtures=PWA_FIXTURES,
    )
    assert result['ok'] is True, (result['failures'], result.get('pwa'))
    assert result['requested_pwa'] is True
    pwa = result['pwa']
    assert pwa['ok'] is True, pwa
    assert pwa['surface'] == 'web_app'
    assert pwa['worker_controlled'] is True
    assert "offline" in pwa['offline_heading'].lower()
    assert pwa['online_recovered'] is True
    queue = pwa['queue']
    assert queue['applicable'] is True
    assert queue['ui_queued'] is True
    assert queue['enqueued'] == 1
    assert queue['posts'] == 1
    assert queue['post_ids'] == [queue['client_id']]
    assert len(queue['client_id']) == 36
    assert queue['cleared'] is True
    assert queue['ui_cleared'] is True
    # The shipped queue's 50-record cap and its failure/retry behaviour are
    # measured through the real Records page and IndexedDB, not markers.
    assert queue['max_records'] == 50
    assert queue['max_enforced'] is True
    assert queue['max_kept'] == 50
    assert queue['retry_attempts'] == 3
    assert queue['failed_flush_kept'] is True
    assert queue['no_success_before_confirmation'] is True
    assert 'Sync pending' in queue['banner_copy']
    assert pwa['failures'] == []
    shot = Path(pwa['offline_screenshot']['path'])
    assert shot.is_file()
    assert browser_qa._png_evidence(shot)['ok']
    assert browser_qa.evidence_passes(result)
    assert 'qa-token' not in json.dumps(result)
    assert qa_jwt('user-a') not in json.dumps(result)


def test_real_generated_pwa_prompts_for_worker_update_and_reloads(real_pwa_project):
    from playwright.sync_api import sync_playwright

    qa, base, server = serve_pwa(real_pwa_project)
    sw_path = real_pwa_project / 'frontend' / 'dist' / 'sw.js'
    original = sw_path.read_text(encoding='utf-8')
    updated = original.replace("-v1'", "-v2'", 1)
    assert updated != original
    expected_version = re.search(r"const VERSION = '([^']+)'", updated).group(1)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 900})
            qa._configure_context(context)
            page = context.new_page()
            page.set_default_timeout(10000)
            page.goto(base + '/login', wait_until='domcontentloaded', timeout=30000)
            page.wait_for_function(
                "() => 'serviceWorker' in navigator"
                " && navigator.serviceWorker.ready.then(() => true)",
                timeout=20000,
            )
            page.reload(wait_until='domcontentloaded', timeout=30000)
            page.wait_for_function(
                '() => !!navigator.serviceWorker.controller', timeout=10000)

            sw_path.write_text(updated, encoding='utf-8')
            page.evaluate(
                '() => navigator.serviceWorker.getRegistration().then(r => r.update())')
            page.wait_for_selector('#pwa-update-prompt', state='visible', timeout=20000)
            region = page.locator('#pwa-update-prompt')
            assert region.get_attribute('role') == 'status'
            assert region.get_attribute('aria-live') == 'polite'
            assert region.get_attribute('aria-label') == 'Application update available'
            button = page.get_by_role('button', name='Reload to update')
            assert button.is_visible() and button.is_enabled()
            with page.expect_navigation(wait_until='domcontentloaded', timeout=20000):
                button.click()
            page.wait_for_function(
                '() => !!navigator.serviceWorker.controller', timeout=10000)
            assert page.evaluate(ACTIVE_WORKER_VERSION) == expected_version
            context.close()
            browser.close()
    finally:
        sw_path.write_text(original, encoding='utf-8')
        server.shutdown()
        server.server_close()


def test_real_generated_pwa_queue_is_user_scoped_and_signout_clears(real_pwa_project):
    from playwright.sync_api import sync_playwright

    posts, failed, auth = [], [], []
    qa, base, server = serve_pwa(real_pwa_project, api_fixtures=PWA_FIXTURES)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 900})
            qa._configure_context(
                context, pwa_posts=posts, pwa_failed_posts=failed, pwa_auth=auth)
            page = context.new_page()
            page.set_default_timeout(10000)
            page.goto(base + '/login', wait_until='domcontentloaded', timeout=30000)
            set_session(page, 'user-a')
            page.goto(base + '/records', wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector('#record-title', state='visible', timeout=10000)

            context.set_offline(True)
            page.wait_for_function('() => navigator.onLine === false', timeout=5000)
            page.locator('#record-title').fill('User A offline record')
            page.locator('#record-body').fill('Owned by user A.')
            page.get_by_role('button', name='Create record').click()
            page.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            first_rows = page.evaluate(browser_qa._QUEUE_ROWS_JS)
            assert len(first_rows) == 1
            assert first_rows[0]['owner'] == 'user-a'
            first_id = first_rows[0]['id']
            assert posts == []

            # A different signed-in user must not see or flush the first queue.
            set_session(page, 'user-b')
            context.set_offline(False)
            page.reload(wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector('#record-title', state='visible', timeout=10000)
            page.wait_for_timeout(800)
            assert posts == []
            assert page.evaluate(browser_qa._QUEUE_ROWS_JS) == first_rows
            assert page.evaluate(
                "() => document.querySelector('#record-queue')?.dataset.queueCount"
            ) == '0'

            # The owner can still flush the record with the owner's token.
            set_session(page, 'user-a')
            page.reload(wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector('#record-title', state='visible', timeout=10000)
            assert wait_for(page, lambda: len(posts) == 1), posts
            assert posts[0]['id'] == first_id
            assert auth[-1] == f'Bearer {qa_jwt("user-a")}'
            assert wait_for(page, lambda: page.evaluate(browser_qa._QUEUE_ROWS_JS) == [])

            # Signing out discards the signed-out user's pending queue.
            context.set_offline(True)
            page.wait_for_function('() => navigator.onLine === false', timeout=5000)
            page.locator('#record-title').fill('User A unsigned record')
            page.locator('#record-body').fill('Must never flush under user B.')
            page.get_by_role('button', name='Create record').click()
            page.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            pending = page.evaluate(browser_qa._QUEUE_ROWS_JS)
            assert len(pending) == 1 and pending[0]['owner'] == 'user-a'
            unsigned_id = pending[0]['id']
            page.get_by_role('button', name='Sign out').click()
            page.wait_for_function('() => location.pathname === "/login"', timeout=8000)
            assert wait_for(page, lambda: page.evaluate(browser_qa._QUEUE_ROWS_JS) == [])

            set_session(page, 'user-b')
            context.set_offline(False)
            page.goto(base + '/records', wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector('#record-title', state='visible', timeout=10000)
            page.wait_for_timeout(800)
            assert len(posts) == 1
            assert unsigned_id not in [payload.get('id') for payload in posts]
            assert page.evaluate(browser_qa._QUEUE_ROWS_JS) == []
            context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_real_generated_pwa_flushes_at_boot_and_retries_bounded(real_pwa_project):
    from playwright.sync_api import sync_playwright

    posts, failed, auth = [], [], []
    qa, base, server = serve_pwa(real_pwa_project, api_fixtures=PWA_FIXTURES)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 900})
            qa._configure_context(
                context, pwa_posts=posts, pwa_failed_posts=failed, pwa_auth=auth)
            page = context.new_page()
            page.set_default_timeout(10000)
            page.goto(base + '/login', wait_until='domcontentloaded', timeout=30000)
            set_session(page, 'user-a')
            page.goto(base + '/records', wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector('#record-title', state='visible', timeout=10000)

            # Queue while offline, close the page, then boot a fresh page online:
            # no `online` event can explain the flush, only the boot sync.
            context.set_offline(True)
            page.wait_for_function('() => navigator.onLine === false', timeout=5000)
            page.locator('#record-title').fill('Boot flush record')
            page.locator('#record-body').fill('Sent by the boot sync.')
            page.get_by_role('button', name='Create record').click()
            page.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            boot_id = page.evaluate(browser_qa._QUEUE_ROWS_JS)[0]['id']
            page.close()
            context.set_offline(False)
            booted = context.new_page()
            booted.set_default_timeout(10000)
            booted.goto(base + '/dashboard', wait_until='domcontentloaded', timeout=30000)
            assert wait_for(booted, lambda: len(posts) == 1), posts
            assert posts[0]['id'] == boot_id
            assert wait_for(
                booted, lambda: booted.evaluate(browser_qa._QUEUE_ROWS_JS) == [])

            # One failed server response is retried inside the same flush.
            booted.goto(base + '/records', wait_until='domcontentloaded', timeout=30000)
            booted.wait_for_selector('#record-title', state='visible', timeout=10000)
            context.set_offline(True)
            booted.wait_for_function('() => navigator.onLine === false', timeout=5000)
            booted.locator('#record-title').fill('Retried record')
            booted.locator('#record-body').fill('First POST fails, second succeeds.')
            booted.get_by_role('button', name='Create record').click()
            booted.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            retry_id = booted.evaluate(browser_qa._QUEUE_ROWS_JS)[0]['id']
            qa._pwa_fail_posts = 1
            context.set_offline(False)
            assert wait_for(booted, lambda: len(posts) == 2), (posts, failed)
            assert len(failed) == 1
            assert failed[0]['id'] == retry_id
            assert posts[1]['id'] == retry_id
            assert wait_for(
                booted, lambda: booted.evaluate(browser_qa._QUEUE_ROWS_JS) == [])

            # A server that never confirms gets exactly three bounded attempts.
            context.set_offline(True)
            booted.wait_for_function('() => navigator.onLine === false', timeout=5000)
            booted.locator('#record-title').fill('Bounded failure record')
            booted.locator('#record-body').fill('Never confirmed by the server.')
            booted.get_by_role('button', name='Create record').click()
            booted.wait_for_function(
                "() => document.querySelector('#record-queue')?.dataset.queueCount === '1'",
                timeout=8000,
            )
            bounded_id = booted.evaluate(browser_qa._QUEUE_ROWS_JS)[0]['id']
            failed_before = len(failed)
            qa._pwa_fail_posts = 3
            context.set_offline(False)
            assert wait_for(booted, lambda: len(failed) >= failed_before + 3), failed
            booted.wait_for_timeout(600)
            assert len(failed) == failed_before + 3
            kept = booted.evaluate(browser_qa._QUEUE_ROWS_JS)
            assert len(kept) == 1 and kept[0]['id'] == bounded_id
            banner = booted.locator('#pwa-connection-banner').inner_text()
            assert 'Sync pending' in banner
            assert 'when the connection returns' not in banner.lower()
            assert all(header == f'Bearer {qa_jwt("user-a")}' for header in auth)
            qa._pwa_fail_posts = 0
            booted.evaluate(browser_qa._QUEUE_CLEAR_JS)
            context.close()
            browser.close()
    finally:
        qa._pwa_fail_posts = 0
        server.shutdown()
        server.server_close()


def test_evidence_requires_the_pwa_proof_when_requested(tmp_path):
    report = good_report(tmp_path)
    report['requested_pwa'] = True
    assert not browser_qa.evidence_passes(report)
    report['pwa'] = {
        'ok': True, 'failures': [], 'worker_controlled': True,
        'offline_heading': "You're offline", 'online_recovered': True,
        'queue': {
            'applicable': True, 'enqueued': 1, 'posts': 1, 'post_ids': ['one'],
            'client_id': 'one', 'cleared': True, 'max_records': 50,
            'max_enforced': True, 'retry_attempts': 3, 'failed_flush_kept': True,
            'no_success_before_confirmation': True,
        },
    }
    assert browser_qa.evidence_passes(report)
    report['pwa']['queue']['posts'] = 2
    assert not browser_qa.evidence_passes(report)
    report['pwa']['queue']['posts'] = 1
    report['pwa']['queue']['max_enforced'] = False
    assert not browser_qa.evidence_passes(report)
    report['pwa']['queue']['max_enforced'] = True
    report['pwa']['queue']['no_success_before_confirmation'] = False
    assert not browser_qa.evidence_passes(report)


def test_live_pwa_proof_is_not_measured_and_never_faked(tmp_path):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(CLEAN.encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = browser_qa.run_browser_qa(
            str(tmp_path), f'http://127.0.0.1:{server.server_port}',
            route_expectations={'/': {'heading': 'Home'}},
            viewports=SMALL, requested_pwa=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result['ok'] is False
    assert result['status'] == 'failed'
    assert result['pwa']['status'] == 'not_measured'
    assert result['pwa']['ok'] is False
    assert result['pwa']['worker_controlled'] is False
    # The normal matrix performs one navigation, and its independent
    # reduced-motion proof performs a second. The live PWA stage must add none:
    # a third request would mean it opened a context and navigated before the
    # live guard returned.
    assert requests == ['/', '/']
    assert not browser_qa.evidence_passes(result)


def test_live_pwa_stage_returns_not_measured_without_a_browser(tmp_path):
    class NoBrowser:
        def new_context(self, *args, **kwargs):
            raise AssertionError('live PWA must not open a browser context')

    qa = browser_qa.BrowserQA(
        str(tmp_path), 'http://127.0.0.1:9', requested_pwa=True)
    qa._app_surface = 'web_app'
    result = qa._measure_pwa(
        NoBrowser(), 'http://127.0.0.1:9',
        {'/dashboard': {'heading': 'Your workspace'}},
    )
    assert result['status'] == 'not_measured'
    assert result['ok'] is False
    assert result['worker_controlled'] is False
    assert result['route'] == '/dashboard'
    assert result['failures']


def _qa_run_report(tmp_path, screenshot_path):
    """The report in exactly the shape `run()` hands to `_finish`. The skeleton comes
    from a real `run()` against an empty project — which fails closed at "No build
    output found to QA" — rather than from a retyped literal, so a key added to the
    product cannot quietly turn this fixture into a lie."""
    empty = tmp_path / 'empty-project'
    empty.mkdir()
    report = browser_qa.BrowserQA(str(empty)).run()
    assert report['failures'] == ['No build output found to QA.'], report['failures']
    vp = {'width': 375, 'height': 812}
    sample = good_report(tmp_path)['results'][0]
    sample['screenshot'] = {'ok': True, 'path': str(screenshot_path)}
    report.update(
        failures=[], requested_routes=['/'], requested_viewports=[vp],
        results=[sample], report_path=str(tmp_path / 'qa' / 'qa-report.json'),
    )
    return report


def test_a_qa_run_leaves_only_the_captures_it_measured(tmp_path):
    """`qa/qa-report.json` and `qa/route-<hash>-<WxH>.png` are both named by their
    inputs, so the isolated one-sample re-run of the website-only representative
    replaced a 35-sample report and left all 34 of its captures beside it — a buyer
    counting files against verdicts reads 35 proven samples where one was measured."""
    from PIL import Image

    qa = browser_qa.BrowserQA(str(tmp_path))
    qa.qa_dir.mkdir(parents=True)
    own = qa.qa_dir / 'route-8a5edab282632443-375x812.png'
    earlier = qa.qa_dir / 'route-7394a2bb766646ca-1920x1080.png'
    Image.new('RGB', (375, 812), 'white').save(own)
    Image.new('RGB', (1920, 1080), 'white').save(earlier)
    (qa.qa_dir / 'qa-report.json').write_text('{"ok": true}', encoding='utf-8')
    report = _qa_run_report(tmp_path, own)

    qa._finish(report)

    assert report['ok'] is True, report['failures']
    assert report['failures'] == []
    assert not earlier.is_file(), 'an earlier run capture was left beside this report'
    assert own.is_file(), 'this run lost the capture it measured'
    written = json.loads(Path(report['report_path']).read_text(encoding='utf-8'))
    assert written['evidence']['viewport_captures'] == 1


def test_a_capture_that_cannot_be_removed_keeps_its_run_from_being_believed(tmp_path):
    """A capture held by another process is the one case where the directory would
    describe a run that never happened, so the run fails closed instead of shipping a
    folder full of somebody else's screens. The blocker is a real `OSError` from the
    operating system (`stale.png` is a directory), not a patched `unlink`."""
    qa = browser_qa.BrowserQA(str(tmp_path))
    qa.qa_dir.mkdir(parents=True)
    from PIL import Image
    own = qa.qa_dir / 'route-8a5edab282632443-375x812.png'
    Image.new('RGB', (375, 812), 'white').save(own)
    (qa.qa_dir / 'stale-from-an-earlier-run.png').mkdir()
    report = _qa_run_report(tmp_path, own)

    qa._finish(report)

    assert report['ok'] is False
    assert any(
        'QA capture from an earlier run is still beside this report' in failure
        and 'stale-from-an-earlier-run.png' in failure
        for failure in report['failures']
        if isinstance(failure, str)
    ), report['failures']
    assert own.is_file(), 'this run lost the capture it measured'
    written = json.loads(Path(report['report_path']).read_text(encoding='utf-8'))
    assert written['ok'] is False
