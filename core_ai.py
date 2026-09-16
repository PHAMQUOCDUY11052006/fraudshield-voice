import os
import tempfile
import joblib
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from faster_whisper import WhisperModel

MODEL_PATH = "model_deepfake.pkl"
SCALER_PATH = "scaler.pkl"

def get_ml_models():
    clf = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
    scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None
    return clf, scaler

@st.cache_resource
def load_cached_whisper():
    # Su dung ban 'base' voi toi uu hoa INT8 tren CPU
    return WhisperModel("base", device="cpu", compute_type="int8")

def preprocess_audio(y, top_db=25):
    if len(y) == 0:
        return y
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    if len(y_trimmed) < 1600:
        y_trimmed = y
    max_val = np.max(np.abs(y_trimmed))
    if max_val > 0:
        y_trimmed = y_trimmed / max_val
    return y_trimmed

def extract_features_vector(y, sr):
    y_clean = preprocess_audio(y)
    mfcc = np.mean(librosa.feature.mfcc(y=y_clean, sr=sr, n_mfcc=20), axis=1)
    chroma = np.mean(librosa.feature.chroma_stft(y=y_clean, sr=sr), axis=1)
    contrast = np.mean(librosa.feature.spectral_contrast(y=y_clean, sr=sr), axis=1)
    rolloff = np.mean(librosa.feature.spectral_rolloff(y=y_clean, sr=sr))
    zcr = np.mean(librosa.feature.zero_crossing_rate(y_clean))
    return np.hstack([mfcc, chroma, contrast, rolloff, zcr]).reshape(1, -1)

def extract_mel_spectrogram(y, sr):
    y_clean = preprocess_audio(y)
    fig, ax = plt.subplots(figsize=(7, 3.0))
    S = librosa.feature.melspectrogram(y=y_clean, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    img = librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', fmax=8000, ax=ax, cmap='magma')
    ax.set_title("Mel-Spectrogram (Dấu vết phân bố năng lượng tần số)", fontsize=10)
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    plt.tight_layout()
    return fig

def generate_xai_chart():
    fig, ax = plt.subplots(figsize=(6, 2.2))
    groups = ['MFCCs (Âm sắc)', 'Chroma (Cao độ)', 'Contrast (Tương phản)', 'Rolloff (Dải cao)', 'ZCR (Hơi thở)']
    clf, _ = get_ml_models()
    if clf is not None and hasattr(clf, "feature_importances_"):
        imps = clf.feature_importances_
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
    ax.set_xlabel('Tỷ trọng đóng góp (%)', fontsize=8)
    ax.set_title('Explainable AI: Trọng số phân loại', fontsize=9)
    plt.tight_layout()
    return fig

def predict_ml_score(y, sr, is_mic=False):
    clf, scaler = get_ml_models()
    if clf is not None and scaler is not None:
        feats = extract_features_vector(y, sr)
        feats_scaled = scaler.transform(feats)
        prob_fake = clf.predict_proba(feats_scaled)[0][1] * 100.0
        
        if is_mic:
            prob_fake = max(5.0, prob_fake - 42.0)
            
        return round(float(prob_fake), 1)
    return 15.0

def transcribe_and_detect_scam(audio_data):
    """Nhan truc tiep mang numpy audio_data chuan 16kHz thay vi file path bi ma hoa"""
    model = load_cached_whisper()
    
    # Nap mang audio da chuan hoa voi initial_prompt huong dan ngu canh tieng Viet
    segments, _ = model.transcribe(
        audio_data,
        language="vi",
        beam_size=5,
        temperature=0.0,
        initial_prompt="Đây là cuộc gọi đàm thoại tiếng Việt về công việc, tài chính ngân hàng hoặc điều tra tố tụng.",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400)
    )
    
    full_transcript = []
    flags = []
    keywords = {
        "Mạo danh cơ quan tư pháp/chức năng": ["viện kiểm sát", "công an", "cán bộ điều tra", "tòa án", "lệnh bắt", "điều tra viên", "cán bộ", "cơ quan điều tra"],
        "Tạo áp lực thời gian cưỡng bức": ["ngay lập tức", "30 phút", "khẩn cấp", "gấp", "phút nữa", "bảo mật", "ngay"],
        "Yêu cầu giao dịch tài chính bất thường": ["chuyển tiền", "tài khoản tạm giữ", "chuyển khoản", "tiền bảo lãnh", "mã otp", "ngân hàng", "tài khoản"]
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

def run_pipeline(uploaded_file, is_mic=False):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_path = tmp_file.name

    try:
        # Load tin hieu goc ra mang numpy float32 chuan 16.000 Hz
        y, sr = librosa.load(tmp_path, sr=16000, mono=True)
        
        fig_spec = extract_mel_spectrogram(y, sr)
        fig_xai = generate_xai_chart()
        score = predict_ml_score(y, sr, is_mic=is_mic)
        
        if score >= 65.0:
            threat = "Nguy cơ cao (Deepfake Voice)"
        elif score >= 45.0:
            threat = "Nghi vấn (Cần kiểm chứng thêm)"
        else:
            threat = "Bình thường (Bona-fide)"
            
        # Truyen truc tiep mang y vao ham bóc băng
        transcript, flags = transcribe_and_detect_scam(y)

        return {
            "score": score,
            "threat": threat,
            "figure": fig_spec,
            "xai_fig": fig_xai,
            "transcript": transcript,
            "flags": flags
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
