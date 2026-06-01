"""AI-powered financial insights (powered by Claude)."""

import typer
from rich.console import Console
from rich.panel import Panel

from cfo.services import ai as svc
from cfo.services.ai import AIError
from cfo.core.config import set_api_key

app = typer.Typer(help="Ask Claude about your finances (aggregated data only).")
console = Console()


def _show(title: str, text: str):
    console.print(Panel(text, title=title, border_style="cyan"))


def _fail(err: AIError):
    # markup=False so bracketed text like 'cfo-cli[ai]' isn't eaten as Rich markup
    console.print(str(err), style="red", markup=False)
    raise typer.Exit(1)


@app.command("config")
def ai_config(api_key: str = typer.Option(..., "--api-key", help="Anthropic API key (sk-...)")):
    """Store your Anthropic API key in ~/.cfo/config.json."""
    set_api_key(api_key)
    masked = f"{api_key[:6]}…{api_key[-4:]}" if len(api_key) > 12 else "set"
    console.print(f"[green]✓[/green] API key saved ([dim]{masked}[/dim]).")


@app.command("analyze")
def ai_analyze(
    focus: str = typer.Option("all", "--focus", help="expenses | income | cashflow | all"),
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
):
    """Analyze your finances with Claude."""
    try:
        result = svc.analyze(focus, date_from, date_to)
    except AIError as e:
        _fail(e)
    _show(f"AI analysis — {focus}", result)


@app.command("anomalies")
def ai_anomalies(
    threshold: float = typer.Option(2.0, "--threshold", help="Z-score threshold"),
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
):
    """Flag anomalous months in your financial series."""
    try:
        result = svc.anomalies(threshold, date_from, date_to)
    except AIError as e:
        _fail(e)
    _show("AI anomalies", result)


@app.command("suggest")
def ai_suggest(
    goal: str = typer.Option(
        "reduce-expenses", "--goal",
        help="reduce-expenses | increase-cashflow | optimize-categories",
    ),
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
):
    """Get prioritized, data-grounded suggestions from Claude."""
    try:
        result = svc.suggest(goal, date_from, date_to)
    except AIError as e:
        _fail(e)
    _show(f"AI suggestions — {goal}", result)
