"""Budget service layer. CLI only parses args and calls this."""

from cfo.storage.database import get_connection, init_db
from cfo.core.models import VALID_PERIODS, VALID_CURRENCIES


class BudgetError(Exception):
    """Validation or lookup failure surfaced as a clean message."""


def create_budget(name: str, period: str = "monthly") -> int:
    if period not in VALID_PERIODS:
        raise BudgetError(f"Invalid period '{period}'. Choose from: {', '.join(VALID_PERIODS)}")
    init_db()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM budgets WHERE name = ?", (name,)).fetchone()
        if existing:
            raise BudgetError(f"Budget '{name}' already exists.")
        cur = conn.execute("INSERT INTO budgets (name, period) VALUES (?, ?)", (name, period))
        return cur.lastrowid


def add_budget_line(budget_name: str, category: str, amount: float, currency: str = "EUR") -> int:
    currency = currency.upper()
    if currency not in VALID_CURRENCIES:
        raise BudgetError(f"Unknown currency '{currency}'. Supported: {', '.join(VALID_CURRENCIES)}")
    if amount <= 0:
        raise BudgetError("Amount must be greater than zero.")
    init_db()
    with get_connection() as conn:
        budget = conn.execute("SELECT id FROM budgets WHERE name = ?", (budget_name,)).fetchone()
        if not budget:
            raise BudgetError(f"Budget '{budget_name}' not found.")
        cur = conn.execute(
            "INSERT INTO budget_lines (budget_id, category, amount, currency) VALUES (?, ?, ?, ?)",
            (budget["id"], category.lower(), amount, currency),
        )
        return cur.lastrowid


def list_budgets() -> list:
    init_db()
    with get_connection() as conn:
        return conn.execute(
            "SELECT b.name, b.period, b.created_at, COUNT(l.id) as lines FROM budgets b "
            "LEFT JOIN budget_lines l ON l.budget_id = b.id GROUP BY b.id ORDER BY b.created_at DESC"
        ).fetchall()


def get_budget(name: str) -> dict:
    init_db()
    with get_connection() as conn:
        budget = conn.execute("SELECT * FROM budgets WHERE name = ?", (name,)).fetchone()
        if not budget:
            raise BudgetError(f"Budget '{name}' not found.")
        lines = conn.execute(
            "SELECT category, amount, currency FROM budget_lines WHERE budget_id = ? ORDER BY category",
            (budget["id"],),
        ).fetchall()
        return {
            "id": budget["id"],
            "name": budget["name"],
            "period": budget["period"],
            "created_at": budget["created_at"],
            "lines": [dict(row) for row in lines]
        }


def delete_budget(name: str) -> None:
    init_db()
    with get_connection() as conn:
        budget = conn.execute("SELECT id FROM budgets WHERE name = ?", (name,)).fetchone()
        if not budget:
            raise BudgetError(f"Budget '{name}' not found.")
        conn.execute("DELETE FROM budgets WHERE id = ?", (budget["id"],))
