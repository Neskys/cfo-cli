"""Budget planning commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from cfo.storage.database import get_connection, init_db
from cfo.core.models import VALID_PERIODS, VALID_CURRENCIES

app = typer.Typer(help="Manage budgets: create, view, and plan financial periods.")
console = Console()


def _require_budget(conn, name: str) -> dict:
    row = conn.execute("SELECT * FROM budgets WHERE name = ?", (name,)).fetchone()
    if not row:
        console.print(f"[red]Budget '{name}' not found.[/red] Run [bold]cfo budget list[/bold] to see all budgets.")
        raise typer.Exit(1)
    return row


@app.command("create")
def budget_create(
    name: str = typer.Argument(..., help="Budget name, e.g. 'Q3 2026'"),
    period: str = typer.Option("monthly", "--period", "-p", help="Period: monthly, quarterly, annual"),
):
    """Create a new budget for a given period."""
    if period not in VALID_PERIODS:
        console.print(f"[red]Invalid period '{period}'.[/red] Choose from: {', '.join(VALID_PERIODS)}")
        raise typer.Exit(1)
    init_db()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM budgets WHERE name = ?", (name,)).fetchone()
        if existing:
            console.print(f"[yellow]Budget '{name}' already exists.[/yellow]")
            raise typer.Exit(1)
        conn.execute("INSERT INTO budgets (name, period) VALUES (?, ?)", (name, period))
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
    init_db()
    with get_connection() as conn:
        budget = _require_budget(conn, name)
        conn.execute(
            "INSERT INTO budget_lines (budget_id, category, amount, currency) VALUES (?, ?, ?, ?)",
            (budget["id"], category.lower(), amount, currency),
        )
    console.print(f"[green]✓[/green] Added [bold]{category}[/bold]: {amount:,.2f} {currency} → '{name}'")


@app.command("view")
def budget_view(
    name: str = typer.Argument(..., help="Budget name"),
):
    """View all line items in a budget."""
    init_db()
    with get_connection() as conn:
        budget = _require_budget(conn, name)
        lines = conn.execute(
            "SELECT category, amount, currency FROM budget_lines WHERE budget_id = ? ORDER BY category",
            (budget["id"],),
        ).fetchall()

    table = Table(
        title=f"Budget: {name}  [{budget['period']}]",
        box=box.ROUNDED,
        show_footer=True,
    )
    table.add_column("Category", style="cyan", footer="TOTAL")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Currency", justify="center")

    totals: dict[str, float] = {}
    for line in lines:
        table.add_row(line["category"].title(), f"{line['amount']:,.2f}", line["currency"])
        totals[line["currency"]] = totals.get(line["currency"], 0.0) + line["amount"]

    total_str = "  |  ".join(f"{v:,.2f} {k}" for k, v in sorted(totals.items()))
    table.columns[1].footer = total_str

    if not lines:
        console.print(f"[yellow]No line items yet.[/yellow] Use [bold]cfo budget add-line '{name}'[/bold] to add one.")
    else:
        console.print(table)


@app.command("list")
def budget_list():
    """List all budgets."""
    init_db()
    with get_connection() as conn:
        budgets = conn.execute(
            "SELECT b.name, b.period, b.created_at, COUNT(l.id) as lines FROM budgets b "
            "LEFT JOIN budget_lines l ON l.budget_id = b.id GROUP BY b.id ORDER BY b.created_at DESC"
        ).fetchall()

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
    init_db()
    with get_connection() as conn:
        budget = _require_budget(conn, name)
        if not yes:
            typer.confirm(f"Delete budget '{name}' and all its data?", abort=True)
        conn.execute("DELETE FROM budgets WHERE id = ?", (budget["id"],))
    console.print(f"[green]✓[/green] Budget '{name}' deleted.")
