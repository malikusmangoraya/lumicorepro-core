import json
import sys
from pathlib import Path

import pytest

AI_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

from agent.reflex_project_generator import ReflexGenerationError, ReflexProjectGenerator
from agent.project_framework import generate_project_for_framework


def test_generate_writes_minimal_reflex_project(tmp_path):
    destination = tmp_path / 'sample_app'
    result = ReflexProjectGenerator().generate(str(destination), 'sample_app')

    assert result['framework'] == 'reflex'
    assert result['status'] == 'created'
    assert (destination / 'sample_app' / 'sample_app.py').is_file()
    assert (destination / 'rxconfig.py').is_file()
    assert 'reflex==' in (destination / 'requirements.txt').read_text()
    assert json.loads((destination / 'generation-report.json').read_text())['framework'] == 'reflex'


def test_rejects_unsafe_project_name(tmp_path):
    with pytest.raises(ReflexGenerationError, match='project name'):
        ReflexProjectGenerator().generate(str(tmp_path / 'bad'), '../bad')


def test_does_not_overwrite_nonempty_destination(tmp_path):
    destination = tmp_path / 'existing'
    destination.mkdir()
    marker = destination / 'keep.txt'
    marker.write_text('untouched')

    with pytest.raises(ReflexGenerationError, match='not empty'):
        ReflexProjectGenerator().generate(str(destination), 'sample_app')

    assert marker.read_text() == 'untouched'


def test_framework_dispatch_defaults_to_react_path():
    sentinel = object()
    result = generate_project_for_framework('react', lambda: sentinel, lambda: None)

    assert result is sentinel


def test_framework_dispatch_routes_explicit_reflex():
    sentinel = object()
    result = generate_project_for_framework('reflex', lambda: None, lambda: sentinel)

    assert result is sentinel


def test_framework_dispatch_rejects_unknown_values():
    with pytest.raises(ValueError, match='framework'):
        generate_project_for_framework('unknown', lambda: None, lambda: None)


def test_generated_app_has_no_unverified_integrations(tmp_path):
    destination = tmp_path / 'sample_app'
    ReflexProjectGenerator().generate(str(destination), 'sample_app')
    app_source = (destination / 'sample_app' / 'sample_app.py').read_text()

    assert 'import reflex as rx' in app_source
    assert 'class State(rx.State)' in app_source
    assert 'rx.App()' in app_source


def test_runtime_validation_reports_missing_optional_dependency(tmp_path, monkeypatch):
    destination = tmp_path / 'runtime_checked'

    real_import = __import__

    def import_without_reflex(name, *args, **kwargs):
        if name == 'reflex':
            raise ModuleNotFoundError("No module named 'reflex'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr('builtins.__import__', import_without_reflex)

    with pytest.raises(ReflexGenerationError, match='optional Reflex dependency'):
        ReflexProjectGenerator().generate(str(destination), 'runtime_checked', validate_runtime=True)

    assert not destination.exists()
