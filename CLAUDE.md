# CLAUDE.md — cfo-cli

This file provides context to Claude Code when working on this repository.

## What This Is

**cfo-cli** is an open-source Python CLI tool for freelancers, consultants, and small teams to manage budgets, track expenses, forecast cash flow, and get AI-powered financial insights — all from the terminal.

- Local-first: SQLite at `~/.cfo/data.db`, no cloud dependency
- Stack: Python 3.10+, typer, rich, pydantic, sqlite3
- Repo: https://github.com/Neskys/cfo-cli

---

## Project Structure

```
cfo/
├── cli/           # typer sub-apps (one file per command group)
│   ├── main.py    # registers all sub-apps, entrypoint
│   ├── budget.py  # ✅ implemented
│   ├── expense.py # 🔜 v0.2 — stub only
│   ├── forecast.py# 🔜 v0.3 — stub only
│   ├── report.py  # 🔜 v0.4 — stub only
│   └── ai.py      # 🔜 v0.5 — stub only
├── core/
│   └── models.py  # pydantic models: Budget, BudgetLine, Expense
├── storage/
│   └── database.py# SQLite connection, init_db(), schema
└── reports/       # future: CSV/PDF generators

tests/
└── test_budget.py # pytest tests for budget commands
```

---

## Current DB Schema (v0.1)

```sql
budgets       (id, name, period, created_at)
budget_lines  (id, budget_id, category, amount, currency, created_at)
expenses      (id, budget_id, category, amount, currency, date, note, created_at)
```

The `expenses` table exists but is unused — it will be activated in v0.2.

---

## Implemented Commands (v0.1)

```bash
cfo budget create "Q3 2026" --period quarterly   # monthly|quarterly|annual
cfo budget add-line "Q3 2026" --category salaries --amount 5000 --currency EUR
cfo budget view "Q3 2026"
cfo budget list
cfo budget delete "Q3 2026" [--yes]
cfo version
```

---

## Roadmap

### v0.2 — Expense Tracking (next)

**Goal:** activate the `expenses` table and build the full expense module.

New files to create:
- `cfo/storage/migrations.py` — numbered migrations system (apply on `init_db()`)
- `cfo/services/__init__.py`
- `cfo/services/expense.py` — CRUD logic (keep under 150 lines)
- `cfo/cli/expense.py` — replace the stub with real typer commands
- `cfo/formatters/__init__.py`
- `cfo/formatters/tables.py` — reusable Rich table helpers
- `tests/test_expense.py`

DB changes: add `schema_migrations` table + indexes on `expenses`.

Commands to implement:
```bash
cfo expense add --category salaries --amount 4800 [--currency EUR] [--date YYYY-MM-DD] [--budget "Q3 2026"] [--note "text"]
cfo expense list [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--category X] [--limit 50]
cfo expense view <ID>
cfo expense edit <ID> [--amount X] [--category X] [--date X] [--note X]
cfo expense delete <ID> [--yes]
cfo expense summary [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--group-by category|month]
```

Key logic:
- `--date` defaults to today if omitted
- `expense summary` shows % of total per category, and % of budget execution if `--budget` was set
- Months/categories over budget shown in red (Rich style)
- Amounts must be > 0, currency validated against `VALID_CURRENCIES`

---

### v0.3 — Income Tracking

New tables:
```sql
income_sources (id, name, client, is_recurring, recur_every, created_at)
income_entries (id, source_id, amount, currency, date, invoice_ref, note, created_at)
```

Commands:
```bash
cfo income source add --name "Acme Corp" [--client "Acme"] [--recurring] [--recur-every monthly]
cfo income source list / delete <ID>
cfo income add --amount 3500 [--source-id 1] [--currency EUR] [--date X] [--invoice-ref "INV-042"]
cfo income list / view <ID> / edit <ID> / delete <ID>
cfo income summary [--group-by source|month]
```

`income_service` must expose `get_monthly_average(source_id, months=6)` — consumed by v0.4 forecast.

---

### v0.4 — Cash Flow Forecasting

New tables:
```sql
forecast_scenarios   (id, name, period_from, period_to, created_at)
forecast_adjustments (id, scenario_id, type, category, factor, absolute_delta, note, created_at)
```

Commands:
```bash
cfo forecast run [--months 6] [--scenario base|optimist|pessimist]
cfo forecast scenario create --name "Best case" --from 2026-07-01 --to 2026-12-31
cfo forecast scenario add-adjustment <ID> --type income --factor 1.2
cfo forecast scenario list / view <ID> / delete <ID>
```

Algorithm:
- Income projection: average last 6 months per recurring source
- Expense projection: average last 3 months per category
- 3 built-in scenarios: base (1.0×), optimist (income ×1.2 / expense ×0.9), pessimist (income ×0.8 / expense ×1.1)
- Output: table with Mes | Ingressos | Despeses | Net | Balanç acumulat

---

### v0.5 — Reports (CSV + PDF)

New dependency: `reportlab` (add to pyproject.toml)

Commands:
```bash
cfo report expenses / income / cashflow / full \
    [--from X] [--to X] [--format csv|pdf] [--output PATH]
```

PDF structure: cover page → expenses table → income table → monthly cashflow → page numbers.

---

### v0.6 — Multi-currency

New table: `exchange_rates (base_currency, quote_currency, rate, fetched_at)`

New dependency: `httpx`

API: `https://open.er-api.com/v6/latest/{base}` (free, no key needed, 1500 req/month)
Cache TTL: 24h in SQLite. Fallback to cached rate if offline.

Config stored in `~/.cfo/config.json` (not DB):
```json
{"base_currency": "EUR"}
```

Commands:
```bash
cfo currency convert --amount 1000 --from USD --to EUR
cfo currency rates [--base EUR] [--refresh]
cfo currency set-base EUR
```

Flag `--in-base-currency` added to `expense list`, `income list`, `expense summary`, `income summary`.

---

### v0.7 — AI Insights (Claude)

New optional dependency: `anthropic` (extras: `pip install cfo-cli[ai]`)

Commands:
```bash
cfo ai config --api-key sk-...
cfo ai analyze [--from X] [--to X] [--focus expenses|income|cashflow|all]
cfo ai anomalies [--threshold 2.0]
cfo ai suggest [--goal reduce-expenses|increase-cashflow|optimize-categories]
```

Key: send aggregated data (not raw rows) to minimize tokens. Use prompt caching for the financial context block. Default model: `claude-sonnet-4-6`.

---

## Coding Rules

1. **One file per command group** in `cfo/cli/` — never mix two domains
2. **Service layer** in `cfo/services/` handles all DB logic — CLI files only parse args and call services
3. **Max 150 lines per file** — split into two if needed
4. **No new dependencies** without adding to `pyproject.toml` and documenting here
5. **Surgical changes** — only modify what the task requires
6. **Tests required** for every new command group (`tests/test_<module>.py`)

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

---

## Migrations Pattern

From v0.2 onwards, all schema changes go through `cfo/storage/migrations.py`.
Each migration is a numbered function. `init_db()` auto-applies pending ones:

```python
# cfo/storage/migrations.py
MIGRATIONS = {
    1: ("Add expense indexes", migration_001),
    2: ("Add income tables", migration_002),
    ...
}
```

Never edit existing migrations — always add a new numbered one.
