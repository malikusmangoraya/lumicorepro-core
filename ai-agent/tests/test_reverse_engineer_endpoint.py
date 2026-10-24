"""Contract tests for the `/api/reverse-engineer` route.

The analyser is read-only by design, but the route takes a filesystem path, so
what these tests really pin down is the confinement: an authenticated caller
must not be able to point it at an arbitrary directory on the host, and the
response must not leak secrets (the analyser reports risk names and paths only).
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as server_mod  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(server_mod, "_AGENT_API_KEY", "test-agent-key")
    return TestClient(server_mod.app)


HEADERS = {"X-API-KEY": "test-agent-key"}


@pytest.fixture()
def sample_repo(tmp_path, monkeypatch):
    """A tiny two-file repo made reachable through REVERSE_ENGINEER_ROOTS."""
    repo = tmp_path / "acme"
    (repo / "backend").mkdir(parents=True)
    (repo / "package.json").write_text(
        '{"name":"acme","dependencies":{"express":"^4","react":"^19"}}', encoding="utf-8"
    )
    (repo / "backend" / "routes.js").write_text(
        "router.get('/products', list);\nrouter.post('/orders', create);\n"
        "db.query(`SELECT * FROM users WHERE id = ${id}`);\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("REVERSE_ENGINEER_ROOTS", str(repo))
    return repo


def test_rejects_missing_api_key(client):
    response = client.post("/api/reverse-engineer", json={"path": "."})
    assert response.status_code == 401


def test_rejects_path_outside_allowed_roots(client, tmp_path):
    outside = tmp_path / "somewhere-else"
    outside.mkdir()
    response = client.post(
        "/api/reverse-engineer", json={"path": str(outside)}, headers=HEADERS
    )
    assert response.status_code == 403
    assert "allowed scan roots" in response.json()["detail"]


def test_rejects_a_file_not_a_directory(client, sample_repo):
    response = client.post(
        "/api/reverse-engineer",
        json={"path": str(sample_repo / "package.json")},
        headers=HEADERS,
    )
    assert response.status_code == 404


def test_rejects_a_nonexistent_path(client, sample_repo):
    response = client.post(
        "/api/reverse-engineer",
        json={"path": str(sample_repo / "nope")},
        headers=HEADERS,
    )
    assert response.status_code == 404


def test_returns_scan_plan_and_report(client, sample_repo):
    response = client.post(
        "/api/reverse-engineer",
        json={"path": str(sample_repo), "max_files": 50},
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["scan"]["stats"]["files_scanned"] >= 1
    assert body["scan"]["stats"]["languages"]
    assert body["scan"]["stack"]["frameworks"]
    paths = {route["path"] for route in body["scan"]["routes"]}
    assert {"/products", "/orders"} <= paths
    backlog = " ".join(body["plan"]["risk_backlog"])
    assert "sql-string-interpolation" in backlog
    assert "## " in body["report_markdown"]


def test_include_report_false_omits_markdown(client, sample_repo):
    response = client.post(
        "/api/reverse-engineer",
        json={"path": str(sample_repo), "include_report": False},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert "report_markdown" not in response.json()


def test_reported_secret_risk_names_the_file_not_the_value(client, tmp_path, monkeypatch):
    repo = tmp_path / "leaky"
    repo.mkdir()
    (repo / "config.js").write_text(
        'const AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE1234";\n', encoding="utf-8"
    )
    monkeypatch.setenv("REVERSE_ENGINEER_ROOTS", str(repo))
    response = client.post(
        "/api/reverse-engineer", json={"path": str(repo)}, headers=HEADERS
    )
    assert response.status_code == 200
    assert "AKIAIOSFODNN7EXAMPLE1234" not in response.text


def test_max_files_is_clamped_by_the_schema(client):
    response = client.post(
        "/api/reverse-engineer", json={"path": ".", "max_files": 0}, headers=HEADERS
    )
    assert response.status_code == 422
