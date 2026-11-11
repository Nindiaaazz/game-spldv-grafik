"""
Semua layar/tampilan game SPLDV metode grafik.

ATURAN: modul ini TIDAK mengimpor tkinter secara langsung.
Canvas (1100x700) dibuat di main.py lalu diberikan ke App. Semua tombol,
teks, dan grafik digambar sendiri memakai method canvas.

Setiap layar adalah class dengan method:
    gambar()                 -> menggambar ulang seluruh layar
    klik(x, y)               -> klik kiri mouse
    gerak(x, y)              -> mouse bergerak
    ketik(keysym, char)      -> tombol keyboard ditekan
"""

import math
import textwrap
from fractions import Fraction
from pathlib import Path

from . import data_soal, penyimpanan
from .logika import (
    MINUS, POIN_DIBANTU, POIN_LANGSUNG, Persamaan, StatusLevel,
    format_angka, format_titik, potong_garis_dengan_kotak,
)

# ===========================================================================
# Warna & huruf
# ===========================================================================
HURUF = "Segoe UI"

WARNA = {
    "latar": "#EEF3FA",
    "putih": "#FFFFFF",
    "utama": "#2B6CB0",
    "utama_gelap": "#1E4E8C",
    "utama_muda": "#EBF4FF",
    "utama_tepi": "#90CDF4",
    "teks": "#1A202C",
    "lembut": "#4A5568",
    "abu": "#A0AEC0",
    "tepi": "#CBD5E0",
    "grid": "#E2E8F0",
    "sumbu": "#2D3748",
    "garis1": "#2B6CB0",
    "garis2": "#DD6B20",
    "potong": "#E53E3E",
    "benar": "#2F855A",
    "benar_muda": "#E6FFED",
    "salah": "#C53030",
    "salah_muda": "#FFF5F5",
    "kuning": "#ECC94B",
    "kuning_tua": "#B7791F",
    "kuning_muda": "#FEFCBF",
    "bintang": "#ECC94B",
    "bintang_tepi": "#B7791F",
    "bintang_kosong": "#E2E8F0",
}
WARNA_GARIS = (WARNA["garis1"], WARNA["garis2"])

# (isi, isi saat hover, tepi, warna teks)
GAYA_TOMBOL = {
    "utama": (WARNA["utama"], WARNA["utama_gelap"], WARNA["utama"], WARNA["putih"]),
    "sekunder": (WARNA["putih"], WARNA["utama_muda"], WARNA["utama"], WARNA["utama"]),
    "hijau": (WARNA["benar"], "#276749", WARNA["benar"], WARNA["putih"]),
    "kuning": (WARNA["kuning"], "#D69E2E", WARNA["kuning_tua"], WARNA["teks"]),
    "bahaya": (WARNA["salah"], "#9B2C2C", WARNA["salah"], WARNA["putih"]),
    "pilihan": (WARNA["putih"], WARNA["utama_muda"], WARNA["tepi"], WARNA["teks"]),
    "opsi_salah": (WARNA["salah_muda"], WARNA["salah_muda"], WARNA["salah"], WARNA["salah"]),
    "opsi_benar": (WARNA["benar_muda"], WARNA["benar_muda"], WARNA["benar"], WARNA["benar"]),
    "nonaktif": ("#EDF2F7", "#EDF2F7", WARNA["tepi"], WARNA["abu"]),
}

KEYPAD = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", MINUS, ",", "⌫"]
TOMBOL_HAPUS = "⌫"   # ⌫


# ===========================================================================
# Fungsi bantu menggambar
# ===========================================================================
def huruf(ukuran, tebal=False):
    return (HURUF, ukuran, "bold") if tebal else (HURUF, ukuran)


def _tags(tag):
    if not tag:
        return ()
    return (tag,) if isinstance(tag, str) else tuple(tag)


def bungkus(teks, lebar_px, ukuran=11, tebal=False):
    """Memecah teks menjadi beberapa baris (textwrap) agar muat dalam lebar_px.

    Lebar rata-rata huruf Segoe UI diperkirakan ~0,6 x ukuran (px per karakter).
    Baris baru (\\n) pada teks asli tetap dipertahankan. Sebagai pengaman,
    create_text juga diberi width sehingga teks tidak mungkin keluar kotak.
    """
    lebar_huruf = ukuran * (0.66 if tebal else 0.6)
    maks = max(4, int(lebar_px / lebar_huruf))
    hasil = []
    for paragraf in str(teks).split("\n"):
        if not paragraf.strip():
            hasil.append("")
            continue
        hasil.extend(textwrap.wrap(paragraf, width=maks, break_on_hyphens=False) or [""])
    return "\n".join(hasil)


def tulis(c, x, y, teks, ukuran=11, tebal=False, warna=None, lebar=None,
          anchor="nw", rata="left", tag=None):
    """Menulis teks; jika lebar diberikan, teks dibungkus agar tidak keluar kotak."""
    if lebar:
        teks = bungkus(teks, lebar, ukuran, tebal)
    return c.create_text(x, y, text=teks, font=huruf(ukuran, tebal),
                         fill=warna or WARNA["teks"], anchor=anchor, justify=rata,
                         width=lebar or 0, tags=_tags(tag))


def bawah(c, item, cadangan=0):
    kotak = c.bbox(item)
    return kotak[3] if kotak else cadangan


def kotak_bulat(c, x1, y1, x2, y2, r=12, **opsi):
    """Persegi panjang bersudut bulat (create_polygon dengan smooth=True)."""
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    titik = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1,
        x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2,
        x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2,
        x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    if "tags" in opsi:
        opsi["tags"] = _tags(opsi["tags"])
    return c.create_polygon(titik, smooth=True, **opsi)


def kotak_teks(c, x1, y, x2, teks, ukuran=11, judul=None, isi=None, tepi=None,
               warna_judul=None, warna_teks=None, tebal=False, pad=12, tag=None):
    """Kotak bulat yang tingginya menyesuaikan isi teks. Mengembalikan y bawah."""
    lebar = x2 - x1 - 2 * pad
    yy = y + pad
    pertama = None
    if judul:
        pertama = tulis(c, x1 + pad, yy, judul, max(8, ukuran - 2), True,
                        warna_judul or WARNA["utama"], lebar, tag=tag)
        yy = bawah(c, pertama, yy) + 4
    item = tulis(c, x1 + pad, yy, teks, ukuran, tebal, warna_teks, lebar, tag=tag)
    pertama = pertama or item
    y_bawah = bawah(c, item, yy) + pad
    latar = kotak_bulat(c, x1, y, x2, y_bawah, 12, fill=isi or WARNA["putih"],
                        outline=tepi or WARNA["tepi"], width=1.5, tags=tag)
    c.tag_lower(latar, pertama)
    return y_bawah


def bintang(c, cx, cy, r, terisi=True, tag=None):
    """Satu bintang segi lima."""
    titik = []
    for k in range(10):
        sudut = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        titik += [cx + rr * math.cos(sudut), cy + rr * math.sin(sudut)]
    return c.create_polygon(
        titik, fill=WARNA["bintang"] if terisi else WARNA["bintang_kosong"],
        outline=WARNA["bintang_tepi"] if terisi else WARNA["abu"], width=1.5,
        tags=_tags(tag))


def deret_bintang(c, cx, cy, r, jumlah, maks=3, tag=None):
    jarak = r * 2.3
    awal = cx - jarak * (maks - 1) / 2
    for i in range(maks):
        bintang(c, awal + i * jarak, cy, r, i < jumlah, tag)


# ===========================================================================
# Tombol buatan sendiri
# ===========================================================================
class Tombol:
    """Tombol di canvas: kotak bulat + teks, dengan efek hover dan deteksi klik."""

    _nomor = 0

    def __init__(self, canvas, x1, y1, x2, y2, teks, aksi=None, gaya="utama",
                 ukuran=11, aktif=True, rata="tengah", tebal=True, tag=None):
        self.c = canvas
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.teks, self.aksi = teks, aksi
        # tombol nonaktif berwarna abu-abu, kecuali penanda opsi benar/salah
        self.gaya = gaya if (aktif or gaya.startswith("opsi_")) else "nonaktif"
        self.ukuran, self.aktif, self.rata, self.tebal = ukuran, aktif, rata, tebal
        Tombol._nomor += 1
        self.tags = (f"tombol{Tombol._nomor}",) + _tags(tag)
        self.hover = False
        self.id_kotak = None

    def gambar(self):
        isi, _, tepi, warna_teks = GAYA_TOMBOL[self.gaya]
        self.id_kotak = kotak_bulat(self.c, self.x1, self.y1, self.x2, self.y2, 10,
                                    fill=isi, outline=tepi, width=1.5, tags=self.tags)
        lebar = self.x2 - self.x1 - 20
        if len(self.teks) <= 3:
            lebar = None  # tombol keypad: tidak perlu dibungkus
        tengah_y = (self.y1 + self.y2) / 2
        if self.rata == "kiri":
            tulis(self.c, self.x1 + 14, tengah_y, self.teks, self.ukuran, self.tebal,
                  warna_teks, self.x2 - self.x1 - 28, anchor="w", tag=self.tags)
        else:
            tulis(self.c, (self.x1 + self.x2) / 2, tengah_y, self.teks, self.ukuran,
                  self.tebal, warna_teks, lebar, anchor="center", rata="center",
                  tag=self.tags)
        return self

    def berisi(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def atur_hover(self, nilai):
        if nilai == self.hover or self.id_kotak is None:
            return
        self.hover = nilai
        isi, isi_hover, _, _ = GAYA_TOMBOL[self.gaya]
        self.c.itemconfig(self.id_kotak, fill=isi_hover if nilai else isi)

    def tekan(self):
        if self.aktif and self.aksi:
            self.aksi()


# ===========================================================================
# Bidang Kartesius
# ===========================================================================
class Grafik:
    """Bidang Kartesius di dalam kotak (x1, y1, x2, y2) pada canvas."""

    PAD_KIRI, PAD_KANAN, PAD_ATAS, PAD_BAWAH = 36, 30, 30, 28

    def __init__(self, canvas, x1, y1, x2, y2, rentang, langkah_grid=1,
                 tag="grafik", ukuran_angka=9):
        self.c = canvas
        self.kotak = (x1, y1, x2, y2)
        self.xmin, self.xmax, self.ymin, self.ymax = rentang
        self.g = Fraction(langkah_grid)
        self.tag = tag
        self.ukuran_angka = ukuran_angka

        lebar = x2 - x1 - self.PAD_KIRI - self.PAD_KANAN
        tinggi = y2 - y1 - self.PAD_ATAS - self.PAD_BAWAH
        self.skala = min(lebar / (self.xmax - self.xmin), tinggi / (self.ymax - self.ymin))
        w = self.skala * (self.xmax - self.xmin)
        h = self.skala * (self.ymax - self.ymin)
        self.px_kiri = x1 + self.PAD_KIRI + (lebar - w) / 2
        self.px_kanan = self.px_kiri + w
        self.py_atas = y1 + self.PAD_ATAS + (tinggi - h) / 2
        self.py_bawah = self.py_atas + h

        self.kx_min = math.ceil(self.xmin / self.g)
        self.kx_maks = math.floor(self.xmax / self.g)
        self.ky_min = math.ceil(self.ymin / self.g)
        self.ky_maks = math.floor(self.ymax / self.g)
        # letak sumbu: di 0 bila 0 ada dalam rentang, selain itu di tepi
        self.sumbu_x = 0 if self.xmin <= 0 <= self.xmax else self.xmin
        self.sumbu_y = 0 if self.ymin <= 0 <= self.ymax else self.ymin

    # ---- konversi koordinat ------------------------------------------------
    def ke_px(self, x, y):
        return (self.px_kiri + float(x - self.xmin) * self.skala,
                self.py_bawah - float(y - self.ymin) * self.skala)

    def dari_px(self, px, py):
        """Klik (px, py) -> titik grid terdekat (Fraction), atau None di luar grafik."""
        toleransi = self.skala * float(self.g) / 2
        if not (self.px_kiri - toleransi <= px <= self.px_kanan + toleransi
                and self.py_atas - toleransi <= py <= self.py_bawah + toleransi):
            return None
        x = self.xmin + (px - self.px_kiri) / self.skala
        y = self.ymin + (self.py_bawah - py) / self.skala
        kx = min(max(round(x / float(self.g)), self.kx_min), self.kx_maks)
        ky = min(max(round(y / float(self.g)), self.ky_min), self.ky_maks)
        return (kx * self.g, ky * self.g)

    # ---- gambar ------------------------------------------------------------
    def gambar(self):
        c, t = self.c, (self.tag,)
        x1, y1, x2, y2 = self.kotak
        kotak_bulat(c, x1, y1, x2, y2, 14, fill=WARNA["putih"], outline=WARNA["tepi"],
                    width=1.5, tags=t)
        for k in range(self.kx_min, self.kx_maks + 1):
            px, _ = self.ke_px(k * self.g, 0)
            c.create_line(px, self.py_atas, px, self.py_bawah, fill=WARNA["grid"], tags=t)
        for k in range(self.ky_min, self.ky_maks + 1):
            _, py = self.ke_px(0, k * self.g)
            c.create_line(self.px_kiri, py, self.px_kanan, py, fill=WARNA["grid"], tags=t)

        px0, py0 = self.ke_px(self.sumbu_x, self.sumbu_y)
        c.create_line(self.px_kiri, py0, self.px_kanan + 14, py0, fill=WARNA["sumbu"],
                      width=2, arrow="last", arrowshape=(9, 11, 4), tags=t)
        c.create_line(px0, self.py_bawah, px0, self.py_atas - 14, fill=WARNA["sumbu"],
                      width=2, arrow="last", arrowshape=(9, 11, 4), tags=t)
        tulis(c, self.px_kanan + 18, py0, "x", 11, True, WARNA["sumbu"], anchor="w", tag=t)
        tulis(c, px0, self.py_atas - 16, "y", 11, True, WARNA["sumbu"], anchor="s", tag=t)

        loncat = max(1, math.ceil(20 / (self.skala * float(self.g))))
        ada_asal = self.sumbu_x == 0 and self.sumbu_y == 0
        for k in range(self.kx_min, self.kx_maks + 1):
            nilai = k * self.g
            if k % loncat or (nilai == 0 and ada_asal):
                continue
            px, _ = self.ke_px(nilai, 0)
            tulis(c, px, py0 + 4, format_angka(nilai), self.ukuran_angka, False,
                  WARNA["lembut"], anchor="n", tag=t)
        for k in range(self.ky_min, self.ky_maks + 1):
            nilai = k * self.g
            if k % loncat or (nilai == 0 and ada_asal):
                continue
            _, py = self.ke_px(0, nilai)
            tulis(c, px0 - 5, py, format_angka(nilai), self.ukuran_angka, False,
                  WARNA["lembut"], anchor="e", tag=t)
        if ada_asal:
            tulis(c, px0 - 5, py0 + 4, "O", self.ukuran_angka, True, WARNA["lembut"],
                  anchor="ne", tag=t)

    def gambar_garis(self, p, warna, tebal=3, putus=False):
        ujung = potong_garis_dengan_kotak(p, self.xmin, self.xmax, self.ymin, self.ymax)
        if ujung is None:
            return
        (xa, ya), (xb, yb) = ujung
        self.c.create_line(*self.ke_px(xa, ya), *self.ke_px(xb, yb), fill=warna,
                           width=tebal, capstyle="round", dash=(8, 5) if putus else None,
                           tags=(self.tag,))

    def _label(self, px, py, teks, warna, r, latar=None, warna_teks=None,
               tags=None, ukuran=9, tebal=True):
        kanan = px < self.px_kanan - 70
        atas = py > self.py_atas + 26
        lx = px + r + 3 if kanan else px - r - 3
        ly = py - r - 1 if atas else py + r + 1
        anchor = ("s" if atas else "n") + ("w" if kanan else "e")
        tags = tags or (self.tag,)
        item = self.c.create_text(lx, ly, text=teks, anchor=anchor,
                                  font=huruf(ukuran, tebal),
                                  fill=warna_teks or warna, tags=tags)
        kb = self.c.bbox(item)
        if kb:
            latar_id = kotak_bulat(self.c, kb[0] - 4, kb[1] - 1, kb[2] + 4, kb[3] + 1, 5,
                                   fill=latar or WARNA["putih"], outline="", tags=tags)
            self.c.tag_lower(latar_id, item)

    def titik(self, x, y, warna, label=None, kosong=False, r=6):
        px, py = self.ke_px(x, y)
        self.c.create_oval(px - r, py - r, px + r, py + r,
                           fill=WARNA["putih"] if kosong else warna, outline=warna,
                           width=2.5 if kosong else 1.5, tags=(self.tag,))
        if label:
            self._label(px, py, label, warna, r)

    def lingkaran_bantu(self, x, y, warna, r=14):
        """Lingkaran putus-putus sebagai tanda titik bantu (petunjuk)."""
        px, py = self.ke_px(x, y)
        self.c.create_oval(px - r, py - r, px + r, py + r, outline=warna, width=2,
                           dash=(4, 3), tags=(self.tag,))

    def silang(self, x, y, warna=None, r=7):
        px, py = self.ke_px(x, y)
        warna = warna or WARNA["potong"]
        for dx in (-r, r):
            self.c.create_line(px - dx, py - r, px + dx, py + r, fill=warna, width=3,
                               tags=(self.tag,))

    def proyeksi(self, x, y, warna):
        """Garis putus-putus dari titik ke sumbu x dan sumbu y."""
        px, py = self.ke_px(x, y)
        px0, py0 = self.ke_px(self.sumbu_x, self.sumbu_y)
        for koordinat in ((px, py, px, py0), (px, py, px0, py)):
            self.c.create_line(*koordinat, fill=warna, width=1.5, dash=(4, 3),
                               tags=(self.tag,))

    def tampilkan_hover(self, x, y):
        """Penanda koordinat di bawah kursor (tag "hover" agar mudah dihapus)."""
        px, py = self.ke_px(x, y)
        self.c.create_oval(px - 9, py - 9, px + 9, py + 9, outline=WARNA["utama"],
                           width=2, dash=(3, 2), tags=("hover",))
        self._label(px, py, format_titik(x, y), WARNA["utama"], 10,
                    latar=WARNA["utama"], warna_teks=WARNA["putih"],
                    tags=("hover",), ukuran=10)

    def hapus_hover(self):
        self.c.delete("hover")


def legenda(c, x, y, butir, ukuran=10):
    """butir: list (teks, warna). Digambar mendatar mulai dari (x, y)."""
    for teks, warna in butir:
        c.create_line(x, y, x + 22, y, fill=warna, width=3)
        item = tulis(c, x + 28, y, teks, ukuran, True, warna, anchor="w")
        x = c.bbox(item)[2] + 24


# ===========================================================================
# Layar dasar
# ===========================================================================
class Layar:
    def __init__(self, app):
        self.app = app
        self.c = app.canvas
        self.tombol = []
        self._hover = None

    def gambar(self):
        self.c.delete("all")
        self.tombol = []
        self._hover = None
        self.c.config(cursor="")
        self.c.create_rectangle(0, 0, self.app.lebar, self.app.tinggi,
                                fill=WARNA["latar"], outline="")
        self.gambar_isi()

    def gambar_isi(self):
        pass

    def tambah_tombol(self, x1, y1, x2, y2, teks, aksi, gaya="utama", ukuran=11,
                      aktif=True, **opsi):
        t = Tombol(self.c, x1, y1, x2, y2, teks, aksi, gaya, ukuran, aktif, **opsi)
        self.tombol.append(t.gambar())
        return t

    def klik(self, x, y):
        """Mengembalikan True jika klik mengenai tombol."""
        for t in reversed(self.tombol):
            if t.berisi(x, y):
                t.tekan()
                return True
        return False

    def gerak(self, x, y):
        baru = None
        for t in reversed(self.tombol):
            if t.aktif and t.berisi(x, y):
                baru = t
                break
        if baru is not self._hover:
            if self._hover:
                self._hover.atur_hover(False)
            if baru:
                baru.atur_hover(True)
            self._hover = baru
            self.c.config(cursor="hand2" if baru else "")

    def ketik(self, keysym, char):
        pass

    def bilah_atas(self, judul, sub=None, kembali=None, teks_kembali="◀ Menu"):
        c = self.c
        c.create_rectangle(0, 0, self.app.lebar, 70, fill=WARNA["putih"], outline="")
        c.create_line(0, 70, self.app.lebar, 70, fill=WARNA["tepi"])
        x = 20
        if kembali:
            self.tambah_tombol(20, 18, 150, 52, teks_kembali, kembali, "sekunder", 10)
            x = 170
        tulis(c, x, 10 if sub else 22, judul, 16, True, WARNA["utama"], lebar=700)
        if sub:
            tulis(c, x, 42, sub, 9, False, WARNA["lembut"], lebar=700)


# ===========================================================================
# 1. Menu
# ===========================================================================
MATERI_P1 = Persamaan(1, 1, 4)    # x + y = 4
MATERI_P2 = Persamaan(1, -1, 2)   # x − y = 2


class LayarMenu(Layar):
    def __init__(self, app, pesan=""):
        super().__init__(app)
        self.pesan = pesan

    def gambar_isi(self):
        c = self.c
        kotak_bulat(c, 50, 60, 610, 640, 24, fill=WARNA["putih"], outline=WARNA["tepi"],
                    width=1.5)
        x, lebar = 90, 480
        i = tulis(c, x, 96, "MEDIA PEMBELAJARAN MATEMATIKA · SMP KELAS VIII", 9, True,
                  WARNA["utama"], lebar)
        i = tulis(c, x, bawah(c, i) + 8, "Petualangan Grafik SPLDV", 27, True,
                  WARNA["teks"], lebar)
        i = tulis(c, x, bawah(c, i) + 8,
                  "Belajar menyelesaikan Sistem Persamaan Linear Dua Variabel dengan "
                  "metode grafik melalui 5 level tantangan.", 11, False, WARNA["lembut"],
                  lebar)
        y = bawah(c, i) + 26

        tulis(c, x, y, "Nama / NIM", 10, True, WARNA["teks"])
        y += 22
        kotak_bulat(c, x, y, x + lebar, y + 46, 10, fill="#F7FAFC",
                    outline=WARNA["utama"], width=2)
        if self.app.nama:
            tulis(c, x + 14, y + 23, self.app.nama + "|", 13, False, WARNA["teks"],
                  anchor="w")
        else:
            tulis(c, x + 14, y + 23, "Ketik namamu di sini...", 12, False, WARNA["abu"],
                  anchor="w")
        y += 52
        if self.pesan:
            tulis(c, x, y, self.pesan, 10, True, WARNA["salah"], lebar)
        y += 30

        self.tambah_tombol(x, y, x + lebar, y + 52, "▶  Mulai Bermain", self.mulai,
                           "utama", 14)
        y += 64
        w = (lebar - 20) / 3
        self.tambah_tombol(x, y, x + w, y + 44, "Materi Singkat", self.materi,
                           "sekunder", 10)
        self.tambah_tombol(x + w + 10, y, x + 2 * w + 10, y + 44, "Lihat Hasil Belajar",
                           self.hasil, "sekunder", 10)
        self.tambah_tombol(x + 2 * w + 20, y, x + lebar, y + 44, "Keluar",
                           self.app.keluar, "sekunder", 10)

        # hiasan: grafik kecil dua garis berpotongan
        g = Grafik(c, 650, 100, 1060, 520, (-1, 5, -3, 5), 1, ukuran_angka=8)
        g.gambar()
        g.gambar_garis(MATERI_P1, WARNA["garis1"])
        g.gambar_garis(MATERI_P2, WARNA["garis2"])
        g.proyeksi(3, 1, WARNA["potong"])
        g.titik(3, 1, WARNA["potong"], "(3, 1)", r=7)
        legenda(c, 690, 548, [(MATERI_P1.teks(), WARNA["garis1"]),
                              (MATERI_P2.teks(), WARNA["garis2"])], 11)
        tulis(c, 855, 590, "Titik potong kedua garis = penyelesaian SPLDV", 11, True,
              WARNA["lembut"], anchor="n")

    def ketik(self, keysym, char):
        if keysym in ("Return", "KP_Enter"):
            self.mulai()
            return
        if keysym == "BackSpace":
            self.app.nama = self.app.nama[:-1]
        elif char and char.isprintable() and len(self.app.nama) < 40:
            self.app.nama += char
        else:
            return
        self.pesan = ""
        self.gambar()

    def _wajib_nama(self):
        if not self.app.nama.strip():
            self.pesan = "Isi Nama/NIM terlebih dahulu ya."
            self.gambar()
            return False
        self.app.siapkan_pemain()
        return True

    def mulai(self):
        if self._wajib_nama():
            self.app.ganti_layar(LayarPilihLevel)

    def hasil(self):
        if self._wajib_nama():
            self.app.ganti_layar(LayarHasil)

    def materi(self):
        self.app.ganti_layar(LayarMateri)


# ===========================================================================
# 2. Materi singkat
# ===========================================================================
def _halaman_materi():
    p1, p2 = MATERI_P1, MATERI_P2
    return [
        {
            "judul": "Apa itu SPLDV?",
            "blok": [
                ("teks", "Sistem Persamaan Linear Dua Variabel (SPLDV) adalah dua "
                         "persamaan linear yang memiliki dua variabel yang sama, "
                         "misalnya x dan y."),
                ("contoh", f"Contoh:\n{p1.teks()}\n{p2.teks()}"),
                ("teks", "Grafik persamaan linear dua variabel berbentuk GARIS LURUS. "
                         "Semua titik yang terletak pada garis itu memenuhi "
                         "persamaannya."),
                ("contoh", f"Titik-titik pada garis {p1.teks()}:\n"
                           + "\n".join(f"{format_titik(t)}  →  {p1.cek_teks(*t)}"
                                       for t in [(0, 4), (1, 3), (2, 2), (4, 0)])),
            ],
            "garis": [0],
            "titik": [((0, 4), 0, False), ((1, 3), 0, False), ((2, 2), 0, False),
                      ((4, 0), 0, False)],
            "potong": False,
        },
        {
            "judul": "Langkah 1: Menentukan Titik Koordinat",
            "blok": [
                ("teks", "Untuk menggambar sebuah garis, cukup cari DUA titik. Cara "
                         "termudah: substitusi x = 0, lalu substitusi y = 0."),
                ("contoh", f"{p1.teks()}\n"
                           f"x = 0  →  {p1.substitusi_teks('x', 0)}  →  y = 4"
                           f"  →  titik (0, 4)\n"
                           f"y = 0  →  {p1.substitusi_teks('y', 0)}  →  x = 4"
                           f"  →  titik (4, 0)"),
                ("contoh", f"{p2.teks()}\n"
                           f"x = 0  →  {p2.substitusi_teks('x', 0)}  →  "
                           f"{MINUS}y = 2  →  y = {MINUS}2  →  titik (0, {MINUS}2)\n"
                           f"y = 0  →  {p2.substitusi_teks('y', 0)}  →  x = 2"
                           f"  →  titik (2, 0)"),
                ("teks", "Titik-titik itu adalah titik potong garis dengan sumbu y "
                         "(saat x = 0) dan dengan sumbu x (saat y = 0)."),
            ],
            "garis": [],
            "titik": [((0, 4), 0, True), ((4, 0), 0, True), ((0, -2), 1, True),
                      ((2, 0), 1, True)],
            "potong": False,
        },
        {
            "judul": "Langkah 2: Menggambar Garis",
            "blok": [
                ("teks", "Letakkan titik-titik tadi pada bidang Kartesius, lalu "
                         "hubungkan dua titik dari persamaan yang sama dengan garis "
                         "lurus."),
                ("contoh", f"Garis {p1.teks()} melalui (0, 4) dan (4, 0).\n"
                           f"Garis {p2.teks()} melalui (0, {MINUS}2) dan (2, 0)."),
                ("tips", "Jika hasilnya pecahan, misalnya pada 2x + y = 11 dengan "
                         "y = 0 diperoleh x = 5,5, titik (5,5; 0) sulit digambar tepat "
                         "di grid. Pilih nilai x lain agar y bilangan bulat, misalnya "
                         "x = 5 → y = 1, sehingga diperoleh titik (5, 1)."),
            ],
            "garis": [0, 1],
            "titik": [((0, 4), 0, False), ((4, 0), 0, False), ((0, -2), 1, False),
                      ((2, 0), 1, False)],
            "potong": False,
        },
        {
            "judul": "Langkah 3: Menentukan Titik Potong",
            "blok": [
                ("teks", "Titik tempat kedua garis berpotongan adalah PENYELESAIAN "
                         "SPLDV, karena titik itu terletak pada KEDUA garis sehingga "
                         "memenuhi KEDUA persamaan."),
                ("contoh", "Titik potong: (3, 1)\n"
                           f"{p1.teks()}  →  {p1.cek_teks(3, 1)}\n"
                           f"{p2.teks()}  →  {p2.cek_teks(3, 1)}\n"
                           "Jadi HP = {(3, 1)}, artinya x = 3 dan y = 1."),
                ("tips", "Jika kedua garis sejajar, SPLDV tidak memiliki penyelesaian. "
                         "Jika kedua garis berimpit, penyelesaiannya tak hingga banyak."),
            ],
            "garis": [0, 1],
            "titik": [],
            "potong": True,
        },
    ]


class LayarMateri(Layar):
    def __init__(self, app, halaman=0):
        super().__init__(app)
        self.daftar = _halaman_materi()
        self.halaman = halaman

    def gambar_isi(self):
        c = self.c
        data = self.daftar[self.halaman]
        self.bilah_atas("Materi Singkat: SPLDV Metode Grafik",
                        f"Halaman {self.halaman + 1} dari {len(self.daftar)}",
                        kembali=lambda: self.app.ganti_layar(LayarMenu))

        x1, x2 = 40, 540
        i = tulis(c, x1, 90, data["judul"], 18, True, WARNA["teks"], x2 - x1)
        y = bawah(c, i) + 14
        for jenis, teks in data["blok"]:
            if jenis == "teks":
                i = tulis(c, x1, y, teks, 11, False, WARNA["teks"], x2 - x1)
                y = bawah(c, i) + 12
            elif jenis == "contoh":
                y = kotak_teks(c, x1, y, x2, teks, 11, isi=WARNA["utama_muda"],
                               tepi=WARNA["utama_tepi"]) + 12
            else:
                y = kotak_teks(c, x1, y, x2, teks, 11, judul="TIPS",
                               isi=WARNA["kuning_muda"], tepi=WARNA["kuning"],
                               warna_judul=WARNA["kuning_tua"]) + 12

        # grafik contoh
        dipakai = sorted(set(data["garis"]) | {gi for _, gi, _ in data["titik"]}
                         | ({0, 1} if data["potong"] else set()))
        persamaan = (MATERI_P1, MATERI_P2)
        legenda(c, 590, 92, [(persamaan[gi].teks(), WARNA_GARIS[gi]) for gi in dipakai])
        g = Grafik(c, 580, 110, 1070, 620, (-2, 6, -3, 6), 1)
        g.gambar()
        for gi in data["garis"]:
            g.gambar_garis(persamaan[gi], WARNA_GARIS[gi])
        for t, gi, kosong in data["titik"]:
            g.titik(*t, WARNA_GARIS[gi], format_titik(t), kosong=kosong)
        if data["potong"]:
            g.proyeksi(3, 1, WARNA["potong"])
            g.titik(3, 1, WARNA["potong"], "(3, 1) = penyelesaian", r=7)

        # navigasi
        awal, akhir = self.halaman == 0, self.halaman == len(self.daftar) - 1
        self.tambah_tombol(40, 636, 210, 676, "◀ Sebelumnya", self.sebelumnya,
                           "sekunder", 11, aktif=not awal)
        for k in range(len(self.daftar)):
            cx = 262 + k * 22
            warna = WARNA["utama"] if k == self.halaman else WARNA["tepi"]
            c.create_oval(cx - 6, 650, cx + 6, 662, fill=warna, outline="")
        self.tambah_tombol(370, 636, 540, 676, "Berikutnya ▶", self.berikutnya,
                           "sekunder", 11, aktif=not akhir)
        self.tambah_tombol(860, 636, 1070, 676, "▶  Mulai Bermain", self.mulai_bermain,
                           "utama", 12)

    def sebelumnya(self):
        if self.halaman > 0:
            self.halaman -= 1
            self.gambar()

    def berikutnya(self):
        if self.halaman < len(self.daftar) - 1:
            self.halaman += 1
            self.gambar()

    def mulai_bermain(self):
        if self.app.nama.strip():
            self.app.siapkan_pemain()
            self.app.ganti_layar(LayarPilihLevel)
        else:
            self.app.ganti_layar(LayarMenu, pesan="Isi Nama/NIM terlebih dahulu, lalu "
                                                  "tekan Mulai Bermain.")

    def ketik(self, keysym, char):
        if keysym == "Left":
            self.sebelumnya()
        elif keysym in ("Right", "Return", "KP_Enter"):
            self.berikutnya()


# ===========================================================================
# 3. Pilih level
# ===========================================================================
class LayarPilihLevel(Layar):
    def gambar_isi(self):
        c = self.c
        self.tambah_tombol(20, 20, 140, 56, "◀ Menu",
                           lambda: self.app.ganti_layar(LayarMenu), "sekunder", 10)
        self.tambah_tombol(920, 20, 1080, 56, "Hasil Belajar",
                           lambda: self.app.ganti_layar(LayarHasil), "sekunder", 10)
        tulis(c, 550, 16, "Pilih Level", 24, True, WARNA["utama"], anchor="n")
        tulis(c, 550, 64, f"Halo, {self.app.nama.strip()}! Kerjakan level secara "
                          "berurutan, dari langkah prosedural sampai soal cerita.",
              11, False, WARNA["lembut"], 700, anchor="n", rata="center")
        # lebar kartu menyesuaikan banyak level (dirancang untuk 5 kartu)
        jarak, x = 15, 20
        banyak = len(self.app.info_level)
        lebar = (self.app.lebar - 40 - jarak * (banyak - 1)) / banyak
        for lv in self.app.info_level:
            self._kartu(x, 110, x + lebar, 610, lv)
            x += lebar + jarak
        total, total_maks = self.app.total_skor()
        tulis(c, 550, 640, f"Total skor: {total} dari {total_maks}", 13, True,
              WARNA["teks"], anchor="n")

    def _kartu(self, x1, y1, x2, y2, lv):
        c = self.c
        terbaik = self.app.hasil_terbaik.get(lv.nomor)
        tepi = WARNA["benar"] if terbaik and terbaik["bintang"] == 3 else WARNA["tepi"]
        kotak_bulat(c, x1, y1, x2, y2, 18, fill=WARNA["putih"], outline=tepi, width=2)
        cx, lebar = (x1 + x2) / 2, x2 - x1 - 24
        c.create_oval(cx - 26, y1 + 20, cx + 26, y1 + 72, fill=WARNA["utama"], outline="")
        tulis(c, cx, y1 + 46, str(lv.nomor), 20, True, WARNA["putih"], anchor="center")
        i = tulis(c, cx, y1 + 86, lv.judul, 12, True, WARNA["teks"], lebar,
                  anchor="n", rata="center")
        proses, _, uraian = lv.indikator.partition(":")
        i = tulis(c, cx, bawah(c, i) + 10, proses.strip(), 9, True, WARNA["utama"], lebar,
                  anchor="n", rata="center")
        tulis(c, cx, bawah(c, i) + 4, uraian.strip(), 9, False, WARNA["lembut"], lebar,
              anchor="n", rata="center")

        deret_bintang(c, cx, y2 - 150, 16, terbaik["bintang"] if terbaik else 0)
        maks = POIN_LANGSUNG * len(lv.langkah)
        teks = (f"Skor terbaik: {terbaik['skor']} / {maks}" if terbaik
                else "Belum dimainkan")
        tulis(c, cx, y2 - 124, teks, 10, True,
              WARNA["teks"] if terbaik else WARNA["abu"], anchor="n")
        tulis(c, cx, y2 - 102, f"{len(lv.langkah)} langkah", 9, False, WARNA["lembut"],
              anchor="n")
        self.tambah_tombol(x1 + 16, y2 - 64, x2 - 16, y2 - 20,
                           "Main Lagi ▶" if terbaik else "Mainkan ▶",
                           lambda n=lv.nomor: self.app.ganti_layar(LayarLevel, nomor=n),
                           "utama", 11)


# ===========================================================================
# 4. Bermain satu level
# ===========================================================================
GAYA_UMPAN = {
    # jenis: (judul, isi, tepi, warna judul)
    "benar": ("BENAR ✔", WARNA["benar_muda"], WARNA["benar"], WARNA["benar"]),
    "salah": ("BELUM TEPAT", WARNA["salah_muda"], WARNA["salah"], WARNA["salah"]),
    "info": ("INFO", "#EDF2F7", WARNA["abu"], WARNA["lembut"]),
    "pembahasan": ("PEMBAHASAN", WARNA["utama_muda"], WARNA["utama"], WARNA["utama"]),
}


class LayarLevel(Layar):
    X1, X2 = 20, 540            # kolom kiri
    Y_ATAS = 82
    BATAS_BAWAH = 626           # batas isi kolom kiri (di atas tombol bawah)
    Y_TOMBOL = 634

    def __init__(self, app, nomor):
        super().__init__(app)
        self.level = data_soal.ambil_level(nomor)
        self.status = StatusLevel(self.level)
        self.grafik = Grafik(self.c, 560, 112, 1080, 684, self.level.rentang,
                             self.level.langkah_grid)
        self.input = ""
        self.umpan = None           # (jenis, teks)
        self.titik_salah = None
        self.opsi_salah = set()
        self.konfirmasi = False     # konfirmasi "Lihat Pembahasan"
        self.selesai = False
        self.pesan_simpan = None
        self.hover = None

    # ---- gambar ------------------------------------------------------------
    def gambar_isi(self):
        self.hover = None
        lv, s = self.level, self.status
        self.bilah_atas(f"Level {lv.nomor}: {lv.judul}", lv.indikator,
                        kembali=lambda: self.app.ganti_layar(LayarPilihLevel),
                        teks_kembali="◀ Pilih Level")
        tulis(self.c, 1080, 12, "SKOR", 9, True, WARNA["lembut"], anchor="ne")
        tulis(self.c, 1080, 28, f"{s.skor} / {s.skor_maks}", 16, True, WARNA["teks"],
              anchor="ne")
        self._gambar_grafik()
        if self.selesai:
            self._gambar_panel_selesai()
        else:
            self._gambar_kiri_adaptif()
            self._gambar_tombol_bawah()

    def _gambar_grafik(self):
        c, g, s, lv = self.c, self.grafik, self.status, self.level
        legenda(c, 566, 96, [(f"Garis {i + 1}: {p.teks()}", WARNA_GARIS[i])
                             for i, p in enumerate(lv.persamaan)])
        g.gambar()
        for gi in sorted(s.garis_tergambar):
            g.gambar_garis(lv.persamaan[gi], WARNA_GARIS[gi])

        berlabel = set()
        for t, gi in s.titik_ditemukan:
            warna = WARNA_GARIS[gi] if gi is not None else WARNA["utama"]
            g.titik(*t, warna, format_titik(t), kosong=True)
            berlabel.add(t)
        for gi, pasangan in s.garis_tergambar.items():
            for t in pasangan:
                g.titik(*t, WARNA_GARIS[gi], None if t in berlabel else format_titik(t), r=5)
                berlabel.add(t)

        lk = s.langkah_aktif
        if lk is not None and lk.jenis == "plot" and not s.langkah_selesai:
            warna = WARNA_GARIS[lk.garis]
            if s.catatan_aktif.petunjuk_dipakai >= 2:
                for t in lk.titik:
                    g.lingkaran_bantu(*t, warna)
            for t in s.titik_terpilih:
                g.titik(*t, warna, None if t in berlabel else format_titik(t), r=6)
        if self.titik_salah is not None:
            g.silang(*self.titik_salah)
        if s.titik_potong_ditemukan is not None:
            tp = s.titik_potong_ditemukan
            g.proyeksi(*tp, WARNA["potong"])
            g.titik(*tp, WARNA["potong"], format_titik(tp), r=7)

    def _gambar_kiri_adaptif(self):
        """Menggambar kolom kiri; huruf diperkecil bila isinya terlalu panjang."""
        awal = len(self.tombol)
        for ukuran in (11, 10, 9):
            del self.tombol[awal:]
            self.c.delete("kiri")
            if self._gambar_kiri(ukuran) <= self.BATAS_BAWAH:
                break

    def _gambar_kiri(self, u):
        c, s, lv, T = self.c, self.status, self.level, "kiri"
        X1, X2 = self.X1, self.X2
        lk, cat = s.langkah_aktif, s.catatan_aktif

        y = kotak_teks(c, X1, self.Y_ATAS, X2, lv.cerita, u - 1, judul="SOAL",
                       tepi="#BFD3EE", tag=T) + 10

        # kemajuan langkah
        tulis(c, X1, y + 8, f"Langkah {s.nomor_langkah} dari {s.jumlah_langkah}", 9, True,
              WARNA["lembut"], anchor="w", tag=T)
        for i, catatan in enumerate(s.catatan):
            cx = X1 + 132 + i * 22
            if catatan.selesai:
                warna = {POIN_LANGSUNG: WARNA["benar"],
                         POIN_DIBANTU: WARNA["kuning"]}.get(catatan.poin, "#FC8181")
                c.create_oval(cx - 7, y + 1, cx + 7, y + 15, fill=warna, outline="", tags=T)
            elif i == s.indeks:
                c.create_oval(cx - 8, y, cx + 8, y + 16, fill=WARNA["utama"],
                              outline=WARNA["utama_tepi"], width=3, tags=T)
            else:
                c.create_oval(cx - 7, y + 1, cx + 7, y + 15, fill=WARNA["tepi"],
                              outline="", tags=T)
        y += 26

        y = kotak_teks(c, X1, y, X2, lk.pertanyaan, u,
                       judul=f"LANGKAH {s.nomor_langkah} · {lk.tahap.upper()}",
                       isi=WARNA["utama_muda"], tepi=WARNA["utama_tepi"], tebal=True,
                       tag=T) + 10

        if lk.jenis == "pilihan" or not s.langkah_selesai:
            y = self._gambar_area_jawaban(lk, y, u) + 10

        if self.umpan:
            jenis, teks = self.umpan
            judul, isi, tepi, warna_judul = GAYA_UMPAN[jenis]
            y = kotak_teks(c, X1, y, X2, teks, u - 1, judul=judul, isi=isi, tepi=tepi,
                           warna_judul=warna_judul, tag=T) + 8

        terlihat = s.petunjuk_terlihat
        if terlihat:
            teks = "\n".join(f"{i}. {p}" for i, p in enumerate(terlihat, start=1))
            y = kotak_teks(c, X1, y, X2, teks, u - 1, judul="PETUNJUK",
                           isi=WARNA["kuning_muda"], tepi=WARNA["kuning"],
                           warna_judul=WARNA["kuning_tua"], tag=T)
        return y

    def _gambar_area_jawaban(self, lk, y, u):
        c, s, X1, X2, T = self.c, self.status, self.X1, self.X2, "kiri"
        if lk.jenis == "isian":
            kotak_bulat(c, X1, y, X1 + 300, y + 44, 10, fill=WARNA["putih"],
                        outline=WARNA["utama"], width=2, tags=T)
            if self.input:
                tulis(c, X1 + 14, y + 22, self.input + "|", u + 4, True, WARNA["teks"],
                      anchor="w", tag=T)
            else:
                tulis(c, X1 + 14, y + 22, "Ketik jawaban...", u, False, WARNA["abu"],
                      anchor="w", tag=T)
            self.tambah_tombol(X1 + 310, y, X2, y + 44, "Cek Jawaban ✔",
                               self.cek_isian, "hijau", u, tag=T)
            y += 52
            lebar = (X2 - X1 - 4 * (len(KEYPAD) - 1)) / len(KEYPAD)
            for i, k in enumerate(KEYPAD):
                x = X1 + i * (lebar + 4)
                self.tambah_tombol(x, y, x + lebar, y + 36, k,
                                   lambda k=k: self.tekan_keypad(k), "pilihan", u + 1,
                                   tag=T)
            return y + 36

        if lk.jenis == "pilihan":
            for i, opsi in enumerate(lk.opsi):
                teks = f"{'ABCD'[i]}.  {opsi}"
                baris = bungkus(teks, X2 - X1 - 28, u - 1).count("\n") + 1
                tinggi = max(38, 14 + baris * int((u - 1) * 1.8))
                if s.langkah_selesai:
                    gaya, aktif = ("opsi_benar" if i == lk.benar else "pilihan"), False
                else:
                    gaya, aktif = ("opsi_salah" if i in self.opsi_salah else "pilihan"), True
                self.tambah_tombol(X1, y, X2, y + tinggi, teks,
                                   lambda i=i: self.pilih(i), gaya, u - 1, aktif,
                                   rata="kiri", tebal=False, tag=T)
                y += tinggi + 6
            return y - 6

        # plot / potong
        if lk.jenis == "plot":
            p = self.level.persamaan[lk.garis]
            teks = (f"▶ Klik 2 titik pada grafik di sebelah kanan yang terletak pada "
                    f"garis {p.teks()}.")
            if s.titik_terpilih:
                info = ("Titik terpilih: " + ", ".join(format_titik(t) for t in s.titik_terpilih)
                        + f"  ({len(s.titik_terpilih)}/2)")
            else:
                info = "Belum ada titik yang dipilih (0/2)."
            teks += "\n" + info
        else:
            teks = "▶ Klik titik potong kedua garis pada grafik di sebelah kanan."
        i = tulis(c, X1 + 4, y, teks, u, False, WARNA["lembut"], X2 - X1 - 8, tag=T)
        return bawah(c, i, y)

    def _gambar_tombol_bawah(self):
        s, X1, X2, y = self.status, self.X1, self.X2, self.Y_TOMBOL
        if s.langkah_selesai:
            terakhir = s.indeks == s.jumlah_langkah - 1
            self.tambah_tombol(X1, y, X2, y + 42,
                               "Selesaikan Level ▶" if terakhir else "Lanjut ▶",
                               self.lanjut, "hijau", 12)
            return
        lk, cat = s.langkah_aktif, s.catatan_aktif
        sisa = len(lk.petunjuk) - cat.petunjuk_dipakai
        self.tambah_tombol(X1, y, X1 + 250, y + 42,
                           f"Petunjuk ({sisa} lagi)" if sisa else "Petunjuk habis",
                           self.petunjuk, "kuning", 11, aktif=sisa > 0)
        if self.konfirmasi:
            self.tambah_tombol(X1 + 260, y, X2, y + 42, "Yakin? Poin langkah ini jadi 0",
                               self.pembahasan, "bahaya", 10)
        else:
            self.tambah_tombol(X1 + 260, y, X2, y + 42, "Lihat Pembahasan",
                               self.pembahasan, "sekunder", 11)

    def _gambar_panel_selesai(self):
        c, s, lv = self.c, self.status, self.level
        X1, X2 = self.X1, self.X2
        cx, lebar = (X1 + X2) / 2, X2 - X1 - 48
        kotak_bulat(c, X1, self.Y_ATAS, X2, self.BATAS_BAWAH, 18, fill=WARNA["putih"],
                    outline=WARNA["tepi"], width=1.5)
        tulis(c, cx, 100, "Level Selesai!", 24, True, WARNA["utama"], anchor="n")
        deret_bintang(c, cx, 178, 26, s.bintang)
        tulis(c, cx, 214, f"Skor: {s.skor} / {s.skor_maks}", 16, True, WARNA["teks"],
              anchor="n")

        y = 260
        perlu = s.tahap_perlu_latihan
        if perlu:
            i = tulis(c, X1 + 24, y, "Bagian yang perlu dilatih lagi:", 11, True,
                      WARNA["salah"])
            i = tulis(c, X1 + 24, bawah(c, i) + 4, "\n".join(f"• {t}" for t in perlu),
                      11, False, WARNA["teks"], lebar)
        else:
            i = tulis(c, X1 + 24, y, "Hebat! Semua langkah kamu kerjakan tanpa bantuan.",
                      11, True, WARNA["benar"], lebar)
        y = bawah(c, i) + 16

        tp = lv.titik_potong
        kesimpulan = (f"Titik potong {format_titik(tp)} terletak pada kedua garis, sehingga "
                      f"penyelesaiannya x = {format_angka(tp[0])} dan "
                      f"y = {format_angka(tp[1])}. {lv.kesimpulan}").strip()
        y = kotak_teks(c, X1 + 24, y, X2 - 24, kesimpulan, 11, judul="KESIMPULAN",
                       isi=WARNA["utama_muda"], tepi=WARNA["utama_tepi"]) + 12
        if self.pesan_simpan:
            tulis(c, X1 + 24, y, self.pesan_simpan, 9, True, WARNA["salah"], lebar)
        else:
            tulis(c, X1 + 24, y, "Hasil belajar sudah tersimpan.", 9, False,
                  WARNA["lembut"], lebar)

        self.tambah_tombol(X1, self.Y_TOMBOL, X1 + 200, self.Y_TOMBOL + 42,
                           "↻ Ulangi Level",
                           lambda: self.app.ganti_layar(LayarLevel, nomor=lv.nomor),
                           "sekunder", 11)
        teks = ("Level Berikutnya ▶" if lv.nomor < data_soal.jumlah_level()
                else "Lihat Hasil Belajar ▶")
        self.tambah_tombol(X1 + 210, self.Y_TOMBOL, X2, self.Y_TOMBOL + 42, teks,
                           self.level_berikutnya, "utama", 12)

    # ---- aksi --------------------------------------------------------------
    def _bersihkan_konfirmasi(self):
        self.konfirmasi = False

    def tekan_keypad(self, k):
        if k == TOMBOL_HAPUS:
            self.input = self.input[:-1]
        elif k == MINUS:
            self.input = self.input[1:] if self.input.startswith(MINUS) else MINUS + self.input
        elif k == ",":
            if "," not in self.input:
                self.input = (self.input if self.input.strip(MINUS) else self.input + "0") + ","
        elif len(self.input.replace(MINUS, "").replace(",", "")) < 7:
            self.input += k
        self.gambar()

    def cek_isian(self):
        self._bersihkan_konfirmasi()
        if not self.input.strip(MINUS + ","):
            self.umpan = ("info", "Ketik jawabanmu dulu, lalu tekan Cek Jawaban.")
        else:
            u = self.status.jawab_isian(self.input)
            self.umpan = ("benar" if u.benar else "salah", u.pesan)
            if u.benar:
                self.input = ""
        self.gambar()

    def pilih(self, i):
        if i in self.opsi_salah:
            return
        self._bersihkan_konfirmasi()
        u = self.status.jawab_pilihan(i)
        if not u.benar:
            self.opsi_salah.add(i)
        self.umpan = ("benar" if u.benar else "salah", u.pesan)
        self.gambar()

    def klik_grafik(self, titik):
        self._bersihkan_konfirmasi()
        sudah_dipilih = titik in self.status.titik_terpilih
        u = self.status.klik_titik(*titik)
        self.titik_salah = None if (u.benar or sudah_dipilih) else titik
        self.umpan = ("benar" if u.benar else "salah", u.pesan)
        self.gambar()

    def petunjuk(self):
        self._bersihkan_konfirmasi()
        self.status.minta_petunjuk()
        self.gambar()

    def pembahasan(self):
        if not self.konfirmasi:
            self.konfirmasi = True
        else:
            self.konfirmasi = False
            u = self.status.lihat_pembahasan()
            self.umpan = ("pembahasan", u.pesan)
            self.titik_salah = None
        self.gambar()

    def lanjut(self):
        if not self.status.langkah_selesai:
            return
        level_selesai = self.status.lanjut()
        self.input, self.umpan, self.titik_salah = "", None, None
        self.opsi_salah = set()
        self.konfirmasi = False
        if level_selesai:
            self.selesai = True
            self.pesan_simpan = self.app.level_selesai(self.status)
        self.gambar()

    def level_berikutnya(self):
        if self.level.nomor < data_soal.jumlah_level():
            self.app.ganti_layar(LayarLevel, nomor=self.level.nomor + 1)
        else:
            self.app.ganti_layar(LayarHasil)

    # ---- event -------------------------------------------------------------
    def klik(self, x, y):
        if super().klik(x, y):
            return True
        s = self.status
        if self.selesai or s.langkah_selesai:
            return False
        if s.langkah_aktif.jenis in ("plot", "potong"):
            titik = self.grafik.dari_px(x, y)
            if titik is not None:
                self.klik_grafik(titik)
                return True
        return False

    def gerak(self, x, y):
        super().gerak(x, y)
        titik = self.grafik.dari_px(x, y)
        if titik != self.hover:
            self.hover = titik
            self.grafik.hapus_hover()
            if titik is not None:
                self.grafik.tampilkan_hover(*titik)

    def ketik(self, keysym, char):
        enter = keysym in ("Return", "KP_Enter")
        if self.selesai:
            if enter:
                self.level_berikutnya()
            return
        s = self.status
        if s.langkah_selesai:
            if enter or keysym == "space":
                self.lanjut()
            return
        lk = s.langkah_aktif
        if lk.jenis == "isian":
            if char and char.isdigit() and char.isascii():
                self.tekan_keypad(char)
            elif keysym in ("minus", "KP_Subtract") or char == "-":
                self.tekan_keypad(MINUS)
            elif keysym in ("comma", "period", "KP_Decimal") or (char and char in ",."):
                self.tekan_keypad(",")
            elif keysym == "BackSpace":
                self.tekan_keypad(TOMBOL_HAPUS)
            elif enter:
                self.cek_isian()
        elif lk.jenis == "pilihan" and char:
            kunci = char.lower()
            for i, (angka, huruf_opsi) in enumerate(zip("1234", "abcd")):
                if kunci in (angka, huruf_opsi) and i < len(lk.opsi):
                    if not s.langkah_selesai:
                        self.pilih(i)
                    break


# ===========================================================================
# 5. Hasil belajar
# ===========================================================================
class LayarHasil(Layar):
    KOLOM = [("Level", 40, 110), ("Judul", 110, 370), ("Skor", 370, 490),
             ("Bintang", 490, 620), ("Bagian yang perlu dilatih", 620, 1060)]

    def gambar_isi(self):
        c = self.c
        self.bilah_atas(f"Hasil Belajar: {self.app.nama.strip()}",
                        "Skor terbaik setiap level beserta bagian yang perlu dilatih.",
                        kembali=lambda: self.app.ganti_layar(LayarMenu))

        y = 100
        kotak_bulat(c, 40, y, 1060, y + 38, 8, fill=WARNA["utama"], outline="")
        for judul, x1, _ in self.KOLOM:
            tulis(c, x1 + 12, y + 19, judul, 11, True, WARNA["putih"], anchor="w")
        y += 42

        tinggi = min(70, 360 / len(self.app.info_level))  # muat 5 baris atau lebih
        for n, lv in enumerate(self.app.info_level):
            c.create_rectangle(40, y, 1060, y + tinggi,
                               fill=WARNA["putih"] if n % 2 == 0 else "#F7FAFC",
                               outline=WARNA["grid"])
            tengah = y + tinggi / 2
            terbaik = self.app.hasil_terbaik.get(lv.nomor)
            maks = POIN_LANGSUNG * len(lv.langkah)
            tulis(c, 52, tengah, str(lv.nomor), 14, True, WARNA["utama"], anchor="w")
            tulis(c, 122, tengah, lv.judul, 11, True, WARNA["teks"], 240, anchor="w")
            if terbaik:
                tulis(c, 382, tengah, f"{terbaik['skor']} / {maks}", 12, True,
                      WARNA["teks"], anchor="w")
                deret_bintang(c, 555, tengah, 12, terbaik["bintang"])
                perlu = (", ".join(terbaik["tahap"]) if terbaik["tahap"]
                         else "Tidak ada (semua langkah dikerjakan tanpa bantuan)")
                tulis(c, 632, tengah, perlu, 10, False,
                      WARNA["teks"] if terbaik["tahap"] else WARNA["benar"], 416,
                      anchor="w")
            else:
                tulis(c, 382, tengah, "Belum dimainkan", 10, False, WARNA["abu"],
                      anchor="w")
                deret_bintang(c, 555, tengah, 12, 0)
                tulis(c, 632, tengah, "-", 10, False, WARNA["abu"], anchor="w")
            y += tinggi

        c.create_rectangle(40, y, 1060, y + 44, fill=WARNA["utama_muda"],
                           outline=WARNA["utama_tepi"])
        total, total_maks = self.app.total_skor()
        tulis(c, 122, y + 22, f"Total skor: {total} dari {total_maks}", 13, True,
              WARNA["utama"], anchor="w")
        y += 56
        tulis(c, 40, y, "Setiap percobaan tersimpan di: "
              + str(penyimpanan.path_file(self.app.folder_data)), 9, False,
              WARNA["lembut"], 1020)

        self.tambah_tombol(880, 636, 1060, 676, "Pilih Level ▶",
                           lambda: self.app.ganti_layar(LayarPilihLevel), "utama", 11)


# ===========================================================================
# Pengendali utama
# ===========================================================================
class App:
    """Menyimpan status permainan dan meneruskan event tkinter ke layar aktif."""

    def __init__(self, canvas, lebar, tinggi, folder_data):
        self.canvas = canvas
        self.lebar = lebar
        self.tinggi = tinggi
        self.folder_data = Path(folder_data)
        self.nama = ""
        self.hasil_terbaik = {}         # nomor level -> ringkasan terbaik
        self._nama_termuat = None
        self.info_level = data_soal.semua_level()
        self.layar = None

        canvas.bind("<Button-1>", self._saat_klik)
        canvas.bind("<Motion>", self._saat_gerak)
        canvas.bind("<Leave>", lambda e: self.layar and self.layar.gerak(-100, -100))
        canvas.bind("<Key>", self._saat_ketik)

    # ---- event dari tkinter ------------------------------------------------
    def _saat_klik(self, event):
        self.canvas.focus_set()
        if self.layar:
            self.layar.klik(event.x, event.y)

    def _saat_gerak(self, event):
        if self.layar:
            self.layar.gerak(event.x, event.y)

    def _saat_ketik(self, event):
        if self.layar:
            self.layar.ketik(event.keysym, event.char or "")

    # ---- alur --------------------------------------------------------------
    def mulai(self):
        self.ganti_layar(LayarMenu)

    def ganti_layar(self, kelas_layar, **data):
        self.layar = kelas_layar(self, **data)
        self.layar.gambar()

    def siapkan_pemain(self):
        """Memuat hasil terbaik dari CSV bila nama pemain berganti."""
        nama = self.nama.strip()
        if nama.lower() == self._nama_termuat:
            return
        try:
            self.hasil_terbaik = penyimpanan.hasil_terbaik_pemain(self.folder_data, nama)
        except (OSError, UnicodeDecodeError):
            self.hasil_terbaik = {}
        self._nama_termuat = nama.lower()

    def total_skor(self):
        """(jumlah skor terbaik, jumlah skor maksimal) seluruh level."""
        total = sum(h["skor"] for h in self.hasil_terbaik.values())
        maks = sum(POIN_LANGSUNG * len(lv.langkah) for lv in self.info_level)
        return total, maks

    def level_selesai(self, status):
        """Dipanggil LayarLevel saat level selesai. Mengembalikan pesan galat atau None."""
        penyimpanan.perbarui_terbaik(self.hasil_terbaik, status.level.nomor,
                                     penyimpanan.ringkasan(status))
        try:
            penyimpanan.simpan_hasil(self.folder_data,
                                     penyimpanan.buat_baris(self.nama, status))
        except OSError:
            return ("Hasil BELUM tersimpan ke file CSV. Jika hasil_belajar.csv sedang "
                    "dibuka di Excel, tutup dulu lalu ulangi level ini.")
        return None

    def tutup(self):
        """Dipanggil main.py saat jendela ditutup. Hasil sudah disimpan per level."""
        pass

    def keluar(self):
        self.tutup()
        self.canvas.winfo_toplevel().destroy()
