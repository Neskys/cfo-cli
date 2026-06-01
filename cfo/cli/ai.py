"""AI-powered financial insights (powered by Claude)."""

import typer
from rich.console import Console
from rich.panel import Panel

from cfo.services import ai as svc
from cfo.services.ai import AIError, VALID_PROVIDERS
from cfo.core.config import set_api_key, set_provider, set_ai_model, get_provider

app = typer.Typer(help="Ask Claude or OpenAI about your finances (aggregated data only).")
console = Console()


def _show(title: str, text: str):
    console.print(Panel(text, title=title, border_style="cyan"))


def _fail(err: AIError):
    # markup=False so bracketed text like 'cfo-cli[ai]' isn't eaten as Rich markup
    console.print(str(err), style="red", markup=False)
    raise typer.Exit(1)


@app.command("config")
def ai_config(
    api_key: str = typer.Option(..., "--api-key", help="API key for the provider (sk-...)"),
    provider: str = typer.Option(None, "--provider", help="anthropic | openai"),
    model: str = typer.Option(None, "--model", help="Override the provider's default model"),
):
    """Store an API key (and optionally provider/model) in ~/.cfo/config.json."""
    if provider is not None:
        provider = provider.lower()
        if provider not in VALID_PROVIDERS:
            console.print(f"[red]Unknown provider '{provider}'.[/red] Choose: {', '.join(VALID_PROVIDERS)}")
            raise typer.Exit(1)
        set_provider(provider)
    target = provider or get_provider()
    set_api_key(api_key, target)
    if model:
        set_ai_model(model, target)
    masked = f"{api_key[:6]}…{api_key[-4:]}" if len(api_key) > 12 else "set"
    console.print(f"[green]✓[/green] API key saved for [bold]{target}[/bold] ([dim]{masked}[/dim]).")


@app.command("set-provider")
def ai_set_provider(provider: str = typer.Argument(..., help="anthropic | openai")):
    """Switch the active AI provider."""
    provider = provider.lower()
    if provider not in VALID_PROVIDERS:
        console.print(f"[red]Unknown provider '{provider}'.[/red] Choose: {', '.join(VALID_PROVIDERS)}")
        raise typer.Exit(1)
    set_provider(provider)
    console.print(f"[green]✓[/green] AI provider set to [bold]{provider}[/bold].")


@app.command("analyze")
def ai_analyze(
    focus: str = typer.Option("all", "--focus", help="expenses | income | cashflow | all"),
    date_from: str = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
):
    """Analyze your finances with the configured AI provider."""
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
    """Get prioritized, data-grounded suggestions from the configured AI provider."""
    try:
        result = svc.suggest(goal, date_from, date_to)
    except AIError as e:
        _fail(e)
    _show(f"AI suggestions — {goal}", result)
