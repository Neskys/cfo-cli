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
