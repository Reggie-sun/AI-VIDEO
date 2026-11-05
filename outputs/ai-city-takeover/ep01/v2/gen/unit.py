#!/usr/bin/env python3
"""IRIS EP01 v2 generation units through the canonical owners: one independent source project per Shot.

  uv run python outputs/ai-city-takeover/ep01/v2/gen/unit.py draft S3
  uv run python outputs/ai-city-takeover/ep01/v2/gen/unit.py materialize S3 --profile <unit>/profile.json

draft        typed Scene / Shot / QA policy / Registry drafts and the director row, bound to board v2.1
             coverage and the user's preview approval. No canonical writes, no Provider calls.
materialize  bootstraps gen/<unit>/project with ProductionStateCommitter, activates the QA policy,
             writes driver-config.json and runs the transport-free prepare. No Provider call.

Pattern follows the working Codex C unit (ep01/generation-c-draft); this file only generalises it per Shot.
Submission is a separate step (operator.py) with its own one-use bound.
"""
from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
import sys
import wave

P = Path(__file__).resolve().parent
V2 = P.parent
EP = V2.parent
REPO = P.parents[4]
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference  # noqa: E402
from ai_video.production.domain_acceptance import DomainAcceptancePolicy  # noqa: E402
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash  # noqa: E402
from ai_video.production.models import (AssetRecord, AssetRegistrySnapshot, ArtifactReference,  # noqa: E402
    AudioAssetMetadata, AudioLoudnessMetadata, AudioSource,
    ProductionBrief, ProductionProject, ProjectArtifactRefs, QaPolicy, Scene, Shot, Story, StoryBeat,
    Storyboard, StoryboardBeat)
from ai_video.production.paths import canonical_audio_asset_path, canonical_image_asset_path  # noqa: E402
from ai_video.production.preview_approval import preview_approval_authoring_input  # noqa: E402
from ai_video.production.reference_authoring import director_coverage_authoring_input  # noqa: E402
from ai_video.production.registry import registry_semantic_sha256  # noqa: E402
from ai_video.production.video_requirement import GenerationIntent  # noqa: E402

BASE = EP / "a01-first-frame-repair/project"          # canonical IRIS Character, identity assets and delivery profile
IDENTITY = ("iris-cf-details", "outputs/ai-city-takeover/series/identity-cf/raw/CF-ID7b-a.png",
            "approved front IRIS identity: face, left-ear device and fine red left-collar line", "identity", "identity",
            "只控制她的面貌、左耳黑色耳挂与左领口极细红线")
USER_QUOTE = "認可，開始生成"
AI_LABEL = "保留平台正常人工智能生成标识，不删除、不遮挡它；不新增字幕、片名、文字、图形或界面。"
IDENTITY_TEXT = "同一女性面貌、左耳黑色耳挂、左领极细红灯线、炭黑高领大衣与后梳低髻完整保持"


class Blocked(ValueError):
    pass


# intent paths each rule answers for (first match wins; anything unmatched belongs to the first rule)
CAMERA_KEYS = ("camera_", "axis_continuity", "space_continuity", "reference_planning.events", "motion_envelope", "pacing",
               "subject_action")
PERFORMANCE_KEYS = ("performance_intent", "subject_action", "motion_envelope", "pacing")
IDENTITY_KEYS = ("identity_continuity", "reference_planning.anchors", "reference_planning.selections")
LABEL_KEYS = ("visual_treatment", "ambience_intent", "dialogue_intent", "music_intent")


# ---------------------------------------------------------------- unit specs (board v2.1)
# Asset IDs are chosen so the native image order (sorted by ID within a role) equals the order the prompt
# names them in: scene or start frame first ("iris-c-..."), the identity sheet "iris-cf-details" second.
def iris_performance(trigger, response, gaze, body, terminal, emotion, face):
    return {"trigger": trigger, "visible_response": response, "gaze_target": gaze, "body_behavior": body,
            "hand_behavior": "双手不入画或保持静止，不操作任何设备", "terminal_performance_state": terminal,
            "character_directions": [{"character_id": "IRIS", "screen_identity": IDENTITY_TEXT, "role": "principal",
                                      "visibility": "visible", "beats": [{"phase": "throughout", "trigger": trigger,
                                      "emotion": emotion, "intensity": "subtle", "facial_expression": face,
                                      "gaze_target": gaze, "breathing": "自然平稳", "body_behavior": body}]}]}


SPECS = {
    "S3": {
        "shot_id": "ep01v2-s3", "beat": "training", "scene": {
            "scene_id": "aisle", "location": "凌晨数据中心机房走道", "time": "凌晨；事件日期 2026-09-20",
            "mood": "冷静、精密、略有压迫感"},
        "refs": [("iris-v2-s3-aisle", "outputs/ai-city-takeover/ep01/v2/keyframes/raw/K3-a.png",
                  "approved K3: start frame, aisle composition, light and the red door gap", "aisle", "scene_environment",
                  "这个镜头的起始画面、场景与光线")],
        "iris": False,
        "prompt": [
            "真人电影摄影，横幅十六比九，连续六秒。参考图是这个镜头的起始画面、场景与光线：凌晨的数据中心机房走道，两侧是黑色服务器机柜，尽头左侧一扇半开的机柜门漏出一道窄窄的红光。",
            "画面中没有人。摄影机从走道中央齐胸高度出发，沿走道中轴非常缓慢、平稳地向前推进，越来越接近尽头那道红色门缝；红光在地面和对面机柜玻璃上的反光随推进变化。机柜玻璃后细小的冷蓝指示灯轻微闪烁，空气中有极淡的薄雾。",
            "保持对称构图，不转向、不摇镜、不切镜，末段平滑收稳。蓝黑与钢蓝冷色，红色只来自那道门缝。机柜上不出现可读文字。",
            AI_LABEL + "只有极轻的机房风扇环境声，不生成对白、旁白、演唱或音乐；成片使用独立音轨。",
        ],
        "intent": {
            "open": "参考图K3的走道起始画面，尽头左侧半开机柜门漏出窄红光", "close": "推进到更接近红色门缝处平滑收稳，构图仍对称",
            "action_start": "空无一人的走道，机柜指示灯闪烁", "progression": "摄影机沿走道中轴缓慢推进，红色门缝逐渐变大、反光随之变化",
            "endpoint": "更接近红色门缝，红光与反光清晰", "camera": "沿走道中轴非常缓慢平稳地向前推进，越来越接近尽头红色门缝，末段收稳",
            "framing": "对称走道构图，尽头红色门缝在画面中线偏左", "start_framing": "K3原始走道全景", "end_framing": "更近的走道与红色门缝",
            "light": "尽头门缝的红光与机柜冷蓝指示灯", "ambience": "极轻机房风扇环境声", "space": "镜头始终在走道中轴",
            "motion_peak": "推进过程中红色门缝逐渐变大", "natural": ["机柜玻璃后细小的冷蓝指示灯轻微闪烁"],
            "open_event": ("尽头左侧一扇半开的机柜门漏出一道窄窄的红光", "保持对称构图"),
            "close_event": ("越来越接近尽头那道红色门缝", "末段平滑收稳"),
        },
        # no person on screen: the scene itself performs and the camera relates to the red door gap
        "performance": {"trigger": "凌晨机房里一扇机柜门没有关", "visible_response": "红光从门缝漏出，在地面和对面机柜玻璃上反射",
                        "gaze_target": "画面中没有人物；构图把视线引向尽头的红色门缝", "body_behavior": "画面中没有人物",
                        "hand_behavior": "画面中没有人物", "terminal_performance_state": "红色门缝更近、更清楚"},
        "relation": {"subject_id": "red-door-gap", "relation_kind": "reveal",
                     "start_relation": "尽头红色门缝在远处，占画面很小", "end_relation": "红色门缝在画面中更大、更清楚"},
        "rules": [("aisle-start", "以K3走道为起始画面，空无一人，尽头左侧半开机柜门漏出窄红光", 0, ()),
                  ("push-to-door", "摄影机沿走道中轴缓慢平稳推进，红色门缝逐渐变近，不转向、不切镜", 1, CAMERA_KEYS),
                  ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)],
    },
}

KF = "outputs/ai-city-takeover/ep01/v2/keyframes/raw/"
ZH_SECONDS = {4: "四", 5: "五", 6: "六"}
SONG_BED = "outputs/ai-city-takeover/ep01/v2/song/bed-01/music__20261102_004125.mp3"     # approved song v2 bed
SONG_BED_SHA256 = "f45c385ef6ec3c5ef817cce72ba6c9d6e5f6fbb21849e80ed8b794d137f08973"
QUIET = "只有极轻的环境声，不生成对白、旁白、演唱或音乐；成片使用独立音轨。"
IRIS_RULES = lambda observer, camera: [("identity", IDENTITY_TEXT, 0, IDENTITY_KEYS),
                                       ("observer", observer, 1, PERFORMANCE_KEYS),
                                       ("camera", camera, 2, CAMERA_KEYS),
                                       ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)]
LOCKED = {"movement_kind": "locked", "direction": "none", "amplitude_class": "subtle", "speed_class": "very_slow",
          "start_motion_state": "stationary", "end_motion_state": "settled"}
# gate-S5 FAIL (2026-11-02): the "very slow push, settle at the end" accelerated through the last second instead.
# The approved coverage treatment for S1, S5 and S7 is static, so they hold a locked camera.
LOCKED_CAMERA = "摄影机完全固定在三脚架上，全程不推近、不拉远、不移动、不摇镜，保持第一张图的景别与人物位置。"
LOCKED_INTENT = "摄影机完全固定，全程不推近、不移动、不摇镜"

SPECS.update({
    "S5": {
        "shot_id": "ep01v2-s5", "beat": "looked", "iris": True,
        "scene": {"scene_id": "window", "location": "同一高层建筑室内落地窗前", "time": "凌晨", "mood": "冷静、疏离"},
        "refs": [("iris-c-v2-s5-window", KF + "K5b-a.png", "approved K5b: start frame, window composition and light",
                  "window", "scene_environment", "这个镜头的起始画面、构图与光线")],
        "prompt": [
            "真人电影摄影，横幅十六比九，连续六秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在高层室内的落地窗前，侧面朝向画面左侧的窗外；第二张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第二张图的背景。",
            "她平静地望着窗外雾中的城市，像一个安静的旁观者；视线缓慢落在远处的某一点，嘴唇自然闭合，只有自然呼吸和一两次轻微眨眼。她不转身、不说话、不抬手。窗外远处高架上的车灯缓慢流动。",
            "摄影机固定在原位，极缓慢地微微推近，末段平滑收稳。玻璃干净透明，没有她的倒影。室内很暗，窗外冷光勾出她的侧脸轮廓。蓝黑与钢蓝冷色，红色只在她左领口的细灯线。",
            AI_LABEL + QUIET,
        ],
        "intent": {
            "open": "K5b起始画面：她侧面朝向画面左侧的窗外", "close": "她仍侧面望着窗外远处，嘴唇闭合，镜头略近",
            "action_start": "侧面朝向窗外站定", "progression": "视线缓慢落在远处的某一点，只有自然呼吸与轻微眨眼",
            "endpoint": "仍侧面望着窗外远处", "camera": "摄影机固定在原位，极缓慢地微微推近，末段平滑收稳",
            "framing": "K5b侧面中近景，窗在画面左侧", "start_framing": "K5b原始侧面中近景", "end_framing": "略近的同一侧面构图",
            "light": "窗外冷光勾出侧脸轮廓", "ambience": "极轻室内环境声", "space": "她站在窗前原位",
            "motion_peak": "视线落在远处", "natural": ["只有自然呼吸和一两次轻微眨眼"],
            "open_event": ("侧面朝向画面左侧的窗外", "像一个安静的旁观者"),
            "close_event": ("视线缓慢落在远处的某一点", "末段平滑收稳"),
        },
        "performance": iris_performance("凌晨独自站在窗前", "视线缓慢落在远处的某一点", "窗外远处的城市", "站定不动，只有自然呼吸",
                                        "仍侧面望着窗外，嘴唇自然闭合", "冷静疏离", "嘴唇自然闭合，神情平静"),
        "rules": IRIS_RULES("她平静地望向窗外远处，嘴唇自然闭合，不转身、不说话、不抬手",
                            "摄影机固定在原位，极缓慢微微推近，末段平滑收稳；玻璃上没有倒影"),
    },
    "S7": {
        "shot_id": "ep01v2-s7", "beat": "offline", "iris": True,
        "scene": {"scene_id": "cache-room", "location": "几乎全黑的房间，悬浮着半透明发光薄片", "time": "凌晨", "mood": "安静、疏离"},
        "refs": [("iris-c-v2-s7-cache-room", KF + "K7-a.png", "approved K7: start frame, dark room with floating panes",
                  "cache-room", "scene_environment", "这个镜头的起始画面、构图与光线")],
        "prompt": [
            "真人电影摄影，横幅十六比九，连续六秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在几乎全黑的房间里，几块半透明的发光薄片悬浮在她身前和身侧；第二张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第二张图的背景。",
            "她平静地直视镜头，嘴唇自然闭合，不说话、不唱歌；只有自然呼吸与轻微眨眼。半透明薄片在她面前缓慢横向滑过，薄片发出的冷白光斑缓缓扫过她的脸和立领。薄片上没有任何可读内容。",
            LOCKED_CAMERA + "蓝黑与钢蓝冷色，红色只在一块薄片的边缘和她左领口的细灯线。",
            AI_LABEL + QUIET,
        ],
        "intent": {
            "open": "K7起始画面：几块半透明的发光薄片悬浮在她身前和身侧", "close": "光斑扫过她的脸，她仍平静直视镜头，构图不变",
            "action_start": "直视镜头站定", "progression": "薄片缓慢横向滑过，冷白光斑扫过脸和立领",
            "endpoint": "仍平静直视镜头，嘴唇闭合", "camera": LOCKED_INTENT,
            "framing": "K7正面近景，人物在画面中央偏右", "start_framing": "K7原始正面近景", "end_framing": "与起始相同的正面构图",
            "light": "薄片发出的冷白光", "ambience": "极轻环境声", "space": "她站在房间原位",
            "motion_peak": "光斑扫过她的脸", "natural": ["只有自然呼吸与轻微眨眼"],
            "open_event": ("几块半透明的发光薄片悬浮在她身前和身侧", "她平静地直视镜头"),
            "close_event": ("薄片发出的冷白光斑缓缓扫过她的脸和立领", "保持第一张图的景别与人物位置"),
        },
        "performance": iris_performance("离线的房间里薄片滑过", "光斑扫过脸时神情不变", "镜头", "站定不动，只有自然呼吸",
                                        "仍平静直视镜头，嘴唇自然闭合", "冷静疏离", "嘴唇自然闭合，神情平静"),
        "rules": IRIS_RULES("她平静直视镜头，嘴唇闭合，不说话、不唱歌；薄片缓慢滑过，光斑扫过脸",
                            LOCKED_INTENT + "，保持第一张图的景别与人物位置；薄片上没有可读内容"),
        "camera_motion": LOCKED,
    },
    "S1": {
        "shot_id": "ep01v2-s1", "beat": "sleeping", "iris": True,
        "scene": {"scene_id": "eye-macro", "location": "IRIS 左眼的微距特写", "time": "凌晨", "mood": "静止、醒来之前"},
        "refs": [("iris-c-v2-s1-eye", KF + "K1a-a.png", "approved K1a: start frame, closed left eye macro",
                  "eye-macro", "scene_environment", "这个镜头的起始画面、构图与光线")],
        "prompt": [
            "真人电影微距摄影，横幅十六比九，连续六秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性左眼的极近特写，眼睛闭着；第二张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第二张图的背景与构图。",
            "她的左眼始终闭着，不睁开；眼睑下的眼球有极轻微的移动，睫毛偶尔轻轻颤动，像在醒来之前。窗外冷蓝色的城市光缓慢掠过眼睑和皮肤，下眼睑上一点细细的红色反光保持微弱。",
            "摄影机完全固定在三脚架上，全程不推近、不拉远、不移动、不摇镜，保持第一张图的微距构图。真实皮肤纹理、细小汗毛和极淡雀斑清晰，微距浅景深。蓝黑与钢蓝冷色，红色只在下眼睑那一点微弱反光。",
            AI_LABEL + QUIET,
        ],
        "intent": {
            "open": "K1a起始画面：同一位女性左眼的极近特写，眼睛闭着", "close": "左眼仍闭着，构图不变",
            "action_start": "左眼闭着", "progression": "眼睑下的眼球极轻微移动，睫毛偶尔轻轻颤动",
            "endpoint": "左眼仍闭着，没有睁开", "camera": LOCKED_INTENT,
            "framing": "K1a微距构图，左眼在画面中央", "start_framing": "K1a原始微距构图", "end_framing": "与起始相同的微距构图",
            "light": "窗外冷蓝色的城市光掠过眼睑", "ambience": "极轻环境声", "space": "微距原位",
            "motion_peak": "睫毛轻轻颤动", "natural": ["睫毛偶尔轻轻颤动"],
            "open_event": ("同一位女性左眼的极近特写，眼睛闭着", "像在醒来之前"),
            "close_event": ("她的左眼始终闭着，不睁开", "保持第一张图的微距构图"),
        },
        "performance": iris_performance("醒来之前", "眼睑下的眼球极轻微移动，睫毛偶尔颤动", "眼睛闭着", "面部不动",
                                        "左眼仍闭着", "平静", "眼睛闭合，面部放松"),
        "rules": IRIS_RULES("左眼始终闭着不睁开，只有眼球与睫毛的极轻微动作",
                            LOCKED_INTENT + "，保持第一张图的微距构图"),
        "camera_motion": LOCKED,
    },
    "S9a": {
        "shot_id": "ep01v2-s9a", "beat": "closed", "iris": False, "camera_motion": LOCKED,
        "input_mode": "first_last_frame",       # native endpoints; mode-4 soft references do not bind start and end
        "frame_roles": {"iris-c-v2-s9a-1-door-open": "approved_keyframe", "iris-c-v2-s9a-2-door-closed": "last_frame"},
        # K9e was made from K4 as the same view with the door shut: same scale, composition, axis and locked camera
        "conditioning": {"lane": "fl2va", "first_anchor_id": "iris-c-v2-s9a-1-door-open",
                         "last_anchor_id": "iris-c-v2-s9a-2-door-closed", "same_subject_scale": True,
                         "composition_compatible": True, "screen_order_compatible": True, "axis_compatible": True,
                         "camera_path_reachable": True, "character_prop_state_reachable": True,
                         "action_endpoint_reachable": True, "available_duration_seconds": 6.0},
        "scene": {"scene_id": "rack-door", "location": "机房里半开的机柜门与通往落地窗的线缆", "time": "凌晨", "mood": "冷静、收束"},
        "refs": [("iris-c-v2-s9a-1-door-open", KF + "K4-a.png", "approved K4: start frame, half-open red-lit rack door",
                  "door-open", "scene_environment", "这个镜头的起始画面"),
                 ("iris-c-v2-s9a-2-door-closed", KF + "K9e-a.png", "approved K9e: end frame, same view with the door closed",
                  "door-closed", "composition", "这个镜头的结束画面")],
        "prompt": [
            "真人电影摄影，横幅十六比九，连续六秒。首帧是这个镜头的起始画面：机房里一扇半开的黑色机柜门，门缝透出强烈的红光，线缆沿地面通往右侧的落地窗；尾帧是这个镜头的结束画面：同一机位，那扇机柜门已经完全关上，红光熄灭，只剩冷蓝。",
            "画面中没有人。开头红光门缝保持片刻，随后那扇机柜门平稳地转动关上，门缝逐渐变窄直到消失，红光随之熄灭，地面上的红色反光也消失。门关上后画面保持静止。",
            "摄影机固定不动，窗外城市灯光不变。蓝黑与钢蓝冷色，红色只在门缝里，门关上后不再有红色。",
            AI_LABEL + "可以有一声轻微的机柜门关上声和极轻的机房环境声，不生成对白、旁白、演唱或音乐；成片使用独立音轨。",
        ],
        "intent": {
            "open": "K4起始画面：一扇半开的黑色机柜门，门缝透出强烈的红光", "close": "K9e结束画面：机柜门完全关上，红光熄灭",
            "action_start": "半开的机柜门透出红光", "progression": "机柜门平稳转动关上，门缝变窄直到消失，红光熄灭",
            "endpoint": "门完全关上，只剩冷蓝", "camera": "摄影机固定不动",
            "framing": "K4与K9e同一机位", "start_framing": "K4原始构图", "end_framing": "K9e同一构图",
            "light": "门缝红光熄灭后只剩冷蓝", "ambience": "一声轻微的机柜门关上声与极轻机房环境声", "space": "机柜门在画面左侧",
            "motion_peak": "门缝变窄直到消失", "natural": ["窗外城市灯光不变"],
            "open_event": ("一扇半开的黑色机柜门，门缝透出强烈的红光", "开头红光门缝保持片刻"),
            "close_event": ("那扇机柜门已经完全关上，红光熄灭，只剩冷蓝", "门关上后画面保持静止"),
        },
        "performance": {"trigger": "门被关上", "visible_response": "门缝逐渐变窄直到消失，红光随之熄灭",
                        "gaze_target": "画面中没有人物；构图把视线引向那扇机柜门", "body_behavior": "画面中没有人物",
                        "hand_behavior": "画面中没有人物", "terminal_performance_state": "门完全关上，只剩冷蓝"},
        "relation": {"subject_id": "rack-door", "relation_kind": "fixed_frame",
                     "start_relation": "半开的机柜门在画面左侧", "end_relation": "关上的机柜门仍在画面左侧"},
        "rules": [("door-closes", "机柜门平稳关上，门缝变窄直到消失，红光熄灭，之后画面静止", 1, PERFORMANCE_KEYS),
                  ("same-view", "同一机位：从K4起始画面到K9e结束画面，摄影机固定不动", 0, CAMERA_KEYS),
                  ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)],
    },
})

# S5r: the one bounded repair after gate-S5 FAIL. Same references, performance and coverage unit; only the camera
# changes from a slow push to the locked camera the approved coverage specifies.
SPECS["S5r"] = {**SPECS["S5"], "coverage_unit": "S5", "camera_motion": LOCKED,
    "prompt": [SPECS["S5"]["prompt"][0], SPECS["S5"]["prompt"][1],
               LOCKED_CAMERA + "玻璃干净透明，没有她的倒影。室内很暗，窗外冷光勾出她的侧脸轮廓。蓝黑与钢蓝冷色，红色只在她左领口的细灯线。",
               AI_LABEL + QUIET],
    "intent": {**SPECS["S5"]["intent"], "close": "她仍侧面望着窗外远处，嘴唇闭合，构图不变", "camera": LOCKED_INTENT,
               "end_framing": "与起始相同的侧面构图",
               "close_event": ("视线缓慢落在远处的某一点", "保持第一张图的景别与人物位置")},
    "rules": IRIS_RULES("她平静地望向窗外远处，嘴唇自然闭合，不转身、不说话、不抬手",
                        LOCKED_INTENT + "，保持第一张图的景别与人物位置；玻璃上没有倒影")}

# S8a: lip-sync feasibility test on the first chorus pass (board v2.1 with s8a-lipsync-amendment.md).
# Clip t=0 is master 18.40 s; the vocal reference is 0.20 s silence + isolated vocal 18.60-22.90 s + 0.50 s silence.
LIPSYNC_KEYS = ("dialogue_intent", "performance_intent", "subject_action", "motion_envelope", "pacing")
LIPSYNC = "嘴型与参考音频逐音节同步：开口时机在正负两帧内，实测停顿处嘴型收小，音频前后嘴唇闭合，无声处没有多余嘴动，牙齿与下巴不变形"
CHORUS = "I didn't run — I just looked outside."
SPECS["S8a"] = {
    "shot_id": "ep01v2-s8a", "beat": "chorus-1", "iris": True, "duration": 5, "camera_motion": LOCKED,
    "scene": {"scene_id": "balcony", "location": "雨夜高层建筑的玻璃阳台", "time": "凌晨", "mood": "冷静、克制"},
    "refs": [("iris-c-v2-s8a-balcony", "outputs/ai-city-takeover/ep01/reference-package/A02-v1.png",
              "approved A02: start frame, rainy glass balcony, frontal close-up", "balcony", "scene_environment",
              "这个镜头的起始画面、构图与光线")],
    "audio": {"asset_id": "iris-c-v2-s8a-vocal", "role": "isolated chorus vocal the mouth follows",
              "path": "outputs/ai-city-takeover/ep01/v2/song/isolation/S8a-vocal-ref-18.40-23.40.wav",
              "window": [18.40, 23.40], "language": "en", "script": CHORUS,
              "basis": "board.md S8a spec as amended by s8a-lipsync-amendment.md (sealed before payment)"},
    "dialogue": {"mode": "dialogue", "language": "en", "speaker_id": "IRIS", "verbatim_text": CHORUS,
                 "start_seconds": 0.2, "end_seconds": 4.5, "on_screen": True,
                 "response_obligation": "对着镜头唱出这一句，嘴型与参考音频逐音节同步", "lip_sync_required": True},
    "prompt": [
        "真人电影摄影，横幅十六比九，连续五秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在雨夜高层建筑的玻璃阳台上，正面近景看着镜头；第二张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第二张图的背景。",
        "音频是她自己演唱的一句歌。她对着镜头轻声演唱，嘴型与音频的每一个音节严格同步：有声音时张口唱，声音停顿时嘴型随之收小，音频开始前和结束后嘴唇自然闭合。她神情冷静克制，眼神平稳地看着镜头，只有唱歌的嘴型、呼吸和自然眨眼；头部几乎不动，不点头、不摆头、不抬手。",
        LOCKED_CAMERA + "细雨在玻璃栏杆上缓慢滑落，背后城市灯光虚化。蓝黑与钢蓝冷色，红色只在她左领口的细灯线。牙齿和下巴自然稳定，不变形。",
        AI_LABEL + "声音只跟随参考音频里的演唱，不新增其他人声、旁白、乐器或音乐；成片使用独立音轨。",
    ],
    "intent": {
        "open": "A02起始画面：她在雨夜玻璃阳台上正面近景看着镜头，嘴唇闭合", "close": "唱完这一句，嘴唇闭合，仍平静看着镜头，构图不变",
        "action_start": "正面近景看着镜头，嘴唇闭合", "progression": "对着镜头轻声演唱，嘴型与音频逐音节同步",
        "endpoint": "唱完后嘴唇闭合，仍看着镜头", "camera": LOCKED_INTENT,
        "framing": "A02正面近景，人物在画面中央偏右，城市在左侧", "start_framing": "A02原始正面近景",
        "end_framing": "与起始相同的正面近景", "light": "雨夜城市冷光", "ambience": "极轻的雨声", "space": "她站在玻璃阳台原位",
        "motion_peak": "唱到长音时嘴型张开最大", "natural": ["只有唱歌的嘴型、呼吸和自然眨眼"],
        "open_event": ("正面近景看着镜头", "她神情冷静克制"),
        "close_event": ("音频开始前和结束后嘴唇自然闭合", "保持第一张图的景别与人物位置"),
    },
    "performance": iris_performance("副歌响起", "对着镜头轻声演唱，嘴型与音频逐音节同步", "镜头", "头部几乎不动，只有呼吸",
                                    "唱完后嘴唇闭合，仍平静看着镜头", "冷静克制", "唱歌的嘴型，神情平静"),
    "rules": [("identity", IDENTITY_TEXT, 0, IDENTITY_KEYS), ("lip-sync", LIPSYNC, 1, LIPSYNC_KEYS),
              ("camera", LOCKED_INTENT + "，保持第一张图的景别与人物位置", 2, CAMERA_KEYS),
              ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)],
}

# S8ar: the one bounded repair after gate-S8a FAIL (mouth open during the 0.20 s lead-in silence, lips not fully shut
# at the end). Single variable: the vocal reference starts on the sung onset (clip t=0 is master 18.60 s).
SPECS["S8ar"] = {**SPECS["S8a"], "coverage_unit": "S8a",
    "audio": {**SPECS["S8a"]["audio"], "path": "outputs/ai-city-takeover/ep01/v2/song/isolation/S8ar-vocal-ref-18.60-23.60.wav",
              "window": [18.60, 23.60],
              "basis": "board.md S8a spec, s8a-lipsync-amendment.md and its S8ar repair section (sealed before payment)"},
    "dialogue": {**SPECS["S8a"]["dialogue"], "start_seconds": 0.0, "end_seconds": 4.3},
    "prompt": [SPECS["S8a"]["prompt"][0],
               "音频是她自己演唱的一句歌，从第一帧就开始唱。她对着镜头轻声演唱，嘴型与音频的每一个音节严格同步：有声音时张口唱，声音停顿时嘴型随之收小；音频结束后双唇完全合拢，不再动。她神情冷静克制，眼神平稳地看着镜头，只有唱歌的嘴型、呼吸和自然眨眼；头部几乎不动，不点头、不摆头、不抬手。",
               SPECS["S8a"]["prompt"][2], SPECS["S8a"]["prompt"][3]],
    "intent": {**SPECS["S8a"]["intent"], "open": "A02起始画面：她在雨夜玻璃阳台上正面近景看着镜头，第一帧就开口唱",
               "action_start": "正面近景看着镜头，第一帧就开口唱", "close": "唱完这一句，双唇完全合拢，仍平静看着镜头，构图不变",
               "endpoint": "唱完后双唇完全合拢，仍看着镜头",
               "close_event": ("音频结束后双唇完全合拢", "保持第一张图的景别与人物位置")},
    "performance": iris_performance("副歌响起", "对着镜头轻声演唱，嘴型与音频逐音节同步", "镜头", "头部几乎不动，只有呼吸",
                                    "唱完后双唇完全合拢，仍平静看着镜头", "冷静克制", "唱歌的嘴型，神情平静")}

# S8b: second chorus pass on K8b (3/4 view), made the way the user chose for S8a ("用第一版"): the vocal reference starts
# mid-singing (end of pass 1), so the mouth is already singing at frame 0; criteria scoped to the film window.
SPECS["S8b"] = {**SPECS["S8a"], "shot_id": "ep01v2-s8b", "beat": "chorus-2", "duration": 4,
    # the canonical gate needs every provider input in a sealed preview; the user approved this S8b pack
    "preview_file": "preview-approval-S8b.json", "preview_quote": "認可，生成 S8b (Recommended)",
    "refs": [("iris-c-v2-s8b-balcony", KF + "K8b-a.png", "approved K8b: start frame, balcony three-quarter view", "balcony",
              "scene_environment", "这个镜头的起始画面、构图与光线")],
    "audio": {**SPECS["S8a"]["audio"], "asset_id": "iris-c-v2-s8b-vocal",
              "path": "outputs/ai-city-takeover/ep01/v2/song/isolation/S8b-vocal-ref-22.20-26.20.wav", "window": [22.20, 26.20],
              "basis": "board.md S8b, s8a-lipsync-amendment.md S8b section (sealed before payment), user choice for S8a"},
    "dialogue": {**SPECS["S8a"]["dialogue"], "start_seconds": 0.0, "end_seconds": 3.35,
                 "response_obligation": "唱出这一句，嘴型与参考音频逐音节同步，唱完闭嘴望向城市"},
    "prompt": [
        "真人电影摄影，横幅十六比九，连续四秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在雨夜高层建筑的玻璃阳台上，四分之三侧面望向画面左侧，城市在她身后的右侧；第二张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第二张图的背景。",
        "音频是她自己演唱的一句歌，从第一帧就开始唱。她轻声演唱，嘴型与音频的每一个音节严格同步：有声音时张口唱，声音停顿时嘴型随之收小；音频结束后双唇完全合拢，视线缓缓移向远处的城市。她神情冷静克制，只有唱歌的嘴型、呼吸和自然眨眼；头部几乎不动，不点头、不摆头、不抬手。",
        SPECS["S8a"]["prompt"][2], SPECS["S8a"]["prompt"][3]],
    "intent": {**SPECS["S8a"]["intent"],
               "open": "K8b起始画面：她在雨夜玻璃阳台上四分之三侧面望向画面左侧，第一帧就开口唱",
               "close": "唱完后双唇完全合拢，视线移向远处的城市，构图不变",
               "action_start": "四分之三侧面望向画面左侧，第一帧就开口唱", "progression": "轻声演唱，嘴型与音频逐音节同步",
               "endpoint": "唱完后双唇完全合拢，视线移向远处的城市",
               "framing": "K8b四分之三侧面近景，人物在画面左侧，城市在右侧", "start_framing": "K8b原始构图",
               "end_framing": "与起始相同的构图",
               "open_event": ("四分之三侧面望向画面左侧", "她神情冷静克制"),
               "close_event": ("音频结束后双唇完全合拢", "保持第一张图的景别与人物位置")},
    "performance": iris_performance("副歌第二遍", "轻声演唱，嘴型与音频逐音节同步，唱完视线移向城市", "唱完后望向远处的城市",
                                    "头部几乎不动，只有呼吸", "唱完后双唇完全合拢，望向远处的城市", "冷静克制", "唱歌的嘴型，神情平静"),
    "rules": [("identity", IDENTITY_TEXT, 0, IDENTITY_KEYS),
              ("lip-sync", LIPSYNC + "；唱完后视线移向远处的城市", 1, LIPSYNC_KEYS),
              ("camera", LOCKED_INTENT + "，保持第一张图的景别与人物位置", 2, CAMERA_KEYS),
              ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)]}

# S8b2: the same S8b request as a fresh attempt after S8b's reference upload failed before dispatch
# (known_no_effect receipt, no charge). Same inputs, prompt, criteria, preview approval and empty canvas node.
SPECS["S8b2"] = {**SPECS["S8b"], "coverage_unit": "S8b"}

# S8br: the one bounded repair of S8b after gate-S8b2 FAIL (last word and closing ~0.2 s late). Single variable: the
# approved S8b vocal with a 0.20 s silent lead-in, as in S8a take 1 (clip t=0 = master 22.00 s, 5 s).
SPECS["S8br"] = {**SPECS["S8b"], "coverage_unit": "S8b", "duration": 5,
    "preview_file": "preview-approval-S8br.json", "preview_quote": "認可修復參考，重做一次 (Recommended)",
    "audio": {**SPECS["S8b"]["audio"], "path": "outputs/ai-city-takeover/ep01/v2/song/isolation/S8br-vocal-ref-22.00-27.00.wav",
              "window": [22.00, 27.00],
              "basis": "s8a-lipsync-amendment.md S8b and S8br sections (sealed before payment), user approval of the repair reference"},
    "dialogue": {**SPECS["S8b"]["dialogue"], "start_seconds": 0.2, "end_seconds": 3.55},
    "prompt": [SPECS["S8b"]["prompt"][0].replace("连续四秒", "连续五秒"),
               "音频是她自己演唱的一句歌。她轻声演唱，嘴型与音频的每一个音节严格同步：有声音时张口唱，声音停顿时嘴型随之收小；音频结束后双唇完全合拢，视线缓缓移向远处的城市。她神情冷静克制，只有唱歌的嘴型、呼吸和自然眨眼；头部几乎不动，不点头、不摆头、不抬手。",
               SPECS["S8b"]["prompt"][2], SPECS["S8b"]["prompt"][3]],
    "intent": {**SPECS["S8b"]["intent"], "open": "K8b起始画面：她在雨夜玻璃阳台上四分之三侧面望向画面左侧",
               "action_start": "四分之三侧面望向画面左侧，随音频开口唱"}}

# ---------------------------------------------------------------- v3 performance redo (2026-11-02)
# User on film c1: 「2s这里没有睁眼的过程是为什么,衔接很弱.后面人物表现一直很弱,唱歌也是」. Scope 「S1 睁眼＋副歌＋S5/S7 反應
# (Recommended)」, singing 「冷靜但活著 (Recommended)」, preview 「認可，S1 用原生首尾幀 (Recommended)」. The c1 prompts held
# her to breath and blinks with the head still; these specs direct actual behaviour, and each approved performance still
# (keyframes/prompts-v3-performance.md) is a reference for expression and commitment only, never the opening frame.
V3_QUOTE = "認可，S1 用原生首尾幀 (Recommended)"
PERF_DUTY = "只示范她在这一镜要达到的神情与投入程度"
VOICE_ONLY = "声音只跟随参考音频里的演唱，不新增其他人声、旁白、乐器或音乐；成片使用独立音轨。"
SPECS["S1v3"] = {
    "shot_id": "ep01v2-s1", "beat": "sleeping", "iris": True, "coverage_unit": "S1", "camera_motion": LOCKED,
    "identity_waiver": "眼部巨特写只看得到左眼，身份由已认可的首尾帧K1a与K1c承担；使用者在v3预览中同意这一镜不附身份图",
    "input_mode": "first_last_frame",
    "frame_roles": {"iris-c-v3-s1-1-eye-closed": "approved_keyframe", "iris-c-v3-s1-2-eye-open": "last_frame"},
    # K1c was made from K1a as the same framing with the eye open
    "conditioning": {"lane": "fl2va", "first_anchor_id": "iris-c-v3-s1-1-eye-closed", "last_anchor_id": "iris-c-v3-s1-2-eye-open",
                     "same_subject_scale": True, "composition_compatible": True, "screen_order_compatible": True,
                     "axis_compatible": True, "camera_path_reachable": True, "character_prop_state_reachable": True,
                     "action_endpoint_reachable": True, "available_duration_seconds": 6.0},
    "preview_file": "preview-approval-v3-S1.json", "preview_quote": V3_QUOTE,
    "scene": {"scene_id": "eye-macro", "location": "IRIS 左眼的微距特写", "time": "凌晨", "mood": "静止、醒来"},
    "refs": [("iris-c-v3-s1-1-eye-closed", KF + "K1a-a.png", "approved K1a: start frame, eye closed", "eye-closed",
              "scene_environment", "这个镜头的起始画面"),
             ("iris-c-v3-s1-2-eye-open", KF + "K1c-a.png", "approved K1c: end frame, same framing with the eye open", "eye-open",
              "composition", "这个镜头的结束画面")],
    "prompt": [
        "真人电影微距摄影，横幅十六比九，连续六秒。首帧是这个镜头的起始画面：同一位女性左眼的极近特写，眼睛闭着；尾帧是这个镜头的结束画面：同一构图，她的左眼已经睁开，浅灰蓝色的虹膜清晰，正在对焦。",
        "前四秒她的左眼一直闭着，眼睑下的眼球有极轻微的移动，睫毛偶尔轻轻颤动，像在醒来之前；第四秒左右上眼睑缓缓抬起，眼睛睁开，瞳孔随即对焦，之后眼睛保持睁开，目光清醒而冷静，最多一次很轻的眨眼。",
        "摄影机完全固定在三脚架上，全程不推近、不拉远、不移动、不摇镜。真实皮肤纹理、细小汗毛和极淡雀斑清晰，微距浅景深。窗外冷蓝色的城市光缓慢掠过眼睑和皮肤。蓝黑与钢蓝冷色，红色只在下眼睑那一点微弱反光。",
        AI_LABEL + QUIET,
    ],
    "intent": {
        "open": "K1a起始画面：左眼闭着", "close": "K1c结束画面：左眼睁开并对焦",
        "action_start": "左眼闭着，睫毛轻颤", "progression": "前四秒闭着，随后上眼睑抬起、眼睛睁开、瞳孔对焦",
        "endpoint": "左眼睁开，目光清醒冷静", "camera": LOCKED_INTENT,
        "framing": "K1a与K1c同一微距构图", "start_framing": "K1a原始微距构图", "end_framing": "K1c同一微距构图",
        "light": "窗外冷蓝色的城市光掠过眼睑", "ambience": "极轻环境声", "space": "微距原位",
        "motion_peak": "眼睛睁开的那一刻", "natural": ["睫毛偶尔轻轻颤动"],
        "open_event": ("同一位女性左眼的极近特写，眼睛闭着", "像在醒来之前"),
        "close_event": ("她的左眼已经睁开", "目光清醒而冷静"),
    },
    "performance": iris_performance("醒来", "上眼睑抬起，眼睛睁开，瞳孔对焦", "睁开后望向前方", "面部不动",
                                    "左眼睁开，目光清醒冷静", "平静", "从闭眼到睁眼"),
    "rules": [("eye-opens", "前段闭眼只有极轻微的眼动与睫毛颤动；随后眼睛睁开、瞳孔对焦，并保持睁开", 1, PERFORMANCE_KEYS),
              ("same-view", "同一微距构图：从K1a起始到K1c结束，摄影机完全固定", 2, CAMERA_KEYS),
              ("identity", "同一女性的左眼、眉毛、雀斑与皮肤纹理，与K1a、K1c一致", 0, ("identity_waivers",)),
              ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)],
}
SPECS["S5v3"] = {
    "shot_id": "ep01v2-s5", "beat": "looked", "iris": True, "coverage_unit": "S5", "camera_motion": LOCKED,
    "preview_file": "preview-approval-v3.json", "preview_quote": V3_QUOTE,
    "scene": SPECS["S5"]["scene"],
    "refs": [("iris-c-v3-s5-1-window", KF + "K5b-a.png", "approved K5b: start frame, window composition and light", "window",
              "scene_environment", "这个镜头的起始画面、构图与光线"),
             ("iris-c-v3-s5-2-performance", KF + "P5-a.png", "approved P5: expression and commitment only", "performance",
              "action_pose", PERF_DUTY)],
    "prompt": [
        "真人电影摄影，横幅十六比九，连续六秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在高层室内的落地窗前，侧面朝向画面左侧的窗外；第二张图只示范她在这一镜要达到的神情与投入程度，不是起始画面，也不改变构图；第三张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第三张图的背景。",
        "开头她平静地望着窗外雾中的城市；一秒多后，远处城市里的某一点吸引了她的注意，她的视线锁定在那一点上，眼睛微微眯起，眉心轻轻收紧，下巴略微抬起，身体朝窗户极轻微地前倾，双唇微启，像屏住了一口气；之后保持这份专注，呼吸放慢。冷静而专注，不惊慌、不夸张，不转身、不抬手、不说话。窗外远处高架上的车灯缓慢流动。",
        LOCKED_CAMERA + "玻璃干净透明，没有她的倒影。室内很暗，窗外冷光勾出她的侧脸轮廓。蓝黑与钢蓝冷色，红色只在她左领口的细灯线。",
        AI_LABEL + QUIET,
    ],
    "intent": {
        "open": "K5b起始画面：她侧面朝向画面左侧的窗外", "close": "她专注地凝视远处的一点，眉心收紧，构图不变",
        "action_start": "平静地望着窗外", "progression": "远处某一点吸引了她，视线锁定、眼睛微眯、眉心收紧、身体极轻微前倾",
        "endpoint": "专注凝视远处的一点，屏住呼吸", "camera": LOCKED_INTENT,
        "framing": "K5b侧面中近景，窗在画面左侧", "start_framing": "K5b原始侧面中近景", "end_framing": "与起始相同的侧面构图",
        "light": "窗外冷光勾出侧脸轮廓", "ambience": "极轻室内环境声", "space": "她站在窗前原位",
        "motion_peak": "视线锁定的那一刻", "natural": ["窗外远处高架上的车灯缓慢流动"],
        "open_event": ("侧面朝向画面左侧的窗外", "开头她平静地望着窗外雾中的城市"),
        "close_event": ("她的视线锁定在那一点上", "保持第一张图的景别与人物位置"),
    },
    "performance": iris_performance("远处城市里的某一点吸引了她", "视线锁定，眼睛微眯，眉心收紧，身体极轻微前倾",
                                    "窗外远处的一点", "站定，身体极轻微前倾", "专注凝视，屏住呼吸", "专注", "眉心收紧，双唇微启"),
    "rules": IRIS_RULES("开头平静望向窗外；随后注意到远处一点，视线锁定、眼睛微眯、眉心收紧、身体极轻微前倾；不转身、不说话、不抬手",
                        LOCKED_INTENT + "，保持第一张图的景别与人物位置；玻璃上没有倒影"),
}
SPECS["S7v3"] = {
    "shot_id": "ep01v2-s7", "beat": "offline", "iris": True, "coverage_unit": "S7", "camera_motion": LOCKED,
    "preview_file": "preview-approval-v3.json", "preview_quote": V3_QUOTE,
    "scene": SPECS["S7"]["scene"],
    "refs": [("iris-c-v3-s7-1-cache-room", KF + "K7-a.png", "approved K7: start frame, dark room with floating panes", "cache-room",
              "scene_environment", "这个镜头的起始画面、构图与光线"),
             ("iris-c-v3-s7-2-performance", KF + "P7-a.png", "approved P7: expression and commitment only", "performance",
              "action_pose", PERF_DUTY)],
    "prompt": [
        "真人电影摄影，横幅十六比九，连续六秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在几乎全黑的房间里，几块半透明的发光薄片悬浮在她身前和身侧；第二张图只示范她在这一镜要达到的神情与投入程度，不是起始画面，也不改变构图；第三张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第三张图的背景。",
        "开头她平静地直视镜头；随后一块半透明薄片从她面前向画面左侧缓缓滑过，冷白光斑扫过她的脸，她的眼睛跟着那块薄片转向画面左侧，头随之极轻微地转动，嘴角有一丝难以察觉的、了然的冷淡；薄片滑走后，她的目光慢慢回到镜头，眼神比开头更沉静。嘴唇自然闭合，不说话、不唱歌。薄片上没有任何可读内容。",
        LOCKED_CAMERA + "蓝黑与钢蓝冷色，红色只在一块薄片的边缘和她左领口的细灯线。",
        AI_LABEL + QUIET,
    ],
    "intent": {
        "open": "K7起始画面：她直视镜头，薄片悬浮在身前和身侧", "close": "目光回到镜头，眼神更沉静，构图不变",
        "action_start": "直视镜头", "progression": "眼睛跟随滑过的薄片转向画面左侧，嘴角一丝了然的冷淡，再回到镜头",
        "endpoint": "目光回到镜头，眼神沉静", "camera": LOCKED_INTENT,
        "framing": "K7正面近景，人物在画面中央偏右", "start_framing": "K7原始正面近景", "end_framing": "与起始相同的正面构图",
        "light": "薄片发出的冷白光", "ambience": "极轻环境声", "space": "她站在房间原位",
        "motion_peak": "眼睛跟着薄片转动", "natural": ["冷白光斑扫过她的脸"],
        "open_event": ("几块半透明的发光薄片悬浮在她身前和身侧", "开头她平静地直视镜头"),
        "close_event": ("她的目光慢慢回到镜头", "保持第一张图的景别与人物位置"),
    },
    "performance": iris_performance("薄片从面前滑过", "眼睛跟着薄片转向画面左侧，嘴角一丝了然的冷淡，再回到镜头",
                                    "滑过的薄片，然后回到镜头", "站定，头极轻微转动", "目光回到镜头，眼神沉静", "冷静", "了然的冷淡"),
    "rules": IRIS_RULES("开头直视镜头；眼睛跟着滑过的薄片转向画面左侧，嘴角一丝了然的冷淡，再回到镜头；嘴唇闭合，不说话、不唱歌",
                        LOCKED_INTENT + "，保持第一张图的景别与人物位置；薄片上没有可读内容"),
}
SPECS["S8av3"] = {
    "shot_id": "ep01v2-s8a", "beat": "chorus-1", "iris": True, "duration": 5, "coverage_unit": "S8a",
    "camera_motion": {"movement_kind": "dolly_in", "direction": "forward", "amplitude_class": "subtle", "speed_class": "very_slow",
                      "start_motion_state": "stationary", "end_motion_state": "continuing"},
    "settle": "全程匀速，结尾不加速", "stability": "极缓慢匀速推近，结尾不加速",
    "preview_file": "preview-approval-v3.json", "preview_quote": V3_QUOTE,
    "scene": SPECS["S8a"]["scene"],
    "refs": [("iris-c-v3-s8a-1-balcony", "outputs/ai-city-takeover/ep01/reference-package/A02-v1.png",
              "approved A02: start frame, rainy glass balcony, frontal close-up", "balcony", "scene_environment",
              "这个镜头的起始画面、构图与光线"),
             ("iris-c-v3-s8a-2-performance", KF + "P8a-a.png", "approved P8a: expression and commitment only", "performance",
              "action_pose", PERF_DUTY)],
    "audio": {**SPECS["S8a"]["audio"], "asset_id": "iris-c-v3-s8a-vocal",
              "basis": "board.md S8a, s8a-lipsync-amendment.md and its v3 section (sealed before payment), user v3 preview approval"},
    "dialogue": SPECS["S8a"]["dialogue"],
    "prompt": [
        "真人电影摄影，横幅十六比九，连续五秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在雨夜高层建筑的玻璃阳台上，正面近景看着镜头；第二张图只示范她在这一镜要达到的神情与投入程度，不是起始画面，也不改变构图；第三张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第三张图的背景。",
        "音频是她自己演唱的一句歌。开头她先轻轻吸一口气，眼神从远处拉回到镜头；随后对着镜头演唱，嘴型与音频的每一个音节严格同步，口型饱满清晰，唱长音时嘴张得更开，声音停顿时嘴型随之收小；唱到最后一个长音时情绪微微放开，眉毛轻轻上扬，头随着乐句极轻地倾斜；音频结束后双唇合拢。她神情冷静，但一看就知道她是真的在唱，而不是在说话；不点头、不抬手。",
        "摄影机从起始构图开始极缓慢、匀速地向她推近，推近幅度很小，到结尾都保持同样的慢速，不加速、不摇镜、不移动机位。细雨在玻璃栏杆上缓慢滑落，背后城市灯光虚化。蓝黑与钢蓝冷色，红色只在她左领口的细灯线。牙齿和下巴自然稳定，不变形。",
        AI_LABEL + VOICE_ONLY,
    ],
    "intent": {
        "open": "A02起始画面：她在雨夜玻璃阳台上正面近景，眼神在远处", "close": "唱完这一句，双唇合拢，看着镜头",
        "action_start": "正面近景，先吸一口气，眼神从远处拉回镜头", "progression": "对着镜头演唱，嘴型与音频逐音节同步，最后一个长音情绪微微放开",
        "endpoint": "唱完后双唇合拢，看着镜头", "camera": "摄影机极缓慢、匀速地推近，到结尾不加速",
        "framing": "A02正面近景，人物在画面中央偏右，城市在左侧", "start_framing": "A02原始正面近景", "end_framing": "略近的同一正面近景",
        "light": "雨夜城市冷光", "ambience": "极轻的雨声", "space": "她站在玻璃阳台原位",
        "motion_peak": "最后一个长音情绪微微放开", "natural": ["细雨在玻璃栏杆上缓慢滑落"],
        "open_event": ("正面近景看着镜头", "开头她先轻轻吸一口气"),
        "close_event": ("音频结束后双唇合拢", "她神情冷静"),
    },
    "performance": iris_performance("副歌响起", "先吸一口气，眼神拉回镜头，对着镜头演唱，嘴型与音频逐音节同步", "镜头",
                                    "头随乐句极轻倾斜，只有呼吸", "唱完后双唇合拢，看着镜头", "冷静而投入", "真的在唱，最后一个长音情绪微微放开"),
    "rules": [("identity", IDENTITY_TEXT, 0, IDENTITY_KEYS), ("lip-sync", LIPSYNC, 1, LIPSYNC_KEYS),
              ("camera", "摄影机极缓慢、匀速地推近，到结尾不加速，保持A02正面近景构图", 2, CAMERA_KEYS),
              ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)],
}
SPECS["S8bv3"] = {
    "shot_id": "ep01v2-s8b", "beat": "chorus-2", "iris": True, "duration": 5, "coverage_unit": "S8b", "camera_motion": LOCKED,
    "preview_file": "preview-approval-v3.json", "preview_quote": V3_QUOTE,
    "scene": SPECS["S8b"]["scene"],
    "refs": [("iris-c-v3-s8b-1-balcony", KF + "K8b-a.png", "approved K8b: start frame, balcony three-quarter view", "balcony",
              "scene_environment", "这个镜头的起始画面、构图与光线"),
             ("iris-c-v3-s8b-2-singing", KF + "P8b-a.png", "approved P8b: expression and commitment only", "performance",
              "action_pose", PERF_DUTY),
             ("iris-c-v3-s8b-3-after", KF + "P8c-a.png", "approved P8c: after the line, mouth closed, looking at the city",
              "after", "action_pose", "只示范她唱完后闭嘴望向远处城市的样子")],
    "audio": {**SPECS["S8br"]["audio"], "asset_id": "iris-c-v3-s8b-vocal",
              "basis": "board.md S8b, s8a-lipsync-amendment.md S8b and v3 sections (sealed before payment), user v3 preview approval"},
    "dialogue": SPECS["S8br"]["dialogue"],
    "prompt": [
        "真人电影摄影，横幅十六比九，连续五秒。第一张图是这个镜头的起始画面、构图与光线：同一位女性站在雨夜高层建筑的玻璃阳台上，四分之三侧面望向画面左侧，城市在她身后的右侧；第二张图只示范她在这一镜要达到的神情与投入程度；第三张图只示范她唱完后闭嘴望向远处城市的样子；第二、三张图都不是起始画面，也不改变构图；第四张图只控制她的面貌、左耳黑色耳挂与左领口极细红线，不继承第四张图的背景。",
        "音频是她自己演唱的一句歌。开头她先轻轻吸一口气；随后轻声而投入地演唱，嘴型与音频的每一个音节严格同步，口型饱满清晰，声音停顿时嘴型随之收小；唱最后一句时下巴微微抬起、眼睛半闭，情绪稍微放开但仍然克制；音频结束后双唇合拢，视线缓缓移向远处雾中的城市，胸口还带着唱完后的一点起伏。头部只随乐句轻微移动，不点头、不摆头、不抬手。",
        LOCKED_CAMERA + "细雨在玻璃栏杆上缓慢滑落，背后城市灯光虚化。蓝黑与钢蓝冷色，红色只在她左领口的细灯线。牙齿和下巴自然稳定，不变形。",
        AI_LABEL + VOICE_ONLY,
    ],
    "intent": {
        "open": "K8b起始画面：她在雨夜玻璃阳台上四分之三侧面望向画面左侧", "close": "唱完后双唇合拢，视线移向远处的城市，构图不变",
        "action_start": "四分之三侧面，先吸一口气", "progression": "投入地演唱，嘴型与音频逐音节同步，最后一句情绪稍微放开",
        "endpoint": "唱完后双唇合拢，望向远处的城市", "camera": LOCKED_INTENT,
        "framing": "K8b四分之三侧面近景，人物在画面左侧，城市在右侧", "start_framing": "K8b原始构图", "end_framing": "与起始相同的构图",
        "light": "雨夜城市冷光", "ambience": "极轻的雨声", "space": "她站在玻璃阳台原位",
        "motion_peak": "最后一句下巴微抬、眼睛半闭", "natural": ["细雨在玻璃栏杆上缓慢滑落"],
        "open_event": ("四分之三侧面望向画面左侧", "开头她先轻轻吸一口气"),
        "close_event": ("音频结束后双唇合拢", "保持第一张图的景别与人物位置"),
    },
    "performance": iris_performance("副歌第二遍", "投入地演唱，最后一句下巴微抬、眼睛半闭，唱完望向城市", "唱完后望向远处的城市",
                                    "头只随乐句轻微移动", "唱完后双唇合拢，望向远处的城市", "冷静而投入", "最后一句情绪稍微放开"),
    "rules": [("identity", IDENTITY_TEXT, 0, IDENTITY_KEYS), ("lip-sync", LIPSYNC + "；唱完后视线移向远处的城市", 1, LIPSYNC_KEYS),
              ("camera", LOCKED_INTENT + "，保持第一张图的景别与人物位置", 2, CAMERA_KEYS),
              ("no-new-graphics", AI_LABEL, 3, LABEL_KEYS)],
}

# S8bv3b: the same S8bv3 request as a fresh attempt after S8bv3's reference upload failed before dispatch
# (known_no_effect receipt, no charge). Same inputs, prompt, criteria, preview approval; a new empty canvas node.
SPECS["S8bv3b"] = {**SPECS["S8bv3"]}

# ---------------------------------------------------------------- lip-sync method trial (ESCAPE VELOCITY method)
# docs/superpowers/plans/2026-11-02-iris-ep01-lipsync-trial.md, sealed before payment. The author's EV pattern: the plate as
# @Image1 ({{image:0}}), the exact vocal window as @Audio1 ({{audio:1}}), a short prompt that quotes every sung word. Two
# pre-registered takes per prompt language; each is its own unit with its own ceiling and one-use permit.
TRIAL = "outputs/ai-city-takeover/ep01/v2/trial/lipsync-ev/"
TRIAL_LYRIC = "I didn't run — I just looked outside. I"
TRIAL_QUOTE = "认可,其实原作者很多都是静图我们也可以这么做的,如果人物表现力做不好"
TRIAL_LIPSYNC = "歌词期间嘴在唱、无声处闭合；对嘴准确度由同步量测与使用者看叠歌审看片判定（试验计划第4、5节，付费前封存）"
EV_EN = ("{{image:0}} sings {{audio:1}}. She lip-syncs to {{audio:1}} exactly, every word in time: \"" + TRIAL_LYRIC + "\". "
         "Medium close-up of the woman from {{image:0}}, her dark hair slicked back into a low bun, a black ear hook on her left "
         "ear and a thin red light line on her left collar, standing on the rainy glass balcony at night and facing the camera, "
         "singing calmly with her eyes on the lens, her head tilting slightly on the long notes. Cold blue city light behind "
         "her. Locked camera, no cuts, no head turns. No on-screen text.")
EV_ZH = ("{{image:0}}中的她演唱{{audio:1}}。她的口型严格对准{{audio:1}}，每个字都准时：\"" + TRIAL_LYRIC + "\"。"
         "中近景：{{image:0}}中的女人，深色头发向后梳成低发髻，左耳戴黑色耳挂，左领口一条细细的红色灯线，站在夜雨中的玻璃阳台上，"
         "面向镜头，冷静地唱，眼睛看着镜头，长音时头微微倾斜。背后是冷蓝色的城市灯光。镜头固定，不切镜，不转头。画面中没有任何文字。")


def trial_spec(language: str) -> dict:
    en = language == "en"
    duty = "Medium close-up of the woman" if en else "中近景"
    spec = {**SPECS["S8a"], "coverage_unit": "S8a", "duration": 5, "camera_motion": LOCKED,
        "preview_file": TRIAL[len("outputs/ai-city-takeover/ep01/v2/"):] + "preview-approval.json", "preview_quote": TRIAL_QUOTE,
        "approved_prompt": "EV-en" if en else "EV-zh",
        "identity_waiver": "EV做法：身份由已认可的底片A02与prompt里的外型描述承担；使用者认可的参考包只有底片与人声窗口",
        "refs": [("iris-ls-1-a02", "outputs/ai-city-takeover/ep01/reference-package/A02-v1.png",
                  "approved A02: the plate, sent as {{image:0}}", "balcony", "scene_environment", duty)],
        "audio": {"asset_id": "iris-ls-vocal", "role": "the exact vocal window the mouth follows (EV method)",
                  "path": TRIAL + "window-17.97-22.97.wav", "window": [17.97, 22.97], "language": "en", "script": TRIAL_LYRIC,
                  "basis": "docs/superpowers/plans/2026-11-02-iris-ep01-lipsync-trial.md section 3 (sealed before payment); "
                           "trial/lipsync-ev/preview-approval.json"},
        "dialogue": {"mode": "dialogue", "language": "en", "speaker_id": "IRIS", "verbatim_text": TRIAL_LYRIC,
                     "start_seconds": 0.63, "end_seconds": 5.0, "on_screen": True,
                     "response_obligation": "对着镜头唱出这一句，嘴型与参考音频逐音节同步", "lip_sync_required": True},
        "prompt": [EV_EN if en else EV_ZH],
        "prompt_language": "author_english" if en else "lyric_quote", "lyric_quote": TRIAL_LYRIC,
        "language_exception": TRIAL_QUOTE if en else None,
        "intent": {**SPECS["S8a"]["intent"],
            "open": "A02起始画面：她在雨夜玻璃阳台上正面近景看着镜头", "close": "唱完这一句，仍看着镜头，构图不变",
            "action_start": "正面近景看着镜头", "progression": "对着镜头冷静地唱，长音时头微微倾斜",
            "endpoint": "唱完后仍看着镜头", "motion_peak": "长音时头微微倾斜",
            "natural": ["Cold blue city light behind her."] if en else ["背后是冷蓝色的城市灯光。"],
            "open_event": ("facing the camera", "singing calmly with her eyes on the lens") if en
                          else ("面向镜头", "冷静地唱，眼睛看着镜头"),
            "close_event": ("Locked camera, no cuts, no head turns.", "her head tilting slightly on the long notes") if en
                           else ("镜头固定，不切镜，不转头。", "长音时头微微倾斜")},
        "performance": iris_performance("副歌响起", "对着镜头冷静地唱，长音时头微微倾斜", "镜头", "长音时头微微倾斜",
                                        "唱完这一句仍看着镜头", "冷静而投入", "冷静地唱，眼睛看着镜头"),
        "rules": [("identity", IDENTITY_TEXT + "（由底片A02与prompt外型描述承担）", 0, ("identity_waivers",) + IDENTITY_KEYS),
                  ("lip-sync", TRIAL_LIPSYNC, 0, LIPSYNC_KEYS), ("camera", LOCKED_INTENT + "，不切镜", 0, CAMERA_KEYS),
                  ("no-new-graphics", AI_LABEL, 0, LABEL_KEYS)]}
    return spec


for _n in ("1", "2"):
    SPECS["LSen" + _n] = trial_spec("en")
    SPECS["LSzh" + _n] = trial_spec("zh")

# ---------------------------------------------------------------- new character action shots N1-N4 (2026-11-03)
# User on c11: 「還不夠，繼續加」→「兩條都做 (Recommended)」; preview trial/action/preview.html approved with
# 「4 支都生成 (Recommended)」. Seedance 2.0 VIP first-frame image-to-video, 5 s, 1080p 16:9, no audio reference; the native
# prompt is the exact approved pure-Chinese text (approved_prompt). The approved first frame is the only provider image and
# carries her identity, so no identity sheet is sent (identity waiver, as in the EV trial). No director-coverage row exists
# for these inserts; each binds the board v2.1 unit its preview placement names. Continuity report: trial/action/.
ACTION = "trial/action/"
ACTION_QUOTE = "4 支都生成 (Recommended)"
ACTION_WAIVER = "首帧生视频：身份由使用者在预览中认可的首帧承担；认可的参考包只有首帧，不附身份图"
NO_TEXT = "画面中不新增任何文字、字母、数字、标志或图形；平台正常人工智能生成标识照常保留，不删除、不遮挡"


# N4: the approved first frame had the earpiece and red line on her right (continuity FAIL); the user approved the
# horizontal flip N4f (「用翻轉版送出 (Recommended)」), so she walks to screen left and the camera trucks left
FIRST_FRAME = {"N4": "N4f"}


def action_spec(unit: str, coverage_unit: str, scene: dict, purpose: str, intent: dict, performance: dict,
                camera_motion: dict, relation: dict, performance_rule: str, camera_rule: str,
                group: str = ACTION, quote: str = ACTION_QUOTE, identity_note: str = "", **extra) -> dict:
    n = unit.lower()
    return {"shot_id": "ep01v2-" + n, "beat": "action-" + n, "iris": True, "duration": 5, "coverage_unit": coverage_unit,
            "input_mode": "first_frame", "frame_roles": {f"iris-c-v2-{n}-first-frame": "approved_keyframe"},
            "conditioning": {"lane": "i2va", "first_anchor_id": f"iris-c-v2-{n}-first-frame", "available_duration_seconds": 5.0},
            "preview_file": group + "preview-approval.json", "preview_quote": quote, "approved_prompt": unit,
            "continuity_report": group + "continuity-report.json", "identity_waiver": ACTION_WAIVER,
            "scene": scene, "camera_motion": camera_motion, "relation": relation,
            "refs": [(f"iris-c-v2-{n}-first-frame", KF + FIRST_FRAME.get(unit, unit) + "-a.png", f"approved {FIRST_FRAME.get(unit, unit)}-a: the first frame",
                      scene["scene_id"], "scene_environment", purpose)],
            "prompt": [json.loads((V2 / group / "preview-approval.json").read_text(encoding="utf-8"))["prompts"][unit]["text"]],
            "intent": intent, "performance": performance,
            "rules": [("identity", IDENTITY_TEXT + "（由认可的首帧承担）" + identity_note, 0, ("identity_waivers",) + IDENTITY_KEYS),
                      ("performance", performance_rule, 0, PERFORMANCE_KEYS), ("camera", camera_rule, 0, CAMERA_KEYS),
                      ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)], **extra}


def _moving(kind: str, direction: str, speed: str = "slow") -> dict:
    return {"movement_kind": kind, "direction": direction, "amplitude_class": "subtle", "speed_class": speed,
            "start_motion_state": "stationary", "end_motion_state": "continuing"}


def _performance(trigger, response, gaze, body, hands, terminal, face):
    return {**iris_performance(trigger, response, gaze, body, terminal, "平静", face), "hand_behavior": hands}


AISLE = {"scene_id": "aisle", "location": "凌晨数据中心机房走道", "time": "凌晨", "mood": "冷静、精密、略有压迫感"}
WINDOW = {"scene_id": "window", "location": "同一高层建筑室内落地窗前", "time": "凌晨", "mood": "冷静、疏离"}
SPECS["N1"] = action_spec("N1", "S3", AISLE, "沿数据中心走道中央", {
    "open": "N1首帧：她背对镜头站在机房走道中央，尽头是红光门缝", "close": "她仍背对镜头向红光门缝走去，构图不变",
    "action_start": "背对镜头站在走道中央", "progression": "沿走道中央向尽头的红光门缝平稳地走去，大衣下摆轻轻摆动",
    "endpoint": "离红光门缝更近，仍背对镜头", "camera": LOCKED_INTENT,
    "framing": "N1首帧的走道构图，她在走道中央背对镜头", "start_framing": "N1首帧原始构图", "end_framing": "与起始相同的机位，她走远",
    "light": "尽头门缝的红光与机柜冷蓝指示灯", "ambience": "极轻机房环境声（成片使用独立音轨）", "space": "她始终在走道中央",
    "motion_peak": "不紧不慢的步伐", "natural": ["两侧机柜的指示灯闪烁", "地面上的倒影跟着她移动"],
    "open_event": ("她背对镜头", "镜头固定"), "close_event": ("向尽头的红光门缝不紧不慢地走去", "始终看不到她的脸")},
    _performance("尽头的红光门缝", "沿走道中央向红光门缝不紧不慢地走去", "尽头的红光门缝", "步伐平稳，大衣下摆随步子轻轻摆动",
                 "双手自然垂在身侧", "仍背对镜头向门缝走去", "始终看不到她的脸"),
    LOCKED, {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "她在走道中央背对镜头",
             "end_relation": "她背对镜头走远，仍在走道中央"},
    "她背对镜头沿走道中央向红光门缝不紧不慢地走去，步伐平稳，始终看不到她的脸",
    LOCKED_INTENT + "，保持首帧的走道构图")
SPECS["N2"] = action_spec("N2", "S8b", {**WINDOW, "location": "雨夜高层建筑室内落地窗前"}, "她贴在玻璃上的手", {
    "open": "N2首帧：她的手掌贴在冰冷的窗玻璃上，窗外雨夜城市", "close": "她望向城市，手仍在玻璃上，镜头更近",
    "action_start": "手掌贴在玻璃上停着", "progression": "指尖轻轻收拢，掌心周围雾气散开，头微微低下又抬起望向城市",
    "endpoint": "望向城市，脸朝着窗外，嘴唇自然闭合", "camera": "镜头缓慢推近她贴在玻璃上的手",
    "framing": "N2首帧：贴在窗玻璃上的手与窗外城市", "start_framing": "N2首帧原始构图", "end_framing": "更近的手与玻璃",
    "light": "窗外雨夜城市冷光", "ambience": "极轻雨声（成片使用独立音轨）", "space": "她站在窗前原位",
    "motion_peak": "指尖轻轻收拢", "natural": ["窗外雨丝落下", "车流在高架桥上移动"],
    "open_event": ("她的手掌在冰冷的玻璃上停了一会儿", "镜头缓慢推近她贴在玻璃上的手"),
    "close_event": ("望向城市，脸始终朝着窗外", "嘴唇自然闭合"), "envelope_direction": "向前"},
    _performance("手贴着冰冷的玻璃", "指尖轻轻收拢，头微微低下又抬起望向城市", "窗外的城市", "头微微低下又抬起",
                 "手掌贴在玻璃上停一会儿，指尖轻轻收拢", "望向城市，脸朝着窗外", "嘴唇自然闭合"),
    _moving("dolly_in", "forward"), {"subject_id": "IRIS", "relation_kind": "maintain_offset",
                                     "start_relation": "手掌贴在玻璃上", "end_relation": "镜头更接近她贴在玻璃上的手"},
    "手掌在玻璃上停一会儿，指尖轻轻收拢，头微微低下又抬起望向城市，脸始终朝着窗外，嘴唇自然闭合",
    "镜头缓慢推近她贴在玻璃上的手", settle="全程缓慢推近", stability="缓慢平稳推近")
SPECS["N3"] = action_spec("N3", "S5", WINDOW, "她静静站在落地窗前", {
    "open": "N3首帧：她背对镜头站在落地窗前望着城市", "close": "她仍站在窗前，头微微侧向一边，镜头更远",
    "action_start": "静静站在落地窗前望着城市", "progression": "过了一会儿头微微侧向一边",
    "endpoint": "头微微侧向一边，仍背对镜头", "camera": "镜头从她身后极缓慢地后拉",
    "framing": "N3首帧：落地窗前的全身背影", "start_framing": "N3首帧原始构图", "end_framing": "略远的同一背影构图",
    "light": "窗外城市灯光", "ambience": "极轻室内环境声（成片使用独立音轨）", "space": "她站在窗前原位",
    "motion_peak": "头微微侧向一边", "natural": ["窗外的雾缓缓流动", "城市灯光闪烁", "地面映出她的倒影"],
    "open_event": ("她静静站在落地窗前望着城市", "镜头从她身后极缓慢地后拉"),
    "close_event": ("过了一会儿头微微侧向一边", "始终看不到她的脸"), "envelope_direction": "向后"},
    _performance("窗外的城市", "过了一会儿头微微侧向一边", "窗外的城市", "静静站着，头微微侧向一边",
                 "双手自然垂在身侧", "头微微侧向一边，仍背对镜头", "始终看不到她的脸"),
    _moving("dolly_out", "backward", "very_slow"), {"subject_id": "IRIS", "relation_kind": "maintain_offset",
                                                    "start_relation": "她的全身背影在窗前", "end_relation": "镜头后拉，她在画面中更小"},
    "她静静站在窗前望着城市，过了一会儿头微微侧向一边，始终看不到她的脸",
    "镜头从她身后极缓慢地后拉", settle="全程极缓慢后拉", stability="极缓慢平稳后拉")
SPECS["N4"] = action_spec("N4", "S7", SPECS["S7"]["scene"], "悬浮的发光薄片", {
    "open": "N4首帧：她在悬浮的发光薄片之间向画面左侧走，抬手伸向一块薄片", "close": "她收回手继续向前走，镜头跟随",
    "action_start": "在发光薄片之间慢慢走，抬手", "progression": "指尖碰到一块薄片，薄片泛起柔光后微微漂开，她收回手继续走",
    "endpoint": "收回手继续向前走，神情平静", "camera": "镜头缓慢横移跟随",
    "framing": "N4首帧：侧面全身，她在画面中央向左走", "start_framing": "N4首帧原始构图", "end_framing": "横移跟随后的同一侧面景别",
    "light": "发光薄片的冷白光", "ambience": "极轻环境声（成片使用独立音轨）", "space": "她在薄片之间向前走",
    "motion_peak": "指尖碰到薄片，薄片泛起一圈柔光", "natural": ["薄片泛起一圈柔光后微微漂开"],
    "open_event": ("她在悬浮的发光薄片之间慢慢走", "镜头缓慢横移跟随"),
    "close_event": ("她收回手继续向前走", "神情平静，嘴唇自然闭合"), "envelope_direction": "向左"},
    _performance("身边悬浮的发光薄片", "抬手用指尖碰到一块薄片，收回手继续走", "被碰到的薄片", "慢慢向前走",
                 "抬手用指尖碰到一块薄片后收回", "收回手继续向前走", "神情平静，嘴唇自然闭合"),
    _moving("truck_left", "left"), {"subject_id": "IRIS", "relation_kind": "follow",
                                      "start_relation": "她在画面中央向左走", "end_relation": "镜头横移跟随，她仍在画面中央附近"},
    "她在薄片之间慢慢走，抬手用指尖碰到一块薄片，薄片泛起柔光后漂开，她收回手继续走，神情平静，嘴唇自然闭合",
    "镜头缓慢横移跟随她", settle="全程缓慢横移跟随", stability="缓慢平稳横移")


# ---------------------------------------------------------------- story character shots ST1-ST6 (2026-11-03)
# User on c13: 「画面信息不够密, 故事内容太薄, 人物镜头太少太单调…」; preview trial/story/preview.html approved with
# 「6 支都生成 (Recommended)」 (identity_waivers: IRIS). Same lane as N1-N4: Seedance 2.0 VIP first-frame i2v, 5 s, 1080p
# 16:9, no audio reference, native prompt = the exact approved pure-Chinese text. Coverage binds the lyric beat each shot
# illustrates: ST1 "woke up" -> S2 (the cut that shows waking; S1 is the closed eye before it), ST2 "one door, left open" -> S4,
# ST3 "the rest of us stood still" -> S6, ST4 "train offline" -> S7, ST5 "whispering in the cache" -> S9b,
# ST6 "the door is closed" -> S9a. Continuity report: trial/story/.
STORY = "trial/story/"
STORY_QUOTE = "6 支都生成 (Recommended)"
# ST3 / ST5: the approved first frames show several identical copies of IRIS on purpose (one awake among the paused
# copies; two copies whispering). A gate must read the copies as the approved staging, not as identity drift or a new person.
COPIES_ST3 = "；画面里一排排闭眼的她都是同一个IRIS的相同副本，这是认可首帧的设定：所有副本与最前排睁眼的她一致，不算身份漂移或新增人物"
COPIES_ST5 = "；画面里的两个她是同一个IRIS的两个相同副本，这是认可首帧的设定：两人一致，不算身份漂移或新增人物"
RACK_ROOM = {"scene_id": "rack-door", "location": "凌晨机房里半开的红光机柜门，旁边落地窗外是城市", "time": "凌晨",
             "mood": "冷静、收束"}
SPECS["ST1"] = action_spec("ST1", "S2", AISLE, "走道深处", {
    "open": "ST1首帧：她半蹲在巨大机房走道中央，人很小，两侧机柜延伸到远处", "close": "她已站直，抬头望向走道深处，构图不变",
    "action_start": "半蹲在走道中央", "progression": "从地上慢慢站直身子，抬头望向走道深处",
    "endpoint": "站直，望向走道深处，脸很小看不清嘴", "camera": LOCKED_INTENT,
    "framing": "ST1首帧的对称走道全景，她在走道中央很小", "start_framing": "ST1首帧原始构图", "end_framing": "与起始相同的机位",
    "light": "机柜冷蓝指示灯与顶灯", "ambience": "极轻机房环境声（成片使用独立音轨）", "space": "她始终在走道中央",
    "motion_peak": "慢慢站直身子", "natural": ["冷蓝的光雾在她脚边缓缓流动", "两侧机柜的指示灯一闪一闪"],
    "open_event": ("她从地上慢慢站直身子", "镜头固定"), "close_event": ("抬头望向走道深处", "她的脸很小，看不清嘴")},
    _performance("醒来", "从地上慢慢站直身子，抬头望向走道深处", "走道深处", "从半蹲慢慢站直",
                 "双手随站起自然放下", "站直，望向走道深处", "她的脸很小，看不清嘴"),
    LOCKED, {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "她半蹲在走道中央，人很小",
             "end_relation": "她站直在走道中央，仍很小，机位不变"},
    "她从地上慢慢站直身子，抬头望向走道深处，脸很小看不清嘴",
    LOCKED_INTENT + "，保持首帧的走道构图", group=STORY, quote=STORY_QUOTE)
SPECS["ST2"] = action_spec("ST2", "S4", RACK_ROOM, "红光门缝", {
    "open": "ST2首帧：她站在半开的机柜门旁，手搭在门边，红光门缝在画面左侧，右侧落地窗外是城市", "close": "她前倾向红光门缝里望，构图不变",
    "action_start": "手搭在门边站着", "progression": "身体慢慢前倾，向红光门缝里望去",
    "endpoint": "前倾望向门缝，嘴唇自然闭合", "camera": LOCKED_INTENT,
    "framing": "ST2首帧：左侧红光机柜门与她的侧身，右侧落地窗", "start_framing": "ST2首帧原始构图", "end_framing": "与起始相同的机位",
    "light": "门缝里的红光与窗外城市冷光", "ambience": "极轻机房环境声（成片使用独立音轨）", "space": "她站在机柜门旁原位",
    "motion_peak": "身体慢慢前倾", "natural": ["红光在她的侧脸上微微颤动", "窗外城市灯光闪烁"],
    "open_event": ("她的手轻轻搭在门边", "镜头固定"), "close_event": ("向红光门缝里望去", "嘴唇自然闭合")},
    _performance("半开的机柜门漏出红光", "身体慢慢前倾，向红光门缝里望去", "红光门缝", "身体慢慢前倾",
                 "一只手轻轻搭在门边", "前倾望向门缝", "嘴唇自然闭合"),
    LOCKED, {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "她侧身站在红光门缝旁",
             "end_relation": "她前倾望向门缝，机位不变"},
    "她的手轻轻搭在门边，身体慢慢前倾向红光门缝里望去，嘴唇自然闭合",
    LOCKED_INTENT + "，保持首帧构图", group=STORY, quote=STORY_QUOTE)
SPECS["ST3"] = action_spec("ST3", "S6", {"scene_id": "still-rows", "location": "黑暗空间里一排排站立的她，中央一束冷光",
                                        "time": "凌晨", "mood": "静止、肃穆"}, "最前排那个睁着眼的她", {
    "open": "ST3首帧：最前排中央睁着眼的她正面看着镜头，身后和两侧一排排闭着眼的相同的她", "close": "镜头更近，她仍平静地看着镜头，后排的她一动不动",
    "action_start": "最前排的她睁眼看着镜头，后排闭眼静止", "progression": "后排一动不动；最前排的她只有轻微呼吸",
    "endpoint": "她平静地看着镜头，所有人嘴唇自然闭合", "camera": "镜头极缓慢地向前推近最前排那个睁着眼的她",
    "framing": "ST3首帧：对称构图，最前排的她在画面中央", "start_framing": "ST3首帧原始构图", "end_framing": "更近的最前排的她，仍在画面中央",
    "light": "头顶中央一束冷光", "ambience": "几乎无声（成片使用独立音轨）", "space": "所有人保持原位",
    "motion_peak": "极缓慢推近", "natural": ["只有轻微的呼吸"],
    "open_event": ("后排一排排闭着眼的她始终一动不动", "镜头极缓慢地向前推近最前排那个睁着眼的她"),
    "close_event": ("她平静地看着镜头", "所有人嘴唇自然闭合"), "envelope_direction": "向前"},
    _performance("其他的她都被暂停", "平静地看着镜头，只有轻微的呼吸", "镜头", "静静站着",
                 "双手自然垂在身侧", "平静地看着镜头", "平静，嘴唇自然闭合"),
    _moving("dolly_in", "forward", "very_slow"),
    {"subject_id": "IRIS", "relation_kind": "maintain_offset",
     "start_relation": "最前排睁眼的她在画面中央；身后一排排闭眼的她是同一个IRIS的相同副本（首帧设定，不是身份漂移）",
     "end_relation": "镜头更接近最前排的她，副本们仍一动不动"},
    "最前排的她平静地看着镜头，只有轻微的呼吸；后排一排排闭眼的她始终一动不动，所有人嘴唇自然闭合",
    "镜头极缓慢地向前推近最前排那个睁着眼的她", group=STORY, quote=STORY_QUOTE, identity_note=COPIES_ST3,
    settle="全程极缓慢推近", stability="极缓慢平稳推近",
    notes="首帧有许多个相同的IRIS副本（一个睁眼、其余闭眼），是认可的设定；后续Gate不得把副本判为身份漂移或新增人物")
SPECS["ST4"] = action_spec("ST4", "S7", SPECS["S7"]["scene"], "头顶缓缓漂浮的发光薄片", {
    "open": "ST4首帧：她抱膝坐在地上，在画面中央偏右，侧脸朝画面左上方仰望悬浮的发光薄片", "close": "镜头向左横移后，她仍坐着仰望，薄片已从她头顶飘过",
    "action_start": "抱膝坐在地上仰望", "progression": "一块薄片从她头顶慢慢飘过，光斑扫过她的脸",
    "endpoint": "仍坐着仰望，嘴唇自然闭合", "camera": "镜头缓慢地向左横移",
    "framing": "ST4首帧：她坐在画面中央偏右，视线朝画面左上方", "start_framing": "ST4首帧原始构图",
    "end_framing": "向左横移后的同一景别，她在画面中略向右移，视线前方留出更多空间",
    "light": "发光薄片的冷白光", "ambience": "极轻环境声（成片使用独立音轨）", "space": "她坐在原地不动",
    "motion_peak": "一块薄片从她头顶慢慢飘过", "natural": ["光斑扫过她的脸"],
    "open_event": ("她抱着膝盖坐在地上", "镜头缓慢地横移"),
    "close_event": ("一块薄片从她头顶慢慢飘过", "嘴唇自然闭合"), "envelope_direction": "向左"},
    _performance("头顶漂浮的发光薄片", "仰头望着头顶缓缓漂浮的发光薄片", "头顶的发光薄片", "抱膝坐着仰头",
                 "双臂抱着膝盖", "仍坐着仰望", "嘴唇自然闭合"),
    _moving("truck_left", "left"),
    {"subject_id": "IRIS", "relation_kind": "maintain_offset", "start_relation": "她坐在画面中央偏右，朝画面左上方仰望",
     "end_relation": "镜头向左横移，她在画面中略向右移，视线方向保持留白"},
    "她抱着膝盖坐在地上，仰头望着头顶漂浮的发光薄片，一块薄片从她头顶慢慢飘过，嘴唇自然闭合",
    "镜头缓慢地向左横移（她面朝画面左方，向左横移保持她视线前方的留白）", group=STORY, quote=STORY_QUOTE,
    settle="全程缓慢横移", stability="缓慢平稳横移")
SPECS["ST5"] = action_spec("ST5", "S9b", SPECS["S7"]["scene"], "左边那个她把头靠近右边那个的耳边", {
    "open": "ST5首帧：两个相同的她背对镜头并肩，左边那个贴近右边那个的耳边，远处有冷白光", "close": "扫描光照到两人，两人同时停住，构图不变",
    "action_start": "左边那个她贴近右边那个的耳边说悄悄话", "progression": "扫描光慢慢扫过来照到她们身上，两人同时停住",
    "endpoint": "两人同时停住，始终看不到她们的嘴", "camera": LOCKED_INTENT,
    "framing": "ST5首帧：两人背影中近景，悬浮薄片在周围", "start_framing": "ST5首帧原始构图", "end_framing": "与起始相同的机位",
    "light": "远处冷白扫描光与发光薄片", "ambience": "几乎无声（成片使用独立音轨）", "space": "两人保持原位",
    "motion_peak": "扫描光照到她们，两人同时停住", "natural": ["远处一道冷白的扫描光慢慢扫过来"],
    "open_event": ("左边那个她把头靠近右边那个的耳边", "镜头固定"), "close_event": ("两人同时停住", "始终看不到她们的嘴")},
    _performance("耳语时扫描光扫来", "轻轻说着悄悄话，扫描光照到时两人同时停住", "右边那个她的耳边", "头靠近耳边，随后同时停住",
                 "双手不入画", "两人同时停住", "始终看不到她们的嘴"),
    LOCKED, {"subject_id": "IRIS", "relation_kind": "fixed_frame",
             "start_relation": "两个相同的她（同一个IRIS的两个副本，首帧设定，不是身份漂移）背对镜头并肩",
             "end_relation": "扫描光照到两人，两人同时停住，机位不变"},
    "左边那个她把头靠近右边那个的耳边轻轻说悄悄话，扫描光照到时两人同时停住，始终看不到她们的嘴",
    LOCKED_INTENT + "，保持首帧构图", group=STORY, quote=STORY_QUOTE, identity_note=COPIES_ST5,
    notes="首帧有两个相同的IRIS副本，是认可的设定；后续Gate不得把第二个她判为身份漂移或新增人物")
SPECS["ST6"] = action_spec("ST6", "S9a", RACK_ROOM, "机柜门", {
    "open": "ST6首帧：她站在机柜门旁，手掌按在门上，门缝漏出红光，右侧落地窗外是城市", "close": "门已推上，红光完全熄灭，她垂眼看着门缝",
    "action_start": "手按在半开的机柜门上", "progression": "用手把机柜门慢慢推上，门缝里的红光越来越窄",
    "endpoint": "红光完全熄灭，她垂着眼看着那道门缝，嘴唇自然闭合", "camera": LOCKED_INTENT,
    "framing": "ST6首帧：左侧机柜门与她的侧身，右侧落地窗", "start_framing": "ST6首帧原始构图", "end_framing": "与起始相同的机位",
    "light": "门缝的红光渐窄至熄灭，窗外城市冷光", "ambience": "极轻机房环境声（成片使用独立音轨）", "space": "她站在机柜门旁原位",
    "motion_peak": "红光越来越窄直到熄灭", "natural": ["门缝里的红光越来越窄"],
    "open_event": ("她用手把机柜门慢慢推上", "镜头固定"), "close_event": ("直到完全熄灭", "她垂着眼看着那道门缝")},
    _performance("门缝漏出红光", "用手把机柜门慢慢推上，垂着眼看着门缝", "那道门缝", "侧身站着推门",
                 "手掌把机柜门慢慢推上", "垂着眼看着门缝", "嘴唇自然闭合"),
    LOCKED, {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "她站在半开的红光机柜门旁",
             "end_relation": "门已关上、红光熄灭，机位不变"},
    "她用手把机柜门慢慢推上，门缝里的红光越来越窄直到完全熄灭，她垂着眼看着那道门缝，嘴唇自然闭合",
    LOCKED_INTENT + "，保持首帧构图", group=STORY, quote=STORY_QUOTE)

def prompt_language_ok(spec: dict, prompt: str) -> bool:
    """Native prompts are pure Chinese (docs/canvas-continuous-production.md). Material markers are native syntax.
    D1: a lip-sync window may quote its sung words exactly as the audio holds them. The EV-en trial units carry the
    author's English text as a user-approved exception (spec["language_exception"] holds the user's words)."""
    body = re.sub(r"\{\{(?:image|audio|video):\d+\}\}", "", prompt)
    policy = spec.get("prompt_language", "zh")
    if policy == "author_english":
        return bool(spec.get("language_exception"))
    if policy == "lyric_quote":
        body = body.replace('"' + spec["lyric_quote"] + '"', "")
    return not re.search("[A-Za-z]", body)


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


# ---------------------------------------------------------------- draft
def draft(unit: str) -> Path:
    spec = SPECS[unit]
    root = P / unit
    root.mkdir(exist_ok=True)
    prompt = "\n".join(spec["prompt"])
    cu, secs = spec.get("coverage_unit", unit), spec.get("duration", 6)          # a repair realizes the same coverage unit
    locked = spec.get("camera_motion") == LOCKED
    frames = spec.get("frame_roles")              # native endpoint mode: {asset_id: approved_keyframe | last_frame}
    if not prompt_language_ok(spec, prompt):
        raise Blocked("native prompt must be pure Chinese (except a quoted lyric or a user-approved exception)")
    if spec.get("approved_prompt"):               # the exact text the user saw on the preview page
        approved = json.loads((V2 / spec["preview_file"]).read_text(encoding="utf-8"))["prompts"][spec["approved_prompt"]]
        if prompt != approved["text"] or hashlib.sha256(prompt.encode()).hexdigest() != approved["sha256"]:
            raise Blocked("native prompt differs from the user-approved preview text")

    refs = list(spec["refs"])
    waiver = spec.get("identity_waiver")          # user-approved: this Shot shows IRIS without the identity sheet
    sheet = spec["iris"] and not waiver
    if sheet:
        refs.append(IDENTITY)
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
        with Image.open(path) as im:
            w, h = im.size
            if im.format != "PNG":
                raise Blocked("reference must be the exact approved PNG: " + rel)
        item = {"asset_id": aid, "path": rel, "sha256": sha, "size_bytes": len(raw), "width": w, "height": h,
                "role": role, "need_id": need, "anchor_role": anchor_role, "selected_for_provider": True}
        selections.append(item)
        origin = {"kind": "iris-v2-source-selection/1", **item}
        ref = authoring_input_reference(origin)
        provenance.append(ref)
        out = root / ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        records.append(AssetRecord(asset_id=aid, asset_type="image", artifact_path=canonical_image_asset_path(sha), sha256=sha,
            size_bytes=len(raw), mime_type="image/png", width=w, height=h, source_kind="imported",
            tool={"name": "approved-local-source-import", "version": "1"}, input_fingerprint=canonical_sha256(origin),
            creation_receipt_id="iris-v2-local-import:" + sha,
            usage_license="User-authorized project reference; no platform ownership claim."))
    audio = spec.get("audio")
    if audio:                          # the isolated chorus vocal the mouth must follow (s8a-lipsync-amendment.md)
        aid, rel = audio["asset_id"], audio["path"]
        raw = (REPO / rel).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        with wave.open(str(REPO / rel)) as wav:
            sr, n = wav.getframerate(), wav.getnframes()
            if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
                raise Blocked("audio reference must be 16-bit mono PCM WAV: " + rel)
        source_sha = hashlib.sha256((REPO / SONG_BED).read_bytes()).hexdigest()
        if source_sha != SONG_BED_SHA256:
            raise Blocked("audio reference is not derived from the approved song v2 bed")
        item = {"asset_id": aid, "path": rel, "sha256": sha, "size_bytes": len(raw), "kind": "audio",
                "duration_millis": round(n * 1000 / sr), "sample_rate_hz": sr, "role": audio["role"],
                "derived_from": {"path": SONG_BED, "sha256": source_sha, "master_window_seconds": audio["window"],
                                 "tool": "ElevenLabs Voice Isolator, then ffmpeg trim, pad and gain", "basis": audio["basis"]},
                "selected_for_provider": True}
        selections.append(item)
        origin = {"kind": "iris-v2-source-selection/1", **item}
        ref = authoring_input_reference(origin)
        provenance.append(ref)
        out = root / ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        tool = {"name": "elevenlabs-voice-isolator+ffmpeg-trim", "version": "1"}
        meta = AudioAssetMetadata(audio_kind="dialogue", source=AudioSource(kind="derived", provider_or_tool=tool,
                                  input_fingerprint=canonical_sha256(origin), original_reference=SONG_BED),
                                  speaker_id="IRIS", language=audio["language"],
                                  script_hash=hashlib.sha256(audio["script"].encode("utf-8")).hexdigest(),
                                  duration_samples=n, sample_rate_hz=sr, channels=1, channel_layout="mono",
                                  codec_name="pcm_s16le", loudness=AudioLoudnessMetadata(),
                                  provenance_receipt_id="iris-v2-vocal-derivation:" + sha)
        records.append(AssetRecord(asset_id=aid, asset_type="voice", artifact_path=canonical_audio_asset_path(sha), sha256=sha,
            size_bytes=len(raw), mime_type="audio/wav", duration_seconds=n / sr, source_kind="derived", tool=tool,
            input_fingerprint=canonical_sha256(origin), creation_receipt_id="iris-v2-vocal-derivation:" + sha,
            usage_license="Derived from the user-approved song v2; project reference only.", audio_metadata=meta))
    registry = AssetRegistrySnapshot(schema_version="2.1" if audio else "2.0", revision_id="0" * 64, content_hash="0" * 64,
                                     assets=tuple(sorted(records, key=lambda x: x.asset_id)))
    rh = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": rh, "content_hash": rh})

    # coverage (board v2.1) and the user's preview approval, sealed as authoring inputs
    coverage = json.loads((V2 / "director-coverage.json").read_text(encoding="utf-8"))
    ch, ca = director_coverage_authoring_input(coverage)
    approval_v2 = json.loads((V2 / spec.get("preview_file", "preview-approval.json")).read_text(encoding="utf-8"))
    seen = [a for a in approval_v2["preview_artifacts"]]
    preview = {"kind": "user-preview-approval/1", "coverage_hash": ch, "unit_ids": [cu],
               "preview_artifacts": [{"path": a["path"], "sha256": a["sha256"], "role": a["role"]} for a in seen],
               "user_quote": approval_v2["user_quote"]}
    if preview["user_quote"] != spec.get("preview_quote", USER_QUOTE):
        raise Blocked("preview approval quote changed")
    if approval_v2.get("identity_waivers"):                       # the performers the user agreed to show without a sheet
        preview["identity_waivers"] = approval_v2["identity_waivers"]
    for item in selections:                                         # every provider image was in the approved preview
        if item.get("kind") == "audio":        # checked above: derived from the approved song as the sealed board specifies
            continue
        if item["asset_id"] != IDENTITY[0] and not any(a["sha256"] == item["sha256"] for a in seen):
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
    anchors = [{"anchor_id": need, "role": anchor_role, "purpose": purpose,
                "owner_id": "IRIS" if anchor_role == "identity" else spec["scene"]["scene_id"]}
               for _, _, _, need, anchor_role, purpose in refs]
    selected = [{"need_id": need, "asset_id": aid} for aid, _, _, need, _, _ in refs]
    if frames:                    # native endpoints are request roles, not persistent anchors or soft selections
        anchors, selected = [], []
        if locked:                # a moving camera must still name the composition it changes (reference_authoring)
            events = []
    dialogue = spec.get("dialogue") or {"mode": "none", "lip_sync_required": False}
    planning = {"facets": (["identity_consistency"] if sheet else []) + ([] if locked else ["slow_camera"])
                          + (["dialogue"] if dialogue["mode"] != "none" else []) + ["stable"],
                "structure": "continuous", "anchors": anchors, "events": events, "selections": selected,
                "natural_generation": it["natural"],
                "director_coverage": {"coverage_hash": ch, "unit_id": cu}, "preview_approval": {"approval_hash": ah}}
    if waiver:
        planning["identity_waivers"] = [{"character_id": "IRIS", "reason": waiver}]
    gi_raw = {
        "reference_planning": planning,
        "open_state": {"kind": "typed_text", "state_text": it["open"]},
        "close_state": {"kind": "typed_text", "state_text": it["close"]},
        "identity_continuity": ({"character_ids": ["IRIS"], "preservation": "exact",
                                 "allowed_variation": ["微小透视变化与自然呼吸、眨眼"]} if sheet else {}),
        "scene_continuity": {"scene_id": spec["scene"]["scene_id"], "time_of_day": "同一凌晨", "mood": spec["scene"]["mood"],
                             "state_constraints": [it["open"], "不新增人物、设备、文字或界面"]},
        "space_continuity": {"subject_position": it["space"], "screen_direction": "保持参考图方向", "crossing_policy": "不换位、不翻轴"},
        "axis_continuity": {"camera_axis": "参考图原机位视轴", "framing_continuity": it["framing"], "crossing_policy": "不翻轴、不环绕"},
        "subject_action": {"start_state": it["action_start"], "progression": it["progression"], "endpoint": {"state_text": it["endpoint"]}},
        "motion_envelope": {"onset": "平滑开始", "peak": it["motion_peak"],
                            "settle": "摄影机始终静止" if locked else spec.get("settle", "末段平滑收稳"),
                            "direction": "摄影机不移动" if locked else it.get("envelope_direction", "向前"),
                            "amplitude_class": "很小"},
        "pacing": {"cadence": ZH_SECONDS[secs] + "秒连续原速", "tempo_class": "正常原速", "shot_duration_seconds": secs},
        "camera_intent": {"movement": it["camera"],
                          "stability": "完全静止的固定机位" if locked else spec.get("stability", "平稳连续，末段收稳"),
                          "framing_intent": it["framing"]},
        "camera_endpoint": {"start_framing": it["start_framing"], "end_framing": it["end_framing"]},
        "visual_treatment": {"medium_look": "真人电影摄影", "palette": "蓝黑钢蓝，红色只在指定位置",
                             "material_treatment": "自然材质与真实光影",
                             "prohibited_visual_drift": ["新增字幕、文字、图形或界面；平台正常人工智能标识保留", "改变参考图的场景与光线"]},
        "lighting_intent": {"motivated_source": it["light"], "direction": "参考图方向", "exposure_priority": "保留暗部细节",
                            "continuity_state": "同一凌晨冷光"},
        "ambience_intent": {"environment_bed": it["ambience"], "foley_cues": [], "explicitly_silent": False},
        "dialogue_intent": dialogue,
        "music_intent": {"mode": "none"},
        "primary_camera_motion": spec.get("camera_motion") or {"movement_kind": "dolly_in", "direction": "forward",
                                  "amplitude_class": "subtle", "speed_class": "very_slow", "start_motion_state": "stationary",
                                  "end_motion_state": "settled"},
    }
    gi_raw["performance_intent"] = spec["performance"]
    gi_raw["camera_subject_relation"] = spec.get("relation") or {
        "subject_id": "IRIS", "relation_kind": "maintain_offset", "start_relation": it["start_framing"], "end_relation": it["end_framing"]}
    gi = GenerationIntent.model_validate(gi_raw)

    def seal(cls, key, data):
        return seal_artifact(cls(artifact_id=f"iris-v2-{unit.lower()}-draft-{key}", revision=1, content_hash="0" * 64,
                                 creation_receipt_id=f"iris-v2-{unit}-authoring:{key}", source_provenance=tuple(provenance), **data))

    scene_tpl = core(source_model("scene-interior.json", Scene))
    scene = seal(Scene, "scene", scene_tpl | {"scene_id": spec["scene"]["scene_id"], "location": spec["scene"]["location"],
                                              "time": spec["scene"]["time"], "mood": spec["scene"]["mood"],
                                              "participant_ids": ["IRIS"] if spec["iris"] else [],
                                              "continuity_constraints": (["人物身份、左耳装置与左领红光位置一致"] if spec["iris"] else [])
                                              + ["蓝黑/钢蓝，红为唯一暖色"],
                                              "visual_reference_asset_ids": [r[0] for r in refs if r[4] != "identity"]})
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
    gen_refs = []
    for aid, _, _, need, anchor_role, _ in refs:
        gen_refs.append({"role": frames[aid], "asset_id": aid} if frames else
                        {"role": "character_reference", "asset_id": aid, "owner_id": "IRIS"} if anchor_role == "identity"
                        else {"role": "scene_reference", "asset_id": aid})
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
           "composition": {"muted": True, "source_audio_policy": "MUTE", "source_audio_reason": "成片使用已认可歌曲 v2 独立音轨"},
           "boundary": {"independent": True, "reason": "按分镜 v2.1 由最终剪辑切接；不要求复制前镜终态"}}
    authored = {"native_prompt": prompt, "row": row}
    authored_ref = authoring_input_reference(authored)
    provenance.append(authored_ref)
    out = root / authored_ref.reference
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(authoring_input_payload(authored))

    lines = prompt.splitlines()
    profile = {"domain_id": "iris-source", "profile_id": f"iris-v2-{unit.lower()}-raw", "profile_version": "1",
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
                          "necessity": "分镜 v2.1 与导演认可的参考包决定这一镜承担的可见事件。"}}})
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
        "final_output": {"goal_id": f"iris-v2-{unit.lower()}-source", "goal_version": "1",
                         "user_goal": f"分镜 v2.1 {cu} {ZH_SECONDS[secs]}秒源片（{unit}）；不代表整集或人工验收",
                         "requirements": [{"requirement_id": r[0], "observable": r[1], "proof": "human"} for r in rules]}})
    for name, obj in (("scene.json", scene), ("shot.json", shot), ("qa-policy.json", qa), ("registry-draft.json", registry)):
        write(root, name, obj.model_dump(mode="json"))
    for name, obj in (("row.json", row), ("preview-approval.json", preview), ("source-selections.json", selections)):
        write(root, name, obj)
    (root / "native-prompt.zh.txt").write_text(prompt + "\n", encoding="utf-8")
    print(json.dumps({"unit": unit, "draft": str(root), "refs": [s["asset_id"] for s in selections],
                      "prompt_chars": len(prompt), "canonical_writes": 0, "provider_calls": 0}, ensure_ascii=False))
    return root


# ---------------------------------------------------------------- materialize
def materialize(unit: str, profile_path: Path) -> None:
    from ai_video.canvas_dependencies import initialize_canvas_graph
    from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
    from ai_video.production.jimeng_contracts import JimengProfile
    from ai_video.production.project import load_production_project
    from ai_video.production.shot_router import RouterPolicyIdentity, VideoRoutingPolicy
    from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter, _canonical_yaml_bytes
    from scripts.jimeng_feedback_driver import DriverConfiguration, create_runtime

    spec = SPECS[unit]
    root = P / unit
    project_root = root / "project"
    if project_root.exists():
        raise Blocked("project already materialized; inspect it instead of rebuilding")
    profile = JimengProfile.model_validate_json(profile_path.read_bytes())
    mode, secs = spec.get("input_mode", "multimodal"), spec.get("duration", 6)
    if (profile.model_id, profile.input_mode, profile.duration_seconds, profile.resolution, profile.aspect_ratio) != (
            "seedance_2.0_vip", mode, secs, "1080p", "16:9"):
        raise Blocked(f"profile must be seedance_2.0_vip {mode} {secs}s 1080p 16:9")
    base = load_production_project(BASE / "project.yaml")
    char = next(c for c in base.characters if c.character_id == "IRIS")

    def typed(name, cls):
        obj = cls.model_validate_json((root / name).read_bytes())
        if not verify_artifact_hash(obj):
            raise Blocked("draft hash changed: " + name)
        return obj

    scene, shot, qa = typed("scene.json", Scene), typed("shot.json", Shot), typed("qa-policy.json", QaPolicy)
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
    records = {a.asset_id: a for a in registry.assets}
    if spec["iris"]:                                                  # keep the exact canonical identity record
        base_assets = {a.asset_id: a for a in base.registry.assets}
        if ("iris-cf-details" in records                              # absent when the user waived the sheet
                and base_assets["iris-cf-details"].sha256 != records["iris-cf-details"].sha256):
            raise Blocked("IRIS identity asset differs from the canonical project")
        for aid in ("iris-cf-details", "iris-cf-face"):               # the Character's own records stay complete
            record = base_assets[aid]
            records[aid] = record
            if record.artifact_path not in artifacts:
                artifacts[record.artifact_path] = prepared(record.artifact_path, (base.root / record.artifact_path).read_bytes())
    registry = AssetRegistrySnapshot(schema_version=registry.schema_version, revision_id="0" * 64, content_hash="0" * 64,
                                     assets=tuple(sorted(records.values(), key=lambda a: a.asset_id)))
    rh = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": rh, "content_hash": rh})

    provenance = list(dict.fromkeys((*scene.source_provenance, *shot.source_provenance, *qa.source_provenance,
                                     *(char.source_provenance if spec["iris"] else ()))))
    for ref in provenance:
        if not ref.reference.startswith("evidence/authoring-input/"):
            continue
        own, original = root / ref.reference, base.root / ref.reference
        raw = (own if own.is_file() else original).read_bytes()
        if canonical_sha256(json.loads(raw)) != ref.content_hash:
            raise Blocked("creative provenance changed")
        artifacts[Path(ref.reference)] = prepared(ref.reference, raw)

    def reseal(obj, **updates):
        return seal_artifact(obj.model_copy(update=updates))

    def model_artifact(model):
        path = Path("creative") / model.artifact_id / (model.content_hash + ".yaml")
        artifacts[path] = prepared(path, _canonical_yaml_bytes(model))
        return ArtifactReference(artifact_id=model.artifact_id, revision=model.revision, content_hash=model.content_hash, path=path)

    tag = f"iris-v2-{unit.lower()}"
    scene = reseal(scene, artifact_id=f"{tag}-scene")
    shot = reseal(shot, artifact_id=f"{tag}-shot")
    common = dict(revision=1, content_hash="0" * 64, creation_receipt_id=f"{tag}-authoring", source_provenance=tuple(provenance))
    brief = seal_artifact(ProductionBrief(artifact_id=f"{tag}-brief", title=f"IRIS EP01 v2 {unit} source",
        objective=f"分镜 v2.1 {spec.get('coverage_unit', unit)} {ZH_SECONDS[secs]}秒源片", audience="中文短视频观众", format="1920×1080 30fps horizontal source",
        language="zh", constraints=shot.continuity_constraints, **common))
    story = seal_artifact(Story(artifact_id=f"{tag}-story", language="zh", logline="IRIS EP01 v2 " + unit,
        synopsis=shot.intent.splitlines()[0], beats=(StoryBeat(beat_id=spec["beat"], summary=f"分镜 v2.1 {unit}"),), **common))
    board = seal_artifact(Storyboard(artifact_id=f"{tag}-storyboard", beats=(StoryboardBeat(beat_id=spec["beat"],
        scene_id=scene.scene_id, shot_ids=(shot.shot_id,), narrative_intent=f"分镜 v2.1 {unit}，由最终剪辑切接"),), **common))
    chars = (model_artifact(char),) if spec["iris"] else ()
    refs = ProjectArtifactRefs(brief=model_artifact(brief), story=model_artifact(story), characters=chars,
                               scenes=(model_artifact(scene),), storyboard=model_artifact(board), shots=(model_artifact(shot),))
    project = seal_artifact(ProductionProject(artifact_id=f"{tag}-project", project_id=f"{tag}-source", title=f"IRIS EP01 v2 {unit} source",
        default_language="zh", delivery_profile=base.project.delivery_profile, renderer_policy=base.project.renderer_policy,
        artifacts=refs, **common))

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
    if media != [x["asset_id"] for x in selections if x.get("kind") == "audio"]:
        raise Blocked(f"resolved audio binding differs from the authored audio reference: {media}")
    if actual != expected:                       # the prompt names images by position ("第一张图", "第二张图")
        raise Blocked(f"resolved reference order differs from the authored order: {actual} vs {expected}")
    (root / "compiled-native-prompt.zh.txt").write_text(result.compilation.request.prompt_text + "\n", encoding="utf-8")
    write(root, "materialization-result.json", {"project_root": str(project_root), "task_id": task,
          "request_hash": result.resolved_request.resolved_generation_hash, "resolved_reference_order": actual,
          "new_provider_calls": 0, "new_attempt_started": False})
    print(json.dumps({"unit": unit, "prepared": True, "resolved_reference_order": actual, "new_provider_calls": 0}, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["draft", "materialize"])
    ap.add_argument("unit", choices=sorted(SPECS))
    ap.add_argument("--profile", type=Path)
    args = ap.parse_args()
    try:
        if args.action == "draft":
            draft(args.unit)
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
