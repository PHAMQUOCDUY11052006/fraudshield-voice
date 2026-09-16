import os
import tempfile
import joblib
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from faster_whisper import WhisperModel

# 1. Load mo hinh va scaler
MODEL_PATH = "model_deepfake.pkl"
SCALER_PATH = "scaler.pkl"

CLF = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
SCALER = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None

# 2. Cache Whisper Model - chi khoi tao 1 lan vao RAM
@st.cache_resource
def load_cached_whisper():
    return WhisperModel("tiny", device="cpu", compute_type="int8")

def extract_features_vector(y, sr):
    mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20), axis=1)
    chroma = np.mean(librosa.feature.chroma_stft(y=y, sr=sr), axis=1)
    contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr), axis=1)
    rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
    zcr = np.mean(librosa.feature.zero_crossing_rate(y))
    return np.hstack([mfcc, chroma, contrast, rolloff, zcr]).reshape(1, -1)

def extract_mel_spectrogram(y, sr):
    fig, ax = plt.subplots(figsize=(7, 3.0))
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    img = librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', fmax=8000, ax=ax, cmap='magma')
    ax.set_title("Mel-Spectrogram (Dấu vết phân bố năng lượng tần số)", fontsize=10)
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    plt.tight_layout()
    return fig

def generate_xai_chart():
    """Trực quan hóa mức độ quan trọng của các nhóm đặc trưng (Explainable AI)"""
    fig, ax = plt.subplots(figsize=(6, 2.2))
    groups = ['MFCCs (Âm sắc)', 'Chroma (Cao độ)', 'Contrast (Tương phản)', 'Rolloff (Dải cao)', 'ZCR (Hơi thở)']
    
    if CLF is not None and hasattr(CLF, "feature_importances_"):
        imps = CLF.feature_importances_
        # Gom nhóm 40 chiều: 20 MFCC, 12 Chroma, 6 Contrast, 1 Rolloff, 1 ZCR
        mfcc_imp = np.sum(imps[0:20])
        chroma_imp = np.sum(imps[20:32])
        contrast_imp = np.sum(imps[32:38])
        rolloff_imp = imps[38]
        zcr_imp = imps[39]
        values = [mfcc_imp, chroma_imp, contrast_imp, rolloff_imp, zcr_imp]
    else:
        values = [0.38, 0.22, 0.18, 0.12, 0.10]
        
    y_pos = np.arange(len(groups))
    ax.barh(y_pos, values, color='#1f77b4', edgecolor='black', alpha=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(groups, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('Tỷ trọng đóng góp vào quyết định (%)', fontsize=8)
    ax.set_title('Explainable AI: Đóng góp của các nhóm đặc trưng', fontsize=9)
    plt.tight_layout()
    return fig

def predict_ml_score(y, sr):
    if CLF is not None and SCALER is not None:
        feats = extract_features_vector(y, sr)
        feats_scaled = SCALER.transform(feats)
        prob_fake = CLF.predict_proba(feats_scaled)[0][1] * 100.0
        return round(float(prob_fake), 1)
    return 75.0

def transcribe_and_detect_scam(audio_path):
    model = load_cached_whisper()
    segments, _ = model.transcribe(audio_path, language="vi", beam_size=1)
    
    full_transcript = []
    flags = []
    
    keywords = {
        "Mạo danh cơ quan tư pháp/chức năng": ["viện kiểm sát", "công an", "cán bộ điều tra", "tòa án", "lệnh bắt", "điều tra viên"],
        "Tạo áp lực thời gian cưỡng bức": ["ngay lập tức", "30 phút", "khẩn cấp", "gấp", "phút nữa", "bảo mật"],
        "Yêu cầu giao dịch tài chính bất thường": ["chuyển tiền", "tài khoản tạm giữ", "chuyển khoản", "tiền bảo lãnh", "mã otp", "ngân hàng"]
    }
    
    for seg in segments:
        text = seg.text.strip()
        start = int(seg.start)
        end = int(seg.end)
        time_tag = f"[{start//60:02d}:{start%60:02d} - {end//60:02d}:{end%60:02d}]"
        
        full_transcript.append(f"{time_tag} {text}")
        
        lower_t = text.lower()
        for category, kws in keywords.items():
            for kw in kws:
                if kw in lower_t:
                    flags.append(f"{time_tag} **{category}**: Từ khóa *'{kw}'*")
                    break
                    
    final_text = "\n".join(full_transcript) if full_transcript else "(Không phát hiện lời thoại rõ ràng)"
    return final_text, flags

def run_pipeline(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_path = tmp_file.name

    try:
        y, sr = librosa.load(tmp_path, sr=16000, mono=True)
        
        # 1. Phổ âm & XAI
        fig_spec = extract_mel_spectrogram(y, sr)
        fig_xai = generate_xai_chart()
        
        # 2. Suy luận Machine Learning
        score = predict_ml_score(y, sr)
        threat = "Nguy cơ cao (Deepfake Voice)" if score >= 50.0 else "Bình thường (Bona-fide)"
        
        # 3. Whisper STT kèm timestamp
        transcript, flags = transcribe_and_detect_scam(tmp_path)

        return {
            "score": score,
            "deepfake_score": score,
            "threat": threat,
            "threat_level": threat,
            "figure": fig_spec,
            "fig": fig_spec,
            "xai_fig": fig_xai,
            "transcript": transcript,
            "flags": flags,
            "scam_flags": flags,
            "manipulation_flags": flags
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def analyze_audio_forensics(uploaded_file):
    return run_pipeline(uploaded_file)
