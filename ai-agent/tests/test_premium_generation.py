import builtins
import json
import traceback
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.fullstack_ultra_engine import FullStackUltraEngine
from agent.factory_pipeline import read_app_contract
from agent.generation_contract import resolve_generation_contract
from agent.omni_repair_engine import OmniRepairEngine


def generate(root, engine=None):
    return (engine or FullStackUltraEngine()).generate_project(
        str(root), prompt='A records workspace', brand_name='Northstar'
    )


@pytest.mark.parametrize('stage,target', [
    ('ai_saas_kit', 'agent.ai_saas_kit.inject_ai_saas_kit'),
    ('production_spec', 'agent.production_spec_kit.apply_production_spec'),
    ('schema_mirror', 'agent.fullstack_ultra_engine.FullStackUltraEngine._write_database_schema'),
    ('repair', 'agent.omni_repair_engine.OmniRepairEngine.scan_and_repair_project'),
])
def test_mandatory_exception_stops_generation(tmp_path, monkeypatch, stage, target):
    def fail(*args, **kwargs):
        raise RuntimeError('owner-secret-must-not-leak')

    monkeypatch.setattr(target, fail)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == stage
    assert result['generation_steps'][-1] == {'name': stage, 'ok': False}
    assert 'owner-secret-must-not-leak' not in json.dumps(result)
    if stage == 'ai_saas_kit':
        assert not (tmp_path / 'backend/routes/records.routes.js').exists()
    if stage == 'production_spec':
        assert not (tmp_path / 'database/schema.sql').exists()


@pytest.mark.parametrize('stage,target', [
    ('ai_saas_kit', 'agent.ai_saas_kit.inject_ai_saas_kit'),
    ('production_spec', 'agent.production_spec_kit.apply_production_spec'),
    ('repair', 'agent.omni_repair_engine.OmniRepairEngine.scan_and_repair_project'),
])
def test_explicit_failure_cannot_be_reported_as_generated(tmp_path, monkeypatch, stage, target):
    monkeypatch.setattr(target, lambda *a, **kw: {
        'status': 'failed', 'success': False, 'message': 'owner-secret-must-not-leak'
    })
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == stage
    assert 'owner-secret-must-not-leak' not in json.dumps(result)


def test_concurrent_file_write_failure_stops_before_kits(tmp_path, monkeypatch):
    original = builtins.open

    def fail_one(path, *args, **kwargs):
        if Path(path).as_posix().endswith('/src/main.jsx') and args and args[0] == 'w':
            raise OSError('owner-secret-must-not-leak')
        return original(path, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', fail_one)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'file_write'
    assert not (tmp_path / 'backend/routes/records.routes.js').exists()
    assert 'owner-secret-must-not-leak' not in json.dumps(result)


@pytest.mark.parametrize('relative', [
    'frontend/src/pages/Login.jsx',
    'frontend/src/pages/Register.jsx',
    'frontend/src/pages/Dashboard.jsx',
    'frontend/src/hooks/useRealtime.js',
    'backend/routes/records.routes.js',
    'backend/routes/events.routes.js',
    'backend/routes/health.routes.js',
    'backend/middleware/validate.js',
    'backend/models/index.js',
    'backend/utils/jwtSecret.js',
    'backend/services/changeBus.js',
    'backend/routes/ai.js',
    'backend/services/aiClient.js',
    'backend/services/keyVault.js',
    'backend/services/stream.js',
    'backend/services/prompts.js',
    'backend/services/ragLite.js',
    'backend/migrations/001_create_core_tables.js',
    'backend/migrations/002_create_records_table.js',
    'backend/migrations/003_create_contact_messages.js',
    'database/schema.sql',
])
def test_missing_final_artifact_prevents_success(tmp_path, monkeypatch, relative):
    from agent.omni_repair_engine import OmniRepairEngine
    original = OmniRepairEngine.scan_and_repair_project

    def remove_after_repair(self, destination):
        report = original(self, destination)
        (Path(destination) / relative).unlink()
        return report

    monkeypatch.setattr(OmniRepairEngine, 'scan_and_repair_project', remove_after_repair)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'artifacts'
    assert relative in str(result['errors'])


@pytest.mark.parametrize('relative,old,new', [
    ('frontend/src/pages/Login.jsx', '/auth/login', '/unwired/login'),
    ('frontend/src/pages/Register.jsx', '/auth/register', '/unwired/register'),
    ('frontend/src/pages/Dashboard.jsx', '/records', '/unwired'),
    ('frontend/src/hooks/useRealtime.js', '/events', '/unwired'),
    ('backend/server.js', "app.use('/api/v1/events', require('./routes/events.routes'));", ''),
    ('backend/server.js', "app.use('/api/v1/ai', require('./routes/ai'));", ''),
    ('backend/server.js', "app.use('/api/v1/contact', require('./routes/contact.routes'));", ''),
    ('backend/server.js', "app.use('/api/v1/health', healthRoutes);", ''),
    ('backend/server.js', "app.use(errorHandler);", ''),
    ('backend/server.js', "app.use('/api/v1/ai', require('./routes/ai'));",
     "app.use('/api/v1/ai', (_req, res) => res.end()); require('./routes/ai');"),
    ('backend/server.js', "app.use('/api/v1/auth', authRoutes);",
     "app.use('/api/v1/auth', (_req, res) => res.end());"),
])
def test_disconnected_final_artifact_prevents_success(tmp_path, monkeypatch, relative, old, new):
    from agent.omni_repair_engine import OmniRepairEngine
    original = OmniRepairEngine.scan_and_repair_project

    def disconnect(self, destination):
        report = original(self, destination)
        path = Path(destination) / relative
        text = path.read_text(encoding='utf-8')
        assert old in text
        path.write_text(text.replace(old, new), encoding='utf-8')
        return report

    monkeypatch.setattr(OmniRepairEngine, 'scan_and_repair_project', disconnect)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'artifacts'


def test_idempotent_kits_do_not_require_newly_written_files(tmp_path):
    first = generate(tmp_path)
    second = generate(tmp_path)
    assert first['success'] is True
    assert second['success'] is True
    assert all(step['ok'] for step in second['generation_steps'])
    assert second['generation_steps'][-1]['name'] == 'artifacts'


@pytest.mark.parametrize('relative', [
    'backend/routes/ai.js',
    'backend/services/aiClient.js',
    'backend/services/keyVault.js',
    'backend/services/stream.js',
    'backend/services/prompts.js',
    'backend/services/ragLite.js',
])
@pytest.mark.parametrize('corruption', ['empty_module', 'empty_exports'])
def test_real_idempotent_kit_rejects_corrupt_existing_artifact(tmp_path, relative, corruption):
    assert generate(tmp_path)['success'] is True
    path = tmp_path / relative
    content = path.read_text(encoding='utf-8')
    if corruption == 'empty_module':
        content = 'module.exports = {};\n'
    else:
        # Keep every implementation/name; only disconnect its CommonJS exports.
        content = content[:content.rindex('module.exports =')] + 'module.exports = {};\n'
    path.write_text(content, encoding='utf-8')

    result = generate(tmp_path)

    assert path.read_text(encoding='utf-8') == content  # The real kit skipped it.
    assert result['success'] is False
    assert result['failed_stage'] == 'artifacts'
    assert relative in str(result['errors'])
    assert {'name': 'ai_saas_kit', 'ok': True} in result['generation_steps']


@pytest.mark.parametrize('relative,old,new', [
    ('backend/routes/ai.js', "router.post('/generate'", "router.post('/unwired'"),
    ('backend/routes/ai.js', "router.post('/chat'", "router.post('/unwired'"),
    ('backend/routes/ai.js', "router.post('/files'", "router.post('/unwired'"),
    ('backend/routes/ai.js', "router.get('/health'", "router.get('/unwired'"),
    ('backend/services/aiClient.js', '{ complete, completeStream };', '{ complete };'),
    ('backend/services/keyVault.js', '{ setKey, getKey, hasKey };', '{ setKey, hasKey };'),
    ('backend/services/stream.js', '{ sseInit, sseSend, sseStreamText };', '{ sseInit };'),
    ('backend/services/prompts.js', '{ render, list, TEMPLATES };', '{ list, TEMPLATES };'),
    ('backend/services/ragLite.js', '{ chunk, embed, upsert, search };', '{ chunk, embed };'),
])
def test_real_idempotent_kit_rejects_partial_contract(tmp_path, relative, old, new):
    assert generate(tmp_path)['success'] is True
    path = tmp_path / relative
    content = path.read_text(encoding='utf-8')
    assert old in content
    content = content.replace(old, new)
    path.write_text(content, encoding='utf-8')

    result = generate(tmp_path)

    assert path.read_text(encoding='utf-8') == content
    assert result['success'] is False
    assert result['failed_stage'] == 'artifacts'
    assert relative in str(result['errors'])


@pytest.mark.parametrize('relative', [
    'backend/routes/auth.routes.js',
    'backend/routes/health.routes.js',
    'backend/routes/records.routes.js',
    'backend/routes/events.routes.js',
    'backend/routes/contact.routes.js',
    'backend/middleware/validate.js',
    'backend/models/index.js',
    'backend/utils/jwtSecret.js',
    'backend/services/changeBus.js',
    'backend/migrations/_guards.js',
])
def test_missing_dependency_exports_prevents_success(tmp_path, monkeypatch, relative):
    original = OmniRepairEngine.scan_and_repair_project

    def disconnect(self, destination):
        report = original(self, destination)
        path = Path(destination) / relative
        content = path.read_text(encoding='utf-8')
        content = content[:content.rindex('module.exports =')] + 'module.exports = {};\n'
        path.write_text(content, encoding='utf-8')
        return report

    monkeypatch.setattr(OmniRepairEngine, 'scan_and_repair_project', disconnect)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'artifacts'
    assert relative in str(result['errors'])


@pytest.fixture
def repair_io_failure(tmp_path, monkeypatch):
    def inject(operation):
        target = tmp_path / 'frontend/src/RepairTarget.jsx'
        target.parent.mkdir(parents=True, exist_ok=True)
        content = 'export default function RepairTarget() { return <TechIcon />; }\n'
        target.write_text(content, encoding='utf-8')

        def fail(*args, **kwargs):
            raise OSError('owner-secret-must-not-leak')

        @contextmanager
        def failing_open(path, mode, **kwargs):
            with builtins.open(path, mode, **kwargs) as handle:
                if Path(path) == target and mode == ('r' if operation == 'read' else 'w'):
                    yield SimpleNamespace(**{operation: fail})
                else:
                    yield handle

        # Fault the actual internal read/write, not the repair method or generator writes.
        monkeypatch.setattr('agent.omni_repair_engine.open', failing_open, raising=False)

    return inject


@pytest.mark.parametrize('operation', ['read', 'write'])
def test_internal_repair_io_failure_stops_generation(tmp_path, repair_io_failure, operation, caplog):
    repair_io_failure(operation)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'repair'
    assert result['generation_steps'][-1] == {'name': 'repair', 'ok': False}
    assert not any(step['name'] == 'artifacts' for step in result['generation_steps'])
    assert 'owner-secret-must-not-leak' not in json.dumps(result) + caplog.text


@pytest.mark.parametrize('operation', ['read', 'write'])
def test_omni_repair_propagates_sanitized_io_failure(tmp_path, repair_io_failure, operation, caplog):
    repair_io_failure(operation)
    with pytest.raises(OSError, match=operation) as caught:
        OmniRepairEngine().scan_and_repair_project(str(tmp_path))
    rendered = ''.join(traceback.format_exception(caught.value))
    assert 'owner-secret-must-not-leak' not in rendered + caplog.text
    assert str(tmp_path) not in str(caught.value)


def test_preparation_exception_is_a_sanitized_failure(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('owner-secret-must-not-leak')

    monkeypatch.setattr(FullStackUltraEngine, '_build_frontend_files', fail)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'prepare'
    assert 'owner-secret-must-not-leak' not in json.dumps(result)


@pytest.mark.parametrize('returned', [None, False, {}, {'status': 'failed'}])
def test_incomplete_repair_result_is_a_failure(tmp_path, monkeypatch, returned):
    monkeypatch.setattr('agent.omni_repair_engine.OmniRepairEngine.scan_and_repair_project',
                        lambda *a, **kw: returned)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'repair'


def test_schema_explicit_false_is_a_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(FullStackUltraEngine, '_write_database_schema', lambda *a: False)
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'schema_mirror'


def test_repair_canvas_suspense_wrapper_emits_valid_jsx(tmp_path):
    target = tmp_path / 'src/components/motion/CanvasThing.jsx'
    target.parent.mkdir(parents=True)
    target.write_text(
        "import React from 'react';\nimport { Canvas } from '@react-three/fiber';\n"
        "export default function CanvasThing() { return <Canvas onCreated={() => {}} />; }\n",
        encoding='utf-8')
    OmniRepairEngine().scan_and_repair_project(str(tmp_path))
    repaired = target.read_text(encoding='utf-8')
    assert '\\"' not in repaired
    assert '<Suspense fallback={<div className="w-full h-full' in repaired
    assert "import React, { Suspense } from 'react';" in repaired
    assert repaired.count('<Suspense') == repaired.count('</Suspense>') == 1
    assert '<Canvas onCreated={() => {}} />' in repaired


def test_generated_project_ships_premium_shell_and_qa_contract(tmp_path):
    result = generate(tmp_path)
    assert result['success'] is True, result
    home = (tmp_path / 'frontend/src/pages/Home.jsx').read_text(encoding='utf-8')
    assert 'hero-' in home
    assert 'Modern3DScene' not in home
    contract = json.loads((tmp_path / 'qa-contract.json').read_text(encoding='utf-8'))
    assert contract == {'version': 1, 'routes': {
        '/': {'heading': 'Northstar'},
        '/features': {'heading': 'What you can do'},
        '/pricing': {'heading': 'Choose your next step'},
        '/about': {'heading': 'Built for your work'},
        '/contact': {'heading': "Let's talk"},
        '/login': {'heading': 'Sign in'},
        '/register': {'heading': 'Create your account'},
    }}
    assert (tmp_path / 'frontend/public/assets/workflow.svg').is_file()
    assert (tmp_path / 'frontend/public/favicon.svg').is_file()
    assert 'href="/favicon.svg"' in (tmp_path / 'frontend/index.html').read_text(encoding='utf-8')


def test_requested_scene_emits_lazy_genuine_renderer_and_dependencies(tmp_path):
    contract = resolve_generation_contract({'scene': {'archetype': 'cyber_grid'}})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='A records workspace', brand_name='Northstar',
        generation_contract=contract,
    )
    assert result['success'] is True, result
    assert result['scene'] == {'archetype': 'cyber_grid'}
    assert {'name': 'scene', 'ok': True} in result['generation_steps']
    contract = json.loads((tmp_path / 'qa-contract.json').read_text(encoding='utf-8'))
    assert contract['scene'] == {'archetype': 'cyber_grid'}
    shell = (tmp_path / 'frontend/src/components/motion/Modern3DScene.jsx').read_text(encoding='utf-8')
    assert 'Enable 3D' in shell and 'Rotate left' in shell and 'data-scene-state' in shell
    canvas = (tmp_path / 'frontend/src/components/motion/SceneCanvas.jsx').read_text(encoding='utf-8')
    assert '@react-three/fiber' in canvas and 'OrbitControls' in canvas
    home = (tmp_path / 'frontend/src/pages/Home.jsx').read_text(encoding='utf-8')
    assert "lazy(() => import('../components/motion/Modern3DScene.jsx'))" in home
    package = json.loads((tmp_path / 'frontend/package.json').read_text(encoding='utf-8'))
    assert {'three', '@react-three/fiber', '@react-three/drei'} <= set(package['dependencies'])
    assert 'model_path' not in json.dumps(result)


def test_scene_artifact_validation_requires_the_renderer(tmp_path):
    contract = resolve_generation_contract({'scene': {'archetype': 'particle_cosmos'}})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='A records workspace', brand_name='Northstar',
        generation_contract=contract,
    )
    assert result['success'] is True, result
    (tmp_path / 'frontend/src/components/motion/SceneCanvas.jsx').write_text('', encoding='utf-8')
    errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, scene={'archetype': 'particle_cosmos'})
    assert any('SceneCanvas.jsx' in error for error in errors)


@pytest.mark.parametrize('old,new', [
    ('async up(', 'async apply('),
    ('async down(', 'async revert('),
    ('module.exports = {', 'const disconnected = {'),
    ("require('./_guards.js')", "require('./wrong/_guards.js')"),
])
def test_idempotent_generation_rejects_disconnected_migration(tmp_path, old, new):
    assert generate(tmp_path)['success'] is True
    relative = 'backend/migrations/002_create_records_table.js'
    path = tmp_path / relative
    content = path.read_text(encoding='utf-8')
    assert old in content
    path.write_text(content.replace(old, new), encoding='utf-8')
    result = generate(tmp_path)
    assert result['success'] is False
    assert result['failed_stage'] == 'artifacts'
    assert relative in str(result['errors'])


def test_generated_backend_ships_the_idempotent_record_identity_test(tmp_path):
    result = generate(tmp_path)
    assert result['success'] is True, result
    route = (tmp_path / 'backend/routes/records.routes.js').read_text(encoding='utf-8')
    assert 'duplicateRecordId(existing, req.user.id)' in route
    assert '!isUniqueViolation(error)' in route
    assert route.count('Record.findByPk(clientId)') >= 2
    helper = (tmp_path / 'backend/utils/recordIdentity.js').read_text(encoding='utf-8')
    assert 'function isUniqueViolation(error)' in helper
    assert 'module.exports = { isUuidV4, duplicateRecordId, isUniqueViolation };' in helper
    test_file = (tmp_path / 'backend/test/record-identity.test.js').read_text(encoding='utf-8')
    assert "require('node:test')" in test_file
    assert 'isUniqueViolation' in test_file
    package = json.loads((tmp_path / 'backend/package.json').read_text(encoding='utf-8'))
    assert package['scripts']['test'] == 'node --test'


def test_generated_backend_test_gate_runs_the_record_identity_suite(tmp_path):
    """The record-identity suite is dependency-free, so `npm test` proves it
    without a database or an install."""
    from agent.factory_pipeline import test_backend

    assert generate(tmp_path)['success'] is True
    (tmp_path / 'backend/node_modules').mkdir()
    gate = test_backend(str(tmp_path), timeout=120)
    assert gate['ok'] is True, gate
    assert 'accepts canonical v4 uuids only' in gate['stdout_tail']
    assert 'same user can retry the same id; another user cannot' in gate['stdout_tail']
    assert 'recognises unique violations and ignores ordinary errors' in gate['stdout_tail']


def web_app_contract():
    contract = resolve_generation_contract({'prompt': 'Build a records web app'})
    assert contract['app'] == {'web': 'web_app', 'pwa': False, 'mobile': None}
    return contract


def generate_web_app(root, engine=None):
    return (engine or FullStackUltraEngine()).generate_project(
        str(root), prompt='Build a records web app', brand_name='Northstar',
        generation_contract=web_app_contract(),
    )


def test_web_app_generation_skips_marketing_and_writes_app_contract(tmp_path):
    result = generate_web_app(tmp_path)
    assert result['success'] is True, result
    assert not (tmp_path / 'frontend/src/pages/Home.jsx').exists()
    assert not (tmp_path / 'frontend/src/pages/Features.jsx').exists()
    assert not (tmp_path / 'frontend/src/pages/Pricing.jsx').exists()
    assert not (tmp_path / 'frontend/src/pages/Contact.jsx').exists()
    app = (tmp_path / 'frontend/src/App.jsx').read_text(encoding='utf-8')
    assert 'AuthGuard' in app and 'localStorage.getItem(\'token\')' in app
    assert (tmp_path / 'frontend/src/auth.js').is_file()
    app_contract = json.loads((tmp_path / 'app-contract.json').read_text(encoding='utf-8'))
    assert app_contract == {'version': 1, 'web': 'web_app', 'pwa': False, 'mobile': None}
    qa_contract = json.loads((tmp_path / 'qa-contract.json').read_text(encoding='utf-8'))
    assert qa_contract == {'version': 1, 'routes': {
        '/login': {'heading': 'Sign in'},
        '/register': {'heading': 'Create your account'},
        '/dashboard': {'heading': 'Your workspace'},
        '/records': {'heading': 'All records'},
        '/settings': {'heading': 'Account settings'},
    }}
    assert FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='web_app') == []


def test_website_generation_keeps_its_contract_and_writes_app_contract(tmp_path):
    assert generate(tmp_path)['success'] is True
    app_contract = json.loads((tmp_path / 'app-contract.json').read_text(encoding='utf-8'))
    assert app_contract == {'version': 1, 'web': 'website', 'pwa': False, 'mobile': None}
    # The marketing lane is untouched by the app-shell branch.
    assert (tmp_path / 'frontend/src/pages/Home.jsx').is_file()
    assert 'hero-' in (tmp_path / 'frontend/src/pages/Home.jsx').read_text(encoding='utf-8')


def test_web_app_artifact_validation_rejects_a_missing_token_guard(tmp_path):
    assert generate_web_app(tmp_path)['success'] is True
    auth = tmp_path / 'frontend/src/auth.js'
    auth.write_text(
        auth.read_text(encoding='utf-8').replace("localStorage.getItem('token')", ''),
        encoding='utf-8')
    errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='web_app')
    assert any('frontend/src/auth.js' in error for error in errors)


def test_web_none_artifact_validation_does_not_require_the_frontend(tmp_path):
    assert generate_web_app(tmp_path)['success'] is True
    import shutil
    shutil.rmtree(tmp_path / 'frontend')
    (tmp_path / 'qa-contract.json').unlink()
    (tmp_path / 'app-contract.json').write_text(
        json.dumps({'version': 1, 'web': 'none', 'pwa': False,
                    'mobile': {'platforms': ['android'], 'verification': 'none'}}),
        encoding='utf-8')
    assert FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='none') == []
    website_errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='website')
    assert any('frontend' in error for error in website_errors)


def test_web_none_generation_writes_no_frontend_files(tmp_path):
    contract = resolve_generation_contract({
        'app': {'web': 'none', 'mobile': {'platforms': ['android'],
                                         'verification': 'none'}},
    })
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='A records app', brand_name='Northstar',
        generation_contract=contract,
    )
    assert result['success'] is True, result
    assert not (tmp_path / 'frontend').exists()
    assert not (tmp_path / 'src').exists()
    assert not (tmp_path / 'Dockerfile').exists()
    assert not (tmp_path / 'nginx.conf').exists()
    assert (tmp_path / 'backend/routes/records.routes.js').is_file()
    app_contract = json.loads((tmp_path / 'app-contract.json').read_text(encoding='utf-8'))
    assert app_contract['web'] == 'none'
    assert app_contract['mobile']['verification'] == 'none'


def test_app_only_generation_has_no_frontend_and_a_mobile_app(tmp_path):
    contract = resolve_generation_contract({'prompt': 'Build a records app'})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='Build a records app', brand_name='Northstar',
        generation_contract=contract)
    assert result['success'] is True, result
    assert not (tmp_path / 'frontend').exists()
    assert (tmp_path / 'mobile/package.json').is_file()
    assert (tmp_path / 'mobile/.maestro/records.yaml').is_file()
    assert (tmp_path / 'backend/routes/records.routes.js').is_file()
    contract_file = json.loads((tmp_path / 'app-contract.json').read_text(encoding='utf-8'))
    assert contract_file['web'] == 'none'
    assert contract_file['mobile']['verification'] == 'apk_emulator'


def test_pwa_flag_never_reaches_the_written_contract_without_a_web_surface(tmp_path):
    """A caller that hands the engine an app block the contract validator would
    have rejected must not get a contract file the factory refuses to read back."""
    contract = resolve_generation_contract({'app': {
        'web': 'none', 'pwa': False,
        'mobile': {'platforms': ['android'], 'verification': 'none'}}})
    contract['app']['pwa'] = True

    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='A records app', brand_name='Northstar',
        generation_contract=contract,
    )

    assert result['success'] is True, result
    written = json.loads((tmp_path / 'app-contract.json').read_text(encoding='utf-8'))
    assert written['web'] == 'none'
    assert written['pwa'] is False
    assert read_app_contract(str(tmp_path)) == {
        'web': 'none', 'pwa': False,
        'mobile': {'platforms': ['android'], 'verification': 'none'},
    }


def test_mobile_generation_reports_the_package_it_wrote(tmp_path):
    contract = resolve_generation_contract({'prompt': 'Build a records app'})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='Build a records app', brand_name='Northstar',
        generation_contract=contract)

    assert result['mobile']['package'] == 'com.lumicore.northstar'
    assert result['mobile']['platforms'] == ['android']
    assert result['mobile']['verification'] == 'apk_emulator'


def test_web_and_app_generation_has_both_surfaces(tmp_path):
    contract = resolve_generation_contract({'prompt': 'Build a website and app'})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='Build a website and app', brand_name='Northstar',
        generation_contract=contract)
    assert result['success'] is True, result
    assert (tmp_path / 'frontend/src/App.jsx').is_file()
    assert (tmp_path / 'mobile/package.json').is_file()
    compose = (tmp_path / 'docker-compose.yml').read_text(encoding='utf-8')
    assert 'context: ./frontend' in compose
    readme = (tmp_path / 'README.md').read_text(encoding='utf-8')
    assert '### 1. Frontend' in readme
    assert '### 3. Mobile' in readme
    assert '### 4. Docker Deploy' in readme
    readme_count = readme.count('### 2.')
    assert readme_count == 1
    instructions = (tmp_path / 'INSTRUCTIONS.md').read_text(encoding='utf-8')
    assert '### Frontend' in instructions and '### Mobile' in instructions
    assert 'EXPO_PUBLIC_API_URL' in instructions


def test_app_only_generation_omits_frontend_from_compose_and_docs(tmp_path):
    contract = resolve_generation_contract({'prompt': 'Build a records app'})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='Build a records app', brand_name='Northstar',
        generation_contract=contract)
    assert result['success'] is True, result

    compose = (tmp_path / 'docker-compose.yml').read_text(encoding='utf-8')
    assert 'frontend' not in compose.lower()
    readme = (tmp_path / 'README.md').read_text(encoding='utf-8')
    assert 'frontend' not in readme.lower()
    assert 'mobile' in readme.lower()
    instructions = (tmp_path / 'INSTRUCTIONS.md').read_text(encoding='utf-8')
    assert 'frontend' not in instructions.lower()
    assert 'mobile' in instructions.lower()
    assert '10.0.2.2' in instructions


def test_mobile_generation_failure_fails_closed(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        return {'success': False, 'files': [], 'errors': ['Mobile generation failed.'],
                'mobile': {}}

    monkeypatch.setattr(
        'agent.fullstack_ultra_engine.generate_mobile_app', fail)
    contract = resolve_generation_contract({'prompt': 'Build a records app'})
    result = FullStackUltraEngine().generate_project(
        str(tmp_path), prompt='Build a records app', brand_name='Northstar',
        generation_contract=contract)
    assert result['success'] is False, result
    assert result['failed_stage'] == 'mobile_generate'
    assert {'name': 'mobile_generate', 'ok': False} in result['generation_steps']
    assert not any(step['name'] == 'ai_saas_kit' for step in result['generation_steps'])
    assert not (tmp_path / 'backend/routes/records.routes.js').exists()
    assert not (tmp_path / 'database/schema.sql').exists()


def test_mobile_artifact_validation_requires_dependencies_and_maestro(tmp_path):
    assert generate_web_app(tmp_path)['success'] is True
    from agent.design_forge import build_design
    from agent.mobile_app_engine import generate_mobile_app

    mobile_contract = {
        'web': 'web_app',
        'pwa': False,
        'mobile': {'platforms': ['android'], 'verification': 'apk_emulator'},
    }
    generated = generate_mobile_app(
        str(tmp_path), 'Northstar', 'saas',
        build_design('Northstar', 'saas', '#2563eb', '#0d9488'),
        mobile_contract,
    )
    assert generated['success'] is True, generated
    mobile = tmp_path / 'mobile'
    app_contract = json.loads((tmp_path / 'app-contract.json').read_text(encoding='utf-8'))
    app_contract['mobile'] = mobile_contract['mobile']
    (tmp_path / 'app-contract.json').write_text(json.dumps(app_contract), encoding='utf-8')
    errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='web_app', mobile=app_contract['mobile'])
    assert errors == []

    (mobile / '.maestro/records.yaml').unlink()
    errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='web_app', mobile=app_contract['mobile'])
    assert any('mobile/.maestro/records.yaml' in error for error in errors)
    package = json.loads((mobile / 'package.json').read_text(encoding='utf-8'))
    del package['dependencies']['react-native-sse']
    (mobile / 'package.json').write_text(json.dumps(package), encoding='utf-8')
    errors = FullStackUltraEngine._validate_generation_artifacts(
        tmp_path, web_surface='web_app', mobile=app_contract['mobile'])
    assert any('react-native-sse' in error for error in errors)


def test_production_spec_repairs_stale_frontend_instructions(tmp_path):
    from agent.production_spec_kit import apply_production_spec

    backend = tmp_path / 'backend'
    backend.mkdir()
    (backend / 'package.json').write_text(json.dumps({'name': 'app'}), encoding='utf-8')
    (tmp_path / 'INSTRUCTIONS.md').write_text(
        '# INSTRUCTIONS — Old\n\n### Frontend\ncd frontend\n', encoding='utf-8')
    result = apply_production_spec(str(tmp_path), brand='Northstar')

    assert result['status'] == 'ok'
    instructions = (tmp_path / 'INSTRUCTIONS.md').read_text(encoding='utf-8')
    assert 'cd frontend' not in instructions
    assert 'frontend' not in instructions.lower()
    assert 'Backend' in instructions


def test_production_spec_skips_frontend_when_frontend_source_is_absent(tmp_path):
    from agent.production_spec_kit import apply_production_spec

    backend = tmp_path / 'backend'
    backend.mkdir()
    (backend / 'package.json').write_text(json.dumps({'name': 'app'}), encoding='utf-8')
    (tmp_path / 'app-contract.json').write_text(json.dumps({
        'version': 1, 'web': 'none', 'pwa': False,
        'mobile': {'platforms': ['android'], 'verification': 'apk_emulator'},
    }), encoding='utf-8')
    result = apply_production_spec(str(tmp_path), brand='Northstar')

    assert result['status'] == 'ok'
    assert (backend / 'Dockerfile').is_file()
    assert not (tmp_path / 'frontend').exists()
    assert not (tmp_path / 'Dockerfile').exists()
    assert not (tmp_path / 'nginx.conf').exists()
    instructions = (tmp_path / 'INSTRUCTIONS.md').read_text(encoding='utf-8')
    assert 'frontend' not in instructions.lower()
    assert 'mobile' in instructions.lower()
    assert '10.0.2.2' in instructions
