# TS-0002: Model Context Protocol (MCP) Server — Technical Specification

- **Status:** Draft
- **Author(s):** Xavier Potrony, Jarvis
- **Created:** 2026-07-01
- **Related:** [RFC-0002](../rfcs/RFC-0002-mcp-server.md), [ADR-0007](../adr/ADR-0007-mcp-authorization-safety.md)

## Overview

Exposes the `cfo` services as tools to AI assistants via the Model Context Protocol (MCP). It wraps existing services inside an stdio-based JSON-RPC server. This document specifies the technical design, dependencies, and implementation details.

## Requirements

### Functional

1. **Stdio Server:** `cfo mcp start` runs a persistent process that reads JSON-RPC messages from `stdin` and writes to `stdout`.
2. **Tool Coverage:**
   - **Read-only tools:** `expense_list`, `expense_summary`, `income_list`, `income_summary`, `budget_list`, `budget_view`, `forecast_run`, `currency_convert`.
   - **Write tools:** `expense_add`, `income_add`, `budget_create`.
3. **Write Protection:** Write tools fail immediately and return an error message unless:
   - `--read-write` was passed to `cfo mcp start`.
   - `"mcp_read_write": true` is configured in `~/.cfo/config.json`.
4. **Stdout Isolation:** All logging, debug messages, and errors must go to `stderr` to avoid corrupting the stdio transport channel (which requires clean JSON-RPC stdout output).

### Non-functional

- **Minimal Dependencies:** The `mcp` SDK is optional. It is added to a `[mcp]` extra in `pyproject.toml`.
- **Zero-Config Database Access:** The server automatically targets the user's active database at `~/.cfo/data.db`.
- **Performance:** Instantaneous startup. No network calls during initialization.

## Design

We will use the official Python `mcp` SDK (from Anthropic), utilizing the high-level `FastMCP` wrapper. `FastMCP` auto-generates tool schemas from Python function signatures, docstrings, and type hints.

```
                  ┌───────────────────────────┐
                  │       cfo mcp start       │
                  └─────────────┬─────────────┘
                                │
                                ▼
                  ┌───────────────────────────┐
                  │    FastMCP("cfo-mcp")     │
                  └─────────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │ (Tool)              │ (Tool)              │ (Tool)
          ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ expense_summary  │  │   forecast_run   │  │   expense_add    │
└─────────┬────────┘  └─────────┬────────┘  └─────────┬────────┘
          │                     │                     │
          │                     │                     │ check config
          │                     │                     ▼
          │                     │            [Write Allowed?]
          │                     │             /            \
          │                     │           No             Yes
          │                     │           /                \
          ▼                     ▼          ▼                  ▼
┌───────────────────────────────────────────────┐   ┌──────────────────┐
│             cfo/services/ modules             │   │   Return Error   │
└───────────────────────────────────────────────┘   └──────────────────┘
```

### Affected components

| Layer | File(s) | Change |
|---|---|---|
| CLI | `cfo/cli/main.py` | Import and add the `mcp.app` subcommand group. |
| CLI | `cfo/cli/mcp.py` (new) | Implement `cfo mcp start` and `cfo mcp config` Typer commands. |
| Service | `cfo/services/mcp_server.py` (new) | Initialize `FastMCP`, register tools with signatures and validation, handle the Stdio loop. |
| Core | `cfo/core/config.py` | Add `get_mcp_read_write()` and `set_mcp_read_write()`. |
| Metadata | `pyproject.toml` | Add `mcp` dependency to the optional `[mcp]` section. |

## Detailed Tool Specifications

Each registered tool will map directly to the corresponding service function, carrying strict type annotations.

### Read Tools

- **`expense_summary(group_by: str = "category", date_from: str = None, date_to: str = None, budget: str = None)`**
  - Maps to: `cfo.services.expense.summary`
  - Returns: Aggregated JSON output representing expenses.
- **`forecast_run(months: int = 6, scenario: str = "base")`**
  - Maps to: `cfo.services.forecast.run`
  - Returns: A JSON dictionary with the projected months, cash balance, and monthly averages.
- **`budget_list()`**
  - Maps to: `cfo.services.budget.list_budgets` (or helper function)
  - Returns: A list of budgets.
- **`budget_view(budget_name: str)`**
  - Maps to: `cfo.services.budget.get_budget` (along with its lines)
- **`expense_list(category: str = None, date_from: str = None, date_to: str = None, limit: int = 50)`**
  - Maps to: `cfo.services.expense.list_expenses`
- **`income_list(source_id: int = None, date_from: str = None, date_to: str = None, limit: int = 50)`**
  - Maps to: `cfo.services.income.list_income_entries`
- **`income_summary(group_by: str = "source", date_from: str = None, date_to: str = None)`**
  - Maps to: `cfo.services.income.summary`

### Write Tools

Before executing, write tools check `get_mcp_read_write()` or the CLI `--read-write` state. If false, they raise an `PermissionError("Write access is disabled for this MCP session.")`.

- **`expense_add(category: str, amount: float, currency: str = "EUR", date: str = None, budget: str = None, note: str = None)`**
  - Maps to: `cfo.services.expense.add_expense`
- **`income_add(amount: float, source_id: int, currency: str = "EUR", date: str = None, invoice_ref: str = None, note: str = None)`**
  - Maps to: `cfo.services.income.add_income_entry`
- **`budget_create(name: str, period: str = "monthly")`**
  - Maps to: `cfo.services.budget.create_budget`

## API / CLI surface

```bash
# Start the stdio MCP server
cfo mcp start [--read-write]

# Configure the mcp options
cfo mcp config --read-write
cfo mcp config --read-only
```

## Error handling & validation

- If the `mcp` SDK is not installed when running `cfo mcp start`, raise a clear `ImportError` instructing the user to install the extra: `pip install -e '.[mcp]'`.
- Validate all arguments inside tool calls using Pydantic or the existing service exceptions. If a service raises `ExpenseError`, catch it and return a descriptive text block to the model so it can correct its input.
- Database access errors are caught and logged to `stderr`.

## Testing plan

We will create `tests/test_mcp.py`.
- **Initialization tests:** Ensure that if `mcp` is not installed, running the command exits with code 1 and prints the correct installation instructions.
- **Protocol tests:** Mock `mcp.server.fastmcp.FastMCP` and verify that all tools are registered with correct arguments.
- **Safety tests:**
  - Mock `get_mcp_read_write` to return `False`. Run write tools and assert they return an error/permission denied message.
  - Mock `get_mcp_read_write` to return `True`. Run write tools and verify they invoke the corresponding service functions.
- **Read-only tests:** Run read-only tools and verify they correctly return the mock database outputs.

## Rollout & docs

1. Add `"mcp>=0.1.0"` to `pyproject.toml` optional dependencies.
2. Implement code on branch `jarvis/feat-mcp`.
3. Add a section to the `README.md` explaining how to configure the server in `claude_desktop_config.json` and Cursor.
4. Update `CLAUDE.md` to document the new `cfo mcp` CLI group.
5. Create a new release `0.10.0` or `1.0.0-rc1` including this feature.
