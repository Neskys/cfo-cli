"""Expense CRUD and aggregation logic. CLI only parses args and calls this."""

from datetime import date as date_cls

from cfo.storage.database import get_connection, init_db
from cfo.core.models import VALID_CURRENCIES


class ExpenseError(Exception):
    """Validation or lookup failure surfaced to the CLI as a clean message."""


def _validate_date(value: str) -> None:
    try:
        date_cls.fromisoformat(value)
    except ValueError:
        raise ExpenseError(f"Invalid date '{value}'. Use YYYY-MM-DD format.")


def _resolve_budget_id(conn, budget_name: str | None) -> int | None:
    if budget_name is None:
        return None
    row = conn.execute("SELECT id FROM budgets WHERE name = ?", (budget_name,)).fetchone()
    if not row:
        raise ExpenseError(f"Budget '{budget_name}' not found.")
    return row["id"]


def add_expense(category, amount, currency="EUR", on_date=None, budget_name=None, note=None) -> int:
    currency = currency.upper()
    if amount <= 0:
        raise ExpenseError("Amount must be greater than zero.")
    if currency not in VALID_CURRENCIES:
        raise ExpenseError(f"Unknown currency '{currency}'. Supported: {', '.join(VALID_CURRENCIES)}")
    on_date = on_date or date_cls.today().isoformat()
    _validate_date(on_date)
    init_db()
    with get_connection() as conn:
        budget_id = _resolve_budget_id(conn, budget_name)
        cur = conn.execute(
            "INSERT INTO expenses (budget_id, category, amount, currency, date, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (budget_id, category.lower(), amount, currency, on_date, note),
        )
        return cur.lastrowid


def list_expenses(date_from=None, date_to=None, category=None, limit=50):
    init_db()
    clauses, params = [], []
    if date_from:
        _validate_date(date_from)
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        _validate_date(date_to)
        clauses.append("date <= ?")
        params.append(date_to)
    if category:
        clauses.append("category = ?")
        params.append(category.lower())
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    with get_connection() as conn:
        return conn.execute(
            f"SELECT * FROM expenses{where} ORDER BY date DESC, id DESC LIMIT ?", params
        ).fetchall()


def get_expense(expense_id: int):
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not row:
        raise ExpenseError(f"Expense #{expense_id} not found.")
    return row


def edit_expense(expense_id, amount=None, category=None, on_date=None, note=None) -> None:
    fields, params = [], []
    if amount is not None:
        if amount <= 0:
            raise ExpenseError("Amount must be greater than zero.")
        fields.append("amount = ?")
        params.append(amount)
    if category is not None:
        fields.append("category = ?")
        params.append(category.lower())
    if on_date is not None:
        _validate_date(on_date)
        fields.append("date = ?")
        params.append(on_date)
    if note is not None:
        fields.append("note = ?")
        params.append(note)
    if not fields:
        raise ExpenseError("Nothing to update. Provide at least one field to edit.")
    init_db()
    params.append(expense_id)
    with get_connection() as conn:
        if not conn.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,)).fetchone():
            raise ExpenseError(f"Expense #{expense_id} not found.")
        conn.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?", params)


def delete_expense(expense_id: int) -> None:
    init_db()
    with get_connection() as conn:
        if not conn.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,)).fetchone():
            raise ExpenseError(f"Expense #{expense_id} not found.")
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def summary(date_from=None, date_to=None, group_by="category", budget_name=None) -> dict:
    if group_by not in ("category", "month"):
        raise ExpenseError("--group-by must be 'category' or 'month'.")
    init_db()
    clauses, params = [], []
    if date_from:
        _validate_date(date_from)
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        _validate_date(date_to)
        clauses.append("date <= ?")
        params.append(date_to)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    key_expr = "category" if group_by == "category" else "substr(date, 1, 7)"
    with get_connection() as conn:
        grouped = conn.execute(
            f"SELECT {key_expr} AS key, SUM(amount) AS amount, COUNT(*) AS count "
            f"FROM expenses{where} GROUP BY key ORDER BY key",
            params,
        ).fetchall()
        budget_lines, budget_total = {}, 0.0
        if budget_name:
            budget_id = _resolve_budget_id(conn, budget_name)
            for ln in conn.execute(
                "SELECT category, SUM(amount) AS amount FROM budget_lines "
                "WHERE budget_id = ? GROUP BY category",
                (budget_id,),
            ):
                budget_lines[ln["category"]] = ln["amount"]
                budget_total += ln["amount"]
    total = sum(r["amount"] for r in grouped) or 0.0
    rows = []
    for r in grouped:
        entry = {
            "key": r["key"],
            "amount": r["amount"],
            "count": r["count"],
            "pct": (r["amount"] / total * 100) if total else 0.0,
            "budget": None,
            "execution": None,
        }
        if budget_name:
            ref = budget_lines.get(r["key"]) if group_by == "category" else budget_total
            if ref:
                entry["budget"] = ref
                entry["execution"] = r["amount"] / ref * 100
        rows.append(entry)
    return {"group_by": group_by, "rows": rows, "total": total, "has_budget": bool(budget_name)}
