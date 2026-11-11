"""Uji alur tampilan memakai KANVAS TIRUAN (tanpa tkinter, tanpa jendela).

KanvasTiruan meniru method tkinter.Canvas yang dipakai ui.py
(create_text, create_line, create_oval, create_rectangle, create_polygon,
bbox, delete, bind, dll.). Event klik/ketik dikirim lewat fungsi yang
didaftarkan App dengan canvas.bind(), persis seperti tkinter.
"""
import math
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from spldv_game import penyimpanan
from spldv_game.logika import MINUS, format_angka

LEBAR, TINGGI = 1100, 700


def _ratakan(nilai):
    """(1, 2), [3, (4, 5)] -> [1, 2, 3, 4, 5]"""
    hasil = []
    for v in nilai:
        if isinstance(v, (list, tuple)):
            hasil.extend(_ratakan(v))
        else:
            hasil.append(float(v))
    return hasil


class JendelaTiruan:
    def __init__(self):
        self.ditutup = False

    def destroy(self):
        self.ditutup = True


class KanvasTiruan:
    """Pengganti tkinter.Canvas untuk pengujian."""

    def __init__(self):
        self.item = {}          # id -> dict(jenis, koordinat, opsi, tags)
        self.urutan = []
        self.ikatan = {}        # "<Button-1>" -> fungsi
        self.kursor = ""
        self.jendela = JendelaTiruan()
        self._id = 0

    # ---- pembuatan item --------------------------------------------------
    def _buat(self, jenis, args, opsi):
        self._id += 1
        tags = opsi.pop("tags", ())
        tags = (tags,) if isinstance(tags, str) else tuple(tags)
        self.item[self._id] = {"jenis": jenis, "koordinat": _ratakan(args),
                               "opsi": opsi, "tags": tags}
        self.urutan.append(self._id)
        return self._id

    def create_text(self, *args, **opsi):
        return self._buat("text", args, opsi)

    def create_line(self, *args, **opsi):
        return self._buat("line", args, opsi)

    def create_oval(self, *args, **opsi):
        return self._buat("oval", args, opsi)

    def create_rectangle(self, *args, **opsi):
        return self._buat("rectangle", args, opsi)

    def create_polygon(self, *args, **opsi):
        return self._buat("polygon", args, opsi)

    # ---- pencarian & ukuran ------------------------------------------------
    def _cocok(self, kunci):
        if kunci == "all":
            return list(self.urutan)
        if isinstance(kunci, int):
            return [kunci] if kunci in self.item else []
        return [i for i in self.urutan if kunci in self.item[i]["tags"]]

    def find_withtag(self, kunci):
        return tuple(self._cocok(kunci))

    def find_all(self):
        return tuple(self.urutan)

    def type(self, i):
        return self.item[i]["jenis"]

    def itemcget(self, i, opsi):
        return self.item[i]["opsi"].get(opsi, "")

    def itemconfig(self, kunci, **opsi):
        for i in self._cocok(kunci):
            self.item[i]["opsi"].update(opsi)

    def _kotak_teks(self, data):
        x, y = data["koordinat"][:2]
        font = data["opsi"].get("font", ("Segoe UI", 11))
        ukuran = font[1]
        lebar_huruf, tinggi_baris = ukuran * 0.8, ukuran * 1.7
        batas = data["opsi"].get("width", 0) or 0
        baris, lebar = 0, 0
        for b in str(data["opsi"].get("text", "")).split("\n"):
            w = len(b) * lebar_huruf
            if batas and w > batas:
                baris += math.ceil(w / batas)
                w = batas
            else:
                baris += 1
            lebar = max(lebar, w)
        tinggi = baris * tinggi_baris
        anchor = data["opsi"].get("anchor", "center")
        x1 = x - lebar / 2
        if "w" in anchor:
            x1 = x
        elif "e" in anchor:
            x1 = x - lebar
        y1 = y - tinggi / 2
        if anchor.startswith("n"):
            y1 = y
        elif anchor.startswith("s"):
            y1 = y - tinggi
        return (x1, y1, x1 + lebar, y1 + tinggi)

    def bbox(self, kunci):
        kotak = []
        for i in self._cocok(kunci):
            data = self.item[i]
            if data["jenis"] == "text":
                kotak.append(self._kotak_teks(data))
            else:
                xs, ys = data["koordinat"][0::2], data["koordinat"][1::2]
                kotak.append((min(xs), min(ys), max(xs), max(ys)))
        if not kotak:
            return None
        return (int(min(k[0] for k in kotak)), int(min(k[1] for k in kotak)),
                int(math.ceil(max(k[2] for k in kotak))),
                int(math.ceil(max(k[3] for k in kotak))))

    # ---- lain-lain ---------------------------------------------------------
    def delete(self, kunci):
        for i in self._cocok(kunci):
            del self.item[i]
            self.urutan.remove(i)

    def tag_lower(self, i, di_bawah=None):
        pass

    def config(self, **opsi):
        self.kursor = opsi.get("cursor", self.kursor)

    def bind(self, urutan, fungsi):
        self.ikatan[urutan] = fungsi

    def focus_set(self):
        pass

    def winfo_toplevel(self):
        return self.jendela

    # ---- alat bantu uji ----------------------------------------------------
    def picu(self, urutan, **data):
        self.ikatan[urutan](SimpleNamespace(**data))

    def semua_teks(self):
        return [self.item[i]["opsi"].get("text", "") for i in self.urutan
                if self.item[i]["jenis"] == "text"]


class TestTampilan(unittest.TestCase):
    def setUp(self):
        from spldv_game import ui
        self.ui = ui
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "data_hasil"
        self.kanvas = KanvasTiruan()
        self.app = ui.App(self.kanvas, LEBAR, TINGGI, self.folder)
        self.app.mulai()

    def tearDown(self):
        self.tmp.cleanup()

    # ---- alat bantu --------------------------------------------------------
    @property
    def layar(self):
        return self.app.layar

    def klik(self, x, y):
        self.kanvas.picu("<Button-1>", x=x, y=y)

    def tekan(self, teks, persis=False):
        """Klik tombol berdasarkan teksnya (awalan, atau persis)."""
        for t in self.layar.tombol:
            if (t.teks == teks) if persis else t.teks.startswith(teks):
                self.assertTrue(t.aktif, f"Tombol '{teks}' nonaktif")
                self.klik((t.x1 + t.x2) / 2, (t.y1 + t.y2) / 2)
                return
        daftar = [t.teks for t in self.layar.tombol]
        self.fail(f"Tombol '{teks}' tidak ada. Tombol tersedia: {daftar}")

    def ketik(self, teks):
        for ch in teks:
            self.kanvas.picu("<Key>", keysym=ch, char=ch)

    def enter(self):
        self.kanvas.picu("<Key>", keysym="Return", char="\r")

    def klik_grafik(self, x, y):
        px, py = self.layar.grafik.ke_px(x, y)
        self.klik(px + 4, py + 3)  # sedikit meleset: harus dibulatkan ke titik grid

    def teks_ada(self, potongan):
        return any(potongan in t for t in self.kanvas.semua_teks())

    def masuk(self, nama="Siti Aminah"):
        self.ketik(nama)
        self.tekan("▶  Mulai Bermain")
        self.assertIsInstance(self.layar, self.ui.LayarPilihLevel)

    def jawab_benar_lewat_tombol(self):
        """Menjawab langkah aktif dengan klik tombol / klik grafik."""
        s, lv = self.layar.status, self.layar.level
        lk = s.langkah_aktif
        if lk.jenis == "isian":
            for ch in format_angka(lk.jawaban):     # keypad di layar
                self.tekan(ch, persis=True)
            self.tekan("Cek Jawaban")
        elif lk.jenis == "pilihan":
            self.tekan("ABCD"[lk.benar] + ".")
        elif lk.jenis == "plot":
            self.klik_grafik(*lk.titik[0])
            self.klik_grafik(*lk.titik[1])
        else:
            self.klik_grafik(*lv.titik_potong)
        self.assertTrue(s.langkah_selesai, f"Gagal: {lk.pertanyaan}")
        self.assertTrue(self.teks_ada("BENAR"))

    # ---- tes ---------------------------------------------------------------
    def test_ui_tidak_memakai_tkinter(self):
        sumber = Path(self.ui.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import tkinter", sumber)
        self.assertNotIn("tkinter", sys.modules.get("spldv_game.ui").__dict__)

    def test_menu_wajib_isi_nama(self):
        self.assertTrue(self.teks_ada("Petualangan Grafik SPLDV"))
        self.tekan("▶  Mulai Bermain")
        self.assertIsInstance(self.layar, self.ui.LayarMenu)
        self.assertTrue(self.teks_ada("Isi Nama/NIM terlebih dahulu"))
        self.ketik("Budi")
        self.kanvas.picu("<Key>", keysym="BackSpace", char="\b")
        self.assertEqual(self.app.nama, "Bud")
        self.enter()
        self.assertIsInstance(self.layar, self.ui.LayarPilihLevel)
        self.assertTrue(self.teks_ada("Halo, Bud!"))

    def test_materi_empat_halaman(self):
        self.tekan("Materi Singkat")
        judul = []
        for k in range(4):
            judul.append(self.layar.daftar[self.layar.halaman]["judul"])
            self.assertTrue(self.teks_ada(judul[-1]))
            if k < 3:
                self.tekan("Berikutnya")
        self.assertEqual(judul[0], "Apa itu SPLDV?")
        self.assertTrue(self.teks_ada("(3, 1) = penyelesaian"))
        self.tekan("◀ Sebelumnya")
        self.assertEqual(self.layar.halaman, 2)

    def test_klik_grafik_salah_dan_petunjuk(self):
        self.masuk()
        self.tekan("Mainkan")
        s = self.layar.status
        self.tekan("Petunjuk (2 lagi)")
        self.assertTrue(self.teks_ada("Ganti (substitusi) x dengan 0"))
        self.assertTrue(any(t.teks == "Petunjuk (1 lagi)" for t in self.layar.tombol))
        self.ketik("9")
        self.enter()
        self.assertTrue(self.teks_ada("Jawaban 9 belum tepat"))
        while s.langkah_aktif.jenis != "plot":
            if s.langkah_selesai:
                self.tekan("Lanjut")
                continue
            self.layar.input = ""
            self.jawab_benar_lewat_tombol()
        self.klik_grafik(3, 3)
        self.assertTrue(self.teks_ada("Titik (3, 3) tidak terletak pada garis 2x + y = 8, "
                                      "karena hasilnya 9, bukan 8."))
        self.assertEqual(s.catatan[0].poin, 5)   # petunjuk + salah di langkah 1

    def test_hover_menampilkan_koordinat(self):
        self.masuk()
        self.tekan("Mainkan")
        px, py = self.layar.grafik.ke_px(3, 2)
        self.kanvas.picu("<Motion>", x=px, y=py)
        teks_hover = [self.kanvas.item[i]["opsi"]["text"]
                      for i in self.kanvas.find_withtag("hover")
                      if self.kanvas.type(i) == "text"]
        self.assertEqual(teks_hover, ["(3, 2)"])

    def test_mainkan_lima_level_skor_penuh_dan_csv(self):
        self.masuk()
        self.tekan("Mainkan")                         # kartu level 1
        for nomor in range(1, 6):
            self.assertIsInstance(self.layar, self.ui.LayarLevel)
            self.assertEqual(self.layar.level.nomor, nomor)
            s = self.layar.status
            while not self.layar.selesai:
                self.jawab_benar_lewat_tombol()
                self.tekan("Selesaikan Level" if s.indeks == s.jumlah_langkah - 1
                           else "Lanjut")
            self.assertTrue(self.teks_ada("Level Selesai!"))
            self.assertTrue(self.teks_ada(f"Skor: {s.skor_maks} / {s.skor_maks}"))
            self.assertTrue(self.teks_ada("Hasil belajar sudah tersimpan."))
            self.tekan("Level Berikutnya" if nomor < 5 else "Lihat Hasil Belajar")

        self.assertIsInstance(self.layar, self.ui.LayarHasil)
        self.assertTrue(self.teks_ada("Total skor: 450 dari 450"))

        baris = penyimpanan.baca_hasil(self.folder)
        self.assertEqual([b["level"] for b in baris], ["1", "2", "3", "4", "5"])
        for b in baris:
            self.assertEqual(b["nama"], "Siti Aminah")
            self.assertEqual(b["skor"], b["skor_maks"])
            self.assertEqual(b["bintang"], "3")
            self.assertEqual(b["tahap_perlu_latihan"], "")
        self.assertTrue((self.folder / "hasil_belajar.csv").exists())

        self.tekan("Pilih Level")
        self.assertTrue(self.teks_ada("Total skor: 450 dari 450"))

    def test_isian_negatif_dan_desimal_lewat_keypad(self):
        self.masuk()
        self.tekan("Mainkan")
        self.tekan(MINUS, persis=True)
        self.tekan("5", persis=True)
        self.tekan(",", persis=True)
        self.tekan("5", persis=True)
        self.assertEqual(self.layar.input, f"{MINUS}5,5")
        self.tekan("⌫", persis=True)
        self.tekan(MINUS, persis=True)
        self.assertEqual(self.layar.input, "5,")

    def test_tombol_keluar(self):
        self.tekan("Keluar")
        self.assertTrue(self.kanvas.jendela.ditutup)


if __name__ == "__main__":
    unittest.main()
