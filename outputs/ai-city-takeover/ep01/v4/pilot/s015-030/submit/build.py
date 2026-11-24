#!/usr/bin/env python3
"""Build the s015-s030 pre-submit preview pack (no Provider, no browser, no canonical writes).

  uv run python outputs/ai-city-takeover/ep01/v4/pilot/s015-030/submit/build.py

Writes, from files already on disk:
- pilot/s015-030/submit/preview-inputs.json  every unit's first frame, exact draft prompt, mode, seconds, vocal window,
  plan row and cost; the stills and the 4K-crop inserts (no generation); known issues
- pilot/s015-030/submit/index.html           the page the user approves (http://127.0.0.1:8769/pilot/s015-030/submit/)
- pilot/s015-030/<UNIT>-approval.template.json  one per unit (take n-1; n-2 differs as its _template_notes say)

Sources: the draft prompts excerpt/flash/s015-030-seedance.md (verbatim ```prompt blocks), the board plates and clips
(board/shots.json), the sealed vocal windows (pilot/audio/windows.json), the director plan rows
(pilot/s015-030/plan/index.html) and gen/unit.py SPECS (seconds, mode, dialogue). Cost: 80 CRD per second at 4k (the
opening's paid rate); the per-take operator ceiling is that rounded up to the next 100.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent            # pilot/s015-030/submit
GROUP = HERE.parent                               # pilot/s015-030
V4 = GROUP.parents[1]
REPO = V4.parents[3]
sys.path.insert(0, str(V4 / "gen"))
import unit as U  # noqa: E402

rel = lambda p: str(Path(p).resolve().relative_to(REPO))
sha = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
PROMPTS = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/s015-030-seedance.md"
PLAN = "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/plan/index.html"
PREVIEW = "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/preview/index.html"
DESIGN = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/design/S15-30/"
PAGE = rel(HERE / "index.html")
INPUTS = rel(HERE / "preview-inputs.json")
RATE = 80                                         # CRD per second, Seedance 2.0 VIP 4k
TAKES = 2
UNITS = ["SG05", "SG06", "INS16", "SG07", "MO08", "MO09", "MO10", "SG08", "SG09", "MO11", "SG10", "MO12", "MO13", "SG11"]
# the user's first-frame choices (logs/decisions.md 2026-11-22; preview/index.html): shot -> design frame
FRAMES = {"s015": "P015/b", "s016": "P016/b", "s017": "CARS/p017-w2b", "s018": "P018/d", "s019": "P019/f2", "s020": "P020/f1",
          "s021": "P021/f2", "s022": "P022/f2", "s023": "P023/f1", "s024": "P024R/b", "s025": "P025/f1",
          "s026": "P026/f1", "s027": "P027B/b", "s028": "P028/f1", "s029": "P029/f1"}
# s024: the car remade to match p025 / p026, 「用 b (Recommended)」 on pilot/s015-030/p024r/index.html (was P024/f1)
# INS16: the s016 handset insert (no person), 「用 d 拍 (Recommended)」 on pilot/s015-030/ins16/index.html; an insert is its
# own board clip of its shot, so its first frame is looked up by unit, not by shot
FRAMES["INS16"] = "INS16/d"
AUDIT_NOTE_N = ("开拍前审查按页面逐句改 prompt（「照页面改 (Recommended)」，pilot/s015-030/audit/index.html）；本 take 文件夹"
                "原先的 approval（旧 prompt）备份为 preview-approval.json.before-audit-2026-11-22，未提交过")
# decisions an approval carries beyond its question (sealed into the template, so both takes say it)
NOTES = {**{u: [AUDIT_NOTE_N] for u in ("MO09", "MO10", "MO11", "MO13")},
         "MO09": [AUDIT_NOTE_N, "审查改过的「她始终完整在画面里，头顶不出画。」改为「她的头顶始终不出画。」（首帧里她从大腿处出画，"
                                "「完整」可能让模型拉远镜头），「改成「头顶始终不出画」 (Recommended)」"],
"INS16": ["使用者看到的是生成 3 s（约 480 积分）；即梦 Seedance 合同最短 4 s（JimengProfile duration_seconds ≥ 4），"
                   "主会话定改为 4 s、每条上限 400（logs/decisions.md 2026-11-22）；首帧与 prompt 不变"]}
# s027: first frame remade (she has just stepped out, the train on her left), 「用 a (Recommended)」 on pilot/s015-030/p027r
# s017: the background pickup turned to face the camera, 「用 b (Recommended)」 on pilot/s015-030/cars/index.html (was P017/a)
STILLS = ["s021", "s023", "s030"]
# take folders sd-<UNIT>-<tag>-1|2: "n" for the first round; a retake after a failed Gate gets its own tag and names the
# approval it replaces (SG05 m: 「按页面重拍 (Recommended)」 on pilot/s015-030/gate/sg05/index.html, logs/decisions.md 2026-11-22)
TAKE_TAG = {"MO12": "p", "SG05": "m", "SG06": "p", "SG07": "m", "SG08": "m", "SG09": "m", "SG10": "m", "SG11": "m"}
REPLACES = {"SG05": ("outputs/ai-city-takeover/ep01/v4/pilot/sd-SG05-n-1/preview-approval.json",
                     "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/gate/sg05/index.html",
                     "s015 重拍 m：n-1、n-2 两条 Gate 不通过（口型：人声从句中 59.157 s 切入、离 two 只有 0.03 s，模型先唱约 1.4 s 前奏，"
                     "7 s 无余量，“that's my cue”被截；n-1 有开走的车的红尾灯；两条左肩成块模糊）；首帧 p015-w1 不变，人声改为 "
                     "58.70–65.666 s（pilot/audio/SG05m.wav）、生成 8 s，prompt 加「街上只有停着的车，没有行驶的车。」；"
                     "n approval 与 sd-SG05-n-1/n-2 产物保留")}
# SG06-SG11 m (「照 s015 的教训改 (Recommended)」, logs/decisions.md 2026-11-22; asked without a review page): the n takes
# were never submitted; their approvals are replaced for the new vocal windows and the extra second
REPLACES |= {u: (f"outputs/ai-city-takeover/ep01/v4/pilot/sd-{u}-n-1/preview-approval.json", None, "人声窗口与余量按 s015 教训调整")
             for u in ("SG06", "SG07", "SG08", "SG09", "SG10", "SG11")}
GATE06 = "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/gate/sg06/index.html"
REPLACES["SG07"] = (REPLACES["SG07"][0], GATE06,
                    "人声窗口与余量按 s015 教训调整（「照 s015 的教训改 (Recommended)」：生成 8→9 s，窗口不变）；首帧换成 p017-w2b"
                    "（背景皮卡由车尾朝镜头改成车头朝镜头、不开灯，「用 b (Recommended)」，pilot/s015-030/cars/index.html）；"
                    "结尾改为只「然后直起身。」不出画（「按页面重拍，唱段不转身 (Recommended)」，pilot/s015-030/gate/sg06/index.html）")
# pre-shoot audit (「照页面改 (Recommended)」 on pilot/s015-030/audit/index.html): prompts reworded; the m approvals of
# SG08-SG11 now carry that question, so their reasons name both decisions
AUDIT = "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/audit/index.html"
AUDIT_NOTE = "开拍前审查按页面逐句改 prompt（「照页面改 (Recommended)」，pilot/s015-030/audit/index.html）"
for _u in ("SG08", "SG09", "SG10", "SG11"):
    REPLACES[_u] = (REPLACES[_u][0], AUDIT, "人声窗口与余量按 s015 教训调整；" + AUDIT_NOTE)
# MO12 p: back-view first frame after both n takes failed the Gate
REPLACES["MO12"] = ("outputs/ai-city-takeover/ep01/v4/pilot/sd-MO12-n-1/preview-approval.json",
                    "outputs/ai-city-takeover/ep01/v4/pilot/s015-030/p027b/index.html",
                    "s027 重拍 p：n-1、n-2 两条 Gate 不通过（都朝镜头斜走，约 1.5 s 脚出画，没从画面右侧出去；n-1 电脑背面露苹果标志，"
                    "n-2 帽衫和电脑上有图形）。使用者选「A 重做背影首帧再拍 (Recommended)」，再在 pilot/s015-030/p027b/index.html 选"
                    "「用 b (Recommended)」：首帧换成 p027-b3（= excerpt/flash/design/S15-30/P027B/b.png，机位在她身后），prompt 换成背影版"
                    "（她背对镜头朝出口楼梯走远、人群在身后两侧跟着、电脑合着背面朝内）；此前开拍前审查的改句随之作废；"
                    "n approval 与 sd-MO12-n-1/n-2 产物保留")
# SG06 p: both m takes failed the Gate; 「按页面重拍，唱段不转身 (Recommended)」 on gate/sg06
REPLACES["SG06"] = ("outputs/ai-city-takeover/ep01/v4/pilot/sd-SG06-m-1/preview-approval.json", GATE06,
                    "s016 重拍 p：m-1、m-2 两条 Gate 不通过（唱到 N 就松开听筒转身，首帧没给过她的背面，模型补了黑色挎包、把裙子画成短裤；"
                    "m-1 听筒自己挂回钩上）；唱段里不转身、不出画，最后一句改为「她仍站在原地看着镜头」；首帧、人声 SG06m、7 s 不变；"
                    "m approval 与 sd-SG06-m-1/m-2 产物保留")
INSERTS = {"s017b": "SG07", "s022b": "SG08", "s026b": "SG10", "s028b": "MO13"}   # cut from that unit's 4K take
# where the draft prompt and its chosen first frame disagree, or the lane needed a technical choice; the main session
# decides each one with the user (nothing here changed creative text)
KNOWN_ISSUES = [
    ("s016/s017/s018/s022/s025/s027/s028", "2026-11-22 主会话已按首帧状态改了 7 处动作句（s014 教训：prompt 从首帧的状态写起）；s028 泛光灯在 119.78 亮起改为后期调色（前段压暗、重音上恢复）。",
     "已改，见 excerpt/flash/s015-030-seedance.md。"),
    ("s024 SG09", "「镜头随车身轻轻晃动」：即梦管线的机位合同没有“晃动”这一类，按分镜「锁定，随车身轻晃」写成固定机位（相对车厢），"
     "spec 的稳定性与收束写明随车身轻晃。", "技术处理，不改 prompt。"),
    ("s026 SG10", "方案把 s026a 切点提前到 109.72（唱 I'm the reason），分镜原窗口从 110.543 起（不含 I'm the）。生成窗口起点已改到 109.7027 拍点，"
     "人声多 0.84 s、秒数 6→7（每条 +80）；分镜 s025/s026 的剪辑区间（plays 110.6199）未动。", "剪辑按方案还是按分镜切，由主会话定。"),
    ("s019/s020 MO09/MO10", "方案的 s019 84.02–87.70、s020 87.70–91.38 与分镜（84.02–88.62、88.62–92.76）不同；动作片段不送人声，按分镜窗口各生成 5 s，"
     "足够覆盖方案的 3.68 s。", "若按方案改分镜窗口为 4 s，每条可省 80 积分。"),
    ("s022 SG08 / s024 SG09", "人声窗口超出生成秒数：SG08 「real.」到 7.07 s、SG09 「Everybody,」到 5.25 s（窗口在那里截断）；spec 的口型结束时间取生成秒数（7.0 / 4.0 s）。"
     "SG08 窗口开头 0.05–0.57 s 是上一句的「instead.」，剪辑从 95.04（片内 0.53 s）起用。", "技术处理。"),
    ("s024 SG09 / s028 MO13", "2026-11-22 开拍前连续性检查（pilot/s015-030/issues/index.html）：s024 首帧的车厢和 s025/s026 对不上，"
     "重做后使用者选「用 b (Recommended)」（pilot/s015-030/p024r/index.html），首帧换成 p024-b2；s028 首帧是台阶下的中景、看不到跳板，"
     "使用者选「按问题页改 (Recommended)」，prompt 改为镜头固定、沿台阶往上走、半途低头看发光的寻呼机、从画面右上方走出。",
     "已改；SG09、MO13 的 approval 按这两条裁决重写，其余 unit 不变。"),
    ("s015 SG05", "n-1、n-2 两条 Gate 不通过（人声从句中 59.157 切入、7 s 无余量，“that's my cue”被截；n-1 开走的车红尾灯；左肩成块模糊）。"
     "使用者选「按页面重拍 (Recommended)」（pilot/s015-030/gate/sg05/index.html）：首帧不变；人声 58.70–65.666 s（SG05m.wav，含 Ten oh two）、"
     "生成 8 s（比窗口多 1 s 给模型的前奏）；prompt 加「街上只有停着的车，没有行驶的车。」；剪辑仍从 59.2341 用起。",
     "重拍 2 条，take 文件夹 sd-SG05-m-1|2；n 的 approval 与产物保留。"),
    ("s016/s017/s022/s024/s026/s029 SG06–SG11", "使用者选「照 s015 的教训改 (Recommended)」：人声窗口从各自那句的句首前约 0.3 s 起"
     "（SG06m 65.517、SG09m 102.64（前一词 guests. 到 102.64 结束，留 0.24 s）、SG10m 109.56、SG11m 125.608；SG07 原窗口已在句首前 0.50 s，"
     "SG08 的剪辑从 95.0393 起、落在 instead. 里，往前 0.3 s 又落在 apps 里，两条窗口不变），生成各多 1 s（SG09 窗口 4.543 s，主会话定生成 6 s 留满 1 s，上限 500）；"
     "剪辑区间与 prompt 不变。", "take 文件夹 sd-<UNIT>-m-1|2；n 的 approval 保留（未提交）。"),
    ("s027 MO12", "n 两条 Gate 不通过（朝镜头斜走、脚出画、标志与图形）。使用者选「A 重做背影首帧再拍 (Recommended)」，"
     "并在 pilot/s015-030/p027b/index.html 选「用 b (Recommended)」：首帧 p027-b3（机位在她身后），prompt 换成背影版。",
     "重拍 sd-MO12-p-1|2，4 s，每条上限 400。"),
    ("s019–s029（MO09、MO10、SG08、SG09、MO11、SG10、MO12、MO13、SG11）", "开拍前按 s014–s018 的教训再审一遍首帧和 prompt："
     "不写朝镜头走、出画；不转身露背面；道具物理和首帧一致；电脑、工牌、寻呼机屏幕写明空白没有标志。使用者选「照页面改 (Recommended)」"
     "（pilot/s015-030/audit/index.html），逐句照改；s027 另重做首帧（pilot/s015-030/p027r/index.html），认可后接入。",
     "prompt 已改；s027 首帧换成 p027-b2（P027R/a，「用 a (Recommended)」）。"),
    ("s016 INS16", "s016 剪辑改为 p-1 的 65.67–69.40 加一条新插镜：投币电话搁板下方的听筒在金属电话线上来回晃（69.40–71.18，Got half an answer），"
     "无人镜头。使用者在 pilot/s015-030/ins16/index.html 选「用 d 拍 (Recommended)」：首帧 p016-ins16（= design/S15-30/INS16/d.png），"
     "prompt 逐字取自 INS16/prompt.md；first_frame 4 s（使用者看到 3 s；即梦最短 4 s，主会话定 3→4 s；剪辑取所需长度）。",
     "take 文件夹 sd-INS16-n-1|2，每条上限 400。"),
    ("s016 SG06 / s017 SG07", "s016 m 两条 Gate 不通过（唱到一半松手转身，模型补出黑色挎包、裙变短裤）。使用者选「按页面重拍，唱段不转身 (Recommended)」"
     "（pilot/s015-030/gate/sg06/index.html）：s016 最后一句改为「她仍站在原地看着镜头」，重拍 sd-SG06-p-1|2；s017 结尾改为只「然后直起身」。"
     "离开画面交给剪辑。", "已改。"),
    ("s017 SG07", "首帧背景有一辆车尾朝镜头的浅色皮卡（动起来会亮红尾灯）。使用者在 pilot/s015-030/cars/index.html 选「用 b (Recommended)」："
     "首帧换成 p017-w2b（= excerpt/flash/design/S15-30/CARS/p017-w2b.png，只把皮卡改成车头朝镜头、不开灯）。s018 出租车是车头朝镜头，不改。",
     "已改；prompt 不变。"),
]


def plan_rows() -> dict:
    """Plan table rows (segment -> time, lyric, picture, why, prep), verbatim from the approved plan page."""
    rows = {}
    for cls, cells in re.findall(r'<tr><td class="(\w)">(.*?)</td></tr>', (REPO / PLAN).read_text(encoding="utf-8")):
        seg, *rest = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells.split("</td><td>")]
        rows[seg] = dict(zip(("time", "lyric", "picture", "why", "prep"), rest), kind=cls)
    return rows


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
    rows, drafts = plan_rows(), prompts()
    assert list(drafts) == UNITS, list(drafts)
    units = []
    for unit in UNITS:
        shot, prompt = drafts[unit]
        spec, clip = U.SPECS[unit], clips[unit]
        insert = "insert" in clip                  # an insert clip has its own plate, not its shot's
        assert clip["used_by"] == [shot] and (insert or shots[shot]["plate"] == clip["start_frame"]) and clip["start_frame"] == spec["plate"]
        frame = DESIGN + FRAMES[unit if insert else shot] + ".png"
        plate = U.PLATES + spec["plate"] + ".png"
        assert sha(frame) == sha(plate) == spec["plate_sha256"]
        secs = spec["duration"]
        row = {"shot": shot, "unit": unit, "clip": unit, "mode": spec["input_mode"], "look": spec["look"],
               "song_span_s": [shots[shot]["t0"], shots[shot]["t1"]],
               "generation_window_s": [clip["window"]["t0"], clip["window"]["t1"]],
               "first_frame": {"path": plate, "sha256": spec["plate_sha256"], "design_frame": frame},
               "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
               "required_phrases": [spec["image"][4], *spec["intent"]["open_event"], *spec["intent"]["close_event"],
                                    *spec["intent"]["natural"]],
               "seconds": secs, "resolution": "4k", "aspect": "16:9", "takes": TAKES,
               "est_cost_per_take_CRD": secs * RATE, "ceiling_per_take_CRD": ceiling(secs),
               "plan": {seg: rows[seg] for seg in rows if seg[:4] == shot}}
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
    stills = [{"shot": s, "plate": U.PLATES + shots[s]["plate"] + ".png", "sha256": sha(U.PLATES + shots[s]["plate"] + ".png"),
               "design_frame": DESIGN + FRAMES[s] + ".png" if s in FRAMES else None,
               "song_span_s": [shots[s]["t0"], shots[s]["t1"]], "plan": {k: v for k, v in rows.items() if k[:4] == s}}
              for s in STILLS]
    inserts = [{"segment": seg, "from_unit": unit, "plan": rows[seg]} for seg, unit in INSERTS.items()]
    est = sum(u["est_cost_per_take_CRD"] for u in units) * TAKES
    ceil_sum = sum(u["ceiling_per_take_CRD"] for u in units)
    return {"schema": "iris-v4-preview-inputs/s015-030-1", "range_s": [shots["s015"]["t0"], shots["s030"]["t1"]],
            "method": "Seedance 2.0 VIP 4k（使用者 2026-11-17：画质最高/积分随便用）",
            "director_plan": {"path": PLAN, "sha256": sha(PLAN)}, "first_frame_preview": {"path": PREVIEW, "sha256": sha(PREVIEW)},
            "source_prompt_file": PROMPTS, "source_prompt_file_sha256": sha(PROMPTS),
            "board": {"path": U.BOARD, "sha256": U.BOARD_SHA256},
            "plan": "每 unit 同一首帧拍 2 条，过逐镜 Gate 后挑一条；每条一次不重试",
            "cost_basis": f"4k 每秒 {RATE} 积分（开头实付口径）；单条上限 = 该价向上取整到百",
            "total_seconds_per_take_set": sum(u["seconds"] for u in units),
            "estimated_total_CRD": est, "ceiling_per_take_sum_CRD": ceil_sum, "ceiling_total_CRD": ceil_sum * TAKES,
            "previous_shot_first_frame": {"shot": "s014", "path": U.PLATES + shots["s014"]["plate"] + ".png",
                                          "sha256": sha(U.PLATES + shots["s014"]["plate"] + ".png")},
            "units": units, "stills": stills, "inserts": inserts,
            "known_issues": [{"where": w, "issue": i, "proposal": p} for w, i, p in KNOWN_ISSUES]}


def page(data: dict) -> str:
    up = lambda p: "../../../" + p.split("ep01/v4/", 1)[1]          # served from ep01/v4/
    esc = html.escape
    out = ['<!doctype html><meta charset="utf-8"><title>IRIS EP01 s015–s030 提交前预览包</title>',
           "<style>body{background:#0b0d12;color:#dfe6ee;font:15px/1.7 system-ui,sans-serif;margin:24px auto;max-width:1500px;"
           "padding:0 24px}.card{display:flex;gap:16px;border-bottom:1px solid #1b2230;padding:14px 0;align-items:flex-start}"
           ".im{flex:0 0 640px}.im img{width:640px;display:block}.th{flex:0 0 120px;font-size:12px;color:#7f8b97}"
           ".th img{width:120px;display:block}.tx{flex:1;min-width:0}h3{margin:0;font-size:16px;color:#f3d9a8}"
           ".pr{background:#11151c;padding:8px 12px;border-radius:6px}.n{color:#ff8a3d}.d{color:#7f8b97;font-size:13px}"
           ".pl{color:#9fb4c7;font-size:14px}audio{width:100%;margin:4px 0}table{border-collapse:collapse}"
           "td,th{border:1px solid #1b2230;padding:4px 8px;text-align:left}li{margin:6px 0}</style>",
           "<h1>IRIS EP01 s015–s030（59.23–134.44 s）· Seedance 2.0 VIP 4k 提交前预览包</h1>",
           f"<p>{len(data['units'])} 条生成（{sum(u['mode'] == 'multimodal' for u in data['units'])} 条唱段/念白用人声口型：首帧 + 人声；"
           f"{sum(u['mode'] == 'first_frame' for u in data['units'])} 条动作与插镜用首帧），每条同一首帧拍 {TAKES} 次、"
           f"每次不重试，过逐镜 Gate 后挑一条。按 4k 每秒 {RATE} 积分：每套 {data['total_seconds_per_take_set']} 秒，"
           f"<b>预计共 {data['estimated_total_CRD']:,} 积分</b>，<b>总上限 {data['ceiling_total_CRD']:,}</b>"
           f"（单条上限按价向上取整到百）。s021、s023、s030 是静图，s017b、s022b、s026b、s028b 从 4K 片子里裁，都不生成。"
           "认可后才提交。</p>"]
    prev = data["previous_shot_first_frame"]["path"]
    for u in data["units"]:
        plan = " ／ ".join(f"{seg} {r['time']}｜{r['lyric']}｜{r['picture']}｜为什么：{r['why']}" for seg, r in u["plan"].items())
        cost = (f"{u['seconds']} s · 4k · 16:9 · {u['mode']} · {u['takes']} 条 × 约 {u['est_cost_per_take_CRD']} 积分"
                f"（共 {u['est_cost_per_take_CRD'] * u['takes']}）· 单条上限 {u['ceiling_per_take_CRD']} · prompt sha {u['prompt_sha256'][:12]}…")
        out.append(f'<div class="card"><div class="th"><img src="{up(prev)}"><span>上一镜首帧</span></div>'
                   f'<div class="im"><img src="{up(u["first_frame"]["path"])}"><div class="d">'
                   f'{Path(u["first_frame"]["path"]).name} = {esc(u["first_frame"]["design_frame"].split("S15-30/")[1])}'
                   f' · sha {u["first_frame"]["sha256"][:12]}…</div></div><div class="tx">'
                   f'<h3>{u["shot"]} · {u["unit"]} · {u["mode"]} · 造型 {u["look"]} · 歌曲 {u["song_span_s"][0]:.2f}–{u["song_span_s"][1]:.2f} s</h3>'
                   f'<p class="pl">方案：{esc(plan)}</p>')
        if "vocal" in u:
            v = u["vocal"]
            out.append(f'<p class="n">人声窗口 {v["song_window_s"][0]}–{v["song_window_s"][1]} s（{v["seconds"]} s，'
                       f'口型 {v["dialogue_s"][0]}–{v["dialogue_s"][1]} s）：{esc(v["lyric_text"])}</p>'
                       f'<audio controls preload="none" src="{up(v["path"])}"></audio>')
        elif u["clip_words"]:
            out.append(f'<p class="d">该窗口歌词（仅参考，不上传人声）：{esc(" ".join(u["clip_words"]))}</p>')
        out.append(f'<p class="pr">{esc(u["prompt"])}</p><p class="d">{esc(cost)}</p></div></div>')
        prev = u["first_frame"]["path"]
    out.append("<h2>静图与插镜（不生成）</h2><table><tr><th>段</th><th>时间 s</th><th>来源</th><th>画面 / 为什么</th></tr>")
    for s in data["stills"]:
        for seg, r in s["plan"].items():
            out.append(f'<tr><td>{seg}</td><td>{r["time"]}</td><td><img src="{up(s["plate"])}" width="200"><br>'
                       f'{Path(s["plate"]).name}（静图）</td><td>{esc(r["picture"])}／{esc(r["why"])}</td></tr>')
    for i in data["inserts"]:
        r = i["plan"]
        out.append(f'<tr><td>{i["segment"]}</td><td>{r["time"]}</td><td>从 {i["from_unit"]} 的 4K 片子裁</td>'
                   f'<td>{esc(r["picture"])}／{esc(r["why"])}</td></tr>')
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
    spec, n, tag = U.SPECS[unit], unit.lower(), TAKE_TAG.get(unit, "n")
    replaces = REPLACES.get(unit)
    label = U.APPROVAL_ROLE[spec["input_mode"]]
    artifacts = [{"path": row["first_frame"]["path"], "sha256": row["first_frame"]["sha256"], "role": f"{unit} {label}"}]
    if "vocal" in row:
        artifacts.append({"path": row["vocal"]["path"], "sha256": row["vocal"]["sha256"], "role": f"{unit} vocal"})
    ceil_ = row["ceiling_per_take_CRD"]
    frame = Path(row["first_frame"]["path"]).name
    look = {"W1": "造型 W1", "B": "造型 B"}[spec["look"]] + ("（本镜从 W1 换成 B）" if unit == "MO09" else "")
    return {
        "schema": "iris-v4-preview-approval/1", "unit_group": f"v4-s015-030-{unit}-{tag}-1",
        "question": f"<主会话问使用者的原问题，逐字（审看页 {replaces[1] if replaces and replaces[1] else PAGE}）>",
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
                                 f"画面里没有人物（{frame}，与 {row['first_frame']['design_frame']} 逐字节相同），不涉及身份",
        "bound_ids": {"attempt_id": f"iris-{n}-{tag}-1-source-001", "policy_id": f"iris-{n}-{tag}-1-source-001",
                      "reservation_id": f"iris-{n}-{tag}-1-reservation-001"},
        "takes": {"approval": "one approval, two takes per unit from the same first frame; the best one is picked after both Gates",
                  "folders": [f"sd-{unit}-{tag}-1", f"sd-{unit}-{tag}-2"], "generations_per_take": 1, "total_generations": 2,
                  "total_ceiling_CRD": ceil_ * 2, "this_take": f"sd-{unit}-{tag}-1"},
        **({"replaces_approval": {"path": replaces[0], "sha256": sha(replaces[0]), "reason": replaces[2]}} if replaces else {}),
        **({"decision_notes": NOTES[unit]} if unit in NOTES else {}),
        "_template_notes": [
            f"本文件是 {tag}-1 的模板；写成 pilot/sd-{unit}-{tag}-1/preview-approval.json 前删除本 _template_notes 字段并填好 question / "
            "user_quote / approved_at 三个占位。prompt 若按「已知问题」改过，先改 s015-030-seedance.md、unit.py spec 与本页并重建，再写 approval。",
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
    print(json.dumps({"page": PAGE, "page_sha256": page_sha, "inputs": INPUTS, "inputs_sha256": inputs_sha,
                      "units": len(data["units"]), "seconds_per_set": data["total_seconds_per_take_set"],
                      "estimated_total_CRD": data["estimated_total_CRD"], "ceiling_total_CRD": data["ceiling_total_CRD"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
