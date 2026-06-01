"""Reporting commands (CSV / PDF exports) — coming in v0.4."""

import typer
from rich.console import Console

app = typer.Typer(help="Export financial summaries as CSV or PDF.")
console = Console()


@app.callback(invoke_without_command=True)
def report_root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print("[yellow]Reports (CSV / PDF) are coming in v0.4[/yellow] — stay tuned!")
        console.print("Follow the project: [link=https://github.com/Neskys/cfo-cli]github.com/Neskys/cfo-cli[/link]")
