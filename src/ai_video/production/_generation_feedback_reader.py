"""Strict readers for decision, qualification and empirical feedback receipts."""
from pathlib import Path
from pydantic import ValidationError
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._lifecycle_schema import (
    GenerationExecutionBindingPointer, GenerationExperienceReceiptPointer,
    GenerationQualityRejectionReceiptPointer, QualificationExecutionBindingPointer,
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

    from ai_video.production.generation_execution import (
        GenerationDecisionExecutionBinding,
    )

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
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
        load_generation_experience(root, pointer)
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
    all_evidence = tuple(
        item
        for experience_pointer in state.generation_experiences
        for item in load_generation_experience(root, experience_pointer).evidence
    )
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
        )
    except (AiVideoError, AttributeError, ValueError) as exc:
        raise _invalid("Quality rejection execution evidence is invalid.", str(exc)) from exc
    if diagnosis != receipt.diagnosis:
        raise _invalid("Quality rejection diagnosis is not exact to retained evidence.")


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
    for receipt in load_imported_history(loaded.root, loaded.manifest):
        request = receipt.source_request.activation_scope.request
        shots = (*loaded.shots, *loaded.production_parents)
        if (receipt.source_manifest.project_id != loaded.project.project_id
                or not any(s.shot_id == request.target_shot_id
                           and s.artifact_id in request.input_artifact_ids for s in shots)):
            raise _invalid("Imported history has a different project or Shot identity.")
