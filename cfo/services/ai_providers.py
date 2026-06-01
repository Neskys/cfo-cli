"""Provider-specific completion calls. SDKs (anthropic / openai) imported lazily.

Both providers receive the same stable instructions + aggregated context first and
the volatile question last:
  - Anthropic: explicit prompt caching via cache_control on the context block.
  - OpenAI: automatic prefix caching (no flag) benefits from stable-content-first.
"""

PROVIDER_DEFAULT_MODEL = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
}
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


def _openai(api_key, model, system_prompt, context, question, max_tokens):
    try:
        import openai
    except ImportError:
        raise AIError("OpenAI provider needs 'openai'. Install: pip install 'cfo-cli[openai]'")
    client = openai.OpenAI(api_key=api_key)
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


def complete(provider, api_key, model, system_prompt, context, question, max_tokens=2048):
    if provider == "anthropic":
        return _anthropic(api_key, model, system_prompt, context, question, max_tokens)
    if provider == "openai":
        return _openai(api_key, model, system_prompt, context, question, max_tokens)
    raise AIError(f"Unknown AI provider '{provider}'. Choose from: {', '.join(VALID_PROVIDERS)}")
