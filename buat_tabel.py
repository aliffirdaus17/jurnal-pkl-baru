from config import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

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
print("Tabel pengajuan_absensi berhasil dibuat!")
cursor.close()
conn.close()