import mysql.connector
from config import get_db_connection

def update_database():
    conn = get_db_connection()
    if not conn:
        print("[ERROR] Gagal terhubung ke database!")
        return

    cursor = conn.cursor()

    # 1. Tambah kolom 'tanggal' ke tabel laporan_harian jika belum ada
    try:
        cursor.execute("ALTER TABLE laporan_harian ADD COLUMN tanggal DATE NULL AFTER siswa_id;")
        conn.commit()
        print("[SUCCESS] Kolom 'tanggal' berhasil ditambahkan.")
    except mysql.connector.Error as err:
        if err.errno == 1060:
            print("[INFO] Kolom 'tanggal' sudah ada.")
        else:
            print(f"[ERROR tanggal]: {err}")

    # 2. Ubah kolom 'minggu_ke', 'tanggal_mulai', dan 'tanggal_selesai' agar boleh NULL
    try:
        cursor.execute("""
            ALTER TABLE laporan_harian 
            MODIFY COLUMN minggu_ke INT NULL,
            MODIFY COLUMN tanggal_mulai DATE NULL,
            MODIFY COLUMN tanggal_selesai DATE NULL;
        """)
        conn.commit()
        print("[SUCCESS] Kolom 'minggu_ke' & tanggal periode berhasil diubah menjadi NULLable!")
    except mysql.connector.Error as err:
        print(f"[ERROR modify columns]: {err}")

    # 3. Buat tabel pengajuan_absensi jika belum ada
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pengajuan_absensi (
                id INT AUTO_INCREMENT PRIMARY KEY,
                siswa_id INT NOT NULL,
                tanggal DATE NOT NULL,
                jenis ENUM('Izin', 'Sakit') NOT NULL,
                alasan TEXT NOT NULL,
                bukti_file VARCHAR(255) NULL,
                status_pengajuan ENUM('Pending', 'Disetujui', 'Ditolak') DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (siswa_id) REFERENCES siswa(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        print("[SUCCESS] Tabel 'pengajuan_absensi' siap digunakan!")
    except mysql.connector.Error as err:
        print(f"[ERROR pengajuan_absensi]: {err}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    update_database()