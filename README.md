# Mock Lock System

- Python
- Flask
- Flask-WTF
- Cryptography (Fernet)
- SQLite
- HTML, CSS, JavaScript

## Persyaratan

Sebelum menjalankan project, instal:

- Python 3.10 atau lebih baru
- Git

## Instalasi Project

### 1. Clone Repository

```bash
git clone URL_REPOSITORY
cd mock_lock_system
```

Ganti `URL_REPOSITORY` dengan URL repository GitHub.

### 2. Membuat Virtual Environment

```bash
python -m venv .venv
```

Aktifkan virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Konfigurasi Environment

Generate SECRET_KEY
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

generate FILE_MASTER_KEY
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Salin `.env.example` menjadi `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Isi nilai SECRET_KEY dan FILE_MASTER_KEY menggunakan key yang dibuat secara lokal.

Jangan mengunggah file `.env` ke repository GitHub.

### 5. Menjalankan Aplikasi

```bash
python run.py
```

Buka aplikasi melalui browser sesuai alamat lokal yang ditampilkan oleh Flask.

## Struktur Project

```text
mock_lock_system/
│
├── app/
│   ├── database/
│   ├── routes/
│   ├── security/
│   └── services/
│
├── instance/
│   └── device storage/
│
├── static/
├── templates/
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── config.py
├── run.py
└── README.md
```

## Aturan Kolaborasi GitHub

Untuk menjaga kestabilan kode utama, seluruh anggota wajib mengikuti aturan berikut:

1. Jangan mengerjakan fitur langsung pada branch `main`.
2. Buat branch baru untuk setiap fitur.
3. Lakukan commit secara berkala.
4. Push pekerjaan ke branch masing-masing.
5. Ajukan Pull Request ke branch `main`.
6. Tunggu review dan persetujuan pemilik repository sebelum merge.

Contoh membuat branch:

```bash
git checkout main
git pull origin main
git checkout -b fitur/nama-fitur
```

## Catatan Keamanan

- Jangan mengunggah `.env` ke GitHub.
- Jangan membagikan SECRET_KEY dan FILE_MASTER_KEY melalui repository.
- Jangan mengunggah database lokal.
- Isi folder `instance/device storage/` merupakan data simulasi lokal dan tidak dibagikan melalui Git.
- Jangan melakukan force push ke branch `main`.

