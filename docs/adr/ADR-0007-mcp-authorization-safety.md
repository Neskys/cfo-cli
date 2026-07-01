# ADR-0007: MCP Authorization & Safety Model

- **Status:** Proposed
- **Date:** 2026-07-01
- **Deciders:** Xavier Potrony, Jarvis

## Context and problem statement

Exposing a local financial database to an AI assistant via Model Context Protocol (MCP) tool-calling introduces security risks, such as prompt injection or erroneous model execution. If the model runs a destructive action (like deleting data or modifying historical transactions) without the user's explicit consent, it can corrupt the user's financial records.

In a classic terminal CLI execution, we can ask for confirmation interactive prompts `[y/N]` (e.g. `cfo budget delete "Q3 2026"`). However, when `cfo` runs headless as an MCP server inside a client like Claude Desktop or Cursor, there is no terminal stdin/stdout available to prompt the user directly. We must decide on a secure authorization model for these tools.

## Decision drivers

- **Security & Data Integrity:** Protect user financial data from corruption or deletion via prompt injection.
- **Ease of Configuration:** Keep setup simple for technical and non-technical users.
- **Utility:** Support the ability to write/add entries when the user explicitly desires it.

## Considered options

1. **Option 1: Full Read-Write by default.** All tools (read and write) are exposed and executable by the model immediately upon connection.
2. **Option 2: Strict Read-Only.** Expose only queries, summaries, and forecasting tools. Do not implement any write/delete tools in the MCP schema.
3. **Option 3: Read-Only by default, with opt-in Read-Write.** Expose write tools but block execution returning an error unless write access is explicitly enabled via the startup flag `--read-write` or in the user's configuration file.

## Decision

We chose **Option 3: Read-Only by default, with opt-in Read-Write**.

The MCP server will register both read and write tools. However, write tools will immediately fail and return an instruction to the model (e.g. *"Error: Write access is disabled for this session."*) unless:
1. The server was started with the `--read-write` command-line flag.
2. The user has explicitly set `"mcp_read_write": true` in `~/.cfo/config.json`.

This ensures that the user is fully protected by default when configuring the server for the first time, while retaining the feature capability of writing entries for advanced users.

## Consequences

- **Positive:**
  - Secure by default. No risk of database mutation on first installation.
  - Transparent error messages: If the model tries to write, it gets a clear response on how the user can enable it.
  - Aligns with the privacy-first, local-first principles of `cfo-cli`.
- **Negative / trade-offs:**
  - Added step: Users who want to use the write functionality must modify their configuration or launch flags.
- **Follow-ups:**
  - Document the setup instructions in the README.
  - Implement a `mcp_read_write` property check in `cfo/core/config.py`.
