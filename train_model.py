import os
import glob
import joblib
import numpy as np
import librosa
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, f1_score

def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=16000, mono=True)
    
    # 1. MFCC (20 he so dau)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    mfcc_mean = np.mean(mfcc, axis=1)
    
    # 2. Chroma STFT
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    
    # 3. Spectral Contrast & Rolloff
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    contrast_mean = np.mean(contrast, axis=1)
    
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    rolloff_mean = np.mean(rolloff)
    
    # 4. Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)
    zcr_mean = np.mean(zcr)
    
    # Vector dac trung gop (40 chieu)
    feature_vector = np.hstack([
        mfcc_mean,
        chroma_mean,
        contrast_mean,
        rolloff_mean,
        zcr_mean
    ])
    return feature_vector

def load_data():
    X = []
    y = []
    
    # Label 0: Real, Label 1: Deepfake
    real_files = glob.glob('dataset/real/*.wav') + glob.glob('dataset/real/*.mp3')
    fake_files = glob.glob('dataset/fake/*.wav') + glob.glob('dataset/fake/*.mp3')
    
    print(f'Dang load {len(real_files)} file Real va {len(fake_files)} file Fake...')
    
    for f in real_files:
        try:
            feats = extract_features(f)
            X.append(feats)
            y.append(0)
        except Exception as e:
            print(f'Loi doc file {f}: {e}')
            
    for f in fake_files:
        try:
            feats = extract_features(f)
            X.append(feats)
            y.append(1)
        except Exception as e:
            print(f'Loi doc file {f}: {e}')
            
    return np.array(X), np.array(y)

def train():
    X, y = load_data()
    if len(X) < 4:
        print('Can it nhat 2 file real va 2 file fake de chay pipeline train.')
        return
        
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Random Forest Classifier
    clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    clf.fit(X_scaled, y)
    
    y_pred = clf.predict(X_scaled)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, zero_division=0)
    
    print('=' * 50)
    print(f'HUAN LUYEN HOAN TAT:')
    print(f'- Training Accuracy: {acc * 100:.2f}%')
    print(f'- F1-Score: {f1:.4f}')
    print('=' * 50)
    
    # Dong goi model va scaler
    joblib.dump(clf, 'model_deepfake.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print('Da luu: model_deepfake.pkl va scaler.pkl')

if __name__ == '__main__':
    train()
