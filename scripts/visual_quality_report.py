"""Local visual review packets; no Production writes or acceptance receipts.

prepare extracts exact frames and writes an unreviewed packet. check reopens
every byte before deriving a development verdict through the final-output gate.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess

from pydantic import Field

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.final_output_review import FinalOutputObservation, adjudicate_final_output_details
from ai_video.production.hashing import canonical_sha256
from ai_video.production.junction_review import (
    JunctionFinding,
    JunctionInventory,
    derive_junction_inventory,
    evaluate_junction_review,
    junction_inventory_sha256,
    validate_probe_matches_report,
    validate_timeline_and_report,
)
from ai_video.production.models import EvidenceStrength
from ai_video.production.visual_quality import VisualDirection, VisualFrameReference, visual_requirements
from scripts.creative_goal_binding import load_goal_binding


LABELS = {"typography": "字体与阅读", "palette": "配色", "layout": "排版与主体",
          "style": "画风一致性", "holistic": "全片观感"}
CONTENT_LABELS = {"advertising": "广告", "drama": "电视剧"}


class ReviewAnswer(StrictModel):
    evaluator_name: str = Field(min_length=1)
    strength: EvidenceStrength
    observation: FinalOutputObservation
    junction_findings: tuple[JunctionFinding, ...] = ()


@dataclass(frozen=True)
class LocalEvidence:
    """Ephemeral adjudicator input, deliberately not a Production ReviewEvidence."""

    strength: EvidenceStrength
    render_output_sha256: str
    measured_payload: dict


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(video: Path, direction: VisualDirection, output: Path, timestamps: tuple[int, ...],
            *, final_output_contract: FinalOutputContract | None = None, goal_binding: Path | None = None,
            timeline: Path | None = None, render_report: Path | None = None):
    if goal_binding is not None and final_output_contract is None:
        raise ValueError("Goal binding requires a complete final-output contract")
    visual = visual_requirements(direction)
    if final_output_contract is not None:
        supplied = {r.requirement_id: r for r in final_output_contract.requirements if r.visual_dimension}
        if direction.content_kind is None or supplied != {r.requirement_id: r for r in visual}:
            raise ValueError("Complete contract visual requirements must match the explicit direction")
        contract = final_output_contract
    else:
        contract = FinalOutputContract(goal_id="overall-visual-quality", goal_version="1",
            user_goal="字体、配色、排版、画风一致性和最终观感符合选定视觉方向。",
            requirements=visual)
    verified = load_goal_binding(goal_binding) if goal_binding is not None else None
    if verified is not None and verified.contract != contract:
        raise ValueError("Goal binding contract differs from the supplied complete contract")
    if final_output_contract is not None and (timeline is None or render_report is None):
        raise ValueError("Full-contract review requires an exact ResolvedTimeline and HyperFrames render report")
    if final_output_contract is None and (timeline is not None or render_report is not None):
        raise ValueError("ResolvedTimeline and render report require a complete final-output contract")
    video = video.resolve(strict=True)
    before = file_hash(video)
    video_size = video.stat().st_size
    timeline_bytes = timeline.read_bytes() if timeline is not None else None
    render_report_bytes = render_report.read_bytes() if render_report is not None else None
    timeline_model = render_model = None
    if timeline_bytes is not None and render_report_bytes is not None:
        timeline_model, render_model = validate_timeline_and_report(
            timeline_bytes,
            render_report_bytes,
            video_path=video,
            video_sha256=before,
            video_size_bytes=video_size,
        )
        inventory = derive_junction_inventory(timeline_model)
        inventory_hash = junction_inventory_sha256(inventory)
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format",
        "-show_streams", "-of", "json", str(video)], check=True, capture_output=True, text=True).stdout)
    if timeline_model is not None and render_model is not None:
        validate_probe_matches_report(probe, timeline_model, render_model)
    duration_ms = int(Decimal(probe["format"]["duration"]) * 1000)
    if not timestamps or len(set(timestamps)) != len(timestamps) or any(t < 0 or t >= duration_ms for t in timestamps):
        raise ValueError("Unique frame timestamps must be inside the video")
    output.mkdir(parents=True, exist_ok=False)
    (output / "frames").mkdir()
    if verified is not None:
        for snapshot in verified.files:
            path = output / "creative" / snapshot.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(snapshot.data)
    if timeline_bytes is not None and render_report_bytes is not None:
        (output / "timeline.json").write_bytes(timeline_bytes)
        (output / "render-report.json").write_bytes(render_report_bytes)
    frames = []
    for stamp in sorted(timestamps):
        path = output / "frames" / f"{stamp:08d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{stamp / 1000:.3f}",
            "-i", str(video), "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "2", str(path)],
            check=True, capture_output=True)
        frames.append({"path": path.relative_to(output).as_posix(), "timestamp_ms": stamp,
            "frame_sha256": file_hash(path), "render_output_sha256": before})
    if file_hash(video) != before:
        raise ValueError("Video changed during extraction")
    version = "visual-review-packet/4" if final_output_contract is not None else "visual-review-packet/1"
    packet = {"schema_version": version, "authority": "development_only",
        "video_path": str(video), "video_sha256": before, "video_size_bytes": video.stat().st_size,
        "duration_ms": duration_ms, "contract": contract.model_dump(mode="json"), "frames": frames}
    if direction.content_kind is not None:
        packet["content_kind"] = direction.content_kind
    if verified is not None:
        packet["goal_binding"] = {**verified.identity(), "path": f"creative/{verified.files[0].path}"}
    if timeline_model is not None and render_model is not None:
        packet["timeline_snapshot"] = {
            "path": "timeline.json",
            "sha256": hashlib.sha256(timeline_bytes).hexdigest(),
            "content_hash": timeline_model.content_hash,
            "composition_fingerprint": timeline_model.composition_fingerprint,
            "total_frames": timeline_model.total_frames,
            "fps": timeline_model.delivery_profile.fps,
            "sample_rate": timeline_model.sample_rate,
        }
        packet["render_report_snapshot"] = {
            "path": "render-report.json",
            "sha256": hashlib.sha256(render_report_bytes).hexdigest(),
            "video_sha256": render_model.sha256,
            "timeline_fingerprint": render_model.timeline_fingerprint,
            "duration_frames": render_model.measured.duration_frames,
            "fps_num": render_model.measured.fps_num,
            "fps_den": render_model.measured.fps_den,
        }
        packet["junction_inventory"] = [item.model_dump(mode="json") for item in inventory]
        packet["junction_inventory_sha256"] = inventory_hash
    packet["subject_hash"] = canonical_sha256(packet)
    write_json(output / "packet.json", packet)
    observation = {"contract_hash": contract.contract_hash,
        "review_request_content_hash": packet["subject_hash"], "viewing_mode": "sampled_frames",
        "visual_frame_inventory": {"duration_ms": duration_ms,
            "frames": [{k: v for k, v in f.items() if k != "path"} for f in frames]},
        "viewing_speed_milli": None,
        "findings": [{"requirement_id": r.requirement_id, "verdict": "not_evaluated",
            "observation": "尚未评审；不得从抽帧成功推断通过。", "visual_frames": []}
            for r in contract.requirements]}
    answer_template = {"evaluator_name": "pending", "strength": "explicit_evaluator",
        "observation": observation}
    if timeline_model is not None:
        answer_template["junction_findings"] = [
            {
                "junction_id": item.junction_id,
                "inventory_sha256": inventory_hash,
                "edit_decision": None,
                "edit_reason": "尚未评审；需记录剪辑决定和依据。",
                "visual_verdict": "not_evaluated",
                "visual_observation": "未评审；1x完整播放该接点，记录动作/画面有无重复、停顿或跳变。",
                "audio_verdict": "not_evaluated",
                "audio_observation": "未聆听；实际监听接点前后音频，记录有无叠音、截断或异常空隙。",
                "audio_basis": "not_listened",
                "audio_reason": None,
                "viewing_mode": None,
                "viewing_speed_milli": None,
            }
            for item in inventory
        ]
    write_json(output / "observations.template.json", answer_template)
    return check(output, output / "observations.template.json")


def reopen(output: Path):
    packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
    body = {k: v for k, v in packet.items() if k != "subject_hash"}
    version = packet.get("schema_version")
    if version not in {"visual-review-packet/1", "visual-review-packet/2", "visual-review-packet/3", "visual-review-packet/4"} or packet.get("authority") != "development_only":
        raise ValueError("Unsupported visual review packet")
    if canonical_sha256(body) != packet["subject_hash"]:
        raise ValueError("Packet identity changed; prepare a new packet")
    video = Path(packet["video_path"])
    if video.stat().st_size != packet["video_size_bytes"] or file_hash(video) != packet["video_sha256"]:
        raise ValueError("Video bytes changed; old review cannot be reused")
    contract = FinalOutputContract.model_validate(packet["contract"])
    visual = tuple(r for r in contract.requirements if r.visual_dimension is not None)
    if {r.visual_dimension for r in visual} != set(LABELS):
        raise ValueError("Packet must retain all five visual requirements")
    if version == "visual-review-packet/1" and visual != contract.requirements:
        raise ValueError("Legacy packet supports only visual requirements")
    kind = packet.get("content_kind")
    if version != "visual-review-packet/1" and kind is None:
        raise ValueError("Complete contract requires an explicit content kind")
    if "content_kind" in packet and (not isinstance(kind, str) or kind not in CONTENT_LABELS):
        raise ValueError("Unknown visual content kind")
    prefix = "visual" if kind is None else f"visual.{kind}"
    if any(r.requirement_id != f"{prefix}.{r.visual_dimension}" for r in visual):
        raise ValueError("Content kind differs from sealed visual requirements")
    if version in {"visual-review-packet/3", "visual-review-packet/4"} and "goal_binding" in packet:
        identity = packet.get("goal_binding")
        if not isinstance(identity, dict) or not isinstance(identity.get("path"), str):
            raise ValueError("Goal binding snapshot is missing")
        path = Path(identity["path"])
        if path.is_absolute() or ".." in path.parts or len(path.parts) != 2 or path.parts[0] != "creative":
            raise ValueError("Goal binding path escapes the creative snapshot")
        verified = load_goal_binding(output / path)
        expected = {**verified.identity(), "path": path.as_posix()}
        if identity != expected or verified.contract != contract:
            raise ValueError("Goal binding snapshot or complete contract identity changed")
    elif version == "visual-review-packet/3":
        raise ValueError("Goal binding snapshot is missing")
    elif "goal_binding" in packet:
        raise ValueError("Legacy packet cannot claim a verified goal binding")
    if version == "visual-review-packet/4":
        try:
            timeline_ref = packet["timeline_snapshot"]
            report_ref = packet["render_report_snapshot"]
            if timeline_ref["path"] != "timeline.json" or report_ref["path"] != "render-report.json":
                raise ValueError("Timeline or render report snapshot path is not canonical")
            timeline_path = output / timeline_ref["path"]
            report_path = output / report_ref["path"]
            if timeline_path.is_symlink() or report_path.is_symlink():
                raise ValueError("Timeline and render report snapshots cannot be symlinks")
            timeline_bytes = timeline_path.read_bytes()
            report_bytes = report_path.read_bytes()
            if (hashlib.sha256(timeline_bytes).hexdigest() != timeline_ref["sha256"]
                    or hashlib.sha256(report_bytes).hexdigest() != report_ref["sha256"]):
                raise ValueError("Timeline or render report snapshot bytes changed")
            timeline_model, render_model = validate_timeline_and_report(
                timeline_bytes,
                report_bytes,
                video_path=video,
                video_sha256=packet["video_sha256"],
                video_size_bytes=packet["video_size_bytes"],
            )
            expected_timeline = {
                "content_hash": timeline_model.content_hash,
                "composition_fingerprint": timeline_model.composition_fingerprint,
                "total_frames": timeline_model.total_frames,
                "fps": timeline_model.delivery_profile.fps,
                "sample_rate": timeline_model.sample_rate,
            }
            expected_report = {
                "video_sha256": render_model.sha256,
                "timeline_fingerprint": render_model.timeline_fingerprint,
                "duration_frames": render_model.measured.duration_frames,
                "fps_num": render_model.measured.fps_num,
                "fps_den": render_model.measured.fps_den,
            }
            if any(timeline_ref.get(key) != value for key, value in expected_timeline.items()):
                raise ValueError("ResolvedTimeline snapshot identity changed")
            if any(report_ref.get(key) != value for key, value in expected_report.items()):
                raise ValueError("Render report snapshot identity changed")
            inventory = derive_junction_inventory(timeline_model)
            inventory_hash = junction_inventory_sha256(inventory)
            supplied_inventory = tuple(
                JunctionInventory.model_validate(item) for item in packet["junction_inventory"]
            )
            if (
                supplied_inventory != inventory
                or packet.get("junction_inventory_sha256") != inventory_hash
            ):
                raise ValueError("Per-cut inventory differs from the exact ResolvedTimeline")
        except (KeyError, OSError, TypeError) as exc:
            raise ValueError("Full-contract timeline or render report snapshot is incomplete") from exc
    elif any(key in packet for key in ("timeline_snapshot", "render_report_snapshot", "junction_inventory", "junction_inventory_sha256")):
        raise ValueError("Legacy packet cannot claim a new junction binding")
    for frame in packet["frames"]:
        path = output / frame["path"]
        if not path.resolve().is_relative_to((output / "frames").resolve()):
            raise ValueError("Frame path escapes review packet")
        if file_hash(path) != frame["frame_sha256"] or frame["render_output_sha256"] != packet["video_sha256"]:
            raise ValueError("Frame bytes or video binding changed")
        if not 0 <= frame["timestamp_ms"] < packet["duration_ms"]:
            raise ValueError("Frame timestamp outside video")
    return packet, contract


def check(output: Path, answers: Path):
    # Remove stale derived PASS displays before validating edited/replaced inputs.
    for name in ("result.json", "report.html"):
        (output / name).unlink(missing_ok=True)
    packet, contract = reopen(output)
    answer = ReviewAnswer.model_validate_json(answers.read_text(encoding="utf-8"))
    if answer.strength not in {EvidenceStrength.HUMAN, EvidenceStrength.EXPLICIT_EVALUATOR}:
        raise ValueError("Visual assessment needs explicit evaluator or human evidence")
    source = answer.observation
    if source.contract_hash != contract.contract_hash or source.review_request_content_hash != packet["subject_hash"]:
        raise ValueError("Review belongs to a different contract or media packet")
    available = {VisualFrameReference.model_validate({k: v for k, v in frame.items() if k != "path"})
        for frame in packet["frames"]}
    if (source.visual_frame_inventory is None
            or source.visual_frame_inventory.duration_ms != packet["duration_ms"]
            or set(source.visual_frame_inventory.frames) != available):
        raise ValueError("Review extraction inventory differs from exact media packet")
    ids = [f.requirement_id for f in source.findings]
    if len(ids) != len(set(ids)) or not set(ids) <= {r.requirement_id for r in contract.requirements}:
        raise ValueError("Unknown or duplicate visual findings")
    for finding in source.findings:
        if not set(finding.visual_frames) <= available:
            raise ValueError("Review references a frame outside the exact extracted packet")
    item = LocalEvidence(answer.strength, packet["video_sha256"], {"final_output": source.model_dump(mode="json")})
    details = adjudicate_final_output_details(contract, (item,), review_request_content_hash=packet["subject_hash"])
    effective = [{"requirement_id": row.requirement_id, "verdict": row.verdict.value,
        "evidence_gaps": list(row.evidence_gaps)} for row in details.requirements]
    junction_result = None
    if packet["schema_version"] == "visual-review-packet/4":
        inventory = tuple(JunctionInventory.model_validate(row) for row in packet["junction_inventory"])
        junction_result = evaluate_junction_review(
            inventory,
            answer.junction_findings,
            inventory_sha256=packet["junction_inventory_sha256"],
            strength=answer.strength,
        )
    elif packet["schema_version"] in {"visual-review-packet/2", "visual-review-packet/3"}:
        from ai_video.production.junction_review import JunctionReviewResult

        junction_result = JunctionReviewResult(
            verdict="not_evaluated",
            evidence_gaps=("missing_junction_binding",),
            cuts=(),
        )
    if junction_result is None:
        combined_verdict = details.verdict.value
        evidence_gaps = list(details.evidence_gaps)
    else:
        if details.verdict.value == "fail" or junction_result.verdict == "fail":
            combined_verdict = "fail"
        elif details.verdict.value == "pass" and junction_result.verdict == "pass":
            combined_verdict = "pass"
        else:
            combined_verdict = "not_evaluated"
        evidence_gaps = list(dict.fromkeys((*details.evidence_gaps, *junction_result.evidence_gaps)))
    result = {"authority": "development_only", "verdict": combined_verdict,
        "review_scope": "visual_only" if packet["schema_version"] == "visual-review-packet/1" else "full_contract",
        "goal_chain": "verified" if "goal_binding" in packet else "not_evaluated",
        "production_acceptance": "not_evaluated", "subject_hash": packet["subject_hash"],
        "video_sha256": packet["video_sha256"], "answers_sha256": file_hash(answers),
        "evaluator_name": answer.evaluator_name, "strength": answer.strength.value,
        "findings": [f.model_dump(mode="json") for f in source.findings],
        "effective_requirements": effective, "evidence_gaps": evidence_gaps}
    if junction_result is not None:
        result["junction_review"] = junction_result.model_dump(mode="json")
    result["completion_summary"] = {"video_sha256": packet["video_sha256"],
        "review_scope": result["review_scope"], "goal_chain": result["goal_chain"],
        "viewing_mode": source.viewing_mode, "viewing_speed_milli": source.viewing_speed_milli,
        "requirements_to_address": [{**row, "next_action": "repair" if row["verdict"] == "fail" else "evidence_repair"}
            for row in effective if row["verdict"] != "pass"],
        "evidence_gaps": evidence_gaps,
        "user_feedback": {"assessment": "parent_review_required",
            "source": packet.get("goal_binding", {}).get("creative_input"),
            "note": "Parent 须核对有效用户反馈并披露未解决的拒绝；工具不判断用户是否撤回意见。"}}
    if junction_result is not None:
        junctions_to_address = [
            {
                "requirement_id": f"junction.{cut.junction_id}",
                "verdict": cut.verdict,
                "evidence_gaps": list(cut.evidence_gaps),
                "next_action": "repair" if cut.verdict == "fail" else "evidence_repair",
            }
            for cut in junction_result.cuts if cut.verdict != "pass"
        ]
        if "missing_junction_binding" in junction_result.evidence_gaps:
            junctions_to_address.append({
                "requirement_id": "junction_binding",
                "verdict": "not_evaluated",
                "evidence_gaps": ["missing_junction_binding"],
                "next_action": "evidence_repair",
            })
        result["completion_summary"]["junctions_to_address"] = junctions_to_address
        result["completion_summary"]["requirements_to_address"].extend(junctions_to_address)
    if "goal_binding" in packet:
        reference = packet["goal_binding"]["creative_input"]
        result["completion_summary"]["user_feedback"]["source"] = {**reference,
            "path": (Path(packet["goal_binding"]["path"]).parent / reference["path"]).as_posix()}
    if "content_kind" in packet:
        result["content_kind"] = packet["content_kind"]
    write_json(output / "result.json", result)
    (output / "report.html").write_text(render_html(packet, contract, result), encoding="utf-8")
    return result


def render_html(packet, contract, result):
    findings = {f["requirement_id"]: f for f in result["findings"]}
    effective = {r["requirement_id"]: r for r in result["effective_requirements"]}
    cards = []
    for rule in contract.requirements:
        finding = findings.get(rule.requirement_id, {"verdict": "not_evaluated", "observation": "缺少该项评审。", "visual_frames": []})
        outcome = effective[rule.requirement_id]
        stamps = " · ".join(f'{f["timestamp_ms"] / 1000:.2f}s' for f in finding["visual_frames"])
        cards.append(f'<article><div class="row"><h3>{escape(LABELS.get(rule.visual_dimension, rule.requirement_id))}</h3>'
            f'<b class="{outcome["verdict"]}">有效结果 · {outcome["verdict"].upper()}</b></div>'
            f'<p class="muted">标准 · {escape(rule.observable)}</p><p>{escape(finding["observation"])}</p>'
            f'<small>原始回答 · {finding["verdict"].upper()}<br>证据缺口 · {escape(", ".join(outcome["evidence_gaps"]) or "none")}</small><br>'
            f'<small>{escape(stamps)}</small></article>')
    frames = ''.join(f'<figure><img src="{escape(f["path"], quote=True)}" alt="成片 {f["timestamp_ms"] / 1000:.2f} 秒">'
        f'<figcaption>{f["timestamp_ms"] / 1000:.2f}s</figcaption></figure>' for f in packet["frames"])
    scope_label = "完整合同逐项评审" if result["review_scope"] == "full_contract" else "仅视觉要求评审"
    chain_label = "目标引用链结构已核对；不证明语义充分" if result["goal_chain"] == "verified" else "目标引用链未核对"
    todo = ''.join(f'<li>{escape(row["requirement_id"])} · {row["verdict"].upper()} · {"修复" if row["next_action"] == "repair" else "补证"}</li>'
        for row in result["completion_summary"]["requirements_to_address"])
    junction_section = ""
    if "junction_review" in result:
        inventory = {row["junction_id"]: row for row in packet.get("junction_inventory", [])}
        cuts = []
        for cut in result["junction_review"]["cuts"]:
            details = inventory.get(cut["junction_id"], {})
            visual_sources = "；".join(
                f'{escape(row["shot_id"])} / {escape(row["layer_id"])} · '
                f'SHA {escape(row["asset_sha256"][:12])} · trim {row["trim_start_frame"]}+'
                f'{row["trim_duration_frames"] if row["trim_duration_frames"] is not None else "source-end"}f'
                for row in details.get("visual_spans", [])
            ) or "无邻近视觉素材记录"
            audio_sources = "；".join(
                f'{escape(row["track_id"])} / {escape(row["audio_kind"])} · '
                f'SHA {escape(row["asset_sha256"][:12])} · source {row["source_start_sample"]}+'
                f'{row["source_duration_samples"]} samples · fades {row["fade_in_samples"]}/'
                f'{row["fade_out_samples"]} samples'
                for row in details.get("audio_spans", [])
            ) or "该窗口没有排定音轨；这本身不构成静音评审通过"
            audio_basis = {"actual_listening": "实际聆听", "deliberately_silent": "明确设计为静音",
                "not_listened": "未聆听", None: "未声明"}.get(cut.get("audio_basis"), "未知")
            cut_viewing = {"full_playback": "完整播放", "sampled_frames": "抽样画面", None: "未声明"}.get(
                cut.get("viewing_mode"), "未知")
            cut_speed = cut.get("viewing_speed_milli")
            cut_speed_text = "未声明速度" if cut_speed is None else f'{cut_speed / 1000:g} 倍速'
            cuts.append(
                f'<article><div class="row"><h3>{escape(cut["from_shot_id"])} → '
                f'{escape(cut["to_shot_id"])} · {details.get("time_ms", cut["frame"])}ms '
                f'(frame {cut["frame"]})</h3><b class="{cut["verdict"]}">有效结果 · '
                f'{cut["verdict"].upper()}</b></div>'
                f'<p>剪辑决定 · {escape(cut["edit_decision"] or "未评审")} · '
                f'{escape(cut["edit_reason"])}</p>'
                f'<p>画面 · {escape(cut["visual_verdict"].upper())} · '
                f'{escape(cut["visual_observation"])}</p>'
                f'<p>声音 · {escape(cut["audio_verdict"].upper())} · '
                f'{escape(cut["audio_observation"])}</p>'
                f'<p>声音依据 · {escape(audio_basis)} · {escape(cut.get("audio_reason") or "无额外说明")}<br>'
                f'观看声明 · {escape(cut_viewing)} / {escape(cut_speed_text)}</p>'
                f'<p class="muted">转换 · {escape(details.get("transition_kind", "unknown"))} / '
                f'{details.get("transition_duration_frames", "?")}f<br>视觉素材与源裁切 · '
                f'{visual_sources}<br>接点附近实际音轨与裁切/淡入淡出 · {audio_sources}</p>'
                f'<small>证据缺口 · {escape(", ".join(cut["evidence_gaps"]) or "none")}</small></article>'
            )
        if cuts:
            content = f'<div class="grid">{"".join(cuts)}</div>'
        elif packet["schema_version"] == "visual-review-packet/4":
            content = '<p>ResolvedTimeline 没有入镜转换；未补造接点。</p>'
        else:
            content = '<p>历史 packet 未绑定 ResolvedTimeline 或接点清单；衔接范围未知。</p>'
        junction_section = (
            f'<section><h2>镜头接点剪辑检查</h2><p>Gate · '
            f'{escape(result["junction_review"]["verdict"].upper())} · '
            f'{len(result["junction_review"]["cuts"])} 个接点</p>'
            f'<p class="muted">此处需对 exact MP4 做正常速度 1x 完整播放并分别记录画面与实际聆听；'
            f'帧绑定、波形、ASR 和渲染通过都不会自动通过接点。</p>{content}</section>'
        )
    summary = result["completion_summary"]
    feedback_source = json.dumps(summary["user_feedback"]["source"], ensure_ascii=False) if summary["user_feedback"]["source"] else "未封存相关用户上下文"
    viewing = {"sampled_frames": "抽样画面", "full_playback": "完整播放"}.get(summary["viewing_mode"], "未声明观看方式")
    speed = summary["viewing_speed_milli"]
    speed_label = "未声明速度" if speed is None else f"{speed / 1000:g} 倍速"
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>成片视觉评审</title>
<style>body{{margin:0;background:#f4f3ef;color:#202523;font:16px/1.7 system-ui,sans-serif}}
main{{max-width:1240px;margin:auto;padding:48px 24px;overflow-wrap:anywhere}}h1{{font-size:38px;line-height:1.2}}h3,p{{margin:8px 0}}
.eyebrow{{color:#53675b;letter-spacing:3px}}.muted,small{{color:#626b65}}.row{{display:flex;justify-content:space-between;gap:20px;align-items:center}}
.row{{flex-wrap:wrap}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}article{{background:white;border:1px solid #dce1db;border-radius:14px;padding:22px}}
.fail{{color:#a42c26}}.pass{{color:#29613e}}.not_evaluated{{color:#855e20}}b{{font-size:13px;white-space:nowrap}}
.frames{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}figure{{margin:0}}img{{width:100%;border-radius:8px}}figcaption{{font-size:13px}}
.identity{{overflow-wrap:anywhere;font:12px/1.8 monospace}}section{{margin-top:36px}}
@media(max-width:720px){{.grid{{grid-template-columns:1fr}}.frames{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:30px}}}}</style>
<main><div class="eyebrow">VISUAL REVIEW / 成片整体视觉</div><h1>让视觉问题有据可查</h1>
<p>{escape(Path(packet["video_path"]).name)} · {packet["duration_ms"] / 1000:.3f}s · {CONTENT_LABELS.get(packet.get("content_kind"), "历史未分类方向")}</p>
<p>{scope_label} · 原目标：{escape(contract.user_goal)}</p>
<p class="{result["verdict"]}"><strong>本次检查：{result["verdict"].upper()}</strong></p>
<p class="muted">开发侧评审报告。截图不证明全片观看；本报告不写入 Production 验收状态。
下方单项标签是原裁决器核验后的有效结果；评审者的原始回答单独列出。
合同覆盖范围由创作者明确；报告不自动检测叙事、表演或音频质量，也不证明已包含全部用户要求。</p>
<section><h2>交付摘要与下一动作</h2><p>{chain_label}</p>
<p>观看声明 · {viewing} / {speed_label}</p>
<ul>{todo}</ul><p>全局证据缺口 · {escape(', '.join(result["evidence_gaps"]) or 'none')}</p>
<p>{escape(summary["user_feedback"]["note"])}</p><p class="identity">用户反馈来源 · {escape(feedback_source)}</p>
<p class="muted">结构检查、独立概念判断、实际观看、用户意见须分别取证。报告仅核验结构和证据声明；Production acceptance: NOT_EVALUATED。</p></section>
<section><h2>要求与逐项评审</h2><div class="grid">{''.join(cards)}</div></section>
{junction_section}
<section><h2>成片画面证据</h2><div class="frames">{frames}</div></section>
<section class="identity">MP4 SHA-256: {packet["video_sha256"]}<br>Review subject: {packet["subject_hash"]}<br>
Evaluator: {escape(result["evaluator_name"])} / {escape(result["strength"])}</section></main></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--video", type=Path, required=True)
    prep.add_argument("--direction", type=Path, required=True)
    prep.add_argument("--contract", type=Path, help="Complete authored FinalOutputContract; preserves nonvisual requirements")
    prep.add_argument("--goal-binding", type=Path, help="Exact development intent binding; requires --contract")
    prep.add_argument("--timeline", type=Path, help="Exact canonical ResolvedTimeline; required with --contract")
    prep.add_argument("--render-report", type=Path, help="Existing HyperFrames render report; required with --contract")
    prep.add_argument("--content-kind", choices=tuple(CONTENT_LABELS), required=True)
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--timestamps-ms", type=int, nargs="+", required=True)
    review = sub.add_parser("check")
    review.add_argument("--packet", type=Path, required=True)
    review.add_argument("--answers", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            direction = VisualDirection.model_validate_json(args.direction.read_text())
            if direction.content_kind != args.content_kind:
                raise ValueError("Explicit content kind must match the direction file")
            contract = FinalOutputContract.model_validate_json(args.contract.read_text()) if args.contract else None
            result = prepare(args.video, direction, args.output, tuple(args.timestamps_ms),
                final_output_contract=contract, goal_binding=args.goal_binding,
                timeline=args.timeline, render_report=args.render_report)
        else:
            result = check(args.packet, args.answers)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({"verdict": "not_evaluated", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.command == "prepare" or result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
