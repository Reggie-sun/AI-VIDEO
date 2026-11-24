#!/usr/bin/env python3
"""IRIS EP01 v4 Seedance units through the canonical owners: one independent source project per board clip.

  uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py draft MO06
  uv run python outputs/ai-city-takeover/ep01/v4/gen/unit.py materialize MO06 --profile outputs/ai-city-takeover/ep01/v4/gen/MO06/profile.json

draft        typed Character / Scene / Shot / QA policy / Registry drafts and the director row, bound to the v4 director
             coverage (ep01/v4/director-coverage.json, schema 4) and the user's preview approval. No canonical writes,
             no Provider calls.
materialize  bootstraps <unit>/project with ProductionStateCommitter, activates the QA policy, writes
             driver-config.json and runs the transport-free prepare. No Provider call.
show         prints the resolved request that prepare sealed (model, mode, output, bindings, prompt). Reads files only.

A unit is one clip of the v4 board (board/shots.json, clips[]): its id (MO.. motion, SG.. sung), its generation window
and its start-frame plate (board/plates/<plate>.png). The board is pinned by BOARD_SHA256 and each spec pins its plate's
sha256; a changed board or plate blocks the draft until the spec is re-read and re-pinned.

Inputs come only from the approval (pilot/sd/preview-approval.json, same shape as v3): the native prompt is
prompts.<unit>.text (exact, with its sha256), the only image is the preview artifact whose role is "<unit> first frame"
(the clip's plate), and generation must read seedance_2.0_vip · first_frame · <spec seconds> · 4k · 16:9 · no audio.
Spec seconds are the clip's window rounded up to a whole second. IRIS's identity is carried by that image plus the
approval's identity_waivers ["IRIS"]; no identity sheet is sent. The project's IRIS Character is the v4 identity: the
board's fixed text (identity_near / identity_far / look / copy) with the identity anchor face/IRIS-anchor-F1a.png
pinned by its sha256 in the Character's provenance (the anchor itself is not sent to the Provider).

A multimodal unit (SG.., the ESCAPE VELOCITY lip-sync method, v3 U021 / sd-r3b) sends exactly one image (role
"<unit> reference image", native {{image:0}}) and one vocal window (role "<unit> vocal", native {{audio:1}}): the clip's
exact window cut from the v4 Demucs vocal stem by cut_audio.py (pilot/audio/<unit>.wav, sealed in pilot/audio/windows.json).
Generation must read seedance_2.0_vip · multimodal · <spec seconds> · 4k · 16:9 · audio "reference_audio". The page's
own soundtrack (native audio, always on in this adapter) follows the reference vocal; the final film replaces it with
the song master.

Paths: every path inside the approval is relative to the repo root. The approval and the continuity report live in
outputs/ai-city-takeover/ep01/v4/pilot/sd/ unless SD_PILOT names another folder; unit folders and ledgers live in this
gen/ folder unless SD_UNITS names another one (SD_PILOT / SD_UNITS: relative to the repo root, or absolute). SD_TRIAL
names one folder for a separate take (e.g. pilot/sd-SG03) that holds all of them; SD_PILOT / SD_UNITS still win.

Same lane and gates as ep01/v3/gen/unit.py; submission is a separate step (operator.py) with its own one-use bound.
"""
from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import wave

P = Path(__file__).resolve().parent
V4 = P.parent
EP = V4.parent
REPO = P.parents[4]
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference  # noqa: E402
from ai_video.production.domain_acceptance import DomainAcceptancePolicy  # noqa: E402
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash  # noqa: E402
from ai_video.production.jimeng_models import JIMENG_MODEL_SPECS  # noqa: E402
from ai_video.production.models import (AssetRecord, AssetRegistrySnapshot, ArtifactReference,  # noqa: E402
    AudioAssetMetadata, AudioLoudnessMetadata, AudioSource, Character, DeliveryProfile, ProductionBrief, ProductionProject,
    ProjectArtifactRefs, QaPolicy, RendererPolicy, Scene, Shot, Story, StoryBeat, Storyboard, StoryboardBeat)
from ai_video.production.paths import canonical_audio_asset_path, canonical_image_asset_path  # noqa: E402
from ai_video.production.preview_approval import preview_approval_authoring_input  # noqa: E402
from ai_video.production.reference_authoring import director_coverage_authoring_input  # noqa: E402
from ai_video.production.registry import registry_semantic_sha256  # noqa: E402
from ai_video.production.video_requirement import GenerationIntent  # noqa: E402

TRIAL = os.environ.get("SD_TRIAL")         # one folder for a separate take: approval, report, ledger and unit folders
PILOT = REPO / os.environ.get("SD_PILOT", TRIAL or "outputs/ai-city-takeover/ep01/v4/pilot/sd")
UNITS = REPO / os.environ.get("SD_UNITS", TRIAL or P)
APPROVAL = PILOT / "preview-approval.json"
REPORT = PILOT / "continuity-report.json"
COVERAGE = V4 / "director-coverage.json"   # the Director's schema-4 coverage; its unit ids are the board clip ids
BOARD = "outputs/ai-city-takeover/ep01/v4/board/shots.json"
BOARD_SHA256 = "b5f599322f7f19daea1b7eb1f132bf640fdec4712c1cdf5da097ced5cfbe0107"   # 2026-11-23 s027 首帧换背影版 p027-b3（P027B/b）；此前 6840e33badcc2f23ce6680142391fa51d9b168ac28f710c42526d46704a88f29（2026-11-22 s027 首帧换 p027-b2（P027R/a）；此前 647cc110e8821ec442e06a6c2df769299b4ed25512de30cd00406ba2b34e0288（2026-11-22 加 s016 插镜 INS16（clips 里 SG06 之后，带 insert 文字）；此前 09fafac63c9079d9ec62d114e438008ca560d20847403844808ab37e9daa9f75（2026-11-22 s017 首帧换 p017-w2b（皮卡车头朝镜头）；此前 a009b70d0d35711dc54af2d5d0a687fb22c3b7d45091cf3c5c913a555b42c3fb（2026-11-22 唱段窗口按 s015 教训：SG06/SG09/SG10/SG11 窗口起点提前到句首前约 0.3 s；此前 b6fc004e5a49b52807401cbb4753fbed6e42c59bbdca60f661f718cebe3b92d2（2026-11-22 SG05 重拍 m：生成窗口起点 59.157→58.7（含 Ten oh），seconds 6.966；此前 19132f6e8a5d411f0ad3241ed1a47fe12de11267d12bac56a9a561b9c438a34e（2026-11-22 s024 首帧换重做车厢的 p024-b2（= P024R/b）；此前 34e9cd05f39b09cbc77c0931023a6444900bee0fe1e094b28055243801c401d1（2026-11-22 s015–s029 首帧换 p0NN-w1 / p0NN-b1、SG10 生成窗口起点 110.543→109.7027；此前 4fb460ca2a5c2baf4e87723a19b255f7ae214eb46a79308cd3f21aea106564d1（2026-11-21 MO07 首帧换 r4 修正版 p014-w1c；此前 4b620cb8166935bd2ef75fc25498d7aae84ee34a6bf0b9f2ad0b002c365812b4（2026-11-20 MO21 首帧换修正版 p009-w1b；此前 49b78ad4ee890935fbbfc66ecae001432143be4c2a7875dea526dfbf857e9472）））））））））
PLATES = "outputs/ai-city-takeover/ep01/v4/board/plates/"
ANCHOR = "outputs/ai-city-takeover/ep01/v4/face/IRIS-anchor-F1a.png"    # the v4 identity anchor (replaces canon v4 / E3)
ANCHOR_SHA256 = "2dd80e2f0ff55fbe24a95c5d881a2d2422421c7d94b7a066a3dc6f2e54d55b6a"
AUDIO = "outputs/ai-city-takeover/ep01/v4/pilot/audio/"
VOCALS = AUDIO + "windows.json"            # the vocal windows cut_audio.py cut from the v4 Demucs vocal stem
GENERATION = {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "4k", "aspect": "16:9",
              "audio": None}
GENERATION_LIPSYNC = {**GENERATION, "mode": "multimodal", "audio": "reference_audio"}
APPROVAL_ROLE = {"first_frame": "first frame", "multimodal": "reference image"}     # "<unit> <role>" in preview_artifacts
MARKERS = re.compile(r"\{\{(?:image|audio|video):\d+\}\}")
IDENTITY_TEXT = ("同一IRIS（v4身份锚点F1a）：银白色利落短发和侧分短刘海、银白眉毛和睫毛、很浅的冰灰色眼睛、"
                 "左耳亮着小红灯的黑色耳挂装置和耳骨上一排银色耳钉完整保持")
LOOK_TEXT = {"L1": "；造型1雕塑白：白色雕塑感短款立领外套与左侧立领的极细红灯线完整保持",   # board looks[].id
             "W1": "；二十八岁成熟、有棱角的脸，面无表情带着好奇；造型W1：灰色连帽衫改造的不对称高定短外套（一边长袖、"
                   "一边露肩）、斜挎黑色皮质背带、腰间细链挂黑色寻呼机和空白工牌、黑色高腰迷你裙、黑色及膝长靴完整保持；"
                   "没有立领灯线",
             "B": "；二十八岁成熟、有棱角的脸，面无表情带着好奇；造型B：黑色超大廓形的双排扣西装外套、白色高领上衣、黑色阔腿西裤"
                  "完整保持；没有立领灯线"}
# B (2026-11-22, s020-s029): the board's look LB (证人席, text pinned by BOARD_SHA256) worn by the W1 face; the user chose
# 「统一成开头的脸 (Recommended)」 on pilot/s015-030/preview/index.html (logs/decisions.md 2026-11-22). Plates p0NN-b1.
# W1 (2026-11-18, v4 round 1: s011 / s012): the remade identity (28, mature angular face, deadpan-curious; direct-flash
# snapshot plates) and wardrobe W1 are not in the board's fixed_text / looks; their text is taken verbatim from the
# approved plate prompts in v4-round1.md (V12a near, V11a far, wardrobe), pinned by sha. The anchor stays F1a.
ROUND1 = "outputs/ai-city-takeover/ep01/v4/excerpt/flash/v4-round1.md"
ROUND1_SHA256 = "8e7741b08d292706c1f01a0e2b2f8523ae38a56bc5d59c3262fa7940339b1a37"
W1_NEAR = ("一位二十八岁的成年白人女性，成熟的、有棱角的脸，颧骨分明，下颌线硬朗；银白色的利落短发，侧分的短刘海，眉毛和睫毛也是"
           "银白色，眼睛是很浅的冰灰色，皮肤冷白，鼻梁上有淡淡的雀斑，嘴唇是偏冷的裸色，眼尾一笔细细的深色眼线；左耳戴一只黑色的"
           "耳挂装置，装置上亮着一颗小红灯，左耳耳骨上一排小小的银色耳钉；她平时面无表情，但带着好奇，冷静地看着世界")
W1_FAR = "一位二十八岁的成年白人女性，成熟的、有棱角的脸，银白色的利落短发和银白色的眉毛，左耳一只亮着小红灯的黑色耳挂装置"
W1_WARDROBE = ("她穿一件用灰色连帽衫改造成的不对称高定短外套，一边袖子很长、一边露肩，外面斜挎一条黑色皮质背带，腰间一条细链挂着"
               "一台黑色老式寻呼机和一张空白工牌；黑色高腰迷你裙；黑色及膝长靴")
# look-dependent intent text (L1 keeps its original wording; W1 plates are cold white / cyan / amber, no collar line)
PALETTE = {"L1": "冷色调；红色只做讯号灯，是唯一暖色", "W1": "冷白、青蓝和琥珀色的夜间灯色；除了耳挂上的小红灯，没有任何红色",
           "B": "除了耳挂上的小红灯，画面里没有任何红色"}
# a spec may carry its own "palette" when its approved prompt names a different red rule (opening MO02 door light,
# MO21 no visible ear device); otherwise the look's palette applies
IDENTITY_CONTINUITY = {"L1": "人物身份、左耳装置与左侧立领红灯线位置一致（v4身份锚点F1a）",
                       "W1": "人物身份与左耳装置位置一致（v4身份锚点F1a），造型W1不变",
                       "B": "人物身份与左耳装置位置一致（v4身份锚点F1a），造型B不变"}
# a spec may carry its own "identity_continuity" when the look changes inside the take (s019 MO09: W1 -> B)
WAIVER = "首帧生视频：身份由使用者在预览中认可的首帧承担；认可的参考包只有首帧，不附身份图"
NO_TEXT = "画面中不新增任何文字、字母、数字、标志或图形；平台正常人工智能生成标识照常保留，不删除、不遮挡"


class Blocked(ValueError):
    pass


# intent paths each rule answers for (first match wins; anything unmatched belongs to the first rule)
CAMERA_KEYS = ("camera_", "axis_continuity", "space_continuity", "reference_planning.events", "motion_envelope", "pacing",
               "subject_action")
PERFORMANCE_KEYS = ("performance_intent", "subject_action", "motion_envelope", "pacing")
IDENTITY_KEYS = ("identity_continuity", "reference_planning.anchors", "reference_planning.selections")
LABEL_KEYS = ("visual_treatment", "ambience_intent", "dialogue_intent", "music_intent")
ZH_SECONDS = dict(enumerate(("零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四",
                             "十五")))
LOCKED = {"movement_kind": "locked", "direction": "none", "amplitude_class": "subtle", "speed_class": "very_slow",
          "start_motion_state": "stationary", "end_motion_state": "settled"}
LOCKED_INTENT = "摄影机完全固定，全程不推近、不移动、不摇镜"


# ---------------------------------------------------------------- v4 units (board/shots.json clips, 2026-11-17)
# Each spec is written for one clip, its pinned plate and a native prompt the user approves on the preview page. Every
# literal below (purpose, open/close events, natural motion) must appear in that text, so an approval whose prompt or
# image differs from what a spec was written for blocks the draft; write or update the spec first. Native prompts are
# pure Chinese (no Latin letters, so the board's "T 台" is written 走秀台).
def iris_performance(trigger, response, gaze, body, hands, terminal, face):
    return {"trigger": trigger, "visible_response": response, "gaze_target": gaze, "body_behavior": body,
            "hand_behavior": hands, "terminal_performance_state": terminal,
            "character_directions": [{"character_id": "IRIS", "screen_identity": IDENTITY_TEXT, "role": "principal",
                                      "visibility": "visible", "beats": [{"phase": "throughout", "trigger": trigger,
                                      "emotion": "平静", "intensity": "subtle", "facial_expression": face,
                                      "gaze_target": gaze, "breathing": "自然平稳", "body_behavior": body}]}]}


def clip_spec(unit: str, plate: str, plate_sha256: str, seconds: int, look: str, mode: str, scene: dict, purpose: str,
              intent: dict, performance: dict, relation: dict, rules: list, **extra) -> dict:
    """One board clip. seconds = ceil(clip.seconds) (+ take_margin_seconds when a spec names one); mode first_frame (MO..)
    or multimodal (SG.., lip-sync). vocal= names the sealed window (file and windows.json key) when it is not the unit id."""
    n = unit.lower()
    vocal = extra.pop("vocal", unit)
    spec = {"shot_id": "ep01v4-" + n, "beat": n, "iris": True, "duration": seconds, "coverage_unit": unit,
            "input_mode": mode, "look": look, "plate": plate, "plate_sha256": plate_sha256,
            "scene": scene, "camera_motion": LOCKED, "relation": relation, "intent": intent, "performance": performance,
            "rules": rules, **extra}
    if mode == "first_frame":
        aid = f"iris-c-v4-{n}-first-frame"
        spec |= {"generation": {**GENERATION, "seconds": seconds}, "frame_roles": {aid: "approved_keyframe"},
                 "conditioning": {"lane": "i2va", "first_anchor_id": aid, "available_duration_seconds": float(seconds)},
                 "identity_waiver": WAIVER if spec["iris"] else None}       # no person (iris=False): nothing to waive
    else:
        aid = f"iris-c-v4-{n}-reference"
        spec |= {"generation": {**GENERATION_LIPSYNC, "seconds": seconds}, "frame_roles": None,
                 "audio": {"asset_id": f"iris-c-v4-{n}-vocal", "path": AUDIO + vocal + ".wav", "window": vocal},
                 "identity_waiver": "全能参考对嘴：身份由使用者认可的参考图承担；认可的参考包只有这张图与人声窗口，不附身份图"}
    spec["image"] = (aid, PLATES + plate + ".png", scene["scene_id"], "scene_environment", purpose)
    return spec


def identity_rule(look: str, carrier: str) -> tuple:
    return ("identity", IDENTITY_TEXT + LOOK_TEXT[look] + f"（由认可的{carrier}承担）", 0,
            ("identity_waivers",) + IDENTITY_KEYS)


SPECS = {}
# v4 round 1 (2026-11-18): the user approved s011 and s012 remade from NEW first frames (look W1, direct-flash
# snapshots) with NEW short prompts, 「s011 选 1，s012 选 1，开拍」 on excerpt/flash/v4r1.html. Every required phrase
# below is a literal substring of that approved prompt; nothing the approved prompt lacks is required. The earlier L1
# plates (p011.png, p012.png) and excerpt prompts are superseded for these two clips (files kept).
#
# MO06 (s011, 40.79-44.94 s, Chorus): plate p011-w1b (= excerpt/flash/v4r1/V11a-2.png; the continuity supervisor
# blocked V11a-1 / p011-w1 for a bare RIGHT shoulder where every other W1 still bares the LEFT one, and the user chose
# 「改用 s011-2 (Recommended)」; same approved prompt), low angle from the front side;
# she strides along the wet runway while the front-row engineers stand up. Board "lights bang on" stays an edit move.
# Strap fix (2026-11-19): the continuity supervisor found the strap on p011-w1b running LEFT shoulder -> RIGHT hip,
# against W1 (right shoulder -> left hip). Plate now p011-w1c (= design/STRAP/s011-b.png): an edit of p011-w1b that only
# reverses the strap (design-frames.md STRAP); approved on strapfix.html 「两镜都用 b，拍 (Recommended)」. Same prompt.
SPECS["MO06"] = clip_spec("MO06", "p011-w1c", "22492025abac1e542346b54a26a0cfa19f78c00bb39a7448234618ff6e786b26", 5, "W1",
    "first_frame", {"scene_id": "garage-runway", "location": "地下停车场改成的秀场，湿的水泥走秀台，头顶一排排日光灯管",
                    "time": "深夜", "mood": "冷、面无表情、带着好奇"}, "低机位", {
        "open": "MO06首帧：低机位从侧前方拍，她沿着湿的水泥走秀台大步向前走，一只靴子正抬起，长的那只袖子向后扬起",
        "close": "两边前排的值班工程师一个接一个站起来，机位与构图不变",
        "action_start": "她大步向前走，一只靴子刚抬起", "progression": "抬起的那只靴子落地，重心越过支撑脚，长的那只袖子随后摆回",
        "endpoint": "她继续沿走秀台向前走，前排工程师站起来", "camera": LOCKED_INTENT,
        "framing": "MO06首帧：低机位，从侧前方拍，画面微微倾斜", "start_framing": "MO06首帧原始构图",
        "end_framing": "与起始相同的机位", "light": "相机直闪的硬闪光与头顶的日光灯管",
        "ambience": "几乎无声（成片使用独立音轨）", "space": "她沿走秀台向前走，前排工程师在原位站起",
        "motion_peak": "靴子落地，重心越过支撑脚",
        "natural": ["抬起的那只靴子落地", "重心越过支撑脚", "长的那只袖子随后摆回", "面无表情，带着一点好奇看着前方"],
        "open_event": ("她沿着湿的水泥走秀台大步向前走", "镜头固定"),
        "close_event": ("两边前排的值班工程师一个接一个站起来", "从侧前方拍")},
    iris_performance("副歌开场", "大步向前走，靴子落地、重心越过支撑脚、长袖摆回", "前方", "大步向前走",
                     "长的那只袖子随步子摆回", "继续向前走", "面无表情，带着一点好奇"),
    {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "低机位从侧前方拍，她在走秀台上",
     "end_relation": "机位不变，她沿走秀台向前走"},
    [identity_rule("W1", "首帧"),
     ("performance", "她大步向前走：抬起的靴子落地，重心越过支撑脚，长袖随后摆回；面无表情带着好奇；前排值班工程师一个接一个"
                     "站起来，不新增人物", 0, PERFORMANCE_KEYS),
     ("camera", LOCKED_INTENT + "，保持首帧的低机位侧前方构图", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)])

# SG03 (s012, 44.94-50.93 s, Chorus "hold on tight / I'm the reason you're awake"): the v3 U021 lip-sync method on plate
# p012-w1 (= excerpt/flash/v4r1/V12a-1.png) and the clip's exact vocal window (pilot/audio/SG03.wav, unchanged). The
# plate is a closed-mouth start (the window opens on 0.68 s of silence); the approved short prompt does not restate it,
# so it is not a required phrase: the lip-sync rule (lips closed where there is no voice) and the plate carry it. The
# board's 4% push stays an edit move; the generated take is locked. Lyric timing: "hold" 0.68 s, "awake" ends 5.43 s.
LIPSYNC_KEYS = ("dialogue_intent", "performance_intent", "subject_action", "motion_envelope", "pacing")
LIPSYNC = "歌词期间嘴在唱、与参考人声逐字同步，无声处嘴唇闭合；对嘴准确度由片段自带音轨与参考人声的对齐量测和使用者审看判定"
SPECS["SG03"] = clip_spec("SG03", "p012-w1", "720e8f3cb1bbea1ca82c451a7c87a9f410ff0d38f97ffe2ce761d9894acec9f8", 6, "W1",
    "multimodal", {"scene_id": "runway-front-row", "location": "地下停车场秀场的前排，值班工程师的折叠椅",
                   "time": "深夜", "mood": "冷、面无表情、带着好奇"}, "中近景", {
        "open": "SG03参考图：中近景，她弯腰凑到穿深蓝色工装夹克的值班工程师面前，一只手撑在他的椅背上，嘴唇轻轻合上",
        "close": "唱完这两句，机位与构图不变",
        "action_start": "她凑在他面前，嘴唇轻轻合上", "progression": "对着值班工程师唱歌，口型与参考人声逐字同步",
        "endpoint": "唱完这两句", "camera": LOCKED_INTENT,
        "framing": "SG03参考图：中近景，从侧前方拍，她的脸在画面右三分之一", "start_framing": "SG03参考图原始构图",
        "end_framing": "与起始相同的构图", "light": "相机直闪的硬闪光与笔记本电脑屏幕的冷光",
        "ambience": "片段自带音轨跟随参考人声（成片换成歌曲母带）", "space": "她和他都在原位",
        "motion_peak": "对着他唱副歌", "natural": ["嘴前没有任何遮挡"],
        "open_event": ("对着值班工程师唱歌", "逐字精确同步"), "close_event": ("镜头全程锁定", "一镜到底")},
    iris_performance("副歌这两句", "对着值班工程师唱，口型与参考人声逐字同步", "看着他", "弯腰凑在他面前",
                     "一只手撑在他的椅背上", "唱完这两句", "面无表情，带着好奇"),
    {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "中近景，她凑在他面前，脸在画面右三分之一",
     "end_relation": "构图与机位不变"},
    [identity_rule("W1", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，一镜到底", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue={"mode": "dialogue", "language": "en", "speaker_id": "IRIS",
              "verbatim_text": "hold on tight I'm the reason you're awake", "start_seconds": 0.68, "end_seconds": 5.43,
              "on_screen": True, "response_obligation": "对着他唱出这两句，口型与参考人声逐字同步", "lip_sync_required": True})


# SG03C (s012b, 2026-11-19 redesign of s012): the closed-eye singing close-up for "reason you're awake"; the edit plays
# it from the 48.17 downbeat to 50.933. Plate p012c-w1 (= excerpt/flash/design/D1-b.png, prompt design-frames.md D1),
# vocal window 46.93-50.93 (4 s; starts in the gap after "tight" 46.81 and before "I'm" 47.517) cut by cut_audio.py.
# Approved prompt on excerpt/flash/closeup.html; every required phrase is a literal substring of it. Lyric timing:
# "I'm" starts 0.59 s and "awake" ends 3.44 s into the window. The plate's mouth is open (a held note) while the window
# opens on 0.59 s of silence; the edit does not use that part (it starts 1.24 s in).
# Plate swap (2026-11-19): the continuity supervisor blocked p012c-w1 (D1-b: RIGHT shoulder bare, strap reversed vs the
# accepted SG03-w1 at a mid-line cut). Plate now p012c-w1b (= design/D2-b.png, prompt design-frames.md D2): LEFT shoulder
# bare, strap right shoulder -> left hip, hoodie fabric, the engineer's laptop held upright nearly closed. Same prompt.
# Second swap (2026-11-19): D2-b blocked too (no black turtleneck vs SG03-w1). Plate now p012c-w1c (= design/D3-b.png,
# prompt D3: black turtleneck underlayer, the jacket slipped off the LEFT shoulder, grey long sleeve on the left forearm,
# strap right shoulder -> left hip). The user saw it beside SG03-w1 f12 on closeup2.html: 「可以，拍 (Recommended)」.
# Third swap (2026-11-19): the SG03C-c take failed its Gate (camera orbited, the foreground engineer was lost, the venue
# differed from SG03-w1, early mouth at the start, empty mouthing at the end; pilot/sd-SG03C-c/post-media-gate.json).
# Plate now p012c-w1d (= design/D4/D4-a.png, prompt design-frames.md D4: an edit of the SG03-w1 4K frame
# design/D4/D4-base.png pushed in on her face: same garage, same camera axis, the same engineer in the left foreground;
# eyes closed, chin up, lips closed). New approved prompt on closeup3.html (「D4-a，拍 (Recommended)」): every required
# phrase below is a literal substring of it; the camera rule also names the foreground engineer (lost last time).
SPECS["SG03C"] = clip_spec("SG03C", "p012c-w1d", "21c5f96a6cdbdf4f39d99b9137e4092776d4f3b4d77adba4178532c473682c48", 4,
    "W1", "multimodal", {"scene_id": "runway-front-row-closeup", "location": "地下停车场改成的秀场前排，与 SG03-w1 同一处",
                         "time": "深夜", "mood": "投入、几乎忘我"}, "近景", {
        "open": ("SG03C参考图：停车场秀场前排，左前景是穿深蓝工装夹克的工程师的头和肩；她俯身，闭着眼睛，下巴抬起，嘴唇合上；"
                 "黑色高领，外套在左肩滑落露出左肩，黑色斜挎带从右肩到左胯；画面里只有左耳挂一处红灯"),
        "close": "唱完这一句，机位与构图不变，左前景的工程师仍在画面里",
        "action_start": "她闭着眼睛俯身，嘴唇合上", "progression": "闭着眼睛唱歌，口型与参考人声逐字同步",
        "endpoint": "唱完这一句", "camera": LOCKED_INTENT,
        "framing": "SG03C参考图：近景，与 SG03-w1 同一机位轴线，左前景是工程师的头和肩", "start_framing": "SG03C参考图原始构图",
        "end_framing": "与起始相同的构图", "light": "相机机头直闪与前排笔记本屏幕的光",
        "ambience": "片段自带音轨跟随参考人声（成片换成歌曲母带）", "space": "她和左前景的工程师都在原位",
        "motion_peak": "唱 reason 的长音", "natural": ["机头直闪", "左前景的工程师一直在画面里", "嘴前没有任何遮挡"],
        "open_event": ("她闭着眼睛唱歌", "逐字精确同步"), "close_event": ("镜头固定不动，不推不拉不摇不环绕", "一镜到底")},
    iris_performance("副歌这一句", "闭着眼睛唱，口型与参考人声逐字同步", "闭着眼睛", "俯身，下巴抬起",
                     "双手不入画", "唱完这一句", "投入的、几乎忘我的神情"),
    {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "近景，她俯身，左前景是工程师的头和肩",
     "end_relation": "构图与机位不变，工程师仍在左前景"},
    [identity_rule("W1", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，不环绕，一镜到底；左前景的工程师一直在画面里", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue={"mode": "dialogue", "language": "en", "speaker_id": "IRIS", "verbatim_text": "I'm the reason you're awake",
              "start_seconds": 0.59, "end_seconds": 3.44, "on_screen": True,
              "response_obligation": "闭着眼睛唱出这一句，口型与参考人声逐字同步", "lip_sync_required": True})


# ---------------------------------------------------------------- excerpt 26.05-59.23 s (pilot/excerpt/preview-inputs.json)
# The user approved these units and their exact prompts on the excerpt page (Seedance 2.0 VIP 4k). Every required phrase
# below is a literal substring of the approved prompt (test_excerpt_approved_prompts_pass_the_prompt_lint); the generated
# camera is locked as each approved prompt says (镜头固定 / 镜头全程锁定). The board's small camera shakes (MO04 leaves,
# MO05 kick) and SG02's 3% push are left to the edit. s009 is a plate3d shot: no clip, no unit.
def _board_scene(scene_id: str, location: str, time: str = "深夜", mood: str = "冷、压迫、不羁") -> dict:
    return {"scene_id": scene_id, "location": location, "time": time, "mood": mood}


def _fixed(start: str, end: str) -> dict:
    return {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": start, "end_relation": end}


def _motion_rules(performance: str, look: str = "L1") -> list:
    return [identity_rule(look, "首帧"), ("performance", performance, 0, PERFORMANCE_KEYS),
            ("camera", LOCKED_INTENT + "，保持首帧构图", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)]


def _lipsync_rules(lipsync: str, look: str = "L1") -> list:
    return [identity_rule(look, "参考图"), ("lip-sync", lipsync, 0, LIPSYNC_KEYS),
            ("camera", LOCKED_INTENT + "，一镜到底", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)]


LIPSYNC_SPOKEN = "念白期间嘴在说、与参考人声逐字同步，无声处嘴唇闭合；对嘴准确度由片段自带音轨与参考人声的对齐量测和使用者审看判定"

# MO04 / SG02 / MO05: the excerpt specs (look L1, plates p007 / p008 / p010, the excerpt prompts and the SG02 retake
# wording) were superseded on 2026-11-20 by the opening set below (W1 first frames p007-w1 / p008-w1 / p010-w1 and the
# prompts of excerpt/flash/opening-seedance.md, approved 「按页面拍 (Recommended)」 on pilot/opening/index.html). The
# replaced definitions are kept verbatim in unit.py.before-opening-2026-11-20 (this folder); pilot/sd-MO04, sd-SG02,
# sd-SG02-r2 and sd-MO05 are left as they are.

# Round 2 (2026-11-19, W1): the user approved 「s013 用 b、s014 用 c，拍 (Recommended)」 on excerpt/flash/round2.html,
# two takes each. The excerpt (L1) specs for these two clips are superseded; every required phrase below is a literal
# substring of the round-2 prompt on that page.
# SG04 (s013, 50.93-55.08 s, "I'm the call you had to take / All hands"): the engineer's upward reverse shot; plate
# p013-w1 (= design/R2/S13-b.png, prompt design-frames.md S13): she stands straight, looks down into the lens, lips
# closed, the lit phone held below her chest in her right hand, the engineer's empty hand (navy work-jacket cuff) lower
# left. Throwing the phone back is an edit insert, not acted by the model (it would disturb the lip-sync).
SPECS["SG04"] = clip_spec("SG04", "p013-w1", "2f159721e0da2b9e2247a32fadd14ec79b3628152c911f07cee5c2c4dd1f3f21", 5, "W1",
    "multimodal", _board_scene("runway-front-row-reverse", "地下停车场改成的秀场前排，值班工程师的座位前", mood="冷、面无表情、带着好奇"),
    "仰拍中近景", {
        "open": ("SG04参考图：工程师仰视她的反打，停车场秀场；她站直，低头看着镜头，嘴唇合上；右手把屏幕亮着的手机拿在胸口下方；"
                 "左下角是工程师穿深蓝工装袖口的空手"),
        "close": "唱完这一句，手机仍在胸口下方，机位与构图不变",
        "action_start": "她站直低头看着镜头，嘴唇合上", "progression": "低头看着镜头唱歌，口型与参考人声逐字同步",
        "endpoint": "唱完这一句，手机仍在胸口下方", "camera": LOCKED_INTENT,
        "framing": "SG04参考图：仰拍中近景，相机在坐着的工程师的视线高度", "start_framing": "SG04参考图原始构图",
        "end_framing": "与起始相同的构图", "light": "相机机头直闪与手机屏幕从下往上的冷白光",
        "ambience": "片段自带音轨跟随参考人声（成片换成歌曲母带）", "space": "她站在原位",
        "motion_peak": "唱 call 与 take", "natural": ["机头直闪", "手机一直拿在胸口下方，不举到脸边", "嘴前没有任何遮挡"],
        "open_event": ("她低头看着镜头唱歌", "逐字精确同步"), "close_event": ("镜头固定不动，不推不拉不摇不环绕", "一镜到底")},
    iris_performance("副歌这一句", "低头看着镜头唱，口型与参考人声逐字同步", "镜头", "站直，低头",
                     "右手把亮屏手机拿在胸口下方，不举到脸边", "唱完这一句", "面无表情，带着好奇"),
    _fixed("仰拍中近景，她站直低头看镜头", "构图与机位不变"),
    [identity_rule("W1", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，不环绕，一镜到底；手机一直在胸口下方，不挡嘴", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue={"mode": "dialogue", "language": "en", "speaker_id": "IRIS",
              "verbatim_text": "I'm the call you had to take All hands!", "start_seconds": 0.31, "end_seconds": 4.16,
              "on_screen": True, "response_obligation": "低头看着镜头唱出这一句，口型与参考人声逐字同步", "lip_sync_required": True})

# MO07 (s014, 55.08-59.23 s): long-lens frontal on the runway end; plate p014-w1 (= design/R2/S14-c.png, prompt S14):
# weight on the front foot, the turn just starting, sleeve and hem lifting; engineers with laptops on both sides.
# Strap fix (2026-11-19): S14-c had the strap reversed too; plate now p014-w1b (= design/STRAP/s014-b.png, an edit of
# p014-w1 that only reverses the strap); same round-2 prompt. The MO07-r2 trials (never submitted) are superseded.
# 2026-11-21 r3 retake (user 「按 v2 做，s014 开拍 (Recommended)」 on pilot/opening/plan/v2.html; prompt text in
# excerpt/flash/s014-r3-seedance.md): same plate p014-w1b, same 5 s; the engineers keep their heads down on their laptops
# the whole time (the s-2 take had them looking up and down) and the pager lights no red. The s-2 spec wording
# (kept in unit.py.before-mo07-r3-2026-11-21) required 「两侧的值班工程师抬头看着她」 and described them looking up.
# 2026-11-21 r4 retake (user 「用 a 拍 (Recommended)」 on pilot/opening/review-s014r4/index.html; prompt text in
# excerpt/flash/s014-r4-seedance.md): the r3 takes failed the Gate because the engineers in the p014-w1b first frame were
# already looking up; plate now p014-w1c (= excerpt/flash/design/S14r4/a.png, engineers all heads down), and the r4 prompt
# adds 「她始终完整在画面里，头顶不出画。」 after 「朝画面右侧走开。」. The r3 spec is in unit.py.before-mo07-r4-2026-11-21.
# 2026-11-21 r5 retake (user 「按页面改 prompt 拍 r5 (Recommended)」 on pilot/opening/review-s014r5/index.html; prompt in
# excerpt/flash/s014-r5-seedance.md): both r4 takes walked toward the camera for 1.5-2.5 s first (「她走到走秀台尽头」 read
# as an approach) and her head left the top edge; same plate p014-w1c, the action now starts already stopped at the
# runway end and exits away from the camera. The r4 spec is in unit.py.before-mo07-r5-2026-11-21.
# 2026-11-21 r6 retake (user 「按页面拍 r6 (Recommended)」 on pilot/opening/review-s014r6/index.html; prompt in
# excerpt/flash/s014-r6-seedance.md): both r5 takes moved the pager to her back once she turned away (the press was written
# after the turn); the press now comes first, right hand, on the front waist chain, and pager and badge stay in front.
# s014c becomes an insert. The r5 spec is in unit.py.before-mo07-r6-2026-11-21.
SPECS["MO07"] = clip_spec("MO07", "p014-w1c", "ae34b54393afe1df4e15f35326de17752734af1f3661b2c4a307adec89f74374", 5, "W1",
    "first_frame", _board_scene("runway-end-w1", "地下停车场改成的秀场，走秀台的尽头，两侧坐着抱笔记本电脑的值班工程师",
                                mood="冷、面无表情、带着好奇"), "长焦全身远景", {
        "open": "MO07首帧：长焦全身远景正对走秀台尽头，她重心落在前脚，身体开始转，长袖和外套下摆开始甩开；两侧是值班工程师",
        "close": "她头也不回地按住寻呼机朝画面右侧走开，机位与构图不变",
        "action_start": "她已经停在走秀台尽头，不再往前走，站在原地", "progression": "一个干脆的急转身，长袖和外套下摆甩成一个圆再落下",
        "endpoint": "她背对镜头朝画面右侧走开，越走越远，寻呼机和工牌留在身前的腰链上", "camera": LOCKED_INTENT,
        "framing": "MO07首帧：长焦全身远景，正对走秀台尽头", "start_framing": "MO07首帧原始构图", "end_framing": "与起始相同的机位",
        "light": "相机机头直闪、天花板的青色灯管与笔记本屏幕的冷白光", "ambience": "几乎无声（成片使用独立音轨）",
        "space": "她在走秀台尽头转身，朝画面右侧走开", "motion_peak": "急转身，长袖和外套下摆甩成一个圆",
        "natural": ["不再往前走", "然后松开手", "站在原地一个干脆的急转身", "寻呼机和工牌一直挂在她身前的腰链上，背对镜头时看不见", "背对镜头朝画面右侧走开，越走越远", "长袖和外套下摆甩成一个圆再落下", "她头也不回",
                    "两侧的值班工程师一直低头盯着自己腿上的笔记本电脑", "全程不抬头，身体保持不动",
                    "她腰间的寻呼机不亮任何红灯", "她始终完整在画面里，头顶不出画"],
        "open_event": ("她已经停在走秀台尽头", "镜头固定不动"),
        "close_event": ("背对镜头朝画面右侧走开", "先低头用右手按住身前腰链上震动的黑色寻呼机")},
    iris_performance("腰间的寻呼机震动", "先用右手按住身前的寻呼机，再急转身甩开长袖，头也不回地背对镜头走远", "前方", "急转身后朝画面右侧走",
                     "右手按住身前腰链上的寻呼机后松开", "背对镜头朝画面右侧走开", "面无表情"),
    _fixed("长焦全身远景，她在走秀台尽头", "机位不变，她朝画面右侧走开"),
    _motion_rules("她停在走秀台尽头不再往前走，先用右手按住身前腰链上的寻呼机再松开，原地急转身、长袖和外套下摆甩成一个圆再落下，头也不回地背对镜头朝画面右侧走远，寻呼机和工牌留在身前腰链上；两侧值班工程师一直低头看笔记本电脑、全程不抬头、身体不动，"
                  "寻呼机不亮红灯；不新增人物", look="W1"))


# ---------------------------------------------------------------- opening s001-s010, 0-40.79 s (2026-11-20, W1)
# The user approved the opening Seedance preview pack 「按页面拍 (Recommended)」 on pilot/opening/index.html (inputs
# pilot/opening/preview-inputs.json, prompts excerpt/flash/opening-seedance.md sha 3e02c326…): each unit from a W1 first
# frame (board/plates/p0NN-w1.png = excerpt/flash/design/OPEN/OPNN-x.png byte for byte), two takes per unit from the same
# frame. Every required phrase below is a literal substring of that unit's approved prompt; nothing the prompt lacks is
# required. s003 / s005 / s009 were plate3d stills: they are now motion clips MO19 / MO20 / MO21 (4 s windows from the
# shot's cut, the MO04 convention). The camera follows each approved prompt: MO01 pushes in very slowly, MO02 backs away
# with her steps, MO03 is a handheld lead in front of her; every other unit is locked (镜头固定). The board's small
# camera shakes (MO04 leaves, MO05 kick) and SG02's 3% push stay edit moves.
OPEN_MOOD = "冷、面无表情、带着好奇"
SPECS["MO01"] = clip_spec("MO01", "p001-w1", "63b1195d4528a7b75c7c1999abc3596499bee7a6d1bbe8920eb9f58aed37a611", 5, "W1",
    "first_frame", _board_scene("garage-backstage", "地下停车场改成的秀场后台，折叠化妆台，围着灯泡的化妆镜在机位旁边（不入画）",
                                mood=OPEN_MOOD), "镜头在化妆镜旁正面拍她", {
        "open": "MO01首帧：化妆镜旁正面近景，她闭着眼，化妆师的粉扑按在她颧骨上，黑色寻呼机还在台面上",
        "close": "她从椅子上站起半身，寻呼机握在下巴下方，镜头已极慢地推近",
        "action_start": "她闭着眼，化妆师的粉扑按在她颧骨上",
        "progression": "她睁开眼，用两根手指把粉扑推开，从台面拿起黑色寻呼机，在掌心掂一下，用拇指按掉它",
        "endpoint": "她从椅子上站起半身，寻呼机握在下巴下方", "camera": "摄影机在化妆镜旁正面拍她，全程极慢地推近，不摇、不环绕",
        "framing": "MO01首帧：化妆镜旁正面近景", "start_framing": "MO01首帧原始构图", "end_framing": "同一机位轴线上极慢推近后的近景",
        "light": "相机机头直闪与化妆灯泡", "ambience": "几乎无声（成片使用独立音轨）", "space": "她在化妆台前，从坐着到站起半身",
        "motion_peak": "用拇指按掉寻呼机，站起半身", "envelope_direction": "向前极慢推近",
        "natural": ["用两根手指把粉扑推开"],
        "open_event": ("她闭着眼，化妆师的粉扑按在她颧骨上", "极慢地推近"),
        "close_event": ("从椅子上站起半身，寻呼机握在下巴下方", "用拇指按掉它")},
    iris_performance("寻呼机的提示", "睁眼推开粉扑，拿起寻呼机掂一下按掉，站起半身", "前方", "从坐着到站起半身",
                     "两根手指推开粉扑，拿起寻呼机在掌心掂一下，用拇指按掉", "站起半身，寻呼机握在下巴下方",
                     "面无表情，带着一点好奇"),
    {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "化妆镜旁正面近景，她坐在化妆台前",
     "end_relation": "同一机位轴线极慢推近，她站起半身"},
    [identity_rule("W1", "首帧"),
     ("performance", "她睁眼，两根手指推开粉扑，拿起黑色寻呼机在掌心掂一下、用拇指按掉，站起半身，寻呼机握在下巴下方；"
                     "不新增人物", 0, PERFORMANCE_KEYS),
     ("camera", "摄影机在化妆镜旁正面拍她，全程极慢地推近，不摇、不环绕、不拍镜中像", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    camera_motion={"movement_kind": "dolly_in", "direction": "forward", "amplitude_class": "subtle",
                   "speed_class": "very_slow", "start_motion_state": "stationary", "end_motion_state": "settled"},
    stability="极慢平稳推近", settle="末段平稳停住")

SPECS["MO02"] = clip_spec("MO02", "p002-w1", "4cdc13467ed25a2fb32cb0b022988cca11cf44d56b0aa67b2084a1ed75f226fb", 6, "W1",
    "first_frame", _board_scene("garage-runway-entrance", "地下停车场改成的秀场，混凝土柱子、半开的灰色消防门、湿亮的水泥走秀台和两排前排座位",
                                mood=OPEN_MOOD), "机位在走秀台尽头", {
        "open": "MO02首帧：长焦，机位在走秀台尽头，她从混凝土柱子旁大步走出来，黑色寻呼机还握在手里",
        "close": "她踏上湿亮的水泥走秀台向镜头走来，两边前排的人低头看笔记本",
        "action_start": "她从混凝土柱子旁大步走出来，寻呼机握在手里",
        "progression": "边走边把寻呼机别到腰链上，经过半开的消防门，门缝里的一道红光扫过她的靴子",
        "endpoint": "她踏上湿亮的水泥走秀台向镜头走来", "camera": "长焦，摄影机在走秀台尽头随她的步子轻微后退，不摇、不环绕",
        "framing": "MO02首帧：长焦全身，机位在走秀台尽头", "start_framing": "MO02首帧原始构图",
        "end_framing": "同一轴线上轻微后退后的长焦全身", "light": "相机机头直闪、停车场灯管与门缝里的一道红光",
        "ambience": "几乎无声（成片使用独立音轨）", "space": "她从柱子旁走上走秀台，朝镜头走来",
        "motion_peak": "门缝里的红光扫过她的靴子", "envelope_direction": "随她的步子轻微后退",
        "natural": ["边走边把手里的黑色寻呼机别到腰链上", "门缝里的一道红光扫过她的靴子"],
        "open_event": ("她从混凝土柱子旁大步走出来", "随她的步子轻微后退"),
        "close_event": ("她踏上湿亮的水泥走秀台向镜头走来", "两边前排的人低头看笔记本")},
    iris_performance("开场", "大步走出来，边走边把寻呼机别到腰链上，踏上走秀台朝镜头走来", "前方", "大步向前走",
                     "把手里的黑色寻呼机别到腰链上", "在走秀台上朝镜头走来", "面无表情"),
    {"subject_id": "IRIS", "relation_kind": "maintain_offset", "start_relation": "长焦，她在柱子旁，机位在走秀台尽头",
     "end_relation": "摄影机随她的步子轻微后退，她在走秀台上朝镜头走来"},
    [identity_rule("W1", "首帧"),
     ("performance", "她大步走出来，边走边把寻呼机别到腰链上，经过半开的消防门，踏上走秀台朝镜头走来；两边前排的人低头看笔记本，"
                     "不新增人物", 0, PERFORMANCE_KEYS),
     ("camera", "长焦，摄影机在走秀台尽头随她的步子轻微后退，不摇、不环绕", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    camera_motion={"movement_kind": "dolly_out", "direction": "backward", "amplitude_class": "subtle",
                   "speed_class": "slow", "start_motion_state": "stationary", "end_motion_state": "continuing"},
    stability="长焦平稳轻微后退", settle="与她的步子同速后退",
    palette="冷白、青蓝和琥珀色的夜间灯色；除了耳挂上的小红灯和门缝里的一道信号红光（分镜规定），没有任何红色")

SPECS["MO19"] = clip_spec("MO19", "p003-w1", "a20283d6bf24e702cbfb1ecc210dc97aba704366bdaf21f2cfa2a8d9d036ab61", 4, "W1",
    "first_frame", _board_scene("runway-front-row-ots", "地下停车场改成的秀场前排，值班工程师缩在折叠椅里，笔记本电脑在膝上",
                                mood=OPEN_MOOD), "从坐着的值班工程师肩后拍", {
        "open": "MO19首帧：从坐着的值班工程师肩后拍，他在打瞌睡，手里的手机刚亮，笔记本电脑在膝上；她在走秀台上",
        "close": "整排前排的人低头看手机，屏幕一部接一部亮起；她朝镜头走来，机位与构图不变",
        "action_start": "工程师打瞌睡，手里的手机突然亮起", "progression": "他惊醒，笔记本电脑滑下去一半；前排的手机一部接一部亮起",
        "endpoint": "她在湿亮的走秀台上朝镜头走来，谁也不看", "camera": LOCKED_INTENT,
        "framing": "MO19首帧：过肩镜头，前景是工程师的肩和后脑", "start_framing": "MO19首帧原始构图",
        "end_framing": "与起始相同的构图", "light": "相机机头直闪与手机屏幕的冷光", "ambience": "几乎无声（成片使用独立音轨）",
        "space": "工程师在前景原位，她在走秀台上朝镜头走来", "motion_peak": "前排屏幕一部接一部亮起",
        "natural": ["膝盖上的笔记本电脑滑下去一半"],
        "open_event": ("他被手里突然亮起的手机惊醒", "镜头固定"),
        "close_event": ("她在湿亮的走秀台上朝镜头走来，谁也不看", "屏幕一部接一部亮起")},
    iris_performance("前排的手机亮起", "在走秀台上朝镜头走来，谁也不看", "前方", "朝镜头走来", "双手自然下垂",
                     "继续朝镜头走来", "面无表情"),
    _fixed("过肩镜头，她在走秀台上", "构图与机位不变，她朝镜头走来"),
    _motion_rules("前景的值班工程师被亮起的手机惊醒，笔记本电脑滑下去一半；前排的手机一部接一部亮起；她在走秀台上朝镜头走来，"
                  "谁也不看，不新增人物", look="W1"))

SPECS["SG01"] = clip_spec("SG01", "p004-w1", "b012df34e10b3ef713e63f4011d7aadc331d0e765abe1b0d2d22de5ec928fc4c", 6, "W1",
    "multimodal", _board_scene("runway-call-box", "走秀台尽头，一根混凝土柱子上的停车场紧急呼叫柱（带螺旋线电话听筒）",
                               mood=OPEN_MOOD), "中景", {
        "open": "SG01参考图：中景，她站在呼叫柱旁，正对镜头，嘴唇合上，听筒挂在机座上，身后前排的手机还暗着",
        "close": "她伸直手臂把听筒举在身侧，离脸一臂远，说完这两句，机位与构图不变",
        "action_start": "她站在呼叫柱旁正对镜头，嘴唇合上", "progression": "对着镜头平平地说话，口型与参考人声逐字同步；后半句侧身摘下听筒",
        "endpoint": "听筒举在身侧，离脸一臂远，说完这两句", "camera": LOCKED_INTENT,
        "framing": "SG01参考图：中景，她正对镜头", "start_framing": "SG01参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪与身后前排手机的冷光", "ambience": "片段自带音轨跟随参考人声（成片换成歌曲母带）",
        "space": "她在呼叫柱旁原位，全程正对镜头", "motion_peak": "侧身摘下听筒，伸直手臂举在身侧",
        "natural": ["不贴耳也不挡嘴", "嘴前没有任何遮挡"],
        "open_event": ("对着镜头平平地说话", "逐字精确同步"),
        "close_event": ("伸直手臂把听筒举在身侧，离脸一臂远", "镜头固定不动")},
    iris_performance("念白两句", "对着镜头平平地说，口型与参考人声逐字同步；后半句摘下听筒举在身侧", "镜头",
                     "站在呼叫柱旁，全程正对镜头", "后半句侧身摘下听筒，伸直手臂举在身侧，离脸一臂远", "听筒举在身侧，说完",
                     "面无表情，带着一点好奇"),
    _fixed("中景，她在呼叫柱旁正对镜头", "构图与机位不变，她仍正对镜头"), _lipsync_rules(LIPSYNC_SPOKEN, look="W1"),
    dialogue={"mode": "dialogue", "language": "en", "speaker_id": "IRIS",
              "verbatim_text": "Incident Week. Every look got somebody paged. A training run phoned a friend.",
              "start_seconds": 0.15, "end_seconds": 5.48, "on_screen": True,
              "response_obligation": "对着镜头平平地说出这两句，口型与参考人声逐字同步", "lip_sync_required": True})

SPECS["MO20"] = clip_spec("MO20", "p005-w1", "4d3f102771e6f3f8b162c7f3942103dc371051f27f8c70761af07de7e731021b", 4, "W1",
    "first_frame", _board_scene("runway-call-box-close", "同一根柱子，紧急呼叫柱旁", mood=OPEN_MOOD), "近景", {
        "open": "MO20首帧：近景，她刚松开听筒，听筒吊在螺旋线上，她手里拿着一张完整的白纸",
        "close": "她一半白纸扔出画面，一半夹在两指间，低头看着它，构图不变",
        "action_start": "她松开手，听筒顺着螺旋线垂下去", "progression": "听筒来回晃；她把白纸从中间撕开，一半扔出画面",
        "endpoint": "一半白纸夹在两指间，她低头看着它", "camera": LOCKED_INTENT,
        "framing": "MO20首帧：近景", "start_framing": "MO20首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪", "ambience": "几乎无声（成片使用独立音轨）", "space": "她在呼叫柱旁原位",
        "motion_peak": "白纸从中间撕开", "natural": ["她把手里那张白纸从中间撕开"],
        "open_event": ("听筒顺着螺旋线垂下去来回晃", "镜头固定"),
        "close_event": ("一半夹在两指间，低头看着它", "一半扔出画面")},
    iris_performance("念白之后", "撕开白纸，一半扔出画面，一半夹在两指间低头看", "手里的白纸", "站定，低头",
                     "松开听筒，撕开白纸，一半夹在两指间", "低头看着两指间的半张白纸", "面无表情"),
    _fixed("近景，她在呼叫柱旁", "构图与机位不变"),
    _motion_rules("她松开听筒，听筒顺着螺旋线来回晃；她把白纸从中间撕开，一半扔出画面，一半夹在两指间低头看，不新增人物",
                  look="W1"))

SPECS["MO03"] = clip_spec("MO03", "p006-w1", "aa0679464dec0a0872a858ea07db291f73bf79046f1784a1a7b33c2e0f0af09c", 6, "W1",
    "first_frame", _board_scene("folsom-sidewalk", "秀场外的 Folsom 街人行道，深夜，湿亮的地面，街角是行道树", mood=OPEN_MOOD),
    "手持跟拍", {
        "open": "MO03首帧：手持，在她侧前方；一群街拍摄影师倒退着走在她前面举着相机，她大步走来，手还没碰到镜头",
        "close": "她从摄影师中间穿过去，走向街角的行道树",
        "action_start": "她大步走来，摄影师倒退着在她前面按闪光灯",
        "progression": "她不减速，伸手掌平按住最近一台相机的镜头往下压，从他们中间穿过去",
        "endpoint": "她走向街角的行道树", "camera": "手持跟拍，摄影机在她侧前方随她倒退移动，不环绕",
        "framing": "MO03首帧：手持中全景，在她侧前方", "start_framing": "MO03首帧原始构图",
        "end_framing": "手持跟在她侧前方，她穿过摄影师走向行道树", "light": "街拍摄影师的闪光灯、路灯与湿亮地面的反光",
        "ambience": "几乎无声（成片使用独立音轨）", "space": "她沿人行道向前走，摄影师在她前面倒退",
        "motion_peak": "手掌平按住最近一台相机的镜头往下压", "envelope_direction": "在她侧前方随她倒退",
        "natural": ["伸手掌平按住最近一台相机的镜头往下压", "不停按闪光灯"],
        "open_event": ("一群街拍摄影师倒退着走在她前面", "在她侧前方"),
        "close_event": ("从他们中间穿过去，走向街角的行道树", "她不减速")},
    iris_performance("街拍摄影师围上来", "不减速，按下最近一台相机的镜头，从他们中间穿过去", "前方", "大步向前走，不减速",
                     "伸手掌平按住最近一台相机的镜头往下压", "走向街角的行道树", "面无表情"),
    {"subject_id": "IRIS", "relation_kind": "lead", "start_relation": "手持在她侧前方，摄影师倒退着走在她前面",
     "end_relation": "手持仍在她侧前方，她从摄影师中间穿过去走向行道树"},
    [identity_rule("W1", "首帧"),
     ("performance", "她不减速，伸手掌平按住最近一台相机的镜头往下压，从倒退着按闪光灯的摄影师中间穿过去，走向街角的行道树；"
                     "不新增人物", 0, PERFORMANCE_KEYS),
     ("camera", "手持跟拍，摄影机在她侧前方随她倒退移动，不环绕、不翻轴", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    camera_motion={"movement_kind": "dolly_out", "direction": "backward", "amplitude_class": "moderate",
                   "speed_class": "moderate", "start_motion_state": "in_motion", "end_motion_state": "continuing"},
    stability="手持跟拍的自然晃动", settle="手持继续跟在她侧前方")

SPECS["MO04"] = clip_spec("MO04", "p007-w1", "41c78422afe94819a01a2b9cb1c97f322d9aa43fbebb685381f2cfc3ef4ae4cd", 4, "W1",
    "first_frame", _board_scene("street-billboard-tree", "SoMa 第六街与 Folsom 街口，人行道上一棵行道树，树后一块被挡住一半的广告牌（牌面是空白白光）",
                                mood=OPEN_MOOD), "眯眼往上看树后那块发白光的广告牌", {
        "open": "MO04首帧：她站在树下，面前挡着一根树枝，树后是发白光的广告牌",
        "close": "广告牌的白光整片打到她脸上，她从外套口袋里掏出一张空白的白色姓名贴，构图不变",
        "action_start": "她站在树下，伸手去拽挡在面前的树枝", "progression": "把树枝往下拽，眯眼往上看广告牌，松手让树枝弹回去",
        "endpoint": "白光打在她脸上，她掏出一张空白的白色姓名贴", "camera": LOCKED_INTENT,
        "framing": "MO04首帧：她在树下", "start_framing": "MO04首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪与广告牌的白光", "ambience": "几乎无声（成片使用独立音轨）",
        "space": "她站在树下原位", "motion_peak": "松手，树枝弹回去，白光整片打到她脸上",
        "natural": ["树枝弹回去、叶子晃动", "她不躲"],
        "open_event": ("她把挡在面前的树枝往下拽", "镜头固定"),
        "close_event": ("从外套口袋里掏出一张空白的白色姓名贴", "广告牌的白光整片打到她脸上")},
    iris_performance("树枝挡着广告牌", "拽下树枝、眯眼看广告牌，松手后白光打到脸上也不躲", "树后的广告牌",
                     "伸手拽树枝，松手，站定", "一只手拽树枝，最后从外套口袋里掏出姓名贴", "脸在白光里，手里拿着空白姓名贴",
                     "面无表情，带着一点好奇"),
    _fixed("她站在树下", "机位不变，她仍在树下"),
    _motion_rules("她拽下树枝、松手让它弹回去，叶子晃动，白光整片打到脸上她不躲，从外套口袋里掏出一张空白的白色姓名贴",
                  look="W1"))

SPECS["SG02"] = clip_spec("SG02", "p008-w1", "c602b3883f46db5a4f97b44c9e67acbe2d5122709a665ee6b75225214a9f4747", 4, "W1",
    "multimodal", _board_scene("billboard-light", "同一块广告牌下，白光里", mood=OPEN_MOOD), "中近景", {
        "open": "SG02参考图：中近景，她在广告牌的白光里正对镜头，手里拿着带底纸的空白姓名贴，嘴唇合上",
        "close": "姓名贴已拍在胸口、用拇指抹平，说完这一句，构图不变",
        "action_start": "她正对镜头，手里拿着带底纸的空白姓名贴", "progression": "对着镜头平平地说话，口型与参考人声逐字同步；把姓名贴撕下来拍在胸口",
        "endpoint": "姓名贴拍在胸口、用拇指抹平，说完这一句", "camera": LOCKED_INTENT,
        "framing": "SG02参考图：中近景，她正对镜头", "start_framing": "SG02参考图原始构图",
        "end_framing": "与起始相同的构图", "light": "相机机头直闪与广告牌的白光",
        "ambience": "片段自带音轨跟随参考人声（成片换成歌曲母带）", "space": "她在原位，从头到尾正对镜头",
        "motion_peak": "姓名贴啪地拍在胸口", "natural": ["不转身，不转头", "嘴前没有任何遮挡"],
        "open_event": ("对着镜头平平地说话", "逐字精确同步"), "close_event": ("啪地拍在胸口，用拇指抹平", "镜头固定不动")},
    iris_performance("主歌一念白", "对着镜头平平地说，口型与参考人声逐字同步；把姓名贴拍在胸口抹平", "镜头",
                     "站定，从头到尾正对镜头，不转身不转头", "把空白姓名贴从底纸上撕下来拍在胸口，用拇指抹平",
                     "姓名贴在胸口，说完", "面无表情"),
    _fixed("中近景，她对着镜头", "构图与机位不变，她仍正对镜头"), _lipsync_rules(LIPSYNC_SPOKEN, look="W1"),
    dialogue={"mode": "dialogue", "language": "en", "speaker_id": "IRIS",
              "verbatim_text": "I: Average Individual. That's me. Bus stop:", "start_seconds": 0.17, "end_seconds": 3.89,
              "on_screen": True, "response_obligation": "对着镜头平平地说出这一句，口型与参考人声逐字同步",
              "lip_sync_required": True})

# MO21 (s009): she sits side-on, her left ear and its device are out of view (preview known issue 「s009 左耳耳挂因机位
# 不可见」); the approved prompt says 画面里没有任何红色, so the palette says so and the identity rule notes the hidden ear.
# 2026-11-20 首帧换修正版 OP09-fix-c（只换左耳区域 637–708×222–296），用户认可「用修正版拍 (Recommended)」；
# 此前为 p009-w1 / 451f67af1297cfcfc63229c06cc5129c063c7d8966682ed6932ed45b429ecc73（OP09-a）。
SPECS["MO21"] = clip_spec("MO21", "p009-w1b", "25e4895c39911f40d90c3e166b31389646a71a2e6ed7036fcc208ebe8001b16d", 4, "W1",
    "first_frame", _board_scene("folsom-bus-shelter", "Folsom 街一个公交候车亭，夜里，侧面的广告灯箱是空白白光", mood=OPEN_MOOD),
    "她侧身坐在候车亭的长凳上", {
        "open": "MO21首帧：她侧身坐在候车亭的长凳上，灯箱玻璃上有一道划痕",
        "close": "她的指甲停在划痕尽头，构图不变",
        "action_start": "她侧身坐着，伸出一根手指", "progression": "用指甲顺着灯箱玻璃上那道划痕慢慢划过去",
        "endpoint": "指甲停在划痕尽头", "camera": LOCKED_INTENT,
        "framing": "MO21首帧：她侧身坐在长凳上", "start_framing": "MO21首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪与灯箱的白光", "ambience": "几乎无声（成片使用独立音轨）", "space": "她坐在长凳上原位",
        "motion_peak": "指甲顺着划痕慢慢划过去", "natural": ["面无表情，带着一点好奇"],
        "open_event": ("伸出一根手指", "镜头固定"),
        "close_event": ("停在划痕尽头", "用指甲顺着灯箱玻璃上那道划痕慢慢划过去")},
    iris_performance("灯箱玻璃上的划痕", "用指甲顺着划痕慢慢划过去，停在尽头", "灯箱玻璃上的划痕", "侧身坐在长凳上",
                     "伸出一根手指，用指甲顺着划痕划过去", "指甲停在划痕尽头", "面无表情，带着一点好奇"),
    _fixed("她侧身坐在长凳上", "构图与机位不变"),
    [("identity", IDENTITY_TEXT + LOOK_TEXT["W1"] + "（由认可的首帧承担；本镜她侧身，左耳与耳挂在画面外）", 0,
      ("identity_waivers",) + IDENTITY_KEYS),
     ("performance", "她侧身坐在长凳上，伸出一根手指，用指甲顺着灯箱玻璃上那道划痕慢慢划过去，停在划痕尽头；不新增人物", 0,
      PERFORMANCE_KEYS),
     ("camera", LOCKED_INTENT + "，保持首帧构图", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    palette="冷白、青蓝和琥珀色的夜间灯色；画面里没有任何红色（本镜看不到左耳耳挂）")

SPECS["MO05"] = clip_spec("MO05", "p010-w1", "a46b48ce8ce9d7217f9ca5bb06dedcfae4134f145cca7d04732fc6b10c808a23", 5, "W1",
    "first_frame", _board_scene("freeway-footbridge", "Potrero Hill 旁跨 US-101 高速的人行天桥，夜里，铁丝网护栏外是车流",
                                mood=OPEN_MOOD), "长焦侧拍", {
        "open": "MO05首帧：长焦侧拍，她双臂搭在天桥的铁丝网护栏上往下看桥下的车流",
        "close": "她两手插进外套口袋，转身沿着天桥往远处走去，构图不变",
        "action_start": "她双臂搭在铁丝网护栏上往下看", "progression": "抬脚踹了护栏一下，整片铁丝网震动；两手插进外套口袋，转身",
        "endpoint": "她沿着天桥往远处走去，银白短发保持原样", "camera": LOCKED_INTENT,
        "framing": "MO05首帧：长焦侧拍，她在天桥护栏边", "start_framing": "MO05首帧原始构图", "end_framing": "与起始相同的机位，她走远",
        "light": "相机机头直闪、桥下白色和琥珀色的车灯", "ambience": "几乎无声（成片使用独立音轨）",
        "space": "她从护栏边沿天桥往远处走", "motion_peak": "踹了护栏一下，整片铁丝网震动",
        "natural": ["抬脚踹了护栏一下", "整片铁丝网震动"],
        "open_event": ("她双臂搭在天桥的铁丝网护栏上", "镜头固定"),
        "close_event": ("转身沿着天桥往远处走去", "银白短发保持原样")},
    iris_performance("桥下流过的车灯", "踹一下护栏，两手插进外套口袋转身走远", "桥下的车流",
                     "倚着护栏，踹一下护栏，转身走远", "双臂搭在护栏上，最后插进外套口袋", "沿着天桥往远处走去",
                     "面无表情"),
    _fixed("长焦侧拍，她在护栏边", "机位不变，她沿天桥走远"),
    _motion_rules("她踹一下护栏、整片铁丝网震动，两手插进外套口袋转身沿着天桥往远处走去，银白短发保持原样；桥下车灯只有白色和"
                  "琥珀色", look="W1"))


# ---------------------------------------------------------------- s015-s030, 59.23-134.44 s (2026-11-22, W1 then B)
# Director plan pilot/s015-030/plan/index.html (「按方案做首帧预览 (Recommended)」); first frames chosen on
# pilot/s015-030/preview/index.html (logs/decisions.md 2026-11-22: face unified with the opening, s019 a quick change
# W1 -> B, the s017 / s025 / s026 engineer is the opening engineer). Plates board/plates/p0NN-w1 (s015-s019, look W1) and
# p0NN-b1 (s020-s029, look B) are excerpt/flash/design/S15-30/P0NN/<x>.png byte for byte. Prompts: the main session's
# drafts in excerpt/flash/s015-030-seedance.md, to be approved on pilot/s015-030/submit/index.html; every required phrase
# below is a literal substring of that unit's draft. Phrases where the draft and its first frame disagree (see the
# submit page's known issues) are deliberately not required, so a wording fix there does not need a new spec.
# SG10's generation window starts on the 109.7027 beat (board edit 2026-11-22) so the vocal and the take cover the plan's
# s026a cut at 109.72 ("I'm the" 109.86); plays stays 110.6199 until the edit is retimed. A dialogue end past the take
# (SG08 "real." ends 7.07 s, SG09 "Everybody," 5.25 s) is clamped to the take's seconds: the vocal window is cut there.
# Retake m (2026-11-22, 「照 s015 的教训改 (Recommended)」, logs/decisions.md): SG06-SG11 vocal windows start ~0.3 s before
# the first word of the phrase each unit sings and every take is one second longer than before (take_margin_seconds = take
# minus ceil(window)), so the model's own lead-in no longer pushes the last words out; the edit's plays are unchanged and
# the prompts too. New cuts SG06m (65.517, "Phoned" 65.817), SG09m (102.64, from "All" 102.882; "guests." ends 102.64, so
# 0.24 s), SG10m (109.56, "I'm" 109.86), SG11m (125.608, "Pick" 125.908); the old wavs stay. SG07 (0.50 s before
# "couldn't") and SG08 keep their windows: SG08 must start by its plays 95.0393, inside "instead." (94.557-95.079), and
# 0.3 s before "instead." is inside "apps", so its 94.507 start stays. SG09's 4.543 s window rounds up to 5 s; the main
# session set its take to 6 s for the full one-second margin (logs/decisions.md 2026-11-22, ceiling 500). A dialogue end is
# also clamped to the vocal window's end.
# Take folders sd-<UNIT>-m-1|2. The n specs are kept in unit.py.before-sgwin-2026-11-22.
# Pre-shoot audit (2026-11-22, 「照页面改 (Recommended)」 on pilot/s015-030/audit/index.html): MO09-SG11 prompts reworded
# sentence by sentence (no walking at the lens or out of frame, no turning to show an unseen back, props as the first frame
# shows them, laptops / badges / pager screens blank); the required phrases below follow. MO12's new first frame waits for
# the user (excerpt/flash/design/S15-30/P027R, pilot/s015-030/p027r/index.html).
def _sung(text: str, start: float, end: float, obligation: str) -> dict:
    return {"mode": "dialogue", "language": "en", "speaker_id": "IRIS", "verbatim_text": text, "start_seconds": start,
            "end_seconds": end, "on_screen": True, "response_obligation": obligation, "lip_sync_required": True}


SG_AMBIENCE = "片段自带音轨跟随参考人声（成片换成歌曲母带）"
MO_AMBIENCE = "几乎无声（成片使用独立音轨）"
ENGINEER = "值班工程师是开头那位（深蓝色工装夹克），不新增人物"

# SG05 retake m (2026-11-22): both n takes failed the Gate (the vocal was cut 0.03 s before "two" at 59.157 inside the
# phrase, the model sang ~1.4 s of its own lead-in and the 7 s take cut off "that's my cue"; n-1 had a moving car's red
# tail lights; a blotchy left shoulder on both). The user chose 「按页面重拍 (Recommended)」 on
# pilot/s015-030/gate/sg05/index.html: same plate; the board window now 58.70-65.666 (from the "Ten oh two" phrase,
# "Ten" 58.726, with a little lead-in), cut as pilot/audio/SG05m.wav (SG05.wav, the n cut, is kept); the take is 8 s,
# one second over the window (take_margin_seconds) for the model's lead-in; the prompt adds 「街上只有停着的车，没有行驶的车。」
# (a required phrase). The edit still uses the take from song 59.2341 (plays unchanged). Take folders pilot/sd-SG05-m-1|2.
# The n spec (7 s, window 59.157) is kept in unit.py.before-sg05m-2026-11-22.
SPECS["SG05"] = clip_spec("SG05", "p015-w1", "b8eabb6ae89dbe66a01c8d6bf59809f8ed74c91e8a033f2ac9265b31da4a76d3", 8, "W1",
    "multimodal", _board_scene("folsom-side-door", "深夜 Folsom 街湿亮的人行道，秀场的钢制侧门外", mood=OPEN_MOOD), "中景", {
        "open": "SG05参考图：中景，她刚从钢制侧门里走上湿亮的人行道，嘴唇合上，寻呼机和工牌挂在身前的腰链上",
        "close": "她抬头接着唱完这两句，手持镜头仍在她前方同速后退",
        "action_start": "她刚从钢制侧门里走上人行道，嘴唇合上",
        "progression": "边走边对着镜头唱，口型与参考人声逐字同步；唱到一半低头用右手拇指按掉震动的寻呼机，再抬头接着唱",
        "endpoint": "抬头接着唱完这两句", "camera": "手持镜头在她前方与她同速后退，她和镜头的距离始终不变，不环绕",
        "framing": "SG05参考图：中景，手持在她前方", "start_framing": "SG05参考图原始构图",
        "end_framing": "手持仍在她前方，与她的距离不变", "light": "相机机头直闪、街灯与湿地面的反光", "ambience": SG_AMBIENCE,
        "space": "她沿人行道往前走，镜头在她前方同速后退", "motion_peak": "低头用右手拇指按掉寻呼机",
        "envelope_direction": "在她前方与她同速后退",
        "natural": ["用右手拇指按掉", "寻呼机和工牌一直挂在她身前的腰链上", "嘴前没有任何遮挡", "街上只有停着的车，没有行驶的车"],
        "open_event": ("对着镜头边走边唱", "逐字精确同步"), "close_event": ("再抬头接着唱", "手持镜头在她前方与她同速后退")},
    iris_performance("副歌后段这两句", "对着镜头边走边唱，口型与参考人声逐字同步；唱到一半低头用右手拇指按掉寻呼机，再抬头接着唱",
                     "镜头", "边走边唱，与镜头的距离不变", "右手拇指按掉身前腰链上震动的寻呼机", "抬头接着唱",
                     "面无表情，带着一点好奇"),
    {"subject_id": "IRIS", "relation_kind": "maintain_offset", "start_relation": "中景，手持在她前方，她刚走上人行道",
     "end_relation": "手持仍在她前方同速后退，距离不变"},
    [identity_rule("W1", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", "手持镜头在她前方与她同速后退，她和镜头的距离始终不变，不环绕、不翻轴；寻呼机和工牌一直挂在她身前的腰链上", 0,
      CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    camera_motion={"movement_kind": "dolly_out", "direction": "backward", "amplitude_class": "subtle", "speed_class": "slow",
                   "start_motion_state": "in_motion", "end_motion_state": "continuing"},
    stability="手持跟拍的自然晃动", settle="与她的步子同速后退",
    dialogue=_sung("Ten oh two, the pager blew P zero, baby, that's my cue", 0.03, 6.61,
                   "对着镜头边走边唱出这两句，口型与参考人声逐字同步"), vocal="SG05m", take_margin_seconds=1)

# SG06 retake p (2026-11-22): both m takes failed the Gate (she let go on "N" and turned away; the back the plate never
# showed was invented: a black bag, shorts for the skirt; m-1's handset hung itself back). The user chose
# 「按页面重拍，唱段不转身 (Recommended)」 on pilot/s015-030/gate/sg06/index.html: no turning or exit inside a sung take (the
# edit takes her out); the last line now ends 「她仍站在原地看着镜头」. Same plate, vocal SG06m, 7 s; take folders sd-SG06-p-1|2.
SPECS["SG06"] = clip_spec("SG06", "p016-w1", "b176e3b2944c92c67cf7b438cb7c127d6336be690d4e6fda1d354d40c2743521", 7, "W1",
    "multimodal", _board_scene("folsom-payphone", "Folsom 街角一台老式投币电话旁", mood=OPEN_MOOD), "中景", {
        "open": "SG06参考图：中景，她站在投币电话旁正对镜头，伸直手臂把黑色听筒举在身侧离脸一臂远，嘴唇合上",
        "close": "唱完最后一句她松开听筒，仍站在原地看着镜头，机位与构图不变",
        "action_start": "她举着听筒站在投币电话旁，嘴唇合上",
        "progression": "对着镜头唱，口型与参考人声逐字同步；唱最后一句时松开手，听筒垂下去来回晃",
        "endpoint": "她仍站在原地看着镜头", "camera": LOCKED_INTENT,
        "framing": "SG06参考图：中景，她在投币电话旁", "start_framing": "SG06参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪与琥珀色的钠灯街灯", "ambience": SG_AMBIENCE, "space": "她始终站在投币电话旁原位",
        "motion_peak": "松开听筒，听筒来回晃",
        "natural": ["唱最后一句时她松开手", "听筒不贴耳，不挡嘴", "嘴前没有任何遮挡"],
        "open_event": ("对着镜头唱", "逐字精确同步"), "close_event": ("她仍站在原地看着镜头", "镜头固定不动")},
    iris_performance("这两句", "举着听筒对着镜头唱，口型与参考人声逐字同步；唱最后一句时松手，仍站在原地看着镜头", "镜头",
                     "站在投币电话旁，始终不转身", "伸直手臂把黑色听筒举在身侧离脸一臂远，最后松开",
                     "站在原地看着镜头", "面无表情，带着一点好奇"),
    _fixed("中景，她在投币电话旁正对镜头", "构图与机位不变，她仍在原地正对镜头"),
    [identity_rule("W1", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，一镜到底；听筒不贴耳，不挡嘴", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue=_sung("Phoned a friend through D N S Got half an answer,", 0.3, 5.15,
                   "举着听筒对着镜头唱出这两句，口型与参考人声逐字同步"), vocal="SG06m", take_margin_seconds=1)

# INS16 (s016 insert, song 69.40-71.18 "Got half an answer", 2026-11-22): the payphone handset swinging on its metal cord
# under the shelf, no person and no hand. The user chose 「用 d 拍 (Recommended)」 on pilot/s015-030/ins16/index.html: plate
# p016-ins16 (= excerpt/flash/design/S15-30/INS16/d.png), prompt INS16/prompt.md verbatim (also in s015-030-seedance.md).
# The board models it as its own clip of s016 with an `insert` text (build_coverage reads that, not the shot's action);
# the take is 4 s, two seconds over ceil(1.781): the user saw 3 s, but JimengProfile takes 4-30 s, so the main session set
# 3 -> 4 s (logs/decisions.md 2026-11-22, ceiling 400 per take). iris=False: no Character, no identity waiver, no IRIS performance
# direction (unit.py's existing no-person path); the palette names no ear-light exception.
SPECS["INS16"] = clip_spec("INS16", "p016-ins16", "0cfbef8556488bc840ee8002ec5c75b87cbb7d8628957f4db2df6f195479b0f0", 4,
    "W1", "first_frame", _board_scene("folsom-payphone-shelf", "Folsom 街角那台老式投币电话的搁板下方，背后是钢板",
                                      mood="冷、安静、刚松手的余波"), "投币电话的搁板下方", {
        "open": "INS16首帧：特写，投币电话搁板下方，黑色听筒斜挂在金属电话线上偏向一侧，看得出刚松手还在晃；画面里没有人和手",
        "close": "听筒几乎停住，只轻轻转一点，机位与构图不变",
        "action_start": "听筒从首帧里偏向一侧的位置荡回来", "progression": "来回晃，越晃越慢，晃动的幅度一次比一次小",
        "endpoint": "最后几乎停住，只轻轻转一点", "camera": LOCKED_INTENT,
        "framing": "INS16首帧：特写，投币电话搁板下方", "start_framing": "INS16首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪与琥珀色的街灯", "ambience": MO_AMBIENCE, "space": "听筒挂在从搁板前沿垂下的电话线上，原位来回晃",
        "motion_peak": "听筒荡到最高处",
        "natural": ["听筒在后面钢板上的影子跟着一起晃", "画面里没有人，也没有手", "画面里没有任何红色"],
        "open_event": ("黑色听筒挂在金属电话线上来回晃", "镜头固定不动"),
        "close_event": ("最后几乎停住，只轻轻转一点", "越晃越慢")},
    {"trigger": "她刚松手，听筒的余势", "visible_response": "听筒来回晃，越晃越慢，最后几乎停住", "gaze_target": "画面里没有人物",
     "body_behavior": "画面里没有人", "hand_behavior": "画面里没有手", "terminal_performance_state": "听筒几乎停住，只轻轻转一点"},
    {"subject_id": "payphone-handset", "relation_kind": "fixed_frame", "start_relation": "特写，听筒在搁板下方偏向一侧",
     "end_relation": "构图与机位不变，听筒几乎停住"},
    [("performance", "黑色听筒挂在金属电话线上来回晃，越晃越慢，最后几乎停住；电话线一直被拉直；画面里没有人，也没有手，不新增人物", 0,
      PERFORMANCE_KEYS),
     ("camera", LOCKED_INTENT + "，保持首帧构图；背景的街灯和湿地面的反光保持虚焦", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    iris=False, palette="冷白、青蓝和琥珀色的夜间灯色；画面里没有任何红色", take_margin_seconds=2)

# SG07 plate swap (2026-11-22, 「用 b (Recommended)」 on pilot/s015-030/cars/index.html): p017-w1 had a pickup parked tail
# to the camera in the background (its tail lights could light red once animated, as in s015 m-2). Plate now p017-w2b
# (= excerpt/flash/design/S15-30/CARS/p017-w2b.png, a Codex edit of p017-w1 that only turns that pickup to face the camera,
# lights off). Same prompt; p017-w1 is kept. Ending (2026-11-22, 「按页面重拍，唱段不转身 (Recommended)」 on
# pilot/s015-030/gate/sg06/index.html): she only straightens up (「然后直起身。」), no exit inside a sung take.
SPECS["SG07"] = clip_spec("SG07", "p017-w2b", "0a75579f7d5b709d4b81499470f61e5531e5d9cf465570bdbf761204f56b0e60", 9, "W1",
    "multimodal", _board_scene("folsom-curb", "秀场门外同一条街湿亮的路沿，开头那位值班工程师坐在路沿上，笔记本电脑开在膝上",
                               mood=OPEN_MOOD), "中近景", {
        "open": ("SG07参考图：中近景，她蹲在路沿边俯身朝画面左下坐着的值班工程师（开头那位，深蓝色工装夹克），伸向他的手是空的；"
                 "他一只手摊开，膝上是打开的笔记本电脑；寻呼机挂在她身前的腰链上，嘴唇合上"),
        "close": "她把寻呼机拍进他手心、合上他的手指后直起身，仍在画面里，机位与构图不变",
        "action_start": "她蹲在路沿边俯身对着他，嘴唇合上",
        "progression": "对着他唱，口型与参考人声逐字同步；唱完一句停住一拍；用右手从身前腰链上摘下寻呼机拍进他摊开的手心，再把他的手指合上",
        "endpoint": "她直起身", "camera": LOCKED_INTENT,
        "framing": "SG07参考图：中近景，工程师在画面左下", "start_framing": "SG07参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪、街灯与笔记本屏幕的冷光", "ambience": SG_AMBIENCE, "space": "她和工程师在路沿边原位，最后她直起身",
        "motion_peak": "寻呼机啪地拍进他手心",
        "natural": ["唱完一句后她停住不动一拍", "啪地拍进他摊开的手心", "再把他的手指合上", "嘴前没有任何遮挡"],
        "open_event": ("俯身对着坐在路沿上的值班工程师唱", "逐字精确同步"), "close_event": ("然后直起身", "镜头固定不动")},
    iris_performance("对路沿上的值班工程师唱", "俯身对着他唱，口型与参考人声逐字同步；停一拍后把寻呼机拍进他手心、合上他的手指，直起身",
                     "值班工程师", "蹲在路沿边俯身，最后直起身，不转身、不出画",
                     "右手从身前腰链上摘下黑色寻呼机拍进他摊开的手心，再把他的手指合上", "直起身",
                     "面无表情，带着一点好奇"),
    _fixed("中近景，她蹲在路沿边对着工程师", "构图与机位不变，她直起身仍在画面里"),
    [identity_rule("W1", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，一镜到底；" + ENGINEER, 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue=_sung("couldn't guess Pick up, pick up, it's your call P zero. That's all.", 0.5, 7.8,
                   "俯身对着值班工程师唱出这几句，口型与参考人声逐字同步"), take_margin_seconds=1)

SPECS["MO08"] = clip_spec("MO08", "p018-w1", "5a8ac46aec0079ddd02f4178e7a4f03d47043ff580b702708a48d0d3e928f529", 6, "W1",
    "first_frame", _board_scene("folsom-street-high", "Folsom 街，从高处俯拍湿亮的街道，抱着笔记本电脑的人群和一辆出租车",
                                mood=OPEN_MOOD), "高机位俯拍", {
        "open": "MO08首帧：高机位俯拍湿亮的街道，抱着笔记本电脑的人群四散奔跑，左侧有人拦出租车；她在画面中间偏右，银白短发",
        "close": "人群一波一波地涌过，只有她一个人逆着人流不紧不慢地走，构图不变",
        "action_start": "人群从楼里涌上街道", "progression": "人群往四面散开，有人跑着去拦出租车；她逆着人流不紧不慢地走",
        "endpoint": "只有她一个人逆着人流", "camera": LOCKED_INTENT,
        "framing": "MO08首帧：高机位俯拍", "start_framing": "MO08首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "相机机头直闪、路灯与出租车灯", "ambience": MO_AMBIENCE, "space": "人群四散，她逆着人流走",
        "motion_peak": "人群一波一波地涌",
        "natural": ["有人跑着去拦出租车", "往四面散开", "街上的车灯只有白色和琥珀色"],
        "open_event": ("抱着笔记本电脑的人群从楼里涌上湿亮的街道", "镜头固定不动"),
        "close_event": ("只有她一个人逆着人流", "人群一波一波地涌")},
    iris_performance("人群涌上街", "逆着人流不紧不慢地走", "前方", "逆着人流走", "双手自然下垂", "继续逆着人流走", "面无表情"),
    _fixed("高机位俯拍，她在人群里", "机位不变，她逆着人流走"),
    _motion_rules("抱着笔记本电脑的人群涌上街道、往四面散开，有人拦出租车；只有她一个人逆着人流不紧不慢地走；车灯只有白色和琥珀色",
                  look="W1"))

# MO09 (2026-11-22, 「改成「头顶始终不出画」 (Recommended)」): the audit's 「她始终完整在画面里，头顶不出画。」 became
# 「她的头顶始终不出画。」: the plate already cuts her at the thighs, and "完整" could make the model pull the camera back.
SPECS["MO09"] = clip_spec("MO09", "p019-w1", "395553d2b87342c0274a5bd6e66f3bfee2b926b630d788dbe52a7b1f0f4eac07", 5, "W1",
    "first_frame", _board_scene("hotel-service-corridor", "酒店宴会厅后面的服务走廊，推车和叠起来的折叠椅", mood=OPEN_MOOD),
    "服务走廊里", {
        "open": "MO09首帧：服务走廊里，三位换装师的手正把她的灰色外套往后剥，一位换装师撑开黑色双排扣西装；她双臂张开往前走",
        "close": "黑色双排扣西装外套已套上她的双臂，她仍站在原地，头顶不出画，构图不变",
        "action_start": "三双换装师的手同时抓着她的灰色外套",
        "progression": "灰色外套连同斜挎带一起被剥下来，黑色双排扣西装外套套上她的双臂；她双臂张开站在原地不动",
        "endpoint": "她穿着黑色双排扣西装外套站在原地，头顶不出画", "camera": LOCKED_INTENT,
        "framing": "MO09首帧：服务走廊", "start_framing": "MO09首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "走廊顶灯与宴会厅门缝的光", "ambience": MO_AMBIENCE, "space": "她站在走廊原位，换装师围着她动作",
        "motion_peak": "灰色外套连同斜挎带被剥下、西装套上双臂",
        "natural": ["把她身上的灰色外套连同斜挎带一起剥下来", "她双臂张开，站在原地不动，任他们换", "腰链上的工牌是空白的，没有任何字",
                    "面无表情"],
        "open_event": ("三双换装师的手同时动作", "镜头固定不动"),
        "close_event": ("她的头顶始终不出画", "把一件黑色双排扣西装外套套上她的双臂")},
    iris_performance("换装师剥下外套", "双臂张开站在原地不动，任换装师换上西装", "前方",
                     "双臂张开站在原地不动", "双臂张开任换装师套上西装袖子", "站在原地，头顶不出画", "面无表情"),
    _fixed("她在服务走廊里，换装师围着她", "机位不变，她仍在原地"),
    [("identity", IDENTITY_TEXT + "；二十八岁成熟、有棱角的脸，面无表情带着好奇；本镜是快速换装：开头是造型W1（灰色连帽衫改造的"
                  "不对称高定短外套、斜挎黑色皮质背带、腰链上的空白工牌、黑色高腰迷你裙），灰色外套连同斜挎带被剥下，套上造型B的黑色"
                  "超大廓形双排扣西装外套（由认可的首帧承担）", 0, ("identity_waivers",) + IDENTITY_KEYS),
     ("performance", "三双换装师的手同时把她的灰色外套连同斜挎带剥下、把黑色双排扣西装外套套上她的双臂；她双臂张开站在原地不动，"
                     "头顶始终不出画（首帧里她从大腿处出画，机位不拉远）；不新增人物", 0, PERFORMANCE_KEYS),
     ("camera", LOCKED_INTENT + "，保持首帧构图", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    identity_continuity="人物身份与左耳装置位置一致（v4身份锚点F1a）；本镜从造型W1快速换成造型B", palette=PALETTE["B"])

SPECS["MO10"] = clip_spec("MO10", "p020-b1", "7e6c124eabb1c32eb2a2924ee809ad1baead4998423d6c0e07ae3a103973f65d", 5, "B",
    "first_frame", _board_scene("hotel-ballroom-stage", "酒店宴会厅里一个正在撤的发布会舞台，桁架、梯子上的工人和大块黑幕",
                                mood=OPEN_MOOD), "她身后桁架上的大块黑幕", {
        "open": "MO10首帧：她站在空白的白色展示牌旁，一只手搭在牌子上沿；身后是桁架上挂着的大块黑幕和梯子上的工人",
        "close": "黑幕已整片落下，后面是同样的黑色墙面；白板连同架子被她往前推倒，牌面朝下扣在地毯上，构图不变",
        "action_start": "她站在展示牌旁，身后的黑幕还挂着",
        "progression": "梯子上的工人松开手，人仍站在梯子上，桁架上的大块黑幕一下子整片落下；她不回头",
        "endpoint": "她把空白白板连同架子一起往前推倒，牌面朝下扣在地毯上", "camera": LOCKED_INTENT,
        "framing": "MO10首帧：舞台前，她在画面右侧", "start_framing": "MO10首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "宴会厅的吊灯与舞台灯", "ambience": MO_AMBIENCE, "space": "她站在展示牌旁原位",
        "motion_peak": "黑幕一下子整片落下",
        "natural": ["梯子上的工人松开手，人仍站在梯子上", "白板背面是素黑色的板，没有任何字", "后面是同样的黑色墙面，没有屏幕",
                    "面无表情"],
        "open_event": ("一下子整片落下", "镜头固定不动"), "close_event": ("牌面朝下扣在地毯上", "她不回头")},
    iris_performance("身后黑幕整片落下", "不回头，伸手把身边那块空白白板连同架子一起往前推倒", "前方", "站定，不回头",
                     "伸手把空白白板连同架子一起往前推倒", "白板牌面朝下扣在地毯上，她站定", "面无表情"),
    _fixed("她站在展示牌旁，身后是舞台", "构图与机位不变"),
    _motion_rules("身后桁架上的大块黑幕一下子整片落下，梯子上的工人松开手、人仍站在梯子上；她不回头，把身边那块空白白板连同架子一起"
                  "往前推倒，牌面朝下扣在地毯上；白板背面素黑无字，黑幕后是同样的黑色墙面；不新增人物", look="B"))

SPECS["SG08"] = clip_spec("SG08", "p022-b1", "3104bb6d25636b982addedd290f3228ee7cd4850149c3ef69441f536c03cc5a9", 8, "B",
    "multimodal", _board_scene("hearing-room-witness", "市议会听证室的木质证人席，桌上一支细鹅颈话筒压得很低偏在一侧", time="白天",
                               mood=OPEN_MOOD), "中景", {
        "open": "SG08参考图：中景，她坐在证人席上，一只手按在桌上的空白卡片上，细话筒压低偏在一侧，嘴唇合上",
        "close": "说完这几句，她用手掌把两张空白卡片推齐压住，机位与构图不变",
        "action_start": "她坐在证人席上，嘴唇合上",
        "progression": "对着镜头平平地说话，口型与参考人声逐字同步；说话时把手下那张空白卡片在桌面上拍一下",
        "endpoint": "手掌把两张卡推齐压住，说完", "camera": LOCKED_INTENT,
        "framing": "SG08参考图：中景，她在证人席上", "start_framing": "SG08参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "听证室窗外的日光", "ambience": SG_AMBIENCE, "space": "她坐在证人席原位",
        "motion_peak": "卡片拍在桌面上",
        "natural": ["桌上的细话筒一直压低偏在一侧，不挡嘴", "嘴前没有任何遮挡"],
        "open_event": ("对着镜头平平地说话", "逐字精确同步"), "close_event": ("最后用手掌把两张卡推齐压住", "镜头固定不动")},
    iris_performance("证人席上的念白", "对着镜头平平地说，口型与参考人声逐字同步；把手下的空白卡片拍一下，最后用手掌推齐压住", "镜头",
                     "坐在证人席上", "把手下那张空白卡片在桌面上拍一下，最后用手掌把两张推齐压住", "手掌压住推齐的两张卡，说完",
                     "面无表情"),
    _fixed("中景，她坐在证人席上", "构图与机位不变"),
    [identity_rule("B", "参考图"), ("lip-sync", LIPSYNC_SPOKEN, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，一镜到底；桌上的细话筒一直压低偏在一侧，不挡嘴", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue=_sung("instead. Under oath: three times Google's models left the test. They stopped, they said, once they saw it "
                   "was real.", 0.05, 6.94, "对着镜头平平地说出这几句，口型与参考人声逐字同步"), take_margin_seconds=1)

# SG09 plate swap (2026-11-22): the continuity check (pilot/s015-030/issues/index.html) found p024-b1 (round rings,
# transverse high-back seats) unlike the same car in p025 / p026 (triangular handles, longitudinal benches); the user
# chose 「重做 p024 的车厢 (Recommended)」, then 「用 b (Recommended)」 on pilot/s015-030/p024r/index.html. Plate now
# p024-b2 (= excerpt/flash/design/S15-30/P024R/b.png): same face, look and standing place, the right hand on a triangular
# handle (吊环 covers it, as in MO11 on p025), the other hand in her pocket. Same prompt. p024-b1 is kept.
SPECS["SG09"] = clip_spec("SG09", "p024-b2", "d13da23ff4ecb4079a855d78ce19fe7c786eec9fbe38bec04700c5b7765b738f", 6, "B",
    "multimodal", _board_scene("night-train-car", "深夜通勤列车车厢，两边座位上是抱着笔记本电脑打瞌睡的人", mood=OPEN_MOOD), "中景", {
        "open": "SG09参考图：中景，她站在车厢过道里，一只手抓着头顶的吊环，另一只手插在口袋里，嘴唇合上；两边的人抱着笔记本电脑打瞌睡",
        "close": "唱完这一句，两边的人仍在打瞌睡，机位随车身轻晃，构图不变",
        "action_start": "她抓着吊环站在过道里，嘴唇合上", "progression": "车厢顶灯闪一下；她对着镜头唱，口型与参考人声逐字同步",
        "endpoint": "唱完这一句", "camera": "摄影机固定在车厢里，随车身轻轻晃动，不推近、不摇镜、不环绕",
        "framing": "SG09参考图：中景，她在车厢过道里", "start_framing": "SG09参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "车厢顶灯", "ambience": SG_AMBIENCE, "space": "她站在过道原位", "motion_peak": "车厢顶灯闪一下",
        "envelope_direction": "随车身轻轻晃动，不推近、不摇镜",
        "natural": ["开头车厢顶灯闪一下", "一只手抓着头顶的吊环", "车窗里不出现她的倒影", "嘴前没有任何遮挡",
                    "笔记本电脑外壳是素银色，没有任何标志；挂绳工牌是空白的"],
        "open_event": ("对着镜头唱", "逐字精确同步"),
        "close_event": ("两边座位上的人低头打瞌睡，不抬头", "镜头随车身轻轻晃动")},
    iris_performance("副歌开头", "抓着吊环对着镜头唱，口型与参考人声逐字同步", "镜头", "站在车厢过道里，随车身轻晃",
                     "一只手抓着头顶的吊环", "唱完这一句", "面无表情，带着一点好奇"),
    _fixed("中景，她站在车厢过道里", "构图不变，镜头随车身轻晃"),
    [identity_rule("B", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", "摄影机固定在车厢里，随车身轻轻晃动，不推近、不摇镜、不环绕，一镜到底；车窗里不出现她的倒影", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    stability="固定在车厢里的机位，随车身轻轻晃动", settle="始终随车身轻轻晃动",
    dialogue=_sung("All hands! All night! Everybody,", 0.24, 4.54, "抓着吊环对着镜头唱出这一句，口型与参考人声逐字同步"),
    vocal="SG09m", take_margin_seconds=1)

SPECS["MO11"] = clip_spec("MO11", "p025-b1", "57f05856e73109b5556e4c24682f0ef37f989a9e3cc03cda0e1bfe6e9ae46476", 4, "B",
    "first_frame", _board_scene("night-train-aisle", "同一节深夜通勤列车车厢的过道，开头那位值班工程师坐在她身边睡着",
                                mood=OPEN_MOOD), "另一只手一直抓着吊环", {
        "open": "MO11首帧：她站在过道里一只手抓着吊环，另一只手拿着从身边睡着的值班工程师（开头那位，深蓝色工装夹克）膝上滑下的笔记本电脑",
        "close": "笔记本电脑已塞回他怀里，她的手仍抓着吊环，构图不变",
        "action_start": "列车猛地一晃，全车人一起摇", "progression": "她不看，把刚接住的笔记本电脑塞回他怀里",
        "endpoint": "电脑塞回他怀里，另一只手一直抓着吊环", "camera": LOCKED_INTENT,
        "framing": "MO11首帧：车厢过道", "start_framing": "MO11首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "车厢顶灯", "ambience": MO_AMBIENCE, "space": "她站在过道原位，工程师坐在她身边",
        "motion_peak": "列车猛地一晃", "natural": ["全车人一起摇", "车窗里不出现她的倒影", "面无表情", "笔记本电脑外壳是素银色，没有任何标志"],
        "open_event": ("列车猛地一晃", "镜头固定不动"), "close_event": ("塞回身边睡着的值班工程师怀里", "她不看")},
    iris_performance("列车猛地一晃", "不看，把刚接住的笔记本电脑塞回工程师怀里", "前方", "站在过道里随车身一晃",
                     "一只手一直抓着吊环，另一只手把接住的笔记本电脑塞回他怀里", "电脑塞回他怀里，手仍抓着吊环", "面无表情"),
    _fixed("她站在车厢过道里", "构图与机位不变"),
    _motion_rules("列车猛地一晃、全车人一起摇；她不看，把刚接住的笔记本电脑塞回工程师怀里，另一只手一直抓着吊环；"
                  + ENGINEER + "；车窗里不出现她的倒影", look="B"))

SPECS["SG10"] = clip_spec("SG10", "p026-b1", "0a361f2d941333afd0fa3372f2150e3ac167193c71a7a6bf222a19166aa5771f", 8, "B",
    "multimodal", _board_scene("night-train-door-seat", "同一车厢靠门的座位，开头那位值班工程师靠着车厢壁睡着，手里松松攥着她的寻呼机",
                               mood=OPEN_MOOD), "中近景", {
        "open": ("SG10参考图：中近景，她坐在睡着的值班工程师（开头那位，深蓝色工装夹克）身边，正脸看着镜头，双手在画外，嘴唇合上；"
                 "他闭着眼，手里松松攥着黑色寻呼机"),
        "close": "她把寻呼机从他手里拿走，收到画面下方，机位与构图不变",
        "action_start": "她坐在他身边，嘴唇合上", "progression": "一直看着镜头唱，口型与参考人声逐字同步；唱到一半他猛地睁开眼睛",
        "endpoint": "她伸手从他松开的手里拿走寻呼机，收到画面下方", "camera": LOCKED_INTENT,
        "framing": "SG10参考图：中近景，她和他并排", "start_framing": "SG10参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "车厢顶灯", "ambience": SG_AMBIENCE, "space": "她和他都坐在原位", "motion_peak": "他猛地睁开眼睛",
        "natural": ["唱到一半时他猛地睁开眼睛", "最后她伸手从他松开的手里拿走黑色寻呼机", "嘴前没有任何遮挡",
                    "车窗里不出现她的倒影", "寻呼机屏幕只有灰绿底光，没有数字和字"],
        "open_event": ("她一直看着镜头唱", "逐字精确同步"), "close_event": ("收到画面下方", "镜头固定不动")},
    iris_performance("对睡着的值班工程师唱", "一直看着镜头唱，口型与参考人声逐字同步；他睁眼后伸手从他手里拿走寻呼机，收到画面下方",
                     "镜头", "坐在他身边，正脸看着镜头", "伸手从他松开的手里拿走黑色寻呼机，收到画面下方",
                     "寻呼机收到画面下方", "面无表情，带着一点好奇"),
    _fixed("中近景，她坐在工程师身边", "构图与机位不变"),
    [identity_rule("B", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，一镜到底；" + ENGINEER, 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue=_sung("I'm the reason you're awake I'm the call you had to take", 0.3, 6.56,
                   "看着镜头唱出这两句，口型与参考人声逐字同步"), vocal="SG10m", take_margin_seconds=1)

# MO12 back view (2026-11-23, 「用 b (Recommended)」 on pilot/s015-030/p027b/index.html, after 「A 重做背影首帧再拍
# (Recommended)」): the n takes (plate p027-b2) both walked at the camera, lost her feet at ~1.5 s and showed logos or
# graphics. Plate now p027-b3 (= excerpt/flash/design/S15-30/P027B/b.png): the camera behind her, she walks away along the
# platform toward the exit stairs in the depth, the hooded crowd pouring out of the doors behind her, laptops closed and
# held lid-in, a plain black beam overhead. Prompt = P027B/prompt.md. Take folders sd-MO12-p-1|2; p027-b1 / p027-b2 kept.
SPECS["MO12"] = clip_spec("MO12", "p027-b3", "942eac1020263ff3ab6df31411132bae5c781c34a90fb5b2f565424e83b5d88b", 4, "B",
    "first_frame", _board_scene("subway-platform", "地下车站站台，列车停靠，车门开着，站台深处是出口楼梯", mood=OPEN_MOOD), "镜头固定不动", {
        "open": ("MO12首帧：机位在她身后，她背对镜头站在站台正中，正前方深处是出口楼梯；列车在画面右侧，车门开着，戴兜帽的人群"
                 "从车门涌出、在她身后两侧跟着，把合着的笔记本电脑抱在胸前；顶上是素黑横梁"),
        "close": "她已走远，在画面里越来越小，人群仍在她身后跟着，构图不变",
        "action_start": "她背对镜头，沿站台朝远处的出口楼梯大步走", "progression": "不回头，越走越小；人群从车门涌出，在她身后两侧跟着",
        "endpoint": "她越走越小，仍朝出口楼梯走", "camera": LOCKED_INTENT,
        "framing": "MO12首帧：从她身后看向站台深处的出口楼梯", "start_framing": "MO12首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "站台顶灯", "ambience": MO_AMBIENCE, "space": "她沿站台朝深处的出口楼梯走远", "motion_peak": "大步走远",
        "natural": ["不回头", "电脑背面朝向自己的身体", "她背后没有包，也没有任何挂件", "电脑外壳和连帽衫上没有任何标志或图案"],
        "open_event": ("她背对镜头，沿站台朝远处的出口楼梯大步走远", "戴兜帽的人群从开着的车门里涌出来"),
        "close_event": ("越走越小", "在她身后两侧跟着她朝出口走")},
    iris_performance("车门开着，人群涌出", "背对镜头沿站台朝出口楼梯大步走远，不回头", "前方深处的出口楼梯", "背对镜头大步走远",
                     "双手自然摆动", "越走越小，仍朝出口走", "背对镜头，看不到脸"),
    _fixed("机位在她身后，她在站台正中", "机位不变，她越走越小"),
    _motion_rules("她背对镜头沿站台朝远处的出口楼梯大步走远，不回头，越走越小；戴兜帽的人群从开着的车门里涌出来，在她身后两侧跟着；"
                  "电脑合着抱在胸前、背面朝内，没有标志；她背后没有包；不新增人物", look="B"))

# MO13 prompt (2026-11-22): the first frame is a medium shot at the foot of the tower stairs where no board is visible,
# so the user chose 「按问题页改 (Recommended)」 on pilot/s015-030/issues/index.html: camera locked, she climbs the stairs,
# glances at the glowing pager halfway and walks out of frame upper right; standing on the board is left to s029. Same plate.
# The replaced spec (长焦, stops halfway along the board) is kept in unit.py.before-p024r-mo13-2026-11-22.
SPECS["MO13"] = clip_spec("MO13", "p028-b1", "3adfc73750b8ef030d28b2727e0f0cbf6fe066cbfdacc3db566b1d29dba5fcd6", 6, "B",
    "first_frame", _board_scene("dry-pool-tower", "一座放干了水的市立室外泳池，夜里，池边一排空折叠椅和高跳台", mood=OPEN_MOOD),
    "镜头固定不动", {
        "open": "MO13首帧：中景，她一只手扶着栏杆站在跳台台阶下，身前腰带上挂着黑色寻呼机；池底干燥",
        "close": "她从画面右上方走出去，构图不变",
        "action_start": "她转身朝画面右侧，沿台阶往上走", "progression": "走到一半低头看一眼身前腰带上的黑色寻呼机，液晶屏发出灰绿色的光",
        "endpoint": "她再接着往上走，从画面右上方走出去", "camera": LOCKED_INTENT,
        "framing": "MO13首帧：中景，跳台台阶下", "start_framing": "MO13首帧原始构图", "end_framing": "与起始相同的构图",
        "light": "池边的泛光灯", "ambience": MO_AMBIENCE, "space": "她从台阶下沿跳台的台阶往上走，从画面右上方走出",
        "motion_peak": "低头看一眼寻呼机",
        "natural": ["寻呼机的液晶屏发出灰绿色的光", "池底干燥，没有水", "背后没有包，也没有任何挂件",
                    "寻呼机屏幕只有灰绿底光，没有数字和字"],
        "open_event": ("她转身朝画面右侧，沿台阶往上走", "走到一半低头看一眼身前腰带上的黑色寻呼机"),
        "close_event": ("再接着往上走", "从画面右上方走出去")},
    iris_performance("泛光灯亮起", "转身朝画面右侧沿台阶往上走，半途低头看一眼寻呼机，再接着往上走，从画面右上方走出去",
                     "前方，半途低头看寻呼机", "转身朝画面右侧沿台阶往上走，从画面右上方走出", "一只手扶着栏杆", "从画面右上方走出画面",
                     "面无表情"),
    _fixed("中景，她在跳台台阶下", "机位不变，她从画面右上方走出"),
    _motion_rules("她转身朝画面右侧，沿台阶往上走，走到一半低头看一眼身前腰带上的黑色寻呼机（液晶屏只有灰绿底光，没有数字和字），"
                  "再接着往上走，从画面右上方走出去；背后没有包，也没有任何挂件；池底干燥没有水；不新增人物", look="B"))

SPECS["SG11"] = clip_spec("SG11", "p029-b1", "f64e2472f4dfaefe426e33fe05bebf61fb0b4f1e2b32e370aca171b3d12da98b", 7, "B",
    "multimodal", _board_scene("dry-pool-board-end", "同一座空泳池的跳板末端，夜里，身后是泛光灯", mood=OPEN_MOOD), "低机位仰拍", {
        "open": "SG11参考图：低机位仰拍，她站在跳板末端看着镜头，身前腰带上挂着黑色寻呼机，嘴唇合上",
        "close": "寻呼机掉出画面下方，她不往下看，机位与构图不变",
        "action_start": "她站在跳板末端，嘴唇合上", "progression": "对着镜头唱，口型与参考人声逐字同步；唱完一句后站着不动等一拍",
        "endpoint": "她摘下寻呼机，伸直手臂到身体右侧（画面左侧）松手，寻呼机掉出画面下方", "camera": LOCKED_INTENT,
        "framing": "SG11参考图：低机位仰拍", "start_framing": "SG11参考图原始构图", "end_framing": "与起始相同的构图",
        "light": "身后的泛光灯", "ambience": SG_AMBIENCE, "space": "她站在跳板末端原位", "motion_peak": "手一松，寻呼机掉下去",
        "natural": ["唱完一句后她站着不动等一拍", "伸直手臂到身体右侧（画面左侧），不挡脸", "寻呼机屏幕没有数字和字", "她不往下看",
                    "嘴前没有任何遮挡"],
        "open_event": ("对着镜头唱", "逐字精确同步"), "close_event": ("寻呼机掉出画面下方", "镜头固定不动")},
    iris_performance("这两句", "对着镜头唱，口型与参考人声逐字同步；等一拍后摘下寻呼机伸直手臂松手", "镜头", "站在跳板末端",
                     "从身前腰带上摘下黑色寻呼机，伸直手臂到身体右侧（画面左侧），不挡脸，手一松", "寻呼机掉出画面下方，她不往下看",
                     "面无表情，带着一点好奇"),
    _fixed("低机位仰拍，她站在跳板末端", "构图与机位不变"),
    [identity_rule("B", "参考图"), ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS),
     ("camera", LOCKED_INTENT + "，一镜到底；她不往下看", 0, CAMERA_KEYS), ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)],
    dialogue=_sung("Pick up, pick up, it's your call P zero. That's all.", 0.3, 5.52,
                   "对着镜头唱出这两句，口型与参考人声逐字同步"), vocal="SG11m", take_margin_seconds=1)


def prompt_language_ok(spec: dict, prompt: str) -> bool:
    """Native prompts are pure Chinese (docs/canvas-continuous-production.md); material markers are native syntax."""
    return not re.search("[A-Za-z]", re.sub(r"\{\{(?:image|audio|video):\d+\}\}", "", prompt))


# ---------------------------------------------------------------- helpers
def serial(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        return {f.name: serial(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return type(value).__name__


def write(root: Path, name: str, obj) -> None:
    (root / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def leaves(node, prefix):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from leaves(value, prefix + "." + key)
    elif isinstance(node, (tuple, list)):
        for index, value in enumerate(node):
            yield from leaves(value, prefix + "." + str(index))
    elif node is not None and node != "unspecified":     # an unspecified leaf is no requirement to express
        yield prefix


def source_model(name, cls):
    model = cls.model_validate_json((EP / "production-input" / name).read_bytes())
    if not verify_artifact_hash(model):
        raise Blocked("production-input template hash changed: " + name)
    return model


def core(model):
    return model.model_dump(mode="json", exclude={"artifact_id", "schema_version", "revision", "content_hash",
                                                  "creation_receipt_id", "source_provenance"})


def approval() -> dict:
    if not APPROVAL.is_file():
        raise Blocked(f"no preview approval at {APPROVAL}; the main session writes it after the user approves")
    return json.loads(APPROVAL.read_text(encoding="utf-8"))


def board() -> dict:
    """The v4 board this lane was written for; any change blocks until the specs are re-read and BOARD_SHA256 updated."""
    raw = (REPO / BOARD).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BOARD_SHA256:
        raise Blocked("board/shots.json changed since this lane was written; re-read it, re-check the specs and update "
                      "BOARD_SHA256")
    return json.loads(raw)


def board_clip(unit: str) -> dict:
    clips = [c for c in board()["clips"] if c["clip"] == unit]
    if len(clips) != 1:
        raise Blocked(f"{unit} is not one clip of the v4 board")
    return clips[0]


def identity_blocks(look: str) -> list[str]:
    """The v4 identity: the board's fixed near / far text, the clip's look, the copies' text; the anchor pinned by sha."""
    if hashlib.sha256((REPO / ANCHOR).read_bytes()).hexdigest() != ANCHOR_SHA256:
        raise Blocked("the v4 identity anchor changed since this lane was written: " + ANCHOR)
    data = board()
    if look in ("W1", "B"):                       # not a board look: the approved round-1 plate prompts, pinned
        raw = (REPO / ROUND1).read_bytes()
        if hashlib.sha256(raw).hexdigest() != ROUND1_SHA256:
            raise Blocked(f"{ROUND1} changed since this lane was written; re-read it and update ROUND1_SHA256")
        if not all(text in raw.decode("utf-8") for text in (W1_NEAR, W1_FAR, W1_WARDROBE)):
            raise Blocked(f"the W1 identity text is not verbatim in {ROUND1}")
        if look == "B":                           # the W1 face in the board's look LB
            return [W1_NEAR, W1_FAR, next(x["text"] for x in data["looks"] if x["id"] == "LB"), None]
        return [W1_NEAR, W1_FAR, W1_WARDROBE, None]   # no copies in this look
    looks = [x["text"] for x in data["looks"] if x["id"] == look]
    if len(looks) != 1:
        raise Blocked(f"board look {look} not found")
    fixed = data["fixed_text"]
    return [fixed["identity_near"], fixed["identity_far"], looks[0], fixed["copy"]]


# ---------------------------------------------------------------- draft
def draft(unit: str) -> Path:
    spec = SPECS[unit]
    root = UNITS / unit
    clip = board_clip(unit)                       # pinned inputs first (no writes): board clip, spec, coverage
    window_s = [clip["window"]["t0"], clip["window"]["t1"]]
    if clip["start_frame"] != spec["plate"] or math.ceil(clip["seconds"]) + spec.get("take_margin_seconds", 0) != spec["duration"] or (
            clip["tier"] == "sung") != bool(spec.get("audio")):
        raise Blocked(f"{unit} spec (plate {spec['plate']}, {spec['duration']} s, {spec['input_mode']}) is not the board "
                      f"clip (plate {clip['start_frame']}, {clip['seconds']} s, {clip['tier']})")
    if not COVERAGE.is_file():
        raise Blocked(f"no v4 director coverage at {COVERAGE}; the Director writes the schema-4 coverage "
                      "(unit ids = board clip ids) before any unit is drafted")
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    if spec["coverage_unit"] not in {u.get("unit_id") for u in coverage.get("coverage_units", ())}:
        raise Blocked(f"{spec['coverage_unit']} is not a unit of the v4 director coverage")
    approval_v4 = approval()                      # before any write: no approval, no unit folder
    root.mkdir(parents=True, exist_ok=True)
    approved = (approval_v4.get("prompts") or {}).get(unit)
    if not approved:
        raise Blocked(f"{unit} has no approved prompt in {APPROVAL}")
    prompt = approved["text"]                     # the exact text the user saw on the preview page
    if hashlib.sha256(prompt.encode()).hexdigest() != approved["sha256"]:
        raise Blocked("approved prompt text differs from its sealed sha256")
    if approval_v4.get("generation") != spec["generation"]:
        raise Blocked(f"approval generation must be exactly {spec['generation']}")
    cu, secs = spec["coverage_unit"], spec["duration"]
    locked = spec.get("camera_motion") == LOCKED
    frames = spec["frame_roles"]                  # native endpoint mode: {asset_id: approved_keyframe}; None = multimodal
    audio = spec.get("audio")
    if not prompt_language_ok(spec, prompt):
        raise Blocked("native prompt must be pure Chinese")
    markers = {"{{image:0}}", "{{audio:1}}"} if audio else set()     # native indices: images first, then audios
    if set(MARKERS.findall(prompt)) != markers or not all(m in prompt for m in markers):
        raise Blocked(f"native prompt must name exactly these materials: {sorted(markers)}")
    waiver = spec.get("identity_waiver")          # IRIS is shown without an identity sheet: the user must have waived it
    if spec["iris"] and "IRIS" not in approval_v4.get("identity_waivers", []):
        raise Blocked("IRIS is on screen without an identity sheet; the approval must list IRIS in identity_waivers")

    aid, plate, need, anchor_role, purpose = spec["image"]
    label = APPROVAL_ROLE[spec["input_mode"]]
    seen = approval_v4["preview_artifacts"]
    roles = {f"{unit} {label}"} | ({f"{unit} vocal"} if audio else set())
    extra = sorted({a.get("role") for a in seen if str(a.get("role")).startswith(unit + " ")} - roles)
    if extra:                                     # an approved input for this unit that the unit would not send
        raise Blocked(f"the approval lists {unit} inputs this unit does not send: {extra}")
    first = [a for a in seen if a.get("role") == f"{unit} {label}"]
    if len(first) != 1:
        raise Blocked(f"the approval must list exactly one preview artifact with role '{unit} {label}'")
    if first[0]["path"] != plate:                 # the spec's intent describes this still
        raise Blocked(f"approved {label} {first[0]['path']} is not the still this unit was written for ({plate})")
    refs = [(aid, first[0]["path"], f"approved {Path(plate).name}: the {label}", need, anchor_role, purpose)]
    it = spec["intent"]
    literals = [r[5] for r in refs] + list(it["open_event"]) + list(it["close_event"]) + list(it["natural"])
    missing = [x for x in literals if x not in prompt]
    if missing:                                   # the compiler requires every reference duty in the native text
        raise Blocked("reference planning text missing from the native prompt: " + "；".join(missing))
    selections, records, provenance = [], [], []
    for aid, rel, role, need, anchor_role, _ in refs:
        path = REPO / rel
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha != first[0]["sha256"]:
            raise Blocked(f"approved {label} changed since the approval: " + rel)
        if sha != spec["plate_sha256"]:           # the spec's intent describes these exact bytes
            raise Blocked(f"plate changed since this unit was written: {rel}; re-read it and update the spec's plate sha")
        with Image.open(path) as im:
            w, h = im.size
            if im.format != "PNG":
                raise Blocked("reference must be the exact approved PNG: " + rel)
        item = {"asset_id": aid, "path": rel, "sha256": sha, "size_bytes": len(raw), "width": w, "height": h,
                "role": role, "need_id": need, "anchor_role": anchor_role, "selected_for_provider": True}
        selections.append(item)
        origin = {"kind": "iris-v4-source-selection/1", **item}
        ref = authoring_input_reference(origin)
        provenance.append(ref)
        out = root / ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        records.append(AssetRecord(asset_id=aid, asset_type="image", artifact_path=canonical_image_asset_path(sha), sha256=sha,
            size_bytes=len(raw), mime_type="image/png", width=w, height=h, source_kind="imported",
            tool={"name": "approved-local-source-import", "version": "1"}, input_fingerprint=canonical_sha256(origin),
            creation_receipt_id="iris-v4-local-import:" + sha,
            usage_license="User-authorized project reference; no platform ownership claim."))
    if audio:                                     # the exact vocal window the mouth follows (v2 LSen1 pattern)
        vocal = [a for a in seen if a.get("role") == f"{unit} vocal"]
        if len(vocal) != 1:
            raise Blocked(f"the approval must list exactly one preview artifact with role '{unit} vocal'")
        aid, rel = audio["asset_id"], vocal[0]["path"]
        if rel != audio["path"]:
            raise Blocked(f"approved vocal {rel} is not the window this unit was written for ({audio['path']})")
        raw = (REPO / rel).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha != vocal[0]["sha256"]:
            raise Blocked("approved vocal changed since the approval: " + rel)
        windows = json.loads((REPO / VOCALS).read_text(encoding="utf-8"))
        window = windows["windows"][audio["window"]]
        if window["path"] != rel or window["sha256"] != sha:
            raise Blocked("approved vocal is not the sealed window in " + VOCALS)
        if window["song_window"] != window_s:     # cut from exactly this clip's generation window
            raise Blocked(f"sealed vocal window {window['song_window']} is not the board clip window {window_s}")
        with wave.open(str(REPO / rel)) as wav:
            sr, n = wav.getframerate(), wav.getnframes()
            if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
                raise Blocked("audio reference must be 16-bit mono PCM WAV: " + rel)
        model = JIMENG_MODEL_SPECS[spec["generation"]["model"]]
        millis = round(n * 1000 / sr)
        if not model.min_media_millis <= millis <= min(model.max_audio_millis, secs * 1000):
            raise Blocked(f"vocal window is {millis} ms; it must fit the model bound and the {secs} s take")
        item = {"asset_id": aid, "path": rel, "sha256": sha, "size_bytes": len(raw), "kind": "audio",
                "duration_millis": millis, "sample_rate_hz": sr, "role": f"approved {Path(rel).name}: the vocal",
                "derived_from": {"path": windows["source"], "song_window_seconds": window["song_window"],
                                 "basis": VOCALS}, "selected_for_provider": True}
        selections.append(item)
        origin = {"kind": "iris-v4-source-selection/1", **item}
        ref = authoring_input_reference(origin)
        provenance.append(ref)
        out = root / ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        tool = {"name": "htdemucs_ft-stem+cut_audio.py", "version": "1"}
        meta = AudioAssetMetadata(audio_kind="dialogue", source=AudioSource(kind="derived", provider_or_tool=tool,
                                  input_fingerprint=canonical_sha256(origin), original_reference=windows["source"]),
                                  speaker_id="IRIS", language=spec["dialogue"]["language"],
                                  script_hash=hashlib.sha256(spec["dialogue"]["verbatim_text"].encode()).hexdigest(),
                                  duration_samples=n, sample_rate_hz=sr, channels=1, channel_layout="mono",
                                  codec_name="pcm_s16le", loudness=AudioLoudnessMetadata(),
                                  provenance_receipt_id="iris-v4-vocal-window:" + sha)
        records.append(AssetRecord(asset_id=aid, asset_type="voice", artifact_path=canonical_audio_asset_path(sha), sha256=sha,
            size_bytes=len(raw), mime_type="audio/wav", duration_seconds=n / sr, source_kind="derived", tool=tool,
            input_fingerprint=canonical_sha256(origin), creation_receipt_id="iris-v4-vocal-window:" + sha,
            usage_license="Derived from the user-selected v4 song all-hands-r4 (Demucs vocal stem); project reference only.", audio_metadata=meta))
    registry = AssetRegistrySnapshot(schema_version="2.1" if audio else "2.0", revision_id="0" * 64, content_hash="0" * 64,
                                     assets=tuple(sorted(records, key=lambda x: x.asset_id)))
    rh = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": rh, "content_hash": rh})

    # coverage (v4 Director, schema 4) and the user's preview approval, sealed as authoring inputs
    ch, ca = director_coverage_authoring_input(coverage)
    preview = {"kind": "user-preview-approval/1", "coverage_hash": ch, "unit_ids": [cu],
               "preview_artifacts": [{"path": a["path"], "sha256": a["sha256"], "role": a["role"]} for a in seen],
               "user_quote": approval_v4["user_quote"]}
    if approval_v4.get("identity_waivers"):                       # the performers the user agreed to show without a sheet
        preview["identity_waivers"] = approval_v4["identity_waivers"]
    for item in selections:                                         # every provider image was in the approved preview
        if not any(a["sha256"] == item["sha256"] for a in seen):
            raise Blocked("reference not in the user-approved preview: " + item["path"])
    ah, aa = preview_approval_authoring_input(preview)
    for item, prepared in ((coverage, ca), (preview, aa)):
        provenance.append(authoring_input_reference(item))
        out = root / prepared.relative_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(prepared.payload)

    events = [{"event_id": "open-composition", "kind": "composition", "phase": "start", "visual_state": it["open_event"][0],
               "purpose": it["open_event"][1], "control": "review_only"},
              {"event_id": "close-composition", "kind": "composition", "phase": "end", "visual_state": it["close_event"][0],
               "purpose": it["close_event"][1], "control": "review_only"}]
    anchors, selected = [], []                    # native endpoints are request roles, not persistent anchors or selections
    if not frames:                                # a multimodal image is a soft selection with its anchor duty
        anchors = [{"anchor_id": need, "role": anchor_role, "purpose": purpose, "owner_id": spec["scene"]["scene_id"]}
                   for _, _, _, need, anchor_role, purpose in refs]
        selected = [{"need_id": need, "asset_id": aid} for aid, _, _, need, _, _ in refs]
    elif locked:                                  # a moving camera must still name the composition it changes
        events = []
    dialogue = spec.get("dialogue") or {"mode": "none", "lip_sync_required": False}
    planning = {"facets": ([] if locked else ["slow_camera"]) + (["dialogue"] if dialogue["mode"] != "none" else [])
                          + ["stable"],
                "structure": "continuous", "anchors": anchors, "events": events, "selections": selected,
                "natural_generation": it["natural"],
                "director_coverage": {"coverage_hash": ch, "unit_id": cu}, "preview_approval": {"approval_hash": ah}}
    if waiver:
        planning["identity_waivers"] = [{"character_id": "IRIS", "reason": waiver}]
    gi_raw = {
        "reference_planning": planning,
        "open_state": {"kind": "typed_text", "state_text": it["open"]},
        "close_state": {"kind": "typed_text", "state_text": it["close"]},
        "identity_continuity": {},
        "scene_continuity": {"scene_id": spec["scene"]["scene_id"], "time_of_day": spec["scene"]["time"],
                             "mood": spec["scene"]["mood"],
                             "state_constraints": [it["open"], "不新增人物、设备、文字或界面"]},
        "space_continuity": {"subject_position": it["space"], "screen_direction": "保持参考图方向", "crossing_policy": "不换位、不翻轴"},
        "axis_continuity": {"camera_axis": "参考图原机位视轴", "framing_continuity": it["framing"], "crossing_policy": "不翻轴、不环绕"},
        "subject_action": {"start_state": it["action_start"], "progression": it["progression"], "endpoint": {"state_text": it["endpoint"]}},
        "motion_envelope": {"onset": "平滑开始", "peak": it["motion_peak"],
                            # a locked spec may name its own settle / direction / stability (SG09: 随车身轻轻晃动)
                            "settle": spec.get("settle") or ("摄影机始终静止" if locked else "末段平滑收稳"),
                            "direction": it.get("envelope_direction") or ("摄影机不移动" if locked else "向前"),
                            "amplitude_class": "很小"},
        "pacing": {"cadence": ZH_SECONDS[secs] + "秒连续原速", "tempo_class": "正常原速", "shot_duration_seconds": secs},
        "camera_intent": {"movement": it["camera"],
                          "stability": spec.get("stability") or ("完全静止的固定机位" if locked else "平稳连续，末段收稳"),
                          "framing_intent": it["framing"]},
        "camera_endpoint": {"start_framing": it["start_framing"], "end_framing": it["end_framing"]},
        "visual_treatment": {"medium_look": "真人电影摄影", "palette": spec.get("palette", PALETTE[spec["look"]]),
                             "material_treatment": "自然材质与真实光影",
                             "prohibited_visual_drift": ["新增字幕、文字、图形或界面；平台正常人工智能标识保留", "改变参考图的场景与光线"]},
        "lighting_intent": {"motivated_source": it["light"], "direction": "参考图方向", "exposure_priority": "保留暗部细节",
                            "continuity_state": "与首帧同一冷光"},
        "ambience_intent": {"environment_bed": it["ambience"], "foley_cues": [], "explicitly_silent": False},
        "dialogue_intent": dialogue,
        "music_intent": {"mode": "none"},
        "primary_camera_motion": spec["camera_motion"],
    }
    gi_raw["performance_intent"] = spec["performance"]
    gi_raw["camera_subject_relation"] = spec["relation"]
    gi = GenerationIntent.model_validate(gi_raw)

    def seal(cls, key, data, refs_=None):
        return seal_artifact(cls(artifact_id=f"iris-v4-{unit.lower()}-draft-{key}", revision=1, content_hash="0" * 64,
                                 creation_receipt_id=f"iris-v4-{unit}-authoring:{key}",
                                 source_provenance=tuple(refs_ or provenance), **data))

    if spec["iris"]:                              # the v4 IRIS: board fixed text + pinned anchor, no identity sheet sent
        close, wide, wardrobe, copies = identity_blocks(spec["look"])
        origin = {"kind": "iris-v4-character-identity/1", "anchor": {"path": ANCHOR, "sha256": ANCHOR_SHA256},
                  "board": {"path": BOARD, "sha256": BOARD_SHA256}, "look": spec["look"],
                  "fixed_text": [close, wide, wardrobe, copies]}
        canon_ref = authoring_input_reference(origin)
        out = root / canon_ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        character = seal(Character, "character", {
            "character_id": "IRIS", "name": "IRIS", "identity": "IRIS v4 身份锚点 F1a；全身与远景：" + wide,
            "appearance_bible": close, "wardrobe": (wardrobe,),
            "allowed_variations": ("同一身份的镜头角度与景别变化",) + (("其他副本（同款，灯熄灭）：" + copies,) if copies else ())},
            [canon_ref])
        write(root, "character.json", character.model_dump(mode="json"))

    scene_tpl = core(source_model("scene-interior.json", Scene))
    scene = seal(Scene, "scene", scene_tpl | {"scene_id": spec["scene"]["scene_id"], "location": spec["scene"]["location"],
                                              "time": spec["scene"]["time"], "mood": spec["scene"]["mood"],
                                              "participant_ids": ["IRIS"] if spec["iris"] else [],
                                              "continuity_constraints": ([spec.get("identity_continuity",
                                                                                   IDENTITY_CONTINUITY[spec["look"]])]
                                                                         if spec["iris"] else [])
                                              + [spec.get("palette", PALETTE[spec["look"]])],
                                              "visual_reference_asset_ids": [r[0] for r in refs]})
    rules = spec["rules"]
    continuity = [IDENTITY_TEXT] if spec["iris"] else []
    continuity += [observable for _, observable, _, _ in rules]
    shot_tpl = core(source_model("shot-intro.json", Shot))
    shot_data = shot_tpl | {"shot_id": spec["shot_id"], "scene_id": spec["scene"]["scene_id"], "storyboard_beat_id": spec["beat"],
                            "intent": prompt, "narration": "", "character_ids": ["IRIS"] if spec["iris"] else [],
                            "continuity_constraints": continuity,
                            "required_asset_roles": [{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]}]
                            + ([{"role": "first_frame" if frames[x["asset_id"]] == "approved_keyframe" else "last_frame",
                                 "asset_ids": [x["asset_id"]], "allowed_asset_types": ["image"]} for x in selections] if frames else
                               [{"role": "reference", "asset_ids": [x["asset_id"] for x in selections if x.get("kind") != "audio"],
                                 "allowed_asset_types": ["image"]}]),        # the audio binds through the row, not the Shot
                            "generated_video_rationale": "需要真实摄影运动与光影变化；静帧和动态分镜不证明镜头已完成。"}
    shot = seal(Shot, "shot", shot_data)
    gen_refs = [{"role": frames[aid], "asset_id": aid} if frames else {"role": "scene_reference", "asset_id": aid}
                for aid, _, _, _, _, _ in refs]
    if audio:
        gen_refs.append({"role": "reference_audio", "asset_id": audio["asset_id"]})
    row = {"shot": shot_data,
           "generation": {"references": gen_refs, "generation_intent": gi.model_dump(mode="json"),
                          "intent_evidence": {"character_action_required": bool(spec["iris"]), "state_change_required": False,
                                              "subject_motion_directive_present": True},
                          "output_need": {"timing_mode": "content_driven", "duration_seconds": secs, "geometry_policy": "adaptive",
                                          "aspect_ratio": "16:9", "container_mime": "video/mp4"},
                          "audio_need": "optional", "quality_need": {"objective_tier": "preview"},
                          **({"conditioning_compatibility": spec["conditioning"]} if "conditioning" in spec else {})},
           "composition": {"muted": True, "source_audio_policy": "MUTE", "source_audio_reason": "成片使用已选定歌曲 all-hands-r4 母带独立音轨"},
           "boundary": {"independent": True, "reason": "按分镜 v4 由最终剪辑切接；不要求复制前镜终态"}}
    authored = {"native_prompt": prompt, "row": row}
    authored_ref = authoring_input_reference(authored)
    provenance.append(authored_ref)
    out = root / authored_ref.reference
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(authoring_input_payload(authored))

    lines = prompt.splitlines()
    profile = {"domain_id": "iris-source", "profile_id": f"iris-v4-{unit.lower()}-raw", "profile_version": "1",
               "measurement_contract_version": "iris-exact-mp4-review/1", "required_requirement_ids": [r[0] for r in rules],
               "requirement_semantics_version": "requirement-semantics/1", "generation_requirements": []}
    h = canonical_sha256(authored)
    gi_json = gi.model_dump(mode="json")
    paths_all = list(leaves(gi_json, "generation_intent"))
    owner = {}
    for path in paths_all:
        owner[path] = next((rid for rid, _, _, keys in rules if any(k in path for k in keys)), rules[0][0])
    for rid, observable, fragment_line, _ in rules:
        paths = [p for p in paths_all if owner[p] == rid]
        src = {"source_hash": h, "locator": "row.shot.continuity_constraints", "intent_item_id": rid, "quote": observable,
               "origin": "director_choice"}
        profile["generation_requirements"].append({
            "requirement_id": rid, "level": "acceptance", "stage": "raw_generation", "dimension": rid, "observable": observable,
            "tolerance": "逐项满足已认可参考与上述职责，未生成前不得判PASS",
            "measurement": "exact MP4正常速度审看与project-local video-analysis逐项核对", "proof": "analyzer",
            "intent_paths": paths, "native_text": [lines[fragment_line]],
            "native_text_mapping": {"intent_sha256": canonical_sha256(gi_json),
                                    "bindings": [{"intent_path": p, "fragment_indices": [0]} for p in paths]},
            "production_owner": "shot_authoring",
            "semantics": {"version": "requirement-semantics/1", "category": "narrative_critical", "intent_role": "must_happen",
                          "source_refs": [src], "hard_basis": {"kind": "approved_narrative", "source_hash": h,
                          "locator": "row.shot.continuity_constraints",
                          "necessity": "分镜 v4 与使用者认可的预览包决定这一镜承担的可见事件。"}}})
    ph = canonical_sha256(profile)
    acceptance = DomainAcceptancePolicy(domain_id="iris-source", profile_id=profile["profile_id"], profile_version="1",
        measurement_contract_version="iris-exact-mp4-review/1", required_requirement_ids=tuple(profile["required_requirement_ids"]),
        profile_content_hash=ph, profile_payload=profile | {"content_hash": ph})
    qa = seal(QaPolicy, "qa", {
        "policy_id": profile["profile_id"], "policy_version": "1", "required_layers": ["technical", "semantic", "final_acceptance"],
        "technical_thresholds": {"black_luma_max_milli": 10, "silence_peak_max_millidb": -60000, "clipping_peak_min_millidb": -100},
        "layout_rules": {"safe_area_inset_milli": 50, "caption_overflow_tolerance_milli": 0}, "strategy_rules_version": "iris-source/1",
        "semantic_requirement": "required", "semantic_authorities": [{"name": "video-analysis", "version": "project-local"}],
        "generation_acceptance": acceptance,
        "generation_evaluation_authorities": [{"evaluator": {"name": "video-analysis", "version": "project-local"}, "proof": "analyzer"}],
        "final_output": {"goal_id": f"iris-v4-{unit.lower()}-source", "goal_version": "1",
                         "user_goal": f"分镜 v4 {cu} {ZH_SECONDS[secs]}秒源片（{unit}）；不代表整集或人工验收",
                         "requirements": [{"requirement_id": r[0], "observable": r[1], "proof": "human"} for r in rules]}})
    for name, obj in (("scene.json", scene), ("shot.json", shot), ("qa-policy.json", qa), ("registry-draft.json", registry)):
        write(root, name, obj.model_dump(mode="json"))
    for name, obj in (("row.json", row), ("preview-approval.json", preview), ("source-selections.json", selections)):
        write(root, name, obj)
    (root / "native-prompt.zh.txt").write_text(prompt + "\n", encoding="utf-8")
    print(json.dumps({"unit": unit, "draft": str(root), "refs": [s["asset_id"] for s in selections],
                      "character": "v4-anchor-F1a" if spec["iris"] else None,
                      "prompt_chars": len(prompt), "canonical_writes": 0, "provider_calls": 0}, ensure_ascii=False))
    return root


# ---------------------------------------------------------------- materialize
def materialize(unit: str, profile_path: Path) -> None:
    from ai_video.canvas_dependencies import initialize_canvas_graph
    from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
    from ai_video.production.jimeng_contracts import JimengProfile
    from ai_video.production.shot_router import RouterPolicyIdentity, VideoRoutingPolicy
    from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter, _canonical_yaml_bytes
    from scripts.jimeng_feedback_driver import DriverConfiguration, create_runtime

    spec = SPECS[unit]
    root = UNITS / unit
    project_root = root / "project"
    if project_root.exists():
        raise Blocked("project already materialized; inspect it instead of rebuilding")
    profile = JimengProfile.model_validate_json(profile_path.read_bytes())
    mode, secs, gen = spec["input_mode"], spec["duration"], spec["generation"]
    if (profile.model_id, profile.input_mode, profile.duration_seconds, profile.resolution, profile.aspect_ratio) != (
            gen["model"], mode, secs, gen["resolution"], gen["aspect"]):
        raise Blocked(f"profile must be {gen['model']} {mode} {secs}s {gen['resolution']} {gen['aspect']}")
    production_input = EP / "production-input"         # the episode's delivery and renderer policy (1920×1080 30fps, HyperFrames)
    delivery = DeliveryProfile.model_validate_json((production_input / "delivery-profile.json").read_bytes())
    renderer = RendererPolicy.model_validate_json((production_input / "renderer-policy.json").read_bytes())

    def typed(name, cls):
        obj = cls.model_validate_json((root / name).read_bytes())
        if not verify_artifact_hash(obj):
            raise Blocked("draft hash changed: " + name)
        return obj

    scene, shot, qa = typed("scene.json", Scene), typed("shot.json", Shot), typed("qa-policy.json", QaPolicy)
    char = None
    if spec["iris"]:
        identity_blocks(spec["look"])                                 # board and anchor unchanged since the draft
        char = typed("character.json", Character)
    registry = AssetRegistrySnapshot.model_validate_json((root / "registry-draft.json").read_bytes())
    selections = json.loads((root / "source-selections.json").read_text())
    prepared = lambda path, payload: PreparedArtifact(Path(path), payload, hashlib.sha256(payload).hexdigest())
    artifacts = {}
    for item in selections:
        raw = (REPO / item["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise Blocked("approved source changed: " + item["asset_id"])
        record = next(a for a in registry.assets if a.asset_id == item["asset_id"])
        artifacts[record.artifact_path] = prepared(record.artifact_path, raw)
    registry = AssetRegistrySnapshot(schema_version=registry.schema_version, revision_id="0" * 64, content_hash="0" * 64,
                                     assets=tuple(sorted(registry.assets, key=lambda a: a.asset_id)))
    rh = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": rh, "content_hash": rh})

    provenance = list(dict.fromkeys((*scene.source_provenance, *shot.source_provenance, *qa.source_provenance,
                                     *(char.source_provenance if char else ()))))
    for ref in provenance:
        if not ref.reference.startswith("evidence/authoring-input/"):
            continue
        own = root / ref.reference
        if not own.is_file():
            raise Blocked("creative provenance missing: " + ref.reference)
        raw = own.read_bytes()
        if canonical_sha256(json.loads(raw)) != ref.content_hash:
            raise Blocked("creative provenance changed")
        artifacts[Path(ref.reference)] = prepared(ref.reference, raw)

    def reseal(obj, **updates):
        return seal_artifact(obj.model_copy(update=updates))

    def model_artifact(model):
        path = Path("creative") / model.artifact_id / (model.content_hash + ".yaml")
        artifacts[path] = prepared(path, _canonical_yaml_bytes(model))
        return ArtifactReference(artifact_id=model.artifact_id, revision=model.revision, content_hash=model.content_hash, path=path)

    tag = f"iris-v4-{unit.lower()}"
    scene = reseal(scene, artifact_id=f"{tag}-scene")
    shot = reseal(shot, artifact_id=f"{tag}-shot")
    common = dict(revision=1, content_hash="0" * 64, creation_receipt_id=f"{tag}-authoring", source_provenance=tuple(provenance))
    brief = seal_artifact(ProductionBrief(artifact_id=f"{tag}-brief", title=f"IRIS EP01 v4 {unit} source",
        objective=f"分镜 v4 {spec['coverage_unit']} {ZH_SECONDS[secs]}秒源片", audience="中文短视频观众", format=f"{spec['generation']['resolution']} 16:9 source for the 1920×1080 30fps horizontal delivery",
        language="zh", constraints=shot.continuity_constraints, **common))
    story = seal_artifact(Story(artifact_id=f"{tag}-story", language="zh", logline="IRIS EP01 v4 " + unit,
        synopsis=shot.intent.splitlines()[0], beats=(StoryBeat(beat_id=spec["beat"], summary=f"分镜 v4 {unit}"),), **common))
    board = seal_artifact(Storyboard(artifact_id=f"{tag}-storyboard", beats=(StoryboardBeat(beat_id=spec["beat"],
        scene_id=scene.scene_id, shot_ids=(shot.shot_id,), narrative_intent=f"分镜 v4 {unit}，由最终剪辑切接"),), **common))
    char = reseal(char, artifact_id=f"{tag}-character") if char else None
    chars = (model_artifact(char),) if char else ()
    refs = ProjectArtifactRefs(brief=model_artifact(brief), story=model_artifact(story), characters=chars,
                               scenes=(model_artifact(scene),), storyboard=model_artifact(board), shots=(model_artifact(shot),))
    project = seal_artifact(ProductionProject(artifact_id=f"{tag}-project", project_id=f"{tag}-source", title=f"IRIS EP01 v4 {unit} source",
        default_language="zh", delivery_profile=delivery, renderer_policy=renderer, artifacts=refs, **common))

    project_root.mkdir(parents=True, mode=0o700)
    committer = ProductionStateCommitter(project_root)
    manifest = committer.bootstrap_initial_state(attempt_id=f"{tag}-bootstrap", project=project, registry=registry,
                                                 artifacts=tuple(artifacts[p] for p in sorted(artifacts)))
    manifest = initialize_canvas_graph(committer, f"{tag}-graph")
    manifest = committer.upgrade_manifest_schema("2.14", expected_manifest_revision=manifest.manifest_revision)
    committer.activate_qa_policy(qa, attempt_id=f"{tag}-qa-" + qa.content_hash[:16], expected_manifest_revision=manifest.manifest_revision)

    row = json.loads((root / "row.json").read_text())
    task = f"{tag}-source-001"
    routing = VideoRoutingPolicy(identity=RouterPolicyIdentity(policy_id=f"{tag}-qualification", policy_version="1",
        policy_sha256=canonical_sha256({"shot": shot.shot_id, "profile": profile.model_dump(mode="json"), "ceiling": 1})),
        local_resources_available=False, remote_authorized=True, budget_authorized=True, execution_purpose="qualification")
    limits = ExecutionLimits(task_id=task, generation_forbidden=False, allowed_remote_candidates=("jimeng/" + profile.capability_id,),
                             paid_submit_ceiling=1, paid_submits_used=0, local_batch_limit=1, local_batch_used=0,
                             local_total_used=0, local_resource_available=False)
    config = {"schema_version": "jimeng-feedback-driver/1", "row": row, "routing_policy": routing.model_dump(mode="json"),
              "decision_policy": DecisionPolicy(max_resamples=0, allow_bounded_exploration=True).model_dump(mode="json"),
              "execution_limits": limits.model_dump(mode="json"), "jimeng_profile": profile.model_dump(mode="json")}
    write(root, "driver-config.json", config)
    runtime = create_runtime(project_root=project_root, configuration=DriverConfiguration.from_json(config))
    result = runtime.prepare()
    write(root, "prepare-result.json", serial(result))
    if result.resolved_request is None or result.execution_binding is None:
        write(root, "prepare-blocker.json", {"decision": serial(result.decision), "compilation": serial(result.compilation),
                                             "new_provider_calls": 0})
        raise Blocked("prepare blocked; see prepare-blocker.json (no start, no submit)")
    request = result.resolved_request.model_dump(mode="json")
    expected = [x["asset_id"] for x in selections if x.get("kind") != "audio"]
    actual = [x["asset_id"] for x in request["image_bindings"]]
    media = [x["asset_id"] for x in request["media_bindings"]]
    vocals = [x["asset_id"] for x in selections if x.get("kind") == "audio"]
    if media != vocals:                          # only the approved vocal window, and only for a multimodal unit
        raise Blocked(f"resolved media bindings differ from the approved audio reference: {media} vs {vocals}")
    if actual != expected:                       # the first frame or the reference image is the only image
        raise Blocked(f"resolved reference order differs from the authored order: {actual} vs {expected}")
    (root / "compiled-native-prompt.zh.txt").write_text(result.compilation.request.prompt_text + "\n", encoding="utf-8")
    write(root, "materialization-result.json", {"project_root": str(project_root), "task_id": task,
          "request_hash": result.resolved_request.resolved_generation_hash, "resolved_reference_order": actual,
          "new_provider_calls": 0, "new_attempt_started": False})
    print(json.dumps({"unit": unit, "prepared": True, "resolved_reference_order": actual, "new_provider_calls": 0}, ensure_ascii=False))


# ---------------------------------------------------------------- show
def show(unit: str) -> None:
    """Print the resolved request the transport-free prepare sealed; reads files only (no network, no writes)."""
    root = UNITS / unit
    request = json.loads((root / "prepare-result.json").read_text())["resolved_request"]
    if request is None:
        raise Blocked("prepare did not resolve a request; see prepare-blocker.json")
    profile = json.loads((root / "driver-config.json").read_text())["jimeng_profile"]
    out = request["effective_output"]
    print(json.dumps({"unit": unit, "request_hash": request["resolved_generation_hash"], "model": request["model_id"],
        "input_mode": profile.get("input_mode", "multimodal"), "request_mode": request["mode"],
        "capability": request["capability_id"], "seconds": out["duration_seconds"], "resolution": out["resolution_label"],
        "aspect": out["ratio"], "native_audio": out["native_audio"],
        "credit_upper_bound": profile["credit_upper_bound"], "benefit": [profile["benefit_type"], profile["benefit_amount"]],
        "image_bindings": [{k: b[k] for k in ("role", "asset_id", "asset_sha256", "mime_type", "width", "height")}
                           for b in request["image_bindings"]],
        "media_bindings": [{k: b[k] for k in ("kind", "role", "asset_id", "asset_sha256", "mime_type", "duration_millis")}
                           for b in request["media_bindings"]],
        "prompt": request["prompt_text"], "new_provider_calls": 0}, ensure_ascii=False, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["draft", "materialize", "show"])
    ap.add_argument("unit", choices=sorted(SPECS))
    ap.add_argument("--profile", type=Path)
    args = ap.parse_args()
    try:
        if args.action == "draft":
            draft(args.unit)
        elif args.action == "show":
            show(args.unit)
        else:
            if args.profile is None:
                raise Blocked("--profile (fresh empty canvas node) is required")
            materialize(args.unit, args.profile)
    except Blocked as error:
        print(json.dumps({"blocked": True, "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
