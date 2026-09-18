import streamlit as st
import pandas as pd
import os
import sqlite3
from datetime import datetime
from core_ai import run_pipeline

st.set_page_config(
    page_title="fraudshield-voice - Giam Dinh Deepfake",
    layout="wide",
    initial_sidebar_state="collapsed"
)

AUDIO_STORE_DIR = "saved_audios"
os.makedirs(AUDIO_STORE_DIR, exist_ok=True)

try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

def init_db():
    conn = sqlite3.connect("forensic_admin.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            fullname TEXT,
            agency TEXT,
            role TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            filename TEXT,
            audio_path TEXT,
            channel TEXT,
            suspect TEXT,
            acoustic_score REAL,
            nlp_score REAL,
            threat_score REAL,
            verdict TEXT,
            investigator TEXT
        )
    """)

    c.execute("SELECT * FROM users WHERE username = 'duy'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES ('duy', '123456', 'Nguyen Duy (Lead Admin)', 'Ban An Ninh Mang', 'admin')")
    else:
        c.execute("UPDATE users SET password = '123456', role = 'admin' WHERE username = 'duy'")

    c.execute("SELECT * FROM users WHERE username = 'hien'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES ('hien', '123456', 'Tran Hien (Lead Admin)', 'Ban An Ninh Mang', 'admin')")
    else:
        c.execute("UPDATE users SET password = '123456', role = 'admin' WHERE username = 'hien'")

    c.execute("SELECT * FROM users WHERE username = 'user'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES ('user', 'user123', 'Dieu Tra Vien Co So', 'Cong An Co So', 'user')")

    conn.commit()
    conn.close()

def check_login(username, password):
    conn = sqlite3.connect("forensic_admin.db")
    c = conn.cursor()
    c.execute("SELECT username, role, fullname FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def register_user(username, password, fullname, agency):
    try:
        conn = sqlite3.connect("forensic_admin.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES (?, ?, ?, ?, 'user')",
                  (username, password, fullname, agency))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_scans(username=None, is_admin=False):
    try:
        conn = sqlite3.connect("forensic_admin.db")
        c = conn.cursor()
        if is_admin:
            c.execute("SELECT id, timestamp, filename, audio_path, channel, suspect, acoustic_score, nlp_score, threat_score, verdict, investigator FROM audit_logs ORDER BY id DESC")
        else:
            c.execute("SELECT id, timestamp, filename, audio_path, channel, suspect, acoustic_score, nlp_score, threat_score, verdict, investigator FROM audit_logs WHERE investigator = ? ORDER BY id DESC", (username,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

init_db()

if "lang" not in st.session_state:
    st.session_state["lang"] = "Tiếng Việt"
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Trang chủ"
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = "guest"

TEXTS = {
    "Tiếng Việt": {
        "brand": "FRAUDSHIELD-VOICE",
        "tab_home": "Trang chủ",
        "tab_guide": "Hướng dẫn",
        "tab_auth": "Tài khoản",
        "hero_tag": "HE THONG GIAM DINH CHUYEN DUNG",
        "hero_title_1": "Hệ thống giám định & điều tra cuộc gọi",
        "hero_title_2": "Deepfake",
        "hero_desc": "Phân tích và giám định kỹ thuật âm thanh số dựa trên cơ chế Dual-Engine kết hợp mô hình xác suất hậu nghiệm, phục vụ điều tra các cuộc gọi nghi vấn mạo danh.",
        "badge_1_title": "Nhận diện Vocoder AI",
        "badge_1_desc": "Trích xuất 40 tham số âm học",
        "badge_2_title": "Phân tích kịch bản thao túng",
        "badge_2_desc": "Bóc băng NLP nhận diện từ khóa",
        "badge_3_title": "Quản lý hồ sơ giám định",
        "badge_3_desc": "Lưu trữ toàn vẹn cơ sở dữ liệu",
        "section_audio_title": "KIỂM TRA ÂM THANH",
        "upload_desc": "Tải lên tệp âm thanh cuộc gọi (.wav, .mp3) để hệ thống thực hiện giám định.",
        "call_source_label": "Kênh liên lạc:",
        "suspect_label": "Đối tượng nghi vấn:",
        "sources": ["Mạng di động (GSM)", "VoIP / Zalo / Telegram", "Ghi âm chứng thực", "Khác"],
        "suspects": ["Cơ quan Công an / Viện kiểm sát", "Ngân hàng / Tài chính", "Người thân / Bạn bè", "Khác"],
        "check_btn": "TIẾN HÀNH GIÁM ĐỊNH",
        "result_heading": "KẾT QUẢ PHÂN TÍCH VÀ ĐÁNH GIÁ CHUYÊN SÂU",
        "high_threat": "CẢNH BÁO NGUY CƠ CAO (DEEPFAKE): Phát hiện giọng nói nhân tạo can thiệp sâu. Khuyến nghị dừng liên lạc và không chuyển tiền hay cung cấp OTP.",
        "safe_threat": "XÁC NHẬN AN TOÀN (REAL VOICE): Tín hiệu giọng nói sinh học tự nhiên, không ghi nhận dấu hiệu can thiệp tổng hợp âm thanh.",
        "history_title": "NHẬT KÝ CÁC PHIÊN GIÁM ĐỊNH (AUDIT LOG)",
        "auth_required": "Yêu cầu đăng nhập: Vui lòng truy cập mục Tài khoản để xem lại dữ liệu lịch sử và nghe lại tệp âm thanh.",
        "guide_heading": "Quy trình giám định âm thanh số",
        "guide_sub": "Tài liệu hướng dẫn nghiệp vụ 4 bước chuẩn hóa dành cho điều tra viên",
        "auth_heading": "Cổng Xác Thực Điều Tra Viên & Quản Trị Viên"
    },
    "English": {
        "brand": "FRAUDSHIELD-VOICE",
        "tab_home": "Home",
        "tab_guide": "Manual Guide",
        "tab_auth": "Account",
        "hero_tag": "FORENSIC SYSTEM",
        "hero_title_1": "Deepfake Call Investigation",
        "hero_title_2": "& Forensic System",
        "hero_desc": "Digital audio forensic evaluation powered by a Dual-Engine architecture with posterior probability modeling for investigating impersonation incidents.",
        "badge_1_title": "Vocoder Identification",
        "badge_1_desc": "Extracts 40 acoustic dimensions",
        "badge_2_title": "Script Manipulation Audit",
        "badge_2_desc": "NLP extortion profiling",
        "badge_3_title": "Audit Trail & Records",
        "badge_3_desc": "Integrity-preserved database",
        "section_audio_title": "AUDIO FORENSIC SCAN",
        "upload_desc": "Upload call recording file (.wav, .mp3) for automated forensic inspection.",
        "call_source_label": "Call Channel:",
        "suspect_label": "Suspected Target:",
        "sources": ["Cellular Network (GSM)", "VoIP / Zalo / Telegram", "Forensic Recording", "Other"],
        "suspects": ["Police / Procuratorate", "Bank / Finance Staff", "Relative / Friend", "Other"],
        "check_btn": "START FORENSIC SCAN",
        "result_heading": "IN-DEPTH FORENSIC ANALYSIS REPORT",
        "high_threat": "HIGH RISK ALERT (DEEPFAKE): Synthetic vocoder markers detected. Cease communication immediately; do not transfer money or disclose credentials.",
        "safe_threat": "SECURE STATUS (REAL VOICE): Biological human vocal patterns confirmed; no artificial generation artifacts detected.",
        "history_title": "FORENSIC AUDIT LOGS & PLAYBACK",
        "auth_required": "Authentication Required: Please sign in via the Account tab to inspect previous session records and audio evidence.",
        "guide_heading": "Forensic Protocol Manual",
        "guide_sub": "Standardized 4-step investigation workflow for forensic analysts",
        "auth_heading": "Forensic Investigator & Admin Portal"
    }
}

t = TEXTS[st.session_state["lang"]]

# Header
col_logo, col_menu, col_lang = st.columns([2.6, 5.0, 2.4], vertical_alignment="center")

with col_logo:
    st.markdown(f'<div class="nav-brand">{t["brand"]}</div>', unsafe_allow_html=True)

with col_menu:
    m1, m2, m3 = st.columns(3)
    curr_tab = st.session_state["active_tab"]

    with m1:
        underline1 = "background-color: #2563eb;" if curr_tab == "Trang chủ" else "background-color: transparent;"
        if st.button(t["tab_home"], use_container_width=True, key="btn_home"):
            st.session_state["active_tab"] = "Trang chủ"
            st.rerun()
        st.markdown(f"<div style='margin-top: 2px; height: 3px; {underline1}'></div>", unsafe_allow_html=True)

    with m2:
        underline2 = "background-color: #2563eb;" if curr_tab == "Hướng dẫn" else "background-color: transparent;"
        if st.button(t["tab_guide"], use_container_width=True, key="btn_guide"):
            st.session_state["active_tab"] = "Hướng dẫn"
            st.rerun()
        st.markdown(f"<div style='margin-top: 2px; height: 3px; {underline2}'></div>", unsafe_allow_html=True)

    with m3:
        underline3 = "background-color: #2563eb;" if curr_tab == "Đăng nhập / Đăng ký" else "background-color: transparent;"
        auth_label = f"{st.session_state['username']}" if st.session_state["is_logged_in"] else t["tab_auth"]
        if st.button(auth_label, use_container_width=True, key="btn_auth"):
            st.session_state["active_tab"] = "Đăng nhập / Đăng ký"
            st.rerun()
        st.markdown(f"<div style='margin-top: 2px; height: 3px; {underline3}'></div>", unsafe_allow_html=True)

with col_lang:
    selected_lang = st.selectbox(
        "Lang",
        ["Tiếng Việt", "English"],
        index=0 if st.session_state["lang"] == "Tiếng Việt" else 1,
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state["lang"]:
        st.session_state["lang"] = selected_lang
        st.rerun()

# TAB 1: TRANG CHỦ
if st.session_state["active_tab"] == "Trang chủ":
    st.markdown(f"""
        <div class="hero-banner-full">
            <div class="hero-tag">{t["hero_tag"]}</div>
            <div class="hero-title">{t["hero_title_1"]} <span>{t["hero_title_2"]}</span></div>
            <div class="hero-desc">{t["hero_desc"]}</div>
            <div class="hero-badges-container">
                <div class="hero-badge-item">
                    <b style="color: #ffffff; font-size: 1.05rem;">{t["badge_1_title"]}</b><br>
                    <span style="color: #93c5fd; font-size: 0.92rem;">{t["badge_1_desc"]}</span>
                </div>
                <div class="hero-badge-item">
                    <b style="color: #ffffff; font-size: 1.05rem;">{t["badge_2_title"]}</b><br>
                    <span style="color: #93c5fd; font-size: 0.92rem;">{t["badge_2_desc"]}</span>
                </div>
                <div class="hero-badge-item">
                    <b style="color: #ffffff; font-size: 1.05rem;">{t["badge_3_title"]}</b><br>
                    <span style="color: #93c5fd; font-size: 0.92rem;">{t["badge_3_desc"]}</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="section-title-container">
            <h2 class="section-title-text">{t["section_audio_title"]}</h2>
            <div class="section-title-underline"></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns([1.8, 1.2], gap="large")

    with col_f1:
        st.markdown(f"<p style='color: #475569; font-weight: 700; margin-bottom: 8px;'>{t['upload_desc']}</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Tải lên file", type=["wav", "mp3"], label_visibility="collapsed")

    with col_f2:
        st.markdown("<p style='color: #475569; font-weight: 700; margin-bottom: 8px;'>Thiết lập thông tin giám định:</p>", unsafe_allow_html=True)
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            call_source = st.selectbox(t["call_source_label"], t["sources"])
        with c_sub2:
            suspect_type = st.selectbox(t["suspect_label"], t["suspects"])

    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        st.audio(uploaded_file)
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            btn_scan = st.button(t["check_btn"], type="primary", use_container_width=True)
    else:
        btn_scan = False

    if btn_scan and uploaded_file is not None:
        st.markdown(f"<h3 style='margin: 30px 0 20px 0; color: #0f172a; font-weight: 800;'>{t['result_heading']}</h3>", unsafe_allow_html=True)

        with st.spinner("Đang bóc tách 40 tham số âm học và quét ma trận ngữ nghĩa..."):
            result = run_pipeline(uploaded_file, is_mic=False)

        ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{ts_now}_{uploaded_file.name}"
        saved_path = os.path.join(AUDIO_STORE_DIR, saved_filename)
        with open(saved_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        score = float(result["score"])
        threat = str(result["threat"])
        p_acoustic = float(result.get("acoustic_fake_prob", 0.0))
        p_nlp = float(result.get("nlp_fake_prob", 0.0))
        inv_name = st.session_state["username"] if st.session_state["is_logged_in"] else "Khach (Guest)"

        try:
            conn = sqlite3.connect("forensic_admin.db")
            c = conn.cursor()
            c.execute("""
                INSERT INTO audit_logs (timestamp, filename, audio_path, channel, suspect, acoustic_score, nlp_score, threat_score, verdict, investigator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uploaded_file.name,
                saved_path,
                call_source,
                suspect_type,
                p_acoustic,
                p_nlp,
                score,
                threat,
                inv_name
            ))
            conn.commit()
            conn.close()
            st.toast("Đã ghi nhận thành công vào cơ sở dữ liệu nhật ký.")
        except Exception as e:
            st.error(f"Lỗi ghi database: {e}")

        if score >= 70 or threat == "Danger":
            st.markdown(f'<div class="status-badge-high">{t["high_threat"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-badge-safe">{t["safe_threat"]}</div>', unsafe_allow_html=True)

        c_score, c_detail, c_status = st.columns([1.1, 1.3, 1.6], gap="medium")

        score_color = "#dc2626" if score >= 70 else ("#d97706" if score >= 40 else "#16a34a")
        badge_tag = '<span class="badge-danger">NGUY HIỂM CAO (DEEPFAKE)</span>' if score >= 70 else ('<span class="badge-warning">CẢNH BÁO (NGHI VẤN)</span>' if score >= 40 else '<span class="badge-safe">AN TOÀN (REAL VOICE)</span>')

        with c_score:
            st.markdown(f"""
            <div class="result-container-left">
                <p style="color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin: 0;">Chỉ Số Nguy Cơ Tổng Hợp</p>
                <div style="font-size: 3.6rem; font-weight: 900; color: {score_color}; line-height: 1.1; margin: 10px 0;">
                    {score}<span style="font-size: 2rem;">%</span>
                </div>
                <div>{badge_tag}</div>
            </div>
            """, unsafe_allow_html=True)

        with c_detail:
            st.markdown(f"""
            <div class="custom-card">
                <p style="color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 12px;">Đo Lường Phân Tầng Dual-Engine</p>
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 700;">
                        <span>Giả mạo Âm học (AI Voice):</span>
                        <span style="color: #dc2626;">{p_acoustic}%</span>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 700;">
                        <span>Kịch bản thao túng (NLP):</span>
                        <span style="color: #7c3aed;">{p_nlp}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_status:
            flags = result.get("flags", [])
            flags_html = " ".join([f'<span style="background:#fee2e2; color:#dc2626; padding:3px 10px; border-radius:4px; font-weight:700; font-size:0.85rem; margin-right:6px; display:inline-block; margin-bottom:4px;">{kw}</span>' for kw in flags]) if flags else ""
            desc_text = f"Phát hiện {len(flags)} dấu hiệu đe dọa / giục chuyển tiền / cấp cứu viện phí." if flags else "Không phát hiện từ khóa bất thường trong kịch bản đàm thoại."
            transcript_text = result.get("transcript", "")

            st.markdown(f"""
            <div class="custom-card">
                <p style="color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;">Dấu Hiệu Thao Túng Tâm Lý</p>
                <div style="font-size: 0.92rem; color: #475569; line-height: 1.5; margin-bottom: 8px;">{desc_text}</div>
                <div style="margin-bottom: 12px;">{flags_html}</div>
                <div style="background: #f8fafc; border-left: 3px solid #3b82f6; padding: 8px 12px; border-radius: 4px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Nội dung bóc băng (Whisper):</span>
                    <p style="font-size: 0.88rem; color: #1e293b; margin: 4px 0 0 0; font-style: italic;">"{transcript_text}"</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2, gap="medium")
        with col_g1:
            st.markdown("##### Phổ Tần Số Âm Học (Mel-Spectrogram)")
            if result.get("figure") is not None:
                st.pyplot(result["figure"])
        with col_g2:
            st.markdown("##### Trọng Số Đóng Góp Đặc Trưng (XAI)")
            if result.get("xai_fig") is not None:
                st.pyplot(result["xai_fig"])

    # Audit Log
    st.markdown(f"""
        <div class="section-title-container" style="margin-top: 50px;">
            <h2 class="section-title-text">{t["history_title"]}</h2>
            <div class="section-title-underline"></div>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state["is_logged_in"]:
        st.markdown(f"<div class='custom-card' style='text-align: center; color: #64748b;'>{t['auth_required']}</div>", unsafe_allow_html=True)
    else:
        is_admin = (st.session_state["role"] == "admin")
        username = st.session_state["username"]

        if is_admin:
            st.info("Quyền Quản Trị Viên (Admin): Hiển thị toàn bộ nhật ký các phiên giám định trên hệ thống.")
        else:
            st.info(f"Tài khoản điều tra viên ({username}): Hiển thị lịch sử các phiên giám định cá nhân.")

        logs = get_scans(username=username, is_admin=is_admin)

        if not logs:
            st.caption("Chưa có bản ghi giám định nào trong cơ sở dữ liệu.")
        else:
            for r in logs:
                r_id, r_time, r_fname, r_path, r_channel, r_suspect, r_acou, r_nlp, r_threat, r_verdict, r_inv = r
                badge_cls = "badge-danger" if r_threat >= 70 else ("badge-warning" if r_threat >= 40 else "badge-safe")

                st.markdown(f"""
                <div class="log-item-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 800; font-size: 1.05rem; color: #0f172a;">Tệp: {r_fname}</span>
                        <span class="{badge_cls}">{r_verdict} ({r_threat}%)</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.88rem; margin: 6px 0 10px 0;">
                        Thời gian: <b>{r_time}</b> | Cán bộ: <b>{r_inv}</b> | Kênh: <b>{r_channel}</b> | Âm học: <b>{r_acou}%</b> | NLP: <b>{r_nlp}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c_play, c_down = st.columns([3.8, 1.2])
                with c_play:
                    if os.path.exists(r_path):
                        st.audio(r_path)
                    else:
                        st.caption("Tệp âm thanh nguồn không khả dụng.")
                with c_down:
                    rep_txt = f"BIEN BAN GIAM DINH\nID: {r_id}\nThoi gian: {r_time}\nTep: {r_fname}\nThreat: {r_threat}%\nVerdict: {r_verdict}\nInvestigator: {r_inv}"
                    st.download_button("Xuất biên bản (.txt)", rep_txt, file_name=f"Report_{r_id}.txt", key=f"dl_{r_id}", use_container_width=True)
                st.write("")

# TAB 2: HƯỚNG DẪN
elif st.session_state["active_tab"] == "Hướng dẫn":
    st.markdown('<div style="margin-top: 80px;">', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align: center; margin: 30px 0 40px 0;">
            <h1 style="color: #0f172a; font-weight: 900; font-size: 2.3rem;">{t["guide_heading"]}</h1>
            <p style="color: #64748b; font-size: 1.15rem;">{t["guide_sub"]}</p>
        </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2, gap="large")
    with col_g1:
        st.markdown("""
            <div class="custom-card">
                <h4 style="color: #1e3a8a; font-weight: 800;">Bước 1: Chuẩn bị tệp âm thanh gốc</h4>
                <p style="color: #475569; line-height: 1.6;">Nạp tệp ghi âm cuộc gọi định dạng tiêu chuẩn <b>.wav</b> hoặc <b>.mp3</b> được trích xuất trực tiếp từ thiết bị hoặc nhật ký viễn thông.</p>
            </div>
            <div class="custom-card">
                <h4 style="color: #1e3a8a; font-weight: 800;">Bước 2: Phân tích phân tầng Dual-Engine</h4>
                <p style="color: #475569; line-height: 1.6;">Hệ thống đồng thời bóc tách <b>40 tham số âm học</b> để phát hiện dấu vết Vocoder AI và bóc băng <b>Whisper NLP</b> để nhận diện kịch bản lừa đảo.</p>
            </div>
        """, unsafe_allow_html=True)

    with col_g2:
        st.markdown("""
            <div class="custom-card">
                <h4 style="color: #1e3a8a; font-weight: 800;">Bước 3: Đánh giá thang đo rủi ro</h4>
                <p style="color: #475569; line-height: 1.6;">
                    • <b>AN TOÀN (< 40%):</b> Giọng sinh học tự nhiên.<br>
                    • <b>CẢNH BÁO (40% - 69%):</b> Nghi vấn dải tần nén bất thường hoặc dính từ khóa cảnh giác.<br>
                    • <b>NGUY HIỂM CAO (≥ 70%):</b> Tín hiệu tổng hợp nhân tạo kết hợp yếu tố thao túng.
                </p>
            </div>
            <div class="custom-card">
                <h4 style="color: #1e3a8a; font-weight: 800;">Bước 4: Xuất biên bản kỹ thuật</h4>
                <p style="color: #475569; line-height: 1.6;">Tải xuống biên bản kiểm định chi tiết (.txt) để hoàn thiện hồ sơ nghiệp vụ bàn giao cơ quan có thẩm quyền.</p>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: ĐĂNG NHẬP / ĐĂNG KÝ
elif st.session_state["active_tab"] == "Đăng nhập / Đăng ký":
    st.markdown('<div style="margin-top: 80px;">', unsafe_allow_html=True)
    col_a1, col_a2, col_a3 = st.columns([1.5, 3.2, 1.5])
    with col_a2:
        if st.session_state["is_logged_in"]:
            st.markdown(f"""
                <div class="custom-card" style="border-top: 5px solid #2563eb; text-align: center;">
                    <h3 style="color: #0f172a; margin-top: 0;">Cán bộ: <b style="color: #2563eb;">{st.session_state['username']}</b></h3>
                    <p style="color: #64748b;">Vai trò: <b>{'Quản Trị Viên (Administrator)' if st.session_state['role'] == 'admin' else 'Điều Tra Viên (User)'}</b></p>
                    <p style="color: #16a34a; font-weight: 700;">Trạng thái: Đã kết nối cơ sở dữ liệu forensic_admin.db thành công.</p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Đăng xuất tài khoản", type="primary", use_container_width=True):
                st.session_state["is_logged_in"] = False
                st.session_state["username"] = ""
                st.session_state["role"] = "guest"
                st.rerun()
        else:
            st.markdown(f"""
                <div class="custom-card" style="margin-bottom: 15px; text-align: center;">
                    <h2 style="color: #0f172a; font-weight: 800; margin: 0;">{t["auth_heading"]}</h2>
                    <p style="color: #64748b; font-size: 0.9rem; margin-top: 6px;">Tài khoản Quản trị mặc định: <b>duy</b> / <b>123456</b></p>
                </div>
            """, unsafe_allow_html=True)

            tab_in, tab_up = st.tabs(["Đăng nhập", "Đăng ký"])

            with tab_in:
                l_user = st.text_input("Tên đăng nhập", placeholder="duy hoặc user")
                l_pass = st.text_input("Mật khẩu", type="password", placeholder="••••••••")
                if st.button("XÁC NHẬN ĐĂNG NHẬP", type="primary", use_container_width=True):
                    res = check_login(l_user, l_pass)
                    if res:
                        st.session_state["is_logged_in"] = True
                        st.session_state["username"] = res[0]
                        st.session_state["role"] = res[1]
                        st.success(f"Xác thực thành công. Vai trò: {res[1].upper()}")
                        st.session_state["active_tab"] = "Trang chủ"
                        st.rerun()
                    else:
                        st.error("Tên đăng nhập hoặc mật khẩu không chính xác.")

            with tab_up:
                r_name = st.text_input("Họ và tên cán bộ")
                r_agency = st.selectbox("Đơn vị", ["Cục An Ninh Mạng", "Phòng Cảnh Sát Hình Sự", "Viện Khoa Học Hình Sự", "Khối Quản Lý Rủi Ro Ngân Hàng"])
                r_user = st.text_input("Tên tài khoản mới")
                r_pass = st.text_input("Mật khẩu mới", type="password")
                if st.button("TẠO TÀI KHOẢN MỚI", use_container_width=True):
                    if r_user and r_pass:
                        if register_user(r_user, r_pass, r_name, r_agency):
                            st.success("Đăng ký tài khoản thành công. Vui lòng chuyển sang tab Đăng nhập.")
                        else:
                            st.error("Tên tài khoản này đã tồn tại trong hệ thống.")
                    else:
                        st.warning("Vui lòng điền đầy đủ các thông tin.")
    st.markdown('</div>', unsafe_allow_html=True)