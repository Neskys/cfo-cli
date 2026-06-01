"""SQLite database setup and connection management."""

import sqlite3
from pathlib import Path

from cfo.storage.migrations import apply_migrations


def get_db_path() -> Path:
    """Return the path to the local database file (~/.cfo/data.db)."""
    db_dir = Path.home() / ".cfo"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "data.db"


def get_connection() -> sqlite3.Connection:
    """Open and return a connection to the local database."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS budgets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                period      TEXT    NOT NULL DEFAULT 'monthly',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS budget_lines (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id   INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
                category    TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                currency    TEXT    NOT NULL DEFAULT 'EUR',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id   INTEGER REFERENCES budgets(id) ON DELETE SET NULL,
                category    TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                currency    TEXT    NOT NULL DEFAULT 'EUR',
                date        TEXT    NOT NULL DEFAULT (date('now')),
                note        TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)
        apply_migrations(conn)
