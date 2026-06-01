# Future ideas

A backlog of *possible* future features for cfo-cli. These are **not committed
roadmap items** — they capture ideas and rough designs so they aren't lost.
Anything here should still go through the normal process (feature branch, tests,
CLAUDE.md updates) if/when it's picked up.

---

## Interactive AI console (Claude Code-style REPL)

**Status:** specified · **Size:** large · **Best after:** v1.0

> Promoted to formal docs: see **[RFC-0001](rfcs/RFC-0001-interactive-console.md)**
> (whether / options) and **[TS-0001](specs/TS-0001-interactive-console.md)**
> (how to build). The summary below is kept for context.

Turn cfo-cli from a one-shot CLI (`cfo <cmd>` runs and exits) into an optional
**interactive, conversational console** — a `cfo chat` / `cfo shell` that stays
open, understands natural language, and performs actions on your finances by
calling the existing services as tools. Conceptually similar to how Claude Code
drives a terminal.

### Why it's feasible
The building blocks already exist in the repo:

- **`cfo/services/*`** are clean, typed functions — effectively a ready-made set
  of "tools" an agent can call.
- **Pydantic models** (`cfo/core/models.py`) can generate the tool JSON schemas
  almost for free.
- **`cfo/services/ai_providers.py`** already adapts the Anthropic and OpenAI
  SDKs, both of which support native tool/function calling.
- `rich` (rendering) and the local-first SQLite store are already in place.

Nothing requires new infrastructure or cloud services — only standard,
well-documented patterns. The hard parts are *design* decisions, not technical
feasibility.

### What's missing (the structural pieces)
1. **A REPL loop** — a persistent input loop (likely a new dependency such as
   `prompt_toolkit` for history, multiline input, autocompletion).
2. **An agent loop with tool-calling** — model → pick tool → execute service →
   feed result back → repeat until the task is done.
3. **A tool registry** — maps each model tool-call to the right service function.
4. **Permission / confirmation flow** — mandatory confirmation before any
   *write* action (add/edit/delete), echoing the existing `--yes` convention.
5. **Session memory** — keep conversation history across turns (with prompt
   caching to control cost).
6. **Streaming output** — render tokens as they arrive (`rich.Live`).
7. **In-console slash commands** — `/help`, `/clear`, `/budget`, etc.

### Open design decisions
- **Data access vs privacy.** Today the AI only ever sees *aggregated* figures.
  An agentic console would need controlled read tools over the DB — how much
  granular access to grant while honouring the local-first/privacy principle.
- **Destructive actions.** Guardrails on what the agent may mutate or delete.

### Suggested phased plan
1. Basic REPL + internal slash-commands (no AI yet).
2. Agent loop with tool-calling over **read-only** tools (query, summarise,
   forecast).
3. **Write** tools (add expense, create budget…) gated behind confirmation.
4. Session memory + streaming.

### Caveats
- Works best with **Claude / OpenAI**; tool-calling with the small **local**
  model (Gemma via Ollama) is less reliable, so the free/offline experience
  would be degraded for complex agentic tasks.
- Adds a new dependency (`prompt_toolkit`) and would be the largest feature so
  far — best tackled **after** the v1.0 release is out.

### Implementation notes (to respect project rules)
- Ship it as a new command group: `cfo/cli/chat.py` (one file per group).
- Put the agent loop / tool registry in the service layer
  (`cfo/services/agent.py` or similar); the CLI file only wires input/output.
- Add `tests/test_chat.py` with the provider SDKs and tool dispatch mocked — no
  live calls, same as `tests/test_ai.py`.
