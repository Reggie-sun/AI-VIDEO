#!/usr/bin/env python3
"""Review page of the IRIS EP01 s015-s030 v1 film (2026-11-23): pilot/s015-030/review-v1/index.html from
qa/s015-030-v1/qa.json (section2_qa.py), data/media-s2/*.json and section2.SHOTS. Numbers only; the look is the user's call.
Run from the repo root:  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section2_review.py [--film NAME --qa DIR]
(--film / --qa: a film in excerpt/renders and its QA folder under excerpt/, e.g. the picture + song preview while the
Agentcut layer export is pending.)
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from section2 import META, SF0, SHOTS, TAKES, INS16, frame_of  # noqa: E402

EXC = Path(__file__).resolve().parent
ARG = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
QA = EXC / ARG("--qa", "qa/s015-030-v1")
PAGE = EXC.parent / "pilot/s015-030/review-v1"
FILM = ARG("--film", "IRIS-EP01-agentcut-ev-s015-030-v1.mp4")
JOINED = "IRIS-EP01-agentcut-ev-000-134-v1.mp4"
E = html.escape


def table(head, rows, raw_cols=()):
    h = "".join(f"<th>{E(str(x))}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{x if i in raw_cols else E(str(x))}</td>" for i, x in enumerate(r)) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def grab(path: Path, frames: list[int], w: int) -> list[Image.Image]:
    h = w * 9 // 16
    sel = "+".join(f"eq(n\\,{f})" for f in frames)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"select='{sel}',scale={w}:{h}", "-vsync", "0", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return [Image.fromarray(np.frombuffer(raw[i * w * h * 3:(i + 1) * w * h * 3], np.uint8).reshape(h, w, 3)) for i in range(len(frames))]


def cut_strip(film: Path, fr: int, a: str, b: str, out: Path, w: int = 360) -> None:
    """frames fr-2, fr-1 | fr, fr+1 (the cut between the 2nd and 3rd), labelled with section frame and song time"""
    frames = [fr - 2, fr - 1, fr, fr + 1]
    h = w * 9 // 16
    S = Image.new("RGB", (w * 4 + 6, h + 20), (17, 17, 17))
    d = ImageDraw.Draw(S)
    for c, (f, im) in enumerate(zip(frames, grab(film, frames, w))):
        x = c * w + (6 if c >= 2 else 0)
        S.paste(im, (x, 20))
        d.text((x + 3, 4), f"{a if c < 2 else b}  f{f}  {(SF0 + f) / 24:.3f} s", fill=(242, 177, 52))
    d.rectangle([2 * w, 20, 2 * w + 5, h + 20], fill=(242, 177, 52))
    S.save(out, quality=86)


def take_label(src: str) -> tuple[str, str]:
    if src.startswith("still:"):
        return src.split(":", 1)[1], ""
    if src == "INS16":
        return "INS16-n-2 amber repair", INS16[1]
    return TAKES[src][0], TAKES[src][2][:8]


def main() -> int:
    qa = json.loads((QA / "qa.json").read_text())
    film = EXC / "renders" / FILM
    PAGE.mkdir(parents=True, exist_ok=True)
    rows, strips = [], []
    for k, s in enumerate(SHOTS):
        m = json.loads((META / f"{s['id']}.json").read_text())
        take, short = take_label(s["src"])
        sha = m.get("clip_sha256") or m.get("still_sha256")
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        if "clip" in m:
            src_span = f"片内 {m['first']['clip_t']:.2f}–{m['last']['clip_t']:.2f} s"
        else:
            src_span = f"静图 {m['still'].split('/')[-1]}"
        rows.append([f"{s['t0']:.4f}–{s['t1']:.4f}", s["id"], f"{f0}–{f1 - 1}", f"{take} {short}".strip(), f"<code>{sha[:16]}…</code>",
                     s["cls"], src_span, E(s["why"])])
        if k:
            out = PAGE / f"cut-{k:02d}-{s['id']}.jpg"
            cut_strip(film, f0, SHOTS[k - 1]["id"], s["id"], out)
            strips.append((s["id"], s["t0"], out.name))
    cuts = qa["cuts"]
    fl = qa["flash"]
    red = qa["red"]
    lips = qa["lips"]
    sp, so = qa["spec"], qa["sound"]
    red_rows = [[sid, v["frames"], v["over_12"], v["max_outside_px"], v["at"], v["max_red_px"]] for sid, v in red["per_shot"].items()]
    lip_rows = [[sid, v["take"], f"{v['song'][0]}–{v['song'][1]}", v["clip_in"], v["sync_check"].get("lag_s"),
                 json.dumps(v["visible_lip_synced_song_s"]), v["covered_share"],
                 f"{v['picture_offset_vs_placement']['0']}/{v['picture_offset_vs_placement']['frames']}"] for sid, v in lips.items()]
    cut_rows = [[c["cut"], c["t"], c["frame"], c["song_frame"], c["nearest_beat"], c["frame_dt_beat"], c["picture_change_peak_frame"],
                 "是" if c["pass"] else "否"] for c in cuts["cuts"]]
    extra = json.loads((QA / "extra.json").read_text()) if (QA / "extra.json").exists() else {}
    joined = EXC / "renders" / JOINED
    jn = (f'<h2>0–134.44 s 连起来看（开头 v3 + 本段，歌曲帧 1422 处接，同一条母带音轨）</h2>'
          f'<video src="../../../excerpt/renders/{JOINED}" controls preload="metadata"></video>'
          f'<p>文件 <code>excerpt/renders/{JOINED}</code>，SHA-256 <code>{extra.get("joined_sha256", "")}</code>。{E(extra.get("joined_note", ""))}</p>'
          if joined.exists() else "")
    open_items = [
        ("s024 SG09 m-2 的非指定推近（103.29–106.50 s）", "m-2 口型段对上（lag 0.5），但片中镜头有一段没要求的推近。请看是否接受；不接受的选项：改用 m-1 前段（后段口型落后 0.24 s）、或 s024 改静图 + 画外唱。"),
        ("s027 MO12 p-2 背景路人看镜头（116.12–119.78 s）", "你已定“背景路人看镜头算次要”；本页请看成片里是否仍然显眼（C 类轻拖影后）。"),
        ("s022 / s029 不对口型的处理与图形", "s022（95.04–99.63）她坐着拍卡推齐、不开口，歌词画外 + 下方字幕，左侧 UNDER OATH · ×1/×2/×3 · LEFT THE TEST 计数砸字；s022b 掌下卡片插镜 + LEFT THE TEST ×3 标签。s029（125.72–131.24）她静站不开口（片内 2.0–4.3 s 放慢到 0.74×），歌词以大字 Coverline 显示在左上，接伸手松开寻呼机（130.76）。请看这样不对口型是否成立。"),
        ("s018 静图（78.98–84.02 s）", "照作者 S0002 高处俯拍静图慢拉远（1.12→1.0，缓入缓出）。出租车：只把 p018-w1 左下车的框（0–495 × 390–845 px）换成 P018E 的深色轿车（无顶灯、无字、无尾灯），框外与原图逐像素相同（耳灯保留）。请看是否像静帧太久、车是否可接受。"),
    ]
    oi = "".join(f"<li><b>{E(a)}</b>：{E(b)}</li>" for a, b in open_items)
    dev = extra.get("deviations", [])
    dv = "".join(f"<li>{E(x)}</li>" for x in dev)
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>IRIS EP01 s015–s030 审片 v1</title>
<style>body{{background:#111;color:#ddd;font:14px/1.5 system-ui,sans-serif;margin:24px;max-width:1500px}}h1,h2{{color:#fff}}
table{{border-collapse:collapse;margin:8px 0 20px;font-size:12.5px}}td,th{{border:1px solid #333;padding:3px 7px;text-align:left;vertical-align:top}}
th{{background:#222}}video,img{{max-width:100%}}code{{color:#F2B134}}li{{margin:4px 0}}</style></head><body>
<h1>IRIS EP01 歌 59.2341–134.4435 s（s015–s030）审片版 v1（24 fps，1805 帧）</h1>
<p>按交接表（pilot/s015-030/HANDOFF-2026-11-23.md）剪的第一版，正常速度、带歌。本页只列做法与测量数字；好不好看由你判。</p>
{('<p style="color:#F2B134">' + E(extra["pending"]) + '</p>') if extra.get("pending") else ""}
<video src="../../../excerpt/renders/{FILM}" controls preload="metadata"></video>
<p>文件 <code>excerpt/renders/{FILM}</code>，SHA-256 <code>{qa['film_sha256']}</code>；纯画面 <code>{qa['picture']}</code>（SHA-256 <code>{qa['picture_sha256'][:16]}…</code>）。</p>
{jn}
<h2>需要你判的</h2><ol>{oi}</ol>
<h2>与交接表的偏差</h2><ul>{dv or "<li>无</li>"}</ul>
<h2>逐镜表（歌曲秒、镜、所用素材与用法）</h2>
{table(["歌曲秒", "镜", "段内帧", "素材", "SHA-256", "模糊类", "取用", "用法"], rows, raw_cols=(4, 7))}
<h2>质检摘要（excerpt/qa/s015-030-v1/qa.json）</h2>
<table><tbody>
<tr><td>规格</td><td>{sp['video']['width']}×{sp['video']['height']} {sp['video']['r_frame_rate']}，{sp['video']['nb_read_frames']} 帧，音轨 {len(sp['audio'])}；通过 {sp['pass']}</td></tr>
<tr><td>声音（对母带 59.25–134.4583 s）</td><td>偏移 {so['offset_samples']} 样本（{so['offset_ms']} ms），RMS 差 {so['rms_diff_db']} dB；通过 {so['pass']}</td></tr>
<tr><td>切点</td><td>{cuts['n']} 个，全部在拍点 ±0.03 s：{cuts['pass']}；画面变化峰值正落在切点帧 {cuts['change_peak_on_cut']}/{cuts['n']}</td></tr>
<tr><td>闪烁（WCAG 2.3.1，4×4 格）</td><td>任一格每秒最多 {fl['max_flashes_per_second_any_cell']} 次（f{fl['at']['frame']}）；通过 {fl['pass']}；切点外单帧跳变 {len(fl['single_frame_jumps'])} 处 {E(json.dumps(fl['single_frame_jumps'][:6]))}</td></tr>
<tr><td>红色（她 matte 外 &gt;12 px 的帧，每 2 帧查 1 帧）</td><td>查 {red['frames_checked']} 帧，有红 {red['frames_with_red']} 帧，超标 {len(red['bad_frames'])} 帧 {E(str(red['bad_frames'][:20]))}；通过 {red['pass']}</td></tr>
{"".join(f"<tr><td>{E(k)}</td><td>{E(str(v))}</td></tr>" for k, v in extra.get("checks", {}).items())}
</tbody></table>
<h3>口型段（剪辑用到的唱段）</h3>
{table(["镜", "素材", "歌曲秒", "片内入点", "sync lag s", "可见对口型歌曲秒", "覆盖比", "画面=预期帧"], lip_rows)}
<h3>切点</h3>
{table(["切到", "歌曲秒", "段内帧", "歌曲帧", "最近拍点", "帧−拍点 s", "画面变化峰值帧", "通过"], cut_rows)}
<h3>红色逐镜</h3>
{table(["镜", "查的帧", "超 12 px 帧", "她外最多 px", "在帧", "全帧红最多 px"], red_rows)}
<h2>每个切点前后（前 2 帧 | 后 2 帧，琥珀竖条为切点）</h2>
{"".join(f'<p><code>{E(sid)}</code> {t:.4f} s</p><img src="{n}" alt="{E(sid)}">' for sid, t, n in strips)}
</body></html>
"""
    (PAGE / "index.html").write_text(page, encoding="utf-8")
    print(PAGE / "index.html", len(strips), "cut strips")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
