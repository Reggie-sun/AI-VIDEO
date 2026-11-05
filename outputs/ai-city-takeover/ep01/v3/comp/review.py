#!/usr/bin/env python3
"""Write the review page of the IRIS EP01 v3 full-length animatic (run from the repository root, after the render):

  uv run python outputs/ai-city-takeover/ep01/v3/comp/review.py [--video <abs path of the review proxy>]
      [--out <abs path>/review/animatic-a2.html]

Spec (../animatic-spec.md 交付 3, a2 交付与检查): a player and one row per unit (unit, time, CTC lyric, voice class, still
thumbnails, components with their on-screen text, graphic_note); a click on a row jumps the player to the unit. The page
may carry Chinese, the video may not. Reads ../shots-map.json, data/units.json (frame-quantised cuts),
data/music-map.json (sections) and review-notes.json (what this pass did and its known problems); writes the page
(default ../review/animatic-a1.html), the still thumbnails and one rendered frame per unit, the middle of its frames
(from the MP4). The version label comes from the page name (animatic-a2.html -> a2, animatic-a2.1.html -> a2.1); a1
keeps ../review/thumbs/, every later version gets its own ../review/thumbs-<label>/, so an earlier page keeps its own
frames.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
from pathlib import Path

from PIL import Image

COMP = Path(__file__).resolve().parent
V3 = COMP.parent
SERIES = V3.parent.parent                               # outputs/ai-city-takeover: shots-map paths are relative to it
REVIEW = V3 / "review"
FPS = 30
VOICE = {"lead": "领唱", "vo": "画外念白", "inside": "刻意闭嘴", "chant": "合唱"}
VIEW = {"system": "系统（监控 OSD）", "iris": "IRIS（无 HUD）", "graphic": "纯图形"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(video: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
                          "stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_packets,sample_rate,channels"
                          ":format=duration", "-of", "json", str(video)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def frames(video: Path, units: list[dict], out: Path) -> None:
    """One JPEG per unit: the rendered frame in the middle of the unit's frames."""
    out.mkdir(parents=True, exist_ok=True)
    picks = [(u["id"], (u["f0"] + u["f1"]) // 2) for u in units]
    expr = "+".join(f"eq(n\\,{f})" for _, f in picks)
    tmp = out / "tmp-%03d.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"select='{expr}',scale=384:-2", "-vsync", "0",
                    "-q:v", "4", str(tmp)], check=True)
    got = sorted(out.glob("tmp-*.jpg"))
    if len(got) != len(picks):
        raise SystemExit(f"grabbed {len(got)} frames for {len(picks)} units")
    for (uid, _), p in zip(picks, got):
        p.replace(out / f"{uid}.jpg")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path, default=V3 / "renders/IRIS-EP01-v3-animatic-a1.mp4")
    ap.add_argument("--out", type=Path, default=REVIEW / "animatic-a1.html")
    args = ap.parse_args()
    m = re.fullmatch(r"animatic-([\w.]+)", args.out.stem)             # animatic-a2.1.html -> a2.1
    label = m.group(1) if m else "a1"
    thumbs = "thumbs" if label == "a1" else f"thumbs-{label}"
    shots = json.loads((V3 / "shots-map.json").read_text(encoding="utf-8"))
    built = json.loads((COMP / "data/units.json").read_text(encoding="utf-8"))
    if built["shots_map_sha256"] != sha(V3 / "shots-map.json"):
        raise SystemExit("data/units.json was built from another shots-map.json: run build.py first")
    units = built["units"]
    by_id = {s["unit"]: s for s in shots["shots"]}
    music = json.loads((COMP / "data/music-map.json").read_text(encoding="utf-8"))
    sections = [{"name": music["pre"]["section"], "t0": music["pre"]["t0"]}] + [
        {"name": s["section"], "t0": s["t0"]} for s in music["sections"]]
    notes = json.loads((COMP / "review-notes.json").read_text(encoding="utf-8"))

    # still thumbnails (320 px JPEG) of every plate the map names
    tdir = args.out.parent / thumbs / "plates"
    tdir.mkdir(parents=True, exist_ok=True)
    for s in shots["shots"]:
        for p in s["plates"]:
            dst = tdir / f"{Path(p['plate']).stem}.jpg"
            if not dst.exists():
                with Image.open(SERIES / p["plate"]) as im:
                    im.convert("RGB").resize((320, round(320 * im.height / im.width)), Image.LANCZOS).save(dst, quality=84)

    video_rel = os.path.relpath(args.video, args.out.parent)
    meta, digest = None, None
    if args.video.exists():
        meta, digest = probe(args.video), sha(args.video)
        frames(args.video, units, args.out.parent / thumbs / "frames")
    v = next((s for s in (meta or {}).get("streams", []) if s["codec_type"] == "video"), None)
    a = next((s for s in (meta or {}).get("streams", []) if s["codec_type"] == "audio"), None)

    def esc(s: str) -> str:
        return html.escape(s or "", quote=True)

    rows, si = [], -1
    for u in units:
        s = by_id[u["id"]]
        while si + 1 < len(sections) and sections[si + 1]["t0"] <= u["t0"] + 1e-6:
            si += 1
            sec = sections[si]
            rows.append(f'<tr class="sec"><td colspan="9">{esc(sec["name"])} · {sec["t0"]:.2f} s</td></tr>')
        t0, t1 = u["f0"] / FPS, u["f1"] / FPS
        voice = " + ".join(VOICE.get(x, x) for x in (s.get("voice") or "").split("+") if x) or "—"
        plates = "".join(
            f'<figure><img loading="lazy" src="{thumbs}/plates/{esc(Path(p["plate"]).stem)}.jpg" alt="">'
            f'<figcaption>{esc(Path(p["plate"]).stem)}{f" · {p['from']:.2f} 起" if p["from"] else ""}</figcaption></figure>'
            for p in s["plates"]) or '<span class="dim">—（纯图形）</span>'
        comps = "<br>".join(f"<code>{esc(g)}</code>" for g in (s["graphic"] or "").split("+") if g) or '<span class="dim">—</span>'
        if s.get("graphic_text"):
            comps += '<div class="ost">' + "<br>".join(esc(x) for x in s["graphic_text"].split("\n")) + "</div>"
        extra = []
        if "cue_s" in s:
            extra.append(f"cue {s['cue_s']:.3f} s")
        if "target" in s:
            extra.append(f"target {s['target']}")
        if "targets" in s:
            extra.append(f"targets {s['targets']}")
        frame = f'<img loading="lazy" src="{thumbs}/frames/{u["id"]}.jpg" alt="">' if digest else ""
        rows.append(
            f'<tr data-t="{t0:.4f}" data-t1="{t1:.4f}" id="{u["id"]}"><td class="id">{u["id"]}</td>'
            f'<td class="tm">{t0:.2f}–{t1:.2f}<br><span class="dim">{t1 - t0:.2f} s · f{u["f0"]}</span></td>'
            f'<td>{esc(s.get("lyric"))}</td><td>{esc(voice)}</td>'
            f'<td>{esc(VIEW.get(s["viewpoint"], s["viewpoint"]))}<br><span class="dim">{esc(s["scale"])} · {esc(s["camera_move"])}</span></td>'
            f'<td class="pl">{plates}</td><td class="cp">{comps}'
            f'{"<div class=dim>" + esc(" · ".join(extra)) + "</div>" if extra else ""}</td>'
            f'<td>{esc(s.get("graphic_note"))}<div class="dim">{esc(s.get("objective"))}</div></td><td class="fr">{frame}</td></tr>')

    if digest:
        info = (f'{v["width"]}×{v["height"]} · {v["r_frame_rate"].split("/")[0]} fps · {int(v["nb_read_packets"])} 帧 · '
                f'{float(meta["format"]["duration"]):.3f} s · 音轨 {a["codec_name"]} {a["sample_rate"]} Hz {a["channels"]} ch'
                f'（T4 母带）· <code>{esc(str(args.video.relative_to(V3)))}</code> · SHA-256 <code>{digest}</code>')
    else:
        info = "尚未渲染"
    note_html = "".join(f"<h3>{esc(k)}</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in vs) + "</ul>" for k, vs in notes.items())
    page = f"""<!doctype html>
<html lang="zh-Hans"><meta charset="utf-8">
<title>IRIS EP01 v3 · 全长动画分镜 {label}（待你审看）</title>
<style>
 :root {{ --bg:#0a0c11; --panel:#11141b; --line:#1f2430; --txt:#dfe3ea; --dim:#8b93a3; --red:#E3342F; }}
 body {{ background:var(--bg); color:var(--txt); font:14px/1.55 system-ui,"Noto Sans CJK SC",sans-serif; margin:0; }}
 header {{ position:sticky; top:0; z-index:2; background:var(--bg); padding:14px 28px 10px; border-bottom:1px solid var(--line); }}
 h1 {{ font-size:20px; font-weight:600; margin:0 0 4px; }} h3 {{ font-size:15px; margin:14px 0 4px; }}
 .dim {{ color:var(--dim); font-size:12px; }} code {{ font-size:12px; word-break:break-all; }}
 .wrap {{ display:flex; gap:18px; align-items:flex-start; }}
 video {{ background:#000; width:min(960px,62vw); display:block; }}
 #now {{ font-size:15px; min-width:280px; }} #now b {{ font-size:22px; }} #now .ost {{ margin-top:6px; }}
 main {{ padding:8px 28px 60px; }}
 table {{ border-collapse:collapse; width:100%; }} td, th {{ border-bottom:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }}
 th {{ color:var(--dim); font-weight:500; position:sticky; top:var(--head,0); background:var(--bg); }}
 tr[data-t] {{ cursor:pointer; }} tr[data-t]:hover {{ background:#141925; }} tr.on {{ background:#1a2131; outline:1px solid #3a4560; }}
 tr.sec td {{ color:#c9d2e3; background:var(--panel); font-weight:600; padding:4px 8px; }}
 td.id {{ font-weight:600; white-space:nowrap; }} td.tm {{ white-space:nowrap; }}
 td.pl figure {{ margin:0 0 4px; }} td.pl img {{ width:150px; display:block; border:1px solid var(--line); }}
 figcaption {{ font-size:11px; color:var(--dim); }} td.fr img {{ width:192px; border:1px solid var(--line); }}
 td.cp {{ max-width:260px; }} .ost {{ margin-top:4px; padding:3px 6px; background:var(--panel); border-left:3px solid var(--red); font:12px/1.4 ui-monospace,monospace; }}
 .box {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:6px 16px 10px; margin:12px 0 18px; }}
 kbd {{ border:1px solid var(--line); border-radius:3px; padding:0 4px; font-size:12px; }}
</style>
<header>
<h1>IRIS EP01《Looked Outside》v3 · 全长动画分镜 {label}（待你审看，不是成片）</h1>
<div class="dim">{info}</div>
<div class="wrap" style="margin-top:8px">
<video id="v" controls preload="auto" src="{esc(video_rel)}"></video>
<div id="now"><span class="dim">点表格任一行跳到该单元；<kbd>[</kbd> <kbd>]</kbd> 上一个 / 下一个单元，<kbd>空格</kbd> 播放 / 暂停。</span></div>
</div>
</header>
<main>
<div class="box">{note_html}</div>
<table>
<thead><tr><th>单元</th><th>时间（s）</th><th>歌词（CTC）</th><th>声音</th><th>视点 · 景别 · 运动</th><th>静图</th><th>组件 · 屏上文字</th><th>说明（graphic_note · 目的）</th><th>{label} 画面（单元中点）</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
</main>
<script>
const v = document.getElementById('v'), now = document.getElementById('now');
const rows = [...document.querySelectorAll('tr[data-t]')];
const unitAt = t => {{ let r = rows[0]; for (const x of rows) if (+x.dataset.t <= t + 1e-4) r = x; return r; }};
let cur = null;
function mark() {{
  const r = unitAt(v.currentTime);
  if (r === cur) return;
  if (cur) cur.classList.remove('on');
  cur = r; r.classList.add('on');
  const c = r.children;
  now.innerHTML = `<b>${{c[0].textContent}}</b> <span class="dim">${{c[1].firstChild.textContent}} s</span><br>${{c[2].textContent || ''}}<br><span class="dim">${{c[3].textContent}} · ${{c[4].firstChild.textContent}}</span>` + (r.querySelector('.ost') ? `<div class="ost">${{r.querySelector('.ost').innerHTML}}</div>` : '');
}}
const seek = r => {{ v.currentTime = +r.dataset.t + 0.001; mark(); }};
rows.forEach(r => r.addEventListener('click', () => {{ seek(r); v.play(); }}));
v.addEventListener('timeupdate', mark); v.addEventListener('seeked', mark);
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'INPUT') return;
  const i = rows.indexOf(unitAt(v.currentTime));
  if (e.key === ']') {{ seek(rows[Math.min(rows.length - 1, i + 1)]); e.preventDefault(); }}
  if (e.key === '[') {{ seek(rows[Math.max(0, v.currentTime - +rows[i].dataset.t > 0.5 ? i : i - 1)]); e.preventDefault(); }}
  if (e.key === ' ' && e.target === document.body) {{ v.paused ? v.play() : v.pause(); e.preventDefault(); }}
}});
document.documentElement.style.setProperty('--head', document.querySelector('header').offsetHeight + 'px');
mark();
</script>
</html>
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(json.dumps({"page": str(args.out), "units": len(units), "video_sha256": digest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
