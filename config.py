import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_database_path():
    # Highest priority: explicit DB path
    explicit_path = os.getenv("DATABASE_PATH")
    if explicit_path:
        return explicit_path

    # If Railway volume exists, store SQLite inside it
    volume_mount = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    if volume_mount:
        return str(Path(volume_mount) / "database.db")

    # Local default
    return "database.db"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this")
    DATABASE = _get_database_path()
    PORT = int(os.getenv("PORT", 5000))

    APP_ENV = os.getenv("APP_ENV", "development").lower()
    DEBUG = APP_ENV != "production"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = APP_ENV == "production"