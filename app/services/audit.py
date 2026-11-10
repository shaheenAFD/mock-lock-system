from datetime import datetime
from app.database.connection import get_db


def log_event(user_id, action, details):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO audit_logs
            (user_id, action, details, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                action,
                details,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )