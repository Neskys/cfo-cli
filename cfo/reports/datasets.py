"""Gather and normalize report data from the service layer.

Each dataset is a dict: {"title": str, "headers": list[str], "rows": list[list]}.
"""

from datetime import date as date_cls

from cfo.services import expense, income

REPORT_TYPES = ("expenses", "income", "cashflow", "full")

_UNBOUNDED = 1_000_000


class ReportError(Exception):
    """Validation failure surfaced to the CLI as a clean message."""


def _validate(value):
    if value is None:
        return
    try:
        date_cls.fromisoformat(value)
    except ValueError:
        raise ReportError(f"Invalid date '{value}'. Use YYYY-MM-DD format.")


def expense_dataset(date_from=None, date_to=None) -> dict:
    rows = expense.list_expenses(date_from, date_to, limit=_UNBOUNDED)
    return {
        "title": "Expenses",
        "headers": ["ID", "Date", "Category", "Amount", "Currency", "Note"],
        "rows": [
            [r["id"], r["date"], r["category"], f"{r['amount']:.2f}", r["currency"], r["note"] or ""]
            for r in rows
        ],
    }


def income_dataset(date_from=None, date_to=None) -> dict:
    rows = income.list_entries(date_from, date_to, limit=_UNBOUNDED)
    return {
        "title": "Income",
        "headers": ["ID", "Date", "Source", "Amount", "Currency", "Invoice", "Note"],
        "rows": [
            [r["id"], r["date"], r["source_name"] or "", f"{r['amount']:.2f}",
             r["currency"], r["invoice_ref"] or "", r["note"] or ""]
            for r in rows
        ],
    }


def cashflow_dataset(date_from=None, date_to=None) -> dict:
    inc = {r["key"]: r["amount"] for r in income.summary(date_from, date_to, "month")["rows"]}
    exp = {r["key"]: r["amount"] for r in expense.summary(date_from, date_to, "month")["rows"]}
    rows, balance = [], 0.0
    for month in sorted(set(inc) | set(exp)):
        i, e = inc.get(month, 0.0), exp.get(month, 0.0)
        net = i - e
        balance += net
        rows.append([month, f"{i:.2f}", f"{e:.2f}", f"{net:.2f}", f"{balance:.2f}"])
    return {
        "title": "Monthly cash flow",
        "headers": ["Month", "Income", "Expense", "Net", "Balance"],
        "rows": rows,
    }


def build(report_type, date_from=None, date_to=None) -> list[dict]:
    if report_type not in REPORT_TYPES:
        raise ReportError(f"Unknown report '{report_type}'. Choose from: {', '.join(REPORT_TYPES)}")
    _validate(date_from)
    _validate(date_to)
    builders = {
        "expenses": [expense_dataset],
        "income": [income_dataset],
        "cashflow": [cashflow_dataset],
        "full": [expense_dataset, income_dataset, cashflow_dataset],
    }[report_type]
    return [fn(date_from, date_to) for fn in builders]
