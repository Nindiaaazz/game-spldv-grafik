"""Uji tampilan (smoke test) memakai canvas tkinter tersembunyi.

Dilewati otomatis jika komputer tidak memiliki tampilan (mis. server CI).
Memeriksa bahwa semua layar dapat digambar, semua level dapat dimainkan lewat
klik/keyboard, dan tidak ada elemen yang keluar dari canvas atau menimpa
tombol bawah, bahkan saat semua petunjuk dibuka dan ada jawaban salah.
"""
import tempfile
import unittest
from pathlib import Path

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None

from spldv_game import data_soal, penyimpanan
from spldv_game.logika import format_angka

LEBAR, TINGGI = 1100, 700


class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if tk is None:
            raise unittest.SkipTest("tkinter tidak tersedia")
        try:
            cls.root = tk.Tk()
        except tk.TclError as e:
            raise unittest.SkipTest(f"Tidak ada tampilan: {e}")
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        from spldv_game import ui
        self.ui = ui
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.canvas = tk.Canvas(self.root, width=LEBAR, height=TINGGI)
        self.canvas.pack()
        self.app = ui.App(self.canvas, LEBAR, TINGGI, self.folder)
        self.app.mulai()

    def tearDown(self):
        self.canvas.destroy()
        self.tmp.cleanup()

    # ---- alat bantu --------------------------------------------------------
    def cek_tata_letak(self):
        c = self.canvas
        for item in c.find_all():
            kotak = c.bbox(item)
            if kotak:
                self.assertTrue(kotak[0] >= -2 and kotak[1] >= -2 and kotak[2] <= LEBAR + 2
                                and kotak[3] <= TINGGI + 2,
                                f"Item keluar canvas: {c.type(item)} {kotak} "
                                f"{c.itemcget(item, 'text') if c.type(item) == 'text' else ''}")
        kiri = c.bbox("kiri")
        if kiri:
            self.assertLessEqual(kiri[3], self.ui.LayarLevel.BATAS_BAWAH + 2,
                                 "Kolom kiri menimpa tombol bawah")

    def tombol(self, awalan):
        for t in self.app.layar.tombol:
            if t.teks.startswith(awalan):
                return t
        self.fail(f"Tombol '{awalan}' tidak ditemukan di {type(self.app.layar).__name__}")

    def tekan(self, awalan):
        t = self.tombol(awalan)
        self.assertTrue(t.aktif, f"Tombol '{awalan}' nonaktif")
        self.app.layar.klik((t.x1 + t.x2) / 2, (t.y1 + t.y2) / 2)
        self.cek_tata_letak()

    def ketik(self, teks):
        for ch in teks:
            keysym = {"-": "minus", ",": "comma", "−": "minus"}.get(ch, ch)
            self.app.layar.ketik(keysym, "-" if ch == "−" else ch)
        self.cek_tata_letak()

    def tombol_keyboard(self, keysym):
        self.app.layar.ketik(keysym, "")
        self.cek_tata_letak()

    def klik_titik(self, x, y):
        layar = self.app.layar
        px, py = layar.grafik.ke_px(x, y)
        layar.klik(px + 3, py - 3)  # sedikit meleset: harus dibulatkan ke grid
        self.cek_tata_letak()

    def masuk(self, nama="Siti Aminah"):
        self.ketik(nama)
        self.tombol_keyboard("Return")
        self.assertIsInstance(self.app.layar, self.ui.LayarPilihLevel)

    # ---- tes ---------------------------------------------------------------
    def test_ui_tidak_mengimpor_tkinter(self):
        sumber = Path(self.ui.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import tkinter", sumber)

    def test_menu_wajib_nama(self):
        self.cek_tata_letak()
        self.tekan("▶  Mulai Bermain")
        self.assertIsInstance(self.app.layar, self.ui.LayarMenu)
        self.assertIn("Isi Nama", self.app.layar.pesan)
        self.masuk()

    def test_materi(self):
        self.tekan("Materi Singkat")
        for _ in range(3):
            self.tekan("Berikutnya")
        self.assertEqual(self.app.layar.halaman, 3)
        self.assertFalse(self.tombol("Berikutnya").aktif)
        self.tombol_keyboard("Left")
        self.assertEqual(self.app.layar.halaman, 2)
        self.tekan("▶  Mulai Bermain")           # nama belum diisi
        self.assertIsInstance(self.app.layar, self.ui.LayarMenu)

    def test_hover_koordinat(self):
        self.masuk()
        self.tombol("Mainkan").tekan()
        layar = self.app.layar
        layar.gerak(*layar.grafik.ke_px(3, 2))
        teks = [self.canvas.itemcget(i, "text") for i in self.canvas.find_withtag("hover")
                if self.canvas.type(i) == "text"]
        self.assertEqual(teks, ["(3, 2)"])

    def test_pembahasan_perlu_konfirmasi(self):
        self.masuk()
        self.tombol("Mainkan").tekan()
        self.tekan("Lihat Pembahasan")
        self.assertFalse(self.app.layar.status.langkah_selesai)
        self.tekan("Yakin?")
        s = self.app.layar.status
        self.assertTrue(s.langkah_selesai)
        self.assertEqual(s.catatan[0].poin, 0)
        self.assertEqual(self.app.layar.umpan[0], "pembahasan")

    def test_mainkan_semua_level_kondisi_terberat(self):
        self.masuk()
        self.tekan("Mainkan")                      # kartu level 1
        for nomor in range(1, data_soal.jumlah_level() + 1):
            layar = self.app.layar
            self.assertIsInstance(layar, self.ui.LayarLevel)
            self.assertEqual(layar.level.nomor, nomor)
            self._mainkan_level_dengan_bantuan()
            self.assertTrue(self.app.layar.selesai)
            self.assertIsNone(self.app.layar.pesan_simpan)
            self.tekan("Level Berikutnya" if nomor < 5 else "Lihat Hasil Belajar")
        self.assertIsInstance(self.app.layar, self.ui.LayarHasil)
        self.tekan("Pilih Level")
        self.assertIsInstance(self.app.layar, self.ui.LayarPilihLevel)
        baris = penyimpanan.baca_hasil(self.folder)
        self.assertEqual([b["level"] for b in baris], ["1", "2", "3", "4", "5"])
        self.assertEqual(set(self.app.hasil_terbaik), {1, 2, 3, 4, 5})

    def _mainkan_level_dengan_bantuan(self):
        layar = self.app.layar
        s, lv = layar.status, layar.level
        while not s.level_selesai:
            lk = s.langkah_aktif
            while s.catatan_aktif.petunjuk_dipakai < len(lk.petunjuk):
                self.tekan("Petunjuk (")
            if lk.jenis == "isian":
                self.ketik(format_angka(lk.jawaban + 1))
                self.tombol_keyboard("Return")
                self.assertEqual(layar.umpan[0], "salah")
                for _ in range(10):
                    self.tombol_keyboard("BackSpace")
                self.ketik(format_angka(lk.jawaban))
                self.tekan("Cek Jawaban")
            elif lk.jenis == "pilihan":
                salah = (lk.benar + 1) % len(lk.opsi)
                self.ketik(str(salah + 1))
                self.assertEqual(layar.umpan[0], "salah")
                self.tekan("ABCD"[lk.benar] + ".")
            elif lk.jenis == "plot":
                p = lv.persamaan[lk.garis]
                xmin, xmax, ymin, ymax = lv.rentang
                salah = next((x, y) for x in range(xmin, xmax + 1, int(lv.langkah_grid))
                             for y in range(ymin, ymax + 1, int(lv.langkah_grid))
                             if not p.dipenuhi(x, y))
                self.klik_titik(*salah)
                self.assertEqual(layar.umpan[0], "salah")
                self.assertIsNotNone(layar.titik_salah)
                self.klik_titik(*lk.titik[0])
                self.klik_titik(*lk.titik[0])        # titik sama: ditolak
                self.assertIn("sudah kamu pilih", layar.umpan[1])
                self.klik_titik(*lk.titik[1])
            else:
                p1, p2 = lv.persamaan
                satu_garis = next(t for t in s.garis_tergambar[0] if not p2.dipenuhi(*t))
                self.klik_titik(*satu_garis)
                self.assertIn("KEDUA garis", layar.umpan[1])
                self.klik_titik(*lv.titik_potong)
            self.assertTrue(s.langkah_selesai, lk.pertanyaan)
            self.assertEqual(layar.umpan[0], "benar")
            self.tekan("Selesaikan Level" if s.indeks == s.jumlah_langkah - 1 else "Lanjut")


if __name__ == "__main__":
    unittest.main()
