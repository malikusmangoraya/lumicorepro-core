"""Genuine, opt-in WebGL scenes and bounded trusted-local glTF bundling.

This emitter writes components and package dependencies, never installs packages or
mounts a page. The public-page emitter owns mounting Modern3DScene. Asset validation
is deliberately conservative: glTF 2, local BIN/PNG/JPEG/WebP or typed base64 data,
no external decoders, scripts, network resources, or escaping resource paths.
"""
import base64
import hashlib
import json
import os
import re
import struct
import tempfile
from pathlib import Path
from typing import Any

from .generation_contract import SCENE_ARCHETYPES, resolve_scene_request

MAX_BUNDLE_BYTES = 50 * 1024 * 1024
MAX_RESOURCES = 128


def _json(value):
    return json.dumps(value, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e')


def _read_bounded(path, remaining):
    if not path.is_file() or path.stat().st_size > remaining:
        raise ValueError('Model bundle is missing a file or exceeds the 50 MiB limit.')
    with path.open('rb') as stream:
        data = stream.read(remaining + 1)
    if len(data) > remaining:
        raise ValueError('Model bundle exceeds the 50 MiB limit.')
    return data


def _local_uri(uri):
    # Reject percent encoding, Windows drives/ADS, backslashes and URL syntax too.
    if not isinstance(uri, str) or len(uri) > 512:
        raise ValueError('Model resource must be a bounded local relative URI.')
    parts = uri.split('/')
    if any(not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_. -]*', part)
           or part.endswith(('.', ' ')) for part in parts):
        raise ValueError('Model resources must stay inside the local bundle; URLs are unsupported.')
    if any(part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
            *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))} for part in parts):
        raise ValueError('Model resource filename is not portable.')
    return uri


def _image(data, mime=None):
    detected = None
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        detected = 'image/png'
    elif data.startswith(b'\xff\xd8\xff'):
        detected = 'image/jpeg'
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        detected = 'image/webp'
    if not detected or (mime and mime != detected):
        raise ValueError('Model images must contain PNG, JPEG or WebP data, not scripts or SVG.')


def _index(items, index):
    if type(index) is not int or not 0 <= index < len(items):
        raise ValueError('Model contains an invalid resource index.')
    return items[index]


def _integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Model contains an invalid resource length.')
    return value


def _model_bundle(model_path):
    """Read a complete validated bundle into memory before creating public outputs."""
    source = Path(model_path)
    if source.suffix.lower() not in {'.glb', '.gltf'} or source.is_symlink():
        raise ValueError('Supply a regular trusted local .glb or .gltf model file.')
    source = source.resolve(strict=True)
    root = source.parent
    original = _read_bounded(source, MAX_BUNDLE_BYTES)
    binary = None
    if source.suffix.lower() == '.glb':
        if len(original) < 20:
            raise ValueError('Invalid GLB header; supply a glTF 2 model.')
        magic, version, length = struct.unpack_from('<4sII', original)
        if magic != b'glTF' or version != 2 or length != len(original):
            raise ValueError('Invalid GLB version or declared length.')
        chunks, offset = [], 12
        while offset < length:
            if offset + 8 > length:
                raise ValueError('Invalid GLB chunk header.')
            size, kind = struct.unpack_from('<II', original, offset)
            offset += 8
            if size % 4 or offset + size > length:
                raise ValueError('Invalid GLB chunk length.')
            chunks.append((kind, original[offset:offset + size]))
            offset += size
        if not chunks or chunks[0][0] != 0x4E4F534A or len(chunks) > 2:
            raise ValueError('GLB requires a leading JSON chunk and optional BIN chunk.')
        if len(chunks) == 2:
            if chunks[1][0] != 0x004E4942:
                raise ValueError('Unsupported GLB chunk type.')
            binary = chunks[1][1]
        payload = chunks[0][1]
    else:
        payload = original
    try:
        document = json.loads(payload.decode('utf-8'))
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError('Model must contain valid glTF 2 JSON.') from None
    if not isinstance(document, dict) or document.get('asset', {}).get('version') != '2.0':
        raise ValueError('Model requires glTF asset version 2.0.')
    if document.get('asset', {}).get('minVersion', '2.0') != '2.0':
        raise ValueError('Model requires an unsupported glTF version.')

    # Unknown extensions may introduce hidden URI loaders or external decoder downloads.
    queue = [(document, 0)]
    uri_count = 0
    while queue:
        item, depth = queue.pop()
        if depth > 64:
            raise ValueError('Model JSON nesting exceeds the supported limit.')
        if isinstance(item, dict):
            if 'extensions' in item and set(item['extensions']) - {'KHR_materials_unlit'}:
                raise ValueError('Model uses unsupported extensions; export standard glTF 2.')
            uri_count += int('uri' in item)
            queue.extend((value, depth + 1) for value in item.values())
        elif isinstance(item, list):
            queue.extend((value, depth + 1) for value in item)
    if set(document.get('extensionsRequired', [])) - {'KHR_materials_unlit'}:
        raise ValueError('Model requires unsupported extensions; export standard glTF 2.')
    buffers = document.get('buffers', [])
    images = document.get('images', [])
    if not isinstance(buffers, list) or not isinstance(images, list):
        raise ValueError('Invalid model resource lists.')
    resources = buffers + images
    if len(resources) > MAX_RESOURCES or uri_count != sum('uri' in item for item in resources):
        raise ValueError('Model has unsupported or too many resource references.')
    files = {'model' + source.suffix.lower(): original}
    total = len(original)

    def resource(uri, image=False):
        nonlocal total
        if isinstance(uri, str) and uri.startswith('data:'):
            match = re.fullmatch(r'data:([^;,]+);base64,([A-Za-z0-9+/=\r\n]+)', uri)
            types = {'image/png', 'image/jpeg', 'image/webp'} if image else {
                'application/octet-stream', 'application/gltf-buffer',
            }
            if not match or match[1] not in types:
                raise ValueError('Only typed base64 binary or raster model resources are supported.')
            try:
                data = base64.b64decode(match[2].replace('\n', '').replace('\r', ''), validate=True)
            except ValueError:
                raise ValueError('Invalid embedded model resource.') from None
            # Embedded bytes already count toward the on-disk JSON/GLB bundle ceiling.
            if image:
                _image(data, match[1])
            return data
        rel = _local_uri(uri)
        suffix = Path(rel).suffix.lower()
        if suffix not in ({'.png', '.jpg', '.jpeg', '.webp'} if image else {'.bin'}):
            raise ValueError('Model references an unsupported binary or image resource format.')
        path = root / rel
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ValueError('Model resource escapes the supplied local bundle.')
        if rel not in files:
            data = _read_bounded(resolved, MAX_BUNDLE_BYTES - total)
            total += len(data)
            files[rel] = data
        data = files[rel]
        if image:
            _image(data)
        return data

    data_buffers = []
    for i, buffer in enumerate(buffers):
        size = _integer(buffer.get('byteLength'), 1)
        data = resource(buffer['uri']) if 'uri' in buffer else binary
        if data is None or ('uri' not in buffer and i != 0) or len(data) < size:
            raise ValueError('Model buffer is missing or shorter than its declared byteLength.')
        if 'uri' not in buffer and len(data) - size > 3:
            raise ValueError('GLB binary chunk length does not match its buffer.')
        data_buffers.append(data[:size])
    views = document.get('bufferViews', [])
    for view in views:
        data = _index(data_buffers, view.get('buffer'))
        start = _integer(view.get('byteOffset', 0))
        size = _integer(view.get('byteLength'), 1)
        if start + size > len(data):
            raise ValueError('Model buffer view exceeds its binary resource bounds.')
    for image in images:
        if 'uri' in image:
            resource(image['uri'], image=True)
        else:
            view = _index(views, image.get('bufferView'))
            data = _index(data_buffers, view.get('buffer'))
            start = view.get('byteOffset', 0)
            _image(data[start:start + view['byteLength']], image.get('mimeType'))
    if not document.get('scenes') or not document.get('meshes'):
        raise ValueError('Product model must contain a scene and renderable mesh geometry.')
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        digest.update(name.encode() + b'\x00' + data)
    prefix = 'assets/models/' + digest.hexdigest()[:20]
    return {prefix + '/' + name: data for name, data in files.items()}, '/' + prefix + '/model' + source.suffix.lower()


def _frontend(project):
    for candidate in (project / 'frontend', project):
        if (candidate / 'package.json').is_file() and (candidate / 'src').is_dir():
            if not candidate.resolve().is_relative_to(project):
                raise ValueError('Frontend must be inside the generated project.')
            package = json.loads((candidate / 'package.json').read_text(encoding='utf-8'))
            dependencies = package.get('dependencies', {})
            match = re.match(r'^[~^]?(18|19)\.', str(dependencies.get('react', '')))
            dom = re.match(r'^[~^]?(18|19)\.', str(dependencies.get('react-dom', '')))
            if not match or not dom or dom[1] != match[1]:
                raise ValueError('Scene requires matching React and React DOM 18 or 19 dependencies.')
            versions = (('^0.180.0', '^9.3.0', '^10.7.0') if match[1] == '19'
                        else ('^0.170.0', '^8.18.0', '^9.122.0'))
            for name, version in zip(('three', '@react-three/fiber', '@react-three/drei'), versions):
                dependencies[name] = version
                package.get('devDependencies', {}).pop(name, None)
            package['dependencies'] = dependencies
            return candidate, package
    raise ValueError('Scene requires an existing frontend package.json and src directory.')


def _safe_destination(path, project):
    if not path.resolve().is_relative_to(project):
        raise ValueError('Scene output cannot escape the generated project through symlinks.')


def _write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


class Modern3DWebsiteEngine:
    """Emit opt-in scenes; successful emission is not proof of browser rendering."""

    ARCHETYPES = list(SCENE_ARCHETYPES)

    def get_supported_archetypes(self):
        return list(self.ARCHETYPES)

    def generate_component_code(self, archetype, brand_name='Lumicore',
                                primary_color='#3b82f6', *, model_url=None):
        """Return the lazy shell; SceneCanvas.jsx and CSS are emitted by inject.

        A product shell needs the emitter's validated public model URL. This method
        does not copy a model or certify that a standalone shell is a working scene.
        """
        if archetype not in SCENE_ARCHETYPES:
            raise ValueError('Unsupported scene archetype; CSS effects are not genuine 3D scenes.')
        if archetype == 'product_viewer' and not (
            isinstance(model_url, str) and re.fullmatch(
                r'/assets/models/[a-f0-9]{20}/model\.(?:glb|gltf)', model_url,
            )
        ):
            raise ValueError('Product scene requires a validated bundled model; use inject_3d_experience.')
        if not isinstance(primary_color, str) or not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', primary_color):
            raise ValueError('Scene primary color must be a valid hex color token.')
        return (_SHELL.replace('__BRAND__', _json(str(brand_name)))
                .replace('__ARCHETYPE__', _json(archetype))
                .replace('__COLOR__', _json(primary_color))
                .replace('__MODEL__', _json(model_url)))

    def inject_3d_experience(self, project_dir, archetype='floating_crystal',
                             brand_name='Lumicore', primary_color='#3b82f6', *, model_path=None):
        """Validate first, then emit. Return relative files and a public-only scene.

        Failure: success=False, files (completed writes), scene=None, safe error.
        Success retains component_name/injected_file for existing callers. No npm
        install, page mounting, source asset path, or certification is returned.
        """
        written = []
        try:
            request = {'archetype': archetype}
            if model_path is not None:
                request['model_path'] = model_path
            request = resolve_scene_request(scene=request)
            project = Path(project_dir).resolve(strict=True)
            root, package = _frontend(project)
            assets, model_url = ({}, None)
            if request['archetype'] == 'product_viewer':
                assets, model_url = _model_bundle(request['model_path'])
            scene = {'archetype': request['archetype']}
            if model_url:
                scene['model_url'] = model_url
            motion = root / 'src/components/motion'
            shell = self.generate_component_code(request['archetype'], brand_name, primary_color,
                                                 model_url=model_url)
            outputs = {root / 'public' / name: data for name, data in assets.items()}
            outputs.update({
                motion / 'Modern3DScene.jsx': shell.encode(),
                motion / 'SceneCanvas.jsx': _CANVAS.encode(),
                motion / 'modern-3d-scene.css': _CSS.encode(),
                root / 'package.json': (json.dumps(package, indent=2) + '\n').encode(),
            })
            for path in outputs:
                _safe_destination(path, project)
            for path, data in outputs.items():
                _write_atomic(path, data)
                written.append(path.relative_to(project).as_posix())
            return {'success': True, 'files': written, 'scene': scene,
                    'archetype': scene['archetype'], 'component_name': 'Modern3DScene',
                    'injected_file': (motion / 'Modern3DScene.jsx').relative_to(project).as_posix()}
        except ValueError as exc:
            # Only our validation messages may cross this boundary, never JSON/parser paths.
            error = str(exc) if str(exc).startswith((
                'Scene ', 'Model ', 'Product ', 'Supply ', 'Invalid ', 'Unsupported ',
                'Only ', 'GLB ', 'Frontend ',
            )) else 'Scene validation failed; check the frontend and local glTF 2 model bundle.'
        except (OSError, TypeError, KeyError, AttributeError, RecursionError, struct.error):
            error = 'Scene generation failed; check local model resources and output permissions.'
        return {'success': False, 'files': written, 'scene': None, 'error': error}


_SHELL = """import React, { Component, Suspense, lazy, useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';
import './modern-3d-scene.css';

const brand = __BRAND__;
const archetype = __ARCHETYPE__;
const modelUrl = __MODEL__;
const primaryColor = __COLOR__;

class SceneBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onFailure('3D could not load. Retry or use the page without 3D.'); }
  render() { return this.state.failed ? null : this.props.children; }
}

export default function Modern3DScene() {
  const root = useRef(null);
  const controls = useRef(null);
  const headingId = useId();
  const [active, setActive] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState('requested');
  const [message, setMessage] = useState('3D is off. Enable it to explore; all page features work without it.');
  const [observations, setObservations] = useState({ frames: 0, calls: 0 });
  const [color, setColor] = useState(primaryColor);
  // A failed lazy load gets a fresh React lazy wrapper only on explicit retry.
  const LazyCanvas = useMemo(() => lazy(() => import('./SceneCanvas.jsx')), [attempt]);
  const fail = useCallback((reason) => {
    controls.current = null;
    setState('failed');
    setMessage(reason);
  }, []);
  const observe = useCallback((frames, calls) => {
    setObservations({ frames, calls });
    if (calls > 0) {
      setState('rendered');
      setMessage('3D enabled. Drag to orbit or use the rotate, zoom and reset buttons.');
    }
  }, []);
  useEffect(() => {
    const token = getComputedStyle(root.current).getPropertyValue('--brand-primary').trim();
    if (/^#[0-9a-f]{3}([0-9a-f]{3})?$/i.test(token)) setColor(token);
    if (window.matchMedia('(max-width: 767px)').matches) setState('fallback');
  }, []);
  useEffect(() => {
    if (!active || state !== 'loading') return undefined;
    const timer = setTimeout(() => fail('3D loading timed out. Retry when ready.'), 20000);
    return () => clearTimeout(timer);
  }, [active, state, fail]);
  const activate = () => {
    setObservations({ frames: 0, calls: 0 });
    setAttempt((value) => value + 1);
    setMessage('Loading 3D. The rest of this page remains available.');
    setState('loading');
    setActive(true);
  };
  const ready = state === 'rendered';
  return (
    <section ref={root} className="modern-scene" aria-labelledby={headingId}
      data-scene-archetype={archetype} data-scene-state={state}
      data-scene-frames={observations.frames} data-scene-draw-calls={observations.calls}>
      <h2 id={headingId}>{brand} — interactive 3D</h2>
      <p className="modern-scene-description" data-scene-fallback>
        {archetype === 'product_viewer'
          ? 'Inspect the supplied product model from different angles. Nothing moves automatically.'
          : 'Explore original spatial geometry. Rotate to see its depth; nothing moves automatically.'}
      </p>
      <p data-scene-status role={state === 'failed' ? 'alert' : 'status'} aria-live="polite">{message}</p>
      {(!active || state === 'failed') && (
        <button type="button" data-scene-enable onClick={activate}>
          {state === 'failed' ? 'Retry 3D' : 'Enable 3D'}
        </button>
      )}
      <div className="modern-scene-viewport" data-scene-viewport>
        {active && state !== 'failed' ? (
          <SceneBoundary key={attempt} onFailure={fail}>
            <Suspense fallback={<p className="modern-scene-placeholder">Loading the 3D engine…</p>}>
              <LazyCanvas archetype={archetype} modelUrl={modelUrl} color={color}
                controlsRef={controls} onFailure={fail} onObserve={observe} />
            </Suspense>
          </SceneBoundary>
        ) : (
          <div className="modern-scene-placeholder">
            <span className="modern-scene-static" aria-hidden="true">◇</span>
            <p>Static preview. Interactive 3D is optional and starts only when you enable it.</p>
          </div>
        )}
      </div>
      <div className="modern-scene-controls" role="group" aria-label="3D view controls">
        <button type="button" disabled={!ready} onClick={() => controls.current?.('left')}>Rotate left</button>
        <button type="button" disabled={!ready} onClick={() => controls.current?.('right')}>Rotate right</button>
        <button type="button" disabled={!ready} onClick={() => controls.current?.('in')}>Zoom in</button>
        <button type="button" disabled={!ready} onClick={() => controls.current?.('out')}>Zoom out</button>
        <button type="button" disabled={!ready} onClick={() => controls.current?.('reset')}>Reset view</button>
      </div>
    </section>
  );
}
"""

_CANVAS = """import React, { memo, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Box3, LoadingManager, Spherical, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

function disposeModel(scene) {
  const textures = new Set();
  scene.traverse((object) => {
    object.geometry?.dispose();
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.filter(Boolean).forEach((material) => {
      Object.values(material).forEach((value) => { if (value?.isTexture) textures.add(value); });
      material.dispose();
    });
  });
  textures.forEach((texture) => texture.dispose());
}

function Product({ url }) {
  const [loaded, setLoaded] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let scene;
    const absolute = new URL(url, window.location.origin);
    const directory = new URL('.', absolute).href;
    const manager = new LoadingManager();
    manager.setURLModifier((resource) => {
      // Embedded raster images are converted to blob URLs by GLTFLoader.
      if (resource.startsWith('blob:') || resource.startsWith('data:')) return resource;
      const resolved = new URL(resource, window.location.href).href;
      if (!resolved.startsWith(directory)) throw new Error('Nonlocal model resource');
      return resolved;
    });
    manager.onError = () => { if (!cancelled) setFailed(true); };
    new GLTFLoader(manager).load(absolute.href, (gltf) => {
      scene = gltf.scene;
      if (cancelled) { disposeModel(scene); return; }
      scene.updateMatrixWorld(true);
      const box = new Box3().setFromObject(scene);
      const center = box.getCenter(new Vector3());
      const size = box.getSize(new Vector3());
      const extent = Math.max(size.x, size.y, size.z);
      if (box.isEmpty() || !Number.isFinite(extent) || extent <= 0) {
        disposeModel(scene);
        scene = null;
        setFailed(true);
        return;
      }
      setLoaded({ scene, center: center.toArray().map((value) => -value), scale: 3 / extent });
    }, undefined, () => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; if (scene) disposeModel(scene); };
  }, [url]);
  if (failed) throw new Error('Product model unavailable');
  return loaded ? (
    <group scale={loaded.scale}>
      <group position={loaded.center}><primitive object={loaded.scene} /></group>
    </group>
  ) : null;
}

function Geometry({ archetype, color, modelUrl }) {
  const particles = useMemo(() => {
    const positions = new Float32Array(900 * 3);
    for (let i = 0; i < 900; i += 1) {
      const y = 1 - (i / 899) * 2;
      const radius = Math.sqrt(1 - y * y) * (1.8 + (i % 7) * 0.035);
      const angle = i * Math.PI * (3 - Math.sqrt(5));
      positions.set([Math.cos(angle) * radius, y * 2, Math.sin(angle) * radius], i * 3);
    }
    return positions;
  }, []);
  if (archetype === 'product_viewer') return <Product url={modelUrl} />;
  if (archetype === 'particle_cosmos') return (
    <points rotation={[0.2, 0.4, 0.1]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[particles, 3]} />
      </bufferGeometry>
      <pointsMaterial color={color} size={0.065} sizeAttenuation />
    </points>
  );
  if (archetype === 'cyber_grid') return (
    <group position={[0, -0.7, 0]}>
      <gridHelper args={[6, 16, color, color]} />
      {Array.from({ length: 25 }, (_, i) => (
        <mesh key={i} position={[(i % 5 - 2) * 0.85, (i % 4 + 1) * 0.16, (Math.floor(i / 5) - 2) * 0.85]}>
          <boxGeometry args={[0.18, (i % 4 + 1) * 0.32, 0.18]} />
          <meshStandardMaterial color={color} roughness={0.45} />
        </mesh>
      ))}
    </group>
  );
  return (
    <group rotation={[0.15, 0.35, 0]}>
      {[[0, 0, 0, 1.25], [-1.8, 0.8, -0.6, 0.6], [1.6, -0.5, 0.4, 0.75]].map(([x, y, z, scale], i) => (
        <mesh key={i} position={[x, y, z]} scale={scale} rotation={[i * 0.3, i * 0.6, 0.2]}>
          <octahedronGeometry args={[1, 0]} />
          <meshStandardMaterial color={color} roughness={0.3} metalness={0.25} />
        </mesh>
      ))}
    </group>
  );
}

function SceneWorld({ archetype, modelUrl, color, controlsRef, onFailure, onObserve }) {
  const orbit = useRef(null);
  const frames = useRef(0);
  const { gl, camera, invalidate } = useThree();
  useEffect(() => {
    const lost = (event) => {
      event.preventDefault();
      onFailure('3D graphics context lost. Retry 3D to create a new view.');
    };
    gl.domElement.addEventListener('webglcontextlost', lost);
    return () => gl.domElement.removeEventListener('webglcontextlost', lost);
  }, [gl, onFailure]);
  useLayoutEffect(() => {
    const control = orbit.current;
    if (!control) return undefined;
    control.saveState();
    controlsRef.current = (action) => {
      if (action === 'reset') control.reset();
      else {
        const offset = camera.position.clone().sub(control.target);
        const spherical = new Spherical().setFromVector3(offset);
        if (action === 'left') spherical.theta -= Math.PI / 8;
        if (action === 'right') spherical.theta += Math.PI / 8;
        if (action === 'in') spherical.radius = Math.max(2, spherical.radius * 0.8);
        if (action === 'out') spherical.radius = Math.min(18, spherical.radius * 1.25);
        camera.position.copy(control.target).add(new Vector3().setFromSpherical(spherical));
        control.update();
      }
      invalidate();
    };
    return () => { controlsRef.current = null; };
  }, [camera, controlsRef, invalidate]);
  // Own the demand frame to observe AFTER drawing, not a source-level ready marker.
  useFrame(({ scene }) => {
    if (gl.getContext().isContextLost()) return;
    try {
      gl.render(scene, camera);
      frames.current += 1;
      onObserve(frames.current, gl.info.render.calls);
    } catch {
      onFailure('3D rendering failed. Retry or continue without 3D.');
    }
  }, 1);
  return (
    <>
      <ambientLight intensity={1.2} />
      <directionalLight position={[5, 7, 6]} intensity={2.5} />
      <directionalLight position={[-4, 2, -3]} intensity={1} />
      <Geometry archetype={archetype} color={color} modelUrl={modelUrl} />
      <OrbitControls ref={orbit} makeDefault enableDamping={false} minDistance={2} maxDistance={18} />
    </>
  );
}

function SceneCanvas(props) {
  return (
    <Canvas frameloop="demand" dpr={[1, 1.5]} camera={{ position: [4, 2.5, 6], fov: 45 }}
      gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
      fallback={<p role="alert">WebGL is unavailable. Use the page without 3D.</p>}
      onCreated={({ gl }) => {
        gl.domElement.setAttribute('aria-label', 'Interactive 3D view');
        gl.domElement.setAttribute('role', 'img');
      }}>
      <SceneWorld {...props} />
    </Canvas>
  );
}

// Observations update the shell, not the Canvas props: no accidental continuous loop.
export default memo(SceneCanvas);
"""

_CSS = """.modern-scene {
  min-width: 0; width: 100%; box-sizing: border-box;
  padding: clamp(1rem, 3vw, 2rem); border: 1px solid var(--muted, currentColor);
  border-radius: var(--radius-card, 1rem); color: var(--ink, CanvasText);
  background: var(--surface, Canvas);
}
.modern-scene h2 { font-size: clamp(1.2rem, 3vw, 1.8rem); margin-block: 0 0.75rem; }
.modern-scene p { max-width: 65ch; line-height: 1.6; overflow-wrap: anywhere; }
.modern-scene-viewport { width: 100%; height: clamp(18rem, 45vw, 32rem); margin-block: 1rem; }
.modern-scene-placeholder { height: 100%; display: grid; place-content: center; text-align: center; }
.modern-scene-static { font-size: 5rem; color: var(--brand-primary, currentColor); }
.modern-scene-controls { display: flex; flex-wrap: wrap; gap: 0.65rem; }
.modern-scene button {
  min-height: 44px; padding: 0.6rem 1rem; max-width: 100%; font: inherit;
  border: 1px solid currentColor; border-radius: var(--radius-button, 0.5rem);
  color: inherit; background: transparent; cursor: pointer;
}
.modern-scene button:hover:not(:disabled) { text-decoration: underline; }
.modern-scene button:focus-visible { outline: 3px solid currentColor; outline-offset: 3px; }
.modern-scene button:disabled { opacity: 0.55; cursor: not-allowed; }
@media (prefers-reduced-motion: reduce) {
  .modern-scene, .modern-scene * { animation: none !important; transition: none !important; }
}
"""
