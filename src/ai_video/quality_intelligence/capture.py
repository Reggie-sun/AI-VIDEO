"""Explicit no-network post-QA projection into Quality Experience v1."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ai_video.quality_intelligence._capture_contracts import (
    CaptureErrorCode,
    PostQaAnalyzerDocument,
    PostQaHumanReviewDocument,
    PostQaHumanReviewMetadata,
    PostQaQ0CaptureRequest,
    QualityExperienceCaptureError,
)
from ai_video.quality_intelligence._capture_human import build_human_review
from ai_video.quality_intelligence._capture_p6 import reopen_p6_pointers
from ai_video.quality_intelligence.models import (
    AnalyzerBinding,
    AnalyzerEvidenceItem,
    AttemptLineage,
    ArtifactEvidenceKnown,
    BoundedFreeText,
    CanonicalRuntimeBoundary,
    ContinuityBinding,
    ContinuityEvidenceBinding,
    DurabilityBinding,
    ExactEvidencePointer,
    EvidenceHex64,
    EvidencePath,
    EvidenceScalar,
    EvidenceState,
    EvidenceString,
    InputBinding,
    InputBindings,
    NamedParameters,
    OutcomeBoundaryBinding,
    OutcomeSucceeded,
    ParameterBinding,
    ParameterSource,
    ParameterSources,
    PlanningBinding,
    PromptBinding,
    ProviderBinding,
    QualityExperienceRecordV1,
    QualityRecordPointer,
    RecordIdentity,
    ReplayCounters,
    RoutingBinding,
)
from ai_video.quality_intelligence.store import (
    QualityExperienceConflict,
    QualityExperienceStore,
)
from ai_video.production._video_project_reader import (
    load_generated_shot_continuity_evidence,
    load_local_video_fetch_receipt,
    load_video_fetch_receipt,
    load_video_probe_receipt,
    load_video_provenance_receipt,
    load_video_request_receipt,
    load_continuity_evaluation_intent,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import VideoAttemptPhase
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.project import (
    load_production_project,
    load_production_project_candidate,
)
from ai_video.production.review import (
    QaVerdict,
    TrackedGeneratedShotContinuityMeasurements,
    adjudicate_generated_shot_continuity,
)


def _reject(code: CaptureErrorCode) -> QualityExperienceCaptureError:
    return QualityExperienceCaptureError(code)


def _source_string(value: str, document: str, span: str) -> EvidenceString:
    return EvidenceString(
        state=EvidenceState.KNOWN,
        value=value,
        source_document=document,
        source_span=span,
    )


def _source_hex(value: str, document: str, span: str) -> EvidenceHex64:
    return EvidenceHex64(
        state=EvidenceState.KNOWN,
        value=value,
        source_document=document,
        source_span=span,
    )


def _not_applicable_string(reason: str) -> EvidenceString:
    return EvidenceString(state=EvidenceState.NOT_APPLICABLE, reason=reason)


def _not_applicable_hex(reason: str) -> EvidenceHex64:
    return EvidenceHex64(state=EvidenceState.NOT_APPLICABLE, reason=reason)


def _validate_analyzer(
    analyzer: AnalyzerBinding,
    *,
    project_root: Path,
    documents: tuple[PostQaAnalyzerDocument, ...],
    asset_id: str,
    artifact_sha256: str,
    continuity_score: float,
) -> AnalyzerBinding:
    if analyzer.state != "known" or not analyzer.evidence:
        raise _reject(CaptureErrorCode.NOT_READY)
    document_by_id = {item.evidence_id: item for item in documents}
    if (
        len(document_by_id) != len(documents)
        or set(document_by_id) != {item.evidence_id for item in analyzer.evidence}
    ):
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    for item in analyzer.evidence:
        document = document_by_id[item.evidence_id]
        reopened = _read_regular_file_nofollow(
            project_root / document.relative_path,
            contained_by=project_root / "analysis",
        )
        if (
            reopened.file_sha256 != document.file_sha256
            or document.artifact_sha256 != artifact_sha256
            or AnalyzerEvidenceItem.model_validate_json(reopened.data) != item
        ):
            raise _reject(CaptureErrorCode.BINDING_INVALID)
        parameters = item.measurements.parameters
        score = next(
            (
                measurement.value.value
                for measurement in parameters
                if measurement.key == "continuity_score"
            ),
            None,
        )
        sources = tuple(
            (measurement.value.source_document, measurement.value.source_span)
            for measurement in parameters
        )
        measurements_hash = canonical_sha256(
            item.measurements.model_dump(mode="json")
        )
        span_hash = canonical_sha256(
            {
                "domain": "ai-video.q0.analyzer-span/v1",
                "artifact_sha256": artifact_sha256,
                "sources": sources,
            }
        )
        evidence_hash = canonical_sha256(
            {
                "domain": "ai-video.q0.analyzer-evidence/v1",
                "evidence_id": item.evidence_id,
                "tool_name": item.tool_name,
                "tool_version": item.tool_version,
                "measurement_contract_version": (
                    item.measurement_contract_version
                ),
                "subject_id": item.subject_id,
                "artifact_sha256": artifact_sha256,
                "span_hash": span_hash,
                "measurements_hash": measurements_hash,
            }
        )
        if (
            item.subject_id != asset_id
            or score != continuity_score
            or any(
                measurement.value.source_document != document.relative_path
                or not measurement.value.source_span
                for measurement in parameters
            )
            or item.measurements_hash != measurements_hash
            or item.span_hash != span_hash
            or item.evidence_hash != evidence_hash
        ):
            raise _reject(CaptureErrorCode.BINDING_INVALID)
    return analyzer


def _continuity_evidence_binding(
    evaluation,
    intent,
    evidence,
) -> ContinuityEvidenceBinding:
    measurements = evidence.raw_measurements
    fallback = (
        measurements.fallback_evidence
        if isinstance(measurements, TrackedGeneratedShotContinuityMeasurements)
        else None
    )
    evidence_document = evaluation.evidence.path.as_posix()
    return ContinuityEvidenceBinding(
        intent=ExactEvidencePointer(
            kind="continuity_intent",
            relative_path=evaluation.intent.path.as_posix(),
            content_hash=evaluation.intent.content_hash,
            file_sha256=evaluation.intent.file_sha256,
            freshness="fresh",
        ),
        evidence=ExactEvidencePointer(
            kind="continuity_evidence",
            relative_path=evidence_document,
            content_hash=evaluation.evidence.content_hash,
            file_sha256=evaluation.evidence.file_sha256,
            freshness="fresh",
        ),
        evaluation_fingerprint=evidence.evaluation_fingerprint,
        artifact_sha256=evidence.artifact_sha256,
        resolved_generation_hash=evidence.resolved_generation_hash,
        target_shot_content_hash=evidence.target_shot_content_hash,
        constraints_hash=evidence.continuity_constraints_hash,
        qa_policy_hash=evidence.qa_policy_content_hash,
        evaluator_profile_hash=intent.evaluator_profile_content_hash,
        evaluator_identity=f"{evidence.evaluator.name}:{evidence.evaluator.version}",
        authority_binding_hash=canonical_sha256(
            {
                "domain": "ai-video.q0.continuity-authority/v1",
                "qa_policy_hash": evidence.qa_policy_content_hash,
                "evaluator": evidence.evaluator.model_dump(mode="json"),
            }
        ),
        human_fallback_hash=(
            EvidenceHex64(
                state=EvidenceState.KNOWN,
                value=fallback.content_hash,
                source_document=evidence_document,
                source_span="raw_measurements.fallback_evidence.content_hash",
            )
            if fallback is not None
            else EvidenceHex64(
                state=EvidenceState.NOT_APPLICABLE,
                reason="automatic_evidence_used",
            )
        ),
    )


def _build_record(request: PostQaQ0CaptureRequest) -> QualityExperienceRecordV1:
    project_root = request.project_root.resolve(strict=True)
    pilot_root = request.pilot_dataset_root.absolute()
    if pilot_root == project_root or project_root in pilot_root.parents:
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    bundle = load_production_project(project_root / "project.yaml")
    matching = tuple(
        item
        for item in bundle.manifest.attempts
        if item.attempt_id == request.attempt_id
    )
    if len(matching) != 1 or matching[0].operation != "video_generation":
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    attempt = matching[0]
    state = attempt.video_generation_state
    if state is None or bundle.manifest.schema_version != "2.10":
        raise _reject(CaptureErrorCode.NOT_READY)
    evaluation = state.continuity_evaluation
    if (
        evaluation is None
        or evaluation.phase.value != "evidenced"
        or evaluation.evidence is None
        or evaluation.probe is None
        or evaluation.provenance is None
    ):
        raise _reject(CaptureErrorCode.NOT_READY)

    resolved = load_video_request_receipt(project_root, state.request)
    base_bundle = load_production_project_candidate(
        project_root,
        bundle.manifest,
        attempt.base_project.path,
        attempt.base_registry.path,
    )
    binding = resolved.continuity_binding
    scope = resolved.activation_scope
    if binding is None or scope is None:
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    intent = load_continuity_evaluation_intent(project_root, evaluation.intent)
    evidence = load_generated_shot_continuity_evidence(
        project_root, evaluation.evidence
    )
    probe = load_video_probe_receipt(project_root, evaluation.probe)
    provenance = load_video_provenance_receipt(
        project_root, evaluation.provenance
    )
    fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
    if fetch_pointer is None:
        raise _reject(CaptureErrorCode.NOT_READY)
    fetch = (
        load_local_video_fetch_receipt(project_root, state.local_fetch_receipt)
        if state.local_fetch_receipt is not None
        else load_video_fetch_receipt(project_root, state.fetch_receipt)
    )
    policy = bundle.qa_policy
    if (
        policy is None
        or policy.content_hash != evidence.qa_policy_content_hash
        or evidence.evaluator not in policy.semantic_authorities
        or intent.evaluation_fingerprint != evidence.evaluation_fingerprint
        or intent.resolved_generation_hash != resolved.resolved_generation_hash
        or evidence.resolved_generation_hash != resolved.resolved_generation_hash
        or intent.target_shot_id != binding.target_shot_id
        or evidence.target_shot_content_hash != binding.target_shot_content_hash
        or evidence.continuity_constraints_hash != binding.constraints.content_hash
        or probe.continuity_evidence != evidence
        or probe.measured.artifact_sha256 != fetch.artifact_sha256
        or provenance.probe_receipt_id != probe.content_hash
        or provenance.artifact_sha256 != fetch.artifact_sha256
        or provenance.profile_sha256 != resolved.provider_profile.profile_sha256
    ):
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    artifact = _read_regular_file_nofollow(
        project_root / fetch_pointer.artifact_path,
        contained_by=project_root / "state" / "video-generation" / "fetch",
    )
    if (
        artifact.file_sha256 != fetch.artifact_sha256
        or len(artifact.data) != fetch.size_bytes
    ):
        raise _reject(CaptureErrorCode.BINDING_INVALID)

    verdict = adjudicate_generated_shot_continuity(evidence)
    if verdict is QaVerdict.NOT_EVALUATED:
        raise _reject(CaptureErrorCode.NOT_READY)
    continuity_score = 1.0 if verdict is QaVerdict.PASS else 0.0
    analyzer = _validate_analyzer(
        request.analyzer,
        project_root=project_root,
        documents=request.analyzer_documents,
        asset_id=resolved.output_asset_id,
        artifact_sha256=artifact.file_sha256,
        continuity_score=continuity_score,
    )

    if resolved.media_bindings or not resolved.image_bindings:
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    assets = {item.asset_id: item for item in base_bundle.registry.assets}
    input_items = []
    for runtime in resolved.image_bindings:
        asset_record = assets.get(runtime.asset_id)
        if asset_record is None or asset_record.sha256 != runtime.asset_sha256:
            raise _reject(CaptureErrorCode.BINDING_INVALID)
        input_items.append(
            InputBinding(
                role=runtime.role,
                artifact_id=runtime.asset_id,
                revision=EvidenceScalar(
                    state=EvidenceState.NOT_APPLICABLE,
                    reason="asset_revision_not_available",
                ),
                content_hash=runtime.asset_sha256,
                file_sha256=asset_record.sha256,
                mime_type=runtime.mime_type,
                size_bytes=asset_record.size_bytes,
                registry_revision=base_bundle.registry.revision_id,
                registry_file_sha256=attempt.base_registry.file_sha256,
                creation_receipt_id=asset_record.creation_receipt_id,
                creation_receipt_hash=_not_applicable_hex(
                    "input_receipt_payload_not_persisted"
                ),
                provenance_receipt_id=_not_applicable_string(
                    "input_receipt_payload_not_persisted"
                ),
                provenance_receipt_hash=_not_applicable_hex(
                    "input_receipt_payload_not_persisted"
                ),
            )
        )
    inputs = InputBindings(
        items=tuple(sorted(input_items, key=lambda item: item.sort_key))
    )

    target = next(
        (
            item
            for item in base_bundle.shots
            if item.shot_id == binding.target_shot_id
        ),
        None,
    )
    scene = (
        next(
            (
                item
                for item in base_bundle.scenes
                if item.scene_id == target.scene_id
            ),
            None,
        )
        if target is not None
        else None
    )
    if (
        target is None
        or scene is None
        or target.revision != binding.target_shot_revision
        or target.content_hash != binding.target_shot_content_hash
    ):
        raise _reject(CaptureErrorCode.BINDING_INVALID)
    manifest_raw = _read_regular_file_nofollow(
        project_root / "state/manifest.json",
        contained_by=project_root / "state",
    )
    request_document = state.request.path.as_posix()
    measured = probe.measured
    execution_kind = resolved.execution_kind.value
    billing_kind = (
        "metered" if resolved.billing_kind.value == "metered" else "unmetered"
    )
    original_seed = scope.request.seed
    requested_seed = (
        EvidenceScalar(
            state=EvidenceState.KNOWN,
            value=original_seed,
            source_document=request_document,
            source_span="activation_scope.request.seed",
        )
        if original_seed is not None
        else EvidenceScalar(
            state=EvidenceState.NOT_APPLICABLE,
            reason="caller_did_not_request_seed",
        )
    )
    effective_seed = (
        EvidenceScalar(
            state=EvidenceState.KNOWN,
            value=resolved.effective_seed,
            source_document=request_document,
            source_span="effective_seed",
        )
        if resolved.effective_seed is not None
        else EvidenceScalar(
            state=EvidenceState.NOT_APPLICABLE,
            reason="provider_has_no_effective_seed",
        )
    )
    unavailable_planning = "planning_artifact_not_persisted"
    planning = PlanningBinding(
        planning_request_hash=_not_applicable_hex(unavailable_planning),
        plan_hash=_not_applicable_hex(unavailable_planning),
        requirement_hash=(
            _source_hex(resolved.requirement_hash, request_document, "requirement_hash")
            if resolved.requirement_hash is not None
            else _not_applicable_hex(unavailable_planning)
        ),
        readiness_request_hash=_not_applicable_hex(unavailable_planning),
        readiness_result_hash=_not_applicable_hex(unavailable_planning),
        readiness_state=_not_applicable_string(unavailable_planning),
        check_reason_codes=(),
    )
    unavailable_routing = "routing_artifact_not_persisted"
    routing = RoutingBinding(
        semantic_decision_hash=_not_applicable_hex(unavailable_routing),
        audit_decision_hash=_not_applicable_hex(unavailable_routing),
        policy_id=_not_applicable_string(unavailable_routing),
        policy_version=_not_applicable_string(unavailable_routing),
        policy_hash=_not_applicable_hex(unavailable_routing),
        provider_capabilities_fingerprint=_not_applicable_hex(unavailable_routing),
        selected_capability_id=resolved.capability_id,
        selected_capability_fingerprint=_not_applicable_hex(unavailable_routing),
        provider_bound_request_hash=(
            _source_hex(
                resolved.provider_bound_request_hash,
                request_document,
                "provider_bound_request_hash",
            )
            if resolved.provider_bound_request_hash is not None
            else _not_applicable_hex(unavailable_routing)
        ),
    )
    compiler_reason = "compiler_lineage_not_persisted"
    compiler_id = (
        _source_string(
            resolved.adapter_compiler_id,
            request_document,
            "adapter_compiler_id",
        )
        if resolved.adapter_compiler_id is not None
        else _not_applicable_string(compiler_reason)
    )
    compiler_version = (
        _source_string(
            resolved.adapter_compiler_version,
            request_document,
            "adapter_compiler_version",
        )
        if resolved.adapter_compiler_version is not None
        else _not_applicable_string(compiler_reason)
    )
    compiler_hash = (
        _source_hex(
            resolved.adapter_compiler_hash,
            request_document,
            "adapter_compiler_hash",
        )
        if resolved.adapter_compiler_hash is not None
        else _not_applicable_hex(compiler_reason)
    )
    workflow_reason = "provider_has_no_workflow_identity"
    provider = ProviderBinding(
        name=resolved.provider_name,
        kind=resolved.provider_kind,
        execution_kind=execution_kind,
        billing_kind=billing_kind,
        profile_id=resolved.provider_profile.profile_id,
        profile_version=resolved.provider_profile.profile_version,
        profile_path=resolved.provider_profile.profile_path.as_posix(),
        profile_sha256=resolved.provider_profile.profile_sha256,
        capability_id=resolved.capability_id,
        workflow_id=_not_applicable_string(workflow_reason),
        workflow_version=_not_applicable_string(workflow_reason),
        workflow_path=EvidencePath(state="not_applicable", reason=workflow_reason),
        workflow_fingerprint=_not_applicable_hex(workflow_reason),
        model_id=_source_string(
            resolved.model_id, request_document, "model_id"
        ),
        adapter_compiler_id=compiler_id,
        adapter_compiler_version=compiler_version,
        adapter_compiler_hash=compiler_hash,
    )
    prompt = PromptBinding(
        prompt_sha256=hashlib.sha256(
            resolved.prompt_text.encode("utf-8")
        ).hexdigest(),
        negative_prompt_sha256=hashlib.sha256(
            resolved.effective_negative_prompt_text.encode("utf-8")
        ).hexdigest(),
        structured_intent_hash=_not_applicable_hex(
            "structured_intent_artifact_not_persisted"
        ),
        compiler_id=compiler_id,
        compiler_version=compiler_version,
        compiler_hash=compiler_hash,
    )
    parameters = ParameterBinding(
        requested_seed=requested_seed,
        effective_seed=effective_seed,
        effective_output_hash=canonical_sha256(
            resolved.effective_output.model_dump(mode="json")
        ),
        duration_milliseconds=measured.duration_milliseconds,
        frame_count=measured.frame_count,
        fps_numerator=measured.fps_numerator,
        fps_denominator=measured.fps_denominator,
        steps=EvidenceScalar(
            state=EvidenceState.NOT_APPLICABLE,
            reason="provider_has_no_steps",
        ),
        sampler=_not_applicable_string("provider_has_no_sampler"),
        scheduler=_not_applicable_string("provider_has_no_scheduler"),
        audio_mode=_source_string(
            "native_audio" if scope.request.output_requirement.native_audio else "silent_video",
            request_document,
            "activation_scope.request.output_requirement.native_audio",
        ),
        provider_parameters=NamedParameters(),
        sources=ParameterSources(
            items=tuple(
                ParameterSource(key=key, source=source)
                for key, source in (
                    ("audio_mode", "requested"),
                    ("duration_milliseconds", "effective"),
                    ("effective_seed", "provider_selected"),
                    ("fps", "effective"),
                    ("frame_count", "effective"),
                    ("requested_seed", "requested"),
                    ("sampler", "default"),
                    ("scheduler", "default"),
                    ("steps", "default"),
                )
            )
        ),
    )
    continuity = ContinuityBinding(
        mode="exact_terminal",
        source_shot_id=_source_string(
            binding.terminal_frame.source_shot_id,
            request_document,
            "continuity_binding.terminal_frame.source_shot_id",
        ),
        target_shot_id=binding.target_shot_id,
        terminal_frame_hash=_source_hex(
            binding.terminal_frame.extracted_sha256,
            request_document,
            "continuity_binding.terminal_frame.extracted_sha256",
        ),
        keyframe_hash=_not_applicable_hex("hard_cut_keyframe_not_used"),
        continuity_state_hash=_source_hex(
            binding.constraints.content_hash,
            request_document,
            "continuity_binding.constraints.content_hash",
        ),
        first_frame_binding_hash=_source_hex(
            binding.binding_hash,
            request_document,
            "continuity_binding.binding_hash",
        ),
        last_frame_binding_hash=_not_applicable_hex("last_frame_not_used"),
    )
    terminal_boundary = (
        "activated"
        if state.phase is VideoAttemptPhase.ACTIVATE
        else "candidate"
        if state.phase is VideoAttemptPhase.CANDIDATE
        else "fetched"
    )
    activation_state = {
        "activated": "activated",
        "candidate": "candidate",
        "fetched": "not_candidate",
    }[terminal_boundary]
    observations = reopen_p6_pointers(project_root, bundle.manifest)
    p6_state = (
        "not_present"
        if not observations
        else "present"
        if any(item.freshness == "fresh" for item in observations)
        else "stale"
    )
    return QualityExperienceRecordV1(
        record_kind="prospective_q0_attempt",
        schema_version="1.1",
        experiment_id=request.experiment_id,
        pilot_id=request.pilot_id,
        captured_at=request.captured_at,
        repository_commit=request.repository_commit,
        purpose=request.purpose,
        hypothesis=request.hypothesis,
        capture_actor=request.capture_actor,
        authorization_boundary=request.authorization_boundary,
        canonical_runtime_boundary=CanonicalRuntimeBoundary.PRODUCTION_MANIFEST,
        identity=RecordIdentity(
            project_artifact_id=base_bundle.project.artifact_id,
            project_artifact_revision=base_bundle.project.revision,
            project_artifact_content_hash=base_bundle.project.content_hash,
            manifest_observation_revision=bundle.manifest.manifest_revision,
            manifest_observation_file_hash=manifest_raw.file_sha256,
            registry_observation_revision=bundle.manifest.manifest_revision,
            registry_observation_file_hash=(
                attempt.base_registry.file_sha256
            ),
            scene_id=scene.scene_id,
            scene_revision=scene.revision,
            scene_content_hash=scene.content_hash,
            shot_id=target.shot_id,
            shot_revision=target.revision,
            shot_content_hash=target.content_hash,
            generation_id=resolved.generation_id,
            attempt_id=attempt.attempt_id,
        ),
        lineage=AttemptLineage(
            attempt_sequence=request.attempt_sequence,
            attempt_kind=request.attempt_kind,
            predecessor=request.predecessor,
        ),
        planning=planning,
        routing=routing,
        provider=provider,
        prompt=prompt,
        parameters=parameters,
        inputs=inputs,
        continuity=continuity,
        continuity_evidence=_continuity_evidence_binding(
            evaluation, intent, evidence
        ),
        outcome=OutcomeSucceeded(
            variant="succeeded",
            terminal_boundary=terminal_boundary,
            observed_at=request.captured_at,
        ),
        artifact_evidence=ArtifactEvidenceKnown(
            state="known",
            boundary="canonical",
            relative_path=fetch_pointer.artifact_path.as_posix(),
            asset_id=resolved.output_asset_id,
            file_sha256=artifact.file_sha256,
            size_bytes=len(artifact.data),
            container=measured.container_name,
            codec=measured.codec_name,
            width=measured.width,
            height=measured.height,
            fps_numerator=measured.fps_numerator,
            fps_denominator=measured.fps_denominator,
            duration_milliseconds=measured.duration_milliseconds,
            frame_count=measured.frame_count,
            audio_stream_count=measured.audio_stream_count,
            ffprobe_hash=probe.content_hash,
            video_probe_receipt_id=probe.content_hash,
            probe_receipt_hash=evaluation.probe.file_sha256,
            provenance_receipt_id=provenance.content_hash,
            provenance_receipt_hash=evaluation.provenance.file_sha256,
        ),
        durability=DurabilityBinding(
            activation_state=activation_state,
            manifest_revision=bundle.manifest.manifest_revision,
            strict_reopen_result="verified",
            recovery_observation="not_required",
            exact_replay_counters=ReplayCounters(
                provider_calls=0,
                renderer_calls=0,
                analyzer_calls=0,
                manifest_writes=0,
            ),
            exact_replay_result="zero_effect",
        ),
        analyzer=analyzer,
        human_review=build_human_review(
            request.human_review,
            request.human_review_document,
            project_root,
            evidence,
        ),
        intervention=request.intervention,
        outcome_boundary=OutcomeBoundaryBinding(
            artifact_claim=BoundedFreeText(
                value="exact generated Shot continuity verdict for this artifact"
            ),
            p6_state=p6_state,
            p6_observations=observations,
            allowed_conclusions=request.allowed_conclusions,
            forbidden_extrapolations=request.forbidden_extrapolations,
        ),
    )


def capture_post_qa_quality_experience(
    request: PostQaQ0CaptureRequest,
) -> QualityRecordPointer:
    """Strictly reopen Production evidence, project it, then write through Q0."""

    try:
        record = _build_record(request)
    except QualityExperienceCaptureError:
        raise
    except Exception:
        raise _reject(CaptureErrorCode.BINDING_INVALID) from None
    try:
        return QualityExperienceStore(request.pilot_dataset_root).write_record(record)
    except QualityExperienceConflict:
        raise
    except Exception:
        raise _reject(CaptureErrorCode.BINDING_INVALID) from None


__all__ = [
    "CaptureErrorCode",
    "PostQaAnalyzerDocument",
    "PostQaHumanReviewDocument",
    "PostQaHumanReviewMetadata",
    "PostQaQ0CaptureRequest",
    "QualityExperienceCaptureError",
    "capture_post_qa_quality_experience",
]
