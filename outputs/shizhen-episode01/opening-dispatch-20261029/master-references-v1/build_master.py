"""Author the dispatch dialogue master (record desk, D1 + D5 + roll-call tail).

Local authoring only: writes M1/row.json, data.json, native prompt, reference
source records and the user preview approval payload. No browser, Provider,
run-root or Manifest writes. Template row: MC01-02-1080p-v3 (multimodal).
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from PIL import Image

from ai_video.production.hashing import canonical_sha256
from ai_video.production.preview_approval import KIND, validate_preview_approval
from ai_video.production.authoring_input import authoring_input_reference
from ai_video.production.video_requirement import GenerationIntent

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "M1"
COVERAGE = HERE.parent / "director-coverage.v6.json"
MULTI = ROOT / "outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-1080p-v3"
PROMPT = HERE / "authoring/master-native-prompt.zh.txt"
DURATION = 30
CHAR = "dong-wenhui"
RELAY = "dispatch-relay"
R = ROOT / "referces/shizhen/macro-opening-20261027/full-opening-references-20261027"
IDENTITY = ROOT / "referces/shizhen/character-packs-20261027/dong-wenhui/identity/identity-v1.png"
# Model inputs in native order: (asset_id, path, reference role, prompt that made it or None).
INPUTS = [  # sorted by asset_id = actual native binding order
    ("M1-env", HERE / "raw/ENV-desk-room-r1.png", "scene_reference", HERE / "prompts/ENV-desk-room-r1.zh.txt"),
    ("M1-identity", IDENTITY, "character_reference",
     ROOT / "referces/shizhen/character-packs-20261027/dong-wenhui/prompts/identity-v1.txt"),
    ("M1-k1", HERE / "raw/K1-D1-listen-v1.png", "scene_reference", HERE / "prompts/K1-D1-listen.zh.txt"),
    ("M1-k2", HERE / "raw/K2-D1-typed-r2.png", "scene_reference", HERE / "prompts/K2-D1-typed-r2.zh.txt"),
    ("M1-k4", HERE / "raw/K4-rollcall-r2.png", "scene_reference", HERE / "prompts/K4-rollcall-r2.zh.txt"),
]
PREVIEW_ONLY = [(HERE / "raw/K3-D5-tally-v1.png", "D5 特写关键帧（一镜到底后仅预览）"),
                (HERE / "raw/PROP-speaker-notebook-v1.png", "道具特写（外观与场景图冲突，仅预览）"),
                (R / "MC03-descent-side-v2.png", "造型参考（仅预览）"), (R / "MC01-normal.png", "风格帧（仅预览）")]
USER_QUOTE = ("先别管声音,就说开场的referces给我看下 / 可以 / 生图修图的额度调高可以10次 / 修 K4 后再认可 / "
              "seedacne2.5最多放30张,对了直接用seedance生成声音 / 认可，开始生成 / 改一镜到底")
UNITS = ["D1-record-desk", "D5-tally", "D6-station-no-report"]
CATEGORIES = {
    "identity": ("identity_continuity",),
    "action": ("open_state", "close_state", "scene_continuity", "subject_action", "motion_envelope", "pacing"),
    "camera": ("axis_continuity", "camera_endpoint", "camera_intent", "camera_subject_relation", "primary_camera_motion"),
    "performance": ("performance_intent",),
    "space": ("space_continuity",),
    "sound": ("ambience_intent", "dialogue_intent", "music_intent"),
    "art": ("lighting_intent", "visual_treatment"),
}
FRAGMENT_LINES = {"identity": [0, 1], "action": [2, 3, 4], "camera": [2, 3, 4], "performance": [2, 3, 4],
                  "space": [0, 4], "sound": [1, 2, 3, 4, 5], "art": [1, 5]}
TURNS = [
    (RELAY, "检修口报，电闸断了，绞盘还在收", False, "她静静听完才开始打字"),
    (RELAY, "七号楼报，下了三层，还在原来那层", False, "她停顿一下继续打字"),
    (RELAY, "急诊说，系统里她已经死了，人还躺着", False, "她手指停在键盘上方"),
    (RELAY, "人民路有人喊救命，在七楼，七楼早就封了", False, "镜头停在中近景，她写下新的一行"),
    (CHAR, "记上，第十四起", True, "笔停住，她把麦克风拉到面前"),
    (CHAR, "三号站台？", True, "随即松开按键，停一下等回答"),
    (RELAY, "暂无报告", False, "她看着扬声器不动"),
]


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


def approval(coverage_hash: str) -> dict:
    artifacts = [{"path": rel(p), "sha256": sha(p), "role": role} for _a, p, role, _pr in INPUTS]
    artifacts += [{"path": rel(p), "sha256": sha(p), "role": role} for p, role in PREVIEW_ONLY]
    payload = {"kind": KIND, "coverage_hash": coverage_hash, "unit_ids": UNITS,
               "preview_artifacts": artifacts, "user_quote": USER_QUOTE}
    validate_preview_approval(payload)
    return payload


def intent(base: dict, coverage_hash: str, approval_hash: str, lines: list[str]) -> dict:
    gi = copy.deepcopy(base)
    open_text = "深夜雨天的应急记录台，扬声器亮着绿灯，董文慧坐在桌后，双手放在键盘上。"
    close_text = "她已松开麦克风按键，看着扬声器不动；记录本上多了新的一行。"
    gi["open_state"].update(state_text=open_text, required_change=False)
    gi["close_state"].update(state_text=close_text, required_change=True)
    gi["identity_continuity"] = {"character_ids": [CHAR], "preservation": "exact", "allowed_variation": []}
    gi["scene_continuity"].update(scene_id="record-desk", time_of_day="雨夜", mood="报告一件件累积，语气越平淡越不安",
                                  state_constraints=["同一记录台与物件位置", "扬声器绿灯常亮", "她不戴耳机",
                                                     "不出现字幕、屏幕文字或可读字符"])
    gi["space_continuity"].update(subject_position="她坐在显示器右侧的椅子上，扬声器在桌面左角",
                                  screen_direction="机位在桌子正前方略偏左", crossing_policy="不越轴")
    gi["axis_continuity"].update(camera_axis="桌子正前方略偏左", framing_continuity="同一机位连续推近",
                                 crossing_policy="不越轴")
    gi["subject_action"].update(start_state=open_text, progression=lines[2])
    gi["subject_action"]["endpoint"].update(state_text=close_text, required_change=True)
    gi["motion_envelope"].update(onset="扬声器报第一起", peak="写下第十四起", settle="问三号站台后等回答",
                                 direction="原地", amplitude_class="正常实时动作")
    gi["pacing"].update(cadence="每句报告后留一秒多只听键盘和雨声", tempo_class="自然原速",
                        shot_duration_seconds=float(DURATION))
    gi["camera_intent"].update(movement="一个连续镜头，从中景缓慢推近", stability="稳定",
                               framing_intent="从中景推近到中近景：她的脸、双手、记录本与麦克风")
    gi["camera_endpoint"].update(start_framing="中景，她和桌面", end_framing="中近景，她的脸、双手、记录本与麦克风",
                                 position_lock=False, orientation_lock=False)
    gi["primary_camera_motion"] = {"movement_kind": "dolly_in", "direction": "forward", "amplitude_class": "subtle",
                                   "speed_class": "slow", "start_motion_state": "stationary",
                                   "end_motion_state": "settled"}
    gi["camera_subject_relation"] = {"subject_id": CHAR, "relation_kind": "reveal", "start_relation": "中景",
                                     "end_relation": "她的脸和双手"}
    gi["performance_intent"] = {
        "trigger": "扬声器一条条报来异常", "visible_response": "她听完才记，不惊慌",
        "gaze_target": "显示器与扬声器", "body_behavior": "坐着工作，最后把麦克风拉到面前",
        "hand_behavior": "打字、写字、按麦克风键", "terminal_performance_state": "看着扬声器不动",
        "character_directions": [
            {"character_id": CHAR, "screen_identity": "穿灰褐连帽外套、低马尾的董文慧", "role": "principal",
             "visibility": "visible", "offscreen_reason": None, "beats": [
                 {"phase": "throughout", "trigger": "扬声器传来的报告", "emotion": "克制、专注，越平淡越不安",
                  "intensity": "subtle", "facial_expression": "平静，眉头放松", "gaze_target": "显示器，问话时看扬声器",
                  "breathing": "自然平稳", "body_behavior": "听完第一句才打字，写字后笔停住，按麦克风键平静问话后松键"}]}]}
    gi["visual_treatment"].update(medium_look="正常速度的真人摄影质感", palette="雨夜冷蓝与台灯暖黄",
                                  material_treatment="旧金属桌面、纸张、塑料扬声器与真实衣物",
                                  prohibited_visual_drift=["慢动作、闪屏、黑屏、鬼影", "字幕、屏幕文字或可读字符"])
    gi["lighting_intent"] = {"motivated_source": "台灯与显示器", "direction": "台灯暖光在右，屏幕冷光照脸",
                             "exposure_priority": "她的脸、手和扬声器绿灯可读", "continuity_state": "灯光不变"}
    gi["ambience_intent"] = {"environment_bed": "窗外雨声、室内安静", "foley_cues": ["键盘声", "写字声", "麦克风按键声"],
                             "explicitly_silent": False}
    gi["dialogue_intent"] = {"mode": "conversation", "language": "zh", "turns": [
        {"speaker_id": s, "verbatim_text": t, "on_screen": on, "lip_sync_required": on, "response_obligation": r}
        for s, t, on, r in TURNS]}
    gi["music_intent"] = {"mode": "none", "instrumentation": None, "tempo_rhythm": None, "dynamics": None}
    gi["reference_planning"] = {
        "facets": ["dialogue", "slow_camera", "identity_consistency"], "structure": "continuous",
        "events": [
            {"event_id": "desk-push", "kind": "composition", "phase": "start",
             "visual_state": "中景，缓慢推近到她的脸和双手", "purpose": "把各处的报告收到记录台",
             "control": "model_guidance"},
            {"event_id": "desk-typed", "kind": "performance", "phase": "interior",
             "visual_state": "她手指停在键盘上方", "purpose": "她停顿一下继续打字", "control": "model_guidance"},
            {"event_id": "tally-line", "kind": "composition", "phase": "interior", "after_event_ids": ["desk-typed"],
             "visual_state": "镜头停在中近景，她的脸、双手和桌上的记录本都在画内", "purpose": "让异常的数量累积起来"},
            {"event_id": "rollcall-ask", "kind": "performance", "phase": "interior", "after_event_ids": ["tally-line"],
             "visual_state": "按住按键，平静地问", "purpose": "停一下，扬声器回答", "control": "model_guidance"},
            {"event_id": "rollcall-wait", "kind": "composition", "phase": "end",
             "visual_state": "她看着扬声器不动", "purpose": "让点名和回答落在同一个画面里"}],
        "anchors": [
            {"anchor_id": "dong-identity", "role": "identity", "purpose": "董文慧的长相", "owner_id": CHAR,
             "priority": "required"},
            {"anchor_id": "desk-room", "role": "scene_environment", "purpose": "记录室的布局、光线",
             "owner_id": "record-desk", "priority": "required"},
            ],
        "selections": [
            {"need_id": "dong-identity", "asset_id": "M1-identity"}, {"need_id": "desk-room", "asset_id": "M1-env"},
            {"need_id": "desk-push", "asset_id": "M1-k1"},
            {"need_id": "desk-typed", "asset_id": "M1-k2"},
            {"need_id": "rollcall-ask", "asset_id": "M1-k4"}],
        "director_coverage": {"coverage_hash": coverage_hash, "unit_id": "D1-record-desk"},
        "preview_approval": {"approval_hash": approval_hash}}
    return GenerationIntent.model_validate(gi).model_dump(mode="json")


def source_record(asset_id: str, path: Path, prompt: Path | None) -> dict:
    with Image.open(path) as image:
        width, height = image.size
    record = {"schema_version": "agent-generated-image-observation/1", "source_path": rel(path),
              "sha256": sha(path), "size_bytes": path.stat().st_size, "width": width, "height": height,
              "reference_role": "reference", "platform_admission": "NOT_EVALUATED",
              "generator": "codex exec built-in image_gen (one call)",
              "semantic_review": "Static review by Parent; user approved the preview package 2026-11-04; not video acceptance"}
    if prompt is not None and prompt.exists():
        record.update(prompt_path=rel(prompt), prompt_sha256=sha(prompt))
    name = f"reference-{asset_id}-source.json"
    write(OUT / name, record)
    return {"asset_id": asset_id, "node_id": asset_id + "-node", "resource_id": asset_id + "-local-generated",
            "path": str(path), "usage_license": "Original fictional reference generated for authorized Shizhen opening",
            "generated_source": {"record_path": rel(OUT / name), "record_sha256": sha(OUT / name),
                                 "tool": {"name": "codex-generated-image", "version": "codex-cli-0.166.0"}}}


def build() -> dict:
    coverage = json.loads(COVERAGE.read_text())
    coverage_hash = canonical_sha256(coverage)
    approval_payload = approval(coverage_hash)
    write(OUT / "preview-approval.json", approval_payload)
    approval_hash = authoring_input_reference(approval_payload).content_hash
    row = json.loads((MULTI / "row.json").read_text())
    data = json.loads((MULTI / "data.json").read_text())
    prompt = PROMPT.read_text().strip()
    lines = prompt.split("\n")
    gi = intent(row["generation"]["generation_intent"], coverage_hash, approval_hash, lines)
    images = [source_record(a, p, pr) for a, p, _role, pr in INPUTS]
    row["generation"]["generation_intent"] = gi
    row["generation"]["output_need"]["duration_seconds"] = DURATION
    row["generation"]["audio_need"] = "required"
    row["generation"]["references"] = [
        {"role": role, "asset_id": a, **({"owner_id": CHAR} if role == "character_reference" else {})}
        for a, _p, role, _pr in INPUTS]
    shot = row["shot"]
    shot.update(shot_id="M1", scene_id="record-desk", storyboard_beat_id="D1-record-desk", intent=prompt,
                dialogue="；".join(t for _s, t, _o, _r in TURNS), character_ids=[CHAR],
                continuity_constraints=["同一记录台、物件位置与灯光", "转报声只从扬声器传出", "无字幕、屏幕文字与配乐"],
                visual_strategy="generated_video",
                required_asset_roles=[{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]}],
                generated_video_rationale="调度对讲版 v5 对白母带：一次生成全部七句对白及 D1、D5 记录台画面")
    shot["duration_policy"] = {"mode": "fixed", "seconds": DURATION}
    for key in ("occurrence_id", "adaptation_reason"):
        row.pop(key, None)
    paths = {k: [p for f in fields for p in leaves(gi[f], "generation_intent." + f)] for k, fields in CATEGORIES.items()}
    fragments = {k: [lines[i] for i in idx] for k, idx in FRAGMENT_LINES.items()}
    observations = {
        "identity": "董文慧与身份参考一致，灰褐连帽外套、低马尾，没有新增人物或换脸",
        "action": "听完第一句才打字、在记录本写下一行笔停住、拉麦克风按键问话后松键、听回答时看扬声器",
        "camera": "一个连续镜头从中景缓慢推近到中近景（脸、双手、记录本），不切镜、不越轴；问话时脸在画内",
        "performance": "平静克制，不惊慌；问话平淡",
        "space": "同一记录台与物件位置，扬声器在桌面左角",
        "sound": "七句对白完整且顺序正确：转报为扬声器音质男声，她是室内干声；第一句时没有键盘声；“暂无报告”在片尾前说完；无配乐",
        "art": "真人摄影质感、雨夜灯光连续，无慢动作、闪屏、字幕或屏幕文字",
    }
    for key in ("source_contract", "actual_model_inputs_planned", "review_only_inputs",
                "required_later_assembly_junction", "qualification_scope", "accepted_source",
                "original_720p_observations"):
        data.pop(key, None)
    data.update(objective="失帧冷开场调度对讲版对白母带：记录台接报、计数与站台点名",
                images=images,
                characters=[{"character_id": CHAR, "name": "董文慧", "identity": "夜间应急文字记录员",
                             "appearance_bible": "以身份参考为脸；灰褐连帽外套、深灰内搭、低马尾",
                             "reference_asset_ids": ["M1-identity"]}],
                scene_images=["M1-env", "M1-k1", "M1-k2", "M1-k4"], observations=observations, paths=paths, fragments=fragments,
                intent_sha256=canonical_sha256(gi),
                coverage={"path": rel(COVERAGE), "sha256": sha(COVERAGE), "coverage_hash": coverage_hash,
                          "unit_id": "D1-record-desk"},
                preview_approval={"path": rel(OUT / "preview-approval.json"), "approval_hash": approval_hash},
                scene={"scene_id": "record-desk", "location": "夜间应急记录室", "mood": "报告一件件累积"})
    write(OUT / "row.json", row)
    write(OUT / "data.json", data)
    (OUT / "native-prompt.zh.txt").write_text(prompt + "\n")
    return {"shot": "M1", "duration": DURATION, "prompt_chars": len(prompt), "images": len(images),
            "approval_hash": approval_hash}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False))
