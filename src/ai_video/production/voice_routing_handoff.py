"""Voice-route consumers at existing voice, generated-audio and P4 boundaries."""

from ai_video.production.voice_routing_contracts import VoiceMode, VoiceRoute


def selected_voice_handoffs(prepared):
    routing = prepared.decision.routing
    bound = routing.provider_bound_request if routing is not None else None
    route = bound.voice_route if bound is not None else None
    if route is None or route.readiness is None:
        return ()
    return route.readiness.context.audio_handoffs


def generate_selected_voice(orchestrator, *, committer, prepared, speaker_id, provider,
                            authorization, paid_preview, video_paid_preview=None,
                            dependency_transition_preparer=None):
    """Delegate one exact selected handoff to the sole voice lifecycle owner.

    The caller supplies the existing authorized Provider/permit infrastructure;
    routing never buys access, looks up credentials, creates a root, or retries.
    After activation the caller prepares again from the changed Registry.
    """
    if not callable(getattr(committer, "_voice_candidate_preparer", None)):
        raise ValueError("selected voice execution requires the existing candidate materializer")
    from ai_video.production.manifest_schema import ManifestCapability, manifest_supports

    current = orchestrator.prepare(limits=prepared.inputs.limits)
    if current.decision != prepared.decision or current.execution_binding is None:
        raise ValueError("selected voice handoff is stale or not executable")
    route = current.decision.routing.provider_bound_request.voice_route
    if route is None or route.route is not VoiceRoute.SEPARATE or route.readiness is None:
        raise ValueError("voice generation requires an exact SEPARATE decision")
    context = route.readiness.context
    if context.final_project_file.parent.resolve() != committer.project_root.resolve():
        raise ValueError("voice handoff cannot change the selected execution layout")
    from ai_video.production.project import load_production_project
    from ai_video.production.voice_routing import build_voice_readiness, route_blockers

    source = load_production_project(context.final_project_file)
    if (manifest_supports(source.manifest.schema_version, ManifestCapability.DEPENDENCY_GRAPH)
            and dependency_transition_preparer is None):
        raise ValueError("selected voice execution requires its dependency transition preparer")
    if any(a.status.value in {"running", "outcome_unknown"} for a in source.manifest.attempts):
        raise ValueError("voice admission requires a resolved Manifest before any voice effect")
    candidate = next(c for c in current.inputs.candidates
                     if c.candidate_id == current.decision.selected_candidate_id)
    observed = build_voice_readiness(source=source,
        requirement=current.execution_binding.projection.requirement, candidate=candidate,
        context=context, generation_id=current.execution_binding.lifecycle.generation_id,
        task_id=current.inputs.limits.task_id)
    if observed != route.readiness or route_blockers(current.execution_binding.projection.requirement, candidate):
        raise ValueError("selected voice handoff is not current in the canonical project")
    from ai_video.production.video_pre_generation import verify_current_video_generation_lineage

    current.execution_binding.validate_current_project(source, preparing_voice=True)
    verify_current_video_generation_lineage(source, current.execution_binding.compiled_request)
    committer._require_current_generation_acceptance(source, current.execution_binding)
    handoff = next((h for h in selected_voice_handoffs(current) if h.speaker_id == speaker_id), None)
    if handoff is None or handoff.voice_request is None or handoff.voice_preview is None:
        raise ValueError("selected voice handoff has no exact request")
    request = handoff.voice_request
    if request.voice_request_fingerprint not in route.readiness.pending_voice_requests:
        # Already registered voices are consumed by P4. Do not invoke an old
        # request again merely because a video component still needs work.
        raise ValueError("selected voice is already registered; reprepare the video")
    if provider.preview(request) != handoff.voice_preview:
        raise ValueError("selected voice Provider preview changed")
    if (paid_preview.secret_reference.reference_id != handoff.credential_reference_id
            or paid_preview.secret_reference.kind != handoff.voice_preview.credential_reference_kind):
        raise ValueError("selected voice credential reference changed")
    _require_joint_monetary_budget(committer, source, current, paid_preview, video_paid_preview)
    from ai_video.production.voice_routing_execution import VoiceRoutingExecutionEnvelope

    if video_paid_preview is None:
        raise ValueError("SEPARATE requires the selected video preview before voice execution")
    envelope = VoiceRoutingExecutionEnvelope.create(
        binding=current.execution_binding,
        video_preview=current.provider.preview(current.resolved_request),
        video_paid_preview=video_paid_preview,
    )
    return committer.generate_voice_asset(request, provider, authorization,
        paid_preview=paid_preview, dependency_transition_preparer=dependency_transition_preparer,
        routing_execution_envelope=envelope)


def _require_joint_monetary_budget(committer, source, prepared, voice_preview, video_paid_preview):
    """Dry-run the existing Budget Guard for both components; never write a ledger."""
    from ai_video.production.paid_provider import reserve_paid_provider_budget, validate_paid_provider_authorization
    from ai_video.production._paid_provider_project_reader import load_paid_provider_budget
    from ai_video.production.video import build_video_paid_permit_binding

    authorizer = getattr(committer, "_paid_provider_authorizer", None)
    if video_paid_preview is None or not callable(authorizer):
        raise ValueError("SEPARATE requires the selected video preview and shared budget authorization before voice")
    voice_authorization = authorizer(voice_preview)
    video_authorization = authorizer(video_paid_preview)
    if voice_authorization is None or video_authorization is None:
        raise ValueError("both selected components require existing budget authorization")
    now = committer._paid_provider_clock()
    validate_paid_provider_authorization(voice_preview, voice_authorization, now=now)
    validate_paid_provider_authorization(video_paid_preview, video_authorization, now=now)
    preview = prepared.provider.preview(prepared.resolved_request)
    build_video_paid_permit_binding(prepared.resolved_request, preview,
                                   video_paid_preview, video_authorization)
    # This prospective video preview is not a permit and cannot be submitted
    # after voice activation. Reprepare must bind the changed Registry anew.
    budget = (load_paid_provider_budget(source.root, source.manifest.active_paid_provider_budget)
              if source.manifest.active_paid_provider_budget is not None else None)
    budget, _ = reserve_paid_provider_budget(budget, preview=voice_preview,
        authorization=voice_authorization, reservation_id=f"voice-route-{voice_preview.attempt_id}")
    reserve_paid_provider_budget(budget, preview=video_paid_preview,
        authorization=video_authorization, reservation_id=f"voice-route-{video_paid_preview.attempt_id}")


def require_native_audio_handoff(source, request, target_root):
    """Protect new routed speech metadata before extraction; legacy stays exact."""
    from ai_video.production._video_project_reader import load_generation_execution_binding

    attempt = next(a for a in source.manifest.attempts if a.attempt_id == request.source_attempt_id)
    pointer = attempt.video_generation_state.execution_binding
    if pointer is None:
        return
    binding = load_generation_execution_binding(source.root, pointer)
    voice = binding.projection.requirement.voice_routing
    if voice is None:
        return
    route = binding.decision.routing.provider_bound_request.voice_route
    if route is None or route.route is not VoiceRoute.NATIVE or route.readiness is None:
        raise ValueError("generated video audio is not the selected voice source")
    context = route.readiness.context
    if context.final_project_file.parent.resolve() != target_root.resolve():
        raise ValueError("native audio cannot change the sealed final project")
    from ai_video.production.project import load_production_project

    final = load_production_project(context.final_project_file)
    shot = next((s for s in final.shots if s.shot_id == binding.context.target_shot_id), None)
    authored = binding.projection.requirement.target_shot
    if (shot is None or shot.voice_routing != voice or shot.dialogue != authored.dialogue
            or shot.narration != authored.narration or shot.character_ids != authored.character_ids):
        raise ValueError("native audio final authoring changed before extraction")
    speaker = next((s for s in voice.speakers if s.speaker_id == request.speaker_id), None)
    handoff = next((h for h in context.audio_handoffs if h.speaker_id == request.speaker_id), None)
    if speaker is None or handoff is None or (
        request.asset_id != handoff.track.asset_id
        or request.audio_kind != handoff.track.audio_kind
        or request.script_hash != speaker.script_hash
        or request.language != speaker.language
        or request.voice_id != (speaker.voice_id if speaker.consistency == "cross_shot_fixed" and speaker.voice_id
            else f"native-{binding.lifecycle.generation_id}-{speaker.speaker_id}")
    ):
        raise ValueError("native audio identity differs from the selected exact handoff")


def require_voice_composition(project, spec, timeline):
    """Consume the selected exact handoff on the sole canonical P4 timeline."""
    from ai_video.production.project import load_production_project
    from ai_video.production._video_project_reader import load_generation_execution_binding
    from ai_video.production.voice_routing import voice_provider_language, _voice_identity_evidence

    assets = {a.asset_id: a for a in project.registry.assets}
    included = {span.shot_id for span in timeline.visual_spans}
    for shot in project.shots:
        voice = shot.voice_routing
        if voice is None or shot.shot_id not in included:
            continue
        tracks = [t for t in spec.audio_tracks if t.shot_id == shot.shot_id]
        if voice.mode is VoiceMode.NO_VOICE:
            if any(t.audio_kind.value in {"dialogue", "narration"} for t in tracks):
                raise ValueError("NO_VOICE composition contains speech")
            continue
        source_ref = next((s for s in spec.voice_sources if s.shot_id == shot.shot_id), None)
        if source_ref is None:
            raise ValueError("voice composition requires the selected execution binding")
        source = load_production_project(source_ref.source_project_file)
        binding = load_generation_execution_binding(source.root, source_ref.execution_binding)
        attempt = next((a for a in source.manifest.attempts if a.video_generation_state is not None
                        and a.video_generation_state.execution_binding == source_ref.execution_binding), None)
        if (attempt is None or attempt.status.value in {"failed", "interrupted", "outcome_unknown"}
                or binding.projection.requirement.target_shot.shot_id != shot.shot_id
                or binding.projection.requirement.voice_routing != voice):
            raise ValueError("voice composition source is not the exact selected video attempt")
        fetch = attempt.video_generation_state.fetch_receipt
        visuals = [s for s in timeline.visual_spans if s.shot_id == shot.shot_id]
        if fetch is None or not any(s.asset_sha256 == fetch.artifact_sha256 for s in visuals):
            raise ValueError("voice composition requires the exact fetched video on the timeline")
        route = binding.decision.routing.provider_bound_request.voice_route
        if route is None or route.readiness is None:
            raise ValueError("voice composition source has no sealed audio handoff")
        context = route.readiness.context
        if context.final_project_file.resolve() != (project.root / "project.yaml").resolve():
            raise ValueError("voice composition changed the sealed final project")
        for non_speech in context.non_speech_tracks:
            if non_speech not in spec.audio_tracks:
                raise ValueError("voice composition discarded a required non-speech track")
        visual = [s for s in timeline.visual_spans if s.shot_id == shot.shot_id]
        shot_start = min(s.start_sample for s in visual)
        shot_end = max(s.start_sample + s.duration_samples for s in visual)
        dialogue = binding.projection.requirement.generation_intent.dialogue_intent
        expected_speech_ids = set()
        for speaker in voice.speakers:
            if speaker.consistency == "cross_shot_fixed" or speaker.reference_asset_id is not None:
                candidate = next(c for c in binding.inputs.candidates
                                 if c.candidate_id == binding.decision.selected_candidate_id)
                if _voice_identity_evidence(project, context, speaker, candidate,
                        route.route, binding.projection.requirement) is None:
                    raise ValueError("voice composition requires current fixed-voice evidence")
            handoff = next((h for h in context.audio_handoffs if h.speaker_id == speaker.speaker_id), None)
            if handoff is None or handoff.track not in tracks:
                raise ValueError("voice composition changed the exact selected speech track")
            expected_speech_ids.add(handoff.track.track_id)
            asset = assets.get(handoff.track.asset_id)
            metadata = asset.audio_metadata if asset is not None else None
            expected_request = (binding.compiled_request.resolved_generation_hash
                if route.route is VoiceRoute.NATIVE else
                handoff.voice_request.voice_request_fingerprint if handoff.voice_request else None)
            if (metadata is None or asset.source_kind.value != "generated"
                    or asset.egress is None or asset.egress.request_fingerprint != expected_request
                    or metadata.speaker_id != speaker.speaker_id
                    or metadata.script_hash != speaker.script_hash
                    or metadata.language != (speaker.language if route.route is VoiceRoute.NATIVE
                                              else voice_provider_language(speaker.language))):
                raise ValueError("voice composition asset differs from the selected generation request")
            spans = [s for s in timeline.audio_spans if s.track_id == handoff.track.track_id]
            if len(spans) != 1:
                raise ValueError("voice composition requires exactly one resolved speech span")
            span = spans[0]
            complete_samples = metadata.duration_samples * spec.sample_rate // metadata.sample_rate_hz
            if (span.source_start_sample != 0 or span.duration_samples != complete_samples
                    or span.gain_millidb != 0 or span.fade_in_samples or span.fade_out_samples
                    or span.ducking is not None):
                raise ValueError("voice composition cannot truncate or transform unqualified speech")
            start = shot_start
            end = shot_end
            if route.route is VoiceRoute.SEPARATE:
                start += int(dialogue.start_seconds * spec.sample_rate)
                end = min(end, shot_start + int(dialogue.end_seconds * spec.sample_rate))
            if span.start_sample != start or span.start_sample + span.duration_samples > end:
                raise ValueError("voice composition speech is outside its authored window")
        if {t.track_id for t in tracks if t.audio_kind.value in {"dialogue", "narration"}} != expected_speech_ids:
            raise ValueError("voice composition contains unselected speech")
