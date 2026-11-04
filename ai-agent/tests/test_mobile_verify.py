import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

AGENT_ROOT = Path(__file__).resolve().parent.parent
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent import android_toolchain, mobile_verify


def _mobile_project(root):
    mobile = root / 'mobile'
    mobile.mkdir(parents=True)
    (mobile / 'package.json').write_text(
        json.dumps({'dependencies': {'expo': '~58.0.20'}}), encoding='utf-8'
    )
    (mobile / 'app.json').write_text(json.dumps({
        'expo': {'android': {'package': 'com.lumicore.northstar'}},
    }), encoding='utf-8')
    (mobile / 'node_modules').mkdir()
    return mobile


def _toolchain(tmp_path):
    """Toolchain dict in the exact shape android_toolchain.toolchain() returns."""
    def made(relative, *, directory=False):
        path = tmp_path / 'tools' / relative
        if directory:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('', encoding='utf-8')
        return str(path)

    return {
        'ready': True,
        'java_home': made('jdk', directory=True),
        'sdk': made('sdk', directory=True),
        'gradle_home': made('gradle', directory=True),
        'avd_home': made('avd', directory=True),
        'avd': 'lumicore_api35',
        'adb': made('sdk/platform-tools/adb'),
        'emulator': made('sdk/emulator/emulator'),
        'maestro': made('maestro/bin/maestro'),
        'cmake': made('sdk/cmake/3.31.6', directory=True),
        'cmake_gap': '',
    }


def _proc(stdout='', stderr='', code=0):
    """A `subprocess.run` result — the shape `mobile_verify._run` receives.

    Stubs that returned `{'stdout_tail': ...}` imitated the output *of the
    capture window*, so they kept passing while the window dropped data."""
    return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)


_BADGING = (
    "package: name='com.lumicore.northstar' versionCode='1' versionName='1.0.0'\n"
    "sdkVersion:'24'\n"
    "targetSdkVersion:'36'\n"
)

# Expo's own prebuild template, trimmed to what the build has to survive. The
# commented `debuggableVariants` line is faithful: a comment is not a setting, so
# a patch that counts it as configured leaves the APK without JavaScript.
_BUILD_GRADLE = '''apply plugin: "com.facebook.react"

react {
    bundleCommand = "export:embed"

    /* Variants */
    //   The list of variants to that are debuggable. For those we're going to
    //   skip the bundling of the JS bundle and the assets. By default is just 'debug'.
    // debuggableVariants = ["liteDebug", "prodDebug"]
}

android {
    namespace 'com.lumicore.northstar'
}
'''


def _native_project(mobile, *, build_gradle=_BUILD_GRADLE):
    """The native tree `expo prebuild` leaves behind, in the shape Gradle needs."""
    android = mobile / 'android'
    android.mkdir(exist_ok=True)
    (android / 'gradlew.bat').write_text('', encoding='utf-8')
    app = android / 'app'
    app.mkdir(exist_ok=True)
    if build_gradle is not None:
        (app / 'build.gradle').write_text(build_gradle, encoding='utf-8')
    return android


def _write_apk(path, *, bundles=('index.android.bundle',)):
    """A real zip archive, because the APK gate reads it with `zipfile`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('AndroidManifest.xml', 'fixture manifest')
        archive.writestr('assets/app.config', '{}')
        for bundle in bundles:
            archive.writestr(f'assets/{bundle}', 'var __d = {};')
    return path


def test_export_runs_all_platforms_and_typescript(tmp_path):
    mobile = _mobile_project(tmp_path)
    calls = []

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if 'export' in cmd:
            for platform in ('android', 'ios', 'web'):
                bundle = mobile / 'dist' / '_expo' / 'static' / 'js' / platform / 'index.js'
                bundle.parent.mkdir(parents=True, exist_ok=True)
                bundle.write_text('export {};\n', encoding='utf-8')
        return _proc()

    report = mobile_verify.export_mobile(str(tmp_path), run=run)

    assert report['ok'] is True, report
    commands = [' '.join(call) for call in calls]
    assert any('expo export' in command for command in commands)
    assert any('tsc --noEmit' in command for command in commands)
    assert any(call[0].startswith('npm') and 'install' in call for call in calls)
    assert {'android', 'ios', 'web'} <= set(report['platforms'])


def test_export_skips_install_when_manifest_dependencies_are_present(tmp_path):
    mobile = _mobile_project(tmp_path)
    (mobile / 'node_modules' / 'expo').mkdir()
    calls = []

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if 'export' in cmd:
            for platform in ('android', 'ios', 'web'):
                bundle = mobile / 'dist' / '_expo' / 'static' / 'js' / platform / 'index.js'
                bundle.parent.mkdir(parents=True, exist_ok=True)
                bundle.write_text('bundle', encoding='utf-8')
        return _proc()

    report = mobile_verify.export_mobile(str(tmp_path), run=run)

    assert report['ok'] is True, report
    assert not any('install' in call for call in calls)


def test_export_falls_back_when_expo_rejects_all_platform(tmp_path):
    mobile = _mobile_project(tmp_path)
    calls = []

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if '--platform' in cmd and 'all' in cmd:
            return _proc(
                code=1,
                stderr='Invalid platform all. Valid platforms are android, ios, web.',
            )
        if 'export' in cmd:
            platform = cmd[cmd.index('--platform') + 1]
            bundle = mobile / 'dist' / '_expo' / 'static' / 'js' / platform / 'index.js'
            bundle.parent.mkdir(parents=True, exist_ok=True)
            bundle.write_text('bundle', encoding='utf-8')
        return _proc()

    report = mobile_verify.export_mobile(str(tmp_path), run=run)

    assert report['ok'] is True, report
    assert set(report['platforms']) == {'android', 'ios', 'web'}
    assert {call[call.index('--platform') + 1] for call in calls if '--platform' in call} == {
        'all', 'android', 'ios', 'web',
    }


def test_export_fails_when_typescript_check_fails(tmp_path):
    _mobile_project(tmp_path)

    def run(cmd, cwd, timeout=900, env=None):
        if 'tsc' in cmd:
            return _proc(code=2, stderr='type error')
        mobile = Path(cwd)
        bundle = mobile / 'dist' / '_expo' / 'static' / 'js' / 'android' / 'index.js'
        bundle.parent.mkdir(parents=True, exist_ok=True)
        bundle.write_text('bundle', encoding='utf-8')
        return _proc()

    report = mobile_verify.export_mobile(str(tmp_path), run=run)

    assert report['ok'] is False
    assert any('TypeScript' in failure for failure in report['errors'])


def test_apk_missing_output_fails(tmp_path):
    _mobile_project(tmp_path)

    def run(cmd, cwd, timeout=900, env=None):
        return _proc()

    report = mobile_verify.build_apk(
        str(tmp_path),
        _toolchain(tmp_path),
        run=run,
    )

    assert report['ok'] is False
    assert 'APK' in report['message']


def test_apk_reports_hash_package_and_minimum_sdk(tmp_path):
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    report = mobile_verify.build_apk(
        str(tmp_path),
        _toolchain(tmp_path),
        run=run,
    )

    assert report['ok'] is True, report
    assert report['sha256'] == hashlib.sha256(apk.read_bytes()).hexdigest()
    assert report['package'] == 'com.lumicore.northstar'
    assert report['min_sdk'] == 24


def test_apk_build_empties_debuggable_variants_so_the_apk_carries_its_js(tmp_path):
    """A debug APK has no JavaScript at all unless the native project says so.

    @react-native/gradle-plugin's `TaskConfiguration.kt` registers
    `createBundle<Variant>JsAndAssets` only when the variant is *not* in
    `debuggableVariants`, whose default is `['debug','debugOptimized']`. proof8's
    assembled APK therefore listed only `assets/app.config` and
    `assets/app.fingerprint`: it installed, launched, and rendered the redbox
    "Unable to load script. Make sure you're running Metro or that your bundle
    'index.android.bundle' is packaged correctly for release." """
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    report = mobile_verify.build_apk(str(tmp_path), _toolchain(tmp_path), run=run)

    assert report['ok'] is True, report
    gradle = (mobile / 'android' / 'app' / 'build.gradle').read_text(encoding='utf-8')
    active = [
        line for line in gradle.splitlines()
        if line.strip().startswith('debuggableVariants')
    ]
    assert active == ['    debuggableVariants = []'], active
    assert report['js_bundle'] == 'index.android.bundle'


def test_the_debuggable_variants_patch_survives_a_rebuild(tmp_path):
    """`expo prebuild --clean` regenerates the native tree on every build, so the
    patch runs again — and must not stack a second assignment or touch a comment."""
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    for _ in range(2):
        report = mobile_verify.build_apk(str(tmp_path), _toolchain(tmp_path), run=run)
        assert report['ok'] is True, report

    gradle = (mobile / 'android' / 'app' / 'build.gradle').read_text(encoding='utf-8')
    assert gradle.count('debuggableVariants = []') == 1
    assert '// debuggableVariants = ["liteDebug", "prodDebug"]' in gradle


def test_a_native_project_that_cannot_be_told_to_bundle_js_fails_the_build(tmp_path):
    mobile = _mobile_project(tmp_path)

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile, build_gradle='android {\n}\n')
        return _proc()

    report = mobile_verify.build_apk(str(tmp_path), _toolchain(tmp_path), run=run)

    assert report['ok'] is False
    assert 'react' in report['message']


def test_an_apk_without_its_javascript_is_not_reported_as_built(tmp_path):
    """The gate reads the archive, not the Gradle exit code.

    A build that skips the bundle task still succeeds — that is the whole point of
    `debuggableVariants` — so only the APK's own contents can prove the app will
    run without a Metro server."""
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk, bundles=())
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    report = mobile_verify.build_apk(str(tmp_path), _toolchain(tmp_path), run=run)

    assert report['ok'] is False
    assert 'no JavaScript bundle' in report['message']
    assert 'debuggableVariants' in report['message']
    assert report['js_bundle'] == ''


def test_prebuild_regenerates_native_project_without_a_prompt(tmp_path):
    """`expo prebuild` asks "android already exists" and blocks forever on a
    re-run, so the command must carry --clean and never wait on stdin."""
    mobile = _mobile_project(tmp_path)
    _native_project(mobile)
    commands = []

    def run(cmd, cwd, timeout=900, env=None):
        commands.append(list(cmd))
        if 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    report = mobile_verify.build_apk(
        str(tmp_path),
        _toolchain(tmp_path),
        run=run,
    )

    prebuild = next(cmd for cmd in commands if 'prebuild' in cmd)
    assert '--clean' in prebuild
    assert '--no-install' in prebuild
    assert report['steps']['prebuild']['ok'] is True


def test_apk_forwards_fixture_api_url_to_expo_and_gradle(tmp_path):
    mobile = _mobile_project(tmp_path)
    (mobile / 'node_modules' / 'expo').mkdir()
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'
    api_url = 'http://10.0.2.2:43127/api/v1'
    toolchain = _toolchain(tmp_path)
    captured_env = []

    def run(cmd, cwd, timeout=900, env=None):
        captured_env.append((list(cmd), dict(env or {})))
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    report = mobile_verify.build_apk(
        str(tmp_path), toolchain, api_url=api_url, run=run
    )

    assert report['ok'] is True, report
    assert len(captured_env) == 3
    assert all(env['EXPO_PUBLIC_API_URL'] == api_url for _, env in captured_env)
    assert all(env['JAVA_HOME'] == toolchain['java_home'] for _, env in captured_env)
    assert all(env['ANDROID_HOME'] == toolchain['sdk'] for _, env in captured_env)
    assert all(env['ANDROID_SDK_ROOT'] == toolchain['sdk'] for _, env in captured_env)
    assert all(
        env['GRADLE_USER_HOME'] == toolchain['gradle_home'] for _, env in captured_env
    )


def test_apk_badging_survives_a_dump_longer_than_the_capture_limit(tmp_path):
    """`aapt dump badging` prints the `package:` line first and a real dump of a
    generated app measured 5,971 characters, but the runner only keeps the last
    4,000, so a successful build was reported as an APK with no package name.
    The stub returns full stdout the way subprocess does instead of a
    pre-truncated string, which is what hid this from the other badging tests."""
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            padding = '\n'.join(
                f"application-label-{index}: North Star module {index}"
                for index in range(240)
            )
            stdout = (
                "package: name='com.lumicore.northstar' versionCode='1' "
                "versionName='1.0.0' platformBuildVersionName='17'\n"
                "sdkVersion:'24'\n"
                f"targetSdkVersion:'36'\n{padding}\n"
            )
            assert len(stdout) > mobile_verify._CAPTURE_LIMIT
            return SimpleNamespace(returncode=0, stdout=stdout, stderr='')
        return _proc()

    report = mobile_verify.build_apk(
        str(tmp_path),
        _toolchain(tmp_path),
        run=run,
    )

    assert report['ok'] is True, report
    assert report['package'] == 'com.lumicore.northstar'
    assert report['min_sdk'] == 24


def test_apk_badging_fails_closed_instead_of_fabricating_a_truncated_package(tmp_path):
    """A head window that stops inside a quoted value used to let `[^']+` run
    past the truncation marker and capture a two-line "package name", which is
    then written to `apk.json` as passing evidence. A lost header must fail
    closed, not invent an identifier."""
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            stdout = (
                "package: name='com.lumicore.northstar"
                + 'x' * (mobile_verify._CAPTURE_HEAD + 40)
                + "' versionCode='1'\n"
                + "sdkVersion:'24'\n"
                + "uses-permission: name='android.permission.INTERNET'\n" * 120
            )
            assert len(stdout) > mobile_verify._CAPTURE_LIMIT
            return SimpleNamespace(returncode=0, stdout=stdout, stderr='')
        return _proc()

    report = mobile_verify.build_apk(
        str(tmp_path),
        _toolchain(tmp_path),
        run=run,
    )

    assert report['ok'] is False
    assert not report['package']
    assert 'APK badging did not contain a package name' in report['errors']


def test_emulator_checks_the_crash_buffer_behind_the_capture_window(
    tmp_path, monkeypatch
):
    """A booted AVD writes far more than 4,000 characters of logcat, so the
    window the verdict reads cannot prove the run was crash-free. Android's own
    `crash` buffer is small and is scanned as well; a crash there means the
    delivery cannot claim `logcat_clean`."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls = []

    class Process:
        def poll(self):
            return None

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(mobile_verify.subprocess, 'Popen', lambda *a, **k: Process())

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if 'pidof' in cmd:
            return _proc(stdout='4213')
        if 'getprop' in cmd:
            return _proc(stdout='1\n')
        if 'logcat' in cmd and 'crash' in cmd:
            return _proc(stdout=(
                'FATAL EXCEPTION: main\nProcess: com.lumicore.northstar (pid 4213)\n'
            ))
        if 'logcat' in cmd:
            return _proc(stdout='ActivityTaskManager: START u0\n' * 2000)
        return _proc()

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
        evidence_dir=str(tmp_path / 'evidence'),
    )

    assert report['logcat_clean'] is False
    assert report['ok'] is False
    assert any('crash' in failure.lower() for failure in report['failures'])
    assert any('-b' in call and 'crash' in call for call in calls)


def test_emulator_boot_failure_carries_the_emulators_own_diagnosis(tmp_path, monkeypatch):
    """The emulator dies within seconds when the AVD home has no room for its
    userdata partition, and its output went to DEVNULL, so the report could only
    say "exited before boot completed". The reason must reach the failure line
    and the evidence file."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    reason = (
        'FATAL        | Not enough space to create userdata partition. '
        'Available: 3816.84 MB at D:\\android-avd, need 7372.80 MB.\n'
    )

    class Process:
        def poll(self):
            return 1

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 1

        def kill(self):
            return None

    def fake_popen(args, env=None, stdout=None, stderr=None):
        stdout.write(reason)
        stdout.flush()
        return Process()

    monkeypatch.setattr(mobile_verify.subprocess, 'Popen', fake_popen)

    def run(cmd, cwd, timeout=900, env=None):
        return _proc(stdout='0')

    evidence = tmp_path / 'evidence'
    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
        evidence_dir=str(evidence),
    )

    assert report['booted'] is False
    assert 'Not enough space to create userdata partition' in report['failures'][0]
    assert 'Android emulator exited before boot completed' in report['failures'][0]
    saved = evidence / 'emulator-boot.log'
    assert saved.is_file()
    assert 'userdata partition' in saved.read_text(encoding='utf-8')


def test_the_boot_budget_is_the_measured_cold_boot_and_says_so(tmp_path, monkeypatch):
    """proof10: launched 04:47:00, `bootcompleted.ini` written 04:53, and the report
    declared `did not boot within 240 seconds` at 04:51:02 — the device came up after
    a budget that had never been measured against anything."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')

    class Process:
        def poll(self):
            return None

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    ticks = iter(range(0, 100000, 100))
    monkeypatch.setattr(mobile_verify.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(mobile_verify.subprocess, 'Popen', lambda *a, **k: Process())

    def run(cmd, cwd, timeout=900, env=None):
        return _proc(stdout='0')

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
    )

    assert mobile_verify._BOOT_TIMEOUT_SECONDS >= 600
    assert report['booted'] is False
    assert f'within {mobile_verify._BOOT_TIMEOUT_SECONDS} seconds' in report['failures'][0]
    assert isinstance(report['boot_seconds'], int)


def adb_serial_command(cmd):
    """The console serial an `adb -s <serial> …` command is pointed at."""
    return cmd[cmd.index('-s') + 1] if '-s' in cmd else ''


def test_the_emulator_vm_is_stopped_and_not_only_its_launcher(tmp_path, monkeypatch):
    """proof10 left `qemu-system-x86_64-headless.exe` running after its report said
    the device never booted: `process.terminate()` stops `emulator.exe`, which is
    only the launcher, so the VM kept 3,933 MB of committed memory and went on
    writing qcow2 onto a volume at 98% full. Every abandoned proof makes the next
    one harder to boot, so the run has to stop the machine it started."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls = []
    state = {'devices': 'List of devices attached\nemulator-5554  device\n'}

    class Process:
        def poll(self):
            return 1

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(mobile_verify.subprocess, 'Popen', lambda *a, **k: Process())

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if 'kill' in cmd:
            state['devices'] = 'List of devices attached\n'
            return _proc(stdout='OK: killing emulator, bye bye\nOK\n')
        if 'avd' in cmd and 'name' in cmd:
            return _proc(stdout='lumicore_api35\nOK\n')
        if 'devices' in cmd:
            return _proc(stdout=state['devices'])
        return _proc(stdout='0')

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
    )

    assert report['booted'] is False
    assert [adb_serial_command(call) for call in calls if 'kill' in call] == [
        'emulator-5554'
    ], [call for call in calls if 'kill' in call]
    assert not any('stop' in failure for failure in report['failures']), report['failures']


def test_a_run_that_cannot_stop_the_emulator_reports_the_device_it_left_behind(
    tmp_path, monkeypatch
):
    """An emulator that survives the shutdown is a machine-state fact the operator
    has to act on, and the next run's boot budget is already spent because of it."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')

    class Process:
        def poll(self):
            return 1

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    ticks = iter(range(0, 100000, 100))
    monkeypatch.setattr(mobile_verify.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(mobile_verify.subprocess, 'Popen', lambda *a, **k: Process())

    def run(cmd, cwd, timeout=900, env=None):
        if 'avd' in cmd and 'name' in cmd:
            return _proc(stdout='lumicore_api35\nOK\n')
        if 'devices' in cmd:
            return _proc(stdout='List of devices attached\nemulator-5554  device\n')
        return _proc(stdout='0')

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
    )

    assert any('emulator-5554' in failure for failure in report['failures']), (
        report['failures']
    )


def test_a_boot_log_that_ends_in_structural_noise_names_no_reason():
    """The last line of proof10's boot log was the closing brace of the netsim
    argument dump, and it was reported as the emulator's diagnosis:
    `Android emulator did not boot within 240 seconds: }`."""
    netsim_tail = (
        'INFO         | netsim startup\n'
        'netsim I 10-28 23:47:12.400 netsimd.rs:386 - Args {\n'
        '    host_dns: Some(\n        "10.108.166.222",\n    ),\n'
        '}\n'
    )
    assert mobile_verify._boot_reason(netsim_tail) == ''
    assert mobile_verify._boot_reason('ERROR        |\n') == ''
    assert mobile_verify._boot_reason(
        'FATAL        | Not enough space to create userdata partition.\n'
    ).startswith('FATAL')


def test_emulator_rejects_fatal_logcat_output(tmp_path, monkeypatch):
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls = []

    class Process:
        def __init__(self):
            self.terminated = False

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            return 0

    process = Process()
    monkeypatch.setattr(
        mobile_verify.subprocess, 'Popen', lambda *args, **kwargs: process
    )

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if 'pidof' in cmd:
            return _proc(stdout='3747')
        if 'logcat' in cmd:
            return _proc(stdout='FATAL EXCEPTION: main')
        if 'getprop' in cmd:
            return _proc(stdout='1\n')
        return _proc()

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
        evidence_dir=str(tmp_path / 'evidence'),
    )

    assert report['ok'] is False
    assert report['logcat_clean'] is False
    assert process.terminated is True
    assert any('install' in command for command in map(' '.join, calls))


def _booted_device(monkeypatch, *, pid='4213', app='', crash='', events='', maestro=None,
                   install=None):
    """A device that booted, installed and launched, with the three log buffers
    the launch verdict reads supplied verbatim.

    `maestro` maps a flow name to the process result it should produce, or to a
    callable that stages that flow's on-disk artifacts and returns the result."""

    class Process:
        def poll(self):
            return None

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(mobile_verify.subprocess, 'Popen', lambda *a, **k: Process())
    calls = []

    def run(cmd, cwd, timeout=900, env=None):
        calls.append(list(cmd))
        if 'pidof' in cmd:
            return _proc(stdout=pid)
        if 'getprop' in cmd:
            return _proc(stdout='1\n')
        if 'install' in cmd:
            return install or _proc()
        if 'logcat' in cmd:
            buffer = cmd[cmd.index('-b') + 1] if '-b' in cmd else 'app'
            return _proc(stdout={'app': app, 'crash': crash, 'events': events}[buffer])
        if 'test' in cmd:
            outcome = (maestro or {}).get(Path(cmd[-1]).stem)
            if outcome is None:
                return _proc(stdout='Flow completed successfully')
            return outcome(Path(cmd[-1]).stem, env) if callable(outcome) else outcome
        return _proc()

    return calls, run


def _verify_on_device(tmp_path, run):
    return mobile_verify.verify_emulator(
        str(tmp_path),
        str(tmp_path / 'app-debug.apk'),
        toolchain=_toolchain(tmp_path),
        api_url='https://api.example.test/api/v1',
        tier='full_stack',
        run=run,
        evidence_dir=str(tmp_path / 'evidence'),
    )


def test_another_packages_crash_noise_does_not_condemn_the_app_under_test(
    tmp_path, monkeypatch
):
    """Under host memory pressure a booted AVD ANRs whatever it likes: the one
    measured launch carried `ANR in com.google.android.gms` and
    `ANR in com.android.phone` while the app under test was fine. A verdict read
    from the whole device would fail the delivery for somebody else's process."""
    mobile = _mobile_project(tmp_path)
    flows = mobile / '.maestro'
    flows.mkdir()
    for name in ('smoke', 'records'):
        (flows / f'{name}.yaml').write_text(
            'appId: com.lumicore.northstar\n', encoding='utf-8'
        )
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls, run = _booted_device(
        monkeypatch,
        app=(
            'I/ReactNative( 4213): Running "main"\n'
            'I/unknown:BridgelessReact( 4213): ReactInstance is created\n'
        ),
        crash=(
            'E/AndroidRuntime( 2981): FATAL EXCEPTION: main\n'
            'E/AndroidRuntime( 2981): Process: com.google.android.gms.persistent\n'
        ),
        events=(
            'I/am_anr  ( 3021): [0,2981,com.google.android.gms.persistent,'
            'executing service com.google.android.gms/.stats.service]\n'
        ),
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is True, report
    assert report['logcat_clean'] is True
    assert report['app_pid'] == '4213'
    assert any('--pid=4213' in ' '.join(call) for call in calls)
    assert sorted(report['maestro']) == ['records', 'smoke']


def test_an_anr_event_naming_the_app_under_test_condemns_the_launch(
    tmp_path, monkeypatch
):
    """`events` tags every crash and ANR with the process it happened to, so the
    app's own `am_anr` is proof the launch was not clean even when the process
    kept logging benign lines."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        events=(
            'I/am_anr  ( 3021): [0,4213,com.lumicore.northstar,'
            'com.lumicore.northstar/.MainActivity,executing broadcast]\n'
        ),
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['logcat_clean'] is False
    assert any('am_anr' in failure for failure in report['failures'])
    assert report['maestro'] == {}
    assert not any('.maestro/' in ' '.join(call) for call in calls)


def test_an_app_that_cannot_load_its_javascript_is_blamed_on_the_apk(
    tmp_path, monkeypatch
):
    """The redbox measured on proof10 said exactly this, and it is an APK defect,
    not a device one: the debug build shipped no bundle under `assets/`. Naming
    the cause is what lets the fix be the build rather than a retry."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls, run = _booted_device(
        monkeypatch,
        pid='3747',
        app=(
            'W/unknown:BridgelessReact( 3747): ReactHost{0}.handleHostException'
            '(message = "Unable to load script.\n'
            'E/unknown:ReactNative( 3747): java.lang.RuntimeException: Unable to '
            'load script.\n'
            "E/unknown:ReactNative( 3747): Make sure you're running Metro or that "
            "your bundle 'index.android.bundle' is packaged correctly for release.\n"
        ),
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['logcat_clean'] is False
    assert any(
        "Unable to load script" in failure and 'without a bundle under assets/'
        in failure
        for failure in report['failures']
    ), report['failures']
    assert not any('.maestro/' in ' '.join(call) for call in calls)
    evidence = (tmp_path / 'evidence' / 'emulator.json').read_text(encoding='utf-8')
    assert 'Unable to load script' in evidence


def test_a_launch_that_leaves_no_process_stops_before_maestro(
    tmp_path, monkeypatch
):
    """`am start` returning 0 only means the request was accepted; the process can
    still die on its way up. With no pid there is no log to attribute, so the run
    must say the app exited rather than certify an empty logcat as clean."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls, run = _booted_device(monkeypatch, pid='')

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['launched'] is True
    assert report['app_pid'] == ''
    assert report['logcat_clean'] is False
    assert report['failures'][0] == (
        'com.lumicore.northstar is not running after launch; the app process exited'
    )
    assert not any('logcat' in call for call in calls)
    assert not any('.maestro/' in ' '.join(call) for call in calls)


def _avd_config(toolchain, text):
    """Write the target AVD's `config.ini` and return its home directory."""
    directory = Path(toolchain['avd_home']) / f"{toolchain['avd']}.avd"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'config.ini').write_text(text, encoding='utf-8')
    return directory


def _free_mb(value):
    return lambda _path: SimpleNamespace(free=int(value * 1024 * 1024),
                                         total=10 * 1024 ** 3, used=0)


class _ExitedProcess:
    def poll(self):
        return 1

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 1


def test_emulator_blocks_when_the_avd_volume_cannot_hold_its_data_partition(
    tmp_path, monkeypatch
):
    """Measured twice on the same machine: the emulator refuses below 120% of
    `disk.dataPartition.size`, and a boot that does start keeps writing qcow2
    clusters onto the volume the APK install and the evidence also need."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    toolchain = _toolchain(tmp_path)
    _avd_config(
        toolchain,
        'abi.type=x86_64\n' 'disk.dataPartition.size = 6442450944\n',
    )
    monkeypatch.setattr(mobile_verify.shutil, 'disk_usage', _free_mb(3800))
    monkeypatch.setattr(
        mobile_verify.subprocess, 'Popen',
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError('the emulator booted on a volume that cannot hold it')
        ),
    )

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=toolchain,
        api_url='http://10.0.2.2:52545/api/v1',
    )

    assert report['status'] == 'blocked'
    assert report['booted'] is False
    failure = report['failures'][0]
    assert '3800 MB free' in failure, failure
    assert '8397 MB' in failure, failure
    assert '6144 MB data partition' in failure, failure


def test_the_same_volume_is_enough_when_the_partition_fits(tmp_path, monkeypatch):
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    toolchain = _toolchain(tmp_path)
    _avd_config(toolchain, 'abi.type=x86_64\ndisk.dataPartition.size = 6442450944\n')
    monkeypatch.setattr(mobile_verify.shutil, 'disk_usage', _free_mb(20000))
    monkeypatch.setattr(
        mobile_verify.subprocess, 'Popen', lambda *_a, **_k: _ExitedProcess()
    )
    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=toolchain,
        api_url='http://10.0.2.2:52545/api/v1',
    )

    assert report['status'] == 'failed'
    assert 'data partition' not in ' '.join(report['failures'])


def test_an_avd_without_a_readable_partition_size_is_not_blocked(tmp_path, monkeypatch):
    """The gate can only refuse what it can measure; an AVD that does not declare
    a size still has to reach the emulator and fail there, not here."""
    mobile = _mobile_project(tmp_path)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    toolchain = _toolchain(tmp_path)
    _avd_config(toolchain, 'abi.type=x86_64\ndisk.dataPartition.size = <temp>\n')
    monkeypatch.setattr(
        mobile_verify.subprocess, 'Popen', lambda *_a, **_k: _ExitedProcess()
    )
    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=toolchain,
        api_url='http://10.0.2.2:52545/api/v1',
    )

    assert report['status'] == 'failed'
    assert 'data partition' not in ' '.join(report['failures'])


def test_emulator_reports_missing_toolchain_as_blocked(tmp_path):
    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(tmp_path / 'missing.apk'),
        toolchain={'ready': False, 'missing': ['adb', 'emulator']},
        api_url='http://127.0.0.1:5000/api/v1',
        tier='app_runs',
    )

    assert report['ok'] is False
    assert report['status'] == 'blocked'
    assert {'adb', 'emulator'} <= set(report['missing'])


def test_emulator_runs_both_maestro_flows_without_recording_credentials(
    tmp_path, monkeypatch
):
    mobile = _mobile_project(tmp_path)
    flows = mobile / '.maestro'
    flows.mkdir()
    (flows / 'smoke.yaml').write_text('appId: com.lumicore.northstar\n', encoding='utf-8')
    (flows / 'records.yaml').write_text('appId: com.lumicore.northstar\n', encoding='utf-8')
    screenshot = flows / 'test-results' / 'record.png'
    screenshot.parent.mkdir()
    screenshot.write_bytes(b'png')
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    calls = []

    class Process:
        def poll(self):
            return None

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(mobile_verify.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(
        mobile_verify.subprocess, 'Popen', lambda *args, **kwargs: Process()
    )

    def run(cmd, cwd, timeout=900, env=None):
        calls.append((list(cmd), dict(env or {})))
        if 'pidof' in cmd:
            return _proc(stdout='4213')
        if 'getprop' in cmd:
            return _proc(stdout='1\n')
        if 'test' in cmd and env:
            flow = Path(cmd[-1]).stem
            output_dir = Path(cmd[cmd.index('--test-output-dir') + 1])
            capture = output_dir / '2026-10-29_060000' / flow / 'screenshots'
            capture.mkdir(parents=True, exist_ok=True)
            (capture / 'step-001-tap-Sign_in.png').write_bytes(b'png')
            return _proc(stdout=(
                f"flow used {env['EMAIL']} {env['PASSWORD']} "
                'Bearer fixture-access-token access_token=secret-token-value'
            ))
        return _proc()

    report = mobile_verify.verify_emulator(
        str(tmp_path),
        str(apk),
        toolchain=_toolchain(tmp_path),
        api_url='http://10.0.2.2:43127/api/v1',
        run=run,
        evidence_dir=str(tmp_path / 'evidence'),
    )

    assert report['ok'] is True, report
    assert report['booted'] is True
    assert report['installed'] is True
    assert report['launched'] is True
    assert report['logcat_clean'] is True
    assert report['app_pid'] == '4213'
    assert any('--pid=4213' in ' '.join(cmd) for cmd, _ in calls)
    maestro_calls = [
        (cmd, env) for cmd, env in calls
        if 'test' in cmd and '.maestro/' in ' '.join(cmd)
    ]
    assert [cmd[-1] for cmd, _ in maestro_calls] == [
        '.maestro/smoke.yaml',
        '.maestro/records.yaml',
    ]
    assert all(env['EMAIL'].endswith('@example.test') for _, env in maestro_calls)
    assert maestro_calls[0][1]['EMAIL'] == maestro_calls[1][1]['EMAIL']
    assert maestro_calls[0][1]['PASSWORD'] == maestro_calls[1][1]['PASSWORD']
    evidence = tmp_path / 'evidence'
    evidence_text = '\n'.join(
        path.read_text(encoding='utf-8')
        for path in evidence.rglob('*.json')
    )
    assert maestro_calls[0][1]['EMAIL'] not in evidence_text
    assert maestro_calls[0][1]['PASSWORD'] not in evidence_text
    assert 'fixture-access-token' not in evidence_text
    assert 'secret-token-value' not in evidence_text
    assert report['screenshots']
    assert Path(report['screenshots'][0]).is_file()
    assert all('record.png' not in path for path in report['screenshots']), (
        'a PNG that this run did not write was handed out as its own capture'
    )


def _maestro_flows(mobile, names=('smoke', 'records')):
    flows = mobile / '.maestro'
    flows.mkdir(parents=True, exist_ok=True)
    for name in names:
        (flows / f'{name}.yaml').write_text(
            'appId: com.lumicore.northstar\n', encoding='utf-8'
        )
    return flows


def _maestro_run_dir(mobile, flow):
    """The directory `maestro test --test-output-dir` leaves for one flow."""
    run_dir = mobile / '.maestro' / 'test-results' / flow / '2026-10-29_054800' / flow
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _stage_maestro_run(mobile, flow, *, log='', screen=''):
    """Write what one `maestro test` invocation leaves in its output directory."""
    run_dir = _maestro_run_dir(mobile, flow)
    if log:
        logs = run_dir / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        (logs / 'maestro.log').write_text(log, encoding='utf-8')
    if screen:
        screens = run_dir / 'screen-hierarchy'
        screens.mkdir(parents=True, exist_ok=True)
        (screens / 'step-004-assertCondition-Sign_in.json').write_text(
            screen, encoding='utf-8'
        )


def _failing_flow(mobile, flow, *, log='', screen=''):
    """A Maestro stub that fails like the real tool does: the artifacts appear while
    the flow runs, and the console it returns is promotion banners."""
    def run_flow(_flow, _env):
        _stage_maestro_run(mobile, flow, log=log, screen=screen)
        return _proc(stdout=_CONSOLE_SWAMP, code=1)

    return run_flow


# `maestro test` prints ANSI banners and a progress bar that measured over 4,000
# characters, which is the whole window the console evidence keeps.
_CONSOLE_SWAMP = ('+------------------------------------------------------------------------------+\n'
                  * 60)

_SIGN_IN_VERDICT = (
    '05:50:33.471 [DEBUG] maestro.Maestro.setPermissionInternal: Failed to set '
    'permission android.permission.ACCESS_LOCAL_NETWORK: shell command failed\n'
    '05:51:01.996 [ERROR] maestro.orchestra.Orchestra.executeCommands: '
    '[Command execution] CommandFailed: Assertion is false: "Sign in" is visible\n'
)

_SYSTEM_UI_SCREEN = json.dumps({
    'children': [{
        'attributes': {
            'text': "System UI isn't responding",
            'resource-id': 'android:id/alertTitle',
        },
        'children': [
            {'attributes': {'text': 'Close app', 'class': 'android.widget.Button'}},
            {'attributes': {'text': 'Wait', 'class': 'android.widget.Button'}},
        ],
    }],
})


def test_a_maestro_failure_names_the_verdict_its_console_window_lost(
    tmp_path, monkeypatch
):
    """proof12 recorded `Maestro smoke flow failed` with only banners attached,
    while the cause — `Assertion is false: "Sign in" is visible` — sat in the
    `logs/maestro.log` the run had just written beside the flow. A failure nobody
    can diagnose is a re-run of a 17-minute build."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={'smoke': _failing_flow(mobile, 'smoke', log=_SIGN_IN_VERDICT)},
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['maestro']['smoke']['ok'] is False
    assert report['maestro']['smoke']['reason'] == (
        'Assertion is false: "Sign in" is visible'
    )
    assert any(
        'Maestro smoke flow failed: Assertion is false: "Sign in" is visible'
        in failure
        for failure in report['failures']
    ), report['failures']
    assert report['maestro']['records']['ok'] is True


def test_a_dialog_the_device_put_over_the_screen_is_named_as_the_devices_own(
    tmp_path, monkeypatch
):
    """The screen proof12 failed on held nothing but `System UI isn't responding`,
    `Close app` and `Wait`: the host was out of memory and its system UI hung while
    the app under test kept its pid and a clean logcat. The verdict must say whose
    dialog it was, and still refuse to certify the run."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={'smoke': _failing_flow(
            mobile, 'smoke', log=_SIGN_IN_VERDICT, screen=_SYSTEM_UI_SCREEN
        )},
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['maestro']['smoke']['reason'] == (
        'Assertion is false: "Sign in" is visible while the device itself was '
        'showing "System UI isn\'t responding"'
    )
    assert any('System UI isn\'t responding' in f for f in report['failures'])


def test_the_screen_maestro_gave_up_on_is_kept_as_evidence_without_the_credentials(
    tmp_path, monkeypatch
):
    """`maestro.log` inside the generated project carries the run's email and
    password in clear, so copying it into the evidence directory unredacted would
    hand a customer's test credentials to whoever reads the report."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    used = []

    def smoke(_flow, env):
        used.append((env['EMAIL'], env['PASSWORD']))
        _stage_maestro_run(
            mobile, 'smoke',
            log=_SIGN_IN_VERDICT
            + f'05:51:02.114 [DEBUG] maestro.orchestra: using '
            f'{env["EMAIL"]} password {env["PASSWORD"]} '
            'Bearer fixture-access-token\n',
            screen=_SYSTEM_UI_SCREEN,
        )
        return _proc(stdout=_CONSOLE_SWAMP, code=1)

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={'smoke': smoke},
    )

    report = _verify_on_device(tmp_path, run)

    email, password = used[0]
    evidence = tmp_path / 'evidence' / 'maestro'
    log_copy = (evidence / 'smoke.log').read_text(encoding='utf-8')
    assert email not in log_copy and '[redacted-email]' in log_copy
    assert password not in log_copy and '[redacted-password]' in log_copy
    assert 'Bearer [redacted-token]' in log_copy
    assert 'Assertion is false: "Sign in" is visible' in log_copy
    screen_copy = (evidence / 'smoke-screen.json').read_text(encoding='utf-8')
    assert json.loads(screen_copy)['children']
    assert email not in screen_copy and password not in screen_copy
    stored = json.loads((evidence / 'smoke.json').read_text(encoding='utf-8'))
    assert stored['ok'] is False
    assert "System UI isn't responding" in stored['reason']


def test_a_maestro_failure_with_nothing_on_disk_still_reports_the_exit_code(
    tmp_path, monkeypatch
):
    """proof12's `records` run left only an empty timestamp directory — Maestro
    died before writing a log. The verdict must not silently be a bare label with
    no cause at all."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    _maestro_run_dir(mobile, 'records')
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={'records': _proc(stdout='', code=1)},
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['maestro']['records']['reason'] == (
        'exit code 1 with no Maestro log on disk'
    )
    assert any(
        'Maestro records flow failed: exit code 1 with no Maestro log on disk'
        in failure for failure in report['failures']
    ), report['failures']
    assert not (tmp_path / 'evidence' / 'maestro' / 'records.log').exists()


def test_an_earlier_runs_maestro_log_cannot_be_read_as_this_runs(tmp_path, monkeypatch):
    """`--test-output-dir` is a stable path, so proof12's timestamped run was still
    sitting under `test-results/smoke/` when proof14 started on this tree: a flow that
    dies before writing its own log would be diagnosed from the previous run's screen,
    and proof14's evidence directory did in fact carry that earlier run's screenshot
    beside its own. Each flow's results directory is cleared before that flow runs."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    stale_logs = {}
    for flow in ('smoke', 'records'):
        stale_dir = _maestro_run_dir(mobile, flow)
        stale_logs[flow] = stale_dir / 'logs' / 'maestro.log'
        stale_logs[flow].parent.mkdir(parents=True, exist_ok=True)
        stale_logs[flow].write_text(_SIGN_IN_VERDICT, encoding='utf-8')
        stale_shot = stale_dir / 'screenshots'
        stale_shot.mkdir(parents=True, exist_ok=True)
        (stale_shot / 'step-004-assertCondition-Sign_in.png').write_bytes(b'old-run')
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    stale_at_flow_time = []

    def watch(flow):
        def run_flow(_flow, _env):
            stale_at_flow_time.append((flow, stale_logs[flow].is_file()))
            return _proc(stdout=_CONSOLE_SWAMP, code=1)
        return run_flow

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={flow: watch(flow) for flow in ('smoke', 'records')},
    )

    report = _verify_on_device(tmp_path, run)

    assert stale_at_flow_time == [('smoke', False), ('records', False)], (
        'an earlier run log was still on disk when its flow started'
    )
    for flow in ('smoke', 'records'):
        assert report['maestro'][flow]['reason'] == (
            'exit code 1 with no Maestro log on disk'
        ), flow
        assert not (mobile / '.maestro' / 'test-results' / flow).exists(), flow
    assert report['screenshots'] == [], report['screenshots']
    assert report['ok'] is False


def test_a_flow_that_cannot_clear_an_earlier_run_fails_instead_of_misreporting(
    tmp_path, monkeypatch
):
    """A locked results directory from a wedged previous Maestro JVM is the one case
    where the diagnosis on disk is somebody else's. Running the flow anyway would
    print that stale verdict as this run's and copy that stale screenshot as its own
    capture, so the stage has to refuse the flow instead."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    stale_dir = _maestro_run_dir(mobile, 'smoke')
    (stale_dir / 'logs').mkdir(parents=True, exist_ok=True)
    (stale_dir / 'logs' / 'maestro.log').write_text(_SIGN_IN_VERDICT, encoding='utf-8')
    stale_shot = stale_dir / 'screenshots'
    stale_shot.mkdir(parents=True, exist_ok=True)
    (stale_shot / 'step-004-assertCondition-Sign_in.png').write_bytes(b'old-run')
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    real_rmtree = mobile_verify.shutil.rmtree

    def locked(path):
        if path.name == 'smoke':
            raise PermissionError('locked by the previous run')
        return real_rmtree(path)

    monkeypatch.setattr(mobile_verify.shutil, 'rmtree', locked)
    started = []
    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={
            'smoke': lambda flow, _env: started.append(flow) or _proc(code=0),
            'records': lambda flow, _env: started.append(flow) or _proc(code=0),
        },
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert any(
        'Could not clear Maestro smoke results from an earlier run' in failure
        for failure in report['failures']
    ), report['failures']
    assert started == ['records'], 'the flow whose stale results survived was run anyway'
    assert report['maestro']['smoke'].get('reason') is None, report['maestro']['smoke']
    assert 'Assertion is false' not in ' '.join(report['failures'])
    assert not (tmp_path / 'evidence' / 'maestro' / 'smoke.log').exists()
    assert report['screenshots'] == [], report['screenshots']


def test_a_run_that_never_reached_maestro_claims_no_screenshots(tmp_path, monkeypatch):
    """A crash on launch stops the stage before any flow runs, but the previous run's
    screenshot was still lying under `.maestro/`. The copy used to walk the whole tree,
    so the report handed out a picture of a screen this run never measured."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    stale_shot = _maestro_run_dir(mobile, 'smoke') / 'screenshots'
    stale_shot.mkdir(parents=True, exist_ok=True)
    (stale_shot / 'step-001-tap-Sign_in.png').write_bytes(b'old-run')
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        crash=(
            'E/AndroidRuntime( 4213): FATAL EXCEPTION: main\n'
            'E/AndroidRuntime( 4213): Process: com.lumicore.northstar (pid 4213)\n'
        ),
    )

    report = _verify_on_device(tmp_path, run)

    assert report['logcat_clean'] is False
    assert report['maestro'] == {}
    assert report['screenshots'] == [], report['screenshots']


_MAESTRO_ACCOUNT_LOG = (
    '05:51:02.114 [DEBUG] maestro.orchestra: using {EMAIL} password {PASSWORD}\n'
    '05:51:03.998 [ERROR] maestro.orchestra.Orchestra.executeCommands: '
    '[Command execution] CommandFailed: Assertion is false: signing in as '
    '{EMAIL} with password {PASSWORD} was rejected\n'
)


def test_a_maestro_verdict_that_echoes_the_test_account_is_redacted_where_it_prints(
    tmp_path, monkeypatch
):
    """Maestro logs its `--env` values at DEBUG, and a flow that fails on the sign-in
    step can quote them back in the very line the diagnosis is taken from. `reason`
    is copied into the buyer report and into `failures` and into the per-flow evidence
    file, so one unredacted line puts the account password in three places."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    seen = []

    def smoke(_flow, env):
        seen.append((env['EMAIL'], env['PASSWORD']))
        _stage_maestro_run(mobile, 'smoke', log=_MAESTRO_ACCOUNT_LOG.format(**env))
        return _proc(stdout=_CONSOLE_SWAMP, code=1)

    _calls, run = _booted_device(
        monkeypatch,
        app='I/ReactNative( 4213): Running "main"\n',
        maestro={'smoke': smoke},
    )

    report = _verify_on_device(tmp_path, run)

    email, password = seen[0]
    assert report['maestro']['smoke']['reason'] == (
        'Assertion is false: signing in as [redacted-email] with password '
        '[redacted-password] was rejected'
    ), report['maestro']['smoke']['reason']
    assert not any(email in failure or password in failure
                   for failure in report['failures']), report['failures']
    stored = json.loads(
        (tmp_path / 'evidence' / 'maestro' / 'smoke.json').read_text(encoding='utf-8')
    )
    assert email not in json.dumps(stored) and password not in json.dumps(stored)


def test_the_newest_maestro_attempt_supplies_the_verdict_and_its_own_screen(tmp_path):
    """`--test-output-dir` appends rather than replaces, so one flow can leave several
    timestamped attempts behind. The first attempt can die on a dialog the retried
    attempt never saw; pairing the last-written log with a screen from a different
    attempt invents a cause."""
    mobile = _mobile_project(tmp_path)
    attempts = (
        ('2026-10-29_054800', 300, 'Timed out waiting for "Records"',
         "System UI isn't responding"),
        ('2026-10-29_061200', 600, 'Could not find element "Sign in"',
         "Lumicore isn't responding"),
    )
    for stamp, second, verdict, dialog in attempts:
        attempt = mobile / '.maestro' / 'test-results' / 'smoke' / stamp / 'smoke'
        (attempt / 'logs').mkdir(parents=True)
        log = attempt / 'logs' / 'maestro.log'
        log.write_text(
            f'05:51:03.998 [ERROR] maestro.orchestra: {verdict}\n', encoding='utf-8'
        )
        os.utime(log, (second, second))
        (attempt / 'screen-hierarchy').mkdir(parents=True)
        screen = attempt / 'screen-hierarchy' / 'step-004.json'
        screen.write_text(
            json.dumps({'children': [{'attributes': {'text': dialog}}]}),
            encoding='utf-8',
        )
        os.utime(screen, (second, second))

    log_text, screen_text = mobile_verify._maestro_artifacts(mobile, 'smoke')

    assert 'Could not find element "Sign in"' in log_text
    assert 'Timed out waiting for "Records"' not in log_text
    assert "Lumicore isn't responding" in screen_text
    assert "System UI isn't responding" not in screen_text


def test_the_screen_the_run_ended_on_is_read_even_when_maestro_wrote_no_log(tmp_path):
    """proof12's `records` run died before opening `maestro.log` and left only its
    timestamped directory, so without the screen hierarchy the exit code is the whole
    verdict. When two attempts leave screens, the newest is the one it gave up on."""
    mobile = _mobile_project(tmp_path)
    root = mobile / '.maestro' / 'test-results' / 'records'
    for stamp, second, dialog in (
        ('2026-10-29_054800', 300, 'Please sign in to continue'),
        ('2026-10-29_061200', 600, "System UI isn't responding"),
    ):
        attempt = root / stamp / 'records' / 'screen-hierarchy'
        attempt.mkdir(parents=True)
        screen = attempt / 'step-004.json'
        screen.write_text(
            json.dumps({'children': [{'attributes': {'text': dialog}}]}),
            encoding='utf-8',
        )
        os.utime(screen, (second, second))

    log_text, screen_text = mobile_verify._maestro_artifacts(mobile, 'records')

    assert log_text == ''
    assert "System UI isn't responding" in screen_text
    assert 'Please sign in to continue' not in screen_text


def test_the_memory_the_avd_was_promised_is_written_into_the_boot_evidence(
    tmp_path, monkeypatch
):
    """proof12's Maestro flows died on the device's own `System UI isn't responding`
    dialog, and the figure that explains a device-side hang is the RAM the AVD was
    promised against what the host could give it. Evidence without that number reads
    as a bad app instead of a starved rig."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    _avd_config(_toolchain(tmp_path), 'abi.type=x86_64\nhw.ramSize = 2048\n')

    _calls, run = _booted_device(
        monkeypatch, app='I/ReactNative( 4213): Running "main"\n'
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is True, report
    measured = json.loads(
        (tmp_path / 'evidence' / 'emulator.json').read_text(encoding='utf-8')
    )
    assert measured['avd_ram_size'] == '2048'


def test_an_avd_that_declares_no_memory_is_not_held_back_by_it(tmp_path, monkeypatch):
    """Guest RAM is disclosed, never gated — host free memory swings by the minute,
    and refusing a boot on a figure the emulator never asked for would fail
    deliveries the device could complete."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    _avd_config(_toolchain(tmp_path), 'abi.type=x86_64\n')

    _calls, run = _booted_device(
        monkeypatch, app='I/ReactNative( 4213): Running "main"\n'
    )

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is True, report
    measured = json.loads(
        (tmp_path / 'evidence' / 'emulator.json').read_text(encoding='utf-8')
    )
    assert measured['avd_ram_size'] == ''


def test_a_run_that_dies_after_the_boot_still_leaves_its_measurements_behind(
    tmp_path, monkeypatch
):
    """proof13 booted in 125 s and then lost its device mid-install, and the
    evidence directory held only a boot log: the `emulator.json` writer sat past the
    install return, so the boot time, the AVD's RAM promise and the volume figures
    existed only in the driver's stdout. A stage that fails is the stage an operator
    most needs the numbers for."""
    mobile = _mobile_project(tmp_path)
    _maestro_flows(mobile)
    apk = tmp_path / 'app-debug.apk'
    apk.write_bytes(b'apk')
    _avd_config(
        _toolchain(tmp_path), 'abi.type=x86_64\nhw.ramSize = 1536\ndisk.dataPartition.size = 2147483648\n'
    )
    monkeypatch.setattr(mobile_verify.shutil, 'disk_usage', _free_mb(4644))

    _calls, run = _booted_device(monkeypatch, install=_proc(stderr='No space left on device', code=1))

    report = _verify_on_device(tmp_path, run)

    assert report['ok'] is False
    assert report['booted'] is True
    assert report['boot_seconds'] is not None
    assert report['installed'] is False
    assert report['failures'] == ['adb install failed'], report['failures']
    measured = json.loads(
        (tmp_path / 'evidence' / 'emulator.json').read_text(encoding='utf-8')
    )
    assert measured['booted'] is True
    assert measured['boot_seconds'] == report['boot_seconds']
    assert measured['installed'] is False
    assert measured['app_pid'] == ''
    assert measured['avd_ram_size'] == '1536'
    assert measured['avd_data_partition_mb'] == 2048.0
    assert measured['avd_volume_free_mb'] == 4644.0
    assert 'logcat_window' not in measured, 'no log was ever read'
    assert (tmp_path / 'evidence' / 'emulator-boot.log').is_file()


def test_app_runs_uses_ephemeral_fixture_origin_for_build_and_emulator(
    tmp_path, monkeypatch
):
    mobile = _mobile_project(tmp_path)
    (mobile / 'node_modules' / 'expo').mkdir()
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'
    captured_urls = []
    emulator_calls = []

    def run(cmd, cwd, timeout=900, env=None):
        if 'export' in cmd:
            for platform in ('android', 'ios', 'web'):
                bundle = mobile / 'dist' / '_expo' / 'static' / 'js' / platform / 'index.js'
                bundle.parent.mkdir(parents=True, exist_ok=True)
                bundle.write_text('bundle', encoding='utf-8')
        elif 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        if env and 'EXPO_PUBLIC_API_URL' in env:
            captured_urls.append(env['EXPO_PUBLIC_API_URL'])
        return _proc()

    def verify_emulator(*args, **kwargs):
        emulator_calls.append(kwargs)
        return {
            'ok': True,
            'failures': [],
            'screenshots': [],
        }

    monkeypatch.setattr(mobile_verify, 'verify_emulator', verify_emulator)
    report = mobile_verify.verify_mobile(
        str(tmp_path),
        toolchain=_toolchain(tmp_path),
        run=run,
        evidence_dir=str(tmp_path / 'evidence'),
    )

    assert report['export']['ok'] is True, report['export']
    assert report['build']['ok'] is True, report['build']['errors']
    assert report['emulator']['ok'] is True, report['emulator']
    assert report['ok'] is True, report
    assert captured_urls
    api_url = captured_urls[0]
    assert re.fullmatch(r'http://10\.0\.2\.2:\d+/api/v1', api_url)
    assert not api_url.endswith(':5000/api/v1')
    assert all(url == api_url for url in captured_urls)
    assert emulator_calls[0]['api_url'] == api_url
    assert (tmp_path / 'evidence' / 'health.json').is_file()
    assert (tmp_path / 'evidence' / 'apk.json').is_file()


def test_full_stack_verification_requires_explicit_api_url(tmp_path):
    report = mobile_verify.verify_mobile(
        str(tmp_path),
        toolchain=_toolchain(tmp_path),
        tier='full_stack',
    )

    assert report['ok'] is False
    assert any('explicit api_url' in error for error in report['errors'])


@pytest.mark.skipif(
    os.environ.get('MOBILE_EMULATOR_TEST') != '1',
    reason='set MOBILE_EMULATOR_TEST=1 to run the real Android emulator test',
)
def test_opt_in_real_mobile_emulator_verification(tmp_path):
    environment = android_toolchain.check_environment()
    assert environment['ready'], (
        'MOBILE_EMULATOR_TEST=1 requires the Android SDK, JDK, AVD, and Maestro; '
        f"missing: {environment.get('missing', [])}"
    )
    toolchain = android_toolchain.toolchain()
    project_dir = os.environ.get('MOBILE_TEST_PROJECT_DIR')
    assert project_dir and (Path(project_dir) / 'mobile').is_dir(), (
        'MOBILE_EMULATOR_TEST=1 requires MOBILE_TEST_PROJECT_DIR to point at '
        'a generated project'
    )
    report = mobile_verify.verify_mobile(
        project_dir,
        toolchain=toolchain,
        evidence_dir=str(tmp_path / 'evidence'),
    )
    assert report['ok'] is True, report


def _apk_stub(tmp_path, commands):
    """Run stub that fabricates the APK Gradle would emit and records each command."""
    mobile = _mobile_project(tmp_path)
    apk = mobile / 'android' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'

    def run(cmd, cwd, timeout=900, env=None):
        commands.append(list(cmd))
        if 'prebuild' in cmd:
            _native_project(mobile)
        elif 'assembleDebug' in cmd:
            _write_apk(apk)
        elif 'badging' in cmd:
            return _proc(stdout=_BADGING)
        return _proc()

    return mobile, run


def test_apk_build_compiles_only_the_target_avd_abi(tmp_path):
    """RN builds one native library set per ABI; asking for all four to install on
    an x86_64 emulator quadrupled build time until the disk filled and
    mergeDebugNativeLibs failed the whole proof."""
    commands = []
    _mobile, run = _apk_stub(tmp_path, commands)
    toolchain = _toolchain(tmp_path)
    config = Path(toolchain['avd_home']) / 'lumicore_api35.avd' / 'config.ini'
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('abi.type=x86_64\nimage.sysdir.1=x\n', encoding='utf-8')

    report = mobile_verify.build_apk(str(tmp_path), toolchain, run=run)

    assert report['ok'] is True, report
    assert report['abi'] == 'x86_64'
    gradle = next(command for command in commands if 'assembleDebug' in command)
    assert '-PreactNativeArchitectures=x86_64' in gradle


def test_apk_build_keeps_every_abi_when_the_avd_reports_none(tmp_path):
    commands = []
    _mobile, run = _apk_stub(tmp_path, commands)

    report = mobile_verify.build_apk(str(tmp_path), _toolchain(tmp_path), run=run)

    assert report['ok'] is True, report
    assert report['abi'] == ''
    gradle = next(command for command in commands if 'assembleDebug' in command)
    assert not any(str(part).startswith('-PreactNativeArchitectures') for part in gradle)
