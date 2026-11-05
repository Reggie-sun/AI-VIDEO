#!/usr/bin/env python
"""Step 0: extract audio + htdemucs stems. Usage: 03_audio_00_stems.py <analysis_root>
Run with the isolated venv python (/home/reggie/.cache/ev-audio-venv/bin/python) -I.
Writes work/audio_tmp/mix.wav and work/audio_tmp/stems/{vocals,drums,bass,other}.wav (44.1k stereo wav)."""
import sys, os, subprocess, json
root = sys.argv[1]
src = os.path.join(root, "..", "source", "2103533196721704960.mp4")
if os.path.exists(os.path.join(root, "manifest.json")):
    m = json.load(open(os.path.join(root, "manifest.json")))
    src = os.path.join(root, "..", "..", "..", m["source_video"]["path_from_repo_root"])
src = os.path.abspath(src)
tmp = os.path.join(root, "work", "audio_tmp"); os.makedirs(tmp, exist_ok=True)
mix = os.path.join(tmp, "mix.wav")
if not os.path.exists(mix):
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", mix])
import torch, torchaudio, soundfile as sf, numpy as np
from demucs.pretrained import get_model
from demucs.apply import apply_model
model = get_model("htdemucs").cuda().eval()
wav, sr = sf.read(mix, dtype="float32"); wav = torch.from_numpy(wav.T)
assert sr == model.samplerate, (sr, model.samplerate)
ref = wav.mean(0); mu, sd = ref.mean(), ref.std()
with torch.no_grad():
    out = apply_model(model, ((wav - mu) / sd)[None].cuda(), shifts=1, split=True, overlap=0.25, progress=False)[0]
out = out * sd + mu
os.makedirs(os.path.join(tmp, "stems"), exist_ok=True)
for name, s in zip(model.sources, out):
    sf.write(os.path.join(tmp, "stems", f"{name}.wav"), s.cpu().numpy().T, sr, subtype="PCM_16")
    print("wrote", name)
