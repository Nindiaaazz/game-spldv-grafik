"""Uji unit untuk spldv_game/data_soal.py."""
import unittest

from spldv_game import data_soal
from spldv_game.data_soal import DAFTAR_TAHAP, langkah_koordinat, langkah_titik_potong
from spldv_game.logika import Persamaan, StatusLevel, format_angka

TITIK_POTONG = {1: (3, 2), 2: (4, 4), 3: (2, 3), 4: (4, 3), 5: (12, 8)}


def di_dalam_dan_di_grid(level, titik):
    xmin, xmax, ymin, ymax = level.rentang
    x, y = titik
    return (xmin <= x <= xmax and ymin <= y <= ymax
            and x % level.langkah_grid == 0 and y % level.langkah_grid == 0)


class TestFungsiBantu(unittest.TestCase):
    def test_langkah_koordinat(self):
        p = Persamaan(2, 1, 8)
        isian1, isian2, plot = langkah_koordinat(p, "Garis 1", [("x", 0), ("y", 0)])
        self.assertIn("Jika x = 0, maka y = ... ?", isian1.pertanyaan)
        self.assertEqual(isian1.petunjuk[0],
                         "Ganti (substitusi) x dengan 0 pada persamaan 2x + y = 8.")
        self.assertIn("2(0) + y = 8", isian1.petunjuk[1])
        self.assertEqual(isian1.pembahasan,
                         "2(0) + y = 8 → y = 8. Jadi diperoleh titik (0, 8).")
        self.assertEqual((isian1.jawaban, isian1.titik_hasil), (8, (0, 8)))
        self.assertEqual((isian2.jawaban, isian2.titik_hasil), (4, (4, 0)))
        self.assertEqual((plot.jenis, plot.garis, plot.titik), ("plot", 0, [(0, 8), (4, 0)]))

    def test_tahapan_hitung_lengkap(self):
        p = Persamaan(2, 1, 11)
        isian, _, _ = langkah_koordinat(p, "Garis 1", [("x", 5), ("x", 0)])
        self.assertEqual(isian.pembahasan,
                         "2(5) + y = 11 → 10 + y = 11 → y = 11 − 10 "
                         "→ y = 1. Jadi diperoleh titik (5, 1).")
        p = Persamaan(1, -1, 1)
        isian, _, _ = langkah_koordinat(p, "Garis 2", [("x", 0), ("y", 0)])
        self.assertEqual(isian.pembahasan,
                         "(0) − y = 1 → −y = 1 → y = −1. "
                         "Jadi diperoleh titik (0, −1).")

    def test_garis_dari_nama(self):
        langkah = langkah_koordinat(Persamaan(1, 1, 5), "Garis 2", [("x", 0), ("y", 0)])
        self.assertTrue(all(lk.garis == 1 for lk in langkah))

    def test_titik_potong_sejajar(self):
        with self.assertRaises(ValueError):
            langkah_titik_potong(Persamaan(1, 1, 2), Persamaan(2, 2, 5))


class TestDataLevel(unittest.TestCase):
    def setUp(self):
        self.semua = data_soal.semua_level()

    def test_lima_level_berurutan(self):
        self.assertEqual(len(self.semua), 5)
        self.assertEqual(data_soal.jumlah_level(), 5)
        self.assertEqual([lv.nomor for lv in self.semua], [1, 2, 3, 4, 5])
        self.assertEqual(data_soal.ambil_level(4).judul, "Belanja Buku dan Pensil")
        with self.assertRaises(ValueError):
            data_soal.ambil_level(6)

    def test_level_baru_setiap_dipanggil(self):
        self.assertIsNot(data_soal.semua_level()[0], self.semua[0])

    def test_titik_potong(self):
        for lv in self.semua:
            self.assertEqual(lv.titik_potong, TITIK_POTONG[lv.nomor], lv.judul)
            self.assertTrue(di_dalam_dan_di_grid(lv, lv.titik_potong), lv.judul)

    def test_setiap_langkah_lengkap(self):
        for lv in self.semua:
            for lk in lv.langkah:
                self.assertGreaterEqual(len(lk.petunjuk), 2)
                self.assertTrue(lk.pembahasan.strip())
                self.assertIn(lk.tahap, DAFTAR_TAHAP)

    def test_titik_bisa_diklik(self):
        """Titik bantu dan titik hasil isian harus di dalam rentang dan tepat di grid."""
        for lv in self.semua:
            for lk in lv.langkah:
                for t in lk.titik + ([lk.titik_hasil] if lk.titik_hasil else []):
                    self.assertTrue(di_dalam_dan_di_grid(lv, t), f"{lv.judul} {t}")

    def test_level4_memakai_x5(self):
        lv = data_soal.ambil_level(4)
        plot = [lk for lk in lv.langkah if lk.jenis == "plot"]
        self.assertEqual(plot[0].titik, [(0, 11), (5, 1)])
        self.assertEqual(plot[1].titik, [(0, 5), (10, 0)])
        isian_x5 = [lk for lk in lv.langkah if lk.titik_hasil == (5, 1)][0]
        self.assertIn("5,5", isian_x5.petunjuk[0])

    def test_level5_grid_dua(self):
        lv = data_soal.ambil_level(5)
        self.assertEqual((lv.rentang, lv.langkah_grid), ((0, 30, 0, 30), 2))
        self.assertTrue(any(lk.jenis == "isian" and lk.jawaban == 56 for lk in lv.langkah))

    def test_simulasi_semua_benar(self):
        """Setiap level dapat diselesaikan dengan skor penuh."""
        for lv in self.semua:
            s = StatusLevel(lv)
            while not s.level_selesai:
                lk = s.langkah_aktif
                if lk.jenis == "isian":
                    u = s.jawab_isian(format_angka(lk.jawaban))
                elif lk.jenis == "pilihan":
                    u = s.jawab_pilihan(lk.benar)
                elif lk.jenis == "plot":
                    s.klik_titik(*lk.titik[0])
                    u = s.klik_titik(*lk.titik[1])
                else:
                    u = s.klik_titik(*lv.titik_potong)
                self.assertTrue(u.benar and u.langkah_selesai, lk.pertanyaan)
                s.lanjut()
            self.assertEqual((s.skor, s.bintang), (s.skor_maks, 3), lv.judul)


if __name__ == "__main__":
    unittest.main()
