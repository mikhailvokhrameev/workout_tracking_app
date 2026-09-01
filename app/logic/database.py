from __future__ import annotations
import sqlite3

from app.logic.migration import migrate_json_to_db
from app.logic.schema import create_schema


def open_database(db_path: str, json_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)
    migrate_json_to_db(conn, json_path)
    return conn
