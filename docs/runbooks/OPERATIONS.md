# Runbook: operations & support

- **Owner:** maintainer
- **Last reviewed:** 2026-06-01

> cfo-cli has no servers — "operations" means keeping CI/release healthy and
> helping users with their **local** install and data. Procedures below are the
> recurring ones.

## Scope

CI failures, the FX rate dependency, and user-data lifecycle (where it lives,
backup/restore, migration troubleshooting). Releasing has its own
[runbook](RELEASE.md).

## CI is red on `main` or a PR

1. Open the failing GitHub Actions run; identify the step (`ruff`, `pytest`, or
   install) and the Python version in the matrix.
2. Reproduce locally with the same command:
   ```bash
   pip install -e ".[dev,ai,openai]"
   ruff check cfo/ tests/
   pytest tests/ -q
   ```
3. Fix on a feature branch, confirm green locally, push. Never disable a check to
   go green.

## FX rate API outage

The rate source is `open.er-api.com` (free, no key).

- **Expected behaviour:** rates are cached 24h; on a failed fetch the last cached
  rate is used. A user with **no** cache for a currency gets a clean
  `CurrencyError` ("offline?").
- **If the API changes shape or disappears:** the failure is isolated to
  `currency._fetch_rates`. Validate the new contract, update that function, add a
  test (httpx mocked). If it's permanently gone, write an ADR before swapping
  providers.

## User data: where it lives & backup/restore

- **Data:** `~/.cfo/data.db` (SQLite). **Config:** `~/.cfo/config.json`.
- **Backup:** copy the folder.
  ```bash
  cp -r ~/.cfo ~/cfo-backup-$(date +%F)
  ```
- **Restore:** copy it back (close any running command first).
- **Move to a new machine:** copy `~/.cfo/` over; the same package version reads it
  directly.

## Migration troubleshooting

Schema upgrades are automatic (`init_db()` applies pending numbered migrations;
see [ADR-0003](../adr/ADR-0003-numbered-migrations.md)).

- **Check what's applied:**
  ```bash
  sqlite3 ~/.cfo/data.db "SELECT version, name, applied_at FROM schema_migrations;"
  ```
- **A migration errored mid-run:** restore the backup, reproduce against a copy,
  fix the migration *as a new number* (never edit a shipped one), ship a patch.

## Documentation site (GitHub Pages)

The docs site is built and deployed by `.github/workflows/docs.yml` on pushes to
`main` that touch `docs/**` or `mkdocs.yml`.

- **One-time setup (required before the first deploy):** repo → Settings → Pages
  → "Build and deployment" → **Source: "GitHub Actions"**. Until this is set, the
  `build` job succeeds but the `deploy` job fails with `404 — Ensure GitHub Pages
  has been enabled`. That failure is expected pre-setup, not a workflow bug.
- **After enabling:** re-run the failed workflow (Actions → Docs → *Re-run jobs*)
  or push any `docs/**` change; the site publishes to
  `https://neskys.github.io/cfo-cli/`.
- **Build fails (not deploy):** reproduce locally with
  `pip install -e ".[docs]" && mkdocs build --strict` and fix the reported
  warning (broken link, page missing from nav, …).

## Common failures

| Symptom (user report) | Likely cause | Action |
|---|---|---|
| `cfo: command not found` | PATH / wrong Python env | Confirm `pip show cfo-cli`; reinstall in the right interpreter. |
| "needs 'openai'/'anthropic'/'reportlab'" | Optional extra not installed | `pip install 'cfo-cli[openai]'` (or `[ai]`); PDF needs base reportlab. |
| AI `Connection error` with `local` provider | Ollama not running / wrong base_url | Start Ollama; check `cfo ai config --base-url`. |
| Wrong currency conversions offline | Stale cached rate | `cfo currency rates --refresh` when back online. |

## Escalation

Bugs → GitHub issues. Suspected security issues → follow
[SECURITY.md](https://github.com/Neskys/cfo-cli/blob/main/SECURITY.md) (do **not** open a public issue).
