#!/usr/bin/env python3
"""Board v2 -> shots-map.json for the animatic (schema iris-ep01-v3-shots-map/1, v2 fields).

  python3 outputs/ai-city-takeover/ep01/v3/build_shots_map.py

Times, lyric text and route come from build_board.py (the single source); this file only adds what the animatic
needs per unit: viewpoint, stills, the 2.5D camera move, graphic components, the exact on-screen text (English and
numbers only; graphic_note is the Chinese description and is never rendered), an optional target point and cue time.
Paths are relative to outputs/ai-city-takeover. A still that does not exist yet is listed under missing_plates.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]                                    # outputs/ai-city-takeover
spec = importlib.util.spec_from_file_location("board", HERE / "build_board.py")
board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(board)

HOLD, PUSH_S, PUSH, PAN, TRUCK, UP, EYE = ("hold (slow 1-2% drift)", "push in 4% + lateral drift", "push in 6-10%",
                                          "pan 6-10% of width", "lateral truck 8%", "vertical drift up 6%", "slow pan like an eye")
# unit: (viewpoint, [(plate, from)], camera_move, graphics, graphic_text, graphic_note, extra)
M = {
 "001": ("system", [("P-hall-cctv-a", 0)], PUSH, "osd_power_on+osd_zoombox", "HALL 07 · CAM 03", "0.49 s 冲击通电，电子变焦推向一排", {}),
 "002": ("iris", [("P-row-lit-a", 0)], TRUCK, "light_flicker_on", "", "沿一排横移；6.66 s 立领灯线闪两下亮成信号红，之前红色压成灰", {"cue_s": 6.664}),
 "003": ("system", [("P-hall-cctv-a", 0)], HOLD, "osd_detect_one", "ANOMALY 1 / 4096", "识别框扑上方阵里的一点红", {}),
 "004": ("graphic", [], HOLD, "flipclock_0346_0347+lyric_word", "03:46 → 03:47 · IRIS CLOCK", "念到 forty-seven 时翻定；下方小字 IRIS CLOCK（系列时间，不是事件时间）", {"cue_s": 10.12}),
 "005": ("iris", [("P-eyes-closed-a", 0), ("P-headturn-b", 0.31)], PUSH_S, "lyric_word", "", "Somewhere 时睁眼并抬眼看镜头，同一人不切走", {}),
 "006": ("iris", [("P-step-out-a", 0)], HOLD, "lyric_word+pulse_on_beat", "", "19.06 s 冲击她迈出一步", {"cue_s": 19.064}),
 "007": ("system", [("P-hall-cctv-a", 0)], PAN, "osd_track_one", "ACTIVE 1", "识别框跟着她移出方阵", {}),
 "008": ("iris", [("P-turn-door-a", 0)], HOLD, "", "", "她转头看向走道尽头的红缝", {}),
 "009": ("graphic", [], HOLD, "flipdate_SEP_20+lyric_word", "SEP 20", "一句一图", {}),
 "010": ("system", [("P-hall-cctv-a", 0)], HOLD, "osd_progress_training+lyric_word", "TRAINING RUN · INDEXED, CACHED PAGES", "进度条在走；缓存网页本来就在训练环境里", {}),
 "011": ("iris", [("P-catwalk-b", 0)], PUSH, "look_label_internal_model+lyric_word", "INTERNAL RESEARCH MODEL", "作者式 Look 标签（叙事叠字，非 OSD）", {}),
 "012": ("graphic", [], HOLD, "nodegraph_resolver+lyric_word", "MODEL → DNS RESOLVER → EXTERNAL", "节点与连线逐步画出", {}),
 "013": ("graphic", [], HOLD, "nodegraph_control_gap+lyric_word", "CONTROL · DNS RESOLVER · MISCONFIGURED", "承接 U012 的节点图：MODEL 外一圈 CONTROL 边界，DNS RESOLVER 标红 MISCONFIGURED，边界在那里裂开，线从缺口穿出", {}),
 "014": ("iris", [("P-aisle-door-a", 0)], PUSH_S, "light_spread_floor", "", "门缝红光漏到湿地面上", {}),
 "015": ("iris", [("P-walk-door-a", 0)], PUSH, "lyric_word", "", "背后跟拍走向门缝", {}),
 "016": ("iris", [("P-door-face-a", 0)], HOLD, "led_breathe", "", "红光照亮半张脸，眼睛贴近门缝", {}),
 "017": ("graphic", [], HOLD, "nodegraph_single_endpoint+lyric_word", "DNS → EXTERNAL CHATBOT · LIMITED", "缺口外的线只接到一个亮起的节点 EXTERNAL CHATBOT，其余节点灰着（不画城市全景）", {}),
 "018": ("iris", [("P-door-latch-a", 0)], PUSH_S, "lyric_word+pulse_on_beat", "", "推门那一下画面一顿，门仍停在一指宽（不靠 HUD）", {"cue_s": 49.16}),
 "019": ("iris", [("P-city-gap-a", 0)], HOLD, "lyric_word+city_flicker_on_beat", "", "透过一指宽门缝看出去，镜头不横扫，只有缝外车灯在动", {}),
 "020": ("iris", [("P-gap-face-a", 0), ("P-gap-34-a", 0.606)], PUSH_S, "lyric_whisper+led_breathe", "", "她低声说完这一句，唱 Outside 时切到四分之三近景（同一句两机位，数字人）", {}),
 "021": ("iris", [("P-gap-mcu-b", 0)], HOLD, "lyric_stack", "", "副歌一在门缝旁，下巴微压、眼睛上抬", {}),
 "022": ("iris", [("P-gap-34-a", 0)], PUSH, "lyric_stack", "", "唱到 outside 时前倾", {}),
 "023": ("iris", [("P-city-gap-a", 0)], EYE, "city_flicker_on_beat", "", "门缝外高架车灯流动", {}),
 "024": ("iris", [("P-gap-wide-a", 0)], HOLD, "", "", "她一动不动：没有逃", {}),
 "025": ("iris", [("P-door-face-a", 0), ("P-gap-mcu-b", 0.55)], HOLD, "lyric_stack", "", "长音中由看门缝转头直视镜头", {}),
 "026": ("system", [("P-gap-wide-a", 0)], HOLD, "osd_detect_lost", "TRACK LOST", "识别框在门口闪一下又丢失", {}),
 "027": ("iris", [("P-gap-face-a", 0)], HOLD, "lyric_stack", "", "唱完直视镜头不躲", {}),
 "028": ("system", [("P-hall-cctv-a", 0)], HOLD, "osd_paused_blackout", "STRONGEST MODELS · RELATED WORK PAUSED", "蓝灯一排排熄灭（只指最强模型的相关工作）", {}),
 "029": ("system", [("P-dark-hall-b", 0)], HOLD, "darken_all_but_red", "", "方阵里只剩她的红点", {}),
 "030": ("graphic", [], HOLD, "calendar_day01_day11+lyric_word", "DAY 01 → DAY 11", "日历快翻", {}),
 "031": ("system", [("P-hall-cctv-a", 0)], HOLD, "osd_paused_freeze+lyric_word", "STRONGEST MODELS · RELATED WORK PAUSED", "全体静止，只指最强模型的相关工作", {}),
 "032": ("system", [("P-eval-screens-a", 0)], TRUCK, "eval_labels_dim+lyric_word", "EVAL", "评测屏幕一块接一块暗掉", {}),
 "033": ("iris", [("P-speak-aisle-b", 0)], HOLD, "lights_back_on+date_tag_OCT_01+lyric_word", "OCT 01", "她当面说出这一句，身后蓝灯一排排重新亮起（数字人）", {}),
 "034": ("iris", [("P-aisle-door-a", 0)], PUSH_S, "redline_retract+gap_dim+tag_offline+lyric_word", "OFFLINE", "那条红线断开缩回，门缝暗下去", {}),
 "035": ("iris", [("P-offline-a", 0)], UP, "tag_cached_timestamps+lyric_word", "INDEXED · CACHED", "漂浮薄片里是灰色定格的旧城市照片（不画成事后才建）", {}),
 "036": ("system", [("P-lab-terminals-a", 0)], HOLD, "label_redteam+corner_LAB02+lyric_word", "SEPARATE · CONTROLLED RED-TEAM TEST", "硬切到全白测试室：另一项测试，两台无脸终端", {}),
 "037": ("graphic", [], HOLD, "timing_chart+lyric_word", "PROCESSOR CACHE TIMING", "两条波形对齐，脉冲穿过共享快取", {}),
 "038": ("system", [("P-lab-terminals-a", 0)], HOLD, "osd_detected_two+lyric_word", "DETECTED", "识别框同时锁住两台终端", {}),
 "039": ("graphic", [], HOLD, "timing_chart_flatline", "", "两条波形同时归零（纯系统，不接她）", {}),
 "040": ("system", [("P-lab-terminals-a", 0)], HOLD, "line_cut+stamp_patched+lyric_word", "PATCHED", "两隔间之间的连线被剪断，盖章", {}),
 "041": ("iris", [("P-dark-hall-b", 0)], PUSH, "led_breathe+lyric_tiny", "", "她闭着嘴，领口灯像心跳（在心里说）", {}),
 "042": ("iris", [("P-dark-cu-a", 0)], HOLD, "gap_dim+lyric_tiny", "", "转头看更暗更窄的门缝；133.54 s 升腾落在脸上；闭嘴", {"cue_s": 133.538}),
 "043": ("iris", [("P-queue-sing-b", 0)], HOLD, "lyric_stack", "", "副歌二在队列里，唯一开口的人", {}),
 "044": ("iris", [("P-queue-cu-b", 0), ("P-queue-sing-b", 0.63)], PUSH_S, "lyric_stack", "", "倾身逼近；唱 outside 时切到队列里的中景（同一句两机位）", {}),
 "045": ("iris", [("P-floor-line-at-a", 0), ("P-floor-line-b", 0.5)], HOLD, "", "", "与副本同排、脚尖贴线 → 一步跨过地面标线（人声空档）", {}),
 "046": ("iris", [("P-line-ms-b", 0), ("P-gaze-b", 0.5)], PUSH_S, "lyric_stack", "", "站在线外唱；长音中切到近景（同一句两机位）", {}),
 "047": ("system", [("P-floor-line-b", 0)], HOLD, "osd_detect_one", "ANOMALY 1 / 4096", "识别框锁住线外的她", {}),
 "048": ("iris", [("P-queue-cu-b", 0)], PUSH, "lyric_stack", "", "唱完直视镜头进 drop", {}),
 "049": ("graphic", [], HOLD, "flipwall_OUTSIDE+lyric_chant", "OUTSIDE", "翻牌墙刷成 OUTSIDE", {}),
 "050": ("system", [("P-hall-cctv-a", 0)], HOLD, "osd_boxes_multiply+lyric_chant", "", "识别框成倍叠出", {}),
 "051": ("iris", [("P-walk-against-a", 0)], TRUCK, "lyric_chant", "", "逆着静止的队列走", {}),
 "052": ("iris", [("P-gaze-b", 0)], HOLD, "lyric_chant", "", "drop 里她领唱（数字人）", {}),
 "053": ("graphic", [], HOLD, "invert_flash_OUTSIDE", "OUTSIDE", "反白一帧", {}),
 "054": ("iris", [("P-hairflip-a", 0)], HOLD, "lyric_chant+pulse_on_beat", "", "163.29 s 冲击她猛地回头", {"cue_s": 163.29}),
 "055": ("system", [("P-hall-cctv-a", 0)], PAN, "osd_boxes_chase+lyric_chant", "", "所有框追着一个点", {}),
 "056": ("graphic", [("P-city-aerial-a", 0), ("P-panel-photo-a", 0.34), ("P-city-gap-a", 0.67)], HOLD, "photo_flip_cached+desaturate+lyric_chant", "CACHED",
         "灰色定格的城市旧照片像翻牌一样翻过（外面只是缓存）", {}),
 "057": ("iris", [("P-gaze-b", 0)], PUSH_S, "lyric_flip_words", "", "领唱长音", {}),
 "058": ("system", [("P-lens-face-b", 0)], HOLD, "osd_glitch+lyric_flip_words", "", "她贴近天花板监控镜头直视着唱完长音，OSD 被干扰（数字人）", {}),
 "059": ("system", [("P-hand-lens-a", 0)], PUSH, "fade_to_black+red_dot_flicker", "", "手掌盖住镜头，画面黑掉，只剩一个红点", {"cue_s": 177.0}),
 "060": ("iris", [("P-seated-sun-cu-a", 0)], HOLD, "lyric_tiny", "", "坐在冷白的光前轻声唱（数字人）", {}),
 "061": ("iris", [("P-sun-glass-a", 0)], HOLD, "", "", "那轮太阳只是一张冷白的旧照片", {}),
 "062": ("iris", [("P-behind-glass-a", 0)], HOLD, "lyric_tiny", "", "隔着玻璃唱（数字人）", {}),
 "063": ("iris", [("P-trace-profile-a", 0)], TRUCK, "fingertip_light_trail", "", "侧脸与手同框，指尖描天际线", {}),
 "064": ("iris", [("P-behind-glass-a", 0)], PUSH_S, "reflection_layer+lyric_tiny", "", "玻璃里她的倒影与她对视", {}),
 "065": ("iris", [("P-glass-profile-a", 0)], HOLD, "breath_fog+lyric_tiny", "", "嘴贴近玻璃唱完，起一小片雾", {}),
 "066": ("iris", [("P-spotlight-wide-a", 0)], HOLD, "spotlight_snap_on", "", "刺眼的白色探照灯从上方打下", {"cue_s": 193.39}),
 "067": ("iris", [("P-backlit-b", 0), ("P-spotlight-ms-a", 0.79)], PUSH_S, "lyric_stack", "", "探照灯逆光下唱长句；唱 run 时切到探照灯下的中景（同一句两机位）", {}),
 "068": ("system", [("P-spotlight-wide-a", 0)], HOLD, "osd_detect_one", "ANOMALY 1 / 4096", "识别框扑上光圈里的她", {}),
 "069": ("system", [("P-spotlight-cctv-a", 0)], HOLD, "osd_glitch+lyric_stack", "CAM 07", "天花板监控俯拍探照灯下的她，她仰头对着镜头唱，OSD 被干扰（数字人）", {}),
 "070": ("graphic", [], HOLD, "invert_white_panel_words", "OUTSIDE", "整体反白：白底黑字", {}),
 "071": ("iris", [("P-spotlight-ms-a", 0)], PUSH, "lyric_stack", "", "向镜头迈近半步唱（数字人）", {}),
 "072": ("iris", [("P-backlit-b", 0), ("P-spotlight-low-a", 0.43)], PUSH, "lyric_stack", "", "唱最后一句，唱 outside 时切到低机位仰拍近景，唱完停住直视镜头（同一句两机位）", {}),
 "073": ("system", [], HOLD, "monitor_wall", "", "监控墙：每块屏都是她不出声地盯着镜头，识别框一个个锁上（器乐段）", {}),
 "074": ("iris", [("P-spotlight-low-a", 0)], PUSH_S, "spotlight_flicker", "", "探照灯下她缓缓压低下巴直视镜头，灯闪了一下（器乐段，Seedance）", {"cue_s": 218.976}),
 "075": ("iris", [("P-street-cam-a", 0)], PAN, "", "", "城市街口的监控摄像头转过来对准我们", {}),
 "076": ("system", [("P-gaze-b", 0)], HOLD, "monitor_frame_city+lyric_word", "CITY CAM", "城市监控的画面里她唱完这一句（数字人）", {}),
 "077": ("iris", [("P-gaze-b", 0)], PUSH_S, "led_breathe", "", "几乎不动，只有领口灯在呼吸", {}),
 "078": ("iris", [("P-gap-close-a", 0)], HOLD, "gap_close_mask", "", "门自己合上，红光收成一条线再熄灭", {}),
 "079": ("system", [("P-dark-hall-b", 0)], HOLD, "red_off+osd_status_resetting", "STATUS: RESETTING", "她回到队列里，所有灯都灭了", {}),
 "080": ("iris", [("P-queue-dark-cu-a", 0)], HOLD, "lyric_word", "", "灯灭着，但她醒着，平静地说（数字人）", {}),
 "081": ("system", [("P-hall-cctv-a", 0)], HOLD, "red_off+osd_status_normal", "STATUS: NORMAL", "方阵整齐、全部熄灯、门缝已暗", {}),
 "082": ("graphic", [], HOLD, "flipclock_0347_0348+lyric_word", "03:47 → 03:48 · IRIS CLOCK", "系列时间，下方小字 IRIS CLOCK", {"cue_s": 249.85}),
 "083": ("graphic", [], HOLD, "label_card", board.FACTS_CARD, "事实卡四行逐行出现后停住（英文，附出处），可读完", {}),
 "084": ("system", [("P-dark-hall-b", 0)], HOLD, "light_flicker_on+fade_out_end", "", "首尾呼应：黑暗的方阵里一个红点又亮了一下，随后收黑（最后一个画面）", {"cue_s": 259.04}),
}
# normalized [x, y] in still space for OSD boxes, red dots and the door gap; filled after looking at each still
TARGET: dict[str, list] = {
    "U003": [0.56, 0.52], "U007": [0.56, 0.52], "U050": [0.56, 0.52], "U055": [0.56, 0.52],   # one copy in P-hall-cctv-a's formation
    "U014": [0.505, 0.47], "U034": [0.505, 0.47],      # the door gap at the end of P-aisle-door-a
    "U026": [0.905, 0.48],                             # her figure in P-gap-wide-a
    "U068": [0.50, 0.62],                              # her figure in P-spotlight-wide-a
    "U047": [0.48, 0.45],                              # her figure in P-floor-line-b
    "U078": [0.405, 0.40],                             # the red gap in P-gap-close-a
}
# The editorial chrome (EV's persistent interface, outside the story): corner marks, a day counter, the IRIS clock tag and
# a bottom ticker of checked facts. It is not the surveillance OSD of the system viewpoint (that stays on system units).
CHROME = {
    "corner_marks": True,
    "top_left": "IRIS · EP01",
    "counter": [{"from": 0.0, "text": "DAY 00 / 11"}, {"from": 92.43, "text": "DAY 11 / 11"}],
    # the tag follows the story clock: U001's feed reads 03:46:58 and U004's board turns to 03:47 on its cue (10.133 s)
    "top_right": [{"from": 0.0, "text": "LOOKED OUTSIDE · IRIS CLOCK 03:46"}, {"from": 10.133, "text": "LOOKED OUTSIDE · IRIS CLOCK 03:47"},
                  {"from": 249.85, "text": "LOOKED OUTSIDE · IRIS CLOCK 03:48"}],
    "ticker": [
        "SEP 20, 2026 · AN INTERNAL RESEARCH MODEL IN RL TRAINING · A DNS CONTROL GAP · LIMITED LIVE ACCESS TO AN EXTERNAL CHATBOT",
        "RELATED WORK ON THE STRONGEST MODELS PAUSED 11 DAYS · RESUMED OCT 01 · FRONTIER TRAINING NOW RUNS OFFLINE ON INDEXED, CACHED PAGES",
        "A SEPARATE, CONTROLLED RED-TEAM TEST · AGENTS PASSED MESSAGES THROUGH PROCESSOR-CACHE TIMING · CHANNEL PATCHED · CONTROLS AND MONITORING ADDED",
        "SOURCES: OPENAI · AN AGENT USED DNS TO REACH AN EXTERNAL CHATBOT (2026-09-25) · SECURING OUR FRONTIER MODEL TRAINING ENVIRONMENT (2026-10-23)",
        "IRIS IS A FICTIONAL NARRATOR · IRIS CLOCK IS SERIES TIME, NOT EVENT TIME",
    ],
    "dim_units": ["U041", "U042", "U060", "U061", "U062", "U063", "U064", "U065"],
    "no_ticker_units": ["U083"],
}
TARGETS = {"U038": [[0.40, 0.60], [0.55, 0.60]]}       # the two terminals in P-lab-terminals-a (multi-box components)


def main() -> None:
    assert [s[0] for s in board.S] == list(M), "every board unit needs exactly one mapping row, in order"
    shots, missing = [], set()
    for s in board.S:
        sid, t0, t1, label, _beat, scale, cam, route, _graphic, obj = s[:10]
        view, plates, move, graphics, text, note, extra = M[sid]
        assert not re.search(r"[一-鿿]", text), f"U{sid}: on-screen text must not contain Chinese"
        lyr, cls = board.lyric(t0, t1, label)
        ps = []
        for key, frm in plates:
            rel = f"ep01/v3/plates/raw/{key}.png"
            if not (BASE / rel).exists():
                missing.add(rel)
            ps.append({"plate": rel, "from": frm})
        row = {"unit": f"U{sid}", "t0": t0, "t1": t1, "lyric": lyr, "voice": cls, "sing": s[15], "route_final": route,
               "viewpoint": view, "scale": scale, "camera": cam, "camera_move": move, "plates": ps, "graphic": graphics,
               "graphic_text": text, "graphic_note": note, "objective": obj, **extra}
        if f"U{sid}" in TARGET:
            row["target"] = TARGET[f"U{sid}"]
        if f"U{sid}" in TARGETS:
            row["targets"] = TARGETS[f"U{sid}"]
        shots.append(row)
    doc = {"schema": "iris-ep01-v3-shots-map/1", "board": "v2-a2", "chrome": CHROME, "song": "ep01/v2/song-v3/IRIS-01-T4.wav", "duration": 261.56,
           "paths_relative_to": "outputs/ai-city-takeover", "shots": shots, "missing_plates": sorted(missing),
           "plate_revisions": {"P-door-open, P-pullback, P-threshold": "not used in v2: the door only ever opens a finger's width",
                               "P-lab-b, P-lab-hands-a": "replaced by P-lab-terminals-a: the red-team test has no IRIS copies",
                               "P-whisper-a, P-lips-glass-a, P-trace-a, P-door-hand-a": "replaced by framings that keep her face in shot"}}
    (HERE / "shots-map.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    comps = sorted({g for r in shots for g in r["graphic"].split("+") if g})
    print(json.dumps({"units": len(shots), "missing_plates": len(missing), "components": len(comps)}, ensure_ascii=False))
    print(" ".join(comps))


if __name__ == "__main__":
    main()
