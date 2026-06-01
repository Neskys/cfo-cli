"""Income tracking commands."""

import typer
from rich.console import Console
from rich import box
from rich.table import Table

from cfo.services import income as svc
from cfo.services import income_source as src_svc
from cfo.services.income_source import IncomeError
from cfo.formatters.tables import sources_table, income_table, income_summary_table

app = typer.Typer(help="Track income sources and revenue entries.")
source_app = typer.Typer(help="Manage income sources (clients, recurring revenue).")
app.add_typer(source_app, name="source")
console = Console()


def _fail(err: IncomeError):
    console.print(f"[red]{err}[/red]")
    raise typer.Exit(1)


@source_app.command("add")
def source_add(
    name: str = typer.Option(..., "--name", "-n", help="Source name, e.g. 'Acme Corp'"),
    client: str = typer.Option(None, "--client", help="Client name"),
    recurring: bool = typer.Option(False, "--recurring", help="Mark as recurring revenue"),
    recur_every: str = typer.Option(None, "--recur-every", help="weekly|monthly|quarterly|annual"),
):
    """Add an income source."""
    try:
        sid = src_svc.add_source(name, client, recurring, recur_every)
    except IncomeError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Income source [bold]#{sid}[/bold] '{name}' added.")


@source_app.command("list")
def source_list():
    """List all income sources."""
    rows = src_svc.list_sources()
    if not rows:
        console.print("[yellow]No income sources.[/yellow] Add one with [bold]cfo income source add[/bold].")
        return
    console.print(sources_table(rows))


@source_app.command("delete")
def source_delete(
    source_id: int = typer.Argument(..., help="Source ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a source (its entries are kept but unlinked)."""
    if not yes:
        typer.confirm(f"Delete income source #{source_id}?", abort=True)
    try:
        src_svc.delete_source(source_id)
    except IncomeError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Income source #{source_id} deleted.")


@app.command("add")
def income_add(
    amount: float = typer.Option(..., "--amount", "-a", help="Amount received"),
    source_id: int = typer.Option(None, "--source-id", help="Link to a source by ID"),
    currency: str = typer.Option("EUR", "--currency", help="Currency code (EUR, USD...)"),
    date: str = typer.Option(None, "--date", help="Date YYYY-MM-DD (defaults to today)"),
    invoice_ref: str = typer.Option(None, "--invoice-ref", help="Invoice reference"),
    note: str = typer.Option(None, "--note", help="Optional note"),
):
    """Record a new income entry."""
    try:
        eid = svc.add_entry(amount, source_id, currency, date, invoice_ref, note)
    except IncomeError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Income [bold]#{eid}[/bold] recorded: {amount:,.2f} {currency.upper()}.")


@app.command("list")
def income_list(
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
    source_id: int = typer.Option(None, "--source-id", help="Filter by source ID"),
    limit: int = typer.Option(50, "--limit", help="Max rows to show"),
):
    """List income entries, optionally filtered."""
    try:
        rows = svc.list_entries(date_from, date_to, source_id, limit)
    except IncomeError as e:
        _fail(e)
    if not rows:
        console.print("[yellow]No income entries.[/yellow] Add one with [bold]cfo income add[/bold].")
        return
    console.print(income_table(rows))


@app.command("view")
def income_view(entry_id: int = typer.Argument(..., help="Income entry ID")):
    """Show a single income entry in detail."""
    try:
        e = svc.get_entry(entry_id)
    except IncomeError as err:
        _fail(err)
    table = Table(title=f"Income #{e['id']}", box=box.ROUNDED, show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("Amount", f"{e['amount']:,.2f} {e['currency']}")
    table.add_row("Date", e["date"])
    table.add_row("Source", e["source_name"] or "—")
    table.add_row("Invoice", e["invoice_ref"] or "—")
    table.add_row("Note", e["note"] or "—")
    table.add_row("Created", e["created_at"])
    console.print(table)


@app.command("edit")
def income_edit(
    entry_id: int = typer.Argument(..., help="Income entry ID"),
    amount: float = typer.Option(None, "--amount", "-a", help="New amount"),
    date: str = typer.Option(None, "--date", help="New date YYYY-MM-DD"),
    invoice_ref: str = typer.Option(None, "--invoice-ref", help="New invoice reference"),
    note: str = typer.Option(None, "--note", help="New note"),
):
    """Edit fields of an existing income entry."""
    try:
        svc.edit_entry(entry_id, amount, date, invoice_ref, note)
    except IncomeError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Income [bold]#{entry_id}[/bold] updated.")


@app.command("delete")
def income_delete(
    entry_id: int = typer.Argument(..., help="Income entry ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete an income entry."""
    if not yes:
        typer.confirm(f"Delete income entry #{entry_id}?", abort=True)
    try:
        svc.delete_entry(entry_id)
    except IncomeError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Income entry #{entry_id} deleted.")


@app.command("summary")
def income_summary(
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
    group_by: str = typer.Option("source", "--group-by", help="Group by source or month"),
):
    """Summarize income with % of total."""
    try:
        data = svc.summary(date_from, date_to, group_by)
    except IncomeError as e:
        _fail(e)
    if not data["rows"]:
        console.print("[yellow]No income to summarize.[/yellow]")
        return
    console.print(income_summary_table(data))
