"""Read-only projection of authored input controls and an existing selection."""

from collections import defaultdict
from collections.abc import Mapping
from enum import Enum

from ai_video.production.video import ResolvedVideoGenerationRequest


_NOT_EVALUATED = "NOT_EVALUATED"
_MECHANISM_BY_DECLARATION = {
    "prompt_guidance": "MODEL_GUIDANCE",
    "reference_guidance": "MODEL_REFERENCE",
    "first_frame": "API_ENDPOINT_INPUT",
    "last_frame": "API_ENDPOINT_INPUT",
    "native_output": "API_PARAMETER_INPUT",
}


def _json_value(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _path_value(value, path):
    current = value
    for part in path.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return False, None
            current = current[part]
        elif isinstance(current, (tuple, list)) and part.isdecimal():
            index = int(part)
            if index >= len(current):
                return False, None
            current = current[index]
        elif current is not None and hasattr(current, part):
            current = getattr(current, part)
        else:
            return False, None
    return True, _json_value(current)


def _intent_value(requirement, path):
    if requirement is None:
        return False, None
    root, separator, remainder = path.partition(".")
    if root in {"generation_intent", "output_need", "audio_need", "quality_need",
                "semantic_reference_roles", "media_reference_asset_ids"}:
        root_value = getattr(requirement, root, None)
        if root_value is None and hasattr(requirement, "model_dump"):
            root_value = requirement.model_dump(mode="json").get(root)
        if not separator:
            return (root_value is not None, _json_value(root_value))
        return _path_value(root_value, remainder)
    if hasattr(requirement, "model_dump"):
        return _path_value(requirement.model_dump(mode="json"), path)
    return False, None


def _control_for(rule):
    control = getattr(rule, "input_control", None)
    if control is None:
        return None
    return control


def _issue_paths(expressions, unsupported_paths):
    """Associate typed compiler rejection paths with only the authored objectives they hit."""
    normalized = tuple(str(path) for path in unsupported_paths)
    result = {}
    for rule in expressions:
        if rule.stage != "raw_generation" or rule.level == "diagnostic":
            result[rule.requirement_id] = ()
            continue
        hits = tuple(sorted({field for field in normalized
            if field == rule.requirement_id or any(
                field == path or field.startswith(path + ".") or path.startswith(field + ".")
                for path in rule.intent_paths)}))
        result[rule.requirement_id] = hits
    return result


def _reference_duties(expressions, references):
    from ai_video.production._video_requirement_routing import native_binding_role
    from ai_video.production.video_requirement import SemanticReferenceRole

    rows_by_requirement = {}
    whitebox_paths = []
    for rule in expressions:
        duties = []
        control = _control_for(rule)
        for duty in (() if control is None else control.references):
            authored = _json_value(duty)
            candidates = [reference for reference in references
                if reference["asset_id"] == duty.asset_id
                and reference["asset_sha256"] == duty.asset_sha256
                and reference["role"] == native_binding_role(SemanticReferenceRole(duty.role))]
            joined = []
            evidence_rows = []
            for reference in candidates:
                matching_semantics = [item for item in reference["semantic_evidence"]
                    if item["role"] == duty.role
                    and item["asset_id"] == duty.asset_id
                    and item["asset_sha256"] == duty.asset_sha256
                    and (duty.canonical_owner_id is None
                         or item["canonical_owner_id"] == duty.canonical_owner_id)]
                if not matching_semantics:
                    continue
                native_binding = {key: reference[key] for key in (
                    "native_path", "native_role", "kind", "mime_type", "asset_id", "asset_sha256")}
                joined.append(native_binding)
                evidence_rows.extend(matching_semantics)
            video_whitebox = (duty.purpose == "whitebox" and any(
                binding["kind"] == "video"
                and str(binding["mime_type"]).startswith("video/")
                and binding["native_role"] == "reference_video"
                for binding in joined))
            static_whitebox = (duty.purpose == "whitebox" and any(
                binding["kind"] == "image"
                and str(binding["mime_type"]).startswith("image/")
                and binding["native_role"] in {"reference_image", "first_frame", "last_frame"}
                for binding in joined))
            if video_whitebox:
                whitebox_paths.extend(binding["native_path"] for binding in joined
                    if binding["kind"] == "video"
                    and str(binding["mime_type"]).startswith("video/")
                    and binding["native_role"] == "reference_video")
            endpoint_whitebox = (static_whitebox and any(
                binding["native_role"] in {"first_frame", "last_frame"} for binding in joined))
            if duty.purpose != "whitebox":
                whitebox_disposition = "NOT_DECLARED"
                whitebox_intent = "NOT_APPLICABLE"
            elif video_whitebox:
                whitebox_disposition = "MODEL_REFERENCE"
                whitebox_intent = "DYNAMIC_VIDEO_REFERENCE"
            elif static_whitebox:
                whitebox_disposition = "API_ENDPOINT_INPUT" if endpoint_whitebox else "MODEL_REFERENCE"
                whitebox_intent = "STATIC_LAYOUT"
            else:
                whitebox_disposition = "UNBOUND"
                whitebox_intent = "UNBOUND"
            duties.append({**authored, "scope_text": duty.scope_text,
                "mime_types": sorted({str(binding["mime_type"]) for binding in joined}),
                "native_bindings": joined,
                "semantic_evidence": evidence_rows,
                "whitebox_disposition": whitebox_disposition,
                "whitebox_intent": whitebox_intent,
                "whitebox_quality": _NOT_EVALUATED})
        rows_by_requirement[rule.requirement_id] = duties
    return rows_by_requirement, tuple(dict.fromkeys(whitebox_paths))


def _objectives(*, expressions, requirement, request, compilation, references):
    from ai_video.production.generation_input_control import input_control_issues

    declared = any(_control_for(rule) is not None for rule in expressions)
    issue_map = {}
    if request is not None and requirement is not None:
        # Keep the compiler's exact shared mapping checks as the only coverage validator.
        issue_map = input_control_issues(expressions, requirement, request.prompt_text)
    unsupported_paths = tuple(getattr(compilation, "unsupported_field_paths", ()))
    unsupported_by_requirement = _issue_paths(expressions, unsupported_paths)
    duty_rows, whitebox_paths = _reference_duties(expressions, references)
    rows = []
    for rule in expressions:
        control = _control_for(rule)
        exact_native = tuple(rule.native_text)
        if request is None:
            native_text_present = "AUTHORED_NOT_COMPILED"
            native_text_status = "AUTHORED_NOT_COMPILED"
        else:
            native_text_present = all(text in request.prompt_text for text in exact_native)
            native_text_status = "PRESENT" if native_text_present else "MISSING"
        if request is None:
            coverage = ("UNSUPPORTED_INPUT" if unsupported_by_requirement[rule.requirement_id]
                        else _NOT_EVALUATED)
            mechanism = _NOT_EVALUATED
        elif requirement is None:
            coverage = _NOT_EVALUATED
            mechanism = _NOT_EVALUATED
        elif rule.requirement_id in issue_map:
            coverage = "UNSUPPORTED_INPUT"
            mechanism = _MECHANISM_BY_DECLARATION.get(
                getattr(control, "mechanism", None), _NOT_EVALUATED)
        elif declared and control is not None:
            coverage = "EXPRESSED_INPUT_ONLY"
            mechanism = _MECHANISM_BY_DECLARATION[control.mechanism]
        else:
            coverage = _NOT_EVALUATED
            mechanism = _NOT_EVALUATED
        values, unresolved = {}, []
        for path in rule.intent_paths:
            found, value = _intent_value(requirement, path)
            if found:
                values[path] = value
            else:
                unresolved.append(path)
        rows.append({
            "requirement_id": rule.requirement_id,
            "observable": rule.observable,
            "level": rule.level,
            "stage": rule.stage,
            "proof": rule.proof,
            "measurement": rule.measurement,
            "tolerance": rule.tolerance,
            "intent_paths": list(rule.intent_paths),
            "intent_values": values,
            "unresolved_intent_paths": unresolved,
            "native_text": list(exact_native),
            "native_text_present": native_text_present,
            "native_text_status": native_text_status,
            "mechanism": mechanism,
            "authored_mechanism": getattr(control, "mechanism", "NOT_DECLARED"),
            "reference_duties": duty_rows[rule.requirement_id],
            "input_coverage": coverage,
            "input_issues": list(issue_map.get(rule.requirement_id, ())),
            "unsupported_field_paths": list(unsupported_by_requirement[rule.requirement_id]),
            "actual_quality": _NOT_EVALUATED,
        })
    return rows, whitebox_paths


def video_reference_control_report(*, request=None, native_parameters=None, requirement=None,
                                   expressions=(), compilation=None):
    """Join authored controls to one exact request, without materialization or QA claims."""
    from ai_video.production._video_requirement_routing import native_binding_role

    if request is not None:
        request = ResolvedVideoGenerationRequest.model_validate(request.model_dump(mode="python"))
        if requirement is not None and requirement.requirement_hash != request.requirement_hash:
            raise ValueError("reference control preview requires the exact compiled requirement")

    known_layout = request is not None and request.provider_name in {
        "minimax_h3_max", "metaso_h3", "seedance"}
    evidence = () if requirement is None else requirement.asset_evidence
    references, groups, counters = [], defaultdict(list), defaultdict(int)
    if request is not None:
        for position, binding in enumerate((*request.image_bindings, *request.media_bindings), 1):
            is_image = position <= len(request.image_bindings)
            kind = "image" if is_image else binding.kind
            counters[kind] += 1
            native_role = ("reference_image" if is_image and binding.role == "reference"
                else binding.role) if known_layout else _NOT_EVALUATED
            semantics = [item.model_dump(mode="json") for item in evidence
                if item.asset_id == binding.asset_id and item.asset_sha256 == binding.asset_sha256
                and native_binding_role(item.role) == binding.role]
            row = {**binding.model_dump(mode="json"), "kind": kind,
                "native_path": f"content[{position}]" if known_layout else _NOT_EVALUATED,
                "native_role": native_role, "per_kind_index": counters[kind],
                "semantic_evidence": semantics, "provider_admission": _NOT_EVALUATED}
            references.append(row)
            groups[(binding.asset_sha256, binding.size_bytes, binding.mime_type)].append(binding.asset_id)

    objectives, whitebox_paths = _objectives(expressions=expressions, requirement=requirement,
        request=request, compilation=compilation, references=references)
    roles = {row["native_role"] for row in references}
    if request is None:
        endpoint = guidance = _NOT_EVALUATED
    else:
        endpoint = "API_ENDPOINT_INPUT"
        guidance = "MODEL_GUIDANCE" if known_layout else _NOT_EVALUATED
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
        ("whitebox_motion", "MODEL_REFERENCE" if whitebox_paths else (
            "UNBOUND" if request is not None else _NOT_EVALUATED),
         "Only an explicit whitebox duty joined to an exact video reference is shown as whitebox guidance."),
    ]
    intent_targets = {
        "opening_frame": ("generation_intent.open_state",),
        "closing_frame": ("generation_intent.close_state", "generation_intent.subject_action.endpoint"),
        "character_identity": ("generation_intent.identity_continuity",),
        "action_timing": ("generation_intent.subject_action", "generation_intent.motion_envelope",
            "generation_intent.pacing"),
        "space_camera": ("generation_intent.scene_continuity", "generation_intent.camera_intent",
            "generation_intent.camera_endpoint", "generation_intent.primary_camera_motion"),
        "whitebox_motion": (),
    }
    role_targets = {"opening_frame": {"first_frame"}, "closing_frame": {"last_frame"},
        "character_identity": {"reference_image", "first_frame", "last_frame"},
        "action_timing": {"reference_video"}, "space_camera": {"reference_image", "reference_video"},
        "whitebox_motion": set()}
    overview = []
    for target, mechanism, limitation in controls:
        authored_fields = {}
        for path in intent_targets[target]:
            found, value = _intent_value(requirement, path)
            if found:
                authored_fields[path] = value
        if target == "whitebox_motion":
            native_paths = list(whitebox_paths)
        else:
            native_paths = [row["native_path"] for row in references
                if row["native_role"] in role_targets[target]]
        overview.append({"target": target, "mechanism": mechanism,
            "limitation": limitation, "authored_fields": authored_fields,
            "native_reference_paths": native_paths, "actual_quality": _NOT_EVALUATED})

    output = request.effective_output.model_dump(mode="json") if request is not None else _NOT_EVALUATED
    unsupported_paths = list(getattr(compilation, "unsupported_field_paths", ()))
    compilation_projection = (_NOT_EVALUATED if compilation is None else {
        "outcome": getattr(compilation, "outcome", _NOT_EVALUATED),
        "unsupported_field_paths": unsupported_paths,
    })
    return {
        "schema_version": "video-reference-control-preview/2",
        "selected_route": ({"provider_name": request.provider_name, "model_id": request.model_id,
            "mode": request.mode.value, "capability_id": request.capability_id,
            "provider_profile": request.provider_profile.model_dump(mode="json"),
            "adapter_compiler_id": request.adapter_compiler_id,
            "adapter_compiler_version": request.adapter_compiler_version,
            "resolved_generation_hash": request.resolved_generation_hash,
            "requirement_hash": request.requirement_hash} if request is not None else _NOT_EVALUATED),
        "native_parameters": native_parameters if native_parameters is not None else _NOT_EVALUATED,
        "compilation": compilation_projection,
        "prompt": ({"text": request.prompt_text, "binding": "exact_compiled_request"}
            if request is not None else {"text": _NOT_EVALUATED, "binding": "not_compiled"}),
        "references": references,
        "reference_summary": {
            "binding_count": len(references) if request is not None else _NOT_EVALUATED,
            "unique_byte_count": len(groups) if request is not None else _NOT_EVALUATED,
            "same_bytes": ([{"sha256": key[0], "size_bytes": key[1], "mime_type": key[2],
                "asset_ids": ids} for key, ids in groups.items() if len(ids) > 1]
                if request is not None else _NOT_EVALUATED),
            "deduplication": "NONE; semantic owners and native indices are preserved",
            "independent_character_evidence": _NOT_EVALUATED},
        "controls_scope": "MODE_OVERVIEW_ONLY",
        "controls": overview,
        "objectives": objectives,
        "timing": {"generation_output": output,
            "reference_media": ([row for row in references if row["kind"] in {"video", "audio"}]
                if request is not None else _NOT_EVALUATED),
            "adopted_cut": "ResolvedTimeline owns final trim/frame/sample/timing",
            "whitebox_purpose_and_alignment": _NOT_EVALUATED},
        "acceptance_requirements": [rule.model_dump(mode="json") for rule in expressions],
        "materialization": _NOT_EVALUATED,
        "actual_quality": _NOT_EVALUATED,
        "proof_boundary": "Exact authored objectives and, when present, one compiled selection only; "
            "input coverage means expressibility, not model compliance or media quality. No media lookup, "
            "credential, transport, permit, state write, QA or authorization. Frame roles and multimodal "
            "references cannot be combined by silently dropping either obligation.",
    }


def prepared_generation_report(prepared):
    """JSON-safe existing prepare result; never copy or serialize runtime objects."""
    def dump(value):
        return None if value is None else value.model_dump(mode="json")

    selected = next((candidate for candidate in prepared.inputs.candidates
        if candidate.candidate_id == prepared.decision.selected_candidate_id), None)
    expressions = selected.recipe.expressions if selected is not None else ()
    binding = prepared.execution_binding
    requirement = binding.projection.requirement if binding is not None else None
    if prepared.resolved_request is not None:
        parameters = None
        # These API families expose a pure scalar view of the actual payload builder.
        if prepared.resolved_request.provider_name in {"minimax_h3_max", "metaso_h3", "seedance"}:
            parameters = prepared.provider.native_control_parameters(prepared.resolved_request)
        reference_control = video_reference_control_report(request=prepared.resolved_request,
            native_parameters=parameters, requirement=requirement, expressions=expressions,
            compilation=prepared.compilation)
    else:
        reference_control = video_reference_control_report(requirement=requirement,
            expressions=expressions, compilation=prepared.compilation)
    return {"inputs": dump(prepared.inputs), "decision": dump(prepared.decision),
        "compilation": dump(prepared.compilation), "resolved_request": dump(prepared.resolved_request),
        "execution_binding": dump(prepared.execution_binding), "target_shot_id": prepared.target_shot_id,
        "reference_control": reference_control,
        "router_assessments": [assessment.model_dump(mode="json")
            for assessment in prepared.decision.assessments],
        "production_acceptance": _NOT_EVALUATED}
