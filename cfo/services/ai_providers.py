"""Provider-specific completion calls. SDKs (anthropic / openai) imported lazily.

Providers:
  - anthropic : Claude API (explicit prompt caching via cache_control).
  - openai    : OpenAI API (automatic prefix caching).
  - local     : OpenAI-compatible local server (Ollama) — runs Gemma 4 at no cost,
                offline, no API key. Reuses the OpenAI SDK with a custom base_url.

All providers receive the stable instructions + aggregated context first and the
volatile question last.
"""

PROVIDER_DEFAULT_MODEL = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "local": "gemma4",
}
# OpenAI-compatible servers that need a non-default endpoint.
PROVIDER_DEFAULT_BASE_URL = {
    "local": "http://localhost:11434/v1",  # Ollama
}
# Providers that authenticate with an API key (local Ollama needs none).
KEY_REQUIRED = ("anthropic", "openai")
VALID_PROVIDERS = tuple(PROVIDER_DEFAULT_MODEL)


class AIError(Exception):
    """Validation, configuration, or API failure surfaced to the CLI cleanly."""


def _anthropic(api_key, model, system_prompt, context, question, max_tokens):
    try:
        import anthropic
    except ImportError:
        raise AIError("Anthropic provider needs 'anthropic'. Install: pip install 'cfo-cli[ai]'")
    client = anthropic.Anthropic(api_key=api_key)
    system = [
        {"type": "text", "text": system_prompt},
        {"type": "text", "text": context, "cache_control": {"type": "ephemeral"}},
    ]
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": question}],
        )
    except Exception as e:
        raise AIError(f"AI request failed: {e}")
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


def _openai(api_key, model, system_prompt, context, question, max_tokens, base_url=None):
    try:
        import openai
    except ImportError:
        raise AIError("This provider needs 'openai'. Install: pip install 'cfo-cli[openai]'")
    # Ollama (local) ignores the key but the SDK requires a non-empty string.
    client = openai.OpenAI(api_key=api_key or "local", base_url=base_url)
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\n{context}"},
                {"role": "user", "content": question},
            ],
        )
    except Exception as e:
        raise AIError(f"AI request failed: {e}")
    return (resp.choices[0].message.content or "").strip()


def complete(provider, api_key, model, system_prompt, context, question, max_tokens=2048, base_url=None):
    if provider == "anthropic":
        return _anthropic(api_key, model, system_prompt, context, question, max_tokens)
    if provider in ("openai", "local"):
        return _openai(api_key, model, system_prompt, context, question, max_tokens, base_url)
    raise AIError(f"Unknown AI provider '{provider}'. Choose from: {', '.join(VALID_PROVIDERS)}")

