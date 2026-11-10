import os
import uuid

from datetime import datetime
from pathlib import Path

from flask import current_app
from cryptography.fernet import Fernet, InvalidToken

from app.database.connection import get_db


# ==========================
# MASTER KEY
# ==========================

def get_master_cipher():

    master_key = current_app.config.get("FILE_MASTER_KEY")

    if not master_key:
        raise RuntimeError(
            "FILE_MASTER_KEY belum dikonfigurasi."
        )

    try:
        return Fernet(master_key.encode("ascii"))

    except (ValueError, UnicodeEncodeError) as error:
        raise RuntimeError(
            "FILE_MASTER_KEY tidak valid."
        ) from error


# ==========================
# GENERATE DEVICE KEY
# ==========================

def generate_device_key(device_id):

    master_cipher = get_master_cipher()

    with get_db() as db:

        # Memastikan device tersedia
        device = db.execute(
            """
            SELECT id
            FROM devices
            WHERE id = ?
            """,
            (device_id,)
        ).fetchone()

        if not device:
            raise ValueError("Device tidak ditemukan.")

        # Periksa apakah device sudah memiliki kunci
        existing_key = db.execute(
            """
            SELECT encrypted_key
            FROM device_encryption_keys
            WHERE device_id = ?
            """,
            (device_id,)
        ).fetchone()

        if existing_key:
            # Jangan membuat kunci baru jika sudah ada
            return master_cipher.decrypt(
                existing_key["encrypted_key"].encode("ascii")
            )

        # Membuat kunci Fernet unik
        device_key = Fernet.generate_key()

        # Melindungi kunci dengan master key
        protected_key = master_cipher.encrypt(device_key)

        db.execute(
            """
            INSERT INTO device_encryption_keys
            (device_id, encrypted_key, created_at)
            VALUES (?, ?, ?)
            """,
            (
                device_id,
                protected_key.decode("ascii"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

    return device_key


# ==========================
# GET DEVICE KEY
# ==========================

def get_device_key(device_id):

    master_cipher = get_master_cipher()

    with get_db() as db:

        record = db.execute(
            """
            SELECT encrypted_key
            FROM device_encryption_keys
            WHERE device_id = ?
            """,
            (device_id,)
        ).fetchone()

    if not record:
        raise ValueError(
            "Kunci enkripsi untuk device ini tidak ditemukan."
        )

    try:
        device_key = master_cipher.decrypt(
            record["encrypted_key"].encode("ascii")
        )

        # Memastikan hasilnya merupakan kunci Fernet valid
        Fernet(device_key)

        return device_key

    except (InvalidToken, ValueError) as error:
        raise RuntimeError(
            "Kunci device gagal dibuka. Periksa FILE_MASTER_KEY."
        ) from error


# ==========================
# FILE ENCRYPTION
# ==========================

def encrypt_file(source_path, destination_path, device_key):

    from pathlib import Path

    source = Path(source_path)
    destination = Path(destination_path)

    cipher = Fernet(device_key)

    file_data = source.read_bytes()
    encrypted_data = cipher.encrypt(file_data)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.write_bytes(encrypted_data)


# ==========================
# FILE DECRYPTION
# ==========================

def decrypt_file(source_path, destination_path, device_key):

    from pathlib import Path

    source = Path(source_path)
    destination = Path(destination_path)

    cipher = Fernet(device_key)

    encrypted_data = source.read_bytes()
    decrypted_data = cipher.decrypt(encrypted_data)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.write_bytes(decrypted_data)

    # ==========================
# ENCRYPT DEVICE FILES
# ==========================

def encrypt_device_files(device_id):

    device_key = get_device_key(device_id)

    storage_root = Path(current_app.config["DEVICE_STORAGE"]).resolve()
    device_dir = (storage_root / f"device_{device_id}").resolve()
    encrypted_dir = device_dir / "encrypted"

    # Pastikan direktori device berada di storage utama
    if not device_dir.is_relative_to(storage_root):
        raise ValueError("Lokasi penyimpanan device tidak valid.")

    if not device_dir.is_dir():
        raise FileNotFoundError("Folder device tidak ditemukan.")

    encrypted_dir.mkdir(parents=True, exist_ok=True)

    encrypted_count = 0

    for folder_name in ("Documents", "Pictures"):

        source_dir = device_dir / folder_name

        if not source_dir.is_dir():
            continue

        for source in source_dir.rglob("*"):

            if source.is_symlink() or not source.is_file():
                continue

            relative_path = source.relative_to(device_dir)

            destination = (
                encrypted_dir
                / f"{relative_path.as_posix()}.enc"
            )

            if destination.exists():
                raise FileExistsError(
                    f"File terenkripsi sudah ada: {destination}"
                )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            temp_path = destination.with_name(
                f".{destination.name}.{uuid.uuid4().hex}.tmp"
            )

            try:
                encrypt_file(
                    source,
                    temp_path,
                    device_key
                )

                # Verifikasi hasil enkripsi
                original_data = source.read_bytes()
                encrypted_data = temp_path.read_bytes()

                verified_data = Fernet(device_key).decrypt(
                    encrypted_data
                )

                if original_data != verified_data:
                    raise RuntimeError(
                        "Verifikasi enkripsi gagal."
                    )

                os.replace(temp_path, destination)
                source.unlink()

                encrypted_count += 1

            finally:
                if temp_path.exists():
                    temp_path.unlink()

    return encrypted_count

# ==========================
# DECRYPT DEVICE FILES
# ==========================

def decrypt_device_files(device_id):

    device_key = get_device_key(device_id)

    device_dir = (
        Path(current_app.config["DEVICE_STORAGE"])
        / f"device_{device_id}"
    ).resolve()

    encrypted_dir = device_dir / "encrypted"

    if not encrypted_dir.is_dir():
        raise FileNotFoundError(
            "Folder encrypted tidak ditemukan."
        )

    decrypted_count = 0

    for encrypted_file in encrypted_dir.rglob("*.enc"):

        if encrypted_file.is_symlink() or not encrypted_file.is_file():
            continue

        relative_path = encrypted_file.relative_to(encrypted_dir)

        original_relative_path = Path(
            str(relative_path)[:-4]
        )

        destination = device_dir / original_relative_path

        if destination.exists():
            raise FileExistsError(
                f"File tujuan sudah ada: {destination}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp_path = destination.with_name(
            f".{destination.name}.{uuid.uuid4().hex}.tmp"
        )

        try:
            decrypt_file(
                encrypted_file,
                temp_path,
                device_key
            )

            # Verifikasi hasil dekripsi
            encrypted_data = encrypted_file.read_bytes()
            decrypted_data = temp_path.read_bytes()

            verified_data = Fernet(device_key).decrypt(
                encrypted_data
            )

            if decrypted_data != verified_data:
                raise RuntimeError(
                    "Verifikasi dekripsi gagal."
                )

            os.replace(temp_path, destination)
            encrypted_file.unlink()

            decrypted_count += 1

        finally:
            if temp_path.exists():
                temp_path.unlink()

    return decrypted_count