import fitz
import re # Impor library regular expression
import json

# =================================================================
#                    PARSER UNTUK VENDOR: AEON 
# =================================================================
def parse_po_aeon(doc):
    """
    Versi definitif dan final untuk AEON, termasuk pembersihan nomor
    urut dan penambahan nomor PO di setiap item.
    """
    KOLOM = {
        "deskripsi": (40, 195), "uom_etc":   (230, 320),
        "barcode":   (320, 390), "qty":       (395, 490),
        "harga":     (570, 635), "po_number": (723, 760) # Jangkauan diperbaiki
    }
    semua_item = []
    nomor_po_dokumen = None # Variabel untuk menyimpan Nomor PO

    # Langkah 1: Cari Nomor PO dari keseluruhan dokumen terlebih dahulu
    for page in doc:
        for kata in page.get_text("words"):
            try:
                x0, y0, x1, y1, teks = kata[:5]
                k = KOLOM["po_number"]
                # Cek koordinat X dan Y
                if k[0] <= x0 < k[1] and 35 <= y0 < 45: 
                    nomor_po_dokumen = teks
                    break # Hentikan setelah ditemukan
            except (ValueError, IndexError): continue
        if nomor_po_dokumen: break
    
    # Langkah 2: Proses setiap item dan tambahkan Nomor PO yang sudah ditemukan
    for page in doc:
        baris_logis = {}
        for kata in page.get_text("words"):
            y_pos = round(kata[1] / 10.0) * 10.0
            if y_pos not in baris_logis: baris_logis[y_pos] = []
            baris_logis[y_pos].append(kata)

        kunci_y_terurut = sorted(baris_logis.keys())
        
        i = 0
        while i < len(kunci_y_terurut):
            y = kunci_y_terurut[i]
            kata_di_baris_ini = sorted(baris_logis[y], key=lambda k: k[0])

            barcode = next((k[4] for k in kata_di_baris_ini if KOLOM['barcode'][0] <= k[0] < KOLOM['barcode'][1] and len(k[4]) == 13 and k[4].isdigit()), None)

            if not barcode:
                i += 1
                continue

            # Buat item baru dan langsung tambahkan nomor PO
            item = {'sku': barcode, 'po_number': nomor_po_dokumen}
            
            deskripsi_parts_ini, uom_parts = [], []

            for kata in kata_di_baris_ini:
                try:
                    x0, _, _, _, teks = kata[:5]
                    label = next((nama for nama, (x_awal, x_akhir) in KOLOM.items() if x_awal <= x0 < x_akhir), None)
                    if label == 'qty': item['qty'] = float(teks.replace(',', ''))
                    elif label == 'harga': item['harga'] = float(teks.replace(',', ''))
                    elif label == 'uom_etc': uom_parts.append(teks)
                    elif label == 'deskripsi': deskripsi_parts_ini.append(teks)
                except (ValueError, IndexError): continue
            
            deskripsi_parts_bawah = []
            if i + 1 < len(kunci_y_terurut):
                y_berikutnya = kunci_y_terurut[i + 1]
                kata_di_baris_berikutnya = baris_logis[y_berikutnya]
                is_baris_lanjutan = not any(KOLOM['barcode'][0] <= k[0] < KOLOM['barcode'][1] and len(k[4]) == 13 and k[4].isdigit() for k in kata_di_baris_berikutnya)
                if is_baris_lanjutan:
                    deskripsi_parts_bawah = [k[4] for k in kata_di_baris_berikutnya if KOLOM['deskripsi'][0] <= k[0] < KOLOM['deskripsi'][1]]
                    i += 1
            
            deskripsi_kotor = ' '.join(deskripsi_parts_ini + deskripsi_parts_bawah)
            
            parts = deskripsi_kotor.strip().split(' ', 1)
            if len(parts) > 1 and parts[0].isdigit():
                item['deskripsi'] = parts[1]
            else:
                item['deskripsi'] = deskripsi_kotor
            
            if uom_parts:
                uom_final = "PCS"
                uom_dikenali = ["PCS", "EACH", "CTN", "PACK", "BOX", "CARTON"]
                for part in uom_parts:
                    if part.upper() in uom_dikenali:
                        uom_final = part.upper(); break
                item['uom'] = uom_final

            if 'qty' in item and 'harga' in item:
                item.setdefault('discount', 0.0); item.setdefault('uom', 'PCS')
                semua_item.append(item)
            
            i += 1
    
    return semua_item

def parse_po_hypermart(halaman_pdf):
    print("Parser Hypermart belum dibuat.")
    return {"header": {}, "items": []}


# =================================================================
#           PARSER UNTUK VENDOR: TOSERBA YOGYA/GRIYA 
# =================================================================
def parse_po_yogya(doc):
    """
    Versi gabungan final: Memindai semua item dan menangani 
    nomor PO yang berbeda di setiap halaman.
    """
    KOLOM = {
        # --- PERBAIKAN: Spasi ekstra dihapus dari 'sku' ---
        "sku":       (50, 110),
        "deskripsi": (210, 440),
        "qty":       (442, 465),
        "uom":       (466, 515),
        "harga":     (515, 560) 
    }
    semua_item = []

    # Proses setiap halaman secara terpisah
    for page in doc:
        nomor_po_halaman_ini = "TIDAK DITEMUKAN"
        semua_kata_halaman = page.get_text("words")

        # --- LANGKAH 1: Cari Nomor PO untuk HALAMAN INI (dari kode baru) ---
        for kata in semua_kata_halaman:
            try:
                x0, y0, _, _, teks = kata[:5]
                # Cari kata yang dimulai dengan 'CR' di area koordinat yang benar
                if 40 <= x0 < 100 and 95 <= y0 < 105 and teks.startswith("CR"):
                    nomor_po_halaman_ini = teks
                    break 
            except (ValueError, IndexError):
                continue

        # --- LANGKAH 2: Gunakan logika parsing tabel dari kode lama yang sudah terbukti ---
        batas_atas_y, batas_bawah_y = 0, float('inf')
        for kata in semua_kata_halaman:
            teks_kata = kata[4] if len(kata) > 4 else ''
            y0, y1 = kata[1], kata[3]
            if teks_kata == "Description" and y0 < 300:
                batas_atas_y = y1
            if "TOTAL" in teks_kata and y0 > 300:
                batas_bawah_y = y0
                break 
        
        # Logika untuk menangani halaman lanjutan tanpa header
        if batas_atas_y == 0 and not semua_item:
            continue
        elif batas_atas_y == 0 and semua_item:
            batas_atas_y = 0 # Untuk halaman 2 dst, mulai pindai dari paling atas

        kata_dalam_tabel = [k for k in semua_kata_halaman if batas_atas_y < k[1] < batas_bawah_y]
        
        baris_logis = {}
        for kata in kata_dalam_tabel:
            y_pos = round(kata[1] / 10.0) * 10.0
            if y_pos not in baris_logis: baris_logis[y_pos] = []
            baris_logis[y_pos].append(kata)

        for y in sorted(baris_logis.keys()):
            kata_di_baris = sorted(baris_logis[y], key=lambda k: k[0])
            
            if not kata_di_baris or not (kata_di_baris[0][4].strip().isdigit() and kata_di_baris[0][0] < 50): 
                continue
            
            # --- LANGKAH 3: Gabungkan po_number ke setiap item ---
            item = {'po_number': nomor_po_halaman_ini}
            deskripsi_parts, uom_parts = [], []

            for kata in kata_di_baris:
                try:
                    x0, teks = kata[0], kata[4]
                    label = next((nama for nama, (x_awal, x_akhir) in KOLOM.items() if x_awal <= x0 < x_akhir), None)
                    
                    if label == 'sku': item['sku'] = teks
                    elif label == 'qty': item['qty'] = int(float(teks))
                    elif label == 'harga': item['harga'] = float(teks.replace(',', ''))
                    elif label == 'deskripsi': deskripsi_parts.append(teks)
                    elif label == 'uom': uom_parts.append(teks)
                except (ValueError, IndexError): 
                    continue
            
            if deskripsi_parts: item['deskripsi'] = ' '.join(deskripsi_parts).split('_')[0].strip()
            if uom_parts: item['uom'] = ' '.join(uom_parts)

            if 'sku' in item and 'qty' in item and 'harga' in item:
                item.setdefault('discount', 0.0)
                if 'uom' not in item or not item['uom']: item['uom'] = 'PCS'
                semua_item.append(item)
    
    return semua_item


# =================================================================
#           PARSER UNTUK VENDOR: SAT (ALFAMART)
# =================================================================
def parse_po_sat(doc):
    """
    Versi final parser SAT dengan penambahan po_number yang akurat menggunakan koordinat.
    """
    KOLOM = {
        "qty":   (200, 250),
        "harga": (340, 400)
    }
    semua_item = []
    nomor_po_dokumen = "TIDAK DITEMUKAN"
    
    # Proses setiap halaman (meskipun SAT biasanya hanya 1 halaman)
    for page in doc:
        semua_kata = page.get_text("words")

        # --- LANGKAH 1: Cari Nomor PO untuk HALAMAN INI menggunakan KOORDINAT ---
        # Berdasarkan output Anda: (x: 490) (y: 50) BZ01POH25011109
        for kata in semua_kata:
            try:
                x0, y0, _, _, teks = kata[:5]
                # Cari kata di area kanan atas yang terlihat seperti Nomor PO
                if 485 < x0 < 550 and 45 < y0 < 60 and teks.startswith("BZ"):
                    nomor_po_dokumen = teks
                    break # Hentikan setelah ditemukan
            except (ValueError, IndexError):
                continue
        
        # --- LANGKAH 2: Ekstrak item seperti sebelumnya ---
        batas_atas_y, batas_bawah_y = 0, float('inf')
        for kata in semua_kata:
            try:
                teks_kata = kata[4] if len(kata) > 4 else ''
                y0, y1 = kata[1], kata[3]
                if teks_kata == "NAME" and y0 < 150:
                    batas_atas_y = y1
                if teks_kata == "INVOICE" and y0 > 150:
                    batas_bawah_y = y0
                    break 
            except (ValueError, IndexError): continue
        
        if batas_atas_y == 0: continue

        kata_dalam_tabel = [k for k in semua_kata if batas_atas_y < k[1] < batas_bawah_y]

        item_terkini = {}
        deskripsi_parts = []
        kata_terurut = sorted(kata_dalam_tabel, key=lambda k: (k[1], k[0]))

        for kata in kata_terurut:
            try:
                x0, _, _, _, teks = kata[:5]
                
                if teks.startswith('#') and len(teks) < 5:
                    if item_terkini.get('sku'):
                        deskripsi_final = ' '.join(deskripsi_parts).strip()
                        parts = deskripsi_final.split(' ', 1)
                        if len(parts) > 1 and parts[0].isdigit():
                            item_terkini['deskripsi'] = parts[1]
                        else:
                            item_terkini['deskripsi'] = deskripsi_final

                        if 'qty' in item_terkini and 'harga' in item_terkini:
                            item_terkini.setdefault('uom', 'PCS')
                            item_terkini.setdefault('discount', 0.0)
                            semua_item.append(item_terkini)
                    
                    # --- LANGKAH 3: Buat item baru dengan Nomor PO ---
                    item_terkini = {'po_number': nomor_po_dokumen}
                    deskripsi_parts = []
                    continue

                if len(teks.strip()) == 13 and teks.strip().isdigit():
                    item_terkini['sku'] = teks.strip()
                    continue

                label = next((nama for nama, (x_awal, x_akhir) in KOLOM.items() if x_awal <= x0 < x_akhir), None)

                if label:
                    angka_bersih = re.sub(r'[^\d.]', '', teks)
                    if not angka_bersih: continue

                    if label == 'qty':
                        item_terkini['qty'] = int(float(angka_bersih))
                    elif label == 'harga':
                        item_terkini['harga'] = float(angka_bersih)
                elif x0 < KOLOM['qty'][0]:
                    deskripsi_parts.append(teks)
            
            except (ValueError, IndexError):
                continue

        if item_terkini.get('sku'):
            deskripsi_final = ' '.join(deskripsi_parts).strip()
            parts = deskripsi_final.split(' ', 1)
            if len(parts) > 1 and parts[0].isdigit():
                item_terkini['deskripsi'] = parts[1]
            else:
                item_terkini['deskripsi'] = deskripsi_final

            if 'qty' in item_terkini and 'harga' in item_terkini:
                item_terkini.setdefault('uom', 'PCS')
                item_terkini.setdefault('discount', 0.0)
                semua_item.append(item_terkini)

    return semua_item

# =================================================================
#           PARSER UNTUK VENDOR: LOTTE MART
# =================================================================
# =================================================================
def parse_po_lotte(doc):
    """
    Versi final: Menggunakan logika item dari KODE LAMA ANDA yang sudah terbukti, 
    digabungkan dengan pencarian po_number berbasis KOORDINAT yang akurat.
    """
    KOLOM = {
        "deskripsi": (150, 270),
        "uom":       (410, 460),
        "qty":       (460, 490),
        "harga":     (490, 530)
    }
    semua_item = []
    
    for page in doc:
        nomor_po_dokumen = "TIDAK DITEMUKAN"
        semua_kata = page.get_text("words")

        # --- LANGKAH 1: Cari Nomor PO menggunakan KOORDINAT (Logika Baru yang Akurat) ---
        for kata in semua_kata:
            try:
                x0, y0, _, _, teks = kata[:5]
                # Berdasarkan analisis koordinat (x: 413, y: 120) atau (x: 432, y: 267)
                is_po_at_top = (410 < x0 < 450 and 115 < y0 < 125)
                is_po_in_table = (430 < x0 < 480 and 260 < y0 < 270)
                
                if (is_po_at_top or is_po_in_table) and len(teks) > 10 and teks.isdigit():
                    nomor_po_dokumen = teks
                    break 
            except (ValueError, IndexError):
                continue
        
        # --- LANGKAH 2: Gunakan logika parsing tabel dari KODE LAMA ANDA ---
        baris_logis = {}
        for kata in semua_kata:
            try:
                y_pos = round(kata[1] / 10.0) * 10.0
                if y_pos not in baris_logis: baris_logis[y_pos] = []
                baris_logis[y_pos].append(kata)
            except IndexError: continue

        kunci_y_terurut = sorted(baris_logis.keys())

        for i, y in enumerate(kunci_y_terurut):
            kata_di_baris_ini = sorted(baris_logis[y], key=lambda k: k[0])
            barcode = next((k[4] for k in kata_di_baris_ini if k[0] < 100 and len(k[4]) >= 12 and k[4].isdigit()), None)

            if not barcode:
                continue
            
            # Buat item baru dan langsung tambahkan Nomor PO yang sudah ditemukan
            item = {'sku': barcode, 'po_number': nomor_po_dokumen}
            
            deskripsi_parts = []
            uom_parts = [] 
            
            # Menggunakan kembali logika "melihat ke baris atas" dari kode lama Anda
            baris_untuk_diperiksa = kunci_y_terurut[max(0, i - 2) : i]

            for y_prev in baris_untuk_diperiksa:
                for kata in baris_logis[y_prev]:
                    try:
                        x0, _, _, _, teks = kata[:5]
                        label = next((nama for nama, (x_awal, x_akhir) in KOLOM.items() if x_awal <= x0 < x_akhir), None)

                        if label == 'deskripsi':
                            deskripsi_parts.append(teks)
                        elif label == 'uom':
                            uom_parts.append(teks)
                        elif label == 'qty' and 'qty' not in item:
                            item['qty'] = int(float(teks.replace('.', '')))
                        elif label == 'harga' and 'harga' not in item:
                            harga_bersih = teks.replace('.', '').replace(',', '.')
                            item['harga'] = float(harga_bersih)
                    except (ValueError, IndexError): continue

            item['deskripsi'] = ' '.join(deskripsi_parts)
            if uom_parts:
                item['uom'] = ' '.join(uom_parts)

            if 'qty' in item and 'harga' in item:
                item.setdefault('discount', 0.0)
                item.setdefault('uom', 'PCS')
                semua_item.append(item)

    return semua_item