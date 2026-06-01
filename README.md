# cfo-cli 📊

> Know how far your business can fly.

**cfo-cli** is an open-source command-line tool for freelancers, consultants, and small teams to manage budgets, track expenses, forecast cash flow, and get AI-powered financial insights — all from your terminal.

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
- **AI-powered** — ask questions about your finances in plain language (Claude integration, coming in v0.5)
- **Multi-currency** — EUR, USD, GBP, CHF and more
- **Open source** — MIT licensed, extensible, transparent

---

## Features

| Feature | Status |
|---|---|
| 📋 Budget Planning | ✅ v0.1 |
| 💸 Expense Tracking | 🔜 v0.2 |
| 📈 Cash Flow Forecasting | 🔜 v0.3 |
| 📄 CSV & PDF Reports | 🔜 v0.4 |
| 🤖 AI Insights (Claude) | 🔜 v0.5 |
| 🌍 Multi-currency | 🔜 v0.5 |

---

## Installation

```bash
pip install cfo-cli
```

Requires Python 3.10+

---

## Quick Start

### Budget Planning

```bash
# Create a quarterly budget
cfo budget create "Q3 2026" --period quarterly

# Add line items
cfo budget add-line "Q3 2026" --category salaries --amount 5000 --currency EUR
cfo budget add-line "Q3 2026" --category infrastructure --amount 300 --currency EUR
cfo budget add-line "Q3 2026" --category marketing --amount 1000 --currency EUR
cfo budget add-line "Q3 2026" --category freelancers --amount 2000 --currency EUR

# View your budget
cfo budget view "Q3 2026"

# List all budgets
cfo budget list

# Delete a budget
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

---

## Roadmap

### v0.2 — Expense Tracking
```bash
cfo expense add --category salaries --amount 4800 --currency EUR --date 2026-06-01
cfo expense list --period this-month
cfo expense compare "Q3 2026"   # Real vs. budget, % deviation
```

### v0.3 — Cash Flow Forecasting
```bash
cfo forecast --months 6
cfo forecast --months 6 --scenario optimistic    # +15% revenue
cfo forecast --months 6 --scenario conservative  # -20% revenue
```

### v0.4 — Reports
```bash
cfo report summary --period Q3-2026
cfo report export --format pdf
cfo report export --format csv
```

### v0.5 — AI Insights (Claude)
```bash
cfo ai ask "What is my cash runway at current burn rate?"
cfo ai insights          # Auto-generated monthly analysis
cfo ai forecast-risk     # Flag financial risks
```

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
