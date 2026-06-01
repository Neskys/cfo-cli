"""Tests for budget commands."""

from typer.testing import CliRunner
from cfo.cli.main import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "cfo-cli" in result.output


def test_budget_create_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["budget", "create", "Test Budget", "--period", "monthly"])
    assert result.exit_code == 0
    assert "Test Budget" in result.output

    result = runner.invoke(app, ["budget", "list"])
    assert result.exit_code == 0
    assert "Test Budget" in result.output


def test_budget_add_line(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["budget", "create", "My Budget", "--period", "monthly"])
    result = runner.invoke(app, [
        "budget", "add-line", "My Budget",
        "--category", "salaries",
        "--amount", "3000",
        "--currency", "EUR",
    ])
    assert result.exit_code == 0
    assert "salaries" in result.output.lower()


def test_budget_view(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["budget", "create", "View Test", "--period", "quarterly"])
    runner.invoke(app, ["budget", "add-line", "View Test", "--category", "infra", "--amount", "500"])
    result = runner.invoke(app, ["budget", "view", "View Test"])
    assert result.exit_code == 0
    assert "500" in result.output


def test_budget_invalid_period(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["budget", "create", "Bad", "--period", "weekly"])
    assert result.exit_code != 0


def test_budget_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["budget", "view", "nonexistent"])
    assert result.exit_code != 0
