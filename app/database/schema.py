
from .connection import get_db


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            operating_system TEXT NOT NULL DEFAULT 'Unknown',
            status TEXT NOT NULL DEFAULT 'Online',
            locked INTEGER NOT NULL DEFAULT 0,
            encrypted INTEGER NOT NULL DEFAULT 0,
            location TEXT NOT NULL DEFAULT 'Lokasi simulasi belum diatur',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id)
                REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id)
                REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS device_encryption_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL UNIQUE,
            encrypted_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(device_id)
                REFERENCES devices(id) ON DELETE CASCADE
        );
        """)

        # Migrasi database lama
        columns = [
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(devices)"
            ).fetchall()
        ]

        if "operating_system" not in columns:
            db.execute("""
                ALTER TABLE devices
                ADD COLUMN operating_system TEXT NOT NULL DEFAULT 'Unknown'
            """)
