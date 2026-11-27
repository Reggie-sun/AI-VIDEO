#!/usr/bin/env python3
"""Build the s031-s048 pre-submit preview pack (no Provider, no browser, no canonical writes).

  uv run python outputs/ai-city-takeover/ep01/v4/pilot/s031-048/submit/build.py

Adapted from pilot/s015-030/submit/build.py. Writes, from files already on disk:
- pilot/s031-048/submit/preview-inputs.json  every unit's first frame, exact draft prompt, mode, seconds, vocal window,
  plan rows, the risks the plan and the lessons flag, and cost; the stills, graphic frame and 4K crop (no generation)
- pilot/s031-048/submit/index.html           the page the user approves (http://127.0.0.1:8769/pilot/s031-048/submit/)
- pilot/s031-048/<UNIT>-approval.template.json  one per unit (take a-1; a-2 differs as its _template_notes say)

Sources: the draft prompts excerpt/flash/s031-048-seedance.md (verbatim ```prompt blocks), the board plates and clips
(board/shots.json), the sealed vocal windows (pilot/audio/windows.json), the director plan (pilot/s031-048/plan/index.html:
segment rows and the unit table) and gen/unit.py SPECS (seconds, mode, dialogue). Cost: 80 CRD per second at 4k; the
per-take operator ceiling is that rounded up to the next 100. Writes no approval; the main session writes approvals.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent            # pilot/s031-048/submit
GROUP = HERE.parent                               # pilot/s031-048
V4 = GROUP.parents[1]
REPO = V4.parents[3]
sys.path.insert(0, str(V4 / "gen"))
import unit as U  # noqa: E402

rel = lambda p: str(Path(p).resolve().relative_to(REPO))
sha = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
PROMPTS = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s031-048-seedance.md"
PLAN = "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/plan/index.html"
PREVIEW = "outputs/ai-city-takeover/ep01/v4/pilot/s031-048/preview/index.html"
DECISIONS = "outputs/ai-city-takeover/logs/decisions.md"
DESIGN = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S31-48/"
PAGE = rel(HERE / "index.html")
INPUTS = rel(HERE / "preview-inputs.json")
RATE = 80                                         # CRD per second, Seedance 2.0 VIP 4k
TAKES = 2
TAG = "a"                                         # take folders sd-<UNIT>-a-1|2
UNITS = ["SG12", "INS33", "SG15", "SG16", "INS37", "SG17", "SG18", "INS41", "SG19", "MO15", "SG20"]
# the user's first-frame choices (「全按推荐 (Recommended)」, logs/decisions.md 2026-11-24; preview/index.html)
# 2026-11-24 pre-submit continuity fixes (pilot/s031-048/issues/index.html, pending re-approval): SG16 / INS37 / SG19 /
# MO15 first frames are the CONT1124 candidates (microwave added; mirrored insert; knee-high boots; hangers bunched)
FRAMES = {"SG12": "P031/a", "INS33": "INS33/b", "SG15": "P036/x", "SG16": "CONT1124/p037-mw-b-comp", "INS37": "CONT1124/ins37-flip",
          "SG17": "P039/b", "SG18": "P041/c", "INS41": "INS41/b", "SG19": "CONT1124/p042-knee-b-comp",
          "MO15": "CONT1124/p046-kh-b-comp", "SG20": "P048/b"}
# stills (not generated): plan segment -> the recommended design frame(s) of the preview page
STILLS = {"s031b": ["S031B/a-2944"], "s032": ["P032/a-fix-2944", "P032/a-palm-2944"], "s033a": ["S033A/a-2944"],
          "s034": ["P034/a-2944"], "s035a": ["S035A/a-2944"], "s035b": ["S035B/a-2944", "S035B/canister-2-2944"],
          "s037a": ["S037A/a-2944"], "s038a": ["P038/a-2944"], "s038b": ["S038B/b-2944"], "s038c": ["P038/a-2944"],
          "s040a": ["P040/a-2944"], "s040b": ["S040B/a2-fix-2944", "S040B/b2-2944"], "s043": ["P043/a-2944"],
          "s044": ["P044/a-2944"], "s045": ["P045/c-2944"], "s047": ["CONT1124/p047-rb-b-2944"]}   # s047 remade: partition on the right
OTHER = {"s036b": "纯图形帧（P0 工单整屏，不生成）", "s046b": "从 MO15 的 4K 片子裁（秒表插镜，不生成）"}
# risks the recorded lessons flag for each unit (HANDOFF-2026-11-23, docs/record_for_agent/2026-11-23-…-checkpoint.md,
# seedance-authoring Turn-Away advisory); the plan's own risk column is shown next to these
LESSONS = {
    "SG12": ["念白口型最不稳（s015–s030 SG08 一条全闭嘴、一条改词；SG11 只对上前 2 s）→ 只验收 134.44–136.27、139.92–141.29 两段",
             "人声尾巴含下一句 “It as-” 约 0.21 s（方案窗口止于 141.293 切点），切点前嘴可能张开",
             "收腰带的手离嘴近；看出口只许动眼，不转头", "售货机商品与小屏会长字、走廊出口灯会出红"],
    "INS33": ["黄铜件会长刻字/刻度", "手指数与松手后盖子的机构（模型可能乱补）", "吸走那一下留给 s034 后期，不让模型做"],
    "SG15": ["窗口起点 155.76（“Ten” 前 0.12 s）：方案的 155.58 落在 “call.” 里，cut_audio 拒切，按 SG08/SG09m 先例从上一词结束处起；"
             "生成因此 5 s（方案 6 s）", "人声尾巴含下一句 “Ten” 约 0.06 s", "寻呼机液晶会出数字或红光；书脊会长字",
             "低眼看读者时转头遮嘴（已写只动眼）；读者挪椅可能带出别的动作"],
    "SG16": ["窗口起点 161.338（“Stop” 前 0.04 s）：方案的 161.08 落在 “picks” 里，cut_audio 拒切，按 SG08（0.05 s）先例从 “up.” 结束处起",
             "工程师转过来露脸（只许一张脸）；罐子/手机/咖啡机长字或亮灯", "念白口型（同 SG12）",
             "首帧加了 S037A 那台微波炉：灯要在“十二点三十四分停掉”那句熄灭（接 INS37 拔插头），不熄就 s037d 接不上；显示屏会长数字"],
    "INS37": ["微波炉显示屏出红色数字（最危险）；按键长字", "拔插头的物理；两个动作挤在 1.37 s（不准就在拍上跳切、挪入点）",
              "首帧是左右镜像：微波炉按键面板到了左边（S037A / SG16 里在右边），插座也在左"],
    "SG17": ["窗口起点 170.1094＝剪辑入点（“Bet” 前 0.195 s）：方案的 170.00 落在 “more.” 里",
             "红光溢到脸上或变成红灯（只许门缝一线，使用者「留红光，和 s002 一样算例外」）", "按手时身体前倾挡嘴；门上长牌子"],
    "SG18": ["窗口起点 177.47（“Eleven” 前 0.22 s）：方案的 177.39 落在 “said.” 里", "半速轻声唱、10 s 长窗口中段漂移（口型风险最高）",
             "玻璃倒影；人台长出脸；模型自己改灯光", "布下衣服被模型编出来（已写看不见布下面的衣服）"],
    "INS41": ["布的物理；手指数；人台长脸；倒影", "方案原写“手退出画面上方”，草稿改为“停在画面上方”（不写出画）"],
    "SG19": ["W1 斜挎带方向、腰链、寻呼机挂点漂移（s014 MO07 转身时寻呼机跳到背后）", "布落下时手去拽、手臂挡嘴；转身露背面",
             "布落得太快（185.585 剪切点约片内 0.92 s 时要还在往下落）；模型补出过膝靴"],
    "MO15": ["搭衣架的是左手（使用者备注，prompt 已写“左手”）", "隔板上冒出第二张脸（副本只许露手）；她转身",
             "衣服吊牌、秒表出数字"],
    "SG20": ["人声 208.80 后静音，剪辑要她静止闭嘴到 209.34（“All” 不能张嘴）；生成 6 s 留余量", "贴耳轻声的口型；说完自己加动作",
             "背后镜子里出现倒影"],
}
NOTES = {"MO15": ["首帧 p046-w1（P046/x）里搭在衣架上的是她的左手；使用者 2026-11-24 备注 MO15 的 prompt 要写“左手”，已改",
                  "2026-11-24 连续性修正：首帧换 p046-w2（及膝长靴；衣架堆在她这一头、靠隔板那段杆空着，推衣架才有地方推）"],
         "SG17": ["门缝下一线红光：使用者「留红光，和 s002 一样算例外 (Recommended)」（只允许这一线，其余除耳挂灯外无红）"],
         "SG18": ["s041→s042 换装：使用者「A 裹布 + 重音剪切 (Recommended)」：她从肩到脚裹在防尘布里，185.585 重音上剪到 W1",
                  "2026-11-24 连续性修正：抓布边绑在最后一个词“十月”（October）刚开口时；只露出手，手腕以上一直在布里"],
         "SG19": ["s041→s042 换装：使用者「A 裹布 + 重音剪切 (Recommended)」：SG19 从“布已离肩”开始，扯布由剪切完成；首帧 P042/a（头到大腿）",
                  "2026-11-24 连续性修正：首帧换 p042-w2（及膝长靴）；布慢慢往下落，唱完这一句之后才落到脚边（185.585 剪切点约片内 0.92 s 时布正落下）"],
         "SG20": ["人声窗口止于 208.80（“All” 208.93 之前），剪辑用到 209.34：生成 = 用到的 4.10 s + 1 s 余量取 6 s（方案同为 6 s）"],
         "SG15": ["方案的人声起点 155.58 落在上一词 “call.” 里（cut_audio 拒切），改从 155.76 起；生成 5 s（方案 6 s）"],
         "SG16": ["方案的人声起点 161.08 落在 “picks” 里（cut_audio 拒切），改从 161.338（“up.” 结束）起；生成 7 s 不变",
                  "2026-11-24 连续性修正：首帧 p037-c2 加上 S037A 那台微波炉（本地合成，她的像素不变）；放碗与灯灭绑在“十二点三十四分停掉”那句"],
         "INS37": ["2026-11-24 连续性修正：工程师右手拿手机，按键的是左手；首帧 p037-ins37b = INS37/b 左右镜像（无损），手从左边伸进来，插座在左边墙上"],
         "SG12": ["2026-11-24 连续性修正：纸币素色无字；收腰带绑在第一个词，塞纸币 + 眼睛往左瞟绑在第四句“运气不好”（No luck），去掉“最后”"],
         "INS33": ["2026-11-24 连续性修正：结尾改为手掌平按在合上的黄铜盖上（接 P034）"]}
KNOWN_ISSUES = [
    ("人声窗口", "SG15、SG16、SG17、SG18 方案写的“句首前 0.3 s”落在上一个词里（cut_audio 拒切，同 s015–s030 的 SG08 / SG09m）："
     "改从上一个词结束处起（SG15 155.76、SG16 161.338、SG18 177.47），SG17 从剪辑入点 170.1094 起。SG15 因此 5 s（方案 6 s，少 160 积分）。",
     "技术处理；主会话可改为包含上一个词的尾巴再切。"),
    ("SG12 / SG15 窗口尾", "方案窗口止于下一镜切点 141.293 / 159.591，人声尾巴各带下一句开头约 0.21 s（It as-）/ 0.06 s（Ten）；"
     "切点前嘴可能张开。", "按方案不改；Gate 时看切点前一帧。"),
    ("SG20", "人声止于 208.80（不含 All），剪辑用到 209.34；生成 6 s（4.10 s + 1 s）。", "与方案一致。"),
    ("静图", "15 张静图与 s036b 图形帧、s046b 4K 裁切不生成；静图推荐件仍在 excerpt/flash/design/S31-48/，未放进 board/plates/（本步只放视频首帧）。",
     "剪辑阶段按预览页推荐件取用。"),
    ("连续性修正（2026-11-24）", "continuity-supervisor 提交前报告的缺口已改：SG12/SG16/SG18 的动作按词落点写；SG19 布慢落、及膝长靴；"
     "INS33 结尾接 P034；INS37 镜像（左手、插座在左）；SG16 首帧加微波炉；SG19/MO15 首帧改及膝长靴；MO15 衣架堆在她这一头；s047 静图重做（隔板在右）。",
     "见问题页 pilot/s031-048/issues/index.html，需要使用者重新认可后再写 approval。"),
    ("INS41", "方案写“手退出画面上方”；草稿改为“两只手松开布，停在画面上方”（教训：不写出画）。剪辑只用 181.02–183.76。", "如要手退出画面，改一句后重建。"),
]


def cells(row: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip() for c in re.split(r"</td>\s*<td[^>]*>", row)]


def plan_rows() -> tuple[dict, dict]:
    """Segment rows (seg -> time, lyric, kind, picture, why …) and unit rows (unit -> risks, gate) of the plan page."""
    text = (REPO / PLAN).read_text(encoding="utf-8")
    segs, units = {}, {}
    for cls, body in re.findall(r'<tr><td class="(\w)">(.*?)</td></tr>', text, re.S):
        c = cells(body)
        if re.fullmatch(r"s\d{3}[a-d]?", c[0]):
            segs[c[0]] = dict(zip(("time", "lyric", "kind", "picture", "why", "why_motion", "graphics", "blur", "look"),
                                  (re.sub(r"\s+", " ", x) for x in c[1:])), cls=cls)
        else:
            units[c[0]] = dict(zip(("shots", "type", "gen", "frame_vocal", "prompt_points", "risks", "gate"),
                                   (re.sub(r"\s+", " ", x) for x in c[1:])))
    return segs, units


def prompts() -> dict:
    text = (REPO / PROMPTS).read_text(encoding="utf-8")
    found = re.findall(r"^## (s\d{3}) · (\w+) · .*?\n\n```prompt\n(.*?)\n```", text, re.S | re.M)
    return {unit: (shot, prompt) for shot, unit, prompt in found}


def ceiling(seconds: int) -> int:
    return math.ceil(seconds * RATE / 100) * 100


def build() -> dict:
    board = json.loads((REPO / U.BOARD).read_bytes())
    shots = {s["id"]: s for s in board["shots"]}
    clips = {c["clip"]: c for c in board["clips"]}
    windows = json.loads((REPO / U.VOCALS).read_text(encoding="utf-8"))["windows"]
    segs, unit_rows = plan_rows()
    drafts = prompts()
    assert list(drafts) == UNITS, list(drafts)
    units = []
    for unit in UNITS:
        shot, prompt = drafts[unit]
        spec, clip = U.SPECS[unit], clips[unit]
        insert = "insert" in clip                  # an insert clip has its own plate, not its shot's
        assert clip["used_by"] == [shot] and (insert or shots[shot]["plate"] == clip["start_frame"]) and clip["start_frame"] == spec["plate"]
        frame = DESIGN + FRAMES[unit] + ".png"
        plate = U.PLATES + spec["plate"] + ".png"
        assert sha(frame) == sha(plate) == spec["plate_sha256"]
        secs = spec["duration"]
        assert 4 <= secs <= 15                     # JimengProfile 4 s minimum; Seedance 2.0 VIP 15 s maximum
        uses = [seg for seg in segs if seg[:4] == shot and unit in segs[seg]["kind"]]
        row = {"shot": shot, "unit": unit, "clip": unit, "mode": spec["input_mode"], "look": spec["look"],
               "song_span_s": [clip["plays"]["t0"], clip["plays"]["t1"]],
               "generation_window_s": [clip["window"]["t0"], clip["window"]["t1"]],
               "first_frame": {"path": plate, "sha256": spec["plate_sha256"], "design_frame": frame},
               "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
               "required_phrases": [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"],
                                    *spec["intent"]["natural"]],
               "seconds": secs, "take_margin_seconds": spec.get("take_margin_seconds", 0), "resolution": "4k",
               "aspect": "16:9", "takes": TAKES, "est_cost_per_take_CRD": secs * RATE, "ceiling_per_take_CRD": ceiling(secs),
               "plan": {seg: segs[seg] for seg in uses}, "plan_unit": unit_rows[unit],
               "lesson_risks": LESSONS[unit]}
        if spec.get("audio"):
            window = windows[spec["audio"]["window"]]
            assert window["path"] == spec["audio"]["path"] and sha(window["path"]) == window["sha256"]
            d = spec["dialogue"]
            row["vocal"] = {"path": window["path"], "sha256": window["sha256"], "seconds": window["seconds"],
                            "song_window_s": window["song_window"], "clip_words": clip["words"],
                            "lyric_text": d["verbatim_text"], "dialogue_s": [d["start_seconds"], d["end_seconds"]]}
        else:
            row["clip_words"] = clip["words"]
        units.append(row)
    stills = [{"segment": seg, "frames": [{"path": DESIGN + f + ".png", "sha256": sha(DESIGN + f + ".png")} for f in frames],
               "plan": segs[seg]} for seg, frames in STILLS.items()]
    others = [{"segment": seg, "what": what, "plan": segs[seg]} for seg, what in OTHER.items()]
    est = sum(u["est_cost_per_take_CRD"] for u in units) * TAKES
    ceil_sum = sum(u["ceiling_per_take_CRD"] for u in units)
    return {"schema": "iris-v4-preview-inputs/s031-048-1", "range_s": [shots["s031"]["t0"], shots["s048"]["t1"]],
            "method": "Seedance 2.0 VIP 4k（使用者 2026-11-17：画质最高/积分随便用）",
            "director_plan": {"path": PLAN, "sha256": sha(PLAN)}, "first_frame_preview": {"path": PREVIEW, "sha256": sha(PREVIEW)},
            "source_prompt_file": PROMPTS, "source_prompt_file_sha256": sha(PROMPTS),
            "board": {"path": U.BOARD, "sha256": U.BOARD_SHA256},
            "plan": "每 unit 同一首帧拍 2 条，过逐镜 Gate 后挑一条；每条一次不重试",
            "cost_basis": f"4k 每秒 {RATE} 积分（开头与 s015–s030 实付口径）；单条上限 = 该价向上取整到百",
            "total_seconds_per_take_set": sum(u["seconds"] for u in units),
            "estimated_total_CRD": est, "ceiling_per_take_sum_CRD": ceil_sum, "ceiling_total_CRD": ceil_sum * TAKES,
            "previous_shot_first_frame": {"shot": "s030", "path": U.PLATES + shots["s030"]["plate"] + ".png",
                                          "sha256": sha(U.PLATES + shots["s030"]["plate"] + ".png")},
            "units": units, "stills": stills, "not_generated": others,
            "known_issues": [{"where": w, "issue": i, "proposal": p} for w, i, p in KNOWN_ISSUES]}


def page(data: dict) -> str:
    up = lambda p: "../../../" + p.split("ep01/v4/", 1)[1]          # served from ep01/v4/
    esc = html.escape
    out = ['<!doctype html><meta charset="utf-8"><title>IRIS EP01 s031–s048 提交前预览包</title>',
           "<style>body{background:#0b0d12;color:#dfe6ee;font:15px/1.7 system-ui,sans-serif;margin:24px auto;max-width:1500px;"
           "padding:0 24px}.card{display:flex;gap:16px;border-bottom:1px solid #1b2230;padding:14px 0;align-items:flex-start}"
           ".im{flex:0 0 640px}.im img{width:640px;display:block}.th{flex:0 0 120px;font-size:12px;color:#7f8b97}"
           ".th img{width:120px;display:block}.tx{flex:1;min-width:0}h3{margin:0;font-size:16px;color:#f3d9a8}"
           ".pr{background:#11151c;padding:8px 12px;border-radius:6px}.n{color:#ff8a3d}.d{color:#7f8b97;font-size:13px}"
           ".pl{color:#9fb4c7;font-size:14px}.rk{color:#ffb4a8;font-size:14px}audio{width:100%;margin:4px 0}"
           "table{border-collapse:collapse}td,th{border:1px solid #1b2230;padding:4px 8px;text-align:left;vertical-align:top}"
           "li{margin:4px 0}</style>",
           "<h1>IRIS EP01 s031–s048（133.87–209.34 s）· Seedance 2.0 VIP 4k 提交前预览包</h1>",
           f"<p>{len(data['units'])} 条生成（{sum(u['mode'] == 'multimodal' for u in data['units'])} 条念白/唱段用人声口型：首帧 + 人声；"
           f"{sum(u['mode'] == 'first_frame' for u in data['units'])} 条插镜与动作用首帧），每条同一首帧拍 {TAKES} 次、"
           f"每次不重试，逐条过 Gate 后挑一条。按 4k 每秒 {RATE} 积分：每套 {data['total_seconds_per_take_set']} 秒，"
           f"<b>预计共 {data['estimated_total_CRD']:,} 积分</b>（{data['total_seconds_per_take_set']} 秒 × {RATE} × {TAKES}），"
           f"<b>总上限 {data['ceiling_total_CRD']:,}</b>（单条上限按价向上取整到百）。静图、s036b 图形帧和 s046b 4K 裁切都不生成。"
           "认可后才提交；本页没有提交任何东西。</p>",
           "<p class=\"d\">规则（已认可的教训）：prompt 从首帧状态写起；念白/唱段不转身；不写走向镜头、不写出画；会长字或亮红灯的东西写明空白/不亮；"
           "只有一张脸；s039 只许门缝一线红光；MO15 写左手；s041 裹在布里；s045/MO15 副本不露脸。人声窗口从句首前约 0.3 s 起"
           "（落在上一个词里就从该词结束处起），生成 = ceil(窗口) + 1 s，最短 4 s。</p>"]
    prev = data["previous_shot_first_frame"]["path"]
    for u in data["units"]:
        plan = " ／ ".join(f"{seg} {r['time']}｜{r['lyric']}｜{r['picture']}" for seg, r in u["plan"].items())
        pu = u["plan_unit"]
        cost = (f"{u['seconds']} s · 4k · 16:9 · {u['mode']} · {u['takes']} 条 × {u['seconds']} s × {RATE} = "
                f"{u['est_cost_per_take_CRD'] * u['takes']} 积分（单条约 {u['est_cost_per_take_CRD']}，单条上限 {u['ceiling_per_take_CRD']}）"
                f" · prompt sha {u['prompt_sha256'][:12]}…")
        out.append(f'<div class="card"><div class="th"><img src="{up(prev)}"><span>上一镜首帧</span></div>'
                   f'<div class="im"><img src="{up(u["first_frame"]["path"])}"><div class="d">'
                   f'{Path(u["first_frame"]["path"]).name} = {esc(u["first_frame"]["design_frame"].split("S31-48/")[1])}'
                   f' · sha {u["first_frame"]["sha256"][:12]}…</div></div><div class="tx">'
                   f'<h3>{u["shot"]} · {u["unit"]} · {u["mode"]} · 造型 {u["look"]} · 剪辑 {u["song_span_s"][0]:.3f}–{u["song_span_s"][1]:.3f} s</h3>'
                   f'<p class="pl">方案：{esc(plan)}</p><p class="d">Gate 只验收：{esc(pu["gate"])}</p>')
        if "vocal" in u:
            v = u["vocal"]
            out.append(f'<p class="n">人声窗口 {v["song_window_s"][0]}–{v["song_window_s"][1]} s（{v["seconds"]} s，'
                       f'口型 {v["dialogue_s"][0]}–{v["dialogue_s"][1]} s）：{esc(v["lyric_text"])}</p>'
                       f'<audio controls preload="none" src="{up(v["path"])}"></audio>')
        elif u["clip_words"]:
            out.append(f'<p class="d">该窗口歌词（仅参考，不上传人声）：{esc(" ".join(u["clip_words"]))}</p>')
        risks = "".join(f"<li>{esc(r)}</li>" for r in u["lesson_risks"])
        out.append(f'<p class="pr">{esc(u["prompt"])}</p><p class="d">{esc(cost)}</p>'
                   f'<div class="rk">风险（教训）：<ul>{risks}</ul>方案风险栏：{esc(pu["risks"])}</div></div></div>')
        prev = u["first_frame"]["path"]
    out.append("<h2>静图、图形帧与插镜（不生成）</h2><table><tr><th>段</th><th>时间 s</th><th>来源</th><th>画面</th></tr>")
    for s in data["stills"]:
        r = s["plan"]
        imgs = "".join(f'<img src="{up(f["path"])}" width="200"><br>{esc(f["path"].split("S31-48/")[1])}<br>' for f in s["frames"])
        out.append(f'<tr><td>{s["segment"]}</td><td>{esc(r["time"])}</td><td>{imgs}（静图推荐件）</td><td>{esc(r["picture"])}</td></tr>')
    for o in data["not_generated"]:
        r = o["plan"]
        out.append(f'<tr><td>{o["segment"]}</td><td>{esc(r["time"])}</td><td>{esc(o["what"])}</td><td>{esc(r["picture"])}</td></tr>')
    out.append("</table><h2>费用</h2><table><tr><th>unit</th><th>秒</th><th>单条约</th><th>2 条约</th><th>单条上限</th></tr>")
    for u in data["units"]:
        out.append(f'<tr><td>{u["shot"]} {u["unit"]}</td><td>{u["seconds"]}</td><td>{u["est_cost_per_take_CRD"]}</td>'
                   f'<td>{u["est_cost_per_take_CRD"] * u["takes"]}</td><td>{u["ceiling_per_take_CRD"]}</td></tr>')
    out.append(f'<tr><td><b>合计</b></td><td>{data["total_seconds_per_take_set"]}×2</td><td></td>'
               f'<td><b>{data["estimated_total_CRD"]:,}</b></td><td>{data["ceiling_per_take_sum_CRD"]:,}×2 = '
               f'{data["ceiling_total_CRD"]:,}</td></tr></table>')
    out.append("<h2>已知问题（提交前要定）</h2><ul>")
    out += [f'<li><b>{esc(k["where"])}</b>：{esc(k["issue"])}<br><span class="d">{esc(k["proposal"])}</span></li>'
            for k in data["known_issues"]]
    out.append("</ul>")
    return "\n".join(out) + "\n"


def template(unit: str, row: dict, page_sha: str, inputs_sha: str) -> dict:
    spec, n, tag = U.SPECS[unit], unit.lower(), TAG
    label = U.APPROVAL_ROLE[spec["input_mode"]]
    artifacts = [{"path": row["first_frame"]["path"], "sha256": row["first_frame"]["sha256"], "role": f"{unit} {label}"}]
    if "vocal" in row:
        artifacts.append({"path": row["vocal"]["path"], "sha256": row["vocal"]["sha256"], "role": f"{unit} vocal"})
    ceil_ = row["ceiling_per_take_CRD"]
    frame = Path(row["first_frame"]["path"]).name
    look = {"W1": "造型 W1", "C": "造型 C（LC 银灰长风衣）"}[spec["look"]] + ("，本镜裹在防尘布里" if unit == "SG18" else "")
    return {
        "schema": "iris-v4-preview-approval/1", "unit_group": f"v4-s031-048-{unit}-{tag}-1",
        "question": f"<主会话问使用者的原问题，逐字（审看页 {PAGE}）>",
        "user_quote": "<使用者原话，逐字>", "approved_at": "<UTC ISO 时间，带时区>",
        "preview_page": {"path": PAGE, "sha256": page_sha}, "preview_inputs": {"path": INPUTS, "sha256": inputs_sha},
        "prompt_source": {"path": PROMPTS, "sha256": sha(PROMPTS)},
        "preview_artifacts": artifacts,
        "prompts": {unit: {"text": row["prompt"], "sha256": row["prompt_sha256"]}},
        "generation": spec["generation"],
        "budget": {"generations": 1, "retries": 0, "operator_ceiling_per_unit_CRD": ceil_, "cumulative_CRD": ceil_},
        "identity_waivers": ["IRIS"] if spec["iris"] else [],
        "identity_waiver_basis": (f"{label}（{frame}，与 {row['first_frame']['design_frame']} 逐字节相同）承担 IRIS（v4 锚点 F1a，"
                                  f"{look}）的身份；不附身份图") if spec["iris"] else
                                 f"画面里没有人脸（{frame}，与 {row['first_frame']['design_frame']} 逐字节相同；只有手），不涉及身份",
        "bound_ids": {"attempt_id": f"iris-{n}-{tag}-1-source-001", "policy_id": f"iris-{n}-{tag}-1-source-001",
                      "reservation_id": f"iris-{n}-{tag}-1-reservation-001"},
        "takes": {"approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
                  "folders": [f"sd-{unit}-{tag}-1", f"sd-{unit}-{tag}-2"], "generations_per_take": 1, "total_generations": 2,
                  "total_ceiling_CRD": ceil_ * 2, "this_take": f"sd-{unit}-{tag}-1"},
        **({"decision_notes": NOTES[unit]} if unit in NOTES else {}),
        "_template_notes": [
            f"本文件是 {tag}-1 的模板；写成 pilot/sd-{unit}-{tag}-1/preview-approval.json 前删除本 _template_notes 字段并填好 question / "
            "user_quote / approved_at 三个占位。prompt 若按「已知问题」改过，先改 s031-048-seedance.md、unit.py spec 与本页并重建，再写 approval。",
            f"{tag}-2：unit_group 末尾 {tag}-1→{tag}-2；bound_ids 三个 id 中 -{tag}-1- → -{tag}-2-；takes.this_take → sd-{unit}-{tag}-2"
            f"（takes.folders 保持 [{tag}-1, {tag}-2]）；其余逐字相同。",
            f"prep_unit.sh 命令（主会话执行）：TRIAL_DIR=outputs/ai-city-takeover/ep01/v4/pilot/sd-{unit}-{tag}-<k> bash "
            f"outputs/ai-city-takeover/ep01/v4/gen/prep_unit.sh {unit} {spec['duration']} {spec['input_mode']} {ceil_}"]}


def main() -> int:
    data = build()
    inputs = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    (HERE / "preview-inputs.json").write_text(inputs, encoding="utf-8")
    text = page(data)
    (HERE / "index.html").write_text(text, encoding="utf-8")
    page_sha, inputs_sha = sha(PAGE), sha(INPUTS)
    for row in data["units"]:
        value = template(row["unit"], row, page_sha, inputs_sha)
        (GROUP / f"{row['unit']}-approval.template.json").write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n",
                                                                      encoding="utf-8")
        for k in (1, 2):                            # empty take folders; the main session writes the approvals
            (GROUP.parent / f"sd-{row['unit']}-{TAG}-{k}").mkdir(exist_ok=True)
    print(json.dumps({"page": PAGE, "page_sha256": page_sha, "inputs": INPUTS, "inputs_sha256": inputs_sha,
                      "units": len(data["units"]), "seconds_per_set": data["total_seconds_per_take_set"],
                      "estimated_total_CRD": data["estimated_total_CRD"], "ceiling_total_CRD": data["ceiling_total_CRD"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
