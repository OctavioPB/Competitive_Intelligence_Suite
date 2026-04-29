import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_DB = "rivalsense.db"
_DB_PATH = Path(os.getenv("DATABASE_URL", _DEFAULT_DB))
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_conn() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SELECT and return results as a DataFrame.

    Args:
        sql: SQL SELECT statement.
        params: Positional parameters for the query.

    Returns:
        DataFrame with query results; empty DataFrame if no rows match.
    """
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql: str, params: tuple = ()) -> None:
    """Execute a single write statement (INSERT, UPDATE, DELETE).

    Args:
        sql: SQL write statement.
        params: Positional parameters.
    """
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()


def executemany(sql: str, params_list: list[tuple]) -> None:
    """Execute a write statement for multiple rows.

    Args:
        sql: SQL write statement with placeholders.
        params_list: List of parameter tuples, one per row.
    """
    with get_conn() as conn:
        conn.executemany(sql, params_list)
        conn.commit()


def init_schema() -> None:
    """Create all tables and indexes from schema.sql if they do not exist."""
    with get_conn() as conn:
        conn.executescript(_SCHEMA_PATH.read_text())
