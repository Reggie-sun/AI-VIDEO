#!/usr/bin/env python3
"""Build the s031-s048 r2 pre-submit pack for SG15, SG17 and SG20 (no Provider, no browser, no canonical writes).

  uv run python outputs/ai-city-takeover/ep01/v4/pilot/s031-048/submit-r2/build.py [--check]

Run it only where gen/unit.py and board/shots.json carry pilot/s031-048/r2/PATCH.md (the scratch copy before the patch is
applied, or the repository after it): it asserts every first frame equals its spec's plate sha. --check rebuilds in memory
and compares with the files on disk (exit 1 on any difference); without it, writes:
- pilot/s031-048/submit-r2/preview-inputs.json   the three units (first frame, exact r2 draft prompt, mode, seconds,
  vocal window, plan rows, risks, cost) and the remade s047 still
- pilot/s031-048/submit-r2/index.html            the pack page the approvals bind
- pilot/s031-048/r2/index.html                   the user's re-approval page (prompt diffs, before/after, decisions)
- pilot/s031-048/r2/<UNIT>-approval.template.json  take a-1 (a-2 differs as its _template_notes say)

Reuses pilot/s031-048/submit/build.py (plan rows, lessons, notes, cost rule) read-only; that pack and its templates stay
as they are (the other eight units are being submitted from them). Writes no approval.
"""
from __future__ import annotations

import difflib
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent            # pilot/s031-048/submit-r2
GROUP = HERE.parent                               # pilot/s031-048
R2 = GROUP / "r2"
_spec = importlib.util.spec_from_file_location("s3148_submit_build", GROUP / "submit/build.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)                       # read-only reuse; importing it writes nothing
U, REPO, sha, rel = B.U, B.REPO, B.sha, B.rel

PROMPTS = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s031-048-seedance-r2.md"
OLD_PROMPTS = B.PROMPTS                           # s031-048-seedance.md (the held a-1 approvals bind it)
PAGE = rel(HERE / "index.html")
INPUTS = rel(HERE / "preview-inputs.json")
REVIEW = rel(R2 / "index.html")
PATCH = rel(R2 / "PATCH.md")
TAG = "a"                                         # the empty take folders sd-<UNIT>-a-1|2 (each a-1 holds the held approval)
UNITS = ["SG15", "SG17", "SG20"]
FRAMES = {"SG15": "P036/x", "SG17": "P039/b", "SG20": "CONT1124/p048-arm-b-comp"}
STILLS = {"s047": ["CONT1124/p047-rb-c-2944"]}    # replaces CONT1124/p047-rb-b-2944 (left arm sleeved)
OLD_STILL = "CONT1124/p047-rb-b-2944"
# the two candidates per image (CONT1124/prompt-r2.md, runs-r2.md; comp.py boxes in r2/PATCH.md); the first is recommended
CANDIDATES = {"p048": {"before": U.PLATES + "p048-w1.png", "pick": "CONT1124/p048-arm-b-comp",
                       "other": "CONT1124/p048-arm-a-comp", "raw": ["CONT1124/p048-arm-b", "CONT1124/p048-arm-a"],
                       "why": "b 的外套左边收在一道拉链边上，和 s042 / s046 那件外套的拉链边一致；a 外套左边是一道平的布边。两张左臂都裸露到手腕，脸、嘴、耳挂、隔板逐像素不变。"},
              "p047": {"before": B.DESIGN + "CONT1124/p047-rb-b.png", "pick": "CONT1124/p047-rc-a-comp",
                       "other": "CONT1124/p047-rc-b-comp", "raw": ["CONT1124/p047-rc-a", "CONT1124/p047-rc-b"],
                       "why": "两张几乎一样；a 的贴回接缝更小（接缝环平均差 4.35 对 5.34），前臂线条更顺。脸、耳挂、手指、纸条逐像素不变。"}}
LESSONS = {
    "SG15": [r for r in B.LESSONS["SG15"]] + ["“最后一句”有歧义（窗口尾巴带下一句 “Ten”），r2 改绑第三句“让开”（Out of my way，片内约 2.79 s）"],
    "SG17": [r for r in B.LESSONS["SG17"]] + ["“最后一句”有歧义（只有两句，句首带上一句 “more.” 尾巴），r2 改绑第二句“他们找到了一道缝”（They found a gap，片内约 2.05 s）"],
    "SG20": [r for r in B.LESSONS["SG20"]] + ["W1 左臂必须从肩到腕裸露（s042 / s046 一致）；首帧 p048-w2 已改，prompt 也写明，Gate 时看她左臂有没有长出袖子"],
}
NOTES = {
    "SG15": [*B.NOTES["SG15"], "2026-11-25 r2：挪椅子改绑第三句“让开”（窗口内句序：Ten oh two: P zero. / Pager screams. / Out of my way.，尾巴带下一句 Ten）；首帧、秒数、人声不变"],
    "SG17": [*B.NOTES["SG17"], "2026-11-25 r2：按手改绑第二句“他们找到了一道缝”（窗口内句序：Bet it couldn't reach outside. / They found a gap instead.）；首帧、秒数、人声不变"],
    "SG20": [*B.NOTES["SG20"], "2026-11-25 r2：首帧换 p048-w2（W1 左臂从肩到腕裸露，本地有界合成只换左臂与外套垂布，其余逐像素等于 p048-w1）；prompt 加“她的左肩和整条左臂一直裸露，灰色外套只有右臂一只长袖”"],
}
KNOWN_ISSUES = [
    ("范围", "本包只有 SG15、SG17、SG20；其余 8 条仍按 submit/ 包与 s031-048-seedance.md 提交，本包不改它们。", "—"),
    ("应用顺序", "本包的 board sha 是 r2/PATCH.md 应用之后的值；PATCH 应用前（当前一批还在提交）不要写这三条的 approval。",
     "当前一批提交完 → 应用 PATCH.md → 跑本脚本 --check 与测试 → 写 approval。"),
    ("s047 静图", "s047 改用 CONT1124/p047-rb-c-2944（左臂裸露）；它是静图，不生成，只影响剪辑取图。", "剪辑时用新图。"),
]


def B_prompts(path: str) -> dict:
    text = (REPO / path).read_text(encoding="utf-8")
    found = re.findall(r"^## (s\d{3}) · (\w+) · .*?\n\n```prompt\n(.*?)\n```", text, re.S | re.M)
    return {unit: (shot, prompt) for shot, unit, prompt in found}


def build() -> dict:
    board = json.loads((REPO / U.BOARD).read_bytes())
    assert hashlib.sha256((REPO / U.BOARD).read_bytes()).hexdigest() == U.BOARD_SHA256, "apply r2/PATCH.md first"
    shots = {s["id"]: s for s in board["shots"]}
    clips = {c["clip"]: c for c in board["clips"]}
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    segs, unit_rows = B.plan_rows()
    new, old = B_prompts(PROMPTS), B_prompts(OLD_PROMPTS)
    assert list(new) == UNITS, list(new)
    units = []
    for unit in UNITS:
        shot, prompt = new[unit]
        assert old[unit][0] == shot
        spec, clip = U.SPECS[unit], clips[unit]
        assert clip["used_by"] == [shot] and shots[shot]["plate"] == clip["start_frame"] == spec["plate"]
        frame = B.DESIGN + FRAMES[unit] + ".png"
        plate = U.PLATES + spec["plate"] + ".png"
        assert sha(frame) == sha(plate) == spec["plate_sha256"]
        literals = [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"], *spec["intent"]["natural"]]
        assert [x for x in literals if x not in prompt] == [] and U.prompt_language_ok(spec, prompt)
        assert "最后" not in prompt
        secs = spec["duration"]
        uses = [seg for seg in segs if seg[:4] == shot and unit in segs[seg]["kind"]]
        window = windows[spec["audio"]["window"]]
        assert window["path"] == spec["audio"]["path"] and sha(window["path"]) == window["sha256"]
        d = spec["dialogue"]
        units.append({
            "shot": shot, "unit": unit, "clip": unit, "mode": spec["input_mode"], "look": spec["look"],
            "song_span_s": [clip["plays"]["t0"], clip["plays"]["t1"]],
            "generation_window_s": [clip["window"]["t0"], clip["window"]["t1"]],
            "first_frame": {"path": plate, "sha256": spec["plate_sha256"], "design_frame": frame},
            "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "previous_prompt": {"path": OLD_PROMPTS, "sha256": hashlib.sha256(old[unit][1].encode()).hexdigest()},
            "required_phrases": literals,
            "seconds": secs, "take_margin_seconds": spec.get("take_margin_seconds", 0), "resolution": "4k", "aspect": "16:9",
            "takes": B.TAKES, "est_cost_per_take_CRD": secs * B.RATE, "ceiling_per_take_CRD": B.ceiling(secs),
            "plan": {seg: segs[seg] for seg in uses}, "plan_unit": unit_rows[unit], "lesson_risks": LESSONS[unit],
            "vocal": {"path": window["path"], "sha256": window["sha256"], "seconds": window["seconds"],
                      "song_window_s": window["song_window"], "clip_words": clip["words"],
                      "lyric_text": d["verbatim_text"], "dialogue_s": [d["start_seconds"], d["end_seconds"]]}})
    stills = [{"segment": seg, "frames": [{"path": B.DESIGN + f + ".png", "sha256": sha(B.DESIGN + f + ".png")} for f in frames],
               "replaces": {"path": B.DESIGN + OLD_STILL + ".png", "sha256": sha(B.DESIGN + OLD_STILL + ".png")},
               "plan": segs[seg]} for seg, frames in STILLS.items()]
    est = sum(u["est_cost_per_take_CRD"] for u in units) * B.TAKES
    ceil_sum = sum(u["ceiling_per_take_CRD"] for u in units)
    return {"schema": "iris-v4-preview-inputs/s031-048-r2-1", "range_s": [shots["s036"]["t0"], shots["s048"]["t1"]],
            "method": "Seedance 2.0 VIP 4k（使用者 2026-11-17：画质最高/积分随便用）",
            "director_plan": {"path": B.PLAN, "sha256": sha(B.PLAN)},
            "first_frame_preview": {"path": B.PREVIEW, "sha256": sha(B.PREVIEW)},
            "base_pack": {"path": B.INPUTS, "sha256": sha(B.INPUTS)},
            "source_prompt_file": PROMPTS, "source_prompt_file_sha256": sha(PROMPTS),
            "board": {"path": U.BOARD, "sha256": U.BOARD_SHA256}, "patch": PATCH,
            "plan": "每 unit 同一首帧拍 2 条，过逐镜 Gate 后挑一条；每条一次不重试",
            "cost_basis": f"4k 每秒 {B.RATE} 积分；单条上限 = 该价向上取整到百（与 submit/ 包同一口径，秒数不变）",
            "total_seconds_per_take_set": sum(u["seconds"] for u in units),
            "estimated_total_CRD": est, "ceiling_per_take_sum_CRD": ceil_sum, "ceiling_total_CRD": ceil_sum * B.TAKES,
            "units": units, "stills": stills,
            "known_issues": [{"where": w, "issue": i, "proposal": p} for w, i, p in KNOWN_ISSUES]}


STYLE = ("<style>body{background:#0b0d12;color:#dfe6ee;font:15px/1.7 system-ui,sans-serif;margin:24px auto;max-width:1500px;"
         "padding:0 24px}.card{display:flex;gap:16px;border-bottom:1px solid #1b2230;padding:14px 0;align-items:flex-start}"
         ".im{flex:0 0 640px}.im img{width:640px;display:block}.tx{flex:1;min-width:0}h3{margin:0;font-size:16px;color:#f3d9a8}"
         ".pr{background:#11151c;padding:8px 12px;border-radius:6px}.n{color:#ff8a3d}.d{color:#7f8b97;font-size:13px}"
         ".pl{color:#9fb4c7;font-size:14px}.rk{color:#ffb4a8;font-size:14px}audio{width:100%;margin:4px 0}"
         "table{border-collapse:collapse}td,th{border:1px solid #1b2230;padding:4px 8px;text-align:left;vertical-align:top}"
         "del{background:#4a1d1d;color:#ffb4a8;text-decoration:line-through}ins{background:#163a22;color:#a8f0bf;text-decoration:none}"
         ".ask{border:2px solid #f3d9a8;border-radius:8px;padding:10px 16px;margin:12px 0}.g{display:flex;gap:10px;flex-wrap:wrap}"
         ".g figure{margin:0;width:480px}.g img{width:480px;display:block}.g figcaption{font-size:13px;color:#9fb4c7}"
         ".rec{outline:3px solid #a8f0bf}li{margin:4px 0}</style>")


def up(p: str) -> str:
    return "../../../" + p.split("ep01/v4/", 1)[1]          # both pages sit two levels under pilot/


def pack_page(data: dict) -> str:
    esc = html.escape
    out = ['<!doctype html><meta charset="utf-8"><title>IRIS EP01 s031–s048 r2 提交包（SG15 · SG17 · SG20）</title>', STYLE,
           "<h1>IRIS EP01 s031–s048 r2 · SG15 · SG17 · SG20 · Seedance 2.0 VIP 4k 提交包</h1>",
           f"<p>3 条念白（multimodal：首帧 + 人声），每条同一首帧拍 {B.TAKES} 次、每次不重试。每套 {data['total_seconds_per_take_set']} 秒，"
           f"<b>预计 {data['estimated_total_CRD']:,} 积分</b>，<b>上限 {data['ceiling_total_CRD']:,}</b>（秒数与 submit/ 包相同，已算在原 10,400 / 11,200 里）。"
           f"认可页：<a href=\"../r2/index.html\">r2/index.html</a>。本页没有提交任何东西。</p>",
           f"<p class=\"d\">board sha {data['board']['sha256'][:12]}…（{esc(data['patch'])} 应用之后）· prompt 来源 "
           f"{esc(data['source_prompt_file'].split('ep01/v4/')[1])} sha {data['source_prompt_file_sha256'][:12]}…</p>"]
    for u in data["units"]:
        plan = " ／ ".join(f"{seg} {r['time']}｜{r['lyric']}｜{r['picture']}" for seg, r in u["plan"].items())
        v = u["vocal"]
        cost = (f"{u['seconds']} s · 4k · 16:9 · {u['mode']} · {u['takes']} 条 × {u['seconds']} s × {B.RATE} = "
                f"{u['est_cost_per_take_CRD'] * u['takes']} 积分（单条上限 {u['ceiling_per_take_CRD']}） · prompt sha {u['prompt_sha256'][:12]}…")
        risks = "".join(f"<li>{esc(r)}</li>" for r in u["lesson_risks"])
        out.append(f'<div class="card"><div class="im"><img src="{up(u["first_frame"]["path"])}"><div class="d">'
                   f'{Path(u["first_frame"]["path"]).name} = {esc(u["first_frame"]["design_frame"].split("S31-48/")[1])}'
                   f' · sha {u["first_frame"]["sha256"][:12]}…</div></div><div class="tx">'
                   f'<h3>{u["shot"]} · {u["unit"]} · {u["mode"]} · 造型 {u["look"]} · 剪辑 {u["song_span_s"][0]:.3f}–{u["song_span_s"][1]:.3f} s</h3>'
                   f'<p class="pl">方案：{esc(plan)}</p><p class="d">Gate 只验收：{esc(u["plan_unit"]["gate"])}</p>'
                   f'<p class="n">人声窗口 {v["song_window_s"][0]}–{v["song_window_s"][1]} s（{v["seconds"]} s，口型 {v["dialogue_s"][0]}–'
                   f'{v["dialogue_s"][1]} s）：{esc(v["lyric_text"])}</p><audio controls preload="none" src="{up(v["path"])}"></audio>'
                   f'<p class="pr">{esc(u["prompt"])}</p><p class="d">{esc(cost)}</p>'
                   f'<div class="rk">风险（教训）：<ul>{risks}</ul></div></div></div>')
    out.append("<h2>静图（不生成）</h2><table><tr><th>段</th><th>时间 s</th><th>新</th><th>原</th></tr>")
    for s in data["stills"]:
        f = s["frames"][0]
        out.append(f'<tr><td>{s["segment"]}</td><td>{esc(s["plan"]["time"])}</td><td><img src="{up(f["path"])}" width="360"><br>'
                   f'{esc(f["path"].split("S31-48/")[1])}</td><td><img src="{up(s["replaces"]["path"])}" width="360"><br>'
                   f'{esc(s["replaces"]["path"].split("S31-48/")[1])}</td></tr>')
    out.append("</table><h2>费用</h2><table><tr><th>unit</th><th>秒</th><th>单条约</th><th>2 条约</th><th>单条上限</th></tr>")
    for u in data["units"]:
        out.append(f'<tr><td>{u["shot"]} {u["unit"]}</td><td>{u["seconds"]}</td><td>{u["est_cost_per_take_CRD"]}</td>'
                   f'<td>{u["est_cost_per_take_CRD"] * u["takes"]}</td><td>{u["ceiling_per_take_CRD"]}</td></tr>')
    out.append(f'<tr><td><b>合计</b></td><td>{data["total_seconds_per_take_set"]}×2</td><td></td><td><b>{data["estimated_total_CRD"]:,}</b></td>'
               f'<td>{data["ceiling_per_take_sum_CRD"]:,}×2 = {data["ceiling_total_CRD"]:,}</td></tr></table><h2>已知问题</h2><ul>')
    out += [f'<li><b>{esc(k["where"])}</b>：{esc(k["issue"])}<br><span class="d">{esc(k["proposal"])}</span></li>' for k in data["known_issues"]]
    return "\n".join(out) + "</ul>\n"


def diff_html(a: str, b: str) -> str:
    out = []
    for op, i0, i1, j0, j1 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(html.escape(a[i0:i1]))
        else:
            if i1 > i0:
                out.append(f"<del>{html.escape(a[i0:i1])}</del>")
            if j1 > j0:
                out.append(f"<ins>{html.escape(b[j0:j1])}</ins>")
    return "".join(out)


def review_page(data: dict, pack_sha: str, inputs_sha: str) -> str:
    esc = html.escape
    old = B_prompts(OLD_PROMPTS)
    D = B.DESIGN
    out = ['<!doctype html><meta charset="utf-8"><title>IRIS EP01 s031–s048 r2 重新认可（SG15 · SG17 · SG20）</title>', STYLE,
           "<h1>s031–s048 r2：SG15、SG17、SG20 剩下的三处连续性缺口</h1>",
           '<div class="ask"><h2 style="margin:4px 0">要你定的（最多两件）</h2><ol>'
           "<li><b>这三条按本页开拍吗？</b>SG15 挪椅子绑第三句“让开”；SG17 按手绑第二句“他们找到了一道缝”；SG20 换左臂裸露的首帧 p048-w2。"
           "秒数和花费都不变：3 条 × 2 次，16 秒一套，预计 2,560 积分（上限 2,600），已算在原来的 10,400 / 11,200 里。"
           "<br>选项：<b>按 r2 开拍 (Recommended)</b> ／ 只改 prompt、首帧仍用 p048-w1 ／ 先不拍。</li>"
           "<li><b>两张图用哪一张？</b>s048 首帧：<b>b (Recommended)</b> ／ a；s047 静图：<b>a (Recommended)</b> ／ b。"
           "选非推荐件时主会话换一张、重跑 build.py 再写 approval。</li></ol>"
           "<p class=\"d\">什么都没提交、没付费、没写 approval、没 commit；unit.py / shots.json 等当前一批提交完再按 PATCH.md 改。</p></div>"]
    out.append("<h2>1 · prompt 改动（红删绿增）</h2>")
    order = {
        "SG15": "人声窗口 155.760–159.591 的句子顺序（words.json + 本地 Whisper 复核 SG15.wav）：① Ten oh two: P zero.（片内 0.12 s 起）"
                "② Pager screams.（1.99 s）③ <b>Out of my way.</b>（2.79–3.57 s）；尾巴还带下一句 “Ten” 约 0.06 s，所以“最后一句”有歧义。",
        "SG17": "人声窗口 170.109–173.778（words.json + 本地 Whisper 复核 SG17.wav）：开头带上一句 “more.” 尾巴 0.03 s；① Bet it couldn't reach outside."
                "（0.19 s 起）② <b>They found a gap instead.</b>（2.05–3.67 s，gap 在 2.73 s，和板子上“gap 上手掌按进光里”一致）。",
        "SG20": "首帧换成左臂裸露的 p048-w2（见下）；prompt 只加一句服装，免得模型把袖子长回来。"}
    for u in data["units"]:
        unit = u["unit"]
        out.append(f'<h3>{u["shot"]} · {unit}</h3><p class="d">{order[unit]}</p><p class="pr">{diff_html(old[unit][1], u["prompt"])}</p>'
                   f'<p class="d">旧 prompt sha {u["previous_prompt"]["sha256"][:12]}… → 新 {u["prompt_sha256"][:12]}… · {u["seconds"]} s · '
                   f'人声 <audio controls preload="none" src="{up(u["vocal"]["path"])}" style="width:320px;vertical-align:middle"></audio></p>')
    out.append("<h2>2 · W1 左臂：改前 / 推荐 / 另一张</h2><p>W1 造型左臂从肩到腕裸露（s042 p042-w2、s046 p046-w2 都是这样）。"
               "原 s047 静图和 s048 首帧里外套滑下来、用一截灰袖子盖住了左臂。Codex 编辑后只把左臂与外套垂布那一块贴回原图，"
               "块外逐像素等于原图：脸、闭着的嘴、左耳耳挂红灯、姿势、隔板、纸条都不变；红色像素与原图一致（只有耳挂灯），画面无字。</p>")
    for key, title in (("p048", "s048 · SG20 首帧"), ("p047", "s047 静图")):
        c = CANDIDATES[key]
        figs = [(c["before"], "改前", ""), (D + c["pick"] + ".png", f"推荐 {c['pick'].split('/')[1]}", "rec"),
                (D + c["other"] + ".png", f"另一张 {c['other'].split('/')[1]}", "")]
        out.append(f'<h3>{title}</h3><div class="g">' + "".join(
            f'<figure class="{cls}"><a href="{up(p)}"><img src="{up(p)}"></a><figcaption>{esc(cap)} · sha {sha(p)[:12]}…</figcaption></figure>'
            for p, cap, cls in figs) + f'</div><p class="d">推荐理由：{esc(c["why"])}</p>')
    out.append(f'<p class="d">放大与 240 px 对照（含开场脸）：<a href="{up(D + "CONT1124/check/CONT1124-p048-arm-b-comp.jpg")}">p048 b</a> · '
               f'<a href="{up(D + "CONT1124/check/CONT1124-p048-arm-a-comp.jpg")}">p048 a</a> · '
               f'<a href="{up(D + "CONT1124/check/CONT1124-p047-rc-a-comp.jpg")}">p047 a</a> · '
               f'<a href="{up(D + "CONT1124/check/CONT1124-p047-rc-b-comp.jpg")}">p047 b</a> · '
               f'<a href="{up(D + "CONT1124/check/r2-arm-zoom.jpg")}">左臂原尺寸对照</a></p>')
    out.append("<h2>3 · 秒数与花费（不变）</h2><table><tr><th>unit</th><th>秒</th><th>2 条约</th><th>单条上限</th></tr>")
    for u in data["units"]:
        out.append(f'<tr><td>{u["shot"]} {u["unit"]}</td><td>{u["seconds"]}</td><td>{u["est_cost_per_take_CRD"] * u["takes"]}</td>'
                   f'<td>{u["ceiling_per_take_CRD"]}</td></tr>')
    out.append(f'<tr><td><b>合计</b></td><td>{data["total_seconds_per_take_set"]}</td><td><b>{data["estimated_total_CRD"]:,}</b></td>'
               f'<td>{data["ceiling_per_take_sum_CRD"]:,}×2 = {data["ceiling_total_CRD"]:,}</td></tr></table>')
    out.append(f'<p class="d">提交包：<a href="../submit-r2/index.html">submit-r2/index.html</a>（sha {pack_sha[:12]}…；'
               f'preview-inputs sha {inputs_sha[:12]}…）· 应用步骤：{esc(PATCH.split("ep01/v4/")[1])} · '
               f'approval 模板：pilot/s031-048/r2/&lt;UNIT&gt;-approval.template.json</p>')
    return "\n".join(out) + "\n"


def template(row: dict, page_sha: str, inputs_sha: str, review_sha: str) -> dict:
    unit = row["unit"]
    value = B.template(unit, row, page_sha, inputs_sha)
    value["unit_group"] = f"v4-s031-048-r2-{unit}-{TAG}-1"
    value["question"] = f"<主会话问使用者的原问题，逐字（认可页 {REVIEW}）>"
    value["preview_page"] = {"path": PAGE, "sha256": page_sha}
    value["preview_inputs"] = {"path": INPUTS, "sha256": inputs_sha}
    value["prompt_source"] = {"path": PROMPTS, "sha256": sha(PROMPTS)}
    value["review_page"] = {"path": REVIEW, "sha256": review_sha}
    value["decision_notes"] = NOTES[unit]
    value["_template_notes"] = [
        f"本文件是 r2 的 {TAG}-1 模板；先按 {PATCH} 改好 unit.py / shots.json / 测试并跑通，再写成 pilot/sd-{unit}-{TAG}-1/preview-approval.json："
        "删除本 _template_notes 字段并填好 question / user_quote / approved_at 三个占位（同一文件夹里的 preview-approval.held-r2.json 是被 r2 取代的旧件，保留不动）。",
        f"{TAG}-2：unit_group 末尾 {TAG}-1→{TAG}-2；bound_ids 三个 id 中 -{TAG}-1- → -{TAG}-2-；takes.this_take → sd-{unit}-{TAG}-2"
        f"（takes.folders 保持 [{TAG}-1, {TAG}-2]）；其余逐字相同。",
        value["_template_notes"][2]]
    return value


def render() -> dict[Path, str]:
    data = build()
    files: dict[Path, str] = {}
    inputs = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    pack = pack_page(data)
    files[HERE / "preview-inputs.json"], files[HERE / "index.html"] = inputs, pack
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    review = review_page(data, h(pack), h(inputs))
    files[R2 / "index.html"] = review
    for row in data["units"]:
        value = template(row, h(pack), h(inputs), h(review))
        files[R2 / f"{row['unit']}-approval.template.json"] = json.dumps(value, ensure_ascii=False, indent=1) + "\n"
    return files


def main() -> int:
    files = render()
    if "--check" in sys.argv:
        bad = [rel(p) for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        print(json.dumps({"matches": not bad, "differs": bad}, ensure_ascii=False))
        return 1 if bad else 0
    R2.mkdir(exist_ok=True)
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(json.dumps({rel(p): sha(rel(p)) for p in files}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
