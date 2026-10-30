"""Local Kokoro synthesis of the dispatch lines; no network, no credential."""
import hashlib, json, sys, time
from pathlib import Path
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from misaki import zh
D = Path('/home/reggie/.cache/ai-video-tools/kokoro-zh-v1.1')
out = Path(sys.argv[1]); script = json.loads((out / 'dispatch-script.json').read_text())
speed = float(sys.argv[2])
k = Kokoro(str(D / 'kokoro-v1.1-zh.onnx'), str(D / 'voices-v1.1-zh.bin'), vocab_config=str(D / 'config.json'))
g2p = zh.ZHG2P(version='1.1')
records = []
for line in script['lines']:
    voice = script['speakers'][line['speaker']]['voice']
    phonemes, _ = g2p(line['text'])
    t = time.time(); samples, sr = k.create(phonemes, voice=voice, speed=speed, is_phonemes=True)
    path = out / 'raw' / f"{line['id']}-{voice}.wav"; sf.write(path, samples, sr, subtype='PCM_16')
    records.append({'id': line['id'], 'voice': voice, 'text': line['text'], 'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'sample_rate': sr, 'duration_seconds': round(len(samples) / sr, 3), 'generation_seconds': round(time.time() - t, 2)})
prov = {'tool': 'kokoro-onnx', 'model': 'Kokoro-82M-v1.1-zh', 'model_sha256': hashlib.sha256((D / 'kokoro-v1.1-zh.onnx').read_bytes()).hexdigest(),
        'voices_sha256': hashlib.sha256((D / 'voices-v1.1-zh.bin').read_bytes()).hexdigest(), 'license': 'Apache-2.0', 'speed': speed,
        'remote_calls': 0, 'hearing': 'USER_REVIEW_PENDING', 'lines': records}
(out / 'raw' / 'synthesis-provenance.json').write_text(json.dumps(prov, ensure_ascii=False, indent=2) + '\n')
print(json.dumps([(r['id'], r['duration_seconds']) for r in records]))
