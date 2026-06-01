# ADR-0002: Layered architecture with a service layer

- **Status:** Accepted
- **Date:** 2026-01 (backfilled)
- **Deciders:** Xavier Potrony

## Context and problem statement

The CLI grows one command group at a time (budget, expense, income, …). Without
discipline, parsing, business logic and SQL tend to pile into the command files,
becoming untestable and entangled.

## Decision drivers

- Testability — logic must be exercisable without invoking the CLI.
- Separation of concerns — keep UI parsing apart from data logic.
- Predictable structure as the surface area grows.

## Considered options

1. **Strict layering:** `cli/` parses and renders; `services/` holds all DB logic
   and raises typed errors; one file per command group.
2. **Logic inside the typer command functions** (no service layer).
3. **A fat "models" layer** mixing persistence and behaviour.

## Decision

We chose **strict layering**: `cfo/cli/<group>.py` only parses arguments, calls a
service, and renders; `cfo/services/<name>.py` owns all database access and
raises typed errors (`ExpenseError`, `CurrencyError`, …) that the CLI catches and
reports cleanly. One file per command group; files kept small (~150 lines).

## Consequences

- **Positive:** services are unit-tested directly (every service module is at
  100% coverage); CLI files stay thin; clear place for each kind of change.
- **Negative / trade-offs:** some boilerplate (a CLI wrapper per service call);
  a few mature service modules slightly exceed the size guideline.
- **Follow-ups:** documented as coding rules in CLAUDE.md and CONTRIBUTING.md.
