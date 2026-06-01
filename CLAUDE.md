# CLAUDE.md — cfo-cli

This file provides context to Claude Code when working on this repository.

## What This Is

**cfo-cli** is an open-source Python CLI tool for freelancers, consultants, and small teams to manage budgets, track expenses, track income, forecast cash flow, export reports, work in multiple currencies, and (soon) get AI-powered financial insights — all from the terminal.

- Local-first: SQLite at `~/.cfo/data.db`, no cloud dependency
- Config (non-DB): `~/.cfo/config.json` (e.g. `base_currency`)
- Stack: Python 3.10+, typer, rich, pydantic, sqlite3, reportlab (PDF), httpx (FX rates)
- Repo: https://github.com/Neskys/cfo-cli
- Current version: **0.7.0** (v0.1–v0.7 shipped — full roadmap complete)

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
│   └── ai.py               # aggregated context + Claude calls (prompt caching)
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

# AI insights (v0.7) — needs: pip install 'cfo-cli[ai]'
cfo ai config --api-key sk-...
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
| `anthropic` *(extra `[ai]`)* | v0.7 | Claude integration (lazy-imported; install via `pip install 'cfo-cli[ai]'`) |

Dev extras (`[dev]`): `pytest`, `pytest-cov`, `ruff`.

---

## Roadmap

### ✅ Shipped

- **v0.1 — Budget planning**
- **v0.2 — Expense tracking** — migrations system, `expenses` activated, `summary` with % of total and budget execution (over-budget shown in red)
- **v0.3 — Income tracking** — sources + entries; `income_service.get_monthly_average(source_id, months=6)` consumed by forecast
- **v0.4 — Cash flow forecasting** — `run()` projects recurring income (6-mo avg) vs expenses (3-mo avg) with base/optimist/pessimist factors; custom scenarios + adjustments persisted
- **v0.5 — Reports (CSV + PDF)** — `datasets` from services → `csv_writer` / `pdf_writer` (cover → tables → page numbers)
- **v0.6 — Multi-currency** — `exchange_rates` cache (24h TTL, offline fallback), `convert`/`rates`/`set-base`, `--in-base-currency` on list/summary
- **v0.7 — AI Insights (Claude)** — `ai config`/`analyze`/`anomalies`/`suggest` via the `anthropic` SDK (`[ai]` extra, lazy-imported). Sends **aggregated data only** (built from the summary services), **prompt-caches** the financial-context block, default model `claude-sonnet-4-6`, API key in `~/.cfo/config.json`. Tests mock the Anthropic client — no live calls.

### 🎉 Roadmap complete

All planned versions (v0.1–v0.7) have shipped. Future work is open-ended — see GitHub issues.

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
# Install in editable mode
pip install -e ".[dev]"

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
