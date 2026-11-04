import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import agent.factory_pipeline as factory
from agent.factory_pipeline import read_app_contract


def _project(tmp_path, *, web='none', pwa=False, mobile=None):
    project = tmp_path / 'app'
    (project / 'backend').mkdir(parents=True)
    (project / 'backend' / 'package.json').write_text('{}', encoding='utf-8')
    (project / 'backend' / 'server.js').write_text('', encoding='utf-8')
    (project / 'app-contract.json').write_text(json.dumps({
        'version': 1,
        'web': web,
        'pwa': pwa,
        'mobile': mobile,
    }), encoding='utf-8')
    return project


def _mobile():
    return {'platforms': ['android'], 'verification': 'apk_emulator'}


def _toolchain_fixture():
    """Match android_toolchain.toolchain(): the mobile stages consume paths, not
    readiness booleans, so a boolean here would hide a producer/consumer drift."""
    root = Path(tempfile.gettempdir()) / 'lumicore-app-delivery-toolchain'
    paths = {
        name: root / name for name in
        ('java_home', 'sdk', 'adb', 'emulator', 'maestro', 'gradle_home', 'avd_home',
         'cmake')
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('', encoding='utf-8')
    return {
        'ready': True,
        'java_home': str(paths['java_home']),
        'sdk': str(paths['sdk']),
        'adb': str(paths['adb']),
        'emulator': str(paths['emulator']),
        'avd': 'lumicore_api35',
        'avd_home': str(paths['avd_home']),
        'maestro': str(paths['maestro']),
        'gradle_home': str(paths['gradle_home']),
        'cmake': str(paths['cmake']),
        'cmake_gap': '',
    }


def _run_mobile_mocks(*, full_stack=False, verify=None, export=None, apk=None,
                      toolchain=None):
    fixture_server = Mock()
    fixture_url = 'http://127.0.0.1:43127'
    calls = []
    apk_evidence = []

    def start_fixture_api(port=0):
        calls.append(('fixture', port))
        return fixture_server, fixture_url

    def export_mobile(project_dir, *, run=None):
        calls.append(('export', project_dir))
        return export or {'ok': True}

    def build_apk(project_dir, toolchain, *, run=None, api_url='', evidence_dir=''):
        calls.append(('apk', api_url))
        apk_evidence.append(evidence_dir)
        return apk or {'ok': True, 'apk': 'android/app.apk', 'sha256': 'abc123'}

    def verify_emulator(project_dir, apk_path, *, toolchain, api_url='', tier='app_runs',
                        run=None, evidence_dir=''):
        calls.append(('emulator', api_url, tier))
        return verify or {
            'ok': True,
            'tier': 'full_stack' if full_stack else 'app_runs',
            'maestro': {'smoke': {'ok': True, 'code': 0}, 'records': {'ok': True, 'code': 0}},
            'test_account': 'mobile-1234abcd@example.test',
        }

    return fixture_server, calls, {
        'agent.mobile_verify.export_mobile': export_mobile,
        'agent.mobile_verify.build_apk': build_apk,
        'agent.mobile_verify.verify_emulator': verify_emulator,
        'agent.mobile_fixture_api.start_fixture_api': start_fixture_api,
        'agent.factory_pipeline._probe_mobile_fixture_api': lambda base_url: {
            'ok': True,
            'status': 'passed',
            'url': f'{base_url}/api/v1/health',
            'body': {'status': 'ok', 'fixture': True},
        },
        'agent.android_toolchain.toolchain': lambda: (
            _toolchain_fixture() if toolchain is None else toolchain
        ),
        'apk_evidence': apk_evidence,
    }


def _api_host_mocks():
    return (
        patch.object(factory, '_host_database',
                     return_value=({'status': 'created', 'database': 'appdb',
                                    'host': 'db.test'}, 'postgres://database/appdb')),
        patch.object(factory, '_host_api',
                     return_value={'status': 'live', 'url': 'https://api.test',
                                   'health_url': 'https://api.test/health',
                                   'verified': True}),
        patch.object(factory, '_prove_api', return_value={'ok': True, 'status': 'verified'}),
    )


def test_missing_app_contract_keeps_legacy_website_lane(tmp_path):
    assert read_app_contract(str(tmp_path)) is None


def test_read_app_contract_returns_only_delivery_surfaces(tmp_path):
    (tmp_path / 'app-contract.json').write_text(json.dumps({
        'version': 1,
        'web': 'none',
        'pwa': False,
        'mobile': {'platforms': ['android'], 'verification': 'apk_emulator'},
        'untrusted_extra': 'ignored',
    }), encoding='utf-8')

    assert read_app_contract(str(tmp_path)) == {
        'web': 'none',
        'pwa': False,
        'mobile': {'platforms': ['android'], 'verification': 'apk_emulator'},
    }


def test_invalid_app_contract_fails_closed(tmp_path):
    (tmp_path / 'app-contract.json').write_text(json.dumps({
        'version': 99,
        'web': 'none',
        'pwa': True,
        'mobile': None,
    }), encoding='utf-8')

    with pytest.raises(ValueError, match='app contract'):
        read_app_contract(str(tmp_path))


def test_app_only_skips_web_stages_and_delivers_verified_mobile(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    fixture_server, calls, mobile_patches = _run_mobile_mocks(full_stack=True)
    host_db, host_api, prove_api = _api_host_mocks()

    with patch.object(factory, 'build_project', side_effect=AssertionError('web build')), \
         patch.object(factory, 'run_qa', side_effect=AssertionError('web QA')), \
         patch.object(factory, 'test_backend', return_value={'ok': True}), \
         host_db, host_api, prove_api, \
         patch('agent.mobile_verify.export_mobile', side_effect=mobile_patches[
             'agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk', side_effect=mobile_patches[
             'agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator', side_effect=mobile_patches[
             'agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']), \
         patch('agent.deploy_engine.deploy_project') as deploy_frontend:
        result = factory.run_factory(str(project), video=False, deploy='vercel')

    assert 'build' not in result['stages']
    assert 'qa' not in result['stages']
    assert result['stages']['deploy']['status'] == 'api-only'
    assert result['stages']['mobile_emulator']['tier'] == 'full_stack'
    assert result['status'] == 'delivered', result.get('failures')
    assert calls == [('export', str(project)), ('apk', 'https://api.test'),
                     ('emulator', 'https://api.test', 'full_stack')]
    handoff = (project / '.factory' / 'report.md').read_text(encoding='utf-8')
    assert 'Requested surfaces' in handoff
    assert 'android/app.apk' in handoff
    assert 'abc123' in handoff
    assert 'full_stack' in handoff
    assert 'skipped surface: `web_build`' in handoff
    assert '## deploy — PASS' in handoff
    fixture_server.shutdown.assert_not_called()
    fixture_server.server_close.assert_not_called()
    deploy_frontend.assert_not_called()


def test_web_and_mobile_requests_run_both_lanes_in_order(tmp_path):
    project = _project(tmp_path, web='website', mobile=_mobile())
    _, calls, mobile_patches = _run_mobile_mocks()
    events = []
    with patch.object(factory, 'build_project',
                      side_effect=lambda *args, **kwargs: (
                          events.append('web build'), {'ok': True, 'dist': 'dist'})[1]), \
         patch.object(factory, 'test_backend',
                       side_effect=lambda *args, **kwargs: (
                           events.append('backend tests'), {'ok': True})[1]), \
         patch.object(factory, 'run_qa',
                       side_effect=lambda *args, **kwargs: (
                           events.append('web QA'), {'ok': True, 'status': 'passed'})[1]), \
         patch('agent.deploy_engine.deploy_project') as deploy_frontend, \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    events.extend(call[0] for call in calls)
    assert events == [
        'web build', 'backend tests', 'web QA', 'export', 'fixture', 'apk', 'emulator',
    ]
    assert result['stages']['build']['ok'] is True
    assert result['stages']['qa']['ok'] is True
    assert result['stages']['mobile_emulator']['tier'] == 'app_runs'
    assert result['status'] == 'partial'


def test_app_only_without_hosting_uses_closed_fixture_and_stays_partial(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    fixture_server, calls, mobile_patches = _run_mobile_mocks(
        verify={'ok': True, 'tier': 'full_stack'},
    )

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch.object(factory, 'build_project', side_effect=AssertionError('web build')), \
         patch.object(factory, 'run_qa', side_effect=AssertionError('web QA')), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['status'] == 'partial'
    assert result['verified'] is False
    assert result['mobile_tier'] == 'app_runs'
    assert result['stages']['mobile_fixture_api']['ok'] is True
    health_path = tmp_path / 'app' / '.factory' / 'mobile' / 'health.json'
    assert health_path.is_file()
    assert json.loads(health_path.read_text(encoding='utf-8')) == {
        'status': 'ok',
        'fixture': True,
        'url': 'http://127.0.0.1:43127/api/v1/health',
    }
    assert result['stages']['mobile_emulator']['ok'] is False
    assert result['stages']['mobile_emulator']['reported_tier'] == 'full_stack'
    assert calls == [('export', str(project)), ('fixture', 0),
                     ('apk', 'http://10.0.2.2:43127/api/v1'),
                     ('emulator', 'http://10.0.2.2:43127/api/v1', 'app_runs')]
    fixture_server.shutdown.assert_called_once()
    fixture_server.server_close.assert_called_once()


def test_hosted_api_without_hosted_database_cannot_verify_full_stack(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    fixture_server, calls, mobile_patches = _run_mobile_mocks(full_stack=True)
    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch.object(factory, '_prove_api', return_value={'ok': True, 'status': 'verified'}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='vercel',
                                     api_url='https://external-api.test')

    assert result['stages']['api']['status'] == 'live'
    assert result['stages']['database']['status'] == 'skipped'
    assert result['mobile_tier'] == 'app_runs'
    assert result['status'] == 'partial'
    assert calls[-1] == ('emulator', 'http://10.0.2.2:43127/api/v1', 'app_runs')
    handoff = (project / '.factory' / 'report.md').read_text(encoding='utf-8')
    assert '## deploy — FAIL/UNVERIFIED' in handoff
    fixture_server.shutdown.assert_called_once()
    fixture_server.server_close.assert_called_once()


def test_mobile_export_failure_blocks_delivery(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks(export={'ok': False, 'message': 'export failed'})

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk') as build_apk:
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['status'] != 'delivered'
    assert any('export failed' in failure for failure in result['failures'])
    build_apk.assert_not_called()


def test_missing_android_toolchain_blocks_mobile_delivery(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks()
    # toolchain() reports readiness through empty path keys and never returns a
    # `missing` list, so the blocked message has to be derived from the paths.
    not_ready = _toolchain_fixture()
    not_ready.update({'ready': False, 'sdk': '', 'adb': '', 'emulator': '',
                      'avd': '', 'maestro': '', 'gradle_home': ''})
    mobile_patches['agent.android_toolchain.toolchain'] = lambda: not_ready

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk') as build_apk, \
         patch('agent.mobile_fixture_api.start_fixture_api') as start_fixture, \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['status'] == 'partial'
    assert any('toolchain' in failure.lower() for failure in result['failures'])
    build_apk.assert_not_called()
    start_fixture.assert_not_called()
    assert result['stages']['mobile_apk']['status'] == 'blocked'
    assert result['mobile_tier'] == 'blocked'
    blocked_message = result['stages']['mobile_apk']['message']
    assert 'Android toolchain is not ready' in blocked_message
    for label in ('Android SDK', 'adb', 'emulator', 'Maestro'):
        assert label in blocked_message, blocked_message


def test_a_cmake_without_a_long_path_aware_ninja_blocks_mobile_delivery(tmp_path):
    """Gradle chooses the CMake package itself, so the too-old ninja bundled with
    one of them only announces itself 12 minutes into the native build."""
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks()
    no_cmake = _toolchain_fixture()
    no_cmake.update({
        'ready': False,
        'cmake': '',
        'cmake_gap': 'run sdkmanager --uninstall "cmake;3.22.1"',
    })
    mobile_patches['agent.android_toolchain.toolchain'] = lambda: no_cmake

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk') as build_apk, \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['stages']['mobile_apk']['status'] == 'blocked'
    build_apk.assert_not_called()
    blocked_message = result['stages']['mobile_apk']['message']
    assert 'CMake with a long-path-aware ninja' in blocked_message
    # "not ready" alone leaves the operator with a blocked delivery and no fix.
    assert 'sdkmanager --uninstall "cmake;3.22.1"' in blocked_message


def test_mobile_apk_failure_blocks_emulator_and_delivery(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks(
        apk={'ok': False, 'status': 'blocked', 'message': 'Android toolchain missing'},
    )

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator') as verify_emulator, \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['status'] == 'partial'
    assert any('Android toolchain missing' in failure for failure in result['failures'])
    verify_emulator.assert_not_called()


def test_mobile_emulator_failure_blocks_delivery(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks(
        verify={'ok': False, 'status': 'failed', 'message': 'Maestro scenario failed',
                'maestro': {}},
    )

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['status'] == 'partial'
    assert any('Maestro scenario failed' in failure for failure in result['failures'])
    handoff = (project / '.factory' / 'report.md').read_text(encoding='utf-8')
    assert '- **Maestro result:** `no flow evidence produced`' in handoff


def test_requested_pwa_failure_is_a_delivery_gate(tmp_path):
    project = _project(tmp_path, web='website', pwa=True)

    with patch.object(factory, 'build_project', return_value={'ok': True, 'dist': 'dist'}), \
         patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch.object(factory, 'run_qa', return_value={
             'ok': True, 'status': 'passed',
             'pwa': {'ok': False, 'failures': ['service worker registration failed']},
         }):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['stages']['pwa']['ok'] is False
    assert result['status'] != 'delivered'
    assert any('service worker registration failed' in failure for failure in result['failures'])


def test_run_qa_preserves_raw_pwa_evidence():
    raw_pwa = {'ok': True, 'failures': [], 'installability': {'ok': True}}
    with patch('agent.extensions.browser_qa.run_browser_qa', return_value={
            'ok': True, 'status': 'passed', 'failures': [], 'pwa': raw_pwa,
        }), patch('agent.extensions.browser_qa.evidence_passes', return_value=True):
        result = factory.run_qa('project')

    assert result['pwa'] == raw_pwa


def test_mobile_verification_none_exports_but_is_never_delivered(tmp_path):
    project = _project(tmp_path, mobile={
        'platforms': ['android'], 'verification': 'none',
    })
    _, calls, mobile_patches = _run_mobile_mocks()
    host_db, host_api, prove_api = _api_host_mocks()

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         host_db, host_api, prove_api, \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk') as build_apk, \
         patch('agent.mobile_verify.verify_emulator') as verify_emulator:
        result = factory.run_factory(str(project), video=False, deploy='vercel')

    assert result['status'] == 'partial'
    assert result['mobile_tier'] == 'not_verified'
    assert calls == [('export', str(project))]
    build_apk.assert_not_called()
    verify_emulator.assert_not_called()


def test_malformed_contract_fails_before_running_delivery_stages(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    (project / 'app-contract.json').write_text('{not json', encoding='utf-8')

    with patch.object(factory, 'build_project') as build, \
         patch.object(factory, 'test_backend') as backend:
        result = factory.run_factory(str(project), video=False)

    assert result['status'] == 'failed'
    assert 'app contract' in result['message'].lower()
    build.assert_not_called()
    backend.assert_not_called()


def test_legacy_project_keeps_website_build_and_qa_lane(tmp_path):
    project = tmp_path / 'legacy'
    project.mkdir()
    with patch.object(factory, 'build_project',
                      return_value={'ok': True, 'dist': 'dist'}) as build, \
         patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch.object(factory, 'run_qa', return_value={'ok': True, 'status': 'passed'}) as qa:
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['stages']['build']['ok'] is True
    assert result['stages']['qa']['ok'] is True
    build.assert_called_once()
    qa.assert_called_once()


def test_contract_without_any_client_surface_fails_closed(tmp_path):
    """A contract that requests neither web nor mobile has no product to deliver,
    so it must not reach the delivered gate as an empty success."""
    project = _project(tmp_path, web='none', mobile=None)

    with patch.object(factory, 'build_project') as build, \
         patch.object(factory, 'test_backend') as backend:
        result = factory.run_factory(str(project), video=False)

    assert result['status'] == 'failed'
    assert 'at least one client surface' in result['message']
    build.assert_not_called()
    backend.assert_not_called()


def test_contract_errors_name_the_broken_field(tmp_path):
    cases = [
        ({'version': 1, 'web': 'blog', 'pwa': False, 'mobile': None},
         'unsupported web surface'),
        ({'version': 1, 'web': 'none', 'pwa': True, 'mobile': None},
         'PWA requires a web surface'),
        ({'web': 'website', 'pwa': False, 'mobile': None},
         'version, web, pwa and mobile are all required'),
        ({'version': 1, 'web': 'website', 'pwa': False,
          'mobile': {'platforms': ['tizen'], 'verification': 'none'}},
         'unsupported mobile platforms'),
    ]
    for index, (payload, expected) in enumerate(cases):
        project = tmp_path / f'contract-case-{index}'
        project.mkdir()
        (project / 'app-contract.json').write_text(json.dumps(payload), encoding='utf-8')
        with pytest.raises(ValueError, match=expected):
            read_app_contract(str(project))


def test_app_only_run_never_films_the_api_host(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks(full_stack=True)
    host_db, host_api, prove_api = _api_host_mocks()

    with patch.object(factory, 'build_project', side_effect=AssertionError('web build')), \
         patch.object(factory, 'run_qa', side_effect=AssertionError('web QA')), \
         patch.object(factory, 'test_backend', return_value={'ok': True}), \
         host_db, host_api, prove_api, \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']), \
         patch('agent.demo_video.generate_demo_video') as video:
        result = factory.run_factory(str(project), video=True, deploy='vercel')

    video.assert_not_called()
    assert result['stages']['video']['status'] == 'skipped'
    assert result['stages']['video']['verified'] is False
    handoff = (project / '.factory' / 'report.md').read_text(encoding='utf-8')
    assert '## video — SKIPPED' in handoff
    assert '## video — PASS' not in handoff
    # The skip must not read as a gate: before this, every prompt-driven app-only
    # delivery capped at `partial` because video defaults to True in the caller.
    assert result['status'] == 'delivered', result.get('failures')


def test_handoff_reports_every_maestro_flow_and_the_apk_evidence(tmp_path):
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks(full_stack=True)
    host_db, host_api, prove_api = _api_host_mocks()

    with patch.object(factory, 'build_project', side_effect=AssertionError('web build')), \
         patch.object(factory, 'run_qa', side_effect=AssertionError('web QA')), \
         patch.object(factory, 'test_backend', return_value={'ok': True}), \
         host_db, host_api, prove_api, \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='vercel')

    assert result['status'] == 'delivered', result.get('failures')
    # build_apk is the only writer of apk.json, so the factory must hand it the
    # evidence directory or the APK proof exists only inside report.json.
    assert mobile_patches['apk_evidence'] == [str(project / '.factory' / 'mobile')]
    handoff = (project / '.factory' / 'report.md').read_text(encoding='utf-8')
    assert 'Maestro result:** `passed` (records passed; smoke passed)' in handoff
    assert 'mobile-1234abcd@example.test' in handoff
    assert 'password was never written to this report' in handoff


def test_toolchain_gaps_are_named_when_the_readiness_report_blanks_them(tmp_path):
    """toolchain() carries paths, not a `missing` list; a not-ready run still has
    to say which component is absent."""
    project = _project(tmp_path, mobile=_mobile())
    _, _, mobile_patches = _run_mobile_mocks(
        toolchain={'ready': False, 'java_home': 'D:/tools/jdk17', 'sdk': 'D:/android-sdk',
                   'avd': 'lumicore_api35', 'gradle_home': 'D:/gradle-cache'},
    )

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk') as build_apk, \
         patch('agent.mobile_fixture_api.start_fixture_api') as start_fixture, \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    message = next(failure for failure in result['failures'] if 'toolchain' in failure.lower())
    assert 'adb' in message and 'Android emulator' in message and 'Maestro' in message
    assert 'JDK 17' not in message
    build_apk.assert_not_called()
    start_fixture.assert_not_called()


def test_ios_requests_are_not_measured_without_blocking_android(tmp_path):
    project = _project(tmp_path, mobile={
        'platforms': ['android', 'ios'], 'verification': 'apk_emulator',
    })
    _, calls, mobile_patches = _run_mobile_mocks()

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch.object(factory, 'build_project', side_effect=AssertionError('web build')), \
         patch.object(factory, 'run_qa', side_effect=AssertionError('web QA')), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk',
               side_effect=mobile_patches['agent.mobile_verify.build_apk']), \
         patch('agent.mobile_verify.verify_emulator',
               side_effect=mobile_patches['agent.mobile_verify.verify_emulator']), \
         patch('agent.mobile_fixture_api.start_fixture_api',
               side_effect=mobile_patches['agent.mobile_fixture_api.start_fixture_api']), \
         patch('agent.factory_pipeline._probe_mobile_fixture_api',
               side_effect=mobile_patches[
                   'agent.factory_pipeline._probe_mobile_fixture_api']), \
         patch('agent.android_toolchain.toolchain',
               side_effect=mobile_patches['agent.android_toolchain.toolchain']):
        result = factory.run_factory(str(project), video=False, deploy='none')

    assert result['stages']['mobile_ios']['status'] == 'not_measured'
    assert result['stages']['mobile_ios']['platforms'] == ['ios']
    assert [call[0] for call in calls] == ['export', 'fixture', 'apk', 'emulator']
    handoff = (project / '.factory' / 'report.md').read_text(encoding='utf-8')
    assert '## mobile_ios — NOT MEASURED' in handoff
    # A requested surface this pipeline never measured must still show up in the
    # buyer's "Not proven" block, not hide behind an all-clear summary line.
    assert '- not measured: `mobile_ios`' in handoff
    assert 'Nothing — every stage above was verified' not in handoff


def test_ios_only_request_blocks_instead_of_blaming_the_toolchain(tmp_path):
    project = _project(tmp_path, mobile={
        'platforms': ['ios'], 'verification': 'apk_emulator',
    })
    _, _, mobile_patches = _run_mobile_mocks()

    with patch.object(factory, 'test_backend', return_value={'ok': True}), \
         patch('agent.mobile_verify.export_mobile',
               side_effect=mobile_patches['agent.mobile_verify.export_mobile']), \
         patch('agent.mobile_verify.build_apk') as build_apk, \
         patch('agent.android_toolchain.toolchain') as resolve_toolchain:
        result = factory.run_factory(str(project), video=False, deploy='none')

    build_apk.assert_not_called()
    resolve_toolchain.assert_not_called()
    assert result['mobile_tier'] == 'blocked'
    assert any('no Android target' in failure for failure in result['failures'])
    assert not any('toolchain is not ready' in failure for failure in result['failures'])
