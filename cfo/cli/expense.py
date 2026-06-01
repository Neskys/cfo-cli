"""Expense tracking commands."""

import typer
from rich.console import Console
from rich import box
from rich.table import Table

from cfo.services import expense as svc
from cfo.formatters.tables import expenses_table, summary_table

app = typer.Typer(help="Track real expenses and compare against your budget.")
console = Console()


def _fail(err: svc.ExpenseError):
    console.print(f"[red]{err}[/red]")
    raise typer.Exit(1)


@app.command("add")
def expense_add(
    category: str = typer.Option(..., "--category", "-c", help="Expense category"),
    amount: float = typer.Option(..., "--amount", "-a", help="Amount spent"),
    currency: str = typer.Option("EUR", "--currency", help="Currency code (EUR, USD...)"),
    date: str = typer.Option(None, "--date", help="Date YYYY-MM-DD (defaults to today)"),
    budget: str = typer.Option(None, "--budget", help="Link to a budget by name"),
    note: str = typer.Option(None, "--note", help="Optional note"),
):
    """Record a new expense."""
    try:
        eid = svc.add_expense(category, amount, currency, date, budget, note)
    except svc.ExpenseError as e:
        _fail(e)
    console.print(
        f"[green]✓[/green] Expense [bold]#{eid}[/bold] recorded: "
        f"{amount:,.2f} {currency.upper()} ({category.lower()})."
    )


@app.command("list")
def expense_list(
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    limit: int = typer.Option(50, "--limit", help="Max rows to show"),
):
    """List expenses, optionally filtered by date range and category."""
    try:
        rows = svc.list_expenses(date_from, date_to, category, limit)
    except svc.ExpenseError as e:
        _fail(e)
    if not rows:
        console.print("[yellow]No expenses found.[/yellow] Add one with [bold]cfo expense add[/bold].")
        return
    console.print(expenses_table(rows))


@app.command("view")
def expense_view(expense_id: int = typer.Argument(..., help="Expense ID")):
    """Show a single expense in detail."""
    try:
        e = svc.get_expense(expense_id)
    except svc.ExpenseError as err:
        _fail(err)
    table = Table(title=f"Expense #{e['id']}", box=box.ROUNDED, show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("Category", e["category"].title())
    table.add_row("Amount", f"{e['amount']:,.2f} {e['currency']}")
    table.add_row("Date", e["date"])
    table.add_row("Budget ID", str(e["budget_id"]) if e["budget_id"] else "—")
    table.add_row("Note", e["note"] or "—")
    table.add_row("Created", e["created_at"])
    console.print(table)


@app.command("edit")
def expense_edit(
    expense_id: int = typer.Argument(..., help="Expense ID"),
    amount: float = typer.Option(None, "--amount", "-a", help="New amount"),
    category: str = typer.Option(None, "--category", "-c", help="New category"),
    date: str = typer.Option(None, "--date", help="New date YYYY-MM-DD"),
    note: str = typer.Option(None, "--note", help="New note"),
):
    """Edit fields of an existing expense."""
    try:
        svc.edit_expense(expense_id, amount, category, date, note)
    except svc.ExpenseError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Expense [bold]#{expense_id}[/bold] updated.")


@app.command("delete")
def expense_delete(
    expense_id: int = typer.Argument(..., help="Expense ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete an expense."""
    if not yes:
        typer.confirm(f"Delete expense #{expense_id}?", abort=True)
    try:
        svc.delete_expense(expense_id)
    except svc.ExpenseError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Expense #{expense_id} deleted.")


@app.command("summary")
def expense_summary(
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
    group_by: str = typer.Option("category", "--group-by", help="Group by category or month"),
    budget: str = typer.Option(None, "--budget", help="Compare against a budget by name"),
):
    """Summarize expenses with % of total and optional budget execution."""
    try:
        data = svc.summary(date_from, date_to, group_by, budget)
    except svc.ExpenseError as e:
        _fail(e)
    if not data["rows"]:
        console.print("[yellow]No expenses to summarize.[/yellow]")
        return
    console.print(summary_table(data))
