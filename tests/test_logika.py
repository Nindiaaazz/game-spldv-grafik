"""Uji unit untuk spldv_game/logika.py."""
import sys
import unittest
from fractions import Fraction as F

from spldv_game.logika import (
    BERIMPIT, BERPOTONGAN, SEJAJAR, Langkah, Level, Persamaan, StatusLevel,
    baca_angka, format_angka, format_titik, hubungan_garis,
    potong_garis_dengan_kotak, titik_potong,
)

P1 = Persamaan(2, 1, 8)   # 2x + y = 8
P2 = Persamaan(1, -1, 1)  # x − y = 1   -> titik potong (3, 2)


def petunjuk():
    return ["Petunjuk 1", "Petunjuk 2"]


def buat_level(langkah):
    return Level(1, "Uji", "Indikator", "Cerita", [P1, P2], (-2, 10, -2, 10), 1, langkah)


class TestTanpaTkinter(unittest.TestCase):
    def test_logika_tidak_mengimpor_tkinter(self):
        sys.modules.pop("tkinter", None)
        sys.modules.pop("spldv_game.logika", None)
        import spldv_game.logika  # noqa: F401
        self.assertNotIn("tkinter", sys.modules)


class TestAngka(unittest.TestCase):
    def test_format_angka(self):
        self.assertEqual(format_angka(5.5), "5,5")
        self.assertEqual(format_angka(-1), "−1")
        self.assertEqual(format_angka(F(11, 2)), "5,5")
        self.assertEqual(format_angka(F(-1, 4)), "−0,25")
        self.assertEqual(format_angka(F(1, 3)), "1/3")
        self.assertEqual(format_angka(0), "0")
        self.assertEqual(format_angka(4.0), "4")

    def test_format_titik(self):
        self.assertEqual(format_titik(3, 2), "(3, 2)")
        self.assertEqual(format_titik((F(3), F(-2))), "(3, −2)")
        self.assertEqual(format_titik(F(11, 2), 2), "(5,5; 2)")

    def test_baca_angka(self):
        self.assertEqual(baca_angka("5,5"), F(11, 2))
        self.assertEqual(baca_angka("-1"), -1)
        self.assertEqual(baca_angka("−1"), -1)
        self.assertEqual(baca_angka(" 4 "), 4)
        self.assertEqual(baca_angka("11/2"), F(11, 2))
        for salah in ("", "abc", "1/0", "2x", "1,2,3", "nan", "--1"):
            self.assertIsNone(baca_angka(salah), salah)


class TestPersamaan(unittest.TestCase):
    def test_teks(self):
        self.assertEqual(P1.teks(), "2x + y = 8")
        self.assertEqual(P2.teks(), "x − y = 1")
        self.assertEqual(Persamaan(-1, 2, 4).teks(), "−x + 2y = 4")
        self.assertEqual(Persamaan(0, 1, 3).teks(), "y = 3")
        self.assertEqual(Persamaan(F(1, 2), 1, -3).teks(), "0,5x + y = −3")

    def test_tidak_valid(self):
        with self.assertRaises(ValueError):
            Persamaan(0, 0, 5)

    def test_dipenuhi_dan_hitung(self):
        self.assertTrue(P1.dipenuhi(3, 2))
        self.assertFalse(P1.dipenuhi(3, 3))
        self.assertEqual(P1.y_jika_x(0), 8)
        self.assertEqual(P1.x_jika_y(0), 4)
        self.assertEqual(Persamaan(2, 0, 11).x_jika_y(0), F(11, 2))
        self.assertIsNone(Persamaan(1, 0, 2).y_jika_x(0))
        self.assertIsNone(Persamaan(0, 1, 2).x_jika_y(0))

    def test_substitusi_dan_cek(self):
        self.assertEqual(P1.substitusi_teks("x", 0), "2(0) + y = 8")
        self.assertEqual(P1.substitusi_teks("y", 0), "2x + (0) = 8")
        self.assertEqual(P2.substitusi_teks("y", -2), "x − (−2) = 1")
        self.assertEqual(P1.cek_teks(3, 2), "2(3) + (2) = 8 ✓")
        self.assertEqual(P1.cek_teks(3, 3), "2(3) + (3) = 9 ≠ 8 ✗")


class TestGaris(unittest.TestCase):
    def test_titik_potong(self):
        self.assertEqual(titik_potong(P1, P2), (3, 2))
        self.assertEqual(titik_potong(Persamaan(2, 0, 11), Persamaan(0, 1, 1)),
                         (F(11, 2), 1))
        self.assertIsNone(titik_potong(P1, Persamaan(4, 2, 5)))

    def test_hubungan(self):
        self.assertEqual(hubungan_garis(P1, P2), BERPOTONGAN)
        self.assertEqual(hubungan_garis(P1, Persamaan(4, 2, 5)), SEJAJAR)
        self.assertEqual(hubungan_garis(P1, Persamaan(4, 2, 16)), BERIMPIT)

    def test_potong_kotak(self):
        self.assertEqual(potong_garis_dengan_kotak(P1, 0, 10, 0, 10), ((0, 8), (4, 0)))
        self.assertEqual(potong_garis_dengan_kotak(Persamaan(1, 0, 2), -5, 5, -5, 5),
                         ((2, -5), (2, 5)))
        self.assertEqual(potong_garis_dengan_kotak(Persamaan(1, -1, 0), 0, 4, 0, 4),
                         ((0, 0), (4, 4)))
        self.assertIsNone(potong_garis_dengan_kotak(P1, 20, 30, 20, 30))


class TestLangkahLevel(unittest.TestCase):
    def test_petunjuk_minimal_dua(self):
        with self.assertRaises(ValueError):
            Langkah("isian", "T", "?", ["satu"], "b", jawaban=1)

    def test_titik_bantu_harus_di_garis(self):
        with self.assertRaises(ValueError):
            buat_level([Langkah("plot", "T", "?", petunjuk(), "b", garis=0,
                                titik=[(0, 8), (1, 1)])])

    def test_potong_butuh_garis_berpotongan(self):
        with self.assertRaises(ValueError):
            Level(1, "U", "I", "C", [P1, Persamaan(4, 2, 5)], (0, 10, 0, 10), 1,
                  [Langkah("potong", "T", "?", petunjuk(), "b")])


class TestStatusLevel(unittest.TestCase):
    def setUp(self):
        self.level = buat_level([
            Langkah("isian", "Titik potong sumbu", "Jika x = 0, y = ?", petunjuk(),
                    "Pembahasan isian", jawaban=8, garis=0, titik_hasil=(0, 8)),
            Langkah("plot", "Menggambar garis", "Gambar garis 1", petunjuk(),
                    "Pembahasan plot", garis=0, titik=[(0, 8), (4, 0)]),
            Langkah("pilihan", "Jenis penyelesaian", "Hubungan garis?", petunjuk(),
                    "Pembahasan pilihan", opsi=["Sejajar", "Berpotongan"], benar=1),
            Langkah("potong", "Titik potong", "Klik titik potong", petunjuk(),
                    "Pembahasan potong"),
        ])
        self.status = StatusLevel(self.level)

    def test_semua_benar_langsung(self):
        s = self.status
        u = s.jawab_isian("8")
        self.assertTrue(u.benar and u.langkah_selesai)
        self.assertEqual(s.titik_ditemukan, [((0, 8), 0)])
        s.lanjut()
        u = s.klik_titik(0, 8)
        self.assertTrue(u.benar)
        self.assertFalse(u.langkah_selesai)
        self.assertTrue(s.klik_titik(1, 6).langkah_selesai)  # titik mana saja di garis
        self.assertEqual(s.garis_tergambar[0], ((0, 8), (1, 6)))
        s.lanjut()
        self.assertTrue(s.jawab_pilihan(1).benar)
        s.lanjut()
        self.assertTrue(s.klik_titik(3.0, 2.0).benar)
        self.assertTrue(s.lanjut())
        self.assertTrue(s.level_selesai)
        self.assertEqual((s.skor, s.skor_maks, s.bintang), (40, 40, 3))
        self.assertEqual(s.tahap_perlu_latihan, [])

    def test_isian_salah_dan_format(self):
        s = self.status
        self.assertFalse(s.jawab_isian("abc").benar)
        self.assertEqual(s.catatan[0].salah, 0)  # salah format tidak dihitung
        self.assertFalse(s.jawab_isian("4").benar)
        self.assertTrue(s.jawab_isian("8,0").benar)
        self.assertEqual(s.catatan[0].poin, 5)

    def test_plot_pesan_salah_dan_titik_sama(self):
        s = self.status
        s.jawab_isian("8")
        s.lanjut()
        u = s.klik_titik(3, 3)
        self.assertEqual(u.pesan, "Titik (3, 3) tidak terletak pada garis 2x + y = 8, "
                                  "karena hasilnya 9, bukan 8.")
        s.klik_titik(0, 8)
        u = s.klik_titik(0, 8)
        self.assertFalse(u.benar)
        self.assertIn("sudah kamu pilih", u.pesan)
        self.assertEqual(s.catatan[1].salah, 1)  # klik ulang tidak menambah salah

    def test_potong_satu_garis(self):
        s = self.status
        for _ in range(3):
            s.lihat_pembahasan()
            s.lanjut()
        u = s.klik_titik(4, 0)
        self.assertEqual(u.pesan, "Titik (4, 0) hanya terletak pada garis 2x + y = 8. "
                                  "Titik potong harus terletak pada KEDUA garis.")
        u = s.klik_titik(9, 9)
        self.assertIn("maupun", u.pesan)

    def test_petunjuk_dan_pembahasan(self):
        s = self.status
        self.assertEqual(s.minta_petunjuk(), "Petunjuk 1")
        self.assertEqual(s.minta_petunjuk(), "Petunjuk 2")
        self.assertIn("Semua petunjuk", s.minta_petunjuk())
        self.assertEqual(s.petunjuk_terlihat, ["Petunjuk 1", "Petunjuk 2"])
        s.jawab_isian("8")
        self.assertEqual(s.catatan[0].poin, 5)
        s.lanjut()
        s.klik_titik(0, 8)
        u = s.lihat_pembahasan()
        self.assertTrue(u.langkah_selesai)
        self.assertEqual(u.pesan, "Pembahasan plot")
        self.assertEqual(s.catatan[1].poin, 0)
        self.assertEqual(s.garis_tergambar[0], ((0, 8), (4, 0)))  # pakai titik bantu
        s.lanjut()
        s.jawab_pilihan(1)
        s.lanjut()
        s.klik_titik(3, 2)
        self.assertEqual((s.skor, s.bintang), (25, 2))  # 5+0+10+10 = 25/40
        self.assertEqual(s.tahap_perlu_latihan, ["Titik potong sumbu", "Menggambar garis"])

    def test_bintang(self):
        s = self.status
        for _ in range(4):
            s.lihat_pembahasan()
            s.lanjut()
        self.assertEqual((s.skor, s.bintang), (0, 0))

        s = StatusLevel(self.level)
        s.jawab_isian("1"); s.jawab_isian("8"); s.lanjut()     # 5
        for _ in range(3):
            s.lihat_pembahasan(); s.lanjut()                     # 0
        self.assertEqual((s.skor, s.bintang), (5, 1))

    def test_aksi_tidak_sah(self):
        s = self.status
        with self.assertRaises(ValueError):
            s.klik_titik(0, 8)          # langkah aktif adalah isian
        with self.assertRaises(RuntimeError):
            s.lanjut()                  # belum selesai
        s.jawab_isian("8")
        with self.assertRaises(RuntimeError):
            s.jawab_isian("8")          # sudah selesai


# ===========================================================================
# Uji memakai 5 soal asli dari data_soal.py
# ===========================================================================
from spldv_game import data_soal  # noqa: E402

TITIK_POTONG_SOAL = {1: (3, 2), 2: (4, 4), 3: (2, 3), 4: (4, 3), 5: (12, 8)}


def selesaikan_langkah(status):
    """Menjawab langkah aktif dengan benar pada percobaan pertama."""
    lk, lv = status.langkah_aktif, status.level
    if lk.jenis == "isian":
        return status.jawab_isian(format_angka(lk.jawaban))
    if lk.jenis == "pilihan":
        return status.jawab_pilihan(lk.benar)
    if lk.jenis == "plot":
        status.klik_titik(*lk.titik[0])
        return status.klik_titik(*lk.titik[1])
    return status.klik_titik(*lv.titik_potong)


class TestLimaSoal(unittest.TestCase):
    def test_titik_potong_kelima_soal(self):
        for lv in data_soal.semua_level():
            with self.subTest(level=lv.nomor):
                self.assertEqual(lv.titik_potong, TITIK_POTONG_SOAL[lv.nomor])
                for p in lv.persamaan:
                    self.assertTrue(p.dipenuhi(*lv.titik_potong))

    def test_semua_level_bisa_skor_penuh(self):
        total = 0
        for lv in data_soal.semua_level():
            with self.subTest(level=lv.nomor):
                s = StatusLevel(lv)
                while not s.level_selesai:
                    u = selesaikan_langkah(s)
                    self.assertTrue(u.benar and u.langkah_selesai)
                    s.lanjut()
                self.assertEqual((s.skor, s.bintang), (s.skor_maks, 3))
                self.assertEqual(s.tahap_perlu_latihan, [])
                total += s.skor
        self.assertEqual(total, 450)

    def test_salah_dan_petunjuk_mengurangi_poin(self):
        lv = data_soal.ambil_level(1)
        s = StatusLevel(lv)
        # langkah 1 (isian): salah sekali -> 5 poin
        self.assertFalse(s.jawab_isian("7").benar)
        selesaikan_langkah(s)
        s.lanjut()
        # langkah 2 (isian): memakai petunjuk -> 5 poin
        s.minta_petunjuk()
        selesaikan_langkah(s)
        s.lanjut()
        # langkah 3 (plot): melihat pembahasan -> 0 poin
        s.lihat_pembahasan()
        s.lanjut()
        # sisa langkah benar langsung -> 10 poin
        while not s.level_selesai:
            selesaikan_langkah(s)
            s.lanjut()
        self.assertEqual([c.poin for c in s.catatan[:4]], [5, 5, 0, 10])
        self.assertEqual(s.skor, 80 - 5 - 5 - 10)
        self.assertEqual(s.tahap_perlu_latihan,
                         ["Menentukan titik koordinat", "Menggambar garis"])

    def test_klik_titik_salah_memberi_pesan(self):
        lv = data_soal.ambil_level(1)
        s = StatusLevel(lv)
        while s.langkah_aktif.jenis != "plot":
            selesaikan_langkah(s)
            s.lanjut()
        u = s.klik_titik(3, 3)
        self.assertFalse(u.benar)
        self.assertEqual(u.pesan, "Titik (3, 3) tidak terletak pada garis 2x + y = 8, "
                                  "karena hasilnya 9, bukan 8.")
        while s.langkah_aktif.jenis != "potong":
            selesaikan_langkah(s)
            s.lanjut()
        u = s.klik_titik(4, 0)
        self.assertEqual(u.pesan, "Titik (4, 0) hanya terletak pada garis 2x + y = 8. "
                                  "Titik potong harus terletak pada KEDUA garis.")
        u = s.klik_titik(0, 0)
        self.assertEqual(u.pesan, "Titik (0, 0) tidak terletak pada garis 2x + y = 8 "
                                  "maupun x − y = 1.")


if __name__ == "__main__":
    unittest.main()
