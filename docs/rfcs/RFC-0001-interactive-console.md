# RFC-0001: Interactive AI console (`cfo chat`)

- **Status:** Draft
- **Author(s):** Xavier Potrony
- **Created:** 2026-06-01
- **Discussion:** (open a PR/issue to discuss)

## Summary

Add an optional interactive, conversational console — `cfo chat` (a.k.a.
`cfo shell`) — that stays open, understands natural language, and performs
actions on the user's finances by calling the existing services as **agent
tools**. Conceptually similar to how an agentic terminal (e.g. Claude Code)
drives a workspace.

## Motivation

Today cfo-cli is a one-shot CLI: each command runs and exits, and the AI features
are read-only analysis over aggregated data. Users who don't remember exact flags
would benefit from describing intent in plain language ("how much did I spend on
software last quarter?", "add a 49.99 software expense for Adobe") and having the
tool do it. This lowers the barrier for non-power-users while keeping everything
local-first.

Doing nothing is acceptable — the CLI works — but the interactive mode is the
single biggest UX lever left.

## Goals / Non-goals

- **Goals:** a persistent REPL; natural-language → action via tool-calling over
  existing services; safe writes behind confirmation; works with hosted providers.
- **Non-goals:** replacing the classic CLI (it stays the primary interface);
  multi-user; a GUI; sending raw data to the cloud beyond what the user approves.

## Proposal

A new command group `cfo chat` that:

1. Opens a REPL (history, multiline, autocomplete).
2. On each user turn, sends the conversation + a **tool catalogue** (the service
   functions) to the configured AI provider.
3. Executes the tool calls the model returns, **confirming** any write, and feeds
   results back until the turn completes.
4. Streams the assistant's reply.

Read tools (query/summarise/forecast) are always available; write tools
(add/edit/delete) require explicit confirmation.

## Alternatives considered

- **Do nothing** — keep the one-shot CLI. Rejected: leaves the biggest UX gain on
  the table.
- **A natural-language *parser* that maps phrases to existing commands** (no LLM
  tool-calling). Rejected: brittle, reinvents intent parsing the SDKs already do.
- **A TUI dashboard** (forms/menus, no AI). Reasonable but a different product;
  could co-exist later. Out of scope here.

## Risks & open questions

- **Data access vs privacy:** read tools imply granting the model controlled
  access to query the DB — how much, and how to keep it aligned with the
  aggregated-only stance of ADR-0004.
- **Destructive actions:** guardrails and confirmation UX.
- **Local model quality:** tool-calling with small local models (Gemma/Ollama) is
  less reliable than with hosted ones.

## Impact

- New dependency (`prompt_toolkit`) and a new command group + service.
- New `tests/test_chat.py` (SDKs and tool dispatch mocked).
- Largest feature so far → best after v1.0.

## Decision

Pending review. If accepted, implementation is specified in
[TS-0001](../specs/TS-0001-interactive-console.md).
