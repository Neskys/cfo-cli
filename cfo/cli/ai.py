"""AI-powered financial insights — coming in v0.5."""

import typer
from rich.console import Console

app = typer.Typer(help="Ask questions about your finances in plain language (powered by LLM).")
console = Console()


@app.callback(invoke_without_command=True)
def ai_root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print("[yellow]AI insights are coming in v0.5[/yellow] — stay tuned!")
        console.print("This feature will use Claude to answer questions like:")
        console.print('  [dim]cfo ai ask "What is my cash runway at current burn rate?"[/dim]')
        console.print("Follow the project: [link=https://github.com/Neskys/cfo-cli]github.com/Neskys/cfo-cli[/link]")
