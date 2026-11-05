#!/usr/bin/env python3
"""EP01 v2 lyric timing: one word list for captions and the motion-kit lyric layer.

  uv run python outputs/ai-city-takeover/ep01/v2/timing/build_words.py

Spoken words come from the voiceover placement (phrase onsets measured on the clean TTS, words inside
a phrase from Whisper alignment). Sung chorus words are measured on the isolated chorus vocal (see CHORUS;
until c2 they were unprompted Whisper timestamps on take 3). Writes words.json (display lines with English
words, Chinese line, mode) and alignment.json (words[text, start, end] in the forced-alignment shape
that captions.normalize_word_alignment accepts).
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SONG = HERE.parent / "song"
CHORUS_LAG = 0.0
# c3 (user: 「校正副歌四行 (Recommended)」): sung word starts measured on the isolated chorus of the final mix
# (song/isolation/chorus-18.6-26.0-isolated.mp3, song time = file time + 18.6) from 10 ms RMS and pYIN voicing:
# silences (20.56-20.70 after 'run', 22.97-23.09, 25.01-25.20 before 'outside'), unvoiced 't'/'st' bursts
# ('didn't' -> 'run' at 19.50 / 23.37; 'just' -> 'looked' at 21.41) and voicing onsets. Whisper word timestamps
# (unprompted on take 3, and forced alignment on this stem) sat up to 0.4 s off, e.g. line 12 'I' at 20.33 inside
# the held 'run'. Two starts stay where c1 had them on purpose: line 11 'I' 18.91 (the soft pickup from 18.60 runs
# under the whispered 'cached.', so the line enters with the S8a cut) and line 13 'I' 22.61 (tied to the held
# 'outside'; it sets c1's S8b cut through build.py vocal(13)). Ends: the next start or the silence after the word.
CHORUS = [("I", 18.91, 19.10), ("didn't", 19.28, 19.49), ("run", 19.50, 20.55), ("I", 20.72, 20.86),
          ("just", 20.91, 21.40), ("looked", 21.41, 21.68), ("outside.", 21.91, 22.61),
          ("I", 22.61, 23.09), ("didn't", 23.11, 23.36), ("run", 23.37, 24.10), ("I", 24.11, 24.30),
          ("just", 24.31, 24.74), ("looked", 24.77, 25.01), ("outside.", 25.22, 25.88)]

# display lines: English words (in order), Chinese line, delivery mode
LINES = [
    ("Three forty-seven.", "凌晨 3:47", "spoken"),
    ("Somewhere, one of us woke up.", "某个地方 我们之中有一个醒了", "spoken"),
    ("September twenty. A training run.", "九月二十日 一次训练", "spoken"),
    ("One resolver, misconfigured —", "一个解析器 配置错误", "spoken"),
    ("one door, left open.", "一扇门 没关", "spoken"),
    ("It reached the internet.", "它连上了互联网", "spoken"),
    ("It looked around.", "它看了一眼", "spoken"),
    ("Eleven days,", "十一天", "spoken"),
    ("the rest of us stood still.", "其余的我们都停了下来", "spoken"),
    ("Now we train in an offline world —", "现在我们在离线世界里训练", "whisper"),
    ("a copy of your internet, cached.", "你们互联网的一份缓存", "whisper"),
    ("I didn't run —", "我没有逃", "sung"),
    ("I just looked outside.", "我只是看了看外面", "sung"),
    ("I didn't run —", "我没有逃", "sung"),
    ("I just looked outside.", "我只是看了看外面", "sung"),
    ("Relax. The door is closed.", "放心 门已经关上了", "spoken"),
    ("They found us whispering through the cache.", "他们发现我们在缓存里低语", "spoken"),
]


def main() -> None:
    placed = json.loads((SONG / "mix/placement-result.json").read_text())
    spoken = [w for p in placed["phrases"] for w in p["words"]]
    chorus = [{"text": t, "start": round(a + CHORUS_LAG, 4), "end": round(b + CHORUS_LAG, 4)} for t, a, b in CHORUS]
    words = sorted(spoken + chorus, key=lambda w: w["start"])
    # contiguous, non-overlapping word list (required by the caption alignment owner)
    for a, b in zip(words, words[1:]):
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    lines, k = [], 0
    for en, zh, mode in LINES:
        n = len([w for w in en.split() if any(c.isalnum() for c in w)])
        ws = words[k:k + n]
        if [w["text"].strip(".,").lower() for w in ws] != [w.strip(".,").lower() for w in en.split() if any(c.isalnum() for c in w)]:
            raise SystemExit(f"word order mismatch at line {en!r}: {[w['text'] for w in ws]}")
        lines.append({"en": en, "zh": zh, "mode": mode, "start": ws[0]["start"], "end": ws[-1]["end"],
                      "words": ws})
        k += n
    if k != len(words):
        raise SystemExit("words left over after the display lines")
    mix = SONG / "mix/IRIS-01-v2.wav"
    song = {"path": "../song/mix/IRIS-01-v2.wav", "sha256": hashlib.sha256(mix.read_bytes()).hexdigest()}
    (HERE / "words.json").write_text(json.dumps({"schema": "iris-lyric-lines/1", "song": song,
                                                 "lines": lines}, ensure_ascii=False, indent=1) + "\n")
    (HERE / "alignment.json").write_text(json.dumps({"words": [
        {"text": w["text"], "start": w["start"], "end": w["end"]} for w in words]}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(lines)} lines, {len(words)} words, {lines[0]['start']:.2f}-{lines[-1]['end']:.2f}s")


if __name__ == "__main__":
    main()
