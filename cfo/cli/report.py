"""Reporting commands (CSV / PDF exports)."""

from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from cfo.reports import datasets
from cfo.reports.datasets import ReportError
from cfo.reports.csv_writer import write_csv
from cfo.reports.pdf_writer import write_pdf, PDFNotAvailable

app = typer.Typer(help="Export financial summaries as CSV or PDF.")
console = Console()


def _generate(report_type, date_from, date_to, fmt, output):
    fmt = fmt.lower()
    if fmt not in ("csv", "pdf"):
        console.print(f"[red]Unknown format '{fmt}'. Use csv or pdf.[/red]")
        raise typer.Exit(1)
    try:
        data = datasets.build(report_type, date_from, date_to)
        path = Path(output) if output else Path(f"cfo-{report_type}-{date.today().isoformat()}.{fmt}")
        write_csv(data, path) if fmt == "csv" else write_pdf(data, path)
    except (ReportError, PDFNotAvailable) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    rows = sum(len(d["rows"]) for d in data)
    console.print(f"[green]✓[/green] {report_type.title()} report ({rows} rows) → [bold]{path}[/bold]")


def _opts():
    return (
        typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
        typer.Option(None, "--to", help="End date YYYY-MM-DD"),
        typer.Option("csv", "--format", help="csv or pdf"),
        typer.Option(None, "--output", "-o", help="Output file path"),
    )


_FROM, _TO, _FMT, _OUT = _opts()


@app.command("expenses")
def report_expenses(date_from: str = _FROM, date_to: str = _TO, fmt: str = _FMT, output: str = _OUT):
    """Export the expenses report."""
    _generate("expenses", date_from, date_to, fmt, output)


@app.command("income")
def report_income(date_from: str = _FROM, date_to: str = _TO, fmt: str = _FMT, output: str = _OUT):
    """Export the income report."""
    _generate("income", date_from, date_to, fmt, output)


@app.command("cashflow")
def report_cashflow(date_from: str = _FROM, date_to: str = _TO, fmt: str = _FMT, output: str = _OUT):
    """Export the monthly cash flow report."""
    _generate("cashflow", date_from, date_to, fmt, output)


@app.command("full")
def report_full(date_from: str = _FROM, date_to: str = _TO, fmt: str = _FMT, output: str = _OUT):
    """Export the full report (expenses + income + cash flow)."""
    _generate("full", date_from, date_to, fmt, output)
