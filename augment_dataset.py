import os
import glob
import librosa
import soundfile as sf

def augment_and_split(input_dir, output_dir, prefix):
    os.makedirs(output_dir, exist_ok=True)
    files = glob.glob(os.path.join(input_dir, "*.wav")) + glob.glob(os.path.join(input_dir, "*.mp3"))
    count = 0
    
    for f in files:
        try:
            y, sr = librosa.load(f, sr=16000, mono=True)
            duration = len(y) / sr
            chunk_len = 3 * sr  # Doan 3 giay
            
            # Cat thanh cac mau 3s
            for i in range(0, len(y) - chunk_len + 1, chunk_len):
                chunk = y[i:i + chunk_len]
                out_name = f"{output_dir}/{prefix}_chunk_{count}.wav"
                sf.write(out_name, chunk, sr)
                count += 1
                
                # Tang cuong: Them bien the thay doi toc do nhe (Augmentation)
                chunk_speed = librosa.effects.time_stretch(chunk, rate=1.08)
                sf.write(f"{output_dir}/{prefix}_aug_{count}.wav", chunk_speed, sr)
                count += 1
        except Exception as e:
            print(f"Bo qua file {f}: {e}")
            
    print(f"Da tao thanh cong {count} mau du lieu chuan hoa tai {output_dir}")

augment_and_split("dataset/real", "dataset/real", "real")
augment_and_split("dataset/fake", "dataset/fake", "fake")
