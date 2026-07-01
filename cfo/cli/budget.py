"""Budget planning commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from cfo.core.models import VALID_PERIODS, VALID_CURRENCIES
from cfo.services import budget as svc
from cfo.services.budget import BudgetError

app = typer.Typer(help="Manage budgets: create, view, and plan financial periods.")
console = Console()


@app.command("create")
def budget_create(
    name: str = typer.Argument(..., help="Budget name, e.g. 'Q3 2026'"),
    period: str = typer.Option("monthly", "--period", "-p", help="Period: monthly, quarterly, annual"),
):
    """Create a new budget for a given period."""
    if period not in VALID_PERIODS:
        console.print(f"[red]Invalid period '{period}'.[/red] Choose from: {', '.join(VALID_PERIODS)}")
        raise typer.Exit(1)
    try:
        svc.create_budget(name, period)
    except BudgetError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] Budget [bold]{name}[/bold] ({period}) created.")


@app.command("add-line")
def budget_add_line(
    name: str = typer.Argument(..., help="Budget name"),
    category: str = typer.Option(..., "--category", "-c", help="Line category, e.g. 'salaries'"),
    amount: float = typer.Option(..., "--amount", "-a", help="Planned amount"),
    currency: str = typer.Option("EUR", "--currency", help="Currency code (EUR, USD, GBP...)"),
):
    """Add a line item to a budget."""
    currency = currency.upper()
    if currency not in VALID_CURRENCIES:
        console.print(f"[red]Unknown currency '{currency}'.[/red] Supported: {', '.join(VALID_CURRENCIES)}")
        raise typer.Exit(1)
    if amount <= 0:
        console.print("[red]Amount must be greater than zero.[/red]")
        raise typer.Exit(1)
    try:
        svc.add_budget_line(name, category, amount, currency)
    except BudgetError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] Added [bold]{category}[/bold]: {amount:,.2f} {currency} → '{name}'")


@app.command("view")
def budget_view(
    name: str = typer.Argument(..., help="Budget name"),
):
    """View all line items in a budget."""
    try:
        b = svc.get_budget(name)
    except BudgetError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    table = Table(
        title=f"Budget: {name}  [{b['period']}]",
        box=box.ROUNDED,
        show_footer=True,
    )
    table.add_column("Category", style="cyan", footer="TOTAL")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Currency", justify="center")

    totals: dict[str, float] = {}
    for line in b["lines"]:
        table.add_row(line["category"].title(), f"{line['amount']:,.2f}", line["currency"])
        totals[line["currency"]] = totals.get(line["currency"], 0.0) + line["amount"]

    total_str = "  |  ".join(f"{v:,.2f} {k}" for k, v in sorted(totals.items()))
    table.columns[1].footer = total_str

    if not b["lines"]:
        console.print(f"[yellow]No line items yet.[/yellow] Use [bold]cfo budget add-line '{name}'[/bold] to add one.")
    else:
        console.print(table)


@app.command("list")
def budget_list():
    """List all budgets."""
    try:
        budgets = svc.list_budgets()
    except BudgetError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not budgets:
        console.print("[yellow]No budgets found.[/yellow] Create one with [bold]cfo budget create[/bold].")
        return

    table = Table(title="Budgets", box=box.SIMPLE_HEAD)
    table.add_column("Name", style="bold cyan")
    table.add_column("Period", style="dim")
    table.add_column("Lines", justify="right")
    table.add_column("Created", style="dim")

    for b in budgets:
        table.add_row(b["name"], b["period"], str(b["lines"]), b["created_at"][:10])

    console.print(table)


@app.command("delete")
def budget_delete(
    name: str = typer.Argument(..., help="Budget name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a budget and all its line items."""
    try:
        # Check budget existence first
        svc.get_budget(name)
        if not yes:
            typer.confirm(f"Delete budget '{name}' and all its data?", abort=True)
        svc.delete_budget(name)
    except BudgetError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] Budget '{name}' deleted.")
