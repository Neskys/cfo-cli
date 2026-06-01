"""Expense tracking commands — coming in v0.2."""

import typer
from rich.console import Console

app = typer.Typer(help="Track real expenses and compare against your budget.")
console = Console()


@app.callback(invoke_without_command=True)
def expense_root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print("[yellow]Expense tracking is coming in v0.2[/yellow] — stay tuned!")
        console.print("Follow the project: [link=https://github.com/Neskys/cfo-cli]github.com/Neskys/cfo-cli[/link]")
