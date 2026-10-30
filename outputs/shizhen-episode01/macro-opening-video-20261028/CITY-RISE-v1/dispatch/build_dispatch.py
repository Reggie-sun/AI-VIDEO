"""Lay trimmed Kokoro lines on a 20s timeline, color them as walkie-talkie radio,
add squelch clicks and a static bed, and emit ASS captions (shot-local times).

Local only; review layer, not a Production P4 render.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FF = "/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg"
SR = 48000
LENGTH = 20.0
START = 0.25
GAPS = {"L2": 0.15, "L3": 0.15, "L4": 0.10, "L5": 0.20, "L6": 0.10, "L7": 0.15, "L8": 0.10}
RADIO = ("highpass=f=380,lowpass=f=3300,acompressor=threshold=-24dB:ratio=6:attack=3:release=60:makeup=6,"
         "asoftclip=type=tanh:threshold=0.6,equalizer=f=1800:t=q:w=1.2:g=4")


def pcm(path: Path, af: str | None = None) -> np.ndarray:
    args = [FF, "-v", "error", "-i", str(path)] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(args, capture_output=True, check=True).stdout, np.float32).copy()


def squelch(rng: np.random.Generator, seconds: float, level: float) -> np.ndarray:
    n = int(seconds * SR)
    burst = rng.standard_normal(n).astype(np.float32) * level
    env = np.linspace(1, 0, n, dtype=np.float32) ** 2
    return burst * env


def main() -> None:
    script = json.loads((HERE / "dispatch-script.json").read_text())
    rng = np.random.default_rng(20261028)
    voice = np.zeros(int(LENGTH * SR), np.float32)
    clicks = np.zeros_like(voice)
    cues, t = [], START
    for line in script["lines"]:
        t += GAPS.get(line["id"], 0.0)
        src = next((HERE / "trim").glob(line["id"] + "-*.wav"))
        x = pcm(src, RADIO)
        x = x / (np.abs(x).max() + 1e-9) * 0.55
        a = int(t * SR)
        assert a + len(x) <= len(voice), (line["id"], t)
        voice[a:a + len(x)] += x
        on = squelch(rng, 0.06, 0.25); off = squelch(rng, 0.11, 0.18)
        clicks[max(0, a - len(on)):a] += on[:a - max(0, a - len(on))]
        e = a + len(x); clicks[e:e + len(off)] += off[:len(clicks) - e]
        cues.append({"id": line["id"], "text": line["text"], "start": round(t, 3), "end": round(t + len(x) / SR, 3), "source": src.name,
                     "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest()})
        t += len(x) / SR
    assert t <= LENGTH - 0.15, t
    first, last = int(cues[0]["start"] * SR) - SR // 4, int(cues[-1]["end"] * SR) + SR // 5
    static = rng.standard_normal(len(voice)).astype(np.float32) * 0.012
    gate = np.zeros_like(voice); gate[first:last] = 1.0
    ramp = SR // 10; gate[first:first + ramp] = np.linspace(0, 1, ramp); gate[last - ramp:last] = np.linspace(1, 0, ramp)
    mix = voice + clicks + static * gate
    raw = HERE / "dispatch-radio-20s.f32"
    raw.write_bytes(mix.astype(np.float32).tobytes())
    out = HERE / "dispatch-radio-20s-48k.wav"
    subprocess.run([FF, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
                    "-af", RADIO.split(",asoftclip")[0].replace("highpass=f=380", "highpass=f=300") + ",alimiter=limit=0.8",
                    "-c:a", "pcm_s16le", str(out)], check=True)
    raw.unlink()
    for cue in cues[:-1]:
        nxt = cues[cues.index(cue) + 1]["start"]
        cue["caption_end"] = round(min(cue["end"] + 0.25, nxt - 0.02), 3)
    cues[-1]["caption_end"] = round(min(cues[-1]["end"] + 0.25, LENGTH), 3)
    (HERE / "dispatch-cues.json").write_text(json.dumps({"timeline": "CITY-RISE shot-local seconds", "length": LENGTH,
        "audio": out.name, "audio_sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "radio_filter": RADIO,
        "cues": cues}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps([(c["id"], c["start"], c["end"]) for c in cues], ensure_ascii=False))


if __name__ == "__main__":
    main()
