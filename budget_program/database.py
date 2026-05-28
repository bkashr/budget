"""Database helpers and schema initialization for the budget app."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "budget.db"


def connect() -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys enabled and row dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute(query: str, params: tuple = ()) -> int:
    """Execute a write query and return lastrowid."""
    with connect() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def fetchall(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Fetch all rows for a query."""
    with connect() as conn:
        return conn.execute(query, params).fetchall()


def fetchone(query: str, params: tuple = ()) -> sqlite3.Row | None:
    """Fetch one row for a query."""
    with connect() as conn:
        return conn.execute(query, params).fetchone()


def init_db() -> None:
    """Create all tables needed by the budget program."""
    schema_statements = [
        """
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            institution TEXT,
            type TEXT NOT NULL,
            balance REAL NOT NULL,
            interest_rate REAL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS debts(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            institution TEXT,
            type TEXT NOT NULL,
            balance REAL NOT NULL,
            interest_rate REAL,
            min_payment REAL,
            due_day INTEGER,
            created_at TEXT NOT NULL
        )
        """,
        # Flexible-spending categories. allocation_pct is a share of "spendable"
        # money (income left after subscriptions and goal savings are reserved).
        """
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            parent_id INTEGER,
            allocation_pct REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(parent_id) REFERENCES categories(id)
        )
        """,
        # Actual money received. No fixed cadence is required: log a paycheck,
        # tips, a side gig, anything, whenever it lands.
        """
        CREATE TABLE IF NOT EXISTS income_entries(
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            source TEXT,
            note TEXT
        )
        """,
        # Optional expected income used to project the monthly budget and pace
        # goals. Single row (id = 1). Cadence is weekly/biweekly/semimonthly/monthly.
        """
        CREATE TABLE IF NOT EXISTS income_profile(
            id INTEGER PRIMARY KEY CHECK (id = 1),
            expected_amount REAL,
            cadence TEXT,
            updated_at TEXT NOT NULL
        )
        """,
        # Recurring/consistent spending (subscriptions, memberships, fixed bills).
        # Normalized to a monthly cost and reserved off the top of income.
        """
        CREATE TABLE IF NOT EXISTS recurring_expenses(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            cadence TEXT NOT NULL,
            category_id INTEGER,
            due_day INTEGER,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category_id INTEGER NOT NULL,
            paid_amount REAL NOT NULL DEFAULT 0,
            note TEXT,
            tags TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS account_allocations(
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            account_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS balance_updates(
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            old_balance REAL NOT NULL,
            new_balance REAL NOT NULL,
            note TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS goals(
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            link_type TEXT,
            link_id INTEGER,
            start_amount REAL,
            target_amount REAL,
            target_date TEXT,
            year INTEGER,
            contribution_limit REAL,
            contributed_so_far REAL,
            current_amount_override REAL,
            created_at TEXT NOT NULL
        )
        """,
    ]

    with connect() as conn:
        for stmt in schema_statements:
            conn.execute(stmt)
        conn.commit()


def has_initial_data() -> bool:
    """Return True once the budget has been configured.

    The setup wizard always finishes by saving budget categories, so their
    presence is the signal that onboarding is complete.
    """
    row = fetchone("SELECT COUNT(*) AS c FROM categories")
    return bool(row and row["c"] > 0)
