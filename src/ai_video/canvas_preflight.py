"""Read-only filmmaking preparation from the existing source and asset owners.

Provenance, planned handoff and Provider admission are different facts. This
projection never certifies an input, authorizes a submit or owns lifecycle.
"""
from copy import deepcopy

from ai_video.canvas_authoring import direction_reference


def _reference_measurements(asset):
    measurements = {"width": asset.width, "height": asset.height}
    metadata = asset.video_metadata
    if metadata is not None:
        measurements.update({
            "duration_seconds": asset.duration_seconds,
            "duration_milliseconds": metadata.duration_milliseconds,
            "fps": {"numerator": metadata.fps_numerator,
                    "denominator": metadata.fps_denominator},
            "frame_count": metadata.frame_count,
            "container_name": metadata.container_name,
            "codec_name": metadata.codec_name,
        })
    elif asset.duration_seconds is not None:
        measurements["duration_seconds"] = asset.duration_seconds
    return measurements


def _reference_inventory(references, assets):
    groups = {}
    for reference in references:
        asset = assets.get(reference["asset_id"])
        if asset is None:
            continue
        key = (asset.sha256, asset.size_bytes, asset.mime_type)
        binding = {"asset_id": reference["asset_id"], "role": reference["role"]}
        if "owner_id" in reference:
            binding["owner_id"] = reference["owner_id"]
        groups.setdefault(key, []).append(binding)
    exact_groups = [
        {"sha256": sha256, "size_bytes": size_bytes, "mime_type": mime_type,
         "bindings": bindings}
        for (sha256, size_bytes, mime_type), bindings in groups.items()
    ]
    return {
        "semantic_binding_count": len(references),
        "unique_exact_byte_count": len(exact_groups),
        "duplicate_byte_groups": [group for group in exact_groups if len(group["bindings"]) > 1],
    }


def canvas_reference_preflight(*, packet, direction, registry, qa_policy=None,
                               qa_authority="NOT_EVALUATED", authored_shots=()):
    """Project inputs already validated by author_canvas_project; no verdicts."""
    from ai_video.production.production_responsibility import production_responsibility_report
    from ai_video.production.performance_authoring import performance_authoring_report
    from ai_video.canvas_visual_style import visual_style_report

    authored = {shot.shot_id: shot for shot in authored_shots}
    assets = {asset.asset_id: asset for asset in registry.assets}
    rows = direction["shots"]
    units = {unit["occurrence_id"]: unit for unit in packet["units"]}
    by_occurrence = {row["occurrence_id"]: row["shot"]["shot_id"] for row in rows}
    shots = []
    for row in rows:
        unit = units[row["occurrence_id"]]
        plan = row.get("state_reference")
        replacements = row.get("reference_replacements", {})
        references = []
        generation = row.get("generation", {})
        generation_references = generation.get("references", [])
        for reference in generation_references:
            aid = reference["asset_id"]
            asset = assets.get(aid)
            value = {"asset_id": aid, "role": reference["role"],
                "provider_admission": "NOT_EVALUATED",
                "source_status": "MISSING" if asset is None else "REGISTERED_BYTES"}
            if "owner_id" in reference:
                value["owner_id"] = reference["owner_id"]
            if asset is not None:
                value["identity"] = {"sha256": asset.sha256, "size_bytes": asset.size_bytes,
                    "mime_type": asset.mime_type, "source_kind": asset.source_kind.value,
                    "tool": asset.tool.model_dump(mode="json"),
                    "creation_receipt_id": asset.creation_receipt_id,
                    "input_artifact_ids": list(asset.input_artifact_ids),
                    "usage_license": asset.usage_license}
                value["measurements"] = _reference_measurements(asset)
            if plan and aid == plan["replace_asset_id"]:
                value["source_status"] = "AUTHORING_PLACEHOLDER_NOT_ACCEPTED_STATE"
            references.append(value)
        state = None
        if plan is not None:
            expected = {"source_shot_id": plan["source_shot_id"], "frame_index": plan["frame_index"],
                        "original_asset_id": plan["replace_asset_id"]}
            conditioning = plan.get("conditioning", "extracted_frame")
            bound = [aid for aid, evidence in replacements.items()
                if all(evidence.get(key) == value for key, value in expected.items())
                and evidence.get("conditioning", "extracted_frame") == conditioning]
            video_ids = sorted({evidence["video_asset_id"] for evidence in replacements.values()
                if evidence.get("conditioning") == "source_video"
                and all(evidence.get(key) == value for key, value in expected.items())
                and isinstance(evidence.get("video_asset_id"), str)})
            video_inputs = sorted({reference["asset_id"] for reference in row.get("generation", {}).get("references", [])
                if reference.get("role") == "existing_video"})
            exact_video_binding = (conditioning != "source_video"
                or (len(video_ids) == 1 and video_ids == video_inputs))
            state = {**deepcopy(plan), "input_kind": conditioning,
                "binding_status": "DECLARED_BINDING_REQUIRES_GATE" if bound and exact_video_binding
                    else "PENDING_ACCEPTED_SOURCE",
                "bound_asset_ids": bound if exact_video_binding else [],
                "accepted_video_asset_ids": video_ids if exact_video_binding else [],
                "provider_admission": "NOT_EVALUATED",
                "state_acceptance": "NOT_EVALUATED",
                "required_evidence": ["source_exact_mp4_per_shot_pass", "approved_state_reference",
                    "exact_extraction_and_reference_binding",
                    *( ["same_accepted_original_video_reference_binding"] if conditioning == "source_video" else []),
                    "selected_provider_input_admission", "successor_own_per_shot_pass"]}
        shot = row["shot"]
        output_need = generation.get("output_need", {})
        candidate_video_asset_ids = [reference["asset_id"] for reference in generation_references
            if reference.get("role") == "existing_video"]
        shots.append({"occurrence_id": row["occurrence_id"], "shot_id": shot["shot_id"],
            "visual_style_control": visual_style_report(row, registry),
            "performance_control": performance_authoring_report(
                intent=generation.get("generation_intent"),
                characters=tuple(shot.get("character_ids", ())),
                prompt_text=shot["intent"]),
            "production_control": production_responsibility_report(qa_policy=qa_policy,
                shot=authored.get(shot["shot_id"]), target_shot_id=shot["shot_id"],
                qa_authority=qa_authority),
            "source_text": unit["source_text"], "authored_text": shot["intent"],
            "dialogue": shot.get("dialogue", ""), "narration": shot.get("narration", ""),
            "source_settings": deepcopy(unit.get("observed_parameters", {})),
            "generation_intent": deepcopy(generation.get("generation_intent")),
            "generation_requirements": {name: deepcopy(generation.get(name)) for name in
                ("generation_operation", "audio_need", "quality_need", "output_need")},
            "references": references, "boundary": deepcopy(row.get("boundary")),
            "reference_inventory": _reference_inventory(generation_references, assets),
            "independent_character_evidence": "NOT_EVALUATED",
            "selected_route": "NOT_EVALUATED",
            "whitebox_reference": {"candidate_video_asset_ids": candidate_video_asset_ids,
                "purpose_validation": "NOT_EVALUATED",
                "timing_validation": "NOT_EVALUATED"},
            "state_reference": state, "composition": deepcopy(row.get("composition")),
            "requested_duration_seconds": deepcopy(output_need.get("duration_seconds")),
            "provider_admission": "NOT_EVALUATED", "per_shot_acceptance": "NOT_EVALUATED"})
    return {"schema_version": "canvas-production-preflight/1", "project_id": direction["project_id"],
        "production_control": production_responsibility_report(qa_policy=qa_policy,
            qa_authority=qa_authority),
        "source_snapshot_sha256": packet["source_snapshot_sha256"],
        "director_content_hash": direction_reference(packet, direction).content_hash,
        "generation_order": [row["shot"]["shot_id"] for row in rows],
        "composition_order": [by_occurrence[occurrence] for occurrence in
            direction.get("composition_order", list(by_occurrence))],
        "shots": shots, "cut_requirements": deepcopy(direction.get("cut_requirements", {})),
        "required_before_paid_submit": ["review_all_shot_reference_roles_and_sources",
            "verify_downstream_input_route_not_just_first_shot_capability",
            "exact_preview_authorization_budget_and_one_use_permit"],
        "proof_boundary": "Read-only preparation; registered or derived bytes do not prove Provider admission. "
            "An extracted frame is not a Provider-returned tail image or an original video. "
            "Future dependencies are not a Provider prohibition or permission.",
        "production_acceptance": "NOT_EVALUATED"}
