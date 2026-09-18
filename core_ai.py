import os
import io
import pickle
import unicodedata
import numpy as np
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
from faster_whisper import WhisperModel

# 1. Khởi tạo mô hình Faster-Whisper
try:
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
except Exception as e:
    print(f"[!] Canh bao khoi tao Whisper: {e}")
    whisper_model = None

# 2. Nạp mô hình học máy và bộ chuẩn hóa đặc trưng
MODEL_PATH = "model_deepfake.pkl"
SCALER_PATH = "scaler.pkl"

clf = None
scaler = None

if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
    try:
        with open(MODEL_PATH, "rb") as f:
            clf = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
        print(f"[✓] Da nap model ML thanh cong. Classes: {getattr(clf, 'classes_', 'N/A')}")
    except Exception as e:
        print(f"[!] Loi load model ML: {e}")

# 3. Ma trận từ khóa đa kịch bản
DANGEROUS_KEYWORDS = [
    # Kịch bản 1: Viện phí / Cấp cứu / Tai nạn
    "cấp cứu", "cap cuu", "bệnh viện", "benh vien", "viện phí", "vien phi",
    "tai nạn", "tai nan", "chấn thương", "chan thuong", "phẫu thuật", "phau thuat",
    "chữa trị", "chua tri", "con đang", "con bị", "con bi", "cháu bị", "cháu bi",
    "nguy kịch", "nguy kich", "nộp viện phí", "nop vien phi",

    # Kịch bản 2: Cơ quan công quyền / Đe dọa tố tụng
    "công an", "cong an", "viện kiểm sát", "vien kiem sat", "tòa án", "toa an",
    "cảnh sát điều tra", "canh sat dieu tra", "lệnh bắt", "lenh bat", "bắt giam", "bat giam",
    "tạm giam", "tam giam", "khởi tố", "khoi to", "rửa tiền", "rua tien",
    "buôn ma túy", "buon ma tuy", "phạt nguội", "phat nguoi", "truy nã", "truy na",
    "điều tra kín", "dieu tra kin", "phong tỏa tài sản", "phong toa tai san",

    # Kịch bản 3: Thúc ép tài chính / Mã xác thực OTP
    "chuyển tiền", "chuyen tien", "chuyển khoản", "chuyen khoan", "tiền gấp", "tien gap",
    "mã otp", "otp", "tài khoản ngân hàng", "tai khoan ngan hang", "nạp tiền", "nap tien",
    "chuyển gấp", "chuyen gap", "tài khoản tạm giữ", "tai khoan tam giu",
    "xác minh số dư", "xac minh so du", "chứng minh tài chính", "chung minh tai chinh",

    # Kịch bản 4: Giả danh viễn thông / Định danh VNeID
    "khóa sim", "khoa sim", "chặn cuộc gọi", "chan cuoc goi", "định danh", "dinh danh",
    "vneid", "văn phòng viễn thông", "van phong vien thong", "thu hồi sim", "thu hoi sim",
    "cập nhật sinh trắc học", "cap nhat sinh trac hoc", "khóa thuê bao", "khoa thue bao",

    # Kịch bản 5: Lừa đảo đầu tư / Việc làm online
    "trúng thưởng", "trung thuong", "tiền hoa hồng", "tien hoa hong", "nhận quà", "nhan qua",
    "làm nhiệm vụ", "lam nhiem vu", "sàn giao dịch", "san giao dich", "nạp ví", "nap vi",
    "rút tiền", "rut tien", "đầu tư sinh lời", "dau tu sinh loi",

    # Kịch bản 6: Thao túng tâm lý / Ép buộc cô lập
    "tuyệt đối bí mật", "tuyet doi bi mat", "không cúp máy", "khong cup may",
    "không báo cho ai", "khong bao cho ai", "nghe theo tôi", "nghe theo toi",
    "khẩn cấp", "khan cap", "ngay lập tức", "ngay lap tuc"
]

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

def load_audio_safely(uploaded_file):
    temp_path = "temp_eval_audio.wav"

    if isinstance(uploaded_file, str):
        audio_bytes = open(uploaded_file, "rb").read()
        file_name = uploaded_file
    else:
        audio_bytes = uploaded_file.getvalue()
        file_name = getattr(uploaded_file, "name", "input_audio.wav")

    try:
        data, sr = sf.read(io.BytesIO(audio_bytes))
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        if sr != 16000:
            data = librosa.resample(data.astype(float), orig_sr=sr, target_sr=16000)
            sr = 16000
        sf.write(temp_path, data, sr, format='WAV', subtype='PCM_16')
        return data.astype(float), sr, temp_path
    except Exception:
        pass

    ext = os.path.splitext(file_name)[1].lower()
    if not ext:
        ext = ".wav"
    raw_temp = f"temp_raw_file{ext}"

    with open(raw_temp, "wb") as f:
        f.write(audio_bytes)

    try:
        y, sr = librosa.load(raw_temp, sr=16000, mono=True)
        sf.write(temp_path, y, 16000, format='WAV', subtype='PCM_16')
        return y, sr, temp_path
    finally:
        if os.path.exists(raw_temp):
            try:
                os.remove(raw_temp)
            except Exception:
                pass

def extract_features(y, sr):
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = np.mean(chroma.T, axis=0)

    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    contrast_mean = np.mean(contrast.T, axis=0)

    tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
    tonnetz_mean = np.mean(tonnetz.T, axis=0)

    return np.hstack([mfcc_mean, chroma_mean, contrast_mean, tonnetz_mean[:1]])

def predict_ml_score(y, sr, is_mic=False):
    """
    Xác suất giả mạo âm học: 0 là Real, 1 là Fake.
    Luôn lấy probs[1] để phản ánh đúng xác suất Fake.
    """
    global clf, scaler
    feats = extract_features(y, sr).reshape(1, -1)

    if clf is not None and scaler is not None:
        scaled = scaler.transform(feats)
        probs = clf.predict_proba(scaled)[0]
        p_fake = float(probs[1]) if len(probs) > 1 else float(probs[0])
        importances = getattr(clf, "feature_importances_", np.ones(40) / 40.0)
    else:
        contrast_val = np.mean(feats[0, 32:39])
        p_fake = float(np.clip((contrast_val - 15.0) / 25.0, 0.05, 0.95))
        importances = np.ones(40) / 40.0

    return p_fake, importances

def analyze_nlp_transcript(audio_path):
    if whisper_model is None or not os.path.exists(audio_path):
        return "Không có mô hình Whisper hoặc tệp âm thanh.", [], 0.0

    try:
        segments, _ = whisper_model.transcribe(
            audio_path,
            language="vi",
            beam_size=5,
            initial_prompt="Cuộc gọi khẩn cấp, bệnh viện, cấp cứu, viện phí, chuyển tiền, công an, viện kiểm sát, OTP."
        )
        transcript = " ".join([seg.text for seg in segments]).strip()
    except Exception as e:
        print(f"[!] Loi transcribe Whisper: {e}")
        return f"Lỗi bóc băng: {str(e)}", [], 0.0

    if not transcript:
        return "Không nhận diện được giọng nói trong tệp.", [], 0.0

    t_lower = transcript.lower()
    t_no_accent = remove_accents(transcript)

    detected = []
    for kw in DANGEROUS_KEYWORDS:
        kw_lower = kw.lower()
        kw_no_accent = remove_accents(kw)
        if (kw_lower in t_lower) or (kw_no_accent in t_no_accent):
            if kw not in detected and kw_no_accent not in [remove_accents(d) for d in detected]:
                detected.append(kw)

    count = len(detected)
    if count >= 3:
        p_nlp = 0.90
    elif count == 2:
        p_nlp = 0.65
    elif count == 1:
        p_nlp = 0.40
    else:
        p_nlp = 0.0

    return transcript, detected, p_nlp

def generate_spectrogram(y, sr):
    fig, ax = plt.subplots(figsize=(6, 3))
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax, cmap='viridis')
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    ax.set_title("Mel-frequency Spectrogram", fontsize=10, fontweight='bold')
    fig.tight_layout()
    return fig

def generate_xai_figure(importances):
    fig, ax = plt.subplots(figsize=(6, 3))
    top_indices = np.argsort(importances)[-6:]
    labels = [f"F_{idx}" for idx in top_indices]
    vals = importances[top_indices]

    ax.barh(labels, vals, color="#2563eb")
    ax.set_title("Top Acoustic Features Impact (XAI)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Weight")
    fig.tight_layout()
    return fig

def run_pipeline(uploaded_file, is_mic=False):
    try:
        y, sr, temp_wav_path = load_audio_safely(uploaded_file)
    except Exception as e:
        print(f"[!] Loi doc audio: {e}")
        fig_err, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, f"Audio Load Error:\n{str(e)[:35]}", ha='center', va='center')
        return {
            "score": 0.0, "threat": "Safe", "flags": [],
            "figure": fig_err, "xai_fig": fig_err, "verdict": "Lỗi tệp",
            "acoustic_fake_prob": 0.0, "nlp_fake_prob": 0.0, "transcript": ""
        }

    # 1. Trích xuất âm học (chuẩn nhãn probs[1])
    p_acoustic_fake, importances = predict_ml_score(y, sr, is_mic=is_mic)

    # 2. Bóc băng NLP
    transcript, detected_keywords, p_nlp_fake = analyze_nlp_transcript(temp_wav_path)

    # 3. Biểu đồ trực quan
    fig = generate_spectrogram(y, sr)
    xai_fig = generate_xai_figure(importances)

    # 4. CƠ CHẾ DUAL-ENGINE FORENSIC CHÍNH XÁC:
    # A. Nếu đặc trưng âm học là giọng sinh học người thật (<= 28%):
    # Dù có từ khóa thông thường (cấp cứu, bệnh viện...) vẫn là AN TOÀN, từ khóa chỉ tính hệ số phụ nhẹ.
    if p_acoustic_fake <= 0.28:
        threat_score = (p_acoustic_fake * 0.85) + (p_nlp_fake * 0.08)
    
    # B. Nếu là kịch bản lừa đảo (có OTP, chuyển tiền) và âm học ở vùng nghi vấn (> 30%):
    # Kích hoạt báo động mức CAO
    elif p_nlp_fake >= 0.35 and p_acoustic_fake >= 0.30:
        z = (6.0 * p_acoustic_fake) + (4.5 * p_nlp_fake) - 2.8
        threat_score = float(1.0 / (1.0 + np.exp(-z)))
    
    # C. Nếu âm học phát hiện giả lập cao (>= 55%):
    elif p_acoustic_fake >= 0.55:
        z = (5.5 * p_acoustic_fake) + (2.0 * p_nlp_fake) - 2.5
        threat_score = float(1.0 / (1.0 + np.exp(-z)))
        
    # D. Các trường hợp trung gian
    else:
        threat_score = (p_acoustic_fake * 0.70) + (p_nlp_fake * 0.30)

    threat_percentage = round(threat_score * 100, 2)
    acoustic_pct = round(p_acoustic_fake * 100, 2)
    nlp_pct = round(p_nlp_fake * 100, 2)

    level = "Safe" if threat_percentage < 40 else ("Warning" if threat_percentage < 70 else "Danger")
    verdict = "Real" if level == "Safe" else ("Suspicious" if level == "Warning" else "Fake")

    return {
        "score": threat_percentage,
        "threat": level,
        "flags": detected_keywords,
        "figure": fig,
        "xai_fig": xai_fig,
        "verdict": verdict,
        "acoustic_fake_prob": acoustic_pct,
        "nlp_fake_prob": nlp_pct,
        "transcript": transcript
    }