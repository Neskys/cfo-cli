"""Tests for report commands and the report writers."""

import csv
from pathlib import Path

from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.reports import datasets

runner = CliRunner()


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["income", "source", "add", "--name", "Acme", "--recurring"])
    runner.invoke(app, ["income", "add", "--amount", "1000", "--source-id", "1", "--date", "2026-01-10"])
    runner.invoke(app, ["income", "add", "--amount", "500", "--date", "2026-02-10"])
    runner.invoke(app, ["expense", "add", "--category", "infra", "--amount", "300", "--date", "2026-01-15"])
    runner.invoke(app, ["expense", "add", "--category", "food", "--amount", "200", "--date", "2026-02-15"])


def test_csv_expenses(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    out = tmp_path / "exp.csv"
    result = runner.invoke(app, ["report", "expenses", "--output", str(out)])
    assert result.exit_code == 0 and out.exists()
    with out.open() as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["ID", "Date", "Category", "Amount", "Currency", "Note"]
    assert len(rows) == 3  # header + 2 expenses


def test_csv_cashflow_balance(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    out = tmp_path / "cf.csv"
    runner.invoke(app, ["report", "cashflow", "--output", str(out)])
    with out.open() as f:
        rows = list(csv.reader(f))
    # header + 2 months. Jan: 1000-300=700; Feb: 500-200=300 → balance 1000
    assert rows[1][0] == "2026-01" and rows[1][3] == "700.00"
    assert rows[2][4] == "1000.00"


def test_csv_full_has_sections(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    out = tmp_path / "full.csv"
    runner.invoke(app, ["report", "full", "--output", str(out)])
    text = out.read_text()
    assert "# Expenses" in text and "# Income" in text and "# Monthly cash flow" in text


def test_pdf_output(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    out = tmp_path / "report.pdf"
    result = runner.invoke(app, ["report", "full", "--format", "pdf", "--output", str(out)])
    assert result.exit_code == 0 and out.exists()
    assert out.read_bytes()[:4] == b"%PDF"


def test_date_filter(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    out = tmp_path / "exp.csv"
    runner.invoke(app, ["report", "expenses", "--from", "2026-02-01", "--output", str(out)])
    with out.open() as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2  # header + only the February expense


def test_invalid_format(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert runner.invoke(app, ["report", "expenses", "--format", "xml"]).exit_code != 0


def test_invalid_date(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert runner.invoke(app, ["report", "expenses", "--from", "nope"]).exit_code != 0


def test_default_output_path(tmp_path, monkeypatch):
    _seed(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["report", "income"])
    assert result.exit_code == 0
    generated = list(Path(tmp_path).glob("cfo-income-*.csv"))
    assert len(generated) == 1


def test_build_unknown_type(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    try:
        datasets.build("bogus")
        assert False, "expected ReportError"
    except datasets.ReportError:
        pass
