import streamlit as st
import pandas as pd
from core_ai import run_pipeline
from database import init_db, add_user, verify_user, save_scan_result, get_user_scans

# ==============================
# CẤU HÌNH TRANG & CƠ SỞ DỮ LIỆU
# ==============================
st.set_page_config(
    page_title="HỆ THỐNG GIÁM ĐỊNH & ĐIỀU TRA CUỘC GỌI DEEPFAKE",
    page_icon="🛡️",
    layout="wide"
)

init_db()

try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Quản lý phiên làm việc (Session State)
if "lang" not in st.session_state:
    st.session_state["lang"] = "Tiếng Việt"
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "consent_given" not in st.session_state:
    st.session_state["consent_given"] = False

TEXTS = {
    "Tiếng Việt": {
        "title": "HỆ THỐNG GIÁM ĐỊNH & ĐIỀU TRA CUỘC GỌI DEEPFAKE",
        "menu_home": "Trang chủ",
        "menu_guide": "Hướng dẫn",
        "menu_auth": "Đăng nhập / Đăng ký",
        "input_section": "Nạp dữ liệu âm thanh phân tích",
        "method_label": "Phương thức nạp:",
        "method_file": "Tải tệp âm thanh (.wav, .mp3)",
        "method_mic": "Thu âm trực tiếp qua Micro",
        "file_upload_label": "Chọn tệp âm thanh cần giám định",
        "mic_label": "Nhấn để bắt đầu/dừng ghi âm trực tiếp",
        "call_source_label": "Nguồn cuộc gọi:",
        "suspect_label": "Đối tượng nghi ngờ giả mạo:",
        "sources": ["GSM (Mạng di động)", "Zalo", "Telegram", "Micro trực tiếp", "Khác"],
        "suspects": ["Cơ quan Công an / Viện kiểm sát", "Ngân hàng", "Người thân", "Khác"],
        "run_btn": "TIẾN HÀNH GIÁM ĐỊNH",
        "info_wait": "Đang trích xuất đặc trưng và phân tích pháp y số...",
        "result_title": "KẾT QUẢ PHÂN TÍCH VÀ ĐÁNH GIÁ CHUYÊN SÂU",
        "sys_info_title": "Thông tin chi tiết phiên giám định",
        "risk_score_label": "Chỉ số rủi ro Deepfake",
        "conclusion": "Kết luận:",
        "high_threat": "CẢNH BÁO: Phát hiện tín hiệu âm thanh có dấu hiệu can thiệp công nghệ giả mạo.",
        "safe_threat": "AN TOÀN: Không phát hiện dấu hiệu bất thường từ tệp âm thanh.",
        "transcript_label": "Bản ghi hội thoại kèm mốc thời gian",
        "manipulation_label": "Dấu hiệu thao túng tâm lý",
        "no_flags": "Không phát hiện từ khóa kịch bản độc hại.",
        "tab_spec": "Biểu đồ phổ tần số (Mel-Spectrogram)",
        "tab_xai": "Phân tích trọng số Explainable AI (XAI)",
        "guide_title": "Hướng dẫn sử dụng hệ thống",
        "guide_tabs": ["Hướng dẫn bằng văn bản", "Quy trình phân tích"],
        "auth_title": "Cổng quản lý tài khoản người sử dụng",
        "login_tab": "Đăng nhập hệ thống",
        "reg_tab": "Đăng ký tài khoản mới",
        "login_btn": "Xác nhận đăng nhập",
        "reg_btn": "Đăng ký tài khoản",
        "logout_btn": "Đăng xuất tài khoản",
        "history_title": "Lịch sử các phiên giám định của tài khoản"
    },
    "English": {
        "title": "DEEPFAKE CALL INVESTIGATION & FORENSIC SYSTEM",
        "menu_home": "Home",
        "menu_guide": "Guide",
        "menu_auth": "Login / Register",
        "input_section": "Audio Data Input for Analysis",
        "method_label": "Input Method:",
        "method_file": "Upload Audio File (.wav, .mp3)",
        "method_mic": "Direct Microphone Recording",
        "file_upload_label": "Select audio file for forensics",
        "mic_label": "Click to start/stop live recording",
        "call_source_label": "Call Source:",
        "suspect_label": "Suspicious Impersonation Target:",
        "sources": ["Mobile Network (GSM)", "Zalo", "Telegram", "Direct Mic", "Other"],
        "suspects": ["Police / Procuratorate", "Bank", "Relative", "Other"],
        "run_btn": "PROCEED FORENSIC ANALYSIS",
        "info_wait": "Extracting features and analyzing forensic signals...",
        "result_title": "IN-DEPTH ANALYSIS & ASSESSMENT RESULTS",
        "sys_info_title": "Forensic Session Details",
        "risk_score_label": "Deepfake Risk Score",
        "conclusion": "Conclusion:",
        "high_threat": "WARNING: Audio signal shows signs of artificial deepfake manipulation.",
        "safe_threat": "SAFE: No abnormal signs detected in the audio file.",
        "transcript_label": "Conversation Transcript with Timestamps",
        "manipulation_label": "Manipulation Flags",
        "no_flags": "No malicious script keywords detected.",
        "tab_spec": "Frequency Spectrum (Mel-Spectrogram)",
        "tab_xai": "Explainable AI (XAI) Weight Distribution",
        "guide_title": "System User Guide",
        "guide_tabs": ["Text Guide", "Workflow Diagram"],
        "auth_title": "User Account Management Portal",
        "login_tab": "System Login",
        "reg_tab": "Register New Account",
        "login_btn": "Confirm Login",
        "reg_btn": "Register Account",
        "logout_btn": "Log out",
        "history_title": "Account Forensic Session History"
    }
}

t = TEXTS[st.session_state["lang"]]

# Quy chế bảo mật
if not st.session_state["consent_given"]:
    @st.dialog("Quy chế bảo mật hệ thống / System Security Policy")
    def consent_dialog():
        st.write("Chào mừng bạn đến với Hệ thống Giám định & Điều tra cuộc gọi Deepfake. Dữ liệu âm thanh của bạn được xử lý bảo mật và tuân thủ các quy tắc đạo đức AI.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Từ chối / Decline", use_container_width=True):
                st.stop()
        with col_c2:
            if st.button("Đồng ý / Agree", type="primary", use_container_width=True):
                st.session_state["consent_given"] = True
                st.rerun()
    consent_dialog()

# ==============================
# 1. BANNER PHÍA TRÊN CÙNG
# ==============================
st.markdown(f"""
    <div class="portal-header">
        <h1 class="portal-header-title">{t['title']}</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# ==============================
# 2. MENU & NGÔN NGỮ CĂN GIỮA
# ==============================
col_menu, col_lang = st.columns([5, 1], gap="small")

with col_menu:
    menu_selection = st.tabs([
        t["menu_home"],
        t["menu_guide"],
        t["menu_auth"]
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
# 3. NỘI DUNG CHI TIẾT
# ==============================

# --- TAB 1: TRANG CHỦ ---
with menu_selection[0]:
    st.markdown(f"<h2 style='text-align: center; color: #1a365d; margin-top: 15px; margin-bottom: 20px;'>{t['input_section']}</h2>", unsafe_allow_html=True)
    
    col_left_input, col_right_input = st.columns(2, gap="large")

    with col_left_input:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        input_method = st.radio(
            t["method_label"],
            [t["method_file"], t["method_mic"]],
            horizontal=True
        )

        is_mic = (input_method == t["method_mic"])

        if not is_mic:
            uploaded_file = st.file_uploader(t["file_upload_label"], type=["wav", "mp3"])
            file_label = uploaded_file.name if uploaded_file else "file_upload.wav"
        else:
            uploaded_file = st.audio_input(t["mic_label"])
            file_label = "Micro_Live_Record.wav"
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right_input:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        call_source = st.selectbox(t["call_source_label"], t["sources"])
        suspect_type = st.selectbox(t["suspect_label"], t["suspects"])
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            btn_run = st.button(t["run_btn"], type="primary", use_container_width=True)
    else:
        btn_run = False
        st.info("Vui lòng nạp tệp âm thanh hoặc ghi âm ở cột bên trái để tiếp tục." if st.session_state["lang"] == "Tiếng Việt" else "Please upload or record an audio file on the left to proceed.")

    # --- KẾT QUẢ PHÂN TÍCH CHUYÊN SÂU ---
    if btn_run and uploaded_file is not None:
        st.markdown(f"<h2 style='text-align: center; color: #1a365d; margin-top: 30px;'>{t['result_title']}</h2>", unsafe_allow_html=True)
        
        with st.spinner(t["info_wait"]):
            # Truyền chính xác cờ is_mic để kích hoạt bộ bù suy hao micro
            result = run_pipeline(uploaded_file, is_mic=is_mic)

        # Lưu log gắn với tài khoản đang đăng nhập hoặc Guest
        current_user = st.session_state["username"] if st.session_state["logged_in"] else "Guest"
        save_scan_result(current_user, file_label, result["score"], result["threat"], call_source, suspect_type)

        score = result["score"]
        threat = result["threat"]

        # Bảng thông tin phiên căn giữa
        st.markdown(f"<h3 style='text-align: center;'>{t['sys_info_title']}</h3>", unsafe_allow_html=True)
        df_info = pd.DataFrame({
            "Thông số hệ thống" if st.session_state["lang"] == "Tiếng Việt" else "System Parameter": [
                "Tên tệp âm thanh" if st.session_state["lang"] == "Tiếng Việt" else "Audio Filename", 
                "Nguồn cuộc gọi" if st.session_state["lang"] == "Tiếng Việt" else "Call Source", 
                "Đối tượng nghi ngờ" if st.session_state["lang"] == "Tiếng Việt" else "Suspicious Target",
                "Tài khoản giám định" if st.session_state["lang"] == "Tiếng Việt" else "Examiner Account"
            ],
            "Giá trị ghi nhận" if st.session_state["lang"] == "Tiếng Việt" else "Recorded Value": [
                file_label, call_source, suspect_type, current_user
            ]
        })
        st.dataframe(df_info, use_container_width=True, hide_index=True)
        st.write("")

        # BỐ CỤC CHÍNH: Trái (Chỉ số rủi ro) | Phải (Cảnh báo -> Bản ghi hội thoại -> Dấu hiệu thao túng)
        col_res_left, col_res_right = st.columns([1, 2], gap="large")

        with col_res_left:
            st.markdown(f"""
                <div class="result-container-left">
                    <p class="risk-score-title">{t['risk_score_label']}</p>
                    <h1 class="risk-score-number" style="color: {'#9b2c2c' if score >= 65 else ('#d69e2e' if score >= 45 else '#22543d')};">{score}%</h1>
                    <p class="risk-score-conclusion"><b>{t['conclusion']}</b> {threat}</p>
                </div>
            """, unsafe_allow_html=True)

        with col_res_right:
            if "Nguy cơ cao" in threat or "High" in threat:
                st.markdown(f'<div class="status-badge-high">{t["high_threat"]}</div>', unsafe_allow_html=True)
            elif "Nghi vấn" in threat:
                st.warning(f"⚠️ Cảnh báo: {threat}")
            else:
                st.markdown(f'<div class="status-badge-safe">{t["safe_threat"]}</div>', unsafe_allow_html=True)

            with st.expander(t["transcript_label"], expanded=True):
                st.info(result["transcript"])

            st.markdown(f"<h3 style='text-align: center;'>{t['manipulation_label']}</h3>", unsafe_allow_html=True)
            if result["flags"]:
                for flag in result["flags"]:
                    st.warning(f"{flag}")
            else:
                st.success(t["no_flags"])

        st.write("")
        
        # Biểu đồ âm học và XAI
        col_sub1, col_sub2 = st.columns(2, gap="large")
        with col_sub1:
            st.markdown(f"<h3 style='text-align: center;'>{t['tab_spec']}</h3>", unsafe_allow_html=True)
            st.pyplot(result["figure"])
        with col_sub2:
            st.markdown(f"<h3 style='text-align: center;'>{t['tab_xai']}</h3>", unsafe_allow_html=True)
            st.pyplot(result["xai_fig"])

# --- TAB 2: HƯỚNG DẪN ---
with menu_selection[1]:
    st.markdown(f"<h2 style='text-align: center;'>{t['guide_title']}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    g_tab1, g_tab2 = st.tabs(t["guide_tabs"])
    with g_tab1:
        st.markdown("""
        **Quy trình sử dụng hệ thống gồm 3 bước:**
        1. **Nạp mẫu âm thanh:** Chọn tải lên tệp (.wav, .mp3) hoặc bật micro thu âm trực tiếp một đoạn thoại ngắn (3–10 giây).
        2. **Khởi chạy phân tích:** Nhấn nút *TIẾN HÀNH GIÁM ĐỊNH* để kích hoạt luồng trích xuất đặc trưng âm học 40 chiều và bóc băng lời thoại ASR.
        3. **Đọc kết luận pháp y:** Xem xét chỉ số rủi ro Deepfake, đối chiếu mốc thời gian vi phạm kịch bản lừa đảo và biểu đồ XAI giải thích quyết định.
        """)
    with g_tab2:
        st.code("[ Nạp tệp / Micro ] ──> [ Chuẩn hóa 16kHz + VAD ] ──> [ Random Forest + Faster-Whisper ] ──> [ Kết quả & XAI ]", language="text")

# --- TAB 3: ĐĂNG NHẬP / ĐĂNG KÝ & LỊCH SỬ ---
with menu_selection[2]:
    st.markdown(f"<h2 style='text-align: center;'>{t['auth_title']}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    if not st.session_state["logged_in"]:
        a_tab1, a_tab2 = st.tabs([t["login_tab"], t["reg_tab"]])
        with a_tab1:
            l_user = st.text_input("Tên đăng nhập" if st.session_state["lang"] == "Tiếng Việt" else "Username")
            l_pass = st.text_input("Mật khẩu" if st.session_state["lang"] == "Tiếng Việt" else "Password", type="password")
            if st.button(t["login_btn"], type="primary"):
                if verify_user(l_user, l_pass):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = l_user
                    st.rerun()
                else:
                    st.error("Tên đăng nhập hoặc mật khẩu không chính xác!" if st.session_state["lang"] == "Tiếng Việt" else "Invalid username or password!")
        with a_tab2:
            r_user = st.text_input("Tên đăng nhập mới" if st.session_state["lang"] == "Tiếng Việt" else "New Username")
            r_pass = st.text_input("Mật khẩu mới" if st.session_state["lang"] == "Tiếng Việt" else "New Password", type="password")
            r_confirm = st.text_input("Xác nhận mật khẩu" if st.session_state["lang"] == "Tiếng Việt" else "Confirm Password", type="password")
            if st.button(t["reg_btn"]):
                if not r_user or not r_pass:
                    st.warning("Vui lòng điền đủ thông tin!" if st.session_state["lang"] == "Tiếng Việt" else "Please fill in all fields!")
                elif r_pass != r_confirm:
                    st.error("Mật khẩu xác nhận không khớp!" if st.session_state["lang"] == "Tiếng Việt" else "Passwords do not match!")
                else:
                    if add_user(r_user, r_pass):
                        st.success("Đăng ký thành công! Hãy chuyển sang tab Đăng nhập." if st.session_state["lang"] == "Tiếng Việt" else "Registration successful! Please login.")
                    else:
                        st.error("Tên tài khoản đã tồn tại!" if st.session_state["lang"] == "Tiếng Việt" else "Username already exists!")
    else:
        st.markdown(f"<h3 style='text-align: center;'>Xin chào / Hello, **{st.session_state['username']}**</h3>", unsafe_allow_html=True)
        if st.button(t["logout_btn"]):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

        st.markdown("---")
        st.markdown(f"<h3 style='text-align: center;'>{t['history_title']}</h3>", unsafe_allow_html=True)
        user_data = get_user_scans(st.session_state["username"], limit=15)
        if user_data:
            df_history = pd.DataFrame(user_data, columns=["Thời gian", "Tên tệp", "Điểm AI (%)", "Đánh giá", "Nguồn gọi", "Đối tượng"])
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có lịch sử phiên giám định nào của bạn." if st.session_state["lang"] == "Tiếng Việt" else "No forensic history found for your account.")
