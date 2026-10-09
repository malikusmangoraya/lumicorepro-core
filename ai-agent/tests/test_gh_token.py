"""Canonical GITHUB_TOKEN handling — quote stripping, placeholders, ordering."""
import os
import sys
from pathlib import Path

import pytest

AI_AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

from agent.gh_token import (  # noqa: E402
    clean_token,
    is_placeholder,
    load_token,
    looks_like_token,
    token_from_env_files,
    validate_token,
)

VALID = "ghp_" + "a" * 36


class TestCleanToken:
    def test_plain_token_unchanged(self):
        assert clean_token(VALID) == VALID

    def test_strips_double_quotes(self):
        assert clean_token(f'"{VALID}"') == VALID

    def test_strips_single_quotes(self):
        assert clean_token(f"'{VALID}'") == VALID

    def test_strips_unbalanced_trailing_quote(self):
        # The real-world `setx TOKEN "ghp_..."` failure mode.
        assert clean_token(f'{VALID}"') == VALID

    def test_strips_surrounding_whitespace(self):
        assert clean_token(f"  {VALID}\n") == VALID

    def test_empty_inputs(self):
        assert clean_token(None) == ""
        assert clean_token("") == ""
        assert clean_token("   ") == ""


class TestPlaceholder:
    @pytest.mark.parametrize(
        "value",
        ["", None, "your_github_token_here", "ghp_xxx", "CHANGEME", "<token>"],
    )
    def test_placeholders_detected(self, value):
        assert is_placeholder(value) is True

    def test_real_token_is_not_placeholder(self):
        assert is_placeholder(VALID) is False


class TestLooksLikeToken:
    def test_classic_pat_shape(self):
        assert looks_like_token(VALID) is True
        assert looks_like_token(f'"{VALID}"') is True

    def test_fine_grained_shape(self):
        assert looks_like_token("github_pat_" + "b" * 30) is True

    def test_wrong_shape_rejected(self):
        assert looks_like_token("ghp_short") is False


class TestEnvFileParsing:
    def test_reads_and_quote_strips(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text(f'GITHUB_TOKEN="{VALID}"\nOTHER=1\n', encoding="utf-8")
        assert token_from_env_files([env]) == VALID

    def test_skips_placeholder_and_takes_next(self, tmp_path):
        first = tmp_path / "a.env"
        first.write_text("GITHUB_TOKEN=your_token_here\n", encoding="utf-8")
        second = tmp_path / "b.env"
        second.write_text(f"GITHUB_TOKEN={VALID}\n", encoding="utf-8")
        assert token_from_env_files([first, second]) == VALID

    def test_missing_files_ignored(self, tmp_path):
        assert token_from_env_files([tmp_path / "nope.env"]) == ""

    def test_none_paths_ignored(self):
        assert token_from_env_files([None, ""]) == ""


class TestLoadToken:
    def test_env_file_wins_over_process_env(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text(f"GITHUB_TOKEN={VALID}\n", encoding="utf-8")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "z" * 36)
        assert load_token(env_files=[env]) == VALID

    def test_falls_back_to_process_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", f'"{VALID}"')
        assert load_token(env_files=[tmp_path / "missing.env"]) == VALID

    def test_ignores_placeholder_process_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "your_token_here")
        assert load_token(env_files=[tmp_path / "missing.env"]) == ""

    def test_empty_when_nothing_available(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        assert load_token(env_files=[tmp_path / "missing.env"]) == ""


class TestValidateToken:
    def test_empty_token_rejected_without_network(self):
        ok, detail = validate_token("")
        assert ok is False
        assert detail == "no token found"

    def test_placeholder_rejected_without_network(self):
        ok, detail = validate_token("your_token_here")
        assert ok is False
        assert detail == "token is a placeholder"

    def test_network_failure_is_unprovable_not_invalid(self, monkeypatch):
        # Offline/DNS/TLS trouble must never be reported as bad credentials.
        import urllib.error
        import urllib.request

        import agent.gh_token as gh_token

        def boom(*_args, **_kwargs):
            raise urllib.error.URLError("name resolution failed")

        monkeypatch.setattr(gh_token.urllib.request, "urlopen", boom)
        ok, detail = gh_token.validate_token(VALID, timeout=1)
        assert ok is False
        assert "Bad credentials" not in detail
        assert "could not verify" in detail

    def test_real_api_rejects_a_dead_token(self):
        ok, detail = validate_token("ghp_" + "0" * 36, timeout=20)
        assert ok is False
        assert "Bad credentials" in detail or "HTTP" in detail or "could not verify" in detail


def test_no_token_committed_to_repo():
    """Guard: no real-looking PAT may be introduced into tracked files."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "grep", "-lE", r"ghp_[A-Za-z0-9]{36}"],
            cwd=str(Path(__file__).resolve().parents[2]),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        pytest.skip("git unavailable")
    offenders = [
        line
        for line in out.stdout.splitlines()
        if line and ".env" not in line and "tests/" not in line
    ]
    assert not offenders, f"PAT-shaped literals in tracked files: {offenders}"