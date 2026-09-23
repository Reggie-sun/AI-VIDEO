"""Offline Ecommerce Job integration through the canonical Production owners."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace

from ai_video.production.ad_creative import (
    compile_ad_creative_handoff,
    create_ad_creative_plan,
)
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.composition_contracts import (
    AudioKind,
    AudioTrackSpec,
    RendererIdentity,
    RendererKind,
)
from ai_video.production.dependency import ProductionDependencyInputs
from ai_video.production.ecommerce_job import (
    EcommerceProductionJobService,
    EcommerceShotExecutionPlan,
)
from ai_video.production.ecommerce_job_assembly import (
    EcommerceCompositionExecutionPlan,
    EcommerceHyperFramesInvocation,
)
from ai_video.production.ecommerce_job_review import (
    EcommerceDeliveryExecutionPlan,
    EcommercePostMediaExecutionPlan,
)
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
)
from ai_video.production.final_output_contracts import (
    FinalOutputContract,
    FinalOutputRequirement,
)
from ai_video.production.final_output_review import (
    FinalOutputFinding,
    FinalOutputObservation,
)
from ai_video.production.ecommerce_quality_gate import EcommerceWholeAdEvaluationPayload
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetRoleRequirement,
    AssetSourceKind,
    AssetType,
    DeliveryProfile,
    EgressMetadata,
    QaLayer,
    QaVerdict,
    ToolIdentity,
    VisualStrategy,
)
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from ai_video.production.video import VideoOutputRequirement
from ai_video.production.video_candidate_composition import (
    build_video_candidate_composition_spec,
)
from production_project_factory import (
    _make_audio_asset,
    _p7_png,
    _refresh_p7_ready_project_registry_nodes,
    make_composition_spec,
)
from ai_video.production.quality_gate_coordinator import (
    UniversalHardCheck,
    UniversalQaApplicability,
    UniversalQaCheckOutcome,
    UniversalQaProfile,
)
from test_production_ecommerce_job import (
    _activate_offline_ecommerce_policy,
    _real_input,
    _request,
    _two_shot_runtime_handoff,
)
from test_production_ecommerce_post_media_e2e import _passing_payload
from test_production_hyperframes import (
    FakeRunner,
    _CountingRenderCommitter,
    _Manifest25RenderFixture,
    _write_executable,
)
from test_production_review import _Manifest25ReviewFixture
from test_production_commercial_visual_review import REVIEW_TOOL


VIDEO = Path(__file__).parent / "fixtures/ecommerce_job/vertical-3s.mp4"
FINAL_VIDEO = Path(__file__).parent / "fixtures/ecommerce_job/vertical-6s-audio.mp4"
OUTPUT = VideoOutputRequirement(
    duration_seconds=3,
    width=1080,
    height=1920,
    fps=24,
    container="mp4",
    mime_type="video/mp4",
    native_audio=False,
)


def _handoff_and_compiled():
    original = _two_shot_runtime_handoff()
    first, second = original.artifact_proposals.shots
    first = seal_artifact(
        first.model_copy(
            update={
                "revision": first.revision + 1,
                "content_hash": "0" * 64,
                "visual_strategy": VisualStrategy.STATIC_IMAGE,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="final_visual",
                        asset_ids=("hero-still",),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                    AssetRoleRequirement(
                        role="product_overlay",
                        asset_ids=("asset-product",),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
                "generated_video_rationale": None,
            }
        )
    )
    layout = original.layout_plan
    layout_values = {
        name: getattr(layout, name)
        for name in type(layout).model_fields
        if name != "layout_plan_id"
    }
    layout = type(layout).create(
        **{
            **layout_values,
            "shots": (
                layout.shots[0].model_copy(
                    update={"visual_strategy": VisualStrategy.STATIC_IMAGE}
                ),
                layout.shots[1],
            ),
        }
    )
    profile = original.compile_profile
    profile_values = {
        name: getattr(profile, name)
        for name in type(profile).model_fields
        if name != "profile_id"
    }
    profile = type(profile).create(
        **{
            **profile_values,
            "layout_plan_id": layout.layout_plan_id,
            "requirement_resolutions": tuple(
                item.model_copy(
                    update={
                        "evidence_ids": (
                            original.delivery_profile.profile_id,
                            original.visual_system_profile.profile_id,
                            layout.layout_plan_id,
                        )
                    }
                )
                for item in profile.requirement_resolutions
            ),
        }
    )
    handoff_values = {
        name: getattr(original, name)
        for name in EcommerceProductionHandoff.model_fields
        if name != "handoff_id"
    }
    handoff = EcommerceProductionHandoff.create(
        **{
            **handoff_values,
            "layout_plan": layout,
            "compile_profile": profile,
            "artifact_proposals": original.artifact_proposals.model_copy(
                update={"shots": (first, second)}
            ),
            "ad_creative_plan_proposal": original.ad_creative_plan_proposal.model_copy(
                update={
                    "ad_arc": (
                        original.ad_creative_plan_proposal.ad_arc[0].model_copy(
                            update={"shot_ids": ("shot-hero", "shot-proof")}
                        ),
                        *original.ad_creative_plan_proposal.ad_arc[1:],
                    )
                }
            ),
        }
    )
    plan = create_ad_creative_plan(
        handoff.ad_creative_plan_proposal,
        artifact_id="ecommerce-offline-e2e-plan",
        revision=1,
        creation_receipt_id="ecommerce-offline-e2e-plan",
        source_provenance=(
            SourceReference(
                kind="derived",
                reference=f"ecommerce-handoff:{handoff.handoff_id}",
                content_hash=handoff.handoff_id,
            ),
            SourceReference(
                kind="derived",
                reference=f"ecommerce-compile-profile:{profile.profile_id}",
                content_hash=profile.profile_id,
            ),
        ),
    )
    composition = make_composition_spec(shot_ids=("shot-hero", "shot-proof"))
    base_layer = composition.layers[0]
    composition = seal_artifact(
        composition.model_copy(
            update={
                "schema_version": "2.1",
                "revision": composition.revision + 1,
                "content_hash": "0" * 64,
                "delivery_profile": DeliveryProfile(width=1080, height=1920, fps=24),
                "layers": (
                    base_layer.model_copy(
                        update={
                            "layer_id": "layer-primary",
                            "asset_role": "final_visual",
                            "asset_id": "hero-still",
                        }
                    ),
                    base_layer.model_copy(
                        update={
                            "layer_id": "layer-product",
                            "asset_role": "product_overlay",
                            "asset_id": "asset-product",
                            "z_index": 10,
                        }
                    ),
                    composition.layers[1].model_copy(
                        update={
                            "asset_role": "final_visual",
                            "asset_id": "proof-pre-generation-source",
                        }
                    ),
                ),
                "audio_tracks": (
                    AudioTrackSpec(
                        track_id="audio-music",
                        audio_kind=AudioKind.BGM,
                        asset_id="audio-music-asset",
                        start_sample=0,
                    ),
                ),
            }
        )
    )
    return handoff, plan, compile_ad_creative_handoff(plan, composition)


def _bootstrap(root: Path, handoff: EcommerceProductionHandoff, composition_spec):
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-product-one",
    )
    image_payloads = (
        ("hero-still", _p7_png(1080, 1920)),
        ("asset-product", _p7_png(1080, 1920, rgba=b"\x20\x40\x60\xff")),
        (
            "proof-pre-generation-source",
            _p7_png(1080, 1920, rgba=b"\x30\x50\x70\xff"),
        ),
    )
    records = []
    prepared = []
    for asset_id, payload in image_payloads:
        digest = hashlib.sha256(payload).hexdigest()
        path = canonical_image_asset_path(digest)
        records.append(
            AssetRecord(
                asset_id=asset_id,
                asset_type=AssetType.IMAGE,
                artifact_path=path,
                sha256=digest,
                size_bytes=len(payload),
                mime_type="image/png",
                width=1080,
                height=1920,
                source_kind=AssetSourceKind.IMPORTED,
                tool=ToolIdentity(name="offline-fixture", version="1"),
                input_fingerprint=digest,
                creation_receipt_id=f"offline-{asset_id}",
                usage_license="fixture",
                egress=EgressMetadata(remote=False),
            )
        )
        prepared.append(PreparedArtifact(path, payload, digest))
    (root / "assets/files").mkdir(parents=True, exist_ok=True)
    music, path = _make_audio_asset(
        root,
        asset_id="audio-music-asset",
        audio_kind=AudioKind.BGM,
        duration_samples=288_000,
    )
    records.append(music)
    prepared.append(PreparedArtifact(music.artifact_path, path.read_bytes(), music.sha256))
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=tuple(records),
    )
    digest = registry_semantic_sha256(registry)
    compiled = replace(
        compiled,
        registry=registry.model_copy(
            update={"revision_id": digest, "content_hash": digest}
        ),
        artifacts=(*compiled.artifacts, *prepared),
    )
    bootstrap_ecommerce_production_project(
        root,
        attempt_id="ecommerce-offline-e2e-bootstrap",
        compiled=compiled,
    )
    inputs = ProductionDependencyInputs(
        project=load_production_project(root / "project.yaml"),
        composition_spec=composition_spec,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        voice_requests=(),
        resolver_contract_fingerprint="1" * 64,
        source_materializer_contract_fingerprint="2" * 64,
        render_contract_fingerprint="3" * 64,
        caption_style_fingerprints=(),
    )
    final_output = FinalOutputContract(
        goal_id="ecommerce-offline-e2e-final-output",
        goal_version="1",
        user_goal="Deliver the exact accepted offline Ecommerce ad.",
        requirements=tuple(
            FinalOutputRequirement(
                requirement_id=item.requirement_id,
                observable=item.description,
                proof="evaluator",
            )
            for item in handoff.acceptance_requirements
            if item.scope == "FINAL_OUTPUT"
        ),
    )
    _activate_offline_ecommerce_policy(
        root,
        inputs,
        output=OUTPUT,
        final_output=final_output,
        required_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.SEMANTIC),
    )


def test_canonical_two_shot_job_closes_offline_and_replays_without_effect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    handoff, plan, compiled = _handoff_and_compiled()
    request = _request(tmp_path, handoff)
    assert (
        EcommerceProductionJobService().inspect(request, handoff).next_action
        is EcommerceJobNextAction.BOOTSTRAP_PROJECT
    )
    assert tuple(
        (item.target_shot_id, item.invoke_video_provider)
        for item in compiled.commercial_execution_projections
    ) == (("shot-hero", False), ("shot-proof", True))
    _bootstrap(tmp_path, handoff, compiled.composition_spec)
    execution, provider = _real_input(
        root=tmp_path,
        execution=SimpleNamespace(handoff=compiled),
        shot_id="shot-proof",
        composition_spec=compiled.composition_spec,
        output=OUTPUT,
        artifact_bytes=VIDEO.read_bytes(),
    )
    shots = EcommerceShotExecutionPlan(
        handoff=compiled,
        plan=plan,
        shots=(execution,),
    )
    job = EcommerceProductionJobService()

    projected = job.inspect(request, handoff, shot_execution=shots)
    advanced = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.GENERATE_SHOT,
        shot_execution=shots,
    )
    assert projected.next_action is EcommerceJobNextAction.GENERATE_SHOT
    assert projected.next_shot_id == "shot-proof"
    assert advanced.next_action is EcommerceJobNextAction.PREPARE_COMPOSITION, advanced
    assert provider.submit_calls == 1
    assert provider.fetch_calls == 1
    _refresh_p7_ready_project_registry_nodes(
        tmp_path, ProductionStateCommitter(tmp_path)
    )

    final_spec = build_video_candidate_composition_spec(
        compiled.composition_spec,
        target_shot_id="shot-proof",
        target_asset_role="final_visual",
        output_asset_id="canonical-ecommerce-shot-proof-video",
    )
    final_handoff = compiled.model_copy(update={"composition_spec": final_spec})
    tools = tmp_path / "ecommerce-offline-render-tools"
    binary = tools / "node_modules/.bin/hyperframes"
    binary.parent.mkdir(parents=True)
    browser = _write_executable(tools / "chrome")
    unshare = _write_executable(tools / "unshare")
    ip_path = _write_executable(tools / "ip")
    bash = _write_executable(tools / "bash")
    ffmpeg = _write_executable(tools / "ffmpeg")
    ffprobe = _write_executable(tools / "ffprobe")
    committer = _CountingRenderCommitter(tmp_path)
    fixture_ref = {}
    composition = EcommerceCompositionExecutionPlan(
        handoff=final_handoff,
        plan=plan,
        renderer_version="0.7.103",
        hyperframes=EcommerceHyperFramesInvocation(
            committer=committer,
            attempt_id="ecommerce-offline-e2e-render",
            selection_receipt_id="ecommerce-offline-e2e-render-selection",
            binary_path=binary,
            browser_path=browser,
            unshare_path=unshare,
            ip_path=ip_path,
            bash_path=bash,
            ffmpeg_path=ffmpeg,
            ffprobe_path=ffprobe,
            dependency_transition_preparer=lambda activation: fixture_ref[
                "fixture"
            ].prepare_transition(activation),
        ),
    )
    prepared = composition.prepare(handoff, project_root=tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    fixture = _Manifest25RenderFixture(
        root=tmp_path,
        committer=committer,
        begin_request=prepared.begin_request,
        timeline=prepared.timeline,
        asset_sources=dict(prepared.asset_sources),
        browser=browser,
        ip_path=ip_path,
        runner=FakeRunner(),
        dependency_graph=loaded.dependency_graph,
        candidate_dependency_states=loaded.manifest.dependency_states,
        changed_nodes=[],
    )
    fixture_ref["fixture"] = fixture
    original_run = fixture.runner.run

    def render_fixture_media(command, args, *, cwd, env, timeout_seconds):
        result = original_run(
            command, args, cwd=cwd, env=env, timeout_seconds=timeout_seconds
        )
        if command == "render" and result.returncode == 0:
            Path(args[args.index("-o") + 1]).write_bytes(FINAL_VIDEO.read_bytes())
        return result

    monkeypatch.setattr(fixture.runner, "run", render_fixture_media)
    monkeypatch.setattr(
        "ai_video.production.hyperframes._NetworkIsolatedHyperFramesRunner",
        lambda **_kwargs: fixture.runner,
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.probe_clip_fd_with_executable",
        lambda _fd, _path: {
            "streams": [
                {
                    "codec_type": "video",
                    "width": prepared.timeline.delivery_profile.width,
                    "height": prepared.timeline.delivery_profile.height,
                    "r_frame_rate": f"{prepared.timeline.delivery_profile.fps}/1",
                    "nb_frames": str(prepared.timeline.total_frames),
                    "codec_name": "h264",
                },
                {
                    "codec_type": "audio",
                    "index": 1,
                    "codec_name": "aac",
                    "sample_rate": str(prepared.timeline.sample_rate),
                    "channels": 2,
                    "channel_layout": "stereo",
                },
            ],
            "packets": [
                {
                    "stream_index": 1,
                    "pts": "-1024",
                    "duration": "1024",
                    "side_data_list": [
                        {
                            "side_data_type": "Skip Samples",
                            "skip_samples": 1024,
                            "discard_padding": 0,
                        }
                    ],
                },
                {"stream_index": 1, "pts": "0", "duration": "768"},
            ],
        },
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.decoded_audio_sha256_fd_with_executable",
        lambda _fd, _rate, _channels, _path: (
            prepared.timeline.total_samples + 256,
            "a" * 64,
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.decoded_frame_sha256_fd",
        lambda _fd: "b" * 64,
    )
    prepared_projection = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PREPARE_COMPOSITION,
        shot_execution=shots,
        composition_execution=composition,
    )
    rendered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.RENDER_FINAL,
        shot_execution=shots,
        composition_execution=composition,
    )

    assert prepared_projection.next_action is EcommerceJobNextAction.RENDER_FINAL
    assert rendered.next_action is EcommerceJobNextAction.REVIEW_FINAL, rendered
    assert fixture.runner.calls
    assert load_production_project(tmp_path / "project.yaml").manifest.active_render_state

    loaded = load_production_project(tmp_path / "project.yaml")
    policy = loaded.qa_policy
    assert policy is not None and policy.final_output is not None
    def measured_technical_windows(_request, evidence):
        payload = dict(evidence.measured_payload)
        payload["windows"] = [
            {
                **window,
                "unique_frame_count": (
                    72 if window["visual_strategy"] == VisualStrategy.GENERATED_VIDEO.value
                    else 1
                ),
            }
            for window in payload["windows"]
        ]
        return seal_artifact(
            evidence.model_copy(
                update={"content_hash": "0" * 64, "measured_payload": payload}
            )
        )

    for layer in (QaLayer.TECHNICAL, QaLayer.LAYOUT):
        _Manifest25ReviewFixture(
            root=tmp_path,
            committer=ProductionStateCommitter(tmp_path),
            timeline=prepared.timeline,
            policy=policy,
            review_layer=layer,
            review_attempt_id=f"ecommerce-offline-e2e-{layer.value}",
            evidence_factory=(
                measured_technical_windows if layer is QaLayer.TECHNICAL else None
            ),
        ).run_required_review()
    universal = UniversalQaProfile.create(
        profile_id="ecommerce-offline-e2e",
        profile_version="1",
        delivery_profile=prepared.timeline.delivery_profile,
        applicability=UniversalQaApplicability(
            has_audio=True,
            has_graphics=True,
            has_safe_area_requirements=True,
            has_transitions=True,
        ),
        required_hard_checks=(
            UniversalHardCheck.ASSET_PROVENANCE,
            UniversalHardCheck.MEDIA_DECODE,
            UniversalHardCheck.TIMELINE_BINDING,
            UniversalHardCheck.RENDER_OUTPUT,
            UniversalHardCheck.AUDIO_CAPTION_BINDING,
        ),
        required_review_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT),
    )
    review = EcommercePostMediaExecutionPlan(
        handoff=final_handoff,
        plan=plan,
        shot_facades=shots.build_facades(handoff, project_root=tmp_path),
        committer=ProductionStateCommitter(tmp_path),
        universal_profile=universal,
        run_hard_check=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        run_review_layer=lambda *_: UniversalQaCheckOutcome(
            verdict=QaVerdict.PASS, current=True
        ),
        tool_identity=REVIEW_TOOL,
        evaluate=lambda target, _profile: EcommerceWholeAdEvaluationPayload(
            domain_acceptance=_passing_payload(),
            final_output=FinalOutputObservation(
                contract_hash=policy.final_output.contract_hash,
                review_request_content_hash=target.review_request_content_hash,
                findings=tuple(
                    FinalOutputFinding(
                        requirement_id=item.requirement_id,
                        verdict="pass",
                        observation="Observed on exact offline final candidate.",
                    )
                    for item in policy.final_output.requirements
                ),
            ),
        ),
        review_attempt_id="ecommerce-offline-e2e-semantic",
        review_request_id="ecommerce-offline-e2e-semantic-request",
        evidence_id="ecommerce-offline-e2e-semantic-evidence",
        review_id="ecommerce-offline-e2e-semantic-review",
        final_acceptance_id="ecommerce-offline-e2e-acceptance",
    )
    reviewed = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.REVIEW_FINAL,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=review,
    )
    assert reviewed.next_action is EcommerceJobNextAction.PACKAGE_DELIVERY, reviewed

    delivery = EcommerceDeliveryExecutionPlan(
        delivery_root=tmp_path / "deliveries",
        plan=plan,
        compiled_handoff=final_handoff,
        exported_at="2026-09-19T12:00:00+00:00",
        tool_identity=ToolIdentity(name="ecommerce-offline-packager", version="1"),
    )
    delivered = job.advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=review,
        delivery_execution=delivery,
    )
    assert delivered.next_action is EcommerceJobNextAction.COMPLETE, delivered
    packaged = delivery.inspect(
        handoff, project_root=tmp_path, job_id=request.job_id
    )
    assert packaged is not None
    assert packaged.render_output_sha256 == hashlib.sha256(
        FINAL_VIDEO.read_bytes()
    ).hexdigest()
    manifest_before = (tmp_path / "state/manifest.json").read_bytes()
    files_before = {
        path.relative_to(delivery.delivery_root): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in delivery.delivery_root.rglob("*")
        if path.is_file()
    }
    render_call_count = len(fixture.runner.calls)
    replay = EcommerceProductionJobService().advance_once(
        request,
        handoff,
        expected_action=EcommerceJobNextAction.PACKAGE_DELIVERY,
        shot_execution=shots,
        composition_execution=composition,
        review_execution=review,
        delivery_execution=delivery,
    )
    assert replay.next_action is EcommerceJobNextAction.COMPLETE
    assert delivery.inspect(
        handoff, project_root=tmp_path, job_id=request.job_id
    ) == packaged
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_before
    assert len(fixture.runner.calls) == render_call_count
    assert (provider.submit_calls, provider.fetch_calls) == (1, 1)
    assert {
        path.relative_to(delivery.delivery_root): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in delivery.delivery_root.rglob("*")
        if path.is_file()
    } == files_before
