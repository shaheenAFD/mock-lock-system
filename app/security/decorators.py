from functools import wraps

from flask import session, flash, redirect, url_for

from app.database.connection import get_db


def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        user_id = session.get("user_id")

        if not user_id:
            session.clear()

            flash(
                "Silakan login terlebih dahulu.",
                "warning"
            )

            return redirect(url_for("auth.login"))

        # Pastikan user masih terdaftar
        with get_db() as db:

            user = db.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

        if not user:
            session.clear()

            flash(
                "Sesi tidak valid. Silakan login kembali.",
                "warning"
            )

            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped