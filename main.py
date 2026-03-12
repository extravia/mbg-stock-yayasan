from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import mysql.connector
from mysql.connector import pooling

app = FastAPI()

db_pool = pooling.MySQLConnectionPool(
    pool_name="mbg_pool", pool_size=5,
    host="localhost", user="root", password="", database="db_mbg_yayasan"
)

def get_db_conn():
    return db_pool.get_connection()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM stok_barang")
        items = cursor.fetchall()
        cursor.execute("SELECT * FROM riwayat_stok ORDER BY waktu DESC LIMIT 10")
        logs = cursor.fetchall()
        
        rows = "".join([f"<tr><td>{i['nama_bahan']}</td><td><b>{i['jumlah_stok']}</b></td><td>{i['satuan']}</td></tr>" for i in items])
        options = "".join([f'<option value="{i["nama_bahan"]}">{i["nama_bahan"]}</option>' for i in items])
        log_rows = "".join([f"<tr><td>{l['waktu'].strftime('%H:%M')}</td><td>{l['nama_bahan']}</td><td>{l['aksi']}</td><td>{l['jumlah']}</td><td>{l['oleh_siapa']}</td></tr>" for l in logs])

        return f"""
        <html>
            <head>
                <title>Sistem MBG</title>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; background: #f4f7f6; }}
                    .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }}
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }}
                    th, td {{ padding: 10px; border-bottom: 1px solid #eee; text-align: left; }}
                    th {{ background: #2980b9; color: white; }}
                    .btn {{ color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; width: 100%; }}
                    input {{ width: 100%; margin: 5px 0; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>📦 Dashboard Stok & Petugas</h2>
                    <table>
                        <tr><th>Bahan</th><th>Sisa</th><th>Satuan</th></tr>
                        {rows}
                    </table>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                        <div style="background: #fff5eb; padding: 15px; border-radius: 8px;">
                            <form action="/update-stok" method="post">
                                <input type="hidden" name="aksi" value="kurang">
                                <select name="nama" style="width:100%; padding:8px;">{options}</select>
                                <input type="number" step="0.01" name="jumlah" placeholder="Jumlah" required>
                                <input type="text" name="petugas" placeholder="Nama Petugas (Misal: Adi)" required>
                                <button type="submit" class="btn" style="background: #e67e22;">Potong Stok</button>
                            </form>
                        </div>
                        <div style="background: #f0fff4; padding: 15px; border-radius: 8px;">
                            <form action="/update-stok" method="post">
                                <input type="hidden" name="aksi" value="tambah">
                                <select name="nama" style="width:100%; padding:8px;">{options}</select>
                                <input type="number" step="0.01" name="jumlah" placeholder="Jumlah" required>
                                <input type="text" name="petugas" placeholder="Nama Petugas (Misal: Adi)" required>
                                <button type="submit" class="btn" style="background: #27ae60;">Tambah Stok</button>
                            </form>
                        </div>
                    </div>
                    <h3>📜 Riwayat Aktivitas</h3>
                    <table>
                        <tr style="background: #95a5a6; color: white;"><th>Jam</th><th>Bahan</th><th>Aksi</th><th>Jumlah</th><th>Petugas</th></tr>
                        {log_rows}
                    </table>
                </div>
            </body>
        </html>
        """
    finally:
        if conn: conn.close()

@app.post("/update-stok")
def update_stok(nama: str = Form(...), jumlah: float = Form(...), aksi: str = Form(...), petugas: str = Form(...)):
    conn = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        operator = "+" if aksi == "tambah" else "-"
        cursor.execute(f"UPDATE stok_barang SET jumlah_stok = jumlah_stok {operator} %s WHERE nama_bahan = %s", (jumlah, nama))
        cursor.execute("INSERT INTO riwayat_stok (nama_bahan, aksi, jumlah, oleh_siapa) VALUES (%s, %s, %s, %s)", (nama, aksi, jumlah, petugas))
        conn.commit()
    finally:
        if conn: conn.close()
    return RedirectResponse(url="/", status_code=303)