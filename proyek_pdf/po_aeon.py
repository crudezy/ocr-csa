import fitz
import json

def parse_po_aeon(halaman_pdf):
    """
    Versi final yang mengekstrak header dan item, lalu menambahkan
    nomor_po ke setiap item.
    """
    print("Memulai parser AEON (Menambahkan No. PO ke setiap item)...")
    
    # Koordinat untuk data header dan item
    KOLOM = {
        "nomor_po":  (720, 750, 35, 45),    # x0, x1, y0, y1
        "deskripsi": (50, 215),
        "uom":       (225, 280),
        "barcode":   (320, 350),
        "qty":       (398, 428),
        "harga":     (570, 610)
    }

    hasil = {
        "header": {},
        "items": []
    }
    
    semua_kata = halaman_pdf.get_text("words")
    nomor_po_dokumen = "TIDAK DITEMUKAN"

    # --- Ekstrak Nomor PO dari Header ---
    for kata in semua_kata:
        try:
            x0, y0, x1, y1, teks = kata[:5]
            k = KOLOM["nomor_po"]
            if k[0] < x0 < k[1] and k[2] < y0 < k[3]:
                nomor_po_dokumen = teks
                break # Hentikan setelah ketemu
        except ValueError: continue
    
    hasil["header"]["nomor_po"] = nomor_po_dokumen
    
    # --- Ekstrak data Items (Metode Gunting) ---
    batas_atas_y, batas_bawah_y = 0, float('inf')
    for kata in semua_kata:
        _, y0, _, y1, teks = kata[:5]
        if "BARCODE" in teks: batas_atas_y = y1
        if "TOTAL" == teks.strip() and y0 > 300:
            batas_bawah_y = y0
            break
    
    kata_dalam_tabel = [k for k in semua_kata if batas_atas_y < k[1] < batas_bawah_y]

    # ... (Logika parsing item tetap sama seperti sebelumnya) ...
    baris_logis = {}
    for kata in kata_dalam_tabel:
        y_pos = round(kata[1] / 10.0) * 10.0
        if y_pos not in baris_logis: baris_logis[y_pos] = []
        baris_logis[y_pos].append(kata)

    items = []
    # ... (Sisa logika parsing item yang kompleks ada di sini) ...
    # (Untuk singkatnya, logika ini tidak ditampilkan lagi, tapi ada di kode lengkap Anda)

    final_items = [] # Ganti dengan hasil parsing item Anda
            
    # --- LANGKAH PENTING: Tambahkan nomor PO ke setiap item ---
    for item in final_items:
        item['nomor_po'] = nomor_po_dokumen

    hasil["items"] = final_items
    
    return hasil

# Parser lain tetap sama
def parse_po_hypermart(halaman_pdf):
    print("Parser Hypermart belum dibuat.")
    return {"header": {}, "items": []}