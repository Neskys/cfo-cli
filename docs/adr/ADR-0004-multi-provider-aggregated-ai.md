# ADR-0004: Multi-provider AI, aggregated data only

- **Status:** Accepted
- **Date:** 2026-04 (backfilled, v0.7–v0.9)
- **Deciders:** Xavier Potrony

## Context and problem statement

We want AI-powered insights (analysis, anomalies, suggestions) without
compromising the local-first/privacy promise, and without locking users into one
vendor or forcing a paid API on them.

## Decision drivers

- Privacy — the AI must not see raw transactions.
- Choice — support more than one provider; avoid lock-in.
- Cost — offer a genuinely free path.
- Simplicity of auth — the inference APIs are API-key based, not OAuth.

## Considered options

1. **Provider-agnostic layer** sending **aggregated** context only, with
   Anthropic, OpenAI, and a free local (Ollama/Gemma) provider.
2. **Single hosted provider** (Anthropic only).
3. **Send full transaction history** for richer answers.

## Decision

We chose a **provider-agnostic design** (`services/ai.py` builds context from the
summary services; `services/ai_providers.py` adapts each SDK). Only **aggregated
figures** are ever sent. Providers: `anthropic` (default `claude-sonnet-4-6`),
`openai` (`gpt-4o`), and `local` (Gemma 4 via Ollama — no key, no cost, offline,
reusing the OpenAI-compatible client against a configurable `base_url`). Hosted
providers authenticate by API key stored locally; the stable context block is
prompt-cached.

## Consequences

- **Positive:** privacy preserved; users pick their provider or pay nothing with
  `local`; adding a provider is a small adapter.
- **Negative / trade-offs:** aggregation limits answer depth; tool-calling/agentic
  use with small local models is less reliable (noted for future work).
- **Follow-ups:** `KEY_REQUIRED` excludes `local`; tests mock all SDKs — no live
  calls.
