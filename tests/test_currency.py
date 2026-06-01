"""Tests for currency commands and the currency service."""

import pytest
from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.services import currency
from cfo.storage.database import get_connection, init_db
from cfo.core.config import get_base_currency

runner = CliRunner()

# Fake API rate tables keyed by base currency (avoids real network in tests).
FAKE_RATES = {
    "USD": {"USD": 1.0, "EUR": 0.5, "GBP": 0.8},
    "EUR": {"EUR": 1.0, "USD": 2.0, "GBP": 0.9},
    "GBP": {"GBP": 1.0, "EUR": 1.1, "USD": 1.25},
}


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(currency, "_fetch_rates", lambda base: FAKE_RATES[base.upper()])
    return tmp_path


def test_set_base_and_get(home):
    result = runner.invoke(app, ["currency", "set-base", "usd"])
    assert result.exit_code == 0
    assert get_base_currency() == "USD"


def test_set_base_invalid(home):
    assert runner.invoke(app, ["currency", "set-base", "XYZ"]).exit_code != 0


def test_convert_same_currency(home):
    assert currency.convert(100, "EUR", "EUR") == 100.0


def test_convert(home):
    result = runner.invoke(app, ["currency", "convert", "--amount", "100", "--from", "USD", "--to", "EUR"])
    assert result.exit_code == 0 and "50.00" in result.output
    assert currency.convert(100, "USD", "EUR") == 50.0


def test_rates_cached(home):
    result = runner.invoke(app, ["currency", "rates", "--base", "EUR"])
    assert result.exit_code == 0 and "USD" in result.output
    with get_connection() as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM exchange_rates WHERE base_currency='EUR'").fetchone()["c"]
    assert n == len(FAKE_RATES["EUR"])


def test_offline_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO exchange_rates (base_currency, quote_currency, rate, fetched_at) "
            "VALUES ('USD', 'EUR', 0.4, '2000-01-01 00:00:00')"
        )

    def boom(base):
        raise currency.CurrencyError("network down")

    monkeypatch.setattr(currency, "_fetch_rates", boom)
    # stale cache used as fallback rather than failing
    assert currency.get_rate("USD", "EUR") == 0.4


def test_no_rate_no_cache_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    def boom(base):
        raise currency.CurrencyError("network down")

    monkeypatch.setattr(currency, "_fetch_rates", boom)
    with pytest.raises(currency.CurrencyError):
        currency.get_rate("USD", "EUR")


def test_expense_list_in_base(home):
    runner.invoke(app, ["currency", "set-base", "EUR"])
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "100", "--currency", "USD"])
    # 100 USD → 50 EUR
    result = runner.invoke(app, ["expense", "list", "--in-base-currency"])
    assert result.exit_code == 0 and "50.00" in result.output and "EUR" in result.output


def test_expense_summary_in_base(home):
    runner.invoke(app, ["currency", "set-base", "EUR"])
    runner.invoke(app, ["expense", "add", "--category", "a", "--amount", "100", "--currency", "USD"])
    runner.invoke(app, ["expense", "add", "--category", "a", "--amount", "10", "--currency", "EUR"])
    # a = 50 (from USD) + 10 = 60 EUR
    result = runner.invoke(app, ["expense", "summary", "--in-base-currency"])
    assert result.exit_code == 0 and "60.00" in result.output


def test_income_summary_in_base(home):
    runner.invoke(app, ["currency", "set-base", "EUR"])
    runner.invoke(app, ["income", "add", "--amount", "100", "--currency", "USD"])
    result = runner.invoke(app, ["income", "summary", "--in-base-currency"])
    assert result.exit_code == 0 and "50.00" in result.output


def test_migration_004_applied(home):
    runner.invoke(app, ["currency", "rates", "--base", "EUR"])
    with get_connection() as conn:
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exchange_rates'"
        ).fetchone()
    assert 4 in versions and tbl is not None
