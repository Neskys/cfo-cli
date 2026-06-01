"""Tests for forecast commands and the forecast services."""

from datetime import date

from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.storage.database import get_connection
from cfo.services import forecast as svc

runner = CliRunner()


def _seed(monkeypatch, tmp_path):
    """One recurring income source (1000/mo) and 300/mo of expenses."""
    monkeypatch.setenv("HOME", str(tmp_path))
    today = date.today().isoformat()
    runner.invoke(app, ["income", "source", "add", "--name", "Acme", "--recurring"])
    runner.invoke(app, ["income", "add", "--amount", "1000", "--source-id", "1", "--date", today])
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "300", "--date", today])


def test_run_base_scenario(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    data = svc.run(months=6, scenario="base")
    # 1000 income over a 6-month window → ~166.67/mo; 300 expense over 3 months → 100/mo
    assert round(data["monthly_income"], 2) == round(1000 / 6, 2)
    assert round(data["monthly_expense"], 2) == 100.0
    assert len(data["rows"]) == 6
    # accumulated balance grows monotonically by net each month
    net = data["rows"][0]["net"]
    assert round(data["rows"][5]["balance"], 2) == round(net * 6, 2)


def test_run_scenario_factors(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    base = svc.run(scenario="base")
    opt = svc.run(scenario="optimist")
    pes = svc.run(scenario="pessimist")
    assert round(opt["monthly_income"], 2) == round(base["monthly_income"] * 1.2, 2)
    assert round(opt["monthly_expense"], 2) == round(base["monthly_expense"] * 0.9, 2)
    assert round(pes["monthly_income"], 2) == round(base["monthly_income"] * 0.8, 2)
    assert round(pes["monthly_expense"], 2) == round(base["monthly_expense"] * 1.1, 2)


def test_run_only_recurring_income_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    today = date.today().isoformat()
    runner.invoke(app, ["income", "source", "add", "--name", "OneOff"])  # not recurring
    runner.invoke(app, ["income", "add", "--amount", "5000", "--source-id", "1", "--date", today])
    data = svc.run()
    assert data["monthly_income"] == 0.0


def test_run_cli(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    result = runner.invoke(app, ["forecast", "run", "--months", "3"])
    assert result.exit_code == 0
    assert "Cash flow forecast" in result.output and "Balanç acumulat" in result.output


def test_run_bad_scenario(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["forecast", "run", "--scenario", "wild"])
    assert result.exit_code != 0


def test_scenario_crud(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(
        app, ["forecast", "scenario", "create", "--name", "Best", "--from", "2026-07-01", "--to", "2026-12-31"]
    )
    assert result.exit_code == 0 and "#1" in result.output

    result = runner.invoke(
        app, ["forecast", "scenario", "add-adjustment", "1", "--type", "income", "--factor", "1.2"]
    )
    assert result.exit_code == 0

    result = runner.invoke(app, ["forecast", "scenario", "view", "1"])
    assert result.exit_code == 0 and "income" in result.output

    result = runner.invoke(app, ["forecast", "scenario", "list"])
    assert "Best" in result.output

    result = runner.invoke(app, ["forecast", "scenario", "delete", "1", "--yes"])
    assert result.exit_code == 0
    with get_connection() as conn:
        rows = conn.execute("SELECT COUNT(*) AS c FROM forecast_adjustments").fetchone()
    assert rows["c"] == 0  # adjustments cascaded


def test_scenario_bad_dates(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(
        app, ["forecast", "scenario", "create", "--name", "X", "--from", "2026-12-31", "--to", "2026-01-01"]
    )
    assert result.exit_code != 0


def test_adjustment_requires_factor_or_delta(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(
        app, ["forecast", "scenario", "create", "--name", "X", "--from", "2026-01-01", "--to", "2026-06-01"]
    )
    result = runner.invoke(app, ["forecast", "scenario", "add-adjustment", "1", "--type", "income"])
    assert result.exit_code != 0


def test_migration_003_applied(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["forecast", "scenario", "list"])
    with get_connection() as conn:
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='forecast_scenarios'"
        ).fetchone()
    assert 3 in versions and tbl is not None
