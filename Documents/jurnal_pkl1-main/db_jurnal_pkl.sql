-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 12 Nov 2026 pada 08.26
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_jurnal_pkl`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `absensi`
--

CREATE TABLE `absensi` (
  `id` int(11) NOT NULL,
  `siswa_id` int(11) NOT NULL,
  `tanggal` date NOT NULL,
  `status` enum('Hadir','Izin','Sakit','Alpa') NOT NULL,
  `keterangan` text DEFAULT NULL,
  `foto_bukti` varchar(255) DEFAULT NULL,
  `lokasi` varchar(255) DEFAULT NULL,
  `is_manual` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `absensi`
--

INSERT INTO `absensi` (`id`, `siswa_id`, `tanggal`, `status`, `keterangan`, `foto_bukti`, `lokasi`, `is_manual`, `created_at`) VALUES
(22, 12, '2026-11-11', 'Alpa', 'Otomatis Alpa oleh Sistem (Lewat Jam 15:00 WIB)', NULL, NULL, 0, '2026-11-11 10:42:06'),
(23, 11, '2026-11-11', 'Alpa', 'Otomatis Alpa oleh Sistem (Lewat Jam 15:00 WIB)', NULL, NULL, 0, '2026-11-11 12:19:36'),
(24, 11, '2026-11-12', 'Hadir', 'Terlambat (ACC Pembimbing): laptop saya di cas', 'absensi_11_2026-11-12_555355.png', '', 0, '2026-11-12 04:11:40'),
(25, 13, '2026-11-12', 'Hadir', 'Terlambat (ACC Pembimbing): saya terlambat karena harus kerumah sakit dulu', 'absensi_13_2026-11-12_f8dbc4.png', '', 0, '2026-11-12 06:39:48');

-- --------------------------------------------------------

--
-- Struktur dari tabel `laporan_harian`
--

CREATE TABLE `laporan_harian` (
  `id` int(11) NOT NULL,
  `siswa_id` int(11) NOT NULL,
  `tanggal` date DEFAULT NULL,
  `minggu_ke` int(11) DEFAULT NULL,
  `tanggal_mulai` date DEFAULT NULL,
  `tanggal_selesai` date DEFAULT NULL,
  `deskripsi_kegiatan` text NOT NULL,
  `foto_bukti` varchar(255) NOT NULL,
  `alasan_terlambat` text DEFAULT NULL,
  `status_validasi` enum('Pending','Disetujui','Revisi') DEFAULT 'Pending',
  `catatan_pembimbing` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `laporan_harian`
--

INSERT INTO `laporan_harian` (`id`, `siswa_id`, `tanggal`, `minggu_ke`, `tanggal_mulai`, `tanggal_selesai`, `deskripsi_kegiatan`, `foto_bukti`, `alasan_terlambat`, `status_validasi`, `catatan_pembimbing`, `created_at`) VALUES
(9, 11, '2026-11-09', NULL, NULL, NULL, 'Membuat erd', '9d04438a6de14740ba793ff79aa92aac_Cuplikan_layar_2026-08-03_101649.png', 'Tidak ada laptop', 'Disetujui', 'Bagus', '2026-11-09 06:28:14'),
(10, 13, '2026-11-12', NULL, NULL, NULL, 'saya mengerjakan hosting web', '28c3fca64d2a4502a219eb37df2086b3_Cuplikan_layar_2026-11-09_120046.png', 'saya terlambat karena harus kerumah sakit dulu', 'Disetujui', 'ganti erdnya', '2026-11-12 06:40:54'),
(11, 13, '2026-11-12', NULL, NULL, NULL, '10243316jsjchsjajsdjsa', '330e41c66e8a452983e78a84e6cab02d_Cuplikan_layar_2026-08-03_100616.png', ';;;;sdscscecjhsaic', 'Disetujui', 'mukanya benerin', '2026-11-12 06:41:32'),
(12, 13, '2026-11-12', NULL, NULL, NULL, 'sdfghjkjhgfdfghjkl', '81fcfac43a64477e87af1f60dc9824ef_Cuplikan_layar_2026-08-03_101649.png', 'hgfdfghjkjhgfghjk', 'Disetujui', 'itu si hideng ngapain', '2026-11-12 06:42:31'),
(13, 13, '2026-11-11', NULL, NULL, NULL, 'hayuuuuuuuuuuuu', 'd76e915617b64882a4e23967c59ce6b2_Cuplikan_layar_2026-08-03_100810.png', 'yaaaaaaaaaaaaaaaaaa', 'Pending', NULL, '2026-11-12 07:01:39');

-- --------------------------------------------------------

--
-- Struktur dari tabel `nilai_pkl`
--

CREATE TABLE `nilai_pkl` (
  `id` int(11) NOT NULL,
  `siswa_id` int(11) NOT NULL,
  `pembimbing_id` int(11) NOT NULL,
  `nilai_absensi` decimal(5,2) DEFAULT 0.00,
  `nilai_laporan` decimal(5,2) DEFAULT 0.00,
  `nilai_sikap` int(11) DEFAULT 0,
  `nilai_teknis` int(11) DEFAULT 0,
  `nilai_akhir` decimal(5,2) DEFAULT 0.00,
  `predikat` varchar(2) DEFAULT 'B',
  `catatan_pembimbing` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `nilai_pkl`
--

INSERT INTO `nilai_pkl` (`id`, `siswa_id`, `pembimbing_id`, `nilai_absensi`, `nilai_laporan`, `nilai_sikap`, `nilai_teknis`, `nilai_akhir`, `predikat`, `catatan_pembimbing`, `created_at`, `updated_at`) VALUES
(1, 13, 3, 100.00, 100.00, 0, 98, 69.40, 'C', 'yang sopan ya', '2026-11-12 13:45:58', '2026-11-12 14:13:59');

-- --------------------------------------------------------

--
-- Struktur dari tabel `pembimbing`
--

CREATE TABLE `pembimbing` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `nama_perusahaan` varchar(150) DEFAULT NULL,
  `jabatan` varchar(100) DEFAULT NULL,
  `divisi` varchar(100) DEFAULT NULL,
  `no_hp` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `alamat_perusahaan` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pembimbing`
--

INSERT INTO `pembimbing` (`id`, `user_id`, `nama_perusahaan`, `jabatan`, `divisi`, `no_hp`, `email`, `alamat_perusahaan`, `created_at`) VALUES
(1, 3, 'PT. Media Naraya Cipta', 'Developer', 'IT', '0838666666', 'moonveilmc6@gmail.com', 'Jl. Mekarwangi', '2026-10-24 04:19:18');

-- --------------------------------------------------------

--
-- Struktur dari tabel `pengajuan_absensi`
--

CREATE TABLE `pengajuan_absensi` (
  `id` int(11) NOT NULL,
  `siswa_id` int(11) NOT NULL,
  `tanggal` date NOT NULL,
  `jenis` enum('Izin','Sakit','Terlambat') NOT NULL,
  `alasan` text NOT NULL,
  `bukti_file` varchar(255) DEFAULT NULL,
  `status_pengajuan` enum('Pending','Disetujui','Ditolak') DEFAULT 'Pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `sudah_dilihat` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pengajuan_absensi`
--

INSERT INTO `pengajuan_absensi` (`id`, `siswa_id`, `tanggal`, `jenis`, `alasan`, `bukti_file`, `status_pengajuan`, `created_at`, `sudah_dilihat`) VALUES
(21, 11, '2026-11-12', 'Terlambat', 'laptop saya di cas', NULL, 'Disetujui', '2026-11-12 04:07:46', 0),
(22, 13, '2026-11-12', 'Terlambat', 'saya terlambat karena harus kerumah sakit dulu', NULL, 'Disetujui', '2026-11-12 06:38:19', 0);

-- --------------------------------------------------------

--
-- Struktur dari tabel `pengumuman_pembimbing`
--

CREATE TABLE `pengumuman_pembimbing` (
  `id` int(11) NOT NULL,
  `pesan` text NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pengumuman_pembimbing`
--

INSERT INTO `pengumuman_pembimbing` (`id`, `pesan`, `updated_at`) VALUES
(1, 'besok libur', '2026-11-11 10:02:10'),
(2, 'tes', '2026-11-11 10:02:14'),
(3, 'tes', '2026-11-11 10:02:19'),
(4, 'tes', '2026-11-11 10:02:26'),
(5, 'tes', '2026-11-11 10:06:33'),
(6, 'tes', '2026-11-11 12:54:40'),
(7, 'tes', '2026-11-11 12:54:52'),
(8, 'untuk besok kita libur nya barudak', '2026-11-12 06:48:42'),
(9, 'hayu balik barudak', '2026-11-12 07:11:11');

-- --------------------------------------------------------

--
-- Struktur dari tabel `siswa`
--

CREATE TABLE `siswa` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `nisn` varchar(20) NOT NULL,
  `kelas_jurusan` varchar(50) DEFAULT NULL,
  `sekolah` varchar(100) DEFAULT NULL,
  `tgl_mulai_pkl` date DEFAULT NULL,
  `tgl_selesai_pkl` date DEFAULT NULL,
  `tempat_lahir` varchar(100) DEFAULT NULL,
  `tanggal_lahir` date DEFAULT NULL,
  `jenis_kelamin` enum('L','P') DEFAULT NULL,
  `no_hp` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `alamat` text DEFAULT NULL,
  `foto_profil` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `siswa`
--

INSERT INTO `siswa` (`id`, `user_id`, `nisn`, `kelas_jurusan`, `sekolah`, `tgl_mulai_pkl`, `tgl_selesai_pkl`, `tempat_lahir`, `tanggal_lahir`, `jenis_kelamin`, `no_hp`, `email`, `alamat`, `foto_profil`) VALUES
(11, 14, '10243301', 'XII PPLG B', 'SMK Negeri 2 Cimahi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(12, 15, '10243300', 'XII PPLG B', 'SMK Negeri 2 Cimahi', '2026-07-13', '2026-11-13', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(13, 16, '10243316', 'XII PPLG B', 'SMK Negeri 2 Cimahi', '2026-07-13', '2026-11-13', 'Cimahi', '2009-04-14', 'L', '0830000000', 'moonveilmc6@gmail.com', 'Jalan Pangauban', NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nama` varchar(100) NOT NULL,
  `role` enum('pembimbing_industri','pembimbing_pkl','siswa') NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `nama`, `role`, `is_active`, `created_at`) VALUES
(2, 'pembimbing_pkl', 'scrypt:32768:8:1$OqTkMEpguJtcfeXZ$9bffd894dbb88ac08989170212e22cd91612908600b32b45eb9f914fcbba48c5a669c1d76b8d3178a309763e2d010e3798fe8693c6ec32c9028fa5553a2b0aef', 'Budi S.Kom (Guru)', 'pembimbing_pkl', 1, '2026-08-15 03:22:21'),
(3, 'pembimbing_ind', 'scrypt:32768:8:1$OqTkMEpguJtcfeXZ$9bffd894dbb88ac08989170212e22cd91612908600b32b45eb9f914fcbba48c5a669c1d76b8d3178a309763e2d010e3798fe8693c6ec32c9028fa5553a2b0aef', 'Erik Setiawan', 'pembimbing_industri', 1, '2026-08-15 03:22:21'),
(14, '10243301', 'scrypt:32768:8:1$KFCTGYHiVtZjCnfm$482598ab584b52684757a0a72e894ead3bfc423b70e1a0af462a4cfa3a8cf58732b70e422bc54033375564b21e2d7d13f36b7a7a6375e52ca07ca154db8113f8', 'Muhammad Alif Firdaus', 'siswa', 0, '2026-11-09 06:23:38'),
(15, '10243300', 'scrypt:32768:8:1$cebcDkpUgBeVayx6$d118c49e7a49f15cbb5a8d05c3406ad79101ba4ea8ce4484d6081d8c3b495c2a49eba38434d2ef11f24ef0ec5e805d88d522f9f6401e84ca0b1e30b1989165ac', 'Muhammad Akbar', 'siswa', 1, '2026-11-09 07:01:16'),
(16, '10243316', 'scrypt:32768:8:1$1SjKUVpFqE2sJz4h$5ac0ae1f6cab5c0c5b4ccd9100e19e777b37967e30a677e1b77b0e31f89d9b928f5a85c393575796ca5212a324d75c874d0627871614965ce90ee477ebe20fbe', 'Rizqy Indrawan Putra', 'siswa', 0, '2026-11-12 06:32:08');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `absensi`
--
ALTER TABLE `absensi`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`);

--
-- Indeks untuk tabel `laporan_harian`
--
ALTER TABLE `laporan_harian`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`);

--
-- Indeks untuk tabel `nilai_pkl`
--
ALTER TABLE `nilai_pkl`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`),
  ADD KEY `pembimbing_id` (`pembimbing_id`);

--
-- Indeks untuk tabel `pembimbing`
--
ALTER TABLE `pembimbing`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`);

--
-- Indeks untuk tabel `pengumuman_pembimbing`
--
ALTER TABLE `pengumuman_pembimbing`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `siswa`
--
ALTER TABLE `siswa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nisn` (`nisn`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `absensi`
--
ALTER TABLE `absensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT untuk tabel `laporan_harian`
--
ALTER TABLE `laporan_harian`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT untuk tabel `nilai_pkl`
--
ALTER TABLE `nilai_pkl`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `pembimbing`
--
ALTER TABLE `pembimbing`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT untuk tabel `pengumuman_pembimbing`
--
ALTER TABLE `pengumuman_pembimbing`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT untuk tabel `siswa`
--
ALTER TABLE `siswa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT untuk tabel `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `absensi`
--
ALTER TABLE `absensi`
  ADD CONSTRAINT `absensi_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `laporan_harian`
--
ALTER TABLE `laporan_harian`
  ADD CONSTRAINT `laporan_harian_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `nilai_pkl`
--
ALTER TABLE `nilai_pkl`
  ADD CONSTRAINT `nilai_pkl_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `nilai_pkl_ibfk_2` FOREIGN KEY (`pembimbing_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `pembimbing`
--
ALTER TABLE `pembimbing`
  ADD CONSTRAINT `pembimbing_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  ADD CONSTRAINT `pengajuan_absensi_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `siswa`
--
ALTER TABLE `siswa`
  ADD CONSTRAINT `siswa_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
