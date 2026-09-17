import os
import pickle
import numpy as np
import librosa
from faster_whisper import WhisperModel

# 1. Danh muc tu khoa lua dao & he so phat hien
SCAM_KEYWORDS = {
    "viện kiểm sát": 25,
    "công an": 25,
    "lệnh bắt": 30,
    "tạm giam": 30,
    "phong tỏa": 25,
    "rửa tiền": 25,
    "mã otp": 35,
    "chuyển tiền": 20,
    "tài khoản tạm giữ": 30,
    "bí mật chuyên án": 25,
    "khóa sim": 20,
    "viễn thông": 15,
    "cưỡng chế": 25,
    "truy nã": 30
}

# Cache model whisper de tranh khoi tao lai nhieu lan
whisper_model = None

def get_whisper():
    global whisper_model
    if whisper_model is None:
        # Chay model tiny tren CPU de tiet kiem bo nho Streamlit Cloud
        whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return whisper_model

def extract_features_inference(audio_path):
    """Trich xuat dac trung dong bo voi pipeline huan luyen."""
    try:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        if len(y) < sr * 0.3:
            return None
            
        y, _ = librosa.effects.trim(y, top_db=25)
        
        rms = np.sqrt(np.mean(y**2))
        if rms > 1e-6:
            y = y / rms

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        mfcc_mean = np.mean(mfcc.T, axis=0)

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma.T, axis=0)

        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(contrast.T, axis=0)

        tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
        tonnetz_mean = np.mean(tonnetz.T, axis=0)

        features = np.hstack([mfcc_mean, chroma_mean, contrast_mean, tonnetz_mean[:1]])
        return features.reshape(1, -1)
    except Exception as e:
        print(f"Loi doc audio test: {e}")
        return None

def analyze_audio_forensics(audio_path):
    """Du doan xac suat Fake qua am hoc."""
    if not os.path.exists("model_deepfake.pkl") or not os.path.exists("scaler.pkl"):
        return 0.5  # Fallback neu chua co model
        
    with open("model_deepfake.pkl", "rb") as f:
        model = pickle.load(f)
    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
        
    feat = extract_features_inference(audio_path)
    if feat is None:
        return 0.5
        
    scaled_feat = scaler.transform(feat)
    proba = model.predict_proba(scaled_feat)[0]
    p_fake_raw = proba[1]
    
    # Hieu chinh do nhay: Neu xac suat fake >= 0.35 thi kich hoat scale canh bao
    if p_fake_raw >= 0.35:
        p_fake = min(1.0, p_fake_raw * 1.3)
    else:
        p_fake = p_fake_raw * 0.8
        
    return p_fake

def analyze_nlp_transcript(audio_path):
    """Boc bang am thanh va cham diem tu khoa kich ban lua dao."""
    try:
        model = get_whisper()
        segments, _ = model.transcribe(audio_path, language="vi")
        transcript = " ".join([seg.text for seg in segments]).strip()
    except Exception as e:
        transcript = ""
        
    detected_words = []
    nlp_score = 0
    transcript_lower = transcript.lower()
    
    for kw, score in SCAM_KEYWORDS.items():
        if kw in transcript_lower:
            detected_words.append(kw)
            nlp_score += score
            
    nlp_score = min(100, nlp_score) / 100.0
    return transcript, detected_words, nlp_score

def run_pipeline(audio_path):
    """Tong hop ket qua giam dinh da tang."""
    # 1. Forensic Acoustic Analysis (60%)
    p_acoustic_fake = analyze_audio_forensics(audio_path)
    
    # 2. NLP Semantic Analysis (40%)
    transcript, detected_keywords, p_nlp_fake = analyze_nlp_transcript(audio_path)
    
    # Tong hop diem rui ro (Threat Score: 0 - 100%)
    threat_score = (p_acoustic_fake * 0.6) + (p_nlp_fake * 0.4)
    threat_percentage = round(threat_score * 100, 2)
    
    if threat_percentage < 40:
        verdict = "Real"
        level = "Safe"
    elif threat_percentage < 70:
        verdict = "Suspicious"
        level = "Warning"
    else:
        verdict = "Fake"
        level = "Danger"
        
    return {
        "verdict": verdict,
        "threat_score": threat_percentage,
        "risk_level": level,
        "acoustic_fake_prob": round(p_acoustic_fake * 100, 2),
        "nlp_fake_prob": round(p_nlp_fake * 100, 2),
        "transcript": transcript,
        "keywords": detected_keywords
    }