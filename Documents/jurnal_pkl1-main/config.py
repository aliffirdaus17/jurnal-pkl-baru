import os
import warnings
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

class Config:
    # Secret key untuk Flask session (diambil dari .env)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-ganti-lewat-env-SECRET_KEY'

    # Konfigurasi Database MySQL (Samakan kunci os.environ.get dengan isi .env)
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', '')
    MYSQL_DB = os.environ.get('DB_NAME', 'db_jurnal_pkl')
    # Mengambil DB_PORT dari .env (Fallback ke MYSQLPORT / 3306)
    MYSQL_PORT = int(os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT') or 3306)

    # Cookie sesi & keamanan HTTP
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 12  # 12 Jam

    # Pengaturan Upload File (Path Absolut)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

if Config.SECRET_KEY.startswith('dev-only') and Config.SESSION_COOKIE_SECURE:
    warnings.warn('SECRET_KEY belum diatur di environment produksi! Sesi bisa dipalsukan.', RuntimeWarning)


def get_db_connection():
    """Fungsi pembantu untuk membuka koneksi ke database MySQL."""
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"[MYSQL ERROR]: {e}")
        return None


if __name__ == '__main__':
    conn = get_db_connection()
    if conn and conn.is_connected():
        print("[SUCCESS] Koneksi database BERHASIL!")
        conn.close()
    else:
        print("[FAILED] Gagal terhubung ke database. Periksa konfigurasi MySQL Anda.")