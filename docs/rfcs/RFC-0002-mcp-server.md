# RFC-0002: Model Context Protocol (MCP) Server

- **Status:** Draft
- **Author(s):** Xavier Potrony, Jarvis
- **Created:** 2026-07-01
- **Discussion:** (open a PR/issue to discuss)

## Summary

Add a Model Context Protocol (MCP) server subcommand (`cfo mcp start`) that exposes the local SQLite database to AI clients (like Claude Desktop, Cursor, or Zed) via standard input/output (stdio). This allows users to query, analyze, and manage their finances using natural language in their primary workspace without leaving their editor or browser.

## Motivation

Today, `cfo-cli` is a powerful local-first CLI tool, but it requires users to remember specific terminal command structures and flags. Manual data entry is also a known friction point for financial tracking.

In 2026, the Model Context Protocol (MCP) has emerged as the standard way to hook local databases and APIs into LLM workflows. Exposing `cfo-cli`'s capabilities as an MCP server:
1. Resolves the CLI learning curve: Users can ask questions like "How much did I spend on software last quarter?" or "Add an expense of 49.99 for Adobe under Software" in plain language.
2. Combines local-first privacy with AI utility: Your financial data remains local in SQLite, but you get the productivity of an integrated AI accountant.
3. High positioning value: There are very few local-first financial MCP servers on GitHub in Q2 2026, creating a strong differentiator for the project and increasing our chance for the OpenAI Codex for OSS sponsorship.

## Goals / Non-goals

- **Goals:**
  - Build a compliant MCP server executing over stdin/stdout.
  - Expose the core services (Expenses, Income, Budgets, Forecast) as MCP tools.
  - Build a security system where writes (mutations) are safe and disabled by default.
  - Support easy configuration for Claude Desktop and Cursor.
- **Non-goals:**
  - Building a web server or hosting financial data in the cloud.
  - Replacing the standard CLI (the CLI remains the primary interface).
  - Designing a graphical user interface (GUI) or TUI dashboard.

## Proposal

Implement an MCP server that uses the official Anthropic Python MCP SDK. We will add a new CLI command group `cfo mcp` with a subcommand `start` to launch the server:

```bash
cfo mcp start [--read-write]
```

When started, it runs an HTTP-free stdio JSON-RPC server. It defines a tool list representing the service layer functions:

- **Read Tools:**
  - `expense_list` (date range, category filters)
  - `expense_summary` (aggregates, budget comparison)
  - `income_list` / `income_summary`
  - `budget_list` / `budget_view`
  - `forecast_run` (cash flow projection)
- **Write Tools** (active only if `--read-write` or enabled in config):
  - `expense_add`
  - `income_add`
  - `budget_create`

To protect data, the server defaults to **Read-Only** mode. Mutation tools will return an error explaining that write access is disabled unless `--read-write` is provided or `"mcp_read_write": true` is set in `~/.cfo/config.json`.

## Alternatives considered

- **Do nothing:** Keep `cfo-cli` as a pure terminal command. Rejected: Leaves the best integration pathway for developer-centric users unbuilt.
- **Implement a custom terminal REPL (`cfo chat` - RFC-0001):** Keep the user in the terminal using a custom conversational loop. While interesting, it requires a lot of UI maintenance (`prompt_toolkit`), whereas MCP integrates directly with the chat interfaces developers already use (Claude Desktop, Cursor). The MCP server has a higher leverage-to-effort ratio. We decide to prioritize MCP and keep `cfo chat` parked.
- **Local TUI (Terminal User Interface):** Build a keyboard-driven visual dashboard (using a framework like Textual). This is a useful but different UX approach; it could co-exist later but does not solve the natural language query requirement.

## Risks & open questions

- **Tool-calling accuracy with local models:** Small local models (like Gemma 4 via Ollama) might struggle with tool schema execution, which is a known limitation. We will document that hosted models (Claude, OpenAI) are recommended for write operations.
- **DB concurrency:** Since `cfo-cli` is single-process, multiple concurrent queries from Cursor/Claude might cause SQLite locks. However, since SQLite is extremely fast and there is only a single user, this is highly unlikely to be a bottleneck.
- **Security boundary:** Can a user accidentally delete their whole database via prompt injection? We must ensure the write tools do not support raw SQL queries and are strictly limited to structured model actions (validated by Pydantic models).

## Impact

- **Dependencies:** Adds `mcp` (Model Context Protocol Python SDK) as an optional extra `cfo-cli[mcp]`.
- **Backward compatibility:** None. The core CLI and database schema remain unchanged.
- **Security:** Safe read-only default. No secrets or tokens are exposed to the LLM.

## Decision

Pending review. If accepted, implementation is specified in [TS-0002](../specs/TS-0002-mcp-server.md).
