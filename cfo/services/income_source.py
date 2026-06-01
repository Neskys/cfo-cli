"""Income source CRUD. CLI only parses args and calls this."""

from cfo.storage.database import get_connection, init_db
from cfo.core.models import VALID_RECUR_INTERVALS


class IncomeError(Exception):
    """Validation or lookup failure surfaced to the CLI as a clean message."""


def add_source(name, client=None, is_recurring=False, recur_every=None) -> int:
    if is_recurring and recur_every is None:
        recur_every = "monthly"
    if recur_every is not None:
        recur_every = recur_every.lower()
        if recur_every not in VALID_RECUR_INTERVALS:
            raise IncomeError(
                f"Invalid recur interval '{recur_every}'. "
                f"Choose from: {', '.join(VALID_RECUR_INTERVALS)}"
            )
    init_db()
    with get_connection() as conn:
        if conn.execute("SELECT id FROM income_sources WHERE name = ?", (name,)).fetchone():
            raise IncomeError(f"Income source '{name}' already exists.")
        cur = conn.execute(
            "INSERT INTO income_sources (name, client, is_recurring, recur_every) "
            "VALUES (?, ?, ?, ?)",
            (name, client, 1 if is_recurring else 0, recur_every),
        )
        return cur.lastrowid


def list_sources():
    init_db()
    with get_connection() as conn:
        return conn.execute(
            "SELECT s.*, COUNT(e.id) AS entries, COALESCE(SUM(e.amount), 0) AS total "
            "FROM income_sources s LEFT JOIN income_entries e ON e.source_id = s.id "
            "GROUP BY s.id ORDER BY s.name"
        ).fetchall()


def delete_source(source_id: int) -> None:
    init_db()
    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM income_sources WHERE id = ?", (source_id,)
        ).fetchone():
            raise IncomeError(f"Income source #{source_id} not found.")
        # Keep entries but unlink them (ON DELETE SET NULL is not enforced by default).
        conn.execute("UPDATE income_entries SET source_id = NULL WHERE source_id = ?", (source_id,))
        conn.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
