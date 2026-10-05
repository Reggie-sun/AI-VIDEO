"""Read-only voice feasibility and exact handoff; selection stays in the Router.

Snapshots are replay data, not lifecycle authority. New execution must rebuild
them from the standard project/Registry/Review readers before any effect.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.audio import VoiceGenerationPreview, VoiceGenerationRequest
from ai_video.production.composition_contracts import AudioTrackSpec
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ReviewReceiptPointer
from ai_video.production.voice_routing_contracts import VoiceMode, VoiceRoute

SHA256 = r"^[0-9a-f]{64}$"


def voice_provider_language(language):
    """Exact supported legacy MiniMax language labels; never guess variants."""
    return {"en": "English", "zh": "Chinese"}.get(language)


class VoiceAudioHandoff(StrictModel):
    speaker_id: str = Field(min_length=1)
    track: AudioTrackSpec
    voice_request: VoiceGenerationRequest | None = None
    voice_preview: VoiceGenerationPreview | None = None
    credential_reference_id: str | None = None

    @model_validator(mode="after")
    def _request_pair(self):
        if (self.voice_request is None) != (self.voice_preview is None):
            raise ValueError("voice request and preview must be paired")
        if self.voice_request is not None and (
            self.voice_request.speaker_id != self.speaker_id
            or self.voice_preview.request_fingerprint != self.voice_request.voice_request_fingerprint
        ):
            raise ValueError("voice handoff does not bind the exact request")
        return self


class VoiceRoutingContext(StrictModel):
    """Caller-selected existing execution layout, never permission to create roots."""

    final_project_file: Path
    audio_handoffs: tuple[VoiceAudioHandoff, ...] = ()
    non_speech_tracks: tuple[AudioTrackSpec, ...] = ()
    identity_reviews: tuple[ReviewReceiptPointer, ...] = ()

    @model_validator(mode="after")
    def _identities(self):
        if not self.final_project_file.is_absolute() or self.final_project_file.name != "project.yaml":
            raise ValueError("voice final project must name an absolute canonical project.yaml")
        ids = [h.speaker_id for h in self.audio_handoffs]
        if len(ids) != len(set(ids)):
            raise ValueError("voice handoff speakers must be unique")
        return self


class VoiceRouteReadiness(StrictModel):
    """Immutable observations rebuilt at new execution; no mutable progress."""

    context: VoiceRoutingContext
    source_identity: str = Field(pattern=SHA256)
    final_identity: str = Field(pattern=SHA256)
    native_blockers: tuple[str, ...]
    separate_blockers: tuple[str, ...]
    evidence_hashes: tuple[str, ...] = ()
    pending_voice_requests: tuple[str, ...] = ()
    voice_submits_used: int = Field(default=0, strict=True, ge=0)


class VoiceRouteBinding(StrictModel):
    route: VoiceRoute
    requirement_hash: str = Field(pattern=SHA256)
    readiness: VoiceRouteReadiness | None = None

    @property
    def content_hash(self):
        return canonical_sha256(self.model_dump(mode="json"))

    @property
    def fit_hash(self):
        # Readiness binds an exact execution, not media-quality scope. Budget
        # settlement and fulfilled handoffs cannot invalidate an accepted clip.
        recipes = []
        if self.route is VoiceRoute.SEPARATE and self.readiness is not None:
            for handoff in self.readiness.context.audio_handoffs:
                request = handoff.voice_request
                if request is not None:
                    recipes.append({"speaker": handoff.speaker_id,
                        "provider": request.provider_kind, "model": request.model_id,
                        "parameters": request.provider_parameters_hash,
                        "voice": request.voice_id, "language": request.language,
                        "sample_rate": request.output_sample_rate_hz, "channels": request.output_channels,
                        "endpoint": handoff.voice_preview.destination})
        return canonical_sha256({"route": self.route.value,
            "requirement_hash": self.requirement_hash, "voice_recipes": recipes})


def validate_voice_requirement(requirement) -> None:
    voice = requirement.voice_routing
    if voice != requirement.target_shot.voice_routing:
        raise ValueError("voice routing must match canonical Shot authoring")
    if voice is None:
        return
    if requirement.audio_need.value != voice.audio_need:
        raise ValueError("voice routing conflicts with legacy audio_need")
    shot = requirement.target_shot
    if voice.mode is VoiceMode.NO_VOICE:
        if shot.dialogue or shot.narration:
            raise ValueError("NO_VOICE cannot discard canonical speech")
        return
    texts = tuple(s.script_text for s in voice.speakers)
    canonical = tuple(text for text in (shot.dialogue, shot.narration) if text)
    if texts != canonical:
        raise ValueError("voice speakers must bind exact canonical dialogue/narration")
    if any(s.speaker_id not in shot.character_ids for s in voice.speakers):
        raise ValueError("voice speaker must be a canonical Shot Character")
    dialogue = requirement.generation_intent.dialogue_intent
    if dialogue is None or dialogue.mode != "dialogue":
        raise ValueError("voice routing requires sealed dialogue intent")
    speaker = voice.speakers[0]
    if (dialogue.speaker_id != speaker.speaker_id or dialogue.verbatim_text != speaker.script_text
            or dialogue.language != speaker.language):
        raise ValueError("voice requirement differs from sealed dialogue intent")


def voice_routes(requirement):
    voice = requirement.voice_routing
    if voice is None:
        return (None,)
    return {
        VoiceMode.AUTO: (VoiceRoute.NATIVE, VoiceRoute.SEPARATE),
        VoiceMode.NATIVE_REQUIRED: (VoiceRoute.NATIVE,),
        VoiceMode.SEPARATE_REQUIRED: (VoiceRoute.SEPARATE,),
        VoiceMode.NO_VOICE: (VoiceRoute.NO_VOICE,),
    }[voice.mode]


def _project_identity(project):
    manifest = project.manifest
    return canonical_sha256({
        "project": manifest.active_project.model_dump(mode="json"),
        "registry": manifest.active_registry.model_dump(mode="json"),
        "schema": manifest.schema_version,
        # The Budget Guard owns current reservations/settlement. Including its
        # mutable pointer would invalidate the video at its own permit gate.
        # Accounting-layout compatibility is rebuilt separately below.
        "qa": manifest.active_qa_policy.model_dump(mode="json") if manifest.active_qa_policy else None,
    })


def _voice_identity_evidence(final, context, speaker, candidate, route, requirement):
    """Only current QA-owned human evidence can qualify a fixed voice.

    The measured extension binds the exact reference, language and execution
    recipe. A model, seed or voice_id alone never supplies a passing finding.
    """
    from ai_video.production.project import load_review_evidence, load_review_receipt

    # Current native compilers expose no exact speaker/reference control. Even
    # a listening result cannot turn a TTS voice_id into such a native binding.
    if route is VoiceRoute.NATIVE:
        return None

    variant = next(v for v in candidate.capabilities.variants if v.capability_id == candidate.capability_id)
    for pointer in context.identity_reviews:
        if pointer not in final.manifest.active_review_receipts:
            continue
        receipt = load_review_receipt(final.root, pointer)
        if receipt.verdict.value != "pass" or receipt.qa_policy != final.manifest.active_qa_policy:
            continue
        for evidence_pointer in receipt.evidence:
            evidence = load_review_evidence(final.root, evidence_pointer)
            payload = evidence.measured_payload.get("voice_identity")
            if (not isinstance(payload, dict) or evidence.strength.value != "human"
                    or evidence.measurement_contract_version != "voice-identity/1"
                    or evidence.layer.value != "semantic" or final.qa_policy is None
                    or evidence.tool_identity not in final.qa_policy.semantic_authorities):
                continue
            if speaker.reference_asset_id is not None and speaker.reference_asset_id not in evidence.subject_ids:
                continue
            expected = {
                "contract_version": "voice-identity/1", "route": route.value,
                "speaker_id": speaker.speaker_id, "language": speaker.language,
                "voice_id": speaker.voice_id, "reference_sha256": speaker.reference_sha256,
                "provider_name": candidate.capabilities.provider_name,
                "model_id": variant.model_id, "profile_sha256": candidate.provider_profile.profile_sha256,
                "compiler_hash": candidate.compiler_contract.compiler_hash,
                "character_hashes": {c.character_id: c.content_hash for c in requirement.characters},
                "listening_speed_milli": 1000,
            }
            if route is VoiceRoute.SEPARATE:
                handoff = next((h for h in context.audio_handoffs if h.speaker_id == speaker.speaker_id), None)
                if handoff is None or handoff.voice_request is None or handoff.voice_preview is None:
                    continue
                expected.update(voice_model_id=handoff.voice_request.model_id,
                    voice_parameters_hash=handoff.voice_request.provider_parameters_hash,
                    voice_endpoint=handoff.voice_preview.destination)
            artifacts = payload.get("artifact_sha256s", ())
            findings = payload.get("findings", {})
            if (all(payload.get(k) == v for k, v in expected.items())
                    and isinstance(artifacts, (list, tuple)) and all(isinstance(a, str) for a in artifacts)
                    and len(set(artifacts)) >= 2
                    and _separate_identity_samples(final, evidence, artifacts, speaker, handoff)
                    and findings == {"voice_identity": "PASS", "language": "PASS", "scope": "PASS"}):
                return evidence_pointer.content_hash
    return None


def _separate_identity_samples(final, evidence, artifacts, speaker, handoff):
    """Reopen real same-layout voice requests, rather than trusting payload labels."""
    from ai_video.production._voice_project_reader import read_canonical_voice_model

    shot_ids = set()
    for sha in artifacts:
        asset = next((a for a in final.registry.assets if a.sha256 == sha), None)
        if (asset is None or asset.source_kind.value != "generated" or asset.audio_metadata is None
                or asset.egress is None or asset.asset_id not in evidence.subject_ids):
            return False
        metadata = asset.audio_metadata
        attempt = next((a for a in final.manifest.attempts if a.status.value == "succeeded"
                        and a.voice_request is not None
                        and a.voice_request.request_fingerprint == asset.egress.request_fingerprint), None)
        if attempt is None:
            return False
        request, _ = read_canonical_voice_model(final.root, attempt.attempt_id,
                                                "request.json", VoiceGenerationRequest)
        expected = handoff.voice_request
        if (request.voice_request_fingerprint != attempt.voice_request.request_fingerprint
                or asset.asset_id != f"voice-{attempt.attempt_id}"
                or request.provider_kind != expected.provider_kind or request.model_id != expected.model_id
                or request.provider_parameters_hash != expected.provider_parameters_hash
                or attempt.voice_request.destination != handoff.voice_preview.destination
                or request.speaker_id != speaker.speaker_id or request.voice_id != expected.voice_id
                or request.language != expected.language or metadata.voice_id != request.voice_id
                or metadata.script_hash != request.script_hash or metadata.language != request.language
                or metadata.speaker_id != request.speaker_id):
            return False
        samples = [s for s in final.shots if s.artifact_id in request.input_artifact_ids
                   and s.shot_id in evidence.subject_ids and speaker.speaker_id in s.character_ids
                   and request.script_text in (s.dialogue, s.narration)]
        if len(samples) != 1:
            return False
        shot_ids.add(samples[0].shot_id)
    return len(shot_ids) >= 2


def build_voice_readiness(*, source, requirement, candidate, context, generation_id,
                          task_id=None, voice_attempt_id=None):
    """Read existing layout and registered bytes. No secret lookup or Provider call."""
    from ai_video.production.project import load_production_project

    final = load_production_project(context.final_project_file)
    native, separate, evidence, pending = [], [], [], []
    # Only durable Router provenance for this task counts.  Historical voice
    # samples and another task's effects cannot consume this task's ceiling.
    voice_submits_used = sum(1 for a in source.manifest.attempts
        if task_id is not None and a.voice_request is not None and a.paid_provider_state is not None
        and a.paid_provider_state.submit_receipt is not None
        and a.voice_request.routing_task_id == task_id)
    voice = requirement.voice_routing
    if voice is None:
        raise ValueError("voice readiness requires an authored voice requirement")
    from ai_video.production.manifest_schema import ManifestCapability, manifest_supports

    if (not manifest_supports(source.manifest.schema_version, ManifestCapability.VIDEO_GENERATION)
            or source.manifest.active_dependency_graph is None or source.dependency_graph is None
            or source.manifest.active_qa_policy is None or source.qa_policy is None):
        native.append("VIDEO_EXECUTION_LAYOUT_UNSUPPORTED")
        separate.append("VIDEO_EXECUTION_LAYOUT_UNSUPPORTED")
    source_shot = next((s for s in source.shots if s.shot_id == requirement.target_shot.shot_id), None)
    if source_shot != requirement.target_shot:
        native.append("SOURCE_SHOT_NOT_CURRENT")
        separate.append("SOURCE_SHOT_NOT_CURRENT")
    final_shot = next((s for s in final.shots if s.shot_id == requirement.target_shot.shot_id), None)
    if (final_shot is None or final_shot.voice_routing != voice
            or final_shot.dialogue != requirement.target_shot.dialogue
            or final_shot.narration != requirement.target_shot.narration
            or final_shot.character_ids != requirement.target_shot.character_ids):
        native.append("FINAL_SHOT_NOT_CURRENT")
        separate.append("FINAL_SHOT_NOT_CURRENT")
    variant = next(v for v in candidate.capabilities.variants if v.capability_id == candidate.capability_id)
    for project in (source, final):
        for attempt in project.manifest.attempts:
            if attempt.status.value == "outcome_unknown":
                native.append("UNKNOWN_OUTCOME")
                separate.append("UNKNOWN_OUTCOME")
            elif attempt.status.value == "running":
                # The current video intent may be reopened at its own submit
                # gate. It never permits a subsequent same-Manifest voice call.
                own_video = (project.root == source.root and attempt.video_generation_state is not None
                    and attempt.video_generation_state.request.generation_id == generation_id)
                own_voice = (project.root == source.root and attempt.attempt_id == voice_attempt_id
                             and attempt.voice_request is not None)
                if not own_video and not own_voice:
                    native.append("UNRESOLVED_LAYOUT_ATTEMPT")
                    separate.append("UNRESOLVED_LAYOUT_ATTEMPT")
    if voice.native_sound_required:
        separate.append("NATIVE_SOUND_REQUIRED")
    if (variant.execution_kind.value != "remote" or variant.billing_kind.value != "metered"
            or final.manifest.schema_version not in {"2.0", "2.1", "2.2"}
            or final.registry.schema_version != "2.1"):
        native.append("NATIVE_AUDIO_HANDOFF_UNSUPPORTED")
    if final.root != source.root:
        separate.append("GENERATED_VOICE_CROSS_PROJECT_HANDOFF_UNSUPPORTED")
    budget = None
    if source.manifest.active_paid_provider_budget is not None:
        from ai_video.production._paid_provider_project_reader import load_paid_provider_budget

        budget = load_paid_provider_budget(source.root, source.manifest.active_paid_provider_budget)
        if variant.execution_kind.value == "remote" and budget.voice_batch_submit_limit is not None:
            native.append("VOICE_VIDEO_LEDGER_INCOMPATIBLE")
            separate.append("VOICE_VIDEO_LEDGER_INCOMPATIBLE")
    intent = requirement.generation_intent
    dialogue = intent.dialogue_intent
    if dialogue and (dialogue.on_screen or dialogue.lip_sync_required):
        separate.append("SEPARATE_SYNCHRONIZATION_UNSUPPORTED")
    covered_kinds = set()
    for track in context.non_speech_tracks:
        asset = next((a for a in final.registry.assets if a.asset_id == track.asset_id), None)
        if (asset is not None and asset.audio_metadata is not None
                and asset.audio_metadata.audio_kind == track.audio_kind
                and track.audio_kind.value in {"ambience", "sfx", "bgm"}):
            covered_kinds.add(track.audio_kind.value)
    needed_kinds = set()
    if intent.ambience_intent and not intent.ambience_intent.explicitly_silent:
        needed_kinds.add("ambience")
        if intent.ambience_intent.foley_cues:
            needed_kinds.add("sfx")
    if intent.music_intent and intent.music_intent.mode != "none":
        needed_kinds.add("bgm")
    if not needed_kinds <= covered_kinds:
        separate.append("NON_SPEECH_COVERAGE_REQUIRED")
    for speaker in voice.speakers:
        if speaker.reference_asset_id is not None and not any(
            a.asset_id == speaker.reference_asset_id and a.sha256 == speaker.reference_sha256
            for a in final.registry.assets
        ):
            native.append("VOICE_REFERENCE_NOT_CURRENT")
            separate.append("VOICE_REFERENCE_NOT_CURRENT")
        if speaker.consistency == "cross_shot_fixed" or speaker.reference_asset_id:
            for route, blockers in ((VoiceRoute.NATIVE, native), (VoiceRoute.SEPARATE, separate)):
                # A configured separate voice_id needs no cross-Shot proof
                # for an unconstrained single Shot. Native cannot pretend a
                # TTS voice_id is a bindable native control.
                if route is VoiceRoute.SEPARATE and speaker.consistency == "single_shot" and speaker.reference_asset_id is None:
                    continue
                proof = _voice_identity_evidence(final, context, speaker, candidate, route, requirement)
                if proof is None:
                    blockers.append("EVIDENCE_REQUIRED")
                else:
                    evidence.append(proof)
        handoff = next((h for h in context.audio_handoffs if h.speaker_id == speaker.speaker_id), None)
        if handoff is None:
            native.append("AUDIO_TRACK_HANDOFF_REQUIRED")
            separate.append("AUDIO_TRACK_HANDOFF_REQUIRED")
            continue
        if handoff.track.audio_kind.value not in {"dialogue", "narration"}:
            native.append("AUDIO_TRACK_KIND_CONFLICT")
            separate.append("AUDIO_TRACK_KIND_CONFLICT")
        if handoff.track.shot_id != requirement.target_shot.shot_id:
            native.append("AUDIO_TRACK_SHOT_CONFLICT")
            separate.append("AUDIO_TRACK_SHOT_CONFLICT")
        track = handoff.track
        if (track.trim_start_sample != 0 or track.trim_duration_samples is not None
                or track.gain_millidb != 0 or track.fade_in_samples != 0
                or track.fade_out_samples != 0 or track.ducking is not None):
            native.append("VOICE_SIGNAL_TRANSFORM_UNQUALIFIED")
            separate.append("VOICE_SIGNAL_TRANSFORM_UNQUALIFIED")
        request, preview = handoff.voice_request, handoff.voice_preview
        if request is None or preview is None:
            separate.append("EXACT_VOICE_REQUEST_REQUIRED")
            continue
        if (request.provider_kind != "minimax-speech" or request.script_hash != speaker.script_hash
                or request.speaker_id != speaker.speaker_id
                or request.language != voice_provider_language(speaker.language)
                or handoff.track.asset_id != f"voice-{request.attempt_id}"
                or request.audio_kind != handoff.track.audio_kind
                or not speaker.voice_id or request.voice_id != speaker.voice_id
                or preview.destination not in {"https://api.minimaxi.com", "https://api.minimax.io"}
                or not handoff.credential_reference_id or not preview.timing_supported or not preview.output_supported):
            separate.append("VOICE_REQUEST_OR_CAPABILITY_CONFLICT")
        asset = next((a for a in final.registry.assets if a.asset_id == handoff.track.asset_id), None)
        existing = next((a for a in source.manifest.attempts if a.attempt_id == request.attempt_id), None)
        if existing is not None and existing.status.value in {"failed", "interrupted"}:
            native.append("VOICE_RUNTIME_FAILURE")
            separate.append("VOICE_RUNTIME_FAILURE")
        if asset is not None:
            if (asset.source_kind.value != "generated" or asset.audio_metadata is None
                    or asset.egress is None or asset.egress.request_fingerprint != request.voice_request_fingerprint
                    or asset.audio_metadata.script_hash != speaker.script_hash
                    or asset.audio_metadata.speaker_id != speaker.speaker_id
                    or asset.audio_metadata.language != voice_provider_language(speaker.language)
                    or asset.audio_metadata.audio_kind != request.audio_kind
                    or asset.audio_metadata.voice_id != request.voice_id
                    or existing is None or existing.status.value != "succeeded"):
                separate.append("REGISTERED_VOICE_IDENTITY_CONFLICT")
            if (asset.audio_metadata is not None and dialogue is not None
                    and dialogue.start_seconds is not None and dialogue.end_seconds is not None
                    and asset.audio_metadata.duration_samples >
                    (dialogue.end_seconds - dialogue.start_seconds) * asset.audio_metadata.sample_rate_hz):
                separate.append("VOICE_DURATION_EXCEEDS_DIALOGUE_WINDOW")
        else:
            pending.append(request.voice_request_fingerprint)
            if existing is not None and existing.attempt_id != voice_attempt_id:
                separate.append("VOICE_EXISTING_ATTEMPT_REQUIRES_RECOVERY")
            if (request.base_project != source.manifest.active_project
                    or request.base_registry != source.manifest.active_registry):
                separate.append("VOICE_REQUEST_BASE_STALE")
            count_based = preview.policy_decision == "standing_minimax_speech_batch"
            if (count_based and variant.execution_kind.value == "remote"
                    or budget is not None and count_based != (budget.voice_batch_submit_limit is not None)):
                separate.append("VOICE_VIDEO_LEDGER_INCOMPATIBLE")
    return VoiceRouteReadiness(context=context, source_identity=_project_identity(source),
        final_identity=_project_identity(final), native_blockers=tuple(sorted(set(native))),
        separate_blockers=tuple(sorted(set(separate))), evidence_hashes=tuple(sorted(set(evidence))),
        pending_voice_requests=tuple(pending), voice_submits_used=voice_submits_used)


def route_blockers(requirement, candidate):
    binding = candidate.voice_route
    voice = requirement.voice_routing
    if voice is None:
        return () if binding is None else ("UNAUTHORED_VOICE_ROUTE",)
    if binding is None or binding.requirement_hash != voice.content_hash:
        return ("VOICE_ROUTE_BINDING_REQUIRED",)
    if binding.route not in voice_routes(requirement):
        return ("USER_VOICE_ROUTE_CONSTRAINT",)
    if len(voice.speakers) > 1:
        return ("MULTISPEAKER_COMPILER_UNSUPPORTED",)
    expected_audio = (binding.route is VoiceRoute.NATIVE or
                      binding.route is VoiceRoute.NO_VOICE and voice.native_sound_required)
    if binding.route is not VoiceRoute.NO_VOICE and candidate.output_requirement.native_audio != expected_audio:
        return ("VOICE_ROUTE_OUTPUT_CONFLICT",)
    if binding.route is VoiceRoute.NO_VOICE:
        intent = requirement.generation_intent
        has_audio = bool(voice.native_sound_required
            or intent.ambience_intent and not intent.ambience_intent.explicitly_silent
            or intent.music_intent and intent.music_intent.mode != "none")
        return ("NO_VOICE_COVERAGE_REQUIRED",) if has_audio else ()
    if binding.readiness is None:
        return ("VOICE_READINESS_REQUIRED",)
    # Only the actual compiler family that implements route projection can be
    # admitted. Other registered adapters remain explicit capability gaps.
    compiler = candidate.compiler_contract
    if (compiler.compiler_id, compiler.compiler_version) not in {
        ("vidu-video-compiler", "3"), ("seedance-video-compiler", "2")
    }:
        return ("VOICE_COMPILER_UNSUPPORTED",)
    return (binding.readiness.native_blockers if binding.route is VoiceRoute.NATIVE
            else binding.readiness.separate_blockers)


def expand_voice_candidates(candidate, *, requirement, source=None, context=None, generation_id=None,
                            task_id=None):
    """Enumerate, never select. Keep legacy candidate bytes/IDs unchanged."""
    if requirement.voice_routing is None:
        return (candidate,)
    result = []
    readiness = None
    if source is not None and context is not None:
        context = VoiceRoutingContext.model_validate(context)
        readiness = build_voice_readiness(source=source, requirement=requirement, candidate=candidate,
            context=context, generation_id=generation_id, task_id=task_id)
    for route in voice_routes(requirement):
        output = candidate.output_requirement
        if route is not VoiceRoute.NO_VOICE:
            output = output.model_copy(update={"native_audio": route is VoiceRoute.NATIVE})
        result.append(candidate.model_copy(update={
            "candidate_id": f"{candidate.candidate_id}/voice-{route.value}",
            "output_requirement": output,
            "voice_route": VoiceRouteBinding(route=route,
                requirement_hash=requirement.voice_routing.content_hash, readiness=readiness),
        }))
    return tuple(result)


def validate_voice_compilation(requirement, bound, native_prompt, *, continuity_expression=None):
    """Fail closed even when an adapter is called outside the orchestrator."""
    voice, binding = requirement.voice_routing, bound.voice_route
    if voice is None:
        return () if binding is None else ("voice_route",)
    if (binding is None or binding.requirement_hash != voice.content_hash
            or binding.route not in voice_routes(requirement)):
        return ("voice_route",)
    if binding.route is not VoiceRoute.NO_VOICE and (
        bound.output_requirement.native_audio != (binding.route is VoiceRoute.NATIVE)
    ):
        return ("voice_route.output",)
    if native_prompt is None:
        return ("voice_route.native_prompt",)
    if binding.route is VoiceRoute.NATIVE and (
            binding.readiness is None or binding.readiness.native_blockers):
        return ("voice_route.readiness",)
    if binding.route is VoiceRoute.SEPARATE:
        if (voice.native_sound_required or binding.readiness is None
                or binding.readiness.separate_blockers):
            return ("voice_route.readiness",)
        # Compare with the exact compiler output rather than searching for
        # script substrings (a short utterance can also be legitimate visuals).
        from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt
        expected = compile_remote_video_prompt(requirement, voice_route=binding,
            provider_bound=bound, continuity_expression=continuity_expression)
        if (expected.outcome != "compiled" or expected.prompt_text != native_prompt.prompt_text
                or expected.prompt_sha256 != native_prompt.prompt_sha256
                or expected.expressed_control_paths != native_prompt.expressed_control_paths):
            return ("voice_route.native_prompt",)
    return ()


def voice_expression_recipe(recipe, requirement, binding):
    if binding is None or binding.route is not VoiceRoute.SEPARATE:
        return recipe
    # Remove only lexical speech obligations delegated to the exact voice
    # request. The persisted recipe and final acceptance inventory stay intact.
    dialogue = requirement.generation_intent.dialogue_intent
    delegated = {dialogue.verbatim_text, dialogue.language, dialogue.speaker_id}
    delegated_paths = {f"generation_intent.dialogue_intent.{name}"
                       for name in ("verbatim_text", "language", "speaker_id")}
    expressions = tuple(item.model_copy(update={
        "native_text": tuple(text for text in item.native_text if text not in delegated)
    }) if item.intent_paths and set(item.intent_paths) <= delegated_paths else item
        for item in recipe.expressions)
    return recipe.model_copy(update={"expressions": expressions})


def validate_voice_execution(binding, source, *, preparing_voice=False, voice_attempt_id=None):
    candidate = next(c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id)
    route = candidate.voice_route
    if route is None:
        raise ValueError("voice route was removed from execution")
    if route.route is VoiceRoute.NO_VOICE:
        if route_blockers(binding.projection.requirement, candidate):
            raise ValueError("NO_VOICE cannot discard audio coverage")
        return
    if route.readiness is None:
        raise ValueError("voice execution requires current readiness")
    own_voice_attempt_id = (
        voice_attempt_id
        if any(
            handoff.voice_request is not None
            and handoff.voice_request.attempt_id == voice_attempt_id
            for handoff in route.readiness.context.audio_handoffs
        )
        else None
    )
    current = build_voice_readiness(source=source, requirement=binding.projection.requirement,
        candidate=candidate, context=route.readiness.context, generation_id=binding.lifecycle.generation_id,
        task_id=binding.inputs.limits.task_id, voice_attempt_id=own_voice_attempt_id)
    if current != route.readiness or route_blockers(binding.projection.requirement, candidate):
        raise ValueError("voice routing evidence or execution layout is stale")
    submitted_attempt_ids = {
        attempt.attempt_id
        for attempt in source.manifest.attempts
        if (
            attempt.voice_request is not None
            and attempt.voice_request.routing_task_id == binding.inputs.limits.task_id
            and attempt.paid_provider_state is not None
            and attempt.paid_provider_state.submit_receipt is not None
        )
    }
    from ai_video.production._video_project_reader import load_generation_execution_binding

    for attempt in source.manifest.attempts:
        state = attempt.video_generation_state
        if (
            state is None
            or state.execution_binding is None
            or attempt.paid_provider_state is None
            or attempt.paid_provider_state.submit_receipt is None
        ):
            continue
        prior_video = load_generation_execution_binding(source.root, state.execution_binding)
        if prior_video.inputs.limits.task_id == binding.inputs.limits.task_id:
            submitted_attempt_ids.add(attempt.attempt_id)
    if len(submitted_attempt_ids) > binding.inputs.limits.paid_submits_used:
        raise ValueError("voice routing task submit usage exceeds the sealed execution limit")
    if current.voice_submits_used:
        from ai_video.production._voice_project_reader import read_canonical_voice_model
        from ai_video.production.voice_routing_execution import VoiceRoutingExecutionEnvelope

        prior_ceilings = []
        for attempt in source.manifest.attempts:
            receipt = attempt.voice_request
            if (
                receipt is None
                or receipt.routing_task_id != binding.inputs.limits.task_id
                or receipt.routing_binding_hash is None
                or attempt.paid_provider_state is None
                or attempt.paid_provider_state.submit_receipt is None
            ):
                continue
            prior_envelope, _ = read_canonical_voice_model(
                source.root,
                attempt.attempt_id,
                "routing-binding.json",
                VoiceRoutingExecutionEnvelope,
            )
            prior = prior_envelope.binding
            if (
                prior_envelope.envelope_hash != receipt.routing_binding_hash
                or prior.inputs.limits.task_id != receipt.routing_task_id
            ):
                raise ValueError("prior voice route task provenance is invalid")
            prior_ceilings.append(prior.inputs.limits.paid_submit_ceiling)
        if prior_ceilings and (
            binding.inputs.limits.paid_submit_ceiling > min(prior_ceilings)
        ):
            raise ValueError("voice routing task submit ceiling cannot increase after a voice submit")
    if route.route is VoiceRoute.SEPARATE and current.pending_voice_requests and not preparing_voice:
        raise ValueError("complete the exact voice handoff before preparing a video intent; replan from current Registry")


def validate_routed_voice_handoff(binding, request, preview) -> None:
    """Require one sealed SEPARATE handoff before the voice committer acts."""

    candidate = next((item for item in binding.inputs.candidates
                      if item.candidate_id == binding.decision.selected_candidate_id), None)
    route = candidate.voice_route if candidate is not None else None
    if route is None or route.route is not VoiceRoute.SEPARATE or route.readiness is None:
        raise ValueError("voice execution binding does not select an exact SEPARATE route")
    handoff = next((item for item in route.readiness.context.audio_handoffs
                    if item.speaker_id == request.speaker_id), None)
    if (handoff is None or handoff.voice_request != request or handoff.voice_preview != preview
            or request.voice_request_fingerprint not in route.readiness.pending_voice_requests):
        raise ValueError("voice execution binding does not contain the exact pending handoff")


def validate_routed_paid_voice_preview(binding, voice_preview, paid_preview) -> None:
    """Bind the paid gate to the sealed handoff's credential and price preview."""

    candidate = next((item for item in binding.inputs.candidates
                      if item.candidate_id == binding.decision.selected_candidate_id), None)
    route = candidate.voice_route if candidate is not None else None
    if route is None or route.readiness is None:
        raise ValueError("voice execution binding has no sealed handoff")
    handoff = next((item for item in route.readiness.context.audio_handoffs
                    if item.voice_preview == voice_preview), None)
    request = handoff.voice_request if handoff is not None else None
    if (
        handoff is None
        or request is None
        or paid_preview.operation != "voice_generation"
        or paid_preview.request_fingerprint != request.voice_request_fingerprint
        or paid_preview.provider_kind != request.provider_kind
        or paid_preview.model_id != request.model_id
        or paid_preview.destination != voice_preview.destination
        or paid_preview.currency != voice_preview.currency
        or paid_preview.estimated_cost_upper_bound_microunits
        != voice_preview.estimated_cost_upper_bound_microunits
        or paid_preview.secret_reference.kind != voice_preview.credential_reference_kind
        or paid_preview.secret_reference.reference_id != handoff.credential_reference_id
    ):
        raise ValueError("paid voice preview does not match the sealed route handoff")
