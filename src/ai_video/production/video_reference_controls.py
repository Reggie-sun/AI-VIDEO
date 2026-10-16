"""Read-only explanation of an existing selection, never a route or QA owner."""

from collections import defaultdict

from ai_video.production.video import ResolvedVideoGenerationRequest


def video_reference_control_report(*, request, native_parameters=None, requirement=None,
                                   expressions=()):
    """Join compiled input order to semantic evidence without materializing media.

    Native scalar parameters come from the selected adapter's payload builder.
    Content locators are deliberately absent: bytes/materialization, admission,
    paid authority and output quality still require their existing owners.
    """
    request = ResolvedVideoGenerationRequest.model_validate(request.model_dump(mode="python"))
    if requirement is not None and requirement.requirement_hash != request.requirement_hash:
        raise ValueError("reference control preview requires the exact compiled requirement")
    known_layout = request.provider_name in {"minimax_h3_max", "metaso_h3", "seedance"}
    evidence = () if requirement is None else requirement.asset_evidence
    references, groups, counters = [], defaultdict(list), defaultdict(int)
    for position, binding in enumerate((*request.image_bindings, *request.media_bindings), 1):
        is_image = position <= len(request.image_bindings)
        kind = "image" if is_image else binding.kind
        counters[kind] += 1
        native_role = ("reference_image" if is_image and binding.role == "reference"
                       else binding.role) if known_layout else "NOT_EVALUATED"
        semantics = [e.model_dump(mode="json") for e in evidence
            if e.asset_id == binding.asset_id and e.asset_sha256 == binding.asset_sha256]
        row = {**binding.model_dump(mode="json"), "kind": kind,
            "native_path": f"content[{position}]" if known_layout else "NOT_EVALUATED",
            "native_role": native_role, "per_kind_index": counters[kind],
            "semantic_evidence": semantics, "provider_admission": "NOT_EVALUATED"}
        references.append(row)
        groups[(binding.asset_sha256, binding.size_bytes, binding.mime_type)].append(binding.asset_id)
    roles = {r["native_role"] for r in references}
    endpoint = "API_ENDPOINT_INPUT"
    guidance = "MODEL_GUIDANCE" if known_layout else "NOT_EVALUATED"
    controls = [
        ("opening_frame", endpoint if "first_frame" in roles else guidance,
         "first_frame is a native endpoint input; reference_image plus prompt is guidance only."),
        ("closing_frame", endpoint if "last_frame" in roles else guidance,
         "last_frame addresses the generated endpoint, not an earlier adopted cut."),
        ("character_identity", guidance,
         "Semantic Character ownership and exact reference bytes do not guarantee identity or cast count."),
        ("action_timing", guidance,
         "Prompt timing and reference motion guide the model; duration is not an event-time constraint."),
        ("space_camera", guidance,
         "Layout, axis, optics, reflections and camera intent require actual output observation."),
        ("whitebox_motion", "MODEL_REFERENCE" if "reference_video" in roles else "UNBOUND",
         "A video binding is not proof of whitebox purpose, faithful geometry or motion inheritance."),
    ]
    output = request.effective_output.model_dump(mode="json")
    role_targets = {"opening_frame": {"first_frame"}, "closing_frame": {"last_frame"},
        "character_identity": {"reference_image", "first_frame", "last_frame"},
        "action_timing": {"reference_video"}, "space_camera": {"reference_image", "reference_video"},
        "whitebox_motion": {"reference_video"}}
    intent_targets = {"opening_frame": ("open_state",), "closing_frame": ("close_state", "subject_endpoint"),
        "character_identity": ("identity_continuity",),
        "action_timing": ("subject_action", "motion_intent"),
        "space_camera": ("scene_continuity", "camera_intent", "camera_endpoint", "primary_camera_motion"),
        "whitebox_motion": ()}
    intent = {} if requirement is None else requirement.generation_intent.model_dump(mode="json")
    return {"schema_version": "video-reference-control-preview/1",
        "selected_route": {"provider_name": request.provider_name, "model_id": request.model_id,
            "mode": request.mode.value, "capability_id": request.capability_id,
            "provider_profile": request.provider_profile.model_dump(mode="json"),
            "adapter_compiler_id": request.adapter_compiler_id,
            "adapter_compiler_version": request.adapter_compiler_version,
            "resolved_generation_hash": request.resolved_generation_hash,
            "requirement_hash": request.requirement_hash},
        "native_parameters": native_parameters if native_parameters is not None else "NOT_EVALUATED",
        "prompt": {"text": request.prompt_text, "binding": "exact_compiled_request"},
        "references": references,
        "reference_summary": {"binding_count": len(references), "unique_byte_count": len(groups),
            "same_bytes": [{"sha256": key[0], "size_bytes": key[1], "mime_type": key[2],
                "asset_ids": ids} for key, ids in groups.items() if len(ids) > 1],
            "deduplication": "NONE; semantic owners and native indices are preserved",
            "independent_character_evidence": "NOT_EVALUATED"},
        "controls": [{"target": target, "mechanism": mechanism, "limitation": limitation,
            "authored_fields": {f"generation_intent.{key}": intent[key]
                for key in intent_targets[target] if key in intent},
            "native_reference_paths": [r["native_path"] for r in references
                if r["native_role"] in role_targets[target]],
            "actual_quality": "NOT_EVALUATED"} for target, mechanism, limitation in controls],
        "timing": {"generation_output": output,
            "reference_media": [r for r in references if r["kind"] in {"video", "audio"}],
            "adopted_cut": "ResolvedTimeline owns final trim/frame/sample/timing",
            "whitebox_purpose_and_alignment": "NOT_EVALUATED"},
        "acceptance_requirements": [rule.model_dump(mode="json") for rule in expressions],
        "materialization": "NOT_EVALUATED", "actual_quality": "NOT_EVALUATED",
        "proof_boundary": "Exact compiled selection and parameter projection only; no media lookup, "
            "credential, transport, permit, state write, QA or authorization. Frame roles and "
            "multimodal references cannot be combined by silently dropping either obligation."}


def prepared_generation_report(prepared):
    """JSON-safe existing prepare result; never copy or serialize runtime objects."""
    def dump(value):
        return None if value is None else value.model_dump(mode="json")

    reference_control = {"selected_route": "NOT_EVALUATED", "actual_quality": "NOT_EVALUATED"}
    if prepared.resolved_request is not None:
        parameters = None
        # These two API families expose a pure scalar view of their actual
        # payload builder. Other adapters remain explicitly unevaluated.
        if prepared.resolved_request.provider_name in {"minimax_h3_max", "metaso_h3", "seedance"}:
            parameters = prepared.provider.native_control_parameters(prepared.resolved_request)
        binding = prepared.execution_binding
        selected = next((c for c in prepared.inputs.candidates
            if c.candidate_id == prepared.decision.selected_candidate_id), None)
        reference_control = video_reference_control_report(request=prepared.resolved_request,
            native_parameters=parameters,
            requirement=binding.projection.requirement if binding is not None else None,
            expressions=selected.recipe.expressions if selected is not None else ())
    return {"inputs": dump(prepared.inputs), "decision": dump(prepared.decision),
        "compilation": dump(prepared.compilation), "resolved_request": dump(prepared.resolved_request),
        "execution_binding": dump(prepared.execution_binding), "target_shot_id": prepared.target_shot_id,
        "reference_control": reference_control, "production_acceptance": "NOT_EVALUATED"}
