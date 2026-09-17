from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import ActorIdentity
from ai_video.production.video import VideoGenerationMode, VideoMediaReferenceBinding
from test_production_seedance import (
    _FakeTransport,
    _authorization,
    _json_response,
    _paid_preview,
    _permit,
    _profile,
    _request,
)


FIXED_NOW = datetime(2026, 8, 19, 1, 0, tzinfo=UTC)
SOURCE_BYTES = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2white-model-motion"
SOURCE_SHA256 = hashlib.sha256(SOURCE_BYTES).hexdigest()
UPLOAD_URL = "https://upload.storage.example/white-model.mp4?signature=put-secret"
READ_URL = "https://media.storage.example/white-model.mp4?signature=get-secret"


class _Readback:
    def __init__(self, chunks: tuple[bytes, ...]) -> None:
        self.status_code = 200
        self.headers = {"content-type": "video/mp4"}
        self._chunks = chunks

    def iter_bytes(self):
        yield from self._chunks


class _MaterializationTransport:
    def __init__(self, *, readback: bytes = SOURCE_BYTES) -> None:
        self.requests = []
        self.readback = readback

    def upload(self, request, source_bytes: bytes):
        self.requests.append((request, source_bytes))
        return type(
            "UploadResponse",
            (),
            {
                "status_code": 200,
                "headers": {"etag": '"upload-etag"', "x-tos-version-id": "version-1"},
            },
        )()

    @contextmanager
    def stream(self, request):
        self.requests.append((request, None))
        yield _Readback((self.readback[:17], self.readback[17:]))


class _PathSwapTransport(_MaterializationTransport):
    def __init__(self, source_path):
        super().__init__()
        self.source_path = source_path

    def upload(self, request, source_bytes: bytes):
        self.source_path.write_bytes(b"swapped-after-validation")
        return super().upload(request, source_bytes)


def _binding() -> VideoMediaReferenceBinding:
    return VideoMediaReferenceBinding(
        kind="video",
        role="reference_video",
        asset_id="white-model-motion",
        asset_sha256=SOURCE_SHA256,
        mime_type="video/mp4",
        size_bytes=len(SOURCE_BYTES),
        width=1280,
        height=720,
        fps=24,
        duration_millis=5000,
    )


def _contracts(
    module,
    binding: VideoMediaReferenceBinding,
    *,
    target_request_fingerprint: str = "1" * 64,
):
    preview = module.SeedanceLocalVideoMaterializationPreview.create(
        attempt_id="white-model-materialization-1",
        task_scope_id="seedance-blender-white-model-r2v-20260917-001",
        target_provider_kind="volcengine_ark_seedance",
        target_model_id="doubao-seedance-2-0-mini-260615",
        target_request_fingerprint=target_request_fingerprint,
        source_asset_id=binding.asset_id,
        source_registry_revision_id="2" * 64,
        source_asset_sha256=binding.asset_sha256,
        source_mime_type=binding.mime_type,
        source_size_bytes=binding.size_bytes,
        source_width=binding.width,
        source_height=binding.height,
        source_fps=binding.fps,
        source_duration_millis=binding.duration_millis,
        classification="synthetic_non_identity_bearing_video",
        storage_provider="volcengine_tos",
        storage_account_scope="ai-video-development",
        storage_bucket="ai-video-transient",
        storage_object_key_sha256="3" * 64,
        upload_origin="https://upload.storage.example",
        read_origin="https://media.storage.example",
        credential_reference_kind="secret_store",
        credential_reference_id="VOLCENGINE_TOS_UPLOAD",
        retention_mode="task_transient",
        created_at=FIXED_NOW,
        expires_at=FIXED_NOW + timedelta(hours=2),
    )
    authorization = module.SeedanceLocalVideoMaterializationAuthorization.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="operator", actor_kind="human"),
        egress_authorized=True,
        egress_policy_receipt_id="egress-white-model-materialization",
        live_test_authorized=True,
        live_authorization_receipt_id="live-white-model-materialization",
        issued_at=FIXED_NOW - timedelta(minutes=1),
        expires_at=FIXED_NOW + timedelta(minutes=30),
        max_upload_count=1,
    )
    grant = module.SeedanceLocalVideoUploadGrant(
        upload_url=UPLOAD_URL,
        read_url=READ_URL,
        storage_provider=preview.storage_provider,
        storage_account_scope=preview.storage_account_scope,
        storage_bucket=preview.storage_bucket,
        storage_object_key_sha256=preview.storage_object_key_sha256,
        not_after=FIXED_NOW + timedelta(hours=2),
    )
    permit = module.issue_seedance_local_video_materialization_permit(
        preview=preview,
        authorization=authorization,
        durability_validator=lambda: True,
        now=FIXED_NOW,
    )
    return preview, authorization, grant, permit


def test_exact_local_non_identity_video_materializes_and_drives_mini_payload(tmp_path):
    from ai_video.production import seedance_local_video as module
    from ai_video.production.seedance import SeedanceVideoProvider

    source_path = tmp_path / "white-model-motion.mp4"
    source_path.write_bytes(SOURCE_BYTES)
    binding = _binding()
    profile = _profile()
    request = _request(
        profile,
        model_id="doubao-seedance-2-0-mini-260615",
        mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        media_bindings=(binding,),
    )
    preview, authorization, grant, permit = _contracts(
        module,
        binding,
        target_request_fingerprint=request.request_input_hash,
    )
    materialization_transport = _MaterializationTransport()
    materialized = module.SeedanceLocalVideoMaterializer(
        transport=materialization_transport,
        now=lambda: FIXED_NOW,
    ).materialize(
        binding=binding,
        source_path=source_path,
        preview=preview,
        authorization=authorization,
        permit=permit,
        grant=grant,
    )

    assert [request.method for request, _ in materialization_transport.requests] == [
        "PUT",
        "GET",
    ]
    assert materialized.receipt.source_asset_sha256 == SOURCE_SHA256
    assert materialized.receipt.readback_sha256 == SOURCE_SHA256
    assert materialized.receipt.upload_response_identity_sha256 == hashlib.sha256(
        b'"upload-etag"'
    ).hexdigest()
    assert materialized.receipt.storage_object_version_id == "version-1"
    assert "signature=" not in materialized.receipt.model_dump_json()
    assert "signature=" not in repr(materialized)

    resolver = module.SeedanceLocalVideoReferenceResolver(
        materializations=(materialized,),
        now=lambda: FIXED_NOW + timedelta(minutes=1),
    )
    provider_transport = _FakeTransport()
    provider_transport.responses.append(_json_response({"id": "task-white-model-r2v"}))
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=provider_transport,
        credential=lambda: "offline-fixture-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW + timedelta(minutes=1),
    )
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(resolved, video_preview)
    paid_authorization = _authorization(paid_preview)

    provider.submit(
        resolved,
        video_preview,
        paid_preview,
        paid_authorization,
        _permit(resolved, video_preview, paid_preview, paid_authorization),
    )

    request_body = json.loads(provider_transport.requests[-1].body)
    assert request_body["model"] == "doubao-seedance-2-0-mini-260615"
    assert request_body["content"][1] == {
        "type": "video_url",
        "video_url": {"url": READ_URL},
        "role": "reference_video",
    }


def test_source_byte_drift_stops_before_upload_without_consuming_permit(tmp_path):
    from ai_video.production import seedance_local_video as module

    source_path = tmp_path / "white-model-motion.mp4"
    source_path.write_bytes(b"changed")
    binding = _binding()
    preview, authorization, grant, permit = _contracts(module, binding)
    transport = _MaterializationTransport()
    materializer = module.SeedanceLocalVideoMaterializer(
        transport=transport,
        now=lambda: FIXED_NOW,
    )

    with pytest.raises(AiVideoError) as exc_info:
        materializer.materialize(
            binding=binding,
            source_path=source_path,
            preview=preview,
            authorization=authorization,
            permit=permit,
            grant=grant,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert transport.requests == []
    source_path.write_bytes(SOURCE_BYTES)
    assert materializer.materialize(
        binding=binding,
        source_path=source_path,
        preview=preview,
        authorization=authorization,
        permit=permit,
        grant=grant,
    ).receipt.source_asset_sha256 == SOURCE_SHA256


def test_materializer_holds_exact_source_bytes_across_permit_and_upload(tmp_path):
    from ai_video.production import seedance_local_video as module

    source_path = tmp_path / "white-model-motion.mp4"
    source_path.write_bytes(SOURCE_BYTES)
    binding = _binding()
    preview, authorization, grant, permit = _contracts(module, binding)
    transport = _PathSwapTransport(source_path)

    module.SeedanceLocalVideoMaterializer(
        transport=transport,
        now=lambda: FIXED_NOW,
    ).materialize(
        binding=binding,
        source_path=source_path,
        preview=preview,
        authorization=authorization,
        permit=permit,
        grant=grant,
    )

    assert transport.requests[0][1] == SOURCE_BYTES


def test_readback_mismatch_consumes_one_use_permit_and_blocks_retry(tmp_path):
    from ai_video.production import seedance_local_video as module

    source_path = tmp_path / "white-model-motion.mp4"
    source_path.write_bytes(SOURCE_BYTES)
    binding = _binding()
    preview, authorization, grant, permit = _contracts(module, binding)
    transport = _MaterializationTransport(readback=SOURCE_BYTES + b"tampered")
    materializer = module.SeedanceLocalVideoMaterializer(
        transport=transport,
        now=lambda: FIXED_NOW,
    )

    with pytest.raises(AiVideoError) as exc_info:
        materializer.materialize(
            binding=binding,
            source_path=source_path,
            preview=preview,
            authorization=authorization,
            permit=permit,
            grant=grant,
        )

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.requests) == 2

    with pytest.raises(AiVideoError) as retry_exc:
        materializer.materialize(
            binding=binding,
            source_path=source_path,
            preview=preview,
            authorization=authorization,
            permit=permit,
            grant=grant,
        )

    assert retry_exc.value.code is ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert len(transport.requests) == 2


def test_materialization_for_another_request_is_rejected_before_provider_effect(tmp_path):
    from ai_video.production import seedance_local_video as module
    from ai_video.production.seedance import SeedanceVideoProvider

    source_path = tmp_path / "white-model-motion.mp4"
    source_path.write_bytes(SOURCE_BYTES)
    binding = _binding()
    preview, authorization, grant, permit = _contracts(module, binding)
    materialized = module.SeedanceLocalVideoMaterializer(
        transport=_MaterializationTransport(),
        now=lambda: FIXED_NOW,
    ).materialize(
        binding=binding,
        source_path=source_path,
        preview=preview,
        authorization=authorization,
        permit=permit,
        grant=grant,
    )
    resolver = module.SeedanceLocalVideoReferenceResolver(
        materializations=(materialized,),
        now=lambda: FIXED_NOW + timedelta(minutes=1),
    )
    profile = _profile()
    provider_transport = _FakeTransport()
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=provider_transport,
        credential=lambda: "offline-fixture-secret",
        input_reference=resolver,
        now=lambda: FIXED_NOW + timedelta(minutes=1),
    )

    with pytest.raises(AiVideoError) as exc_info:
        provider.resolve(
            _request(
                profile,
                model_id="doubao-seedance-2-0-mini-260615",
                mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                media_bindings=(binding,),
            )
        )

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert provider_transport.requests == []
