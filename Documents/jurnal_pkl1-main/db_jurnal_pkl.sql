-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 11, 2026 at 04:21 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

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
-- Table structure for table `absensi`
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
-- Dumping data for table `absensi`
--

INSERT INTO `absensi` (`id`, `siswa_id`, `tanggal`, `status`, `keterangan`, `foto_bukti`, `lokasi`, `is_manual`, `created_at`) VALUES
(22, 12, '2026-11-11', 'Alpa', 'Otomatis Alpa oleh Sistem (Lewat Jam 15:00 WIB)', NULL, NULL, 0, '2026-11-11 10:42:06'),
(23, 11, '2026-11-11', 'Alpa', 'Otomatis Alpa oleh Sistem (Lewat Jam 15:00 WIB)', NULL, NULL, 0, '2026-11-11 12:19:36');

-- --------------------------------------------------------

--
-- Table structure for table `laporan_harian`
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
-- Dumping data for table `laporan_harian`
--

INSERT INTO `laporan_harian` (`id`, `siswa_id`, `tanggal`, `minggu_ke`, `tanggal_mulai`, `tanggal_selesai`, `deskripsi_kegiatan`, `foto_bukti`, `alasan_terlambat`, `status_validasi`, `catatan_pembimbing`, `created_at`) VALUES
(9, 11, '2026-11-09', NULL, NULL, NULL, 'Membuat erd', '9d04438a6de14740ba793ff79aa92aac_Cuplikan_layar_2026-08-03_101649.png', 'Tidak ada laptop', 'Disetujui', 'Bagus', '2026-11-09 06:28:14');

-- --------------------------------------------------------

--
-- Table structure for table `nilai_pkl`
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

-- --------------------------------------------------------

--
-- Table structure for table `pembimbing`
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
-- Dumping data for table `pembimbing`
--

INSERT INTO `pembimbing` (`id`, `user_id`, `nama_perusahaan`, `jabatan`, `divisi`, `no_hp`, `email`, `alamat_perusahaan`, `created_at`) VALUES
(1, 3, 'PT. Media Naraya Cipta', 'Developer', 'IT', '0838666666', 'moonveilmc6@gmail.com', 'Jl. Mekarwangi', '2026-10-24 04:19:18');

-- --------------------------------------------------------

--
-- Table structure for table `pengajuan_absensi`
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

-- --------------------------------------------------------

--
-- Table structure for table `pengumuman_pembimbing`
--

CREATE TABLE `pengumuman_pembimbing` (
  `id` int(11) NOT NULL,
  `pesan` text NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pengumuman_pembimbing`
--

INSERT INTO `pengumuman_pembimbing` (`id`, `pesan`, `updated_at`) VALUES
(1, 'besok libur', '2026-11-11 10:02:10'),
(2, 'tes', '2026-11-11 10:02:14'),
(3, 'tes', '2026-11-11 10:02:19'),
(4, 'tes', '2026-11-11 10:02:26'),
(5, 'tes', '2026-11-11 10:06:33'),
(6, 'tes', '2026-11-11 12:54:40'),
(7, 'tes', '2026-11-11 12:54:52');

-- --------------------------------------------------------

--
-- Table structure for table `siswa`
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
-- Dumping data for table `siswa`
--

INSERT INTO `siswa` (`id`, `user_id`, `nisn`, `kelas_jurusan`, `sekolah`, `tgl_mulai_pkl`, `tgl_selesai_pkl`, `tempat_lahir`, `tanggal_lahir`, `jenis_kelamin`, `no_hp`, `email`, `alamat`, `foto_profil`) VALUES
(11, 14, '10243301', 'XII PPLG B', 'SMK Negeri 2 Cimahi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(12, 15, '10243300', 'XII PPLG B', 'SMK Negeri 2 Cimahi', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `users`
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
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `nama`, `role`, `is_active`, `created_at`) VALUES
(2, 'pembimbing_pkl', 'scrypt:32768:8:1$OqTkMEpguJtcfeXZ$9bffd894dbb88ac08989170212e22cd91612908600b32b45eb9f914fcbba48c5a669c1d76b8d3178a309763e2d010e3798fe8693c6ec32c9028fa5553a2b0aef', 'Budi S.Kom (Guru)', 'pembimbing_pkl', 1, '2026-08-15 03:22:21'),
(3, 'pembimbing_ind', 'scrypt:32768:8:1$OqTkMEpguJtcfeXZ$9bffd894dbb88ac08989170212e22cd91612908600b32b45eb9f914fcbba48c5a669c1d76b8d3178a309763e2d010e3798fe8693c6ec32c9028fa5553a2b0aef', 'Erik Setiawan', 'pembimbing_industri', 1, '2026-08-15 03:22:21'),
(14, '10243301', 'scrypt:32768:8:1$KFCTGYHiVtZjCnfm$482598ab584b52684757a0a72e894ead3bfc423b70e1a0af462a4cfa3a8cf58732b70e422bc54033375564b21e2d7d13f36b7a7a6375e52ca07ca154db8113f8', 'Muhammad Alif Firdaus', 'siswa', 1, '2026-11-09 06:23:38'),
(15, '10243300', 'scrypt:32768:8:1$cebcDkpUgBeVayx6$d118c49e7a49f15cbb5a8d05c3406ad79101ba4ea8ce4484d6081d8c3b495c2a49eba38434d2ef11f24ef0ec5e805d88d522f9f6401e84ca0b1e30b1989165ac', 'Muhammad Akbar', 'siswa', 1, '2026-11-09 07:01:16');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `absensi`
--
ALTER TABLE `absensi`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`);

--
-- Indexes for table `laporan_harian`
--
ALTER TABLE `laporan_harian`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`);

--
-- Indexes for table `nilai_pkl`
--
ALTER TABLE `nilai_pkl`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`),
  ADD KEY `pembimbing_id` (`pembimbing_id`);

--
-- Indexes for table `pembimbing`
--
ALTER TABLE `pembimbing`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  ADD PRIMARY KEY (`id`),
  ADD KEY `siswa_id` (`siswa_id`);

--
-- Indexes for table `pengumuman_pembimbing`
--
ALTER TABLE `pengumuman_pembimbing`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `siswa`
--
ALTER TABLE `siswa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nisn` (`nisn`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `absensi`
--
ALTER TABLE `absensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `laporan_harian`
--
ALTER TABLE `laporan_harian`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `nilai_pkl`
--
ALTER TABLE `nilai_pkl`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `pembimbing`
--
ALTER TABLE `pembimbing`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT for table `pengumuman_pembimbing`
--
ALTER TABLE `pengumuman_pembimbing`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `siswa`
--
ALTER TABLE `siswa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `absensi`
--
ALTER TABLE `absensi`
  ADD CONSTRAINT `absensi_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `laporan_harian`
--
ALTER TABLE `laporan_harian`
  ADD CONSTRAINT `laporan_harian_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `nilai_pkl`
--
ALTER TABLE `nilai_pkl`
  ADD CONSTRAINT `nilai_pkl_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `nilai_pkl_ibfk_2` FOREIGN KEY (`pembimbing_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `pembimbing`
--
ALTER TABLE `pembimbing`
  ADD CONSTRAINT `pembimbing_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `pengajuan_absensi`
--
ALTER TABLE `pengajuan_absensi`
  ADD CONSTRAINT `pengajuan_absensi_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `siswa`
--
ALTER TABLE `siswa`
  ADD CONSTRAINT `siswa_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
