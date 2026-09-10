from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image_import import (
    AUTOMATED_BROWSER_IMAGE_IMPORT_TOOL,
    HUMAN_IMAGE_IMPORT_TOOL,
    AutomatedBrowserImageImportReceipt,
    CommercialImageImportReceipt,
    HumanImageImportReceipt,
    automated_browser_image_import_asset,
    commercial_image_import_asset,
    human_image_import_asset,
    prepare_automated_browser_image_import_commit,
    prepare_human_image_import_commit,
    validate_automated_browser_image_import,
    validate_commercial_image_import,
    validate_human_image_import,
)
from ai_video.production.image_import_video_frame import (
    VideoFrameImageImportReferenceBinding,
    validate_video_frame_reference_bytes,
)
from ai_video.production.commercial_reference import (
    ProductReferenceAssetBinding,
    ProductReferenceSet,
)
from ai_video.production.dependency import (
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ActorIdentity,
    ArtifactReference,
    AssetRegistrySnapshot,
    AssetSourceKind,
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
)
from ai_video.production.paths import (
    canonical_automated_browser_image_import_receipt_path,
    canonical_dependency_graph_snapshot_path,
    canonical_human_image_import_receipt_path,
    canonical_image_asset_path,
    canonical_image_shot_revision_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
import production_project_factory as project_factory


def _receipt(image_bytes: bytes, **overrides: object) -> HumanImageImportReceipt:
    values: dict[str, object] = {
        "declared_ui_product_label": "ChatGPT Images 2.0",
        "original_filename": "downloaded-image.png",
        "output_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "output_size_bytes": len(image_bytes),
        "output_width": 2,
        "output_height": 1,
        "imported_at": "2026-08-18T10:00:00+08:00",
        "prompt_fingerprint": "1" * 64,
        "references": (),
        "target_kind": "key_shot",
        "target_artifact_id": "shot-artifact-1",
        "target_asset_role": "still",
        "human_actor": ActorIdentity(actor_id="human-operator", actor_kind="human"),
        "approved": True,
        "approved_at": "2026-08-18T10:01:00+08:00",
        "license_source_note": "Human supplied; ownership not inferred.",
    }
    values.update(overrides)
    return HumanImageImportReceipt.create(**values)


def _automated_receipt(
    image_bytes: bytes, **overrides: object
) -> AutomatedBrowserImageImportReceipt:
    values: dict[str, object] = {
        "declared_ui_product_label": "GPT Image 2",
        "original_filename": "image-01.png",
        "output_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "output_size_bytes": len(image_bytes),
        "output_width": 2,
        "output_height": 1,
        "generated_at": "2026-08-23T01:23:28+08:00",
        "approved_at": "2026-08-23T01:25:00+08:00",
        "imported_at": "2026-08-23T01:30:00+08:00",
        "prompt_fingerprint": "2" * 64,
        "references": (),
        "target_kind": "key_shot",
        "target_artifact_id": "shot-artifact-1",
        "target_asset_role": "still",
        "automation_actor": ActorIdentity(
            actor_id="gpt-image-2-mcp", actor_kind="automation"
        ),
        "human_approval_actor": ActorIdentity(
            actor_id="human-operator", actor_kind="human"
        ),
        "approved": True,
        "license_source_note": "User-approved generated reference; rights not inferred.",
    }
    values.update(overrides)
    return AutomatedBrowserImageImportReceipt.create(**values)


def _ffmpeg_version() -> str:
    return subprocess.run(
        ["ffmpeg", "-version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0].split()[2]


def _video_frame_reference(
    tmp_path: Path, source_video: Path, *, frame_index: int
) -> tuple[bytes, dict[str, object], tuple[PreparedArtifact, ...]]:
    extracted = tmp_path / "extracted-frame.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(source_video),
            "-vf",
            f"select=eq(n\\,{frame_index})",
            "-frames:v",
            "1",
            str(extracted),
        ],
        check=True,
    )
    source_bytes = source_video.read_bytes()
    frame_bytes = extracted.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    frame_sha256 = hashlib.sha256(frame_bytes).hexdigest()
    with Image.open(BytesIO(frame_bytes)) as image:
        width, height = image.size
    reference = {
        "role": "video_frame",
        "source_video_path": f"evidence/video-frame-import/{source_sha256}.mp4",
        "source_video_sha256": source_sha256,
        "source_video_size_bytes": len(source_bytes),
        "extracted_frame_path": f"evidence/video-frame-import/{frame_sha256}.png",
        "extracted_frame_sha256": frame_sha256,
        "extracted_frame_size_bytes": len(frame_bytes),
        "extracted_frame_width": width,
        "extracted_frame_height": height,
        "frame_index": frame_index,
        "extraction_contract_version": "video-frame-import-v1",
        "extractor_name": "ffmpeg",
        "extractor_version": _ffmpeg_version(),
    }
    binding = VideoFrameImageImportReferenceBinding.model_validate(reference)
    return (
        frame_bytes,
        reference,
        (
            PreparedArtifact(
                binding.source_video_path,
                source_bytes,
                source_sha256,
            ),
            PreparedArtifact(
                binding.extracted_frame_path,
                frame_bytes,
                frame_sha256,
            ),
        ),
    )


def test_human_import_receipt_is_truthful_sealed_and_builds_imported_asset() -> None:
    png = project_factory._p7_png()
    receipt = _receipt(png)

    validate_human_image_import(receipt, png)
    asset = human_image_import_asset(receipt)

    assert receipt.source_surface == "chatgpt_images_2_web"
    assert receipt.backend_model_id is None
    assert receipt.provider_request_id is None
    assert not receipt.durable_submit_intent_present
    assert not receipt.automated_browser
    assert asset.source_kind is AssetSourceKind.IMPORTED
    assert asset.tool == HUMAN_IMAGE_IMPORT_TOOL
    assert asset.creation_receipt_id == receipt.content_hash


def test_codex_imagegen_import_keeps_its_truthful_source_tool_identity() -> None:
    png = project_factory._p7_png()
    receipt = _receipt(
        png,
        source_surface="codex_imagegen_tool",
        declared_ui_product_label="OpenAI imagegen",
        original_filename="approved-endpoint.png",
    )

    validate_human_image_import(receipt, png)
    asset = human_image_import_asset(receipt)

    assert receipt.source_surface == "codex_imagegen_tool"
    assert receipt.backend_model_id is None
    assert receipt.provider_request_id is None
    assert not receipt.automated_browser
    assert asset.tool.name == "codex-imagegen-import"
    assert asset.tool.version == "1"


def test_automated_browser_import_is_truthful_sealed_and_distinct() -> None:
    png = project_factory._p7_png()
    receipt = _automated_receipt(png)

    validate_automated_browser_image_import(receipt, png)
    asset = automated_browser_image_import_asset(receipt)

    assert receipt.source_surface == "gpt_image_2_mcp_chatgpt_web"
    assert receipt.backend_model_id is None
    assert receipt.provider_request_id is None
    assert receipt.automated_browser
    assert receipt.source_generation_remote
    assert asset.tool == AUTOMATED_BROWSER_IMAGE_IMPORT_TOOL
    assert asset.tool != HUMAN_IMAGE_IMPORT_TOOL
    assert receipt.content_hash == (
        "c64366d543e373ce4958e92abd58b68a97a29634e12bf4b74b1328a9d019eb68"
    )


def test_automated_browser_import_accepts_a_truthful_raw_video_frame_reference() -> None:
    png = project_factory._p7_png()

    receipt = _automated_receipt(
        png,
        references=(
            {
                "role": "video_frame",
                "source_video_path": f"evidence/video-frame-import/{'a' * 64}.mp4",
                "source_video_sha256": "a" * 64,
                "source_video_size_bytes": 123,
                "extracted_frame_path": (
                    "evidence/video-frame-import/"
                    f"{hashlib.sha256(png).hexdigest()}.png"
                ),
                "extracted_frame_sha256": hashlib.sha256(png).hexdigest(),
                "extracted_frame_size_bytes": len(png),
                "extracted_frame_width": 2,
                "extracted_frame_height": 1,
                "frame_index": 71,
                "extraction_contract_version": "video-frame-import-v1",
                "extractor_name": "ffmpeg",
                "extractor_version": "fixture-1",
            },
        ),
    )

    assert receipt.references[0].role == "video_frame"


def test_video_frame_reference_rejects_wrong_frame_tampering_and_traversal(
    tmp_path: Path, tiny_video: Path
) -> None:
    frame_bytes, reference, artifacts = _video_frame_reference(
        tmp_path, tiny_video, frame_index=7
    )
    binding = VideoFrameImageImportReferenceBinding.model_validate(reference)

    validate_video_frame_reference_bytes(
        binding,
        source_video_bytes=artifacts[0].payload,
        extracted_frame_bytes=frame_bytes,
        verify_derivation=True,
    )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            binding.model_copy(update={"frame_index": 8}),
            source_video_bytes=artifacts[0].payload,
            extracted_frame_bytes=frame_bytes,
            verify_derivation=True,
        )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            binding,
            source_video_bytes=artifacts[0].payload + b"tampered",
            extracted_frame_bytes=frame_bytes,
            verify_derivation=False,
        )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            binding,
            source_video_bytes=artifacts[0].payload,
            extracted_frame_bytes=frame_bytes + b"tampered",
            verify_derivation=False,
        )
    with pytest.raises(ValidationError):
        VideoFrameImageImportReferenceBinding.model_validate(
            {**reference, "source_video_path": "../source.mp4"}
        )


def test_video_frame_reference_rejects_alpha_disguised_source_and_pixel_count_collision(
    tmp_path: Path, tiny_video: Path
) -> None:
    frame_bytes, reference, artifacts = _video_frame_reference(
        tmp_path, tiny_video, frame_index=7
    )
    binding = VideoFrameImageImportReferenceBinding.model_validate(reference)

    def frame_binding(payload: bytes, *, width: int, height: int):
        digest = hashlib.sha256(payload).hexdigest()
        return VideoFrameImageImportReferenceBinding.model_validate(
            {
                **binding.model_dump(mode="json"),
                "extracted_frame_path": f"evidence/video-frame-import/{digest}.png",
                "extracted_frame_sha256": digest,
                "extracted_frame_size_bytes": len(payload),
                "extracted_frame_width": width,
                "extracted_frame_height": height,
            }
        )

    with Image.open(BytesIO(frame_bytes)) as image:
        rgb = image.convert("RGB")
        reshaped = Image.frombytes("RGB", (160, 480), rgb.tobytes())
        reshaped_output = BytesIO()
        reshaped.save(reshaped_output, format="PNG")
        transparent = rgb.convert("RGBA")
        alpha = Image.new("L", transparent.size, color=255)
        alpha.putpixel((0, 0), 0)
        transparent.putalpha(alpha)
        transparent_output = BytesIO()
        transparent.save(transparent_output, format="PNG")

    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            frame_binding(reshaped_output.getvalue(), width=160, height=480),
            source_video_bytes=artifacts[0].payload,
            extracted_frame_bytes=reshaped_output.getvalue(),
            verify_derivation=True,
        )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            frame_binding(transparent_output.getvalue(), width=320, height=240),
            source_video_bytes=artifacts[0].payload,
            extracted_frame_bytes=transparent_output.getvalue(),
            verify_derivation=False,
        )
    disguised = VideoFrameImageImportReferenceBinding.model_validate(
        {
            **binding.model_dump(mode="json"),
            "source_video_path": (
                "evidence/video-frame-import/"
                f"{hashlib.sha256(frame_bytes).hexdigest()}.mp4"
            ),
            "source_video_sha256": hashlib.sha256(frame_bytes).hexdigest(),
            "source_video_size_bytes": len(frame_bytes),
        }
    )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            disguised,
            source_video_bytes=frame_bytes,
            extracted_frame_bytes=frame_bytes,
            verify_derivation=False,
        )

    def box(kind: bytes, payload: bytes) -> bytes:
        return (len(payload) + 8).to_bytes(4, "big") + kind + payload

    external_dref = box(
        b"dref",
        b"\x00\x00\x00\x00"
        + (1).to_bytes(4, "big")
        + box(b"url ", b"\x00\x00\x00\x00external.mov\x00"),
    )
    external_source = box(b"ftyp", b"isom\x00\x00\x02\x00isom") + box(
        b"moov", box(b"trak", box(b"mdia", box(b"minf", box(b"dinf", external_dref))))
    )
    external_digest = hashlib.sha256(external_source).hexdigest()
    external = VideoFrameImageImportReferenceBinding.model_validate(
        {
            **binding.model_dump(mode="json"),
            "source_video_path": f"evidence/video-frame-import/{external_digest}.mp4",
            "source_video_sha256": external_digest,
            "source_video_size_bytes": len(external_source),
        }
    )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            external,
            source_video_bytes=external_source,
            extracted_frame_bytes=frame_bytes,
            verify_derivation=False,
        )

    nested = b""
    for _ in range(10):
        nested = box(b"moov", nested)
    deep_source = box(b"ftyp", b"isom\x00\x00\x02\x00isom") + nested
    deep_digest = hashlib.sha256(deep_source).hexdigest()
    deep = VideoFrameImageImportReferenceBinding.model_validate(
        {
            **binding.model_dump(mode="json"),
            "source_video_path": f"evidence/video-frame-import/{deep_digest}.mp4",
            "source_video_sha256": deep_digest,
            "source_video_size_bytes": len(deep_source),
        }
    )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            deep,
            source_video_bytes=deep_source,
            extracted_frame_bytes=frame_bytes,
            verify_derivation=False,
        )


def test_video_frame_reference_accepts_autorotated_frame_and_rejects_reshaping(
    tmp_path: Path, tiny_video: Path
) -> None:
    rotated = tmp_path / "rotated.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(tiny_video),
            "-c",
            "copy",
            "-metadata:s:v:0",
            "rotate=90",
            str(rotated),
        ],
        check=True,
    )
    frame_bytes, reference, artifacts = _video_frame_reference(
        tmp_path, rotated, frame_index=7
    )
    binding = VideoFrameImageImportReferenceBinding.model_validate(reference)
    assert (binding.extracted_frame_width, binding.extracted_frame_height) == (240, 320)
    validate_video_frame_reference_bytes(
        binding,
        source_video_bytes=artifacts[0].payload,
        extracted_frame_bytes=frame_bytes,
        verify_derivation=True,
    )
    with Image.open(BytesIO(frame_bytes)) as image:
        reshaped = Image.frombytes("RGB", (480, 160), image.convert("RGB").tobytes())
        output = BytesIO()
        reshaped.save(output, format="PNG")
    reshaped_bytes = output.getvalue()
    digest = hashlib.sha256(reshaped_bytes).hexdigest()
    reshaped_binding = VideoFrameImageImportReferenceBinding.model_validate(
        {
            **binding.model_dump(mode="json"),
            "extracted_frame_path": f"evidence/video-frame-import/{digest}.png",
            "extracted_frame_sha256": digest,
            "extracted_frame_size_bytes": len(reshaped_bytes),
            "extracted_frame_width": 480,
            "extracted_frame_height": 160,
        }
    )
    with pytest.raises(AiVideoError):
        validate_video_frame_reference_bytes(
            reshaped_binding,
            source_video_bytes=artifacts[0].payload,
            extracted_frame_bytes=reshaped_bytes,
            verify_derivation=True,
        )


def test_bootstrap_validates_video_frame_derivation_only_before_initial_write(
    tmp_path: Path, tiny_video: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    valid_target = tmp_path / "valid-target"
    invalid_target = tmp_path / "invalid-target"
    source.mkdir()
    valid_target.mkdir()
    invalid_target.mkdir()
    project_factory.write_production_project(source)
    base = load_production_project(source / "project.yaml")
    frame_bytes, reference, reference_artifacts = _video_frame_reference(
        tmp_path, tiny_video, frame_index=7
    )

    def bootstrap_inputs(
        target: Path, raw_reference: dict[str, object]
    ) -> tuple[ProductionStateCommitter, AssetRegistrySnapshot, tuple[PreparedArtifact, ...]]:
        writer = ProductionStateCommitter(target)
        receipt = _automated_receipt(frame_bytes, references=(raw_reference,))
        asset = automated_browser_image_import_asset(receipt)
        provisional = base.registry.model_copy(
            update={
                "revision_id": "0" * 64,
                "content_hash": "0" * 64,
                "assets": (*base.registry.assets, asset),
            }
        )
        registry_hash = registry_semantic_sha256(provisional)
        registry = provisional.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        )
        required = {
            base.project.artifacts.brief.path,
            base.project.artifacts.story.path,
            base.project.artifacts.storyboard.path,
            *(item.path for item in base.project.artifacts.characters),
            *(item.path for item in base.project.artifacts.scenes),
            *(item.path for item in base.project.artifacts.shots),
            *(item.artifact_path for item in base.registry.assets),
        }
        prepared = [
            writer.prepare_artifact("bootstrap-video-frame", path, (source / path).read_bytes())
            for path in sorted(required, key=Path.as_posix)
        ]
        prepared.extend(
            (
                writer.prepare_artifact(
                    "bootstrap-video-frame", canonical_image_asset_path(asset.sha256), frame_bytes
                ),
                writer.prepare_artifact(
                    "bootstrap-video-frame",
                    canonical_automated_browser_image_import_receipt_path(receipt.content_hash),
                    _canonical_json_bytes(receipt),
                ),
                *reference_artifacts,
            )
        )
        return writer, registry, tuple(prepared)

    writer, registry, artifacts = bootstrap_inputs(valid_target, reference)
    committed = writer.bootstrap_initial_state(
        attempt_id="bootstrap-video-frame",
        project=base.project,
        registry=registry,
        artifacts=artifacts,
    )

    import ai_video.production.image_import_video_frame as video_frame_module

    original_validate = video_frame_module.validate_video_frame_reference_bytes

    def fail_if_rederived(*args, **kwargs):
        if kwargs["verify_derivation"]:
            raise AssertionError("exact bootstrap replay must not decode media")
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(
        video_frame_module, "validate_video_frame_reference_bytes", fail_if_rederived
    )
    assert writer.bootstrap_initial_state(
        attempt_id="bootstrap-video-frame-replay",
        project=base.project,
        registry=registry,
        artifacts=artifacts,
    ) == committed

    bad_writer, bad_registry, bad_artifacts = bootstrap_inputs(
        invalid_target, {**reference, "frame_index": 8}
    )
    monkeypatch.setattr(
        video_frame_module,
        "validate_video_frame_reference_bytes",
        original_validate,
    )
    with pytest.raises(AiVideoError):
        bad_writer.bootstrap_initial_state(
            attempt_id="bootstrap-video-frame-bad-index",
            project=base.project,
            registry=bad_registry,
            artifacts=bad_artifacts,
        )
    assert not (invalid_target / "state/manifest.json").exists()


def test_commercial_interaction_import_binds_product_character_scene_and_exact_png() -> None:
    png = project_factory._p7_png()
    reference_set = ProductReferenceSet.create(
        artifact_id="product-reference-qingyan",
        revision=1,
        product_id="qingyan-spray",
        sku_id="qingyan-yellow-50ml",
        formal_name="青颜净味喷雾",
        truth_reference_ids=("truth-packaging",),
        registry_revision_id="8" * 64,
        registry_content_hash="8" * 64,
        assets=(
            ProductReferenceAssetBinding(
                asset_id="product-front",
                asset_sha256="5" * 64,
                mime_type="image/png",
                width=2,
                height=1,
                view="front",
                purpose="product_truth",
            ),
            ProductReferenceAssetBinding(
                asset_id="product-label",
                asset_sha256="6" * 64,
                mime_type="image/png",
                width=2,
                height=1,
                view="label",
                purpose="label",
            ),
        ),
        packaging_form="yellow carton and spray bottle",
        bottle_silhouette="slender bottle",
        dominant_color="yellow",
        cap_color="white",
        logo_label_identity="青颜 yellow label",
        protected_text_zones=("front-label",),
    )
    receipt = CommercialImageImportReceipt.create(
        source_kind="human_observed_import",
        original_filename="qingyan-interaction-04.png",
        output_asset_id="interaction-keyframe-04",
        output_sha256=hashlib.sha256(png).hexdigest(),
        output_size_bytes=len(png),
        output_width=2,
        output_height=1,
        imported_at="2026-08-25T10:00:00+08:00",
        prompt_fingerprint="3" * 64,
        target_kind="commercial_interaction_keyframe",
        target_id="source-request-04",
        product_reference_set=reference_set,
        target_shot_id="shot-04",
        target_shot_content_hash="7" * 64,
        character_reference_ids=("character-qingyan",),
        scene_reference_ids=("scene-bedroom",),
        observed_by=ActorIdentity(actor_id="human-operator", actor_kind="human"),
        provenance_note="Human-observed local import; no Provider submit claimed.",
        usage_license="test-only",
    )

    validate_commercial_image_import(receipt, png)
    asset = commercial_image_import_asset(receipt)

    assert asset.asset_id == "interaction-keyframe-04"
    assert asset.sha256 == receipt.output_sha256
    assert asset.source_kind is AssetSourceKind.IMPORTED
    assert asset.input_artifact_ids == (
        "product-label",
        "product-front",
        "character-qingyan",
        "scene-bedroom",
        "shot-04",
    )
    with pytest.raises(AiVideoError) as caught:
        validate_commercial_image_import(receipt, png + b"tampered")
    assert caught.value.code is ErrorCode.IMAGE_ASSET_INVALID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("backend_model_id", "invented-model"),
        ("provider_request_id", "invented-request"),
        ("durable_submit_intent_present", True),
        ("automated_browser", True),
        ("approved", False),
        ("license_source_note", ""),
        ("human_actor", ActorIdentity(actor_id="bot", actor_kind="automation")),
    ],
)
def test_human_import_receipt_rejects_invented_or_nonhuman_evidence(
    field: str,
    value: object,
) -> None:
    with pytest.raises((ValidationError, ValueError)):
        _receipt(project_factory._p7_png(), **{field: value})


def test_human_import_rejects_tampered_or_non_png_bytes() -> None:
    png = project_factory._p7_png()
    receipt = _receipt(png)

    with pytest.raises(AiVideoError) as tampered:
        validate_human_image_import(receipt, png + b"tampered")
    with pytest.raises(AiVideoError) as non_png:
        validate_human_image_import(receipt, b"not-png")

    assert tampered.value.code is ErrorCode.IMAGE_ASSET_INVALID
    assert non_png.value.code is ErrorCode.IMAGE_ASSET_INVALID


def test_human_import_original_filename_is_a_png_basename() -> None:
    png = project_factory._p7_png()
    with pytest.raises(ValidationError):
        _receipt(png, original_filename="../downloaded-image.png")
    with pytest.raises(ValidationError):
        _receipt(png, original_filename="downloaded-image.webp")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("imported_at", "2026-08-18T10:00:00"),
        ("approved_at", "not-a-timestamp"),
        ("approved_at", "2026-08-18T09:59:59+08:00"),
    ],
)
def test_human_import_requires_ordered_offset_timestamps(
    field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        _receipt(project_factory._p7_png(), **{field: value})


@pytest.mark.parametrize(
    "target_kind",
    ["character_master", "scene_reference", "key_shot", "repair_replacement"],
)
@pytest.mark.parametrize(
    "import_kind", ["human", "automated_browser", "codex_imagegen"]
)
def test_human_import_reuses_atomic_project_registry_graph_commit_and_replays(
    tmp_path: Path,
    target_kind: str,
    import_kind: str,
) -> None:
    project_factory.write_production_project(tmp_path)
    base_inputs = project_factory.make_p7_image_generation_base(tmp_path)
    initial = load_production_project(tmp_path / "project.yaml")
    ProductionStateCommitter(tmp_path).upgrade_manifest_schema(
        "2.5", expected_manifest_revision=initial.manifest.manifest_revision
    )
    base = load_production_project(tmp_path / "project.yaml")
    field = {
        "character_master": "characters",
        "scene_reference": "scenes",
        "key_shot": "shots",
        "repair_replacement": "shots",
    }[target_kind]
    base_target = getattr(base, field)[0]
    target_role = (
        base_target.required_asset_roles[0].role if field == "shots" else "reference"
    )
    png = project_factory._p7_png()
    receipt_factory = (
        _automated_receipt if import_kind == "automated_browser" else _receipt
    )
    asset_factory = (
        human_image_import_asset
        if import_kind != "automated_browser"
        else automated_browser_image_import_asset
    )
    commit_preparer = (
        prepare_human_image_import_commit
        if import_kind != "automated_browser"
        else prepare_automated_browser_image_import_commit
    )
    receipt_overrides = (
        {
            "source_surface": "codex_imagegen_tool",
            "declared_ui_product_label": "OpenAI imagegen",
        }
        if import_kind == "codex_imagegen"
        else {}
    )
    receipt = receipt_factory(
        png,
        target_kind=target_kind,
        target_artifact_id=base_target.artifact_id,
        target_asset_role=target_role,
        **receipt_overrides,
    )
    asset = asset_factory(receipt)

    candidate_registry = base.registry.model_copy(
        update={
            "revision_id": "0" * 64,
            "content_hash": "0" * 64,
            "assets": (*base.registry.assets, asset),
        }
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_payload = _canonical_json_bytes(candidate_registry)
    registry_pointer = RegistrySnapshotPointer(
        path=Path(f"assets/registry.{registry_hash}.json"),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )

    target_update = {
        "revision": base_target.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": receipt.content_hash,
    }
    if field == "characters":
        target_update["reference_asset_ids"] = (asset.asset_id,)
    elif field == "scenes":
        target_update["visual_reference_asset_ids"] = (asset.asset_id,)
    else:
        target_update["required_asset_roles"] = tuple(
            role.model_copy(update={"asset_ids": (asset.asset_id,)})
            if role.role == receipt.target_asset_role
            else role
            for role in base_target.required_asset_roles
        )
    candidate_target = seal_artifact(
        base_target.model_copy(
            update={
                **target_update,
            }
        )
    )
    target_path = (
        canonical_image_shot_revision_path(
            candidate_target.revision, candidate_target.content_hash
        )
        if field == "shots"
        else Path(
            f"creative/{field}/{candidate_target.artifact_id}."
            f"{candidate_target.revision}.{candidate_target.content_hash}.yaml"
        )
    )
    target_payload = _canonical_yaml_bytes(candidate_target)
    candidate_project = seal_artifact(
        base.project.model_copy(
            update={
                "revision": base.project.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": receipt.content_hash,
                "artifacts": base.project.artifacts.model_copy(
                    update={
                        field: tuple(
                            ArtifactReference(
                                artifact_id=candidate_target.artifact_id,
                                revision=candidate_target.revision,
                                content_hash=candidate_target.content_hash,
                                path=target_path,
                            )
                            if item.artifact_id == candidate_target.artifact_id
                            else item
                            for item in getattr(base.project.artifacts, field)
                        )
                    }
                ),
            }
        )
    )
    project_payload = _canonical_yaml_bytes(candidate_project)
    project_path = Path(
        f"state/projects/project.{candidate_project.revision}."
        f"{candidate_project.content_hash}.yaml"
    )
    project_pointer = ProjectSnapshotPointer(
        path=project_path,
        revision=candidate_project.revision,
        content_hash=candidate_project.content_hash,
        file_sha256=hashlib.sha256(project_payload).hexdigest(),
    )
    candidate_loaded = base.model_copy(
        update={
            "project": candidate_project,
            field: tuple(
                candidate_target
                if item.artifact_id == candidate_target.artifact_id
                else item
                for item in getattr(base, field)
            ),
            "registry": candidate_registry,
            "asset_paths": {
                **base.asset_paths,
                asset.asset_id: tmp_path / asset.artifact_path,
            },
            "manifest": base.manifest.model_copy(
                update={
                    "active_project": project_pointer,
                    "active_registry": registry_pointer,
                }
            ),
        }
    )
    candidate_inputs = replace(base_inputs, project=candidate_loaded)
    graph = build_production_dependency_graph(candidate_inputs)
    resolution = resolve_dependency_state(graph, base.manifest.dependency_states)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=base.manifest.manifest_revision,
        base_dependency_graph=base.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=resolution.states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_payload = _canonical_json_bytes(graph)
    assert transition.candidate_dependency_graph == DependencyGraphSnapshotPointer(
        revision_id=graph.revision_id,
        content_hash=graph.content_hash,
        path=canonical_dependency_graph_snapshot_path(graph.revision_id),
        file_sha256=hashlib.sha256(graph_payload).hexdigest(),
    )
    base_commit = prepare_project_registry_commit(
        manifest=base.manifest,
        project=candidate_project,
        registry=candidate_registry,
        attempt_id="human-image-import-1",
    )
    base_commit = replace(
        base_commit,
        dependency_graph_transition=transition,
        artifacts=tuple(
            sorted(
                (
                    *base_commit.artifacts,
                    PreparedArtifact(
                        target_path,
                        target_payload,
                        hashlib.sha256(target_payload).hexdigest(),
                    ),
                    PreparedArtifact(
                        transition.candidate_dependency_graph.path,
                        graph_payload,
                        hashlib.sha256(graph_payload).hexdigest(),
                    ),
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
    )
    request = commit_preparer(
        base=base,
        receipt=receipt,
        image_bytes=png,
        candidate_target=candidate_target,
        candidate_project=candidate_project,
        base_commit=base_commit,
    )

    final = ProductionStateCommitter(tmp_path).commit(request)
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest == final
    assert loaded.registry.assets[-1] == asset
    assert getattr(loaded, field)[0] == candidate_target
    assert not any(item.operation == "image_generation" for item in final.attempts)
    assert final.attempts[-1].operation == "commit_project_registry"
    assert final.dependency_states == resolution.states

    if import_kind == "codex_imagegen":
        active_receipt_path = tmp_path / canonical_human_image_import_receipt_path(
            receipt.content_hash
        )
        original_receipt = active_receipt_path.read_bytes()
        tampered_receipt = json.loads(original_receipt)
        tampered_receipt["declared_ui_product_label"] = "tampered"
        active_receipt_path.write_text(
            json.dumps(tampered_receipt, sort_keys=True) + "\n", encoding="utf-8"
        )
        with pytest.raises(AiVideoError):
            load_production_project(tmp_path / "project.yaml")
        active_receipt_path.write_bytes(original_receipt)

    decoy = receipt.model_copy(update={"content_hash": "f" * 64})
    decoy_path = tmp_path / (
        canonical_human_image_import_receipt_path("f" * 64)
        if import_kind != "automated_browser"
        else canonical_automated_browser_image_import_receipt_path("f" * 64)
    )
    decoy_path.parent.mkdir(parents=True, exist_ok=True)
    decoy_path.write_text(
        json.dumps(decoy.model_dump(mode="json"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert load_production_project(tmp_path / "project.yaml").manifest == final

    class _NoWriteCommitter(ProductionStateCommitter):
        def _write_manifest_atomic(self, manifest, *, on_replace=None):
            raise AssertionError("exact import replay must not write")

    assert _NoWriteCommitter(tmp_path).commit(request) == final
