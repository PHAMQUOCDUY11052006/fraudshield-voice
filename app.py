import streamlit as st
import pandas as pd
import os
import sqlite3
from datetime import datetime
from core_ai import run_pipeline

# ==============================
# CẤU HÌNH TRANG & GIAO DIỆN
# ==============================
st.set_page_config(
    page_title="HỆ THỐNG GIÁM ĐỊNH & ĐIỀU TRA CUỘC GỌI DEEPFAKE",
    page_icon="🛡️",
    layout="wide"
)

AUDIO_STORE_DIR = "saved_audios"
os.makedirs(AUDIO_STORE_DIR, exist_ok=True)

try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ==============================
# QUẢN TRỊ CƠ SỞ DỮ LIỆU SQLITE
# ==============================
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
    
    # Khởi tạo mặc định admin Duy và user thường
    c.execute("SELECT * FROM users WHERE username = 'duy'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES ('duy', '123456', 'Nguyễn Duy (Lead Admin)', 'Ban Chỉ Đạo An Ninh Mạng', 'admin')")
    else:
        c.execute("UPDATE users SET password = '123456', role = 'admin' WHERE username = 'duy'")

    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES ('admin', 'admin123', 'Quản Trị Viên Hệ Thống', 'Cục An Ninh Mạng', 'admin')")

    c.execute("SELECT * FROM users WHERE username = 'user'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, fullname, agency, role) VALUES ('user', 'user123', 'Điều Tra Viên Cơ Sở', 'Công An Địa Phương', 'user')")
        
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

# ==============================
# QUẢN LÝ SESSION STATE
# ==============================
if "lang" not in st.session_state:
    st.session_state["lang"] = "Tiếng Việt"
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = "guest"
if "consent_given" not in st.session_state:
    st.session_state["consent_given"] = False

# ==============================
# TỪ ĐIỂN ĐA NGÔN NGỮ
# ==============================
TEXTS = {
    "Tiếng Việt": {
        "title": "HỆ THỐNG GIÁM ĐỊNH & ĐIỀU TRA CUỘC GỌI DEEPFAKE",
        "menu_home": "Trang chủ",
        "menu_guide": "Hướng dẫn",
        "menu_auth": "Đăng nhập / Đăng ký",
        "input_section": "Nạp dữ liệu âm thanh phân tích",
        "file_upload_label": "Chọn tệp âm thanh cần giám định (.wav, .mp3)",
        "call_source_label": "Nguồn cuộc gọi:",
        "suspect_label": "Đối tượng nghi ngờ giả mạo:",
        "sources": ["Mạng di động (GSM)", "Zalo / Telegram", "Ghi âm chứng thực", "Khác"],
        "suspects": ["Cơ quan Công an / Viện kiểm sát", "Ngân hàng / Tài chính", "Người thân", "Khác"],
        "run_btn": "TIẾN HÀNH GIÁM ĐỊNH",
        "info_wait": "Đang trích xuất 40 đặc trưng âm học và quét ngữ nghĩa...",
        "result_title": "KẾT QUẢ PHÂN TÍCH VÀ ĐÁNH GIÁ CHUYÊN SÂU",
        "sys_info_title": "Thông tin chi tiết phiên giám định",
        "risk_score_label": "Chỉ số rủi ro tổng hợp",
        "conclusion": "Kết luận:",
        "high_threat": "CẢNH BÁO: Phát hiện tín hiệu âm thanh có dấu hiệu can thiệp công nghệ giả mạo (AI Voice).",
        "safe_threat": "AN TOÀN: Không phát hiện dấu hiệu bất thường từ tệp âm thanh (Giọng sinh học tự nhiên).",
        "manipulation_label": "Dấu hiệu thao túng tâm lý",
        "no_flags": "Không phát hiện từ khóa kịch bản độc hại.",
        "tab_spec": "Biểu đồ phổ tần số (Mel-Spectrogram)",
        "tab_xai": "Phân tích trọng số đặc trưng (XAI)",
        "guide_title": "Hướng dẫn sử dụng hệ thống",
        "guide_tabs": ["Quy trình nghiệp vụ", "Cơ chế Dual-Engine & Thang đo"],
        "auth_title": "Cổng quản lý tài khoản điều tra viên",
        "login_tab": "Đăng nhập hệ thống",
        "reg_tab": "Đăng ký tài khoản mới",
        "login_btn": "Xác nhận đăng nhập",
        "reg_btn": "Đăng ký tài khoản",
        "logout_btn": "Đăng xuất tài khoản",
        "history_title": "Lịch sử các phiên giám định gần đây (Audit Log)"
    },
    "English": {
        "title": "DEEPFAKE CALL INVESTIGATION & FORENSIC SYSTEM",
        "menu_home": "Home",
        "menu_guide": "Guide",
        "menu_auth": "Login / Register",
        "input_section": "Audio Data Input for Analysis",
        "file_upload_label": "Select audio file for forensics (.wav, .mp3)",
        "call_source_label": "Call Source:",
        "suspect_label": "Suspicious Impersonation Target:",
        "sources": ["Mobile Network (GSM)", "Zalo / Telegram", "Forensic Recording", "Other"],
        "suspects": ["Police / Procuratorate", "Bank / Finance", "Relative", "Other"],
        "run_btn": "PROCEED FORENSIC ANALYSIS",
        "info_wait": "Extracting 40 acoustic features and analyzing linguistic context...",
        "result_title": "IN-DEPTH ANALYSIS & ASSESSMENT RESULTS",
        "sys_info_title": "Forensic Session Details",
        "risk_score_label": "Composite Risk Score",
        "conclusion": "Conclusion:",
        "high_threat": "WARNING: Audio signal exhibits strong markers of artificial deepfake synthesis.",
        "safe_threat": "SAFE: No abnormal indicators detected (Natural biological human voice).",
        "manipulation_label": "Psychological Manipulation Flags",
        "no_flags": "No malicious script keywords detected.",
        "tab_spec": "Frequency Spectrum (Mel-Spectrogram)",
        "tab_xai": "Feature Importance (XAI)",
        "guide_title": "System User Guide",
        "guide_tabs": ["Standard Protocol", "Dual-Engine & Scoring"],
        "auth_title": "User Account Management Portal",
        "login_tab": "System Login",
        "reg_tab": "Register New Account",
        "login_btn": "Confirm Login",
        "reg_btn": "Register Account",
        "logout_btn": "Log out",
        "history_title": "Recent Forensic Session History (Audit Log)"
    }
}

t = TEXTS[st.session_state["lang"]]

if not st.session_state["consent_given"]:
    @st.dialog("Quy chế bảo mật hệ thống / Security Policy")
    def consent_dialog():
        st.write("Chào mừng bạn đến với Hệ thống Giám định & Điều tra cuộc gọi Deepfake. Vui lòng xác nhận đồng ý với quy chế xử lý dữ liệu để tiếp tục.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Từ chối / Decline", use_container_width=True):
                st.stop()
        with col_c2:
            if st.button("Đồng ý / Agree", type="primary", use_container_width=True):
                st.session_state["consent_given"] = True
                st.rerun()
    consent_dialog()

# Banner Header
st.markdown(f"""
    <div class="portal-header">
        <h1 class="portal-header-title">{t['title']}</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# Tabs điều hướng & Ngôn ngữ
col_menu, col_lang = st.columns([5.2, 1.0], vertical_alignment="center")

with col_menu:
    menu_selection = st.tabs([
        t["menu_home"],
        t["menu_guide"],
        f"{t['menu_auth']} ({st.session_state['username']})" if st.session_state["logged_in"] else t["menu_auth"]
    ])

with col_lang:
    selected_lang = st.selectbox(
        "Language",
        ["Tiếng Việt", "English"],
        index=0 if st.session_state["lang"] == "Tiếng Việt" else 1,
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state["lang"]:
        st.session_state["lang"] = selected_lang
        st.rerun()

# ==============================
# TAB 1: TRANG CHỦ
# ==============================
with menu_selection[0]:
    st.markdown(f"<h2 style='text-align: center; color: #1a365d; margin-top: 15px; margin-bottom: 20px;'>{t['input_section']}</h2>", unsafe_allow_html=True)
    
    col_left_input, col_right_input = st.columns(2, gap="large")

    with col_left_input:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(t["file_upload_label"], type=["wav", "mp3"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right_input:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        call_source = st.selectbox(t["call_source_label"], t["sources"])
        suspect_type = st.selectbox(t["suspect_label"], t["suspects"])
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        st.audio(uploaded_file)
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            btn_run = st.button(t["run_btn"], type="primary", use_container_width=True)
    else:
        btn_run = False
        st.info("Vui lòng tải tệp âm thanh ở cột bên trái để thực hiện giám định." if st.session_state["lang"] == "Tiếng Việt" else "Please upload an audio file on the left to proceed.")

    # XỬ LÝ PHÂN TÍCH & GHI DATABASE
    if btn_run and uploaded_file is not None:
        st.markdown(f"<h2 style='text-align: center; color: #1a365d; margin-top: 30px;'>{t['result_title']}</h2>", unsafe_allow_html=True)
        
        with st.spinner(t["info_wait"]):
            result = run_pipeline(uploaded_file, is_mic=False)

        # Lưu audio tĩnh để phát lại trong phần log
        ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{ts_now}_{uploaded_file.name}"
        saved_path = os.path.join(AUDIO_STORE_DIR, saved_filename)
        with open(saved_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        score = float(result["score"])
        threat = str(result["threat"])
        p_acoustic = float(result.get("acoustic_fake_prob", 0.0))
        p_nlp = float(result.get("nlp_fake_prob", 0.0))
        inv_name = st.session_state["username"] if st.session_state["logged_in"] else "Khách (Guest)"

        # Ghi trực tiếp vào SQLite (luôn lưu dù đã đăng nhập hay chưa)
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
            st.toast("✓ Đã lưu thành công vào cơ sở dữ liệu nhật ký!", icon="💾")
        except Exception as e:
            st.error(f"Lỗi ghi database: {e}")

        # Bảng thông tin phiên
        st.markdown(f"<h3 style='text-align: center;'>{t['sys_info_title']}</h3>", unsafe_allow_html=True)
        df_info = pd.DataFrame({
            "Thông số hệ thống" if st.session_state["lang"] == "Tiếng Việt" else "System Parameter": [
                "Tên tệp âm thanh", "Nguồn cuộc gọi", "Đối tượng nghi vấn", "Điều tra viên phụ trách"
            ],
            "Giá trị ghi nhận" if st.session_state["lang"] == "Tiếng Việt" else "Recorded Value": [
                uploaded_file.name, call_source, suspect_type, inv_name
            ]
        })
        st.dataframe(df_info, use_container_width=True, hide_index=True)
        st.write("")

        # Khung chỉ số rủi ro
        col_res_left, col_res_right = st.columns([1, 2], gap="large")

        with col_res_left:
            score_color = '#9b2c2c' if score >= 70 else ('#d69e2e' if score >= 40 else '#22543d')
            st.markdown(f"""
                <div class="result-container-left">
                    <p class="risk-score-title">{t['risk_score_label']}</p>
                    <h1 class="risk-score-number" style="color: {score_color};">{score}%</h1>
                    <p class="risk-score-conclusion"><b>{t['conclusion']}</b> {threat}</p>
                </div>
            """, unsafe_allow_html=True)

        with col_res_right:
            if score >= 70 or "Danger" in threat:
                st.markdown(f'<div class="status-badge-high">{t["high_threat"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-badge-safe">{t["safe_threat"]}</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="custom-card" style="padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 8px;">
                    <span>Giả mạo Âm học (AI Voice - 85%):</span>
                    <span style="color: #dc2626;">{p_acoustic}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-weight: 700;">
                    <span>Kịch bản thao túng (NLP - 15%):</span>
                    <span style="color: #7c3aed;">{p_nlp}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"<h4>{t['manipulation_label']}</h4>", unsafe_allow_html=True)
            if result.get("flags"):
                for flag in result["flags"]:
                    st.warning(f"⚠️ Phát hiện từ khóa nghi vấn: {flag}")
            else:
                st.success(t["no_flags"])

        # Biểu đồ âm học & XAI
        st.write("")
        col_sub1, col_sub2 = st.columns(2, gap="large")
        with col_sub1:
            st.markdown(f"<h4>{t['tab_spec']}</h4>", unsafe_allow_html=True)
            if result.get("figure") is not None:
                st.pyplot(result["figure"])
        with col_sub2:
            st.markdown(f"<h4>{t['tab_xai']}</h4>", unsafe_allow_html=True)
            if result.get("xai_fig") is not None:
                st.pyplot(result["xai_fig"])

    # LỊCH SỬ GIÁM ĐỊNH (AUDIT LOG KÈM FILE AUDIO)
    st.markdown("<hr style='margin-top: 30px;'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{t['history_title']}</h3>", unsafe_allow_html=True)

    if not st.session_state["logged_in"]:
        st.info("🔒 Vui lòng **Đăng nhập tài khoản** để xem danh sách lịch sử và nghe lại các tệp âm thanh đã giám định.")
    else:
        is_admin = (st.session_state["role"] == "admin")
        username = st.session_state["username"]

        if is_admin:
            st.success("👑 **Tài khoản Quản trị viên (Admin):** Bạn đang xem toàn bộ lịch sử giám định của mọi tài khoản trong hệ thống.")
        else:
            st.info(f"👤 **Tài khoản cá nhân ({username}):** Hiển thị lịch sử các phiên giám định do bạn thực hiện.")

        records = get_scans(username=username, is_admin=is_admin)

        if not records:
            st.caption("Chưa có phiên giám định nào được ghi nhận.")
        else:
            for r in records:
                r_id, r_time, r_fname, r_path, r_channel, r_suspect, r_acou, r_nlp, r_threat, r_verdict, r_inv = r
                badge_bg = "#fdf2f2" if r_threat >= 70 else ("#fefcbf" if r_threat >= 40 else "#f0fff4")
                badge_color = "#9b2c2c" if r_threat >= 70 else ("#b7791f" if r_threat >= 40 else "#22543d")

                st.markdown(f"""
                <div class="custom-card" style="text-align: left; padding: 15px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 1.05rem; color: #1a365d;">📄 {r_fname}</span>
                        <span style="background: {badge_bg}; color: {badge_color}; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.9rem;">
                            {r_verdict} ({r_threat}%)
                        </span>
                    </div>
                    <div style="color: #4a5568; font-size: 0.9rem; margin-top: 5px;">
                        Thời gian: <b>{r_time}</b> | Điều tra viên: <b>{r_inv}</b> | Kênh: <b>{r_channel}</b> | Âm học AI: <b>{r_acou}%</b> | Kịch bản NLP: <b>{r_nlp}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_p, col_d = st.columns([4, 1])
                with col_p:
                    if os.path.exists(r_path):
                        st.audio(r_path)
                    else:
                        st.caption("Tệp âm thanh nguồn không tồn tại.")
                with col_d:
                    rep_txt = f"BIEN BAN GIAM DINH\nID: {r_id}\nTime: {r_time}\nFile: {r_fname}\nThreat: {r_threat}%\nVerdict: {r_verdict}\nInvestigator: {r_inv}"
                    st.download_button("Xuất biên bản", rep_txt, file_name=f"Report_{r_id}.txt", key=f"btn_dl_{r_id}", use_container_width=True)
                st.write("")

# ==============================
# TAB 2: HƯỚNG DẪN
# ==============================
with menu_selection[1]:
    st.markdown(f"<h2 style='text-align: center; color: #1a365d;'>{t['guide_title']}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    g_tab1, g_tab2 = st.tabs(t["guide_tabs"])
    with g_tab1:
        st.markdown("""
        <div class="custom-card" style="text-align: left;">
            <h4 style="color: #1a365d;">Quy trình 3 bước vận hành giám định pháp y âm thanh</h4>
            <p><b>Bước 1: Nạp tệp âm thanh gốc (.wav, .mp3)</b><br>Tải lên bản ghi âm cuộc gọi trực tiếp từ GSM hoặc Zalo/Telegram. Tránh thu lại qua loa ngoài để tránh suy hao đặc trưng phổ tần số cao.</p>
            <p><b>Bước 2: Hệ thống chạy mô hình phân tích Dual-Engine</b><br>Hệ thống tự động kích hoạt bộ trích xuất 40 đặc trưng âm học kết hợp mô hình học máy và phân tích ngữ nghĩa bóc băng.</p>
            <p><b>Bước 3: Đánh giá bằng chứng và xuất biên bản</b><br>Đối chiếu chỉ số rủi ro, phân tích tương quan Mel-Spectrogram và tải xuống biên bản kỹ thuật có chữ ký giám định.</p>
        </div>
        """, unsafe_allow_html=True)
    with g_tab2:
        st.markdown("""
        <div class="custom-card" style="text-align: left;">
            <h4 style="color: #1a365d;">Thang phân loại rủi ro tổng hợp</h4>
            <ul>
                <li><b>AN TOÀN (&lt; 40%):</b> Giọng nói tự nhiên, hài hòa năng lượng các dải hài âm Formant.</li>
                <li><b>CẢNH BÁO (40% - 69%):</b> Nghi vấn có dấu hiệu nén dải tần hoặc xuất hiện từ ngữ gây áp lực tâm lý.</li>
                <li><b>NGUY HIỂM CAO (≥ 70%):</b> Dấu hiệu can thiệp Vocoder/AI Voice rõ rệt, khuyến nghị phong tỏa giao dịch ngay.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# TAB 3: ĐĂNG NHẬP / ĐĂNG KÝ
# ==============================
with menu_selection[2]:
    st.markdown(f"<h2 style='text-align: center; color: #1a365d;'>{t['auth_title']}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not st.session_state["logged_in"]:
        a_tab1, a_tab2 = st.tabs([t["login_tab"], t["reg_tab"]])
        with a_tab1:
            st.caption("Tài khoản Admin kiểm thử: `duy` / `123456` hoặc `admin` / `admin123`")
            l_user = st.text_input("Tên đăng nhập" if st.session_state["lang"] == "Tiếng Việt" else "Username")
            l_pass = st.text_input("Mật khẩu" if st.session_state["lang"] == "Tiếng Việt" else "Password", type="password")
            if st.button(t["login_btn"], type="primary"):
                user_res = check_login(l_user, l_pass)
                if user_res:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_res[0]
                    st.session_state["role"] = user_res[1]
                    st.success(f"Đăng nhập thành công! Quyền hạn: {user_res[1].upper()}")
                    st.rerun()
                else:
                    st.error("Tên đăng nhập hoặc mật khẩu không chính xác!")
        with a_tab2:
            r_fullname = st.text_input("Họ và tên điều tra viên")
            r_agency = st.selectbox("Đơn vị công tác", ["Cục An Ninh Mạng", "Phòng Cảnh Sát Hình Sự", "Viện Khoa Học Hình Sự", "Ngân Hàng / Tài Chính"])
            r_user = st.text_input("Tên đăng nhập mới")
            r_pass = st.text_input("Mật khẩu mới", type="password")
            if st.button(t["reg_btn"]):
                if r_user and r_pass:
                    if register_user(r_user, r_pass, r_fullname, r_agency):
                        st.success("Đăng ký tài khoản thành công! Vui lòng chuyển sang tab Đăng nhập.")
                    else:
                        st.error("Tên đăng nhập đã tồn tại trên hệ thống!")
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin!")
    else:
        st.markdown(f"""
        <div class="custom-card">
            <h3>Xin chào, <b style="color: #1a365d;">{st.session_state['username']}</b>!</h3>
            <p>Vai trò hệ thống: <b>{'Quản Trị Viên (Administrator)' if st.session_state['role'] == 'admin' else 'Điều Tra Viên (User)'}</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t["logout_btn"], type="primary"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["role"] = "guest"
            st.rerun()