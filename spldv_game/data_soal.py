"""
Data 5 level soal SPLDV metode grafik.

Diambil dari instrumen soal Mathematical Literacy, diurutkan dari
prosedural ke kontekstual:

    Level 1  Employing                      (instrumen no. 3)
    Level 2  Mathematical Reasoning         (instrumen no. 1)
    Level 3  Mathematical Reasoning         (instrumen no. 5)
    Level 4  Formulating                    (instrumen no. 2)
    Level 5  Interpreting & Evaluating      (instrumen no. 4)

Langkah isian koordinat + plot dan langkah titik potong dibuat otomatis
dari persamaan memakai langkah_koordinat() dan langkah_titik_potong(),
sehingga teks petunjuk dan pembahasan selalu konsisten dengan angkanya.
"""

import re
from fractions import Fraction

from .logika import (
    MINUS, Langkah, Level, Persamaan, format_angka, format_titik, ke_pecahan,
)

# Nama tahap (dipakai untuk laporan "tahap yang perlu dilatih")
TAHAP_MODEL = "Menyusun model matematika"
TAHAP_KOORDINAT = "Menentukan titik koordinat"
TAHAP_GARIS = "Menggambar garis"
TAHAP_POTONG = "Menentukan titik potong"
TAHAP_SIMPULAN = "Menyimpulkan / menafsirkan hasil"

DAFTAR_TAHAP = [TAHAP_MODEL, TAHAP_KOORDINAT, TAHAP_GARIS, TAHAP_POTONG, TAHAP_SIMPULAN]


# ===========================================================================
# Fungsi bantu pembuat langkah
# ===========================================================================
def _suku(koef, var):
    """2, "y" -> "2y";  1 -> "y";  −1 -> "−y"."""
    if koef == 1:
        return var
    if koef == -1:
        return MINUS + var
    return format_angka(koef) + var


def _tahapan_hitung(p, var, nilai):
    """Langkah hitung setelah substitusi, mis. ["2(5) + y = 11", "10 + y = 11",
    "y = 11 − 10", "y = 1"]. Mengembalikan (daftar_teks, variabel_lain, hasil)."""
    nilai = ke_pecahan(nilai)
    if var == "x":
        diketahui, koef_lain, lain = p.a * nilai, p.b, "y"
    elif var == "y":
        diketahui, koef_lain, lain = p.b * nilai, p.a, "x"
    else:
        raise ValueError("var harus 'x' atau 'y'.")
    if koef_lain == 0:
        raise ValueError(f"Substitusi {var} = {nilai} pada {p.teks()} tidak "
                         f"menghasilkan nilai {('y' if var == 'x' else 'x')}.")

    hasil = (p.c - diketahui) / koef_lain
    c = format_angka(p.c)
    teks = [p.substitusi_teks(var, nilai)]
    if diketahui != 0:
        tanda = MINUS if koef_lain < 0 else "+"
        teks.append(f"{format_angka(diketahui)} {tanda} {_suku(abs(koef_lain), lain)} = {c}")
        tanda = MINUS if diketahui > 0 else "+"
        teks.append(f"{_suku(koef_lain, lain)} = {c} {tanda} {format_angka(abs(diketahui))}")
    if koef_lain != 1:
        teks.append(f"{_suku(koef_lain, lain)} = {format_angka(p.c - diketahui)}")
    teks.append(f"{lain} = {format_angka(hasil)}")
    return teks, lain, hasil


def _indeks_dari_nama(nama_garis):
    cocok = re.search(r"(\d+)\s*$", nama_garis)
    if not cocok:
        raise ValueError("Beri argumen garis=0/1 jika nama garis tidak diakhiri nomor.")
    return int(cocok.group(1)) - 1


def langkah_koordinat(p, nama_garis, daftar_substitusi, garis=None):
    """Membuat 2 langkah isian koordinat + 1 langkah plot untuk satu garis.

    daftar_substitusi berisi 2 pasangan (variabel, nilai), boleh ditambah
    elemen ketiga berupa list petunjuk tambahan, contoh:
        [("x", 0), ("x", 5, ["Mengapa x = 5? ..."])]
    garis (0/1) otomatis dibaca dari nama, mis. "Garis 2" -> 1.
    """
    if len(daftar_substitusi) != 2:
        raise ValueError("Butuh tepat 2 substitusi untuk memperoleh 2 titik.")
    if garis is None:
        garis = _indeks_dari_nama(nama_garis)

    hasil_langkah = []
    titik_diperoleh = []
    for isi in daftar_substitusi:
        var, nilai = isi[0], ke_pecahan(isi[1])
        tambahan = list(isi[2]) if len(isi) > 2 else []
        tahapan, lain, hasil = _tahapan_hitung(p, var, nilai)
        titik = (nilai, hasil) if var == "x" else (hasil, nilai)
        titik_diperoleh.append(titik)
        teks_nilai = format_angka(nilai)

        petunjuk = tambahan + [
            f"Ganti (substitusi) {var} dengan {teks_nilai} pada persamaan {p.teks()}.",
            f"Setelah disubstitusi menjadi: {tahapan[0]}. "
            f"Sederhanakan, lalu cari nilai {lain}.",
        ]
        hasil_langkah.append(Langkah(
            jenis="isian",
            tahap=TAHAP_KOORDINAT,
            pertanyaan=f"{nama_garis}: {p.teks()}\n"
                       f"Jika {var} = {teks_nilai}, maka {lain} = ... ?",
            petunjuk=petunjuk,
            pembahasan=" → ".join(tahapan)
                       + f". Jadi diperoleh titik {format_titik(titik)}.",
            jawaban=hasil,
            garis=garis,
            titik_hasil=titik,
            umpan_benar=f"Tepat! {lain} = {format_angka(hasil)}, "
                        f"jadi diperoleh titik {format_titik(titik)}.",
        ))

    t1, t2 = titik_diperoleh
    hasil_langkah.append(Langkah(
        jenis="plot",
        tahap=TAHAP_GARIS,
        pertanyaan=f"Gambar {nama_garis} ({p.teks()}): klik 2 titik berbeda "
                   "yang terletak pada garis tersebut.",
        petunjuk=[
            f"Kamu sudah menemukan titik {format_titik(t1)} dan {format_titik(t2)}. "
            "Klik kedua titik itu pada bidang koordinat.",
            "Titik (x, y) artinya: dari titik O(0, 0) geser x satuan ke kanan, "
            "lalu y satuan ke atas.",
        ],
        pembahasan=f"Titik {format_titik(t1)} dan {format_titik(t2)} memenuhi "
                   f"{p.teks()}: {p.cek_teks(*t1)} dan {p.cek_teks(*t2)}. "
                   f"Hubungkan kedua titik itu sehingga terbentuk {nama_garis}.",
        garis=garis,
        titik=[t1, t2],
        umpan_benar=f"Bagus! {nama_garis} ({p.teks()}) sudah tergambar.",
    ))
    return hasil_langkah


def langkah_titik_potong(p1, p2):
    """Membuat langkah "potong" beserta pembahasan yang mengecek kedua persamaan."""
    from .logika import titik_potong
    titik = titik_potong(p1, p2)
    if titik is None:
        raise ValueError("Kedua garis tidak berpotongan di satu titik.")
    x, y = titik
    teks_titik = format_titik(titik)
    return Langkah(
        jenis="potong",
        tahap=TAHAP_POTONG,
        pertanyaan="Klik titik potong kedua garis pada bidang koordinat.",
        petunjuk=[
            "Titik potong adalah titik tempat kedua garis bertemu.",
            f"Titik potong harus memenuhi KEDUA persamaan sekaligus, yaitu "
            f"{p1.teks()} dan {p2.teks()}. Periksa titik yang kamu pilih dengan "
            "substitusi ke kedua persamaan.",
        ],
        pembahasan=f"Kedua garis berpotongan di titik {teks_titik}. "
                   f"Cek: {p1.cek_teks(x, y)} dan {p2.cek_teks(x, y)}. "
                   f"Jadi x = {format_angka(x)} dan y = {format_angka(y)}.",
        umpan_benar=f"Tepat! Titik potongnya {teks_titik}. "
                    f"Cek: {p1.cek_teks(x, y)} dan {p2.cek_teks(x, y)}.",
    )


def pilihan(tahap, pertanyaan, opsi, benar, petunjuk, pembahasan, umpan_benar=""):
    """Singkatan pembuatan langkah pilihan ganda."""
    return Langkah(jenis="pilihan", tahap=tahap, pertanyaan=pertanyaan,
                   petunjuk=petunjuk, pembahasan=pembahasan, opsi=opsi,
                   benar=benar, umpan_benar=umpan_benar)


# ===========================================================================
# Level 1 - Employing (instrumen no. 3)
# ===========================================================================
def _level_1():
    p1 = Persamaan(2, 1, 8)    # 2x + y = 8
    p2 = Persamaan(1, -1, 1)   # x − y = 1
    langkah = (
        langkah_koordinat(p1, "Garis 1", [("x", 0), ("y", 0)])
        + langkah_koordinat(p2, "Garis 2", [("x", 0), ("y", 0)])
        + [langkah_titik_potong(p1, p2)]
        + [pilihan(
            TAHAP_SIMPULAN,
            "Jadi, himpunan penyelesaian (HP) sistem persamaan tersebut adalah ...",
            ["HP = {(2, 3)}", "HP = {(3, 2)}",
             "HP = {(4, 0), (1, 0)}", "HP = {(0, 8), (0, −1)}"],
            1,
            ["HP berisi titik yang memenuhi kedua persamaan, yaitu titik potong "
             "kedua garis.",
             "Perhatikan urutan (x, y): nilai x ditulis lebih dulu. Titik-titik "
             "pada sumbu hanya membantu menggambar garis."],
            "Kedua garis berpotongan di (3, 2), artinya x = 3 dan y = 2. "
            "Jadi HP = {(3, 2)}. Pilihan {(2, 3)} urutannya tertukar, sedangkan "
            "(4, 0), (1, 0), (0, 8), (0, −1) hanyalah titik potong garis dengan sumbu.",
            "Tepat! HP = {(3, 2)}.",
        )]
    )
    return Level(
        nomor=1,
        judul="Pemanasan: Langkah Metode Grafik",
        indikator="Employing: menerapkan langkah-langkah metode grafik untuk "
                  "menentukan himpunan penyelesaian SPLDV.",
        cerita="Tentukan himpunan penyelesaian dari sistem persamaan\n"
               "2x + y = 8 dan x − y = 1 dengan metode grafik.",
        persamaan=[p1, p2],
        rentang=(-2, 9, -2, 9),
        langkah_grid=1,
        langkah=langkah,
        kesimpulan="Jadi HP = {(3, 2)}.",
    )


# ===========================================================================
# Level 2 - Mathematical Reasoning (instrumen no. 1)
# ===========================================================================
def _level_2():
    p1 = Persamaan(1, 1, 8)    # x + y = 8
    p2 = Persamaan(2, 1, 12)   # 2x + y = 12
    langkah = (
        langkah_koordinat(p1, "Garis 1", [("x", 0), ("y", 0)])
        + langkah_koordinat(p2, "Garis 2", [("x", 0), ("y", 0)])
        + [langkah_titik_potong(p1, p2)]
        + [
            pilihan(
                TAHAP_SIMPULAN,
                "Siswa A menjawab (4, 4), siswa B menjawab (3, 5). "
                "Jawaban siapa yang benar?",
                ["Siswa A", "Siswa B", "Keduanya benar", "Keduanya salah"],
                0,
                ["Bandingkan jawaban A dan B dengan titik potong yang kamu temukan "
                 "pada grafik.",
                 "Penyelesaian SPLDV hanya ada satu jika kedua garis berpotongan, "
                 "yaitu titik potongnya."],
                "Grafik menunjukkan titik potong (4, 4). Cek: 4 + 4 = 8 ✓ dan "
                "2(4) + 4 = 12 ✓. Jadi jawaban siswa A yang benar.",
                "Tepat! Jawaban siswa A, (4, 4), sesuai dengan titik potong grafik.",
            ),
            pilihan(
                TAHAP_SIMPULAN,
                "Mengapa jawaban siswa B, yaitu (3, 5), salah?",
                ["(3, 5) tidak memenuhi x + y = 8",
                 "Karena nilai x harus lebih besar daripada y",
                 "(3, 5) hanya memenuhi x + y = 8, tetapi 2(3) + 5 = 11, bukan 12",
                 "(3, 5) terletak pada kedua garis, tetapi B salah menulis"],
                2,
                ["Substitusikan x = 3 dan y = 5 ke persamaan pertama: 3 + 5 = ...?",
                 "Sekarang substitusikan ke persamaan kedua: 2(3) + 5 = ...? "
                 "Apakah hasilnya 12?"],
                f"{p1.cek_teks(3, 5)}, tetapi {p2.cek_teks(3, 5)}. Titik (3, 5) "
                "hanya terletak pada garis x + y = 8, tidak pada garis 2x + y = 12, "
                "sehingga bukan penyelesaian.",
                "Tepat! Penyelesaian harus memenuhi KEDUA persamaan.",
            ),
        ]
    )
    return Level(
        nomor=2,
        judul="Siapa yang Benar?",
        indikator="Mathematical Reasoning: memeriksa kebenaran jawaban dan "
                  "memberikan alasan berdasarkan grafik.",
        cerita="Diberikan SPLDV x + y = 8 dan 2x + y = 12.\n"
               "Siswa A menjawab penyelesaiannya (4, 4), sedangkan siswa B menjawab "
               "(3, 5).\nSelidiki dengan metode grafik, jawaban siapa yang benar?",
        persamaan=[p1, p2],
        rentang=(0, 13, 0, 13),
        langkah_grid=1,
        langkah=langkah,
        kesimpulan="Jadi jawaban siswa A, yaitu (4, 4), yang benar.",
    )


# ===========================================================================
# Level 3 - Mathematical Reasoning (instrumen no. 5)
# ===========================================================================
def _level_3():
    p1 = Persamaan(1, 1, 5)    # x + y = 5
    p2 = Persamaan(1, 2, 8)    # x + 2y = 8
    langkah = (
        langkah_koordinat(p1, "Garis 1", [("x", 0), ("y", 0)])
        + langkah_koordinat(p2, "Garis 2", [("x", 0), ("y", 0)])
        + [langkah_titik_potong(p1, p2)]
        + [pilihan(
            TAHAP_SIMPULAN,
            "Seorang siswa menyatakan titik potongnya (2, 3). "
            "Apakah kamu setuju? Pilih jawaban beserta alasan yang tepat.",
            ["Setuju, karena 2 + 3 = 5 sudah cukup membuktikannya",
             "Setuju, karena 2 + 3 = 5 dan 2 + 2(3) = 8",
             "Tidak setuju, karena titik potongnya (3, 2)",
             "Tidak setuju, karena 2 + 2(3) = 10, bukan 8"],
            1,
            ["Bandingkan pernyataan siswa dengan titik potong pada grafikmu.",
             "Alasan yang lengkap harus mengecek titik (2, 3) pada KEDUA persamaan, "
             "bukan hanya satu."],
            f"Titik potong grafik memang (2, 3). Cek: {p1.cek_teks(2, 3)} dan "
            f"{p2.cek_teks(2, 3)}. Jadi pernyataan siswa benar. Mengecek satu "
            "persamaan saja belum cukup, karena banyak titik lain yang memenuhi "
            "x + y = 5, misalnya (1, 4).",
            "Tepat! Kamu setuju dengan alasan yang lengkap.",
        )]
    )
    return Level(
        nomor=3,
        judul="Setuju atau Tidak?",
        indikator="Mathematical Reasoning: menilai pernyataan dan memberikan "
                  "alasan dengan memeriksa kedua persamaan.",
        cerita="Seorang siswa menyatakan:\n\"Titik potong grafik x + y = 5 dan "
               "x + 2y = 8 adalah (2, 3).\"\nApakah kamu setuju? Buktikan dengan "
               "metode grafik.",
        persamaan=[p1, p2],
        rentang=(0, 9, 0, 9),
        langkah_grid=1,
        langkah=langkah,
        kesimpulan="Jadi kita setuju dengan pernyataan siswa tersebut.",
    )


# ===========================================================================
# Level 4 - Formulating (instrumen no. 2)
# ===========================================================================
def _level_4():
    p1 = Persamaan(2, 1, 11)   # 2x + y = 11  (Rina)
    p2 = Persamaan(1, 2, 10)   # x + 2y = 10  (Dika)
    alasan_x5 = [
        "Mengapa memakai x = 5, bukan y = 0? Jika y = 0, maka 2x = 11 sehingga "
        "x = 5,5. Titik (5,5; 0) sulit digambar tepat pada grid. Karena itu kita "
        "memilih nilai x yang membuat y bilangan bulat, yaitu x = 5.",
    ]
    langkah = (
        [pilihan(
            TAHAP_MODEL,
            "Misalkan x = harga 1 buku tulis dan y = harga 1 pensil (ribuan rupiah). "
            "Model matematika yang tepat adalah ...",
            ["x + 2y = 11 dan 2x + y = 10",
             "2x + y = 10 dan x + 2y = 11",
             "2x + y = 11 dan x + 2y = 10",
             "x + y = 11 dan x + y = 10"],
            2,
            ["Rina: 2 buku tulis + 1 pensil = 11 ribu. Ganti \"buku tulis\" dengan x "
             "dan \"pensil\" dengan y.",
             "Dika: 1 buku tulis + 2 pensil = 10 ribu. Perhatikan angka mana yang "
             "menempel pada x dan mana yang menempel pada y."],
            "Belanjaan Rina: 2 buku + 1 pensil = Rp11.000 → 2x + y = 11. "
            "Belanjaan Dika: 1 buku + 2 pensil = Rp10.000 → x + 2y = 10.",
            "Tepat! Modelnya 2x + y = 11 dan x + 2y = 10.",
        )]
        + langkah_koordinat(p1, "Garis 1", [("x", 0), ("x", 5, alasan_x5)])
        + langkah_koordinat(p2, "Garis 2", [("x", 0), ("y", 0)])
        + [langkah_titik_potong(p1, p2)]
        + [pilihan(
            TAHAP_SIMPULAN,
            "Titik potong (4, 3). Apa artinya dalam soal belanja ini?",
            ["Harga 1 buku tulis Rp3.000 dan 1 pensil Rp4.000",
             "Harga 1 buku tulis Rp4.000 dan 1 pensil Rp3.000",
             "Harga 1 buku tulis Rp4 dan 1 pensil Rp3",
             "Harga 1 buku tulis dan 1 pensil seluruhnya Rp43.000"],
            1,
            ["Ingat pemisalan: x = harga buku tulis, y = harga pensil.",
             "Satuan harga dalam soal adalah ribuan rupiah, jadi 4 artinya Rp4.000."],
            "Titik (4, 3) berarti x = 4 dan y = 3 (ribuan rupiah). Jadi harga 1 buku "
            "tulis Rp4.000 dan 1 pensil Rp3.000. Cek: Rina 2(4.000) + 3.000 = 11.000 ✓, "
            "Dika 4.000 + 2(3.000) = 10.000 ✓.",
            "Tepat! Buku tulis Rp4.000 dan pensil Rp3.000.",
        )]
    )
    return Level(
        nomor=4,
        judul="Belanja Buku dan Pensil",
        indikator="Formulating: mengubah masalah sehari-hari menjadi model SPLDV "
                  "lalu menyelesaikannya dengan grafik.",
        cerita="Rina membeli 2 buku tulis dan 1 pensil seharga Rp11.000.\n"
               "Dika membeli 1 buku tulis dan 2 pensil seharga Rp10.000.\n"
               "Berapakah harga 1 buku tulis dan harga 1 pensil?",
        persamaan=[p1, p2],
        rentang=(0, 12, 0, 12),
        langkah_grid=1,
        langkah=langkah,
        kesimpulan="Artinya, harga 1 buku tulis Rp4.000 dan harga 1 pensil Rp3.000.",
    )


# ===========================================================================
# Level 5 - Interpreting & Evaluating (instrumen no. 4)
# ===========================================================================
def _level_5():
    p1 = Persamaan(1, 1, 20)   # x + y = 20
    p2 = Persamaan(2, 4, 56)   # 2x + 4y = 56
    langkah = (
        [pilihan(
            TAHAP_MODEL,
            "Misalkan x = banyak sepeda motor dan y = banyak mobil. "
            "Model matematika yang tepat adalah ...",
            ["x + y = 56 dan 2x + 4y = 20",
             "x + y = 20 dan 4x + 2y = 56",
             "x + y = 20 dan x + y = 56",
             "x + y = 20 dan 2x + 4y = 56"],
            3,
            ["Banyak kendaraan seluruhnya 20, jadi motor + mobil = 20.",
             "Sepeda motor memiliki 2 roda dan mobil 4 roda. Banyak roda seluruhnya "
             "56, jadi 2 × (banyak motor) + 4 × (banyak mobil) = 56."],
            "Banyak kendaraan: x + y = 20. Banyak roda: motor 2 roda dan mobil "
            "4 roda, jadi 2x + 4y = 56.",
            "Tepat! Modelnya x + y = 20 dan 2x + 4y = 56.",
        )]
        + langkah_koordinat(p1, "Garis 1", [("x", 0), ("y", 0)])
        + langkah_koordinat(p2, "Garis 2", [("x", 0), ("y", 0)])
        + [langkah_titik_potong(p1, p2)]
        + [
            pilihan(
                TAHAP_SIMPULAN,
                "Titik potong (12, 8). Apa artinya dalam soal tempat parkir?",
                ["8 sepeda motor dan 12 mobil",
                 "12 sepeda motor dan 8 mobil",
                 "12 roda sepeda motor dan 8 roda mobil",
                 "20 kendaraan dan 56 roda"],
                1,
                ["Ingat pemisalan: x = banyak sepeda motor, y = banyak mobil.",
                 "Pada titik (12, 8), nilai x = 12 dan nilai y = 8."],
                "Titik (12, 8) berarti x = 12 dan y = 8, yaitu ada 12 sepeda motor "
                "dan 8 mobil.",
                "Tepat! Ada 12 sepeda motor dan 8 mobil.",
            ),
            Langkah(
                jenis="isian",
                tahap=TAHAP_SIMPULAN,
                pertanyaan="Cek kewajaran: apakah jumlah rodanya benar 56?\n"
                           "12 × 2 + 8 × 4 = ... ?",
                petunjuk=["Hitung dulu roda sepeda motor: 12 × 2 = 24.",
                          "Lalu roda mobil: 8 × 4 = 32. Jumlahkan keduanya."],
                pembahasan="12 × 2 + 8 × 4 = 24 + 32 = 56. Jumlah roda sesuai "
                           "soal, dan 12 + 8 = 20 kendaraan. Jawaban masuk akal.",
                jawaban=56,
                umpan_benar="Tepat! 24 + 32 = 56, sesuai dengan soal.",
            ),
            pilihan(
                TAHAP_SIMPULAN,
                "Seorang teman menjawab (10,5; 9,5). Apakah jawaban itu masuk akal?",
                ["Ya, karena 10,5 + 9,5 = 20",
                 "Tidak, karena banyak kendaraan harus bilangan bulat",
                 "Ya, karena titiknya dekat dengan titik potong",
                 "Tidak, karena banyak motor harus lebih sedikit daripada mobil"],
                1,
                ["Mungkinkah ada 10,5 sepeda motor di tempat parkir?",
                 "Coba juga cek persamaan roda: 2(10,5) + 4(9,5) = ...?"],
                "Banyak kendaraan harus bilangan cacah; tidak mungkin ada 10,5 sepeda "
                f"motor. Selain itu {p2.cek_teks(Fraction(21, 2), Fraction(19, 2))}. "
                "Jadi jawaban yang benar tetap 12 sepeda motor dan 8 mobil.",
                "Tepat! Jawaban soal cerita harus masuk akal sesuai konteksnya.",
            ),
        ]
    )
    return Level(
        nomor=5,
        judul="Tempat Parkir",
        indikator="Interpreting & Evaluating: menafsirkan titik potong sesuai "
                  "konteks dan menilai kewajaran jawaban.",
        cerita="Di sebuah tempat parkir terdapat 20 kendaraan yang terdiri atas "
               "sepeda motor dan mobil.\nJumlah seluruh roda kendaraan itu 56.\n"
               "Berapa banyak sepeda motor dan mobil di tempat parkir tersebut?",
        persamaan=[p1, p2],
        rentang=(0, 30, 0, 30),
        langkah_grid=2,
        langkah=langkah,
        kesimpulan="Artinya, di tempat parkir ada 12 sepeda motor dan 8 mobil.",
    )


# ===========================================================================
# Akses data level
# ===========================================================================
_PEMBUAT_LEVEL = [_level_1, _level_2, _level_3, _level_4, _level_5]


def semua_level():
    """Mengembalikan list 5 objek Level BARU (aman diubah tanpa memengaruhi data asli)."""
    return [buat() for buat in _PEMBUAT_LEVEL]


def jumlah_level():
    return len(_PEMBUAT_LEVEL)


def ambil_level(nomor):
    """Mengambil satu Level baru berdasarkan nomor (1-5)."""
    if not 1 <= nomor <= len(_PEMBUAT_LEVEL):
        raise ValueError(f"Nomor level harus 1 sampai {len(_PEMBUAT_LEVEL)}.")
    return _PEMBUAT_LEVEL[nomor - 1]()
