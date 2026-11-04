"""Export, build, and exercise Expo projects on an Android emulator."""

import hashlib
import http.client
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from agent.mobile_fixture_api import start_fixture_api


_CAPTURE_LIMIT = 4000
_CAPTURE_HEAD = 1200
_PLATFORMS = ('android', 'ios', 'web')

# The emulator asks for 120% of the AVD's declared data partition before it will
# create userdata; the reserve covers the APK install and the evidence it writes.
_EMULATOR_PARTITION_HEADROOM = 1.2
_EMULATOR_RESERVE_MB = 1024
# A cold `-no-snapshot` boot with software rendering is bounded by the host, not by
# the app. proof10 measured it: the launcher started at 04:47:00 and the AVD wrote
# `bootcompleted.ini` at 04:53 on an 8 GB machine holding 42 MB of free RAM, so the
# 240-second budget that was there before declared failure two minutes early and the
# report said `booted=False` about a device that was coming up fine. The number
# below is that measurement plus margin; a proof that needs more is a machine that
# needs less running on it, and the boot seconds are recorded to show which it was.
_BOOT_TIMEOUT_SECONDS = 900
# `adb emu kill` is asynchronous: the guest tears down and only then leaves the
# device list. proof10's shutdown was measured against a live VM, so the wait is
# bounded by how long a real emulator took to unregister rather than by hope.
_EMULATOR_STOP_TIMEOUT_SECONDS = 60
_CRASH_PATTERNS = ('FATAL EXCEPTION', 'ANR in')
# The redbox React Native raises when the APK has no script to run. Measured in the
# app's own logcat as `E/unknown:ReactNative: java.lang.RuntimeException: Unable to
# load script.` followed by "Make sure you're running Metro or that your bundle
# 'index.android.bundle' is packaged correctly for release".
_JS_BUNDLE_MISSING_MARKER = 'Unable to load script'


def _capture(value):
    """Bound a command's output while keeping its first lines.

    `aapt dump badging` prints the `package:` line first and its real output runs
    past 5,000 characters, so a tail-only window parses as a valid APK with no
    package name. The middle is what a human can live without. Both cuts land on
    a newline so a half-line cannot be read as a whole one, and the window keeps
    the `stdout_tail`/`stderr_tail` key names because persisted evidence files
    and the buyer handoff are shaped by them."""
    text = str(value or '')
    if len(text) <= _CAPTURE_LIMIT:
        return text
    marker = '\n[... truncated ...]\n'
    head = text[:_CAPTURE_HEAD]
    boundary = head.rfind('\n')
    if boundary > 0:
        head = head[:boundary]
    tail = text[-(_CAPTURE_LIMIT - _CAPTURE_HEAD - len(marker)):]
    boundary = tail.find('\n')
    if 0 <= boundary < len(tail) - 1:
        tail = tail[boundary + 1:]
    return head + marker + tail


def _result(value):
    if isinstance(value, dict):
        return {
            'ok': bool(value.get('ok', value.get('code', 1) == 0)),
            'code': value.get('code', 0 if value.get('ok') else 1),
            'stdout_tail': _capture(value.get('stdout_tail', value.get('stdout', ''))),
            'stderr_tail': _capture(value.get('stderr_tail', value.get('stderr', ''))),
            'elapsed_ms': value.get('elapsed_ms', 0),
        }
    return {
        'ok': getattr(value, 'returncode', 1) == 0,
        'code': getattr(value, 'returncode', 1),
        'stdout_tail': _capture(getattr(value, 'stdout', '')),
        'stderr_tail': _capture(getattr(value, 'stderr', '')),
        'elapsed_ms': 0,
    }


def _run(args, cwd, timeout=900, env=None):
    """Run a local command without a shell except for Windows batch files."""
    command = list(map(str, args))
    if os.name == 'nt' and command and command[0].lower().endswith(('.cmd', '.bat')):
        command = ['cmd.exe', '/c', *command]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return _result({
            'ok': completed.returncode == 0,
            'code': completed.returncode,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
            'elapsed_ms': int((time.monotonic() - started) * 1000),
        })
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            'ok': False,
            'code': -1,
            'stdout_tail': _capture(getattr(exc, 'stdout', '')),
            'stderr_tail': _capture(str(exc)),
            'elapsed_ms': int((time.monotonic() - started) * 1000),
        }


def _invoke(run, args, cwd, timeout, env=None):
    try:
        return _result(run(args, str(cwd), timeout=timeout, env=env))
    except Exception as exc:
        return {
            'ok': False,
            'code': -1,
            'stdout_tail': '',
            'stderr_tail': _capture(f'{type(exc).__name__}: {exc}'),
            'elapsed_ms': 0,
        }


def _npx():
    return 'npx.cmd' if os.name == 'nt' else 'npx'


def _npm():
    return 'npm.cmd' if os.name == 'nt' else 'npm'


def _dependency_state(mobile):
    package_path = mobile / 'package.json'
    if not package_path.is_file():
        return None, ['mobile/package.json is missing']
    try:
        package = json.loads(package_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f'mobile/package.json is invalid: {exc}']
    if not isinstance(package, dict):
        return None, ['mobile/package.json must contain an object']
    modules = mobile / 'node_modules'
    dependencies = package.get('dependencies') or {}
    missing = [
        name for name in dependencies
        if not (modules / name.replace('/', os.sep)).exists()
    ]
    return package, missing


def _install_if_needed(mobile, package, missing, *, run, timeout, env=None):
    if not package:
        return None
    if not (mobile / 'node_modules').is_dir() or missing:
        return _invoke(
            run,
            [_npm(), 'install', '--no-audit', '--no-fund'],
            mobile,
            timeout,
            env,
        )
    return None


def _failure(report, message):
    report['errors'].append(message)
    report['ok'] = False
    report['status'] = 'failed'
    report['message'] = message


def _platform_bundles(dist):
    found = {}
    if dist.is_dir():
        for platform in _PLATFORMS:
            found[platform] = any(
                candidate.is_file()
                for root in (
                    dist / '_expo' / 'static' / 'js' / platform,
                    dist / platform,
                )
                if root.is_dir()
                for candidate in root.rglob('*')
            )
    else:
        found = {platform: False for platform in _PLATFORMS}
    return found


def _supports_platform_all(result):
    message = f"{result['stdout_tail']}\n{result['stderr_tail']}".lower()
    return result['code'] != 0 and (
        'invalid platform' in message
        or 'unknown platform' in message
        or ('platform' in message and 'all' in message and 'valid' in message)
    )


def export_mobile(project_dir, *, run=_run, timeout=1800):
    """Export all Expo platforms, type-check the project, and verify bundles."""
    mobile = Path(project_dir) / 'mobile'
    report = {
        'ok': False,
        'status': 'failed',
        'steps': {},
        'errors': [],
        'platforms': [],
    }
    package, missing = _dependency_state(mobile)
    if package is None:
        _failure(report, missing[0])
        return report

    install = _install_if_needed(
        mobile, package, missing, run=run, timeout=timeout
    )
    if install is not None:
        report['steps']['install'] = install
        if not install['ok']:
            _failure(report, 'npm install failed in mobile/')
            return report

    export_result = _invoke(
        run,
        [_npx(), 'expo', 'export', '--platform', 'all'],
        mobile,
        timeout,
    )
    report['steps']['export_all'] = export_result
    if not export_result['ok'] and _supports_platform_all(export_result):
        for platform in _PLATFORMS:
            step = _invoke(
                run,
                [_npx(), 'expo', 'export', '--platform', platform],
                mobile,
                timeout,
            )
            report['steps'][f'export_{platform}'] = step
            if not step['ok']:
                _failure(report, f'Expo export failed for {platform}')
                return report
    elif not export_result['ok']:
        _failure(report, 'Expo export failed')
        return report

    typecheck = _invoke(
        run, [_npx(), 'tsc', '--noEmit'], mobile, timeout
    )
    report['steps']['typescript'] = typecheck
    if not typecheck['ok']:
        _failure(report, 'TypeScript check failed')
        return report

    bundle_state = _platform_bundles(mobile / 'dist')
    report['platforms'] = [
        platform for platform, found in bundle_state.items() if found
    ]
    missing_platforms = [
        platform for platform, found in bundle_state.items() if not found
    ]
    if missing_platforms:
        _failure(
            report,
            f"Expo export did not create mobile/dist bundles for: {', '.join(missing_platforms)}",
        )
        return report
    report.update(ok=True, status='passed')
    return report


_PATH_ALIASES = {
    'java_home': ('java_home',),
    'sdk': ('sdk', 'sdk_path'),
    'gradle_home': ('gradle_home', 'gradle_home_path'),
    'adb': ('adb', 'adb_path'),
    'emulator': ('emulator', 'emulator_path'),
    'maestro': ('maestro', 'maestro_path'),
    'avd_home': ('avd_home',),
    'aapt': ('aapt',),
}


def _toolchain_paths(toolchain, required=()):
    """Resolve installed toolchain paths, rejecting readiness booleans.

    `android_toolchain.check_environment()` reports `sdk: True`, while the build
    stages need the SDK directory; feeding the report in used to write
    `sdk.dir=True` into android/local.properties, so Gradle built against a
    directory literally named "True" and surfaced the mistake as an SDK licence
    failure seven minutes later.
    """
    source = toolchain if isinstance(toolchain, dict) else {}
    paths = {}
    problems = []
    for name, aliases in _PATH_ALIASES.items():
        for alias in (name, *aliases):
            if alias not in source:
                continue
            value = source[alias]
            if value in (None, ''):
                continue
            if not isinstance(value, str):
                problems.append(f'{alias}={value!r} is not a filesystem path')
                break
            if value and not Path(value).exists():
                problems.append(f'{alias} does not exist')
                break
            paths[name] = value
            break
    for name in ('avd', 'build_tools'):
        value = source.get(name)
        if isinstance(value, str) and value:
            paths[name] = value
    for name in required:
        if not paths.get(name):
            problems.append(f'{name} is missing')
    return paths, sorted(set(problems))


def _avd_config_value(paths, key):
    """Read one value out of the target AVD's `config.ini`, or '' if it cannot."""
    avd = paths.get('avd', '')
    if not avd:
        return ''
    home = paths.get('avd_home') or str(Path.home() / '.android' / 'avd')
    config = Path(home) / f'{avd}.avd' / 'config.ini'
    try:
        lines = config.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return ''
    for line in lines:
        name, _, value = line.partition('=')
        if name.strip() == key and value.strip():
            return value.strip()
    return ''


def _avd_abi(paths):
    """Return the ABI the target AVD image ships, or '' when it cannot be read.

    React Native compiles a native library set per ABI, so asking Gradle for all
    four ABIs to install on an x86_64 emulator costs ~4x the build time and disk;
    a full disk then fails the proof inside `mergeDebugNativeLibs`.
    """
    return _avd_config_value(paths, 'abi.type')


def _avd_disk_measurement(paths):
    """Return (partition MB, free MB, volume) for the AVD, with None when unreadable.

    The declared partition size is what the emulator measures against, so a proof
    AVD that declares a smaller disk gets a smaller requirement — and the number
    belongs in the evidence, not in a footnote, or a boot cannot be re-explained."""
    declared = _avd_config_value(paths, 'disk.dataPartition.size')
    try:
        partition_mb = int(declared) / (1024 * 1024)
    except ValueError:
        partition_mb = None
    home = paths.get('avd_home') or str(Path.home() / '.android' / 'avd')
    try:
        free_mb = shutil.disk_usage(home).free / (1024 * 1024)
    except OSError:
        free_mb = None
    return partition_mb, free_mb, home


def _avd_ram(paths):
    """The RAM the target AVD declares, verbatim from its own `config.ini`.

    proof12's Maestro flows died on a `System UI isn't responding` dialog while the
    app under test stayed alive, and the only figure that explains that is how much
    memory the guest was promised against what the host had. Recorded as evidence,
    never as a gate: host free memory swings by the minute, and refusing a boot on
    it would fail deliveries that the device itself could complete."""
    return _avd_config_value(paths, 'hw.ramSize')


def _emulator_disk_gap(paths):
    """Return why the AVD volume cannot hold an emulator boot, or '' when it can.

    Measured on the same volume twice: the emulator refuses to create userdata
    below 120% of `disk.dataPartition.size` (a 6,144 MB partition asks for
    7,372.80 MB), and a boot that does start keeps writing qcow2 clusters onto the
    volume that also has to take the APK install and the evidence files.
    """
    partition_mb, free_mb, home = _avd_disk_measurement(paths)
    if partition_mb is None or free_mb is None:
        return ''
    needed_mb = partition_mb * _EMULATOR_PARTITION_HEADROOM + _EMULATOR_RESERVE_MB
    if free_mb >= needed_mb:
        return ''
    return (
        f'{free_mb:.0f} MB free at {home}, needs {needed_mb:.0f} MB for the AVD\'s '
        f'{partition_mb:.0f} MB data partition plus {_EMULATOR_RESERVE_MB} MB of '
        'install and evidence headroom'
    )


def _build_env(paths, api_url):
    env = dict(os.environ)
    if paths.get('java_home'):
        env['JAVA_HOME'] = paths['java_home']
    if paths.get('sdk'):
        env['ANDROID_HOME'] = paths['sdk']
        env['ANDROID_SDK_ROOT'] = paths['sdk']
    if paths.get('gradle_home'):
        env['GRADLE_USER_HOME'] = paths['gradle_home']
    if api_url:
        env['EXPO_PUBLIC_API_URL'] = api_url
    return env


def _package_name(mobile):
    app_config = mobile / 'app.json'
    if not app_config.is_file():
        return ''
    try:
        config = json.loads(app_config.read_text(encoding='utf-8'))
        return str((config.get('expo') or {}).get('android', {}).get('package') or '')
    except (OSError, json.JSONDecodeError, AttributeError):
        return ''


def _apk_badging(paths, apk, mobile, *, run, timeout, env):
    sdk = paths.get('sdk')
    aapt = paths.get('aapt')
    if not aapt and sdk:
        build_tools = (paths.get('build_tools') or '35.0.0')
        aapt = str(Path(sdk) / 'build-tools' / str(build_tools) /
                   ('aapt.exe' if os.name == 'nt' else 'aapt'))
    if not aapt:
        return None, 'Android aapt is not configured in the toolchain'
    result = _invoke(
        run, [aapt, 'dump', 'badging', str(apk)], mobile, timeout, env
    )
    if not result['ok']:
        return None, f"Could not inspect APK badging: {result['stderr_tail']}"
    output = f"{result['stdout_tail']}\n{result['stderr_tail']}"
    package_match = re.search(r"package:\s+name='([^'\n]+)'", output)
    min_sdk_match = re.search(r"minSdkVersion=['\"]?(\d+)", output)
    if not min_sdk_match:
        min_sdk_match = re.search(r"sdkVersion:['\"]?(\d+)", output)
    if not package_match:
        return None, 'APK badging did not contain a package name'
    if not min_sdk_match:
        return None, 'APK badging did not contain a minimum SDK'
    return {
        'package': package_match.group(1),
        'min_sdk': int(min_sdk_match.group(1)),
    }, ''


def _bundle_js_in_debug_build(android):
    """Tell the native project to put JavaScript inside the debug APK.

    @react-native/gradle-plugin registers `createBundle<Variant>JsAndAssets` only
    for variants that are *not* in `debuggableVariants` (`TaskConfiguration.kt`,
    default `['debug', 'debugOptimized']`), so a stock `assembleDebug` succeeds
    without bundling a byte of JS. proof8's APK measured that: it listed only
    `assets/app.config` and `assets/app.fingerprint`, installed cleanly, launched
    cleanly, and rendered "Unable to load script. Make sure you're running Metro
    or that your bundle 'index.android.bundle' is packaged correctly for release."
    An empty list bundles the debug variant the way release does while keeping the
    debug signing config, which is what makes the APK installable and standalone.
    `expo prebuild --clean` rewrites this file every build, so the patch is applied
    per build and must stay idempotent. Returns '' or why the build cannot proceed.
    """
    build_gradle = Path(android) / 'app' / 'build.gradle'
    try:
        text = build_gradle.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as exc:
        return (
            f'APK build cannot proceed: {build_gradle} is unreadable after Expo '
            f'prebuild ({type(exc).__name__})'
        )
    if re.search(r'(?m)^\s*debuggableVariants\b', text):
        return ''
    if not re.search(r'(?m)^\s*react\s*\{', text):
        return (
            'APK build cannot proceed: android/app/build.gradle has no `react { }` '
            'block, so the debug variant cannot be told to bundle its JavaScript'
        )
    patched = re.sub(
        r'(?m)^(\s*react\s*\{)\n',
        lambda match: f'{match.group(1)}\n    debuggableVariants = []\n',
        text,
        count=1,
    )
    try:
        build_gradle.write_text(patched, encoding='utf-8')
    except OSError as exc:
        return (
            f'APK build cannot proceed: could not write {build_gradle} '
            f'({type(exc).__name__})'
        )
    return ''


def _apk_js_bundle(apk):
    """Return (bundle asset name, gap) for the JavaScript inside an APK.

    Gradle exits 0 whether or not it bundled, so the archive is the only evidence
    that the app can start without a Metro server on the host."""
    try:
        with zipfile.ZipFile(apk) as archive:
            names = archive.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        return '', f'APK could not be read as a zip archive: {type(exc).__name__}'
    bundles = sorted(
        name for name in names
        if name.startswith('assets/') and name.endswith('.bundle')
    )
    if bundles:
        return bundles[0].rsplit('/', 1)[-1], ''
    return '', (
        'the APK contains no JavaScript bundle under assets/, so it can only run '
        'against a Metro server on the build host; android/app/build.gradle must '
        'set `react { debuggableVariants = [] }` before assembleDebug'
    )


def build_apk(
    project_dir,
    toolchain,
    *,
    api_url='',
    run=_run,
    timeout=3600,
    evidence_dir='',
):
    """Prebuild and assemble a debug APK, reporting its hash and manifest data."""
    mobile = Path(project_dir) / 'mobile'
    report = {
        'ok': False,
        'status': 'failed',
        'apk': '',
        'sha256': '',
        'package': '',
        'min_sdk': None,
        'abi': '',
        'js_bundle': '',
        'errors': [],
        'steps': {},
    }
    if not toolchain or not toolchain.get('ready'):
        report['status'] = 'blocked'
        report['errors'].append('Android toolchain is not ready')
        report['missing'] = list((toolchain or {}).get('missing', []))
        report['message'] = report['errors'][0]
        return report

    paths, path_problems = _toolchain_paths(toolchain, required=('java_home', 'sdk'))
    if path_problems:
        report['status'] = 'blocked'
        report['errors'].append(
            'Android toolchain paths are not usable: ' + '; '.join(path_problems)
        )
        report['message'] = report['errors'][0]
        return report

    package, missing = _dependency_state(mobile)
    if package is None:
        _failure(report, missing[0])
        return report
    env = _build_env(paths, api_url)
    install = _install_if_needed(
        mobile, package, missing, run=run, timeout=timeout, env=env
    )
    if install is not None:
        report['steps']['install'] = install
        if not install['ok']:
            _failure(report, 'npm install failed in mobile/')
            return report

    prebuild = _invoke(
        run,
        [
            _npx(), 'expo', 'prebuild', '--platform', 'android',
            '--no-install', '--clean',
        ],
        mobile,
        timeout,
        env,
    )
    report['steps']['prebuild'] = prebuild
    if not prebuild['ok']:
        _failure(report, 'Expo Android prebuild failed')
        return report

    android = mobile / 'android'
    bundle_gap = _bundle_js_in_debug_build(android)
    if bundle_gap:
        _failure(report, bundle_gap)
        return report
    gradle = android / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
    if not gradle.is_file():
        _failure(report, 'APK build cannot proceed: Gradle wrapper is missing after Expo prebuild')
        return report
    gradle_cmd = [str(gradle), 'assembleDebug']
    abi = _avd_abi(paths)
    if abi:
        gradle_cmd.append(f'-PreactNativeArchitectures={abi}')
    report['abi'] = abi
    gradle_result = _invoke(run, gradle_cmd, android, timeout, env)
    report['steps']['gradle'] = gradle_result
    if not gradle_result['ok']:
        _failure(report, 'Gradle assembleDebug failed')
        return report

    apk = android / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'
    if not apk.is_file():
        _failure(report, 'Debug APK was not created')
        return report
    report['apk'] = str(apk.resolve())
    report['sha256'] = hashlib.sha256(apk.read_bytes()).hexdigest()
    js_bundle, js_gap = _apk_js_bundle(apk)
    if js_gap:
        _failure(report, f'Debug APK was built without its JavaScript: {js_gap}')
        return report
    report['js_bundle'] = js_bundle

    badging, error = _apk_badging(
        paths, apk, mobile, run=run, timeout=timeout, env=env
    )
    if error:
        _failure(report, error)
        return report
    report['package'] = badging['package']
    report['min_sdk'] = badging['min_sdk']
    configured_package = _package_name(mobile)
    if configured_package and configured_package != report['package']:
        _failure(
            report,
            'APK package does not match mobile/app.json '
            f'({report["package"]} != {configured_package})',
        )
        return report
    report.update(ok=True, status='passed')
    if evidence_dir:
        try:
            _write_json(Path(evidence_dir) / 'apk.json', {
                'apk': report['apk'],
                'sha256': report['sha256'],
                'package': report['package'],
                'min_sdk': report['min_sdk'],
                'abi': report['abi'],
                'js_bundle': report['js_bundle'],
                'api_url': api_url,
            })
        except OSError as exc:
            _failure(report, f'Could not write APK evidence: {type(exc).__name__}')
    return report


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def _evidence_safe(value, email, password):
    text = str(value or '')
    if email:
        text = text.replace(email, '[redacted-email]')
    if password:
        text = text.replace(password, '[redacted-password]')
    text = re.sub(
        r'(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*',
        'Bearer [redacted-token]',
        text,
    )
    text = re.sub(
        r'(?i)("(?:access_?token|refresh_?token|token|password|email)"\s*:\s*")[^"]*(")',
        r'\1[redacted]\2',
        text,
    )
    text = re.sub(
        r'(?i)\b(?:access_?token|refresh_?token|token|password|email)\s*[=:]\s*[^\s,;]+',
        '[redacted-credential]',
        text,
    )
    return text


def _copy_maestro_screenshots(evidence_dir, results_dirs):
    """Copy PNGs only from the flow output directories this run cleared and filled.

    The flow YAMLs keep their anchor images under `.maestro/`, and a wedged earlier
    run leaves its own screenshots in the same roots. Neither is evidence of this
    run, so the caller hands in exactly the directories it owns.
    """
    screenshots = []
    destination = evidence_dir / 'maestro' / 'screenshots'
    for root in results_dirs:
        if not root.is_dir():
            continue
        for image in sorted(root.rglob('*.png')):
            try:
                target = destination / root.name / image.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(image, target)
                screenshots.append(str(target))
            except OSError:
                continue
    return screenshots


def _read_package(mobile, paths, apk, run, timeout, env):
    package = _package_name(mobile)
    if package:
        return package
    badging, error = _apk_badging(
        paths, Path(apk), mobile, run=run, timeout=timeout, env=env
    )
    if error:
        return ''
    return badging['package']


def _boot_reason(text):
    """Pick the line that explains a boot failure, not the banner noise around it.

    proof10's boot log ended inside the netsim argument dump, so "the last line"
    was a single `}` and the failure read
    `Android emulator did not boot within 240 seconds: }`. A reason has to name
    something, so a line with no word in it is not one and the whole log stays in
    `emulator-boot.log` for a human."""
    for line in text.splitlines():
        if 'FATAL' not in line and 'ERROR' not in line:
            continue
        stripped = line.strip()
        if any(character.isalpha() for character in stripped.rsplit('|', 1)[-1]):
            return stripped
    return ''


def _avd_serial(run, adb, avd, cwd, env):
    """Return the console serial of the emulator hosting `avd`, or ''.

    `adb emu kill` is the only command that stops the virtual machine, and it needs
    the serial the emulator picked for itself. Matching on `emu avd name` keeps the
    shutdown pointed at the AVD this run launched rather than at whatever else is
    attached."""
    listed = _invoke(run, [adb, 'devices'], cwd, 30, env)
    if not listed['ok']:
        return ''
    for line in listed['stdout_tail'].splitlines()[1:]:
        fields = line.split()
        if not fields or not fields[0].startswith('emulator-'):
            continue
        serial = fields[0]
        named = _invoke(run, [adb, '-s', serial, 'emu', 'avd', 'name'], cwd, 30, env)
        if named['ok'] and named['stdout_tail'].split('\n')[0].strip() == avd:
            return serial
    return ''


def _stop_emulator(run, adb, avd, process, cwd, env):
    """Stop the emulator this run started; return '' or the device still attached.

    `process.terminate()` kills `emulator.exe`, which is only the launcher. proof10
    measured the consequence: the report said the device never booted while
    `qemu-system-x86_64-headless.exe` was still running with its guest coming up
    normally, holding 3,933 MB of committed memory on an 8 GB host and growing
    `userdata-qemu.img.qcow2` to 825 MB on a volume at 98% full. A leak like that
    spends the next run's boot budget before it starts, so it is closed here and
    named in the report when it cannot be."""
    serial = _avd_serial(run, adb, avd, cwd, env)
    if serial:
        _invoke(run, [adb, '-s', serial, 'emu', 'kill'], cwd, 60, env)
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    deadline = time.monotonic() + _EMULATOR_STOP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if not _avd_serial(run, adb, avd, cwd, env):
            return ''
        time.sleep(2)
    return (
        f'{serial or avd} is still attached; stop it before the next run, because a '
        'live emulator spends the memory and disk the next boot needs'
    )


def _app_pid(run, adb, package, mobile, env):
    """Return the pid of the launched app, or '' when Android is not running it."""
    if not package:
        return ''
    result = _invoke(run, [adb, 'shell', 'pidof', package], mobile, 30, env)
    if not result['ok']:
        return ''
    fields = result['stdout_tail'].split()
    return fields[0] if fields and fields[0].isdigit() else ''


def _app_logs(run, adb, package, pid, mobile, env):
    """Collect the three logs that can show the app under test misbehaving.

    A whole-device logcat is simultaneously too noisy and too small. Measured on a
    launch where the app itself was fine, it carried `ANR in
    com.google.android.gms`, `ANR in com.android.phone` and
    `ANR in com.google.android.googlequicksearchbox:search` from host memory
    pressure, while the app's own `Unable to load script` exception sat at line
    2,797 of 4,052 — outside the 4,000-character window any verdict has to be read
    from. So the app's process is filtered on the device with `--pid`, and the two
    buffers that name a process on every line (`crash`, and `events`'
    `am_crash`/`am_anr`) are attributed to the package instead of pattern-matched
    anywhere in the dump."""
    return {
        'app': _invoke(
            run, [adb, 'logcat', '-d', '-v', 'brief', f'--pid={pid}'],
            mobile, 60, env,
        ),
        'crash': _invoke(
            run, [adb, 'logcat', '-d', '-b', 'crash', '-v', 'brief'],
            mobile, 60, env,
        ),
        'events': _invoke(
            run, [adb, 'logcat', '-d', '-b', 'events', '-v', 'brief'],
            mobile, 60, env,
        ),
    }


def _app_crash_reason(logs, package):
    """Why the app under test is not clean, or '' when nothing is its fault."""
    app_output = f"{logs['app']['stdout_tail']}\n{logs['app']['stderr_tail']}"
    if _JS_BUNDLE_MISSING_MARKER.lower() in app_output.lower():
        return (
            'the app could not load its JavaScript (it logged '
            f"'{_JS_BUNDLE_MISSING_MARKER}'), which means the APK shipped without "
            'a bundle under assets/'
        )
    if any(pattern in app_output for pattern in _CRASH_PATTERNS):
        return 'the app logged a fatal exception or an application not responding'
    crash_output = f"{logs['crash']['stdout_tail']}\n{logs['crash']['stderr_tail']}"
    if package and package in crash_output:
        return f'Android recorded a crash for {package} in the crash buffer'
    events_output = f"{logs['events']['stdout_tail']}\n{logs['events']['stderr_tail']}"
    for line in events_output.splitlines():
        if package and package in line and ('am_crash' in line or 'am_anr' in line):
            return f'Android recorded a crash or ANR for {package}: {line.strip()}'
    return ''


def _app_logs_readable(logs):
    """Return the name of a log that could not be read, or '' when all three were."""
    for name, log in logs.items():
        if not log['ok']:
            return name
    return ''


_MAESTRO_REASON_MARKERS = ('Assertion is false', 'Could not find', 'Timed out')


def _newest(paths):
    """The most recently modified of `paths`, ignoring any that vanished mid-scan.

    A file Maestro deleted between the glob and the `stat` must not take the report
    down: an unreadable artifact degrades to no artifact, and the caller still gets a
    verdict out of the exit code."""
    statable = []
    for path in paths:
        try:
            statable.append((path.stat().st_mtime, path))
        except OSError:
            continue
    if not statable:
        return None
    return max(statable, key=lambda entry: entry[0])[1]


def _maestro_artifacts(mobile, flow):
    """Maestro's own log for the run, and the screen it gave up on.

    `maestro test` prints the failing command in its console output, but that
    output is dominated by ANSI banners, so the bounded 4,000-character window the
    JSON evidence keeps can lose the only line that says why the flow failed:
    proof12 recorded `Maestro smoke flow failed` with nothing but promotional
    boxes attached, while the real reason — `Assertion is false: "Sign in" is
    visible` with a `System UI isn't responding` dialog on screen — sat in
    `logs/maestro.log` and `screen-hierarchy/` inside the project. Both are read
    here so the verdict names its cause and the operator can check it.

    The flow's results directory was cleared before this run started, so what is in
    it now belongs to this run; if Maestro wrote more than one timestamped directory,
    the newest one is the run in progress, and the log and the screen are reported
    from the same directory so a verdict cannot be paired with another attempt's
    screen. A flow that died before writing a log still gets its screen read."""
    root = mobile / '.maestro' / 'test-results' / flow
    if not root.is_dir():
        return '', ''
    logs = [path for path in root.rglob('logs/maestro.log') if path.is_file()]
    screens = [path for path in root.rglob('screen-hierarchy/*.json') if path.is_file()]
    newest_log = _newest(logs)
    if newest_log is not None:
        step_dir = newest_log.parent.parent
        paired = [path for path in screens if path.parent.parent == step_dir]
        newest_screen = _newest(paired)
    else:
        newest_screen = _newest(screens)

    def read(path):
        if path is None:
            return ''
        try:
            return path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            return ''

    return read(newest_log), read(newest_screen)


def _maestro_reason(log_text):
    """The last verdict Maestro wrote, without its timestamp and logger prefix."""
    for line in reversed(log_text.splitlines()):
        for marker in _MAESTRO_REASON_MARKERS:
            if marker in line:
                return _capture(line[line.find(marker):].strip())
    return ''


_DEVICE_UNRESPONSIVE = "isn't responding"


def _maestro_dialog(screen_text):
    """The dialog the device itself had up on the screen Maestro gave up on.

    proof12's failing hierarchy contained nothing but `System UI isn't responding`,
    `Close app` and `Wait`, while the app under test held its pid and a clean logcat:
    the host was out of memory and its own system UI hung. A bare "flow failed"
    blames the delivered app for that; naming the dialog points at the remedy.
    """
    try:
        tree = json.loads(screen_text)
    except (TypeError, ValueError):
        return ''
    stack = [tree]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        stack.extend(node.get('children') or [])
        text = str((node.get('attributes') or {}).get('text') or '').strip()
        if _DEVICE_UNRESPONSIVE in text:
            return f'the device itself was showing "{text}"'
    return ''


def verify_emulator(
    project_dir,
    apk,
    *,
    toolchain,
    api_url='',
    tier='app_runs',
    run=_run,
    evidence_dir='',
):
    """Boot Android, install and launch the app, check logs, and run Maestro."""
    mobile = Path(project_dir) / 'mobile'
    evidence = Path(evidence_dir) if evidence_dir else None
    report = {
        'ok': False,
        'status': 'failed',
        'tier': tier,
        'booted': False,
        'boot_seconds': None,
        'installed': False,
        'launched': False,
        'app_pid': '',
        'logcat_clean': False,
        'maestro': {},
        'screenshots': [],
        'failures': [],
    }
    if tier not in ('app_runs', 'full_stack'):
        report['failures'].append(f'Unknown verification tier: {tier}')
        return report
    if not api_url:
        report['failures'].append(
            'An explicit API URL is required; use app_runs fixture orchestration '
            'or provide full_stack api_url'
        )
        return report
    if not toolchain or not toolchain.get('ready'):
        report['status'] = 'blocked'
        report['missing'] = list((toolchain or {}).get('missing', []))
        report['failures'].append('Android emulator toolchain is not ready')
        return report
    if not Path(apk).is_file():
        report['failures'].append('Debug APK does not exist')
        return report

    paths, path_problems = _toolchain_paths(
        toolchain, required=('adb', 'emulator', 'maestro')
    )
    avd = paths.get('avd', '')
    if not avd:
        path_problems = [*path_problems, 'avd is missing']
    if path_problems:
        report['status'] = 'blocked'
        report['missing'] = sorted(
            {problem.split(' ')[0] for problem in path_problems}
        )
        report['failures'].append(
            'Android toolchain paths are not usable: ' + '; '.join(path_problems)
        )
        return report
    adb, emulator, maestro = paths['adb'], paths['emulator'], paths['maestro']
    disk_gap = _emulator_disk_gap(paths)
    if disk_gap:
        report['status'] = 'blocked'
        report['missing'] = ['disk']
        report['failures'].append(f'Android emulator cannot run: {disk_gap}')
        return report
    partition_mb, free_mb, avd_volume = _avd_disk_measurement(paths)
    avd_ram = _avd_ram(paths)

    env = _build_env(paths, api_url)
    if paths.get('avd_home'):
        env['ANDROID_AVD_HOME'] = paths['avd_home']
    process = None
    device_logs = {}
    owned_results = []
    boot_log_fd, boot_log_path = tempfile.mkstemp(
        prefix='lumicore-emulator-boot-', suffix='.log'
    )
    email = f'mobile-{secrets.token_hex(8)}@example.test'
    password = secrets.token_urlsafe(24)
    report['test_account'] = email

    def boot_output():
        try:
            return _capture(
                Path(boot_log_path).read_text(encoding='utf-8', errors='replace')
            )
        except OSError:
            return ''

    try:
        with os.fdopen(boot_log_fd, 'w', encoding='utf-8', errors='replace') as boot_log:
            try:
                process = subprocess.Popen(
                    [
                        emulator, '-avd', avd, '-no-window', '-no-audio',
                        '-no-snapshot', '-no-snapshot-save',
                        '-gpu', 'swiftshader_indirect', '-accel', 'auto',
                    ],
                    env=env,
                    stdout=boot_log,
                    stderr=subprocess.STDOUT,
                )
            except OSError as exc:
                report['failures'].append(f'Could not start Android emulator: {exc}')
                return report
        launched_at = time.monotonic()
        deadline = launched_at + _BOOT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            boot = _invoke(
                run, [adb, 'shell', 'getprop', 'sys.boot_completed'],
                mobile, 15, env,
            )
            report['boot_seconds'] = round(time.monotonic() - launched_at)
            if boot['ok'] and boot['stdout_tail'].strip() == '1':
                report['booted'] = True
                break
            if process.poll() is not None:
                reason = _boot_reason(boot_output())
                report['failures'].append(
                    'Android emulator exited before boot completed'
                    + (f': {reason}' if reason else '')
                )
                return report
            time.sleep(3)
        if not report['booted']:
            reason = _boot_reason(boot_output())
            report['failures'].append(
                f'Android emulator did not boot within {_BOOT_TIMEOUT_SECONDS} seconds'
                + (f': {reason}' if reason else '')
            )
            return report

        installed = _invoke(
            run, [adb, 'install', '-r', str(Path(apk).resolve())],
            mobile, 180, env,
        )
        if not installed['ok']:
            report['failures'].append('adb install failed')
            return report
        report['installed'] = True

        package = _read_package(mobile, paths, apk, run, 60, env)
        if not package:
            report['failures'].append('Could not determine Android application package')
            return report
        launch = _invoke(
            run,
            [adb, 'shell', 'am', 'start', '-n', f'{package}/.MainActivity'],
            mobile,
            60,
            env,
        )
        if not launch['ok']:
            report['failures'].append('Android activity launch failed')
            return report
        report['launched'] = True
        time.sleep(5)

        pid = _app_pid(run, adb, package, mobile, env)
        report['app_pid'] = pid
        if not pid:
            report['failures'].append(
                f'{package} is not running after launch; the app process exited'
            )
            return report

        logs = _app_logs(run, adb, package, pid, mobile, env)
        unreadable = _app_logs_readable(logs)
        if unreadable:
            report['failures'].append(
                f'Android could not provide the {unreadable} logcat, so the launch '
                'cannot be certified without it'
            )
            return report
        crash_reason = _app_crash_reason(logs, package)
        report['logcat_clean'] = not crash_reason
        if crash_reason:
            report['failures'].append(
                f'Android app is not running cleanly: {crash_reason}'
            )
        device_logs.update({
            'logcat_window': _evidence_safe(logs['app']['stdout_tail'], email, password),
            'crash_buffer': _evidence_safe(
                logs['crash']['stdout_tail'], email, password
            ),
            'events_buffer': _evidence_safe(
                logs['events']['stdout_tail'], email, password
            ),
        })

        if report['logcat_clean']:
            for flow in ('smoke', 'records'):
                flow_path = mobile / '.maestro' / f'{flow}.yaml'
                if not flow_path.is_file():
                    report['maestro'][flow] = {'ok': False, 'error': 'Maestro flow is missing'}
                    report['failures'].append(f'Maestro {flow} flow is missing')
                    continue
                results_dir = mobile / '.maestro' / 'test-results' / flow
                try:
                    shutil.rmtree(results_dir)
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    report['maestro'][flow] = {
                        'ok': False,
                        'error': (
                            f'Could not clear Maestro {flow} results from an earlier '
                            f'run: {type(exc).__name__}'
                        ),
                    }
                    report['failures'].append(
                        f'Could not clear Maestro {flow} results from an earlier run: '
                        f'{type(exc).__name__}'
                    )
                    continue
                owned_results.append(results_dir)
                result = _invoke(
                    run,
                    [
                        maestro, 'test',
                        '--env', f'EMAIL={email}',
                        '--env', f'PASSWORD={password}',
                        '--test-output-dir',
                        str(results_dir),
                        f'.maestro/{flow}.yaml',
                    ],
                    mobile,
                    900,
                    {**env, 'EMAIL': email, 'PASSWORD': password},
                )
                output = f"{result['stdout_tail']}\n{result['stderr_tail']}"
                failed_count = re.search(
                    r'\b[1-9]\d*\s+(?:failed|failures?)\b', output, re.I
                )
                flow_ok = result['ok'] and failed_count is None
                report['maestro'][flow] = {
                    'ok': flow_ok,
                    'code': result['code'],
                    'stdout_tail': _evidence_safe(result['stdout_tail'], email, password),
                    'stderr_tail': _evidence_safe(result['stderr_tail'], email, password),
                }
                if not flow_ok:
                    log_text, screen_text = _maestro_artifacts(mobile, flow)
                    detail = _evidence_safe(
                        ' while '.join(
                            part for part in (
                                _maestro_reason(log_text), _maestro_dialog(screen_text)
                            ) if part
                        ) or f'exit code {result["code"]} with no Maestro log on disk',
                        email,
                        password,
                    )
                    report['maestro'][flow]['reason'] = detail
                    report['failures'].append(f'Maestro {flow} flow failed: {detail}')
                if evidence:
                    try:
                        _write_json(
                            evidence / 'maestro' / f'{flow}.json',
                            report['maestro'][flow],
                        )
                        if not flow_ok:
                            for suffix, text in (
                                ('.log', log_text), ('-screen.json', screen_text)
                            ):
                                if text:
                                    (evidence / 'maestro' / f'{flow}{suffix}').write_text(
                                        _evidence_safe(text, email, password),
                                        encoding='utf-8',
                                    )
                    except OSError as exc:
                        report['failures'].append(
                            f'Could not write Maestro {flow} evidence: {exc}'
                        )
        if evidence:
            report['screenshots'] = _copy_maestro_screenshots(evidence, owned_results)
    finally:
        leftover = _stop_emulator(run, adb, avd, process, mobile, env)
        if leftover:
            report['failures'].append(f'Android emulator did not stop: {leftover}')
        if evidence:
            try:
                _write_json(evidence / 'emulator.json', {
                    'tier': tier,
                    'booted': report['booted'],
                    'boot_seconds': report['boot_seconds'],
                    'avd_volume': avd_volume,
                    'avd_data_partition_mb': partition_mb,
                    'avd_volume_free_mb': free_mb,
                    'avd_ram_size': avd_ram,
                    'installed': report['installed'],
                    'launched': report['launched'],
                    'app_pid': report['app_pid'],
                    'logcat_clean': report['logcat_clean'],
                    **device_logs,
                })
            except OSError as exc:
                report['failures'].append(f'Could not write emulator evidence: {exc}')
            try:
                (evidence / 'emulator-boot.log').write_text(
                    boot_output(), encoding='utf-8'
                )
            except OSError as exc:
                report['failures'].append(
                    'Could not write emulator boot log evidence: '
                    f'{type(exc).__name__}'
                )
        try:
            os.unlink(boot_log_path)
        except OSError:
            pass

    report['ok'] = (
        report['booted']
        and report['installed']
        and report['launched']
        and report['logcat_clean']
        and len(report['maestro']) == 2
        and all(result.get('ok') for result in report['maestro'].values())
        and not report['failures']
    )
    report['status'] = 'passed' if report['ok'] else 'failed'
    return report


def _fixture_health(base_url):
    parsed = urlsplit(base_url)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        connection.request('GET', '/api/v1/health')
        response = connection.getresponse()
        payload = json.loads(response.read() or b'{}')
        return response.status == 200 and payload.get('success') is True, payload
    finally:
        connection.close()


def verify_mobile(
    project_dir,
    *,
    toolchain,
    tier='app_runs',
    api_url='',
    run=_run,
    timeout=3600,
    evidence_dir='',
):
    """Run export, build, and emulator checks with a per-run fixture for app_runs."""
    report = {
        'ok': False,
        'status': 'failed',
        'tier': tier,
        'export': {},
        'build': {},
        'emulator': {},
        'errors': [],
    }
    if tier not in ('app_runs', 'full_stack'):
        report['errors'].append(f'Unknown verification tier: {tier}')
        return report
    if tier == 'full_stack' and not api_url:
        report['errors'].append('full_stack verification requires an explicit api_url')
        return report
    if not toolchain or not toolchain.get('ready'):
        report['status'] = 'blocked'
        report['errors'].append('Android emulator toolchain is not ready')
        return report
    fixture = None
    fixture_origin = ''
    if tier == 'app_runs':
        fixture, base_url = start_fixture_api(port=0)
        healthy, health = _fixture_health(base_url)
        if not healthy:
            fixture.shutdown()
            fixture.server_close()
            report['errors'].append('Ephemeral fixture API health check failed')
            return report
        parsed = urlsplit(base_url)
        fixture_origin = f'http://10.0.2.2:{parsed.port}/api/v1'
        if evidence_dir:
            try:
                _write_json(Path(evidence_dir) / 'health.json', health)
            except OSError as exc:
                report['errors'].append(f'Could not write fixture health evidence: {exc}')
                fixture.shutdown()
                fixture.server_close()
                return report
    target_api_url = fixture_origin if tier == 'app_runs' else api_url.rstrip('/')
    try:
        report['export'] = export_mobile(project_dir, run=run, timeout=timeout)
        if not report['export']['ok']:
            report['errors'].extend(report['export']['errors'])
            return report

        report['build'] = build_apk(
            project_dir,
            toolchain,
            api_url=target_api_url,
            run=run,
            timeout=timeout,
            evidence_dir=evidence_dir,
        )
        if not report['build']['ok']:
            report['errors'].extend(report['build']['errors'])
            return report

        report['emulator'] = verify_emulator(
            project_dir,
            report['build']['apk'],
            toolchain=toolchain,
            api_url=target_api_url,
            tier=tier,
            run=run,
            evidence_dir=evidence_dir,
        )
        if not report['emulator']['ok']:
            report['errors'].extend(report['emulator']['failures'])
            return report
        report.update(ok=True, status='passed')
        return report
    finally:
        if fixture is not None:
            fixture.shutdown()
            fixture.server_close()
