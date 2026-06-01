"""Reusable Rich table builders for cfo output."""

from rich.table import Table
from rich import box


def expenses_table(rows) -> Table:
    """Build a table listing individual expenses."""
    table = Table(title="Expenses", box=box.SIMPLE_HEAD)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Date", style="cyan")
    table.add_column("Category")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Cur", justify="center")
    table.add_column("Note", style="dim", overflow="fold")
    for r in rows:
        table.add_row(
            str(r["id"]),
            r["date"],
            r["category"].title(),
            f"{r['amount']:,.2f}",
            r["currency"],
            r["note"] or "",
        )
    return table


def sources_table(rows) -> Table:
    """Build a table listing income sources with entry counts and totals."""
    table = Table(title="Income sources", box=box.SIMPLE_HEAD)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Name", style="bold cyan")
    table.add_column("Client", style="dim")
    table.add_column("Recurring", justify="center")
    table.add_column("Entries", justify="right")
    table.add_column("Total", justify="right", style="green")
    for r in rows:
        recur = r["recur_every"] if r["is_recurring"] else "—"
        table.add_row(
            str(r["id"]), r["name"], r["client"] or "—",
            recur, str(r["entries"]), f"{r['total']:,.2f}",
        )
    return table


def income_table(rows) -> Table:
    """Build a table listing individual income entries."""
    table = Table(title="Income", box=box.SIMPLE_HEAD)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Date", style="cyan")
    table.add_column("Source")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Cur", justify="center")
    table.add_column("Invoice", style="dim")
    for r in rows:
        table.add_row(
            str(r["id"]), r["date"], r["source_name"] or "—",
            f"{r['amount']:,.2f}", r["currency"], r["invoice_ref"] or "",
        )
    return table


def income_summary_table(data: dict) -> Table:
    """Build a grouped income summary table with % of total."""
    group_by = data["group_by"]
    header = "Source" if group_by == "source" else "Month"
    table = Table(title=f"Income summary by {group_by}", box=box.ROUNDED, show_footer=True)
    table.add_column(header, style="cyan", footer="TOTAL")
    table.add_column("Amount", justify="right", style="green", footer=f"{data['total']:,.2f}")
    table.add_column("% total", justify="right")
    for row in data["rows"]:
        table.add_row(row["key"], f"{row['amount']:,.2f}", f"{row['pct']:.1f}%")
    return table


def forecast_table(data: dict) -> Table:
    """Build the cash-flow projection table (negative net/balance in red)."""
    table = Table(title=f"Cash flow forecast — {data['scenario']}", box=box.ROUNDED)
    table.add_column("Mes", style="cyan")
    table.add_column("Ingressos", justify="right", style="green")
    table.add_column("Despeses", justify="right", style="red")
    table.add_column("Net", justify="right")
    table.add_column("Balanç acumulat", justify="right")
    for r in data["rows"]:
        net_style = "green" if r["net"] >= 0 else "red"
        bal_style = "green" if r["balance"] >= 0 else "red"
        table.add_row(
            r["month"],
            f"{r['income']:,.2f}",
            f"{r['expense']:,.2f}",
            f"[{net_style}]{r['net']:,.2f}[/{net_style}]",
            f"[{bal_style}]{r['balance']:,.2f}[/{bal_style}]",
        )
    return table


def scenarios_table(rows) -> Table:
    """Build a table listing custom forecast scenarios."""
    table = Table(title="Forecast scenarios", box=box.SIMPLE_HEAD)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Name", style="bold cyan")
    table.add_column("From", style="dim")
    table.add_column("To", style="dim")
    table.add_column("Adjustments", justify="right")
    for r in rows:
        table.add_row(
            str(r["id"]), r["name"], r["period_from"], r["period_to"], str(r["adjustments"])
        )
    return table


def summary_table(data: dict) -> Table:
    """Build a grouped summary table with % of total and optional budget execution.

    Categories or months over budget render their execution in red.
    """
    group_by = data["group_by"]
    has_budget = data["has_budget"]
    header = "Category" if group_by == "category" else "Month"
    table = Table(title=f"Expense summary by {group_by}", box=box.ROUNDED, show_footer=True)
    table.add_column(header, style="cyan", footer="TOTAL")
    table.add_column("Amount", justify="right", style="green", footer=f"{data['total']:,.2f}")
    table.add_column("% total", justify="right")
    if has_budget:
        table.add_column("Budget", justify="right")
        table.add_column("Execution", justify="right")
    for row in data["rows"]:
        key = row["key"].title() if group_by == "category" else row["key"]
        cells = [key, f"{row['amount']:,.2f}", f"{row['pct']:.1f}%"]
        if has_budget:
            if row["budget"] is None:
                cells += ["—", "—"]
            else:
                exec_pct = row["execution"]
                style = "red" if exec_pct > 100 else "green"
                cells += [f"{row['budget']:,.2f}", f"[{style}]{exec_pct:.1f}%[/{style}]"]
        table.add_row(*cells)
    return table
