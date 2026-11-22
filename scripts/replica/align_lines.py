"""Align approved subtitle lines to each narration take using Whisper word timings.

Transcribes the exact normalized take with no prompt and matches the script to the
ASR characters. The audio reads `say` (number readings such as 一千日元 for 1000日元), so
line edges are first carried from the subtitle text onto `say` through a difflib alignment, and timing uses the
spoken characters. Both the subtitle and the spoken alignment are tried and the higher ratio wins (Whisper writes
some numbers as digits, some as words); groups whose two texts agree are unaffected. Every line must match at least MIN_LINE of its characters: a dropped
sentence barely moves the group ratio, so low lines are listed and the script exits 2 after writing the file.
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode

from scripts.replica._local import cli, read_json, tool_path, write_bytes
from scripts.replica import normalize_vo, transcribe, tts_run

PUNCT = re.compile(r"[\s，。、,.!?！？：:；;「」『』“”‘’（）()《》【】…—·～~\"'-]")
MIN_LINE = 0.8  # a line with fewer matched characters than this is treated as dropped or misread


def norm(s: str) -> str:
    return PUNCT.sub("", s).lower()


def char_times(segments) -> list[tuple[str, float, float]]:
    chars = []
    for seg in segments:
        for w in seg.get("words", []):
            t = norm(w["word"])
            if not t:
                continue
            d = (w["end"] - w["start"]) / len(t)
            for i, c in enumerate(t):
                chars.append((c, w["start"] + i * d, w["start"] + (i + 1) * d))
    return chars


CLAUSE_END = set("，。、,.!?！？：:；;…")


def _cuts(say: str) -> set[int]:
    """Normalised positions in `say` that directly follow a clause mark: preferred line edges."""
    cuts, n = set(), 0
    for ch in say:
        if norm(ch):
            n += 1
        elif ch in CLAUSE_END:
            cuts.add(n)
    return cuts


def _carry(i: int, ops, cuts=frozenset()) -> int:
    """Map position i of sequence a onto sequence b through SequenceMatcher opcodes. Text inserted in b exactly at
    an edge goes to whichever side a clause mark in b points to (default: the next line); inner points of a
    replaced run map proportionally."""
    for tag, i1, i2, j1, j2 in ops:
        if tag == "insert" and i == i1:
            marks = [j for j in range(j1, j2 + 1) if j in cuts]
            return marks[-1] if marks else j1
        if i1 <= i < i2:
            if tag == "equal":
                return j1 + (i - i1)
            return j1 + round((i - i1) * (j2 - j1) / (i2 - i1))
    return ops[-1][4] if ops else 0


def spoken_spans(lines: list[str], say: str | None) -> tuple[str, list[tuple[int, int]]]:
    """Normalised spoken text and each line's [lo, hi) span in it. Lines that normalise to nothing get an empty
    span; spoken text that would fall to them goes to the previous non-empty line."""
    sub = [norm(l) for l in lines]
    edges, pos = [], 0
    for s in sub:
        edges.append(pos)
        pos += len(s)
    edges.append(pos)
    joined = "".join(sub)
    spoken = norm(say) if say else joined
    if spoken != joined:
        ops = difflib.SequenceMatcher(None, joined, spoken, autojunk=False).get_opcodes()
        cuts = _cuts(say)
        edges = [_carry(e, ops, cuts) for e in edges[:-1]] + [len(spoken)]
        for k in range(1, len(edges)):
            edges[k] = max(edges[k], edges[k - 1])
    spans = [[edges[k], edges[k + 1]] for k in range(len(lines))]
    last = None
    for k, s in enumerate(sub):
        if s:
            last = k
        elif spans[k][1] > spans[k][0]:
            if last is not None:
                spans[last][1] = spans[k][1]
            elif k + 1 < len(spans):
                spans[k + 1][0] = spans[k][0]
            spans[k] = [spans[k][1], spans[k][1]] if last is not None else [spans[k][0], spans[k][0]]
    return spoken, [tuple(x) for x in spans]


def match_lines(lines: list[str], chars, say: str | None = None) -> tuple[float, list[dict]]:
    """Align against the subtitle text and, when `say` differs, against the spoken text too; keep the better.
    Whisper sometimes writes spoken numbers as digits (1000日元) and sometimes as words (一千日元)."""
    best = _match(lines, chars, None)
    if say and norm(say) != "".join(norm(l) for l in lines):
        spoken = _match(lines, chars, say)
        if spoken[0] > best[0]:
            best = spoken
    return best


def _match(lines: list[str], chars, say: str | None) -> tuple[float, list[dict]]:
    asr = "".join(c for c, _, _ in chars)
    spoken, spans = spoken_spans(lines, say)
    sm = difflib.SequenceMatcher(None, spoken, asr, autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    out = []
    for k, l in enumerate(lines):
        lo, hi = spans[k]
        idx = [mp[i] for i in range(lo, hi) if i in mp]
        out.append({"text": l, "start": chars[idx[0]][1] if idx else None, "end": chars[idx[-1]][2] if idx else None,
                    "matched": len(idx), "chars": hi - lo})
    return round(sm.ratio(), 3), out


def weak_lines(lines: list[dict]) -> list[dict]:
    """Lines with subtitle text whose spoken span is missing, empty or matched below MIN_LINE."""
    return [x for x in lines if norm(x["text"]) and
            (x["start"] is None or not x["chars"] or x["matched"] / x["chars"] < MIN_LINE)]


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("vo_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--whisper-checkpoint", type=Path, required=True)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_args(argv)
    cfg = read_json(args.script)
    groups = tts_run.selected_groups(cfg)
    takes = {g["id"]: normalize_vo.processed_path(g, cfg, args.vo_dir) for g in groups}
    if any(path.is_symlink() or not path.is_file() for path in takes.values()):
        raise AiVideoError(ErrorCode.AUDIO_ASSET_INVALID, "The current normalized voice takes are required.")
    if args.output.resolve() in {args.script.resolve(), *(path.resolve() for path in takes.values())}:
        raise AiVideoError(ErrorCode.OUTPUT_INVALID, "Alignment output overlaps an input.")
    ffmpeg = tool_path("ffmpeg", args.ffmpeg)
    model = transcribe.load_model(args.whisper_checkpoint)
    res, bad = {}, []
    for g in groups:
        audio = takes[g["id"]]
        sha256 = hashlib.sha256(audio.read_bytes()).hexdigest()
        r = transcribe.transcribe(model, audio, ffmpeg, language=args.language)
        if hashlib.sha256(audio.read_bytes()).hexdigest() != sha256:
            raise AiVideoError(ErrorCode.AUDIO_ASSET_INVALID, "A normalized voice take changed during alignment.")
        ratio, lines = match_lines(g["lines"], char_times(r["segments"]), g.get("say"))
        res[g["id"]] = {"asr": r["text"], "ratio": ratio, "lines": lines, "audio_sha256": sha256}
        print(g["id"], ratio, [(round(x["start"] or -1, 2), round(x["end"] or -1, 2), x["matched"], x["chars"]) for x in lines], flush=True)
        weak = weak_lines(lines)
        bad += [f"{g['id']} 第{i + 1}句 {x['matched']}/{x['chars']} {x['text']}" for i, x in enumerate(lines) if x in weak]
    write_bytes(args.output, json.dumps(res, ensure_ascii=False, indent=1).encode())
    if bad:
        print("LOW LINES（可能漏读或读错，先听再说）:\n  " + "\n  ".join(bad), file=sys.stderr)
        return 2


if __name__ == "__main__":
    cli(main)
