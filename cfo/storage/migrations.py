"""Numbered schema migrations, applied automatically by init_db().

Each migration is a function taking an open sqlite3.Connection. Register it in
MIGRATIONS with the next free integer key. Never edit an existing migration —
always add a new numbered one.
"""

import sqlite3


def migration_001(conn: sqlite3.Connection) -> None:
    """Add indexes on expenses for faster filtering by date, category, budget."""
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_expenses_date     ON expenses(date);
        CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
        CREATE INDEX IF NOT EXISTS idx_expenses_budget   ON expenses(budget_id);
        """
    )


def migration_002(conn: sqlite3.Connection) -> None:
    """Add income tables (sources + entries) with supporting indexes."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS income_sources (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL UNIQUE,
            client       TEXT,
            is_recurring INTEGER NOT NULL DEFAULT 0,
            recur_every  TEXT,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS income_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id   INTEGER REFERENCES income_sources(id) ON DELETE SET NULL,
            amount      REAL    NOT NULL,
            currency    TEXT    NOT NULL DEFAULT 'EUR',
            date        TEXT    NOT NULL DEFAULT (date('now')),
            invoice_ref TEXT,
            note        TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_income_entries_date   ON income_entries(date);
        CREATE INDEX IF NOT EXISTS idx_income_entries_source ON income_entries(source_id);
        """
    )


MIGRATIONS = {
    1: ("Add expense indexes", migration_001),
    2: ("Add income tables", migration_002),
}


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply every pending migration in order, tracked in schema_migrations."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    for version in sorted(MIGRATIONS):
        if version in applied:
            continue
        name, fn = MIGRATIONS[version]
        fn(conn)
        conn.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
            (version, name),
        )
