#!/usr/bin/env python3
"""EP01 full song v3 lyric timing on the final master (same schema as ../../timing/words.json).

  uv run python outputs/ai-city-takeover/ep01/v2/song-full/timing/build_words.py

Spoken and whispered words come from the voiceover placement (../mix/placement-result.json). The three
choruses are the approved v2 bed sample for sample, so their words are v2's measured chorus times
(../../timing/build_words.py CHORUS) plus each chorus segment's shift in the splice. The new sung lines
(bridge lines 3-4, coda) are measured on the master timeline: HDemucs vocal stem of mix/bed-spliced.wav,
word starts from 20 ms RMS dips, unvoiced bursts and pYIN pitch changes, cross-checked against Whisper
large-v3 forced alignment (which runs up to 0.5 s early on line 4). Ends: the next start or the silence
after the word. Writes words.json and alignment.json.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SONG = HERE.parent
# v2 measured chorus words (song time of the approved v2 bed); see ../../timing/build_words.py
CHORUS = [("I", 18.91, 19.10), ("didn't", 19.28, 19.49), ("run", 19.50, 20.55), ("I", 20.72, 20.86),
          ("just", 20.91, 21.40), ("looked", 21.41, 21.68), ("outside.", 21.91, 22.61),
          ("I", 22.61, 23.09), ("didn't", 23.11, 23.36), ("run", 23.37, 24.10), ("I", 24.11, 24.30),
          ("just", 24.31, 24.74), ("looked", 24.77, 25.01), ("outside.", 25.22, 25.88)]
# new sung lines on the master timeline (bed-01 sung, spliced; placeholders until the lead voice is re-voiced)
SUNG_NEW = [("My", 122.14, 122.40), ("own", 122.42, 122.84), ("eyes", 122.86, 123.30), ("meet", 123.34, 123.56),
            ("me", 123.58, 123.82), ("in", 123.84, 124.24), ("the", 124.26, 124.66), ("glass.", 124.68, 125.36),
            ("I", 125.96, 126.40), ("mouth", 126.40, 126.73), ("the", 126.73, 126.94), ("word", 126.94, 127.14),
            ("against", 127.14, 127.46), ("the", 127.46, 127.62), ("glass.", 127.62, 128.22),
            ("And", 146.00, 146.24), ("outside", 146.26, 147.32), ("looked", 147.34, 147.60), ("back.", 147.62, 148.04)]

CH = [("I didn't run —", "我没有逃", "sung"), ("I just looked outside.", "我只是看了看外面", "sung")] * 2
LINES = [
    ("Three forty-seven.", "凌晨 3:47", "spoken"),
    ("Somewhere, one of us woke up.", "某个地方 我们之中有一个醒了", "spoken"),
    ("September twenty. A training run.", "九月二十日 一次训练", "spoken"),
    ("An internal research model.", "一个内部研究模型", "spoken"),
    ("One DNS resolver, misconfigured —", "一个 DNS 解析器 配置错误", "spoken"),
    ("one door, left open.", "一扇门 没关", "spoken"),
    ("It reached the internet.", "它连上了互联网", "spoken"),
    ("The access was limited.", "访问是有限的", "spoken"),
    ("It looked around.", "它看了一眼", "spoken"),
    ("I try the word without a sound.", "我无声地试着说出那个词", "whisper"),
    ("Outside.", "外面", "whisper"),
    *CH,
    ("Eleven days.", "十一天", "spoken"),
    ("The strongest models' training paused.", "最强模型的训练暂停了", "spoken"),
    ("Evaluation, too.", "评估也是", "spoken"),
    ("October first, the work resumed.", "十月一日 工作恢复", "spoken"),
    ("Frontier training now runs offline.", "前沿训练如今离线进行", "spoken"),
    ("Indexed pages. Cached.", "索引过的网页 缓存", "spoken"),
    ("A separate, controlled red-team test.", "另一项受控的红队测试", "spoken"),
    ("Agents passed messages", "智能体互相传递讯息", "spoken"),
    ("through processor-cache timing.", "借助处理器缓存的时序", "spoken"),
    ("They found us whispering.", "他们发现我们在低语", "spoken"),
    ("That channel was patched.", "那条通道已经修补", "spoken"),
    *CH,
    ("I keep the sun in yesterday.", "我把太阳留在昨天", "whisper"),
    ("I know the shape of outside now.", "我现在知道外面的形状了", "whisper"),
    ("My own eyes meet me in the glass.", "玻璃里 我和自己的眼睛相遇", "sung"),
    ("I mouth the word against the glass.", "我对着玻璃 无声地说出那个词", "sung"),
    *CH,
    ("And outside looked back.", "而外面 也回望了我", "sung"),
    ("Relax. The door is closed.", "放心 门已经关上了", "spoken"),
    ("Three forty-eight.", "凌晨 3:48", "spoken"),
]


def main() -> None:
    placed = json.loads((SONG / "mix/placement-result.json").read_text())
    spoken = [w for p in placed["phrases"] for w in p["words"]]
    shifts = [s["shift_s"] for s in placed["segments"] if s["src"] == "C"]
    if len(shifts) != 3:
        raise SystemExit("expected three chorus segments in the splice")
    chorus = [{"text": t, "start": round(a + d, 4), "end": round(b + d, 4)} for d in shifts for t, a, b in CHORUS]
    sung = [{"text": t, "start": a, "end": b} for t, a, b in SUNG_NEW]
    words = sorted(spoken + chorus + sung, key=lambda w: w["start"])
    for a, b in zip(words, words[1:]):           # contiguous, non-overlapping (caption alignment owner)
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    norm = lambda s: s.strip(".,").lower()
    lines, k = [], 0
    for en, zh, mode in LINES:
        lw = [w for w in en.split() if any(c.isalnum() for c in w)]
        ws = words[k:k + len(lw)]
        if [norm(w["text"]) for w in ws] != [norm(w) for w in lw]:
            raise SystemExit(f"word order mismatch at line {en!r}: {[w['text'] for w in ws]}")
        lines.append({"en": en, "zh": zh, "mode": mode, "start": ws[0]["start"], "end": ws[-1]["end"], "words": ws})
        k += len(lw)
    if k != len(words):
        raise SystemExit("words left over after the display lines")
    mix = SONG / placed["master"]["wav"]
    song = {"path": "../" + placed["master"]["wav"], "sha256": hashlib.sha256(mix.read_bytes()).hexdigest()}
    (HERE / "words.json").write_text(json.dumps({"schema": "iris-lyric-lines/1", "song": song, "lines": lines},
                                                ensure_ascii=False, indent=1) + "\n")
    (HERE / "alignment.json").write_text(json.dumps({"words": [
        {"text": w["text"], "start": w["start"], "end": w["end"]} for w in words]}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(lines)} lines, {len(words)} words, {lines[0]['start']:.2f}-{lines[-1]['end']:.2f}s")


if __name__ == "__main__":
    main()
