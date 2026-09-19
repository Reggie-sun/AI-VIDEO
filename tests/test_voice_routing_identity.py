"""Qualified fixed-voice admission through the public review and Router seams."""

from __future__ import annotations

import hashlib
import io
import re
import subprocess
import wave
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_video.production.audio import VoiceGenerationRequest, VoiceProviderParameters
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    ActorIdentity,
    AudioKind,
    EvidenceStrength,
    QaLayer,
    QaVerdict,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewReceipt,
    ReviewRequest,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    SecretReference,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production.voice_candidate import make_voice_candidate_preparer
from ai_video.production.voice_routing import VoiceAudioHandoff, VoiceRoutingContext
from ai_video.production.voice_routing_contracts import VoiceMode, VoiceRoutingRequirement
from ai_video.production.composition_contracts import AudioTrackSpec
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from test_production_minimax_speech import (
    _DummySecret,
    _FakeTransport,
    _authorization,
    _policy,
    _pricing,
    _response,
)
from test_production_voice_candidate import _toolchain
from test_voice_routing_integration import (
    _SCRIPT,
    _VOICE_ID,
    _orchestrator,
    _voice_requirement,
    _voice_setup,
)

import production_project_factory as project_factory
from production_e2e_support import DeterministicHyperFramesRunner


_NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)
_HUMAN = ToolIdentity(name="voice-identity-human", version="1")


class _TimelineDeterministicRenderer(DeterministicHyperFramesRunner):
    """Make the existing fake renderer honor its materialized timeline duration."""

    def run(self, command, args, *, cwd, env, timeout_seconds):
        if command != "render":
            return super().run(
                command, args, cwd=cwd, env=env, timeout_seconds=timeout_seconds
            )
        from production_e2e_support import RendererCommandResult, _RendererCall

        self.calls.append(_RendererCall(command))
        duration = re.search(
            r'data-duration="([0-9.]+)"', (cwd / "index.html").read_text()
        )
        assert duration is not None
        output = Path(args[args.index("-o") + 1])
        mixed_wavs = tuple(sorted((cwd / "assets").glob("*.wav")))
        source_sha256 = hashlib.sha256((cwd / "index.html").read_bytes()).hexdigest()
        command_line = [
            str(self.ffmpeg_path), "-nostdin", "-v", "error", "-y", "-f", "lavfi",
            "-i", f"color=c=0x{source_sha256[:6]}:s=1280x720:r=24:d={duration.group(1)}",
        ]
        if mixed_wavs:
            command_line.extend(("-i", str(mixed_wavs[0])))
        command_line.extend(("-map", "0:v:0"))
        if mixed_wavs:
            command_line.extend(("-map", "1:a:0"))
        command_line.extend((
            "-t", duration.group(1), "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-threads", "1",
        ))
        if mixed_wavs:
            command_line.extend(("-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"))
        command_line.extend(("-map_metadata", "-1", "-movflags", "+faststart", str(output)))
        completed = subprocess.run(
            command_line,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            env=env,
        )
        return RendererCommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout.decode(errors="replace"),
            stderr=completed.stderr.decode(errors="replace"),
        )


def _qualified_sample_wav(marker: str) -> bytes:
    """Match the existing P4 deterministic candidate's measured fixture length."""
    pulse = int.from_bytes(hashlib.sha256(marker.encode("utf-8")).digest()[:2], "big")
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(44_100)
        target.writeframes(pulse.to_bytes(2, "little") + b"\0\0" * 95_999)
    return output.getvalue()


def _minimax_provider(script: str, *, sample_marker: str):
    from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider

    def mutate(payload) -> None:
        payload["extra_info"].update(usage_characters=len(script))
        payload["trace_id"] = f"minimax-{sample_marker}"

    return MiniMaxSpeechVoiceProvider(
        transport=_FakeTransport(_response(
            audio=_qualified_sample_wav(sample_marker), mutate=mutate
        )),
        pricing=_pricing().model_copy(update={"currency": "CNY"}),
        api_key=_DummySecret(),
        policy=_policy(),
    )


def _paid_preview(provider, request: VoiceGenerationRequest) -> PaidProviderCallPreview:
    preview = provider.preview(request)
    return PaidProviderCallPreview.create(
        attempt_id=request.attempt_id,
        operation="voice_generation",
        provider_kind=request.provider_kind,
        model_id=request.model_id,
        request_fingerprint=request.voice_request_fingerprint,
        billing_mode="remote_metered",
        currency=preview.currency,
        estimated_cost_upper_bound_microunits=preview.estimated_cost_upper_bound_microunits,
        destination=preview.destination,
        method="POST",
        egress_items=(PaidProviderEgressItem(
            item_id="script",
            sha256=request.script_hash,
            size_bytes=len(request.script_text.encode("utf-8")),
            mime_type="text/plain",
            purpose="script",
        ),),
        retention_mode=provider._policy.retention_mode,
        provider_policy_snapshot_id=provider._policy.policy_receipt_id,
        secret_reference=SecretReference(
            kind=provider._policy.credential_reference_kind,
            reference_id=provider._policy.credential_reference_id,
        ),
    )


def _paid_authorization(preview: PaidProviderCallPreview) -> PaidProviderAuthorizationDecision:
    return PaidProviderAuthorizationDecision.create(
        attempt_id=preview.attempt_id,
        preview_fingerprint=preview.preview_fingerprint,
        explicit_opt_in=True,
        actor=ActorIdentity(actor_id="fixture-owner", actor_kind="human"),
        opt_in_policy_receipt_id="fixture-opt-in",
        budget_policy_id="fixture-voice-budget",
        budget_currency="CNY",
        project_budget_ceiling_microunits=100_000_000,
        per_call_ceiling_microunits=10_000_000,
        egress_authorized=True,
        egress_policy_receipt_id="fixture-egress",
        live_test_authorized=True,
        live_authorization_receipt_id="fixture-live",
        issued_at=_NOW,
        expires_at=_NOW + timedelta(minutes=10),
        max_submit_count=1,
        voice_batch_submit_limit=None,
    )


def _sample_request(project, *, shot_id: str, attempt_id: str) -> VoiceGenerationRequest:
    shot = next(item for item in project.shots if item.shot_id == shot_id)
    return VoiceGenerationRequest.create(
        request_id=f"voice-identity-{attempt_id}",
        attempt_id=attempt_id,
        provider_kind="minimax-speech",
        model_id="speech-2.8-hd",
        audio_kind=AudioKind.DIALOGUE,
        script_text=_SCRIPT,
        speaker_id="hero",
        voice_id=_VOICE_ID,
        language="English",
        output_container="wav",
        output_codec="pcm_s16le",
        output_sample_rate_hz=44_100,
        output_channels=1,
        provider_parameters=VoiceProviderParameters(speed_milli=1000),
        base_project=project.manifest.active_project,
        base_registry=project.manifest.active_registry,
        input_artifact_ids=(shot.artifact_id,),
        input_fingerprint=shot.content_hash,
        pricing_snapshot_id="minimax-token-plan-2026-08-19",
        budget_reservation_receipt_id=f"fixture-budget-{attempt_id}",
        egress_authorization_receipt_id=f"fixture-egress-{attempt_id}",
    )


def _activate_sample(runtime, request: VoiceGenerationRequest) -> None:
    provider = _minimax_provider(request.script_text, sample_marker=request.attempt_id)
    preview = _paid_preview(provider, request)
    authorization = _paid_authorization(preview)
    committer = ProductionStateCommitter(
        runtime.root,
        voice_candidate_preparer=make_voice_candidate_preparer(runtime.root, _toolchain()),
        paid_provider_authorizer=lambda exact: authorization if exact == preview else None,
        paid_provider_clock=lambda: _NOW,
    )
    committer.generate_voice_asset(
        request,
        provider,
        _authorization(provider, request),
        paid_preview=preview,
        dependency_transition_preparer=lambda candidate: _sample_transition(
            runtime, candidate, request
        ),
    )


def _sample_transition(runtime, request, voice_request: VoiceGenerationRequest):
    """Rebuild the current graph for a generated sample without a caption sidecar."""
    from ai_video.production.dependency import build_applied_dependency_evidence
    from ai_video.production.models import AssetRegistrySnapshot, ProductionProject
    from production_project_factory import make_base_ai_comic_current_composition
    import yaml

    active = load_production_project(runtime.root / "project.yaml")
    project_artifact = next(item for item in request.artifacts if item.relative_path == request.next_project.path)
    registry_artifact = next(item for item in request.artifacts if item.relative_path == request.next_registry.path)
    project = ProductionProject.model_validate(yaml.safe_load(project_artifact.payload))
    registry = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
    candidate = active.model_copy(update={
        "project": project,
        "registry": registry,
        "manifest": active.manifest.model_copy(update={
            "active_project": request.next_project,
            "active_registry": request.next_registry,
        }),
        "dependency_graph": None,
        "render_state": None,
    })
    assert runtime._voice_request is not None
    composition, styles = make_base_ai_comic_current_composition(
        candidate,
        runtime.image_runtime.base_inputs,
        revision=1,
        voice_request=runtime._voice_request,
        artifacts=request.artifacts,
    )
    inputs = replace(
        runtime.image_runtime.base_inputs,
        project=candidate,
        composition_spec=composition,
        # Only the candidate attempt has the new Registry pointer. Historical
        # generated assets remain byte/provenance-backed graph inputs here.
        voice_requests=(voice_request,),
        caption_style_fingerprints=styles,
    )
    graph = build_production_dependency_graph(inputs)
    states = resolve_dependency_state(
        graph, build_applied_dependency_evidence(inputs, None)
    ).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=request.expected_manifest_revision,
        base_dependency_graph=active.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_payload = _canonical_json_bytes(graph)
    return replace(request, dependency_graph_transition=transition, artifacts=tuple(sorted((
        *request.artifacts,
        PreparedArtifact(
            transition.candidate_dependency_graph.path,
            graph_payload,
            hashlib.sha256(graph_payload).hexdigest(),
        ),
    ), key=lambda item: item.relative_path.as_posix())))


def _author_voice_routing(runtime, voice: VoiceRoutingRequirement | None):
    """Commit current two-Shot authoring through the existing graph owner."""
    loaded = load_production_project(runtime.root / "project.yaml")
    shots = []
    refs = []
    artifacts: list[PreparedArtifact] = []
    for shot, reference in zip(loaded.shots, loaded.project.artifacts.shots, strict=True):
        updated = seal_artifact(shot.model_copy(update={
            "revision": shot.revision + 1,
            "content_hash": "0" * 64,
            "dialogue": _SCRIPT,
            "voice_routing": voice if shot.shot_id == "shot-1" else None,
            **(
                {
                    "visual_strategy": project_factory.VisualStrategy.GENERATED_VIDEO,
                    "required_asset_roles": (
                        project_factory.AssetRoleRequirement(
                            role="final_visual",
                            asset_ids=(),
                            allowed_asset_types=(project_factory.AssetType.VIDEO,),
                        ),
                    ),
                    "generated_video_rationale": "The sealed Shot requires a generated performance.",
                }
                if voice is not None and shot.shot_id == "shot-1"
                else {}
            ),
        }))
        path = Path(f"creative/shots/{shot.shot_id}-voice-identity-{updated.content_hash[:12]}.yaml")
        refs.append(reference.model_copy(update={
            "revision": updated.revision,
            "content_hash": updated.content_hash,
            "path": path,
        }))
        payload = _canonical_yaml_bytes(updated)
        artifacts.append(PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest()))
        shots.append(updated)
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": tuple(refs)}),
    }))
    request = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=loaded.registry,
        attempt_id=(
            "voice-identity-dialogue-authoring"
            if voice is None
            else "voice-identity-route-authoring"
        ),
    )
    candidate = loaded.model_copy(update={
        "project": project,
        "shots": tuple(shots),
        "manifest": loaded.manifest.model_copy(update={"active_project": request.next_project}),
    })
    from production_project_factory import make_base_ai_comic_current_composition
    assert runtime._voice_request is not None
    composition_candidate = candidate.model_copy(update={
        "shots": tuple(
            original if voice is not None and original.shot_id == "shot-1" else updated
            for original, updated in zip(loaded.shots, candidate.shots, strict=True)
        )
    })
    composition, styles = make_base_ai_comic_current_composition(
        composition_candidate,
        runtime.image_runtime.base_inputs,
        revision=1,
        voice_request=runtime._voice_request,
    )
    current_voice_requests: tuple[VoiceGenerationRequest, ...] = (
        runtime._voice_request,
    )
    if voice is not None:
        from ai_video.production._voice_project_reader import read_canonical_voice_model

        sample_request, _ = read_canonical_voice_model(
            runtime.root,
            "voice-identity-shot-1",
            "request.json",
            VoiceGenerationRequest,
        )
        composition = seal_artifact(composition.model_copy(update={
            "content_hash": "0" * 64,
            "shot_ids": ("shot-2",),
            "layers": tuple(
                layer for layer in composition.layers if layer.shot_id == "shot-2"
            ),
            "transitions": (),
            "audio_tracks": tuple(
                track.model_copy(update={"shot_id": None, "start_sample": 0})
                if track.shot_id not in (None, "shot-2")
                else track
                for track in composition.audio_tracks
            ),
            "caption_tracks": tuple(
                binding.model_copy(update={"shot_id": None})
                if binding.shot_id not in (None, "shot-2")
                else binding
                for binding in composition.caption_tracks
            ),
        }))
        current_voice_requests = (sample_request,)
    inputs = replace(
        runtime.image_runtime.base_inputs,
        project=candidate,
        composition_spec=composition,
        voice_requests=current_voice_requests,
        caption_style_fingerprints=styles,
    )
    graph = build_production_dependency_graph(inputs)
    states = resolve_dependency_state(
        graph, build_applied_dependency_evidence(inputs, None)
    ).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired_fingerprints(graph),
    )
    graph_payload = _canonical_json_bytes(graph)
    request = replace(request, dependency_graph_transition=transition, artifacts=tuple(sorted((
        *request.artifacts,
        *artifacts,
        PreparedArtifact(
            transition.candidate_dependency_graph.path,
            graph_payload,
            hashlib.sha256(graph_payload).hexdigest(),
        ),
        ), key=lambda item: item.relative_path.as_posix())))
    ProductionStateCommitter(runtime.root).commit(request)
    return composition
    return load_production_project(runtime.root / "project.yaml")


def _activate_voice_identity_policy(runtime) -> None:
    loaded = load_production_project(runtime.root / "project.yaml")
    base_policy = loaded.qa_policy or runtime._qa_policy()
    policy = seal_artifact(base_policy.model_copy(update={
        "artifact_id": "voice-identity-qa-policy",
        "revision": base_policy.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": "voice-identity-qa-policy",
        "source_provenance": (SourceReference(kind="derived", reference="voice-identity"),),
        "required_layers": tuple(dict.fromkeys((*base_policy.required_layers, QaLayer.SEMANTIC))),
        "semantic_requirement": "required",
        "semantic_authorities": (_HUMAN,),
    }))
    ProductionStateCommitter(runtime.root).activate_qa_policy(
        policy,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="activate-voice-identity-policy",
    )


def _record_identity_review(runtime, *, candidate, handoff, projection):
    """Persist a human semantic review through the ordinary P6 request/receipt seam."""
    from ai_video.production.review import build_technical_review_context
    from ai_video.production.paths import canonical_review_evidence_path

    loaded = load_production_project(runtime.root / "project.yaml")
    assert loaded.render_state is not None and loaded.qa_policy is not None
    timeline = loaded.render_state.timeline
    from ai_video.production.models import ResolvedTimeline
    timeline_model = ResolvedTimeline.model_validate_json((runtime.root / timeline.path).read_bytes())
    context = build_technical_review_context(
        loaded, timeline_model,
        render_output_sha256=loaded.render_state.output.file_sha256,
        measurement_contract_version="voice-identity/1",
    )
    request = seal_artifact(ReviewRequest(
        artifact_id="voice-identity-review-request",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="voice-identity-review-request",
        source_provenance=(SourceReference(kind="derived", reference="voice-identity"),),
        request_id="voice-identity-review-request",
        base_manifest_revision=loaded.manifest.manifest_revision,
        dependency_graph=loaded.manifest.active_dependency_graph,
        dependency_states_hash=canonical_sha256({"dependency_states": [
            item.model_dump(mode="json") for item in loaded.manifest.dependency_states
        ]}),
        render_state=loaded.manifest.active_render_state,
        render_output_sha256=loaded.render_state.output.file_sha256,
        timeline_fingerprint=loaded.render_state.timeline_fingerprint,
        qa_policy=loaded.manifest.active_qa_policy,
        requested_layers=(QaLayer.SEMANTIC,),
        evidence_tool_identities=(_HUMAN,),
        technical_context=context,
    ))
    committer = ProductionStateCommitter(runtime.root)
    begun = committer.begin_review(request, attempt_id="voice-identity-review")
    review_pointer = next(item.review_request for item in begun.attempts if item.attempt_id == "voice-identity-review")
    assert review_pointer is not None

    def analyze(durable, permit):
        assert permit._consume_review_analysis_permit(
            request_content_hash=durable.content_hash,
            render_output_sha256=durable.render_output_sha256,
            technical_context_hash=canonical_sha256(
                durable.technical_context.model_dump(mode="json")
            ),
        )
        return durable

    committer.run_review_analysis(
        review_request=review_pointer,
        expected_manifest_revision=begun.manifest_revision,
        analyzer=analyze,
    )
    speaker = candidate.voice_route.readiness.context.audio_handoffs[0].speaker_id
    request_handoff = handoff.voice_request
    assert request_handoff is not None
    variant = next(item for item in candidate.capabilities.variants if item.capability_id == candidate.capability_id)
    assets = [
        next(item for item in loaded.registry.assets if item.asset_id == f"voice-{attempt}")
        for attempt in ("voice-identity-shot-1", "voice-identity-shot-2")
    ]
    payload = {
        "coverage_complete": True,
        "evaluator_identity": f"{_HUMAN.name}@{_HUMAN.version}",
        "semantic_match": True,
        "voice_identity": {
            "contract_version": "voice-identity/1",
            "route": "separate",
            "speaker_id": speaker,
            "language": "en",
            "voice_id": _VOICE_ID,
            "reference_sha256": None,
            "provider_name": candidate.capabilities.provider_name,
            "model_id": variant.model_id,
            "profile_sha256": candidate.provider_profile.profile_sha256,
            "compiler_hash": candidate.compiler_contract.compiler_hash,
            "character_hashes": {
                item.character_id: item.content_hash
                for item in projection.requirement.characters
            },
            "listening_speed_milli": 1000,
            "voice_model_id": request_handoff.model_id,
            "voice_parameters_hash": request_handoff.provider_parameters_hash,
            "voice_endpoint": handoff.voice_preview.destination,
            "artifact_sha256s": [assets[0].sha256, assets[1].sha256],
            "findings": {"voice_identity": "PASS", "language": "PASS", "scope": "PASS"},
        },
    }
    evidence = seal_artifact(ReviewEvidence(
        artifact_id="voice-identity-evidence",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="voice-identity-evidence",
        source_provenance=(SourceReference(kind="derived", reference="human-1x-review"),),
        evidence_id="voice-identity-evidence",
        layer=QaLayer.SEMANTIC,
        strength=EvidenceStrength.HUMAN,
        render_output_sha256=request.render_output_sha256,
        timeline_fingerprint=request.timeline_fingerprint,
        dependency_graph_revision_id=request.dependency_graph.revision_id,
        tool_identity=_HUMAN,
        measurement_contract_version="voice-identity/1",
        subject_ids=tuple(item.asset_id for item in assets) + ("shot-1", "shot-2"),
        measured_payload=payload,
    ))
    evidence_payload = _canonical_json_bytes(evidence)
    evidence_pointer = ReviewEvidencePointer(
        path=canonical_review_evidence_path(evidence.content_hash),
        evidence_id=evidence.evidence_id,
        layer=evidence.layer,
        strength=evidence.strength,
        content_hash=evidence.content_hash,
        file_sha256=hashlib.sha256(evidence_payload).hexdigest(),
    )
    receipt = seal_artifact(ReviewReceipt(
        artifact_id="voice-identity-review-receipt",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="voice-identity-review-receipt",
        source_provenance=(SourceReference(kind="derived", reference=evidence.evidence_id),),
        review_id="voice-identity-review",
        layer=QaLayer.SEMANTIC,
        review_request=review_pointer,
        render_state=request.render_state,
        render_output_sha256=request.render_output_sha256,
        timeline_fingerprint=request.timeline_fingerprint,
        dependency_graph_revision_id=request.dependency_graph.revision_id,
        qa_policy=request.qa_policy,
        evidence=(evidence_pointer,),
        evidence_ids=(evidence.evidence_id,),
        tool_identities=(_HUMAN,),
        verdict=QaVerdict.PASS,
    ))
    reviewed = committer.record_review_receipt(
        receipt, (evidence,),
        expected_manifest_revision=committer._read_manifest().manifest_revision,
        attempt_id="voice-identity-review",
    )
    return next(item for item in reviewed.active_review_receipts if item.layer is QaLayer.SEMANTIC)


def test_cross_shot_fixed_separate_voice_requires_and_accepts_qualified_human_evidence(tmp_path: Path) -> None:
    runtime = project_factory.make_base_ai_comic_e2e_runtime(tmp_path)
    runtime.generate_two_shot_images()
    runtime.generate_voice_and_captions()
    ProductionStateCommitter(tmp_path).upgrade_manifest_schema(
        "2.7", expected_manifest_revision=ProductionStateCommitter(tmp_path)._read_manifest().manifest_revision
    )

    _author_voice_routing(runtime, None)
    sample_shot_artifact_ids = {
        shot.shot_id: shot.artifact_id
        for shot in load_production_project(tmp_path / "project.yaml").shots
    }
    for shot_id in ("shot-2", "shot-1"):
        current = load_production_project(tmp_path / "project.yaml")
        _activate_sample(runtime, _sample_request(
            current, shot_id=shot_id, attempt_id=f"voice-identity-{shot_id}"
        ))

    voice = _voice_requirement(mode=VoiceMode.AUTO, consistency="cross_shot_fixed")
    review_composition = _author_voice_routing(runtime, voice)
    assert {
        shot.shot_id: shot.artifact_id
        for shot in load_production_project(tmp_path / "project.yaml").shots
    } == sample_shot_artifact_ids
    from ai_video.production._voice_project_reader import read_canonical_voice_model

    runtime._voice_request = read_canonical_voice_model(
        tmp_path,
        "voice-identity-shot-1",
        "request.json",
        VoiceGenerationRequest,
    )[0]
    runtime.renderer = _TimelineDeterministicRenderer(runtime.renderer.ffmpeg_path)
    runtime.render_current_composition(composition=review_composition)
    _activate_voice_identity_policy(runtime)
    source = load_production_project(tmp_path / "project.yaml")
    setup, _ = _voice_setup(source.shots[0], mode=VoiceMode.AUTO)
    setup["context"] = setup["context"].model_copy(update={
        "selected_registry_revision_id": source.manifest.active_registry.revision_id,
    })
    setup["lifecycle"] = setup["lifecycle"].model_copy(update={
        "target_asset_role": source.shots[0].required_asset_roles[0].role,
        "base_project": source.manifest.active_project,
        "base_registry": source.manifest.active_registry,
        "base_dependency_graph": source.manifest.active_dependency_graph,
        "input_artifact_ids": (source.shots[0].artifact_id,),
    })
    request = _sample_request(source, shot_id="shot-1", attempt_id="voice-route-current")
    provider = _minimax_provider(request.script_text, sample_marker=request.attempt_id)
    handoff = VoiceAudioHandoff(
        track=AudioTrackSpec(
            track_id="voice-route-current",
            audio_kind=AudioKind.DIALOGUE,
            asset_id=f"voice-{request.attempt_id}",
            shot_id="shot-1",
        ),
        speaker_id="hero",
        voice_request=request,
        voice_preview=provider.preview(request),
        credential_reference_id="MINIMAX_SPEECH_API_KEY",
    )
    context = VoiceRoutingContext(
        final_project_file=(tmp_path / "project.yaml").resolve(),
        audio_handoffs=(handoff,),
    )
    orchestrator, limits, _provider, projection = _orchestrator(
        setup=setup, source_project=source, voice_context=context
    )
    before = orchestrator.prepare(limits=limits)
    native = next(item for item in before.inputs.candidates if item.voice_route.route.value == "native")
    separate = next(item for item in before.inputs.candidates if item.voice_route.route.value == "separate")
    assert "EVIDENCE_REQUIRED" in native.voice_route.readiness.native_blockers
    assert "EVIDENCE_REQUIRED" in separate.voice_route.readiness.separate_blockers

    receipt = _record_identity_review(
        runtime, candidate=separate, handoff=handoff, projection=projection
    )
    current = load_production_project(tmp_path / "project.yaml")
    reviewed_context = context.model_copy(update={"identity_reviews": (receipt,)})
    reprepare, limits, _provider, _projection = _orchestrator(
        setup=setup, source_project=current, voice_context=reviewed_context
    )
    prepared = reprepare.prepare(limits=limits)
    native = next(item for item in prepared.inputs.candidates if item.voice_route.route.value == "native")
    assert prepared.decision.selected_candidate_id is not None, (
        prepared.decision,
        tuple((item.candidate_id, item.voice_route.readiness.separate_blockers)
              for item in prepared.inputs.candidates),
    )
    selected = next(
        item for item in prepared.inputs.candidates
        if item.candidate_id == prepared.decision.selected_candidate_id
    )
    assert "EVIDENCE_REQUIRED" in native.voice_route.readiness.native_blockers
    assert selected.voice_route.route.value == "separate"
    assert "EVIDENCE_REQUIRED" not in selected.voice_route.readiness.separate_blockers
