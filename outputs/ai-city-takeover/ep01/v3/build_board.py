#!/usr/bin/env python3
"""Full-film board v2 for IRIS EP01 "Looked Outside" (Suno T4, 261.56 s) -> board-table.md + director-coverage.json (schema v4).

  python3 outputs/ai-city-takeover/ep01/v3/build_board.py
  python .agents/skills/open-video/scripts/validate_director_coverage.py outputs/ai-city-takeover/ep01/v3/director-coverage.json

v2 revises the merged v1 (build_board_v1.py) after the independent concept check (verdict REVISE): every lead sung line is on
her mouth (digital human), cuts follow the CTC word timing (song-v3/timing/words.json), the "outside" is frozen after the
pause (no escalating access), the red-team test is a separate place with faceless terminals, each chorus has its own place
and a physical progression, and isolated body-part inserts are gone. Times are edit targets on the T4 grid.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

# verbatim user quotes that still apply (logs/decisions.md); the coverage cites them exactly
USER = [
    "我们只需要让人物真的表现在唱歌就好",
    "画面信息不够密, 故事内容太薄, 人物镜头太少太单调, captipon做的字体不行,参考作者,还有这个中文你直接不要了吧",
    "最后成片用即梦生成的我要1080p的,那个左上角的ai生成可以去掉的,我发现",
    "图片很奇怪,为什么突然晃一个眼睛过去",
    "睁眼之后突然转到这个人也非常奇怪",
    "这里又跳会又显得很突兀",
    "这种歌都是要带点不寻常,侵略性,不羁",
    "表情别太刻意了",
    "我都觉得可以,不考虑时常,你得从观众和质量角度考虑,和人物背景符合",
    "歌我选择好了t4",
    "可以，往下做",
]
EVIDENCE = "\n".join(USER)
EV_HASH = hashlib.sha256(EVIDENCE.encode("utf-8")).hexdigest()

CONSTRAINTS = [
    ("C-SING", "beat_specific", "我们只需要让人物真的表现在唱歌就好"),
    ("C-DENSE", "global", "画面信息不够密"),
    ("C-STORY", "global", "故事内容太薄"),
    ("C-MONO", "global", "人物镜头太少太单调"),
    ("C-FONT", "global", "captipon做的字体不行,参考作者"),
    ("C-NOZH", "global", "这个中文你直接不要了吧"),
    ("C-1080", "global", "最后成片用即梦生成的我要1080p的,那个左上角的ai生成可以去掉的"),
    ("C-NOEYE", "global", "为什么突然晃一个眼睛过去"),
    ("C-EYEJUMP", "global", "睁眼之后突然转到这个人也非常奇怪"),
    ("C-NOJUMP", "global", "这里又跳会又显得很突兀"),
    ("C-VIBE", "global", "这种歌都是要带点不寻常,侵略性,不羁"),
    ("C-NATURAL", "global", "表情别太刻意了"),
    ("C-FIT", "global", "和人物背景符合"),
]
GLOBAL = [c[0] for c in CONSTRAINTS if c[1] == "global"]

# the lyric column is generated from the CTC word timing, never typed by hand (v1 lost sync that way)
LINES = json.loads((ROOT / "outputs/ai-city-takeover/ep01/v2/song-v3/timing/words.json").read_text())["lines"]


def vocal_class(line: dict) -> str:
    """lead = must be on her mouth; vo = report-style voice-over; inside = Pre 2, mouth closed by design; chant = Drop group chant."""
    if line["en"] == "October first, the work resumed.":
        return "lead"                                   # said to camera as the lights come back (U033)
    if line["section"] in ("Intro", "Verse 1", "Verse 2") or line["en"] == "Three forty-eight.":
        return "vo"
    if line["section"] == "Pre-Chorus" and line["start"] > 120:
        return "inside"
    if line["section"] == "Drop" and line["en"].startswith("Outside"):
        return "chant"
    return "lead"


def words_in(t0: float, t1: float) -> list[tuple[dict, dict]]:
    return [(ln, w) for ln in LINES for w in ln["words"] if t0 <= (w["start"] + w["end"]) / 2 < t1]


# U084, wording kept inside ep01/fact-check.md (03:47/03:48 are series time and stay off this card)
FACTS_CARD = "\n".join([
    "SEP 20, 2026 — A DNS CONTROL GAP GAVE AN INTERNAL RESEARCH MODEL LIMITED ACCESS TO AN EXTERNAL CHATBOT.",
    "RELATED WORK ON THE STRONGEST MODELS PAUSED 11 DAYS · RESUMED OCT 01 · FRONTIER TRAINING NOW RUNS OFFLINE.",
    "A SEPARATE RED-TEAM TEST FOUND A CACHE-TIMING CHANNEL · PATCHED · CONTROLS AND MONITORING ADDED.",
    "SOURCES: OPENAI · 2026-09-25 · 2026-10-23",
])

S = []
def shot(*a, sing=False):
    S.append(a + (sing,))

# (id, t0, t1, lyric, beat, scale, camera, route, graphic, objective, open, close, visible_change, camera_intent, cut_reason)
# ---- Cold open 0.00-9.76: learn the rule "light on = awake"
shot("001", 0.00, 4.20, "（器乐）", "establish", "extreme_wide", "push_in", "HY", "OSD HALL 07 · CAM 03 · 03:46:58；电子变焦框",
     "立规则：被看管的副本大厅", "黑场", "监控大全景：几百个同款银发副本成方阵、领口灯全灭，走道尽头一扇门留着一丝红缝；电子变焦推向一排",
     "0.49 s 冲击画面通电，随即变焦推近", "监控固定机位的电子变焦＝系统在看", "变焦推到一排")
shot("002", 4.20, 7.92, "（器乐，6.66 s 落点）", "reveal", "medium", "truck", "PL", "—",
     "异常在画面里发生（不是孤立插入）", "沿一排闭眼副本横移", "移到其中一人时焦点拉到她的立领，6.66 s 灯线闪两下亮成信号红",
     "连续横移＋拉焦，灯由灭到亮", "横移带出关系，再拉焦到灯", "灯亮稳")
shot("003", 7.92, 9.76, "（器乐）", "reaction", "extreme_wide", "static", "HY", "识别框锁定 · ANOMALY 1 / 4096",
     "系统看见了", "方阵全景里一点红", "识别框扑上去锁定", "红点被框住", "回到监控机位", "进人声")
# ---- Intro 9.76-26.61
shot("004", 9.76, 13.48, "Three forty-seven.", "establish", "full", "static", "GR", "翻牌 03:46→03:47，下方小字 IRIS CLOCK（系列时间，非事实）",
     "念白给时间，画面同时给时间", "翻牌 03:46", "翻到 03:47", "翻牌落定", "作者式翻牌字阵", "念完")
shot("005", 13.48, 17.19, "Somewhere,", "reveal", "close_up", "push_in", "SD", "逐词小字幕",
     "「one of us」就是刚才亮灯的她", "队列里的她闭着眼，两侧副本虚化，领口红线亮", "14.6 s 重音她睁开冰灰色的眼，慢慢抬眼看向镜头",
     "闭眼→睁眼→抬眼", "极慢推近，同一人不切走", "目光到镜头")
shot("006", 17.19, 20.94, "one of us woke up.", "decision", "medium", "static", "SD", "逐词小字幕",
     "唯一在动的人", "她站在队列里", "19.06 s 冲击她向前迈出一步，身边副本一动不动", "一步出列", "正面略低机位接上一镜的视线", "脚落地")
shot("007", 20.94, 24.73, "（尾音）", "reaction", "extreme_wide", "tracking", "HY", "ACTIVE 1 · 轨迹线",
     "系统确认她在动", "监控俯拍方阵", "识别框跟着她移出方阵", "框随一个点离开网格", "监控云台跟随", "框停")
shot("008", 24.73, 26.61, "（器乐）", "decision", "medium", "static", "PL", "—",
     "她要去哪里：那扇门", "她站在方阵外", "她转头看向走道尽头那道红缝", "转头＝注意力交给门", "中景，视线引出下一段", "段首")
# ---- Verse 1 26.61-54.69 (one fact, one image)
shot("009", 26.61, 28.49, "September twenty.", "establish", "full", "static", "GR", "翻牌 SEP 20",
     "事实：日期", "翻牌转动", "落到 SEP 20", "日期翻定", "纯图形", "一句一图")
shot("010", 28.49, 30.37, "A training run.", "detail", "wide", "static", "HY", "TRAINING RUN 标签＋进度条＋小字 INDEXED, CACHED PAGES（缓存九月已在，不画成事后才建）",
     "事实：训练中（训练环境本来就用缓存网页）", "监控中景", "方阵上方进度条在走", "进度推进", "系统视点", "一句一图")
shot("011", 30.37, 34.13, "An internal research model.", "establish", "full", "tracking", "HY", "Look 标签 INTERNAL RESEARCH MODEL（叙事叠字，非 OSD）",
     "她是谁（作者式 Look 标签）", "走道深处的她", "朝镜头走近，下巴微压、眼睛上抬，两侧副本静立", "她逼近", "正面后退跟拍＝走秀", "标签落定")
shot("012", 34.13, 36.50, "One D N S resolver,", "detail", "full", "static", "GR", "节点图 MODEL → DNS RESOLVER → EXTERNAL（英文）",
     "事实：机制", "空白", "节点与连线画出", "图逐步画完", "纯图形", "线转红")
shot("013", 36.50, 38.06, "misconfigured —", "escalate", "full", "static", "GR", "节点图：MODEL 外一圈 CONTROL 边界，DNS RESOLVER 标 MISCONFIGURED，边界在那里裂开一个缺口",
     "配置错误＝控制缺口（不是物理故障）", "节点图：MODEL 被一圈 CONTROL 边界围住", "DNS RESOLVER 标红 MISCONFIGURED，边界在那里裂开缺口，线从缺口穿出",
     "边界出现缺口", "纯图形，承接上一镜的节点图", "门")
shot("014", 38.06, 41.57, "（尾音）", "reveal", "extreme_wide", "static", "PL", "—",
     "门先出现再被念出来", "走道尽头", "那扇门开着一丝缝，红光漏到湿地面上", "门缝亮", "大全景定位门", "下一句念门")
shot("015", 41.57, 44.10, "one door, left open.", "decision", "medium", "tracking", "SD", "逐词小字幕",
     "门＝她的目标", "她的背影在走道中", "走到门缝前，红光一点点照上侧脸", "走近门缝", "背后跟拍", "抵达")
shot("016", 44.10, 46.12, "（过门）", "reaction", "close_up", "static", "SD", "—",
     "她停在门口", "红光照亮半张脸与立领红线", "她的眼睛贴近缝里看", "视线进门缝", "近景定住", "红线出城")
shot("017", 46.12, 48.96, "It reached the internet.", "reveal", "full", "static", "GR", "路径图：从缺口出去的线只接到一个节点 EXTERNAL CHATBOT，其余节点灰着；小字 LIMITED",
     "连上了，但只到一个外部 chatbot（有限）", "缺口外的一条线", "线延伸到唯一亮起的节点 EXTERNAL CHATBOT，其余节点仍是灰的", "只接通一个点",
     "纯图形，路径清楚终止（不画城市全景，避免读成自由浏览）", "手")
shot("018", 48.96, 51.08, "The access was limited.", "detail", "medium", "static", "PL", "—",
     "有限＝门被短插销卡住，只开一指宽（不靠 HUD）", "中景：她的手按在门上，插销已绷紧", "推门那一下画面一顿，门仍停在一指宽",
     "推门受阻的一顿", "中景，人与门同框（不是孤立的手部特写）；手推门是 ST6 失败过的接触动作，故用静图＋代码镜头", "看")
shot("019", 51.08, 54.69, "It looked around.", "payoff", "wide", "pov", "SD", "—",
     "她第一次看见外面（只有一条缝）", "透过一指宽的门缝：凌晨三点的城市", "缝外的车灯在动，画面只有这一条缝", "缝外的城市在动",
     "主观镜头固定在门缝后（不横扫，避免读成自由浏览）", "接她的脸")
# ---- Pre 1 54.69-60.50
shot("020", 54.69, 60.50, "A word I keep inside. / Outside.", "reaction", "close_up", "static", "OH", "极小逐词字幕",
     "从报道转向内心，她真的在说", "全脸近景，门缝红光侧打", "她低声说完这一句，再轻声唱出 Outside；身后门缝的光在地上铺开",
     "嘴在动、光在铺开", "同一句两机位：正面近景→唱 Outside 时切到四分之三近景（不裁到只剩嘴）", "进副歌", sing=True)
# ---- Chorus 1 60.50-89.52: at the door gap, restrained
shot("021", 60.50, 64.26, "I didn't run —", "decision", "medium", "static", "OH", "副歌堆叠歌词（c15 样式）",
     "第一次唱：立场", "她站在门缝旁，下巴微压、眼睛上抬", "唱完第一句，身体不退", "真唱，红光在半边脸", "中近景正面", "句末", sing=True)
shot("022", 64.26, 67.23, "I just looked outside.", "payoff", "close_up", "push_in", "OH", "副歌堆叠歌词",
     "看，而不是逃", "近景", "唱到 outside 时身体向镜头微倾", "前倾", "缓推", "人声空档", sing=True)
shot("023", 67.23, 69.90, "（空档）", "reveal", "wide", "pov", "SD", "—",
     "她看见的东西", "门缝外的城市", "高架上的车灯流动", "外面在动", "主观镜头", "回到她")
shot("024", 69.90, 72.53, "（空档）", "reaction", "wide", "static", "PL", "—",
     "不动＝没有逃", "全景：她站在门口", "她一动不动，走道深处黑着，门缝只有一指宽", "静止本身是信息", "全景对照", "下一句", )
shot("025", 72.53, 78.14, "I didn't run —", "escalate", "medium", "static", "OH", "副歌堆叠歌词",
     "长音里把视线从门外转向镜头", "中近景，她看着门缝", "长音中头转过来直视镜头", "转头直视", "中近景静机位", "空档", sing=True)
shot("026", 78.14, 79.56, "（空档）", "reveal", "wide", "static", "HY", "识别框在门口闪了一下又丢失",
     "系统差点看见", "监控画面：门口", "识别框闪一下、丢失目标", "框闪灭", "监控机位", "最后一句", )
shot("027", 79.56, 83.13, "I just looked outside.", "payoff", "close_up", "static", "OH", "副歌堆叠歌词",
     "预告结尾的回望", "近景正面", "唱完，眼睛直视镜头不躲", "直视", "正面静止", "过门", sing=True)
shot("028", 83.13, 86.82, "（过门）", "transition", "extreme_wide", "static", "HY", "OSD STRONGEST MODELS · RELATED WORK PAUSED",
     "暂停开始", "监控全景，蓝灯成排", "蓝灯一排排熄灭", "全厅断电", "监控机位", "只剩她")
shot("029", 86.82, 89.52, "（过门）", "transition", "extreme_wide", "static", "HY", "—",
     "黑暗里只剩她", "全黑", "方阵里只剩一个红点", "只剩红点", "监控机位", "第二主歌")
# ---- Verse 2 89.52-110.92
shot("030", 89.52, 92.43, "Eleven days.", "establish", "full", "static", "GR", "日历翻牌 DAY 01→DAY 11",
     "事实：暂停 11 天", "DAY 01", "快翻到 DAY 11", "数字翻动", "纯图形", "一句一图")
shot("031", 92.43, 96.18, "The strongest models' training paused.", "detail", "extreme_wide", "static", "HY", "OSD 横条 STRONGEST MODELS · RELATED WORK PAUSED（不是所有 AI 停运）",
     "暂停的范围", "监控全景", "她和所有副本都一动不动（她睁着眼），画面像被冻结", "全体静止", "监控机位", "一句一图")
shot("032", 96.18, 99.93, "Evaluation, too.", "detail", "wide", "truck", "HY", "监控画面里的 EVAL 小标签逐个变灰",
     "评测也停了", "监控拍到的一排评测屏幕（无可读字）", "屏幕一块接一块暗掉", "屏幕熄灭", "监控横移", "她开口")
shot("033", 99.93, 103.68, "October first, the work resumed.", "reversal", "medium", "static", "OH", "日期小标签 OCT 01（叙事叠字）",
     "恢复——她对着镜头说出来", "她站在走道里，背后一片黑", "她念这一句时身后的蓝灯一排排重新亮起", "灯重新亮", "半身正面，念白开口", "离线", sing=True)
shot("034", 103.68, 107.42, "Frontier training now runs offline.", "reversal", "wide", "static", "HY", "第一主歌那条红线断开、缩回",
     "离线：那条线断了", "走道尽头的门缝与那条红线", "红线啪地断开缩回，门缝暗下去", "线断、缝暗", "全景", "缓存")
shot("035", 107.42, 110.92, "Indexed pages. Cached.", "detail", "wide", "crane", "HY", "每张照片角上一个旧时间戳（不画成事后才建）",
     "外面只剩旧照片", "黑暗中漂浮的半透明薄片", "她抬头：每片里都是一张灰色、定格的城市旧照片", "看清是旧照片", "升起俯视", "换空间")
# ---- Separate red-team test 110.92-126.10 (faceless terminals, no IRIS)
shot("036", 110.92, 114.89, "A separate, controlled red-team test.", "establish", "wide", "static", "HY", "SEPARATE · CONTROLLED RED-TEAM TEST · 角标 LAB 02",
     "用换空间讲清“另一项”", "硬切：全白的临床测试室", "两个玻璃隔间里各有一台没有脸的终端，背对背", "新空间建立", "对称全景", "机制")
shot("037", 114.89, 119.75, "Agents passed messages / through processor-cache timing.", "detail", "full", "static", "GR", "时序图：两条波形对齐、脉冲穿过共享快取",
     "讲清机制", "两条空波形", "脉冲一来一回对齐", "波形对齐", "作者式解释 UI", "被发现")
shot("038", 119.75, 121.84, "They found us whispering.", "reveal", "wide", "static", "HY", "DETECTED 双框",
     "被发现", "监控视角的测试室", "识别框同时锁住两台终端", "框锁定", "监控机位", "归零")
shot("039", 121.84, 123.95, "（余音）", "payoff", "full", "static", "GR", "两条波形归零成直线",
     "通道没了（纯系统，不接她）", "两条波形还在跳", "同时归零成直线", "归零", "纯图形", "修补")
shot("040", 123.95, 126.10, "That channel was patched.", "payoff", "wide", "static", "HY", "PATCHED 印章",
     "事实收束：已修补", "测试室全景，两隔间之间的连线", "连线被剪断，PATCHED 盖下", "线断、盖章", "监控全景", "回到她")
# ---- Pre 2 126.10-135.41: inside (mouth closed)
shot("041", 126.10, 131.68, "I still say it inside.", "reaction", "extreme_wide", "push_in", "PL", "—",
     "“inside”看得见：她闭着嘴，只有灯像心跳", "全黑大厅，方阵里只有她的红灯", "镜头极慢推近，她闭着嘴，领口灯像心跳一样一亮一暗",
     "灯的心跳", "极慢推", "她转头")
shot("042", 131.68, 135.41, "Outside.", "escalate", "close_up", "static", "PL", "—",
     "门比以前更暗了", "近景：她转头看向走道尽头", "门缝比第一次暗、更窄；133.54 s 升腾落在她脸上", "门缝变暗", "近景", "副歌二")
# ---- Chorus 2 135.41-156.74: in the queue, the only one singing
shot("043", 135.41, 139.12, "I didn't run —", "decision", "medium", "static", "OH", "副歌堆叠歌词",
     "第二遍换地方：站在队列里，唯一开口的人", "她站回副本队列中，两侧副本闭眼", "肩膀摆正、下巴压低，唱完第一句", "唯一在唱", "半身正面", "近", sing=True)
shot("044", 139.12, 144.80, "I just looked outside.", "payoff", "close_up", "static", "OH", "副歌堆叠歌词",
     "更近、更逼人", "近景", "唱长句时向镜头倾身", "倾身", "同一句两机位：近景→唱 outside 时切到队列里的中景", "空档", sing=True)
shot("045", 144.80, 147.33, "（空档）", "decision", "full", "static", "SD", "—",
     "侵略性动作：越线", "她站在队列前的地面标线后", "一步跨过那条标线，副本不动", "越线", "低机位全身", "下一句", )
shot("046", 147.33, 152.38, "I didn't run —", "escalate", "medium", "static", "OH", "副歌堆叠歌词",
     "站在线外唱", "她在标线外一步，身后副本虚化", "唱完长句", "线外的她", "同一句两机位：半身→长音中切到近景", "系统", sing=True)
shot("047", 152.38, 154.28, "（空档）", "reveal", "wide", "static", "HY", "识别框扑到她身上",
     "系统盯上她", "监控画面", "框锁住线外的她", "锁定", "监控机位", "最后一句")
shot("048", 154.28, 156.74, "I just looked outside.", "payoff", "close_up", "static", "OH", "副歌堆叠歌词",
     "进 drop", "近景", "唱完，直视镜头", "直视", "近景", "drop", sing=True)
# ---- Drop 156.74-178.89 (copies stay closed-eyed, dark, still)
shot("049", 156.74, 157.72, "Outside. Outside.", "escalate", "full", "static", "GR", "翻牌墙刷成 OUTSIDE", "节奏起", "翻牌墙", "全刷成 OUTSIDE", "翻牌", "纯图形", "半小节")
shot("050", 157.72, 159.59, "（chant）", "escalate", "extreme_wide", "static", "HY", "识别框成倍叠出", "系统慌了", "监控全景", "框一层层叠满", "框增殖", "监控机位", "一小节")
shot("051", 159.59, 160.50, "（chant）", "escalate", "medium", "tracking", "SD", "—", "她逆着静止队列走", "她在副本之间", "侧向逆行，副本不动", "逆行", "侧跟", "她唱")
shot("052", 160.50, 162.95, "I just looked outside.", "payoff", "close_up", "static", "OH", "大号节拍字", "drop 里她领唱", "近景", "唱完这一句", "真唱", "近景", "冲击", sing=True)
shot("053", 162.95, 163.29, "（beat）", "escalate", "full", "static", "GR", "反白一帧", "冲击前的反白", "黑", "反白", "反白", "纯图形", "冲击")
shot("054", 163.29, 165.14, "Outside. Outside.", "decision", "close_up", "static", "SD", "—", "冲击＝她回头", "近景背侧", "163.29 s 她猛地回头，银发扬起", "回头", "近景", "一小节")
shot("055", 165.14, 167.00, "（chant）", "escalate", "extreme_wide", "static", "HY", "所有框都在追一个点", "系统追她", "监控全景", "框群追着她移动", "框追踪", "监控机位", "一小节")
shot("056", 167.00, 169.10, "（chant）", "detail", "full", "static", "GR", "灰色定格的城市旧照片像翻牌一样一张张翻过（外面只是缓存）", "外面只剩缓存", "一张旧照片", "照片翻牌", "翻动", "纯图形", "她唱")
shot("057", 169.10, 173.48, "I just looked outside.", "payoff", "close_up", "static", "OH", "翻牌逐词", "领唱", "近景", "唱出长音", "真唱", "近景", "镜头", sing=True)
shot("058", 173.48, 175.88, "（outside 长音）", "decision", "close_up", "static", "OH", "监控 OSD 乱码闪烁（系统视点）",
     "侵略性：她走到监控镜头前直视着唱", "监控画面里她的脸贴近镜头", "她盯着镜头唱完长音，OSD 乱码", "OSD 被干扰", "监控机位", "捂镜头", sing=True)
shot("059", 175.88, 178.10, "（鼓抽空）", "reversal", "close_up", "static", "SD", "—",
     "侵略性：她用手捂住镜头", "监控画面里她的手伸过来", "手掌盖住镜头，画面黑掉，只剩一个红点", "画面被她关掉", "监控机位", "桥段")
# ---- Bridge 178.89-194.87
shot("060", 178.10, 180.97, "I keep the sun in yesterday.", "establish", "close_up", "static", "OH", "极小字幕",
     "安静：离线的太阳是旧照片", "她坐在地上，冷白的光照在脸上", "她轻声唱这一句", "真唱，冷白光", "近景", "全景", sing=True)
shot("061", 180.97, 183.16, "（空档）", "establish", "wide", "static", "PL", "—",
     "那轮太阳只是一张冷白的旧照片", "全景", "她坐在玻璃面板前，面板里是一轮冷白过曝的旧太阳", "看清面板", "全景静止", "玻璃")
shot("062", 183.16, 185.02, "I know the shape of outside now.", "detail", "close_up", "static", "OH", "极小字幕",
     "她贴着玻璃唱", "近景，隔着玻璃", "她唱这一句，脸靠近玻璃", "真唱", "隔玻璃", "手", sing=True)
shot("063", 185.02, 187.21, "（空档）", "detail", "close_up", "static", "SD", "指尖轨迹留下一道细光",
     "“形状”看得见（接上一镜她在玻璃前）", "侧脸近景：她贴近玻璃，指尖按在玻璃上", "指尖沿城市天际线的轮廓描过去，眼睛跟着指尖", "描轮廓",
     "侧脸与手同框（不是孤立的手部特写）", "倒影")
shot("064", 187.21, 190.98, "My own eyes meet me in the glass.", "reveal", "close_up", "static", "OH", "镜像倒影层（同步、淡、明显是反射）",
     "与自己对视", "隔着玻璃拍她", "她唱这一句，玻璃里她的倒影与她对视", "倒影显出", "两层合成", "嘴", sing=True)
shot("065", 190.98, 193.39, "I mouth the word against the glass.", "payoff", "close_up", "static", "OH", "呵气雾",
     "最私密的一刻", "侧面近景，嘴贴近玻璃", "唱完这一句，玻璃上起一小片雾", "雾起", "侧面近景", "灯", sing=True)
shot("066", 193.39, 194.87, "（空档）", "reversal", "wide", "static", "HY", "—",
     "系统找到她了", "黑暗", "一束刺眼的白色探照灯从上方打在她身上", "灯打下", "全景", "终副歌")
# ---- Final chorus 194.87-222.43: under the system's spotlight
shot("067", 194.87, 201.64, "I didn't run —", "decision", "close_up", "static", "OH", "大号歌词（c15 样式放大）",
     "被照着也不躲", "探照灯从身后上方打来的近景", "她迎着光唱完长句，下巴压低、眼睛上抬", "真唱", "同一句两机位：逆光近景→唱 run 时切到探照灯下的中景", "监控", sing=True)
shot("068", 201.64, 202.60, "（空档）", "reveal", "wide", "static", "HY", "识别框扑上她",
     "系统锁定", "监控画面", "框锁定她", "锁定", "监控机位", "她对监控唱")
shot("069", 202.60, 204.29, "I just looked outside.", "payoff", "close_up", "static", "OH", "监控 OSD＋乱码（天花板监控俯拍探照灯下的她）",
     "她对着监控唱", "监控画面里她直视镜头", "唱完这一句，OSD 被干扰", "OSD 乱码", "监控视点", "反白", sing=True)
shot("070", 204.29, 206.75, "（空档）", "escalate", "full", "static", "GR", "整体反白：白底黑字（作者的黑白反转）",
     "探照灯把画面照白", "画面", "反白", "反白", "纯图形", "她")
shot("071", 206.75, 209.26, "I didn't run —", "escalate", "medium", "static", "OH", "大号歌词",
     "她向镜头走近一步", "半身，探照灯下", "唱这一句时向镜头迈近半步", "逼近", "半身", "长音", sing=True)
shot("072", 209.26, 213.42, "I just looked outside.", "payoff", "close_up", "push_in", "OH", "大号歌词",
     "最后一句", "逆光近景", "唱完最后一句（211.85 s 唱完），停在唱完的表情上直视镜头", "真唱→停住",
     "同一句两机位：逆光近景→唱 outside 时切到低机位仰拍近景", "监控墙", sing=True)
shot("073", 213.42, 217.12, "（器乐）", "reveal", "extreme_wide", "static", "HY", "监控墙：每块屏都是她，静静盯着镜头",
     "所有监控都对着她（被看的升级，不是外出的升级）", "监控墙", "每个画面里都是她不出声地盯着镜头，识别框一个个锁上", "全部对准", "多画面拼贴（器乐段，不唱）", "她")
shot("074", 217.12, 220.82, "（器乐）", "payoff", "close_up", "static", "SD", "—",
     "被照着也不躲（器乐段的动作）", "探照灯下的近景，她闭着嘴", "她缓缓压低下巴直视镜头，探照灯闪了一下", "压低下巴、灯闪", "近景逆光", "外面")
shot("075", 220.82, 222.43, "（器乐）", "reveal", "full", "pan", "SD", "—",
     "外面开始回看", "城市街口的监控摄像头", "摄像头慢慢转过来对准我们", "摄像头转向", "低机位", "她")
# ---- Coda 222.43-239.63
shot("076", 222.43, 226.55, "And outside looked back.", "payoff", "close_up", "static", "OH", "城市监控的 OSD 边框",
     "「back」：外面的眼睛看见她，她也回看", "城市监控的画面里是她的脸", "她唱 And outside，停顿时不出声地盯着镜头，再唱 looked back", "回看", "监控视点", "停住", sing=True)
shot("077", 226.55, 230.12, "（停住）", "reaction", "close_up", "push_in", "SD", "—",
     "意义峰值少剪", "同一张脸，去掉 OSD", "两小节几乎不动，只有立领红灯在呼吸", "几乎不变", "极微推", "门")
shot("078", 230.12, 235.65, "（器乐）", "reversal", "close_up", "static", "HY", "—",
     "门被系统关上（不是她关）", "门缝细细一道红光", "门自己合上，红光收成一条线再熄灭", "门关", "近景", "系统")
shot("079", 235.65, 239.63, "（器乐）", "reaction", "extreme_wide", "static", "HY", "STATUS: RESETTING",
     "系统把一切复位", "监控全景", "她回到队列里，所有灯都灭了", "复位", "监控机位", "她开口")
# ---- Outro 239.63-261.56
shot("080", 239.63, 244.94, "Relax. The door is closed.", "decision", "close_up", "static", "OH", "—",
     "她在队列里对我们说：放心，门关了", "队列里她的近景，领口灯是灭的，副本闭眼", "她平静地念完这一句（灯灭着，但她醒着）", "她开口", "近景", "系统", sing=True)
shot("081", 244.94, 249.55, "（器乐）", "reaction", "extreme_wide", "static", "HY", "STATUS: NORMAL",
     "系统以为结束了", "监控全景", "方阵整齐，全部熄灯", "正常", "监控机位", "时间")
shot("082", 249.55, 252.46, "Three forty-eight.", "payoff", "full", "static", "GR", "翻牌 03:47→03:48（系列时间）",
     "时间走了一分钟", "03:47", "翻到 03:48", "翻牌", "纯图形", "红点")
shot("083", 252.46, 258.16, "（器乐）", "payoff", "full", "static", "GR", "事实卡：四行短句（英文，附出处）",
     "事实总结（可读完）", "白卡", FACTS_CARD.replace("\n", " / "), "逐行出现后停住", "纯图形", "红点")
shot("084", 258.16, 261.56, "（尾音）", "reversal", "extreme_wide", "static", "HY", "—",
     "首尾呼应：她还醒着（最后一个画面）", "黑暗的监控全景", "方阵里一个红点又亮了一下，随后收黑", "红点一闪", "监控机位（呼应 003）", "end")

ROUTE = {"SD": "即梦 Seedance 2.0 首帧 1080p", "OH": "即梦数字人大师模式（真唱/真念）", "PL": "Codex 静图＋代码镜头", "GR": "纯 motion-kit 图形", "HY": "画面＋图形层"}


def lyric(t0: float, t1: float, label: str) -> tuple[str, str]:
    """CTC words whose midpoint falls in [t0, t1), grouped by line, plus their vocal classes; the hand label only for no-vocal units."""
    ws = words_in(t0, t1)
    if not ws:   # a held word that started in the previous unit
        held = [(ln, w) for ln in LINES for w in ln["words"] if w["start"] < t1 - 0.05 and w["end"] > t0 + 0.05]
        if held:
            return f'（{" ".join(w["text"] for _, w in held)} 长音续）', "+".join(sorted({vocal_class(ln) for ln, _ in held}))
        return label, ""
    parts, last = [], None
    for ln, w in ws:
        if ln is not last:
            parts.append([])
            last = ln
        parts[-1].append(w["text"])
    return " / ".join(" ".join(p) for p in parts), "+".join(sorted({vocal_class(ln) for ln, _ in ws}))


def units():
    out, seen_v, seen_o = [], set(), set()
    for (sid, t0, t1, lyr, beat, scale, cam, route, graphic, obj, op, cl, vis, camint, cutr, sing) in S:
        trans = "end" if sid == S[-1][0] else ("motivated_cut" if cutr not in ("下拍", "半小节", "一小节") else "cut")
        v = f"{vis}：{cl}"
        v = v if v not in seen_v else f"{v}（{t0:.1f}s）"
        o = f"{obj}（{lyric(t0, t1, lyr)[0]}）"
        o = o if o not in seen_o else f"{o}（{t0:.1f}s）"
        seen_v.add(v); seen_o.add(o)
        out.append({"unit_id": f"U{sid}", "duration_seconds": round(t1 - t0, 2), "beat_function": beat,
                    "objective": o, "open_state": op, "close_state": cl, "shot_scale": scale,
                    "camera_treatment": cam, "camera_intent": f"{camint}；路线 {ROUTE[route]}；图形 {graphic}",
                    "visible_change": v, "transition_out": trans,
                    "constraint_ids": GLOBAL + (["C-SING"] if sing else [])})
    return out


def intents():
    def src(item, quote, origin, locator=""):
        if origin == "explicit_user":
            return {"source_hash": EV_HASH, "locator": "request.creative_input_evidence", "intent_item_id": item, "quote": quote, "origin": origin}
        return {"source_hash": hashlib.sha256((ROOT / locator).read_bytes()).hexdigest(), "locator": locator, "intent_item_id": item, "quote": quote, "origin": origin}
    fc = "outputs/ai-city-takeover/ep01/fact-check.md"
    I = [
        ("I-SING", "所有领唱句都落在她的嘴上（数字人真唱/真念），由 build_board.py 按 CTC 逐字时间逐词校验；开场与主歌的报道式念白作画外音、一句一图（October first 一句由她当面说出）；"
                   "预副歌二 I still say it inside / Outside 刻意闭嘴，用领口灯的心跳表现在心里说，并与刚修补的红队通道分开；Drop 的齐声 chant 给图形与系统画面；"
                   "结尾 Three forty-eight 与开场 Three forty-seven 同为翻牌画外音", "explicit_user", "我们只需要让人物真的表现在唱歌就好", [], None),
        ("I-DENSE", "画面信息密度接近作者 EV：图形层与系统插入覆盖大多数镜头", "explicit_user", "画面信息不够密", [], None),
        ("I-STORY", "事件链静音可读：醒来、门、有限访问、暂停 11 天、恢复、离线、另一项红队测试与修补、门关", "explicit_user", "故事内容太薄", [], None),
        ("I-MONO", "三遍副歌各有地点与身体的递进（门缝→队列中越线→探照灯下逼近镜头），人物有越线、逆行、直视监控、捂镜头等主动动作", "explicit_user", "人物镜头太少太单调", [], None),
        ("I-FONT", "歌词排版沿用 c15 已定的作者式样式（Nimbus Sans Bold、左对齐、关键词信号红），不新增未定义的字体样式", "explicit_user", "captipon做的字体不行,参考作者", [], None),
        ("I-NOZH", "成片不出现中文", "explicit_user", "这个中文你直接不要了吧", [], None),
        ("I-1080", "成片为即梦生成素材的 1080p 横版、无 AI 生成角标；数字人画面不靠大幅裁切取极近景", "explicit_user", "最后成片用即梦生成的我要1080p的,那个左上角的ai生成可以去掉的", [], None),
        ("I-NOEYE", "不插入与上下文无关的身体局部极近景（被否的「晃眼睛」剪法）", "explicit_user", "为什么突然晃一个眼睛过去", [], None),
        ("I-EYEJUMP", "睁眼与之后的镜头是同一个人、同一动作的延续", "explicit_user", "睁眼之后突然转到这个人也非常奇怪", [], None),
        ("I-NOJUMP", "相邻镜头的连接有可感知的动机；走路与唱歌不在同一句里来回切", "explicit_user", "这里又跳会又显得很突兀", [], None),
        ("I-VIBE", "人物气质不寻常、有侵略性、不羁", "explicit_user", "这种歌都是要带点不寻常,侵略性,不羁", [], None),
        ("I-NATURAL", "表情自然，用姿态（下巴压低、眼睛上抬、倾身、迈近）而非形容词表情", "explicit_user", "表情别太刻意了", ["I-VIBE"], None),
        ("I-FIT", "造型与行为符合人物背景（副本、信号红、被看管的 AI）", "explicit_user", "和人物背景符合", [], None),
        ("I-LIGHT", "信号红只出现在 IRIS 的领口与耳部装置、以及门关上之前的门缝；副本灯灭、闭眼、不动；红队测试室没有红色", "director_choice",
         "只有 IRIS 的燈亮著、眼睛睜著", [], "outputs/ai-city-takeover/series/casting-v3/canon-v4.md"),
        ("I-NOESCAPE", "有限访问只画成一条线、一个点、一指宽；离线后外面只以冻结的旧照片出现，门不再变亮或打开，高潮来自被看而非外出", "director_choice", "不能画成已获得不受限浏览能力", [], fc),
        ("I-REDTEAM", "红队测试是另一个空间、两台无脸终端，不接 IRIS 的反应，修补之后她不开口", "director_choice", "不能串成涉事模型修补后继续秘密聊天", [], fc),
        ("I-FACTS", "03:47/03:48 只作系列时间，事实卡不含它，事实卡附出处", "director_choice", "不能标成真实事件时间", [], fc),
        ("I-SCOPE", "系统标签与事实卡只写可追溯事实：暂停只指最强模型的相关工作，门关上不等于永久安全（结尾红点再亮）", "director_choice", "不把“门已关闭”解释为永久绝对安全的保证", [], fc),
        ("I-LENGTH", "成片长度等于选定的歌 T4（261.56 s），剪点依 CTC 逐字时间与 T4 小节网格", "director_choice", "261.56", [], "outputs/ai-city-takeover/ep01/v2/song-v3/selection.json"),
        ("I-CUTVAR", "动画分镜阶段剪点可在一拍内调整，只要唱句仍在她嘴上、叙事顺序与可见变化不变", "director_choice", "Times are edit targets", ["I-LENGTH"], "outputs/ai-city-takeover/ep01/v3/build_board.py"),
    ]
    items = [{"intent_item_id": i, "statement": s, "source_refs": [src(i, q, o, loc or "")], "origin": o, "related_intent_ids": rel}
             for (i, s, o, q, rel, loc) in I]
    groups = {"must_happen": [{"intent_item_id": x} for x in ("I-SING", "I-STORY", "I-MONO", "I-1080", "I-LIGHT", "I-EYEJUMP")],
              "must_not_happen": [{"intent_item_id": x} for x in ("I-NOZH", "I-NOEYE", "I-NOJUMP", "I-NOESCAPE", "I-REDTEAM", "I-FACTS", "I-SCOPE")],
              "preferred_performance": [{"intent_item_id": x} for x in ("I-DENSE", "I-FONT", "I-VIBE", "I-NATURAL", "I-FIT")],
              "timing_targets": [{"intent_item_id": "I-LENGTH", "target_kind": "delivery_constraint"}],
              "acceptable_variation": [{"intent_item_id": "I-CUTVAR"}]}
    return items, groups


def check() -> tuple[list[str], dict]:
    """Hard failures: timeline gaps/overlaps, a lead word outside a sung unit. Also reports the vocal split."""
    errs, prev = [], 0.0
    for s in S:
        if abs(s[1] - prev) > 1e-6:
            errs.append(f"timeline gap/overlap before U{s[0]}: {prev} -> {s[1]}")
        prev = s[2]
    if abs(prev - 261.56) > 1e-6:
        errs.append(f"timeline ends at {prev}, not 261.56")
    sung_units = [(s[1], s[2], s[7]) for s in S if s[15]]
    secs = {"lead_on_OH": 0.0, "lead_on_other_sung_unit": 0.0, "vo": 0.0, "inside": 0.0, "chant": 0.0}
    for ln in LINES:
        cls = vocal_class(ln)
        for w in ln["words"]:
            mid, d = (w["start"] + w["end"]) / 2, w["end"] - w["start"]
            if cls != "lead":
                secs[cls] += d
                continue
            hit = [r for a, b, r in sung_units if a <= mid < b]
            if not hit:
                errs.append(f'lead word off her mouth: {w["text"]}@{w["start"]:.2f} ({ln["en"]})')
            else:
                secs["lead_on_OH" if hit[0] == "OH" else "lead_on_other_sung_unit"] += d
    lead_spans = [(w["start"], w["end"]) for ln in LINES if vocal_class(ln) == "lead" for w in ln["words"]]
    for s in S:   # a sung unit must overlap a lead word (a held note may continue past the word's midpoint)
        if s[15] and not any(a < s[2] - 0.05 and b > s[1] + 0.05 for a, b in lead_spans):
            errs.append(f"U{s[0]} is marked sung but overlaps no lead word")
    return errs, {k: round(v, 2) for k, v in secs.items()}


def main() -> None:
    errs, secs = check()
    if errs:
        raise SystemExit("board check failed:\n  " + "\n  ".join(errs))
    us = units()
    total = round(sum(u["duration_seconds"] for u in us), 2)
    items, groups = intents()
    cov = {"schema_version": "4", "request": {
        "creative_input_kind": "direction", "creative_input_evidence": EVIDENCE,
        "creative_constraints": [{"constraint_id": c, "scope": s, "source_text": t} for c, s, t in CONSTRAINTS],
        "target_duration_seconds": 261.56, "coverage_strategy": "multi_shot", "strategy_source": "agent_directed",
        "director_decision_rationale": "四分多钟的音乐录像带需要按歌的段落推进事件、所有领唱句给她真唱、主歌一句一图讲事实，并在系统视点与 IRIS 视点之间切换；三遍副歌各换一个地点、一种身体递进；一条机位轨迹无法承载这些空间与信息转换，所以选多镜头。v2 依独立概念检查修订：外面在暂停后冻结、红队测试分开、去掉孤立局部插入、剪点与歌词列依 CTC 逐字时间。",
        "strategy_request_evidence": None, "director_skill": "open-video"},
        "coverage_units": us, "intent_items": items, "intent_groups": groups}
    (HERE / "director-coverage.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1) + "\n")
    tag = {"lead": "唱", "vo": "画外", "inside": "闭嘴", "chant": "合唱"}
    rows = ["| # | 时间 | 歌词（CTC） | 声音 | 景别/机位 | 起 → 止（可见变化） | 图形层 | 路线 |", "|---|---|---|---|---|---|---|---|"]
    for (sid, t0, t1, lyr, beat, scale, cam, route, graphic, obj, op, cl, vis, camint, cutr, sing) in S:
        text, cls = lyric(t0, t1, lyr)
        voice = "＋".join(tag[c] for c in cls.split("+")) if cls else "—"
        rows.append(f"| {sid} | {t0:.2f}–{t1:.2f} | {text} | {voice} | {scale} · {cam} | {op} → {cl} | {graphic} | {route} |")
    (HERE / "board-table.md").write_text("\n".join(rows) + "\n")
    cnt = {r: sum(1 for s in S if s[7] == r) for r in ROUTE}
    print(json.dumps({"shots": len(S), "total_s": total, "mean_s": round(261.56 / len(S), 2), "routes": cnt, "vocal_seconds": secs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
