# CLAUDE.md — cfo-cli

This file provides context to Claude Code when working on this repository.

## What This Is

**cfo-cli** is an open-source Python CLI tool for freelancers, consultants, and small teams to manage budgets, track expenses, track income, forecast cash flow, export reports, work in multiple currencies, and (soon) get AI-powered financial insights — all from the terminal.

- Local-first: SQLite at `~/.cfo/data.db`, no cloud dependency
- Config (non-DB): `~/.cfo/config.json` (e.g. `base_currency`)
- Stack: Python 3.10+, typer, rich, pydantic, sqlite3, reportlab (PDF), httpx (FX rates)
- Repo: https://github.com/Neskys/cfo-cli
- Current version: **0.9.0** (v0.1–v0.7 roadmap complete; v0.8 adds OpenAI; v0.9 adds a free local provider — Gemma 4 via Ollama)

---

## Project Structure

```
cfo/
├── cli/                    # typer sub-apps (one file per command group)
│   ├── main.py             # registers all sub-apps, entrypoint, `version`
│   ├── budget.py           # ✅ v0.1
│   ├── expense.py          # ✅ v0.2
│   ├── income.py           # ✅ v0.3 (income + nested `source` sub-app)
│   ├── forecast.py         # ✅ v0.4 (run + nested `scenario` sub-app)
│   ├── report.py           # ✅ v0.5
│   ├── currency.py         # ✅ v0.6
│   └── ai.py               # ✅ v0.7
├── core/
│   ├── models.py           # pydantic models + VALID_* constants
│   ├── config.py           # ~/.cfo/config.json read/write (base_currency)
│   └── dates.py            # window_cutoff() — rolling-average window helper
├── services/               # all DB logic lives here; CLI only parses + calls
│   ├── expense.py          # expense CRUD + summary + get_monthly_average
│   ├── income.py           # income entry CRUD + summary + get_monthly_average
│   ├── income_source.py    # income source CRUD
│   ├── forecast.py         # run() projection + scenario factors
│   ├── forecast_scenario.py# custom scenario + adjustment CRUD
│   ├── currency.py         # FX fetch/cache/convert + base-currency helpers
│   ├── ai.py               # aggregated context + orchestration (provider-agnostic)
│   └── ai_providers.py     # Anthropic / OpenAI completion adapters (lazy SDKs)
├── formatters/
│   └── tables.py           # reusable Rich table builders
├── reports/
│   ├── datasets.py         # normalize report data from services
│   ├── csv_writer.py       # CSV export
│   └── pdf_writer.py       # PDF export (reportlab, imported lazily)
└── storage/
    ├── database.py         # connection, init_db(), base schema
    └── migrations.py       # numbered migrations, auto-applied by init_db()

tests/
├── test_budget.py
├── test_expense.py
├── test_income.py
├── test_forecast.py
├── test_report.py
├── test_currency.py
└── test_ai.py
```

---

## Current DB Schema

Base tables (created in `storage/database.py`):

```sql
budgets        (id, name, period, created_at)
budget_lines   (id, budget_id, category, amount, currency, created_at)
expenses       (id, budget_id, category, amount, currency, date, note, created_at)
```

Added via migrations (`storage/migrations.py`):

```sql
-- 001  indexes on expenses(date), expenses(category), expenses(budget_id)
-- 002
income_sources       (id, name, client, is_recurring, recur_every, created_at)
income_entries       (id, source_id, amount, currency, date, invoice_ref, note, created_at)
-- 003
forecast_scenarios   (id, name, period_from, period_to, created_at)
forecast_adjustments (id, scenario_id, type, category, factor, absolute_delta, note, created_at)
-- 004
exchange_rates       (base_currency, quote_currency, rate, fetched_at)  -- PK (base, quote)

schema_migrations    (version, name, applied_at)  -- tracks applied migrations
```

---

## Implemented Commands (v0.1–v0.6)

```bash
# Budgets (v0.1)
cfo budget create "Q3 2026" --period quarterly   # monthly|quarterly|annual
cfo budget add-line "Q3 2026" --category salaries --amount 5000 --currency EUR
cfo budget view "Q3 2026"
cfo budget list
cfo budget delete "Q3 2026" [--yes]

# Expenses (v0.2)
cfo expense add --category salaries --amount 4800 [--currency EUR] [--date YYYY-MM-DD] [--budget "Q3 2026"] [--note "text"]
cfo expense list [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--category X] [--limit 50] [--in-base-currency]
cfo expense view <ID>
cfo expense edit <ID> [--amount X] [--category X] [--date X] [--note X]
cfo expense delete <ID> [--yes]
cfo expense summary [--from X] [--to X] [--group-by category|month] [--budget NAME] [--in-base-currency]

# Income (v0.3)
cfo income source add --name "Acme Corp" [--client "Acme"] [--recurring] [--recur-every monthly]
cfo income source list / delete <ID> [--yes]
cfo income add --amount 3500 [--source-id 1] [--currency EUR] [--date X] [--invoice-ref "INV-042"] [--note X]
cfo income list [--from X] [--to X] [--source-id N] [--limit 50] [--in-base-currency]
cfo income view <ID> / edit <ID> / delete <ID> [--yes]
cfo income summary [--group-by source|month] [--from X] [--to X] [--in-base-currency]

# Forecast (v0.4)
cfo forecast run [--months 6] [--scenario base|optimist|pessimist]
cfo forecast scenario create --name "Best case" --from 2026-07-01 --to 2026-12-31
cfo forecast scenario add-adjustment <ID> --type income|expense [--factor 1.2] [--absolute-delta N] [--category X] [--note X]
cfo forecast scenario list / view <ID> / delete <ID> [--yes]

# Reports (v0.5)
cfo report expenses|income|cashflow|full [--from X] [--to X] [--format csv|pdf] [--output PATH]

# Currency (v0.6)
cfo currency convert --amount 1000 --from USD --to EUR
cfo currency rates [--base EUR] [--refresh]
cfo currency set-base EUR

# AI insights (v0.7; multi-provider since v0.8; free local provider since v0.9)
cfo ai config [--api-key sk-...] [--provider anthropic|openai|local] [--model NAME] [--base-url URL]
cfo ai set-provider anthropic|openai|local   # 'local' = Gemma 4 via Ollama, no key, no cost
cfo ai analyze [--focus expenses|income|cashflow|all] [--from X] [--to X]
cfo ai anomalies [--threshold 2.0] [--from X] [--to X]
cfo ai suggest [--goal reduce-expenses|increase-cashflow|optimize-categories] [--from X] [--to X]

cfo version
```

---

## Dependencies

Declared in `pyproject.toml`. **Add new ones here and document them in this section.**

| Dependency | Since | Why |
|---|---|---|
| `typer[all]`, `rich` | v0.1 | CLI framework + terminal rendering |
| `pydantic` | v0.1 | data models |
| `pandas` | v0.1 | (declared from the start) |
| `reportlab` | v0.5 | PDF report generation (imported lazily so CSV works without it) |
| `httpx` | v0.6 | fetch FX rates from open.er-api.com |
| `anthropic` *(extra `[ai]`)* | v0.7 | Claude integration (lazy-imported; `pip install 'cfo-cli[ai]'`) |
| `openai` *(extra `[openai]`)* | v0.8 | OpenAI integration (lazy-imported; `pip install 'cfo-cli[openai]'`) |

Dev extras (`[dev]`): `pytest`, `pytest-cov`, `ruff`.
Docs extra (`[docs]`): `mkdocs-material` (builds the documentation site; see below).

---

## Roadmap

### ✅ Shipped

- **v0.1 — Budget planning**
- **v0.2 — Expense tracking** — migrations system, `expenses` activated, `summary` with % of total and budget execution (over-budget shown in red)
- **v0.3 — Income tracking** — sources + entries; `income_service.get_monthly_average(source_id, months=6)` consumed by forecast
- **v0.4 — Cash flow forecasting** — `run()` projects recurring income (6-mo avg) vs expenses (3-mo avg) with base/optimist/pessimist factors; custom scenarios + adjustments persisted
- **v0.5 — Reports (CSV + PDF)** — `datasets` from services → `csv_writer` / `pdf_writer` (cover → tables → page numbers)
- **v0.6 — Multi-currency** — `exchange_rates` cache (24h TTL, offline fallback), `convert`/`rates`/`set-base`, `--in-base-currency` on list/summary
- **v0.7 — AI Insights (Claude)** — `ai config`/`analyze`/`anomalies`/`suggest` via the `anthropic` SDK (`[ai]` extra, lazy-imported). Sends **aggregated data only** (built from the summary services), **prompt-caches** the financial-context block, default model `claude-sonnet-4-6`, API key in `~/.cfo/config.json`. Tests mock the client — no live calls.

### Beyond the roadmap

- **v0.8 — Multi-provider AI** — OpenAI alongside Claude, both via **API key** (no OAuth — the inference APIs are key-based). `ai_providers.py` adapts each SDK; `ai config --provider`, `ai set-provider`, per-provider key/model in `~/.cfo/config.json`. Anthropic uses explicit `cache_control`; OpenAI relies on automatic prefix caching (stable context sent first either way). Defaults: anthropic→`claude-sonnet-4-6`, openai→`gpt-4o`.
- **v0.9 — Free local provider** — `local` provider runs **Gemma 4 via Ollama** at no cost, offline, **no API key**. It reuses the OpenAI-compatible adapter (`openai` SDK) pointed at a configurable `base_url` (default `http://localhost:11434/v1`), default model `gemma4`. No new pip dependency — needs the `[openai]` extra plus a separately-installed Ollama runtime. `KEY_REQUIRED` excludes `local`; `_complete` injects a placeholder key. Local servers have no server-side prompt caching (cost is zero anyway).

### Toward v1.0 (productization)

With the feature roadmap complete, work shifted to hardening for a public release
(see the *Continuous Integration & Releases* section below):

- **CI** — `ci.yml` runs ruff + pytest on Python 3.10/3.11/3.12 for every PR/push.
- **Coverage** — raised to **94%**; every `cfo/services/*` module is at 100%.
- **Release pipeline** — `release.yml` publishes to PyPI via Trusted Publishing on a `v*.*.*` tag. License metadata modernised to PEP 639.

Further feature work is open-ended — see GitHub issues.

Candidate features that are *not* committed yet are parked in
[`docs/IDEAS.md`](docs/IDEAS.md) (e.g. an interactive AI console / `cfo chat`
REPL that drives the existing services as agent tools).

---

## Coding Rules

1. **One file per command group** in `cfo/cli/` — never mix two domains
2. **Service layer** in `cfo/services/` handles all DB logic — CLI files only parse args and call services
3. **Keep files small (~150 lines)** — split into two if needed (a few mature service modules slightly exceed this for cohesion; new code should aim under)
4. **No new dependencies** without adding to `pyproject.toml` and documenting in the Dependencies section above
5. **Surgical changes** — only modify what the task requires
6. **Tests required** for every new command group (`tests/test_<module>.py`)
7. **Validation** — amounts must be > 0; currencies validated against `VALID_CURRENCIES`; dates are `YYYY-MM-DD`; `--date` defaults to today
8. **Services raise typed errors** (e.g. `ExpenseError`, `IncomeError`, `CurrencyError`, `ForecastError`, `ReportError`); CLIs catch them and exit cleanly

---

## Dev Setup

```bash
# Install in editable mode (use the extras you need)
pip install -e ".[dev]"             # core + test/lint tooling
pip install -e ".[dev,ai,openai]"   # also pull the AI SDKs (Anthropic + OpenAI/Ollama)

# Run CLI
cfo --help

# Run tests
pytest tests/ -v

# Lint
ruff check cfo/
```

Notes:
- Tests isolate the database/config by setting `HOME` to a `tmp_path`.
- Network is never hit in tests: FX rates are mocked (`currency._fetch_rates`) or the cache is pre-seeded.
- **Claude Code on the web:** `.claude/hooks/session-start.sh` (a `SessionStart` hook, web-only) runs `pip install -e ".[dev,ai,openai]"` so tests, linters, and every AI provider work from the first prompt. It also prints the active git branch as a reminder (see Git Workflow below).

---

## Git Workflow (branch discipline)

This repo is developed on a **feature branch per task**, then merged into `main`.
To avoid accidentally leaving uncommitted work — or commits — on `main`:

1. **Always develop and commit on the feature branch**, never directly on `main`.
2. After merging a feature into `main` and pushing, **switch back to the feature
   branch** (`git checkout <feature-branch>`) before continuing — `git merge`
   leaves you on `main`, which is the usual cause of stray work landing there.
3. Before any commit, confirm the branch with `git rev-parse --abbrev-ref HEAD`.
   The SessionStart hook echoes it at startup as a first-line reminder.
4. Keep `main` in sync with `origin/main`; merge with `--no-ff` so each version
   (v0.x) is a clear merge commit.

---

## Continuous Integration & Releases

Three GitHub Actions workflows live in `.github/workflows/`:

- **`ci.yml`** — on every push to `main` and every PR: install with all extras,
  `ruff check cfo/ tests/`, and `pytest` across Python 3.10/3.11/3.12.
- **`release.yml`** — on pushing a `v*.*.*` tag: re-runs the test gate, verifies
  the tag matches `cfo.__version__`, builds the sdist+wheel, `twine check`s them,
  and publishes to **PyPI via Trusted Publishing (OIDC — no API token stored)**.
- **`docs.yml`** — on push to `main` touching `docs/**`/`mkdocs.yml`: builds the
  MkDocs (Material) site with `mkdocs build --strict` and deploys to GitHub Pages.
  Requires Pages source set to "GitHub Actions" (one-time, in repo Settings).

To cut a release: bump `version` in both `pyproject.toml` **and** `cfo/__init__.py`
(they must match — the workflow enforces it), commit, then
`git tag vX.Y.Z && git push origin vX.Y.Z`. A PyPI version is permanent once
published. First-time setup requires registering the trusted publisher on PyPI
and creating a `pypi` GitHub Environment (steps are documented in `release.yml`).

License metadata follows **PEP 639**: `license = "MIT"` + `license-files`
(emitted as `License-Expression`), with no `License ::` classifier.

Engineering & product documentation lives in [`docs/`](docs/) (PRD, RFCs, ADRs,
Tech Specs, System Design, runbooks, post-mortems, glossary) — see
[`docs/README.md`](docs/README.md) for what each type is and when to use it.
Preview the site locally with `pip install -e ".[docs]" && mkdocs serve`.

---

## Migrations Pattern

From v0.2 onwards, all schema changes go through `cfo/storage/migrations.py`.
Each migration is a numbered function. `init_db()` auto-applies pending ones and
records them in `schema_migrations`:

```python
# cfo/storage/migrations.py
MIGRATIONS = {
    1: ("Add expense indexes", migration_001),
    2: ("Add income tables", migration_002),
    3: ("Add forecast tables", migration_003),
    4: ("Add exchange rates table", migration_004),
    # next: 5: (...)
}
```

Never edit existing migrations — always add a new numbered one.
