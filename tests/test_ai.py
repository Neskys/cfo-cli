"""Tests for AI commands and the AI service (Anthropic client mocked — no live calls)."""

from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.services import ai
from cfo.core.config import get_api_key

runner = CliRunner()


class _FakeMessages:
    def __init__(self, capture):
        self.capture = capture

    def create(self, **kwargs):
        self.capture.update(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="AI RESULT TEXT")],
            usage=SimpleNamespace(cache_read_input_tokens=0, cache_creation_input_tokens=0),
        )


class _FakeClient:
    def __init__(self, capture):
        self.messages = _FakeMessages(capture)


@pytest.fixture
def ai_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    capture: dict = {}
    monkeypatch.setattr(ai, "_client", lambda api_key: _FakeClient(capture))
    runner.invoke(app, ["ai", "config", "--api-key", "sk-ant-test-key-123456"])
    # Seed a little data so the context is non-trivial.
    runner.invoke(app, ["income", "add", "--amount", "1000", "--date", "2026-01-10"])
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "300", "--date", "2026-01-15"])
    return capture


def test_config_saves_key(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["ai", "config", "--api-key", "sk-ant-abcdef123456"])
    assert result.exit_code == 0
    assert get_api_key() == "sk-ant-abcdef123456"


def test_analyze_uses_sonnet_and_caching(ai_env):
    result = runner.invoke(app, ["ai", "analyze", "--focus", "expenses"])
    assert result.exit_code == 0 and "AI RESULT TEXT" in result.output
    # Correct model
    assert ai_env["model"] == "claude-sonnet-4-6"
    # Prompt caching: cache_control on the context block (last system block)
    system = ai_env["system"]
    assert system[-1]["cache_control"] == {"type": "ephemeral"}
    # Aggregated data only — no raw-row leakage marker
    assert "no individual transactions" in system[-1]["text"]


def test_analyze_no_key_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["ai", "analyze"])
    assert result.exit_code != 0


def test_analyze_bad_focus(ai_env):
    assert runner.invoke(app, ["ai", "analyze", "--focus", "bogus"]).exit_code != 0


def test_anomalies(ai_env):
    result = runner.invoke(app, ["ai", "anomalies", "--threshold", "1.5"])
    assert result.exit_code == 0 and "AI RESULT TEXT" in result.output
    assert "1.5 standard deviations" in ai_env["messages"][0]["content"]


def test_anomalies_bad_threshold(ai_env):
    assert runner.invoke(app, ["ai", "anomalies", "--threshold", "0"]).exit_code != 0


def test_suggest(ai_env):
    result = runner.invoke(app, ["ai", "suggest", "--goal", "increase-cashflow"])
    assert result.exit_code == 0 and "AI RESULT TEXT" in result.output
    assert "increase cashflow" in ai_env["messages"][0]["content"]


def test_suggest_bad_goal(ai_env):
    assert runner.invoke(app, ["ai", "suggest", "--goal", "buy-lambos"]).exit_code != 0


def test_build_context_is_aggregated(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "300"])
    context = ai.build_context()
    assert "AGGREGATED FINANCIAL DATA" in context
    assert "Expenses by category" in context and "Income by month" in context


def test_missing_anthropic_package(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["ai", "config", "--api-key", "sk-ant-xyz789abcdef"])

    import builtins

    real_import = builtins.__import__

    def _no_anthropic(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_anthropic)
    result = runner.invoke(app, ["ai", "analyze"])
    assert result.exit_code != 0
