import sqlite3
from contextlib import contextmanager
from flask import current_app


@contextmanager
def get_db():
    db_path = current_app.config["DATABASE"]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()