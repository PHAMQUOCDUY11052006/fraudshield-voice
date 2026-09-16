import streamlit as st

st.set_page_config(page_title="FraudShield Voice", page_icon="🛡️")
st.title("🛡️ Cổng Giám Định Âm Thanh FraudShield Voice")
st.write("Hệ thống phát hiện cuộc gọi lừa đảo Deepfake voice - Bảng C 2026")

uploaded_file = st.file_uploader("Tải lên file âm thanh (.wav, .mp3)", type=["wav", "mp3"])
if uploaded_file is not None:
    st.audio(uploaded_file)
    if st.button("Tiến hành giám định", type="primary"):
        st.success("Tải file thành công! Sẵn sàng phân tích.")
