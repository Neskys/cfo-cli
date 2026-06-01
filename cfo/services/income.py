"""Income entry CRUD, summary, and forecasting helpers."""

from datetime import date as date_cls

from cfo.storage.database import get_connection, init_db
from cfo.core.models import VALID_CURRENCIES
from cfo.core.dates import window_cutoff
from cfo.services.income_source import IncomeError


def _validate_date(value: str) -> None:
    try:
        date_cls.fromisoformat(value)
    except ValueError:
        raise IncomeError(f"Invalid date '{value}'. Use YYYY-MM-DD format.")


def _require_source(conn, source_id):
    if source_id is None:
        return
    if not conn.execute("SELECT id FROM income_sources WHERE id = ?", (source_id,)).fetchone():
        raise IncomeError(f"Income source #{source_id} not found.")


def add_entry(amount, source_id=None, currency="EUR", on_date=None, invoice_ref=None, note=None) -> int:
    currency = currency.upper()
    if amount <= 0:
        raise IncomeError("Amount must be greater than zero.")
    if currency not in VALID_CURRENCIES:
        raise IncomeError(f"Unknown currency '{currency}'. Supported: {', '.join(VALID_CURRENCIES)}")
    on_date = on_date or date_cls.today().isoformat()
    _validate_date(on_date)
    init_db()
    with get_connection() as conn:
        _require_source(conn, source_id)
        cur = conn.execute(
            "INSERT INTO income_entries (source_id, amount, currency, date, invoice_ref, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (source_id, amount, currency, on_date, invoice_ref, note),
        )
        return cur.lastrowid


def list_entries(date_from=None, date_to=None, source_id=None, limit=50, in_base=False):
    init_db()
    clauses, params = [], []
    if date_from:
        _validate_date(date_from)
        clauses.append("e.date >= ?")
        params.append(date_from)
    if date_to:
        _validate_date(date_to)
        clauses.append("e.date <= ?")
        params.append(date_to)
    if source_id is not None:
        clauses.append("e.source_id = ?")
        params.append(source_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT e.*, s.name AS source_name FROM income_entries e "
            f"LEFT JOIN income_sources s ON s.id = e.source_id{where} "
            "ORDER BY e.date DESC, e.id DESC LIMIT ?",
            params,
        ).fetchall()
    if in_base:
        from cfo.services import currency
        from cfo.core.config import get_base_currency
        rows = currency.to_base_rows(rows, get_base_currency())
    return rows


def get_entry(entry_id: int):
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT e.*, s.name AS source_name FROM income_entries e "
            "LEFT JOIN income_sources s ON s.id = e.source_id WHERE e.id = ?",
            (entry_id,),
        ).fetchone()
    if not row:
        raise IncomeError(f"Income entry #{entry_id} not found.")
    return row


def edit_entry(entry_id, amount=None, on_date=None, invoice_ref=None, note=None) -> None:
    fields, params = [], []
    if amount is not None:
        if amount <= 0:
            raise IncomeError("Amount must be greater than zero.")
        fields.append("amount = ?")
        params.append(amount)
    if on_date is not None:
        _validate_date(on_date)
        fields.append("date = ?")
        params.append(on_date)
    if invoice_ref is not None:
        fields.append("invoice_ref = ?")
        params.append(invoice_ref)
    if note is not None:
        fields.append("note = ?")
        params.append(note)
    if not fields:
        raise IncomeError("Nothing to update. Provide at least one field to edit.")
    init_db()
    params.append(entry_id)
    with get_connection() as conn:
        if not conn.execute("SELECT id FROM income_entries WHERE id = ?", (entry_id,)).fetchone():
            raise IncomeError(f"Income entry #{entry_id} not found.")
        conn.execute(f"UPDATE income_entries SET {', '.join(fields)} WHERE id = ?", params)


def delete_entry(entry_id: int) -> None:
    init_db()
    with get_connection() as conn:
        if not conn.execute("SELECT id FROM income_entries WHERE id = ?", (entry_id,)).fetchone():
            raise IncomeError(f"Income entry #{entry_id} not found.")
        conn.execute("DELETE FROM income_entries WHERE id = ?", (entry_id,))


def summary(date_from=None, date_to=None, group_by="source", in_base=False) -> dict:
    if group_by not in ("source", "month"):
        raise IncomeError("--group-by must be 'source' or 'month'.")
    init_db()
    base = None
    if in_base:
        from cfo.services import currency
        from cfo.core.config import get_base_currency
        base = get_base_currency()
    clauses, params = [], []
    if date_from:
        _validate_date(date_from)
        clauses.append("e.date >= ?")
        params.append(date_from)
    if date_to:
        _validate_date(date_to)
        clauses.append("e.date <= ?")
        params.append(date_to)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    if group_by == "source":
        key_expr = "COALESCE(s.name, 'Unassigned')"
        join = " LEFT JOIN income_sources s ON s.id = e.source_id"
    else:
        key_expr = "substr(e.date, 1, 7)"
        join = ""
    cur_col = ", e.currency AS currency" if in_base else ""
    group_extra = ", e.currency" if in_base else ""
    with get_connection() as conn:
        raw = conn.execute(
            f"SELECT {key_expr} AS key{cur_col}, SUM(e.amount) AS amount, COUNT(*) AS count "
            f"FROM income_entries e{join}{where} GROUP BY key{group_extra} ORDER BY key",
            params,
        ).fetchall()
    if in_base:
        collapsed = currency.collapse_to_base(raw, base)
        grouped = [{"key": k, "amount": a, "count": c} for k, (a, c) in sorted(collapsed.items())]
    else:
        grouped = raw
    total = sum(r["amount"] for r in grouped) or 0.0
    rows = [
        {
            "key": r["key"],
            "amount": r["amount"],
            "count": r["count"],
            "pct": (r["amount"] / total * 100) if total else 0.0,
        }
        for r in grouped
    ]
    return {"group_by": group_by, "rows": rows, "total": total}


def get_monthly_average(source_id, months=6) -> float:
    """Average monthly income for a source over the last `months` months.

    Consumed by the v0.4 cash-flow forecast for recurring-source projection.
    """
    if months <= 0:
        raise IncomeError("months must be greater than zero.")
    init_db()
    cutoff = window_cutoff(months)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM income_entries "
            "WHERE source_id = ? AND date >= ?",
            (source_id, cutoff),
        ).fetchone()
    return row["total"] / months
