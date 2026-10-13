"""Read-only filmmaking preparation from the existing source and asset owners.

Provenance, planned handoff and Provider admission are different facts. This
projection never certifies an input, authorizes a submit or owns lifecycle.
"""
from copy import deepcopy

from ai_video.canvas_authoring import direction_reference


def canvas_reference_preflight(*, packet, direction, registry):
    """Project inputs already validated by author_canvas_project; no verdicts."""
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
        for reference in row.get("generation", {}).get("references", []):
            aid = reference["asset_id"]
            asset = assets.get(aid)
            value = {"asset_id": aid, "role": reference["role"],
                "provider_admission": "NOT_EVALUATED",
                "source_status": "MISSING" if asset is None else "REGISTERED_BYTES"}
            if asset is not None:
                value["identity"] = {"sha256": asset.sha256, "size_bytes": asset.size_bytes,
                    "mime_type": asset.mime_type, "source_kind": asset.source_kind.value,
                    "tool": asset.tool.model_dump(mode="json"),
                    "creation_receipt_id": asset.creation_receipt_id,
                    "input_artifact_ids": list(asset.input_artifact_ids),
                    "usage_license": asset.usage_license}
            if plan and aid == plan["replace_asset_id"]:
                value["source_status"] = "AUTHORING_PLACEHOLDER_NOT_ACCEPTED_STATE"
            references.append(value)
        state = None
        if plan is not None:
            expected = {"source_shot_id": plan["source_shot_id"], "frame_index": plan["frame_index"],
                        "original_asset_id": plan["replace_asset_id"]}
            bound = [aid for aid, evidence in replacements.items() if evidence == expected]
            state = {**deepcopy(plan), "input_kind": "extracted_frame",
                "binding_status": "DECLARED_BINDING_REQUIRES_GATE" if bound else "PENDING_ACCEPTED_SOURCE",
                "bound_asset_ids": bound, "provider_admission": "NOT_EVALUATED",
                "state_acceptance": "NOT_EVALUATED",
                "required_evidence": ["source_exact_mp4_per_shot_pass", "approved_state_reference",
                    "exact_extraction_and_reference_binding", "selected_provider_input_admission",
                    "successor_own_per_shot_pass"]}
        shot = row["shot"]
        shots.append({"occurrence_id": row["occurrence_id"], "shot_id": shot["shot_id"],
            "source_text": unit["source_text"], "authored_text": shot["intent"],
            "dialogue": shot.get("dialogue", ""), "narration": shot.get("narration", ""),
            "source_settings": deepcopy(unit.get("observed_parameters", {})),
            "generation_intent": deepcopy(row.get("generation", {}).get("generation_intent")),
            "generation_requirements": {name: deepcopy(row.get("generation", {}).get(name)) for name in
                ("generation_operation", "audio_need", "quality_need", "output_need")},
            "references": references, "boundary": deepcopy(row.get("boundary")),
            "state_reference": state, "composition": deepcopy(row.get("composition")),
            "provider_admission": "NOT_EVALUATED", "per_shot_acceptance": "NOT_EVALUATED"})
    return {"schema_version": "canvas-production-preflight/1", "project_id": direction["project_id"],
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
