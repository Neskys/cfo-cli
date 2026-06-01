"""Multi-currency conversion and exchange-rate commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from cfo.services import currency as svc
from cfo.services.currency import CurrencyError
from cfo.core.config import get_base_currency, set_base_currency
from cfo.core.models import VALID_CURRENCIES

app = typer.Typer(help="Convert amounts and manage exchange rates.")
console = Console()


def _fail(err: CurrencyError):
    console.print(f"[red]{err}[/red]")
    raise typer.Exit(1)


@app.command("convert")
def currency_convert(
    amount: float = typer.Option(..., "--amount", "-a", help="Amount to convert"),
    from_cur: str = typer.Option(..., "--from", help="Source currency code"),
    to_cur: str = typer.Option(..., "--to", help="Target currency code"),
):
    """Convert an amount between two currencies."""
    try:
        result = svc.convert(amount, from_cur, to_cur)
    except CurrencyError as e:
        _fail(e)
    console.print(
        f"[green]{amount:,.2f}[/green] {from_cur.upper()} = "
        f"[bold green]{result:,.2f}[/bold green] {to_cur.upper()}"
    )


@app.command("rates")
def currency_rates(
    base: str = typer.Option(None, "--base", help="Base currency (defaults to configured)"),
    refresh: bool = typer.Option(False, "--refresh", help="Force a fresh fetch from the API"),
):
    """Show exchange rates for a base currency."""
    base = (base or get_base_currency()).upper()
    try:
        rows = svc.get_all_rates(base, refresh)
    except CurrencyError as e:
        _fail(e)
    if not rows:
        console.print(f"[yellow]No rates available for {base}.[/yellow]")
        return
    table = Table(title=f"Exchange rates (base {base})", box=box.SIMPLE_HEAD)
    table.add_column("Currency", style="cyan")
    table.add_column("Rate", justify="right", style="green")
    table.add_column("Fetched", style="dim")
    for r in rows:
        table.add_row(r["quote_currency"], f"{r['rate']:,.4f}", r["fetched_at"])
    console.print(table)


@app.command("set-base")
def currency_set_base(currency: str = typer.Argument(..., help="New base currency code")):
    """Set the default base currency (stored in ~/.cfo/config.json)."""
    currency = currency.upper()
    if currency not in VALID_CURRENCIES:
        console.print(f"[red]Unknown currency '{currency}'.[/red] Supported: {', '.join(VALID_CURRENCIES)}")
        raise typer.Exit(1)
    set_base_currency(currency)
    console.print(f"[green]✓[/green] Base currency set to [bold]{currency}[/bold].")
