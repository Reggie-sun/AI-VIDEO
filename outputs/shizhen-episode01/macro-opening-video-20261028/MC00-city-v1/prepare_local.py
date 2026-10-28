"""Write MC00 source-bound authoring data only. No browser, provider or run writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import GenerationIntent


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LABEL = "MC00-CITY"
FIRST = "MC00-first-eave"
LAST = "MC00-last-approved-MC01-frame0"
PROMPT = (HERE / "native-prompt.zh.txt").read_text().strip()
SHOTBOARD = ROOT / "outputs/shizhen-episode01/opening-A-revision-20261026/production-inputs/MACRO-SHOTBOARD-20261027.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name: str, value: object) -> None:
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source_image(asset_id: str, relative: str, role: str, expected: str) -> dict:
    path = ROOT / relative
    assert sha(path) == expected
    with Image.open(path) as image:
        width, height = image.size
        assert image.format == "PNG"
    record = {
        "schema_version": "agent-generated-image-observation/1",
        "source_path": relative,
        "sha256": sha(path),
        "size_bytes": path.stat().st_size,
        "width": width,
        "height": height,
        "reference_role": role,
        "platform_admission": "NOT_EVALUATED",
        "semantic_review": "Static authoring source only; no generated video or junction acceptance",
    }
    if role == "first_frame":
        record.update(
            generator="builtin image_gen.imagegen",
            tool_identity_claim="builtin only; exact internal model not exposed",
            source_intent_path="referces/shizhen/macro-opening-20261027/MC00-photoreal-20261027/02-eave-start-intent.json",
            fictional_characters=True,
        )
        record["source_intent_sha256"] = sha(ROOT / record["source_intent_path"])
        prior_intent = json.loads((ROOT / record["source_intent_path"]).read_text())
        assert prior_intent["status"] == "KNOWN_OUTPUT_SAVED"
        assert prior_intent["output_sha256"] == expected
        tool = {"name": "builtin-imagegen", "version": "tool-interface"}
    else:
        record.update(
            generator="exact decoded video frame extraction; existing PNG reused",
            source_video_path="outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4",
            source_video_sha256="b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d",
            source_frame_index=0,
            source_fps_numerator=24,
            source_fps_denominator=1,
            inherited_acceptance_scope="Exact original municipal video only; not this future MC00 output",
        )
        assert sha(ROOT / record["source_video_path"]) == record["source_video_sha256"]
        tool = {"name": "exact-video-frame-extraction", "version": "existing-frame-copy-v1"}
    name = "reference-" + role + "-source.json"
    dump(name, record)
    return {
        "asset_id": asset_id,
        "node_id": asset_id + "-local-authoring-node",
        "resource_id": asset_id + "-local-source",
        "path": str(path),
        "usage_license": "Task-owned Shizhen reference; director-declared local copy, not platform adoption",
        "generated_source": {
            "record_path": str((HERE / name).relative_to(ROOT)),
            "record_sha256": sha(HERE / name),
            "tool": tool,
        },
    }


def main() -> None:
    assert not any("A" <= char <= "Z" or "a" <= char <= "z" for char in PROMPT)
    assert len(PROMPT) <= 500
    images = [
        source_image(FIRST, "referces/shizhen/macro-opening-20261027/MC00-photoreal-20261027/02-eave-start-v1.png",
                     "first_frame", "38af8b4fa48bba43acc98df2740367669290b3c257f1e2b7c917890dd7fb9b61"),
        source_image(LAST, "referces/shizhen/macro-opening-20261027/full-opening-references-20261027/MC01-normal.png",
                     "last_frame", "a2cef0e9ff42796e09e72105bb04ea336149b4551a20dc767ffdd3179910eeed"),
    ]
    parts = PROMPT.splitlines()
    start = "室外屋檐滴雨近景，建筑外转角部分遮挡城市，但始终可见城市一角"
    close = "相机已完全停稳，正常市政作业的构图、透视、门位、工人姿态与灯态落到已认可MC01第0帧"
    intent = {
        "open_state": {"kind": "typed_text", "state_text": start, "required_change": False},
        "close_state": {"kind": "typed_text", "state_text": close, "required_change": True},
        "identity_continuity": {"character_ids": ["municipal-worker"], "preservation": "exact", "allowed_variation": []},
        "scene_continuity": {
            "scene_id": "city-eave-to-municipal",
            "time_of_day": "同一雨夜",
            "mood": "城市正常运转，异常尚未发生",
            "state_constraints": ["同一主路与沿途住宅、站棚及市政入口", "工作灯亮，工人不提前按停", "尾态以已认可MC01第0帧为唯一锚点"],
        },
        "space_continuity": {"subject_position": "从建筑室外屋檐，经开放道路上方到市政牵引线街侧",
                             "screen_direction": "沿同一主路纵深前进下降，再逐渐收至市政观察侧",
                             "crossing_policy": "不穿墙、不穿玻璃、不跨钢索、不翻轴"},
        "axis_continuity": {"camera_axis": "道路纵深到市政牵引线街侧，与尾帧同侧",
                            "framing_continuity": "屋檐近景、城市展开、沿路下降及市政落点连成一条可追踪路径",
                            "crossing_policy": "全镜不中断，不用掠黑、满屏遮挡或叠化藏切点"},
        "subject_action": {"start_state": start, "progression": "\n".join(parts[:3]),
                           "endpoint": {"state_text": close, "required_change": True}},
        "motion_envelope": {"onset": "沿檐口横移越过建筑外转角，城市从遮挡后显露",
                            "peak": "沿同一主路缓弧前进下降，住宅与站棚依次显露",
                            "settle": "钢索入前景，逐渐减速并完全停稳于市政尾态",
                            "direction": "室外侧移后沿道路纵深下降，收至街侧观察位",
                            "amplitude_class": "从屋檐近景到城市，再到正常市政场地，保持可信尺度"},
        "pacing": {"cadence": "揭示后下降、近街面逐渐减速，留出认路和看清作业关系的时间",
                   "tempo_class": "正常原速，不为凑时长加速、冻结或删事件", "shot_duration_seconds": 20},
        "camera_intent": {"movement": "一条连续的屋檐横移揭示、沿路缓弧下降及街侧减速落点",
                          "stability": "平稳连续，末段完全停稳", "framing_intent": "每次移动对应一次可见揭示，路网与地标可追踪",
                          "expression_strength": "semantic_prompt_allowed"},
        "camera_endpoint": {"start_framing": start, "end_framing": close, "position_lock": False, "orientation_lock": False},
        "performance_intent": {
            "trigger": "市政作业仍正常，异常尚未发生", "visible_response": "接近后才看清工人正常作业，不提前按停或惊恐",
            "gaze_target": "工人关注原作业设备", "body_behavior": "原位置正常作业，不闯入钢索路径",
            "hand_behavior": "不演按停与收手，终态姿势以尾帧为准", "terminal_performance_state": "尾帧正常作业、灯亮，尚未完成停止操作",
            "character_directions": [{"character_id": "municipal-worker", "screen_identity": "尾帧中黄色安全帽、深蓝工装的同一作业工人",
                "role": "supporting", "visibility": "visible", "beats": [{"phase": "throughout", "trigger": "正常市政作业，接近后人物才可辨",
                    "emotion": "平常专注", "intensity": "subtle", "facial_expression": "自然专注，不提前惊恐", "gaze_target": "作业设备",
                    "breathing": "自然平稳", "body_behavior": "留在原作业位置，末态与尾帧一致，不重复按停或收手"}]}],
        },
        "visual_treatment": {"medium_look": "雨夜真人电影摄影质感", "palette": "深蓝灰夜色、冷白路灯与少量暖窗及作业灯",
                             "material_treatment": "真实湿金属檐口、旧住宅、棚柱、沥青及市政机械",
                             "prohibited_visual_drift": ["建筑扭曲、鱼眼或突然变焦", "分格、叠化、隐切、冻结或加速", "新增对白、片名、字幕或音乐"]},
        "lighting_intent": {"motivated_source": "城市路灯、窗户与市政工作灯", "direction": "同一雨夜实用照明，尾态继承MC01第0帧",
                            "exposure_priority": "近处雨滴、路网地标和末段钢索设备人物关系可读", "continuity_state": "工作灯始终亮，不提前断控"},
        "ambience_intent": {"environment_bed": "近檐滴水退远、城市交通接管、现场马达逐渐清楚，结尾对齐MC01既有现场声",
                            "foley_cues": ["檐口雨滴", "轮胎压水", "正常市政马达与机械声"], "explicitly_silent": False},
        "dialogue_intent": {"mode": "none", "lip_sync_required": False},
        "music_intent": {"mode": "none"},
        "primary_camera_motion": {"movement_kind": "crane_down", "direction": "down", "amplitude_class": "pronounced", "speed_class": "moderate",
                                  "start_motion_state": "in_motion", "end_motion_state": "settled"},
        "camera_subject_relation": {"subject_id": "city-eave-to-municipal", "relation_kind": "reveal",
                                    "start_relation": "屋檐遮挡与城市一角同框", "end_relation": "钢索、工人、控制盒和铁门关系清楚，构图为批准尾帧"},
    }
    intent = GenerationIntent.model_validate(intent).model_dump(mode="json")
    compatibility = {"lane": "fl2va", "first_anchor_id": FIRST, "last_anchor_id": LAST,
        "same_subject_scale": None, "composition_compatible": None, "screen_order_compatible": None,
        "axis_compatible": None, "camera_path_reachable": None, "character_prop_state_reachable": None,
        "action_endpoint_reachable": None, "available_duration_seconds": 20}
    row = {
        "shot": {"shot_id": LABEL, "scene_id": "city-eave-to-municipal", "storyboard_beat_id": "one-city-one-continuous-move",
            "intent": PROMPT, "dialogue": "", "duration_policy": {"mode": "fixed", "seconds": 20}, "character_ids": ["municipal-worker"],
            "continuity_constraints": ["MC00独立内部一镜到底，MC01–06及B6不重编成一镜", "屋檐横移真实揭示，同一主路与住宅站棚可追踪",
                "不穿墙、不跨牵引线、不翻轴、不提前按停", "方案A尾态只用已认可MC01精确第0帧，旧近似末态降为路线参考",
                "原市政与B6不重生成、不重剪；接缝只处理MC00一侧", "完整原速声画和接点另行验收"],
            "visual_strategy": "generated_video", "generated_video_rationale": "完整连续城市揭示与空间下降须由一次20秒源承载，不能为15秒阈值拆段掩切",
            "required_asset_roles": [{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]},
                {"role": "first_frame", "asset_ids": [FIRST], "allowed_asset_types": ["image"]},
                {"role": "last_frame", "asset_ids": [LAST], "allowed_asset_types": ["image"]}]},
        "generation": {"references": [{"role": "approved_keyframe", "asset_id": FIRST}, {"role": "last_frame", "asset_id": LAST}],
            "generation_intent": intent, "conditioning_compatibility": compatibility,
            "intent_evidence": {"character_action_required": False, "state_change_required": True, "subject_motion_directive_present": True},
            "output_need": {"timing_mode": "content_driven", "duration_seconds": 20, "geometry_policy": "adaptive", "aspect_ratio": "16:9", "fps": None, "container_mime": "video/mp4"},
            "audio_need": "required", "quality_need": {"objective_tier": "preview"}},
        "composition": {"muted": False, "source_audio_policy": "KEEP"},
    }
    observations = {
        "identity": "接近市政后同一黄帽深蓝工装工人，与尾帧位置及造型一致，无新增故事人物",
        "action": "屋檐横移揭示城市，再沿同一主路缓弧下降，住宅和站棚依次真正显露，钢索入前景后交给作业",
        "camera": "全镜连续无切点、叠化或冻结，下降自然，末段逐渐减速到完全停稳，构图与透视收至批准尾帧",
        "performance": "正常作业状态，工人不提前按停、收手或惊恐；门正常缓慢右移，灯始终亮",
        "space": "道路地标可追踪，建筑硬几何稳定，不穿墙或跨钢索翻轴，末态设备、门位、工人姿态和灯态对应MC01第0帧",
        "art": "同一写实雨夜，真实建筑与设备尺度，不用模糊、雾或掠黑掩盖空间，不新增片名字幕或奇观",
        "sound": "原生滴水随远离退去、城市交通接管、现场马达渐清，无对白旁白或音乐；与MC01既有声音的原速接点另验",
    }
    paths = {
        "identity": ["generation_intent.identity_continuity.character_ids.0", "generation_intent.identity_continuity.preservation"],
        "action": ["generation_intent.subject_action.progression", "generation_intent.subject_action.endpoint.state_text"],
        "camera": ["generation_intent.camera_intent.movement", "generation_intent.camera_endpoint.end_framing", "generation_intent.primary_camera_motion.end_motion_state"],
        "performance": ["generation_intent.performance_intent.hand_behavior", "generation_intent.performance_intent.terminal_performance_state"],
        "space": ["generation_intent.space_continuity.crossing_policy", "generation_intent.axis_continuity.camera_axis", "generation_intent.close_state.state_text"],
        "art": ["generation_intent.visual_treatment.medium_look", "generation_intent.visual_treatment.prohibited_visual_drift.0"],
        "sound": ["generation_intent.ambience_intent.environment_bed", "generation_intent.dialogue_intent.mode", "generation_intent.music_intent.mode"],
    }
    fragments = {"identity": [parts[2], parts[3]], "action": parts[:3], "camera": parts[:2] + [parts[3]],
                 "performance": [parts[2], parts[3]], "space": parts[:3] + [parts[3]], "art": [parts[0], parts[1]], "sound": [parts[3]]}
    data = {"objective": "MC00城市独立长镜头完整揭示城市空间，按方案A无可见跳动接入已认可MC01第0帧；不重做市政或B6",
        "images": images, "characters": [{"character_id": "municipal-worker", "name": "市政工人", "identity": "已认可MC01第0帧中的同一个作业工人",
            "appearance_bible": "黄色安全帽、深蓝工装及尾帧所见原造型；不从文字另造面孔", "reference_asset_ids": [LAST]}],
        "scene_images": [FIRST, LAST], "observations": observations, "paths": paths, "fragments": fragments,
        "intent_sha256": canonical_sha256(intent),
        "source_contract": {"path": str(SHOTBOARD.relative_to(ROOT)), "sha256": sha(SHOTBOARD), "source_revision": "59e80dde2e5e91bf118109fe58bcf26be8535828", "section": "MC00 — One City, One Continuous Move", "landing_plan": "A"},
        "actual_model_inputs_planned": [FIRST, LAST], "review_only_inputs": ["MC00 city reveal and descent images", "local continuous Blender rehearsal"],
        "required_later_assembly_junction": "MC00→原MC01 exact0帧：原速检查位置、门速、车流雨线、姿态与声音；仅MC00侧处理接缝，重复同构帧只留一帧",
        "qualification_scope": "one unqualified 480p preview, not Production acceptance or 1080p pixel match"}
    dump("row.json", row)
    dump("data.json", data)
    dump("conditioning-review-pending.json", {"status": "NOT_EVALUATED_BLOCKS_EXECUTION", "evidence": compatibility,
        "reason": "首帧为屋檐近景、尾帧为市政中远景，不能以模板自行断言same_subject_scale及可达性全True；须现有conditioning owner作真实审查或返回契约缺口",
        "must_not_do": ["伪填全True", "移除rich camera intent以旁路conditioning", "以两张静态端点代替连续路径证明"]})
    dump("live-profile-required.json", {"status": "MISSING_CURRENT_NATIVE_BINDING", "selected_fixed_fields": {"model_id": "seedance_2.5", "input_mode": "first_last_frame", "duration_seconds": 20, "resolution": "480p", "aspect_ratio": "16:9", "native_audio": True},
        "required_current_fields": ["account_sha256", "project_id", "node_id", "benefit_amount", "benefit_type", "credit_upper_bound", "native_mode3_current_config_identity", "native_quote_and_budget_reservation"],
        "new_attempt_id_to_allocate": "Parent must allocate one new exact MC00 attempt through current owner",
        "suggested_new_root": "runs/shizhen-macro-opening-20261028/MC00-city-v1",
        "operator_bound_source_only": "outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-v1/operator-bound.json",
        "historical_operator_per_call_upper_bound_CRD": 1500,
        "not_a_new_quote_or_authorization": True, "planned_new_submit_count": 1, "historical_known_macro_submits": 6,
        "old_downstairs_door_unit_not_reallocated": True, "do_not_copy_old_attempt_permit_or_profile": True})
    print(json.dumps({"written": True, "prompt_chars": len(PROMPT), "actual_inputs": 2, "video_calls": 0, "run_writes": 0, "status": "LOCAL_DRAFT_BLOCKED_ON_CONDITIONING_AND_LIVE_BINDING"}))


if __name__ == "__main__":
    main()
