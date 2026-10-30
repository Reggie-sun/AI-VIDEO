"""Author the dispatch scene shots (D2/D3/D4 multimodal, D6 first-last frame).

Local authoring only: writes per-shot row/data/prompt/reference records under this
directory. No browser, Provider, run-root or Manifest writes. Rows derive from the
approved 1080p Seedance 2.0 VIP template (MC01-02-1080p-v3) and CITY-RISE (FLF).
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import GenerationIntent

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from prompts import PROMPTS  # noqa: E402

PKG = HERE.parent
COVERAGE = PKG / "director-coverage.v5.json"
MULTI = ROOT / "outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-1080p-v3"
FLF = ROOT / "outputs/shizhen-episode01/macro-opening-video-20261028/CITY-RISE-v1"
B6_SOURCE = ("runs/shizhen-fusion-B-motion-20261027/render-ASSEMBLY-B6/source/assets/"
             "587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc.mp4",
             "587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc")
CATEGORIES = {
    "identity": ("identity_continuity",),
    "action": ("open_state", "close_state", "scene_continuity", "subject_action", "motion_envelope", "pacing"),
    "camera": ("axis_continuity", "camera_endpoint", "camera_intent", "camera_subject_relation", "primary_camera_motion"),
    "performance": ("performance_intent",),
    "space": ("space_continuity",),
    "sound": ("ambience_intent", "dialogue_intent", "music_intent"),
    "art": ("lighting_intent", "visual_treatment"),
}
FRAGMENT_LINES = {"identity": [0, 1], "action": [1], "camera": [2], "performance": [1],
                  "space": [1], "sound": [3], "art": [1, 3]}
LOCKED = {"movement_kind": "locked", "direction": "none", "amplitude_class": "subtle", "speed_class": "very_slow",
          "start_motion_state": "stationary", "end_motion_state": "settled"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def leaves(node, prefix):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{prefix}.{index}")
    elif node is not None:
        yield prefix


def direction(cid, identity, role, trigger, emotion, face, gaze, body, intensity="subtle"):
    return {"character_id": cid, "screen_identity": identity, "role": role, "visibility": "visible",
            "offscreen_reason": None, "beats": [{"phase": "throughout", "trigger": trigger, "emotion": emotion,
            "intensity": intensity, "facial_expression": face, "gaze_target": gaze, "breathing": "自然平稳",
            "body_behavior": body}]}


SPECS = {
"D2": dict(
    unit="D2-stair-return", duration=6, scene_id="stair-loop", location="雨夜老旧住宅楼梯间",
    characters=[{"character_id": "stair-resident", "name": "楼梯住户", "identity": "只露背影的住户，背黄色帆布包",
                 "appearance_bible": "深色外套、黄色帆布包，全程背影"}],
    open="雨夜楼梯间转角平台，前景墙角一只侧面凹陷的红色灭火器，住户背对镜头站在平台上准备下楼。",
    close="同一名背黄色帆布包的住户从上方那段楼梯回到同一个平台，背对镜头停在同一只凹陷的灭火器前。",
    mood="楼梯照常，却回到了原来那层", constraints=["同一只凹陷的灭火器始终在前景", "同一名住户，只露背影", "不加字幕、楼层号或音乐"],
    position="住户从平台走下右侧楼梯出画，再从右上方楼梯回到平台", screen="下楼向右下出画，回来从右上入画",
    onset="住户走下楼梯拐弯出画", peak="同一住户从上方楼梯走下来", settle="停在凹陷的灭火器前", motion_dir="下楼出画再从上方回到原处",
    cadence="离开、短暂空画、从上方回来、停住", camera_move="固定", camera_framing="平台、凹陷的灭火器和上下两段楼梯同框",
    start_framing="平台全景，凹陷的灭火器在前景", end_framing="同一全景，住户停在灭火器前",
    motion=LOCKED, relation=("stair-resident", "fixed_frame", "平台与灭火器同框", "住户回到平台"),
    perf=dict(trigger="下楼离开", visible_response="从上方回到原处，停在灭火器前", gaze="前方楼梯",
              body="正常下楼，回来后停住，不回头", hand="自然下垂", terminal="背对镜头停在灭火器前"),
    directions=[direction("stair-resident", "背黄色帆布包、穿深色外套的住户背影", "principal", "正常下楼",
                          "平常，没有察觉异常", "不可见", "前方楼梯", "正常下楼出画，再从上方楼梯走回平台停住，不回头")],
    light=("吸顶灯与窗外雨夜", "偏冷顶光", "凹陷的灭火器和住户背影可读", "同一盏灯常亮"),
    ambience=("楼梯间脚步回声、远处雨声、吸顶灯轻微电流声", ["脚步回声"]),
    events=[], facets=["stable"],
    ref=("D2-ref-stair", "codex-image/raw/D2-v1.png", "scene_reference", None),
),
"D2r1": None,
"D3": dict(
    unit="D3-er-recorded-dead", duration=6, scene_id="er-bay", location="夜间医院急诊区",
    characters=[{"character_id": "er-nurse", "name": "急诊护士", "identity": "戴蓝色口罩的护士",
                 "appearance_bible": "浅蓝护士服、蓝色口罩、盘发"},
                {"character_id": "er-patient", "name": "女病人", "identity": "六十多岁的女病人",
                 "appearance_bible": "灰白短发、病号服、白色腕带"}],
    open="护士站在病床旁，手持扫码枪对准女病人手腕上的白色腕带，病人平躺、睁着眼睛。",
    close="镜头停在女病人的脸部近景，她睁着眼睛、正常呼吸；扫码枪已两次亮红。",
    mood="系统说她已经死了，人还活着", constraints=["同一护士与病人", "指示灯只亮红，不显示文字", "不加字幕、屏幕文字或音乐"],
    position="护士在左，病人躺在右侧病床", screen="镜头从左侧扫码枪推向右侧病人的脸",
    onset="扫码枪第一次亮红", peak="第二次亮红，护士抬眼", settle="停在病人睁着眼的脸", motion_dir="从扫码枪推向病人",
    cadence="两次扫码失败、护士抬眼、推到病人的脸", camera_move="从扫码枪红灯缓慢推向病人的脸",
    camera_framing="先看清红色指示灯，再落到病人睁着的眼睛", start_framing="扫码枪与腕带近景",
    end_framing="病人的脸部近景",
    motion={"movement_kind": "dolly_in", "direction": "forward", "amplitude_class": "moderate", "speed_class": "slow",
            "start_motion_state": "stationary", "end_motion_state": "settled"},
    relation=("er-patient", "reveal", "扫码枪与腕带", "病人睁着眼的脸"),
    perf=dict(trigger="扫码两次失败", visible_response="护士抬眼看病人，停住", gaze="护士看病人的脸，病人看护士",
              body="护士手里的扫码枪停在腕带上方", hand="护士右手持扫码枪", terminal="病人平静地看着护士，正常呼吸"),
    directions=[direction("er-nurse", "戴蓝色口罩的护士", "supporting", "扫码枪两次亮红", "职业性的迟疑",
                          "口罩上方的眼睛微微一顿", "从扫码枪抬眼看病人", "再扫一次后停手，不说话"),
                direction("er-patient", "睁着眼睛的六十多岁女病人", "principal", "护士扫她的腕带", "平静",
                          "睁着眼睛，面容平静", "看着护士", "平躺，胸口随正常呼吸起伏，不说话")],
    light=("急诊区冷白顶灯", "顶光与侧前补光", "红色指示灯和病人睁着的眼睛可读", "灯光不变"),
    ambience=("监护仪平稳的嘀声、远处急诊区低低的嘈杂", ["扫码失败提示音两声"]),
    events=[{"event_id": "scanner-red", "kind": "composition", "phase": "start",
             "visual_state": "扫码枪的红色指示灯", "purpose": "让观众先看到系统判定失败"},
            {"event_id": "eyes-open", "kind": "composition", "phase": "end",
             "visual_state": "病人的脸部近景，她睁着眼睛、正常呼吸",
             "purpose": "让观众先看到系统判定失败，再看到她明明活着"}],
    facets=["slow_camera"],
    ref=("D3-ref-er", "codex-image/raw/D3-v1.png", "scene_reference", None),
),
"D4": dict(
    unit="D4-sealed-seventh", duration=7, scene_id="sealed-building", location="雨夜老旧住宅楼外",
    characters=[{"character_id": "night-guard", "name": "保安", "identity": "只露背影的夜班保安",
                 "appearance_bible": "深色制服、透明雨衣、手电"}],
    open="保安背对镜头站在楼下，手电光斑照在一楼的窗户上。",
    close="镜头停在第七层一扇被木板钉死的窗上，手电光斑停在那里。",
    mood="有人在早已封死的七楼呼救", constraints=["第七层所有窗户被木板封死", "保安只露背影、不说话", "不加字幕、招牌或音乐"],
    position="保安在楼下前景，楼体在后", screen="镜头与光斑一起向上",
    onset="手电照亮一楼窗户", peak="光斑逐层上移", settle="停在七楼封死的窗上", motion_dir="由下往上",
    cadence="逐层上移，停住，雨声里一声极轻的呼救", camera_move="跟着手电光斑由下往上摇",
    camera_framing="逐层经过窗户，停在七楼封死的窗", start_framing="保安肩后低位，一楼窗户",
    end_framing="七楼被木板封死的窗",
    motion={"movement_kind": "tilt_up", "direction": "up", "amplitude_class": "pronounced", "speed_class": "slow",
            "start_motion_state": "stationary", "end_motion_state": "settled"},
    relation=("night-guard", "follow", "保安肩后与一楼", "七楼封死的窗"),
    perf=dict(trigger="接到人民路的呼救报告", visible_response="举手电逐层往上照", gaze="手电光斑",
              body="站在楼下不动", hand="右手举手电往上照", terminal="手电停在七楼封死的窗上"),
    directions=[direction("night-guard", "穿透明雨衣的保安背影", "principal", "楼上有人呼救",
                          "警觉", "不可见", "手电光斑", "右手举手电由下往上照，不说话")],
    light=("手电光与楼内窗光", "手电由下往上", "光斑与七楼木板可读", "雨夜不变"),
    ambience=("密集雨声、雨点打在雨衣上、远处车流", ["光斑停住后木板后极轻的一声呼救"]),
    events=[{"event_id": "guard-ground", "kind": "composition", "phase": "start",
             "visual_state": "楼下保安肩后的低位", "purpose": "跟着手电光斑平稳地向上摇，逐层经过窗户"},
            {"event_id": "sealed-seventh", "kind": "composition", "phase": "end",
             "visual_state": "第七层那扇被木板封死的窗",
             "purpose": "让观众数着楼层看见七楼早已封死"}],
    facets=["slow_camera"],
    ref=("D4-ref-facade", "codex-image/raw/D4-v1.png", "scene_reference", None),
),
"D6": dict(
    unit="D6-station-no-report", duration=5, scene_id="rain-stop", location="雨夜玻璃公交站棚",
    characters=[{"character_id": "gao-zheng", "name": "高峥", "identity": "B6第0帧左侧戴眼镜的中年男人",
                 "appearance_bible": "眼镜、棕色夹克、斜挎包，按B6原造型"},
                {"character_id": "luo-min", "name": "罗敏", "identity": "B6第0帧右侧打电话的短发年轻女人",
                 "appearance_bible": "短发、墨绿色外套、手机，按B6原造型"}],
    open="已认可B6第0帧：玻璃站棚正前方，左侧中年男人低头，右侧短发女人打电话。",
    close="回到已认可B6第0帧的同一画面与姿态。",
    mood="站台照常，暂无报告", constraints=["首尾都是B6第0帧", "两人原地不动、不说话", "不加新字幕或音乐"],
    position="左高峥右罗敏，原位", screen="不镜像",
    onset="雨中静候", peak="只有呼吸和雨水", settle="回到首帧姿态", motion_dir="原地",
    cadence="安静等待，只有极小动作", camera_move="固定", camera_framing="B6第0帧构图",
    start_framing="B6第0帧", end_framing="B6第0帧", motion=LOCKED,
    relation=("luo-min", "fixed_frame", "B6第0帧", "B6第0帧"),
    perf=dict(trigger="等车", visible_response="原地等待", gaze="男人看地面，女人看前方", body="原地站立",
              hand="女人手机贴耳，男人手插口袋", terminal="与B6第0帧一致"),
    directions=[direction("gao-zheng", "左侧戴眼镜、穿棕色夹克的中年男人", "supporting", "等车", "平常",
                          "自然", "地面", "低头原地站立，手插口袋"),
                direction("luo-min", "右侧穿墨绿色外套的短发年轻女人", "principal", "等电话接通", "平常",
                          "自然", "前方", "手机贴耳，原地站立")],
    light=("站棚暖灯与路灯", "同B6第0帧", "两人与站棚可读", "站棚灯常亮"),
    ambience=("站棚上的雨声和远处车流", ["雨声"]),
    events=[], facets=["stable"],
    ref=None,
),
}


SPECS["D2r1"] = dict(SPECS["D2"], open="住户背对镜头，右手扶着扶手，正踏下往下那段楼梯的第一级；前景墙角是侧面凹陷的红色灭火器。",
                     position="住户先沿扶手旁往下的楼梯走出画面，再从右上方楼梯回到平台",
                     screen="往下离开走出画面，回来从右上入画", first_frame="codex-image/raw/D2-first-frame-v1.png",
                     first_frame_prompt="codex-image/D2-first-frame-prompt.zh.txt",
                     ref=None)

SPECS["D4r1"] = dict(SPECS["D4"], open="保安背对镜头站在楼下，手电光斑照在低层的窗户上；画面只见下面三层，楼体向上出画。",
                     first_frame="codex-image/raw/D4-first-frame-v1.png",
                     first_frame_prompt="codex-image/D4-first-frame-prompt.zh.txt", ref=None)


def intent_for(name: str, spec: dict, base: dict, coverage_hash: str) -> dict:
    gi = copy.deepcopy(base)
    lines = PROMPTS[name]
    gi["open_state"].update(state_text=spec["open"], required_change=False)
    gi["close_state"].update(state_text=spec["close"], required_change=True)
    # Extras appear once and are carried by the scene reference / anchor frame, not identity sheets.
    gi["identity_continuity"] = {"character_ids": [], "preservation": "unspecified", "allowed_variation": []}
    gi["scene_continuity"].update(scene_id=spec["scene_id"], time_of_day="雨夜", mood=spec["mood"],
                                  state_constraints=spec["constraints"])
    gi["space_continuity"].update(subject_position=spec["position"], screen_direction=spec["screen"],
                                  crossing_policy="不越轴、不穿墙")
    gi["axis_continuity"].update(camera_axis="单一机位方向", framing_continuity=spec["camera_framing"],
                                 crossing_policy="不越轴")
    gi["subject_action"].update(start_state=spec["open"], progression=lines[1])
    gi["subject_action"]["endpoint"].update(state_text=spec["close"], required_change=True)
    gi["motion_envelope"].update(onset=spec["onset"], peak=spec["peak"], settle=spec["settle"],
                                 direction=spec["motion_dir"], amplitude_class="正常实时动作")
    gi["pacing"].update(cadence=spec["cadence"], tempo_class="自然原速", shot_duration_seconds=float(spec["duration"]))
    gi["camera_intent"].update(movement=spec["camera_move"], stability="稳定", framing_intent=spec["camera_framing"])
    gi["camera_endpoint"].update(start_framing=spec["start_framing"], end_framing=spec["end_framing"],
                                 position_lock=spec["motion"]["movement_kind"] == "locked",
                                 orientation_lock=spec["motion"]["movement_kind"] == "locked")
    gi["primary_camera_motion"] = dict(spec["motion"])
    sid, kind, start, end = spec["relation"]
    gi["camera_subject_relation"] = {"subject_id": sid, "relation_kind": kind, "start_relation": start,
                                     "end_relation": end}
    p = spec["perf"]
    gi["performance_intent"] = {"trigger": p["trigger"], "visible_response": p["visible_response"],
                                "gaze_target": p["gaze"], "body_behavior": p["body"], "hand_behavior": p["hand"],
                                "terminal_performance_state": p["terminal"], "character_directions": spec["directions"]}
    gi["visual_treatment"].update(medium_look="正常速度的真人摄影质感", palette="雨夜冷灰与实用灯",
                                  material_treatment="潮湿墙面、金属、雨水与真实衣物",
                                  prohibited_visual_drift=["慢动作、闪屏、黑屏、鬼影", "片名、字幕、说明文字或分格"])
    src, direction_, exposure, cont = spec["light"]
    gi["lighting_intent"] = {"motivated_source": src, "direction": direction_, "exposure_priority": exposure,
                             "continuity_state": cont}
    bed, cues = spec["ambience"]
    gi["ambience_intent"] = {"environment_bed": bed, "foley_cues": cues, "explicitly_silent": False}
    gi["dialogue_intent"] = {"mode": "none", "speaker_id": None, "verbatim_text": None, "start_seconds": None,
                             "end_seconds": None, "on_screen": None, "response_obligation": None,
                             "lip_sync_required": False}
    gi["music_intent"] = {"mode": "none", "instrumentation": None, "tempo_rhythm": None, "dynamics": None}
    gi["reference_planning"] = {"facets": spec["facets"], "events": spec["events"],
                                "director_coverage": {"coverage_hash": coverage_hash, "unit_id": spec["unit"]}}
    return GenerationIntent.model_validate(gi).model_dump(mode="json")


def reference_image(name: str, spec: dict, out: Path) -> list[dict]:
    if spec.get("first_frame"):
        frame = HERE / spec["first_frame"]
        with Image.open(frame) as image:
            width, height = image.size
        record = {"schema_version": "agent-generated-image-observation/1", "source_path": rel(frame),
                  "sha256": sha(frame), "size_bytes": frame.stat().st_size, "width": width, "height": height,
                  "reference_role": "first_frame", "platform_admission": "NOT_EVALUATED",
                  "generator": "codex exec built-in image_gen (one call)",
                  "prompt_path": rel(HERE / spec["first_frame_prompt"]),
                  "prompt_sha256": sha(HERE / spec["first_frame_prompt"]),
                  "semantic_review": "Static review by Parent before use; not video acceptance"}
        write(out / "reference-first-frame-source.json", record)
        return [{"asset_id": f"{name}-first-frame", "node_id": f"{name}-first-frame-node",
                 "resource_id": f"{name}-first-frame-local-generated", "path": str(frame),
                 "usage_license": "Original fictional reference generated for authorized Shizhen opening",
                 "generated_source": {"record_path": rel(out / "reference-first-frame-source.json"),
                                      "record_sha256": sha(out / "reference-first-frame-source.json"),
                                      "tool": {"name": "codex-generated-image", "version": "codex-cli-0.166.0"}}}]
    if spec["ref"] is None:
        frame = out / "anchors/b6-source-f0.png"
        assert frame.exists(), "extract B6 frame 0 first"
        record = {"schema_version": "agent-generated-image-observation/1", "source_path": rel(frame),
                  "sha256": sha(frame), "size_bytes": frame.stat().st_size, "width": 1920, "height": 1080,
                  "reference_role": "first_frame/last_frame", "platform_admission": "NOT_EVALUATED",
                  "generator": "exact decoded video frame extraction (ffmpeg -vsync 0 select)",
                  "source_video_path": B6_SOURCE[0], "source_video_sha256": B6_SOURCE[1], "source_frame_index": 0,
                  "semantic_review": "Exact approved B6 source frame; carries the source clock and provider watermark"}
        write(out / "reference-b6-f0-source.json", record)
        last = out / "anchors/b6-source-f0-last.png"
        last_record = dict(record, source_path=rel(last), sha256=sha(last), size_bytes=last.stat().st_size,
                           reference_role="last_frame", lossless_reencode_of=rel(frame),
                           semantic_review="Pixel-identical lossless PNG re-encode of B6 frame 0; distinct bytes only "
                                           "because lifecycle input identities must be unique")
        write(out / "reference-b6-f0-last-source.json", last_record)
        def entry(suffix, path, record_name, tool):
            return {"asset_id": f"{name}-b6-f0{suffix}", "node_id": f"{name}-b6-f0{suffix}-node",
                    "resource_id": f"{name}-b6-f0{suffix}-local", "path": str(path),
                    "usage_license": "Task-owned approved Shizhen footage frame",
                    "generated_source": {"record_path": rel(out / record_name), "record_sha256": sha(out / record_name),
                                         "tool": tool}}
        return [entry("", frame, "reference-b6-f0-source.json",
                      {"name": "exact-video-frame-extraction", "version": "ffmpeg-select-v1"}),
                entry("-last", last, "reference-b6-f0-last-source.json",
                      {"name": "ffmpeg-lossless-png-reencode", "version": "compression-level-9"})]
    asset_id, raw, _role, _owner = spec["ref"]
    raw_path = HERE / raw
    with Image.open(raw_path) as image:
        width, height = image.size
    record = {"schema_version": "agent-generated-image-observation/1", "source_path": rel(raw_path),
              "sha256": sha(raw_path), "size_bytes": raw_path.stat().st_size, "width": width, "height": height,
              "reference_role": "reference", "platform_admission": "NOT_EVALUATED",
              "generator": "codex exec built-in image_gen (one call)",
              "prompt_path": rel(HERE / f"codex-image/{name}-prompt.zh.txt"),
              "prompt_sha256": sha(HERE / f"codex-image/{name}-prompt.zh.txt"),
              "semantic_review": "Static review by Parent: composition and key evidence readable; not video acceptance"}
    write(out / "reference-source.json", record)
    return [{"asset_id": asset_id, "node_id": asset_id + "-node", "resource_id": asset_id + "-local-generated",
             "path": str(raw_path), "usage_license": "Original fictional reference generated for authorized Shizhen opening",
             "generated_source": {"record_path": rel(out / "reference-source.json"),
                                  "record_sha256": sha(out / "reference-source.json"),
                                  "tool": {"name": "codex-generated-image", "version": "codex-cli-0.166.0"}}}]


def build(name: str) -> dict:
    spec = SPECS[name]
    out = HERE / name
    coverage = json.loads(COVERAGE.read_text())
    coverage_hash = canonical_sha256(coverage)
    template = FLF if spec["ref"] is None else MULTI
    row = json.loads((template / "row.json").read_text())
    data = json.loads((template / "data.json").read_text())
    base = json.loads((MULTI / "row.json").read_text())["generation"]["generation_intent"]
    intent = intent_for(name, spec, base, coverage_hash)
    prompt = "\n".join(PROMPTS[name])
    images = reference_image(name, spec, out)
    row["generation"]["generation_intent"] = intent
    row["generation"]["output_need"]["duration_seconds"] = spec["duration"]
    row["generation"]["audio_need"] = "required"
    if spec.get("first_frame"):
        first = images[0]["asset_id"]
        row["generation"]["references"] = [{"role": "approved_keyframe", "asset_id": first}]
        row["generation"]["conditioning_compatibility"] = {
            "lane": "i2va", "first_anchor_id": first, "available_duration_seconds": spec["duration"],
            "composition_compatible": True, "screen_order_compatible": True, "axis_compatible": True,
            "camera_path_reachable": True, "character_prop_state_reachable": True, "action_endpoint_reachable": True}
        roles = [{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]},
                 {"role": "first_frame", "asset_ids": [first], "allowed_asset_types": ["image"]}]
    elif spec["ref"] is None:
        first, last_id = images[0]["asset_id"], images[1]["asset_id"]
        row["generation"]["references"] = [{"role": "approved_keyframe", "asset_id": first},
                                           {"role": "last_frame", "asset_id": last_id}]
        compat = row["generation"]["conditioning_compatibility"]
        compat.pop("scale_transition", None)
        compat.update(first_anchor_id=first, last_anchor_id=last_id, available_duration_seconds=spec["duration"],
                      same_subject_scale=True, composition_compatible=True, screen_order_compatible=True,
                      axis_compatible=True, camera_path_reachable=True, character_prop_state_reachable=True,
                      action_endpoint_reachable=True)
        roles = [{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]},
                 {"role": "first_frame", "asset_ids": [first], "allowed_asset_types": ["image"]},
                 {"role": "last_frame", "asset_ids": [last_id], "allowed_asset_types": ["image"]}]
    else:
        asset_id, _raw, role, owner = spec["ref"]
        reference = {"role": role, "asset_id": asset_id}
        if owner:
            reference["owner_id"] = owner
        row["generation"]["references"] = [reference]
        roles = [{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]}]
    shot = row["shot"]
    shot.update(shot_id=name, scene_id=spec["scene_id"], storyboard_beat_id=spec["unit"], intent=prompt, dialogue="",
                character_ids=[c["character_id"] for c in spec["characters"]],
                continuity_constraints=spec["constraints"] + ["现场人物都不开口，对白来自记录台母带"],
                visual_strategy="generated_video", required_asset_roles=roles,
                generated_video_rationale=f"调度蒙太奇 {spec['unit']}：现场无对白画面，铺在对白母带的转报声下")
    shot["duration_policy"] = {"mode": "fixed", "seconds": spec["duration"]}
    for key in ("occurrence_id", "adaptation_reason"):
        row.pop(key, None)
    paths = {key: [p for field in fields for p in leaves(intent[field], "generation_intent." + field)]
             for key, fields in CATEGORIES.items()}
    lines = PROMPTS[name]
    fragments = {key: [lines[i] for i in index] for key, index in FRAGMENT_LINES.items()}
    observations = {
        "identity": "人物与参考或首帧一致，没有新增人物或换脸",
        "action": lines[1],
        "camera": lines[2],
        "performance": "人物都不开口，反应克制自然",
        "space": spec["position"],
        "sound": lines[3],
        "art": "真人摄影质感、雨夜光线连续，无慢动作、闪屏、字幕、屏幕文字",
    }
    if not any(p != "generation_intent.identity_continuity.preservation" for p in paths["identity"]):
        # No registered identity: extras are carried by the scene reference; keep the check under art.
        observations["art"] = "没有新增人物或换脸；" + observations["art"]
        for mapping in (paths, fragments, observations):
            mapping.pop("identity")
    for key in ("source_contract", "actual_model_inputs_planned", "review_only_inputs",
                "required_later_assembly_junction", "qualification_scope", "accepted_source",
                "original_720p_observations"):
        data.pop(key, None)
    data.update(objective=f"失帧冷开场调度蒙太奇 {spec['unit']}：{spec['mood']}；无对白现场画面",
                images=images, characters=[dict(c, reference_asset_ids=[images[0]["asset_id"]])
                                           for c in spec["characters"]],
                scene_images=[images[0]["asset_id"]], observations=observations, paths=paths,
                fragments=fragments, intent_sha256=canonical_sha256(intent),
                coverage={"path": rel(COVERAGE), "sha256": sha(COVERAGE), "coverage_hash": coverage_hash,
                          "unit_id": spec["unit"]},
                scene={"scene_id": spec["scene_id"], "location": spec["location"], "mood": spec["mood"]})
    write(out / "row.json", row)
    write(out / "data.json", data)
    (out / "native-prompt.zh.txt").write_text(prompt + "\n")
    return {"shot": name, "duration": spec["duration"], "prompt_chars": len(prompt),
            "mode": "first_frame" if spec.get("first_frame") else "first_last_frame" if spec["ref"] is None else "multimodal"}


if __name__ == "__main__":
    print(json.dumps([build(name) for name in (sys.argv[1:] or ("D2", "D3", "D4", "D6"))], ensure_ascii=False))
