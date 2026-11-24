#!/usr/bin/env python3
"""Review page of the IRIS EP01 opening v2 film: pilot/opening/review-v2/index.html from qa/opening-v2/qa.json
(qa_opening.py) and qa_v2.json (qa_opening_v2.py). Numbers only; no judgement of the look. Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/review_opening_v2.py [--v2c | --v2d]

--v2c (2026-11-21, s014 reshot as MO07 r6-2): the page from qa/opening-v2c/ for IRIS-EP01-agentcut-ev-v2c-000-059.mp4,
with the v2 -> v2c QA comparison (qa/opening-v2/) and the changes mapped to the complaints on review-final.
--v2d: the same page for IRIS-EP01-agentcut-ev-v2d-000-059.mp4 (qa/opening-v2d/, v2 -> v2c -> v2d), linking v2c.
--v3 (2026-11-21, the v2d review: s004's hold, the s014 pager press, one blur level everywhere): pilot/opening/review-v3/
from qa/opening-v3/ (qa.json, qa_v2.json, blur/blur_v3.json and its pair_*.jpg) against qa/opening-v2d/: the film, the
three complaints and their fixes, the blur class table with EV's class ranges and the EV | IRIS pairs, one frame per
shot, before / after strips of 13-16.9 s and 55-57 s (v2d film | v3 film), the QA comparison.
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

EXC = Path(__file__).resolve().parent
V2D = "--v2d" in sys.argv                                # v2c + the two layout fixes (agentcut_v2_layers.py --v2d)
V2C = "--v2c" in sys.argv or V2D
QA = EXC / ("qa/opening-v2d" if V2D else "qa/opening-v2c" if V2C else "qa/opening-v2")
PAGE = EXC.parent / "pilot/opening/review-v2"
FILM = "IRIS-EP01-agentcut-ev-v2d-000-059.mp4" if V2D else "IRIS-EP01-agentcut-ev-v2c-000-059.mp4" if V2C else "IRIS-EP01-agentcut-ev-v2-000-059.mp4"
PREV = "IRIS-EP01-agentcut-ev-v2c-000-059.mp4" if V2D else "IRIS-EP01-agentcut-ev-v2-000-059.mp4" if V2C else "IRIS-EP01-agentcut-ev-000-059.mp4"
E = html.escape


def table(head, rows):
    h = "".join(f"<th>{E(str(x))}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{E(str(x))}</td>" for x in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def strip(films, frames, out, w=320):
    """One row per film, one column per frame (song frames), w px wide each, labelled."""
    import subprocess
    from PIL import Image, ImageDraw
    import numpy as np
    h = w * 9 // 16
    S = Image.new("RGB", (w * len(frames) + 90, (h + 18) * len(films)), (17, 17, 17))
    d = ImageDraw.Draw(S)
    for r, (name, path) in enumerate(films):
        sel = "+".join(f"eq(n\\,{f})" for f in frames)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"select='{sel}',scale={w}:{h}", "-vsync", "0", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        for c, f in enumerate(frames):
            im = Image.fromarray(np.frombuffer(raw[c * w * h * 3:(c + 1) * w * h * 3], np.uint8).reshape(h, w, 3))
            S.paste(im, (90 + c * w, r * (h + 18) + 18))
            d.text((92 + c * w, r * (h + 18) + 3), f"f{f}  {f / 24:.2f} s", fill=(242, 177, 52))
        d.text((4, r * (h + 18) + 18 + h // 2), name, fill=(255, 255, 255))
    S.save(out, quality=86)


def main_v3() -> int:
    qa3, qa2 = EXC / "qa/opening-v3", EXC / "qa/opening-v2d"
    page = EXC.parent / "pilot/opening/review-v3"
    film, prev = "IRIS-EP01-agentcut-ev-v3-000-059.mp4", "IRIS-EP01-agentcut-ev-v2d-000-059.mp4"
    q, v = json.loads((qa3 / "qa.json").read_text()), json.loads((qa3 / "qa_v2.json").read_text())
    q2, v2 = json.loads((qa2 / "qa.json").read_text()), json.loads((qa2 / "qa_v2.json").read_text())
    B = json.loads((qa3 / "blur/blur_v3.json").read_text())
    B0 = json.loads((qa3 / "blur-before-v2c/blur_v3.json").read_text())["shots"]        # the v2c picture, same measure
    page.mkdir(parents=True, exist_ok=True)
    for f in ("contact.jpg", "ev_compare.jpg"):
        shutil.copyfile(qa3 / f, page / f)
    pairs = sorted(p.name for p in (qa3 / "blur").glob("pair_*.jpg"))
    for f in pairs:
        shutil.copyfile(qa3 / "blur" / f, page / f)
    R = EXC / "renders"
    films = [("v2d", R / prev), ("v3", R / film)]
    strip(films, [312, 330, 344, 356, 368, 380, 392, 404], page / "strip-13-17s.jpg")
    strip(films, [1322, 1330, 1338, 1346, 1354, 1362, 1366, 1372], page / "strip-55-57s.jpg")
    # the complaints
    sh = B["shots"]
    cls_line = "；".join(f"{k} {x['target']}→{x['class']}" for k, x in sh.items() if "@" not in k)
    complaints = [
        ("14s这里静止很奇怪", "s004（12.78–16.90 s）去掉后半段定格：SG01-o-2 视频从头播到切点（口型段的画面不变），14.33 s 之后不再停住。见下方 13–17 s 前后对比条。"),
        ("56s那里那个动作我没看懂", "s014 在 56.9237 拍切成同一条 r6-2 的两段，不新生成：55.08–56.92 用 4K 原片数字推近到腰部中景（1.96→2.0×，即 4K 1:1，不放大），"
         "能看清她低头、右手按身前腰链上的寻呼机（按压在素材 0.5–1.8 s，全在推近段内）；推近段加一个跟着寻呼机走的标注 PAGER · 10:02 · BUZZING，在切点退场；"
         "56.92 起切回全景，看她转身、甩一次袖、往画右后方走远。ALL HANDS! ALL NIGHT! 照 v2 的规则在新切点拆成两段（字不消失，第二段的字已在场）。"),
        ("还是都是一个模糊程度，太单调", "按 EV 实测的模糊用法逐镜分类（A 全清为底 / B 浅景深 / C 运动拖影 / D 整帧柔暗 / E 整帧失焦），并用 blur_study 的同一套测量核对："
         + cls_line + "。"),
    ]
    rng = B["ev_class_ranges"]
    rr = lambda x: "-" if not x else f"{x[0]}–{x[2]}（中位 {x[1]}）"
    ev_rows = [[c, r["n"], " ".join(r["shots"]), rr(r["main"]), rr(r["bg"]), rr(r["bg_over_main"]), rr(r["p2"]), rr(r["p98"]), rr(r["move"])] for c, r in rng.items()]
    f1 = lambda x: "-" if x is None else ("flat" if x >= 90 else f"{x:.1f}")
    bl_rows = [[k, f"{x['frames'][0]}–{x['frames'][1]}", x["cat"], x["target"], f"{B0[k]['class']}（{f1(B0[k]['main'])} / {f1(B0[k]['se_bg'])}）" if k in B0 else "-",
                x["class"], f1(x["main"]), f1(x["se_bg"]),
                "-" if x["bg_over_main"] is None else f"{x['bg_over_main']:.2f}", f1(x["p2"]), f1(x["p98"]), f1(x["move_subj"]),
                "PASS" if x["pass"] else "FAIL", x["rule"]] for k, x in sh.items()]
    red = lambda r, ks: f"{sum(r[k]['over_12'] for k in ks if k in r)}/{sum(r[k]['frames'] for k in ks if k in r)}（最大 {max((r[k]['max_outside_px'] for k in ks if k in r), default=0)} px）"
    n_cut = lambda x: f"{len(x['cuts']['cuts'])} 个，全在拍点 {x['cuts']['pass']}，画面变化峰值落在切点 {x['cuts']['change_peak_on_cut']}"
    lip = lambda x, k: f"可见同步帧 {x['lips'][k]['visible_lip_synced_frames']}，取帧偏移 0 的帧 {x['lips'][k]['picture_offset_vs_placement']['0']}/{x['lips'][k]['picture_offset_vs_placement']['frames']}"
    cols = [("v2d", q2, v2), ("v3", q, v)]
    row = lambda name, fn: [name, *(fn(a, b) for _, a, b in cols)]
    cmp_rows = [row("规格", lambda x, y: f"{x['spec']['frames']} 帧 {x['spec']['fps']} {x['spec']['width']}×{x['spec']['height']} 通过 {x['spec']['pass']}"),
                row("声音偏移 / RMS 差", lambda x, y: f"{x['sound']['offset_samples']} 样本 / {x['sound']['rms_diff_db']} dB，通过 {x['sound']['pass']}"),
                row("切点", lambda x, y: n_cut(x)),
                row("s014 切点（帧）", lambda x, y: "、".join(f"{c['cut']} {c['frame']}（拍差 {c['frame_dt_beat']:+.4f} s）" for c in x["cuts"]["cuts"] if c["cut"].startswith("s014"))),
                row("全片红 >12 px 帧（每 2 帧查）", lambda x, y: x["red"]["frames_with_red_outside_her_over_12px"]),
                row("s014 红（她 matte 外 >12 px）", lambda x, y: red(x["red"]["per_shot"], ["s014a", "s014p"])),
                row("matte 内大块红帧", lambda x, y: len(x["red"]["frames_with_large_red_inside_matte"])),
                row("闪烁（任一格最多次/秒，超 3 次窗口起点）", lambda x, y: f"{x['flash']['max_flashes_per_second_any_cell']}，{x['flash']['windows_over_3_per_second_start_frames']}"),
                row("单帧跳变", lambda x, y: len(x["flash"]["single_frame_jumps"])),
                row("s004 口型", lambda x, y: lip(x, "s004")),
                row("s008 口型", lambda x, y: lip(x, "s008")),
                row("非视频帧占比", lambda x, y: f"{y['motion']['share']['non_video']:.1%}"),
                row("跨切图形", lambda x, y: len(y["graphics"]["clips_over_cut"]))]
    cuts = table(["切点", "歌曲秒", "帧", "最近拍点", "帧−拍点 s", "画面变化峰值帧"],
                 [[c["cut"], c["t"], c["frame"], c["nearest_beat"], c["frame_dt_beat"], c["film_change_peak_frame"]] for c in q["cuts"]["cuts"]])
    shares = B["counts"]
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>IRIS EP01 0–59.23 s 审片 v3</title>
<style>body{{background:#111;color:#ddd;font:14px/1.5 system-ui,sans-serif;margin:24px;max-width:1500px}}h1,h2{{color:#fff}}
table{{border-collapse:collapse;margin:8px 0 20px;font-size:12.5px}}td,th{{border:1px solid #333;padding:3px 7px;text-align:left;vertical-align:top}}
th{{background:#222}}video,img{{max-width:100%}}code{{color:#F2B134}}</style></head><body>
<h1>IRIS EP01 歌 0–59.2341 s 审片版 v3（24 fps，1422 帧）</h1>
<p>按你对 v2d 的三条意见改。本页列改动和测量数字；好不好看由你判。</p>
<video src="../../../excerpt/renders/{film}" controls preload="metadata"></video>
<p>文件 <code>excerpt/renders/{film}</code>，SHA-256 <code>{q['film_sha256']}</code>；上一版 <a href="../../../excerpt/renders/{prev}" style="color:#F2B134">{prev}</a>。</p>
<h2>三条意见 → 这一版怎么改</h2>{table(['你的意见', '这一版怎么改'], complaints)}
<h2>13–17 s 前后对比（上 v2d，下 v3）</h2><p>v2d 从 f344 起定格；v3 视频播到 f405。</p><img src="strip-13-17s.jpg" alt="13-17 s">
<h2>55–57 s 前后对比（上 v2d，下 v3）</h2><p>v3 1322–1365 推近看按寻呼机，1366 切回全景。</p><img src="strip-55-57s.jpg" alt="55-57 s">
<h2>逐镜模糊分类（blur_study 同一测量，纯画面 <code>IRIS-EP01-v3-picture-000-1422.mp4</code>）</h2>
<p>σ_e 单位为 1920 宽下的像素（480 宽测，最强 10% 边缘）；main 在脸/中景取脸框，其余取主体框；分类规则 <code>blur_study/work/classify.py</code>。每镜取中帧 ±6 三帧的中位数；“@peak”行为拖影最强的帧。实测类计数：{E(json.dumps(shares))}。</p>
{table(['镜', '帧', '类型', '目标', 'v2c 实测（main / 背景）', 'v3 实测', 'main σ_e', '背景 σ_e', '背景/main', 'p2', 'p98', '运动 px/帧', '结果', '规则'], bl_rows)}
<p>v2c（上一版画面）同一测量：{E(json.dumps({c: sum(1 for k, x in B0.items() if '@' not in k and x['class'] == c) for c in ('A', 'B', 'C', 'D', 'E')}))}；v3：{E(json.dumps({c: shares.get(c, 0) for c in ('A', 'B', 'C', 'D', 'E')}))}。</p>
<h3>没达到 EV 分类阈值的地方（如实）</h3><ul>
<li>C 类（s006 闪光后的拖影、s014 全景转身/走远）：画面上拖影看得见（见并排图），但按 EV 的规则（主体最强 10% 边缘的 σ_e ≥ 12）测不到：拖影峰值帧主体 σ_e 从干净素材的约 6 升到 7–9，因为沿运动方向的边缘和不动的部分（s006 伸向镜头的手、s014 落地的靴子）仍然清楚；s006 拖影已经强到脸认不出，再加只会更像故障，所以停在这里。这两镜按规则实测为 A（拖影帧之间本来就是清楚的）。</li>
<li>s012c（D）实测脸 σ_e {f1(sh['s012c']['main'])}，比 EV 闭眼近景 S0054/S0056/S0063 的 11.5–13.2 略软一点；p98 {f1(sh['s012c']['p98'])}（EV 99–107）。</li>
<li>s009 的背景按 EV 的框只能测到窗玻璃和白板（白板本身平，没有边），手臂到指尖按距离逐渐虚（对焦在脸上，手伸向更远的白板）。</li>
</ul>
<h3>EV 0–120 s 各类实测范围（shots_ev.csv，最小–最大）</h3>
{table(['类', '镜数', '镜头', 'main σ_e', '背景 σ_e', '背景/main', 'p2', 'p98', '运动 px/帧'], ev_rows)}
<h3>EV 与 IRIS 同类并排（上 EV，下 IRIS v3；中间 2× 为脸/主体，右 2× 为背景，NEAREST 放大）</h3>
{''.join(f'<p><code>{E(f)}</code></p><img src="{E(f)}" alt="{E(f)}">' for f in pairs)}
<h2>每镜一帧</h2><img src="contact.jpg" alt="contact">
<h2>v2d → v3 质检对比</h2><p>v2d：<code>excerpt/qa/opening-v2d/</code>；v3：<code>excerpt/qa/opening-v3/</code>。</p>
{table(['项', 'v2d', 'v3'], cmp_rows)}
<h2>切点表（含新切点 56.9237）</h2>{cuts}
<h3>质检说明</h3><ul>
<li>单帧跳变 1 处（f187，7.79 s）：是 s002 原片里柱子被闪光照亮的那一帧（v2d 同帧同样亮：均值 49→75→49），不是新加的；v3 背景虚化后前后帧的细节变化变小，检测条件才被触发。闪烁最大值与 v2d 相同（3.5 次/秒，f607，s006 原片的摄影闪光）。</li>
<li>红色：她 matte 外红 &gt;12 px 的帧 v2d {q2['red']['frames_with_red_outside_her_over_12px']} → v3 {q['red']['frames_with_red_outside_her_over_12px']}。部分 A 类镜头（s011、s012b、s013b、s014 全景）计数上升：放大看是线网/点网三色错位在肤色和暖色灯上留下的零散红条纹（15×15 窗口内最多 10–26 px），不是红色物体；s014 推近段只有左耳耳挂灯是红的（1 帧 18 px 同为网纹）。s002 门缝外的红光是原片的 OUTSIDE 光源，v2d 已有，v3 背景虚化后最大面积 5914 → 2231 px。</li>
</ul>
<h2>网型对照（左 EV，右 IRIS v3）</h2><img src="ev_compare.jpg" alt="EV compare">
</body></html>"""
    (page / "index.html").write_text(doc, encoding="utf-8")
    print(page / "index.html")
    return 0


def main() -> int:
    if "--v3" in sys.argv:
        return main_v3()
    q = json.loads((QA / "qa.json").read_text())
    v = json.loads((QA / "qa_v2.json").read_text())
    PAGE.mkdir(parents=True, exist_ok=True)
    for f in ("contact.jpg", "ev_compare.jpg"):
        shutil.copyfile(QA / f, PAGE / f)
    s, so = q["spec"], q["sound"]
    cuts = table(["切点", "歌曲秒", "帧", "最近拍点", "切点−拍点 s", "帧−拍点 s", "画面变化峰值帧"],
                 [[c["cut"], c["t"], c["frame"], c["nearest_beat"], c["cut_dt_beat"], c["frame_dt_beat"], c["film_change_peak_frame"]] for c in q["cuts"]["cuts"]])
    marks = json.loads((EXC / "data/edl-opening-v2.json").read_text())["beat_marks"]
    ev_rows = [["s004 定格起点", 344, "口型段终点 14.3333 s（clip 3.02 s）", "不在拍点：最近拍 14.141（−0.19 s）"],
               ["s007 马赛克 + 推一级", 636, "拍 26.5056", f"{marks['636']:+.4f} s"],
               ["s007 马赛克 + 推一级", 647, "拍 26.97", f"{marks['647']:+.4f} s"],
               ["s010 纯黑图形帧起", 956, "拍 39.8454", f"{marks['956']:+.4f} s"],
               ["s013a 断网", "1233", "拍 51.3858", f"{marks['1233']:+.4f} s"],
               ["s013a 断网（2 帧）", "1244–1245", "拍 51.8502", f"{marks['1244']:+.4f} s"],
               ["s005 抖动/复印", "417–427", "PARTIAL ANSWER 气泡 17.355 s", "11 帧"]]
    lips = []
    for k in ("s004", "s008"):
        L = q["lips"][k]
        sc = L["sync_check"]
        lips.append([k, L["take"], f"{L['frames'][0]}–{L['frames'][1]}", json.dumps(L["picture_offset_vs_placement"], ensure_ascii=False),
                     json.dumps({x: sc[x] for x in list(sc)[:4]}, ensure_ascii=False), json.dumps(L["visible_lip_synced_frames"])])
    tex_rows = []
    for sid, r in v["texture"]["film"].items():
        p = v["texture"]["picture"][sid]
        other = "; ".join(f"{k} {a[0]}–{a[-1]}（{len(a)} 帧）" for k, a in p["other"].items())
        tex_rows.append([sid, f"{p['frames'][0]}–{p['frames'][1]}", p["screen"], p["pitch_px"], p["angle_deg"], p["orth_ratio"], other or "—",
                         ",".join(map(str, p["mosaic"])) or "—", f"{r['screen']} {r['share']:.0%} / {r['pitch_px']} px / {r['angle_deg']}°"])
    mo = v["motion"]
    mo_rows = [[sid, r["source"], r["median_change"], r["push_pct_per_s"] if r["push_pct_per_s"] is not None else "—"] for sid, r in mo["shots"].items()]
    g = v["graphics"]
    g_rows = [[sid, r["events"], f"{r['area_mean']:.1%}", "是" if r["bottom_right"] else "否", " ".join(r["ids"])] for sid, r in g["shots"].items()]
    cells = g["cells_all"]
    fl, rd = q["flash"], q["red"]
    worst = rd["worst"][:5]
    old = {"静帧/定格时长": "7.1%（4 镜）", "每镜事件图形中位数": "2（≤1 个的镜 6/20）", "面积中位数": "7.4%",
           "左中格墨迹": "56.4%", "出现过右下格的镜": "0/20", "工单卡": "93% 帧在场，430×97～430×286（2.0–5.9%）",
           "网": "1422/1422 帧同一线网 3.99 px/18.2°，点网 0 帧，一次性处理 0", "跨切图形": "SungLine 1014–1290 跨 7 镜等"}
    new = {"静帧/定格时长": f"{mo['share']['non_video']:.1%}（静帧 {mo['frames']['still']} 帧 + 定格 {mo['frames']['hold']} + 纯黑 {mo['frames']['black']}）",
           "每镜事件图形中位数": f"{g['events_median']:.0f}（IQR {g['events_iqr'][0]:.0f}–{g['events_iqr'][1]:.0f}）",
           "面积中位数": f"{g['area_median']:.1%}（静帧镜 {g['area_median_stills']:.1%}）", "左中格墨迹": f"{cells[1][0]:.1%}",
           "出现过右下格的镜": f"{g['shots_with_bottom_right']}/20", "工单卡": f"小组件 230×83（{g['chip_share']:.2%}），右上频谱下方",
           "网": "见下表", "跨切图形": f"{len(g['clips_over_cut'])} 个"}
    changes = ["s003、s007、s009、s010 改静帧（选定 take 首帧，经同一 prep 与红色修复；推近 0.69–0.8%/s，s007 不推，只在两拍上各推一级，最高 1.10×）",
               "s004 口型段之后（f344 起）定格在她举听筒那一帧（prepared 第 80 张，原视频的歌曲 f387）",
               "s010 最后 23 帧（956–978）纯黑，ALL 打在黑底上，不加网；工单组件同时反白",
               "主歌改为彩色点网 4.2 px（0°/90°）；修复上一版点网未生效：引擎 grade 合并时 GRADE_V4R4（uHalftone 0、uLineAM 0.3）覆盖了镜头的网点参数",
               "一次性处理：s005 抖动/复印 11 帧、s007 马赛克 2 帧、s010 纯黑、s011 粗线网 5.95 px、s013a 粗网点 7.2 px 按拍断网",
               "工单卡改为右上 230×83 小组件（单号/SEV + PAGED 计数）；左上只留一行章节字",
               "事件图形每镜在本镜切点退场，跨切的拆开；分散到右下、右中、上方等格；s001 寻呼机标签移到右下，引线锚点跟随寻呼机",
               "声音：母带原样，导出关闭响度归一（gain 0 dB）"]
    head = "v2d" if V2D else "v2c" if V2C else "v2"
    pic = "v2c" if V2C else "v2"                          # v2d has v2c's picture (layout fixes only)
    intro = ("按已认可的 v2 方案（<code>pilot/opening/plan/v2.html</code>、<code>plan/index.html</code>），s014 换成重拍的 MO07 r6-2（逐镜 Gate PASS）。"
             + ("v2d 只改两处版式：右下寻呼机堆叠上移，不再压住 SONG/BAR 读数；左前排检测框改为 LOOKING AT / THEIR LAPTOP。" if V2D else "")
             + "本页只列测量数字，好不好看由你判。") if V2C else \
        "按已认可的 v2 方案（<code>pilot/opening/plan/v2.html</code>、<code>plan/index.html</code>）。本页只列测量数字，好不好看由你判。s014 本轮沿用现有素材，重拍另做。"
    extra = ""
    if V2C:
        cols = [(n, json.loads((EXC / f"qa/opening-{n}/qa.json").read_text()), json.loads((EXC / f"qa/opening-{n}/qa_v2.json").read_text()))
                for n in (["v2", "v2c"] if V2D else ["v2"])] + [(head, q, v)]
        red = lambda r, ks: f"{sum(r[k]['over_12'] for k in ks)}/{sum(r[k]['frames'] for k in ks)}（最大 {max(r[k]['max_outside_px'] for k in ks)} px）"
        n_cut = lambda x: f"{len(x['cuts']['cuts'])} 个，全在拍点 {x['cuts']['pass']}，画面变化峰值落在切点 {x['cuts']['change_peak_on_cut']}"
        s014_red = lambda r: ("s014a " + red(r, ["s014a"]) + "；s014b " + red(r, ["s014b"])) if "s014b" in r else "s014 " + red(r, ["s014a"])
        row = lambda name, fn: [name, *(fn(qq, vv) for _, qq, vv in cols)]
        cmp_rows = [row("规格", lambda x, y: f"{x['spec']['frames']} 帧 {x['spec']['fps']} 通过 {x['spec']['pass']}"),
                    row("声音偏移 / RMS 差", lambda x, y: f"{x['sound']['offset_samples']} 样本 / {x['sound']['rms_diff_db']} dB"),
                    row("切点", lambda x, y: n_cut(x)),
                    row("s014 切点", lambda x, y: "、".join(str(c["frame"]) for c in x["cuts"]["cuts"] if c["cut"].startswith("s014"))),
                    row("s014 她 matte 外红 >12 px（每 2 帧）", lambda x, y: s014_red(x["red"]["per_shot"])),
                    row("s014c 红", lambda x, y: red(x["red"]["per_shot"], ["s014c"])),
                    row("全片红 >12 px 帧", lambda x, y: x["red"]["frames_with_red_outside_her_over_12px"]),
                    row("闪烁（最多次/秒，超 3 次的窗口）", lambda x, y: f"{x['flash']['max_flashes_per_second_any_cell']}，{x['flash']['windows_over_3_per_second_start_frames']}"),
                    row("单帧跳变", lambda x, y: len(x["flash"]["single_frame_jumps"])),
                    row("非视频帧占比", lambda x, y: f"{y['motion']['share']['non_video']:.1%}"),
                    row("每镜事件图形中位数 / 面积中位数", lambda x, y: f"{y['graphics']['events_median']:.0f} / {y['graphics']['area_median']:.1%}"),
                    row("跨切图形", lambda x, y: len(y["graphics"]["clips_over_cut"]))]
        s14 = v["texture"]["picture"]["s014a"]
        complaints = [("s003 倒退", "s003 改成静帧（选定 take 首帧，推近不到 1%/s），画面里不再有她往后退。"),
                      ("工单卡太 low / 只有一种蒙板", f"工单卡缩成右上 230×83 小组件（约 {g['chip_share']:.2%} 画面）；质感改为主歌彩色网点 4.2 px、副歌线网 3.99 px / 18.2°，"
                       "再各用一次：s005 抖动/复印、s007 马赛克（2 帧）、s010 纯黑、s011 粗线网 5.95 px、s013a 粗网点 7.2 px。"),
                      ("全是动态", f"s003 / s007 / s009 / s010 静帧，s004 后半（f344 起）定格，s010 最后 23 帧纯黑上打 ALL；非视频帧 {mo['share']['non_video']:.1%}。"),
                      ("57 s 观众抬头低头", "s014 换重拍的 MO07 r6-2：观众全程低头；55.0777–58.7697 一镜到底，去掉 57.3765 的跳切；"
                       "甩袖落在 57.3765 拍上（素材起点 0.035 s，素材 2.333 s 那张在 f1377）；之后 s014c 寻呼机插入镜不变。"
                       f"s014 画面网型：{s14['screen']} {s14['pitch_px']} px / {s14['angle_deg']}°。")]
        extra = (f"<h2>对上一轮被否的 review-final 的改动</h2>{table(['你的意见', '这一版怎么改'], complaints)}"
                 f"<h2>{' → '.join(n for n, _, _ in cols)} 质检对比</h2><p>"
                 + "；".join(f"{n}：<code>excerpt/qa/opening-{n}/qa.json</code>" for n, _, _ in cols) + "。</p>"
                 f"{table(['项', *(n for n, _, _ in cols)], cmp_rows)}"
                 "<p>s013b、s014c 的画面与 v2 相同（纯画面逐帧对比：s014 之前除 s013b 末 24 帧有 ≤1 级的编码差，其余为 0；s014c 为 0），"
                 "它们红色计数的小幅变化（s014c 帧 1414/1416 约 15 px、s013b 1262 帧 32 px）是成片里分散的单个像素（导出 H.264 与线网色噪），不是红色物体。</p>"
                 + ("<p>v2d 与 v2c 画面相同，只改两处图形。s014 多出的 1 个红色帧（f1380，17 px）是远处墙面上分散的暗锈色像素"
                    "（v2c 同一帧同一位置 5 px），属导出编码差异，不是图形或红色物体。</p>" if V2D else ""))
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>IRIS EP01 0–59.23 s 审片 {head}</title>
<style>body{{background:#111;color:#ddd;font:14px/1.5 system-ui,sans-serif;margin:24px;max-width:1500px}}h1,h2{{color:#fff}}
table{{border-collapse:collapse;margin:8px 0 20px;font-size:12.5px}}td,th{{border:1px solid #333;padding:3px 7px;text-align:left;vertical-align:top}}
th{{background:#222}}video,img{{max-width:100%}}code{{color:#F2B134}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}</style></head><body>
<h1>IRIS EP01 歌 0–59.2341 s 审片版 {head}（24 fps，1422 帧）</h1>
<p>{intro}</p>
<video src="../../../excerpt/renders/{FILM}" controls preload="metadata"></video>
<p>文件 <code>excerpt/renders/{FILM}</code>，SHA-256 <code>{q['film_sha256']}</code>；上一版 <a href="../../../excerpt/renders/{PREV}" style="color:#F2B134">{PREV}</a>。</p>
{extra}
<h2>与 v2 之前的版本对比</h2>
{table(["项", "上一版（texture_study 实测）", f"{head}（本页实测）"], [[k, old[k], new[k]] for k in old])}
<ul>{''.join(f'<li>{E(c)}</li>' for c in changes)}</ul>
<h2>规格与声音</h2>
{table(["宽", "高", "帧率", "帧数", "视频", "音频", "时长 s", "通过"], [[s['width'], s['height'], s['fps'], s['frames'], s['video_codec'] + ' ' + str(s['pix_fmt']), json.dumps(s['audio']), s['duration_s'], s['pass']]])}
{table(["与母带样本偏移", "RMS 差 dB", "对齐后残差 dB", "通过"], [[f"{so['offset_samples']} 样本（{so['offset_ms']} ms）", so['rms_diff_db'], so['residual_db_after_alignment'], so['pass']]])}
<h2>切点表（拍点误差）</h2>{cuts}
<h3>镜内事件帧</h3>{table(["事件", "帧", "依据", "与拍点差"], ev_rows)}
<h2>两段口型重测</h2>{table(["镜", "take", "帧", "画面实际取帧 vs 放置", "sync_check", "可见口型同步帧"], lips)}
<h2>逐镜质感（REPORT.md §1.1 口径）</h2>
<p>前 9 列在纯画面 <code>IRIS-EP01-{pic}-picture-000-1422.mp4</code> 上测（50 Mbit/s）；最后一列在成片上测（Agentcut 导出 H.264 约 6 Mbit/s，含图形层）。dot = 两方向点网（第二轴/主峰 ≥ 0.3），line = 单向线网。抖动/复印帧（近二值）：{E(', '.join(map(str, v['dither_frames'])) or '无')}。</p>
{table(["镜", "帧", "主网型", "点距 px", "角度°", "第二轴/主峰", "其他帧", "马赛克帧", "成片：主网型 占比 / 点距 / 角度"], tex_rows)}
<h2>动静</h2>
<p>按来源：静帧 {mo['frames']['still']} 帧（{mo['share']['still']:.1%}）、定格 {mo['frames']['hold']} 帧（{mo['share']['hold']:.1%}）、纯黑图形 {mo['frames']['black']} 帧（{mo['share']['black']:.1%}）、视频 {mo['frames']['video']} 帧（{mo['share']['video']:.1%}）；非视频合计 {mo['share']['non_video']:.1%}。EV 0–120 s：下限 25.7%，实测 44.6%。</p>
{table(["镜", "来源", "帧间变化中位数（480×270 灰度，8-bit）", "设计推近 %/s"], mo_rows)}
<h2>图形密度与位置（REPORT.md §1.3 口径）</h2>
<p>每镜事件图形中位数 {g['events_median']:.0f}（IQR {g['events_iqr'][0]:.0f}–{g['events_iqr'][1]:.0f}）；块化面积中位数 {g['area_median']:.1%}，静帧镜 {g['area_median_stills']:.1%}；跨切 clip {len(g['clips_over_cut'])} 个；出现过右下格的镜 {g['shots_with_bottom_right']}/20。墨迹九宫格（行：上/中/下，列：左/中/右）：{E(json.dumps(cells))}。</p>
{table(["镜", "事件数", "面积均值", "右下格", "clip"], g_rows)}
<h2>红色与闪烁（WCAG 2.3.1）</h2>
<p>闪烁：任一格每秒最多 {fl['max_flashes_per_second_any_cell']} 次（帧 {fl['at']['frame']}，格 {fl['at']['cell']}）；超过 3 次/秒的窗口起点 {E(json.dumps(fl['windows_over_3_per_second_start_frames']))}；通过 {fl['pass']}。</p>
<p>红色：检查 {rd['frames_checked']} 帧（每 2 帧），她 matte 外红色 &gt;12 px 的帧 {rd['frames_with_red_outside_her_over_12px']}，matte 内大块红 {len(rd['frames_with_large_red_inside_matte'])} 帧；最差 5 帧 {E(json.dumps(worst))}。</p>
<h2>每镜一帧</h2><img src="contact.jpg" alt="contact">
<h2>EV 对照（左 EV，右 IRIS {head}）</h2><img src="ev_compare.jpg" alt="EV compare">
<h2>未完成 / 未验证</h2><ul>
{'<li>s014 的检测框「LOOKING AT / THEIR LAPTOP」沿用原位置（左前排），延到 1410 切点退场；寻呼机堆叠底边从 990 上移到 950。</li>' if V2D else '<li>s014 r6-2 只换了画面；s014 的检测框「LOOKING AT / THEIR PAGER」沿用原位置（左前排），延到 1410 切点退场。</li>' if V2C else '<li>s014 重拍未做（本轮沿用现有素材）。</li>'}
<li>成片经 Agentcut 浏览器导出（约 6 Mbit/s），细点网在运动镜头中被压缩削弱，见质感表最后一列。</li>
<li>新增的检测框/标签文字取自分镜表、工单与歌词，未新增事实；位置按画面目测放置，未逐帧跟踪（s001 寻呼机除外）。</li></ul>
</body></html>"""
    (PAGE / "index.html").write_text(doc, encoding="utf-8")
    print(PAGE / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
