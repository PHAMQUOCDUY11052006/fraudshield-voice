import os
import glob
import pickle
import numpy as np
import librosa
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def extract_features(file_path):
    """Trích xuất 40 đặc trưng âm học chuẩn hóa."""
    try:
        y, sr = librosa.load(file_path, sr=16000, mono=True)

        # Cắt khoảng lặng hai đầu
        y_trimmed, _ = librosa.effects.trim(y, top_db=20)
        if len(y_trimmed) > sr * 0.3:
            y = y_trimmed

        # Chuẩn hóa năng lượng RMS
        rms = np.sqrt(np.mean(y**2))
        if rms > 1e-6:
            y = y / rms

        # 20 MFCCs
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        mfcc_mean = np.mean(mfcc.T, axis=0)

        # 12 Chroma
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma.T, axis=0)

        # 7 Spectral Contrast
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(contrast.T, axis=0)

        # 1 Tonnetz
        tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
        tonnetz_mean = np.mean(tonnetz.T, axis=0)

        return np.hstack([mfcc_mean, chroma_mean, contrast_mean, tonnetz_mean[:1]])
    except Exception as e:
        print(f"[!] Loi doc file {file_path}: {e}")
        return None

def train():
    real_files = glob.glob("dataset/real/*.wav") + glob.glob("dataset/real/*.mp3")
    fake_files = glob.glob("dataset/fake/*.wav") + glob.glob("dataset/fake/*.mp3")

    print(f"[*] So luong mau: Real = {len(real_files)} | Fake = {len(fake_files)}")
    if len(real_files) == 0 or len(fake_files) == 0:
        print("[!] Thu muc dataset/real hoac dataset/fake dang thieu file.")
        return

    X, y = [], []

    print("[*] Dang trich xuat dac trung cho tap Real...")
    for f in real_files:
        feat = extract_features(f)
        if feat is not None:
            X.append(feat)
            y.append(0)  # 0: Real

    print("[*] Dang trich xuat dac trung cho tap Fake...")
    for f in fake_files:
        feat = extract_features(f)
        if feat is not None:
            X.append(feat)
            y.append(1)  # 1: Fake

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Random Forest can bang trong so
    clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train_scaled, y_train)

    y_pred = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[✓] Do chinh xac tren tap kiem thu: {acc * 100:.2f}%\n")
    print(classification_report(y_test, y_pred, target_names=["Real", "Fake"]))

    with open("model_deepfake.pkl", "wb") as f:
        pickle.dump(clf, f)
    with open("scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    print("[✓] Da xuat model_deepfake.pkl va scaler.pkl thanh cong.")

if __name__ == "__main__":
    train()