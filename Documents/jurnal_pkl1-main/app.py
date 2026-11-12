import os
import time
import uuid
import io
import hmac
import secrets
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import date, datetime

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    abort,
    jsonify,
    send_from_directory,
    session,
    url_for,
    send_file
)
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config, get_db_connection

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# =========================================================
# KEAMANAN: CSRF, header respons, pembatasan percobaan login
# =========================================================
def csrf_token():
    """Token CSRF per-sesi; dipakai di template lewat {{ csrf_token() }}."""
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_hex(32)
    return session['_csrf']

app.jinja_env.globals['csrf_token'] = csrf_token

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', 
                           code="403", 
                           title="Akses Ditolak", 
                           message="Anda tidak memiliki hak akses untuk membuka halaman atau file ini."), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                           code="404", 
                           title="Halaman Tidak Ditemukan", 
                           message="Halaman atau file yang Anda cari tidak ditemukan atau telah dipindahkan."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                           code="500", 
                           title="Kesalahan Server", 
                           message="Terjadi masalah internal pada server. Silakan coba beberapa saat lagi."), 500


@app.before_request
def lindungi_csrf():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None
    dikirim = request.form.get('csrf_token') or request.headers.get('X-CSRFToken') or ''
    asli = session.get('_csrf', '')
    if asli and hmac.compare_digest(dikirim, asli):
        return None
    if request.headers.get('X-CSRFToken') is not None or request.is_json:
        return jsonify({'status': 'error', 'message': 'Token keamanan tidak valid.'}), 400
    flash('Sesi formulir kedaluwarsa. Silakan muat ulang halaman dan coba lagi.', 'danger')
    return redirect(request.referrer or url_for('login'))


@app.after_request
def tambah_header_keamanan(resp):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.setdefault('Referrer-Policy', 'same-origin')
    return resp


# Pembatasan login sederhana (in-memory, per proses): 5 gagal / 10 menit per IP+username
LOGIN_MAX_GAGAL = 5
LOGIN_JENDELA_DETIK = 600
_login_gagal = {}

def _kunci_login(username):
    return f"{request.remote_addr}|{username.lower()}"

def login_terkunci(username):
    sekarang = time.time()
    daftar = [t for t in _login_gagal.get(_kunci_login(username), []) if sekarang - t < LOGIN_JENDELA_DETIK]
    _login_gagal[_kunci_login(username)] = daftar
    return len(daftar) >= LOGIN_MAX_GAGAL

def catat_login_gagal(username):
    _login_gagal.setdefault(_kunci_login(username), []).append(time.time())

def reset_login_gagal(username):
    _login_gagal.pop(_kunci_login(username), None)

# =========================================================
# PERBAIKAN: Tentukan Absolute Path & Ekstensi File yang Diizinkan
# =========================================================
# Menyimpan direktori upload secara absolut di folder static/uploads/profil
UPLOAD_FOLDER_PROFIL = os.path.join(app.root_path, 'static', 'uploads', 'profil')
app.config['UPLOAD_FOLDER_PROFIL'] = UPLOAD_FOLDER_PROFIL

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_logged_in():
    return 'logged_in' in session and session['logged_in'] is True

# =========================================================
# HELPER: Auto-Alpa Jika Lewat Jam 15:00 WIB
# =========================================================
# =========================================================
# HELPER: Auto-Alpa Presisi (Senin - Sabtu & Periode PKL)
# =========================================================
def cek_dan_set_alpa_otomatis(siswa_id, today_str):
    waktu_sekarang = datetime.now().time()
    jam_batas_alpa = datetime.strptime("15:00:00", "%H:%M:%S").time()

    # 1. Cek apakah hari ini Minggu (6)
    # Python weekday: Senin(0), Selasa(1), ..., Sabtu(5), Minggu(6)
    today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
    if today_date.weekday() == 6:
        return  # Libur hari Minggu, jangan set Auto-Alpa

    if waktu_sekarang >= jam_batas_alpa:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor(dictionary=True)
        try:
            # 2. Cek apakah hari ini masuk dalam Periode PKL siswa
            cursor.execute("""
                SELECT tgl_mulai_pkl, tgl_selesai_pkl 
                FROM siswa WHERE id = %s
            """, (siswa_id,))
            s_periode = cursor.fetchone()

            if s_periode and s_periode['tgl_mulai_pkl'] and s_periode['tgl_selesai_pkl']:
                if not (s_periode['tgl_mulai_pkl'] <= today_date <= s_periode['tgl_selesai_pkl']):
                    return  # Di luar periode PKL siswa, abaikan Auto-Alpa

            # 3. Cek apakah sudah ada catatan absensi
            cursor.execute("SELECT id FROM absensi WHERE siswa_id = %s AND tanggal = %s", (siswa_id, today_str))
            ada_absensi = cursor.fetchone()

            # 4. Cek pengajuan Izin/Sakit/Terlambat
            cursor.execute("""
                SELECT id FROM pengajuan_absensi 
                WHERE siswa_id = %s AND tanggal = %s AND status_pengajuan IN ('Pending', 'Disetujui')
            """, (siswa_id, today_str))
            ada_pengajuan = cursor.fetchone()

            if not ada_absensi and not ada_pengajuan:
                cursor.execute("""
                    INSERT INTO absensi (siswa_id, tanggal, status, keterangan, is_manual, created_at)
                    VALUES (%s, %s, 'Alpa', 'Otomatis Alpa oleh Sistem (Lewat Jam 15:00 WIB)', 0, NOW())
                """, (siswa_id, today_str))
                conn.commit()

        except Exception as e:
            conn.rollback()
            print(f"[ERROR AUTO ALPA]: {e}")
        finally:
            cursor.close()
            conn.close()

@app.context_processor
def inject_siswa():
    if is_logged_in() and session.get('role') == 'siswa' and session.get('siswa_id'):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT s.*, u.nama, u.username 
                FROM siswa s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.id = %s
            """, (session['siswa_id'],))
            siswa_data = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(siswa=siswa_data)
        except Exception:
            return dict(siswa=None)
    return dict(siswa=None)

@app.route('/')
def index():
    if is_logged_in():
        role = session.get('role')
        if role == 'siswa':
            return redirect(url_for('dashboard_siswa'))
        elif role in ['pembimbing_pkl', 'pembimbing_industri']:
            return redirect(url_for('dashboard_pembimbing'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username dan password wajib diisi!', 'danger')
            return render_template('login.html')

        if login_terkunci(username):
            flash('Terlalu banyak percobaan login. Coba lagi dalam 10 menit.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash('Gagal terhubung ke server database.', 'danger')
            return render_template('login.html')

        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                # -----------------------------------------------------------------
                # 📌 PENGECEKAN STATUS AKUN (is_active)
                # Jika is_active == 0, blokir akses login dan tampilkan notifikasi.
                # -----------------------------------------------------------------
                if user.get('is_active') == 0:
                    flash('Akun Anda telah dinonaktifkan oleh Pembimbing. Silakan hubungi Pembimbing PKL Anda.', 'danger')
                    cursor.close()
                    conn.close()
                    return render_template('login.html')

                # Membersihkan frasa (Guru) atau (Pembimbing) dari nama
                nama_bersih = user['nama'].replace(' (Guru)', '').replace('(Guru)', '').replace(' (Pembimbing)', '').replace('(Pembimbing)', '').strip()

                reset_login_gagal(username)
                session.clear()  # cegah session fixation
                session['logged_in'] = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['nama'] = nama_bersih  # Tersimpan bersih di session
                session['role'] = user['role']

                if user['role'] == 'siswa':
                    cursor.execute("SELECT id FROM siswa WHERE user_id = %s", (user['id'],))
                    siswa_data = cursor.fetchone()
                    if siswa_data:
                        session['siswa_id'] = siswa_data['id']

                # Redirect sesuai role
                if user['role'] == 'siswa':
                    return redirect(url_for('dashboard_siswa'))
                else:
                    return redirect(url_for('dashboard_pembimbing'))
            else:
                catat_login_gagal(username)
                flash('Username atau password salah!', 'danger')
        except mysql.connector.Error as e:
            flash(f'Error Database: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')

@app.route('/dashboard/siswa')
def dashboard_siswa():
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    waktu_lokal = datetime.now()
    today_str = waktu_lokal.strftime('%Y-%m-%d')
    jam_sekarang = waktu_lokal.time()

    # =========================================================================
    # JALANKAN PENGECEKAN AUTO ALPA (Siswa > 15:00 WIB yang Belum Absen)
    # =========================================================================
    cek_dan_set_alpa_otomatis(siswa_id, today_str)

    conn = get_db_connection()
    if conn is None:
        flash('Gagal terhubung ke database.', 'danger')
        return redirect(url_for('login'))

    cursor = conn.cursor(dictionary=True)

    # 1. Detail Data Siswa
    cursor.execute("""
        SELECT s.*, u.nama, u.username 
        FROM siswa s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.id = %s
    """, (siswa_id,))
    detail_siswa = cursor.fetchone()

    # 2. Statistik Validasi Laporan Harian
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COALESCE(SUM(CASE WHEN status_validasi = 'Disetujui' THEN 1 ELSE 0 END), 0) as disetujui,
            COALESCE(SUM(CASE WHEN status_validasi = 'Pending' THEN 1 ELSE 0 END), 0) as pending,
            COALESCE(SUM(CASE WHEN status_validasi = 'Revisi' THEN 1 ELSE 0 END), 0) as revisi
        FROM laporan_harian 
        WHERE siswa_id = %s
    """, (siswa_id,))
    stat_laporan = cursor.fetchone()

    # 3. Statistik Presensi Kehadiran Siswa (Akan langsung ter-update jika Alpa bertambah)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Hadir' THEN 1 ELSE 0 END), 0) as hadir,
            COALESCE(SUM(CASE WHEN status = 'Izin' THEN 1 ELSE 0 END), 0) as izin,
            COALESCE(SUM(CASE WHEN status = 'Sakit' THEN 1 ELSE 0 END), 0) as sakit,
            COALESCE(SUM(CASE WHEN status = 'Alpa' THEN 1 ELSE 0 END), 0) as alpa
        FROM absensi 
        WHERE siswa_id = %s
    """, (siswa_id,))
    stat_absensi = cursor.fetchone()

    # 4. Riwayat Laporan Harian Terbaru
    cursor.execute("""
        SELECT *, TIME_FORMAT(created_at, '%H:%i') as jam_kirim 
        FROM laporan_harian 
        WHERE siswa_id = %s 
        ORDER BY created_at DESC LIMIT 5
    """, (siswa_id,))
    laporan_terbaru = cursor.fetchall()

    # 5. Cek absensi hari ini
    cursor.execute("SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s", (siswa_id, today_str))
    sudah_absen = cursor.fetchone()

    # 6. Pengumuman Pembimbing
    cursor.execute("SELECT * FROM pengumuman_pembimbing ORDER BY id DESC")
    pengumuman_list = cursor.fetchall()

    cursor.close()
    conn.close()

    # Peringatan flash jika belum absen antara jam 09:30 s.d 15:00 WIB
    jam_mulai_notif = datetime.strptime("09:30:00", "%H:%M:%S").time()
    jam_batas_akhir = datetime.strptime("15:00:00", "%H:%M:%S").time()
    
    if not sudah_absen and (jam_mulai_notif <= jam_sekarang < jam_batas_akhir):
        flash('⚠️ Perhatian: Anda belum melakukan absensi hari ini! Waktu presensi tepat waktu (09.30 WIB) telah terlewat.', 'warning')
    elif sudah_absen and sudah_absen['status'] == 'Alpa':
        flash('❌ Anda tercatat ALPA untuk hari ini karena tidak melakukan presensi hingga pukul 15:00 WIB.', 'danger')

    return render_template(
        'dashboard_siswa.html',
        siswa=detail_siswa,
        laporan=stat_laporan,
        absensi=stat_absensi,
        laporan_list=laporan_terbaru,
        pengumuman_list=pengumuman_list
    )


@app.route('/dashboard/pembimbing')
def dashboard_pembimbing():
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak. Silakan login sebagai Pembimbing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Total Siswa
    cursor.execute("SELECT COUNT(*) as total_siswa FROM siswa")
    total_siswa = cursor.fetchone()['total_siswa']

    # 2. Statistik Validasi Laporan Harian
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN status_validasi = 'Pending' THEN 1 ELSE 0 END), 0) as pending,
            COALESCE(SUM(CASE WHEN status_validasi = 'Disetujui' THEN 1 ELSE 0 END), 0) as disetujui,
            COALESCE(SUM(CASE WHEN status_validasi = 'Revisi' THEN 1 ELSE 0 END), 0) as revisi
        FROM laporan_harian
    """)
    stat_laporan = cursor.fetchone()

    # 3. Statistik Absensi Siswa
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Hadir' THEN 1 ELSE 0 END), 0) as total_hadir,
            COALESCE(SUM(CASE WHEN status = 'Izin' THEN 1 ELSE 0 END), 0) as total_izin,
            COALESCE(SUM(CASE WHEN status = 'Sakit' THEN 1 ELSE 0 END), 0) as total_sakit,
            COALESCE(SUM(CASE WHEN status = 'Alpa' THEN 1 ELSE 0 END), 0) as total_alpa
        FROM absensi
    """)
    stat_absensi = cursor.fetchone()

    # 4. Statistik Pengajuan Izin/Sakit Pending
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN status_pengajuan = 'Pending' THEN 1 ELSE 0 END), 0) as pending_izin
        FROM pengajuan_absensi
    """)
    stat_pengajuan = cursor.fetchone()

    # 5. Laporan Harian Terbaru (5 Teratas)
    cursor.execute("""
        SELECT l.*, u.nama as nama_siswa, s.kelas_jurusan 
        FROM laporan_harian l
        JOIN siswa s ON l.siswa_id = s.id
        JOIN users u ON s.user_id = u.id
        ORDER BY l.created_at DESC LIMIT 5
    """)
    laporan_pending = cursor.fetchall()

    # 6. TAMBAHAN: Ambil pengumuman aktif untuk ditampilkan di form dashboard pembimbing
    cursor.execute("SELECT * FROM pengumuman_pembimbing ORDER BY id DESC LIMIT 1")
    pengumuman = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard_pembimbing.html',
        total_siswa=total_siswa,
        laporan=stat_laporan,
        absensi=stat_absensi,
        pengajuan=stat_pengajuan,
        laporan_list=laporan_pending,
        penguman=pengumuman  # Dikirim ke HTML pembimbing
    )


# TAMBAHAN: Rute untuk memproses simpan/perbarui pesan pengumuman dari pembimbing
@app.route('/pembimbing/update-pesan', methods=['POST'])
def update_pesan_pembimbing():
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    pesan_baru = request.form.get('pesan', '').strip()

    if pesan_baru:
        conn = get_db_connection()
        cursor = conn.cursor()
        # INSERT pesan baru ke tabel pengumuman_pembimbing
        cursor.execute("INSERT INTO pengumuman_pembimbing (pesan) VALUES (%s)", (pesan_baru,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Pengumuman baru berhasil dikirim ke seluruh siswa!', 'success')
    else:
        flash('Pesan pengumuman tidak boleh kosong!', 'danger')

    return redirect(url_for('dashboard_pembimbing'))
# =========================================================
# ROUTE PROFIL SISWA
# =========================================================
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        aksi = request.form.get('aksi')

        # 1. PROSES UPDATE DATA PROFIL LENGKAP & FOTO PROFIL
        if aksi == 'update_profil':
            nama = request.form.get('nama', '').strip()
            tempat_lahir = request.form.get('tempat_lahir', '').strip() or None
            tanggal_lahir = request.form.get('tanggal_lahir', '').strip() or None
            jenis_kelamin = request.form.get('jenis_kelamin', '').strip() or None
            kelas_jurusan = request.form.get('kelas_jurusan', '').strip()
            sekolah = request.form.get('sekolah', '').strip()
            no_hp = request.form.get('no_hp', '').strip() or None
            email = request.form.get('email', '').strip() or None
            alamat = request.form.get('alamat', '').strip() or None

            if not nama:
                flash('Nama lengkap wajib diisi!', 'danger')
            else:
                try:
                    # Update nama di tabel users & session agar navbar ter-update
                    cursor.execute("UPDATE users SET nama = %s WHERE id = %s", (nama, user_id))
                    session['nama'] = nama

                    # Handling unggah foto profil jika ada file
                    foto_file = request.files.get('foto_profil')
                    foto_nama = None

                    if foto_file and foto_file.filename != '' and allowed_file(foto_file.filename):
                        os.makedirs(app.config['UPLOAD_FOLDER_PROFIL'], exist_ok=True)
                        
                        ext = foto_file.filename.rsplit('.', 1)[1].lower()
                        timestamp = int(time.time())
                        foto_nama = f"foto_profil_{siswa_id}_{timestamp}.{ext}"
                        
                        foto_path = os.path.join(app.config['UPLOAD_FOLDER_PROFIL'], foto_nama)
                        foto_file.save(foto_path)

                    # Update data siswa di database MySQL (TANPA kolom 'nama')
                    if foto_nama:
                        query_siswa = """
                            UPDATE siswa 
                            SET tempat_lahir = %s, tanggal_lahir = %s, jenis_kelamin = %s,
                                kelas_jurusan = %s, sekolah = %s, no_hp = %s, email = %s, 
                                alamat = %s, foto_profil = %s 
                            WHERE id = %s
                        """
                        cursor.execute(query_siswa, (
                            tempat_lahir, tanggal_lahir, jenis_kelamin,
                            kelas_jurusan, sekolah, no_hp, email,
                            alamat, foto_nama, siswa_id
                        ))
                    else:
                        query_siswa = """
                            UPDATE siswa 
                            SET tempat_lahir = %s, tanggal_lahir = %s, jenis_kelamin = %s,
                                kelas_jurusan = %s, sekolah = %s, no_hp = %s, email = %s, 
                                alamat = %s 
                            WHERE id = %s
                        """
                        cursor.execute(query_siswa, (
                            tempat_lahir, tanggal_lahir, jenis_kelamin,
                            kelas_jurusan, sekolah, no_hp, email,
                            alamat, siswa_id
                        ))

                    conn.commit()
                    flash('Profil berhasil diperbarui!', 'success')
                except mysql.connector.Error as e:
                    conn.rollback()
                    flash(f'Gagal memperbarui profil: {e}', 'danger')

        # 2. PROSES GANTI PASSWORD
        elif aksi == 'ganti_password':
            password_lama = request.form.get('password_lama', '').strip()
            password_baru = request.form.get('password_baru', '').strip()
            konfirmasi_password = request.form.get('konfirmasi_password', '').strip()

            cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()

            if not user_data or not check_password_hash(user_data['password'], password_lama):
                flash('Password lama / NISN yang Anda masukkan salah!', 'danger')
            elif password_baru != konfirmasi_password:
                flash('Konfirmasi password baru tidak cocok!', 'danger')
            elif len(password_baru) < 6:
                flash('Password baru minimal harus 6 karakter!', 'danger')
            else:
                try:
                    hashed_new_pw = generate_password_hash(password_baru)
                    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_new_pw, user_id))
                    conn.commit()
                    flash('Password berhasil diganti! Gunakan password baru Anda saat login berikutnya.', 'success')
                except mysql.connector.Error as e:
                    conn.rollback()
                    flash(f'Gagal mengganti password: {e}', 'danger')

        cursor.close()
        conn.close()
        # WAJIB RETURN REDIRECT SETELAH PROSES POST
        return redirect(url_for('profil'))

    # REQUEST GET: Ambil Data Profil Siswa
    cursor.execute("""
        SELECT s.*, u.nama, u.username 
        FROM siswa s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.id = %s
    """, (siswa_id,))
    detail_siswa = cursor.fetchone()

    cursor.close()
    conn.close()

    # WAJIB RETURN RENDER TEMPLATE SAAT GET
    return render_template('profil.html', siswa=detail_siswa)

@app.route('/siswa')
def daftar_siswa():
    # Validasi otorisasi role khusus pembimbing
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak. Halaman khusus Pembimbing.', 'danger')
        return redirect(url_for('login'))

    # Tangkap parameter filter terpisah dari URL (GET)
    filter_nama = request.args.get('nama', '').strip()
    filter_nisn = request.args.get('nisn', '').strip()
    filter_sekolah = request.args.get('sekolah', '').strip()

    conn = get_db_connection()
    if not conn:
        flash('Gagal terhubung ke database.', 'danger')
        return render_template('siswa.html', siswa_list=[], filter_nama='', filter_nisn='', filter_sekolah='')

    cursor = conn.cursor(dictionary=True)

    try:
        # Query dasar penggabungan tabel siswa dan users
        query = """
            SELECT s.*, u.nama, u.username, u.is_active
            FROM siswa s
            JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []

        # Tambahkan klausa WHERE dinamis berdasarkan input yang terisi
        if filter_nama:
            query += " AND u.nama LIKE %s"
            params.append(f"%{filter_nama}%")

        if filter_nisn:
            query += " AND s.nisn LIKE %s"
            params.append(f"%{filter_nisn}%")

        if filter_sekolah:
            query += " AND s.sekolah LIKE %s"
            params.append(f"%{filter_sekolah}%")

        query += " ORDER BY u.nama ASC"

        cursor.execute(query, tuple(params))
        siswa_list = cursor.fetchall()

    except mysql.connector.Error as e:
        flash(f'Terjadi kesalahan saat mengambil data: {e}', 'danger')
        siswa_list = []
    finally:
        cursor.close()
        conn.close()

    # Kirim variabel filter ke template agar nilai di form tetap bertahan setelah submit
    return render_template(
        'siswa.html',
        siswa_list=siswa_list,
        filter_nama=filter_nama,
        filter_nisn=filter_nisn,
        filter_sekolah=filter_sekolah
    )

@app.route('/siswa/<int:siswa_id>')
def detail_siswa(siswa_id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak. Halaman khusus Pembimbing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

        # Profil Siswa
    cursor.execute("""
        SELECT s.*, u.nama, u.username, u.is_active, u.created_at
        FROM siswa s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """, (siswa_id,))
    siswa = cursor.fetchone()

    if not siswa:
        cursor.close()
        conn.close()
        flash('Data siswa tidak ditemukan!', 'danger')
        return redirect(url_for('daftar_siswa'))

    # Ringkasan Absensi Siswa
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status = 'Hadir' THEN 1 ELSE 0 END) as hadir,
            SUM(CASE WHEN status = 'Izin' THEN 1 ELSE 0 END) as izin,
            SUM(CASE WHEN status = 'Sakit' THEN 1 ELSE 0 END) as sakit,
            SUM(CASE WHEN status = 'Alpa' THEN 1 ELSE 0 END) as alpa
        FROM absensi WHERE siswa_id = %s
    """, (siswa_id,))
    absensi = cursor.fetchone()

    # Total Laporan
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status_validasi = 'Disetujui' THEN 1 ELSE 0 END) as disetujui,
            SUM(CASE WHEN status_validasi = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status_validasi = 'Revisi' THEN 1 ELSE 0 END) as revisi
        FROM laporan_harian WHERE siswa_id = %s
    """, (siswa_id,))
    laporan = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('siswa_detail.html', siswa=siswa, absensi=absensi, laporan=laporan)

import base64

@app.route('/absensi', methods=['GET', 'POST'])
def absensi():
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    today_str = date.today().strftime('%Y-%m-%d')

    # Jalankan pengecekan Auto-Alpa jika waktu sudah >= 15:00 WIB
    cek_dan_set_alpa_otomatis(siswa_id, today_str)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # -------------------------------------------------------------------------
    # VALIDASI BATAS WAKTU JAM PRESENSI
    # -------------------------------------------------------------------------
    jam_sekarang = datetime.now().time()
    jam_buka = datetime.strptime("09:00:00", "%H:%M:%S").time()
    jam_batas_terlambat = datetime.strptime("09:30:00", "%H:%M:%S").time()

    belum_buka = jam_sekarang < jam_buka
    is_terlambat = jam_sekarang >= jam_batas_terlambat

    # 1. Cek absensi hari ini (Termasuk jika sudah di-set Alpa otomatis)
    cursor.execute("SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s", (siswa_id, today_str))
    absensi_hari_ini = cursor.fetchone()

    # 2. Cek status pengajuan terlambat
    cursor.execute("""
        SELECT * FROM pengajuan_absensi 
        WHERE siswa_id = %s AND tanggal = %s AND jenis = 'Terlambat'
        ORDER BY id DESC LIMIT 1
    """, (siswa_id, today_str))
    pengajuan_terlambat = cursor.fetchone()

    # 3. Cek status pengajuan Izin / Sakit
    cursor.execute("""
        SELECT * FROM pengajuan_absensi 
        WHERE siswa_id = %s AND tanggal = %s AND jenis IN ('Izin', 'Sakit')
        ORDER BY id DESC LIMIT 1
    """, (siswa_id, today_str))
    pengajuan_izin_sakit = cursor.fetchone()

    if request.method == 'POST':
        # CEK A: Mencegah absen jika belum pukul 09:00 WIB
        if belum_buka:
            flash('Presensi belum dibuka! Sistem presensi baru dibuka pada pukul 09:00 WIB.', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('absensi'))

        # CEK B: Mencegah absen jika sudah ada di tabel absensi (atau sudah Alpa)
        if absensi_hari_ini:
            if absensi_hari_ini['status'] == 'Alpa':
                flash('Waktu presensi telah ditutup (pukul 15:00 WIB). Anda tercatat Alpa untuk hari ini.', 'danger')
            else:
                flash('Anda sudah menyelesaikan presensi untuk hari ini!', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('absensi'))

        # CEK C: Mencegah double pengajuan jika sudah mengajukan Izin / Sakit
        if pengajuan_izin_sakit:
            status_p = pengajuan_izin_sakit['status_pengajuan']
            jenis_p = pengajuan_izin_sakit['jenis']
            flash(f'Anda sudah mengajukan {jenis_p} untuk hari ini (Status: {status_p}).', 'info')
            cursor.close()
            conn.close()
            return redirect(url_for('absensi'))

        keterangan = request.form.get('keterangan', '').strip()
        foto_base64 = request.form.get('foto_base64')
        lokasi = request.form.get('lokasi', '').strip()

        # KONDISI 1: PENGAJUAN TERLAMBAT BARU (Lewat 09:30 WIB)
        if is_terlambat and not pengajuan_terlambat:
            if not keterangan:
                flash('Alasan keterlambatan wajib diisi!', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('absensi'))

            cursor.execute("""
                INSERT INTO pengajuan_absensi 
                (siswa_id, tanggal, jenis, alasan, status_pengajuan, created_at)
                VALUES (%s, %s, 'Terlambat', %s, 'Pending', NOW())
            """, (siswa_id, today_str, keterangan))
            
            conn.commit()
            flash('Pengajuan terlambat telah dikirim ke Pembimbing. Silakan tunggu persetujuan (ACC).', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('absensi'))

        # KONDISI 2: AMBIL FOTO SELFIE (Pukul 09:00 - 09:30 WIB ATAU Terlambat yang sudah di-ACC)
        else:
            if not foto_base64:
                flash('Gagal! Foto selfie presensi wajib diambil secara langsung.', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('absensi'))

            try:
                filename_db = f"absensi_{siswa_id}_{today_str}_{uuid.uuid4().hex[:6]}.png"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_db)
                
                img_data = foto_base64.split(',')[1]
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(img_data))

                if pengajuan_terlambat and pengajuan_terlambat['status_pengajuan'] == 'Disetujui':
                    ket_simpan = f"Terlambat (ACC Pembimbing): {pengajuan_terlambat['alasan']}"
                else:
                    ket_simpan = "Tepat Waktu"

                cursor.execute("""
                    INSERT INTO absensi (siswa_id, tanggal, status, keterangan, foto_bukti, lokasi, is_manual, created_at) 
                    VALUES (%s, %s, 'Hadir', %s, %s, %s, 0, NOW())
                """, (siswa_id, today_str, ket_simpan, filename_db, lokasi))
                
                conn.commit()
                flash('Presensi selfie berhasil disimpan!', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('riwayat_absensi'))
            except Exception as e:
                conn.rollback()
                flash(f'Gagal memproses presensi: {e}', 'danger')

    cursor.execute("SELECT * FROM siswa WHERE id = %s", (siswa_id,))
    siswa = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('absensi.html',
                           today=today_str, 
                           absensi_hari_ini=absensi_hari_ini,
                           pengajuan_terlambat=pengajuan_terlambat,
                           pengajuan_izin_sakit=pengajuan_izin_sakit,
                           is_terlambat=is_terlambat,
                           siswa=siswa)


@app.route('/absensi/riwayat')
def riwayat_absensi():
    if not is_logged_in():
        return redirect(url_for('login'))

    role = session.get('role')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if role == 'siswa':
        siswa_id = session.get('siswa_id')
        cursor.execute("""
            SELECT 
                a.*, 
                TIME_FORMAT(a.created_at, '%H:%i') AS jam_absen 
            FROM absensi a
            WHERE a.siswa_id = %s 
            ORDER BY a.tanggal DESC
        """, (siswa_id,))
        
        absensi_list = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('riwayat_absensi.html', absensi_list=absensi_list, is_pembimbing=False)

    else:
        filter_tanggal = request.args.get('tanggal', '').strip()
        filter_status = request.args.get('status', '').strip()
        filter_nama = request.args.get('nama_siswa', '').strip()

        query = """
            SELECT 
                a.*, 
                TIME_FORMAT(a.created_at, '%H:%i') AS jam_absen, 
                u.nama AS nama_siswa, 
                s.kelas_jurusan 
            FROM absensi a
            JOIN siswa s ON a.siswa_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []

        if filter_tanggal:
            query += " AND a.tanggal = %s"
            params.append(filter_tanggal)
        if filter_status:
            query += " AND a.status = %s"
            params.append(filter_status)
        if filter_nama:
            query += " AND u.nama LIKE %s"
            params.append(f"%{filter_nama}%")

        query += " ORDER BY a.tanggal DESC, u.nama ASC"

        cursor.execute(query, tuple(params))
        absensi_list = cursor.fetchall()

        # Opsi daftar siswa + sisa kuota toleransi untuk Modal Absen Manual
        cursor.execute("""
            SELECT s.id, u.nama, s.nisn, s.kelas_jurusan,
                   (1 - COUNT(CASE WHEN a.is_manual = 1 THEN 1 END)) AS sisa_toleransi
            FROM siswa s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN absensi a ON s.id = a.siswa_id
            GROUP BY s.id, u.nama, s.nisn, s.kelas_jurusan
            ORDER BY u.nama ASC
        """)
        siswa_list = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template('riwayat_absensi.html', 
                               absensi_list=absensi_list, 
                               is_pembimbing=True, 
                               siswa_list=siswa_list,
                               filter_tanggal=filter_tanggal,
                               filter_status=filter_status,
                               filter_nama=filter_nama)



# Helper validasi ekstensi file upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route untuk menyajikan file gambar dari folder uploads/
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if not is_logged_in():
        abort(403)
    # Siswa hanya boleh melihat file miliknya; pembimbing boleh semua.
    if session.get('role') == 'siswa':
        conn = get_db_connection()
        if not conn:
            abort(503)
        cursor = conn.cursor()
        try:
            sid = session.get('siswa_id')
            cursor.execute("""
                SELECT 1 FROM absensi WHERE siswa_id = %s AND foto_bukti = %s
                UNION SELECT 1 FROM laporan_harian WHERE siswa_id = %s AND foto_bukti = %s
                UNION SELECT 1 FROM pengajuan_absensi WHERE siswa_id = %s AND bukti_file = %s
                UNION SELECT 1 FROM siswa WHERE id = %s AND foto_profil = %s
                LIMIT 1
            """, (sid, filename) * 4)
            if cursor.fetchone() is None:
                abort(403)
        finally:
            cursor.close()
            conn.close()
    resp = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    resp.headers['Cache-Control'] = 'private, max-age=3600'
    return resp

@app.route('/laporan')
def laporan():
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # PERBAIKAN: Gunakan created_at DESC agar aman dari error kolom tanggal
    cursor.execute("""
        SELECT * FROM laporan_harian 
        WHERE siswa_id = %s 
        ORDER BY created_at DESC
    """, (siswa_id,))
    laporan_list = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('laporan.html', laporan_list=laporan_list)

@app.route('/laporan/tambah', methods=['GET', 'POST'])
def laporan_tambah():
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    today_str = date.today().strftime('%Y-%m-%d')
    now = datetime.now()
    is_terlambat = now.hour >= 11

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Cek status absensi hari ini di tabel absensi
    cursor.execute("""
        SELECT status FROM absensi 
        WHERE siswa_id = %s AND tanggal = %s
    """, (siswa_id, today_str))
    absensi_today = cursor.fetchone()
    status_absen = absensi_today['status'].lower() if (absensi_today and absensi_today.get('status')) else None

    # 2. Cek apakah ada data pengajuan (Izin, Sakit, atau Terlambat) hari ini
    cursor.execute("""
        SELECT status_pengajuan, jenis FROM pengajuan_absensi 
        WHERE siswa_id = %s AND tanggal = %s
        ORDER BY created_at DESC LIMIT 1
    """, (siswa_id, today_str))
    pengajuan_today = cursor.fetchone()

    cursor.close()
    conn.close()

    # ==========================================
    # 3. VALIDASI HAK AKSES ISI LAPORAN HARIAN
    # ==========================================
    
    if status_absen == 'hadir':
        pass # Lolos ke proses form / POST laporan
    elif status_absen in ['izin', 'sakit']:
        flash(f'Hari ini Anda tercatat {status_absen.capitalize()}. Anda tidak perlu mengisi laporan harian.', 'warning')
        return redirect(url_for('laporan'))
    elif pengajuan_today:
        status_p = pengajuan_today['status_pengajuan']
        jenis_p = pengajuan_today['jenis']

        if jenis_p in ['Izin', 'Sakit']:
            if status_p == 'Pending':
                flash(f'Pengajuan {jenis_p} Anda sedang menunggu persetujuan Pembimbing.', 'warning')
            elif status_p == 'Disetujui':
                flash(f'Pengajuan {jenis_p} Anda hari ini sudah disetujui. Anda tidak perlu mengisi laporan harian.', 'info')
            elif status_p == 'Ditolak':
                flash(f'Pengajuan {jenis_p} Anda ditolak. Silakan lakukan absensi hadir.', 'danger')
            return redirect(url_for('laporan'))

        elif jenis_p == 'Terlambat':
            if status_p == 'Pending':
                flash('Pengajuan keterlambatan Anda sedang menunggu persetujuan Pembimbing.', 'warning')
                return redirect(url_for('laporan'))
            elif status_p == 'Disetujui' and status_absen != 'hadir':
                flash('Pengajuan terlambat Anda sudah di-ACC! Silakan lakukan absensi foto terlebih dahulu.', 'warning')
                return redirect(url_for('absensi'))
            elif status_p == 'Ditolak':
                flash('Pengajuan keterlambatan Anda ditolak oleh Pembimbing.', 'danger')
                return redirect(url_for('laporan'))
    else:
        flash('Anda belum melakukan Absensi Hadir hari ini! Silakan absen terlebih dahulu sebelum mengisi laporan.', 'danger')
        return redirect(url_for('laporan'))

    # ==========================================
    # 4. PROSES POST & RENDER FORM LAPORAN
    # ==========================================
    if request.method == 'POST':
        tanggal = request.form.get('tanggal', today_str)
        deskripsi_kegiatan = request.form.get('deskripsi_kegiatan', '').strip()
        alasan_terlambat = request.form.get('alasan_terlambat', '').strip()
        file_foto = request.files.get('foto_bukti')

        # Validasi Input Form
        if not tanggal or not deskripsi_kegiatan:
            flash('Tanggal dan Deskripsi Kegiatan wajib diisi!', 'danger')
            return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

        if is_terlambat and not alasan_terlambat:
            flash('Pengiriman terlambat! Harap isi alasan keterlambatan Anda.', 'danger')
            return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        # VALIDASI PENTING: Cek apakah laporan untuk tanggal tersebut sudah pernah dibuat sebelumnya
        cursor.execute("""
            SELECT id FROM laporan_harian 
            WHERE siswa_id = %s AND tanggal = %s
        """, (siswa_id, tanggal))
        existing_laporan = cursor.fetchone()

        if existing_laporan:
            cursor.close()
            conn.close()
            flash(f'Laporan harian untuk tanggal {tanggal} sudah pernah dibuat! Silakan pilih tanggal lain.', 'danger')
            return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

        # Upload Foto Bukti
        filename_db = None
        if file_foto and file_foto.filename != '':
            if not allowed_file(file_foto.filename):
                cursor.close()
                conn.close()
                flash('Format file tidak didukung! Gunakan format PNG, JPG, atau JPEG.', 'danger')
                return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

            original_name = secure_filename(file_foto.filename)
            unique_name = f"{uuid.uuid4().hex}_{original_name}"
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_foto.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            filename_db = unique_name

        try:
            cursor.execute("""
                INSERT INTO laporan_harian 
                (siswa_id, tanggal, deskripsi_kegiatan, foto_bukti, status_validasi, alasan_terlambat)
                VALUES (%s, %s, %s, %s, 'Pending', %s)
            """, (siswa_id, tanggal, deskripsi_kegiatan, filename_db, alasan_terlambat if is_terlambat else None))

            conn.commit()
            flash('Laporan harian berhasil dikirim!', 'success')
            return redirect(url_for('laporan'))

        except Exception as e:
            conn.rollback()
            print(f"[ERROR SAVE LAPORAN]: {e}")
            flash(f'Terjadi kesalahan saat menyimpan laporan: {str(e)}', 'danger')
            return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

        finally:
            cursor.close()
            conn.close()

    return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

@app.route('/laporan/edit/<int:laporan_id>', methods=['GET', 'POST'])
def laporan_edit(laporan_id):
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM laporan_harian WHERE id = %s AND siswa_id = %s", (laporan_id, siswa_id))
    laporan_data = cursor.fetchone()

    if not laporan_data:
        cursor.close()
        conn.close()
        flash('Laporan tidak ditemukan!', 'danger')
        return redirect(url_for('laporan'))

    # ATURAN EDIT: Hanya boleh jika statusnya Pending atau Revisi. Jika Disetujui, tolak total!
    if laporan_data['status_validasi'] == 'Disetujui':
        cursor.close()
        conn.close()
        flash('Laporan yang sudah disetujui oleh pembimbing tidak dapat diubah kembali!', 'danger')
        return redirect(url_for('laporan'))

    if request.method == 'POST':
        tanggal = request.form.get('tanggal', laporan_data['tanggal'])
        deskripsi_kegiatan = request.form.get('deskripsi_kegiatan', '').strip()
        file_foto = request.files.get('foto_bukti')

        # Cek duplikasi tanggal jika tanggal diubah saat edit
        if tanggal != str(laporan_data['tanggal']):
            cursor.execute("""
                SELECT id FROM laporan_harian 
                WHERE siswa_id = %s AND tanggal = %s AND id != %s
            """, (siswa_id, tanggal, laporan_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                flash(f'Laporan untuk tanggal {tanggal} sudah ada! Silakan pilih tanggal lain.', 'danger')
                return render_template('laporan_form.html', is_edit=True, laporan=laporan_data)

        filename_db = laporan_data['foto_bukti']
        if file_foto and file_foto.filename != '':
            if not allowed_file(file_foto.filename):
                cursor.close()
                conn.close()
                flash('Format file tidak didukung! Gunakan PNG, JPG, atau JPEG.', 'danger')
                return render_template('laporan_form.html', is_edit=True, laporan=laporan_data)

            original_name = secure_filename(file_foto.filename)
            unique_name = f"{uuid.uuid4().hex}_{original_name}"
            
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_foto.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            filename_db = unique_name

        try:
            # Jika status sebelumnya 'Revisi', ubah kembali menjadi 'Pending' saat diedit ulang oleh siswa
            new_status = 'Pending' if laporan_data['status_validasi'] == 'Revisi' else laporan_data['status_validasi']

            cursor.execute("""
                UPDATE laporan_harian 
                SET tanggal = %s, deskripsi_kegiatan = %s, foto_bukti = %s, status_validasi = %s
                WHERE id = %s AND siswa_id = %s
            """, (tanggal, deskripsi_kegiatan, filename_db, new_status, laporan_id, siswa_id))
            conn.commit()
            flash('Laporan harian berhasil diperbarui!', 'success')
            return redirect(url_for('laporan'))
        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Gagal mengupdate laporan: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    cursor.close()
    conn.close()
    return render_template('laporan_form.html', is_edit=True, laporan=laporan_data)


@app.route('/laporan/detail/<int:laporan_id>')
def laporan_detail(laporan_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT l.*, u.nama as nama_siswa, s.kelas_jurusan, s.sekolah 
        FROM laporan_harian l
        JOIN siswa s ON l.siswa_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE l.id = %s
    """, (laporan_id,))
    laporan_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not laporan_data:
        flash('Detail laporan tidak ditemukan!', 'danger')
        return redirect(url_for('laporan'))

    return render_template('laporan_detail.html', laporan=laporan_data)


# ==================== MODUL VALIDASI LAPORAN (PEMBIMBING) ====================

@app.route('/laporan/pembimbing')
def validasi_laporan():
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak. Halaman khusus Pembimbing.', 'danger')
        return redirect(url_for('login'))

    filter_status = request.args.get('status', '').strip()
    filter_siswa = request.args.get('siswa_id', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT l.*, u.nama as nama_siswa, s.kelas_jurusan 
        FROM laporan_harian l
        JOIN siswa s ON l.siswa_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE 1=1
    """
    params = []

    if filter_status:
        query += " AND l.status_validasi = %s"
        params.append(filter_status)
    if filter_siswa:
        query += " AND l.siswa_id = %s"
        params.append(filter_siswa)

    # PERBAIKAN: Gunakan l.created_at DESC agar tidak error 1054
    query += " ORDER BY l.created_at DESC"

    cursor.execute(query, tuple(params))
    laporan_list = cursor.fetchall()

    # Opsi filter daftar siswa
    cursor.execute("""
        SELECT s.id, u.nama 
        FROM siswa s 
        JOIN users u ON s.user_id = u.id 
        ORDER BY u.nama ASC
    """)
    dft_siswa = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('validasi_laporan.html', 
                           laporan_list=laporan_list, 
                           dft_siswa=dft_siswa,
                           filter_status=filter_status,
                           filter_siswa=filter_siswa)


@app.route('/laporan/pembimbing/detail/<int:laporan_id>', methods=['GET', 'POST'])
def validasi_detail(laporan_id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak. Halaman khusus Pembimbing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        action = request.form.get('action')
        catatan = request.form.get('catatan_pembimbing', '').strip()

        if action not in ['Disetujui', 'Revisi']:
            flash('Aksi validasi tidak valid!', 'danger')
        else:
            try:
                cursor.execute("""
                    UPDATE laporan_harian 
                    SET status_validasi = %s, catatan_pembimbing = %s 
                    WHERE id = %s
                """, (action, catatan, laporan_id))
                conn.commit()
                flash(f'Laporan harian berhasil diperbarui menjadi {action}!', 'success')
                return redirect(url_for('validasi_laporan'))
            except mysql.connector.Error as e:
                flash(f'Gagal memperbarui status laporan: {e}', 'danger')

    cursor.execute("""
        SELECT l.*, u.nama as nama_siswa, s.kelas_jurusan, s.sekolah, s.nisn 
        FROM laporan_harian l
        JOIN siswa s ON l.siswa_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE l.id = %s
    """, (laporan_id,))
    laporan_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not laporan_data:
        flash('Data laporan tidak ditemukan!', 'danger')
        return redirect(url_for('validasi_laporan'))

    return render_template('validasi_detail.html', laporan=laporan_data)

# ==================== MODUL PENGAJUAN IZIN / SAKIT (SISWA) ====================
# ==================== MODUL PENGAJUAN IZIN / SAKIT (SISWA) ====================
@app.route('/pengajuan-absensi', methods=['GET', 'POST'])
def pengajuan_absensi():
    if not is_logged_in() or session.get('role') != 'siswa':
        flash('Akses ditolak. Silakan login sebagai Siswa.', 'danger')
        return redirect(url_for('login'))

    siswa_id = session.get('siswa_id')
    today_str = date.today().strftime('%Y-%m-%d')
    
    # Jalankan pengecekan Auto-Alpa (jika waktu sudah > 15:00 WIB)
    cek_dan_set_alpa_otomatis(siswa_id, today_str)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Cek status absensi hari ini di tabel absensi (Hadir/Alpa/Izin/Sakit)
    cursor.execute("""
        SELECT status FROM absensi 
        WHERE siswa_id = %s AND tanggal = %s
    """, (siswa_id, today_str))
    absensi_today = cursor.fetchone()
    
    status_absen_hari_ini = absensi_today['status'] if absensi_today else None
    sudah_hadir = True if (status_absen_hari_ini and status_absen_hari_ini.lower() == 'hadir') else False
    sudah_alpa = True if (status_absen_hari_ini and status_absen_hari_ini.lower() == 'alpa') else False

    # 2. Cek apakah sudah pernah mengajukan izin/sakit/terlambat hari ini
    cursor.execute("""
        SELECT id FROM pengajuan_absensi 
        WHERE siswa_id = %s AND tanggal = %s
    """, (siswa_id, today_str))
    pengajuan_today = cursor.fetchone()
    sudah_pengajuan = True if pengajuan_today else False

    if request.method == 'POST':
        # CEK A: Jika sudah Hadir
        if sudah_hadir:
            flash('Anda sudah mengisi absensi hadir hari ini, sehingga tidak dapat mengajukan izin/sakit.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('pengajuan_absensi'))

        # CEK B: Jika sudah ALPA (Waktu habis > 15:00 WIB atau Alpa Manual)
        if sudah_alpa:
            flash('Waktu presensi dan pengajuan telah ditutup. Anda telah tercatat ALPA untuk hari ini.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('pengajuan_absensi'))
        
        # CEK C: Jika sudah ada pengajuan sebelumnya
        if sudah_pengajuan:
            flash('Anda sudah mengirimkan pengajuan untuk hari ini.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('pengajuan_absensi'))

        jenis = request.form.get('jenis')
        alasan = request.form.get('alasan', '').strip()
        file_bukti = request.files.get('bukti_file')

        if jenis not in ['Izin', 'Sakit'] or not alasan:
            flash('Pilih jenis pengajuan dan isi alasan dengan benar!', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('pengajuan_absensi'))

        filename_db = None
        if file_bukti and file_bukti.filename != '':
            if allowed_file(file_bukti.filename):
                original_name = secure_filename(file_bukti.filename)
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_bukti.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                filename_db = unique_name

        try:
            cursor.execute("""
                INSERT INTO pengajuan_absensi (siswa_id, tanggal, jenis, alasan, bukti_file, status_pengajuan, created_at)
                VALUES (%s, %s, %s, %s, %s, 'Pending', NOW())
            """, (siswa_id, today_str, jenis, alasan, filename_db))
            conn.commit()
            flash('Pengajuan Izin/Sakit berhasil dikirim! Menunggu persetujuan Pembimbing.', 'success')
            return redirect(url_for('pengajuan_absensi'))
        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Gagal mengirim pengajuan: {e}', 'danger')

    cursor.execute("SELECT * FROM pengajuan_absensi WHERE siswa_id = %s ORDER BY created_at DESC", (siswa_id,))
    pengajuan_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'pengajuan_absensi.html', 
        pengajuan_list=pengajuan_list, 
        today=today_str,
        sudah_hadir=sudah_hadir,
        sudah_alpa=sudah_alpa, # Variabel baru dikirim ke HTML
        sudah_pengajuan=sudah_pengajuan
    )

# ==================== MODUL CETAK REKAPITULASI ====================

@app.route('/cetak/absensi')
def cetak_absensi():
    if not is_logged_in():
        return redirect(url_for('login'))

    role = session.get('role')
    siswa_id = request.args.get('siswa_id')

    # Jika login sebagai siswa, otomatis cetak absensi sendiri
    if role == 'siswa':
        siswa_id = session.get('siswa_id')
    elif not siswa_id:
        flash('Silakan pilih siswa yang akan dicetak!', 'warning')
        return redirect(url_for('riwayat_absensi'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Detail Siswa
    cursor.execute("""
        SELECT s.*, u.nama, u.username
        FROM siswa s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """, (siswa_id,))
    detail_siswa = cursor.fetchone()

    # 2. Daftar Absensi
    cursor.execute("""
        SELECT * FROM absensi 
        WHERE siswa_id = %s 
        ORDER BY tanggal ASC
    """, (siswa_id,))
    absensi_list = cursor.fetchall()

    # 3. Rekap Total
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status = 'Hadir' THEN 1 ELSE 0 END) as hadir,
            SUM(CASE WHEN status = 'Izin' THEN 1 ELSE 0 END) as izin,
            SUM(CASE WHEN status = 'Sakit' THEN 1 ELSE 0 END) as sakit,
            SUM(CASE WHEN status = 'Alpa' THEN 1 ELSE 0 END) as alpa
        FROM absensi WHERE siswa_id = %s
    """, (siswa_id,))
    rekap = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('cetak_absensi.html', siswa=detail_siswa, absensi_list=absensi_list, rekap=rekap)


@app.route('/cetak/laporan')
def cetak_laporan():
    if not is_logged_in():
        return redirect(url_for('login'))

    role = session.get('role')
    siswa_id = request.args.get('siswa_id')

    if role == 'siswa':
        siswa_id = session.get('siswa_id')
    elif not siswa_id:
        flash('Silakan pilih siswa yang akan dicetak!', 'warning')
        return redirect(url_for('validasi_laporan'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Detail Siswa
    cursor.execute("""
        SELECT s.*, u.nama, u.username
        FROM siswa s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """, (siswa_id,))
    detail_siswa = cursor.fetchone()

    # 2. Daftar Laporan Mingguan
    cursor.execute("""
        SELECT * FROM laporan_harian 
        WHERE siswa_id = %s 
        ORDER BY tanggal ASC
    """, (siswa_id,))
    laporan_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('cetak_laporan.html', siswa=detail_siswa, laporan_list=laporan_list)

# ==================== MODUL PERSETUJUAN ABSENSI (PEMBIMBING) ====================

@app.route('/pembimbing/pengajuan-absensi')
def persetujuan_absensi():
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl']:
        flash('Akses ditolak. Khusus Pembimbing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, u.nama as nama_siswa, s.kelas_jurusan
        FROM pengajuan_absensi p
        JOIN siswa s ON p.siswa_id = s.id
        JOIN users u ON s.user_id = u.id
        ORDER BY FIELD(p.status_pengajuan, 'Pending', 'Disetujui', 'Ditolak'), p.created_at DESC
    """)
    pengajuan_list = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('persetujuan_absensi.html', pengajuan_list=pengajuan_list)


@app.route('/pembimbing/pengajuan-absensi/proses/<int:id>/<string:aksi>', methods=['POST'])
def proses_pengajuan(id, aksi):
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl']:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    if aksi not in ['Disetujui', 'Ditolak']:
        flash('Aksi tidak valid!', 'danger')
        return redirect(url_for('persetujuan_absensi'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pengajuan_absensi WHERE id = %s", (id,))
    p = cursor.fetchone()

    if p:
        try:
            # Update status pengajuan di tabel pengajuan_absensi
            cursor.execute("UPDATE pengajuan_absensi SET status_pengajuan = %s WHERE id = %s", (aksi, id))

            # Jika DISETUJUI dan jenisnya Izin / Sakit -> Langsung masuk tabel absensi
            # Jika jenisnya 'Terlambat' -> Hanya update status pengajuan agar kamera di sisi siswa bisa terbuka
            if aksi == 'Disetujui' and p['jenis'] in ['Izin', 'Sakit']:
                cursor.execute("DELETE FROM absensi WHERE siswa_id = %s AND tanggal = %s", (p['siswa_id'], p['tanggal']))
                
                cursor.execute("""
                    INSERT INTO absensi (siswa_id, tanggal, status, keterangan, foto_bukti)
                    VALUES (%s, %s, %s, %s, %s)
                """, (p['siswa_id'], p['tanggal'], p['jenis'], f"{p['jenis']}: {p['alasan']}", p.get('bukti_file')))

            conn.commit()
            
            if p['jenis'] == 'Terlambat' and aksi == 'Disetujui':
                flash(f"Pengajuan Terlambat di ACC. Siswa sekarang sudah bisa melakukan absensi foto selfie.", 'success')
            else:
                flash(f"Pengajuan {p['jenis']} berhasil di {aksi}!", 'success')

        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Terjadi kesalahan database: {e}', 'danger')

    cursor.close()
    conn.close()
    return redirect(url_for('persetujuan_absensi'))

@app.route('/pembimbing/siswa/tambah', methods=['GET', 'POST'])
def tambah_siswa_page():
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl', 'pembimbing']:
        flash('Akses ditolak. Silakan login sebagai Pembimbing.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        nisn = request.form.get('nisn', '').strip()
        kelas_jurusan = request.form.get('kelas_jurusan', '').strip()
        sekolah = request.form.get('sekolah', '').strip()
        tgl_mulai = request.form.get('tgl_mulai_pkl', '').strip() or None
        tgl_selesai = request.form.get('tgl_selesai_pkl', '').strip() or None

        if not nama or not nisn or not kelas_jurusan or not sekolah:
            flash('Harap isi semua bidang wajib!', 'danger')
            return render_template('tambah_siswa.html', nama=nama, nisn='', kelas_jurusan=kelas_jurusan, sekolah=sekolah)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("SELECT id FROM users WHERE username = %s", (nisn,))
            if cursor.fetchone():
                flash(f'NISN {nisn} sudah terdaftar. Harap gunakan NISN lain.', 'danger')
                return render_template('tambah_siswa.html', nama=nama, nisn='', kelas_jurusan=kelas_jurusan, sekolah=sekolah)

            hashed_pw = generate_password_hash(nisn)
            cursor.execute("""
                INSERT INTO users (username, password, nama, role) 
                VALUES (%s, %s, %s, 'siswa')
            """, (nisn, hashed_pw, nama))
            user_id = cursor.lastrowid

            # SIMPAN DENGAN TANGGAL PERIODE PKL
            cursor.execute("""
                INSERT INTO siswa (user_id, nisn, kelas_jurusan, sekolah, tgl_mulai_pkl, tgl_selesai_pkl)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, nisn, kelas_jurusan, sekolah, tgl_mulai, tgl_selesai))

            conn.commit()
            flash(f'{nama} (NISN: {nisn}) berhasil ditambahkan!', 'success')
            return redirect(url_for('daftar_siswa'))

        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Terjadi kesalahan saat menyimpan data: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('tambah_siswa.html', nama='', nisn='', kelas_jurusan='', sekolah='')

@app.route('/pembimbing/siswa/reset-password/<int:siswa_id>', methods=['POST'])
def reset_password_siswa(siswa_id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        flash('Akses ditolak. Khusus Pembimbing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Ambil data NISN dan user_id siswa
        cursor.execute("""
            SELECT s.nisn, s.user_id, u.nama 
            FROM siswa s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.id = %s
        """, (siswa_id,))
        siswa = cursor.fetchone()

        if not siswa:
            flash('Data siswa tidak ditemukan!', 'danger')
            return redirect(url_for('daftar_siswa'))

        # Hash password baru menggunakan NISN
        hashed_password = generate_password_hash(siswa['nisn'])

        # Update password di tabel users
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, siswa['user_id']))
        conn.commit()

        flash(f"Password untuk siswa {siswa['nama']} berhasil direset kembali ke NISN ({siswa['nisn']})!", 'success')

    except mysql.connector.Error as e:
        conn.rollback()
        flash(f'Gagal mereset password: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('detail_siswa', siswa_id=siswa_id))

# =========================================================
# ROUTE: EDIT DATA SISWA (PEMBIMBING)
# =========================================================
@app.route('/pembimbing/siswa/edit/<int:siswa_id>', methods=['GET', 'POST'])
def edit_siswa_page(siswa_id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl', 'pembimbing']:
        flash('Akses ditolak. Silakan login sebagai Pembimbing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.*, u.nama, u.username 
        FROM siswa s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.id = %s
    """, (siswa_id,))
    siswa = cursor.fetchone()

    if not siswa:
        cursor.close()
        conn.close()
        flash('Data siswa tidak ditemukan!', 'danger')
        return redirect(url_for('daftar_siswa'))

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        nisn = request.form.get('nisn', '').strip()
        kelas_jurusan = request.form.get('kelas_jurusan', '').strip()
        sekolah = request.form.get('sekolah', '').strip()
        tgl_mulai = request.form.get('tgl_mulai_pkl', '').strip() or None
        tgl_selesai = request.form.get('tgl_selesai_pkl', '').strip() or None

        if not nama or not nisn or not kelas_jurusan or not sekolah:
            flash('Harap isi semua bidang wajib!', 'danger')
            return render_template('edit_siswa.html', siswa=siswa)

        try:
            cursor.execute("UPDATE users SET nama = %s, username = %s WHERE id = %s", (nama, nisn, siswa['user_id']))

            # UPDATE DATA SISWA DAN PERIODE PKL
            cursor.execute("""
                UPDATE siswa 
                SET nisn = %s, kelas_jurusan = %s, sekolah = %s, tgl_mulai_pkl = %s, tgl_selesai_pkl = %s 
                WHERE id = %s
            """, (nisn, kelas_jurusan, sekolah, tgl_mulai, tgl_selesai, siswa_id))

            conn.commit()
            flash(f'Data siswa {nama} berhasil diperbarui!', 'success')
            return redirect(url_for('detail_siswa', siswa_id=siswa_id))

        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Terjadi kesalahan database: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    cursor.close()
    conn.close()
    return render_template('edit_siswa.html', siswa=siswa)


# =========================================================
# ROUTE: TOGGLE STATUS (NONAKTIFKAN / AKTIFKAN SISWA)
# =========================================================
# =========================================================
# ROUTE: TOGGLE STATUS (NONAKTIFKAN / AKTIFKAN SISWA)
# =========================================================
@app.route('/pembimbing/siswa/toggle-status/<int:siswa_id>', methods=['POST'])
def toggle_status_siswa(siswa_id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl', 'pembimbing']:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT s.user_id, u.nama, u.is_active 
            FROM siswa s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.id = %s
        """, (siswa_id,))
        siswa = cursor.fetchone()

        if siswa:
            # Mengonversi nilai ke integer 1 atau 0 secara tegas
            current_status = int(siswa['is_active']) if siswa.get('is_active') is not None else 1
            status_baru = 0 if current_status == 1 else 1

            # Update ke database
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (status_baru, siswa['user_id']))
            conn.commit()

            label = "dinonaktifkan" if status_baru == 0 else "diaktifkan kembali"
            flash(f"Akun siswa {siswa['nama']} berhasil {label}!", "warning" if status_baru == 0 else "success")

    except mysql.connector.Error as e:
        conn.rollback()
        flash(f'Gagal mengubah status siswa: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(request.referrer or url_for('daftar_siswa'))

# =========================================================
# ROUTE: INPUT & EDIT NILAI PKL SISWA
# =========================================================
@app.route('/pembimbing/siswa/nilai/<int:siswa_id>', methods=['GET', 'POST'])
def nilai_siswa_page(siswa_id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl', 'pembimbing']:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Ambil Data Profil Siswa
        cursor.execute("""
            SELECT s.*, u.nama, u.username 
            FROM siswa s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.id = %s
        """, (siswa_id,))
        siswa = cursor.fetchone()

        if not siswa:
            flash('Data siswa tidak ditemukan!', 'danger')
            return redirect(url_for('daftar_siswa'))

        # 2. Hitung Nilai Absensi Otomatis (Rasio Hadir vs Total Hari Absensi)
        cursor.execute("SELECT COUNT(*) AS total_hadir FROM absensi WHERE siswa_id = %s AND status = 'Hadir'", (siswa_id,))
        total_hadir = cursor.fetchone()['total_hadir'] or 0

        cursor.execute("SELECT COUNT(*) AS total_hari FROM absensi WHERE siswa_id = %s", (siswa_id,))
        total_hari_absen = cursor.fetchone()['total_hari'] or 1
        
        nilai_absensi_auto = min(100.0, round((total_hadir / total_hari_absen) * 100, 2))

        # 3. Hitung Nilai Laporan Otomatis dari tabel `laporan_harian` & kolom `status_validasi`
        cursor.execute("""
            SELECT COUNT(*) AS laporan_acc 
            FROM laporan_harian 
            WHERE siswa_id = %s AND status_validasi = 'Disetujui'
        """, (siswa_id,))
        laporan_acc = cursor.fetchone()['laporan_acc'] or 0
        
        nilai_laporan_auto = min(100.0, round((laporan_acc / total_hari_absen) * 100, 2))

        # 4. Ambil Nilai Eksisting (jika ada)
        cursor.execute("SELECT * FROM nilai_pkl WHERE siswa_id = %s", (siswa_id,))
        nilai = cursor.fetchone()

        if request.method == 'POST':
            nilai_sikap = int(request.form.get('nilai_sikap', 0))
            nilai_teknis = int(request.form.get('nilai_teknis', 0))
            catatan = request.form.get('catatan_pembimbing', '').strip()

            # KALKULASI NILAI AKHIR (Absensi 20% + Laporan 20% + Sikap 30% + Teknis 30%)
            nilai_akhir = round(
                (nilai_absensi_auto * 0.20) + 
                (nilai_laporan_auto * 0.20) + 
                (nilai_sikap * 0.30) + 
                (nilai_teknis * 0.30), 2
            )

            # Penentuan Predikat
            if nilai_akhir >= 85:
                predikat = 'A'
            elif nilai_akhir >= 75:
                predikat = 'B'
            elif nilai_akhir >= 65:
                predikat = 'C'
            else:
                predikat = 'D'

            if nilai:
                cursor.execute("""
                    UPDATE nilai_pkl SET 
                        nilai_absensi=%s, nilai_laporan=%s, nilai_sikap=%s, nilai_teknis=%s, 
                        nilai_akhir=%s, predikat=%s, catatan_pembimbing=%s, pembimbing_id=%s
                    WHERE siswa_id=%s
                """, (nilai_absensi_auto, nilai_laporan_auto, nilai_sikap, nilai_teknis, nilai_akhir, predikat, catatan, session['user_id'], siswa_id))
            else:
                cursor.execute("""
                    INSERT INTO nilai_pkl 
                    (siswa_id, pembimbing_id, nilai_absensi, nilai_laporan, nilai_sikap, nilai_teknis, nilai_akhir, predikat, catatan_pembimbing)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (siswa_id, session['user_id'], nilai_absensi_auto, nilai_laporan_auto, nilai_sikap, nilai_teknis, nilai_akhir, predikat, catatan))

            conn.commit()
            flash(f'Penilaian untuk {siswa["nama"]} berhasil disimpan! (Nilai Akhir: {nilai_akhir} / Predikat: {predikat})', 'success')
            return redirect(url_for('detail_siswa', siswa_id=siswa_id))

    except mysql.connector.Error as e:
        conn.rollback()
        flash(f'Terjadi kesalahan database: {e}', 'danger')
        return redirect(url_for('daftar_siswa'))
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'nilai_siswa.html', 
        siswa=siswa, 
        nilai=nilai, 
        nilai_absensi_auto=nilai_absensi_auto, 
        nilai_laporan_auto=nilai_laporan_auto
    )

@app.route('/pembimbing/profil', methods=['GET'])
def profil_pembimbing():
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl']:
        flash('Akses ditolak. Silakan login terlebih dahulu.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = get_db_connection()
    if not conn:
        flash('Gagal terhubung ke database.', 'danger')
        return redirect(url_for('dashboard_pembimbing'))

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT u.id AS user_id, u.username, u.nama, u.role,
                   p.nama_perusahaan, p.jabatan, p.divisi, p.no_hp, p.email, p.alamat_perusahaan
            FROM users u
            LEFT JOIN pembimbing p ON u.id = p.user_id
            WHERE u.id = %s
        """
        cursor.execute(query, (user_id,))
        pembimbing_data = cursor.fetchone()

    except mysql.connector.Error as e:
        flash(f'Terjadi kesalahan database: {e}', 'danger')
        pembimbing_data = None
    finally:
        cursor.close()
        conn.close()

    return render_template('profil_pembimbing.html', pembimbing=pembimbing_data)


@app.route('/pembimbing/profil/update', methods=['POST'])
def update_profil_pembimbing():
    if not is_logged_in() or session.get('role') not in ['pembimbing_industri', 'pembimbing_pkl']:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    nama = request.form.get('nama', '').strip()
    nama_perusahaan = request.form.get('nama_perusahaan', '').strip()
    jabatan = request.form.get('jabatan', '').strip()
    divisi = request.form.get('divisi', '').strip()
    no_hp = request.form.get('no_hp', '').strip()
    email = request.form.get('email', '').strip()
    alamat_perusahaan = request.form.get('alamat_perusahaan', '').strip()

    if not nama:
        flash('Nama lengkap wajib diisi!', 'danger')
        return redirect(url_for('profil_pembimbing'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Update nama di tabel users & perbarui session nama
        cursor.execute("UPDATE users SET nama = %s WHERE id = %s", (nama, user_id))
        
        nama_bersih = nama.replace(' (Guru)', '').replace('(Guru)', '').replace(' (Pembimbing)', '').replace('(Pembimbing)', '').strip()
        session['nama'] = nama_bersih

        # 2. Simpan atau perbarui data di tabel pembimbing
        cursor.execute("SELECT id FROM pembimbing WHERE user_id = %s", (user_id,))
        pembimbing_rec = cursor.fetchone()

        if pembimbing_rec:
            cursor.execute("""
                UPDATE pembimbing 
                SET nama_perusahaan = %s, jabatan = %s, divisi = %s, no_hp = %s, email = %s, alamat_perusahaan = %s
                WHERE user_id = %s
            """, (nama_perusahaan, jabatan, divisi, no_hp, email, alamat_perusahaan, user_id))
        else:
            cursor.execute("""
                INSERT INTO pembimbing (user_id, nama_perusahaan, jabatan, divisi, no_hp, email, alamat_perusahaan)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, nama_perusahaan, jabatan, divisi, no_hp, email, alamat_perusahaan))

        conn.commit()
        flash('Profil Pembimbing Industri berhasil diperbarui!', 'success')

    except mysql.connector.Error as e:
        conn.rollback()
        flash(f'Gagal memperbarui profil: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('profil_pembimbing'))

@app.route('/pembimbing/absen-manual', methods=['POST'])
def absen_manual_pembimbing():
    if not is_logged_in() or session.get('role') not in ['pembimbing', 'pembimbing_industri', 'pembimbing_pkl']:
        flash('Akses tidak diizinkan.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    siswa_id = request.form.get('siswa_id')
    tanggal = request.form.get('tanggal')
    status = request.form.get('status', 'Hadir')
    keterangan = request.form.get('keterangan', 'Absen Manual oleh Pembimbing')

    # 1. Cek batas toleransi absen manual (Maksimal 1x per siswa)
    cursor.execute("""
        SELECT COUNT(*) AS total_manual 
        FROM absensi 
        WHERE siswa_id = %s AND is_manual = 1
    """, (siswa_id,))
    cek_manual = cursor.fetchone()

    if cek_manual and cek_manual['total_manual'] >= 1:
        cursor.close()
        conn.close()
        flash('Batas toleransi absen manual untuk siswa ini sudah habis (Maksimal 1x)!', 'danger')
        return redirect(url_for('riwayat_absensi'))

    # 2. Cek apakah siswa sudah punya catatan absensi di tanggal tersebut
    cursor.execute("SELECT id FROM absensi WHERE siswa_id = %s AND tanggal = %s", (siswa_id, tanggal))
    ada_absen = cursor.fetchone()

    if ada_absen:
        cursor.close()
        conn.close()
        flash('Siswa sudah memiliki catatan presensi pada tanggal tersebut!', 'danger')
        return redirect(url_for('riwayat_absensi'))

    # 3. Simpan Absen Manual
    cursor.execute("""
        INSERT INTO absensi (siswa_id, tanggal, status, keterangan, is_manual, created_at)
        VALUES (%s, %s, %s, %s, 1, NOW())
    """, (siswa_id, tanggal, status, keterangan))
    
    conn.commit()
    cursor.close()
    conn.close()

    flash('Presensi manual berhasil disimpan!', 'success')
    return redirect(url_for('riwayat_absensi'))

@app.route('/tandai-dilihat/<int:id>', methods=['POST'])
def tandai_dilihat(id):
    if not is_logged_in() or session.get('role') not in ['pembimbing_pkl', 'pembimbing_industri']:
        return jsonify({'status': 'unauthorized'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE pengajuan_absensi SET sudah_dilihat = 1 WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/pembimbing/ekspor-absensi')
def ekspor_absensi():
  if not is_logged_in() or session.get('role') not in [
      'pembimbing_industri',
      'pembimbing_pkl',
  ]:
    flash('Akses ditolak.', 'danger')
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor(dictionary=True, buffered=True)

  # Ambil data rekap absensi seluruh siswa
  cursor.execute("""
        SELECT 
            u.nama AS nama, 
            s.nisn AS nis, 
            s.kelas_jurusan,
            SUM(CASE WHEN a.status = 'Hadir' THEN 1 ELSE 0 END) AS total_hadir,
            SUM(CASE WHEN a.status = 'Izin' THEN 1 ELSE 0 END) AS total_izin,
            SUM(CASE WHEN a.status = 'Sakit' THEN 1 ELSE 0 END) AS total_sakit
        FROM siswa s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN absensi a ON s.id = a.siswa_id
        GROUP BY s.id, u.nama, s.nisn, s.kelas_jurusan
        ORDER BY u.nama ASC
    """)
  rekap_data = cursor.fetchall()
  cursor.close()
  conn.close()

  # --- MEMBUAT FILE EXCEL YANG RAPI (OPENPYXL) ---
  wb = openpyxl.Workbook()
  ws = wb.active
  ws.title = "Rekap Absensi PKL"

  # Pastikan gridlines (garis kotak excel) terlihat jelas
  ws.views.sheetView[0].showGridLines = True

  # 🎨 DEFINISI STYLES & PALET WARNA
  font_family = 'Plus Jakarta Sans'

  title_font = Font(name=font_family, size=14, bold=True, color="0F172A")
  subtitle_font = Font(name=font_family, size=9, italic=True, color="64748B")

  header_fill = PatternFill(
      start_color="4F46E5", end_color="4F46E5", fill_type="solid"
  )
  header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")

  regular_font = Font(name=font_family, size=10, color="0F172A")
  bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
  zebra_fill = PatternFill(
      start_color="F8FAFC", end_color="F8FAFC", fill_type="solid"
  )
  white_fill = PatternFill(
      start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"
  )

  hadir_fill = PatternFill(
      start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"
  )
  hadir_font = Font(name=font_family, size=10, bold=True, color="15803D")

  izin_fill = PatternFill(
      start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"
  )
  izin_font = Font(name=font_family, size=10, bold=True, color="B45309")

  sakit_fill = PatternFill(
      start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"
  )
  sakit_font = Font(name=font_family, size=10, bold=True, color="B91C1C")

  thin_border = Border(
      left=Side(style='thin', color='CBD5E1'),
      right=Side(style='thin', color='CBD5E1'),
      top=Side(style='thin', color='CBD5E1'),
      bottom=Side(style='thin', color='CBD5E1'),
  )

  total_border = Border(
      left=Side(style='thin', color='94A3B8'),
      right=Side(style='thin', color='94A3B8'),
      top=Side(style='thin', color='94A3B8'),
      bottom=Side(style='double', color='0F172A'),
  )

  # 1. HEADER JUDUL LAPORAN (CENTRALIZED / DI TENGAH)
  ws.merge_cells('A1:G1')
  ws['A1'] = 'REKAPITULASI PRESENSI SISWA PKL'
  ws['A1'].font = title_font
  ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
  ws.row_dimensions[1].height = 28

  ws.merge_cells('A2:G2')
  ws['A2'] = (
      'Sistem Informasi E-Jurnal PKL — Tanggal Cetak:'
      f" {date.today().strftime('%d %B %Y')}"
  )
  ws['A2'].font = subtitle_font
  ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
  ws.row_dimensions[2].height = 18

  ws.row_dimensions[3].height = 10

  # 2. HEADER TABEL (Baris 4)
  headers = [
      'No',
      'NISN',
      'Nama Siswa',
      'Kelas / Jurusan',
      'Hadir',
      'Izin',
      'Sakit',
  ]
  ws.row_dimensions[4].height = 26

  for col_num, header in enumerate(headers, 1):
    cell = ws.cell(row=4, column=col_num, value=header)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(
        horizontal='center', vertical='center', wrap_text=True
    )
    cell.border = thin_border

  # 3. ISI DATA TABEL (Mulai Baris 5)
  start_row = 5
  for idx, row in enumerate(rekap_data, 1):
    current_row = start_row + idx - 1
    ws.row_dimensions[current_row].height = 22
    row_bg = zebra_fill if idx % 2 == 0 else white_fill

    row_values = [
        (idx, 'center', regular_font, row_bg),
        (str(row['nis'] or '-'), 'center', regular_font, row_bg),
        (row['nama'] or '-', 'left', regular_font, row_bg),
        (row['kelas_jurusan'] or '-', 'center', regular_font, row_bg),
    ]

    for col_idx, (val, align, font, bg) in enumerate(row_values, 1):
      cell = ws.cell(row=current_row, column=col_idx, value=val)
      cell.alignment = Alignment(horizontal=align, vertical='center')
      cell.font = font
      cell.fill = bg
      cell.border = thin_border

    # Status Hadir
    h_val = row['total_hadir'] or 0
    c5 = ws.cell(row=current_row, column=5, value=h_val)
    c5.alignment = Alignment(horizontal='center', vertical='center')
    c5.fill = hadir_fill if h_val > 0 else row_bg
    c5.font = hadir_font if h_val > 0 else regular_font
    c5.border = thin_border

    # Status Izin
    i_val = row['total_izin'] or 0
    c6 = ws.cell(row=current_row, column=6, value=i_val)
    c6.alignment = Alignment(horizontal='center', vertical='center')
    c6.fill = izin_fill if i_val > 0 else row_bg
    c6.font = izin_font if i_val > 0 else regular_font
    c6.border = thin_border

    # Status Sakit
    s_val = row['total_sakit'] or 0
    c7 = ws.cell(row=current_row, column=7, value=s_val)
    c7.alignment = Alignment(horizontal='center', vertical='center')
    c7.fill = sakit_fill if s_val > 0 else row_bg
    c7.font = sakit_font if s_val > 0 else regular_font
    c7.border = thin_border

  # 4. BARIS TOTAL KESELURUHAN (DI LUAR LOOP DATA SISWA)
  total_row = start_row + len(rekap_data)
  ws.row_dimensions[total_row].height = 24

  ws.merge_cells(
      start_row=total_row, start_column=1, end_row=total_row, end_column=4
  )
  t_label = ws.cell(row=total_row, column=1, value="TOTAL KESELURUHAN")
  t_label.font = bold_font
  t_label.alignment = Alignment(horizontal='right', vertical='center')

  # Pasang border pada kolom 1 sampai 4
  for col_idx in range(1, 5):
    ws.cell(row=total_row, column=col_idx).border = total_border

  # Formula SUM Excel
  last_data_row = total_row - 1
  if len(rekap_data) > 0:
    t_hadir = ws.cell(
        row=total_row, column=5, value=f"=SUM(E5:E{last_data_row})"
    )
    t_izin = ws.cell(
        row=total_row, column=6, value=f"=SUM(F5:F{last_data_row})"
    )
    t_sakit = ws.cell(
        row=total_row, column=7, value=f"=SUM(G5:G{last_data_row})"
    )
  else:
    t_hadir = ws.cell(row=total_row, column=5, value=0)
    t_izin = ws.cell(row=total_row, column=6, value=0)
    t_sakit = ws.cell(row=total_row, column=7, value=0)

  for cell_t in [t_hadir, t_izin, t_sakit]:
    cell_t.font = bold_font
    cell_t.alignment = Alignment(horizontal='center', vertical='center')
    cell_t.border = total_border

  # 5. PERHITUNGAN AUTOFIT LEBAR KOLOM (Mengabaikan Judul A1 & A2)
  min_widths = {1: 8, 2: 18, 3: 28, 4: 20, 5: 12, 6: 12, 7: 12}

  for col in ws.columns:
    col_idx = col[0].column
    col_letter = get_column_letter(col_idx)
    max_len = 0

    for cell in col:
      # Abaikan baris 1 & 2 (judul merged)
      if cell.row in [1, 2]:
        continue

      if cell.value is not None:
        val_str = str(cell.value)
        if len(val_str) > max_len:
          max_len = len(val_str)

    calculated_width = max_len + 4
    default_min = min_widths.get(col_idx, 12)
    ws.column_dimensions[col_letter].width = max(calculated_width, default_min)

  # 6. SIMPAN & RESPONSE
  output = io.BytesIO()
  wb.save(output)
  output.seek(0)

  filename = f"Rekap_Absensi_PKL_{date.today().strftime('%Y%m%d')}.xlsx"

  return send_file(
      output,
      mimetype=(
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ),
      as_attachment=True,
      download_name=filename,
  )

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah keluar dari sistem.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', port=int(os.environ.get('PORT', 5000)))