import sounddevice as sd
import soundfile as sf

sr = 16000
duration = 4  # Thu moi mau 4 giay

for i in range(1, 4):
    print(f'=== CHUAN BI THU MAU {i}/3 ===')
    input('Nhan Enter va noi 1 cau bat ky trong 4 giay...')
    print('Dang thu am...')
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    file_path = f'dataset/real/mic_sample_{i}.wav'
    sf.write(file_path, audio, sr)
    print(f'Da luu: {file_path}\n')
print('Hoan tat thu 3 mau giong micro thuc te!')
