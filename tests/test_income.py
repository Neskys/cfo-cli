"""Tests for income commands and the income services."""

from datetime import date

from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.storage.database import get_connection
from cfo.services import income as svc

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


def test_migration_002_applied(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--amount", "10")
    with get_connection() as conn:
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='income_entries'"
        ).fetchone()
    assert 2 in versions and tbl is not None
