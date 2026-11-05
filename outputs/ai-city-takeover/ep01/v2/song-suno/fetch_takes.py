#!/usr/bin/env python3
"""Fetch the user's new Suno takes of "Looked Outside" (read-only CLI) and build a loudness-matched audition page.

  python3 outputs/ai-city-takeover/ep01/v2/song-suno/fetch_takes.py [--since 2026-11-04]

The user clicks Create in the official Suno page (each generation needs a human verification); this script
only reads: `suno list`, `suno download --format wav`, `suno timed-lyrics`. Nothing is generated, deleted or
edited. Takes land in takes/<clip_id>.{wav,json,timed.json}; audition MP3s (-14 LUFS) in takes/audition/;
the page is index-takes.html, with the current full version (song-full v3) as the reference.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAKES = HERE / "takes"
REF = HERE.parent / "song-full/mix/IRIS-01-full-v3.wav"


def suno(*args: str) -> dict:
    out = subprocess.run(["suno", "--json", "--no-browser", *args], capture_output=True, text=True, timeout=600)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"suno {' '.join(args)}: unreadable output (exit {out.returncode}): {out.stdout[:300]} {out.stderr[:300]}")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loudnorm(src: Path, dst: Path) -> dict:
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", "loudnorm=I=-14:TP=-1.5:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", "48000", "-c:a", "libmp3lame", "-b:a", "256k", str(dst)], check=True)
    return {"input_lufs": float(m["input_i"]), "input_tp": float(m["input_tp"])}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-11-04", help="only clips created on or after this date (UTC)")
    ap.add_argument("--title", default="Looked Outside")
    a = ap.parse_args()
    (TAKES / "audition").mkdir(parents=True, exist_ok=True)
    listing = suno("list")
    data = listing.get("data")
    clips = data if isinstance(data, list) else (data or {}).get("clips") or []
    mine = [c for c in clips if (c.get("created_at") or "") >= a.since and a.title.lower() in (c.get("title") or "").lower()]
    mine.sort(key=lambda c: (c.get("created_at") or "", c.get("id")))
    rows = []
    for i, c in enumerate(mine, 1):
        cid = c["id"]
        meta = TAKES / f"{cid}.json"
        meta.write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n")
        if c.get("status") != "complete":
            rows.append({"n": i, "id": cid, "status": c.get("status")})
            continue
        wav = TAKES / f"{cid}.wav"
        if not wav.exists():
            got = suno("download", cid, "--format", "wav", "-o", str(TAKES))
            found = sorted(TAKES.glob(f"*{cid}*.wav")) or sorted(TAKES.glob("*.wav"), key=lambda p: p.stat().st_mtime)[-1:]
            if not found:
                raise SystemExit(f"{cid}: download reported {got.get('status')} but no WAV appeared")
            if found[0] != wav:
                found[0].rename(wav)
        timed = TAKES / f"{cid}.timed.json"
        if not timed.exists():
            timed.write_text(json.dumps(suno("timed-lyrics", cid), ensure_ascii=False, indent=1) + "\n")
        mp3 = TAKES / "audition" / f"T{i}.mp3"
        loud = loudnorm(wav, mp3)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                                   capture_output=True, text=True).stdout.strip())
        rows.append({"n": i, "id": cid, "status": "complete", "wav": wav.name, "wav_sha256": sha(wav), "duration": round(dur, 2),
                     "model": c.get("model_name") or c.get("major_model_version"), "created_at": c.get("created_at"), **loud})
    ref_mp3 = TAKES / "audition" / "current-v3.mp3"
    if REF.exists() and not ref_mp3.exists():
        loudnorm(REF, ref_mp3)
    (TAKES / "takes.json").write_text(json.dumps({"since": a.since, "title": a.title, "takes": rows}, ensure_ascii=False, indent=1) + "\n")
    cards = "".join(
        f'<div class="v"><b>T{r["n"]}</b> <span class="dim">{r.get("duration", "")} s · {html.escape(str(r.get("model", "")))}</span>'
        + (f'<audio controls preload="auto" src="takes/audition/T{r["n"]}.mp3"></audio>' if r.get("status") == "complete"
           else f'<div class="dim">还没生成完（{html.escape(str(r.get("status")))}）</div>') + "</div>" for r in rows)
    (HERE / "index-takes.html").write_text(f"""<!doctype html><html lang="zh-Hans"><meta charset="utf-8"><title>IRIS EP01 · Suno 试听</title>
<style>body{{background:#0a0c10;color:#dfe3ea;font:15px/1.7 system-ui,"Noto Sans CJK SC",sans-serif;padding:24px 36px;max-width:1200px}}
.vs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(520px,1fr));gap:14px}}.v{{background:#11151c;border:1px solid #1f2430;padding:12px 14px;border-radius:6px}}
audio{{width:100%;margin-top:6px}}.dim{{color:#8b93a3;font-size:13px}}</style>
<h1>IRIS EP01《Looked Outside》· Suno 试听</h1>
<div class="dim">全部统一到 −14 LUFS 再比较，编号按生成先后。先整首听，再比较：念白→副歌的衔接、第二遍副歌的发展、桥段→最后一遍副歌、结尾。</div>
<div class="vs">{cards}<div class="v"><b>对照：现在的完整版 v3</b> <span class="dim">ElevenLabs 伴奏＋Stella 念白＋v2 副歌</span><audio controls preload="auto" src="takes/audition/current-v3.mp3"></audio></div></div>
</html>
""")
    print(json.dumps({"takes": [{k: r.get(k) for k in ("n", "id", "status", "duration")} for r in rows]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
