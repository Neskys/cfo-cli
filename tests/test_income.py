"""Tests for income commands and the income services."""

from datetime import date, datetime

import pytest
from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.storage.database import get_connection, init_db
from cfo.services import income as svc
from cfo.services.income_source import IncomeError, add_source

runner = CliRunner()


def _add_source(*args):
    return runner.invoke(app, ["income", "source", "add", *args])


def _add(*args):
    return runner.invoke(app, ["income", "add", *args])


def test_source_add_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add_source("--name", "Acme Corp", "--client", "Acme", "--recurring")
    assert result.exit_code == 0 and "#1" in result.output
    result = runner.invoke(app, ["income", "source", "list"])
    assert "Acme Corp" in result.output and "monthly" in result.output


def test_source_duplicate_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add_source("--name", "Dup")
    result = _add_source("--name", "Dup")
    assert result.exit_code != 0


def test_source_bad_recur_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add_source("--name", "X", "--recur-every", "hourly")
    assert result.exit_code != 0


def test_add_entry_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add_source("--name", "Acme")
    result = _add("--amount", "3500", "--source-id", "1", "--invoice-ref", "INV-042")
    assert result.exit_code == 0 and "#1" in result.output
    result = runner.invoke(app, ["income", "list"])
    assert "Acme" in result.output and "3,500.00" in result.output and "INV-042" in result.output


def test_add_defaults_to_today(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--amount", "100")
    with get_connection() as conn:
        row = conn.execute("SELECT date, source_id FROM income_entries WHERE id = 1").fetchone()
    assert row["date"] == date.today().isoformat()
    assert row["source_id"] is None


def test_add_rejects_zero_amount(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert _add("--amount", "0").exit_code != 0


def test_add_unknown_source_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert _add("--amount", "10", "--source-id", "99").exit_code != 0


def test_view_edit_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--amount", "200")
    assert runner.invoke(app, ["income", "view", "1"]).exit_code == 0

    result = runner.invoke(app, ["income", "edit", "1", "--amount", "250", "--note", "fixed"])
    assert result.exit_code == 0
    with get_connection() as conn:
        row = conn.execute("SELECT amount, note FROM income_entries WHERE id = 1").fetchone()
    assert row["amount"] == 250 and row["note"] == "fixed"

    assert runner.invoke(app, ["income", "delete", "1", "--yes"]).exit_code == 0
    assert runner.invoke(app, ["income", "view", "1"]).exit_code != 0


def test_edit_nothing_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--amount", "200")
    assert runner.invoke(app, ["income", "edit", "1"]).exit_code != 0


def test_delete_source_unlinks_entries(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add_source("--name", "Acme")
    _add("--amount", "500", "--source-id", "1")
    runner.invoke(app, ["income", "source", "delete", "1", "--yes"])
    with get_connection() as conn:
        row = conn.execute("SELECT source_id FROM income_entries WHERE id = 1").fetchone()
    assert row["source_id"] is None


def test_summary_by_source(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add_source("--name", "Acme")
    _add("--amount", "75", "--source-id", "1")
    _add("--amount", "25")
    result = runner.invoke(app, ["income", "summary"])
    assert "Acme" in result.output and "Unassigned" in result.output
    assert "75.0%" in result.output and "25.0%" in result.output


def test_summary_by_month(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--amount", "10", "--date", "2026-01-05")
    _add("--amount", "30", "--date", "2026-02-05")
    result = runner.invoke(app, ["income", "summary", "--group-by", "month"])
    assert "2026-01" in result.output and "2026-02" in result.output


def test_get_monthly_average(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add_source("--name", "Acme")
    today = date.today()
    _add("--amount", "600", "--source-id", "1", "--date", today.isoformat())
    _add("--amount", "600", "--source-id", "1", "--date", today.isoformat())
    # 1200 total over a 6-month window → 200/month
    assert svc.get_monthly_average(1, months=6) == 200.0


# --- service-level edge cases (validation, filters, conversions) ---


def test_add_entry_rejects_invalid_date(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(IncomeError):
        svc.add_entry(100, on_date="2026-13-40")


def test_add_entry_rejects_unknown_currency(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(IncomeError):
        svc.add_entry(100, currency="XYZ")


def test_list_entries_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    svc.add_entry(10, source_id=None, on_date="2026-01-10")
    sid = add_source("Acme")
    svc.add_entry(20, source_id=sid, on_date="2026-03-10")
    # date window + source filter each narrow the result set
    assert len(svc.list_entries(date_from="2026-02-01")) == 1
    assert len(svc.list_entries(date_to="2026-02-01")) == 1
    assert len(svc.list_entries(source_id=sid)) == 1


def test_list_entries_in_base(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    svc.add_entry(100, currency="USD")
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO exchange_rates VALUES ('USD', 'EUR', 0.5, ?)", (now,)
        )
    runner.invoke(app, ["currency", "set-base", "EUR"])
    rows = svc.list_entries(in_base=True)
    assert rows[0]["amount"] == 50.0 and rows[0]["currency"] == "EUR"


def test_edit_entry_branches(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    svc.add_entry(100)
    svc.edit_entry(1, on_date="2026-02-02", invoice_ref="INV-9")
    row = svc.get_entry(1)
    assert row["date"] == "2026-02-02" and row["invoice_ref"] == "INV-9"


def test_edit_entry_rejects_zero_amount(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    svc.add_entry(100)
    with pytest.raises(IncomeError):
        svc.edit_entry(1, amount=0)


def test_edit_and_delete_missing_entry_fail(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    init_db()
    with pytest.raises(IncomeError):
        svc.edit_entry(999, amount=5)
    with pytest.raises(IncomeError):
        svc.delete_entry(999)


def test_summary_rejects_bad_group_by(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(IncomeError):
        svc.summary(group_by="weekly")


def test_summary_date_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    svc.add_entry(10, on_date="2026-01-10")
    svc.add_entry(40, on_date="2026-03-10")
    result = svc.summary(date_from="2026-02-01", date_to="2026-04-01")
    assert result["total"] == 40


def test_monthly_average_rejects_bad_window(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(IncomeError):
        svc.get_monthly_average(1, months=0)


def test_migration_002_applied(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--amount", "10")
    with get_connection() as conn:
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='income_entries'"
        ).fetchone()
    assert 2 in versions and tbl is not None
