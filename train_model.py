import os
import glob
import joblib
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from core_ai import extract_features_vector

print('Dang load du lieu huan luyen...')
X, y = [], []

# 1. Load Real samples (Nhan 0)
real_files = glob.glob('dataset/real/*.wav') + glob.glob('dataset/real/*.mp3')
for f in real_files:
    try:
        sig, sr = librosa.load(f, sr=16000, mono=True)
        feats = extract_features_vector(sig, sr)
        X.append(feats.flatten())
        y.append(0)
    except Exception:
        pass

# 2. Load Fake samples (Nhan 1)
fake_files = glob.glob('dataset/fake/*.wav') + glob.glob('dataset/fake/*.mp3')
for f in fake_files:
    try:
        sig, sr = librosa.load(f, sr=16000, mono=True)
        feats = extract_features_vector(sig, sr)
        X.append(feats.flatten())
        y.append(1)
    except Exception:
        pass

X = np.array(X)
y = np.array(y)

print(f'Tong cong: {np.sum(y == 0)} mau Real va {np.sum(y == 1)} mau Fake.')

# Chuan hoa dac trung
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Huan luyen voi Random Forest toi uu chong overfitting tren moi truong thuc
clf = RandomForestClassifier(
    n_estimators=150,
    max_depth=5,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42
)
clf.fit(X_scaled, y)

joblib.dump(clf, 'model_deepfake.pkl')
joblib.dump(scaler, 'scaler.pkl')

train_acc = clf.score(X_scaled, y) * 100.0
print(f'Huan luyen thanh cong! Accuracy tong the: {train_acc:.2f}%')
print('Da luu lai model_deepfake.pkl va scaler.pkl!')
