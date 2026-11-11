"""Uji unit untuk spldv_game/penyimpanan.py."""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from spldv_game import data_soal, penyimpanan
from spldv_game.logika import StatusLevel


def mainkan(nomor, pakai_pembahasan_langkah_pertama=False):
    lv = data_soal.ambil_level(nomor)
    s = StatusLevel(lv)
    pertama = True
    while not s.level_selesai:
        lk = s.langkah_aktif
        if pertama and pakai_pembahasan_langkah_pertama:
            s.lihat_pembahasan()
        elif lk.jenis == "isian":
            s.jawab_isian(str(lk.jawaban))
        elif lk.jenis == "pilihan":
            s.jawab_pilihan(lk.benar)
        elif lk.jenis == "plot":
            s.klik_titik(*lk.titik[0])
            s.klik_titik(*lk.titik[1])
        else:
            s.klik_titik(*lv.titik_potong)
        pertama = False
        s.lanjut()
    return s


class TestPenyimpanan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "data_hasil"

    def tearDown(self):
        self.tmp.cleanup()

    def test_buat_baris(self):
        s = mainkan(1, pakai_pembahasan_langkah_pertama=True)
        baris = penyimpanan.buat_baris(" Siti ", s, datetime(2026, 11, 11, 8, 30))
        self.assertEqual(baris["waktu"], "2026-11-11 08:30:00")
        self.assertEqual(baris["nama"], "Siti")
        self.assertEqual((baris["level"], baris["skor"], baris["skor_maks"]), (1, 70, 80))
        self.assertEqual(baris["tahap_perlu_latihan"], "Menentukan titik koordinat")
        self.assertIn("1. Menentukan titik koordinat (isian): salah 0, petunjuk 0, "
                      "pembahasan ya, poin 0", baris["rincian_langkah"])

    def test_simpan_dua_kali_dan_baca(self):
        for nomor in (1, 2):
            path = penyimpanan.simpan_hasil(
                self.folder, penyimpanan.buat_baris("Siti", mainkan(nomor)))
        isi = path.read_bytes()
        self.assertTrue(isi.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(isi.count(b"\xef\xbb\xbf"), 1)  # BOM hanya sekali
        baris_pertama = isi.decode("utf-8-sig").splitlines()[0]
        self.assertEqual(baris_pertama, ";".join(penyimpanan.KOLOM_CSV))

        data = penyimpanan.baca_hasil(self.folder)
        self.assertEqual([d["level"] for d in data], ["1", "2"])
        self.assertEqual(data[1]["judul"], "Siapa yang Benar?")

    def test_hasil_terbaik(self):
        penyimpanan.simpan_hasil(self.folder, penyimpanan.buat_baris(
            "Siti", mainkan(1, pakai_pembahasan_langkah_pertama=True)))
        penyimpanan.simpan_hasil(self.folder, penyimpanan.buat_baris("Siti", mainkan(1)))
        penyimpanan.simpan_hasil(self.folder, penyimpanan.buat_baris("Budi", mainkan(2)))
        terbaik = penyimpanan.hasil_terbaik_pemain(self.folder, "siti")
        self.assertEqual(list(terbaik), [1])
        self.assertEqual((terbaik[1]["skor"], terbaik[1]["bintang"], terbaik[1]["tahap"]),
                         (80, 3, []))

    def test_nama_seperti_rumus_excel(self):
        baris = penyimpanan.buat_baris("=1+1", mainkan(1))
        self.assertEqual(baris["nama"], "'=1+1")

    def test_folder_belum_ada(self):
        self.assertEqual(penyimpanan.baca_hasil(self.folder), [])


if __name__ == "__main__":
    unittest.main()
