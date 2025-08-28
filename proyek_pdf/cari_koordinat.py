import fitz

# ==========================================================
# GANTI NAMA FILE & NOMOR HALAMAN SESUAI KEBUTUHAN
# ==========================================================
NAMA_FILE_PDF = 'PO_AEON.pdf'
NOMOR_HALAMAN = 1
# ==========================================================

try:
    doc = fitz.open(NAMA_FILE_PDF)
    # Ambil halaman, ingat index dimulai dari 0
    page = doc[NOMOR_HALAMAN - 1] 

    # Dapatkan semua kata beserta posisinya
    words = page.get_text("words")

    print(f"--- Menganalisis Kata di Halaman {NOMOR_HALAMAN} dari file {NAMA_FILE_PDF} ---")
    print("Format: (x: koordinat_x) (y: koordinat_y) Teks_Kata\n")

    for w in words:
        x0, y0, _, _, text = w[:5]
        # Kita bulatkan agar mudah dibaca
        print(f"(x: {int(x0)}) \t(y: {int(y0)}) \t{text}")

    doc.close()

except FileNotFoundError:
    print(f"Error: File '{NAMA_FILE_PDF}' tidak ditemukan. Pastikan nama file sudah benar.")
except IndexError:
    print(f"Error: Halaman {NOMOR_HALAMAN} tidak ada di dalam file.")
except Exception as e:
    print(f"Terjadi error: {e}")