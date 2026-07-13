"""MCP server integration service."""

from mcp.server.fastmcp import FastMCP

from cfo.core.config import get_mcp_read_write
from cfo.services import expense, income, budget, forecast
from cfo.services import currency as currency_service
from cfo.services.expense import ExpenseError
from cfo.services.income import IncomeError
from cfo.services.budget import BudgetError
from cfo.services.forecast import ForecastError
from cfo.services.currency import CurrencyError

# Initialize FastMCP
mcp = FastMCP("cfo")

# Global flag to allow CLI override
WRITE_ALLOWED = False


def _check_write_permission():
    if not (WRITE_ALLOWED or get_mcp_read_write()):
        raise PermissionError(
            "Write access is disabled for this MCP session. "
            "To enable it, start the server with 'cfo mcp start --read-write' "
            "or set 'mcp_read_write': true in ~/.cfo/config.json."
        )


# Read-only tools

@mcp.tool()
def expense_list(
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    in_base_currency: bool = False,
) -> str:
    """List expenses matching filters. Returns details in base currency if in_base_currency is True."""
    try:
        rows = expense.list_expenses(
            category=category,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            in_base=in_base_currency
        )
        if not rows:
            return "No expenses found matching the criteria."

        result = []
        for r in rows:
            r_dict = dict(r)
            note_str = f" ({r_dict['note']})" if r_dict.get("note") else ""
            result.append(
                f"#{r_dict['id']}: {r_dict['date']} - {r_dict['category'].title()}: "
                f"{r_dict['amount']:.2f} {r_dict['currency']}{note_str}"
            )
        return "\n".join(result)
    except ExpenseError as e:
        return f"Error: {e}"


@mcp.tool()
def expense_summary(
    group_by: str = "category",
    date_from: str | None = None,
    date_to: str | None = None,
    budget_name: str | None = None,
    in_base_currency: bool = False,
) -> str:
    """Summarize expenses by category or month. Compares to budget_name if provided."""
    if group_by not in ("category", "month"):
        return "Error: group_by must be 'category' or 'month'."
    try:
        res = expense.summary(
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
            budget_name=budget_name,
            in_base=in_base_currency
        )
        output = [f"Total Expenses: {res['total']:.2f}"]
        if budget_name:
            output.append(f"Compared against budget: '{budget_name}'")
        output.append("\nBreakdown:")
        for r in res["rows"]:
            budget_part = ""
            if r["budget"] is not None:
                budget_part = f" / Budget: {r['budget']:.2f} ({r['execution']:.1f}% executed)"
            output.append(
                f"  {r['key'].title()}: {r['amount']:.2f} ({r['pct']:.1f}%){budget_part} - "
                f"{r['count']} txn(s)"
            )
        return "\n".join(output)
    except ExpenseError as e:
        return f"Error: {e}"


@mcp.tool()
def income_list(
    source_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    in_base_currency: bool = False,
) -> str:
    """List income entries matching filters. Returns details in base currency if in_base_currency is True."""
    try:
        rows = income.list_entries(
            source_id=source_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            in_base=in_base_currency
        )
        if not rows:
            return "No income entries found matching the criteria."

        result = []
        for r in rows:
            r_dict = dict(r)
            src_str = f" [{r_dict['source_name']}]" if r_dict.get("source_name") else ""
            note_str = f" ({r_dict['note']})" if r_dict.get("note") else ""
            ref_str = f" Ref: {r_dict['invoice_ref']}" if r_dict.get("invoice_ref") else ""
            result.append(
                f"#{r_dict['id']}: {r_dict['date']} - {r_dict['amount']:.2f} {r_dict['currency']}"
                f"{src_str}{ref_str}{note_str}"
            )
        return "\n".join(result)
    except IncomeError as e:
        return f"Error: {e}"


@mcp.tool()
def income_summary(
    group_by: str = "source",
    date_from: str | None = None,
    date_to: str | None = None,
    in_base_currency: bool = False,
) -> str:
    """Summarize income entries by source or month."""
    if group_by not in ("source", "month"):
        return "Error: group_by must be 'source' or 'month'."
    try:
        res = income.summary(
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
            in_base=in_base_currency
        )
        output = [f"Total Income: {res['total']:.2f}", "\nBreakdown:"]
        for r in res["rows"]:
            output.append(f"  {r['key'].title()}: {r['amount']:.2f} ({r['pct']:.1f}%) - {r['count']} txn(s)")
        return "\n".join(output)
    except IncomeError as e:
        return f"Error: {e}"


@mcp.tool()
def budget_list() -> str:
    """List all budgets and their period details."""
    try:
        budgets_list = budget.list_budgets()
        if not budgets_list:
            return "No budgets found."

        result = []
        for b in budgets_list:
            result.append(
                f"'{b['name']}' ({b['period']}) - {b['lines']} line(s), "
                f"created: {b['created_at'][:10]}"
            )
        return "\n".join(result)
    except BudgetError as e:
        return f"Error: {e}"


@mcp.tool()
def budget_view(budget_name: str) -> str:
    """View line items and total amounts of a specific budget."""
    try:
        b = budget.get_budget(budget_name)
        result = [f"Budget: '{b['name']}' ({b['period']})", "Lines:"]
        totals = {}
        for line in b["lines"]:
            result.append(f"  - {line['category'].title()}: {line['amount']:.2f} {line['currency']}")
            totals[line["currency"]] = totals.get(line["currency"], 0.0) + line["amount"]

        total_str = ", ".join(f"{v:,.2f} {k}" for k, v in sorted(totals.items()))
        result.append(f"Total planned: {total_str or '0.00 EUR'}")
        return "\n".join(result)
    except BudgetError as e:
        return f"Error: {e}"


@mcp.tool()
def forecast_run(months: int = 6, scenario: str = "base") -> str:
    """Run a cash flow forecast for the next N months using a scenario (base, optimist, pessimist)."""
    try:
        res = forecast.run(months=months, scenario=scenario)
        output = [
            f"Forecast Scenario: {scenario.upper()} ({months} months)",
            f"Projected Monthly Income (6-mo avg): {res['monthly_income']:.2f} EUR",
            f"Projected Monthly Expense (3-mo avg): {res['monthly_expense']:.2f} EUR",
            "\nProjection Timeline:"
        ]
        for r in res["rows"]:
            output.append(
                f"  {r['month']}: projected income {r['income']:.2f} EUR, "
                f"expense {r['expense']:.2f} EUR | Net: {r['net']:.2f} EUR, "
                f"Cum. Balance: {r['balance']:.2f} EUR"
            )
        return "\n".join(output)
    except ForecastError as e:
        return f"Error: {e}"


@mcp.tool()
def currency_convert(amount: float, currency_from: str, currency_to: str) -> str:
    """Convert an amount from one currency to another using cached rates."""
    try:
        converted = currency_service.convert(amount, currency_from, currency_to)
        return (
            f"{amount:.2f} {currency_from.upper()} is equivalent to "
            f"{converted:.2f} {currency_to.upper()}"
        )
    except CurrencyError as e:
        return f"Error: {e}"


# Write tools

@mcp.tool()
def expense_add(
    category: str,
    amount: float,
    currency: str = "EUR",
    date: str | None = None,
    budget_name: str | None = None,
    note: str | None = None,
) -> str:
    """Add a new expense. category, amount are required. currency defaults to EUR. date is YYYY-MM-DD."""
    try:
        _check_write_permission()
        expense_id = expense.add_expense(
            category=category,
            amount=amount,
            currency=currency,
            on_date=date,
            budget_name=budget_name,
            note=note
        )
        return (
            f"Success: Expense #{expense_id} added under category "
            f"'{category.lower()}' for {amount:.2f} {currency.upper()}."
        )
    except (ExpenseError, PermissionError) as e:
        return f"Error: {e}"


@mcp.tool()
def income_add(
    amount: float,
    source_id: int,
    currency: str = "EUR",
    date: str | None = None,
    invoice_ref: str | None = None,
    note: str | None = None,
) -> str:
    """Add a new income entry. amount, source_id are required. currency defaults to EUR. date is YYYY-MM-DD."""
    try:
        _check_write_permission()
        entry_id = income.add_entry(
            amount=amount,
            source_id=source_id,
            currency=currency,
            on_date=date,
            invoice_ref=invoice_ref,
            note=note
        )
        return (
            f"Success: Income entry #{entry_id} added under source "
            f"#{source_id} for {amount:.2f} {currency.upper()}."
        )
    except (IncomeError, PermissionError) as e:
        return f"Error: {e}"


@mcp.tool()
def budget_create(name: str, period: str = "monthly") -> str:
    """Create a new budget. name is required. period can be monthly, quarterly, or annual."""
    try:
        _check_write_permission()
        budget.create_budget(name=name, period=period)
        return f"Success: Budget '{name}' ({period}) created successfully."
    except (BudgetError, PermissionError) as e:
        return f"Error: {e}"


def start_server():
    """Start the FastMCP stdio server."""
    mcp.run()
