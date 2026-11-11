"""
Game Edukasi SPLDV Metode Grafik - Kelas VIII SMP
==================================================

Titik masuk program. File ini hanya bertugas:
  1. memeriksa versi Python,
  2. membuat jendela tkinter dan SATU Canvas berukuran 1100x700,
  3. menyerahkan seluruh tampilan kepada App (spldv_game/ui.py),
  4. memastikan data tersimpan ketika jendela ditutup.

Cara menjalankan (dari folder game-spldv-grafik):
    python main.py
"""

import sys
from pathlib import Path

VERSI_PYTHON_MINIMAL = (3, 9)

if sys.version_info < VERSI_PYTHON_MINIMAL:
    print(
        "Program ini membutuhkan Python 3.9 atau lebih baru. "
        "Versi Python Anda: " + sys.version.split()[0]
    )
    sys.exit(1)

import tkinter as tk  # noqa: E402  (diimpor setelah pemeriksaan versi)

from spldv_game.ui import App  # noqa: E402

# ---------------------------------------------------------------------------
# Pengaturan jendela
# ---------------------------------------------------------------------------
JUDUL_JENDELA = "Petualangan SPLDV: Metode Grafik"
LEBAR_LAYAR = 1100
TINGGI_LAYAR = 700
WARNA_LATAR = "#F4F7FB"

FOLDER_PROGRAM = Path(__file__).resolve().parent
FOLDER_DATA = FOLDER_PROGRAM / "data_hasil"  # tempat file CSV hasil belajar


RUANG_TAMBAHAN = 90  # perkiraan tinggi title bar + taskbar Windows


def atur_dpi_jika_layar_kecil():
    """Khusus Windows: bila jendela 1100x700 tidak muat karena skala tampilan
    (mis. laptop 1920x1080 dengan skala 150% terbaca 1280x720), aktifkan mode
    DPI-aware agar jendela memakai piksel asli layar dan tidak terpotong.

    Harus dipanggil SEBELUM tk.Tk() dibuat. Mengembalikan True bila diaktifkan.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        user32 = ctypes.windll.user32
        lebar, tinggi = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        if lebar >= LEBAR_LAYAR + 20 and tinggi >= TINGGI_LAYAR + RUANG_TAMBAHAN:
            return False  # sudah muat, biarkan Windows yang memperbesar
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return True
    except (AttributeError, OSError):
        return False


def posisikan_di_tengah(jendela, lebar, tinggi):
    """Meletakkan jendela kira-kira di tengah layar monitor."""
    jendela.update_idletasks()
    x = max((jendela.winfo_screenwidth() - lebar) // 2, 0)
    y = max((jendela.winfo_screenheight() - tinggi - RUANG_TAMBAHAN) // 2, 0)
    jendela.geometry(f"{lebar}x{tinggi}+{x}+{y}")


def buat_jendela():
    """Membuat jendela utama beserta satu-satunya Canvas permainan."""
    dpi_aware = atur_dpi_jika_layar_kecil()
    jendela = tk.Tk()
    if dpi_aware:
        # Ukuran huruf tetap seperti rancangan (96 DPI) agar tata letak 1100x700 utuh.
        jendela.tk.call("tk", "scaling", 96 / 72)
    jendela.title(JUDUL_JENDELA)
    jendela.resizable(False, False)
    jendela.configure(bg=WARNA_LATAR)
    posisikan_di_tengah(jendela, LEBAR_LAYAR, TINGGI_LAYAR)

    canvas = tk.Canvas(
        jendela,
        width=LEBAR_LAYAR,
        height=TINGGI_LAYAR,
        bg=WARNA_LATAR,
        highlightthickness=0,
        bd=0,
    )
    canvas.pack()
    canvas.focus_set()  # agar input keyboard langsung diterima canvas
    return jendela, canvas


def main():
    jendela, canvas = buat_jendela()
    app = App(canvas, LEBAR_LAYAR, TINGGI_LAYAR, FOLDER_DATA)

    def saat_ditutup():
        """Dipanggil ketika tombol X jendela ditekan."""
        try:
            app.tutup()  # beri kesempatan App menyimpan data terakhir
        finally:
            jendela.destroy()

    jendela.protocol("WM_DELETE_WINDOW", saat_ditutup)
    app.mulai()
    jendela.mainloop()


if __name__ == "__main__":
    main()
