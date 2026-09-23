"""Read-only atomic packaging of one exact Final Accepted Ecommerce render."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.ad_creative_types import AdCreativePlan, CompiledAdCreativeHandoff
from ai_video.production.composition_contracts import ResolvedTimeline
from ai_video.production.ecommerce_job_assembly import validate_ecommerce_plan_binding
from ai_video.production.ecommerce_job_contracts import EcommerceProductionHandoff
from ai_video.production.ecommerce_quality_gate import (
    EcommerceWholeAdAcceptanceTarget,
    validate_ecommerce_final_output_contract,
    validate_ecommerce_review_evidence_binding,
)
from ai_video.production.final_output_review import adjudicate_final_output
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    QaLayer,
    QaVerdict,
    RenderReceipt,
    ReviewLifecycle,
    ToolIdentity,
)
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    _read_regular_file_nofollow,
)
from ai_video.production.project import (
    load_final_acceptance_receipt,
    load_production_project,
    load_review_evidence,
    load_review_receipt,
    load_review_request,
)

_SHA256 = r"^[0-9a-f]{64}$"


class EcommerceDeliveryBundleResult(StrictModel):
    schema_version: Literal["ecommerce-delivery-bundle-result/1"] = (
        "ecommerce-delivery-bundle-result/1"
    )
    bundle_id: str = Field(pattern=_SHA256)
    bundle_path: Path
    inventory_hash: str = Field(pattern=_SHA256)
    render_output_sha256: str = Field(pattern=_SHA256)
    final_acceptance_content_hash: str = Field(pattern=_SHA256)


def _invalid(message: str, *, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        ErrorCode.FINAL_ACCEPTANCE_INVALID,
        message,
        technical_detail=detail,
        retryable=False,
    )


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _file_identity(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _write_file(path: Path, payload: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _load_render_receipt(project_root: Path, render_state) -> RenderReceipt:
    pointer = render_state.render_receipt
    try:
        snapshot = _read_regular_file_nofollow(
            project_root / pointer.path,
            contained_by=project_root / "state",
        )
        receipt = RenderReceipt.model_validate_json(snapshot.data)
    except (OSError, ValueError) as exc:
        raise _invalid("Delivery render receipt is invalid.", detail=str(exc)) from exc
    if (
        snapshot.file_sha256 != pointer.file_sha256
        or receipt.content_hash != pointer.content_hash
        or not verify_artifact_hash(receipt)
        or receipt.output_sha256 != render_state.output.file_sha256
        or receipt.output_size_bytes != render_state.output.size_bytes
        or receipt.timeline_fingerprint != render_state.timeline_fingerprint
    ):
        raise _invalid("Delivery render receipt does not match current render state.")
    return receipt


def _load_resolved_timeline(project_root: Path, render_state) -> ResolvedTimeline:
    pointer = render_state.timeline
    try:
        snapshot = _read_regular_file_nofollow(
            project_root / pointer.path,
            contained_by=project_root / "state",
        )
        timeline = ResolvedTimeline.model_validate_json(snapshot.data)
    except (OSError, ValueError) as exc:
        raise _invalid("Delivery ResolvedTimeline is invalid.", detail=str(exc)) from exc
    if (
        snapshot.file_sha256 != pointer.file_sha256
        or timeline.content_hash != pointer.content_hash
        or timeline.revision != pointer.revision
        or timeline.composition_fingerprint != render_state.timeline_fingerprint
        or not verify_artifact_hash(timeline)
    ):
        raise _invalid("Delivery ResolvedTimeline does not match current render state.")
    return timeline


def _current_lineage(
    project_root: Path,
    *,
    job_id: str,
    handoff: EcommerceProductionHandoff,
    plan: AdCreativePlan,
    compiled_handoff: CompiledAdCreativeHandoff,
    exported_at: str,
    tool_identity: ToolIdentity,
) -> tuple[dict[str, object], Path, str, int, str]:
    validate_ecommerce_plan_binding(handoff, compiled_handoff, plan)
    try:
        parsed_exported_at = datetime.fromisoformat(exported_at)
    except ValueError as exc:
        raise _invalid("Delivery export timestamp is invalid.", detail=str(exc)) from exc
    if parsed_exported_at.tzinfo is None:
        raise _invalid("Delivery export timestamp requires an explicit timezone.")
    try:
        loaded = load_production_project(project_root / "project.yaml")
    except (OSError, ValueError, AiVideoError) as exc:
        if isinstance(exc, AiVideoError):
            raise
        raise _invalid(
            "Delivery requires valid canonical Production state.",
            detail=str(exc),
        ) from exc
    manifest = loaded.manifest
    acceptance_state = manifest.final_acceptance_state
    if (
        acceptance_state is None
        or acceptance_state.lifecycle is not ReviewLifecycle.FRESH
        or acceptance_state.active_receipt is None
        or loaded.render_state is None
        or manifest.active_render_state is None
        or manifest.active_dependency_graph is None
        or manifest.active_qa_policy is None
    ):
        raise _invalid("Delivery requires current Final Acceptance.")
    acceptance_pointer = acceptance_state.active_receipt
    acceptance = load_final_acceptance_receipt(project_root, acceptance_pointer)
    policy = loaded.qa_policy
    if policy is None:
        raise _invalid("Delivery requires the selected QA policy.")
    try:
        validate_ecommerce_final_output_contract(handoff, policy)
    except ValueError as exc:
        raise _invalid(str(exc)) from exc
    project_provenance = {
        (item.reference, item.content_hash) for item in loaded.project.source_provenance
    }
    if {
        (f"ecommerce-handoff:{handoff.handoff_id}", handoff.handoff_id),
        (
            f"ecommerce-compile-profile:{handoff.compile_profile.profile_id}",
            handoff.compile_profile.profile_id,
        ),
    }.difference(project_provenance):
        raise _invalid("Current Production project does not bind the Ecommerce handoff.")
    provenance = {
        (item.reference, item.content_hash) for item in acceptance.source_provenance
    }
    required_provenance = {
        (f"ecommerce-handoff:{handoff.handoff_id}", handoff.handoff_id),
        (
            f"ecommerce-source-package:{handoff.source_package_id}",
            handoff.source_package_id,
        ),
        (f"ad-creative-plan:{plan.artifact_id}", plan.content_hash),
        (
            f"composition:{compiled_handoff.composition_spec.artifact_id}",
            compiled_handoff.composition_spec.content_hash,
        ),
    }
    if not required_provenance.issubset(provenance):
        raise _invalid(
            "Final Acceptance does not bind the exact Ecommerce handoff lineage."
        )
    render = loaded.render_state
    render_receipt = _load_render_receipt(project_root, render)
    timeline = _load_resolved_timeline(project_root, render)
    composition = compiled_handoff.composition_spec
    if (
        not verify_artifact_hash(composition)
        or composition.ad_creative_plan_id != plan.artifact_id
        or composition.ad_creative_plan_hash != plan.content_hash
        or timeline.composition_spec_id != composition.artifact_id
        or timeline.composition_spec_revision != composition.revision
        or timeline.composition_spec_hash != composition.content_hash
        or timeline.delivery_profile.width != handoff.delivery_profile.width
        or timeline.delivery_profile.height != handoff.delivery_profile.height
        or timeline.delivery_profile.fps != handoff.delivery_profile.fps
        or timeline.delivery_profile.codec_profile
        != handoff.delivery_profile.codec_profile
    ):
        raise _invalid(
            "Delivery timeline does not bind the exact Ecommerce composition."
        )
    timeline_shot_ids = tuple(
        dict.fromkeys(item.shot_id for item in timeline.visual_spans)
    )
    proposal_shot_ids = tuple(
        item.shot_id for item in handoff.artifact_proposals.shots
    )
    selected_by_shot = {item.shot_id: item for item in loaded.shots}
    if (
        timeline_shot_ids != composition.shot_ids
        or proposal_shot_ids != composition.shot_ids
        or tuple(item.shot_id for item in loaded.shots) != composition.shot_ids
        or set(selected_by_shot) != set(composition.shot_ids)
        or loaded.storyboard.artifact_id
        != handoff.artifact_proposals.storyboard.artifact_id
        or tuple(item.artifact_id for item in loaded.shots)
        != tuple(item.artifact_id for item in handoff.artifact_proposals.shots)
    ):
        raise _invalid(
            "Delivery selected Storyboard and Shots do not match the Ecommerce timeline."
        )
    if (
        acceptance.verdict is not QaVerdict.PASS
        or acceptance.render_state != manifest.active_render_state
        or acceptance.render_output_sha256 != render.output.file_sha256
        or acceptance.timeline_fingerprint != render.timeline_fingerprint
        or acceptance.dependency_graph != manifest.active_dependency_graph
        or acceptance.qa_policy != manifest.active_qa_policy
        or set(acceptance.required_review_receipts)
        != set(manifest.active_review_receipts)
    ):
        raise _invalid("Delivery Final Acceptance is not bound to current state.")
    semantic_pointers = tuple(
        item
        for item in acceptance.required_review_receipts
        if item.layer is QaLayer.SEMANTIC
    )
    if len(semantic_pointers) != 1:
        raise _invalid("Delivery requires one exact Ecommerce semantic receipt.")
    semantic = load_review_receipt(project_root, semantic_pointers[0])
    request = load_review_request(project_root, semantic.review_request)
    evidence_items = tuple(
        load_review_evidence(project_root, item) for item in semantic.evidence
    )
    try:
        target = EcommerceWholeAdAcceptanceTarget.model_validate(
            evidence_items[0].measured_payload.get("acceptance_target")
        )
    except (IndexError, TypeError, ValueError) as exc:
        raise _invalid("Delivery Ecommerce acceptance target is invalid.") from exc
    if (
        len(evidence_items) != 1
        or semantic.verdict is not QaVerdict.PASS
        or not validate_ecommerce_review_evidence_binding(
            policy=policy,
            evidence=evidence_items[0],
            review_request_content_hash=request.content_hash,
        )
        or policy.final_output is None
        or adjudicate_final_output(
            policy.final_output,
            evidence_items,
            review_request_content_hash=request.content_hash,
        )
        is not QaVerdict.PASS
        or target.ad_creative_plan_hash != plan.content_hash
        or target.composition_spec_content_hash != composition.content_hash
        or target.resolved_timeline_content_hash != timeline.content_hash
        or target.project_content_hash != manifest.active_project.content_hash
        or target.registry_content_hash != manifest.active_registry.content_hash
        or target.dependency_graph_revision_id
        != manifest.active_dependency_graph.revision_id
        or target.render_state_content_hash
        != manifest.active_render_state.content_hash
        or target.render_output_sha256 != render.output.file_sha256
        or target.qa_policy_content_hash != policy.content_hash
    ):
        raise _invalid(
            "Delivery semantic evidence does not accept the exact Ecommerce output."
        )
    source = (project_root / render.output.path).resolve(strict=True)
    source_hash, source_size = _file_identity(source)
    if (
        source_hash != render.output.file_sha256
        or source_size != render.output.size_bytes
    ):
        raise _invalid("Delivery render bytes do not match Final Acceptance.")
    provider_lineage = []
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        if state is None or state.commercial_evaluation is None:
            continue
        commercial = state.commercial_evaluation
        provider_lineage.append(
            {
                "attempt_id": attempt.attempt_id,
                "status": attempt.status.value,
                "request": state.request.model_dump(mode="json"),
                "execution_binding": (
                    None
                    if state.execution_binding is None
                    else state.execution_binding.model_dump(mode="json")
                ),
                "paid_submit_receipt": (
                    None
                    if state.paid_submit_receipt is None
                    else state.paid_submit_receipt.model_dump(mode="json")
                ),
                "local_submit_receipt": (
                    None
                    if state.local_submit_receipt is None
                    else state.local_submit_receipt.model_dump(mode="json")
                ),
                "fetch_receipt": (
                    None
                    if state.fetch_receipt is None
                    else state.fetch_receipt.model_dump(mode="json")
                ),
                "local_fetch_receipt": (
                    None
                    if state.local_fetch_receipt is None
                    else state.local_fetch_receipt.model_dump(mode="json")
                ),
                "commercial_evaluation": commercial.model_dump(mode="json"),
                "candidate_video_asset_ids": state.candidate_video_asset_ids,
            }
        )
    lineage: dict[str, object] = {
        "schema_version": "ecommerce-delivery-lineage/1",
        "job_id": job_id,
        "handoff_id": handoff.handoff_id,
        "source_package_id": handoff.source_package_id,
        "source_input_hash": handoff.source_input_hash,
        "ad_creative_plan": {
            "artifact_id": plan.artifact_id,
            "revision": plan.revision,
            "content_hash": plan.content_hash,
        },
        "storyboard": {
            "artifact_id": loaded.storyboard.artifact_id,
            "revision": loaded.storyboard.revision,
            "content_hash": loaded.storyboard.content_hash,
        },
        "shots": [
            {
                "artifact_id": item.artifact_id,
                "revision": item.revision,
                "content_hash": item.content_hash,
            }
            for item in loaded.shots
        ],
        "composition": {
            "artifact_id": compiled_handoff.composition_spec.artifact_id,
            "revision": compiled_handoff.composition_spec.revision,
            "content_hash": compiled_handoff.composition_spec.content_hash,
        },
        "project_id": manifest.project_id,
        "manifest_revision": manifest.manifest_revision,
        "project": manifest.active_project.model_dump(mode="json"),
        "project_source_provenance": [
            item.model_dump(mode="json") for item in loaded.project.source_provenance
        ],
        "registry": manifest.active_registry.model_dump(mode="json"),
        "dependency_graph": manifest.active_dependency_graph.model_dump(mode="json"),
        "render_state": manifest.active_render_state.model_dump(mode="json"),
        "render_timeline": render.timeline.model_dump(mode="json"),
        "render_receipt": render.render_receipt.model_dump(mode="json"),
        "render_media_facts": render_receipt.measured.model_dump(mode="json"),
        "render_output_sha256": render.output.file_sha256,
        "render_output_size_bytes": render.output.size_bytes,
        "timeline_fingerprint": render.timeline_fingerprint,
        "qa_policy": manifest.active_qa_policy.model_dump(mode="json"),
        "review_receipts": [
            item.model_dump(mode="json")
            for item in acceptance.required_review_receipts
        ],
        "approved_repair": (
            None
            if manifest.active_approved_repair is None
            else manifest.active_approved_repair.model_dump(mode="json")
        ),
        "repair_outcomes": [
            item.model_dump(mode="json")
            for item in manifest.repair_outcome_receipts
        ],
        "final_acceptance": acceptance_pointer.model_dump(mode="json"),
        "provider_materialization_and_shot_gates": provider_lineage,
        "asset_requirements": [
            item.model_dump(mode="json") for item in handoff.asset_requirements
        ],
        "delivery_profile": loaded.project.delivery_profile.model_dump(mode="json"),
        "renderer": render.renderer.model_dump(mode="json"),
        "exported_at": exported_at,
        "tool_identity": tool_identity.model_dump(mode="json"),
    }
    return (
        lineage,
        source,
        source_hash,
        source_size,
        acceptance_pointer.content_hash,
    )


def _expected_bundle(
    lineage: dict[str, object],
    *,
    source_hash: str,
    source_size: int,
) -> tuple[str, str, bytes, bytes]:
    lineage_payload = _json_bytes(lineage)
    lineage_hash = hashlib.sha256(lineage_payload).hexdigest()
    entries = (
        {
            "path": "final.mp4",
            "sha256": source_hash,
            "size_bytes": source_size,
        },
        {
            "path": "lineage.json",
            "sha256": lineage_hash,
            "size_bytes": len(lineage_payload),
        },
    )
    inventory_hash = canonical_sha256(
        {"schema": "ecommerce-delivery-inventory/1", "entries": entries}
    )
    bundle_id = canonical_sha256(
        {
            "schema": "ecommerce-delivery-bundle/1",
            "handoff_id": lineage["handoff_id"],
            "final_acceptance": lineage["final_acceptance"],
            "inventory_hash": inventory_hash,
        }
    )
    bundle_payload = _json_bytes(
        {
            "schema_version": "ecommerce-delivery-bundle/1",
            "bundle_id": bundle_id,
            "inventory_hash": inventory_hash,
            "entries": entries,
        }
    )
    return bundle_id, inventory_hash, lineage_payload, bundle_payload


def _verify_bundle(
    bundle_path: Path,
    *,
    lineage_payload: bytes,
    bundle_payload: bytes,
    source_hash: str,
    source_size: int,
) -> None:
    if not bundle_path.is_dir() or bundle_path.is_symlink():
        raise _invalid("Delivery bundle path is not a regular directory.")
    expected = {"bundle.json", "final.mp4", "lineage.json"}
    if {item.name for item in bundle_path.iterdir()} != expected:
        raise _invalid("Delivery bundle inventory is incomplete or contains extras.")
    try:
        lineage = _read_regular_file_nofollow(
            bundle_path / "lineage.json", contained_by=bundle_path
        )
        inventory = _read_regular_file_nofollow(
            bundle_path / "bundle.json", contained_by=bundle_path
        )
        if lineage.link_count != 1 or inventory.link_count != 1:
            raise ValueError("Delivery bundle metadata must own its bytes.")
        digest = hashlib.sha256()
        size = 0
        with _open_regular_file_nofollow(
            bundle_path / "final.mp4", contained_by=bundle_path
        ) as (descriptor, opened):
            if opened.st_nlink != 1:
                raise ValueError("Delivery media must own its bytes.")
            while chunk := os.read(descriptor, 1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
            final = os.fstat(descriptor)
            if final.st_nlink != 1 or final.st_size != size:
                raise ValueError("Delivery media changed during verification.")
    except (OSError, ValueError) as exc:
        raise _invalid(
            "Delivery bundle entries must be independent regular files.", detail=str(exc)
        ) from exc
    if lineage.data != lineage_payload:
        raise _invalid("Delivery lineage bytes do not match the accepted render.")
    if inventory.data != bundle_payload:
        raise _invalid("Delivery inventory bytes are invalid.")
    if digest.hexdigest() != source_hash or size != source_size:
        raise _invalid("Delivery media bytes do not match the accepted render.")


def package_ecommerce_delivery(
    *,
    project_root: str | Path,
    delivery_root: str | Path,
    job_id: str,
    handoff: EcommerceProductionHandoff,
    plan: AdCreativePlan,
    compiled_handoff: CompiledAdCreativeHandoff,
    exported_at: str,
    tool_identity: ToolIdentity,
) -> EcommerceDeliveryBundleResult:
    """Publish exact accepted bytes through a verified same-filesystem rename."""

    root = Path(project_root).resolve(strict=True)
    destination = Path(delivery_root).resolve(strict=False)
    if not job_id.strip():
        raise _invalid("Delivery Job identity is invalid.")
    lineage, source, source_hash, source_size, acceptance_hash = _current_lineage(
        root,
        job_id=job_id,
        handoff=handoff,
        plan=plan,
        compiled_handoff=compiled_handoff,
        exported_at=exported_at,
        tool_identity=tool_identity,
    )
    bundle_id, inventory_hash, lineage_payload, bundle_payload = _expected_bundle(
        lineage,
        source_hash=source_hash,
        source_size=source_size,
    )
    bundle_path = destination / f"bundle.{bundle_id}"
    result = EcommerceDeliveryBundleResult(
        bundle_id=bundle_id,
        bundle_path=bundle_path,
        inventory_hash=inventory_hash,
        render_output_sha256=source_hash,
        final_acceptance_content_hash=acceptance_hash,
    )
    if bundle_path.exists() or bundle_path.is_symlink():
        _verify_bundle(
            bundle_path,
            lineage_payload=lineage_payload,
            bundle_payload=bundle_payload,
            source_hash=source_hash,
            source_size=source_size,
        )
        return result

    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{bundle_id}.", dir=destination))
    try:
        shutil.copyfile(source, staging / "final.mp4")
        with (staging / "final.mp4").open("rb") as handle:
            os.fsync(handle.fileno())
        _write_file(staging / "lineage.json", lineage_payload)
        _write_file(staging / "bundle.json", bundle_payload)
        _verify_bundle(
            staging,
            lineage_payload=lineage_payload,
            bundle_payload=bundle_payload,
            source_hash=source_hash,
            source_size=source_size,
        )
        current = _current_lineage(
            root,
            job_id=job_id,
            handoff=handoff,
            plan=plan,
            compiled_handoff=compiled_handoff,
            exported_at=exported_at,
            tool_identity=tool_identity,
        )
        if current[0] != lineage or current[2:5] != (
            source_hash,
            source_size,
            acceptance_hash,
        ):
            raise _invalid("Final Acceptance changed during delivery packaging.")
        _fsync_directory(staging)
        os.replace(staging, bundle_path)
        _fsync_directory(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    _verify_bundle(
        bundle_path,
        lineage_payload=lineage_payload,
        bundle_payload=bundle_payload,
        source_hash=source_hash,
        source_size=source_size,
    )
    return result


def inspect_ecommerce_delivery(
    *,
    project_root: str | Path,
    delivery_root: str | Path,
    job_id: str,
    handoff: EcommerceProductionHandoff,
    plan: AdCreativePlan,
    compiled_handoff: CompiledAdCreativeHandoff,
    exported_at: str,
    tool_identity: ToolIdentity,
) -> EcommerceDeliveryBundleResult | None:
    """Return one exact existing bundle without creating directories or files."""

    root = Path(project_root).resolve(strict=True)
    destination = Path(delivery_root).resolve(strict=False)
    lineage, _, source_hash, source_size, acceptance_hash = _current_lineage(
        root,
        job_id=job_id,
        handoff=handoff,
        plan=plan,
        compiled_handoff=compiled_handoff,
        exported_at=exported_at,
        tool_identity=tool_identity,
    )
    bundle_id, inventory_hash, lineage_payload, bundle_payload = _expected_bundle(
        lineage,
        source_hash=source_hash,
        source_size=source_size,
    )
    bundle_path = destination / f"bundle.{bundle_id}"
    if not bundle_path.exists() and not bundle_path.is_symlink():
        return None
    _verify_bundle(
        bundle_path,
        lineage_payload=lineage_payload,
        bundle_payload=bundle_payload,
        source_hash=source_hash,
        source_size=source_size,
    )
    return EcommerceDeliveryBundleResult(
        bundle_id=bundle_id,
        bundle_path=bundle_path,
        inventory_hash=inventory_hash,
        render_output_sha256=source_hash,
        final_acceptance_content_hash=acceptance_hash,
    )


__all__ = [
    "EcommerceDeliveryBundleResult",
    "inspect_ecommerce_delivery",
    "package_ecommerce_delivery",
]
