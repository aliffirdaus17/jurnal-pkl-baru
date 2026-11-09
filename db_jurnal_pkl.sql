-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 31 Okt 2026 pada 07.31
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
(14, 9, '2026-10-30', 'Izin', 'Izin: Ada acara keluarga', '9ebcf9f962c44c97af481ff6b38f2a08_Cuplikan_layar_2026-08-03_100616.png', NULL, 0, '2026-10-30 07:36:21'),
(15, 9, '2026-10-31', 'Hadir', 'Terlambat (ACC Pembimbing): Bangun kesiangan', 'absensi_9_2026-10-31_61d9ad.png', '', 0, '2026-10-31 04:16:34'),
(16, 10, '2026-10-31', 'Hadir', 'Terlambat (ACC Pembimbing): Karena tidak ada kuota', 'absensi_10_2026-10-31_abc383.png', '', 0, '2026-10-31 04:31:26');

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
(11, 9, '2026-10-30', 'Izin', 'Ada acara keluarga', '9ebcf9f962c44c97af481ff6b38f2a08_Cuplikan_layar_2026-08-03_100616.png', 'Disetujui', '2026-10-30 07:35:44', 1),
(12, 9, '2026-10-31', 'Terlambat', 'Bangun kesiangan', NULL, 'Disetujui', '2026-10-31 03:59:45', 0),
(13, 10, '2026-10-31', 'Terlambat', 'Karena tidak ada kuota', NULL, 'Disetujui', '2026-10-31 04:27:58', 0);

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

INSERT INTO `siswa` (`id`, `user_id`, `nisn`, `kelas_jurusan`, `sekolah`, `tempat_lahir`, `tanggal_lahir`, `jenis_kelamin`, `no_hp`, `email`, `alamat`, `foto_profil`) VALUES
(9, 12, '10243301', 'XII PPLG B', 'SMK Negeri 2 Cimahi', 'Cimahi', '2008-07-17', 'L', '083863286499', 'mfirdausalif1218@gmail.com', 'Jl. Kebon Kopi', 'foto_profil_9_1793419038.png'),
(10, 13, '10243300', 'XII PPLG B', 'SMK Negeri 2 Cimahi', NULL, NULL, NULL, NULL, NULL, NULL, NULL);

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
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `nama`, `role`, `created_at`) VALUES
(2, 'pembimbing_pkl', 'scrypt:32768:8:1$OqTkMEpguJtcfeXZ$9bffd894dbb88ac08989170212e22cd91612908600b32b45eb9f914fcbba48c5a669c1d76b8d3178a309763e2d010e3798fe8693c6ec32c9028fa5553a2b0aef', 'Budi S.Kom (Guru)', 'pembimbing_pkl', '2026-08-15 03:22:21'),
(3, 'pembimbing_ind', 'scrypt:32768:8:1$OqTkMEpguJtcfeXZ$9bffd894dbb88ac08989170212e22cd91612908600b32b45eb9f914fcbba48c5a669c1d76b8d3178a309763e2d010e3798fe8693c6ec32c9028fa5553a2b0aef', 'Erik Setiawan', 'pembimbing_industri', '2026-08-15 03:22:21'),
(12, '10243301', 'scrypt:32768:8:1$lbIeehJVQVbEUvCT$817b86ba740bdbbadefd4e91293a6a8fa1ae0c0162f9952a143be665006f9ca8c208fdda62acbda26af1395d5161299e3ad615cec28d069d5cb01a8937e7b1c1', 'Muhammad Alif Firdaus', 'siswa', '2026-10-30 07:31:51'),
(13, '10243300', 'scrypt:32768:8:1$i2h20P7iyWB3Nudk$23c8da4e34f228938b0f17a75e5cef2bd2a5e52cbcc6fa7e5316a2d0f730685bbe4f546496bc663c76066f2ed4bb407b9d24e79efe14ab059285a5db4d129405', 'Muhammad Akbar', 'siswa', '2026-10-31 04:27:07');

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT untuk tabel `laporan_harian`
--
ALTER TABLE `laporan_harian`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT untuk tabel `pembimbing`
--
ALTER TABLE `pembimbing`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT untuk tabel `siswa`
--
ALTER TABLE `siswa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT untuk tabel `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

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
