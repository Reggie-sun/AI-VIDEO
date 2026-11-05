#!/usr/bin/env python3
"""Director Coverage Evidence (open-video v4) for IRIS EP01 board v2.

  uv run python outputs/ai-city-takeover/ep01/v2/build_coverage.py
  uv run python .agents/skills/open-video/scripts/validate_director_coverage.py \
      outputs/ai-city-takeover/ep01/v2/director-coverage.json

Creative input evidence is the director's verbatim words (brief + decision log); every explicit_user
intent quotes a substring of it and binds its SHA-256. Units mirror board.md shot for shot.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIEF = (HERE / "../../brief/creative-input.md").resolve()

LATER = [
    "我需要的是横版的",
    "固定系列",
    "B 固定 AI 角色",
    "寫實人形 / 唱歌（歌詞 MV） / AI 新聞／熱點解說 / 冷靜觀察者",
    "欧美 / 英文",
    "我更像让第一个女的当主角",
    "IRIS",
    "我考虑的是这种词语适合我这个背景吗,能唱好吗,我要换成和作者一个风格的吗,唱歌我还是准备用英文.一些字体你可以用中文",
    "原作架構＋IRIS 冷調 (Recommended) / 英文歌詞＋中文譯句 (Recommended)",
    "認可，我去 Suno 生成",
    "你别管codex,我觉得他没做好",
    "我希望全自动别要我点击",
    "主歌改半唱半念，再試 (Recommended)",
    "保留第 3 版副歌，其餘補念白 (Recommended)",
    "A · Stella",
    "可以，往下做分鏡",
]


def evidence() -> str:
    text = BRIEF.read_text(encoding="utf-8")
    start = text.index("你是一支由技术导演")
    end = text.index("## 2026-10-30 · user · 追加（执行中）")
    initial = text[start:end].strip()
    return "\n".join(["[初始需求]", initial, "[後續導演回覆，逐字]"] + LATER)


GLOBAL = [
    ("landscape", "我需要的是横版的"),
    ("cinematic-no-template", "风格必须电影化、高级、统一，杜绝廉价科幻 UI 模板。"),
    ("original-no-copy", "不要照搬原片文案、音乐或完整镜头。"),
    ("english-song-chinese-type", "唱歌我还是准备用英文.一些字体你可以用中文"),
    ("bilingual-captions", "英文歌詞＋中文譯句 (Recommended)"),
    ("iris-lead", "我更像让第一个女的当主角"),
    ("no-quality-cut", "不要为了完成任务而降低质量标准。"),
]

UNITS = [
    ("S1", 2.867, "establish", "extreme_close_up", "static",
     "IRIS 閉著的眼與「03:47」：還沒醒來的那一刻",
     "微距，左眼閉合，領口紅光映在下眼瞼", "眼睛仍閉著，只有細微眼動與光的變化",
     "鏡頭不動，讓靜止的閉眼承擔「醒來之前」", "細微眼動、光線變化", "cut"),
    ("S2", 1.933, "reveal", "medium", "push_in",
     "唱到「woke」時切到睜眼注視鏡頭的 IRIS，用剪接表達醒來",
     "陽台中近景，IRIS 睜眼注視鏡頭", "同一構圖略推近，事件日期出現",
     "數位緩推 1.00→1.05，交代講述者與城市", "微推與自然呼吸", "cut"),
    ("S3", 3.333, "establish", "wide", "push_in",
     "OpenAI 內部研究模型的訓練機房，盡頭半開的紅光門縫就是配置錯誤的 DNS 解析器",
     "機房走道正中，冷藍機櫃，盡頭紅光門縫", "鏡頭推近，門縫上標出「DNS 解析器 · 配置错误」",
     "沿走道中軸緩慢前推，把注意力帶向紅光門縫", "鏡頭前推，拓撲依字出現", "motivated_cut"),
    ("S4", 3.334, "escalate", "close_up", "push_in",
     "紅色脈衝沿線纜跑到窗玻璃就停，只探出一條細虛線＝有限聯網",
     "半開機櫃門近景，紅光門縫", "虛線收回，脈衝停在玻璃內側",
     "2.5D 緩推，跟隨脈衝方向", "脈衝移動到窗邊，虛線伸出再收回", "cut"),
    ("S5", 1.9, "reaction", "medium", "static",
     "IRIS 旁觀遠處一扇窗亮起紅光，玻璃上閃過遮蔽過的查詢日誌",
     "IRIS 側臉望向窗外城市", "遠處紅窗亮著，遮蔽日誌出現",
     "固定機位，讓遠處的紅窗成為唯一事件", "紅窗亮起與遮蔽條出現", "cut"),
    ("S6", 1.433, "payoff", "medium", "static",
     "只停了相關訓練：機櫃靜止、窗外車流照常，大字「最强模型训练 暂停 11 天」",
     "機櫃與窗外車流", "日期快進到 10-01，車流仍在動",
     "固定機位，用內外對比說明暫停範圍", "日期快進、窗外車流移動", "cut"),
    ("S7", 4.067, "transition", "close_up", "static",
     "連線斷開＝離線；網頁薄片逐一蓋上灰白「已缓存」",
     "黑房間，IRIS 正面近景，紅色連線斷開", "多張薄片已蓋「已缓存」",
     "固定機位，靠薄片與戳記逐拍推進", "連線斷開、戳記逐拍落下", "cut"),
    ("S8a", 3.7, "decision", "close_up", "static",
     "IRIS 唱出副歌第一遍，對嘴同步",
     "陽台正面近景，嘴閉", "唱完第一遍，嘴型與歌聲同步",
     "固定正面近景，讓對嘴與表情清楚可讀", "唱歌的嘴型與呼吸", "cut"),
    ("S8b", 3.333, "payoff", "close_up", "static",
     "副歌第二遍，3/4 側面固定機位，唱完閉嘴望向城市",
     "陽台左前 3/4 近景，開始演唱", "唱完閉嘴，視線望向城市",
     "固定機位，表演本身承擔第二遍的變化", "唱歌、閉嘴、轉望城市", "cut"),
    ("S9a", 2.4, "reversal", "close_up", "static",
     "門已經關上：機櫃門關閉、紅光熄滅，解析器已修復",
     "半開機櫃門近景，紅光門縫", "門完全關上，紅光消失",
     "固定機位，讓門關上的動作完整可見", "機櫃門關上，紅光熄滅", "cut"),
    ("S9b", 2.2, "reveal", "extreme_close_up", "static",
     "另一項紅隊測試：CPU 快取時序訊號在兩個核心之間來回，漏洞已修補",
     "CPU 晶片微距，兩個核心上各有紅點", "訊號來回後，落下「03:48 · IRIS · NEWS 01」",
     "微距固定，時序訊號就是唯一運動", "紅點交替、訊號往返、片尾字落下", "end"),
]


def main() -> None:
    ev = evidence()
    ev_hash = hashlib.sha256(ev.encode("utf-8")).hexdigest()
    for _, quote in GLOBAL:
        assert quote in ev, quote
    constraints = [{"constraint_id": cid, "scope": "global", "source_text": q} for cid, q in GLOBAL]
    gids = [cid for cid, _ in GLOBAL]
    units = [{"unit_id": u, "duration_seconds": d, "beat_function": bf, "objective": obj,
              "open_state": o, "close_state": c, "shot_scale": sc, "camera_treatment": cam,
              "camera_intent": ci, "visible_change": vc, "transition_out": tr, "constraint_ids": gids}
             for u, d, bf, sc, cam, obj, o, c, ci, vc, tr in UNITS]
    user = lambda iid, statement, quote: {
        "intent_item_id": iid, "statement": statement, "origin": "explicit_user", "related_intent_ids": [],
        "source_refs": [{"source_hash": ev_hash, "locator": "request.creative_input_evidence",
                         "intent_item_id": iid, "quote": quote, "origin": "explicit_user"}]}
    board_hash = hashlib.sha256((HERE / "board.md").read_bytes()).hexdigest()
    director = lambda iid, statement, related=(): {
        "intent_item_id": iid, "statement": statement, "origin": "director_choice", "related_intent_ids": list(related),
        "source_refs": [{"source_hash": board_hash, "locator": "board.md", "intent_item_id": iid,
                         "quote": statement, "origin": "director_choice"}]}
    items = [
        user("landscape", "成片為 1920×1080 橫版", "我需要的是横版的"),
        user("bilingual", "英文歌詞逐字點亮，下方一行簡中譯句", "英文歌詞＋中文譯句 (Recommended)"),
        user("iris-lead", "IRIS（CF-a）是唯一主角，身份與造型沿用 canon", "我更像让第一个女的当主角"),
        user("no-template", "圖形是畫面內訊號，不做廉價科幻 UI 模板", "杜绝廉价科幻 UI 模板"),
        user("no-copy", "文案、音樂、鏡頭原創，不搬原作", "不要照搬原片文案、音乐或完整镜头"),
        user("cold-observer", "IRIS 表演冷靜克制、不誇張", "冷靜觀察者"),
        director("lip-sync", "副歌 S8a/S8b 由 IRIS 對嘴演唱，嘴型與歌聲同步"),
        director("facts-limited", "用連上／看了一眼，不寫逃出；不捏造查詢；暫停只指相關最強模型；快取低語是另一項測試"),
        director("ai-label", "保留即夢 AI 生成標識，HUD 與字幕不遮擋"),
        director("beat-cuts", "剪點落在拍點或人聲起點，歌詞逐字點亮誤差 ≤1 幀"),
        director("reuse-a01", "S2 沿用已過 Gate 的 A01-v2，只取 1.9 s 並加數位緩推", ("iris-lead",)),
    ]
    groups = {
        "must_happen": [{"intent_item_id": i} for i in ("landscape", "bilingual", "iris-lead", "lip-sync")],
        "must_not_happen": [{"intent_item_id": i} for i in ("no-template", "no-copy", "facts-limited", "ai-label")],
        "preferred_performance": [{"intent_item_id": "cold-observer"}],
        "timing_targets": [{"intent_item_id": "beat-cuts", "target_kind": "delivery_constraint"}],
        "acceptable_variation": [{"intent_item_id": "reuse-a01"}],
    }
    payload = {
        "schema_version": "4",
        "request": {
            "creative_input_kind": "direction", "creative_input_evidence": ev,
            "creative_constraints": constraints, "target_duration_seconds": 30.5,
            "coverage_strategy": "multi_shot", "strategy_source": "agent_directed",
            "director_decision_rationale": "依原作「歌先行」方法，按已認可歌曲的小節與人聲起點剪接；每鏡只承擔一個可見事件，"
                                           "解說圖形畫進畫面內，歌詞逐字點亮；付費生成只用於人物表演與必要的物理動作。",
            "strategy_request_evidence": None, "director_skill": "open-video"},
        "coverage_units": units, "intent_items": items, "intent_groups": groups,
    }
    (HERE / "director-coverage.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    print(f"{len(units)} units, {sum(u['duration_seconds'] for u in units):.3f} s, evidence {ev_hash[:12]}")


if __name__ == "__main__":
    main()
