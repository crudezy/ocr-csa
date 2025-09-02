import fitz
import json
import os
from flask import Flask, request, render_template, jsonify
import parsers
import pyodbc

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Konfigurasi Database Tetap di Sini ---
SERVER = 'CRUDE'
DATABASE = 'parse-csan'
USERNAME = 'sa'
PASSWORD = 'crudezy' # Pastikan ini password Anda yang benar

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file yang diupload"}), 400
    
    file = request.files['file']
    vendor = request.form.get('vendor')
    
    if not file or not vendor:
        return jsonify({"error": "File atau Vendor belum dipilih"}), 400

    if file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        hasil_akhir = []
        doc = None
        try:
            doc = fitz.open(filepath)
            
            if vendor == "AEON":
                hasil_akhir = parsers.parse_po_aeon(doc)
            elif vendor == "TOSERBA YOGYA/GRIYA": 
                hasil_akhir = parsers.parse_po_yogya(doc)
            elif vendor == "SAT":
                hasil_akhir = parsers.parse_po_sat(doc)
            elif vendor == "LOTTE":
                hasil_akhir = parsers.parse_po_lotte(doc)
            else:
                return jsonify({"error": f"Tidak ada parser untuk vendor '{vendor}'"}), 400
            
            if hasil_akhir:
                print(f"Menyimpan {len(hasil_akhir)} item ke database...")
                cnxn = None
                try:
                    # --- PERUBAHAN UTAMA: Koneksi Langsung ke File Driver ---
                    connection_string = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={SERVER};"
                        f"DATABASE={DATABASE};"
                        f"UID={USERNAME};"
                        f"PWD={PASSWORD};"
                    )
                    cnxn = pyodbc.connect(connection_string)
                    # --------------------------------------------------------
                    
                    cursor = cnxn.cursor()
                    
                    sql_insert_query = """
                        INSERT INTO PurchaseOrderItems (vendor, source_file, sku, deskripsi, qty, uom, harga, discount, po_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """
                    
                    for item in hasil_akhir:
                        cursor.execute(sql_insert_query, 
                                       vendor, file.filename, item.get('sku'),
                                       item.get('deskripsi'), item.get('qty'),
                                       item.get('uom'), item.get('harga'),
                                       item.get('discount', 0.0), item.get('po_number'))
                    cnxn.commit()
                    print("SUKSES: Data berhasil disimpan ke database.")
                except pyodbc.Error as db_error:
                    print(f"ERROR DATABASE: {db_error}")
                finally:
                    if cnxn: cnxn.close()

        except Exception as e:
            return jsonify({"error": f"Terjadi kesalahan saat memproses PDF: {str(e)}"}), 500
        finally:
            if doc: doc.close()
            if os.path.exists(filepath): os.remove(filepath)
            
        return jsonify(hasil_akhir)
    
    return jsonify({"error": "File harus dalam format PDF"}), 400

@app.route('/details')
def details_page():
    return render_template('details.html')

if __name__ == '__main__':
    app.run(debug=True)