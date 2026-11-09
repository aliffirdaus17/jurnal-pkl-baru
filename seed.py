from config import get_db_connection

def seed_data():
    conn = get_db_connection()
    if not conn:
        print("Gagal terhubung ke database!")
        return

    cursor = conn.cursor()
    try:
        # Masukkan data dummy untuk tabel users (password: password123)
        query_users = """
        INSERT IGNORE INTO users (id, username, password, nama, role) VALUES 
        (1, 'siswa1', 'scrypt:32768:8:1$vT0cQeFwJ38lK2mL$bc59d749dc5e4d26279f0616edccb45d55b08e2f0d9aa17ff7e13ef51213f5fb47db02901ebc6b245e9eeab8b31a0dc082e6d62ea0b240161a03f8373ef5e0e2', 'Ahmad Siswa', 'siswa'),
        (2, 'pembimbing_pkl', 'scrypt:32768:8:1$vT0cQeFwJ38lK2mL$bc59d749dc5e4d26279f0616edccb45d55b08e2f0d9aa17ff7e13ef51213f5fb47db02901ebc6b245e9eeab8b31a0dc082e6d62ea0b240161a03f8373ef5e0e2', 'Budi S.Kom (Guru)', 'pembimbing_pkl'),
        (3, 'pembimbing_ind', 'scrypt:32768:8:1$vT0cQeFwJ38lK2mL$bc59d749dc5e4d26279f0616edccb45d55b08e2f0d9aa17ff7e13ef51213f5fb47db02901ebc6b245e9eeab8b31a0dc082e6d62ea0b240161a03f8373ef5e0e2', 'Eko Prasetyo (Industri)', 'pembimbing_industri');
        """
        cursor.execute(query_users)

        # Masukkan data dummy untuk tabel siswa
        query_siswa = """
        INSERT IGNORE INTO siswa (user_id, nisn, kelas_jurusan, sekolah) VALUES 
        (1, '0051234567', 'XII RPL 1', 'SMKN 2 Cimahi');
        """
        cursor.execute(query_siswa)

        conn.commit()
        print("[SUCCESS] Data dummy berhasil ditambahkan ke database!")
    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    seed_data()