import shutil
from pathlib import Path
from datetime import datetime
from app.services.file_protection import generate_device_key

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    current_app
)

from app.database.connection import get_db
from app.security.decorators import login_required
from app.services.audit import log_event

from app.services.lockdown import (
    activate_lockdown,
    recover_device as recover_device_service
)

from app.services.tracking import update_device_location


devices_bp = Blueprint("devices", __name__)


# ==========================
# CHECK DEVICE OWNERSHIP
# ==========================

def get_owned_device(device_id):

    with get_db() as db:
        device = db.execute(
            """
            SELECT *
            FROM devices
            WHERE id=? AND user_id=?
            """,
            (device_id, session["user_id"])
        ).fetchone()

    if not device:
        abort(404)

    return device


# ==========================
# ADD DEVICE
# ==========================

@devices_bp.route("/devices/add", methods=["POST"])
@login_required
def add_device():

    name = request.form.get("device_name", "").strip()
    device_type = request.form.get("device_type", "").strip()
    operating_system = request.form.get("operating_system", "").strip()
    location = request.form.get("location", "").strip()

    if not name or not device_type or not operating_system or not location:
        flash(
        "Semua data perangkat wajib diisi.",
        "danger"
        )
        return redirect(url_for("main.index"))

    device_dir = None
    device_id = None

    try:
        # 1. Simpan device dan ambil ID-nya
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO devices
                (
                    user_id,
                    device_name,
                    device_type,
                    operating_system,
                    location,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    name,
                    device_type,
                    operating_system,
                    location,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            device_id = cursor.lastrowid

        # 2. Siapkan direktori device
        device_dir = (
            Path(current_app.config["DEVICE_STORAGE"])
            / f"device_{device_id}"
        )

        documents_dir = device_dir / "Documents"
        encrypted_dir = device_dir / "encrypted"

        documents_dir.mkdir(parents=True, exist_ok=False)
        encrypted_dir.mkdir()

        # 3. Salin file simulasi
        source_file = (
            Path(current_app.root_path).parent
            / "sample_files"
            / "image_test.jpg"
        )

        if not source_file.is_file():
            raise FileNotFoundError(
                "File image_test.jpg tidak ditemukan."
            )

        shutil.copy2(
            source_file,
            documents_dir / "image_test.jpg"
        )

        # 4. Buat kunci enkripsi khusus device
        generate_device_key(device_id)

    except Exception as error:

        # Hapus direktori yang sempat dibuat
        if device_dir and device_dir.exists():
            shutil.rmtree(device_dir, ignore_errors=True)

        # Hapus data device jika proses persiapan gagal
        if device_id is not None:
            with get_db() as db:
                db.execute(
                    "DELETE FROM devices WHERE id = ? AND user_id = ?",
                    (device_id, session["user_id"])
                )

        current_app.logger.exception(
            "Gagal menyiapkan device dan file protection: %s",
            error
        )

        flash(
            "Pendaftaran device gagal. Periksa konfigurasi, "
            "file simulasi, dan master key.",
            "danger"
        )

        return redirect(url_for("main.index"))

    # 5. Catat aktivitas
    log_event(
        session["user_id"],
        "DEVICE_REGISTERED",
        f"Perangkat '{name}' berhasil didaftarkan. "
        f"Storage ID: device_{device_id}. "
        "File simulasi dan kunci enkripsi berhasil disiapkan."
    )

    flash(
        "Device berhasil didaftarkan beserta file dan kunci enkripsinya.",
        "success"
    )

    return redirect(url_for("main.index"))

# ==========================
# REMOTE LOCKDOWN
# ==========================

@devices_bp.route(
    "/devices/<int:device_id>/lock",
    methods=["POST"]
)
@login_required
def lock_device(device_id):

    device = get_owned_device(device_id)

    activate_lockdown(
        device_id,
        session["user_id"]
    )

    log_event(
        session["user_id"],
        "REMOTE_LOCKDOWN",
        f"Simulasi lockdown untuk '{device['device_name']}'. "
        "Status proteksi file ditandai aktif (simulasi)."
    )

    flash(
        "Simulasi lockdown berhasil. Status perangkat sekarang LOCKED.",
        "success"
    )

    return redirect(url_for("main.index"))


# ==========================
# DEVICE RECOVERY
# ==========================

@devices_bp.route(
    "/devices/<int:device_id>/recover",
    methods=["POST"]
)
@login_required
def recover_device(device_id):

    device = get_owned_device(device_id)

    recover_device_service(
        device_id,
        session["user_id"]
    )

    log_event(
        session["user_id"],
        "DEVICE_RECOVERY",
        f"Simulasi pemulihan untuk '{device['device_name']}'. "
        "Status lock dan proteksi file dinonaktifkan."
    )

    flash(
        "Simulasi pemulihan berhasil. Status perangkat kembali aman.",
        "success"
    )

    return redirect(url_for("main.index"))


# ==========================
# UPDATE LOCATION
# ==========================

@devices_bp.route(
    "/devices/<int:device_id>/location",
    methods=["POST"]
)
@login_required
def update_location(device_id):

    device = get_owned_device(device_id)

    location = request.form.get(
        "location",
        ""
    ).strip()

    if not location:
        flash(
            "Lokasi simulasi tidak boleh kosong.",
            "danger"
        )
        return redirect(url_for("main.index"))

    update_device_location(
        device_id,
        session["user_id"],
        location
    )

    log_event(
        session["user_id"],
        "LOCATION_UPDATED",
        f"Lokasi simulasi '{device['device_name']}' diperbarui."
    )

    flash(
        "Lokasi simulasi berhasil diperbarui.",
        "success"
    )

    return redirect(url_for("main.index"))


# ==========================
# DELETE DEVICE
# ==========================

@devices_bp.route(
    "/devices/<int:device_id>/delete",
    methods=["POST"]
)
@login_required
def delete_device(device_id):

    device = get_owned_device(device_id)

    with get_db() as db:
        db.execute(
            """
            DELETE FROM devices
            WHERE id=? AND user_id=?
            """,
            (device_id, session["user_id"])
        )

    log_event(
        session["user_id"],
        "DEVICE_DELETED",
        f"Perangkat '{device['device_name']}' dihapus."
    )

    flash(
        "Perangkat berhasil dihapus.",
        "success"
    )

    return redirect(url_for("main.index"))