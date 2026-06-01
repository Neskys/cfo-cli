# PRD: cfo-cli

- **Status:** Approved (reflects the shipped product through v0.9)
- **Author:** Xavier Potrony
- **Last updated:** 2026-06-01

> Product-facing. The engineering view lives in
> [System Design](../design/SYSTEM_DESIGN.md) and the Tech Specs.

## Problem

Freelancers and small-team operators spend 5–10 hours a month reconciling
budgets, expenses and income in spreadsheets. The available tools sit at two
unhelpful extremes: heavy accounting suites (QuickBooks, Xero) that are overkill
and expensive, or bare spreadsheets that don't forecast, don't handle currencies,
and don't scale with the business. There is no lightweight, **terminal-first,
local-first** option built for solo operators who live in the shell.

## Target users

- **Freelancers** invoicing clients who need to track project profitability.
- **Consultants** (fractional-CFO, legal, tech) juggling multiple engagements.
- **Small startups** wanting financial visibility without enterprise tooling.
- **Developers** who prefer the terminal over spreadsheets and value scriptable,
  git-friendly, offline tools.

## Goals & success metrics

- **Goal:** let a solo operator manage the full money lifecycle — budget, track,
  forecast, report — from the terminal, offline, in minutes per week.
- **Goal:** zero lock-in; data is a single local file the user fully owns.
- **Metrics:** time-to-first-budget < 2 min after install; a monthly close
  (expenses + income + report) achievable in < 10 min; works with no network
  except optional FX/AI.

## Non-goals

- Not a multi-user / team-collaboration platform (single local user).
- Not a bookkeeping/ledger system for accountants (no double-entry, no tax
  filing).
- No cloud sync, no web UI, no mobile app.

## Requirements (shipped)

Prioritised as **Must** for the v0.1–v0.9 product:

- **Budgets** — plan financial periods with categorised line items. *(v0.1)*
- **Expenses** — record spend, compare against budget, see execution %. *(v0.2)*
- **Income** — track sources (recurring or one-off) and entries. *(v0.3)*
- **Forecasting** — project cash flow from trends with scenarios. *(v0.4)*
- **Reports** — export CSV/PDF summaries. *(v0.5)*
- **Multi-currency** — convert and aggregate across currencies. *(v0.6)*
- **AI insights** — natural-language analysis over **aggregated** data, with a
  free local option. *(v0.7–v0.9)*

## User experience

CLI-first: `cfo <group> <action>`. Rich, readable tables in the terminal;
reports are real files on disk. Example monthly flow:

```bash
cfo budget create "2026" --period annual
cfo expense add --category software --amount 49.99 --note "Adobe"
cfo income add --amount 3500 --source-id 1 --invoice-ref INV-001
cfo forecast run --months 6
cfo report full --format pdf --output report.pdf
```

See the [README](../../README.md) for the full command reference.

## Constraints & assumptions

- **Local-first:** SQLite at `~/.cfo/data.db`; config at `~/.cfo/config.json`.
- **Offline by default:** network only for FX rates (cached 24h) and optional AI.
- **Privacy:** AI features send aggregated figures only — never raw transactions.
- **Platform:** Python 3.10+, cross-platform (Linux/macOS/Windows).

## Risks

- **Adoption:** terminal-only narrows the audience → mitigated by being best-in-
  class for that audience, not by chasing GUIs.
- **FX dependency:** third-party rate API → mitigated by 24h cache + offline
  fallback to last known rate.
- **AI cost/trust:** hosted models cost money and see data → mitigated by
  aggregation-only and a free, offline local provider.

## Future direction

Productization toward v1.0 (CI, coverage, PyPI release) is underway. Candidate
features are parked in [IDEAS.md](../IDEAS.md); the largest (an interactive AI
console) has a dedicated [RFC](../rfcs/RFC-0001-interactive-console.md).
