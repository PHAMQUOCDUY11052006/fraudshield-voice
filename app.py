import os
import streamlit as st
import pandas as pd
from datetime import datetime
from core_ai import run_pipeline
from database import init_db, add_user, verify_user, save_scan_result, get_user_scans, get_all_users, get_all_scans_admin

AUDIO_DIR = "saved_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

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

if "lang" not in st.session_state:
    st.session_state["lang"] = "Tiếng Việt"
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "consent_given" not in st.session_state:
    st.session_state["consent_given"] = False

ADMIN_USERS = ["duy", "admin"]
is_admin = st.session_state["logged_in"] and (st.session_state["username"] in ADMIN_USERS)

TEXTS = {
    "Tiếng Việt": {
        "title": "HỆ THỐNG GIÁM ĐỊNH & ĐIỀU TRA CUỘC GỌI DEEPFAKE",
        "menu_home": "Trang chủ",
        "menu_guide": "Hướng dẫn",
        "menu_auth": "Đăng nhập / Đăng ký",
        "menu_admin": "🛡️ Quản trị hệ thống",
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
        "history_title": "Lịch sử giám định & Nghe lại âm thanh"
    },
    "English": {
        "title": "DEEPFAKE CALL INVESTIGATION & FORENSIC SYSTEM",
        "menu_home": "Home",
        "menu_guide": "Guide",
        "menu_auth": "Login / Register",
        "menu_admin": "🛡️ Admin Console",
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
        "history_title": "Forensic Session History & Playback"
    }
}

t = TEXTS[st.session_state["lang"]]

if not st.session_state["consent_given"]:
    @st.dialog("Quy chế bảo mật hệ thống / System Security Policy")
    def consent_dialog():
        st.write("Chào mừng bạn đến với Hệ thống Giám định & Điều tra cuộc gọi Deepfake. Dữ liệu âm thanh của bạn được lưu trữ bảo mật cục bộ phục vụ công tác điều tra.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Từ chối / Decline", use_container_width=True):
                st.stop()
        with col_c2:
            if st.button("Đồng ý / Agree", type="primary", use_container_width=True):
                st.session_state["consent_given"] = True
                st.rerun()
    consent_dialog()

st.markdown(f"""
    <div class="portal-header">
        <h1 class="portal-header-title">{t['title']}</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

col_menu, col_lang = st.columns([5, 1], gap="small")

# Danh sach menu tabs dong tuy theo quyen han Admin
tab_labels = [t["menu_home"], t["menu_guide"], t["menu_auth"]]
if is_admin:
    tab_labels.append(t["menu_admin"])

with col_menu:
    menu_selection = st.tabs(tab_labels)

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

    if btn_run and uploaded_file is not None:
        st.markdown(f"<h2 style='text-align: center; color: #1a365d; margin-top: 30px;'>{t['result_title']}</h2>", unsafe_allow_html=True)
        
        current_user = st.session_state["username"] if st.session_state["logged_in"] else "Guest"
        time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{current_user}_{time_tag}_{file_label}"
        saved_file_path = os.path.join(AUDIO_DIR, safe_filename)
        
        with open(saved_file_path, "wb") as f_out:
            f_out.write(uploaded_file.getbuffer())

        with st.spinner(t["info_wait"]):
            result = run_pipeline(uploaded_file, is_mic=is_mic)

        save_scan_result(current_user, file_label, result["score"], result["threat"], call_source, suspect_type, audio_path=saved_file_path)

        score = result["score"]
        threat = result["threat"]

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
        st.code("[ Nạp tệp / Micro ] ──> [ Chuẩn hóa 16kHz + VAD ] ──> [ Random Forest + Faster-Whisper ] ──> [ Lưu trữ & Kết quả ]", language="text")

# --- TAB 3: ĐĂNG NHẬP / ĐĂNG KÝ & LỊCH SỬ RIÊNG ---
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
        st.markdown(f"<h3 style='text-align: center;'>Xin chào / Hello, **{st.session_state['username']}** {'👑 (Quản trị viên)' if is_admin else ''}</h3>", unsafe_allow_html=True)
        if st.button(t["logout_btn"]):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

        st.markdown("---")
        st.markdown(f"<h3 style='text-align: center;'>{t['history_title']}</h3>", unsafe_allow_html=True)
        
        user_scans = get_user_scans(st.session_state["username"], limit=15)
        if user_scans:
            for item in user_scans:
                s_id, s_time, s_file, s_score, s_threat, s_src, s_sus, s_path = item
                with st.expander(f"📌 [{s_time}] - Tệp: {s_file} (Rủi ro: {s_score}%)"):
                    col_h1, col_h2 = st.columns([1.5, 1])
                    with col_h1:
                        st.write(f"**Đánh giá:** {s_threat}")
                        st.write(f"**Nguồn:** {s_src} | **Đối tượng:** {s_sus}")
                    with col_h2:
                        if s_path and os.path.exists(s_path):
                            st.write("**Nghe lại đoạn âm thanh:**")
                            st.audio(s_path)
                        else:
                            st.caption("(Không tìm thấy file âm thanh lưu trữ)")
        else:
            st.info("Chưa có lịch sử phiên giám định nào của bạn." if st.session_state["lang"] == "Tiếng Việt" else "No forensic history found for your account.")

# --- TAB 4: BẢNG QUẢN TRỊ ADMIN (Chỉ duy / admin mới thấy) ---
if is_admin:
    with menu_selection[3]:
        st.markdown("<h2 style='text-align: center; color: #1a365d;'>👑 BẢNG QUẢN TRỊ HỆ THỐNG FRAUDSHIELD VOICE</h2>", unsafe_allow_html=True)
        st.caption("Khu vực độc quyền dành cho Quản trị viên theo dõi toàn bộ cơ sở dữ liệu và giám sát hệ thống.")
        st.markdown("---")
        
        all_users = get_all_users()
        all_scans = get_all_scans_admin(limit=100)
        deepfake_alerts = [s for s in all_scans if s[4] >= 65.0]
        
        # Thống kê nhanh (KPI Cards)
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Tổng số tài khoản đã đăng ký", len(all_users))
        kpi2.metric("Tổng số phiên giám định đã thực hiện", len(all_scans))
        kpi3.metric("Số ca phát hiện Deepfake nguy cơ cao", len(deepfake_alerts))
        
        st.markdown("---")
        
        tab_adm1, tab_adm2 = st.tabs(["📋 Toàn bộ dữ liệu phiên giám định & Nghe lại", "👥 Danh sách tài khoản người dùng"])
        
        with tab_adm1:
            st.subheader("Duyệt và nghe lại toàn bộ các cuộc gọi nghi vấn trên hệ thống")
            if all_scans:
                for scan in all_scans:
                    # scan: (id, username, timestamp, filename, score, threat, call_source, suspect_type, audio_path)
                    a_id, a_user, a_time, a_file, a_score, a_threat, a_src, a_sus, a_path = scan
                    with st.expander(f"👤 User: {a_user} | [{a_time}] - {a_file} (Rủi ro: {a_score}%)"):
                        col_a1, col_a2 = st.columns([1.5, 1])
                        with col_a1:
                            st.write(f"**Kết luận pháp y:** {a_threat}")
                            st.write(f"**Nguồn cuộc gọi:** {a_src}")
                            st.write(f"**Đối tượng mạo danh:** {a_sus}")
                            st.caption(f"Đường dẫn vật lý: {a_path}")
                        with col_a2:
                            if a_path and os.path.exists(a_path):
                                st.write("**Trình phát âm thanh điều tra:**")
                                st.audio(a_path)
                            else:
                                st.caption("(Tệp âm thanh không tồn tại trên ổ đĩa)")
            else:
                st.info("Hệ thống chưa ghi nhận phiên giám định nào.")
                
        with tab_adm2:
            st.subheader("Danh sách tài khoản hệ thống")
            if all_users:
                df_users = pd.DataFrame({"STT": range(1, len(all_users) + 1), "Tên tài khoản": all_users})
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có người dùng nào đăng ký.")
