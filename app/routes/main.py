from flask import Blueprint, render_template, session, redirect, url_for

from app.database.connection import get_db


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():

    # Periksa apakah pengguna sudah login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Ambil perangkat milik pengguna
    with get_db() as db:
        devices = db.execute(
            """
            SELECT *
            FROM devices
            WHERE user_id=?
            ORDER BY id DESC
            """,
            (session["user_id"],)
        ).fetchall()

        # Ambil 12 aktivitas terakhir
        logs = db.execute(
            """
            SELECT *
            FROM audit_logs
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 12
            """,
            (session["user_id"],)
        ).fetchall()

    return render_template(
        "dashboard.html",
        devices=devices,
        logs=logs
    )