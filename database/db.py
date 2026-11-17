import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from config import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_DEMO_DB_NAME = "rivalsense_demo.db"
_DEFAULT_DB_NAME = "rivalsense.db"


def _db_path() -> Path:
    """Return the active database path, switching to demo DB when DEMO_MODE=true.

    Read at call time (not import time). Relative paths resolve against the
    repo root; a ``sqlite:///`` prefix on DATABASE_URL is tolerated.
    """
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        return PROJECT_ROOT / _DEMO_DB_NAME

    raw = os.getenv("DATABASE_URL") or _DEFAULT_DB_NAME
    path = Path(raw.removeprefix("sqlite:///"))
    return path if path.is_absolute() else PROJECT_ROOT / path


def get_conn() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set to sqlite3.Row.

    The caller owns the connection and must close it.
    """
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def query_df(sql: str, params: tuple | dict = ()) -> pd.DataFrame:
    """Execute a SELECT and return results as a DataFrame.

    Args:
        sql: SQL SELECT statement.
        params: Positional (tuple) or named (dict) parameters for the query.

    Returns:
        DataFrame with query results; empty DataFrame if no rows match.
    """
    # sqlite3's own context manager only commits — closing() releases the handle.
    with closing(get_conn()) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql: str, params: tuple = ()) -> None:
    """Execute a single write statement (INSERT, UPDATE, DELETE).

    Args:
        sql: SQL write statement.
        params: Positional parameters.
    """
    with closing(get_conn()) as conn, conn:
        conn.execute(sql, params)


def executemany(sql: str, params_list: list[tuple]) -> int:
    """Execute a write statement for multiple rows in one transaction.

    Args:
        sql: SQL write statement with placeholders.
        params_list: List of parameter tuples, one per row.

    Returns:
        Number of rows actually inserted/updated/deleted.
    """
    with closing(get_conn()) as conn, conn:
        return conn.executemany(sql, params_list).rowcount


def init_schema() -> None:
    """Create all tables and indexes from schema.sql if they do not exist."""
    with closing(get_conn()) as conn, conn:
        conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
