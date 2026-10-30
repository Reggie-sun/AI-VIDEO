"""Local Kokoro audition samples (no network): same line, different voices."""
import json, sys
from pathlib import Path
import soundfile as sf
from kokoro_onnx import Kokoro
from misaki import zh
out = Path(sys.argv[1]); c = json.loads((out / 'candidates.json').read_text())
M = Path('/home/reggie/.cache/ai-video-tools/kokoro-zh-v1.1')
k = Kokoro(str(M / 'kokoro-v1.1-zh.onnx'), str(M / 'voices-v1.1-zh.bin'), vocab_config=str(M / 'config.json'))
g2p = zh.ZHG2P(version='1.1')
for role, key in (("dispatcher", "dispatcher_voices"), ("field", "field_voices")):
    ph, _ = g2p(c["lines"][role])
    for v in c[key]:
        s, sr = k.create(ph, voice=v, speed=c["speed"], is_phonemes=True)
        sf.write(out / f"{role}-{v}.wav", s, sr, subtype="PCM_16")
print("ok")
