import streamlit as st
import pandas as pd
from core_ai import run_pipeline
from database import init_db, save_scan_result, get_recent_scans

init_db()

st.set_page_config(page_title="FraudShield Voice", page_icon="🛡️", layout="wide")

st.title("🛡️ CỔNG GIÁM ĐỊNH ÂM THANH FRAUDSHIELD VOICE")
st.caption("Hệ thống phân tích pháp y số và phát hiện cuộc gọi lừa đảo Deepfake Voice - Bảng C")

col_input, col_result = st.columns([1, 1.2], gap="medium")

with col_input:
    st.subheader("📥 Dữ liệu kiểm định")
    uploaded_file = st.file_uploader("Tải tệp âm thanh cuộc gọi nghi vấn (.wav, .mp3)", type=["wav", "mp3"])
    call_source = st.selectbox("Nguồn cuộc gọi", ["GSM (Mạng di động)", "Zalo", "Telegram", "Khác"])
    suspect_type = st.selectbox("Đối tượng nghi vấn", ["Cơ quan điều tra / Viện kiểm sát", "Ngân hàng", "Người thân", "Chưa rõ"])
    
    if uploaded_file is not None:
        st.audio(uploaded_file)
        btn_run = st.button("TIẾN HÀNH GIÁM ĐỊNH", type="primary", use_container_width=True)
    else:
        btn_run = False

with col_result:
    st.subheader("📊 Kết quả phân tích pháp y")
    if btn_run and uploaded_file is not None:
        with st.spinner("Đang trích xuất đặc trưng và phân tích pháp y số..."):
            result = run_pipeline(uploaded_file)
            
            # Luu database SQLite
            save_scan_result(uploaded_file.name, result['score'], result['threat'], call_source, suspect_type)
            
            # Khối kết luận
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Xác suất Giọng AI (Deepfake)", f"{result['score']}%")
            with col_m2:
                if result['score'] >= 50.0:
                    st.error(f"Đánh giá: {result['threat']}")
                else:
                    st.success(f"Đánh giá: {result['threat']}")
                    
            st.markdown("#### 📊 Bằng chứng âm học & Giải thích mô hình:")
            tab1, tab2 = st.tabs(["Phổ Mel-Spectrogram", "Explainable AI (XAI)"])
            with tab1:
                st.pyplot(result["figure"])
            with tab2:
                st.pyplot(result["xai_fig"])
                st.caption("Biểu đồ thể hiện mức độ đóng góp của từng nhóm đặc trưng vào quyết định phân loại.")
            
            st.markdown("#### 📝 Bóc băng kèm mốc thời gian:")
            st.text_area("Hội thoại trích xuất", result["transcript"], height=120)
            
            st.markdown("#### ⚠️ Cảnh báo kịch bản thao túng:")
            if result["flags"]:
                for f in result["flags"]:
                    st.warning(f)
            else:
                st.info("Không phát hiện dấu hiệu thao túng rõ rệt trong lời thoại.")
    else:
        st.info("Vui lòng tải tệp âm thanh và bấm 'TIẾN HÀNH GIÁM ĐỊNH' để xem kết quả.")

st.divider()

st.subheader("🕒 Lịch sử các phiên giám định gần đây (SQLite Audit Log)")
recent_data = get_recent_scans(limit=5)
if recent_data:
    df = pd.DataFrame(recent_data, columns=["Thời gian", "Tên tệp", "Điểm AI (%)", "Đánh giá", "Nguồn gọi", "Đối tượng"])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.caption("Chưa có phiên giám định nào được ghi nhận.")
