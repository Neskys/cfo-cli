# Changelog

All notable changes to **cfo-cli** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Future work is open-ended.

## [0.8.0]

### Added
- Multi-provider AI: **OpenAI** alongside Claude, both via API key.
- `cfo ai config --provider anthropic|openai [--model NAME]` and `cfo ai set-provider`.
- Per-provider API key and model override in `~/.cfo/config.json`.
- `services/ai_providers.py`: provider adapters (Anthropic `cache_control`; OpenAI automatic prefix caching). Default models: `claude-sonnet-4-6`, `gpt-4o`.
- Optional dependency extra `[openai]`.

### Notes
- Authentication is by API key for both providers; neither inference API uses OAuth.

## [0.7.0]

### Added
- AI insights via the Anthropic SDK (optional `[ai]` extra, lazy-imported).
- `cfo ai config --api-key`, `cfo ai analyze --focus`, `cfo ai anomalies --threshold`, `cfo ai suggest --goal`.
- Sends only aggregated data (built from the summary services), prompt-caches the financial-context block, default model `claude-sonnet-4-6`.
- API key stored in `~/.cfo/config.json`.

## [0.6.0]

### Added
- Multi-currency support.
- `exchange_rates` cache table (migration 004) with a 24h TTL and offline fallback to the last cached rate.
- `~/.cfo/config.json` for non-DB configuration (`base_currency`).
- `cfo currency convert`, `cfo currency rates [--base] [--refresh]`, `cfo currency set-base`.
- `--in-base-currency` flag on `expense list`, `expense summary`, `income list`, `income summary`.
- Dependency: `httpx`.

## [0.5.0]

### Added
- CSV and PDF reports: `cfo report expenses|income|cashflow|full [--from] [--to] [--format csv|pdf] [--output]`.
- PDF layout: cover page → tables → page numbers (reportlab imported lazily so CSV works without it).
- Dependency: `reportlab`.

## [0.4.0]

### Added
- Cash flow forecasting: `cfo forecast run [--months] [--scenario base|optimist|pessimist]`.
- Custom scenarios and adjustments (migration 003): `cfo forecast scenario create|add-adjustment|list|view|delete`.
- Recurring-income (6-month) vs expense (3-month) projection with accumulated balance.

## [0.3.0]

### Added
- Income tracking (migration 002): income sources and entries.
- `cfo income source add|list|delete` and `cfo income add|list|view|edit|delete|summary`.
- `income` service exposes `get_monthly_average(source_id, months=6)` for forecasting.

## [0.2.0]

### Added
- Expense tracking: activated the `expenses` table.
- Numbered migrations system (`schema_migrations` + migration 001 indexes).
- `cfo expense add|list|view|edit|delete|summary`, with % of total and budget execution (over-budget shown in red).
- Reusable Rich table helpers and a service layer.

## [0.1.0]

### Added
- Initial release: budget planning.
- `cfo budget create|add-line|view|list|delete` and `cfo version`.
- Local SQLite storage at `~/.cfo/data.db`.

[Unreleased]: https://github.com/Neskys/cfo-cli/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/Neskys/cfo-cli/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Neskys/cfo-cli/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Neskys/cfo-cli/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Neskys/cfo-cli/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Neskys/cfo-cli/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Neskys/cfo-cli/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Neskys/cfo-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Neskys/cfo-cli/releases/tag/v0.1.0
