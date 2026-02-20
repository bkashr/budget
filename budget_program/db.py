from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "budget.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_meta(
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS accounts(
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS debts(
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                minimum_payment REAL NULL,
                interest_rate REAL NULL
            );

            CREATE TABLE IF NOT EXISTS fixed_expenses(
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                amount_monthly REAL NOT NULL,
                due_day INT NULL
            );

            CREATE TABLE IF NOT EXISTS allocations(
                id TEXT PRIMARY KEY,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                percent REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions(
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                date_iso TEXT NOT NULL,
                note TEXT NULL,
                category TEXT NULL,
                account_id TEXT NULL
            );

            CREATE TABLE IF NOT EXISTS allocation_events(
                id TEXT PRIMARY KEY,
                transaction_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                amount REAL NOT NULL
            );
            """
        )


def is_onboarded() -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM app_meta WHERE key='onboarded'").fetchone()
        return bool(row and row["value"] == "1")


def set_onboarded() -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO app_meta(key, value) VALUES('onboarded', '1') ON CONFLICT(key) DO UPDATE SET value='1'"
        )
