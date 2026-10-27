"""Strict readers for decision, qualification and empirical feedback receipts."""
from pathlib import Path
from pydantic import ValidationError
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._lifecycle_schema import (
    GenerationExecutionBindingPointer, GenerationExperienceReceiptPointer,
    GenerationQualityRejectionReceiptPointer, QualificationExecutionBindingPointer,
    GenerationVisualSupersessionReceiptPointer,
    RuntimeRepairAuthorizationPointer,
)
from ai_video.production.paths import _read_regular_file_nofollow, resolve_contained_path

def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _root_and_path(root: str | Path, stored: Path) -> tuple[Path, Path]:
    try:
        resolved_root = Path(root).resolve(strict=True)
        resolved = resolve_contained_path(
            resolved_root, stored, allowed_root=resolved_root / "state"
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid("Video generation evidence path is unsafe.", str(exc)) from exc
    return resolved_root, resolved


def load_generation_execution_binding(
    root: str | Path, pointer: GenerationExecutionBindingPointer
):
    """Reopen the exact pure decision that authorized one new submit."""
    return _load_generation_execution_binding(root, pointer, {})


def _load_generation_execution_binding(root, pointer, validated):
    """Reuse parsed bytes only within the owning reader's current traversal."""

    from ai_video.production.generation_execution import (
        GenerationDecisionExecutionBinding,
    )

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        key = (resolved, raw.file_sha256)
        binding = validated.get(key)
        if binding is None:
            binding = GenerationDecisionExecutionBinding.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid(
            "Could not reopen generation decision execution binding.", str(exc)
        ) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or binding.binding_hash != pointer.binding_hash
        or binding.compiled_request.resolved_generation_hash
        != pointer.request_fingerprint
    ):
        raise _invalid("Generation decision execution binding pointer is invalid.")
    # Every visit above still reads current bytes and checks all pointer fields.
    # Never retain a partial or failed validation, or share it across public reads.
    validated[key] = binding
    return binding



def load_generation_experience(
    root: str | Path, pointer: GenerationExperienceReceiptPointer
):
    from ai_video.production.generation_decision import GenerationCandidate
    from ai_video.production.generation_experience import (
        GenerationExperience,
        bind_experience_models,
    )
    from ai_video.production.hashing import canonical_sha256

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        bind_experience_models(GenerationCandidate)
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        experience = GenerationExperience.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen generation experience.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or canonical_sha256(experience.model_dump(mode="json")) != pointer.content_hash
        or any(entry.request_hash != pointer.request_fingerprint for entry in experience.evidence)
    ):
        raise _invalid("Generation experience pointer identity is invalid.")
    return experience


def load_generation_quality_rejection(
    root: str | Path, pointer: GenerationQualityRejectionReceiptPointer
):
    """Reopen an immutable explicit terminal quality decision."""
    from ai_video.production.generation_rejection import GenerationQualityRejectionReceipt
    from ai_video.production.hashing import canonical_sha256

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        receipt = GenerationQualityRejectionReceipt.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen generation quality rejection.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or canonical_sha256(receipt.model_dump(mode="json")) != pointer.content_hash
        or receipt.attempt_id != pointer.attempt_id
        or receipt.request_fingerprint != pointer.request_fingerprint
        or receipt.artifact_sha256 != pointer.artifact_sha256
        or receipt.experience_content_hash != pointer.experience_content_hash
    ):
        raise _invalid("Generation quality rejection pointer identity is invalid.")
    return receipt


def load_generation_visual_supersession(
    root: str | Path, pointer: GenerationVisualSupersessionReceiptPointer
):
    from ai_video.production.generation_visual_revision import (
        load_generation_visual_supersession as load,
    )

    return load(root, pointer)


def load_runtime_repair_authorization(
    root: str | Path, pointer: RuntimeRepairAuthorizationPointer
):
    """Reopen an immutable runtime repair authorization."""
    from ai_video.production.generation_runtime_repair import RuntimeRepairAuthorization
    from ai_video.production.hashing import canonical_sha256

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        authorization = RuntimeRepairAuthorization.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen runtime repair authorization.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or canonical_sha256(authorization.model_dump(mode="json")) != pointer.content_hash
        or authorization.attempt_id != pointer.attempt_id
        or authorization.evidence_hash != pointer.evidence_hash
    ):
        raise _invalid("Runtime repair authorization pointer identity is invalid.")
    if pointer.revocation is not None:
        from ai_video.production.generation_runtime_repair_revocation import load_revocation

        receipt = load_revocation(root, pointer)
        if receipt.actor != authorization.actor:
            raise _invalid("Runtime repair revocation actor differs from its authorization.")
    return authorization



def load_qualification_execution_binding(
    root: str | Path, pointer: QualificationExecutionBindingPointer
):
    from ai_video.production.generation_execution import _QualificationExecutionBinding

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        binding = _QualificationExecutionBinding.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid(
            "Could not reopen qualification execution binding.", str(exc)
        ) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or binding.binding_hash != pointer.binding_hash
        or binding.request_input_hash != pointer.request_fingerprint
    ):
        raise _invalid("Qualification execution binding pointer is invalid.")
    return binding



def verify_generation_feedback(root, state, request):
    for pointer, loader, label in (
        (state.execution_binding, load_generation_execution_binding, "Generation"),
        (state.qualification_binding, load_qualification_execution_binding, "Qualification"),
    ):
        if pointer is not None:
            binding = loader(root, pointer)
            try:
                binding.validate_request(request)
            except ValueError as exc:
                raise _invalid(f"{label} execution binding is not exact.", str(exc)) from exc
    for pointer in state.generation_experiences:
        experience = load_generation_experience(root, pointer)
        tagged = tuple(
            source for source in experience.evaluation_sources
            if source.commercial_evidence_content_hash is not None
        )
        if tagged:
            from ai_video.production.ecommerce_generation_bridge import (
                validate_commercial_failure_evaluation_source,
            )
            from ai_video.production.project import load_qa_policy

            if len(tagged) != 1 or tagged[0].commercial_qa_policy is None:
                raise _invalid("Commercial generation source has no exact QA checkpoint.")
            try:
                frozen_policy = load_qa_policy(root, tagged[0].commercial_qa_policy)
                validate_commercial_failure_evaluation_source(
                    root=root,
                    state=state,
                    request=request,
                    qa_policy=frozen_policy,
                    qa_policy_pointer=tagged[0].commercial_qa_policy,
                    acceptance=experience.candidate.recipe.acceptance_policy,
                    source=tagged[0],
                )
            except (AiVideoError, OSError, ValueError) as exc:
                raise _invalid("Commercial generation source is not exact.", str(exc)) from exc
        marked = [s for s in experience.evaluation_sources if s.schema_version == "generation-evaluation/2"]
        if marked:
            from ai_video.production._video_project_reader import load_local_video_fetch_receipt, load_video_fetch_receipt

            fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
            if fetch_pointer is None:
                raise _invalid("Marked evaluation has no fetched media.")
            fetch = (load_local_video_fetch_receipt(root, fetch_pointer) if state.local_fetch_receipt
                     else load_video_fetch_receipt(root, fetch_pointer))
            if any(s.artifact_sha256 != fetch.artifact_sha256 or s.size_bytes != fetch.size_bytes for s in marked):
                raise _invalid("Marked evaluation differs from exact fetched media.")
    if state.visual_supersession is not None:
        receipt = load_generation_visual_supersession(root, state.visual_supersession)
        if state.fetch_receipt is None or state.paid_submit_receipt is None:
            raise _invalid("Visual supersession has no exact remote paid fetch.")
        from ai_video.production._video_project_reader import load_video_fetch_receipt

        fetch = load_video_fetch_receipt(root, state.fetch_receipt)
        experience_pointer = state.generation_experiences[-1] if state.generation_experiences else None
        if experience_pointer is None:
            raise _invalid("Visual supersession has no retained generation experience.")
        experience = load_generation_experience(root, experience_pointer)
        evidence = next((item for item in experience.evidence
                         if item.evidence_hash == receipt.evidence_hash), None)
        binding = (
            load_generation_execution_binding(root, state.execution_binding)
            if state.execution_binding is not None else None
        )
        if binding is None or request.activation_scope is None:
            raise _invalid("Visual supersession has no exact decision-bound Shot request.")
        selected = tuple(item for item in binding.inputs.candidates
                         if item.candidate_id == binding.decision.selected_candidate_id)
        request_scope = request.activation_scope.request
        first_frames = tuple(item for item in request_scope.image_bindings
                             if item.role == "first_frame")
        if receipt.schema_version in {
            "generation-visual-supersession/4", "generation-visual-supersession/5",
        }:
            old_frame_matches = (
                len(first_frames) <= 1
                and receipt.old_first_frame_sha256
                == (first_frames[0].asset_sha256 if first_frames else None)
            )
            target_frame_matches = (
                receipt.authored_revision is not None
                and receipt.target_first_frame_sha256 == receipt.authored_revision.first_frame_sha256
                if receipt.schema_version == "generation-visual-supersession/4"
                else receipt.authored_retarget is not None
                and receipt.target_first_frame_sha256 is None
            )
        else:
            old_frame_matches = (
                len(first_frames) == 1
                and receipt.old_first_frame_sha256 == first_frames[0].asset_sha256
            )
            target_frame_matches = (
                (len(first_frames) == 1
                 and receipt.schema_version == "generation-visual-supersession/1"
                 and receipt.target_first_frame_sha256 != first_frames[0].asset_sha256)
                or (receipt.schema_version in {
                    "generation-visual-supersession/2", "generation-visual-supersession/3",
                } and receipt.target_first_frame_sha256 == first_frames[0].asset_sha256)
            )
        if (
            len(selected) != 1
            or experience.projection != binding.projection
            or experience.candidate != selected[0]
            or selected[0].final_output_goal != receipt.old_goal
            or not old_frame_matches
            or not target_frame_matches
            or receipt.attempt_id != state.visual_supersession.attempt_id
            or receipt.request_fingerprint != request.request_input_hash
            or receipt.request_fingerprint != request_scope.request_input_hash
            or receipt.execution_binding != state.execution_binding
            or receipt.fetch_receipt != state.fetch_receipt
            or receipt.paid_submit_receipt != state.paid_submit_receipt
            or receipt.artifact_sha256 != fetch.artifact_sha256
            or receipt.artifact_size_bytes != fetch.size_bytes
            or receipt.experience_content_hash != experience_pointer.content_hash
            or receipt.base_project != request_scope.base_project
            or receipt.task_id != binding.inputs.limits.task_id
            or receipt.shot_id != binding.context.target_shot_id
            or evidence is None
            or evidence.attempt_id != receipt.attempt_id
            or evidence.request_hash != receipt.request_fingerprint
            or evidence.outcome != "media"
            or evidence.artifact_sha256 != receipt.artifact_sha256
            or evidence.task_id != receipt.task_id
            or evidence.shot_id != receipt.shot_id
            or evidence.facts_hash != binding.inputs.facts_hash
            or evidence.recipe_scope_hash != selected[0].scope_hash
            or evidence.rubric_hash != selected[0].recipe.rubric_hash
        ):
            raise _invalid("Visual supersession receipt differs from retained request, media, goal, or evaluation evidence.")
        from ai_video.production.generation_visual_revision import validate_visual_revision_goal

        try:
            if receipt.schema_version == "generation-visual-supersession/4":
                from ai_video.production.generation_authoring_revision import validate_authored_revision_goal

                if receipt.authored_revision is None:
                    raise ValueError("authored supersession has no exact target contract")
                validate_authored_revision_goal(
                    receipt.old_goal,
                    receipt.target_goal,
                    goal_requirement_revisions=receipt.authored_revision.goal_requirement_revisions,
                    authorization_receipt_id=receipt.authorization_receipt_id,
                )
            elif receipt.schema_version == "generation-visual-supersession/5":
                from ai_video.production.generation_authored_retarget import (
                    _same_goal_with_new_version,
                )

                if (receipt.authored_retarget is None
                        or not _same_goal_with_new_version(receipt.old_goal, receipt.target_goal)
                        or receipt.authored_retarget.authorization_reference
                            != receipt.authorization_receipt_id):
                    raise ValueError("retarget supersession has a changed goal or authority")
            else:
                validate_visual_revision_goal(receipt.old_goal, receipt.target_goal)
            if receipt.coverage_revision is not None:
                from ai_video.production.generation_coverage_revision import validate_coverage_target

                validate_coverage_target(binding, experience, receipt.coverage_revision)
            if receipt.resolution_revision is not None:
                from ai_video.production.generation_resolution_revision import validate_resolution_target

                validate_resolution_target(binding, experience, receipt.resolution_revision)
            if receipt.authored_revision is not None:
                from ai_video.production.generation_authoring_revision import (
                    validate_authored_generation_revision_target,
                )

                validate_authored_generation_revision_target(
                    binding, experience, receipt.authored_revision
                )
            if receipt.authored_retarget is not None:
                from ai_video.production.generation_authored_retarget import (
                    validate_authored_generation_retarget_target,
                )

                source_target = receipt.authored_retarget
                if receipt.previous_supersession is not None:
                    original = load_generation_visual_supersession(root, receipt.previous_supersession)
                    source_target = original.authored_retarget
                validate_authored_generation_retarget_target(binding, experience, source_target)
            from ai_video.production.generation_evaluation import validate_generation_evaluation_sources
            from ai_video.production.project import load_qa_policy

            qa_policy = load_qa_policy(root, receipt.qa_policy)
            validate_generation_evaluation_sources(
                sources=experience.evaluation_sources,
                evidence=evidence,
                qa_policy=qa_policy,
                size_bytes=fetch.size_bytes,
                acceptance=selected[0].recipe.acceptance_policy,
                requirement=experience.projection.requirement,
            )
        except ValueError as exc:
            raise _invalid("Visual supersession goal or original QA evidence is invalid.", str(exc)) from exc
        return
    if state.quality_rejection is None:
        return
    receipt = load_generation_quality_rejection(root, state.quality_rejection)
    if not state.generation_experiences:
        raise _invalid("Quality rejection has no generation experience.")
    experience = load_generation_experience(root, state.generation_experiences[-1])
    evidence = next(
        (item for item in experience.evidence
         if item.evidence_hash == receipt.evidence_hash),
        None,
    )
    fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
    if fetch_pointer is None:
        raise _invalid("Quality rejection has no fetched media.")
    try:
        from ai_video.production._video_project_reader import (
            load_local_video_fetch_receipt, load_video_fetch_receipt,
        )

        fetch = (
            load_local_video_fetch_receipt(root, fetch_pointer)
            if state.local_fetch_receipt is not None
            else load_video_fetch_receipt(root, fetch_pointer)
        )
    except AiVideoError:
        raise
    except (OSError, ValueError) as exc:
        raise _invalid("Quality rejection media evidence is invalid.", str(exc)) from exc
    if (
        receipt.request_fingerprint != request.request_input_hash
        or receipt.attempt_id != state.quality_rejection.attempt_id
        or receipt.experience_content_hash != state.generation_experiences[-1].content_hash
        or receipt.artifact_sha256 != fetch.artifact_sha256
        or receipt.artifact_size_bytes != fetch.size_bytes
        or evidence is None
        or receipt.attempt_id != evidence.attempt_id
        or evidence.request_hash != request.request_input_hash
        or evidence.outcome != "media"
        or evidence.artifact_sha256 != fetch.artifact_sha256
        or not experience.evaluation_sources
        or any(
            source.qa_policy_content_hash != receipt.qa_policy_content_hash
            or (
                source.commercial_qa_policy is not None
                and source.commercial_qa_policy != receipt.qa_policy
            )
            for source in experience.evaluation_sources
        )
        or tuple(
            finding
            for source in experience.evaluation_sources
            for finding in source.project_findings()
        ) != evidence.findings
    ):
        raise _invalid("Quality rejection receipt does not match retained evidence.")
    if state.execution_binding is None:
        raise _invalid("Quality rejection has no production execution binding.")
    binding = load_generation_execution_binding(root, state.execution_binding)
    experiences = tuple(load_generation_experience(root, pointer) for pointer in state.generation_experiences)
    all_evidence = tuple(item for stored in experiences for item in stored.evidence)
    sources = tuple(source for stored in experiences for source in stored.evaluation_sources)
    try:
        from ai_video.production.generation_rejection import (
            validate_quality_rejection_experience,
        )
        from ai_video.production.project import load_qa_policy

        binding.validate_request(request)
        diagnosis = validate_quality_rejection_experience(
            binding=binding,
            experience=experience,
            evidence=evidence,
            request=request,
            attempt_id=receipt.attempt_id,
            artifact_sha256=fetch.artifact_sha256,
            qa_policy=load_qa_policy(root, receipt.qa_policy),
            history=all_evidence,
            evaluation_sources=sources,
        )
    except (AiVideoError, AttributeError, ValueError) as exc:
        raise _invalid("Quality rejection execution evidence is invalid.", str(exc)) from exc
    if diagnosis != receipt.diagnosis:
        raise _invalid("Quality rejection diagnosis is not exact to retained evidence.")
    if receipt.abandonment_reason is not None:
        from ai_video.production.generation_rejection import validate_abandoned_result

        try:
            validate_abandoned_result(receipt, experience=experience, evidence=evidence,
                                      history=all_evidence, evaluation_sources=sources)
        except ValueError as exc:
            raise _invalid("Abandoned result evidence is invalid.", str(exc)) from exc


def load_imported_history(root, manifest):
    """Read the Manifest-selected retrospective history in source order."""
    if not manifest.imported_generation_experiences:
        return ()
    from ai_video.production.generation_history_import import load_imported_generation_experience

    receipts = tuple(load_imported_generation_experience(root, p)
                     for p in manifest.imported_generation_experiences)
    if len({r.import_id for r in receipts}) != len(receipts):
        raise _invalid("Historical generation import IDs are duplicated.")
    dates = tuple(r.source_fetch.fetched_at for r in receipts)
    if dates != tuple(sorted(dates)):
        raise _invalid("Historical generation imports are not in source order.")
    return receipts


def verify_manifest_generation_evidence(loaded, manifest):
    from ai_video.production._video_project_reader import verify_manifest_video_evidence

    verify_manifest_video_evidence(loaded, manifest)
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        for pointer in (() if state is None else state.runtime_repairs):
            if pointer.revocation is not None:
                from ai_video.production.generation_runtime_repair_revocation import load_revocation

                load_runtime_repair_authorization(loaded.root, pointer)
                receipt = load_revocation(loaded.root, pointer, project_id=manifest.project_id)
                if (attempt.status.value != "failed" or pointer.attempt_id != attempt.attempt_id
                        or receipt.expected_manifest_revision >= manifest.manifest_revision):
                    raise _invalid("Runtime repair revocation has a different attempt or future revision.")
    for receipt in load_imported_history(loaded.root, loaded.manifest):
        request = receipt.source_request.activation_scope.request
        shots = (*loaded.shots, *loaded.production_parents)
        if (receipt.source_manifest.project_id != loaded.project.project_id
                or not any(s.shot_id == request.target_shot_id
                           and s.artifact_id in request.input_artifact_ids for s in shots)):
            raise _invalid("Imported history has a different project or Shot identity.")
