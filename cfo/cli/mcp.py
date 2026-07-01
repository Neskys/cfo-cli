"""Model Context Protocol (MCP) server commands."""

import typer
from rich.console import Console

from cfo.core.config import get_mcp_read_write, set_mcp_read_write

app = typer.Typer(help="Manage and run the Model Context Protocol (MCP) server.")
console = Console()
console_err = Console(stderr=True)


@app.command("start")
def mcp_start(
    read_write: bool = typer.Option(
        False, "--read-write", help="Enable write tools (expenses/income/budgets additions) for this session"
    )
):
    """Start the stdio-based MCP server."""
    try:
        from cfo.services import mcp_server
    except ImportError as e:
        console_err.print(
            f"[red]Failed to load MCP server dependencies:[/red] {e}\n"
            "Please install the mcp extra: [bold]pip install -e '.[mcp]'[/bold]"
        )
        raise typer.Exit(1)

    if read_write:
        mcp_server.WRITE_ALLOWED = True
        console_err.print("[yellow]WARNING: Write access is enabled for this MCP session.[/yellow]")
    else:
        config_allowed = get_mcp_read_write()
        if config_allowed:
            console_err.print("[yellow]WARNING: Write access is enabled via ~/.cfo/config.json.[/yellow]")
        else:
            console_err.print("[green]Starting MCP server in Read-Only mode.[/green]")

    console_err.print("[green]✓ MCP server running on stdio.[/green]")
    try:
        mcp_server.start_server()
    except Exception as e:
        console_err.print(f"[red]MCP Server error:[/red] {e}")
        raise typer.Exit(1)


@app.command("config")
def mcp_config(
    read_write: bool = typer.Option(None, "--read-write", help="Enable write tools by default in configuration"),
    read_only: bool = typer.Option(None, "--read-only", help="Disable write tools by default in configuration"),
):
    """View or configure the default MCP server permissions."""
    if read_write and read_only:
        console.print("[red]Cannot specify both --read-write and --read-only.[/red]")
        raise typer.Exit(1)

    if read_write is not None:
        set_mcp_read_write(True)
        console.print("[green]✓[/green] Default MCP permissions updated to: [bold]Read-Write[/bold].")
    elif read_only is not None:
        set_mcp_read_write(False)
        console.print("[green]✓[/green] Default MCP permissions updated to: [bold]Read-Only[/bold].")
    else:
        status = "Read-Write" if get_mcp_read_write() else "Read-Only (default)"
        console.print(f"Default MCP permissions: [bold]{status}[/bold].")
