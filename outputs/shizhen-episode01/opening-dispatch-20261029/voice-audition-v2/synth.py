"""Local Kokoro audition per v2 line and voice; no network."""
import json, sys
from pathlib import Path
import soundfile as sf
from kokoro_onnx import Kokoro
from misaki import zh
out = Path(sys.argv[1]); plan = json.loads((out / 'plan.json').read_text())
M = Path('/home/reggie/.cache/ai-video-tools/kokoro-zh-v1.1')
k = Kokoro(str(M / 'kokoro-v1.1-zh.onnx'), str(M / 'voices-v1.1-zh.bin'), vocab_config=str(M / 'config.json'))
g2p = zh.ZHG2P(version='1.1'); phon = {}
for line in plan["lines"]:
    ph, _ = g2p(line["text"]); phon[line["id"]] = ph
    for v in plan["voices"][line["role"]]:
        s, sr = k.create(ph, voice=v, speed=plan["speed"], is_phonemes=True)
        sf.write(out / f"dry-{line['id']}-{v}.wav", s, sr, subtype="PCM_16")
(out / 'phonemes.json').write_text(json.dumps(phon, ensure_ascii=False, indent=1))
print("ok")
