#!/usr/bin/env python3
"""IRIS EP01 v3 Seedance units through the canonical owners: one independent source project per Shot.

  uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py draft U023
  uv run python outputs/ai-city-takeover/ep01/v3/gen/unit.py materialize U023 --profile outputs/ai-city-takeover/ep01/v3/gen/U023/profile.json

draft        typed Character / Scene / Shot / QA policy / Registry drafts and the director row, bound to the v3 director
             coverage (ep01/v3/director-coverage.json, schema 4) and the user's preview approval. No canonical writes,
             no Provider calls.
materialize  bootstraps <unit>/project with ProductionStateCommitter, activates the QA policy, writes
             driver-config.json and runs the transport-free prepare. No Provider call.
show         prints the resolved request that prepare sealed (model, mode, output, bindings, prompt). Reads files only.

Inputs come only from the approval (pilot/sd/preview-approval.json, the shape of v2 trial/story/preview-approval.json):
the native prompt is prompts.<unit>.text (exact, with its sha256), the only image is the preview artifact whose role is
"<unit> first frame" (a still under ep01/v3/plates/raw/), and generation must read seedance_2.0_vip · first_frame · 5 s ·
1080p · 16:9 · no audio. IRIS's identity is carried by that first frame plus the approval's identity_waivers ["IRIS"]; no
identity sheet is sent. The project's IRIS Character is the current canon (series/casting-v3/canon-v4.md, its four
fixed text blocks), not the v2 a01 project.

A multimodal unit (U021, the ESCAPE VELOCITY lip-sync method, v2 LSen1/LSzh1) sends exactly one image (role
"<unit> reference image", native {{image:0}}) and one vocal window (role "<unit> vocal", native {{audio:1}}); generation
must read seedance_2.0_vip · multimodal · 5 s · 1080p · 16:9 · audio "reference_audio". The page's own soundtrack
(native audio, always on in this adapter) follows the reference vocal; the final film replaces it with the song master.

Paths: every path inside the approval is relative to the repo root. The approval and the continuity report live in
outputs/ai-city-takeover/ep01/v3/pilot/sd/ unless SD_PILOT names another folder; unit folders and ledgers live in this
gen/ folder unless SD_UNITS names another one (SD_PILOT / SD_UNITS: relative to the repo root, or absolute). SD_TRIAL
names one folder for a separate take (e.g. pilot/sd-r3) that holds all of them; SD_PILOT / SD_UNITS still win.

Same lane and gates as ep01/v2/gen/unit.py (Codex C unit pattern); submission is a separate step (operator.py) with its
own one-use bound.
"""
from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import wave

P = Path(__file__).resolve().parent
V3 = P.parent
EP = V3.parent
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
PILOT = REPO / os.environ.get("SD_PILOT", TRIAL or "outputs/ai-city-takeover/ep01/v3/pilot/sd")
UNITS = REPO / os.environ.get("SD_UNITS", TRIAL or P)
APPROVAL = PILOT / "preview-approval.json"
REPORT = PILOT / "continuity-report.json"
PLATES = "outputs/ai-city-takeover/ep01/v3/plates/raw/"
GENERATION = {"model": "seedance_2.0_vip", "mode": "first_frame", "seconds": 5, "resolution": "1080p", "aspect": "16:9",
              "audio": None}
GENERATION_LIPSYNC = {**GENERATION, "mode": "multimodal", "audio": "reference_audio"}
APPROVAL_ROLE = {"first_frame": "first frame", "multimodal": "reference image"}     # "<unit> <role>" in preview_artifacts
MARKERS = re.compile(r"\{\{(?:image|audio|video):\d+\}\}")
VOCALS = "outputs/ai-city-takeover/ep01/v3/pilot/audio/windows.json"   # the vocal windows cut from the song-v3 T4 stem
CANON = "outputs/ai-city-takeover/series/casting-v3/canon-v4.md"       # IRIS 定稿 v4 (E3 雕塑白)
CANON_SHA256 = "170443bdde078d4323a8668f5494750794cef7233d543d395fd6e6aec43b91c7"
IDENTITY_TEXT = ("同一IRIS（定稿v4）：银白色利落短发、银白眉毛和睫毛、很浅的冰灰色眼睛、左耳亮着小红灯的黑色耳挂装置、"
                 "白色雕塑感短款立领外套与左侧立领的极细红灯线完整保持；正面时耳挂与立领红线在画面右侧")
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
ZH_SECONDS = {4: "四", 5: "五", 6: "六"}
LOCKED = {"movement_kind": "locked", "direction": "none", "amplitude_class": "subtle", "speed_class": "very_slow",
          "start_motion_state": "stationary", "end_motion_state": "settled"}
LOCKED_INTENT = "摄影机完全固定，全程不推近、不移动、不摇镜"


# ---------------------------------------------------------------- pilot units (board v2 stage 7, 2026-11-04)
# pilot/preview-inputs.json: Seedance 2.0 VIP first-frame i2v, 5 s, 1080p 16:9, no audio reference; the native prompt is the
# exact approved pure-Chinese text. Every literal below (purpose, open/close events, natural motion) must appear in that
# text, so an approval whose prompt or first frame differs from what a spec was written for blocks the draft.
def iris_performance(trigger, response, gaze, body, hands, terminal, face):
    return {"trigger": trigger, "visible_response": response, "gaze_target": gaze, "body_behavior": body,
            "hand_behavior": hands, "terminal_performance_state": terminal,
            "character_directions": [{"character_id": "IRIS", "screen_identity": IDENTITY_TEXT, "role": "principal",
                                      "visibility": "visible", "beats": [{"phase": "throughout", "trigger": trigger,
                                      "emotion": "平静", "intensity": "subtle", "facial_expression": face,
                                      "gaze_target": gaze, "breathing": "自然平稳", "body_behavior": body}]}]}


def pilot_spec(unit: str, plate: str, scene: dict, purpose: str, intent: dict, performance: dict, relation: dict,
               rules: list, iris: bool, **extra) -> dict:
    n = unit.lower()
    aid = f"iris-c-v3-{n}-first-frame"
    return {"shot_id": "ep01v3-" + n, "beat": n, "iris": iris, "duration": 5, "coverage_unit": unit,
            "input_mode": "first_frame", "generation": GENERATION, "frame_roles": {aid: "approved_keyframe"},
            "conditioning": {"lane": "i2va", "first_anchor_id": aid, "available_duration_seconds": 5.0},
            "image": (aid, PLATES + plate, scene["scene_id"], "scene_environment", purpose),
            "identity_waiver": WAIVER if iris else None, "scene": scene, "camera_motion": LOCKED, "relation": relation,
            "intent": intent, "performance": performance, "rules": rules, **extra}


SPECS = {}
SPECS["U023"] = pilot_spec("U023", "P-city-gap-a.png", {
    "scene_id": "door-gap-city", "location": "一指宽的黑色门缝外，凌晨三点雾中的城市", "time": "凌晨三点",
    "mood": "冷、静，门外的城市在动"}, "从一扇只开着一指宽的黑色门缝向外看出去的画面", {
    "open": "U023首帧：从一指宽的黑色门缝向外看，缝里是凌晨三点雾中的城市", "close": "门缝仍只有一指宽，缝外车灯与雾仍在流动，构图不变",
    "action_start": "门缝外的城市", "progression": "高架桥上的车灯缓缓流过，远处窗灯安静地亮着，雾气慢慢飘过",
    "endpoint": "门缝仍只有一指宽，城市仍在动，画面里没有人", "camera": LOCKED_INTENT,
    "framing": "U023首帧：画面中央一道竖直的一指宽门缝，两侧是黑暗的门板边缘", "start_framing": "U023首帧原始构图",
    "end_framing": "与起始相同的机位与门缝宽度", "light": "城市的冷白和钢蓝色灯光", "ambience": "几乎无声（成片使用独立音轨）",
    "space": "主观视点不动，门缝的位置与宽度不变", "motion_peak": "车灯流过高架桥",
    "natural": ["高架桥上的车灯缓缓流过", "远处高楼的窗灯安静地亮着", "雾气慢慢飘过"],
    "open_event": ("门不动，门缝始终只有一指宽", "镜头固定"), "close_event": ("缝外的城市在动", "画面里没有人")},
    # no person on screen: the city performs; the camera is her point of view through the gap
    {"trigger": "凌晨三点，门只开着一指宽", "visible_response": "缝外的城市在动：车灯流过高架桥，雾气飘过",
     "gaze_target": "画面中没有人物；主观视点从门缝看向城市", "body_behavior": "画面中没有人物",
     "hand_behavior": "画面中没有人物", "terminal_performance_state": "门缝仍只有一指宽，城市仍在动"},
    {"subject_id": "door-gap", "relation_kind": "fixed_frame", "start_relation": "一指宽的门缝在画面中央",
     "end_relation": "门缝的宽度与位置不变"},
    [("door-gap", "门缝始终只有一指宽，门没有打开或变宽；画面里没有人、没有红色", 0, ()),
     ("city-moves", "缝外的城市在动：高架桥上的车灯缓缓流过，雾气慢慢飘过", 0, PERFORMANCE_KEYS),
     ("camera", LOCKED_INTENT + "，保持首帧的门缝构图", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)], iris=False)
# U045: the approved first frame shows a row of identical, eyes-closed copies of IRIS beside her on purpose (canon v4:
# same white jacket, collar light off). A gate must read the copies as the approved staging, not as identity drift.
COPIES_U045 = ("；她身边一排闭眼的她都是同一个IRIS的相同副本（canon v4：同款白色雕塑外套，立领灯线熄灭），这是认可首帧的设定："
               "不算身份漂移或新增人物")
SPECS["U045"] = pilot_spec("U045", "P-floor-line-at-a.png", {
    "scene_id": "floor-line", "location": "深夜幽暗的数据中心，湿润水泥地面上一条白色标线，一排闭眼静立的副本",
    "time": "深夜", "mood": "冷、压迫、不羁"}, "一排闭着眼睛、一动不动的副本", {
    "open": "U045首帧：低机位正面全身，一排闭眼静立的副本站在白色标线后，她也站在这一排里、脚尖贴着标线",
    "close": "她一步跨过标线后停在线外，直视镜头；副本仍闭眼不动，标线留在她身后，构图不变",
    "action_start": "她和副本并肩站在标线后，脚尖贴着标线", "progression": "一步跨过地面上的白色标线，停在线外，冰灰色的眼睛直视镜头",
    "endpoint": "停在线外直视镜头，神情平静而带着压迫感；副本始终闭眼不动", "camera": LOCKED_INTENT,
    "framing": "U045首帧：低机位正面全身，一排副本与她并肩站在标线后，她在画面中央", "start_framing": "U045首帧原始构图",
    "end_framing": "与起始相同的机位，她站在标线外、离镜头近一步", "light": "机柜的蓝色指示灯、贴地的冷蓝光雾与湿地面反光",
    "ambience": "几乎无声（成片使用独立音轨）", "space": "她从队列中一步跨过标线；副本保持原位",
    "motion_peak": "一步跨过标线", "natural": ["冷蓝的光雾贴着湿润的地面缓缓流动"],
    "open_event": ("她身边的副本始终闭着眼睛，一动不动", "镜头固定"),
    "close_event": ("一步跨过地面上的白色标线", "冰灰色的眼睛直视镜头")},
    iris_performance("她身边一排闭眼不动的副本", "一步跨过白色标线后停下，直视镜头", "镜头", "一步跨过标线后停下",
                     "双手自然垂在身侧", "停在线外直视镜头", "神情平静而带着压迫感"),
    {"subject_id": "IRIS", "relation_kind": "fixed_frame",
     "start_relation": "她在画面中央、与副本并肩站在标线后；身边一排闭眼的她是同一个IRIS的相同副本（首帧设定，不是身份漂移）",
     "end_relation": "她跨过标线、离镜头近一步并停下，机位不变"},
    [("identity", IDENTITY_TEXT + "（由认可的首帧承担）" + COPIES_U045, 0, ("identity_waivers",) + IDENTITY_KEYS),
     ("performance", "她一步跨过白色标线后停下，直视镜头；副本全程闭眼、静止、灯灭，不变形、不移动", 0, PERFORMANCE_KEYS),
     ("camera", LOCKED_INTENT + "，保持首帧构图", 0, CAMERA_KEYS),
     ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)], iris=True,
    notes="首帧有一排相同的IRIS副本（闭眼、灯灭），是认可的设定；后续Gate不得把副本判为身份漂移或新增人物")

# U021 (2026-11-04): ESCAPE VELOCITY lip-sync method (FINDINGS.md §B8; v2 LSen1 ran it on 2026-11-03): the approved plate
# as {{image:0}}, the exact vocal window as {{audio:1}}, a short pure-Chinese prompt that says she lip-syncs to it exactly.
# Lyric and onset: song-v3 lines-suno.json "I didn't run —" (61.26-64.58 s), timing/ctc-check.json energy onset of "I"
# 61.195 s, i.e. 0.99 s into the 60.20-64.56 s window.
LIPSYNC_KEYS = ("dialogue_intent", "performance_intent", "subject_action", "motion_envelope", "pacing")
LIPSYNC = "歌词期间嘴在唱、与参考人声逐字同步，无声处嘴唇闭合；对嘴准确度由片段自带音轨与参考人声的对齐量测和使用者审看判定"
SPECS["U021"] = {
    "shot_id": "ep01v3-u021", "beat": "u021", "iris": True, "duration": 5, "coverage_unit": "U021",
    "input_mode": "multimodal", "generation": GENERATION_LIPSYNC, "frame_roles": None,
    "image": ("iris-c-v3-u021-reference", PLATES + "P-gap-mcu-sing.png", "door-gap-red", "scene_environment", "中近景"),
    "audio": {"asset_id": "iris-c-v3-u021-vocal", "path": "outputs/ai-city-takeover/ep01/v3/pilot/audio/U021.wav",
              "window": "U021"},
    "dialogue": {"mode": "dialogue", "language": "en", "speaker_id": "IRIS", "verbatim_text": "I didn't run —",
                 "start_seconds": 0.99, "end_seconds": 4.36, "on_screen": True,
                 "response_obligation": "对着镜头唱出这一句，口型与参考人声逐字同步", "lip_sync_required": True},
    "identity_waiver": "全能参考对嘴：身份由使用者认可的参考图承担；认可的参考包只有这张图与人声窗口，不附身份图",
    "scene": {"scene_id": "door-gap-red", "location": "门缝旁，背后是幽暗机房的冷蓝灯光，右侧门缝漏出红光", "time": "凌晨",
              "mood": "冷、静，投入"},
    "camera_motion": LOCKED,
    "intent": {
        "open": "U021参考图：中近景正面，她闭着眼睛对着镜头唱，红光在右半边脸",
        "close": "唱到句尾慢慢睁开眼睛，平静地看着镜头，构图不变",
        "action_start": "中近景正面，闭眼，嘴微张", "progression": "对着镜头投入地唱，口型与参考人声逐字同步",
        "endpoint": "句尾睁开眼睛，平静地看着镜头", "camera": LOCKED_INTENT,
        "framing": "U021参考图：中近景正面，人物居中，右侧是漏红光的门缝", "start_framing": "U021参考图原始构图",
        "end_framing": "与起始相同的构图", "light": "右侧门缝的红光与背后机房的冷蓝灯光",
        "ambience": "片段自带音轨跟随参考人声（成片换成歌曲母带）", "space": "她站在门缝旁原位",
        "motion_peak": "句尾慢慢睁开眼睛", "natural": ["闭着眼睛投入地唱", "神情平静"],
        "open_event": ("对着镜头唱歌", "逐字精确同步"), "close_event": ("唱到句尾慢慢睁开眼睛", "镜头全程锁定")},
    "performance": iris_performance("副歌第一句", "闭着眼睛投入地唱，口型与参考人声逐字同步，句尾慢慢睁开眼睛",
                                    "先闭眼，句尾睁眼平静地看着镜头", "头部稳定朝向镜头，只随呼吸轻微起伏", "双手不入画",
                                    "句尾睁开眼睛，平静地看着镜头",
                                    "神情平静，面无表情，眉头舒展"),
    "relation": {"subject_id": "IRIS", "relation_kind": "fixed_frame", "start_relation": "中近景正面，人物居中",
                 "end_relation": "构图与机位不变"},
    "rules": [("identity", IDENTITY_TEXT + "（由认可的参考图承担）", 0, ("identity_waivers",) + IDENTITY_KEYS),
              ("lip-sync", LIPSYNC, 0, LIPSYNC_KEYS), ("camera", LOCKED_INTENT + "，一镜到底", 0, CAMERA_KEYS),
              ("no-new-graphics", NO_TEXT, 0, LABEL_KEYS)]}


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


def canon_blocks() -> list[str]:
    """The four fixed text blocks of canon v4: close/medium look, full/wide look, wardrobe, the copies' wardrobe."""
    raw = (REPO / CANON).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CANON_SHA256:
        raise Blocked("canon v4 changed since this lane was written; re-read it and update CANON_SHA256")
    blocks = re.findall(r"```text\n(.*?)\n```", raw.decode("utf-8"), re.S)
    if len(blocks) != 4:
        raise Blocked("canon v4 must hold its four fixed text blocks")
    return blocks


# ---------------------------------------------------------------- draft
def draft(unit: str) -> Path:
    spec = SPECS[unit]
    root = UNITS / unit
    approval_v3 = approval()                      # before any write: no approval, no unit folder
    root.mkdir(parents=True, exist_ok=True)
    approved = (approval_v3.get("prompts") or {}).get(unit)
    if not approved:
        raise Blocked(f"{unit} has no approved prompt in {APPROVAL}")
    prompt = approved["text"]                     # the exact text the user saw on the preview page
    if hashlib.sha256(prompt.encode()).hexdigest() != approved["sha256"]:
        raise Blocked("approved prompt text differs from its sealed sha256")
    if approval_v3.get("generation") != spec["generation"]:
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
    if spec["iris"] and "IRIS" not in approval_v3.get("identity_waivers", []):
        raise Blocked("IRIS is on screen without an identity sheet; the approval must list IRIS in identity_waivers")

    aid, plate, need, anchor_role, purpose = spec["image"]
    label = APPROVAL_ROLE[spec["input_mode"]]
    seen = approval_v3["preview_artifacts"]
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
        with Image.open(path) as im:
            w, h = im.size
            if im.format != "PNG":
                raise Blocked("reference must be the exact approved PNG: " + rel)
        item = {"asset_id": aid, "path": rel, "sha256": sha, "size_bytes": len(raw), "width": w, "height": h,
                "role": role, "need_id": need, "anchor_role": anchor_role, "selected_for_provider": True}
        selections.append(item)
        origin = {"kind": "iris-v3-source-selection/1", **item}
        ref = authoring_input_reference(origin)
        provenance.append(ref)
        out = root / ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        records.append(AssetRecord(asset_id=aid, asset_type="image", artifact_path=canonical_image_asset_path(sha), sha256=sha,
            size_bytes=len(raw), mime_type="image/png", width=w, height=h, source_kind="imported",
            tool={"name": "approved-local-source-import", "version": "1"}, input_fingerprint=canonical_sha256(origin),
            creation_receipt_id="iris-v3-local-import:" + sha,
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
        origin = {"kind": "iris-v3-source-selection/1", **item}
        ref = authoring_input_reference(origin)
        provenance.append(ref)
        out = root / ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        tool = {"name": "htdemucs_ft-stem+ffmpeg-trim", "version": "1"}
        meta = AudioAssetMetadata(audio_kind="dialogue", source=AudioSource(kind="derived", provider_or_tool=tool,
                                  input_fingerprint=canonical_sha256(origin), original_reference=windows["source"]),
                                  speaker_id="IRIS", language=spec["dialogue"]["language"],
                                  script_hash=hashlib.sha256(spec["dialogue"]["verbatim_text"].encode()).hexdigest(),
                                  duration_samples=n, sample_rate_hz=sr, channels=1, channel_layout="mono",
                                  codec_name="pcm_s16le", loudness=AudioLoudnessMetadata(),
                                  provenance_receipt_id="iris-v3-vocal-window:" + sha)
        records.append(AssetRecord(asset_id=aid, asset_type="voice", artifact_path=canonical_audio_asset_path(sha), sha256=sha,
            size_bytes=len(raw), mime_type="audio/wav", duration_seconds=n / sr, source_kind="derived", tool=tool,
            input_fingerprint=canonical_sha256(origin), creation_receipt_id="iris-v3-vocal-window:" + sha,
            usage_license="Derived from the user-approved song v3 T4; project reference only.", audio_metadata=meta))
    registry = AssetRegistrySnapshot(schema_version="2.1" if audio else "2.0", revision_id="0" * 64, content_hash="0" * 64,
                                     assets=tuple(sorted(records, key=lambda x: x.asset_id)))
    rh = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": rh, "content_hash": rh})

    # coverage (board v2, schema 4) and the user's preview approval, sealed as authoring inputs
    coverage = json.loads((V3 / "director-coverage.json").read_text(encoding="utf-8"))
    ch, ca = director_coverage_authoring_input(coverage)
    preview = {"kind": "user-preview-approval/1", "coverage_hash": ch, "unit_ids": [cu],
               "preview_artifacts": [{"path": a["path"], "sha256": a["sha256"], "role": a["role"]} for a in seen],
               "user_quote": approval_v3["user_quote"]}
    if approval_v3.get("identity_waivers"):                       # the performers the user agreed to show without a sheet
        preview["identity_waivers"] = approval_v3["identity_waivers"]
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
                            "settle": "摄影机始终静止" if locked else spec.get("settle", "末段平滑收稳"),
                            "direction": "摄影机不移动" if locked else it.get("envelope_direction", "向前"),
                            "amplitude_class": "很小"},
        "pacing": {"cadence": ZH_SECONDS[secs] + "秒连续原速", "tempo_class": "正常原速", "shot_duration_seconds": secs},
        "camera_intent": {"movement": it["camera"],
                          "stability": "完全静止的固定机位" if locked else spec.get("stability", "平稳连续，末段收稳"),
                          "framing_intent": it["framing"]},
        "camera_endpoint": {"start_framing": it["start_framing"], "end_framing": it["end_framing"]},
        "visual_treatment": {"medium_look": "真人电影摄影", "palette": "冷色调；红色只做讯号灯，是唯一暖色",
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
        return seal_artifact(cls(artifact_id=f"iris-v3-{unit.lower()}-draft-{key}", revision=1, content_hash="0" * 64,
                                 creation_receipt_id=f"iris-v3-{unit}-authoring:{key}",
                                 source_provenance=tuple(refs_ or provenance), **data))

    if spec["iris"]:                              # the current IRIS: canon v4's fixed text, no identity sheet
        close, wide, wardrobe, copies = canon_blocks()
        origin = {"kind": "iris-v3-character-canon/1", "path": CANON, "sha256": CANON_SHA256,
                  "fixed_text": [close, wide, wardrobe, copies]}
        canon_ref = authoring_input_reference(origin)
        out = root / canon_ref.reference
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(authoring_input_payload(origin))
        character = seal(Character, "character", {
            "character_id": "IRIS", "name": "IRIS", "identity": "IRIS 定稿 v4（E3 雕塑白）；全身与远景：" + wide,
            "appearance_bible": close, "wardrobe": (wardrobe,),
            "allowed_variations": ("同一身份的镜头角度与景别变化", "其他副本（同款，灯熄灭）：" + copies)}, [canon_ref])
        write(root, "character.json", character.model_dump(mode="json"))

    scene_tpl = core(source_model("scene-interior.json", Scene))
    scene = seal(Scene, "scene", scene_tpl | {"scene_id": spec["scene"]["scene_id"], "location": spec["scene"]["location"],
                                              "time": spec["scene"]["time"], "mood": spec["scene"]["mood"],
                                              "participant_ids": ["IRIS"] if spec["iris"] else [],
                                              "continuity_constraints": (["人物身份、左耳装置与左侧立领红灯线位置一致（canon v4）"]
                                                                         if spec["iris"] else [])
                                              + ["冷色调；红色只做讯号灯，是唯一暖色"],
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
           "composition": {"muted": True, "source_audio_policy": "MUTE", "source_audio_reason": "成片使用已选定歌曲 T4 独立音轨"},
           "boundary": {"independent": True, "reason": "按分镜 v3 由最终剪辑切接；不要求复制前镜终态"}}
    authored = {"native_prompt": prompt, "row": row}
    authored_ref = authoring_input_reference(authored)
    provenance.append(authored_ref)
    out = root / authored_ref.reference
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(authoring_input_payload(authored))

    lines = prompt.splitlines()
    profile = {"domain_id": "iris-source", "profile_id": f"iris-v3-{unit.lower()}-raw", "profile_version": "1",
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
                          "necessity": "分镜 v3 与使用者认可的预览包决定这一镜承担的可见事件。"}}})
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
        "final_output": {"goal_id": f"iris-v3-{unit.lower()}-source", "goal_version": "1",
                         "user_goal": f"分镜 v3 {cu} {ZH_SECONDS[secs]}秒源片（{unit}）；不代表整集或人工验收",
                         "requirements": [{"requirement_id": r[0], "observable": r[1], "proof": "human"} for r in rules]}})
    for name, obj in (("scene.json", scene), ("shot.json", shot), ("qa-policy.json", qa), ("registry-draft.json", registry)):
        write(root, name, obj.model_dump(mode="json"))
    for name, obj in (("row.json", row), ("preview-approval.json", preview), ("source-selections.json", selections)):
        write(root, name, obj)
    (root / "native-prompt.zh.txt").write_text(prompt + "\n", encoding="utf-8")
    print(json.dumps({"unit": unit, "draft": str(root), "refs": [s["asset_id"] for s in selections],
                      "character": "canon-v4" if spec["iris"] else None,
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
        canon_blocks()                                                # canon v4 unchanged since the draft
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

    tag = f"iris-v3-{unit.lower()}"
    scene = reseal(scene, artifact_id=f"{tag}-scene")
    shot = reseal(shot, artifact_id=f"{tag}-shot")
    common = dict(revision=1, content_hash="0" * 64, creation_receipt_id=f"{tag}-authoring", source_provenance=tuple(provenance))
    brief = seal_artifact(ProductionBrief(artifact_id=f"{tag}-brief", title=f"IRIS EP01 v3 {unit} source",
        objective=f"分镜 v3 {spec['coverage_unit']} {ZH_SECONDS[secs]}秒源片", audience="中文短视频观众", format="1920×1080 30fps horizontal source",
        language="zh", constraints=shot.continuity_constraints, **common))
    story = seal_artifact(Story(artifact_id=f"{tag}-story", language="zh", logline="IRIS EP01 v3 " + unit,
        synopsis=shot.intent.splitlines()[0], beats=(StoryBeat(beat_id=spec["beat"], summary=f"分镜 v3 {unit}"),), **common))
    board = seal_artifact(Storyboard(artifact_id=f"{tag}-storyboard", beats=(StoryboardBeat(beat_id=spec["beat"],
        scene_id=scene.scene_id, shot_ids=(shot.shot_id,), narrative_intent=f"分镜 v3 {unit}，由最终剪辑切接"),), **common))
    char = reseal(char, artifact_id=f"{tag}-character") if char else None
    chars = (model_artifact(char),) if char else ()
    refs = ProjectArtifactRefs(brief=model_artifact(brief), story=model_artifact(story), characters=chars,
                               scenes=(model_artifact(scene),), storyboard=model_artifact(board), shots=(model_artifact(shot),))
    project = seal_artifact(ProductionProject(artifact_id=f"{tag}-project", project_id=f"{tag}-source", title=f"IRIS EP01 v3 {unit} source",
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
