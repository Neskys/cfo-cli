# Contributing to cfo-cli

Thanks for your interest in improving **cfo-cli**! This guide covers how to set up
the project and the conventions we follow.

## Development setup

```bash
git clone https://github.com/Neskys/cfo-cli.git
cd cfo-cli
pip install -e ".[dev]"
```

Run the CLI, tests, and linter:

```bash
cfo --help
pytest tests/ -v
ruff check cfo/
```

## Project conventions

The architecture and rules are documented in [CLAUDE.md](CLAUDE.md). In short:

1. **One file per command group** in `cfo/cli/` — never mix two domains.
2. **Service layer** in `cfo/services/` holds all database logic; CLI files only
   parse arguments and call services.
3. **Keep files small** (aim for ~150 lines); split when they grow.
4. **No new dependencies** without adding them to `pyproject.toml` and documenting
   them in the *Dependencies* section of `CLAUDE.md`.
5. **Surgical changes** — only touch what the task requires.
6. **Tests are required** for every new command group (`tests/test_<module>.py`).

### Database changes

All schema changes go through `cfo/storage/migrations.py` as a new numbered
migration. **Never edit an existing migration** — add the next number.

### Validation rules

- Amounts must be greater than zero.
- Currencies are validated against `VALID_CURRENCIES`.
- Dates use `YYYY-MM-DD`; `--date` defaults to today when omitted.
- Services raise typed errors (e.g. `ExpenseError`, `CurrencyError`) that the CLI
  catches and reports cleanly.

### Tests and the network

Tests must not hit the network. Isolate state by pointing `HOME` at a `tmp_path`,
and mock exchange-rate fetches (`currency._fetch_rates`) or pre-seed the cache.

## Pull requests

1. Fork the repo.
2. Create a branch: `git checkout -b feat/my-feature`.
3. Make your change with tests; ensure `pytest` and `ruff check cfo/` pass.
4. Use [Conventional Commits](https://www.conventionalcommits.org/) for messages
   (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
5. Update `CHANGELOG.md` under `[Unreleased]`.
6. Push and open a Pull Request describing the change.

## License

By contributing, you agree that your contributions are licensed under the MIT
License, the same as the project.
