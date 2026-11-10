import sqlite3
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.database.connection import get_db
from app.security.decorators import login_required
from app.services.audit import log_event


auth_bp = Blueprint("auth", __name__)


# ==========================
# REGISTER
# ==========================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 8:
            flash(
                "Username minimal 3 karakter dan password minimal 8 karakter.",
                "danger"
            )
            return render_template("register.html")

        try:
            with get_db() as db:

                db.execute(
                    """
                    INSERT INTO users
                    (username, password_hash, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        username,
                        generate_password_hash(password),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )

                user_id = db.execute(
                    "SELECT id FROM users WHERE username=?",
                    (username,)
                ).fetchone()["id"]

            log_event(
                user_id,
                "REGISTER",
                "Akun berhasil dibuat."
            )

            flash("Registrasi berhasil. Silakan login.", "success")

            return redirect(url_for("auth.login"))

        except sqlite3.IntegrityError:

            flash("Username sudah digunakan.", "danger")

    return render_template("register.html")


# ==========================
# LOGIN
# ==========================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            ).fetchone()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            log_event(
                user["id"],
                "LOGIN_SUCCESS",
                "Pengguna berhasil login."
            )

            return redirect(url_for("main.index"))

        flash("Username atau password salah.", "danger")

        if user:
            log_event(
                user["id"],
                "LOGIN_FAILED",
                "Percobaan login gagal."
            )

    return render_template("login.html")


# ==========================
# LOGOUT
# ==========================

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():

    user_id = session["user_id"]

    log_event(
        user_id,
        "LOGOUT",
        "Pengguna logout."
    )

    session.clear()

    return redirect(url_for("auth.login"))