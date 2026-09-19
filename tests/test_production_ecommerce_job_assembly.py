from __future__ import annotations

from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.ad_creative import (
    compile_ad_creative_handoff,
    compile_ad_creative_plan,
    create_ad_creative_plan,
)
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.composition_contracts import (
    AudioKind,
    AudioTrackSpec,
    RendererKind,
)
from ai_video.production.ecommerce_job_assembly import (
    EcommerceAssemblyDecision,
    EcommerceCompositionExecutionPlan,
    EcommerceHyperFramesInvocation,
    PreparedEcommerceComposition,
    active_render_matches_prepared,
    advance_ecommerce_job_assembly,
    inspect_ecommerce_assembly,
)
from ai_video.production.ecommerce_job_contracts import EcommerceJobNextAction
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetType,
    DeliveryProfile,
    DependencyLifecycle,
    DependencyNodeKind,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StateCommitStatus,
)
from ecommerce_job_factory import make_ecommerce_handoff
from production_project_factory import make_composition_spec
from test_production_hyperframes import (
    _write_executable,
    make_manifest_25_render_fixture,
)


ZERO_HASH = "0" * 64


def _plan_and_handoff():
    runtime_handoff = make_ecommerce_handoff()
    plan = create_ad_creative_plan(
        runtime_handoff.ad_creative_plan_proposal,
        artifact_id="product-one-plan",
        revision=1,
        creation_receipt_id="ecommerce-assembly-test",
        source_provenance=(
            SourceReference(
                kind="derived",
                reference=f"ecommerce-handoff:{runtime_handoff.handoff_id}",
                content_hash=runtime_handoff.handoff_id,
            ),
            SourceReference(
                kind="derived",
                reference=(
                    "ecommerce-compile-profile:"
                    f"{runtime_handoff.compile_profile.profile_id}"
                ),
                content_hash=runtime_handoff.compile_profile.profile_id,
            ),
        ),
    )
    base = make_composition_spec(shot_ids=("shot-hero",))
    base = seal_artifact(
        base.model_copy(
            update={
                "schema_version": "2.1",
                "revision": base.revision + 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": "ecommerce-base-composition",
                "layers": (
                    base.layers[0].model_copy(
                        update={
                            "layer_id": "layer-primary",
                            "asset_role": "final_visual",
                            "asset_id": "video-hero",
                        }
                    ),
                    base.layers[0].model_copy(
                        update={
                            "layer_id": "layer-product",
                            "asset_role": "product_overlay",
                            "asset_id": "asset-product",
                            "z_index": 10,
                        }
                    ),
                ),
                "delivery_profile": DeliveryProfile(
                    width=runtime_handoff.delivery_profile.width,
                    height=runtime_handoff.delivery_profile.height,
                    fps=runtime_handoff.delivery_profile.fps,
                    codec_profile=runtime_handoff.delivery_profile.codec_profile,
                ),
                "sample_rate": runtime_handoff.delivery_profile.audio_sample_rate_hz,
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
    composition = compile_ad_creative_plan(plan, base)
    compiled = compile_ad_creative_handoff(plan, base).model_copy(
        update={"composition_spec": composition}
    )
    return runtime_handoff, plan, compiled


def _loaded(runtime_handoff, root: Path):
    shot = runtime_handoff.artifact_proposals.shots[0]
    shot = seal_artifact(
        shot.model_copy(
            update={
                "revision": shot.revision + 1,
                "content_hash": ZERO_HASH,
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role="final_visual",
                        asset_ids=("video-hero",),
                        allowed_asset_types=(AssetType.VIDEO,),
                    ),
                    AssetRoleRequirement(
                        role="product_overlay",
                        asset_ids=("asset-product",),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
            }
        )
    )
    project_pointer = ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash="2" * 64,
        file_sha256="3" * 64,
    )
    registry_pointer = RegistrySnapshotPointer(
        path=Path(f"assets/registry.{'4' * 64}.json"),
        revision_id="4" * 64,
        content_hash="4" * 64,
        file_sha256="5" * 64,
    )
    return SimpleNamespace(
        root=root,
        shots=(shot,),
        manifest=SimpleNamespace(
            manifest_revision=7,
            active_project=project_pointer,
            active_registry=registry_pointer,
            active_render_state=None,
            attempts=(),
        ),
        asset_paths={
            "video-hero": root / "assets/video-hero.mp4",
            "asset-product": root / "assets/product.png",
            "audio-music-asset": root / "assets/audio-music.wav",
        },
    )


def _execution(compiled, plan, root: Path):
    return EcommerceCompositionExecutionPlan(
        handoff=compiled,
        plan=plan,
        renderer_version="0.7.103",
        hyperframes=EcommerceHyperFramesInvocation(
            committer=SimpleNamespace(project_root=root),
            attempt_id="ecommerce-render-1",
            selection_receipt_id="ecommerce-render-selection-1",
            binary_path=root / "tools/hyperframes/node_modules/.bin/hyperframes",
            browser_path=root / "tools/chromium",
            unshare_path=root / "tools/unshare",
            ip_path=root / "tools/ip",
            bash_path=root / "tools/bash",
            ffmpeg_path=root / "tools/ffmpeg",
            ffprobe_path=root / "tools/ffprobe",
            dependency_transition_preparer=lambda activation: activation,
        ),
    )


def _timeline(spec):
    return SimpleNamespace(
        composition_fingerprint="f" * 64,
        composition_spec_hash=spec.content_hash,
        renderer=SimpleNamespace(
            kind=RendererKind.HYPERFRAMES,
            version="0.7.103",
        ),
        visual_spans=(
            SimpleNamespace(asset_id="video-hero"),
            SimpleNamespace(asset_id="asset-product"),
        ),
        audio_spans=(SimpleNamespace(asset_id="audio-music-asset"),),
        caption_cues=(),
    )


def test_prepare_binds_exact_plan_graphics_audio_and_one_timeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    loaded = _loaded(runtime_handoff, tmp_path)
    timeline = _timeline(compiled.composition_spec)
    observed = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: loaded,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda project, spec, renderer_version: observed.append(
            (project, spec, renderer_version)
        )
        or timeline,
    )
    effects = []
    execution = _execution(compiled, plan, tmp_path)

    prepared = execution.prepare(runtime_handoff, project_root=tmp_path)

    assert len(observed) == 1
    assert observed[0][1] is compiled.composition_spec
    assert prepared.timeline is timeline
    assert prepared.timeline.composition_fingerprint == "f" * 64
    assert dict(prepared.asset_sources) == loaded.asset_paths
    assert tuple(item.role.value for item in prepared.composition_spec.commercial_graphics) == (
        "cta",
        "brand_end_card",
    )
    assert prepared.composition_spec.caption_tracks == ()
    assert effects == []


def test_prepare_rejects_missing_required_music_before_timeline_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    bad_spec = seal_artifact(
        compiled.composition_spec.model_copy(
            update={
                "revision": compiled.composition_spec.revision + 1,
                "content_hash": ZERO_HASH,
                "audio_tracks": (),
            }
        )
    )
    bad_handoff = compiled.model_copy(update={"composition_spec": bad_spec})
    resolved = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: _loaded(runtime_handoff, tmp_path),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda _project, spec, _version: resolved.append(True) or _timeline(spec),
    )

    with pytest.raises(AiVideoError, match="audio"):
        _execution(bad_handoff, plan, tmp_path).prepare(
            runtime_handoff, project_root=tmp_path
        )

    assert resolved == []


def test_prepare_rejects_stale_plan_or_graphics_before_timeline_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    bad_spec = seal_artifact(
        compiled.composition_spec.model_copy(
            update={
                "revision": compiled.composition_spec.revision + 1,
                "content_hash": ZERO_HASH,
                "commercial_graphics": (),
            }
        )
    )
    resolved = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: _loaded(runtime_handoff, tmp_path),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda _project, spec, _version: resolved.append(True) or _timeline(spec),
    )

    with pytest.raises(AiVideoError, match="graphic"):
        _execution(
            compiled.model_copy(update={"composition_spec": bad_spec}),
            plan,
            tmp_path,
        ).prepare(runtime_handoff, project_root=tmp_path)

    assert resolved == []


@pytest.mark.parametrize("drift", ("opacity", "animation"))
def test_prepare_rejects_product_presentation_visual_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift: str,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    spec = compiled.composition_spec
    if drift == "opacity":
        layers = tuple(
            item.model_copy(update={"opacity_milli": 0})
            if item.layer_id == "layer-product"
            else item
            for item in spec.layers
        )
        update = {"layers": layers}
    else:
        update = {"graphic_layer_animations": ()}
    bad_spec = seal_artifact(
        spec.model_copy(
            update={
                **update,
                "revision": spec.revision + 1,
                "content_hash": ZERO_HASH,
            }
        )
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: _loaded(runtime_handoff, tmp_path),
    )
    resolved = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda *_args: resolved.append(True),
    )

    with pytest.raises(AiVideoError, match="presentation"):
        _execution(
            compiled.model_copy(update={"composition_spec": bad_spec}),
            plan,
            tmp_path,
        ).prepare(runtime_handoff, project_root=tmp_path)

    assert resolved == []


def test_render_uses_only_the_canonical_hyperframes_seam(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: _loaded(runtime_handoff, tmp_path),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda _project, spec, _version: _timeline(spec),
    )
    effects = []
    expected = object()
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.render_with_hyperframes",
        lambda **kwargs: effects.append(kwargs) or expected,
    )
    execution = _execution(compiled, plan, tmp_path)
    prepared = execution.prepare(runtime_handoff, project_root=tmp_path)

    assert execution.render(prepared) is expected
    assert len(effects) == 1
    assert effects[0]["timeline"] is prepared.timeline
    assert effects[0]["asset_sources"] is prepared.asset_sources
    assert effects[0]["begin_request"] is prepared.begin_request


def test_prepare_rejects_audio_role_bound_to_wrong_semantic_kind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    bad_track = compiled.composition_spec.audio_tracks[0].model_copy(
        update={"audio_kind": AudioKind.NARRATION}
    )
    bad_spec = seal_artifact(
        compiled.composition_spec.model_copy(
            update={
                "revision": compiled.composition_spec.revision + 1,
                "content_hash": ZERO_HASH,
                "audio_tracks": (bad_track,),
            }
        )
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: _loaded(runtime_handoff, tmp_path),
    )
    resolved = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda *_args: resolved.append(True),
    )

    with pytest.raises(AiVideoError, match="audio"):
        _execution(
            compiled.model_copy(update={"composition_spec": bad_spec}),
            plan,
            tmp_path,
        ).prepare(runtime_handoff, project_root=tmp_path)

    assert resolved == []


def test_inspection_requires_exact_active_render_or_explicit_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    loaded = _loaded(runtime_handoff, tmp_path)
    timeline = _timeline(compiled.composition_spec)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: loaded,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda *_args: timeline,
    )
    execution = _execution(compiled, plan, tmp_path)

    assert inspect_ecommerce_assembly(
        execution, runtime_handoff, project_root=tmp_path
    ).value == "render"

    loaded.manifest.active_render_state = object()
    active_renderer = SimpleNamespace(
        kind=RendererKind.HYPERFRAMES,
        version="0.7.103",
    )
    loaded.render_state = SimpleNamespace(
        timeline_fingerprint=timeline.composition_fingerprint,
        renderer=active_renderer,
        renderer_selection=SimpleNamespace(
            timeline_fingerprint=timeline.composition_fingerprint
        ),
        project=loaded.manifest.active_project,
        registry=loaded.manifest.active_registry,
    )
    assert inspect_ecommerce_assembly(
        execution, runtime_handoff, project_root=tmp_path
    ).value == "active"

    loaded.render_state.project = loaded.manifest.active_project.model_copy(
        update={"revision": 2, "content_hash": "8" * 64}
    )
    assert inspect_ecommerce_assembly(
        execution, runtime_handoff, project_root=tmp_path
    ).value == "render"
    loaded.render_state.project = loaded.manifest.active_project

    active_renderer.version = "0.7.102"
    assert inspect_ecommerce_assembly(
        execution, runtime_handoff, project_root=tmp_path
    ).value == "render"
    active_renderer.version = "0.7.103"

    render_nodes = tuple(
        SimpleNamespace(kind=kind, node_id=f"render-unit-{index}")
        for index, kind in enumerate(
            (
                DependencyNodeKind.COMPOSITION_SPEC,
                DependencyNodeKind.RESOLVED_TIMELINE,
                DependencyNodeKind.RENDERER_SOURCE,
                DependencyNodeKind.RENDER,
            )
        )
    )
    loaded.dependency_graph = SimpleNamespace(nodes=render_nodes)
    loaded.manifest.dependency_states = tuple(
        SimpleNamespace(
            node_id=node.node_id,
            lifecycle=(
                DependencyLifecycle.STALE
                if node.kind is DependencyNodeKind.RENDER
                else DependencyLifecycle.FRESH
            ),
            desired_fingerprint="6" * 64,
            applied_fingerprint=(
                "7" * 64
                if node.kind is DependencyNodeKind.RENDER
                else "6" * 64
            ),
            applied_evidence=SimpleNamespace(
                pointer=loaded.manifest.active_render_state,
                artifact_fingerprint="6" * 64,
            ),
        )
        for node in render_nodes
    )
    assert inspect_ecommerce_assembly(
        execution, runtime_handoff, project_root=tmp_path
    ).value == "render"
    loaded.dependency_graph = None
    loaded.manifest.dependency_states = ()

    loaded.manifest.attempts = (
        SimpleNamespace(
            operation="render_state",
            status=StateCommitStatus.RUNNING,
        ),
    )
    assert inspect_ecommerce_assembly(
        execution, runtime_handoff, project_root=tmp_path
    ).value == "recover"

    prepared = advance_ecommerce_job_assembly(
        execution,
        runtime_handoff,
        project_root=tmp_path,
        render=False,
    )
    assert prepared.next_action.value == "RECOVER_UNKNOWN_OUTCOME"


def test_prepare_restores_durable_begin_request_for_existing_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, plan, compiled = _plan_and_handoff()
    loaded = _loaded(runtime_handoff, tmp_path)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.load_production_project",
        lambda _path: loaded,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.resolve_composition",
        lambda _project, spec, _version: _timeline(spec),
    )
    execution = _execution(compiled, plan, tmp_path)
    original = execution.prepare(runtime_handoff, project_root=tmp_path).begin_request
    loaded.manifest.manifest_revision = 9
    loaded.manifest.attempts = (
        SimpleNamespace(
            attempt_id="ecommerce-render-1",
            operation="render_state",
            base_manifest_revision=original.expected_manifest_revision,
            base_render_state=original.base_render_state,
            renderer_selection=original.renderer_selection,
            status=StateCommitStatus.FAILED,
        ),
    )

    replay = execution.prepare(runtime_handoff, project_root=tmp_path)

    assert replay.begin_request == original


def test_failed_render_replay_blocks_instead_of_reprojecting_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailedReplay:
        def prepare(self, _handoff, *, project_root):
            return SimpleNamespace(
                begin_request=SimpleNamespace(
                    renderer_selection=SimpleNamespace(attempt_id="render-failed")
                )
            )

        def render(self, _prepared):
            return SimpleNamespace(
                attempts=(
                    SimpleNamespace(
                        attempt_id="render-failed",
                        status=StateCommitStatus.FAILED,
                    ),
                )
            )

    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_assembly.inspect_ecommerce_job_assembly",
        lambda *_args, **_kwargs: EcommerceAssemblyDecision(
            EcommerceJobNextAction.RENDER_FINAL
        ),
    )

    result = advance_ecommerce_job_assembly(
        FailedReplay(),
        make_ecommerce_handoff(),
        project_root=tmp_path,
        render=True,
    )

    assert result.next_action is EcommerceJobNextAction.BLOCKED
    assert isinstance(result.error, AiVideoError)
    assert "terminal" in result.error.user_message.lower()


def test_ecommerce_composition_execution_contracts_are_public() -> None:
    from ai_video import production

    assert (
        production.EcommerceCompositionExecutionPlan
        is EcommerceCompositionExecutionPlan
    )
    assert production.EcommerceHyperFramesInvocation is EcommerceHyperFramesInvocation


def test_render_executes_real_canonical_transaction_with_only_runner_replaced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_manifest_25_render_fixture(tmp_path)
    runtime_handoff, plan, compiled = _plan_and_handoff()
    spec = compiled.composition_spec.model_copy(
        update={"content_hash": fixture.timeline.composition_spec_hash}
    )
    compiled = compiled.model_copy(update={"composition_spec": spec})
    tools = tmp_path / "ecommerce-wrapper-tools"
    binary = tools / "node_modules/.bin/hyperframes"
    binary.parent.mkdir(parents=True)
    browser = _write_executable(tools / "chrome")
    unshare = _write_executable(tools / "unshare")
    ip_path = _write_executable(tools / "ip")
    bash = _write_executable(tools / "bash")
    ffmpeg = _write_executable(tools / "ffmpeg")
    ffprobe = _write_executable(tools / "ffprobe")
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
                    "width": fixture.timeline.delivery_profile.width,
                    "height": fixture.timeline.delivery_profile.height,
                    "r_frame_rate": f"{fixture.timeline.delivery_profile.fps}/1",
                    "nb_frames": str(fixture.timeline.total_frames),
                    "codec_name": "h264",
                },
                {
                    "codec_type": "audio",
                    "index": 1,
                    "codec_name": "aac",
                    "sample_rate": str(fixture.timeline.sample_rate),
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
            fixture.timeline.total_samples + 256,
            "a" * 64,
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.hyperframes.decoded_frame_sha256_fd",
        lambda _fd: "b" * 64,
    )
    execution = EcommerceCompositionExecutionPlan(
        handoff=compiled,
        plan=plan,
        renderer_version="0.7.103",
        hyperframes=EcommerceHyperFramesInvocation(
            committer=fixture.committer,
            attempt_id=fixture.begin_request.renderer_selection.attempt_id,
            selection_receipt_id=(
                fixture.begin_request.renderer_selection.receipt_id
            ),
            binary_path=binary,
            browser_path=browser,
            unshare_path=unshare,
            ip_path=ip_path,
            bash_path=bash,
            ffmpeg_path=ffmpeg,
            ffprobe_path=ffprobe,
            dependency_transition_preparer=fixture.prepare_transition,
        ),
    )
    prepared = PreparedEcommerceComposition(
        project_root=tmp_path,
        composition_spec=spec,
        timeline=fixture.timeline,
        asset_sources=MappingProxyType(fixture.asset_sources),
        begin_request=fixture.begin_request,
    )

    activated = execution.render(prepared)

    assert activated.active_render_state is not None
    assert fixture.runner.calls
    assert fixture.load_manifest().active_render_state == activated.active_render_state
    assert active_render_matches_prepared(prepared)
