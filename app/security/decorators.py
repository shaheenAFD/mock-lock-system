from functools import wraps
from flask import session, flash, redirect, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Silakan login terlebih dahulu.",
                "warning"
            )
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped