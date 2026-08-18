from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image import ImageReferenceBinding, _measure_png
from ai_video.production.models import (
    ActorIdentity,
    AssetRecord,
    AssetSourceKind,
    AssetType,
    Character,
    EgressMetadata,
    LoadedProductionProject,
    ProductionProject,
    Scene,
    Shot,
    StrictModel,
    ToolIdentity,
)
from ai_video.production.paths import (
    canonical_human_image_import_receipt_path,
    canonical_image_asset_path,
)

from ._state_commit_common import _canonical_json_bytes, _canonical_yaml_bytes
from ._state_commit_contracts import PreparedArtifact, StateCommitRequest


HUMAN_IMAGE_IMPORT_TOOL = ToolIdentity(
    name="chatgpt-images-2-web-import",
    version="1",
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        ErrorCode.IMAGE_ASSET_INVALID,
        message,
        detail,
        retryable=False,
    )


class HumanImageImportReceipt(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"]
    source_surface: Literal["chatgpt_images_2_web"]
    declared_ui_product_label: str = Field(min_length=1)
    backend_model_id: None = None
    original_filename: str = Field(min_length=1)
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_size_bytes: int = Field(strict=True, gt=0)
    output_width: int = Field(strict=True, gt=0)
    output_height: int = Field(strict=True, gt=0)
    imported_at: str = Field(min_length=1)
    prompt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    references: tuple[ImageReferenceBinding, ...]
    target_kind: Literal[
        "character_master", "scene_reference", "key_shot", "repair_replacement"
    ]
    target_artifact_id: str = Field(min_length=1)
    target_asset_role: str = Field(min_length=1)
    human_actor: ActorIdentity
    approved: Literal[True]
    approved_at: str = Field(min_length=1)
    license_source_note: str = Field(min_length=1)
    provider_request_id: None = None
    durable_submit_intent_present: Literal[False] = False
    automated_browser: Literal[False] = False
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_truthful_receipt(self) -> "HumanImageImportReceipt":
        if self.human_actor.actor_kind != "human":
            raise ValueError("human image import approval requires a human actor")
        if Path(self.original_filename).name != self.original_filename:
            raise ValueError("original image filename must be a basename")
        if Path(self.original_filename).suffix.lower() != ".png":
            raise ValueError("human image import requires an original PNG filename")
        try:
            imported_at = datetime.fromisoformat(self.imported_at)
            approved_at = datetime.fromisoformat(self.approved_at)
        except ValueError as exc:
            raise ValueError("human image import timestamps must be RFC 3339") from exc
        if imported_at.tzinfo is None or approved_at.tzinfo is None:
            raise ValueError("human image import timestamps require an explicit offset")
        if approved_at < imported_at:
            raise ValueError("human approval cannot precede image import")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("content_hash does not match human image import receipt")
        return self

    @classmethod
    def create(cls, **values: object) -> "HumanImageImportReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.setdefault("source_surface", "chatgpt_images_2_web")
        data.setdefault("backend_model_id", None)
        data.setdefault("provider_request_id", None)
        data.setdefault("durable_submit_intent_present", False)
        data.setdefault("automated_browser", False)
        data.pop("content_hash", None)
        if (
            data["backend_model_id"] is not None
            or data["provider_request_id"] is not None
            or data["durable_submit_intent_present"] is not False
            or data["automated_browser"] is not False
        ):
            raise ValueError(
                "human web imports cannot claim backend, submit, or automation evidence"
            )
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)


def validate_human_image_import(
    receipt: HumanImageImportReceipt,
    image_bytes: bytes,
) -> None:
    try:
        checked = HumanImageImportReceipt.model_validate(
            receipt.model_dump(mode="python")
        )
        measured = _measure_png(image_bytes)
    except (AttributeError, ValueError, AiVideoError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid("Human image import receipt or PNG is invalid.", detail) from exc
    if checked != receipt or (
        measured.sha256 != receipt.output_sha256
        or measured.size_bytes != receipt.output_size_bytes
        or measured.width != receipt.output_width
        or measured.height != receipt.output_height
    ):
        raise _invalid("Human image import PNG does not match its receipt.")


def human_image_import_asset(receipt: HumanImageImportReceipt) -> AssetRecord:
    inputs = tuple(
        identity
        for reference in receipt.references
        for identity in (reference.creative_artifact_id, reference.asset_id)
    )
    return AssetRecord(
        asset_id=f"image-import-{receipt.content_hash}",
        asset_type=AssetType.IMAGE,
        artifact_path=canonical_image_asset_path(receipt.output_sha256),
        sha256=receipt.output_sha256,
        size_bytes=receipt.output_size_bytes,
        mime_type="image/png",
        width=receipt.output_width,
        height=receipt.output_height,
        source_kind=AssetSourceKind.IMPORTED,
        tool=HUMAN_IMAGE_IMPORT_TOOL,
        input_artifact_ids=inputs,
        input_fingerprint=receipt.prompt_fingerprint,
        creation_receipt_id=receipt.content_hash,
        usage_license=receipt.license_source_note,
        egress=EgressMetadata(remote=False),
    )


def _selected_target(base: LoadedProductionProject, receipt: HumanImageImportReceipt):
    if receipt.target_kind == "character_master":
        return next(
            (item for item in base.characters if item.artifact_id == receipt.target_artifact_id),
            None,
        )
    if receipt.target_kind == "scene_reference":
        return next(
            (item for item in base.scenes if item.artifact_id == receipt.target_artifact_id),
            None,
        )
    return next(
        (item for item in base.shots if item.artifact_id == receipt.target_artifact_id),
        None,
    )


def _validate_target_revision(
    base_target: Character | Scene | Shot,
    candidate_target: Character | Scene | Shot,
    receipt: HumanImageImportReceipt,
    asset: AssetRecord,
) -> None:
    if type(candidate_target) is not type(base_target):
        raise _invalid("Human image import target kind changed unexpectedly.")
    if isinstance(base_target, Character):
        expected = base_target.model_copy(
            update={
                "revision": base_target.revision + 1,
                "reference_asset_ids": (asset.asset_id,),
                "creation_receipt_id": receipt.content_hash,
                "content_hash": candidate_target.content_hash,
            }
        )
    elif isinstance(base_target, Scene):
        expected = base_target.model_copy(
            update={
                "revision": base_target.revision + 1,
                "visual_reference_asset_ids": (asset.asset_id,),
                "creation_receipt_id": receipt.content_hash,
                "content_hash": candidate_target.content_hash,
            }
        )
    else:
        roles = tuple(
            role.model_copy(update={"asset_ids": (asset.asset_id,)})
            if role.role == receipt.target_asset_role
            else role
            for role in base_target.required_asset_roles
        )
        if roles == base_target.required_asset_roles:
            raise _invalid("Human image import Shot role does not exist.")
        expected = base_target.model_copy(
            update={
                "revision": base_target.revision + 1,
                "required_asset_roles": roles,
                "creation_receipt_id": receipt.content_hash,
                "content_hash": candidate_target.content_hash,
            }
        )
    if expected != candidate_target or canonical_sha256(candidate_target) != candidate_target.content_hash:
        raise _invalid("Human image import changed more than its declared target binding.")


def prepare_human_image_import_commit(
    *,
    base: LoadedProductionProject,
    receipt: HumanImageImportReceipt,
    image_bytes: bytes,
    candidate_target: Character | Scene | Shot,
    candidate_project: ProductionProject,
    base_commit: StateCommitRequest,
) -> StateCommitRequest:
    """Add honest import evidence to one already prepared P5 project/registry commit."""

    validate_human_image_import(receipt, image_bytes)
    asset = human_image_import_asset(receipt)
    base_target = _selected_target(base, receipt)
    if base_target is None:
        raise _invalid("Human image import target is absent from the active project.")
    _validate_target_revision(base_target, candidate_target, receipt, asset)
    assets_by_id = {item.asset_id: item for item in base.registry.assets}
    characters = {item.artifact_id: item for item in base.characters}
    scenes = {item.artifact_id: item for item in base.scenes}
    for reference in receipt.references:
        creative = (
            characters.get(reference.creative_artifact_id)
            if reference.role == "character"
            else scenes.get(reference.creative_artifact_id)
            if reference.role == "scene"
            else None
        )
        selected_asset_ids = (
            creative.reference_asset_ids
            if isinstance(creative, Character)
            else creative.visual_reference_asset_ids
            if isinstance(creative, Scene)
            else ()
        )
        selected_asset = assets_by_id.get(reference.asset_id)
        if (
            creative is None
            or creative.revision != reference.creative_revision
            or creative.content_hash != reference.creative_content_hash
            or reference.asset_id not in selected_asset_ids
            or selected_asset is None
            or selected_asset.sha256 != reference.asset_sha256
        ):
            raise _invalid("Human image import reference identity is not active and exact.")
    if (
        base_commit.operation != "commit_project_registry"
        or base_commit.dependency_graph_transition is None
        or base_commit.expected_manifest_revision != base.manifest.manifest_revision
        or candidate_project.content_hash != base_commit.next_project.content_hash
        or canonical_sha256(candidate_project) != candidate_project.content_hash
    ):
        raise _invalid("Human image import must reuse one exact P5 project/registry commit.")

    registry_artifact = next(
        (
            item
            for item in base_commit.artifacts
            if item.relative_path == base_commit.next_registry.path
        ),
        None,
    )
    if registry_artifact is None:
        raise _invalid("Human image import candidate Registry bytes are missing.")
    from ai_video.production.models import AssetRegistrySnapshot

    candidate_registry = AssetRegistrySnapshot.model_validate_json(
        registry_artifact.payload
    )
    if (
        candidate_registry.assets != (*base.registry.assets, asset)
        or base_commit.next_registry.content_hash != candidate_registry.content_hash
    ):
        raise _invalid("Human image import Registry must append exactly one imported asset.")

    target_reference_sets = {
        "character_master": candidate_project.artifacts.characters,
        "scene_reference": candidate_project.artifacts.scenes,
        "key_shot": candidate_project.artifacts.shots,
        "repair_replacement": candidate_project.artifacts.shots,
    }
    references = target_reference_sets[receipt.target_kind]
    selected = tuple(
        item for item in references if item.artifact_id == receipt.target_artifact_id
    )
    if len(selected) != 1 or selected[0].content_hash != candidate_target.content_hash:
        raise _invalid("Human image import Project does not select the declared target revision.")
    field = {
        "character_master": "characters",
        "scene_reference": "scenes",
        "key_shot": "shots",
        "repair_replacement": "shots",
    }[receipt.target_kind]
    expected_refs = tuple(
        selected[0] if item.artifact_id == receipt.target_artifact_id else item
        for item in getattr(base.project.artifacts, field)
    )
    expected_project = base.project.model_copy(
        update={
            "revision": base.project.revision + 1,
            "creation_receipt_id": receipt.content_hash,
            "content_hash": candidate_project.content_hash,
            "artifacts": base.project.artifacts.model_copy(
                update={field: expected_refs}
            ),
        }
    )
    if expected_project != candidate_project:
        raise _invalid("Human image import Project changed outside its declared target.")
    target_artifact = next(
        (
            item
            for item in base_commit.artifacts
            if item.relative_path == selected[0].path
        ),
        None,
    )
    target_payload = _canonical_yaml_bytes(candidate_target)
    if (
        target_artifact is None
        or target_artifact.payload != target_payload
        or target_artifact.file_sha256 != hashlib.sha256(target_payload).hexdigest()
    ):
        raise _invalid("Human image import target artifact bytes are not exact.")

    receipt_payload = _canonical_json_bytes(receipt)
    additions = (
        PreparedArtifact(
            canonical_human_image_import_receipt_path(receipt.content_hash),
            receipt_payload,
            hashlib.sha256(receipt_payload).hexdigest(),
        ),
        PreparedArtifact(
            asset.artifact_path,
            image_bytes,
            receipt.output_sha256,
        ),
    )
    paths = {item.relative_path for item in base_commit.artifacts}
    if any(item.relative_path in paths for item in additions):
        raise _invalid("Human image import evidence collides with candidate artifacts.")
    return replace(
        base_commit,
        artifacts=tuple(
            sorted((*base_commit.artifacts, *additions), key=lambda item: item.relative_path.as_posix())
        ),
    )
