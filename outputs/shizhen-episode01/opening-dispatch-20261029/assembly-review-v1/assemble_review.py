"""Review rough cut of the dispatch opening (ffmpeg, NOT the canonical HyperFrames render).

Purpose: let the user watch pacing and joins before the formal
CompositionSpec -> ResolvedTimeline -> HyperFrames continuous version.
Reads exact source bytes only; writes into this directory.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
FF = Path("/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg")
SCENES = ROOT / "outputs/shizhen-episode01/opening-dispatch-20261029/scenes-v1"


def fetched(shot: str, run: str) -> Path:
    rel = json.loads((SCENES / shot / "fetch-result.json").read_text())["artifact_path"]
    return ROOT / run / shot / rel


SOURCES = {
    "municipal": (ROOT / "outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4",
                  "b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d"),
    "master": (ROOT / "runs/shizhen-opening-dispatch-20261104/M1-r11/state/video-generation/fetch/files/"
               "9a776d418aff76d3da97c9e37677780e5c39931b852028ed7def612b186d2fa0.mp4",
               "9a776d418aff76d3da97c9e37677780e5c39931b852028ed7def612b186d2fa0"),
    "D2r1": (fetched("D2r1", "runs/shizhen-opening-dispatch-20261030"), "5946ddfe72ebac4e5dbf088f34022d24f574d36870db6fa60bcd7ab78ce6af1a"),
    "D3": (fetched("D3", "runs/shizhen-opening-dispatch-20261030"), "b312bba5ba817919f045fc4266469a77e93eb5b901d967332256210f76ccf85f"),
    "D4r1": (fetched("D4r1", "runs/shizhen-opening-dispatch-20261030"), "f9eb9fefe358566f1c97881bdfad84a3f730534198b0b9c0f7b2c1f1900acb67"),
    "D6": (fetched("D6", "runs/shizhen-opening-dispatch-20261030"), "30808fbb724021960159a3419be9b99dfc09dc898136f97c564bdcc8e607acaa"),
    "B6": (ROOT / "outputs/shizhen-episode01/fusion-B-motion-20261027/variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4",
           "d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a"),
}
ORDER = list(SOURCES)
# Picture segments: (source, in, out) in source seconds.
PICTURE = [("municipal", 0.0, 6.833), ("master", 3.40, 4.50), ("D2r1", 0.0, 6.0), ("D3", 0.0, 6.0),
           ("D4r1", 0.0, 7.0), ("master", 19.80, 23.90), ("D6", 0.0, 5.0), ("B6", 0.0, 21.875)]
starts, t = [], 0.0
for _s, a, b in PICTURE:
    starts.append(round(t, 3))
    t += b - a
TOTAL = round(t, 3)
S = dict(zip(["MUN", "D1", "D2", "D3", "D4", "D5", "D6", "B6"], starts))
# Audio: (source, in, out, output start, gain dB). Scene native ambience sits under the dialogue master lines.
AUDIO = [
    ("municipal", 0.0, 6.833, S["MUN"], None),            # ducked from 3.0 s (see filter)
    ("master", 0.00, 3.45, 3.25, 0),                       # L1 J-cut over municipal tail
    ("master", 3.40, 4.50, S["D1"], 0),                    # D1 desk typing
    ("D2r1", 0.0, 6.0, S["D2"], -8), ("master", 4.45, 8.10, S["D2"] + 0.4, 0),     # L2
    ("D3", 0.0, 6.0, S["D3"], -8), ("master", 9.35, 13.00, S["D3"] + 0.4, 0),      # L3
    ("D4r1", 0.0, 7.0, S["D4"], -8), ("master", 14.05, 18.10, S["D4"] + 0.4, 0),   # L4
    ("master", 19.80, 23.90, S["D5"], 0),                  # D5 writing + L5
    ("D6", 0.0, 5.0, S["D6"], -6), ("master", 25.50, 26.80, S["D6"] + 0.3, 0),     # L6
    ("master", 28.20, 30.00, S["D6"] + 2.4, 0),            # L7 ends before B6
    ("B6", 0.0, 21.875, S["B6"], 0),
]
# Whisper-estimated line times inside the master (+/-0.2 s), mapped to output time.
LINES = [("检修口报，电闸断了，绞盘还在收", 0.00, 3.32, 0.00, 3.25),
         ("七号楼报，下了三层，还在原来那层", 4.54, 7.96, 4.45, S["D2"] + 0.4),
         ("急诊说，系统里她已经死了，人还躺着", 9.46, 12.88, 9.35, S["D3"] + 0.4),
         ("人民路有人喊救命，在七楼，七楼早就封了", 14.16, 17.96, 14.05, S["D4"] + 0.4),
         ("记上，第十四起", 20.62, 22.44, 19.80, S["D5"]),
         ("三号站台", 25.70, 26.64, 25.50, S["D6"] + 0.3),
         ("暂无报告", 28.38, 29.86, 28.20, S["D6"] + 2.4)]


def ts(x: float) -> str:
    h, rem = divmod(x, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def main() -> None:
    for name, (path, digest) in SOURCES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    cues = [(text, out0 + (a - m0), out0 + (b - m0)) for text, a, b, m0, out0 in LINES]
    ass = HERE / "subtitles.ass"
    ass.write_text("\n".join([
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding",
        "Style: Default,Noto Sans CJK SC,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2.5,0.8,2,80,80,70,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *(f"Dialogue: 0,{ts(a)},{ts(b)},Default,,0,0,0,,{text}" for text, a, b in cues)]) + "\n")
    args = [str(FF), "-y", "-v", "error"]
    for name in ORDER:
        args += ["-i", str(SOURCES[name][0])]
    idx = {n: i for i, n in enumerate(ORDER)}
    parts, labels = [], []
    for k, (name, a, b) in enumerate(PICTURE):
        parts.append(f"[{idx[name]}:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=24,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[v{k}]")
        labels.append(f"[v{k}]")
    parts.append("".join(labels) + f"concat=n={len(PICTURE)}:v=1:a=0[vcat]")
    parts.append(f"[vcat]subtitles={ass}[vout]")
    alabels = []
    for k, (name, a, b, start, gain) in enumerate(AUDIO):
        chain = f"[{idx[name]}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo"
        if gain is None:
            chain += ",volume='if(gte(t,3.0),0.32,1)':eval=frame"
        else:
            chain += f",volume={gain}dB"
        chain += f",afade=t=in:d=0.02,afade=t=out:st={max(b - a - 0.04, 0):.3f}:d=0.04,adelay={int(start * 1000)}:all=1[a{k}]"
        parts.append(chain)
        alabels.append(f"[a{k}]")
    parts.append("".join(alabels) + f"amix=inputs={len(AUDIO)}:normalize=0:duration=longest,atrim=0:{TOTAL}[aout]")
    out = HERE / "失帧-调度对讲开场-审看粗剪01.mp4"
    args += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", "[aout]", "-r", "24",
             "-c:v", "libx264", "-preset", "medium", "-b:v", "16M", "-maxrate", "20M", "-bufsize", "32M",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart",
             "-t", str(TOTAL), str(out)]
    subprocess.run(args, check=True)
    receipt = {"kind": "review-rough-cut/ffmpeg (non-canonical; not HyperFrames, not Production)",
               "sources": {n: {"path": str(p.relative_to(ROOT)), "sha256": d} for n, (p, d) in SOURCES.items()},
               "picture": PICTURE, "segment_starts": S, "audio": AUDIO, "subtitles": [list(c) for c in cues],
               "total_seconds": TOTAL, "output": str(out.relative_to(ROOT)),
               "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
               "known_gaps": ["D4 木板后呼救声未做", "D6 站牌时钟未补", "字幕时间来自 Whisper 估计（±0.2s）",
                              "母带 480p 放大到 1080p", "正式连续版须走 CompositionSpec→ResolvedTimeline→HyperFrames"]}
    (HERE / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": receipt["output"], "seconds": TOTAL, "sha256": receipt["output_sha256"][:16]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
