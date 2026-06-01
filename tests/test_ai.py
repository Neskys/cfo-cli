"""Tests for AI commands and services (provider SDKs mocked — no live calls)."""

import sys
import types
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.services import ai, ai_providers
from cfo.core.config import get_api_key, get_provider

runner = CliRunner()


@pytest.fixture
def ai_env(tmp_path, monkeypatch):
    """Anthropic provider configured; ai.complete patched to capture its args."""
    monkeypatch.setenv("HOME", str(tmp_path))
    capture: dict = {}

    def fake_complete(provider, api_key, model, system_prompt, context, question,
                      max_tokens=2048, base_url=None):
        capture.update(provider=provider, api_key=api_key, model=model, system_prompt=system_prompt,
                       context=context, question=question, base_url=base_url)
        return "AI RESULT TEXT"

    monkeypatch.setattr(ai, "complete", fake_complete)
    runner.invoke(app, ["ai", "config", "--api-key", "sk-ant-test-key-123456"])
    runner.invoke(app, ["income", "add", "--amount", "1000", "--date", "2026-01-10"])
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "300", "--date", "2026-01-15"])
    return capture


# ---- config / provider selection ----

def test_config_saves_key_default_anthropic(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["ai", "config", "--api-key", "sk-ant-abcdef123456"])
    assert result.exit_code == 0
    assert get_provider() == "anthropic"
    assert get_api_key("anthropic") == "sk-ant-abcdef123456"


def test_config_openai_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["ai", "config", "--api-key", "sk-openai-xyz789", "--provider", "openai"])
    assert result.exit_code == 0
    assert get_provider() == "openai"
    assert get_api_key("openai") == "sk-openai-xyz789"


def test_config_bad_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert runner.invoke(app, ["ai", "config", "--api-key", "k", "--provider", "grok"]).exit_code != 0


def test_set_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["ai", "config", "--api-key", "sk-ant-123456789012"])
    runner.invoke(app, ["ai", "config", "--api-key", "sk-oai-123456789012", "--provider", "openai"])
    runner.invoke(app, ["ai", "set-provider", "anthropic"])
    assert get_provider() == "anthropic"
    assert runner.invoke(app, ["ai", "set-provider", "nope"]).exit_code != 0


# ---- orchestration: provider/model/context routing ----

def test_analyze_routes_to_anthropic_default(ai_env):
    result = runner.invoke(app, ["ai", "analyze", "--focus", "expenses"])
    assert result.exit_code == 0 and "AI RESULT TEXT" in result.output
    assert ai_env["provider"] == "anthropic"
    assert ai_env["model"] == "claude-sonnet-4-6"
    assert "no individual transactions" in ai_env["context"]


def test_analyze_routes_to_openai(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    capture: dict = {}
    monkeypatch.setattr(ai, "complete",
                        lambda *a, **k: capture.update(provider=a[0], model=a[2]) or "OK")
    runner.invoke(app, ["ai", "config", "--api-key", "sk-oai-abc123456789", "--provider", "openai"])
    result = runner.invoke(app, ["ai", "analyze"])
    assert result.exit_code == 0
    assert capture["provider"] == "openai" and capture["model"] == "gpt-4o"


def test_model_override(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    capture: dict = {}
    monkeypatch.setattr(ai, "complete", lambda *a, **k: capture.update(model=a[2]) or "OK")
    runner.invoke(app, ["ai", "config", "--api-key", "sk-oai-abc123456789",
                        "--provider", "openai", "--model", "gpt-4.1"])
    runner.invoke(app, ["ai", "analyze"])
    assert capture["model"] == "gpt-4.1"


def test_analyze_no_key_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert runner.invoke(app, ["ai", "analyze"]).exit_code != 0


def test_bad_focus_goal_threshold(ai_env):
    assert runner.invoke(app, ["ai", "analyze", "--focus", "bogus"]).exit_code != 0
    assert runner.invoke(app, ["ai", "suggest", "--goal", "buy-lambos"]).exit_code != 0
    assert runner.invoke(app, ["ai", "anomalies", "--threshold", "0"]).exit_code != 0


def test_anomalies_and_suggest_questions(ai_env):
    runner.invoke(app, ["ai", "anomalies", "--threshold", "1.5"])
    assert "1.5 standard deviations" in ai_env["question"]
    runner.invoke(app, ["ai", "suggest", "--goal", "increase-cashflow"])
    assert "increase cashflow" in ai_env["question"]


def test_build_context_is_aggregated(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "300"])
    context = ai.build_context()
    assert "AGGREGATED FINANCIAL DATA" in context
    assert "Expenses by category" in context and "Income by month" in context


# ---- provider adapters (SDKs mocked) ----

def test_anthropic_adapter_uses_cache_control(monkeypatch):
    capture: dict = {}

    class _Msgs:
        def create(self, **kwargs):
            capture.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type="text", text="CLAUDE OUT")])

    class _FakeAnthropic:
        def __init__(self, api_key=None):
            capture["api_key"] = api_key
            self.messages = _Msgs()

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", _FakeAnthropic)
    out = ai_providers._anthropic("k", "claude-sonnet-4-6", "SYS", "CTX", "Q", 2048)
    assert out == "CLAUDE OUT"
    assert capture["model"] == "claude-sonnet-4-6"
    assert capture["system"][-1]["cache_control"] == {"type": "ephemeral"}
    assert capture["system"][-1]["text"] == "CTX"


def test_openai_adapter_message_shape(monkeypatch):
    capture: dict = {}

    class _Completions:
        def create(self, **kwargs):
            capture.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OPENAI OUT"))])

    class _FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            capture["api_key"] = api_key
            capture["base_url"] = base_url
            self.chat = SimpleNamespace(completions=_Completions())

    fake_mod = types.ModuleType("openai")
    fake_mod.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_mod)

    out = ai_providers._openai("k", "gpt-4o", "SYS", "CTX", "Q", 2048)
    assert out == "OPENAI OUT"
    assert capture["model"] == "gpt-4o" and capture["base_url"] is None
    msgs = capture["messages"]
    assert msgs[0]["role"] == "system" and "CTX" in msgs[0]["content"]
    assert msgs[1] == {"role": "user", "content": "Q"}


def test_local_provider_routes_to_ollama(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    capture: dict = {}

    def fake_complete(provider, api_key, model, system_prompt, context, question,
                      max_tokens=2048, base_url=None):
        capture.update(provider=provider, api_key=api_key, model=model, base_url=base_url)
        return "LOCAL OUT"

    monkeypatch.setattr(ai, "complete", fake_complete)
    # No API key needed for local — just switch provider.
    runner.invoke(app, ["ai", "set-provider", "local"])
    result = runner.invoke(app, ["ai", "analyze"])
    assert result.exit_code == 0 and "LOCAL OUT" in result.output
    assert capture["provider"] == "local"
    assert capture["model"] == "gemma4"
    assert capture["base_url"] == "http://localhost:11434/v1"
    assert not capture["api_key"]  # None/empty — local needs no key


def test_local_adapter_uses_base_url_and_placeholder_key(monkeypatch):
    capture: dict = {}

    class _Completions:
        def create(self, **kwargs):
            capture.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="GEMMA OUT"))])

    class _FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            capture["api_key"] = api_key
            capture["base_url"] = base_url
            self.chat = SimpleNamespace(completions=_Completions())

    fake_mod = types.ModuleType("openai")
    fake_mod.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_mod)

    out = ai_providers._openai(None, "gemma4", "SYS", "CTX", "Q", 2048,
                               base_url="http://localhost:11434/v1")
    assert out == "GEMMA OUT"
    assert capture["base_url"] == "http://localhost:11434/v1"
    assert capture["api_key"] == "local"  # placeholder when no key configured


def test_anthropic_api_failure_is_wrapped(monkeypatch):
    class _Messages:
        def create(self, **kwargs):
            raise RuntimeError("boom")

    class _FakeAnthropic:
        def __init__(self, api_key=None):
            self.messages = _Messages()

    fake_mod = types.ModuleType("anthropic")
    fake_mod.Anthropic = _FakeAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake_mod)

    with pytest.raises(ai_providers.AIError, match="AI request failed"):
        ai_providers.complete("anthropic", "k", "claude-sonnet-4-6", "SYS", "CTX", "Q")


def test_openai_missing_package_is_wrapped(monkeypatch):
    # Force `import openai` to fail even though it may be installed.
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ai_providers.AIError, match="needs 'openai'"):
        ai_providers._openai("k", "gpt-4o", "SYS", "CTX", "Q", 2048)


def test_openai_api_failure_is_wrapped(monkeypatch):
    class _Completions:
        def create(self, **kwargs):
            raise RuntimeError("boom")

    class _FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            self.chat = SimpleNamespace(completions=_Completions())

    fake_mod = types.ModuleType("openai")
    fake_mod.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_mod)

    with pytest.raises(ai_providers.AIError, match="AI request failed"):
        ai_providers.complete("openai", "k", "gpt-4o", "SYS", "CTX", "Q")


def test_unknown_provider():
    with pytest.raises(ai_providers.AIError):
        ai_providers.complete("grok", "k", "m", "s", "c", "q")


def test_missing_anthropic_package(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def _no_anthropic(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_anthropic)
    with pytest.raises(ai_providers.AIError):
        ai_providers._anthropic("k", "m", "s", "c", "q", 10)
