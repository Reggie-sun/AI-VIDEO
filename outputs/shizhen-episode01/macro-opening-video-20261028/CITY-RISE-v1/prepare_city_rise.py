"""CITY-RISE v1: municipal last frame -> fast rise, rooftop sweep, dive -> approved B6 frame 0.

Local authoring only: no browser, provider or run writes. Reuses the v4 authored
row/data shape (full native leaf mapping) and swaps anchors, prompt, characters,
camera intent and duration. Dispatch-radio voice and captions are post layers,
not part of this video request.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.video_requirement import (
    GenerationIntent, ScaleTransitionEvidence, scale_transition_camera_intent_hash,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
V4 = HERE.with_name("MC00-city-v4")
LABEL = "CITY-RISE"
DURATION = 20
FIRST = "CITY-RISE-first-municipal-last"
LAST = "CITY-RISE-last-B6-frame0"
MUNICIPAL = ("outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4",
             "b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d", 163)
B6_EVENT = ("runs/shizhen-fusion-B-motion-20261027/render-ASSEMBLY-B6/source/assets/587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc.mp4",
            "587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc", 0)
B6_DELIVERY = ("outputs/shizhen-episode01/fusion-B-motion-20261027/variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4",
               "d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a")
PROMPT = (HERE / "native-prompt.zh.txt").read_text().strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def dump(name: str, value: object) -> None:
    with (HERE / name).open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def anchor(asset_id: str, png: Path, role: str, source: tuple[str, str, int], scope: str) -> dict:
    video, video_sha, index = source
    assert sha(ROOT / video) == video_sha
    with Image.open(png) as image:
        assert image.size == (1920, 1080) and image.format == "PNG"
    record = {"schema_version": "agent-generated-image-observation/1", "source_path": rel(png), "sha256": sha(png),
              "size_bytes": png.stat().st_size, "width": 1920, "height": 1080, "reference_role": role,
              "platform_admission": "NOT_EVALUATED", "generator": "exact decoded video frame extraction (ffmpeg -vsync 0 select)",
              "source_video_path": video, "source_video_sha256": video_sha, "source_frame_index": index,
              "source_fps_numerator": 24, "source_fps_denominator": 1, "inherited_acceptance_scope": scope,
              "semantic_review": "Exact approved-footage frame; no repaint, crop or scale"}
    name = "reference-" + role + "-source.json"
    dump(name, record)
    return {"asset_id": asset_id, "node_id": asset_id + "-local-authoring-node", "resource_id": asset_id + "-local-source",
            "path": str(png), "usage_license": "Task-owned Shizhen approved-footage frame; local copy, not platform adoption",
            "generated_source": {"record_path": rel(HERE / name), "record_sha256": sha(HERE / name),
                                 "tool": {"name": "exact-video-frame-extraction", "version": "ffmpeg-select-v1"}}}


def route_and_review(first: Path, last: Path) -> None:
    dump("route-design.json", {
        "kind": "authored-route-design/1", "status": "AUTHORED_DESIGN_NOT_MEASURED", "duration_seconds": DURATION,
        "beats": [
            {"phase": "rise", "relative_span": "前约四分之一", "motion": "从铁门钢索近景急速向后上方拉起至楼顶以上",
             "visible_change": "作业现场缩成街角灯点"},
            {"phase": "sweep", "relative_span": "中段约四成", "motion": "贴楼顶高度向前横掠",
             "visible_change": "主路车流、旧住宅楼梯窗、红十字医院、九层旧楼与高楼群依次掠过"},
            {"phase": "dive", "relative_span": "后约三成", "motion": "前倾俯冲并加速扎向站棚",
             "visible_change": "玻璃站棚和棚下两人迅速放大"},
            {"phase": "slam_stop", "relative_span": "最后约半秒", "motion": "猛然刹停后静止", "visible_change": "收至B6第0帧"}],
        "audio_design": "调度对讲与字幕为后期层，台词见 dispatch-script.json；本请求原生声只要雨、风、车流",
        "limits": "地理与高度为设计估计；模型路径服从待exact MP4验证"})
    with (HERE / "pre-generation-feasibility.md").open("x") as handle:
        handle.write(f"""# CITY-RISE v1 Pre-generation Feasibility

范围：仅前期作者审查，不是视频或接点验收。

- 首帧：已认可市政片最后一帧（第163帧）原样解码 `anchors/municipal-last-f163.png`，SHA `{sha(first)}`；市政片 SHA `{MUNICIPAL[1]}`。
- 尾帧：已认可B6所用事件源第0帧（无字幕层）`anchors/b6-event-render-f0.png`，SHA `{sha(last)}`；事件源 SHA `{B6_EVENT[1]}`。
- 两端都是固定机位：起点由静止急拉，终点刹停后静止，接B6稳定机位，避免v4末段漂移骤停。
- 首尾景别、地点完全不同，same_subject_scale=False；中段城市为新设计，不声称与已有素材测绘对应。
- 罗敏、高峥身份只由B6第0帧锚定，中段远景不另造面孔；市政工人只在首帧出现。
- 未证明：拉升/横掠/俯冲速度观感、建筑稳定、站棚与人物身份连续、刹停精度与声音，全部待exact MP4验证。
""")


def derive(first: Path, last: Path) -> tuple[dict, dict]:
    row = json.loads((V4 / "row.json").read_text())
    data = json.loads((V4 / "data.json").read_text())
    parts = PROMPT.splitlines()
    assert len(parts) == 4
    start = "已认可市政片末帧：灰色铁门、牵引耳与绷紧钢索近景，工人在左后方，固定机位"
    close = "相机刹停后静止于已认可B6第0帧：玻璃站棚正前方，左侧中年男人低头，右侧短发女人打电话"
    gi = row["generation"]["generation_intent"]
    gi["open_state"]["state_text"] = start
    gi["close_state"]["state_text"] = close
    gi["identity_continuity"]["character_ids"] = ["gao-zheng", "luo-min"]
    gi["scene_continuity"].update(scene_id="municipal-to-station-city", mood="城市照常运转，异常被当作日常报告",
                                  state_constraints=["起点为市政原片末态，不重演按停或断电", "中段为同一雨夜城市", "终点以B6第0帧为唯一锚点"])
    gi["space_continuity"].update(subject_position="从市政铁门前，升到楼顶以上，横掠城市后俯冲到站棚正前方",
                                  screen_direction="后拉上升，再向前横掠，最后前倾俯冲正对站棚",
                                  crossing_policy="不穿墙、不穿玻璃、不穿棚顶")
    gi["axis_continuity"].update(camera_axis="终点正对站棚，与B6第0帧同一观察侧",
                                 framing_continuity="铁门近景、城市高空、站棚正面连成一条可追踪路径",
                                 crossing_policy="全镜不中断，不用掠黑、满屏遮挡或叠化藏切点")
    gi["subject_action"].update(start_state=start, progression="\n".join(parts[:3]))
    gi["subject_action"]["endpoint"]["state_text"] = close
    gi["motion_envelope"].update(onset="从铁门钢索近景急速向后上方拉起", peak="贴楼顶高度横掠城市，随后前倾俯冲加速",
                                 settle="最后约半秒猛然刹停并静止于尾帧", direction="后拉上升、向前横掠、俯冲下降",
                                 amplitude_class="从地面近景到楼顶高空再回到地面中景，保持可信尺度")
    gi["pacing"].update(cadence="拉升约四分之一、横掠约四成、俯冲约三成、最后约半秒刹停",
                        tempo_class="紧凑有力，原速，不冻结或插切", shot_duration_seconds=float(DURATION))
    gi["camera_intent"].update(movement="一条连续的急速拉升、高空横掠、俯冲刹停", stability="运动有力但不抖，刹停后完全静止",
                               framing_intent="每段运动对应一次城市层级变化，终点构图为批准尾帧")
    gi["camera_endpoint"].update(start_framing=start, end_framing=close)
    gi["primary_camera_motion"].update(movement_kind="crane_up", direction="up", amplitude_class="pronounced", speed_class="fast",
                                       start_motion_state="stationary", end_motion_state="settled")
    gi["camera_subject_relation"].update(subject_id="municipal-to-station-city", relation_kind="reveal",
                                         start_relation="铁门钢索占满近景", end_relation="站棚与两人正面中景，构图为批准尾帧")
    perf = gi["performance_intent"]
    perf.update(trigger="站台两人只是在等车，异常尚未发生", visible_response="俯冲接近后才看清两人，男人低头、女人打电话",
                gaze_target="男人看地面，女人看前方", body_behavior="两人原地站立，不走动", hand_behavior="女人右手持手机贴耳，男人手插口袋",
                terminal_performance_state="尾帧两人姿态与B6第0帧一致")
    d0 = perf["character_directions"][0]
    d0.update(character_id="luo-min", screen_identity="B6第0帧右侧穿墨绿色外套打电话的短发年轻女人", role="supporting")
    d0["beats"][0].update(trigger="站台等车，接近后才可辨", emotion="平常", facial_expression="自然", gaze_target="前方",
                          breathing="自然平稳", body_behavior="原地打电话，末态与尾帧一致")
    d1 = json.loads(json.dumps(d0))
    d1.update(character_id="gao-zheng", screen_identity="B6第0帧左侧戴眼镜、穿棕色夹克、斜挎包的中年男人")
    d1["beats"][0].update(gaze_target="地面", body_behavior="原地低头站立、手插口袋，末态与尾帧一致")
    perf["character_directions"] = [d1, d0]
    gi["visual_treatment"].update(material_treatment="真实湿金属铁门与钢索、旧楼、楼顶、沥青路面与玻璃站棚",
                                  prohibited_visual_drift=["建筑扭曲、鱼眼或突然变焦", "分格、叠化、隐切、冻结", "新增对白、片名、字幕或音乐"])
    gi["lighting_intent"].update(motivated_source="路灯、窗户、医院红十字灯与站棚暖灯", direction="同一雨夜实用照明，尾态继承B6第0帧",
                                 exposure_priority="城市层次与站棚两人可读", continuity_state="站棚灯始终亮")
    gi["ambience_intent"].update(environment_bed="雨声，拉升风声增大，高处车流低鸣，俯冲风声呼啸，刹停后只剩站台雨声",
                                 foley_cues=["雨声", "风声", "城市车流"])
    intent = GenerationIntent.model_validate(gi).model_dump(mode="json")
    row["generation"]["generation_intent"] = intent
    row["generation"]["references"] = [{"role": "approved_keyframe", "asset_id": FIRST}, {"role": "last_frame", "asset_id": LAST}]
    row["generation"]["output_need"]["duration_seconds"] = DURATION
    shot = row["shot"]
    shot.update(shot_id=LABEL, scene_id="municipal-to-station-city", storyboard_beat_id="city-rise-dispatch", intent=PROMPT,
                character_ids=["gao-zheng", "luo-min"],
                continuity_constraints=["承接已认可市政原片末帧，不重生成或重剪市政", "一镜到底：拉升、横掠、俯冲、刹停",
                                        "终点为已认可B6第0帧，B6原片不改", "调度对讲与字幕为后期层，不进入视频请求",
                                        "完整原速声画和两个接点另行验收"],
                generated_video_rationale="异常之后拉开城市并落到站台，由一次20秒源承载，不拆段掩切")
    shot["duration_policy"]["seconds"] = DURATION
    shot["required_asset_roles"] = [{"role": "primary_visual", "asset_ids": [], "allowed_asset_types": ["video"]},
                                    {"role": "first_frame", "asset_ids": [FIRST], "allowed_asset_types": ["image"]},
                                    {"role": "last_frame", "asset_ids": [LAST], "allowed_asset_types": ["image"]}]

    data["objective"] = "市政异常之后急速拉开城市并俯冲落到站台，接入已认可B6第0帧；调度对讲与字幕后期叠加；不重做市政或B6"
    data["images"] = [anchor(FIRST, first, "first_frame", MUNICIPAL, "Exact approved municipal video only"),
                      anchor(LAST, last, "last_frame", B6_EVENT, "Exact approved B6 event source only")]
    data["characters"] = [
        {"character_id": "gao-zheng", "name": "高峥", "identity": "已认可B6第0帧左侧戴眼镜的中年男人",
         "appearance_bible": "眼镜、棕色夹克、斜挎包，按B6原造型；不从文字另造面孔", "reference_asset_ids": [LAST]},
        {"character_id": "luo-min", "name": "罗敏", "identity": "已认可B6第0帧右侧打电话的短发年轻女人",
         "appearance_bible": "短发、墨绿色外套、手机，按B6原造型；不从文字另造面孔", "reference_asset_ids": [LAST]}]
    data["scene_images"] = [FIRST, LAST]
    if "generation_intent.identity_continuity.character_ids.1" not in data["paths"]["identity"]:
        data["paths"]["identity"].append("generation_intent.identity_continuity.character_ids.1")
    base = "generation_intent.performance_intent.character_directions."
    for path in list(data["paths"]["performance"]):
        if path.startswith(base + "0."):
            twin = base + "1." + path[len(base) + 2:]
            if twin not in data["paths"]["performance"]:
                data["paths"]["performance"].append(twin)
    for key, indices in {"identity": [2, 3], "action": [0, 1, 2], "camera": [0, 1, 3], "performance": [2, 3],
                         "space": [0, 1, 2, 3], "art": [0, 1, 2, 3], "sound": [3]}.items():
        data["fragments"][key] = [parts[i] for i in indices]
    data["observations"] = {
        "identity": "落地后高峥与罗敏的位置、造型与B6第0帧一致，无新增人物",
        "action": "从市政铁门急速拉升，高空横掠城市，再俯冲扎向站棚",
        "camera": "全镜连续无切点、叠化或冻结；运动紧凑有力，最后约半秒刹停并静止于批准尾帧",
        "performance": "站台两人原地等车，男人低头、女人打电话，末态与B6第0帧一致",
        "space": "建筑硬几何稳定，不穿墙、玻璃或棚顶；终点与B6第0帧同一观察侧",
        "art": "同一写实雨夜，真实建筑与设备尺度，不新增片名字幕或奇观",
        "sound": "原生雨、风、车流随运动变化，无对白旁白或音乐；调度对讲后期另验"}
    data["intent_sha256"] = canonical_sha256(intent)
    data["source_contract"] = {"path": rel(HERE / "README.md"), "section": "CITY-RISE dispatch redesign",
                               "user_quotes": ["我覺得這個宏觀開始的內容是不是就要改", "同時這個時候要有聲音和字幕同時介紹異常", "做的我看下"]}
    data["actual_model_inputs_planned"] = [FIRST, LAST]
    data["review_only_inputs"] = ["dispatch-script.json (post layer, not a model input)", "route-design.json"]
    data["required_later_assembly_junction"] = "市政末帧→CITY-RISE首帧、CITY-RISE末帧→B6第0帧：原速检查运动、人物、声音；重复同构帧只留一帧"
    data["qualification_scope"] = "one unqualified 20s 480p preview, not Production acceptance"
    return row, data


def seal(row: dict, first: Path, last: Path) -> None:
    intent = GenerationIntent.model_validate(row["generation"]["generation_intent"])
    specs = [("first-anchor", "anchor_geometry_review", first), ("last-anchor", "anchor_geometry_review", last),
             ("anchor-review", "anchor_geometry_review", HERE / "pre-generation-feasibility.md"),
             ("route", "trajectory", HERE / "route-design.json")]
    sources = [{"source_id": k, "kind": kind, "evidence_ref": rel(p), "sha256": sha(p)} for k, kind, p in specs]
    findings = [
        {"finding_id": "anchor_correspondence", "verdict": "PASS", "source_ids": ["anchor-review", "first-anchor", "last-anchor"],
         "rationale": "首尾均为已认可成片原样解码帧，两端固定机位；中段为新设计城市，用拉升与俯冲连接两个地点，未声称测绘对应。"},
        {"finding_id": "continuous_camera_path", "verdict": "PASS", "source_ids": ["anchor-review", "route"],
         "rationale": "作者路线为后拉上升、楼顶高度横掠、俯冲刹停，不要求穿墙或穿棚；实际服从待exact MP4验证。"},
        {"finding_id": "duration_reachable", "verdict": "PASS", "source_ids": ["route"],
         "rationale": "20秒按约四分之一拉升、四成横掠、三成俯冲与最后约半秒刹停分配；设计估计，非实测。"},
        {"finding_id": "scale_fov_continuity", "verdict": "PASS", "source_ids": ["anchor-review", "first-anchor", "last-anchor", "route"],
         "rationale": "首尾景别和地点均不同，same_subject_scale=False；景别变化由真实位移产生，不以变焦跳转或隐切替代。"}]
    evidence = ScaleTransitionEvidence.create(first_anchor_id=FIRST, first_anchor_sha256=sources[0]["sha256"],
        last_anchor_id=LAST, last_anchor_sha256=sources[1]["sha256"], camera_intent_hash=scale_transition_camera_intent_hash(intent),
        available_duration_seconds=float(DURATION), sources=sources, findings=findings)
    compat = row["generation"]["conditioning_compatibility"]
    compat.update(first_anchor_id=FIRST, last_anchor_id=LAST, available_duration_seconds=DURATION, same_subject_scale=False,
                  composition_compatible=True, screen_order_compatible=True, axis_compatible=True, camera_path_reachable=True,
                  character_prop_state_reachable=True, action_endpoint_reachable=True, scale_transition=evidence.model_dump(mode="json"))
    dump("conditioning-review.json", {"scope": "PRE_GENERATION_AUTHORED_FEASIBILITY_ONLY", "evidence": compat,
                                      "actual_motion_and_sound": "NOT_EVALUATED", "human_acceptance": "NOT_EVALUATED"})


def operator_bound() -> None:
    prior = json.loads((V4 / "operator-bound.json").read_text())
    v4 = load_production_project(ROOT / "runs/shizhen-macro-opening-20261028/MC00-city-v4/project.yaml")
    attempts = [a for a in v4.manifest.attempts if a.operation == "video_generation"]
    assert len(attempts) == 1 and attempts[0].video_generation_state.fetch_receipt is not None
    a = attempts[0]
    assert a.status.value not in {"outcome_unknown", "interrupted"}
    ancestors = prior["ancestors"] + [{"root": "runs/shizhen-macro-opening-20261028/MC00-city-v4", "attempt_id": a.attempt_id,
        "known_fetched": True, "artifact_sha256": a.video_generation_state.fetch_receipt.artifact_sha256,
        "manifest_sha256": sha(ROOT / "runs/shizhen-macro-opening-20261028/MC00-city-v4/state/manifest.json")}]
    assert len(ancestors) == 8
    dump("historical-generation-audit.json", {"scope": "Eight macro submits; v3/v4 MC00 outcomes known and preserved",
        "unique_macro_attempts": 8, "items": ancestors,
        "unknown_other_history_preserved": prior["historical_unknown_attempts_preserved"], "new_macro_submissions": 0})
    readonly = json.loads((HERE / "native-readonly.json").read_text())
    now = datetime.now(timezone.utc)
    dump("operator-bound.json", {**prior, "authorization_quote": "做的我看下",
        "scope": "One CITY-RISE continuous20s480p first-last-frame native-audio preview; no further shots or activation",
        "predecessor_bound_path": rel(V4 / "operator-bound.json"), "predecessor_bound_sha256": sha(V4 / "operator-bound.json"),
        "failed_same_shot_gate_path": None, "failed_same_shot_gate_sha256": None,
        "issued_at": now.isoformat(), "expires_at": (now + timedelta(hours=2)).isoformat(),
        "max_submit_count": 1, "automatic_retries": 0,
        "macro_paid_submits_before": 8, "macro_cumulative_ceiling_after_authorized_unit": 9,
        "ancestors": ancestors, "current_quote_credits": readonly["quote"]["credits"], "quote_evidence": "native-readonly.json"})


def main() -> None:
    assert len(PROMPT) <= 500 and not any(c.isascii() and c.isalpha() for c in PROMPT)
    first = HERE / "anchors/municipal-last-f163.png"
    last = HERE / "anchors/b6-event-render-f0.png"
    route_and_review(first, last)
    row, data = derive(first, last)
    seal(row, first, last)
    dump("row.json", row)
    dump("data.json", data)
    operator_bound()
    print(json.dumps({"prompt_chars": len(PROMPT), "first_sha256": sha(first), "last_sha256": sha(last),
                      "duration": DURATION, "video_calls": 0, "run_writes": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
