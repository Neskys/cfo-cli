# ADR-0003: Numbered, append-only migrations

- **Status:** Accepted
- **Date:** 2026-02 (backfilled, introduced in v0.2)
- **Deciders:** Xavier Potrony

## Context and problem statement

After the initial budget schema, every later version adds tables (income,
forecast, exchange rates). Users upgrade the package over an **existing** local
database, so the schema must evolve safely without data loss and without a manual
step.

## Decision drivers

- Safe, automatic upgrades of a user's existing `~/.cfo/data.db`.
- Deterministic, ordered, idempotent schema changes.
- Auditability of what has been applied.

## Considered options

1. **Numbered migration functions** auto-applied by `init_db()`, tracked in a
   `schema_migrations` table.
2. **Recreate schema with `CREATE TABLE IF NOT EXISTS`** on every run.
3. **A third-party migration framework** (Alembic).

## Decision

We chose a **small numbered-migrations system** in
`cfo/storage/migrations.py`: a `MIGRATIONS` dict maps an integer to a
`(name, function)`; `init_db()` applies pending ones in order and records them in
`schema_migrations`. **Existing migrations are never edited — always add the next
number.**

## Consequences

- **Positive:** zero-touch upgrades; clear history; no heavy dependency; trivial
  to test (assert a version is recorded and a table exists).
- **Negative / trade-offs:** we maintain the runner ourselves (no downgrade
  support — acceptable for a local single-file DB).
- **Follow-ups:** the "next: N" hint in the MIGRATIONS dict keeps numbering
  unambiguous.
