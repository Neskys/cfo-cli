# Glossary

Domain and project terms used across cfo-cli and its documentation.

| Term | Meaning |
|---|---|
| **Budget** | A named financial plan for a period (`monthly`, `quarterly`, `annual`) containing budget lines. |
| **Budget line** | One categorised planned amount within a budget (e.g. *salaries — 24,000 EUR*). |
| **Expense** | A real outflow recorded against a category, optionally tagged to a budget. |
| **Income source** | A payer/revenue stream; may be **recurring** (with a `recur_every` cadence) or one-off. |
| **Income entry** | A single recorded inflow, optionally linked to an income source and an invoice reference. |
| **Execution %** | An expense category's actual spend as a percentage of its budgeted amount (over-budget shown in red). |
| **Forecast** | A forward projection of cash flow over N months from recent trends. |
| **Scenario** | A named set of forecast adjustments. Built-in: `base`, `optimist`, `pessimist`; custom ones are stored. |
| **Adjustment** | A factor or absolute delta applied to income/expense within a custom scenario. |
| **Monthly average** | The rolling-window basis for projections: income over 6 months, expenses over 3. |
| **Base currency** | The user's reference currency (config `base_currency`, default EUR) used by `--in-base-currency`. |
| **Exchange rate cache** | The `exchange_rates` table; FX rates stored with a 24h TTL and an offline fallback. |
| **Report** | A CSV/PDF export: `expenses`, `income`, `cashflow`, or `full`. |
| **Provider** | An AI backend: `anthropic` (Claude), `openai`, or `local` (Gemma via Ollama). |
| **Aggregated data** | Totals/breakdowns sent to AI providers — never individual transactions (privacy boundary). |
| **Migration** | A numbered, append-only schema change auto-applied by `init_db()` and tracked in `schema_migrations`. |
| **Service layer** | `cfo/services/*` — all business logic and DB access; the CLI's only entry point to data. |
| **Extra** | An optional dependency group (`[ai]`, `[openai]`, `[dev]`) installed on demand. |
| **Trusted Publishing** | OIDC-based PyPI publishing with no stored token, used by the release workflow. |

See also: [System Design](design/SYSTEM_DESIGN.md), [ADRs](adr/README.md), and the command
reference in the [README](https://github.com/Neskys/cfo-cli/blob/main/README.md).
