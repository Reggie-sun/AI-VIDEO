from __future__ import annotations

import hashlib
import fcntl
import json
import os
import shutil
import socket
import subprocess
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

import ai_video.production.audio as production_audio
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioImportRequest,
    AudioProbeToolchain,
    ClaimedAudioMetadata,
    VoiceAssetProvider,
    VoiceCallAuthorization,
    VoiceCostReceipt,
    VoiceGenerationRequest,
    VoiceGenerationPreview,
    VoicePricingSnapshot,
    VoiceProviderResult,
    VoiceProviderParameters,
    VoiceProvenanceReceipt,
    audio_content_fingerprint,
    build_voice_generation_preview,
    materialize_audio_candidate,
    probe_audio_candidate,
    validate_voice_call_authorization,
)
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    AudioKind,
    AudioSource,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ToolIdentity,
)
from ai_video.production.paths import canonical_voice_audio_candidate_path


FIXTURE_ROOT = Path(__file__).parent / "fixtures/voice_captions"
DIALOGUE = FIXTURE_ROOT / "dialogue-mono-48000.wav"
AMBIENCE = FIXTURE_ROOT / "ambience-stereo-48000.wav"
ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def _voice_request(**overrides) -> VoiceGenerationRequest:
    values = {
        "request_id": "request-1",
        "attempt_id": "attempt-1",
        "provider_kind": "fake",
        "model_id": "model-1",
        "audio_kind": AudioKind.DIALOGUE,
        "script_text": "Exact script",
        "speaker_id": "speaker-1",
        "voice_id": "voice-1",
        "language": "en",
        "output_container": "wav",
        "output_codec": "pcm_s16le",
        "output_sample_rate_hz": 48_000,
        "output_channels": 1,
        "provider_parameters": VoiceProviderParameters(stability_milli=500),
        "base_project": ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{ZERO_HASH}.yaml"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        "base_registry": RegistrySnapshotPointer(
            path=Path(f"assets/registry.{ONE_HASH}.json"),
            revision_id=ONE_HASH,
            content_hash=ONE_HASH,
            file_sha256=ZERO_HASH,
        ),
        "input_artifact_ids": ("shot-1",),
        "input_fingerprint": ONE_HASH,
        "pricing_snapshot_id": "pricing-2026-08-10",
        "budget_reservation_receipt_id": "budget-1",
        "egress_authorization_receipt_id": "egress-1",
    }
    values.update(overrides)
    return VoiceGenerationRequest.create(**values)


def _pricing(**overrides) -> VoicePricingSnapshot:
    values = {
        "snapshot_id": "pricing-2026-08-10",
        "effective_date": date(2026, 8, 10),
        "currency": "USD",
        "pricing_unit": "character",
        "unit_price_microunits": 37,
        "minimum_billable_units": 20,
    }
    values.update(overrides)
    return VoicePricingSnapshot(**values)


def _preview(request: VoiceGenerationRequest) -> VoiceGenerationPreview:
    return build_voice_generation_preview(
        request,
        pricing=_pricing(),
        destination="https://api.fixture.invalid",
        credential_reference_kind="environment",
        timing_supported=True,
        output_supported=True,
    )


def _authorization(
    request: VoiceGenerationRequest,
    preview: VoiceGenerationPreview,
    **overrides,
) -> VoiceCallAuthorization:
    values = {
        "request_fingerprint": request.voice_request_fingerprint,
        "preview_fingerprint": preview.preview_fingerprint,
        "pricing_snapshot_id": request.pricing_snapshot_id,
        "budget_reservation_receipt_id": request.budget_reservation_receipt_id,
        "egress_authorization_receipt_id": request.egress_authorization_receipt_id,
        "destination": preview.destination,
        "payload_categories": preview.payload_categories,
        "cost_ceiling_microunits": preview.estimated_cost_upper_bound_microunits,
        "provider_enabled": True,
    }
    values.update(overrides)
    return VoiceCallAuthorization.create(**values)


class _FakeVoiceProvider:
    def __init__(self, fixture_bytes: bytes) -> None:
        self.fixture_bytes = fixture_bytes
        self.generate_calls = 0

    def preview(self, request: VoiceGenerationRequest) -> VoiceGenerationPreview:
        return _preview(request)

    def generate(self, request, authorization, permit) -> VoiceProviderResult:
        preview = self.preview(request)
        validate_voice_call_authorization(
            request, preview, authorization, pricing=_pricing()
        )
        if permit is not _FAKE_DURABLE_PERMIT:
            raise AssertionError("fake provider requires the test-only permit sentinel")
        self.generate_calls += 1
        alignment_bytes = json.dumps(
            {
                "characters": list(request.script_text),
                "character_start_times_seconds": [0] * len(request.script_text),
                "character_end_times_seconds": [1] * len(request.script_text),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        cost = VoiceCostReceipt(
            currency=preview.currency,
            pricing_unit=preview.pricing_unit,
            measured_billable_units=preview.billable_units_upper_bound,
            estimated_cost_upper_bound_microunits=(
                preview.estimated_cost_upper_bound_microunits
            ),
            provider_reported_cost_microunits=None,
            pricing_snapshot_id=preview.pricing_snapshot_id,
            request_id=request.request_id,
            provider_request_id="provider-request-1",
        )
        provenance = VoiceProvenanceReceipt(
            request_id=request.request_id,
            provider_kind=request.provider_kind,
            model_id=request.model_id,
            voice_id=request.voice_id,
            language=request.language,
            request_fingerprint=request.voice_request_fingerprint,
            script_hash=request.script_hash,
            output_container=request.output_container,
            output_codec=request.output_codec,
            output_sample_rate_hz=request.output_sample_rate_hz,
            output_channels=request.output_channels,
            alignment_mode="character",
            adapter=ToolIdentity(name="fixture-provider", version="1"),
            egress_authorization_receipt_id=(
                request.egress_authorization_receipt_id
            ),
            license_policy_decision="fixture-only",
            policy_receipt_id="fixture-policy-receipt",
            retention_mode="provider_standard",
            provider_request_id="provider-request-1",
            provider_trace_id="provider-trace-1",
        )
        return VoiceProviderResult.create(
            request=request,
            preview=preview,
            authorization=authorization,
            pricing=_pricing(),
            audio_bytes=self.fixture_bytes,
            content_type="audio/wav",
            provider_request_id="provider-request-1",
            provider_trace_id="provider-trace-1",
            alignment_receipt_bytes=alignment_bytes,
            cost_receipt=cost,
            provenance_receipt=provenance,
            terminal_status="succeeded",
        )


_FAKE_DURABLE_PERMIT = object()


def _toolchain() -> AudioProbeToolchain:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for deterministic audio probes")
    return AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(strict=True),
        ffprobe_path=Path(ffprobe).resolve(strict=True),
        ffmpeg=ToolIdentity(name="ffmpeg", version="test-pinned"),
        ffprobe=ToolIdentity(name="ffprobe", version="test-pinned"),
    )


def _source(kind: AssetSourceKind = AssetSourceKind.IMPORTED) -> AudioSource:
    return AudioSource(
        kind=kind,
        provider_or_tool=ToolIdentity(name="fixture-import", version="1"),
        input_artifact_ids=("source-1",),
        input_fingerprint=ONE_HASH,
        original_reference="fixture://audio",
    )


def _import_request(kind: AudioKind) -> AudioImportRequest:
    speech = kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
    return AudioImportRequest(
        asset_id=f"audio-{kind.value}-1",
        audio_kind=kind,
        mime_type="audio/wav",
        source=_source(),
        speaker_id="speaker-1" if speech else None,
        language="en" if speech else None,
        script_hash=hashlib.sha256(b"fixture script").hexdigest() if speech else None,
        provenance_receipt_id="receipt-audio-provenance-1",
        creation_receipt_id="receipt-audio-create-1",
        usage_license="fixture-generated",
    )


def test_fixture_identities_are_frozen():
    assert hashlib.sha256(DIALOGUE.read_bytes()).hexdigest() == (
        "f72a3208e25253873858b9f9161e0851e336eb5e97d717a01679df729c428a63"
    )
    assert hashlib.sha256(AMBIENCE.read_bytes()).hexdigest() == (
        "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca"
    )


def test_voice_generation_request_is_immutable_and_self_sealing():
    request = _voice_request()
    assert request.script_hash == hashlib.sha256(b"Exact script").hexdigest()
    assert len(request.provider_parameters_hash) == 64
    assert len(request.voice_request_fingerprint) == 64
    with pytest.raises(ValidationError):
        request.model_copy(update={"audio_kind": AudioKind.BGM}, deep=True).model_validate(
            {**request.model_dump(), "audio_kind": "bgm"}
        )
    with pytest.raises(ValidationError, match="script_hash"):
        VoiceGenerationRequest.model_validate(
            {**request.model_dump(mode="python"), "script_hash": ZERO_HASH}
        )


@pytest.mark.parametrize("audio_kind", [AudioKind.AMBIENCE, AudioKind.SFX, AudioKind.BGM])
def test_voice_generation_request_accepts_only_dialogue_and_narration(audio_kind):
    with pytest.raises(ValidationError, match="dialogue or narration"):
        _voice_request(audio_kind=audio_kind)
    assert _voice_request(audio_kind=AudioKind.NARRATION).audio_kind is AudioKind.NARRATION


def test_preview_is_pure_no_network_and_uses_dated_conservative_pricing(monkeypatch):
    network_calls = []

    def reject_network(*args, **kwargs):
        network_calls.append((args, kwargs))
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket.socket, "connect", reject_network)
    request = _voice_request(script_text="é voice")
    provider: VoiceAssetProvider = _FakeVoiceProvider(DIALOGUE.read_bytes())

    preview = provider.preview(request)

    assert network_calls == []
    assert provider.generate_calls == 0
    assert preview.pricing_effective_date == date(2026, 8, 10)
    assert preview.pricing_snapshot_id == request.pricing_snapshot_id
    assert preview.script_characters == len(request.script_text)
    assert preview.script_utf8_bytes == len(request.script_text.encode("utf-8"))
    assert preview.billable_units_upper_bound == 20
    assert preview.estimated_cost_upper_bound_microunits == 20 * 37
    assert preview.estimated_cost_upper_bound_microunits >= (
        preview.script_characters * 37
    )
    assert preview.payload_categories == (
        "script_text",
        "voice_identity",
        "voice_settings",
        "output_settings",
    )
    assert preview.destination == "https://api.fixture.invalid"
    assert preview.method == "POST"
    assert preview.remote is True
    assert preview.paid_call_required is True
    assert preview.unit_price_microunits == 37
    assert preview.minimum_billable_units == 20


@pytest.mark.parametrize(
    "payload_categories",
    [
        ("script_text",),
        (
            "script_text",
            "voice_identity",
            "voice_settings",
            "output_settings",
            "script_text",
        ),
        (
            "voice_identity",
            "script_text",
            "voice_settings",
            "output_settings",
        ),
    ],
)
def test_preview_requires_exact_ordered_egress_payload_categories(payload_categories):
    request = _voice_request()
    preview = _preview(request)
    data = preview.model_dump(mode="json")
    data["payload_categories"] = payload_categories
    data["preview_fingerprint"] = production_audio.canonical_sha256(
        {key: value for key, value in data.items() if key != "preview_fingerprint"}
    )

    with pytest.raises(ValidationError, match="payload categories"):
        VoiceGenerationPreview.model_validate(data)

    authorization = _authorization(request, preview)
    authorization_data = authorization.model_dump(mode="json")
    authorization_data["payload_categories"] = payload_categories
    authorization_data["authorization_fingerprint"] = (
        production_audio.canonical_sha256(
            {
                key: value
                for key, value in authorization_data.items()
                if key != "authorization_fingerprint"
            }
        )
    )
    with pytest.raises(ValidationError, match="payload categories"):
        VoiceCallAuthorization.model_validate(authorization_data)


def test_preview_locks_nfc_unicode_codepoint_and_utf8_byte_counting():
    request = _voice_request(script_text="é🙂")
    pricing = _pricing(minimum_billable_units=0)
    preview = build_voice_generation_preview(
        request,
        pricing=pricing,
        destination="https://api.fixture.invalid",
        credential_reference_kind="environment",
        timing_supported=True,
        output_supported=True,
    )

    assert preview.script_characters == 2
    assert preview.script_utf8_bytes == 6
    assert preview.billable_units_upper_bound == 2
    assert preview.estimated_cost_upper_bound_microunits == 74


def test_authorization_recomputes_preview_and_rejects_forged_underestimate():
    request = _voice_request(script_text="twenty one characters!")
    preview = _preview(request)
    forged = preview.model_copy(
        update={
            "script_utf8_bytes": 1,
            "script_characters": 1,
            "billable_units_upper_bound": 1,
            "estimated_cost_upper_bound_microunits": 1,
        }
    )
    forged_data = forged.model_dump(mode="json", exclude={"preview_fingerprint"})
    forged = forged.model_copy(
        update={
            "preview_fingerprint": production_audio.canonical_sha256(forged_data)
        }
    )
    authorization = _authorization(request, forged, cost_ceiling_microunits=1)

    with pytest.raises(AiVideoError) as caught:
        validate_voice_call_authorization(
            request, forged, authorization, pricing=_pricing()
        )

    assert caught.value.code is ErrorCode.VOICE_REQUEST_INVALID


@pytest.mark.parametrize(
    ("override", "error_code"),
    [
        ({"request_fingerprint": ZERO_HASH}, ErrorCode.VOICE_REQUEST_INVALID),
        ({"preview_fingerprint": ZERO_HASH}, ErrorCode.VOICE_REQUEST_INVALID),
        ({"pricing_snapshot_id": "stale"}, ErrorCode.VOICE_BUDGET_REJECTED),
        ({"budget_reservation_receipt_id": "wrong"}, ErrorCode.VOICE_BUDGET_REJECTED),
        ({"egress_authorization_receipt_id": "wrong"}, ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED),
        ({"destination": "https://other.invalid"}, ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED),
        ({"cost_ceiling_microunits": 1}, ErrorCode.VOICE_BUDGET_REJECTED),
    ],
)
def test_authorization_mismatch_fails_before_provider_call(override, error_code):
    request = _voice_request()
    provider = _FakeVoiceProvider(DIALOGUE.read_bytes())
    preview = provider.preview(request)
    authorization = _authorization(request, preview, **override)

    with pytest.raises(AiVideoError) as caught:
        provider.generate(request, authorization, _FAKE_DURABLE_PERMIT)

    assert caught.value.code is error_code
    assert provider.generate_calls == 0


def test_authorization_and_result_reject_secrets_and_raw_headers():
    request = _voice_request()
    preview = _preview(request)
    authorization_data = _authorization(request, preview).model_dump(mode="python")
    with pytest.raises(ValidationError) as authorization_error:
        VoiceCallAuthorization.model_validate(
            {**authorization_data, "api_key": "super-secret"}
        )
    assert "super-secret" not in str(authorization_error.value)
    assert "super-secret" not in repr(authorization_error.value)
    with pytest.raises(ValidationError) as parameters_error:
        VoiceProviderParameters.model_validate({"api_key": "super-secret"})
    assert "super-secret" not in str(parameters_error.value)
    assert "super-secret" not in repr(parameters_error.value)
    assert "secret" not in repr(authorization_data).lower()

    mismatched = _authorization(
        request, preview, egress_authorization_receipt_id="super-secret"
    )
    with pytest.raises(AiVideoError) as public_error:
        validate_voice_call_authorization(
            request, preview, mismatched, pricing=_pricing()
        )
    assert "super-secret" not in str(public_error.value)
    assert "super-secret" not in repr(public_error.value)

    provider = _FakeVoiceProvider(DIALOGUE.read_bytes())
    result = provider.generate(
        request, _authorization(request, preview), _FAKE_DURABLE_PERMIT
    )
    with pytest.raises(ValidationError) as result_error:
        VoiceProviderResult.model_validate(
            {**result.model_dump(mode="python"), "response_headers": {"x": "secret"}}
        )
    assert "secret" not in str(result_error.value)
    assert "secret" not in repr(result_error.value)
    assert "super-secret" not in repr(result.model_dump(mode="python"))


def test_fake_provider_returns_deterministic_sealed_receipts_without_state_write(
    tmp_path,
):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("unchanged", encoding="utf-8")
    request = _voice_request()
    provider = _FakeVoiceProvider(DIALOGUE.read_bytes())
    preview = provider.preview(request)
    assert provider.generate_calls == 0

    first = provider.generate(
        request, _authorization(request, preview), _FAKE_DURABLE_PERMIT
    )
    second_provider = _FakeVoiceProvider(DIALOGUE.read_bytes())
    second = second_provider.generate(
        request, _authorization(request, preview), _FAKE_DURABLE_PERMIT
    )

    assert provider.generate_calls == 1
    assert second_provider.generate_calls == 1
    assert first == second
    assert first.audio_bytes == DIALOGUE.read_bytes()
    assert first.audio_sha256 == hashlib.sha256(DIALOGUE.read_bytes()).hexdigest()
    assert hashlib.sha256(first.alignment_receipt_bytes).hexdigest() == (
        first.alignment_receipt_sha256
    )
    assert first.cost_receipt.provider_reported_cost_microunits is None
    assert first.provenance_receipt.request_fingerprint == (
        request.voice_request_fingerprint
    )
    assert first.provider_request_id == "provider-request-1"
    assert manifest.read_text(encoding="utf-8") == "unchanged"
    assert list(tmp_path.iterdir()) == [manifest]


@pytest.mark.parametrize(
    ("receipt_kind", "field", "wrong_value"),
    [
        ("cost", "currency", "EUR"),
        ("cost", "pricing_unit", "word"),
        ("cost", "pricing_snapshot_id", "pricing-wrong"),
        ("cost", "request_id", "request-wrong"),
        ("cost", "provider_request_id", "provider-request-wrong"),
        ("cost", "measured_billable_units", 1_000_000),
        ("cost", "estimated_cost_upper_bound_microunits", 1),
        ("cost", "provider_reported_cost_microunits", 10_000),
        ("provenance", "request_id", "request-wrong"),
        ("provenance", "provider_kind", "provider-wrong"),
        ("provenance", "model_id", "model-wrong"),
        ("provenance", "voice_id", "voice-wrong"),
        ("provenance", "language", "fr"),
        ("provenance", "script_hash", ZERO_HASH),
        ("provenance", "output_container", "mp3"),
        ("provenance", "output_codec", "mp3"),
        ("provenance", "output_sample_rate_hz", 44_100),
        ("provenance", "output_channels", 2),
        ("provenance", "egress_authorization_receipt_id", "egress-wrong"),
        ("provenance", "provider_request_id", "provider-request-wrong"),
        ("provenance", "provider_trace_id", "provider-trace-wrong"),
    ],
)
def test_provider_result_rejects_request_contradicting_receipts_before_fingerprint(
    monkeypatch, receipt_kind, field, wrong_value
):
    request = _voice_request()
    provider = _FakeVoiceProvider(DIALOGUE.read_bytes())
    preview = provider.preview(request)
    authorization = _authorization(request, preview)
    valid = provider.generate(request, authorization, _FAKE_DURABLE_PERMIT)
    cost = valid.cost_receipt
    provenance = valid.provenance_receipt
    if receipt_kind == "cost":
        cost = cost.model_copy(update={field: wrong_value})
    else:
        provenance = provenance.model_copy(update={field: wrong_value})

    fingerprint_calls = []

    def reject_fingerprint(*args, **kwargs):
        fingerprint_calls.append((args, kwargs))
        raise AssertionError("contradicting receipts reached result fingerprinting")

    monkeypatch.setattr(production_audio, "_result_fingerprint", reject_fingerprint)
    with pytest.raises(AiVideoError) as caught:
        VoiceProviderResult.create(
            request=request,
            preview=preview,
            authorization=authorization,
            pricing=_pricing(),
            audio_bytes=valid.audio_bytes,
            content_type=valid.content_type,
            provider_request_id=valid.provider_request_id,
            provider_trace_id=valid.provider_trace_id,
            alignment_receipt_bytes=valid.alignment_receipt_bytes,
            cost_receipt=cost,
            provenance_receipt=provenance,
            terminal_status="succeeded",
        )

    assert caught.value.code is ErrorCode.VOICE_PROVIDER_FAILED
    assert fingerprint_calls == []


def test_provider_result_rejects_mismatched_authorization_before_fingerprint(
    monkeypatch,
):
    request = _voice_request()
    provider = _FakeVoiceProvider(DIALOGUE.read_bytes())
    preview = provider.preview(request)
    authorization = _authorization(request, preview)
    valid = provider.generate(request, authorization, _FAKE_DURABLE_PERMIT)
    fingerprint_calls = []

    def reject_fingerprint(*args, **kwargs):
        fingerprint_calls.append((args, kwargs))
        raise AssertionError("mismatched authorization reached result fingerprinting")

    monkeypatch.setattr(production_audio, "_result_fingerprint", reject_fingerprint)
    authorization_data = authorization.model_dump(
        mode="python", exclude={"authorization_fingerprint"}
    )
    authorization_data["egress_authorization_receipt_id"] = "egress-wrong"
    wrong_authorization = VoiceCallAuthorization.create(**authorization_data)
    with pytest.raises(AiVideoError) as caught:
        VoiceProviderResult.create(
            request=request,
            preview=preview,
            authorization=wrong_authorization,
            pricing=_pricing(),
            audio_bytes=valid.audio_bytes,
            content_type=valid.content_type,
            provider_request_id=valid.provider_request_id,
            provider_trace_id=valid.provider_trace_id,
            alignment_receipt_bytes=valid.alignment_receipt_bytes,
            cost_receipt=valid.cost_receipt,
            provenance_receipt=valid.provenance_receipt,
            terminal_status="succeeded",
        )

    assert caught.value.code is ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED
    assert fingerprint_calls == []


def test_provider_result_binds_preview_and_authorization_fingerprints():
    request = _voice_request()
    preview = _preview(request)
    authorization = _authorization(request, preview)
    result = _FakeVoiceProvider(DIALOGUE.read_bytes()).generate(
        request, authorization, _FAKE_DURABLE_PERMIT
    )

    assert result.preview_fingerprint == preview.preview_fingerprint
    assert result.authorization_fingerprint == authorization.authorization_fingerprint


def test_candidate_path_is_exact_contained_and_rejects_symlink(tmp_path):
    attempt_root = tmp_path / "state/voice/attempts/attempt-1"
    attempt_root.mkdir(parents=True)
    candidate = canonical_voice_audio_candidate_path(tmp_path, "attempt-1")
    assert candidate == attempt_root / "candidate.wav"
    materialize_audio_candidate(
        DIALOGUE.read_bytes(),
        candidate_path=candidate,
        project_root=tmp_path,
        attempt_id="attempt-1",
    )
    assert candidate.read_bytes() == DIALOGUE.read_bytes()

    with pytest.raises(AiVideoError, match="exact attempt-owned"):
        materialize_audio_candidate(
            b"bad",
            candidate_path=attempt_root / "other.wav",
            project_root=tmp_path,
            attempt_id="attempt-1",
        )

    escaped = tmp_path / "escaped"
    escaped.mkdir()
    symlink_root = tmp_path / "state/voice/attempts/attempt-2"
    symlink_root.symlink_to(escaped, target_is_directory=True)
    with pytest.raises(AiVideoError):
        materialize_audio_candidate(
            b"bad",
            candidate_path=symlink_root / "candidate.wav",
            project_root=tmp_path,
            attempt_id="attempt-2",
        )
    assert not (escaped / "candidate.wav").exists()

    attempt_three = tmp_path / "state/voice/attempts/attempt-3"
    attempt_three.mkdir(parents=True)
    protected = escaped / "protected.wav"
    protected.write_bytes(b"protected")
    (attempt_three / "candidate.wav").symlink_to(protected)
    with pytest.raises(AiVideoError):
        materialize_audio_candidate(
            DIALOGUE.read_bytes(),
            candidate_path=attempt_three / "candidate.wav",
            project_root=tmp_path,
            attempt_id="attempt-3",
        )
    assert protected.read_bytes() == b"protected"


@pytest.mark.parametrize("symlink_component", ["state", "voice", "attempts"])
def test_candidate_rejects_symlink_in_parent_chain(tmp_path, symlink_component):
    project_root = tmp_path / "project"
    project_root.mkdir()
    components = ("state", "voice", "attempts")
    link_index = components.index(symlink_component)
    link_parent = project_root.joinpath(*components[:link_index])
    link_parent.mkdir(parents=True, exist_ok=True)
    outside_root = tmp_path / f"outside-{symlink_component}"
    outside_attempt = outside_root.joinpath(
        *components[link_index + 1 :], "attempt-parent-link"
    )
    outside_attempt.mkdir(parents=True)
    (link_parent / symlink_component).symlink_to(
        outside_root, target_is_directory=True
    )
    candidate = canonical_voice_audio_candidate_path(
        project_root, "attempt-parent-link"
    )

    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            DIALOGUE.read_bytes(),
            candidate_path=candidate,
            project_root=project_root,
            attempt_id="attempt-parent-link",
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert not (outside_attempt / "candidate.wav").exists()


def test_materialization_is_idempotent_for_same_bytes_and_conflicts_otherwise(tmp_path):
    attempt_root = tmp_path / "state/voice/attempts/attempt-replay"
    attempt_root.mkdir(parents=True)
    candidate = canonical_voice_audio_candidate_path(tmp_path, "attempt-replay")
    first = materialize_audio_candidate(
        AMBIENCE.read_bytes(),
        candidate_path=candidate,
        project_root=tmp_path,
        attempt_id="attempt-replay",
    )
    second = materialize_audio_candidate(
        AMBIENCE.read_bytes(),
        candidate_path=candidate,
        project_root=tmp_path,
        attempt_id="attempt-replay",
    )
    assert first == second
    assert not list(attempt_root.glob("*.tmp-*"))
    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            DIALOGUE.read_bytes(),
            candidate_path=candidate,
            project_root=tmp_path,
            attempt_id="attempt-replay",
        )
    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert candidate.read_bytes() == AMBIENCE.read_bytes()


def test_same_byte_target_hardlink_is_rejected_before_replay(tmp_path):
    project_root = tmp_path / "project"
    attempt_root = project_root / "state/voice/attempts/attempt-hardlink-target"
    attempt_root.mkdir(parents=True)
    candidate = canonical_voice_audio_candidate_path(
        project_root, "attempt-hardlink-target"
    )
    candidate.write_bytes(AMBIENCE.read_bytes())
    external_alias = tmp_path / "external-target-alias.wav"
    os.link(candidate, external_alias)
    assert candidate.stat().st_nlink == 2

    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            AMBIENCE.read_bytes(),
            candidate_path=candidate,
            project_root=project_root,
            attempt_id="attempt-hardlink-target",
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert candidate.stat().st_nlink == 2
    candidate.unlink()
    accepted = materialize_audio_candidate(
        AMBIENCE.read_bytes(),
        candidate_path=candidate,
        project_root=project_root,
        attempt_id="attempt-hardlink-target",
    )
    external_alias.write_bytes(DIALOGUE.read_bytes())
    assert accepted.link_count == 1
    assert candidate.read_bytes() == AMBIENCE.read_bytes()


def test_preexisting_candidate_temp_hardlink_is_rejected(tmp_path):
    project_root = tmp_path / "project"
    attempt_root = project_root / "state/voice/attempts/attempt-hardlink-temp"
    attempt_root.mkdir(parents=True)
    payload = AMBIENCE.read_bytes()
    candidate = canonical_voice_audio_candidate_path(
        project_root, "attempt-hardlink-temp"
    )
    digest = hashlib.sha256(payload).hexdigest()
    temporary = attempt_root / f".candidate.wav.tmp-{digest}"
    temporary.write_bytes(payload)
    external_alias = tmp_path / "external-temp-alias.wav"
    os.link(temporary, external_alias)

    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            payload,
            candidate_path=candidate,
            project_root=project_root,
            attempt_id="attempt-hardlink-temp",
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert not candidate.exists()
    assert temporary.stat().st_nlink == 2
    assert external_alias.read_bytes() == payload


def test_probe_freezes_samples_channels_pcm_hash_and_loudness():
    with AMBIENCE.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(), mime_type="audio/wav", toolchain=_toolchain()
        )
    assert probe.file_sha256 == "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca"
    assert probe.duration_samples == 48_000
    assert probe.sample_rate_hz == 48_000
    assert probe.channels == 2
    assert probe.channel_layout.value == "stereo"
    assert probe.codec_name == "pcm_s16le"
    assert probe.decoded_pcm_sha256 == (
        "5465d350919ea264287d66d036bf9ee4ddc6b43959a32f2e6d06075fbccafc51"
    )
    assert probe.loudness.measurement_standard == "ebu_r128"
    assert probe.loudness_receipt_id
    assert audio_content_fingerprint(probe) == probe.content_fingerprint

    with DIALOGUE.open("rb") as source:
        dialogue = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
    assert (dialogue.duration_samples, dialogue.sample_rate_hz, dialogue.channels) == (
        96_000,
        48_000,
        1,
    )


def test_probe_rejects_wrong_mime_truncation_and_claimed_metadata(tmp_path):
    with DIALOGUE.open("rb") as source:
        with pytest.raises(AiVideoError) as caught:
            probe_audio_candidate(
                source.fileno(), mime_type="audio/mpeg", toolchain=_toolchain()
            )
    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID

    truncated = tmp_path / "truncated.wav"
    truncated.write_bytes(DIALOGUE.read_bytes()[:32])
    with truncated.open("rb") as source:
        with pytest.raises(AiVideoError) as caught:
            probe_audio_candidate(
                source.fileno(), mime_type="audio/wav", toolchain=_toolchain()
            )
    assert caught.value.code is ErrorCode.AUDIO_PROBE_FAILED

    def wrong_container_runner(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(
                {
                    "streams": [
                        {
                            "codec_type": "audio",
                            "codec_name": "pcm_s16le",
                            "sample_rate": "48000",
                            "channels": 1,
                        }
                    ],
                    "format": {"format_name": "aiff"},
                }
            ),
            stderr="",
        )

    with DIALOGUE.open("rb") as source:
        with pytest.raises(AiVideoError, match="container"):
            probe_audio_candidate(
                source.fileno(),
                mime_type="audio/wav",
                toolchain=_toolchain(),
                runner=wrong_container_runner,
            )

    with DIALOGUE.open("rb") as source:
        with pytest.raises(AiVideoError, match="provider metadata"):
            probe_audio_candidate(
                source.fileno(),
                mime_type="audio/wav",
                toolchain=_toolchain(),
                claimed_metadata=ClaimedAudioMetadata(
                    codec_name="pcm_s16le",
                    duration_samples=96_000,
                    sample_rate_hz=44_100,
                    channels=1,
                ),
            )


def test_probe_unknown_loudness_policy_is_explicit():
    with DIALOGUE.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
    assert probe.loudness.integrated_lufs_milli is None
    assert probe.loudness.true_peak_dbfs_milli is None
    assert probe.loudness.measurement_standard is None


def test_probe_binds_tool_reads_to_held_fd_during_path_replacement(tmp_path):
    source_path = tmp_path / "source.wav"
    source_path.write_bytes(DIALOGUE.read_bytes())
    original_stat = source_path.stat()
    calls = 0

    def replacing_runner(*args, **kwargs):
        nonlocal calls
        result = subprocess.run(*args, **kwargs)
        calls += 1
        if calls == 1:
            replacement = tmp_path / "replacement.wav"
            replacement.write_bytes(AMBIENCE.read_bytes())
            replacement.replace(source_path)
        return result

    with source_path.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            runner=replacing_runner,
        )
    assert probe.file_device == original_stat.st_dev
    assert probe.file_inode == original_stat.st_ino
    assert probe.file_sha256 == hashlib.sha256(DIALOGUE.read_bytes()).hexdigest()
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() != probe.file_sha256


def test_probe_uses_private_snapshot_against_mutation_restore(tmp_path):
    source_path = tmp_path / "source.wav"
    dialogue_bytes = DIALOGUE.read_bytes()
    ambience_bytes = AMBIENCE.read_bytes()
    assert len(dialogue_bytes) == len(ambience_bytes)
    source_path.write_bytes(dialogue_bytes)
    original_stat = source_path.stat()
    calls = 0
    tool_snapshot_stats: list[os.stat_result] = []
    tool_snapshot_access_modes: list[int] = []

    def mutation_restore_runner(argv, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            source_path.write_bytes(ambience_bytes)
        held_path = next(item for item in argv if item.startswith("/proc/self/fd/"))
        snapshot_fd = int(Path(held_path).name)
        tool_snapshot_stats.append(os.fstat(snapshot_fd))
        tool_snapshot_access_modes.append(fcntl.fcntl(snapshot_fd, fcntl.F_GETFL))
        result = subprocess.run(argv, **kwargs)
        if calls == 3:
            source_path.write_bytes(dialogue_bytes)
        return result

    with source_path.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            runner=mutation_restore_runner,
        )

    assert calls == 3
    assert probe.file_sha256 == hashlib.sha256(dialogue_bytes).hexdigest()
    assert probe.decoded_pcm_sha256 == (
        "eeaaf0bf8c11cf327ac65f7e8f7279757cefd11513a3137e35ee769426e1a329"
    )
    assert (probe.duration_samples, probe.channels) == (96_000, 1)
    assert all(item.st_ino != original_stat.st_ino for item in tool_snapshot_stats)
    assert all(item.st_nlink == 0 for item in tool_snapshot_stats)
    assert all((mode & os.O_ACCMODE) == os.O_RDONLY for mode in tool_snapshot_access_modes)
    assert source_path.read_bytes() == dialogue_bytes


def test_content_fingerprint_is_independent_of_machine_inode(tmp_path):
    copy = tmp_path / "ambience-copy.wav"
    copy.write_bytes(AMBIENCE.read_bytes())
    with AMBIENCE.open("rb") as left, copy.open("rb") as right:
        left_probe = probe_audio_candidate(
            left.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
        right_probe = probe_audio_candidate(
            right.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
    assert (left_probe.file_device, left_probe.file_inode) != (
        right_probe.file_device,
        right_probe.file_inode,
    )
    assert left_probe.content_fingerprint == right_probe.content_fingerprint


@pytest.mark.parametrize(
    ("ffmpeg_name", "ffprobe_name"),
    [("ffprobe", "ffmpeg"), ("forged", "ffprobe"), ("ffmpeg", "forged")],
)
def test_audio_toolchain_rejects_swapped_or_forged_identity_names(
    ffmpeg_name, ffprobe_name
):
    toolchain = _toolchain()
    with pytest.raises(ValidationError, match="identity name"):
        AudioProbeToolchain(
            ffmpeg_path=toolchain.ffmpeg_path,
            ffprobe_path=toolchain.ffprobe_path,
            ffmpeg=ToolIdentity(name=ffmpeg_name, version="test-pinned"),
            ffprobe=ToolIdentity(name=ffprobe_name, version="test-pinned"),
        )


@pytest.mark.parametrize(
    ("kind", "expected_type", "fixture"),
    [
        (AudioKind.DIALOGUE, AssetType.VOICE, DIALOGUE),
        (AudioKind.BGM, AssetType.MUSIC, AMBIENCE),
        (AudioKind.SFX, AssetType.SFX, AMBIENCE),
    ],
)
def test_provider_free_import_prepares_typed_bytes_without_active_write(
    tmp_path, kind, expected_type, fixture
):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("unchanged", encoding="utf-8")
    with fixture.open("rb") as source:
        prepared = _import_request(kind).prepare(source.fileno(), toolchain=_toolchain())
    assert prepared.payload == fixture.read_bytes()
    assert prepared.asset_record.asset_type is expected_type
    assert prepared.asset_record.audio_metadata is not None
    assert prepared.asset_record.sha256 == hashlib.sha256(prepared.payload).hexdigest()
    assert prepared.asset_record.artifact_path == Path(
        f"assets/audio/{prepared.asset_record.sha256}.wav"
    )
    assert manifest.read_text(encoding="utf-8") == "unchanged"
    assert list(tmp_path.iterdir()) == [manifest]
