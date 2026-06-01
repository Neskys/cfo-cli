"""Main CLI entrypoint."""

import typer
from cfo.cli import budget, expense, forecast, report, ai

app = typer.Typer(
    name="cfo",
    help="[bold]cfo-cli[/bold] — Financial planning for freelancers and small teams.\n\n"
         "Know how far your business can fly. :airplane:",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

app.add_typer(budget.app, name="budget")
app.add_typer(expense.app, name="expense")
app.add_typer(forecast.app, name="forecast")
app.add_typer(report.app, name="report")
app.add_typer(ai.app, name="ai")


@app.command("version")
def version():
    """Show cfo-cli version."""
    from cfo import __version__
    typer.echo(f"cfo-cli v{__version__}")


if __name__ == "__main__":
    app()
