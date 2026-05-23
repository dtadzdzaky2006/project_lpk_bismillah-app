import streamlit as st
import numpy as np
import sqlite3
import base64
import os

# ==============================================================================
# PROYEK: WATER QUALITY ANALYTICS SYSTEM (DARK ELEGANT GLASS EDITION)
# ==============================================================================

st.set_page_config(page_title="Water Quality Analytics System", page_icon="💧", layout="wide")

DB_FILE = "isis_water_quality.db"

# ==============================================================================
# 🖼️ FUNGSI ENKROPSI GAMBAR BACKGROUND KE BASE64
# ==============================================================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Pastikan file gambar lab kamu sudah di dalam folder dengan nama 'bg_lab.png'
img_base64 = get_base64_image("bg_lab.png")

# ==============================================================================
# 🗃️ INISIALISASI DATABASE FISIK (SQLITE)
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_log (
            id_biner TEXT, sampel TEXT, parameter TEXT, nilai REAL, status TEXT, keterangan TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_knowledge (
            topik TEXT PRIMARY KEY, penjelasan TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM ai_knowledge")
    if cursor.fetchone()[0] == 0:
        knowledge_awal = [
            ("bod", "BOD (Biochemical Oxygen Demand) merupakan takaran jumlah oksigen terlarut yang diperlukan oleh mikroorganisme untuk mendekomposisi bahan organik dalam air selama 5 hari."),
            ("cod", "COD (Chemical Oxygen Demand) adalah jumlah total oksigen yang dibutuhkan untuk mengurai seluruh bahan organik melalui reaksi kimia menggunakan oksidator kuat."),
            ("tss", "TSS (Total Suspended Solids) adalah material padatan tersuspensi (diameter > 1 mikrometer) yang tertahan pada media penyaring seperti kertas saring Whatman 41 setelah dikeringkan pada suhu 103-105°C."),
            ("do", "DO (Dissolved Oxygen) atau oksigen terlarut menunjukkan volume gas oksigen yang terkandung di dalam air. Kadar DO yang tinggi menandakan kualitas air yang baik untuk kehidupan akuatik."),
            ("regulasi", "Baku mutu air nasional diatur dalam PP No. 22 Tahun 2021. Batas parameter sangat bergantung pada kelas peruntukan air sungai atau badan air.")
        ]
        cursor.executemany("INSERT OR IGNORE INTO ai_knowledge VALUES (?, ?)", knowledge_awal)
        
    conn.commit()
    conn.close()

init_db()

# --- FUNGSI QUERY DATABASE ---
def save_water_log(id_biner, sampel, parameter, nilai, status, keterangan):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO water_log VALUES (?, ?, ?, ?, ?, ?)", (id_biner, sampel, parameter, nilai, status, keterangan))
    conn.commit()
    conn.close()

def get_water_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id_biner, sampel, parameter, nilai, status, keterangan FROM water_log")
    rows = cursor.fetchall()
    conn.close()
    return [{"id_biner": r[0], "sampel": r[1], "parameter": r[2], "nilai": r[3], "status": r[4], "keterangan": r[5]} for r in rows]

def clear_water_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM water_log")
    conn.commit()
    conn.close()

def save_ai_knowledge(topik, penjelasan):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO ai_knowledge VALUES (?, ?)", (topik, penjelasan))
    conn.commit()
    conn.close()

def get_ai_knowledge():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT topik, penjelasan FROM ai_knowledge")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


# ==============================================================================
# 🛠️ LOGIKA RUMUS KIMIA ANALISIS AIR
# ==============================================================================
def desimal_ke_biner(desimal):
    if desimal == 0: return "0"
    biner = ""
    temp = desimal
    while temp > 0:
        biner = str(temp % 2) + biner
        temp = temp // 2
    return biner

def hitung_bod(do_nol, do_lima, pengenceran):
    try: return round((do_nol - do_lima) * pengenceran, 4)
    except Exception: return None

def hitung_cod(vol_blanko, vol_sampel, norm_fas, vol_air):
    try: return round(((vol_blanko - vol_sampel) * norm_fas * 8000) / vol_air, 4)
    except ZeroDivisionError: return None

def hitung_tss(berat_akhir, berat_awal, vol_sampel_ml):
    try: return round(((berat_akhir - berat_awal) * 1000000) / vol_sampel_ml, 4)
    except ZeroDivisionError: return None

def hitung_do(vol_thiosulfat, norm_thiosulfat, vol_botol_do):
    try: return round((vol_thiosulfat * norm_thiosulfat * 8000) / (vol_botol_do - 4), 4)
    except ZeroDivisionError: return None


# ==============================================================================
# 🧠 LOGIKA EVALUASI AI (FORMAT PARAGRAF KONTINU)
# ==============================================================================
def ai_water_evaluation(data_baru, batas_acuan, parameter_nama, tipe_ambang="maks"):
    logs = get_water_logs()
    data_sejenis = [d["nilai"] for d in logs if d["parameter"] == data_baru["parameter"] and d["status"] == "MEMENUHI SYARAT"]
    
    pembahasan = f"Berdasarkan hasil analisis data laboratorium yang tersimpan di dalam database fisik, sampel air dengan kode identifikasi biner {data_baru['id_biner']} menunjukkan kadar {parameter_nama} sebesar {data_baru['nilai']:.4f} mg/L. "
    
    if data_baru["status"] == "MEMENUHI SYARAT":
        if tipe_ambang == "maks":
            pembahasan += f"Nilai parameter ini berada di bawah batas ambang regulasi baku mutu lingkungan yang ditetapkan yaitu sebesar {batas_acuan:.4f} mg/L, sehingga sampel air ini dinyatakan bersih dan layak untuk mendukung ekosistem perairan yang sehat. "
        else:
            pembahasan += f"Kadar oksigen terlarut ini berada di atas ambang minimum batas regulasi baku mutu lingkungan yaitu sebesar {batas_acuan:.4f} mg/L, yang menandakan pasokan oksigen bagi biota akuatik berada dalam kondisi sangat optimal. "
    else:
        if tipe_ambang == "maks":
            pembahasan += f"Kadar konsentrasi padatan atau beban limbah organik tersebut telah melampaui batas ambang standar regulasi lingkungan sebesar {batas_acuan:.4f} mg/L, yang menandakan tingkat pencemaran air yang tinggi dan berbahaya bagi badan air. "
        else:
            pembahasan += f"Kadar oksigen terlarut terpantau jatuh di bawah batas minimum kelayakan lingkungan yaitu sebesar {batas_acuan:.4f} mg/L, yang mengindikasikan terjadinya defisit oksigen parah akibat dekomposisi bahan organik berlebih. "

    if len(data_sejenis) >= 3:
        rata_rata = np.mean(data_sejenis)
        pembahasan += f"Apabila dibandingkan dengan data historis pengujian masa lalu, nilai rata-rata optimal untuk sampel yang lolos adalah {rata_rata:.4f} mg/L. Melalui analisis statistik tersebut, AI mengonfirmasi bahwa tren fluktuasi sampel ini masih berada dalam rentang deviasi normal lingkungan industri."
    else:
        pembahasan += "Saat ini AI belum mengaktifkan modul analitik prediktif mendalam dikarenakan jumlah data sampel valid yang tersimpan di harddisk komputer masih kurang dari tiga rekaman historis."
        
    return pembahasan

def ai_chatbot_brain(pertanyaan):
    pertanyaan = pertanyaan.lower().strip()
    memori_pengetahuan = get_ai_knowledge()
    database_air = get_water_logs()
    
    if pertanyaan in ["halo", "hai", "p", "test", "halo ai"]:
        return "Sini, masuk! Ada data lab apa yang mau kita beresin bareng hari ini? 💧"
    if pertanyaan in ["kamu siapa", "siapa kamu", "siapa"]:
        return "Kenalin, aku asisten database AI pribadimu. Panggil aja partner lab-mu, siap bantu hitung data kimia anti-error! 🧠🚀"
    
    for kunci in memori_pengetahuan:
        if kunci in pertanyaan:
            return f"**[Long-Term Memory]:** Nah, kalau soal *{kunci}*, ingatan databaseku mencatat: {memori_pengetahuan[kunci]}"
            
    if "rekap" in pertanyaan or "evaluasi" in pertanyaan or "total" in pertanyaan:
        if not database_air: 
            return "Waduh, database analisis kualitas air di harddisk laptopmu masih kosong melompong nih. Yuk, coba hitung dan simpan satu sampel dulu!"
        
        total = len(database_air)
        reject = sum(1 for d in database_air if d["status"] in ["MELEBIHI AMBANG", "DI BAWAH MINIMUM"])
        
        respons = f"**[Database Report]:** Oke, mari kita cek isi harddisk! Total riwayat pengujian yang berhasil tersimpan ada **{total} sampel**. "
        if reject > 0:
            respons += f"Tapi awas nih, ada **{reject} sampel yang ambang batasnya bermasalah (merah)**. Butuh perhatian ekstra di lingkungan ujinya ya!"
        else:
            respons += "Aman jaya! Sejauh ini belum ada sampel yang melebihi atau menyalahi ambang batas regulasi lingkungan."
            
        return respons
        
    return "Mmm, pola teks atau keyword materi itu belum ketemu di sel otak database-ku nih. Coba ajarkan aku dulu di form manajemen memori supaya aku ingat selamanya!"


# ==============================================================================
# 📱 FRONTEND & ELEMEN ANIMASI GELEMBUNG REALISTIS (DARK MODE INTEGRATION)
# ==============================================================================

# 🌌 1. Injeksi Canvas HTML5 untuk Animasi Gelembung Kaca Laboratorium 3D Berpendar
st.markdown("""
    <canvas id="customLabCanvas" style="position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-1; pointer-events:none; opacity:0.85;"></canvas>
    <script>
    const canvas = document.getElementById('customLabCanvas');
    const ctx = canvas.getContext('2d');

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    const bubbles = [];
    for(let i=0; i<28; i++) {
        bubbles.push({
            x: Math.random() * canvas.width,
            y: canvas.height + Math.random() * 200,
            radius: Math.random() * 7 + 3,
            speed: Math.random() * 0.7 + 0.3,
            wobble: Math.random() * 2,
            wobbleSpeed: Math.random() * 0.015,
            opacity: Math.random() * 0.5 + 0.3
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        bubbles.forEach(b => {
            b.y -= b.speed;
            b.wobble += b.wobbleSpeed;
            b.x += Math.sin(b.wobble) * 0.3;

            if(b.y < -20) {
                b.y = canvas.height + 20;
                b.x = Math.random() * canvas.width;
            }

            // Menggambar gelembung menyala di background gelap
            let gradient = ctx.createRadialGradient(b.x - b.radius*0.2, b.y - b.radius*0.2, b.radius * 0.05, b.x, b.y, b.radius);
            gradient.addColorStop(0, `rgba(255, 255, 255, ${b.opacity + 0.3})`);
            gradient.addColorStop(0.5, `rgba(135, 206, 250, ${b.opacity * 0.3})`);
            gradient.addColorStop(1, `rgba(30, 144, 255, ${b.opacity * 0.6})`);

            ctx.beginPath();
            ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.strokeStyle = `rgba(255, 255, 255, ${b.opacity * 0.4})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
            ctx.fill();

            ctx.beginPath();
            ctx.arc(b.x - b.radius * 0.25, b.y - b.radius * 0.25, b.radius * 0.12, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
            ctx.fill();
        });
        requestAnimationFrame(draw);
    }
    draw();
    </script>
""", unsafe_allow_html=True)

# 🎨 2. CSS KUSTOM: ELEGAN DARK OVERLAY BERGAYA GLASSMORPHISM GELAP
if img_base64:
    # Overlay gradasi warna gelap (dark navy ke deep charcoal) menutup di atas gambar kamu
    bg_style = f"""
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.90) 0%, rgba(8, 15, 30, 0.94) 100%), 
                url('data:image/png;base64,{img_base64}') no-repeat center center fixed;
    background-size: cover;
    """
else:
    bg_style = "background: linear-gradient(135deg, #0f172a 0%, #020617 100%);"

st.markdown(f"""
    <style>
    /* Aplikasi Tema Gelap */
    .stApp {{
        {bg_style}
        color: #f8fafc !important;
    }}
    
    /* Navigasi Sidebar Gelap Elegan */
    [data-testid="stSidebar"] {{
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-right: 1px solid rgba(51, 65, 85, 0.5);
    }}
    
    .main-title {{
        font-size: 38px;
        font-weight: 800;
        background: linear-gradient(45deg, #38bdf8, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* KARTU GLASSMORPHISM GELAP (DARK-GLASS) */
    .card-box-1 {{
        background: rgba(30, 41, 59, 0.55);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        padding: 22px;
        border-radius: 14px;
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-left: 6px solid #0ea5e9;
        color: #f1f5f9;
        margin-bottom: 15px;
    }}
    
    .card-box-2 {{
        background: rgba(30, 41, 59, 0.55);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        padding: 22px;
        border-radius: 14px;
        border: 1px solid rgba(74, 222, 128, 0.25);
        border-left: 6px solid #22c55e;
        color: #f1f5f9;
        margin-bottom: 15px;
    }}
    
    /* Kotak Langkah Kalkulasi Monospace yang Kontras Tinggi */
    .calc-box {{
        background: rgba(15, 23, 42, 0.85);
        border: 1px dashed #38bdf8;
        border-radius: 8px;
        padding: 15px;
        font-family: 'Courier New', Courier, monospace;
        color: #38bdf8 !important;
        margin-top: 10px;
    }}
    
    .section-head {{
        color: #38bdf8;
        font-weight: bold;
        border-bottom: 2px solid rgba(51, 65, 85, 0.6);
        padding-bottom: 5px;
        margin-top: 15px;
    }}
    
    /* Memaksa elemen teks bawaan streamlit mengikuti aturan warna terang di dark mode */
    label, p, span, div, .stMarkdown {{
        color: #e2e8f0 !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #f8fafc !important;
    }}
    
    /* Tombol Biru Neon Cyan */
    .stButton>button {{
        background: linear-gradient(45deg, #0284c7, #3b82f6) !important;
        color: white !important;
        border-radius: 8px !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.3) !important;
    }}
    
    /* Tabel Data agar rapi di layar gelap */
    .stTable table {{
        background-color: rgba(30, 41, 59, 0.4) !important;
        color: #f1f5f9 !important;
    }}
    </style>
""", unsafe_allow_html=True)


# --- SIDEBAR (NAVIGASI) ---
with st.sidebar:
    st.markdown("<h2 style='color: #38bdf8; margin-bottom: 0px; font-weight:800;'>💧 Water Quality</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-style: italic; color: #94a3b8; margin-top:0px;'>Politeknik AKA Bogor</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    pilih_fitur = st.radio(
        "📌 Pilih Fitur Utama:",
        ["Beranda", "Perhitungan BOD", "Perhitungan COD", "Perhitungan TSS", "Perhitungan DO", "Database Riwayat Sampel", "Inteligensia & Konsultasi AI"]
    )
    st.markdown("---")
    
    logs_saat_ini = get_water_logs()
    total_data = len(logs_saat_ini)
    total_bermasalah = sum(1 for d in logs_saat_ini if d["status"] in ["MELEBIHI AMBANG", "DI BAWAH MINIMUM"])
    st.metric("Total Sampel Teruji", f"{total_data} Sampel")
    st.metric("Sampel Bermasalah", f"{total_bermasalah} Sampel", delta=f"+{total_bermasalah}" if total_bermasalah > 0 else "0", delta_color="inverse")


# --- KONTEN UTAMA ---

# 🏠 BERANDA
if pilih_fitur == "Beranda":
    st.markdown("<p class='main-title'>💧 Water Quality Analytics System</p>", unsafe_allow_html=True)
    st.caption("Dashboard Komputasi Terpadu Laboratorium Analisis Kimia Lingkungan")
    st.markdown("---")
    
    col_ref1, col_ref2 = st.columns(2)
    with col_ref1:
        st.markdown("<div class='card-box-1'><h3 style='color: #38bdf8; margin-top:0px;'>🎯 Tujuan Aplikasi</h3><p>Mengotomatisasi pengolahan data praktikum parameter air untuk mencegah kesalahan hitung manual, serta menyimpan data riwayat laboratorium secara aman.</p></div>", unsafe_allow_html=True)
    with col_ref2:
        st.markdown("<div class='card-box-2'><h3 style='color: #4ade80; margin-top:0px;'>📚 Manfaat AI</h3><p>Membantu penyusunan narasi Bab Pembahasan (paragraf kontinu) secara otomatis bersandarkan data historis dan ambang batas baku mutu lingkungan.</p></div>", unsafe_allow_html=True)


# 🧪 PERHITUNGAN BOD
elif pilih_fitur == "Perhitungan BOD":
    st.markdown("<h1 style='color: #38bdf8;'>🧪 Input Analisis Parameter BOD</h1>", unsafe_allow_html=True)
    st.markdown("---")
    bod_max = st.number_input("🚨 Batas Maks Baku Mutu BOD (mg/L):", value=6.0000, step=0.5000, format="%.4f")
    
    col_l1, col_l2 = st.columns([1.3, 1.3])
    with col_l1:
        nama_smpl = st.text_input("📍 Kode / Lokasi Sampel Air:", value="River-Sample-A", key="bod_sample")
        do_0 = st.number_input("Kadar DO Hari Ke-0 (DO0) (mg/L):", value=8.2000, format="%.4f")
        do_5 = st.number_input("Kadar DO Hari Ke-5 (DO5) (mg/L):", value=4.5000, format="%.4f")
        f_pengenceran = st.number_input("Faktor Pengenceran (P):", value=2.0, step=0.5)
        
        if st.button("🔥 Hitung & Simpan Data BOD", use_container_width=True):
            hasil = hitung_bod(do_0, do_5, f_pengenceran)
            status = "MEMENUHI SYARAT" if hasil <= bod_max else "MELEBIHI AMBANG"
            biner_id = desimal_ke_biner(len(get_water_logs()) + 1)
            
            save_water_log(biner_id, nama_smpl, "BOD", hasil, status, f"DO0={do_0}, DO5={do_5}, P={f_pengenceran}")
            st.session_state["pembahasan_bod"] = ai_water_evaluation({"id_biner": biner_id, "parameter": "BOD", "nilai": hasil, "status": status}, bod_max, "BOD", "maks")
            st.session_state["status_bod"] = status
            st.session_state["nilai_bod"] = hasil
            st.session_state["calc_bod"] = f"BOD = (DO0 - DO5) x P\nBOD = ({do_0} - {do_5}) x {f_pengenceran}\nBOD = {round(do_0 - do_5, 4)} x {f_pengenceran}\nBOD = {hasil:.4f} mg/L"
            st.rerun()

    with col_l2:
        st.markdown("<h3 style='color: #38bdf8;'>🧐 Hasil & Rincian Logika Perhitungan</h3>", unsafe_allow_html=True)
        if "pembahasan_bod" in st.session_state:
            if st.session_state["status_bod"] == "MEMENUHI SYARAT":
                st.success(f"🎉 HASIL: {st.session_state['nilai_bod']:.4f} mg/L ({st.session_state['status_bod']})")
            else:
                st.error(f"❌ HASIL: {st.session_state['nilai_bod']:.4f} mg/L ({st.session_state['status_bod']})")
            
            st.markdown("**🔢 Cara Perhitungan Matematika:**")
            st.markdown(f"<pre class='calc-box'>{st.session_state['calc_bod']}</pre>", unsafe_allow_html=True)
            st.info(st.session_state["pembahasan_bod"])


# 🧪 PERHITUNGAN COD
elif pilih_fitur == "Perhitungan COD":
    st.markdown("<h1 style='color: #38bdf8;'>🧪 Input Analisis Parameter COD</h1>", unsafe_allow_html=True)
    st.markdown("---")
    cod_max = st.number_input("🚨 Batas Maks Baku Mutu COD (mg/L):", value=25.0000, step=1.0000, format="%.4f")
    
    col_l1, col_l2 = st.columns([1.3, 1.3])
    with col_l1:
        nama_smpl = st.text_input("📍 Kode / Lokasi Sampel Air:", value="River-Sample-A", key="cod_sample")
        v_blanko = st.number_input("Volume Penitran Blanko (mL):", value=15.20, format="%.2f")
        v_sampel = st.number_input("Volume Penitran Sampel Air (mL):", value=13.60, format="%.2f")
        n_fas = st.number_input("Normalitas Larutan FAS (N):", value=0.1000, format="%.4f")
        vol_air = st.number_input("Volume Sampel Air Teruji (mL):", value=50.00, format="%.2f")
        
        if st.button("🔥 Hitung & Simpan Data COD", use_container_width=True):
            hasil = hitung_cod(v_blanko, v_sampel, n_fas, vol_air)
            status = "MEMENUHI SYARAT" if hasil <= cod_max else "MELEBIHI AMBANG"
            biner_id = desimal_ke_biner(len(get_water_logs()) + 1)
            
            save_water_log(biner_id, nama_smpl, "COD", hasil, status, f"V_B={v_blanko}, V_S={v_sampel}, N={n_fas}")
            st.session_state["pembahasan_cod"] = ai_water_evaluation({"id_biner": biner_id, "parameter": "COD", "nilai": hasil, "status": status}, cod_max, "COD", "maks")
            st.session_state["status_cod"] = status
            st.session_state["nilai_cod"] = hasil
            st.session_state["calc_cod"] = f"COD = ((Vol Blanko - Vol Sampel) x N FAS x 8000) / Vol Air\nCOD = (({v_blanko} - {v_sampel}) x {n_fas} x 8000) / {vol_air}\nCOD = ({round(v_blanko - v_sampel, 2)} x {n_fas} x 8000) / {vol_air}\nCOD = {round((v_blanko - v_sampel) * n_fas * 8000, 4)} / {vol_air}\nCOD = {hasil:.4f} mg/L"
            st.rerun()

    with col_l2:
        st.markdown("<h3 style='color: #38bdf8;'>🧐 Hasil & Rincian Logika Perhitungan</h3>", unsafe_allow_html=True)
        if "pembahasan_cod" in st.session_state:
            if st.session_state["status_cod"] == "MEMENUHI SYARAT":
                st.success(f"🎉 HASIL: {st.session_state['nilai_cod']:.4f} mg/L ({st.session_state['status_cod']})")
            else:
                st.error(f"❌ HASIL: {st.session_state['nilai_cod']:.4f} mg/L ({st.session_state['status_cod']})")
            
            st.markdown("**🔢 Cara Perhitungan Matematika:**")
            st.markdown(f"<pre class='calc-box'>{st.session_state['calc_cod']}</pre>", unsafe_allow_html=True)
            st.info(st.session_state["pembahasan_cod"])


# ⚖️ PERHITUNGAN TSS
elif pilih_fitur == "Perhitungan TSS":
    st.markdown("<h1 style='color: #38bdf8;'>⚖️ Input Analisis Parameter TSS</h1>", unsafe_allow_html=True)
    st.markdown("---")
    tss_max = st.number_input("🚨 Batas Maks Baku Mutu TSS (mg/L):", value=50.0000, step=5.0000, format="%.4f")
    
    col_n1, col_n2 = st.columns([1.3, 1.3])
    with col_n1:
        nama_smpl_baru = st.text_input("📍 Kode / Lokasi Sampel Air:", value="River-Sample-B", key="tss_sample")
        b_awal = st.number_input("Berat Kertas Saring Kosong (gram):", value=1.2345, format="%.4f")
        b_akhir = st.number_input("Berat Kertas Saring + Padatan Kering (gram):", value=1.2455, format="%.4f")
        v_air_tss = st.number_input("Volume Sampel Air yang Disaring (mL):", value=100.00, format="%.2f")
        
        if st.button("🔥 Hitung & Simpan Data TSS", use_container_width=True):
            hasil = hitung_tss(b_akhir, b_awal, v_air_tss)
            status = "MEMENUHI SYARAT" if hasil <= tss_max else "MELEBIHI AMBANG"
            biner_id = desimal_ke_biner(len(get_water_logs()) + 1)
            
            save_water_log(biner_id, nama_smpl_baru, "TSS", hasil, status, f"B_Awal={b_awal} g, B_Akhir={b_akhir} g")
            st.session_state["pembahasan_tss"] = ai_water_evaluation({"id_biner": biner_id, "parameter": "TSS", "nilai": hasil, "status": status}, tss_max, "TSS", "maks")
            st.session_state["status_tss"] = status
            st.session_state["nilai_tss"] = hasil
            st.session_state["calc_tss"] = f"TSS = ((Berat Akhir - Berat Awal) x 1.000.000) / Vol Disaring\nTSS = (({b_akhir} - {b_awal}) x 1.000.000) / {v_air_tss}\nTSS = ({round(b_akhir - b_awal, 4)} x 1.000.000) / {v_air_tss}\nTSS = {round((b_akhir - b_awal) * 1000000, 4)} / {v_air_tss}\nTSS = {hasil:.4f} mg/L"
            st.rerun()

    with col_n2:
        st.markdown("<h3 style='color: #38bdf8;'>🧐 Hasil & Rincian Logika Perhitungan</h3>", unsafe_allow_html=True)
        if "pembahasan_tss" in st.session_state:
            if st.session_state["status_tss"] == "MEMENUHI SYARAT":
                st.success(f"🎉 HASIL: {st.session_state['nilai_tss']:.4f} mg/L ({st.session_state['status_tss']})")
            else:
                st.error(f"❌ HASIL: {st.session_state['nilai_tss']:.4f} mg/L ({st.session_state['status_tss']})")
            
            st.markdown("**🔢 Cara Perhitungan Matematika:**")
            st.markdown(f"<pre class='calc-box'>{st.session_state['calc_tss']}</pre>", unsafe_allow_html=True)
            st.info(st.session_state["pembahasan_tss"])


# 🧪 PERHITUNGAN DO
elif pilih_fitur == "Perhitungan DO":
    st.markdown("<h1 style='color: #38bdf8;'>🧪 Input Analisis Parameter DO</h1>", unsafe_allow_html=True)
    st.markdown("---")
    do_min = st.number_input("🚨 Batas Minimum Baku Mutu DO (mg/L):", value=4.0000, step=0.5000, format="%.4f")
    
    col_n1, col_n2 = st.columns([1.3, 1.3])
    with col_n1:
        nama_smpl_baru = st.text_input("📍 Kode / Lokasi Sampel Air:", value="River-Sample-B", key="do_sample")
        v_thio = st.number_input("Volume Penitran Thiosulfat (mL):", value=5.40, format="%.2f")
        n_thio = st.number_input("Normalitas Larutan Thiosulfat (N):", value=0.0250, format="%.4f")
        v_botol = st.number_input("Volume Botol DO yang Digunakan (mL):", value=250.00, format="%.2f")
        
        if st.button("🔥 Hitung & Simpan Data DO", use_container_width=True):
            hasil = hitung_do(v_thio, n_thio, v_botol)
            status = "MEMENUHI SYARAT" if hasil >= do_min else "DI BAWAH MINIMUM"
            biner_id = desimal_ke_biner(len(get_water_logs()) + 1)
            
            save_water_log(biner_id, nama_smpl_baru, "DO", hasil, status, f"V_Thio={v_thio} mL, N={n_thio}")
            st.session_state["pembahasan_do"] = ai_water_evaluation({"id_biner": biner_id, "parameter": "DO", "nilai": hasil, "status": status}, do_min, "Dissolved Oxygen (DO)", "min")
            st.session_state["status_do"] = status
            st.session_state["nilai_do"] = hasil
            st.session_state["calc_do"] = f"DO = (Vol Thiosulfat x N Thiosulfat x 8000) / (Vol Botol - 4)\nDO = ({v_thio} x {n_thio} x 8000) / ({v_botol} - 4)\nDO = {round(v_thio * n_thio * 8000, 4)} / {v_botol - 4}\nDO = {hasil:.4f} mg/L"
            st.rerun()

    with col_n2:
        st.markdown("<h3 style='color: #38bdf8;'>🧐 Hasil & Rincian Logika Perhitungan</h3>", unsafe_allow_html=True)
        if "pembahasan_do" in st.session_state:
            if st.session_state["status_do"] == "MEMENUHI SYARAT":
                st.success(f"🎉 HASIL: {st.session_state['nilai_do']:.4f} mg/L ({st.session_state['status_do']})")
            else:
                st.warning(f"⚠️ HASIL: {st.session_state['nilai_do']:.4f} mg/L ({st.session_state['status_do']})")
            
            st.markdown("**🔢 Cara Perhitungan Matematika:**")
            st.markdown(f"<pre class='calc-box'>{st.session_state['calc_do']}</pre>", unsafe_allow_html=True)
            st.info(st.session_state["pembahasan_do"])


# 📊 DATABASE RIWAYAT SAMPEL
elif pilih_fitur == "Database Riwayat Sampel":
    st.markdown("<h1 style='color: #38bdf8;'>📊 Rekam Data Kualitas Air Permanen</h1>", unsafe_allow_html=True)
    st.markdown("---")
    if logs_saat_ini:
        st.table(logs_saat_ini)
        st.markdown("---")
        if st.button("🗑️ Kosongkan Seluruh Riwayat Database", use_container_width=True):
            clear_water_logs()
            st.rerun()
    else:
        st.info("Belum ada riwayat pengujian sampel air yang tersimpan di dalam database.")


# 🧠 INTELIGENSIA & KONSULTASI AI
elif pilih_fitur == "Inteligensia & Konsultasi AI":
    st.markdown("<h1 style='color: #38bdf8;'>🧠 Pusat Kendali Pengetahuan & Konsultasi AI</h1>", unsafe_allow_html=True)
    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("<h4>💬 Konsultasi Bersama AI Partner</h4>", unsafe_allow_html=True)
        chat_in = st.text_input("Ketik di sini (Contoh: 'halo', 'do', 'rekap'):", key="chat_input_unique")
        if chat_in:
            with st.chat_message("assistant"):
                st.write(ai_chatbot_brain(chat_in))
    with col_a2:
        st.markdown("<h4>💾 Suntikkan Materi Pengetahuan Baru</h4>", unsafe_allow_html=True)
        topik = st.text_input("Topik Baru (Kata Kunci):").lower().strip()
        penjelasan = st.text_area("Deskripsi SOP / Penjelasan Ilmiah Kimia Analisis:")
        if st.button("🚀 Simpan Permanen ke Memori AI", use_container_width=True):
            if topik and penjelasan:
                save_ai_knowledge(topik, penjelasan)
                st.toast("AI sukses memperbarui memori pengetahuannya!")
                st.rerun()



