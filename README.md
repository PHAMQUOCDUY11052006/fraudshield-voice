# 🛡️ FraudShield Voice: Hệ Thống Giám Định Âm Thanh & Phát Hiện Cuộc Gọi Lừa Đảo Deepfake

> **Dự án tham dự:** Cuộc thi Sáng tạo trẻ Quốc gia trong lĩnh vực Trí tuệ Nhân tạo năm 2026  
> **Bảng thi:** Bảng C (Sinh viên các trường Đại học, Cao đẳng, Học viện)  
> **Đội thi:** Duy & Hiền  
> **Mô hình triển khai:** Web Application (Streamlit Monolithic Architecture)

---

## 📌 1. Giới thiệu bài toán (Problem Statement)
Sự bùng nổ của các mô hình nhân bản giọng nói (Voice Cloning) và tổng hợp giọng nói (Text-to-Speech) độ chân thực cao đang tạo ra làn sóng lừa đảo công nghệ cao mới. Kẻ gian giả danh người thân, cán bộ tư pháp, nhân viên ngân hàng để thao túng tâm lý và chiếm đoạt tài sản.

**FraudShield Voice** là nền tảng phân tích pháp y số (Digital Audio Forensics) đa tầng, kết hợp giữa trích xuất đặc trưng vật lý âm thanh và phân tích hành vi ngữ nghĩa để đưa ra kết luận khách quan, khoa học về tính xác thực của cuộc gọi nghi vấn.

---

## 🚀 2. Tính năng chính (Key Features)
* **Phân tích âm học đa tầng (Acoustic Forensic):** Trích xuất Mel-Spectrogram, phân tích đặc trưng tần số cao nhằm phát hiện các vết tích nén, lỗi pha âm thanh (artifacts) do mô hình AI để lại.
* **Bóc băng hội thoại tự động (Speech-to-Text):** Tích hợp Whisper/Faster-Whisper nhận dạng giọng nói tiếng Việt độ chính xác cao.
* **Nhận diện kịch bản lừa đảo (Linguistic Analysis):** Ứng dụng LLM quét và gắn cờ các thủ thuật thao túng tâm lý (áp lực thời gian, đe dọa tố tụng, yêu cầu chuyển tiền khẩn cấp).
* **Trực quan hóa kết quả:** Giao diện dạng cổng tra cứu tập trung, hiển thị sóng âm, thước đo mức độ rủi ro (%) và danh sách cảnh báo vi phạm.
* **Báo cáo pháp y chuẩn hóa:** Xuất biên bản kết quả phân tích phục vụ trình báo cơ quan chức năng hoặc bộ phận kiểm soát gian lận.

---

## 🏗️ 3. Kiến trúc hệ thống (System Architecture)

```text
[ Tệp âm thanh (.wav/.mp3) ]
           │
           ▼
[ Tiền xử lý âm thanh (16kHz Mono / VAD - Librosa) ]
           │
           ├───► [ Tầng Âm học ] ──► STFT / Mel-Spectrogram ──► Điểm nghi vấn AI (%)
           │
           └───► [ Tầng Ngôn ngữ ] ──► Whisper ASR ──► LLM Agent ──► Thao túng tâm lý
                                                                        │
                                                                        ▼
[ Cổng Tra Cứu Streamlit ] ◄─────────────────────────────────────────────┘
           │
           ├───► Trực quan hóa phổ âm & Đồng hồ đo rủi ro
           ├───► Lưu nhật ký phiên làm việc (SQLite)
           └───► Xuất biên bản giám định pháp y
