"""Tests for expense commands and the expense service."""

from datetime import date

import pytest
from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.storage.database import get_connection, init_db
from cfo.services import expense as esvc
from cfo.services.expense import ExpenseError

runner = CliRunner()


def _add(*args):
    return runner.invoke(app, ["expense", "add", *args])


def test_add_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add("--category", "Software", "--amount", "49.99")
    assert result.exit_code == 0
    assert "#1" in result.output

    result = runner.invoke(app, ["expense", "list"])
    assert result.exit_code == 0
    assert "Software" in result.output
    assert "49.99" in result.output


def test_add_defaults_to_today(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "coffee", "--amount", "3")
    with get_connection() as conn:
        row = conn.execute("SELECT date FROM expenses WHERE id = 1").fetchone()
    assert row["date"] == date.today().isoformat()


def test_add_rejects_zero_amount(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add("--category", "x", "--amount", "0")
    assert result.exit_code != 0


def test_add_rejects_bad_currency(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add("--category", "x", "--amount", "10", "--currency", "XYZ")
    assert result.exit_code != 0


def test_add_rejects_bad_date(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add("--category", "x", "--amount", "10", "--date", "2026-13-01")
    assert result.exit_code != 0


def test_add_with_unknown_budget_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = _add("--category", "x", "--amount", "10", "--budget", "Ghost")
    assert result.exit_code != 0


def test_list_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "travel", "--amount", "100", "--date", "2026-01-10")
    _add("--category", "food", "--amount", "20", "--date", "2026-02-10")
    result = runner.invoke(app, ["expense", "list", "--category", "travel"])
    assert "Travel" in result.output and "Food" not in result.output
    result = runner.invoke(app, ["expense", "list", "--from", "2026-02-01"])
    assert "Food" in result.output and "Travel" not in result.output


def test_view_edit_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "infra", "--amount", "200")

    result = runner.invoke(app, ["expense", "view", "1"])
    assert result.exit_code == 0 and "Infra" in result.output

    result = runner.invoke(app, ["expense", "edit", "1", "--amount", "250", "--note", "updated"])
    assert result.exit_code == 0
    with get_connection() as conn:
        row = conn.execute("SELECT amount, note FROM expenses WHERE id = 1").fetchone()
    assert row["amount"] == 250 and row["note"] == "updated"

    result = runner.invoke(app, ["expense", "delete", "1", "--yes"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["expense", "view", "1"])
    assert result.exit_code != 0


def test_edit_nothing_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "infra", "--amount", "200")
    result = runner.invoke(app, ["expense", "edit", "1"])
    assert result.exit_code != 0


def test_summary_by_category_pct(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "a", "--amount", "75")
    _add("--category", "b", "--amount", "25")
    result = runner.invoke(app, ["expense", "summary"])
    assert result.exit_code == 0
    assert "75.0%" in result.output and "25.0%" in result.output


def test_summary_with_budget_execution(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["budget", "create", "Q1", "--period", "quarterly"])
    runner.invoke(app, ["budget", "add-line", "Q1", "--category", "salaries", "--amount", "1000"])
    _add("--category", "salaries", "--amount", "1200", "--budget", "Q1")
    result = runner.invoke(app, ["expense", "summary", "--budget", "Q1"])
    assert result.exit_code == 0
    assert "120.0%" in result.output  # over budget


def test_summary_by_month(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "x", "--amount", "10", "--date", "2026-01-05")
    _add("--category", "y", "--amount", "30", "--date", "2026-02-05")
    result = runner.invoke(app, ["expense", "summary", "--group-by", "month"])
    assert "2026-01" in result.output and "2026-02" in result.output


# --- service-level edge cases (validation, filters) ---


def test_list_date_to_filter(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    esvc.add_expense("a", 10, on_date="2026-01-10")
    esvc.add_expense("b", 20, on_date="2026-03-10")
    assert len(esvc.list_expenses(date_to="2026-02-01")) == 1


def test_edit_service_branches(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    esvc.add_expense("infra", 100)
    esvc.edit_expense(1, category="Cloud", on_date="2026-03-03")
    row = esvc.get_expense(1)
    assert row["category"] == "cloud" and row["date"] == "2026-03-03"


def test_edit_rejects_zero_amount(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    esvc.add_expense("infra", 100)
    with pytest.raises(ExpenseError):
        esvc.edit_expense(1, amount=0)


def test_edit_and_delete_missing_expense_fail(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    init_db()
    with pytest.raises(ExpenseError):
        esvc.edit_expense(999, amount=5)
    with pytest.raises(ExpenseError):
        esvc.delete_expense(999)


def test_summary_rejects_bad_group_by(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(ExpenseError):
        esvc.summary(group_by="weekly")


def test_summary_date_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    esvc.add_expense("a", 10, on_date="2026-01-10")
    esvc.add_expense("b", 40, on_date="2026-03-10")
    result = esvc.summary(date_from="2026-02-01", date_to="2026-04-01")
    assert result["total"] == 40


def test_monthly_average_rejects_bad_window(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(ExpenseError):
        esvc.get_monthly_average(months=0)


def test_migrations_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _add("--category", "x", "--amount", "10")
    with get_connection() as conn:
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_expenses_date'"
        ).fetchone()
    assert 1 in versions
    assert idx is not None
