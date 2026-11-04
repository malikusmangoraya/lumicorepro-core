import json
import re

import pytest
from PIL import Image

from agent.design_forge import build_design
from agent.mobile_app_engine import generate_mobile_app


def _design():
    return build_design('Northstar', 'saas', '#2563eb', '#0d9488')


def _app():
    return {
        'web': 'none',
        'pwa': False,
        'mobile': {
            'platforms': ['android'],
            'verification': 'apk_emulator',
        },
    }


def test_mobile_project_has_auth_records_feed_and_offline_queue(tmp_path):
    result = generate_mobile_app(
        str(tmp_path),
        'Northstar',
        'saas',
        _design(),
        _app(),
        api_base='https://api.example.test/api/v1',
    )

    assert result['success'] is True, result
    assert result['mobile']['platforms'] == ['android']
    assert result['mobile']['verification'] == 'apk_emulator'
    assert result['mobile']['package'] == 'com.lumicore.northstar'
    files = set(result['files'])
    expected = {
        'mobile/app.json',
        'mobile/package.json',
        'mobile/tsconfig.json',
        'mobile/app/_layout.tsx',
        'mobile/app/(auth)/_layout.tsx',
        'mobile/app/(auth)/sign-in.tsx',
        'mobile/app/(auth)/register.tsx',
        'mobile/app/(tabs)/_layout.tsx',
        'mobile/app/(tabs)/index.tsx',
        'mobile/app/(tabs)/records.tsx',
        'mobile/app/(tabs)/settings.tsx',
        'mobile/app/record/[id].tsx',
        'mobile/app/record/new.tsx',
        'mobile/src/api/client.ts',
        'mobile/src/api/auth.ts',
        'mobile/src/api/records.ts',
        'mobile/src/auth/AuthContext.tsx',
        'mobile/src/realtime/useRecordFeed.ts',
        'mobile/src/offline/queue.ts',
        'mobile/src/theme.ts',
        'mobile/assets/icon.png',
        'mobile/assets/adaptive-icon.png',
        'mobile/assets/splash.png',
        'mobile/.maestro/smoke.yaml',
        'mobile/.maestro/records.yaml',
        'mobile/README.md',
    }
    assert expected <= files

    package = json.loads((tmp_path / 'mobile/package.json').read_text(encoding='utf-8'))
    assert package['dependencies']['expo'] == '~58.0.21'
    assert package['dependencies']['expo-constants'] == '~58.0.14'
    assert package['dependencies']['expo-crypto'] == '~58.0.7'
    assert package['dependencies']['expo-linking'] == '~58.0.15'
    assert package['dependencies']['expo-status-bar'] == '~58.0.4'
    assert package['dependencies']['react'] == '19.3.0'
    # Expo's own tooling is the judge, not the local matrix file: api.expo.dev
    # /v2/versions declares facebookReactNativeVersion 0.88.0 for SDK 58, and
    # `expo install --check` + `expo-doctor` both fail the tree at 0.88.1 even
    # though the installed expo/bundledNativeModules.json lists that patch.
    assert package['dependencies']['react-native'] == '0.88.0'
    assert package['dependencies']['expo-router'] == '~58.0.28'
    assert package['dependencies']['expo-secure-store'] == '~58.0.2'
    assert package['dependencies']['expo-splash-screen'] == '~58.0.12'
    # Every pin must satisfy `npx expo install --check` on the installed Expo SDK;
    # 3.1.1 here made that check fail on every generated project.
    assert package['dependencies']['@react-native-async-storage/async-storage'] == '2.2.0'
    assert package['dependencies']['@react-native-community/netinfo'] == '12.0.1'
    assert package['dependencies']['react-native-safe-area-context'] == '~5.10.1'
    assert package['dependencies']['react-native-screens'] == '~4.30.0'
    assert package['dependencies']['react-native-sse'] == '1.2.1'
    assert package['dependencies']['react-native-web'] == '^0.21.4'
    assert package['dependencies']['react-dom'] == package['dependencies']['react']
    assert package['devDependencies']['typescript'] == '~6.0.3'

    app_config = json.loads((tmp_path / 'mobile/app.json').read_text(encoding='utf-8'))
    assert app_config['expo']['android']['package'] == 'com.lumicore.northstar'
    assert app_config['expo']['orientation'] == 'portrait'
    assert app_config['expo']['scheme'] == 'northstar'
    assert 'expo-status-bar' in app_config['expo']['plugins']
    assert 'splash' not in app_config['expo']
    splash_plugin = next(
        plugin for plugin in app_config['expo']['plugins']
        if isinstance(plugin, list) and plugin[0] == 'expo-splash-screen')
    assert splash_plugin[1]['image'] == './assets/splash.png'
    root_layout = (tmp_path / 'mobile/app/_layout.tsx').read_text(encoding='utf-8')
    assert 'useSegments' in root_layout and 'isAuthenticated' in root_layout
    client = (tmp_path / 'mobile/src/api/client.ts').read_text(encoding='utf-8')
    assert 'api.example.test' in client
    assert 'const DEFAULT_API_BASE = "https://api.example.test/api/v1";' in client
    assert 'expo-secure-store' in client
    assert 'expectedOwnerId' in client
    auth = (tmp_path / 'mobile/src/auth/AuthContext.tsx').read_text(encoding='utf-8')
    assert 'signOut' in auth and 'setQueueScope' in auth
    feed = (tmp_path / 'mobile/src/realtime/useRecordFeed.ts').read_text(encoding='utf-8')
    assert 'EventSource' in feed and '15000' in feed and 'AppState' in feed
    assert 'record:changed' in feed
    queue = (tmp_path / 'mobile/src/offline/queue.ts').read_text(encoding='utf-8')
    assert 'MAX_QUEUE_SIZE = 50' in queue
    assert 'setQueueScope' in queue
    assert 'scope !== queueScope' in queue
    assert 'sequential' in queue.lower()
    assert 'clientId' in queue
    assert queue.index('await send(operation)') < queue.index('await writeQueue(latest, key)')
    records_api = (tmp_path / 'mobile/src/api/records.ts').read_text(encoding='utf-8')
    assert 'body?: string' in records_api
    detail = (tmp_path / 'mobile/app/record/[id].tsx').read_text(encoding='utf-8')
    assert 'queued' in detail and 'Queued offline' in detail
    assert 'if (!record) return;' in detail
    assert '<Button title="Retry"' in detail
    assert "enqueueOperation, flushQueue, getQueueScope, QueuedOperation" in records_api
    assert "EventSource<'record:changed'>" in feed

    assert Image.open(tmp_path / 'mobile/assets/icon.png').size == (1024, 1024)
    assert Image.open(tmp_path / 'mobile/assets/adaptive-icon.png').size == (1024, 1024)
    assert Image.open(tmp_path / 'mobile/assets/splash.png').size == (1284, 2778)

    smoke = (tmp_path / 'mobile/.maestro/smoke.yaml').read_text(encoding='utf-8')
    assert 'Sign in' in smoke and 'Create your account' in smoke
    records = (tmp_path / 'mobile/.maestro/records.yaml').read_text(encoding='utf-8')
    for assertion in ('register', 'create', 'detail', 'edit', 'screenshot'):
        assert assertion in records.lower()
    assert '${EMAIL}' in records and '${PASSWORD}' in records
    assert records.count('takeScreenshot:') >= 5
    assert 'Updated Maestro record' in records
    readme = (tmp_path / 'mobile/README.md').read_text(encoding='utf-8')
    assert '10.0.2.2' in readme and 'EXPO_PUBLIC_API_URL' in readme
    assert 'maestro test' in readme and 'EMAIL=' in readme
    assert 'bundled as https://api.example.test/api/v1' in readme


def test_mobile_release_requires_https():
    with pytest.raises(ValueError):
        generate_mobile_app(
            '.',
            'North',
            'saas',
            _design(),
            _app(),
            api_base='http://api.example.test',
        )


def test_maestro_records_flow_keeps_actions_at_the_flow_root(tmp_path):
    generate_mobile_app(
        str(tmp_path),
        'Northstar',
        'saas',
        _design(),
        _app(),
    )
    records = (tmp_path / 'mobile/.maestro/records.yaml').read_text(encoding='utf-8')

    assert '\n    - tapOn:' not in records
    assert '\n- tapOn: "Create your account"' in records


def test_the_auth_group_ships_its_own_layout_so_no_route_name_shows(tmp_path):
    """A route group without a `_layout.tsx` is flattened into the parent stack, and
    that stack's default header prints the raw route name as the visible title.
    proof15 measured the delivered app's sign-in screen showing `(auth)/sign-in`
    where a customer should see nothing or the brand's own words.
    """
    result = generate_mobile_app(str(tmp_path), 'Northstar', 'saas', _design(), _app())

    assert 'mobile/app/(auth)/_layout.tsx' in set(result['files'])
    layout = (tmp_path / 'mobile/app/(auth)/_layout.tsx').read_text(encoding='utf-8')
    assert 'headerShown: false' in layout
    for screen in ('sign-in', 'register'):
        text = (tmp_path / f'mobile/app/(auth)/{screen}.tsx').read_text(encoding='utf-8')
        titles = ' '.join(line for line in text.splitlines() if 'title' in line)
        assert '(auth)' not in titles, screen


def test_every_declared_screen_option_names_a_route_the_generator_wrote(tmp_path):
    """`<Stack.Screen name="X">` on a name no navigator registers is a silent no-op,
    which is how `(auth)` ended up with the default header in the first place."""
    result = generate_mobile_app(str(tmp_path), 'Northstar', 'saas', _design(), _app())
    routes = {path[len('mobile/app/'):] for path in result['files']
              if path.startswith('mobile/app/')}

    dead_options = []
    for layout in sorted(path for path in routes if path.endswith('_layout.tsx')):
        directory = layout.rsplit('/', 1)[0] if '/' in layout else ''
        text = (tmp_path / 'mobile/app' / layout).read_text(encoding='utf-8')
        for name in re.findall(r'<(?:Stack|Tabs)\.Screen name="([^"]+)"', text):
            stem = f'{directory}/{name}' if directory else name
            candidates = {f'{stem}.tsx', f'{stem}.jsx', f'{stem}/index.tsx',
                          f'{stem}/_layout.tsx'}
            if not candidates & routes:
                dead_options.append(f'{layout}: {name}')

    assert dead_options == []


def test_generated_mobile_tree_gitignores_its_build_output(tmp_path):
    """`expo prebuild` writes mobile/android and `expo export` writes mobile/dist
    inside the delivered project, so a customer who commits their download ships
    node_modules, the native toolchain output, and expired bundle metadata."""
    result = generate_mobile_app(str(tmp_path), 'Northstar', 'saas', _design(), _app())

    assert 'mobile/.gitignore' in set(result['files'])
    ignore = (tmp_path / 'mobile/.gitignore').read_text(encoding='utf-8')
    for entry in ('node_modules/', '/android/', '/ios/', 'dist/', '.expo/',
                  '.maestro/test-results/'):
        assert entry in ignore, entry
    # The Maestro flows are part of the delivery; only their recorded results,
    # which `maestro test` writes inside .maestro/, are build output.
    assert '.maestro' not in ignore.splitlines()
    assert '.maestro/smoke.yaml' not in ignore


def test_gitignore_is_written_to_disk_with_the_rest_of_the_project(tmp_path):
    generate_mobile_app(str(tmp_path), 'Northstar', 'saas', _design(), _app())

    assert (tmp_path / 'mobile/.gitignore').is_file()


def test_brand_is_a_jsx_expression_not_quoted_literal_text(tmp_path):
    """{{BRAND}} used to be pasted into JSX text as a JSON string, so the sign-in
    screen rendered the brand wrapped in literal double quotes."""
    generate_mobile_app(str(tmp_path), 'A{B}"C', 'saas', _design(), _app())

    sign_in = (tmp_path / 'mobile/app/(auth)/sign-in.tsx').read_text(encoding='utf-8')
    assert 'const BRAND = "A{B}\\"C";' in sign_in
    assert "fontWeight: '700' }}>{BRAND}</Text>" in sign_in
    assert '}>"' not in sign_in
    assert '{{BRAND}}' not in sign_in
