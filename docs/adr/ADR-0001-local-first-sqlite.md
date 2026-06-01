# ADR-0001: Local-first SQLite storage

- **Status:** Accepted
- **Date:** 2026-01 (backfilled)
- **Deciders:** Xavier Potrony

## Context and problem statement

cfo-cli manages a user's financial data. We need a persistence layer. The target
users are solo operators who value privacy, offline use, and full ownership of
their data, and who run the tool from a terminal.

## Decision drivers

- Privacy and data ownership — no third party should hold the data.
- Offline-first — must work with no network.
- Zero setup — no database server to install or configure.
- Portability — easy backup and restore.

## Considered options

1. **SQLite file in `~/.cfo/data.db`.**
2. **A cloud/hosted database** (Postgres + a backend service).
3. **Flat files** (JSON/CSV) on disk.

## Decision

We chose **SQLite at `~/.cfo/data.db`**, with non-DB config in
`~/.cfo/config.json`. It is embedded (no server), transactional, queryable with
SQL for aggregates/reports, and the entire dataset is a single portable file the
user owns.

## Consequences

- **Positive:** zero-config, offline, private, trivially backed up (copy one
  file), strong enough querying for summaries and forecasts.
- **Negative / trade-offs:** single-user only; no built-in sync across machines
  (acceptable — multi-user is an explicit non-goal).
- **Follow-ups:** schema evolves via numbered migrations (ADR-0003).
