import fitz

print("--- PENCARI KOORDINAT UNTUK HYPERMART ---")
nama_file = "HPM DC BALARAJA.pdf"
# Kata kunci dari PDF Hypermart [cite: 21]
kata_kunci = ["37004705", "15,766.00", "5,297,376.00", "336"]

try:
    with fitz.open(nama_file) as doc:
        halaman = doc[0]
        semua_kata = halaman.get_text("words")
        
        print("\n--- POSISI KOORDINAT X UNTUK KATA KUNCI ---")
        
        for kata in semua_kata:
            try:
                x0, y0, x1, y1, teks = kata[:5]
                if teks in kata_kunci:
                    print(f"Kata: '{teks}' ditemukan di posisi X_awal: {x0:.2f}")
            except ValueError:
                continue

except Exception as e:
    print(f"GAGAL! Terjadi error: {e}")