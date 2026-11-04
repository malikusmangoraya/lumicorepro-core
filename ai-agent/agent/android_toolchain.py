"""Secure Android SDK/JDK bootstrap and environment diagnostics."""

import hashlib
import os
import re
import shutil
import stat
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath


DEFAULT_ANDROID_HOME = Path('D:/android-sdk')
DEFAULT_JAVA_HOME = Path('D:/tools/jdk17')
DEFAULT_AVD_HOME = Path('D:/android-avd')
DEFAULT_MAESTRO_HOME = Path('D:/tools/maestro')
DEFAULT_GRADLE_HOME = Path('D:/gradle-cache')
AVD_NAME = 'lumicore_api35'
SYSTEM_IMAGE_PACKAGE = 'system-images;android-35;google_apis;x86_64'
CMAKE_PACKAGE = 'cmake;3.31.6'
ANDROID_PACKAGES = (
    'platform-tools',
    'build-tools;35.0.0',
    'platforms;android-35',
    'emulator',
    SYSTEM_IMAGE_PACKAGE,
    CMAKE_PACKAGE,
)

# Ninja became long-path aware in 1.11; the copy bundled with the CMake package
# Gradle falls back to (3.22.1) is 1.10.2 and cannot even stat React Native's
# codegen object files, whose paths embed the absolute source path twice.
NINJA_LONG_PATH_MINIMUM = (1, 11)
IS_WINDOWS = os.name == 'nt'
_PROBE_TIMEOUT = 30
_PROBE_ERRORS = (OSError, UnicodeDecodeError, subprocess.SubprocessError)

JDK_URL = (
    'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/'
    'jdk/hotspot/normal/eclipse'
)
COMMAND_LINE_TOOLS_URL = (
    'https://dl.google.com/android/repository/'
    'commandlinetools-win-11076708_latest.zip'
)
MAESTRO_URL = (
    'https://github.com/mobile-dev-inc/maestro/releases/download/'
    '1.39.0/maestro.zip'
)
OFFICIAL_DOWNLOAD_HOSTS = frozenset({
    'api.adoptium.net',
    'dl.google.com',
    'github.com',
    'objects.githubusercontent.com',
    'release-assets.githubusercontent.com',
})
MINIMUM_FREE_GB = 14
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024


class _OfficialRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        _validate_official_url(new_url)
        return super().redirect_request(
            request, response, code, message, headers, new_url
        )


def _validate_official_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != 'https'
        or parsed.hostname not in OFFICIAL_DOWNLOAD_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
    ):
        raise ValueError('Downloads must use an official HTTPS host')
    return parsed


def _download(url, destination, *, sha256=None):
    """Download only from pinned official hosts, optionally checking SHA-256."""
    _validate_official_url(url)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination.with_name(destination.name + '.part')
    digest = hashlib.sha256()
    total = 0
    opener = urllib.request.build_opener(_OfficialRedirectHandler())

    try:
        with opener.open(url, timeout=90) as response, partial_path.open('wb') as out:
            _validate_official_url(response.geturl())
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError('Download exceeds the configured size limit')
                digest.update(chunk)
                out.write(chunk)
        if sha256 and digest.hexdigest().lower() != sha256.lower():
            raise ValueError('Downloaded file failed SHA-256 verification')
        partial_path.replace(destination)
        return destination
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise


def _extract_zip(archive_path, destination):
    """Validate ZIP integrity and every member path before extracting any data."""
    destination = Path(destination)
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if archive.testzip() is not None:
            raise ValueError('Downloaded ZIP failed CRC integrity validation')

        validated = []
        for member in members:
            name = member.filename.replace('\\', '/')
            posix_name = PurePosixPath(name)
            windows_name = PureWindowsPath(member.filename)
            mode = member.external_attr >> 16
            if (
                not name
                or posix_name.is_absolute()
                or windows_name.is_absolute()
                or windows_name.drive
                or any(part in ('', '.', '..') for part in posix_name.parts)
                or stat.S_ISLNK(mode)
            ):
                raise ValueError(f'unsafe ZIP member: {member.filename}')
            target = (destination / Path(*posix_name.parts)).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError(f'unsafe ZIP member: {member.filename}')
            validated.append((member, target))

        for member, target in validated:
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open('wb') as out:
                shutil.copyfileobj(source, out)
    return destination


def _run(args, *, input_text=None, env=None, cwd=None, timeout=None):
    """Run a local tool without a shell except when invoking Windows batch files.

    Installs pass no timeout because sdkmanager downloads for minutes; every
    read-only probe passes one, because the factory blocks on the answer.
    """
    return subprocess.run(
        args,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=cwd,
        timeout=timeout,
    )


def _binary(directory, name, extensions=('.exe', '')):
    for extension in extensions:
        candidate = Path(directory) / f'{name}{extension}'
        if candidate.is_file():
            return candidate
    return None


def _windows_command(path, *args):
    path = str(path)
    if os.name == 'nt' and path.lower().endswith(('.bat', '.cmd')):
        return ['cmd.exe', '/c', path, *map(str, args)]
    return [path, *map(str, args)]


def _java_is_17(java_path):
    if not java_path:
        return False
    try:
        result = _run([str(java_path), '-version'], timeout=_PROBE_TIMEOUT)
    except _PROBE_ERRORS:
        return False
    version = f'{result.stdout}\n{result.stderr}'
    match = re.search(r'version\s+"?(\d+)(?:[._+"]|$)', version, re.IGNORECASE)
    return result.returncode == 0 and bool(match) and int(match.group(1)) == 17


def _find_installed_java_home(root):
    root = Path(root)
    direct = _binary(root / 'bin', 'java')
    if _java_is_17(direct):
        return root
    for candidate in sorted(root.glob('*/bin/java.exe')):
        if _java_is_17(candidate):
            return candidate.parent.parent
    return None


def _disk_free_gb(path):
    candidate = Path(path)
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    try:
        return shutil.disk_usage(candidate).free / (1024 ** 3)
    except OSError:
        return 0.0


def _avd_is_present(emulator, avd_home, env):
    if not emulator:
        return False
    run_env = dict(env)
    run_env['ANDROID_AVD_HOME'] = str(avd_home)
    try:
        result = _run(
            _windows_command(emulator, '-list-avds'),
            env=run_env,
            timeout=_PROBE_TIMEOUT,
        )
    except _PROBE_ERRORS:
        return False
    return result.returncode == 0 and AVD_NAME in result.stdout.splitlines()


def _ninja_version(binary):
    if not binary:
        return None
    try:
        result = _run([str(binary), '--version'], timeout=_PROBE_TIMEOUT)
    except _PROBE_ERRORS:
        return None
    if result.returncode != 0:
        return None
    match = re.match(r'\s*(\d+)\.(\d+)', result.stdout or '')
    return (int(match.group(1)), int(match.group(2))) if match else None


def _resolve_cmake(sdk_home, *, enforce_long_paths):
    """Return (usable CMake package, gap text) for the SDK's `cmake` directory.

    The package is readiness evidence only: Gradle chooses which CMake to build
    with, so reporting a newer one never redirects a native build. What the gate
    buys is a blocked delivery that names the fix, instead of the same failure
    twelve minutes into `assembleDebug`.
    """
    minimum = '.'.join(str(part) for part in NINJA_LONG_PATH_MINIMUM)
    root = Path(sdk_home) / 'cmake'
    packages = [package for package in sorted(root.iterdir())
                if package.is_dir()] if root.is_dir() else []
    if not packages:
        return None, (
            f'no CMake package is installed; run sdkmanager "{CMAKE_PACKAGE}"'
        )
    usable = []
    for package in packages:
        binary = _binary(package / 'bin', 'ninja')
        if not binary:
            continue
        version = _ninja_version(binary)
        if version is None:
            return None, (
                f'ninja in cmake;{package.name} did not report a version; reinstall it '
                f'with sdkmanager --uninstall "cmake;{package.name}" and '
                f'sdkmanager "cmake;{package.name}"'
            )
        if enforce_long_paths and version < NINJA_LONG_PATH_MINIMUM:
            return None, (
                f'cmake;{package.name} ships ninja {version[0]}.{version[1]}, below the '
                f'{minimum} minimum that can stat Windows long paths, and Gradle builds '
                f'with it anyway; run sdkmanager --uninstall "cmake;{package.name}" and '
                f'keep {CMAKE_PACKAGE}'
            )
        usable.append((version, package))
    if not usable:
        return None, (
            f'no CMake package under {root} has a ninja binary; install '
            f'{CMAKE_PACKAGE} with sdkmanager'
        )
    return max(usable)[1], ''


def check_environment(*, root=None, env=None):
    """Report the installed Android toolchain without downloading or modifying it."""
    env = os.environ if env is None else env
    sdk_home = Path(
        env.get('ANDROID_HOME')
        or env.get('ANDROID_SDK_ROOT')
        or root
        or DEFAULT_ANDROID_HOME
    )
    configured_java_home = env.get('JAVA_HOME')
    if configured_java_home:
        java_home = Path(configured_java_home)
        java = _binary(java_home / 'bin', 'java')
        java17 = _java_is_17(java)
    else:
        java_root = Path(DEFAULT_JAVA_HOME)
        java_home = _find_installed_java_home(java_root) or java_root
        java = _binary(java_home / 'bin', 'java')
        java17 = bool(java)
    avd_home = Path(env.get('ANDROID_AVD_HOME') or DEFAULT_AVD_HOME)
    maestro_home = Path(env.get('MAESTRO_HOME') or DEFAULT_MAESTRO_HOME)
    gradle_home = Path(env.get('GRADLE_USER_HOME') or DEFAULT_GRADLE_HOME)
    sdkmanager = _binary(
        sdk_home / 'cmdline-tools' / 'latest' / 'bin',
        'sdkmanager',
        ('.bat', '.cmd', '.exe', ''),
    )
    adb = _binary(sdk_home / 'platform-tools', 'adb')
    emulator = _binary(sdk_home / 'emulator', 'emulator')
    maestro = next((
        candidate for candidate in (
            _binary(maestro_home, 'maestro', ('.cmd', '.bat', '.exe', '')),
            _binary(maestro_home / 'bin', 'maestro', ('.cmd', '.bat', '.exe', '')),
        ) if candidate
    ), None)
    if not maestro:
        maestro = _find_maestro_binary(maestro_home)

    avd = _avd_is_present(emulator, avd_home, env)
    cmake, cmake_gap = _resolve_cmake(sdk_home, enforce_long_paths=IS_WINDOWS)
    checks = {
        'java17': java17,
        'sdk': sdkmanager is not None,
        'adb': adb is not None,
        'emulator': emulator is not None,
        'avd': avd,
        'maestro': maestro is not None,
        'gradle_home': gradle_home.is_dir(),
        'cmake': cmake is not None,
    }
    missing = [name for name, available in checks.items() if not available]
    return {
        'ready': not missing,
        **checks,
        'java_home': str(java_home) if java17 else '',
        'sdk_path': str(sdk_home) if checks['sdk'] else '',
        'adb_path': str(adb) if adb else '',
        'emulator_path': str(emulator) if emulator else '',
        'avd_home': str(avd_home) if avd else '',
        'maestro_path': str(maestro) if maestro else '',
        'gradle_home_path': str(gradle_home) if gradle_home.is_dir() else '',
        'cmake_path': str(cmake) if cmake else '',
        'cmake_gap': '' if cmake else cmake_gap,
        'disk_free_gb': round(_disk_free_gb(sdk_home), 2),
        'missing': missing,
    }


def toolchain(env=None):
    """Return toolchain readiness and the resolved paths used by mobile verification."""
    report = check_environment(env=env)
    return {
        'ready': report['ready'],
        'java_home': report['java_home'],
        'sdk': report['sdk_path'],
        'adb': report['adb_path'],
        'emulator': report['emulator_path'],
        'avd': AVD_NAME if report['avd'] else '',
        'avd_home': report['avd_home'],
        'maestro': report['maestro_path'],
        'gradle_home': report['gradle_home_path'],
        'cmake': report['cmake_path'],
        'cmake_gap': report['cmake_gap'],
    }


def _emit(progress, stage, status, **details):
    if progress:
        progress({'stage': stage, 'status': status, **details})


def _require_success(result, stage):
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or '').strip()
        raise RuntimeError(f'{stage} failed{": " + detail if detail else ""}')


def _install_archive(url, archive_name, destination):
    archive_path = Path(destination).parent / archive_name
    try:
        _download(url, archive_path)
        _extract_zip(archive_path, destination)
    finally:
        archive_path.unlink(missing_ok=True)


def _find_java_home(extraction_root):
    executable = next(Path(extraction_root).rglob('java.exe'), None)
    if executable is None:
        raise RuntimeError('JDK archive did not contain bin/java.exe')
    return executable.parent.parent


def _set_avd_memory(config_path):
    config_path = Path(config_path)
    lines = config_path.read_text(encoding='utf-8').splitlines()
    lines = [line for line in lines if not line.startswith('hw.ramSize=')]
    lines.append('hw.ramSize=2048')
    config_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _create_avd_if_missing(avdmanager, sdk_home, avd_home, env):
    emulator = _binary(Path(sdk_home) / 'emulator', 'emulator')
    if not emulator:
        raise RuntimeError('Android emulator package was not installed')
    if _avd_is_present(emulator, avd_home, env):
        return False
    result = _run(
        _windows_command(
            avdmanager,
            f'--sdk_root={sdk_home}',
            'create', 'avd',
            '--name', AVD_NAME,
            '--package', SYSTEM_IMAGE_PACKAGE,
            '--device', 'pixel_2',
        ),
        input_text='no\n',
        env=env,
    )
    _require_success(result, 'Android virtual device creation')
    return True


def _find_maestro_binary(home):
    candidates = [path for path in Path(home).rglob('*') if path.is_file()]
    names = (
        ('maestro.bat', 'maestro.cmd', 'maestro.exe', 'maestro')
        if os.name == 'nt'
        else ('maestro', 'maestro.exe', 'maestro.cmd', 'maestro.bat')
    )
    return next((
        path for name in names
        for path in candidates
        if path.name.lower() == name
    ), None)


def _write_environment_file(paths):
    env_file = Path(__file__).resolve().parents[1] / '.env.android'
    env_file.parent.mkdir(parents=True, exist_ok=True)
    contents = ''.join(f'{key}={value}\n' for key, value in paths.items())
    env_file.write_text(contents, encoding='utf-8')
    return env_file


def install_toolchain(root='D:/android-sdk', *, accept_licenses=False, progress=None):
    """Install pinned Android packages after explicit license and disk-space gates."""
    if not accept_licenses:
        return {
            'ok': False,
            'error': 'Android SDK licenses must be accepted; rerun with --accept-licenses.',
        }

    sdk_home = Path(root)
    free_gb = _disk_free_gb(sdk_home)
    if free_gb < MINIMUM_FREE_GB:
        return {
            'ok': False,
            'error': f'Android toolchain installation requires 14 GB free; found {free_gb:.2f} GB.',
            'disk_free_gb': round(free_gb, 2),
        }

    sdk_home.mkdir(parents=True, exist_ok=True)
    sdk_tools_stage = sdk_home / '.cmdline-tools-stage'
    jdk_stage = DEFAULT_JAVA_HOME.parent / '.jdk17-stage'
    maestro_stage = DEFAULT_MAESTRO_HOME.parent / '.maestro-stage'
    try:
        java_home = _find_installed_java_home(DEFAULT_JAVA_HOME)
        if not java_home and DEFAULT_JAVA_HOME.exists():
            raise RuntimeError(
                f'JDK destination already exists but is incomplete: {DEFAULT_JAVA_HOME}'
            )
        if not java_home:
            _emit(progress, 'download', 'running', package='jdk17')
            _install_archive(JDK_URL, 'jdk17.zip', jdk_stage)
            extracted_java_home = _find_java_home(jdk_stage)
            DEFAULT_JAVA_HOME.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(extracted_java_home), str(DEFAULT_JAVA_HOME))
            java_home = DEFAULT_JAVA_HOME
        _emit(progress, 'download', 'running', package='android-command-line-tools')
        sdk_tools_home = sdk_home / 'cmdline-tools' / 'latest'
        sdkmanager = _binary(
            sdk_tools_home / 'bin', 'sdkmanager', ('.bat', '.cmd', '.exe', '')
        )
        avdmanager = _binary(
            sdk_tools_home / 'bin', 'avdmanager', ('.bat', '.cmd', '.exe', '')
        )
        if not sdkmanager or not avdmanager:
            if sdk_tools_home.exists():
                raise RuntimeError(
                    f'Android command-line tools destination is incomplete: {sdk_tools_home}'
                )
            _install_archive(
                COMMAND_LINE_TOOLS_URL, 'commandlinetools.zip', sdk_tools_stage
            )
            unpacked_tools = sdk_tools_stage / 'cmdline-tools'
            if unpacked_tools.is_dir():
                sdk_tools_home.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(unpacked_tools), str(sdk_tools_home))
            sdkmanager = _binary(
                sdk_tools_home / 'bin', 'sdkmanager', ('.bat', '.cmd', '.exe', '')
            )
            avdmanager = _binary(
                sdk_tools_home / 'bin', 'avdmanager', ('.bat', '.cmd', '.exe', '')
            )
        if not sdkmanager or not avdmanager:
            raise RuntimeError('Android command-line tools archive is missing sdkmanager')

        run_env = dict(os.environ)
        run_env.update({
            'JAVA_HOME': str(java_home),
            'ANDROID_HOME': str(sdk_home),
            'ANDROID_SDK_ROOT': str(sdk_home),
            'ANDROID_AVD_HOME': str(DEFAULT_AVD_HOME),
            'GRADLE_USER_HOME': str(DEFAULT_GRADLE_HOME),
            'PATH': str(java_home / 'bin') + os.pathsep + run_env.get('PATH', ''),
        })
        _emit(progress, 'licenses', 'running')
        licenses = _run(
            _windows_command(sdkmanager, f'--sdk_root={sdk_home}', '--licenses'),
            input_text='y\n' * 50,
            env=run_env,
        )
        _require_success(licenses, 'Android SDK license acceptance')
        _emit(progress, 'sdk-packages', 'running')
        packages = _run(
            _windows_command(sdkmanager, f'--sdk_root={sdk_home}', *ANDROID_PACKAGES),
            env=run_env,
        )
        _require_success(packages, 'Android SDK package installation')

        DEFAULT_AVD_HOME.mkdir(parents=True, exist_ok=True)
        DEFAULT_GRADLE_HOME.mkdir(parents=True, exist_ok=True)
        _create_avd_if_missing(avdmanager, sdk_home, DEFAULT_AVD_HOME, run_env)
        _set_avd_memory(DEFAULT_AVD_HOME / f'{AVD_NAME}.avd' / 'config.ini')

        _emit(progress, 'download', 'running', package='maestro')
        maestro_binary = _find_maestro_binary(DEFAULT_MAESTRO_HOME)
        if not maestro_binary:
            if DEFAULT_MAESTRO_HOME.exists():
                raise RuntimeError(
                    f'Maestro destination is incomplete: {DEFAULT_MAESTRO_HOME}'
                )
            _install_archive(MAESTRO_URL, 'maestro.zip', maestro_stage)
            maestro_binary = _find_maestro_binary(maestro_stage)
        if not maestro_binary:
            raise RuntimeError('Maestro archive did not contain a CLI launcher')
        DEFAULT_MAESTRO_HOME.parent.mkdir(parents=True, exist_ok=True)
        if maestro_binary.is_relative_to(maestro_stage):
            shutil.move(str(maestro_stage), str(DEFAULT_MAESTRO_HOME))
        emulator = _binary(sdk_home / 'emulator', 'emulator')
        if not emulator:
            raise RuntimeError('Android emulator package was not installed')
        acceleration = _run(_windows_command(emulator, '-accel-check'), env=run_env)
        _require_success(acceleration, 'Android emulator acceleration check')

        paths = {
            'JAVA_HOME': str(java_home),
            'ANDROID_HOME': str(sdk_home),
            'ANDROID_SDK_ROOT': str(sdk_home),
            'ANDROID_AVD_HOME': str(DEFAULT_AVD_HOME),
            'MAESTRO_HOME': str(DEFAULT_MAESTRO_HOME),
            'GRADLE_USER_HOME': str(DEFAULT_GRADLE_HOME),
        }
        env_file = _write_environment_file(paths)
        report = check_environment(root=sdk_home, env=paths)
        return {
            'ok': report['ready'],
            'environment': report,
            'env_file': str(env_file),
        }
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, urllib.error.URLError) as exc:
        return {'ok': False, 'error': str(exc)}
    finally:
        for stage in (sdk_tools_stage, jdk_stage, maestro_stage):
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
