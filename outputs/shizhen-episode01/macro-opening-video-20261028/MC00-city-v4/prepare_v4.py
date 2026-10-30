"""MC00 v4 redo: same-heading eave reveal + descent into approved MC01 frame 0.

Local authoring only: no browser, provider or run writes. Derives the v4 row/data
from the final v3 authored state, swapping in the new first frame, prompt, route
design and 16s duration; re-seals the prospective conditioning review.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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
V3 = HERE.with_name("MC00-city-v3")
DURATION = 16
FIRST = "MC00-first-eave"
LAST = "MC00-last-approved-MC01-frame0"
LAST_PATH = "referces/shizhen/macro-opening-20261027/full-opening-references-20261027/MC01-normal.png"
LAST_SHA = "a2cef0e9ff42796e09e72105bb04ea336149b4551a20dc767ffdd3179910eeed"
RAW = HERE / "codex-image/raw/first-frame-v2.png"
RAW_SHA = "a425fb681a075a09b4c5279437278c9a0a6dc54340433d54f93cf82fe6713268"
REJECTED = HERE / "codex-image/raw/first-frame-v1.png"
REJECTED_SHA = "d7cb20a6bb0cad075c9c0b1056e8525725c86fd70b6a54d60dd9172a46aa93e3"
PROMPT = (HERE / "native-prompt.zh.txt").read_text().strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def dump(name: str, value: object) -> None:
    with (HERE / name).open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(name: str, text: str) -> None:
    with (HERE / name).open("x") as handle:
        handle.write(text)


def codex_record() -> None:
    eave = ROOT / "referces/shizhen/macro-opening-20261027/MC00-reference-revision-20261028/02-eave-start-v1.png"
    calls = [
        {"id": "01-first-frame", "status": "KNOWN_OUTPUT", "prompt": "codex-image/01-first-frame-prompt.zh.txt",
         "prompt_sha256": sha(HERE / "codex-image/01-first-frame-prompt.zh.txt"),
         "task_wrapper": "codex-image/codex-task-1.md",
         "inputs": [{"role": "参考一 尾帧", "path": LAST_PATH, "sha256": sha(ROOT / LAST_PATH)},
                    {"role": "参考二 湿墙檐口质感", "path": rel(eave), "sha256": sha(eave)}],
         "output": rel(REJECTED), "sha256": sha(REJECTED), "width": 1672, "height": 941,
         "verdict": "FAIL: 主路、车流和天际线已在右半画面露出，揭示余地不足；主路在右与尾帧主路在左不一致"},
        {"id": "02-first-frame-repair", "status": "KNOWN_OUTPUT", "prompt": "codex-image/02-first-frame-repair-prompt.zh.txt",
         "prompt_sha256": sha(HERE / "codex-image/02-first-frame-repair-prompt.zh.txt"),
         "task_wrapper": "codex-image/codex-task-2.md",
         "inputs": [{"role": "参考一 尾帧", "path": LAST_PATH, "sha256": sha(ROOT / LAST_PATH)},
                    {"role": "参考二 上一版起幅（只取质感）", "path": rel(REJECTED), "sha256": sha(REJECTED)}],
         "output": rel(RAW), "sha256": sha(RAW), "width": 1672, "height": 941,
         "verdict": "SELECTED_STATIC_CANDIDATE: 湿墙约占左侧55%，主路和作业区被墙挡住，右侧只露旧住宅屋顶与远处高楼；静态审看，不代表视频通过"},
    ]
    assert calls[0]["sha256"] == REJECTED_SHA and calls[1]["sha256"] == RAW_SHA
    dump("codex-image/generation-record.json", {
        "purpose": "MC00 v4 first frame whose occlusion actually allows an eave reveal",
        "user_instruction": "直接重做,生圖調用codex",
        "provider": "codex exec (codex-cli 0.165.0) built-in image_gen",
        "max_calls": 3, "calls_used": 2, "actual_model_id": "NOT_EXPOSED", "actual_billing": "NOT_EXPOSED",
        "unknown_outcome_rule": "STOP; no retry or fallback", "calls": calls})


def normalize_first() -> Path:
    assert sha(RAW) == RAW_SHA
    out = HERE / "first-frame-1920x1080.png"
    ffmpeg = shutil.which("ffmpeg")
    subprocess.run([ffmpeg, "-v", "error", "-n", "-i", str(RAW), "-vf", "scale=1920:1080:flags=lanczos",
                    "-frames:v", "1", str(out)], check=True)
    with Image.open(out) as image:
        assert image.size == (1920, 1080) and image.format == "PNG"
    dump("input-raster-normalization.json", {
        "kind": "technical-input-raster-normalization/1", "source_path": rel(RAW), "source_sha256": RAW_SHA,
        "source_dimensions": [1672, 941], "output_path": rel(out), "sha256": sha(out), "size_bytes": out.stat().st_size,
        "width": 1920, "height": 1080, "operation": "FFmpeg Lanczos scale only; no crop/repaint/content insertion",
        "generator": "FFmpeg input preprocessing; not a new model image", "ffmpeg_executable": ffmpeg,
        "original_generation_record": rel(HERE / "codex-image/generation-record.json"),
        "original_preserved": True, "output_video_resolution_remains": "480p"})
    return out


def source_image(asset_id: str, path: Path, role: str) -> dict:
    with Image.open(path) as image:
        width, height = image.size
    record = {"schema_version": "agent-generated-image-observation/1", "source_path": rel(path), "sha256": sha(path),
              "size_bytes": path.stat().st_size, "width": width, "height": height, "reference_role": role,
              "platform_admission": "NOT_EVALUATED",
              "semantic_review": "Static authoring source only; no generated video or junction acceptance"}
    if role == "first_frame":
        normalization = json.loads((HERE / "input-raster-normalization.json").read_text())
        assert normalization["sha256"] == record["sha256"]
        record.update(generator="FFmpeg technical input-raster normalization", normalization=normalization,
                      original_codex_source=rel(HERE / "codex-image/generation-record.json"))
        tool = {"name": "ffmpeg-lanczos-input-normalization", "version": "configured-ffmpeg"}
    else:
        assert record["sha256"] == LAST_SHA
        record.update(generator="exact decoded video frame extraction; existing PNG reused",
                      source_video_path="outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4",
                      source_video_sha256="b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d",
                      source_frame_index=0, source_fps_numerator=24, source_fps_denominator=1,
                      inherited_acceptance_scope="Exact original municipal video only; not this future MC00 output")
        assert sha(ROOT / record["source_video_path"]) == record["source_video_sha256"]
        tool = {"name": "exact-video-frame-extraction", "version": "existing-frame-copy-v1"}
    name = "reference-" + role + "-source.json"
    dump(name, record)
    return {"asset_id": asset_id, "node_id": asset_id + "-local-authoring-node", "resource_id": asset_id + "-local-source",
            "path": str(path), "usage_license": "Task-owned Shizhen reference; director-declared local copy, not platform adoption",
            "generated_source": {"record_path": rel(HERE / name), "record_sha256": sha(HERE / name), "tool": tool}}


def route_and_review(first: Path) -> None:
    route = {
        "kind": "authored-route-design/1",
        "status": "AUTHORED_DESIGN_NOT_MEASURED",
        "replaces": "v3 city-map route (camera west of road, ~69m with ~90deg turn into the site)",
        "heading": "起幅朝向与尾帧相同；全程主路在画左、作业区在画右",
        "duration_seconds": DURATION,
        "beats": [
            {"phase": "reveal", "relative_span": "前约四分之一", "motion": "贴檐口向右平移约四至六米，绕过外墙转角",
             "visible_change": "湿墙从左侧滑出，主路、车流与远处高楼群从墙后展开"},
            {"phase": "descent", "relative_span": "中段约一半", "motion": "沿主路右侧上空向前，同时由约六层高度平缓下降",
             "visible_change": "旧住宅（楼梯窗格）与透明玻璃站棚依次从右侧经过，行道树与路灯产生视差"},
            {"phase": "approach", "relative_span": "后约四分之一", "motion": "降到人眼高度并减速，两根钢索从下缘入前景",
             "visible_change": "绞盘、控制盒、黄帽深蓝工装工人、灰色铁门的关系与尾帧一致"},
            {"phase": "settle", "relative_span": "最后约一秒", "motion": "轻轻停稳", "visible_change": "画面收至MC01第0帧"}],
        "why_this_route": [
            "首尾帧朝向一致，模型主要做右移+前进下降，不需凭空发明大转弯",
            "首帧主路被墙遮住，揭示是真实发生的画面变化",
            "16秒避免v3末段约6秒空停"],
        "limits": "米制与位置为设计估计，非照片测绘；模型是否沿此路径运动只能由exact成片验证",
    }
    dump("route-design.json", route)
    write_text("pre-generation-feasibility.md", f"""# MC00 v4 Pre-generation Feasibility

范围：仅前期作者审查，不是视频或接点验收。

- 首帧：`first-frame-1920x1080.png`，SHA `{sha(first)}`；来源为 Codex 生图 `codex-image/raw/first-frame-v2.png`（SHA `{RAW_SHA}`），仅 FFmpeg Lanczos 尺寸适配。
- 尾帧：已认可市政第0帧 `MC01-normal.png`，SHA `{LAST_SHA}`，唯一末态锚点（方案A）。
- 首帧湿墙与檐口约占左侧55%，主路、车流和市政作业区被墙遮挡；右侧仅见旧住宅屋顶、窗灯与远处高楼。向右绕过墙角后主路才出现，符合尾帧“主路在左、作业区在右”的布局。
- 首尾朝向一致：路线为右移揭示→沿主路右侧上空前进下降→人眼高度减速停稳，见 `route-design.json`。
- 景别从高处檐口近景变为地面中景，`same_subject_scale=False`；不以变焦跳转、隐藏切镜或静止尾段替代运动。
- 未证明：实际视差、建筑稳定、站棚形制、工人是否重复按停、声音与 MC01 接点，全部待 exact MP4 验证。
""")


def derive_row_data(first: Path) -> tuple[dict, dict]:
    row = json.loads((V3 / "row.json").read_text())
    data = json.loads((V3 / "data.json").read_text())
    parts = PROMPT.splitlines()
    assert len(parts) == 4
    start = "六层旧楼外金属檐口滴雨近景，湿墙遮挡大半画面，墙角外只露一角城市"
    close = "相机已完全停稳，正常市政作业的构图、透视、门位、工人姿态与灯态落到已认可MC01第0帧"
    gi = row["generation"]["generation_intent"]
    gi["open_state"]["state_text"] = start
    gi["close_state"]["state_text"] = close
    gi["scene_continuity"]["state_constraints"][0] = "同一主路与沿途住宅、站棚及市政作业区"
    gi["space_continuity"].update(subject_position="从旧楼室外檐口，经主路右侧上空，到市政作业区前的人眼高度",
                                  screen_direction="先向右侧移绕过墙角，再沿与尾帧相同的朝向向前下降",
                                  crossing_policy="不穿墙、不穿玻璃、不跨钢索、不翻轴")
    gi["axis_continuity"].update(camera_axis="起幅朝向与尾帧一致，全程主路在画左、作业区在画右的同一观察侧",
                                 framing_continuity="檐口近景、城市展开、沿路下降及作业区落点连成一条可追踪路径")
    gi["subject_action"].update(start_state=start, progression="\n".join(parts[:3]))
    gi["subject_action"]["endpoint"]["state_text"] = close
    gi["motion_envelope"].update(onset="贴檐口向右侧移绕过墙角，城市从湿墙后展开",
                                 peak="沿主路右侧上空向前缓降，住宅与站棚依次经过",
                                 settle="降到人眼高度逐渐放慢，钢索入前景后轻轻停稳于尾帧",
                                 direction="先向右平移，再沿尾帧朝向向前下降")
    gi["pacing"].update(cadence="前约四分之一揭示，中段前进下降，后段放慢，最后约一秒停稳",
                        shot_duration_seconds=float(DURATION))
    gi["camera_intent"]["movement"] = "一条连续的檐口右移揭示、沿主路向前缓降及作业区前减速停稳"
    gi["camera_endpoint"].update(start_framing=start, end_framing=close)
    gi["camera_subject_relation"]["start_relation"] = "湿墙遮挡大半画面，墙角外露出一角城市"
    intent = GenerationIntent.model_validate(gi).model_dump(mode="json")
    row["generation"]["generation_intent"] = intent
    shot = row["shot"]
    shot["intent"] = PROMPT
    shot["duration_policy"]["seconds"] = DURATION
    shot["continuity_constraints"][1] = "檐口右移真实揭示，同一主路与住宅、站棚可追踪"
    shot["generated_video_rationale"] = "完整连续城市揭示与下降落点由一次16秒源承载，不拆段掩切，也不留长段静止尾帧"
    row["generation"]["output_need"]["duration_seconds"] = DURATION

    data["images"] = [source_image(FIRST, first, "first_frame"), source_image(LAST, ROOT / LAST_PATH, "last_frame")]
    for key, indices in {"identity": [2, 3], "action": [0, 1, 2], "camera": [0, 1, 3], "performance": [2, 3],
                         "space": [0, 1, 2, 3], "art": [0, 1, 2, 3], "sound": [3]}.items():
        data["fragments"][key] = [parts[i] for i in indices]
    data["observations"]["action"] = "檐口右移绕过墙角揭示城市，再沿主路向前缓降，住宅和站棚依次经过，钢索入前景后交给作业"
    data["observations"]["camera"] = "全镜连续无切点、叠化或冻结，下降自然，后段放慢并在最后约一秒停稳，构图与透视收至批准尾帧"
    data["intent_sha256"] = canonical_sha256(intent)
    data["review_only_inputs"] = ["Codex first-frame v1 rejected (road and city already open)", "authored route-design.json; not a model input"]
    data["qualification_scope"] = "one unqualified 16s 480p preview, not Production acceptance or 1080p pixel match"
    return row, data


def seal_conditioning(row: dict, data: dict, first: Path) -> None:
    intent = GenerationIntent.model_validate(row["generation"]["generation_intent"])
    specs = [("first-anchor", "anchor_geometry_review", first), ("last-anchor", "anchor_geometry_review", ROOT / LAST_PATH),
             ("anchor-review", "anchor_geometry_review", HERE / "pre-generation-feasibility.md"),
             ("raster-normalization", "anchor_geometry_review", HERE / "input-raster-normalization.json"),
             ("route", "trajectory", HERE / "route-design.json")]
    sources = [{"source_id": k, "kind": kind, "evidence_ref": rel(p), "sha256": sha(p)} for k, kind, p in specs]
    findings = [
        {"finding_id": "anchor_correspondence", "verdict": "PASS", "source_ids": ["anchor-review", "first-anchor", "last-anchor", "raster-normalization"],
         "rationale": "首尾帧朝向一致：首帧主路与作业区藏在左侧湿墙后，尾帧主路在左、作业区在右；揭示后布局可自然对应。首帧仅尺寸适配，无重画或裁切。未声称照片测绘或运镜已成立。"},
        {"finding_id": "continuous_camera_path", "verdict": "PASS", "source_ids": ["anchor-review", "route"],
         "rationale": "作者路线为右移绕墙角后沿尾帧朝向前进下降，不需穿墙、跨索或大角度转向；实际路径服从待exact MP4验证。"},
        {"finding_id": "duration_reachable", "verdict": "PASS", "source_ids": ["route"],
         "rationale": "16秒按约四分之一揭示、一半下降、四分之一减速并最后约一秒停稳分配，无长段静止尾帧；为设计估计，非实测。"},
        {"finding_id": "scale_fov_continuity", "verdict": "PASS", "source_ids": ["anchor-review", "first-anchor", "last-anchor", "route"],
         "rationale": "首尾景别不同，same_subject_scale=False；景别变化由离开檐口、前进与下降产生，不以变焦跳转或隐藏切镜替代。内参未标定，模型服从待实片。"},
    ]
    evidence = ScaleTransitionEvidence.create(first_anchor_id=FIRST, first_anchor_sha256=sources[0]["sha256"],
        last_anchor_id=LAST, last_anchor_sha256=sources[1]["sha256"], camera_intent_hash=scale_transition_camera_intent_hash(intent),
        available_duration_seconds=float(DURATION), sources=sources, findings=findings)
    compat = row["generation"]["conditioning_compatibility"]
    compat.update(available_duration_seconds=DURATION, same_subject_scale=False, composition_compatible=True,
                  screen_order_compatible=True, axis_compatible=True, camera_path_reachable=True,
                  character_prop_state_reachable=True, action_endpoint_reachable=True,
                  scale_transition=evidence.model_dump(mode="json"))
    dump("conditioning-review.json", {"scope": "PRE_GENERATION_AUTHORED_FEASIBILITY_ONLY", "evidence": compat,
                                      "actual_motion_and_sound": "NOT_EVALUATED", "human_acceptance": "NOT_EVALUATED"})


def operator_bound() -> None:
    prior = json.loads((V3 / "operator-bound.json").read_text())
    v3 = load_production_project(ROOT / "runs/shizhen-macro-opening-20261028/MC00-city-v3/project.yaml")
    attempts = [a for a in v3.manifest.attempts if a.operation == "video_generation"]
    assert len(attempts) == 1 and attempts[0].video_generation_state.fetch_receipt is not None
    a = attempts[0]
    assert a.status.value not in {"outcome_unknown", "interrupted"}
    ancestors = prior["ancestors"] + [{"root": "runs/shizhen-macro-opening-20261028/MC00-city-v3", "attempt_id": a.attempt_id,
        "known_fetched": True, "artifact_sha256": a.video_generation_state.fetch_receipt.artifact_sha256,
        "manifest_sha256": sha(ROOT / "runs/shizhen-macro-opening-20261028/MC00-city-v3/state/manifest.json")}]
    assert len(ancestors) == 7
    dump("historical-generation-audit.json", {"scope": "Seven macro submits; v3 FAIL outcome known and preserved",
        "unique_macro_attempts": 7, "items": ancestors,
        "unknown_other_history_preserved": prior["historical_unknown_attempts_preserved"], "new_macro_submissions": 0})
    readonly = json.loads((HERE / "native-readonly.json").read_text())
    now = datetime.now(timezone.utc)
    dump("operator-bound.json", {**prior, "authorization_quote": "直接重做,生圖調用codex",
        "scope": "One MC00 v4 continuous16s480p first-last-frame native-audio redo preview; no MC03+ continuation or activation",
        "predecessor_bound_path": rel(V3 / "operator-bound.json"), "predecessor_bound_sha256": sha(V3 / "operator-bound.json"),
        "failed_same_shot_gate_path": rel(V3 / "qa/post-media-gate.json"), "failed_same_shot_gate_sha256": sha(V3 / "qa/post-media-gate.json"),
        "issued_at": now.isoformat(), "expires_at": (now + timedelta(hours=2)).isoformat(),
        "max_submit_count": 1, "automatic_retries": 0,
        "macro_paid_submits_before": 7, "macro_cumulative_ceiling_after_authorized_unit": 8,
        "ancestors": ancestors, "current_quote_credits": readonly["quote"]["credits"], "quote_evidence": "native-readonly.json"})


def main() -> None:
    assert len(PROMPT) <= 500 and not any(c.isascii() and c.isalpha() for c in PROMPT)
    codex_record()
    first = normalize_first()
    route_and_review(first)
    row, data = derive_row_data(first)
    seal_conditioning(row, data, first)
    dump("row.json", row)
    dump("data.json", data)
    operator_bound()
    print(json.dumps({"prompt_chars": len(PROMPT), "first_sha256": sha(first), "duration": DURATION,
                      "video_calls": 0, "run_writes": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
