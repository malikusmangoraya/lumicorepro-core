"""Contract tests for the `/api/external-agents/*` routes.

These pin the HTTP contract the dashboard relies on: the API key is required,
a missing CLI is 503, and a TUI-only freebuff is 501 rather than a request
that hangs until the subprocess timeout.
"""

import os
import sys
from unittest import mock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as server_mod  # noqa: E402
from agent import external_agents  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(server_mod, "_AGENT_API_KEY", "test-agent-key")
    return TestClient(server_mod.app)


HEADERS = {"X-API-KEY": "test-agent-key"}


@pytest.fixture()
def project_dir(tmp_path):
    path = tmp_path / "project"
    path.mkdir()
    return path


def test_status_requires_the_api_key(client):
    assert client.get("/api/external-agents/status").status_code == 401


def test_status_returns_capabilities(client):
    fake = {
        "opencode": {"installed": True, "path": "opencode", "headless": True},
        "freebuff": {"installed": True, "path": "freebuff", "headless": False},
    }
    with mock.patch.object(external_agents, "tool_status", return_value=fake):
        response = client.get("/api/external-agents/status", headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["opencode"]["headless"] is True
    assert body["data"]["freebuff"]["headless"] is False


def test_opencode_missing_cli_is_503(client, project_dir):
    with mock.patch.object(
        external_agents, "run_opencode", return_value={"status": "not_available"}
    ):
        response = client.post(
            "/api/external-agents/opencode",
            json={"task": "add tests", "project_dir": str(project_dir)},
            headers=HEADERS,
        )
    assert response.status_code == 503


def test_opencode_passed_run_is_200(client, project_dir):
    outcome = {"status": "passed", "exit_code": 0, "output": "done"}
    with mock.patch.object(external_agents, "run_opencode", return_value=outcome):
        response = client.post(
            "/api/external-agents/opencode",
            json={"task": "add tests", "project_dir": str(project_dir)},
            headers=HEADERS,
        )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "passed"


def test_freebuff_tui_only_is_501_not_a_hang(client, project_dir):
    with mock.patch.object(
        external_agents,
        "run_freebuff",
        return_value={"status": "unsupported", "reason": "no_headless_mode"},
    ):
        response = client.post(
            "/api/external-agents/freebuff",
            json={"task": "add tests", "project_dir": str(project_dir)},
            headers=HEADERS,
        )
    assert response.status_code == 501
    assert "headless" in response.json()["detail"]


def test_invalid_project_dir_is_422_before_any_spawn(client):
    with mock.patch.object(external_agents, "run_opencode") as run:
        response = client.post(
            "/api/external-agents/opencode",
            json={"task": "add tests", "project_dir": "does/not/exist"},
            headers=HEADERS,
        )
    assert response.status_code == 422
    run.assert_not_called()
