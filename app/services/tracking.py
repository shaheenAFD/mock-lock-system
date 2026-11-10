from app.database.connection import get_db


def update_device_location(device_id, user_id, location):

    with get_db() as db:
        db.execute(
            """
            UPDATE devices
            SET location=?
            WHERE id=? AND user_id=?
            """,
            (location, device_id, user_id)
        )