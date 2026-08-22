"""Strictly reopen actual P6 observations for Q0 projection."""

from pathlib import Path

from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    ApprovedRepairReceipt,
    ProductionManifest,
    RepairOutcomeReceipt,
    RenderStateSnapshot,
)
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production._repair_freshness import approved_repair_is_current
from ai_video.production.project import (
    load_final_acceptance_receipt,
    load_review_receipt,
)
from ai_video.quality_intelligence._capture_contracts import (
    CaptureErrorCode,
    QualityExperienceCaptureError,
)
from ai_video.quality_intelligence.models import ExactEvidencePointer


def _reject() -> QualityExperienceCaptureError:
    return QualityExperienceCaptureError(CaptureErrorCode.BINDING_INVALID)


def reopen_p6_pointers(
    project_root: Path,
    manifest: ProductionManifest,
    *,
    current_render: RenderStateSnapshot | None = None,
) -> tuple[ExactEvidencePointer, ...]:
    approved_repair_is_fresh = False
    for pointer in manifest.active_review_receipts:
        load_review_receipt(project_root, pointer)
    if manifest.active_approved_repair is not None:
        pointer = manifest.active_approved_repair
        reopened = _read_regular_file_nofollow(
            project_root / pointer.path,
            contained_by=project_root / "state",
        )
        receipt = ApprovedRepairReceipt.model_validate_json(reopened.data)
        if (
            reopened.file_sha256 != pointer.file_sha256
            or receipt.content_hash != pointer.content_hash
            or receipt.repair_id != pointer.repair_id
            or not verify_artifact_hash(receipt)
        ):
            raise _reject()
        approved_repair_is_fresh = approved_repair_is_current(
            manifest, receipt, current_render=current_render
        )
    for pointer in manifest.repair_outcome_receipts:
        reopened = _read_regular_file_nofollow(
            project_root / pointer.path,
            contained_by=project_root / "state",
        )
        receipt = RepairOutcomeReceipt.model_validate_json(reopened.data)
        if (
            reopened.file_sha256 != pointer.file_sha256
            or receipt.content_hash != pointer.content_hash
            or receipt.repair_id != pointer.repair_id
            or not verify_artifact_hash(receipt)
        ):
            raise _reject()
    final_pointer = (
        manifest.final_acceptance_state.active_receipt
        if manifest.final_acceptance_state is not None
        else None
    )
    if final_pointer is not None:
        load_final_acceptance_receipt(project_root, final_pointer)
    values = [
        *(
            ("review_receipt", pointer)
            for pointer in manifest.active_review_receipts
        ),
        ("approved_repair", manifest.active_approved_repair),
        *(
            ("repair_outcome", pointer)
            for pointer in manifest.repair_outcome_receipts
        ),
        ("final_acceptance", final_pointer),
    ]
    result = tuple(
        ExactEvidencePointer(
            kind=kind,
            relative_path=pointer.path.as_posix(),
            content_hash=pointer.content_hash,
            file_sha256=pointer.file_sha256,
            freshness=(
                "fresh"
                if kind != "repair_outcome"
                and (kind != "approved_repair" or approved_repair_is_fresh)
                else "stale"
            ),
        )
        for kind, pointer in values
        if pointer is not None
    )
    return tuple(sorted(result, key=lambda item: (item.kind, item.relative_path)))


__all__ = ["reopen_p6_pointers"]
