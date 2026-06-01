# ADR-0005: Lazy SDK imports behind optional extras

- **Status:** Accepted
- **Date:** 2026-04 (backfilled)
- **Deciders:** Xavier Potrony

## Context and problem statement

Some capabilities need heavy third-party libraries: `reportlab` (PDF) and the AI
SDKs (`anthropic`, `openai`). Most users won't use all of them. Forcing every
dependency on every install bloats the footprint and the attack surface.

## Decision drivers

- Keep the default install light and fast.
- Don't break core features when an optional library is absent.
- Clear, opt-in installation of heavy features.

## Considered options

1. **Optional extras** (`[ai]`, `[openai]`) + **lazy imports** at call sites,
   raising a clean, actionable error if the library is missing.
2. **All dependencies required** in the base install.
3. **Separate companion packages** per feature.

## Decision

We chose **optional extras with lazy imports**. `reportlab` is imported only when
a PDF is generated (CSV works without it); the AI SDKs are imported inside the
provider adapters and gated behind `pip install 'cfo-cli[ai]'` / `[openai]`. A
missing library yields a friendly message telling the user exactly what to
install.

## Consequences

- **Positive:** small default install; core works offline with no AI/PDF deps;
  smaller attack surface; faster cold start.
- **Negative / trade-offs:** import errors surface at call time, not install time
  → mitigated by explicit, tested error messages.
- **Follow-ups:** the `local` AI provider reuses the `[openai]` extra rather than
  adding a new dependency.
