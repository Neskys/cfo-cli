# TS-0000: <feature> — Technical Specification

- **Status:** Draft <!-- Draft | In review | Approved | Implemented -->
- **Author(s):** <name>
- **Created:** YYYY-MM-DD
- **Related:** RFC-XXXX, ADR-XXXX

## Overview

What we're building, in one paragraph. Link the RFC that decided *whether*; this
doc covers *how*.

## Requirements

- **Functional:** what it must do (bullet list, testable).
- **Non-functional:** performance, offline behaviour, privacy, error handling.

## Design

How it works. Modules touched, data flow, key types/functions. Use a Mermaid
diagram if it helps.

### Affected components

| Layer | File(s) | Change |
|---|---|---|
| CLI | `cfo/cli/<group>.py` | … |
| Service | `cfo/services/<name>.py` | … |
| Storage | `cfo/storage/migrations.py` | new migration N (if any) |

### Data model / schema changes

New tables/columns and the migration number. Never edit existing migrations.

## API / CLI surface

Exact commands, flags, defaults, and example output.

## Error handling & validation

Typed errors raised, validation rules, exit codes.

## Testing plan

What `tests/test_<module>.py` will cover; how external calls are mocked.

## Rollout & docs

Version bump, CHANGELOG entry, README/CLAUDE.md updates, any new dependency
(added to `pyproject.toml` + documented).

## Open questions
