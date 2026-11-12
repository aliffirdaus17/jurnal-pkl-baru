from config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

conn = get_db_connection()
if conn:
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Nonaktifkan foreign key checks untuk reset tabel secara bersih
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE absensi;")
        cursor.execute("TRUNCATE TABLE laporan_mingguan;")
        cursor.execute("TRUNCATE TABLE siswa;")
        cursor.execute("TRUNCATE TABLE users;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # 2. Buat password hash yang valid untuk 'password123'
        password_hash = generate_password_hash('password123')

        # 3. Insert Data Users
        users_data = [
            (1, 'siswa1', password_hash, 'Ahmad Siswa', 'siswa'),
            (2, 'pembimbing_pkl', password_hash, 'Budi S.Kom (Guru)', 'pembimbing_pkl'),
            (3, 'pembimbing_ind', password_hash, 'Eko Prasetyo (Industri)', 'pembimbing_industri')
        ]
        
        cursor.executemany(
            "INSERT INTO users (id, username, password, nama, role) VALUES (%s, %s, %s, %s, %s)",
            users_data
        )

        # 4. Insert Data Siswa
        cursor.execute(
            "INSERT INTO siswa (id, user_id, nisn, kelas_jurusan, sekolah) VALUES (1, 1, '0051234567', 'XII RPL 1', 'SMKN 2 Cimahi')"
        )

        conn.commit()
        print("[SUCCESS] Database berhasil di-reset & diisi akun baru!")

        # 5. Uji Coba Pencocokan Password Langsung
        cursor.execute("SELECT * FROM users WHERE username = 'siswa1'")
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], 'password123'):
            print("[VERIFIKASI SUCCESS] Akun 'siswa1' dengan password 'password123' TERVERIFIKASI!")
        else:
            print("[VERIFIKASI FAILED] Verifikasi password gagal.")

    except Exception as e:
        print(f"[ERROR] Gagal mereset database: {e}")
    finally:
        cursor.close()
        conn.close()