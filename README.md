# cfo-cli 📊

> Know how far your business can fly.

**cfo-cli** is an open-source command-line tool for freelancers, consultants, and small teams to manage budgets, track expenses and income, forecast cash flow, export reports, and work across currencies — all from your terminal.

**No SaaS subscriptions. No cloud lock-in. Your financial data stays on your machine.**

[![PyPI version](https://badge.fury.io/py/cfo-cli.svg)](https://badge.fury.io/py/cfo-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Why cfo-cli?

Freelancers and small-team CFOs spend 5–10 hours per month manually reconciling budgets and expenses in spreadsheets. Existing tools are either too complex (QuickBooks, Xero) or too simple (spreadsheets). There's no lightweight, open-source, terminal-first option built for solo operators.

`cfo-cli` fills that gap:

- **CLI-first** — scriptable, git-friendly, fast
- **Local-first** — SQLite database in `~/.cfo/`, zero cloud dependency
- **Multi-currency** — EUR, USD, GBP, CHF and more, with cached exchange rates
- **AI-powered** — analyze your finances in plain language with Claude (`pip install 'cfo-cli[ai]'`)
- **Open source** — MIT licensed, extensible, transparent

---

## Features

| Feature | Status |
|---|---|
| 📋 Budget planning | ✅ v0.1 |
| 💸 Expense tracking | ✅ v0.2 |
| 💰 Income tracking | ✅ v0.3 |
| 📈 Cash flow forecasting | ✅ v0.4 |
| 📄 CSV & PDF reports | ✅ v0.5 |
| 🌍 Multi-currency | ✅ v0.6 |
| 🤖 AI insights (Claude) | ✅ v0.7 |

---

## Installation

```bash
pip install cfo-cli
```

Requires Python 3.10+. Data is stored locally in `~/.cfo/data.db`; configuration in `~/.cfo/config.json`.

---

## Quick Start

### Budgets

```bash
cfo budget create "Q3 2026" --period quarterly          # monthly | quarterly | annual
cfo budget add-line "Q3 2026" --category salaries --amount 5000 --currency EUR
cfo budget view "Q3 2026"
cfo budget list
cfo budget delete "Q3 2026"
```

Example output for `cfo budget view "Q3 2026"`:

```
╭───────────────────────────────────────────╮
│     Budget: Q3 2026  [quarterly]          │
├─────────────────┬──────────────┬──────────┤
│ Category        │       Amount │ Currency │
├─────────────────┼──────────────┼──────────┤
│ Freelancers     │    2,000.00  │   EUR    │
│ Infrastructure  │      300.00  │   EUR    │
│ Marketing       │    1,000.00  │   EUR    │
│ Salaries        │    5,000.00  │   EUR    │
├─────────────────┼──────────────┼──────────┤
│ TOTAL           │    8,300.00  │          │
╰─────────────────┴──────────────┴──────────╯
```

### Expenses

```bash
cfo expense add --category salaries --amount 4800 --budget "Q3 2026" --note "June payroll"
cfo expense list --from 2026-06-01 --to 2026-06-30 --category salaries
cfo expense summary --group-by category --budget "Q3 2026"   # % of total + budget execution
cfo expense edit 1 --amount 5000
cfo expense delete 1 --yes
```

### Income

```bash
cfo income source add --name "Acme Corp" --client "Acme" --recurring --recur-every monthly
cfo income source list
cfo income add --amount 3500 --source-id 1 --invoice-ref "INV-042"
cfo income list
cfo income summary --group-by source
```

### Cash flow forecasting

```bash
cfo forecast run --months 6 --scenario base          # base | optimist | pessimist
cfo forecast scenario create --name "Best case" --from 2026-07-01 --to 2026-12-31
cfo forecast scenario add-adjustment 1 --type income --factor 1.2
cfo forecast scenario list
```

Projects recurring income (6-month average) against recent expenses (3-month average) and shows monthly net plus accumulated balance.

### Reports

```bash
cfo report full --format pdf --output report.pdf        # cover + tables + page numbers
cfo report expenses --from 2026-01-01 --format csv
cfo report cashflow --output cashflow.csv
```

Report types: `expenses`, `income`, `cashflow`, `full`. Formats: `csv`, `pdf`.

### Multi-currency

```bash
cfo currency set-base EUR
cfo currency convert --amount 1000 --from USD --to EUR
cfo currency rates --base EUR --refresh

# Convert and aggregate any list/summary into your base currency:
cfo expense summary --in-base-currency
cfo income list --in-base-currency
```

Exchange rates come from [open.er-api.com](https://open.er-api.com) (free, no key), are cached for 24h in SQLite, and fall back to the last cached rate when offline.

### AI insights (Claude)

Install the optional extra and configure your Anthropic API key:

```bash
pip install 'cfo-cli[ai]'
cfo ai config --api-key sk-...

cfo ai analyze --focus cashflow
cfo ai anomalies --threshold 2.0
cfo ai suggest --goal reduce-expenses
```

cfo-cli sends only **aggregated** figures (totals and breakdowns, never individual transactions) to Claude and uses prompt caching to keep token usage low. The default model is `claude-sonnet-4-6`; your API key is stored locally in `~/.cfo/config.json`.

---

## Roadmap

All planned versions (v0.1–v0.7) have shipped. 🎉 Future work is open-ended — feature requests and issues are welcome on [GitHub](https://github.com/Neskys/cfo-cli/issues).

---

## Contributing

Contributions, issues, and feature requests are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repo
2. Create your branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push and open a Pull Request

---

## Who is this for?

- **Freelancers** who invoice clients and need to track project profitability
- **Consultants** (CFO-as-a-service, legal, tech) managing multiple engagements
- **Small startups** that need financial visibility without enterprise tooling
- **Developers** who prefer terminal over spreadsheets

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built and maintained by [Xavier Potrony](https://github.com/Neskys), CFO consultant based in Catalonia.*
