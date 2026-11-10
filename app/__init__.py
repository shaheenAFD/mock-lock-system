import os
from flask import Flask

from config import Config
from app.database.schema import init_db
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config.from_object(Config)

    # Membuat folder instance jika belum tersedia
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["DEVICE_STORAGE"], exist_ok=True)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY belum dikonfigurasi.")

    csrf.init_app(app)

    # Registrasi Blueprint
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.devices import devices_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(devices_bp)

    # Context processor
    @app.context_processor
    def inject_user():
        from flask import session
        return {
            "current_username": session.get("username")
        }

    # Inisialisasi database
    with app.app_context():
        init_db()

    return app