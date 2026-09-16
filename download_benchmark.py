import soundfile as sf
from datasets import load_dataset

print('Dang tai mau tieng Viet chuan tu AILAB-VNUHCM/vivos (Real)...')
vivos = load_dataset('AILAB-VNUHCM/vivos', split='train', streaming=True, trust_remote_code=True)

real_count = 0
for item in vivos:
    audio = item['audio']
    out_path = f'dataset/real/vivos_{real_count}.wav'
    sf.write(out_path, audio['array'], audio['sampling_rate'])
    real_count += 1
    if real_count >= 50:
        break
print(f'Da tai xong {real_count} file Real tu VIVOS!')
