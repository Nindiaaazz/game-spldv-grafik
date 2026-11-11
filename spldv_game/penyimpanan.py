"""
Penyimpanan hasil belajar siswa ke file CSV.

- Pemisah kolom titik koma (;) dan encoding utf-8-sig, agar langsung rapi
  ketika dibuka dengan Microsoft Excel (pengaturan Indonesia).
- Setiap level yang selesai dimainkan menambah SATU baris (tidak menimpa).
- Hanya memakai modul bawaan: csv, datetime, pathlib. Tanpa tkinter.
"""

import csv
from datetime import datetime
from pathlib import Path

NAMA_FILE = "hasil_belajar.csv"
PEMISAH = ";"
PEMISAH_TAHAP = ", "

KOLOM_CSV = [
    "waktu",
    "nama",
    "level",
    "judul",
    "indikator",
    "skor",
    "skor_maks",
    "bintang",
    "jumlah_salah",
    "jumlah_petunjuk",
    "tahap_perlu_latihan",
    "rincian_langkah",
]


def path_file(folder_data):
    return Path(folder_data) / NAMA_FILE


def _aman_excel(teks):
    """Mencegah teks seperti "=..." dibaca Excel sebagai rumus."""
    teks = str(teks)
    return "'" + teks if teks[:1] in ("=", "+", "-", "@") else teks


def rincian_langkah(status):
    """Rincian salah/petunjuk/pembahasan/poin setiap langkah dalam satu teks."""
    bagian = []
    for i, (lk, cat) in enumerate(zip(status.level.langkah, status.catatan), start=1):
        bagian.append(
            f"{i}. {lk.tahap} ({lk.jenis}): salah {cat.salah}, "
            f"petunjuk {cat.petunjuk_dipakai}, "
            f"pembahasan {'ya' if cat.lihat_pembahasan else 'tidak'}, poin {cat.poin}"
        )
    return " | ".join(bagian)


def ringkasan(status):
    """Ringkasan hasil satu level (dipakai untuk 'hasil terbaik')."""
    return {
        "skor": status.skor,
        "skor_maks": status.skor_maks,
        "bintang": status.bintang,
        "tahap": list(status.tahap_perlu_latihan),
    }


def buat_baris(nama, status, waktu=None):
    """Menyusun satu baris CSV (dict) dari StatusLevel yang sudah selesai."""
    waktu = waktu or datetime.now()
    lv = status.level
    return {
        "waktu": waktu.strftime("%Y-%m-%d %H:%M:%S"),
        "nama": _aman_excel(nama.strip()),
        "level": lv.nomor,
        "judul": lv.judul,
        "indikator": lv.indikator,
        "skor": status.skor,
        "skor_maks": status.skor_maks,
        "bintang": status.bintang,
        "jumlah_salah": status.jumlah_salah,
        "jumlah_petunjuk": status.jumlah_petunjuk,
        "tahap_perlu_latihan": PEMISAH_TAHAP.join(status.tahap_perlu_latihan),
        "rincian_langkah": rincian_langkah(status),
    }


def simpan_hasil(folder_data, baris):
    """Menambahkan satu baris ke CSV (membuat file + header bila belum ada).

    Mengembalikan path file. Dapat memunculkan OSError/PermissionError,
    misalnya bila file sedang dibuka di Excel.
    """
    path = path_file(folder_data)
    path.parent.mkdir(parents=True, exist_ok=True)
    baru = not path.exists() or path.stat().st_size == 0
    # BOM hanya ditulis sekali di awal file baru.
    encoding = "utf-8-sig" if baru else "utf-8"
    with open(path, "a", newline="", encoding=encoding) as f:
        penulis = csv.DictWriter(f, fieldnames=KOLOM_CSV, delimiter=PEMISAH)
        if baru:
            penulis.writeheader()
        penulis.writerow({k: baris.get(k, "") for k in KOLOM_CSV})
    return path


def baca_hasil(folder_data):
    """Membaca semua baris hasil sebagai list of dict (list kosong bila belum ada)."""
    path = path_file(folder_data)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=PEMISAH))


def perbarui_terbaik(kamus, nomor, data):
    """Menyimpan data ke kamus[nomor] bila skornya lebih tinggi. True jika berubah."""
    lama = kamus.get(nomor)
    if lama is None or data["skor"] > lama["skor"]:
        kamus[nomor] = data
        return True
    return False


def hasil_terbaik_pemain(folder_data, nama):
    """Hasil terbaik per level untuk satu nama, dibaca dari CSV."""
    target = _aman_excel(nama.strip()).lower()
    hasil = {}
    for baris in baca_hasil(folder_data):
        if (baris.get("nama") or "").strip().lower() != target:
            continue
        try:
            nomor = int(baris["level"])
            data = {
                "skor": int(baris["skor"]),
                "skor_maks": int(baris["skor_maks"]),
                "bintang": int(baris["bintang"]),
                "tahap": [t for t in (baris.get("tahap_perlu_latihan") or "")
                          .split(PEMISAH_TAHAP) if t.strip()],
            }
        except (KeyError, TypeError, ValueError):
            continue  # baris rusak dilewati
        perbarui_terbaik(hasil, nomor, data)
    return hasil
