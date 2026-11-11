"""
Logika matematika dan penilaian game SPLDV metode grafik.

ATURAN: modul ini TIDAK BOLEH mengimpor tkinter, supaya bisa diuji
dengan unittest tanpa membuka jendela.

Semua bilangan disimpan sebagai fractions.Fraction agar hasil seperti
5,5 atau 1/3 tetap TEPAT (tidak ada galat pembulatan desimal).

Bentuk umum persamaan linear yang dipakai:  a*x + b*y = c
"""

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple, Union

Angka = Union[int, float, Fraction, str]
Titik = Tuple[Fraction, Fraction]

MINUS = "−"        # tanda minus matematika "−"
CENTANG = "✓"      # ✓
SILANG = "✗"       # ✗
TIDAK_SAMA = "≠"   # ≠

JENIS_LANGKAH = ("isian", "pilihan", "plot", "potong")

POIN_LANGSUNG = 10      # benar tanpa salah dan tanpa petunjuk
POIN_DIBANTU = 5        # sempat salah atau memakai petunjuk
POIN_PEMBAHASAN = 0     # melihat pembahasan

# Hubungan dua garis
BERPOTONGAN = "berpotongan"   # tepat satu penyelesaian
SEJAJAR = "sejajar"           # tidak ada penyelesaian
BERIMPIT = "berimpit"         # tak hingga banyak penyelesaian


# ===========================================================================
# Bilangan: konversi, format tampilan, dan pembacaan input siswa
# ===========================================================================
def baca_angka(teks):
    """Membaca input siswa menjadi Fraction, atau None jika bukan angka.

    Menerima: "4", "-1", "−1", "5,5", "5.5", "11/2", " 3 ".
    """
    if not isinstance(teks, str):
        return None
    bersih = teks.strip().replace(" ", "")
    for tanda in (MINUS, "–", "—"):  # −, – (en dash), — (em dash)
        bersih = bersih.replace(tanda, "-")
    bersih = bersih.replace(",", ".")
    if not bersih or any(ch not in "0123456789.+-/" for ch in bersih):
        return None
    try:
        return Fraction(bersih)
    except (ValueError, ZeroDivisionError):
        return None


def ke_pecahan(nilai):
    """Mengubah int/float/Fraction/str menjadi Fraction (ValueError jika gagal)."""
    if isinstance(nilai, bool):
        raise TypeError("Nilai boolean bukan angka.")
    if isinstance(nilai, Fraction):
        return nilai
    if isinstance(nilai, int):
        return Fraction(nilai)
    if isinstance(nilai, float):
        if not math.isfinite(nilai):
            raise ValueError(f"Bukan angka berhingga: {nilai!r}")
        return Fraction(repr(nilai))  # 0.1 -> 1/10, bukan 3602879701896397/...
    if isinstance(nilai, str):
        hasil = baca_angka(nilai)
        if hasil is None:
            raise ValueError(f"Bukan angka: {nilai!r}")
        return hasil
    raise TypeError(f"Tipe tidak didukung: {type(nilai).__name__}")


def _ke_desimal(q):
    """Fraction positif -> teks desimal berkoma, atau None jika tidak berhingga."""
    sisa = q.denominator
    for faktor in (2, 5):
        while sisa % faktor == 0:
            sisa //= faktor
    if sisa != 1:
        return None  # mis. 1/3 = 0,333... (desimal tak berhingga)
    k = 1
    while (10 ** k) % q.denominator != 0:
        k += 1
    digit = str(q.numerator * 10 ** k // q.denominator).rjust(k + 1, "0")
    return digit[:-k] + "," + digit[-k:]


def format_angka(nilai):
    """Angka untuk ditampilkan: 5.5 -> "5,5", -1 -> "−1", 1/3 -> "1/3"."""
    q = ke_pecahan(nilai)
    tanda = MINUS if q < 0 else ""
    q = abs(q)
    if q.denominator == 1:
        return tanda + str(q.numerator)
    desimal = _ke_desimal(q)
    if desimal is None:
        return f"{tanda}{q.numerator}/{q.denominator}"
    return tanda + desimal


def format_titik(x, y=None):
    """(3, 2) -> "(3, 2)". Bisa dipanggil format_titik(x, y) atau format_titik(titik).

    Jika ada koordinat desimal (berkoma), pemisahnya diganti titik koma agar
    tidak membingungkan: "(5,5; 2)".
    """
    if y is None:
        x, y = x
    teks_x, teks_y = format_angka(x), format_angka(y)
    pemisah = "; " if ("," in teks_x or "," in teks_y) else ", "
    return f"({teks_x}{pemisah}{teks_y})"


def _ke_titik(titik):
    x, y = titik
    return (ke_pecahan(x), ke_pecahan(y))


# ===========================================================================
# Persamaan linear dua variabel
# ===========================================================================
@dataclass(frozen=True)
class Persamaan:
    """Persamaan a*x + b*y = c."""

    a: Fraction
    b: Fraction
    c: Fraction

    def __post_init__(self):
        for nama in ("a", "b", "c"):
            object.__setattr__(self, nama, ke_pecahan(getattr(self, nama)))
        if self.a == 0 and self.b == 0:
            raise ValueError("Koefisien x dan y tidak boleh keduanya 0.")

    # ---- teks ------------------------------------------------------------
    def _ruas_kiri(self, isi_x="x", isi_y="y"):
        """Menyusun ruas kiri; isi_x/isi_y bisa "x" atau angka dalam kurung."""
        bagian = []
        for koef, isi in ((self.a, isi_x), (self.b, isi_y)):
            if koef == 0:
                continue
            besar = "" if abs(koef) == 1 else format_angka(abs(koef))
            suku = besar + isi
            if not bagian:
                bagian.append((MINUS if koef < 0 else "") + suku)
            else:
                bagian.append((f" {MINUS} " if koef < 0 else " + ") + suku)
        return "".join(bagian)

    def teks(self):
        """"2x + y = 8", "x − y = 1", "−x + 2y = 4"."""
        return f"{self._ruas_kiri()} = {format_angka(self.c)}"

    def __str__(self):
        return self.teks()

    def substitusi_teks(self, var, nilai):
        """substitusi_teks("x", 0) pada 2x + y = 8 -> "2(0) + y = 8"."""
        isi = f"({format_angka(nilai)})"
        if var == "x":
            kiri = self._ruas_kiri(isi_x=isi)
        elif var == "y":
            kiri = self._ruas_kiri(isi_y=isi)
        else:
            raise ValueError("var harus 'x' atau 'y'.")
        return f"{kiri} = {format_angka(self.c)}"

    def cek_teks(self, x, y):
        """"2(3) + (2) = 8 ✓" jika dipenuhi, "2(3) + (3) = 9 ≠ 8 ✗" jika tidak."""
        kiri = self._ruas_kiri(f"({format_angka(x)})", f"({format_angka(y)})")
        hasil = self.nilai_kiri(x, y)
        if hasil == self.c:
            return f"{kiri} = {format_angka(hasil)} {CENTANG}"
        return (f"{kiri} = {format_angka(hasil)} {TIDAK_SAMA} "
                f"{format_angka(self.c)} {SILANG}")

    # ---- hitungan --------------------------------------------------------
    def nilai_kiri(self, x, y):
        """Nilai a*x + b*y."""
        return self.a * ke_pecahan(x) + self.b * ke_pecahan(y)

    def dipenuhi(self, x, y):
        """True jika titik (x, y) terletak pada garis."""
        return self.nilai_kiri(x, y) == self.c

    def y_jika_x(self, x):
        """Nilai y untuk x tertentu; None jika garis tegak (b = 0)."""
        if self.b == 0:
            return None
        return (self.c - self.a * ke_pecahan(x)) / self.b

    def x_jika_y(self, y):
        """Nilai x untuk y tertentu; None jika garis mendatar (a = 0)."""
        if self.a == 0:
            return None
        return (self.c - self.b * ke_pecahan(y)) / self.a


def titik_potong(p1, p2):
    """Titik potong dua garis dengan aturan Cramer; None jika sejajar/berimpit."""
    determinan = p1.a * p2.b - p2.a * p1.b
    if determinan == 0:
        return None
    x = (p1.c * p2.b - p2.c * p1.b) / determinan
    y = (p1.a * p2.c - p2.a * p1.c) / determinan
    return (x, y)


def hubungan_garis(p1, p2):
    """BERPOTONGAN, SEJAJAR, atau BERIMPIT."""
    if p1.a * p2.b - p2.a * p1.b != 0:
        return BERPOTONGAN
    if p1.a * p2.c == p2.a * p1.c and p1.b * p2.c == p2.b * p1.c:
        return BERIMPIT
    return SEJAJAR


def potong_garis_dengan_kotak(p, xmin, xmax, ymin, ymax):
    """Dua titik ujung bagian garis yang berada di dalam kotak (untuk digambar).

    Mengembalikan ((x1, y1), (x2, y2)) terurut menurut x lalu y,
    atau None jika garis tidak melewati kotak (atau hanya menyentuh sudutnya).
    """
    xmin, xmax, ymin, ymax = (ke_pecahan(v) for v in (xmin, xmax, ymin, ymax))
    calon = set()
    for x in (xmin, xmax):
        y = p.y_jika_x(x)
        if y is not None and ymin <= y <= ymax:
            calon.add((x, y))
    for y in (ymin, ymax):
        x = p.x_jika_y(y)
        if x is not None and xmin <= x <= xmax:
            calon.add((x, y))
    if len(calon) < 2:
        return None
    titik = sorted(calon)
    return (titik[0], titik[-1])


# ===========================================================================
# Data soal: Langkah dan Level
# ===========================================================================
@dataclass
class Langkah:
    """Satu langkah pengerjaan dalam sebuah level.

    jenis:
      "isian"   -> siswa mengetik angka (field jawaban)
      "pilihan" -> siswa memilih salah satu opsi (field opsi & benar)
      "plot"    -> siswa klik 2 titik berbeda pada garis ke-`garis`
      "potong"  -> siswa klik titik potong kedua garis
    """

    jenis: str
    tahap: str                      # nama tahap untuk laporan, mis. "Menentukan titik potong sumbu"
    pertanyaan: str
    petunjuk: List[str]             # minimal 2, ditampilkan bertahap
    pembahasan: str
    jawaban: Optional[Fraction] = None                  # untuk "isian"
    opsi: List[str] = field(default_factory=list)       # untuk "pilihan"
    benar: Optional[int] = None                         # indeks opsi benar
    garis: Optional[int] = None                         # indeks garis (0/1)
    titik: List[Titik] = field(default_factory=list)    # 2 titik bantu untuk "plot"
    titik_hasil: Optional[Titik] = None                 # titik yang diperoleh dari "isian"
    umpan_benar: str = ""

    def __post_init__(self):
        if self.jenis not in JENIS_LANGKAH:
            raise ValueError(f"Jenis langkah tidak dikenal: {self.jenis!r}")
        self.petunjuk = list(self.petunjuk)
        if len(self.petunjuk) < 2:
            raise ValueError("Setiap langkah membutuhkan minimal 2 petunjuk.")
        if self.jawaban is not None:
            self.jawaban = ke_pecahan(self.jawaban)
        self.titik = [_ke_titik(t) for t in self.titik]
        if self.titik_hasil is not None:
            self.titik_hasil = _ke_titik(self.titik_hasil)

        if self.jenis == "isian" and self.jawaban is None:
            raise ValueError("Langkah isian membutuhkan jawaban.")
        if self.jenis == "pilihan":
            if len(self.opsi) < 2:
                raise ValueError("Langkah pilihan membutuhkan minimal 2 opsi.")
            if self.benar is None or not 0 <= self.benar < len(self.opsi):
                raise ValueError("Indeks opsi benar tidak valid.")
        if self.jenis == "plot":
            if self.garis is None:
                raise ValueError("Langkah plot membutuhkan indeks garis.")
            if len(self.titik) != 2 or self.titik[0] == self.titik[1]:
                raise ValueError("Langkah plot membutuhkan 2 titik bantu yang berbeda.")


@dataclass
class Level:
    nomor: int
    judul: str
    indikator: str                  # indikator pencapaian kompetensi
    cerita: str                     # konteks/cerita soal
    persamaan: List[Persamaan]      # tepat 2 persamaan
    rentang: Tuple[int, int, int, int]  # (xmin, xmax, ymin, ymax) bidang kartesius
    langkah_grid: Fraction = Fraction(1)  # jarak antar garis grid / titik klik
    langkah: List[Langkah] = field(default_factory=list)
    kesimpulan: str = ""            # arti titik potong dalam konteks soal

    def __post_init__(self):
        self.persamaan = [p if isinstance(p, Persamaan) else Persamaan(*p)
                          for p in self.persamaan]
        if len(self.persamaan) != 2:
            raise ValueError("Setiap level harus memiliki tepat 2 persamaan.")
        if len(self.rentang) != 4:
            raise ValueError("Rentang harus (xmin, xmax, ymin, ymax).")
        xmin, xmax, ymin, ymax = self.rentang
        if not (xmin < xmax and ymin < ymax):
            raise ValueError("Rentang sumbu tidak valid.")
        self.rentang = tuple(self.rentang)
        self.langkah_grid = ke_pecahan(self.langkah_grid)
        if self.langkah_grid <= 0:
            raise ValueError("langkah_grid harus positif.")
        if not self.langkah:
            raise ValueError("Level harus memiliki minimal 1 langkah.")

        for nomor, lk in enumerate(self.langkah, start=1):
            if lk.garis is not None and lk.garis not in (0, 1):
                raise ValueError(f"Langkah {nomor}: indeks garis harus 0 atau 1.")
            if lk.jenis == "plot":
                p = self.persamaan[lk.garis]
                for t in lk.titik:
                    if not p.dipenuhi(*t):
                        raise ValueError(
                            f"Langkah {nomor}: titik bantu {format_titik(t)} "
                            f"tidak terletak pada {p.teks()}.")
            if lk.jenis == "potong" and self.titik_potong is None:
                raise ValueError(f"Langkah {nomor}: kedua garis tidak berpotongan.")
            if (lk.jenis == "isian" and lk.titik_hasil is not None
                    and lk.garis is not None
                    and not self.persamaan[lk.garis].dipenuhi(*lk.titik_hasil)):
                raise ValueError(f"Langkah {nomor}: titik_hasil tidak terletak pada garis.")

    @property
    def titik_potong(self):
        return titik_potong(*self.persamaan)

    @property
    def hubungan(self):
        return hubungan_garis(*self.persamaan)


# ===========================================================================
# Status permainan satu level (kemajuan & penilaian siswa)
# ===========================================================================
@dataclass
class Umpan:
    """Umpan balik untuk setiap aksi siswa."""

    benar: bool
    pesan: str
    langkah_selesai: bool = False


@dataclass
class CatatanLangkah:
    salah: int = 0
    petunjuk_dipakai: int = 0
    lihat_pembahasan: bool = False
    selesai: bool = False
    poin: int = 0

    @property
    def dibantu(self):
        return self.salah > 0 or self.petunjuk_dipakai > 0 or self.lihat_pembahasan


class StatusLevel:
    """Menyimpan kemajuan siswa dalam satu level.

    Alur pemakaian oleh ui.py:
        status = StatusLevel(level)
        umpan = status.jawab_isian("8")      # / jawab_pilihan / klik_titik
        if umpan.langkah_selesai:
            status.lanjut()                  # ke langkah berikutnya
        ... hingga status.level_selesai
    """

    def __init__(self, level):
        self.level = level
        self.indeks = 0
        self.catatan = [CatatanLangkah() for _ in level.langkah]
        self.titik_terpilih: List[Titik] = []                 # titik benar pada langkah plot aktif
        self.titik_ditemukan: List[Tuple[Titik, Optional[int]]] = []  # (titik, indeks garis)
        self.garis_tergambar: Dict[int, Tuple[Titik, Titik]] = {}
        self.titik_potong_ditemukan: Optional[Titik] = None

    # ---- informasi -------------------------------------------------------
    @property
    def jumlah_langkah(self):
        return len(self.level.langkah)

    @property
    def nomor_langkah(self):
        return min(self.indeks + 1, self.jumlah_langkah)

    @property
    def level_selesai(self):
        return self.indeks >= self.jumlah_langkah

    @property
    def langkah_aktif(self):
        return None if self.level_selesai else self.level.langkah[self.indeks]

    @property
    def catatan_aktif(self):
        return None if self.level_selesai else self.catatan[self.indeks]

    @property
    def langkah_selesai(self):
        return (not self.level_selesai) and self.catatan_aktif.selesai

    @property
    def petunjuk_terlihat(self):
        if self.level_selesai:
            return []
        return self.langkah_aktif.petunjuk[:self.catatan_aktif.petunjuk_dipakai]

    # ---- penilaian -------------------------------------------------------
    @property
    def skor(self):
        return sum(c.poin for c in self.catatan)

    @property
    def skor_maks(self):
        return POIN_LANGSUNG * self.jumlah_langkah

    @property
    def bintang(self):
        if self.skor_maks == 0 or self.skor <= 0:
            return 0
        if self.skor * 10 >= self.skor_maks * 9:   # >= 90%
            return 3
        if self.skor * 10 >= self.skor_maks * 6:   # >= 60%
            return 2
        return 1

    @property
    def jumlah_salah(self):
        return sum(c.salah for c in self.catatan)

    @property
    def jumlah_petunjuk(self):
        return sum(c.petunjuk_dipakai for c in self.catatan)

    @property
    def tahap_perlu_latihan(self):
        """Daftar tahap (tanpa duplikat, urut) yang sempat salah atau dibantu."""
        hasil = []
        for lk, cat in zip(self.level.langkah, self.catatan):
            if cat.dibantu and lk.tahap not in hasil:
                hasil.append(lk.tahap)
        return hasil

    # ---- aksi siswa ------------------------------------------------------
    def _mulai_aksi(self, *jenis_diizinkan):
        if self.level_selesai:
            raise RuntimeError("Level sudah selesai.")
        if self.catatan_aktif.selesai:
            raise RuntimeError("Langkah ini sudah selesai; panggil lanjut().")
        if jenis_diizinkan and self.langkah_aktif.jenis not in jenis_diizinkan:
            raise ValueError(f"Aksi ini tidak berlaku untuk langkah "
                             f"{self.langkah_aktif.jenis!r}.")
        return self.langkah_aktif, self.catatan_aktif

    def _selesaikan(self):
        lk, cat = self.langkah_aktif, self.catatan_aktif
        cat.selesai = True
        if cat.lihat_pembahasan:
            cat.poin = POIN_PEMBAHASAN
        elif cat.salah > 0 or cat.petunjuk_dipakai > 0:
            cat.poin = POIN_DIBANTU
        else:
            cat.poin = POIN_LANGSUNG

        if lk.jenis == "isian" and lk.titik_hasil is not None:
            self.titik_ditemukan.append((lk.titik_hasil, lk.garis))
        elif lk.jenis == "plot":
            if len(self.titik_terpilih) < 2:
                self.titik_terpilih = list(lk.titik)
            self.garis_tergambar[lk.garis] = (self.titik_terpilih[0],
                                              self.titik_terpilih[1])
        elif lk.jenis == "potong":
            self.titik_potong_ditemukan = self.level.titik_potong

    def _umpan_benar(self, bawaan="Tepat!"):
        self._selesaikan()
        return Umpan(True, self.langkah_aktif.umpan_benar or bawaan, True)

    def jawab_isian(self, teks):
        lk, cat = self._mulai_aksi("isian")
        nilai = baca_angka(teks)
        if nilai is None:
            # Salah format tidak dihitung sebagai jawaban salah.
            return Umpan(False, "Jawaban harus berupa angka, misalnya 4, "
                                f"{MINUS}2, atau 5,5.")
        if nilai == lk.jawaban:
            return self._umpan_benar()
        cat.salah += 1
        return Umpan(False, f"Jawaban {format_angka(nilai)} belum tepat. "
                            "Periksa lagi perhitunganmu, atau tekan Petunjuk.")

    def jawab_pilihan(self, indeks_opsi):
        lk, cat = self._mulai_aksi("pilihan")
        if not 0 <= indeks_opsi < len(lk.opsi):
            raise ValueError("Indeks opsi di luar jangkauan.")
        if indeks_opsi == lk.benar:
            return self._umpan_benar()
        cat.salah += 1
        return Umpan(False, "Pilihan itu belum tepat. Coba perhatikan lagi "
                            "grafiknya, atau tekan Petunjuk.")

    def klik_titik(self, x, y):
        lk, cat = self._mulai_aksi("plot", "potong")
        titik = (ke_pecahan(x), ke_pecahan(y))
        teks_titik = format_titik(titik)
        if lk.jenis == "plot":
            return self._klik_plot(lk, cat, titik, teks_titik)
        return self._klik_potong(cat, titik, teks_titik)

    def _klik_plot(self, lk, cat, titik, teks_titik):
        p = self.level.persamaan[lk.garis]
        if titik in self.titik_terpilih:
            return Umpan(False, f"Titik {teks_titik} sudah kamu pilih. "
                                "Pilih titik lain yang berbeda.")
        if not p.dipenuhi(*titik):
            cat.salah += 1
            return Umpan(False,
                         f"Titik {teks_titik} tidak terletak pada garis {p.teks()}, "
                         f"karena hasilnya {format_angka(p.nilai_kiri(*titik))}, "
                         f"bukan {format_angka(p.c)}.")
        self.titik_terpilih.append(titik)
        if len(self.titik_terpilih) < 2:
            return Umpan(True, f"Tepat! Titik {teks_titik} terletak pada garis "
                               f"{p.teks()}. Sekarang pilih satu titik lagi.")
        return self._umpan_benar(f"Tepat! Dua titik sudah cukup untuk "
                                 f"menggambar garis {p.teks()}.")

    def _klik_potong(self, cat, titik, teks_titik):
        p1, p2 = self.level.persamaan
        di_1, di_2 = p1.dipenuhi(*titik), p2.dipenuhi(*titik)
        if di_1 and di_2:
            return self._umpan_benar(f"Tepat! Titik {teks_titik} terletak pada "
                                     "kedua garis, jadi itulah penyelesaiannya.")
        cat.salah += 1
        if di_1 or di_2:
            p = p1 if di_1 else p2
            return Umpan(False, f"Titik {teks_titik} hanya terletak pada garis "
                                f"{p.teks()}. Titik potong harus terletak pada "
                                "KEDUA garis.")
        return Umpan(False, f"Titik {teks_titik} tidak terletak pada garis "
                            f"{p1.teks()} maupun {p2.teks()}.")

    def minta_petunjuk(self):
        """Membuka satu petunjuk berikutnya dan mengembalikan teksnya."""
        lk, cat = self._mulai_aksi()
        if cat.petunjuk_dipakai >= len(lk.petunjuk):
            return ("Semua petunjuk sudah ditampilkan. Jika masih bingung, "
                    "tekan Pembahasan.")
        cat.petunjuk_dipakai += 1
        return lk.petunjuk[cat.petunjuk_dipakai - 1]

    def lihat_pembahasan(self):
        """Menampilkan pembahasan; langkah dianggap selesai dengan 0 poin."""
        lk, cat = self._mulai_aksi()
        cat.lihat_pembahasan = True
        self._selesaikan()
        return Umpan(False, lk.pembahasan, True)

    def lanjut(self):
        """Pindah ke langkah berikutnya. Mengembalikan True jika level selesai."""
        if not self.langkah_selesai:
            raise RuntimeError("Selesaikan langkah ini terlebih dahulu.")
        self.indeks += 1
        self.titik_terpilih = []
        return self.level_selesai
