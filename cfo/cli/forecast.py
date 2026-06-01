"""Cash flow forecasting commands — coming in v0.3."""

import typer
from rich.console import Console

app = typer.Typer(help="Forecast future cash flow based on trends and scenarios.")
console = Console()


@app.callback(invoke_without_command=True)
def forecast_root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print("[yellow]Cash flow forecasting is coming in v0.3[/yellow] — stay tuned!")
        console.print("Follow the project: [link=https://github.com/Neskys/cfo-cli]github.com/Neskys/cfo-cli[/link]")
