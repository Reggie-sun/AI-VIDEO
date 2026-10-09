from __future__ import annotations

import base64
import hashlib
import json
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

import test_production_seedance as fixtures
from test_production_seedance_local_video import _MaterializationTransport, SOURCE_BYTES
from ai_video.errors import AiVideoError
from ai_video.production.models import ActorIdentity, AssetType
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.seedance_mixed_reference import (
    SeedanceMixedReferenceResolver, verify_reference_video,
)
from ai_video.production.seedance_reference_image import measure_reference_image
from ai_video.production.video import VideoGenerationMode, VideoMediaReferenceBinding

URL = "https://media.storage.example/guide.mp4?secret=not-for-logs"


def _fixture(monkeypatch, *, audio=False):
    source = b"ID3\x04\x00\x00\x00\x00\x00\x00fixture" if audio else SOURCE_BYTES
    binding = VideoMediaReferenceBinding(
        kind="video", role="reference_video", asset_id="guide-video",
        asset_sha256=hashlib.sha256(SOURCE_BYTES).hexdigest(), size_bytes=len(SOURCE_BYTES),
        mime_type="video/mp4", width=1280, height=720, fps=24, duration_millis=2000,
    )
    if audio:
        binding = VideoMediaReferenceBinding(kind="audio", role="reference_audio",
            asset_id="voice-reference", asset_sha256=hashlib.sha256(source).hexdigest(),
            size_bytes=len(source), mime_type="audio/mpeg", duration_millis=6504)
    original = fixtures._synthetic_registry
    registry_bytes = None

    def with_video(*args, **kwargs):
        nonlocal registry_bytes
        registry, _, pointer = original(*args, **kwargs)
        video_record = registry.assets[0].model_copy(update={
            "asset_id": binding.asset_id, "asset_type": AssetType.VOICE if audio else AssetType.VIDEO,
            "sha256": binding.asset_sha256, "size_bytes": binding.size_bytes,
            "mime_type": binding.mime_type, "width": binding.width, "height": binding.height,
            "duration_seconds": binding.duration_millis / 1000,
        })
        registry = registry.model_copy(update={"assets": (*registry.assets, video_record)})
        revision = registry_semantic_sha256(registry)
        registry = registry.model_copy(update={"revision_id": revision, "content_hash": revision})
        registry_bytes = fixtures._canonical_model_bytes(registry) + b"\n"
        pointer = pointer.model_copy(update={"revision_id": revision, "content_hash": revision,
                                             "path": Path(f"assets/registry.{revision}.json"),
                                             "file_sha256": hashlib.sha256(registry_bytes).hexdigest()})
        return registry, registry_bytes, pointer

    monkeypatch.setattr(fixtures, "_synthetic_registry", with_video)
    data = fixtures._synthetic_submit_fixture(mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
                                             binding_role="reference", media_bindings=(binding,))
    options = dict(binding=binding, url=URL, allowed_origin="https://media.storage.example",
                   source_bytes=source, registry_snapshot_bytes=registry_bytes,
                   attested_by=ActorIdentity(actor_id="operator", actor_kind="human"),
                   locator_not_after=fixtures.FIXED_NOW + timedelta(hours=1),
                   transport=_MaterializationTransport(), now=lambda: fixtures.FIXED_NOW)
    return data, options


def test_inline_audio_preserves_original_bytes_and_full_paid_preview(monkeypatch):
    from ai_video.production.seedance_mixed_reference import verify_reference_audio
    data, options = _fixture(monkeypatch, audio=True)
    profile, resolved, preview, paid, images, _, _, _ = data
    audio = verify_reference_audio(**{k: options[k] for k in (
        "binding", "source_bytes", "registry_snapshot_bytes", "attested_by")})
    resolver = SeedanceMixedReferenceResolver(images=images, audios=(audio,),
        now=lambda: fixtures.FIXED_NOW)
    transport = fixtures._FakeTransport()
    transport.responses.append(fixtures._json_response({"id": "audio-reference-task"}))
    provider = fixtures.SeedanceVideoProvider(profile=profile, transport=transport,
        credential=lambda: "fixture-key", input_reference=resolver, now=lambda: fixtures.FIXED_NOW)
    authorization = fixtures._authorization(paid).model_copy(update={
        "egress_policy_receipt_id": images.egress_policy_receipt_id})
    permit = fixtures._permit(resolved, preview, paid, authorization)
    wrong_registry = resolved.model_copy(update={"activation_scope": None})
    with pytest.raises(AiVideoError):
        resolver.validate_submit(wrong_registry, paid, authorization)
    wrong_egress = paid.model_copy(update={"egress_items": paid.egress_items[:-1]})
    with pytest.raises(AiVideoError):
        resolver.validate_submit(resolved, wrong_egress, authorization)
    provider.submit(resolved, preview, paid, authorization, permit)
    body = json.loads(transport.requests[0].body)
    item = body["content"][2]
    assert item["role"] == "reference_audio"
    assert item["audio_url"]["url"].startswith("data:audio/mp3;base64,")
    assert base64.b64decode(item["audio_url"]["url"].split(",")[1]) == options["source_bytes"]
    with pytest.raises(AiVideoError):
        provider.submit(resolved, preview, paid, authorization, permit)
    assert len(transport.requests) == 1
    with pytest.raises(AiVideoError):
        resolver(options["binding"].model_copy(update={"duration_millis": 7000}))
    with pytest.raises(AiVideoError):
        images.validate_submit(resolved, paid, authorization)


@pytest.mark.parametrize("fault", ["bytes", "duration", "registry", "attestation", "kind", "format"])
def test_inline_audio_rejects_mismatch(monkeypatch, fault):
    from ai_video.production.seedance_mixed_reference import verify_reference_audio
    _, source = _fixture(monkeypatch, audio=True)
    options = {k: source[k] for k in ("binding", "source_bytes", "registry_snapshot_bytes", "attested_by")}
    if fault == "bytes":
        options["source_bytes"] += b"changed"
    elif fault == "duration":
        options["binding"] = options["binding"].model_copy(update={"duration_millis": 7000})
    elif fault == "registry":
        options["registry_snapshot_bytes"] = b"{}"
    elif fault == "attestation":
        options["attested_by"] = ActorIdentity(actor_id="agent", actor_kind="codex")
    elif fault == "kind":
        options["binding"] = options["binding"].model_copy(update={"kind": "video"})
    else:
        options["source_bytes"] = b"not an audio file"
        options["binding"] = options["binding"].model_copy(update={
            "asset_sha256": hashlib.sha256(options["source_bytes"]).hexdigest(),
            "size_bytes": len(options["source_bytes"])})
    with pytest.raises(AiVideoError):
        verify_reference_audio(**options)


def test_mixed_payload_preserves_images_and_video_and_consumes_once(monkeypatch):
    data, options = _fixture(monkeypatch)
    profile, resolved, preview, paid, images, png, _, _ = data
    video = verify_reference_video(**options)
    assert "secret=" not in json.dumps(video.evidence())
    assert "secret=" not in repr(video)
    resolver = SeedanceMixedReferenceResolver(images=images, videos=(video,), now=lambda: fixtures.FIXED_NOW)
    transport = fixtures._FakeTransport()
    transport.responses.append(fixtures._json_response({"id": "task-mixed"}))
    provider = fixtures.SeedanceVideoProvider(profile=profile, transport=transport,
        credential=lambda: "fixture-key", input_reference=resolver, now=lambda: fixtures.FIXED_NOW)
    authorization = fixtures._authorization(paid).model_copy(update={
        "egress_policy_receipt_id": images.egress_policy_receipt_id})
    permit = fixtures._permit(resolved, preview, paid, authorization)
    provider.submit(resolved, preview, paid, authorization, permit)
    body = json.loads(transport.requests[0].body)
    assert base64.b64decode(body["content"][1]["image_url"]["url"].split(",")[1]) == png
    assert body["content"][2] == {"type": "video_url", "video_url": {"url": URL}, "role": "reference_video"}
    with pytest.raises(AiVideoError):
        provider.submit(resolved, preview, paid, authorization, permit)
    assert len(transport.requests) == 1


@pytest.mark.parametrize("fault", ["changed_remote", "changed_source", "redirect", "origin", "expired", "registry"])
def test_video_readback_rejects_mismatch_before_submit(monkeypatch, fault):
    _, options = _fixture(monkeypatch)
    if fault == "changed_remote":
        options["transport"] = _MaterializationTransport(readback=b"changed")
    elif fault == "changed_source":
        options["source_bytes"] = b"changed"
    elif fault == "origin":
        options["url"] = "https://other.example/guide.mp4"
    elif fault == "expired":
        options["locator_not_after"] = fixtures.FIXED_NOW
    elif fault == "registry":
        options["binding"] = options["binding"].model_copy(update={"duration_millis": 3000})
    else:
        from contextlib import contextmanager
        @contextmanager
        def redirect(_):
            yield type("Redirect", (), {"status_code": 302, "headers": {}})()
        options["transport"].stream = redirect
    with pytest.raises(AiVideoError):
        verify_reference_video(**options)


def test_expired_verified_video_stops_before_credentials_and_permit(monkeypatch):
    data, options = _fixture(monkeypatch)
    profile, resolved, preview, paid, images, _, _, _ = data
    video = verify_reference_video(**options)
    resolver = SeedanceMixedReferenceResolver(images=images, videos=(video,),
        now=lambda: fixtures.FIXED_NOW + timedelta(minutes=6))
    transport = fixtures._FakeTransport()
    def forbidden():
        pytest.fail("expired video must not read credentials")
    provider = fixtures.SeedanceVideoProvider(profile=profile, transport=transport,
        credential=forbidden, input_reference=resolver, now=lambda: fixtures.FIXED_NOW)
    authorization = fixtures._authorization(paid).model_copy(update={
        "egress_policy_receipt_id": images.egress_policy_receipt_id})
    permit = fixtures._permit(resolved, preview, paid, authorization)
    with pytest.raises(AiVideoError):
        provider.submit(resolved, preview, paid, authorization, permit)
    assert not transport.requests
    assert permit._validate_paid_provider_operation_permit(**fixtures.build_video_paid_permit_binding(
        resolved, preview, paid, authorization))


def test_reference_jpeg_measured_without_reencoding():
    stream = BytesIO()
    Image.new("RGB", (320, 300)).save(stream, format="JPEG")
    payload = stream.getvalue()
    result = measure_reference_image(payload, "image/jpeg")
    assert (result.width, result.height, result.size_bytes) == (320, 300, len(payload))
    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError):
        measure_reference_image(fixtures._rgba_png(), "image/jpeg")


def test_pinned_native_prompt_keeps_recipe_coverage_and_exact_text(monkeypatch):
    from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding
    from ai_video.production.video_compiler import CompiledProviderVideoRequest

    captured = {}
    original = fixtures.SeedanceVideoProvider.compile_request
    def capture(self, bound, requirement, **kwargs):
        result = original(self, bound, requirement, **kwargs)
        captured.update(bound=bound, requirement=requirement, result=result)
        return result
    monkeypatch.setattr(fixtures.SeedanceVideoProvider, "compile_request", capture)
    fixtures.test_recipe_compiles_complete_t2v_intent_with_native_remote_grammar()
    monkeypatch.setattr(fixtures.SeedanceVideoProvider, "compile_request", original)
    text = captured["result"].provider_native_prompt + "\nExact authored punctuation: …。" + "原始画布全文。" * 900
    assert len(text) > 6306
    binding = SeedanceNativePromptBinding(
        provider_bound_request_hash=captured["bound"].provider_bound_request_hash,
        prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_evidence_sha256="a" * 64)
    def provider(selected):
        return fixtures.SeedanceVideoProvider(profile=fixtures._profile(),
            transport=fixtures._FakeTransport(), credential=lambda: "unused",
            input_reference=fixtures._sealed_asset_resolver(), native_prompt_binding=selected)
    result = provider(binding).compile_request(captured["bound"], captured["requirement"])
    assert isinstance(result, CompiledProviderVideoRequest)
    assert result.provider_native_prompt == text
    incomplete = binding.model_copy(update={"prompt_text": "A nice shot.",
        "prompt_sha256": hashlib.sha256(b"A nice shot.").hexdigest()})
    assert not isinstance(provider(incomplete).compile_request(
        captured["bound"], captured["requirement"]), CompiledProviderVideoRequest)
    wrong = binding.model_copy(update={"provider_bound_request_hash": "b" * 64})
    with pytest.raises(ValueError, match="another provider-bound"):
        provider(wrong).compile_request(captured["bound"], captured["requirement"])


def test_explicit_credential_reference_matches_preview_without_fallback():
    from ai_video.production.paid_provider import PaidProviderCallPreview, SecretReference
    reference = SecretReference(kind="environment", reference_id="SEEDANCE_API_KEY")
    transport = fixtures._FakeTransport()
    transport.responses.append(fixtures._json_response({"id": "task-explicit-source"}))
    calls = []
    def credential():
        calls.append(True)
        return "fixture-key"
    profile = fixtures._profile()
    provider = fixtures.SeedanceVideoProvider(profile=profile, transport=transport,
        credential=credential, credential_reference=reference,
        input_reference=fixtures._sealed_asset_resolver(), now=lambda: fixtures.FIXED_NOW)
    resolved = provider.resolve(fixtures._request(profile))
    preview = provider.preview(resolved)
    wrong = fixtures._paid_preview(resolved, preview)
    wrong_auth = fixtures._authorization(wrong)
    with pytest.raises(AiVideoError):
        provider.submit(resolved, preview, wrong, wrong_auth,
                        fixtures._permit(resolved, preview, wrong, wrong_auth))
    assert not calls and not transport.requests
    paid = PaidProviderCallPreview.create(**{
        **wrong.model_dump(exclude={"preview_fingerprint"}), "secret_reference": reference})
    authorization = fixtures._authorization(paid)
    provider.submit(resolved, preview, paid, authorization,
                    fixtures._permit(resolved, preview, paid, authorization))
    assert len(calls) == len(transport.requests) == 1


def test_exact_chinese_dialogue_expresses_language_without_appending_text():
    from types import SimpleNamespace
    from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding

    text = '曾亮低声：“先冷静。”'
    binding = SeedanceNativePromptBinding(provider_bound_request_hash="a" * 64,
        prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_evidence_sha256="b" * 64)
    bound = SimpleNamespace(provider_bound_request_hash="a" * 64)
    def compile(language, line):
        dialogue = SimpleNamespace(mode="dialogue", language=language, verbatim_text=line)
        requirement = SimpleNamespace(generation_intent=SimpleNamespace(
            dialogue_intent=dialogue, primary_camera_motion=None))
        return binding.compile(bound, (), requirement=requirement)
    result = compile("zh-CN", "先冷静。")
    assert result.prompt_text == text
    assert result.expressed_control_paths == ("generation_intent.dialogue_intent.language",
                                               "generation_intent.dialogue_intent.mode")
    assert not compile("en", "先冷静。").expressed_control_paths
    assert not compile("zh-CN", "不在原文的台词").expressed_control_paths
    assert not compile("zh-CN", "hello").expressed_control_paths


def test_exact_chinese_push_in_expresses_only_matching_camera_direction():
    from types import SimpleNamespace
    from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding
    text = "轻微手持推近曾亮"
    binding = SeedanceNativePromptBinding(provider_bound_request_hash="a" * 64,
        prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_evidence_sha256="b" * 64)
    motion = SimpleNamespace(movement_kind="dolly_in", direction="forward")
    intent = SimpleNamespace(dialogue_intent=SimpleNamespace(mode="none"), primary_camera_motion=motion)
    result = binding.compile(SimpleNamespace(provider_bound_request_hash="a" * 64), (),
                             requirement=SimpleNamespace(generation_intent=intent))
    assert result.prompt_text == text
    assert result.expressed_control_paths == ("generation_intent.primary_camera_motion.direction",)
    motion.direction = "backward"
    assert not binding.compile(SimpleNamespace(provider_bound_request_hash="a" * 64), (),
        requirement=SimpleNamespace(generation_intent=intent)).expressed_control_paths


def test_exact_chinese_counterclockwise_arc_preserves_camera_direction():
    from types import SimpleNamespace
    from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding
    text = "摄影机沿同一条逆时针弧线移动。"
    binding = SeedanceNativePromptBinding(provider_bound_request_hash="a" * 64,
        prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_evidence_sha256="b" * 64)
    motion = SimpleNamespace(movement_kind="orbit_left", direction="left")
    intent = SimpleNamespace(dialogue_intent=SimpleNamespace(mode="none"), primary_camera_motion=motion)
    def compile():
        return binding.compile(SimpleNamespace(provider_bound_request_hash="a" * 64), (),
            requirement=SimpleNamespace(generation_intent=intent))
    assert compile().prompt_text == text
    assert compile().expressed_control_paths == ("generation_intent.primary_camera_motion.direction",)
    motion.direction = "right"
    assert not compile().expressed_control_paths
