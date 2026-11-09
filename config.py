import os
import mysql.connector
from mysql.connector import Error

class Config:
    # Pengaturan Database MySQL (Membaca dari Environment Variable Railway, fallback ke localhost)
    MYSQL_HOST = os.environ.get('MYSQLHOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQLUSER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD', '')  # Password kosong untuk lokal
    MYSQL_DB = os.environ.get('MYSQLDATABASE', 'db_jurnal_pkl')
    MYSQL_PORT = int(os.environ.get('MYSQLPORT', 3306))
    
    # Secret key untuk Flask session
    SECRET_KEY = os.environ.get('SECRET_KEY', 'jurnal-pkl-rpl-secret-key-super-aman')
    
    # Pengaturan Upload File
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

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
        print(f"Error saat membuat koneksi ke MySQL: {e}")
        return None

# Skrip pengujian koneksi saat file dieksekusi langsung
if __name__ == '__main__':
    conn = get_db_connection()
    if conn and conn.is_connected():
        print("[SUCCESS] Koneksi database BERHASIL!")
        conn.close()
    else:
        print("[FAILED] Gagal terhubung ke database. Periksa konfigurasi MySQL Anda.")