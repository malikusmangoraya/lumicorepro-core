"""Real scene emission and trusted local asset boundary regressions."""
import json
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.modern_3d_engine import Modern3DWebsiteEngine


def frontend(tmp_path, nested=True, react='^19.0.0'):
    root = tmp_path / 'frontend' if nested else tmp_path
    (root / 'src').mkdir(parents=True)
    (root / 'package.json').write_text(json.dumps({
        'dependencies': {'react': react, 'react-dom': react, 'existing': '1.0.0'},
        'scripts': {'build': 'vite build'},
    }))
    return root


def model_document(uri='mesh.bin'):
    return {
        'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
        'nodes': [{'mesh': 0}], 'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
        'buffers': [{'byteLength': 36, **({'uri': uri} if uri is not None else {})}],
        'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 36}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3,
                       'type': 'VEC3', 'min': [-1, -1, 0], 'max': [1, 1, 0]}],
    }


def triangle_bytes():
    return struct.pack('<9f', -1, -1, 0, 1, -1, 0, 0, 1, 0)


def glb_bytes(document=None):
    payload = json.dumps(document or model_document(None)).encode()
    payload += b' ' * (-len(payload) % 4)
    binary = triangle_bytes()
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(payload) + len(binary))
            + struct.pack('<II', len(payload), 0x4E4F534A) + payload
            + struct.pack('<II', len(binary), 0x004E4942) + binary)


def inject(tmp_path, **kwargs):
    return Modern3DWebsiteEngine().inject_3d_experience(str(tmp_path), **kwargs)


@pytest.mark.parametrize('nested', [True, False])
@pytest.mark.parametrize('react,fiber,drei', [('^19.0.0', '^9.', '^10.'), ('^18.2.0', '^8.', '^9.')])
def test_detects_package_src_not_motion_directory_and_adds_only_scene_deps(
    tmp_path, nested, react, fiber, drei,
):
    root = frontend(tmp_path, nested, react)
    result = inject(tmp_path)
    assert result['success'] is True
    assert result['scene'] == {'archetype': 'floating_crystal'}
    assert (root / 'src/components/motion/Modern3DScene.jsx').is_file()
    assert (root / 'src/components/motion/SceneCanvas.jsx').is_file()
    package = json.loads((root / 'package.json').read_text())
    assert package['dependencies']['react'] == react
    assert package['dependencies']['existing'] == '1.0.0'
    assert package['dependencies']['@react-three/fiber'].startswith(fiber)
    assert package['dependencies']['@react-three/drei'].startswith(drei)
    assert set(package['dependencies']) == {
        'react', 'react-dom', 'existing', 'three', '@react-three/fiber', '@react-three/drei',
    }
    assert all((tmp_path / name).is_file() for name in result['files'])
    assert not (root / 'node_modules').exists()
    if nested:
        assert not (tmp_path / 'src').exists()


@pytest.mark.parametrize('archetype', ['holographic_bento', 'unknown', '', None])
def test_unknown_or_css_scene_never_falls_through(tmp_path, archetype):
    root = frontend(tmp_path)
    before = (root / 'package.json').read_bytes()
    result = inject(tmp_path, archetype=archetype)
    assert result['success'] is False
    assert result['files'] == []
    assert not (root / 'src/components').exists()
    assert (root / 'package.json').read_bytes() == before
    with pytest.raises(ValueError, match='scene'):
        Modern3DWebsiteEngine().generate_component_code(archetype)


def test_missing_frontend_fails_without_creating_one(tmp_path):
    assert inject(tmp_path)['success'] is False
    assert list(tmp_path.iterdir()) == []


def test_product_requires_model_before_writing(tmp_path):
    root = frontend(tmp_path)
    result = inject(tmp_path, archetype='product_viewer')
    assert result['success'] is False
    assert 'model' in result['error'].lower()
    assert not (root / 'src/components').exists()


@pytest.mark.parametrize('content', [b'not a model', b'glTF',
    struct.pack('<4sII', b'glTF', 1, 12),
    glb_bytes()[:-4], glb_bytes().replace(b'2.0', b'1.0'),
    glb_bytes().replace(b'JSON', b'FAIL'),
])
def test_rejects_malformed_glb_before_outputs(tmp_path, content):
    root = frontend(tmp_path)
    model = tmp_path / 'private-model.glb'
    model.write_bytes(content)
    result = inject(tmp_path, archetype='product_viewer', model_path=str(model))
    assert result['success'] is False
    assert str(model) not in str(result)
    assert not (root / 'public').exists()
    assert not (root / 'src/components').exists()


@pytest.mark.parametrize('uri', ['../secret.bin', '/secret.bin', 'C:/secret.bin',
    'https://example.com/mesh.bin', '//example.com/mesh.bin', 'file:///secret.bin',
    '%2e%2e/secret.bin', 'sub/../../secret.bin', 'sub\\mesh.bin', 'mesh.js',
    'data:text/javascript;base64,YWxlcnQoMSk=', 'mesh.bin?token=secret',
])
def test_gltf_references_cannot_escape_or_execute(tmp_path, uri):
    root = frontend(tmp_path)
    model = tmp_path / 'private-model.gltf'
    model.write_text(json.dumps(model_document(uri)))
    result = inject(tmp_path, archetype='product_viewer', model_path=str(model))
    assert result['success'] is False
    assert uri not in result.get('error', '')
    assert not (root / 'public').exists()


def test_gltf_resource_bundle_is_copied_with_structure_and_sanitized_url(tmp_path):
    root = frontend(tmp_path)
    bundle = tmp_path / 'owner-private'
    (bundle / 'geometry').mkdir(parents=True)
    (bundle / 'geometry/mesh.bin').write_bytes(triangle_bytes())
    model = bundle / 'secret-name.gltf'
    model.write_text(json.dumps(model_document('geometry/mesh.bin')))
    result = inject(tmp_path, archetype='product_viewer', model_path=str(model))
    assert result['success'] is True
    assert result['scene']['archetype'] == 'product_viewer'
    assert result['scene']['model_url'].startswith('/assets/models/')
    copied = root / 'public' / result['scene']['model_url'].lstrip('/')
    assert json.loads(copied.read_text())['buffers'][0]['uri'] == 'geometry/mesh.bin'
    assert (copied.parent / 'geometry/mesh.bin').read_bytes() == triangle_bytes()
    assert 'owner-private' not in str(result)
    assert 'secret-name' not in str(result)
    shell = (root / 'src/components/motion/Modern3DScene.jsx').read_text()
    assert str(model) not in shell
    assert result['scene']['model_url'] in shell


def test_glb_copy_uses_actual_owner_bytes(tmp_path):
    root = frontend(tmp_path)
    model = tmp_path / 'private.glb'
    model.write_bytes(glb_bytes())
    result = inject(tmp_path, archetype='product_viewer', model_path=str(model))
    assert result['success'] is True
    copied = root / 'public' / result['scene']['model_url'].lstrip('/')
    assert copied.read_bytes() == glb_bytes()


@pytest.mark.parametrize('case', ['missing', 'oversized', 'bundle_total', 'bad_version',
    'short_buffer', 'out_of_bounds_view', 'script_image'])
def test_invalid_local_bundles_fail_actionably(tmp_path, case):
    root = frontend(tmp_path)
    model = tmp_path / 'private.gltf'
    document = model_document()
    (tmp_path / 'mesh.bin').write_bytes(triangle_bytes())
    if case == 'oversized':
        with model.open('wb') as handle:
            handle.truncate(50 * 1024 * 1024 + 1)
    elif case == 'bundle_total':
        with (tmp_path / 'mesh.bin').open('wb') as handle:
            handle.truncate(50 * 1024 * 1024)
        model.write_text(json.dumps(document))
    elif case != 'missing':
        if case == 'bad_version':
            document['asset']['version'] = '1.0'
        if case == 'short_buffer':
            (tmp_path / 'mesh.bin').write_bytes(b'123')
        if case == 'out_of_bounds_view':
            document['bufferViews'][0]['byteLength'] = 100
        if case == 'script_image':
            document['images'] = [{'uri': 'evil.png'}]
            (tmp_path / 'evil.png').write_text('<script>alert(1)</script>')
        model.write_text(json.dumps(document))
    result = inject(tmp_path, archetype='product_viewer', model_path=str(model))
    assert result['success'] is False
    assert result['error']
    assert str(model) not in str(result)
    assert not (root / 'public').exists()


def test_rejects_resource_symlink_escape(tmp_path):
    root = frontend(tmp_path)
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    outside = tmp_path / 'outside.bin'
    outside.write_bytes(triangle_bytes())
    try:
        (bundle / 'mesh.bin').symlink_to(outside)
    except OSError:
        pytest.skip('OS does not permit creating symlinks')
    model = bundle / 'model.gltf'
    model.write_text(json.dumps(model_document()))
    assert inject(tmp_path, archetype='product_viewer', model_path=str(model))['success'] is False
    assert not (root / 'public').exists()


@pytest.mark.parametrize('archetype', ['floating_crystal', 'cyber_grid', 'particle_cosmos'])
def test_emits_lazy_user_driven_scene_contract_not_css_substitute(tmp_path, archetype):
    root = frontend(tmp_path)
    result = inject(tmp_path, archetype=archetype, brand_name='Owner </script> {unsafe}')
    assert result['success'] is True
    shell = (root / 'src/components/motion/Modern3DScene.jsx').read_text()
    canvas = (root / 'src/components/motion/SceneCanvas.jsx').read_text()
    assert "import('./SceneCanvas.jsx')" in shell
    assert '@react-three/' not in shell
    assert 'Enable 3D' in shell and 'Retry 3D' in shell
    for label in ['Rotate left', 'Rotate right', 'Zoom in', 'Zoom out', 'Reset view']:
        assert label in shell
    assert 'data-scene-state' in shell
    assert 'data-scene-frames' in shell and 'data-scene-draw-calls' in shell
    assert 'webglcontextlost' in canvas
    assert 'frameloop="demand"' in canvas
    assert 'GLTFLoader' in canvas and 'Box3' in canvas
    assert 'autoRotate' not in canvas and '<Float' not in canvas
    assert 'torusKnot' not in canvas and 'Environment' not in canvas


def test_generated_scenes_in_real_webgl_browser():
    """Opt-in acceptance: SCENE_BROWSER_TEST=1; artifacts stay in generated-projects.

    These are isolated emitter fixtures, not integrated factory or live-delivery proof.
    Once opted in, missing npm, Chromium or WebGL is a failure, never a skipped pass.
    """
    import functools
    import http.server
    import io
    import os
    import shutil
    import subprocess
    import threading

    if os.environ.get('SCENE_BROWSER_TEST') != '1':
        pytest.skip('Set SCENE_BROWSER_TEST=1 to build and browser-test generated scene fixtures')
    from PIL import Image, ImageChops
    from playwright.sync_api import sync_playwright

    scratch = Path(__file__).resolve().parents[2] / 'generated-projects/scene-runtime'
    scratch.mkdir(parents=True, exist_ok=True)
    harness_package = {
        'private': True, 'type': 'module', 'dependencies': {
            'react': '^19.0.0', 'react-dom': '^19.0.0', 'vite': '^6.0.0',
        },
    }
    # The injector, not this test, chooses the actual 3D dependencies.
    (scratch / 'src').mkdir(exist_ok=True)
    (scratch / 'package.json').write_text(json.dumps(harness_package))
    assert inject(scratch)['success'] is True
    npm = shutil.which('npm.cmd') or shutil.which('npm')
    assert npm, 'npm is required for generated scene browser acceptance'
    install = subprocess.run([npm, 'install', '--no-audit', '--no-fund'], cwd=scratch,
                             capture_output=True, text=True, timeout=240)
    assert install.returncode == 0, install.stderr[-4000:]
    model = scratch / 'private-owner-model.glb'
    model.write_bytes(glb_bytes())
    report = []

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    def pixels(canvas):
        image = Image.open(io.BytesIO(canvas.screenshot())).convert('RGB')
        assert image.width > 0 and image.height > 0
        assert len(image.getcolors(image.width * image.height) or []) > 8
        return image

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=[
            '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl',
        ])
        try:
            for archetype in ['floating_crystal', 'cyber_grid', 'particle_cosmos', 'product_viewer']:
                project = scratch / archetype
                project.mkdir(exist_ok=True)
                (project / 'src').mkdir(exist_ok=True)
                (project / 'package.json').write_text(json.dumps(harness_package))
                result = inject(project, archetype=archetype,
                                **({'model_path': str(model)} if archetype == 'product_viewer' else {}))
                assert result['success'] is True
                (project / 'index.html').write_text(
                    '<html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
                    '</head><body style="margin:0"><div id="root"></div>'
                    '<script type="module" src="/src/main.jsx"></script></body></html>')
                (project / 'src/main.jsx').write_text(
                    "import React from 'react'; import { createRoot } from 'react-dom/client';"
                    "import Scene from './components/motion/Modern3DScene.jsx';"
                    "createRoot(document.getElementById('root')).render(<main><h1>Scene fixture</h1>"
                    "<Scene /><a href='/'>Ordinary navigation</a></main>);")
                build = subprocess.run([
                    shutil.which('node'), str(scratch / 'node_modules/vite/bin/vite.js'), 'build',
                ], cwd=project, capture_output=True, text=True, timeout=120)
                (project / 'build-output.txt').write_text(build.stdout + build.stderr, encoding='utf-8')
                assert build.returncode == 0, build.stderr[-4000:]
                server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
                    QuietHandler, directory=str(project / 'dist'),
                ))
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                context = browser.new_context(viewport={'width': 1440, 'height': 1000},
                                              reduced_motion='reduce')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                try:
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    assert page.locator('canvas').count() == 0
                    page.get_by_role('button', name='Enable 3D', exact=True).click()
                    page.wait_for_selector('[data-scene-state="rendered"]', timeout=25000)
                    canvas = page.locator('canvas')
                    original = pixels(canvas)
                    canvas.screenshot(path=str(project / 'rendered.png'))
                    root = page.locator('[data-scene-state]')
                    assert int(root.get_attribute('data-scene-draw-calls')) > 0
                    frames = int(root.get_attribute('data-scene-frames'))
                    # Enter exercises keyboard activation, not a private camera method.
                    page.get_by_role('button', name='Rotate left', exact=True).focus()
                    page.keyboard.press('Enter')
                    page.wait_for_function("(n) => Number(document.querySelector('[data-scene-frames]').dataset.sceneFrames) > n", arg=frames)
                    rotated = pixels(canvas)
                    assert ImageChops.difference(original, rotated).getbbox() is not None
                    frames = int(root.get_attribute('data-scene-frames'))
                    page.get_by_role('button', name='Zoom in', exact=True).click()
                    page.wait_for_function("(n) => Number(document.querySelector('[data-scene-frames]').dataset.sceneFrames) > n", arg=frames)
                    zoomed = pixels(canvas)
                    assert ImageChops.difference(rotated, zoomed).getbbox() is not None
                    page.get_by_role('button', name='Reset view', exact=True).click()
                    page.wait_for_timeout(200)
                    reset = pixels(canvas)
                    assert ImageChops.difference(original, reset).getbbox() is None
                    idle_frames = root.get_attribute('data-scene-frames')
                    page.wait_for_timeout(350)
                    assert root.get_attribute('data-scene-frames') == idle_frames
                    assert errors == []
                    widths = []
                    for width in [375, 768, 1024, 1440, 1920]:
                        page.set_viewport_size({'width': width, 'height': 1000})
                        page.reload()
                        page.get_by_role('button', name='Enable 3D', exact=True).wait_for()
                        assert page.locator('canvas').count() == 0
                        assert page.evaluate('window.innerWidth') == width
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        if width == 375:
                            assert root.get_attribute('data-scene-state') == 'fallback'
                        page.screenshot(path=str(project / f'fallback-{width}.png'), full_page=True)
                        widths.append(width)
                    page.get_by_role('button', name='Enable 3D', exact=True).click()
                    page.wait_for_selector('[data-scene-state="rendered"]', timeout=25000)
                    assert page.locator('canvas').evaluate("(c) => { const gl = c.getContext('webgl2'); const ext = gl.getExtension('WEBGL_lose_context'); if (!ext) return false; ext.loseContext(); return true; }")
                    page.wait_for_selector('[data-scene-state="failed"]')
                    assert page.get_by_role('button', name='Retry 3D', exact=True).is_visible()
                    assert page.get_by_role('link', name='Ordinary navigation').is_visible()
                    page.get_by_role('button', name='Retry 3D', exact=True).click()
                    page.wait_for_selector('[data-scene-state="rendered"]', timeout=25000)
                    pixels(page.locator('canvas'))
                    if archetype == 'product_viewer':
                        page.route('**/assets/models/**', lambda route: route.abort())
                        page.reload()
                        page.get_by_role('button', name='Enable 3D', exact=True).click()
                        page.wait_for_selector('[data-scene-state="failed"]', timeout=25000)
                        assert page.get_by_role('button', name='Retry 3D', exact=True).is_visible()
                    report.append({'archetype': archetype, 'widths': widths,
                                   'rendered_pixels': True, 'rotate_zoom_pixels_changed': True,
                                   'keyboard': True, 'reset': True, 'idle_frames_stable': True,
                                   'context_loss_and_retry': True, 'reduced_motion': True})
                finally:
                    context.close()
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)
        finally:
            browser.close()
            (scratch / 'browser-report.json').write_text(json.dumps(report, indent=2))
