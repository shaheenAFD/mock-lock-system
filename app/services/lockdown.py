
from app.database.connection import get_db
from app.services.file_protection import (
    encrypt_device_files,
    decrypt_device_files
)


def activate_lockdown(device_id, user_id):
    # Pastikan device benar-benar milik user
    with get_db() as db:
        device = db.execute(
            """
            SELECT id, locked
            FROM devices
            WHERE id=? AND user_id=?
            """,
            (device_id, user_id)
        ).fetchone()

    if not device:
        raise ValueError("Perangkat tidak ditemukan.")

    if device["locked"]:
        raise ValueError("Perangkat sudah dalam kondisi terkunci.")

    # Enkripsi file terlebih dahulu
    encrypted_count = encrypt_device_files(device_id)

    # Ubah status hanya setelah enkripsi berhasil
    with get_db() as db:
        db.execute(
            """
            UPDATE devices
            SET locked=1, encrypted=1
            WHERE id=? AND user_id=?
            """,
            (device_id, user_id)
        )

    return encrypted_count


def recover_device(device_id, user_id):
    # Pastikan device benar-benar milik user
    with get_db() as db:
        device = db.execute(
            """
            SELECT id, locked
            FROM devices
            WHERE id=? AND user_id=?
            """,
            (device_id, user_id)
        ).fetchone()

    if not device:
        raise ValueError("Perangkat tidak ditemukan.")

    if not device["locked"]:
        raise ValueError("Perangkat belum dalam kondisi terkunci.")

    # Dekripsi file terlebih dahulu
    decrypted_count = decrypt_device_files(device_id)

    # Ubah status hanya setelah dekripsi berhasil
    with get_db() as db:
        db.execute(
            """
            UPDATE devices
            SET locked=0, encrypted=0
            WHERE id=? AND user_id=?
            """,
            (device_id, user_id)
        )

    return decrypted_count