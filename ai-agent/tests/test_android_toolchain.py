import hashlib
import io
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

AGENT_ROOT = Path(__file__).resolve().parent.parent
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent import android_toolchain


def test_check_reports_every_missing_piece(monkeypatch, tmp_path):
    monkeypatch.delenv('ANDROID_HOME', raising=False)
    monkeypatch.delenv('JAVA_HOME', raising=False)
    monkeypatch.setattr(android_toolchain, 'DEFAULT_JAVA_HOME', tmp_path / 'jdk')

    report = android_toolchain.check_environment(root=str(tmp_path / 'sdk'), env={})

    assert report['ready'] is False
    assert report['missing']
    assert 'java17' in report['missing']
    assert 'sdk' in report['missing']
    assert 'emulator' in report['missing']


def _fake_sdk(tmp_path, *, cmake_packages=('3.22.1', '3.31.6')):
    """Create a complete-looking toolchain tree, including SDK CMake packages.

    A real SDK keeps every CMake version that was ever installed, and Gradle
    builds with the oldest of them, so a one-package fixture would miss the
    exact state the gate exists to catch.
    """
    sdk = tmp_path / 'sdk'
    paths = [
        sdk / 'cmdline-tools' / 'latest' / 'bin' / 'sdkmanager.bat',
        sdk / 'platform-tools' / 'adb.exe',
        sdk / 'emulator' / 'emulator.exe',
        tmp_path / 'jdk' / 'bin' / 'java.exe',
        tmp_path / 'maestro' / 'bin' / 'maestro.cmd',
    ]
    paths += [
        sdk / 'cmake' / package / 'bin' / 'ninja.exe' for package in cmake_packages
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('', encoding='utf-8')
    (tmp_path / 'gradle').mkdir()
    return {
        'ANDROID_HOME': str(sdk),
        'JAVA_HOME': str(tmp_path / 'jdk'),
        'MAESTRO_HOME': str(tmp_path / 'maestro'),
        'GRADLE_USER_HOME': str(tmp_path / 'gradle'),
        'ANDROID_AVD_HOME': str(tmp_path / 'avds'),
    }


def _stub_readiness(monkeypatch, *, versions=None, windows=True, run=None):
    """Answer `ninja --version` the way the real binary does.

    Stubbing `_ninja_version` would skip over the version parse, the long-path
    comparison and the newest-wins choice that this gate actually turns on.
    """
    monkeypatch.setattr(android_toolchain, '_java_is_17', lambda _path: True)
    monkeypatch.setattr(android_toolchain, '_avd_is_present', lambda *args: True)
    monkeypatch.setattr(android_toolchain, 'IS_WINDOWS', windows)
    if run is not None:
        monkeypatch.setattr(android_toolchain, '_run', run)
        return
    reported = versions or {}

    def fake_run(args, **_kwargs):
        package = Path(args[0]).parents[1].name
        return SimpleNamespace(
            returncode=0, stdout=reported.get(package, '1.12.1\n'), stderr=''
        )

    monkeypatch.setattr(android_toolchain, '_run', fake_run)


def test_toolchain_returns_paths_and_the_avd_identifier(tmp_path, monkeypatch):
    env = _fake_sdk(tmp_path)
    _stub_readiness(monkeypatch)
    sdk = Path(env['ANDROID_HOME'])

    report = android_toolchain.toolchain(env=env)

    assert report == {
        'ready': True,
        'java_home': env['JAVA_HOME'],
        'sdk': str(sdk),
        'adb': str(sdk / 'platform-tools' / 'adb.exe'),
        'emulator': str(sdk / 'emulator' / 'emulator.exe'),
        'avd': 'lumicore_api35',
        'avd_home': env['ANDROID_AVD_HOME'],
        'maestro': str(Path(env['MAESTRO_HOME']) / 'bin' / 'maestro.cmd'),
        'gradle_home': env['GRADLE_USER_HOME'],
        'cmake': str(sdk / 'cmake' / '3.31.6'),
        'cmake_gap': '',
    }


def test_cmake_ninja_that_cannot_stat_windows_long_paths_is_a_gap(tmp_path, monkeypatch):
    """Reanimated's codegen object paths pass 300 characters on Windows because
    CMake embeds the absolute source path twice. The ninja bundled with the
    CMake package Gradle defaults to (3.22.1) is 1.10.2, which refuses to stat
    them, and the build only says so 12 minutes in."""
    env = _fake_sdk(tmp_path, cmake_packages=('3.22.1',))
    _stub_readiness(monkeypatch, versions={'3.22.1': '1.10.2\n'})

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' in report['missing']
    assert report['ready'] is False
    assert report['cmake_path'] == ''
    assert '1.11' in report['cmake_gap']


def test_the_same_ninja_is_accepted_where_paths_are_not_limited(tmp_path, monkeypatch):
    env = _fake_sdk(tmp_path, cmake_packages=('3.22.1',))
    _stub_readiness(monkeypatch, versions={'3.22.1': '1.10.2\n'}, windows=False)

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' not in report['missing']
    assert report['cmake_path']
    assert report['cmake_gap'] == ''


def test_the_newest_usable_cmake_package_is_the_one_reported(tmp_path, monkeypatch):
    env = _fake_sdk(tmp_path)
    _stub_readiness(monkeypatch)

    report = android_toolchain.check_environment(env=env)

    assert report['cmake_path'] == str(
        Path(env['ANDROID_HOME']) / 'cmake' / '3.31.6')
    assert report['cmake_gap'] == ''


def test_a_stale_package_alongside_a_good_one_names_what_to_uninstall(
    tmp_path, monkeypatch
):
    """Installing cmake;3.31.6 does not stop the failing build on its own, so a
    gap that only says "no usable CMake" leaves the operator with no remedy."""
    env = _fake_sdk(tmp_path)
    _stub_readiness(monkeypatch, versions={'3.22.1': '1.10.2\n', '3.31.6': '1.12.1\n'})

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' in report['missing']
    assert report['cmake_path'] == ''
    assert 'cmake;3.22.1' in report['cmake_gap']
    assert 'ninja 1.10' in report['cmake_gap']
    assert '--uninstall "cmake;3.22.1"' in report['cmake_gap']
    assert 'cmake;3.31.6' in report['cmake_gap']


def test_a_sdk_without_any_cmake_package_says_what_to_install(tmp_path, monkeypatch):
    env = _fake_sdk(tmp_path, cmake_packages=())
    _stub_readiness(monkeypatch)

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' in report['missing']
    assert report['ready'] is False
    assert 'cmake;3.31.6' in report['cmake_gap']


def test_a_cmake_directory_without_a_ninja_is_a_gap(tmp_path, monkeypatch):
    """A package can be present but empty after an interrupted install; naming
    the directory is the only way the operator can find it."""
    env = _fake_sdk(tmp_path)
    shutil.rmtree(Path(env['ANDROID_HOME']) / 'cmake' / '3.31.6' / 'bin')
    _stub_readiness(monkeypatch, versions={'3.22.1': '1.10.2\n'})

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' in report['missing']
    assert report['cmake_path'] == ''


def test_a_ninja_that_cannot_report_a_version_names_its_package(tmp_path, monkeypatch):
    env = _fake_sdk(tmp_path)
    _stub_readiness(monkeypatch, versions={'3.22.1': 'ninja: unknown\n'})

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' in report['missing']
    assert 'cmake;3.22.1' in report['cmake_gap']
    assert 'reinstall' in report['cmake_gap']


@pytest.mark.parametrize('failure', [
    subprocess.TimeoutExpired(['ninja', '--version'], 30),
    UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte'),
])
def test_a_ninja_probe_that_cannot_complete_is_a_gap_not_a_crash(
    tmp_path, monkeypatch, failure
):
    env = _fake_sdk(tmp_path)

    def run(_args, **_kwargs):
        raise failure

    _stub_readiness(monkeypatch, run=run)

    report = android_toolchain.check_environment(env=env)

    assert 'cmake' in report['missing']
    assert report['ready'] is False


def test_read_only_probes_all_carry_a_timeout(monkeypatch, tmp_path):
    """`check_environment` runs before every mobile delivery, so one wedged
    binary would hang the factory with nothing on screen to explain it."""
    seen = []

    def run(args, **kwargs):
        seen.append(kwargs.get('timeout'))
        return SimpleNamespace(returncode=0, stdout='openjdk "17.0.2"\n', stderr='')

    monkeypatch.setattr(subprocess, 'run', run)
    binary = tmp_path / 'tool.exe'
    binary.write_text('', encoding='utf-8')

    android_toolchain._java_is_17(binary)
    android_toolchain._avd_is_present(binary, tmp_path, {})
    android_toolchain._ninja_version(binary)

    assert seen == [android_toolchain._PROBE_TIMEOUT] * 3


def test_installs_are_not_bounded_by_the_probe_timeout(monkeypatch):
    """sdkmanager downloads for minutes; a timeout sized for a version probe
    would cancel a working install."""
    seen = []

    def run(args, **kwargs):
        seen.append(kwargs.get('timeout'))
        return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(subprocess, 'run', run)
    android_toolchain._run(['sdkmanager', 'platform-tools'])

    assert seen == [None]


def test_check_discovers_jdk_nested_under_default_java_root(tmp_path, monkeypatch):
    java_root = tmp_path / 'jdk17'
    java_home = java_root / 'jdk-17.0.20'
    java = java_home / 'bin' / 'java.exe'
    java.parent.mkdir(parents=True)
    java.write_text('', encoding='utf-8')
    monkeypatch.setattr(android_toolchain, 'DEFAULT_JAVA_HOME', java_root)
    monkeypatch.setattr(android_toolchain, '_java_is_17', lambda path: path == java)

    report = android_toolchain.check_environment(
        root=str(tmp_path / 'sdk'),
        env={'ANDROID_AVD_HOME': str(tmp_path / 'avds')},
    )

    assert report['java17'] is True
    assert report['java_home'] == str(java_home)


def test_check_discovers_maestro_under_default_install_root(tmp_path, monkeypatch):
    maestro_root = tmp_path / 'maestro'
    maestro = maestro_root / 'maestro' / 'bin' / 'maestro.bat'
    maestro.parent.mkdir(parents=True)
    maestro.write_text('', encoding='utf-8')
    unix_maestro = maestro.with_name('maestro')
    unix_maestro.write_text('', encoding='utf-8')
    monkeypatch.setattr(android_toolchain, 'DEFAULT_MAESTRO_HOME', maestro_root)

    report = android_toolchain.check_environment(
        root=str(tmp_path / 'sdk'),
        env={'ANDROID_AVD_HOME': str(tmp_path / 'avds')},
    )

    assert report['maestro'] is True
    expected = maestro if android_toolchain.os.name == 'nt' else unix_maestro
    assert report['maestro_path'] == str(expected)


def test_install_refuses_without_license_flag(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        android_toolchain, '_download', lambda *args, **kwargs: calls.append('download')
    )

    result = android_toolchain.install_toolchain(str(tmp_path), accept_licenses=False)

    assert result['ok'] is False
    assert 'accept' in result['error'].lower()
    assert calls == []


def test_install_aborts_below_disk_threshold_before_downloading(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(android_toolchain, '_disk_free_gb', lambda _path: 13.99)
    monkeypatch.setattr(
        android_toolchain, '_download', lambda *args, **kwargs: calls.append('download')
    )

    result = android_toolchain.install_toolchain(
        str(tmp_path / 'sdk'), accept_licenses=True
    )

    assert result['ok'] is False
    assert '14 GB' in result['error']
    assert calls == []
    assert not (tmp_path / 'sdk').exists()


def test_install_reuses_a_valid_versioned_jdk_under_default_root(tmp_path, monkeypatch):
    sdk = tmp_path / 'sdk'
    java_root = tmp_path / 'jdk17'
    java_home = java_root / 'jdk-17.0.20'
    java = java_home / 'bin' / 'java.exe'
    avd_home = tmp_path / 'avds'
    maestro_home = tmp_path / 'maestro'
    gradle_home = tmp_path / 'gradle'
    for path in (
        java,
        sdk / 'cmdline-tools' / 'latest' / 'bin' / 'sdkmanager.bat',
        sdk / 'cmdline-tools' / 'latest' / 'bin' / 'avdmanager.bat',
        sdk / 'platform-tools' / 'adb.exe',
        sdk / 'emulator' / 'emulator.exe',
        avd_home / f'{android_toolchain.AVD_NAME}.avd' / 'config.ini',
        maestro_home / 'maestro' / 'bin' / 'maestro.bat',
        sdk / 'cmake' / '3.31.6' / 'bin' / 'ninja.exe',
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        content = 'hw.ramSize=2048\n' if path.name == 'config.ini' else ''
        path.write_text(content, encoding='utf-8')
    gradle_home.mkdir()
    monkeypatch.setattr(android_toolchain, 'DEFAULT_JAVA_HOME', java_root)
    monkeypatch.setattr(android_toolchain, 'DEFAULT_AVD_HOME', avd_home)
    monkeypatch.setattr(android_toolchain, 'DEFAULT_MAESTRO_HOME', maestro_home)
    monkeypatch.setattr(android_toolchain, 'DEFAULT_GRADLE_HOME', gradle_home)
    monkeypatch.setattr(android_toolchain, '_disk_free_gb', lambda _path: 20)
    monkeypatch.setattr(
        android_toolchain, '_java_is_17',
        lambda path: bool(path) and Path(path) == java,
    )
    monkeypatch.setattr(android_toolchain, '_create_avd_if_missing', lambda *args: False)
    monkeypatch.setattr(
        android_toolchain, '_write_environment_file',
        lambda _paths: tmp_path / '.env.android',
    )
    downloads = []
    monkeypatch.setattr(
        android_toolchain, '_install_archive',
        lambda *args, **kwargs: downloads.append(args),
    )

    def run(args, **kwargs):
        if '--version' in args:
            return SimpleNamespace(returncode=0, stdout='1.12.1\n', stderr='')
        output = android_toolchain.AVD_NAME if '-list-avds' in args else ''
        return SimpleNamespace(returncode=0, stdout=output, stderr='')

    monkeypatch.setattr(android_toolchain, '_run', run)

    result = android_toolchain.install_toolchain(str(sdk), accept_licenses=True)

    assert result['ok'] is True, result
    assert result['environment']['java_home'] == str(java_home)
    assert downloads == []


def test_avd_memory_configuration_sets_two_gigabytes_and_preserves_settings(tmp_path):
    avd_config = tmp_path / android_toolchain.AVD_NAME / 'config.ini'
    avd_config.parent.mkdir()
    avd_config.write_text('hw.device.name=pixel\nhw.ramSize=1024\n', encoding='utf-8')

    android_toolchain._set_avd_memory(avd_config)

    assert avd_config.read_text(encoding='utf-8') == (
        'hw.device.name=pixel\nhw.ramSize=2048\n'
    )


def test_existing_avd_is_not_recreated_or_overwritten(tmp_path, monkeypatch):
    calls = []
    emulator_dir = tmp_path / 'sdk' / 'emulator'
    emulator_dir.mkdir(parents=True)
    (emulator_dir / 'emulator.exe').write_text('', encoding='utf-8')
    monkeypatch.setattr(android_toolchain, '_avd_is_present', lambda *args: True)
    monkeypatch.setattr(
        android_toolchain, '_run', lambda *args, **kwargs: calls.append(args)
    )

    created = android_toolchain._create_avd_if_missing(
        tmp_path / 'avdmanager.bat', tmp_path / 'sdk', tmp_path / 'avds', {}
    )

    assert created is False
    assert calls == []


def test_download_rejects_non_official_host_before_network_io(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        android_toolchain.urllib.request, 'build_opener',
        lambda *args: calls.append('network'),
    )

    with pytest.raises(ValueError, match='official HTTPS'):
        android_toolchain._download(
            'https://example.com/android-tools.zip', tmp_path / 'tools.zip'
        )

    assert calls == []


def test_zip_extraction_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / 'unsafe.zip'
    with zipfile.ZipFile(archive_path, 'w') as archive:
        archive.writestr('../outside.txt', 'not allowed')

    destination = tmp_path / 'installed'

    with pytest.raises(ValueError, match='unsafe ZIP member'):
        android_toolchain._extract_zip(archive_path, destination)

    assert not (tmp_path / 'outside.txt').exists()


def test_corrupt_zip_is_rejected_before_extraction(tmp_path):
    archive_path = tmp_path / 'corrupt.zip'
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('payload.txt', 'integrity checked')
    corrupted = bytearray(stream.getvalue())
    payload_offset = corrupted.index(b'integrity checked')
    corrupted[payload_offset] ^= 1
    archive_path.write_bytes(corrupted)

    with pytest.raises(ValueError, match='CRC'):
        android_toolchain._extract_zip(archive_path, tmp_path / 'installed')


def test_download_rejects_a_checksum_mismatch_without_leaving_a_partial_file(
        tmp_path, monkeypatch):
    class Response(io.BytesIO):
        def geturl(self):
            return 'https://dl.google.com/android/repository/tools.zip'

    response = Response(b'valid-looking archive bytes')

    class Opener:
        def open(self, _url, timeout):
            assert timeout == 90
            return response

    monkeypatch.setattr(
        android_toolchain.urllib.request, 'build_opener', lambda *args: Opener()
    )
    destination = tmp_path / 'tools.zip'

    with pytest.raises(ValueError, match='SHA-256'):
        android_toolchain._download(
            'https://dl.google.com/android/repository/tools.zip',
            destination,
            sha256=hashlib.sha256(b'different bytes').hexdigest(),
        )

    assert not destination.exists()
    assert not destination.with_name('tools.zip.part').exists()


def test_install_archive_removes_download_after_zip_validation_fails(
        tmp_path, monkeypatch):
    destination = tmp_path / 'stage' / 'extract'
    archive_path = tmp_path / 'stage' / 'bad.zip'

    def write_unsafe_zip(_url, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, 'w') as archive:
            archive.writestr('../escaped.txt', 'rejected')
        return output_path

    monkeypatch.setattr(android_toolchain, '_download', write_unsafe_zip)

    with pytest.raises(ValueError, match='unsafe ZIP member'):
        android_toolchain._install_archive(
            'https://dl.google.com/android/repository/tools.zip',
            'bad.zip',
            destination,
        )

    assert not archive_path.exists()


def test_install_command_requires_explicit_license_acceptance(monkeypatch, capsys):
    import main

    calls = []
    monkeypatch.setattr(sys, 'argv', ['main.py', '--android-toolchain', 'install'])
    monkeypatch.setattr(
        android_toolchain, '_download', lambda *args, **kwargs: calls.append('download')
    )

    with pytest.raises(SystemExit) as caught:
        main.main()

    assert caught.value.code != 0
    output = capsys.readouterr()
    assert 'accept' in f'{output.out}\n{output.err}'.lower()
    assert calls == []


def test_android_toolchain_check_cli_returns_json_without_provider_config(
        monkeypatch, capsys):
    import main

    monkeypatch.setattr(sys, 'argv', [
        'main.py', '--android-toolchain', 'check', '--factory-json',
    ])
    monkeypatch.setattr(
        android_toolchain, 'check_environment',
        lambda: {'ready': False, 'missing': ['java17']},
    )

    with pytest.raises(SystemExit) as caught:
        main.main()

    assert caught.value.code == 1
    assert '"missing": [' in capsys.readouterr().out


def test_android_toolchain_install_cli_passes_explicit_license_acceptance(
        monkeypatch, capsys):
    import main

    calls = []

    def install_toolchain(*, accept_licenses=False):
        calls.append(accept_licenses)
        return {'ok': True}

    monkeypatch.setattr(sys, 'argv', [
        'main.py', '--android-toolchain', 'install', '--accept-licenses',
        '--factory-json',
    ])
    monkeypatch.setattr(android_toolchain, 'install_toolchain', install_toolchain)

    with pytest.raises(SystemExit) as caught:
        main.main()

    assert caught.value.code == 0
    assert calls == [True]
    assert '"ok": true' in capsys.readouterr().out
