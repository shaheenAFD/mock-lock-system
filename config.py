import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    FILE_MASTER_KEY = os.environ.get("FILE_MASTER_KEY")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get(
        "SESSION_COOKIE_SECURE", "False"
    ).lower() == "true"

    DATABASE = os.path.join(BASE_DIR, "instance", "mock_lock.db")

    DEVICE_STORAGE = os.path.join(
        BASE_DIR, "instance", "device_storage"
    )