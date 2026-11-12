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
    
    # KASUS A: Jika sudah berstatus HADIR di absensi, berikan akses penuh isi laporan!
    if status_absen == 'hadir':
        pass # Lolos ke bawah untuk menampilkan form / proses POST laporan
    
    # KASUS B: Jika tercatat Izin atau Sakit (dan sudah di-ACC), tidak boleh isi laporan
    elif status_absen in ['izin', 'sakit']:
        flash(f'Hari ini Anda tercatat {status_absen.capitalize()}. Anda tidak perlu mengisi laporan harian.', 'warning')
        return redirect(url_for('laporan'))

    # KASUS C: Cek berdasarkan data pengajuan khusus
    elif pengajuan_today:
        status_p = pengajuan_today['status_pengajuan']
        jenis_p = pengajuan_today['jenis'] # Bisa 'Izin', 'Sakit', atau 'Terlambat'

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
                # Jika Terlambat sudah di-ACC tapi siswanya BELUM selesai ambil foto absensi
                flash('Pengajuan terlambat Anda sudah di-ACC! Silakan lakukan absensi foto terlebih dahulu.', 'warning')
                return redirect(url_for('absensi'))
            elif status_p == 'Ditolak':
                flash('Pengajuan keterlambatan Anda ditolak oleh Pembimbing.', 'danger')
                return redirect(url_for('laporan'))

    # KASUS D: Belum melakukan apa pun sama sekali
    else:
        flash('Anda belum melakukan Absensi Hadir hari ini! Silakan absen terlebih dahulu sebelum mengisi laporan.', 'danger')
        return redirect(url_for('laporan'))


    # ==========================================
    # 4. PROSES POST & RENDER FORM LAPORAN
    # ==========================================
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    if request.method == 'POST':
        tanggal = request.form.get('tanggal', today_str)
        deskripsi_kegiatan = request.form.get('deskripsi_kegiatan', '').strip()
        alasan_terlambat = request.form.get('alasan_terlambat', '').strip()
        file_foto = request.files.get('foto_bukti')

        # Validasi Input Form
        if not tanggal or not deskripsi_kegiatan:
            cursor.close()
            conn.close()
            flash('Tanggal dan Deskripsi Kegiatan wajib diisi!', 'danger')
            return render_template('laporan_form.html', is_edit=False, today=today_str, is_terlambat=is_terlambat)

        if is_terlambat and not alasan_terlambat:
            cursor.close()
            conn.close()
            flash('Pengiriman terlambat! Harap isi alasan keterlambatan Anda.', 'danger')
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

    if laporan_data['status_validasi'] != 'Revisi':
        cursor.close()
        conn.close()
        flash('Hanya laporan berstatus Revisi yang dapat diedit!', 'warning')
        return redirect(url_for('laporan'))

    if request.method == 'POST':
        tanggal = request.form.get('tanggal', laporan_data['tanggal'])
        deskripsi_kegiatan = request.form.get('deskripsi_kegiatan', '').strip()
        file_foto = request.files.get('foto_bukti')

        filename_db = laporan_data['foto_bukti']
        if file_foto and file_foto.filename != '':
            if not allowed_file(file_foto.filename):
                flash('Format file tidak didukung! Gunakan PNG, JPG, atau JPEG.', 'danger')
                return render_template('laporan_form.html', is_edit=True, laporan=laporan_data)

            original_name = secure_filename(file_foto.filename)
            unique_name = f"{uuid.uuid4().hex}_{original_name}"
            
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_foto.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            filename_db = unique_name

        try:
            cursor.execute("""
                UPDATE laporan_harian 
                SET tanggal = %s, deskripsi_kegiatan = %s, foto_bukti = %s, status_validasi = 'Pending'
                WHERE id = %s AND siswa_id = %s
            """, (tanggal, deskripsi_kegiatan, filename_db, laporan_id, siswa_id))
            conn.commit()
            flash('Revisi laporan harian berhasil dikirim! Status kembali menjadi Pending.', 'success')
            return redirect(url_for('laporan'))
        except mysql.connector.Error as e:
            flash(f'Gagal mengupdate laporan: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    cursor.close()
    conn.close()
    return render_template('laporan_form.html', is_edit=True, laporan=laporan_data)