"""Cash flow forecasting commands."""

import typer
from rich.console import Console
from rich import box
from rich.table import Table

from cfo.services import forecast as svc
from cfo.services import forecast_scenario as scen_svc
from cfo.services.forecast import ForecastError
from cfo.formatters.tables import forecast_table, scenarios_table

app = typer.Typer(help="Forecast future cash flow based on trends and scenarios.")
scenario_app = typer.Typer(help="Manage custom forecast scenarios and adjustments.")
app.add_typer(scenario_app, name="scenario")
console = Console()


def _fail(err: ForecastError):
    console.print(f"[red]{err}[/red]")
    raise typer.Exit(1)


@app.command("run")
def forecast_run(
    months: int = typer.Option(6, "--months", help="Number of months to project"),
    scenario: str = typer.Option("base", "--scenario", help="base | optimist | pessimist"),
):
    """Project cash flow from recurring income and recent expenses."""
    try:
        data = svc.run(months, scenario)
    except ForecastError as e:
        _fail(e)
    console.print(
        f"[dim]Monthly projection — income {data['monthly_income']:,.2f} / "
        f"expense {data['monthly_expense']:,.2f}[/dim]"
    )
    console.print(forecast_table(data))


@scenario_app.command("create")
def scenario_create(
    name: str = typer.Option(..., "--name", "-n", help="Scenario name"),
    period_from: str = typer.Option(..., "--from", help="Start date YYYY-MM-DD"),
    period_to: str = typer.Option(..., "--to", help="End date YYYY-MM-DD"),
):
    """Create a custom forecast scenario."""
    try:
        sid = scen_svc.create_scenario(name, period_from, period_to)
    except ForecastError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Scenario [bold]#{sid}[/bold] '{name}' created.")


@scenario_app.command("add-adjustment")
def scenario_add_adjustment(
    scenario_id: int = typer.Argument(..., help="Scenario ID"),
    adj_type: str = typer.Option(..., "--type", help="income | expense"),
    category: str = typer.Option(None, "--category", help="Limit to a category"),
    factor: float = typer.Option(None, "--factor", help="Multiplier, e.g. 1.2"),
    absolute_delta: float = typer.Option(None, "--absolute-delta", help="Flat amount delta"),
    note: str = typer.Option(None, "--note", help="Optional note"),
):
    """Add an adjustment to a scenario."""
    try:
        aid = scen_svc.add_adjustment(scenario_id, adj_type, category, factor, absolute_delta, note)
    except ForecastError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Adjustment [bold]#{aid}[/bold] added to scenario #{scenario_id}.")


@scenario_app.command("list")
def scenario_list():
    """List custom forecast scenarios."""
    rows = scen_svc.list_scenarios()
    if not rows:
        console.print("[yellow]No scenarios.[/yellow] Create one with [bold]cfo forecast scenario create[/bold].")
        return
    console.print(scenarios_table(rows))


@scenario_app.command("view")
def scenario_view(scenario_id: int = typer.Argument(..., help="Scenario ID")):
    """Show a scenario and its adjustments."""
    try:
        data = scen_svc.get_scenario(scenario_id)
    except ForecastError as e:
        _fail(e)
    s = data["scenario"]
    table = Table(title=f"Scenario #{s['id']} — {s['name']}", box=box.ROUNDED)
    table.add_column("Adj", justify="right", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Category")
    table.add_column("Factor", justify="right")
    table.add_column("Δ Abs", justify="right")
    table.add_column("Note", style="dim")
    for a in data["adjustments"]:
        table.add_row(
            str(a["id"]), a["type"], a["category"] or "—",
            "—" if a["factor"] is None else f"{a['factor']:.2f}",
            "—" if a["absolute_delta"] is None else f"{a['absolute_delta']:,.2f}",
            a["note"] or "",
        )
    console.print(f"[dim]Period: {s['period_from']} → {s['period_to']}[/dim]")
    if data["adjustments"]:
        console.print(table)
    else:
        console.print("[yellow]No adjustments yet.[/yellow]")


@scenario_app.command("delete")
def scenario_delete(
    scenario_id: int = typer.Argument(..., help="Scenario ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a scenario and its adjustments."""
    if not yes:
        typer.confirm(f"Delete scenario #{scenario_id} and its adjustments?", abort=True)
    try:
        scen_svc.delete_scenario(scenario_id)
    except ForecastError as e:
        _fail(e)
    console.print(f"[green]✓[/green] Scenario #{scenario_id} deleted.")
