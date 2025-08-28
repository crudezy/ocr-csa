import fitz
import re # Impor library regular expression
import json

# =================================================================
#                    PARSER UNTUK VENDOR: AEON 
# =================================================================
def parse_po_aeon(doc):
    """
    Versi definitif dan final untuk AEON, termasuk pembersihan nomor
    urut dari awal deskripsi.
    """
    KOLOM = {
        "deskripsi": (40, 195), "uom_etc":   (230, 320),
        "barcode":   (320, 390), "qty":       (395, 490),
        "harga":     (570, 635)
    }
    semua_item = []

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

            item = {'sku': barcode}
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
            
            # Gabungkan semua bagian deskripsi
            deskripsi_kotor = ' '.join(deskripsi_parts_ini + deskripsi_parts_bawah)
            
            # --- FINAL TOUCH: Hapus nomor urut dari deskripsi ---
            parts = deskripsi_kotor.strip().split(' ', 1)
            if len(parts) > 1 and parts[0].isdigit():
                item['deskripsi'] = parts[1] # Ambil bagian kedua (setelah angka)
            else:
                item['deskripsi'] = deskripsi_kotor # Jika tidak ada angka, ambil semua
            
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

# Anda bisa menambahkan Staf Ahli lain di sini nanti
# def parse_po_lotte(halaman_pdf):
#     ...

# =================================================================
#           PARSER UNTUK VENDOR: TOSERBA YOGYA/GRIYA 
# =================================================================
def parse_po_yogya(doc):
    """
    Versi final dengan perbaikan rentang koordinat harga yang presisi.
    """
    KOLOM = {
        "sku":       (50, 110),
        "deskripsi": (210, 440),
        "qty":       (442, 465),
        "uom":       (466, 515),
        # --- RENTANG HARGA DIPERBAIKI ---
        # Dipersempit agar tidak tumpang tindih dengan kolom diskon
        "harga":     (515, 560) 
    }
    semua_item = []
    
    for page in doc:
        semua_kata = page.get_text("words")
        batas_atas_y, batas_bawah_y = 0, float('inf')
        
        for kata in semua_kata:
            teks_kata = kata[4] if len(kata) > 4 else ''
            y0, y1 = kata[1], kata[3]
            
            if teks_kata == "Description" and y0 < 300:
                batas_atas_y = y1
            if teks_kata == "TOTAL" and y0 > 300:
                batas_bawah_y = y0
                break 
        
        if batas_atas_y == 0 and not semua_item:
            continue
        elif batas_atas_y == 0 and semua_item:
            batas_atas_y = 0 

        kata_dalam_tabel = [k for k in semua_kata if batas_atas_y < k[1] < batas_bawah_y]
        
        baris_logis = {}
        for kata in kata_dalam_tabel:
            y_pos = round(kata[1] / 10.0) * 10.0
            if y_pos not in baris_logis: baris_logis[y_pos] = []
            baris_logis[y_pos].append(kata)

        for y in sorted(baris_logis.keys()):
            kata_di_baris = sorted(baris_logis[y], key=lambda k: k[0])
            
            if not kata_di_baris or not (kata_di_baris[0][4].strip().isdigit() and kata_di_baris[0][0] < 50): 
                continue
            
            item, deskripsi_parts, uom_parts = {}, [], []
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
    Versi final parser SAT dengan pembersihan nomor urut dari deskripsi.
    """
    KOLOM = {
        "qty":   (200, 250),
        "harga": (340, 400)
    }
    semua_item = []

    for page in doc:
        semua_kata = page.get_text("words")
        batas_atas_y, batas_bawah_y = 0, float('inf')
        
        for kata in semua_kata:
            teks_kata = kata[4] if len(kata) > 4 else ''
            y0, y1 = kata[1], kata[3]
            if teks_kata == "NAME" and y0 < 150:
                batas_atas_y = y1
            if teks_kata == "INVOICE" and y0 > 150:
                batas_bawah_y = y0
                break 
        
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
                        
                        # --- PERBAIKAN: Hapus nomor urut dari deskripsi ---
                        deskripsi_final = ' '.join(deskripsi_parts).strip()
                        parts = deskripsi_final.split(' ', 1)
                        if len(parts) > 1 and parts[0].isdigit():
                            item_terkini['deskripsi'] = parts[1]
                        else:
                            item_terkini['deskripsi'] = deskripsi_final
                        # ----------------------------------------------------

                        if 'qty' in item_terkini and 'harga' in item_terkini:
                            item_terkini.setdefault('uom', 'PCS')
                            item_terkini.setdefault('discount', 0.0)
                            semua_item.append(item_terkini)
                    
                    item_terkini = {}
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

        # Lakukan pembersihan yang sama untuk item terakhir di halaman
        if item_terkini.get('sku'):
            
            # --- PERBAIKAN: Hapus nomor urut dari deskripsi ---
            deskripsi_final = ' '.join(deskripsi_parts).strip()
            parts = deskripsi_final.split(' ', 1)
            if len(parts) > 1 and parts[0].isdigit():
                item_terkini['deskripsi'] = parts[1]
            else:
                item_terkini['deskripsi'] = deskripsi_final
            # ----------------------------------------------------

            if 'qty' in item_terkini and 'harga' in item_terkini:
                item_terkini.setdefault('uom', 'PCS')
                item_terkini.setdefault('discount', 0.0)
                semua_item.append(item_terkini)

    return semua_item

# =================================================================
#           PARSER UNTUK VENDOR: LOTTE MART (FINAL)
# =================================================================
def parse_po_lotte(doc):
    """
    Versi final parser Lotte dengan perbaikan pada penggabungan UOM.
    """
    KOLOM = {
        "deskripsi": (150, 270),
        "uom":       (410, 460),
        "qty":       (460, 490),
        "harga":     (490, 530)
    }
    semua_item = []
    
    for page in doc:
        baris_logis = {}
        for kata in page.get_text("words"):
            y_pos = round(kata[1] / 10.0) * 10.0
            if y_pos not in baris_logis: baris_logis[y_pos] = []
            baris_logis[y_pos].append(kata)

        kunci_y_terurut = sorted(baris_logis.keys())

        for i, y in enumerate(kunci_y_terurut):
            kata_di_baris_ini = sorted(baris_logis[y], key=lambda k: k[0])
            barcode = next((k[4] for k in kata_di_baris_ini if k[0] < 100 and len(k[4]) >= 12 and k[4].isdigit()), None)

            if not barcode:
                continue

            item = {'sku': barcode}
            
            deskripsi_parts = []
            uom_parts = [] # <-- 1. Siapkan list kosong untuk UOM
            
            baris_untuk_diperiksa = kunci_y_terurut[max(0, i - 2) : i]

            for y_prev in baris_untuk_diperiksa:
                for kata in baris_logis[y_prev]:
                    x0, teks = kata[0], kata[4]
                    label = next((nama for nama, (x_awal, x_akhir) in KOLOM.items() if x_awal <= x0 < x_akhir), None)

                    if label == 'deskripsi':
                        deskripsi_parts.append(teks)
                    elif label == 'uom':
                        uom_parts.append(teks) # <-- 2. Kumpulkan semua bagian UOM
                    elif label == 'qty' and 'qty' not in item:
                        item['qty'] = int(float(teks.replace('.', '')))
                    elif label == 'harga' and 'harga' not in item:
                        harga_bersih = teks.replace('.', '').replace(',', '.')
                        item['harga'] = float(harga_bersih)

            item['deskripsi'] = ' '.join(deskripsi_parts)
            if uom_parts: # <-- 3. Gabungkan semua bagian UOM
                item['uom'] = ' '.join(uom_parts)

            if 'qty' in item and 'harga' in item:
                item.setdefault('discount', 0.0)
                item.setdefault('uom', 'PCS')
                semua_item.append(item)

    return semua_item