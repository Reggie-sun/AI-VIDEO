#!/usr/bin/env python3
"""Review page of the IRIS EP01 s031-s048 v1 film (2026-11-26): pilot/s031-048/review-v1/index.html from
qa/s031-048-v1/{qa.json,joined.json,extra.json} (section3_qa.py), data/media-s3/*.json and section3.SHOTS. Numbers only;
the look is the user's call. Run from the repo root:  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/section3_review.py
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from section2_review import grab, table  # noqa: E402
from section3 import META, SF0, SHOTS, TAKES, frame_of  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

EXC = Path(__file__).resolve().parent
QA = EXC / "qa/s031-048-v1"
PAGE = EXC.parent / "pilot/s031-048/review-v1"
FILM = "IRIS-EP01-agentcut-ev-s031-048-v1.mp4"
JOINED = "IRIS-EP01-agentcut-ev-000-209-v1.mp4"
E = html.escape


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
    if src == "black":
        return "纯图形帧（黑底）", ""
    return TAKES[src][0], TAKES[src][2][:8]


OPEN_ITEMS = [
    ("丢掉的两个动作拍", "s037d（165.07–166.48）她放碗、s041c（183.76–185.59）她伸手抓布：r4 写法把动作交给剪辑，片段里本来就没有这两个动作，片中只剩念白/唱。请看是否要补（插镜或静图）还是接受。"),
    ("s039 拼切（170.11–173.78）", "第一句用 SG17B p-1（lag 0.875），在 171.955 拍上（两句之间）跳切到 SG17A p-2 第二句（lag 0.600）。同一机位同一姿势，跳切处人会小跳一下。请看是否可接受。"),
    ("s037c 插镜跳切（163.70–165.07）", "INS37 a-1 片内 1.25–1.74（按停止键）在 164.188 拍上跳到 3.10–3.98（拔插头、炉灯灭）。拔插头约落在 164.4，不是 Killed（164.82）。"),
    ("s046b 按秒表是后期做的（201.60–202.97）", "a-1 里那只手从没按下秒表。从 4K 片子 3.5× 裁出秒表（为了不带进她的脸，超过方案的 2×，画面偏软），在 “clocks”（202.24）上快推近 1.12× + 3 帧轻震代表按下。请看能否读成“按下”。"),
    ("s048 纸条插镜（208.41–209.34）", "SG20x r-1 用到 208.41（最近的拍；决定写 208.30 不在拍上），然后切 p047 纸条特写（2.5× 裁）盖住第三遍 crack，ALL HANDS! 在 208.93 砸上。r-1 第三遍 crack 闭嘴的开头约 1 帧仍在 r-1 上。"),
    ("眼睛变浅", "SG16x（s037b）、SG16y（s037d）、SG18x（s041a）片子里她的眼睛几秒后变浅，你已判次要；请在成片速度下再看一眼。"),
    ("s036 静图（155.93–159.59）", "SG15 不用（你定“改静图 + 图形”）：首帧 P036/x 静图缓推 1.0→1.08，中间 156.85–157.77 是 P0 纯图形帧（黑底、琥珀 P0，不用红），念白全在画外。请看这 3.7 s 静图是否太久。"),
]


def main() -> int:
    qa = json.loads((QA / "qa.json").read_text())
    jn = json.loads((QA / "joined.json").read_text())
    extra = json.loads((QA / "extra.json").read_text()) if (QA / "extra.json").exists() else {}
    film = EXC / "renders" / FILM
    PAGE.mkdir(parents=True, exist_ok=True)
    rows, strips = [], []
    for k, s in enumerate(SHOTS):
        m = json.loads((META / f"{s['id']}.json").read_text())
        take, short = take_label(s["src"])
        sha = m.get("clip_sha256") or m.get("still_sha256") or ""
        f0, f1 = frame_of(s["t0"]), frame_of(s["t1"])
        if "clip" in m:
            src_span = f"片内 {m['first']['clip_t']:.3f}–{m['last']['clip_t']:.3f} s" + (f"（裁 {m['crop'][2]}×）" if m.get("crop") else "")
        elif m.get("black"):
            src_span = "黑底"
        else:
            src_span = "静图 " + " + ".join(x["path"].split("S31-48/")[-1] for x in m["stills"])
        rows.append([f"{s['t0']:.4f}–{s['t1']:.4f}", s["id"], f"{f0}–{f1 - 1}", f"{take} {short}".strip(), f"<code>{sha[:16]}…</code>" if sha else "—",
                     s["cls"], src_span, E(s["why"])])
        if k:
            out = PAGE / f"cut-{k:02d}-{s['id']}.jpg"
            cut_strip(film, f0, SHOTS[k - 1]["id"], s["id"], out)
            strips.append((s["id"], s["t0"], out.name))
    cuts, fl, red, lips, sp, so = qa["cuts"], qa["flash"], qa["red"], qa["lips"], qa["spec"], qa["sound"]
    red_rows = [[sid, v["frames"], v["over_12"], v["max_outside_px"], v["at"], v["max_red_px"], v["max_exception_px"]] for sid, v in red["per_shot"].items()]
    lip_rows = [[sid, v["take"], f"{v['song'][0]}–{v['song'][1]}", v["clip_in"], json.dumps(v["gate_spans_in_shot_song_s"]), v["gate_copy"],
                 v["sync_check"].get("lag_s"), json.dumps(v["visible_lip_synced_song_s"]),
                 f"{v['picture_offset_vs_placement']['0']}/{v['picture_offset_vs_placement']['frames']}"] for sid, v in lips.items()]
    cut_rows = [[c["cut"], c["t"], c["frame"], c["song_frame"], c["nearest_beat"], c["frame_dt_beat"], c["picture_change_peak_frame"],
                 "是" if c["pass"] else "否"] for c in cuts["cuts"]]
    snd_rows = [[k, v["master_window_s"][0], round(v["master_window_s"][1], 4), v["offset_samples"], v["rms_diff_db"], v["pass"]] for k, v in jn["sound_windows"].items()]
    oi = "".join(f"<li><b>{E(a)}</b>：{E(b)}</li>" for a, b in OPEN_ITEMS)
    dv = "".join(f"<li>{E(x)}</li>" for x in extra.get("deviations", []))
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>IRIS EP01 s031–s048 审片 v1</title>
<style>body{{background:#111;color:#ddd;font:14px/1.5 system-ui,sans-serif;margin:24px;max-width:1500px}}h1,h2{{color:#fff}}
table{{border-collapse:collapse;margin:8px 0 20px;font-size:12.5px}}td,th{{border:1px solid #333;padding:3px 7px;text-align:left;vertical-align:top}}
th{{background:#222}}video,img{{max-width:100%}}code{{color:#F2B134}}li{{margin:4px 0}}</style></head><body>
<h1>IRIS EP01 歌 134.4435–209.3395 s（s031–s048）审片版 v1（24 fps，1797 帧）</h1>
<p>按交接表（pilot/s031-048/HANDOFF-2026-11-24.md「剪辑用法（2026-11-26）」）剪的第一版，正常速度、带歌。本页只列做法与测量数字；好不好看由你判。</p>
<h2>本段</h2>
<video src="../../../excerpt/renders/{FILM}" controls preload="metadata"></video>
<p>文件 <code>excerpt/renders/{FILM}</code>，SHA-256 <code>{qa['film_sha256']}</code>；纯画面 <code>{qa['picture']}</code>（SHA-256 <code>{qa['picture_sha256'][:16]}…</code>）。</p>
<h2>0–209.34 s 连起来看（0–134 v1 原片不动 + 本段，歌曲帧 3227 处接，一整条母带音轨）</h2>
<video src="../../../excerpt/renders/{JOINED}" controls preload="metadata"></video>
<p>文件 <code>excerpt/renders/{JOINED}</code>，SHA-256 <code>{jn['film_sha256']}</code>，5024 帧。{E(jn['frame_exact'])}；{E(jn['method'])}。</p>
<h2>需要你判的</h2><ol>{oi}</ol>
<h2>与交接表的偏差</h2><ul>{dv or "<li>无</li>"}</ul>
<h2>逐镜表（歌曲秒、镜、所用素材与用法）</h2>
{table(["歌曲秒", "镜", "段内帧", "素材", "SHA-256", "模糊类", "取用", "用法"], rows, raw_cols=(4, 7))}
<h2>质检摘要（excerpt/qa/s031-048-v1/qa.json、joined.json）</h2>
<table><tbody>
<tr><td>规格</td><td>{sp['video']['width']}×{sp['video']['height']} {sp['video']['r_frame_rate']}，{sp['video']['nb_read_frames']} 帧，音轨 {len(sp['audio'])}；通过 {sp['pass']}</td></tr>
<tr><td>声音（对母带 {so['master_window_s'][0]:.4f}–{so['master_window_s'][1]:.4f} s）</td><td>偏移 {so['offset_samples']} 样本（{so['offset_ms']} ms），RMS 差 {so['rms_diff_db']} dB；通过 {so['pass']}</td></tr>
<tr><td>切点</td><td>{cuts['n']} 个（含 s037c、s039 两处跳切），全部在拍点 ±0.03 s：{cuts['pass']}；画面变化峰值正落在切点帧 {cuts['change_peak_on_cut']}/{cuts['n']}</td></tr>
<tr><td>闪烁（WCAG 2.3.1，4×4 格）</td><td>任一格每秒最多 {fl['max_flashes_per_second_any_cell']} 次（f{fl['at']['frame']}）；通过 {fl['pass']}；切点外单帧跳变 {len(fl['single_frame_jumps'])} 处 {E(json.dumps(fl['single_frame_jumps'][:6]))}</td></tr>
<tr><td>红色（她 matte 外 &gt;12 px 的帧，每 2 帧查 1 帧；s039 门缝框内为例外单列）</td><td>查 {red['frames_checked']} 帧，有红 {red['frames_with_red']} 帧，超标 {len(red['bad_frames'])} 帧 {E(str(red['bad_frames'][:20]))}；例外框内有红 {red['exception']['frames_with_exception_red']} 帧；通过 {red['pass']}</td></tr>
{"".join(f"<tr><td>{E(k)}</td><td>{E(str(v))}</td></tr>" for k, v in extra.get("checks", {}).items())}
</tbody></table>
<h3>连片的声画（同一条母带，接点前后各窗口对母带）</h3>
{table(["窗口", "母带起 s", "母带止 s", "偏移样本", "RMS 差 dB", "通过"], snd_rows)}
<p>连片视频帧时间与 k/24 最大偏差 {jn['video_pts_s']['max_dev_from_k_over_24_s']:.1e} s；第 3227 帧在 {jn['video_pts_s']['frame_3227']} s。</p>
<h3>口型段（剪辑用到的唱/念段）</h3>
<p>Gate 同步段 = 生成时 Gate 测的严格同步段落在本镜里的部分；sync_check = 片子自带声轨按本镜入点切出、对人声窗口重测（copy=false 的片子自带声是模型自己配的，只作参考）；画面=预期帧 是 160×90 灰度相关找片子里的哪一帧（静止画面的 ±1–2 帧是噪声，正负对称，没有系统偏移）。</p>
{table(["镜", "素材", "歌曲秒", "片内入点", "Gate 同步段（歌曲秒）", "Gate copy", "sync lag s", "重测同步段", "画面=预期帧"], lip_rows)}
<h3>切点</h3>
{table(["切到", "歌曲秒", "段内帧", "歌曲帧", "最近拍点", "帧−拍点 s", "画面变化峰值帧", "通过"], cut_rows)}
<h3>红色逐镜</h3>
{table(["镜", "查的帧", "超 12 px 帧", "她外最多 px", "在帧", "全帧红最多 px", "例外框内最多 px"], red_rows)}
<h2>每个切点前后（前 2 帧 | 后 2 帧，琥珀竖条为切点）</h2>
{"".join(f'<p><code>{E(sid)}</code> {t:.4f} s</p><img src="{n}" alt="{E(sid)}">' for sid, t, n in strips)}
</body></html>
"""
    (PAGE / "index.html").write_text(page, encoding="utf-8")
    print(PAGE / "index.html", len(strips), "cut strips")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
