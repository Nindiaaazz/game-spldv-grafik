# Petualangan Grafik SPLDV

Media pembelajaran berbentuk **game** untuk materi **Sistem Persamaan Linear Dua Variabel
(SPLDV) metode grafik** bagi siswa SMP kelas VIII. Media ini dikembangkan dengan model
ADDIE (tahap *Development*). Soal-soalnya diambil dari instrumen *Mathematical Literacy*
dan diurutkan dari soal prosedural ke soal kontekstual.

Siswa mengerjakan setiap soal langkah demi langkah:

1. menyusun model matematika,
2. menentukan titik koordinat,
3. menggambar garis pada grafik interaktif,
4. menentukan titik potong,
5. menafsirkan hasilnya.

Setiap langkah langsung mendapat umpan balik, dan siswa bisa membuka petunjuk bertahap.
Hasil belajar tersimpan otomatis ke file CSV.

## Kebutuhan

- Python 3.9 atau lebih baru. Di Windows, tkinter sudah ikut terpasang.
- **Tidak perlu meng-install library tambahan** (lihat `requirements.txt`).

## Cara menjalankan

```
cd game-spldv-grafik
python main.py
```

Game juga bisa dijalankan dari folder di atasnya (`media-pembelajaran-spldv-grafik`)
dengan `python main.py`. File `main.py` di sana hanya bertugas menjalankan game ini.

Menjalankan semua pengujian (dari folder `game-spldv-grafik`):

```
python -m unittest
```

## Alur permainan

1. **Menu.** Siswa mengetik Nama/NIM (wajib), lalu memilih *Mulai Bermain*,
   *Materi Singkat*, *Lihat Hasil Belajar*, atau *Keluar*.
2. **Materi Singkat** terdiri dari 4 halaman dengan contoh `x + y = 4` dan `x − y = 2`:
   apa itu SPLDV, menentukan titik koordinat, menggambar garis (termasuk tips jika
   hasilnya pecahan), dan titik potong (3, 1) sebagai penyelesaian.
3. **Pilih Level.** Terdapat 5 kartu level berisi judul, indikator, bintang terbaik,
   dan skor terbaik.
4. **Bermain.** Kolom kiri berisi soal, penanda kemajuan langkah, pertanyaan, dan area
   jawaban. Area jawaban berupa keypad angka, pilihan A–D, atau klik pada grafik.
   Di bawahnya ada kotak umpan balik dan kotak petunjuk. Kolom kanan berisi grafik
   Kartesius interaktif yang menampilkan koordinat titik di bawah kursor.
   - Benar langsung: **10 poin**. Sempat salah atau memakai petunjuk: **5 poin**.
     Melihat pembahasan: **0 poin**.
   - Bintang: ≥ 90% → 3 bintang, ≥ 60% → 2 bintang, lebih dari 0 → 1 bintang.
5. **Level Selesai.** Muncul bintang, skor, bagian yang perlu dilatih lagi, dan
   kesimpulan arti titik potong. Hasil disimpan ke CSV.
6. **Hasil Belajar.** Tabel skor terbaik setiap level beserta total skor
   (maksimal 450).

Kontrol keyboard:

| Tombol | Fungsi |
|---|---|
| Angka, `-`, `,` | Mengetik jawaban isian |
| Backspace | Menghapus satu karakter |
| Enter | Cek jawaban atau Lanjut |
| `1`–`4` atau `A`–`D` | Memilih opsi |
| Panah kiri/kanan | Pindah halaman materi |

## Lima level

| Level | Judul | Proses literasi matematis | Indikator | SPLDV | Titik potong |
|---|---|---|---|---|---|
| 1 | Pemanasan: Langkah Metode Grafik | *Employing* (instrumen no. 3) | Menerapkan langkah-langkah metode grafik untuk menentukan himpunan penyelesaian SPLDV | 2x + y = 8; x − y = 1 | (3, 2) |
| 2 | Siapa yang Benar? | *Mathematical Reasoning* (instrumen no. 1) | Memeriksa kebenaran jawaban dan memberikan alasan berdasarkan grafik | x + y = 8; 2x + y = 12 | (4, 4) |
| 3 | Setuju atau Tidak? | *Mathematical Reasoning* (instrumen no. 5) | Menilai pernyataan dan memberikan alasan dengan memeriksa kedua persamaan | x + y = 5; x + 2y = 8 | (2, 3) |
| 4 | Belanja Buku dan Pensil | *Formulating* (instrumen no. 2) | Mengubah masalah sehari-hari menjadi model SPLDV lalu menyelesaikannya dengan grafik | 2x + y = 11; x + 2y = 10 | (4, 3) |
| 5 | Tempat Parkir | *Interpreting & Evaluating* (instrumen no. 4) | Menafsirkan titik potong sesuai konteks dan menilai kewajaran jawaban | x + y = 20; 2x + 4y = 56 | (12, 8) |

## Temuan wawancara dan fitur yang dikembangkan

| Temuan wawancara (tahap Analysis) | Fitur dalam game |
|---|---|
| Siswa lupa materi | **Materi Singkat** 4 halaman yang bisa dibuka dari menu |
| Siswa sulit menentukan nilai x dan y | **Isian bertahap** ("Jika x = 0, maka y = ...?") dengan **petunjuk** yang dibuka satu per satu |
| Siswa belum paham makna titik potong | **Visualisasi** titik potong beserta garis proyeksi ke sumbu, dan **pengecekan ke kedua persamaan** pada umpan balik dan pembahasan |
| Siswa ingin ada visualisasi | **Grafik interaktif**: siswa mengklik titik, garis tergambar, dan koordinat di bawah kursor ditampilkan |
| Siswa ingin penjelasan sederhana dan contoh soal | **Satu langkah per layar**, dengan pembahasan per langkah dan contoh pada materi singkat |
| Siswa ingin tahu letak kesalahannya | **Umpan balik per langkah** yang menjelaskan alasannya, misalnya "Titik (3, 3) tidak terletak pada garis 2x + y = 8, karena hasilnya 9, bukan 8." |
| Siswa tertarik pada game | **Skor, bintang, dan level**, serta tabel hasil belajar |

## Struktur folder

```
game-spldv-grafik/
  main.py                    membuat jendela tkinter + canvas 1100x700, menjalankan App
  spldv_game/
    __init__.py
    logika.py                perhitungan (Fraction), Persamaan, Langkah, Level,
                             StatusLevel (penilaian) - tanpa tkinter
    data_soal.py             5 level soal + fungsi pembuat langkah otomatis
    ui.py                    semua layar, digambar di canvas - tanpa import tkinter
    penyimpanan.py           simpan/baca hasil belajar (CSV)
  tests/
    test_logika.py           matematika, penilaian, dan 5 soal
    test_data_soal.py        kelengkapan data soal
    test_penyimpanan.py      file CSV
    test_tampilan.py         alur tampilan dengan kanvas tiruan (tanpa tkinter)
    test_ui.py               uji tata letak dengan tkinter asli (dilewati bila tidak ada layar)
  data_hasil/hasil_belajar.csv   dibuat otomatis saat level pertama selesai
  README.md, requirements.txt, .gitignore
```

## Data hasil belajar

Setiap level yang selesai menambah satu baris ke `data_hasil/hasil_belajar.csv`.
File memakai pemisah `;` dan encoding UTF-8 dengan BOM, sehingga rapi saat dibuka di Excel.

Kolomnya: waktu, nama, level, judul, indikator, skor, skor_maks, bintang,
jumlah_salah, jumlah_petunjuk, tahap_perlu_latihan, rincian_langkah. Kolom terakhir
berisi jumlah salah, petunjuk, dan poin setiap langkah.

Tutup file CSV di Excel sebelum bermain, karena Excel mengunci file sehingga hasil tidak
dapat ditulis. File ini berisi data siswa, jadi tidak ikut diunggah ke git
(lihat `.gitignore`).

## Cara menambah atau mengubah soal

Soal ada di `spldv_game/data_soal.py`. Setiap level dibuat oleh satu fungsi. Contoh:

```python
def _level_6():
    p1 = Persamaan(1, 1, 6)     # x + y = 6
    p2 = Persamaan(1, -1, 2)    # x − y = 2
    langkah = (
        langkah_koordinat(p1, "Garis 1", [("x", 0), ("y", 0)])   # 2 isian + 1 plot
        + langkah_koordinat(p2, "Garis 2", [("x", 0), ("y", 0)])
        + [langkah_titik_potong(p1, p2)]                          # klik titik potong
        + [pilihan(
            TAHAP_SIMPULAN,
            "Himpunan penyelesaiannya adalah ...",
            ["HP = {(2, 4)}", "HP = {(4, 2)}", "HP = {(6, 0)}", "HP = {(0, 6)}"],
            1,                                         # indeks jawaban benar (B)
            ["Petunjuk pertama ...", "Petunjuk kedua ..."],   # minimal 2
            "Pembahasan ...",
        )]
    )
    return Level(nomor=6, judul="...", indikator="Employing: ...",
                 cerita="...", persamaan=[p1, p2], rentang=(0, 8, 0, 8),
                 langkah_grid=1, langkah=langkah, kesimpulan="Jadi HP = {(4, 2)}.")
```

Lalu tambahkan `_level_6` ke daftar `_PEMBUAT_LEVEL` di bagian bawah file.

Hal-hal yang perlu diperhatikan:

- Petunjuk dan pembahasan untuk langkah koordinat, plot, dan titik potong **dibuat
  otomatis** dari persamaannya.
- Jika substitusi menghasilkan pecahan (misalnya x = 5,5), pilih nilai lain dan beri
  alasan sebagai petunjuk tambahan: `("x", 5, ["Mengapa x = 5? ..."])`.
- Semua titik bantu dan titik potong harus berada **di dalam rentang** dan **tepat
  di grid** (kelipatan `langkah_grid`).
- `Level` otomatis menolak data yang salah, misalnya titik bantu yang tidak terletak
  pada garisnya atau langkah yang petunjuknya kurang dari 2.
- Setelah mengubah soal, jalankan `python -m unittest` untuk memastikan semuanya
  masih benar. Untuk soal yang **diubah**, sesuaikan juga nilai harapan di tes,
  misalnya `TITIK_POTONG_SOAL` di `tests/test_logika.py`.
- Tampilan Pilih Level dan Hasil Belajar menyesuaikan jumlah level, tetapi dirancang
  paling nyaman untuk 5 level.
