"""Persisted P2/P5/P6 fixture for production-strategy application tests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

from ai_video.production._state_commit_common import _canonical_yaml_bytes, prepare_project_registry_commit
from ai_video.production._state_commit_contracts import PreparedArtifact
from ai_video.production.composition_contracts import AudioKind, AudioTrackSpec, CaptionTrackBinding
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    build_production_dependency_graph,
    resolve_dependency_state,
)
from ai_video.production.domain_acceptance import (
    ComponentRequirementAllocation,
    DomainAcceptancePolicy,
    GenerationEvaluationAuthority,
    ProductionRequirementAllocation,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.models import (
    ArtifactReference,
    AssetSourceKind,
    AssetType,
    DependencyGraphSnapshotPointer,
    ProductionManifest,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.paths import (
    canonical_dependency_graph_snapshot_path,
    canonical_video_asset_path,
)
from ai_video.production.production_strategy_contracts import (
    ProductionAudioUse,
    ProductionCoverage,
    ProductionIntent,
    ProductionOperation,
    ProductionSourceOption,
    ProductionUnit,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.source_use_evidence import SourceUseEvidence
from ai_video.production.state_commit import ProductionStateCommitter
from production_project_factory import make_p5_dependency_inputs


TECHNICAL = ToolIdentity(name="strategy-fixture-evaluator", version="1")


@dataclass(frozen=True)
class PersistedStrategyFixture:
    root: Path
    committer: ProductionStateCommitter
    parent_shot_id: str
    child_shot_id: str
    task_id: str
    component_generation_acceptance: DomainAcceptancePolicy | None = None


def _prepared_yaml(path: Path, model) -> PreparedArtifact:
    payload = _canonical_yaml_bytes(model)
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def _acceptance(requirement_ids: tuple[str, ...]) -> DomainAcceptancePolicy:
    payload = {
        "domain_id": "strategy-test",
        "profile_id": "strategy-final",
        "profile_version": "1",
        "measurement_contract_version": "strategy-test/1",
        "required_requirement_ids": requirement_ids,
        "source_use_requirements": tuple({"requirement_id": i, "proof": "technical", "stage": "source_use"} for i in requirement_ids),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="strategy-test",
        profile_id="strategy-final",
        profile_version="1",
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="strategy-test/1",
        required_requirement_ids=requirement_ids,
    )


def _generation_acceptance() -> DomainAcceptancePolicy:
    requirement = RequirementExpression(
        requirement_id="visual",
        level="acceptance",
        stage="raw_generation",
        dimension="visual",
        observable="authored visual intent",
        tolerance="exact",
        measurement="fixture technical evaluator",
        proof="technical",
        production_owner="generation",
    )
    payload = {
        "domain_id": "strategy-test",
        "profile_id": "strategy-component-generation",
        "profile_version": "1",
        "measurement_contract_version": "strategy-test/1",
        "required_requirement_ids": ("visual",),
        "generation_requirements": (
            requirement.model_dump(mode="json", exclude={"native_text"}),
        ),
    }
    digest = canonical_sha256(payload)
    return DomainAcceptancePolicy(
        domain_id="strategy-test",
        profile_id="strategy-component-generation",
        profile_version="1",
        profile_content_hash=digest,
        profile_payload={**payload, "content_hash": digest},
        measurement_contract_version="strategy-test/1",
        required_requirement_ids=("visual",),
    )


def _source_evidence(
    *,
    evidence_id: str,
    parent_hash: str,
    acceptance_hash: str,
    component_id: str,
    source: ProductionSourceOption,
    asset_size: int,
    verdict: str = "PASS",
) -> SourceUseEvidence:
    response = {
        "parent_shot_content_hash": parent_hash,
        "task_id": "strategy-task-1",
        "acceptance_profile_hash": acceptance_hash,
        "component_id": component_id,
        "asset_id": source.asset_id,
        "asset_sha256": source.asset_sha256,
        "size_bytes": asset_size,
        "role": source.role,
        "timebase": source.timebase,
        "start": source.start,
        "duration": source.duration,
        "evaluator": TECHNICAL.model_dump(mode="json"),
        "proof": "technical",
        "observations": [
            {"requirement_id": requirement_id, "verdict": verdict, "observation": "fixture qualified"}
            for requirement_id in source.requirement_ids
        ],
    }
    return SourceUseEvidence(
        evidence_id=evidence_id,
        parent_shot_content_hash=parent_hash,
        task_id="strategy-task-1",
        acceptance_profile_hash=acceptance_hash,
        component_id=component_id,
        asset_id=source.asset_id,
        asset_sha256=source.asset_sha256,
        size_bytes=asset_size,
        role=source.role,
        timebase=source.timebase,
        start=source.start,
        duration=source.duration,
        evaluator=TECHNICAL,
        proof="technical",
        response_json=json.dumps(response),
    )


def _activate_graph(root: Path, inputs) -> None:
    graph = build_production_dependency_graph(inputs)
    states = resolve_dependency_state(graph, build_applied_dependency_evidence(inputs, None)).states
    payload = (json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path = canonical_dependency_graph_snapshot_path(graph.revision_id)
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_bytes(payload)
    manifest_path = root / "state/manifest.json"
    manifest = ProductionManifest.model_validate_json(manifest_path.read_bytes())
    manifest = manifest.model_copy(update={
        "schema_version": "2.3",
        "manifest_revision": manifest.manifest_revision + 1,
        "active_dependency_graph": DependencyGraphSnapshotPointer(
            revision_id=graph.revision_id,
            content_hash=graph.content_hash,
            path=path,
            file_sha256=hashlib.sha256(payload).hexdigest(),
        ),
        "dependency_states": states,
    })
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")


def make_persisted_strategy_fixture(
    root: Path, *, source_verdict: str = "PASS", generation_only: bool = False,
    global_caption: bool = False,
    generation_audio: bool = False,
) -> PersistedStrategyFixture:
    """Create P2 authoring through the canonical committer, then activate QA normally."""
    base_inputs = make_p5_dependency_inputs(root, decodable_pngs=True)
    root_loaded = load_production_project(root / "project.yaml")
    parent = root_loaded.shots[0]
    child_shot_id = "strategy-shot-1"

    video_bytes = (
        b"\x00\x00\x00\x14ftypisom\x00\x00\x00\x00isom"
        + b"\x00\x00\x00\x08moov"
    )
    video_sha256 = hashlib.sha256(video_bytes).hexdigest()
    video_path = root / canonical_video_asset_path(video_sha256)
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(video_bytes)
    video = root_loaded.registry.assets[0].model_copy(update={
        "asset_id": "strategy-imported-video",
        "asset_type": AssetType.VIDEO,
        "artifact_path": video_path.relative_to(root),
        "sha256": video_sha256,
        "size_bytes": len(video_bytes),
        "mime_type": "video/mp4",
        "duration_seconds": 5.0,
        "width": 1280,
        "height": 720,
        "source_kind": AssetSourceKind.IMPORTED,
        "tool": ToolIdentity(name="strategy-fixture", version="1"),
        "video_metadata": VideoAssetMetadata(
            container_name="mp4", codec_name="h264", width=1280, height=720,
            fps_numerator=24, fps_denominator=1, duration_milliseconds=5000,
            frame_count=120, probe_receipt_id="strategy-probe",
            request_receipt_fingerprint="1" * 64,
            resolved_generation_hash="2" * 64,
            provenance_receipt_id="strategy-provenance",
        ),
    })
    registry = root_loaded.registry.model_copy(update={
        "schema_version": "2.2",
        "revision_id": "0" * 64,
        "content_hash": "0" * 64,
        "assets": (*base_inputs.project.registry.assets, video),
    })
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": registry_hash, "content_hash": registry_hash})

    video_source = ProductionSourceOption(
        asset_id=video.asset_id, asset_sha256=video.sha256, role="primary_visual",
        timebase="frames", start=4, duration=72, evidence_ids=("video-source-evidence",),
        requirement_ids=("visual",),
    )
    voice = next(item for item in registry.assets if item.asset_id == "voice-dialogue")
    audio_source = ProductionSourceOption(
        asset_id=voice.asset_id, asset_sha256=voice.sha256, role="dialogue_source",
        timebase="samples", start=0, duration=72_000, evidence_ids=("audio-source-evidence",),
        requirement_ids=("dialogue",),
    )
    visual = ProductionUnit(
        component_id="visual-1", shot_id=child_shot_id,
        intent=("Generate the authored dynamic visual." if generation_only
                else "Use the qualified trimmed plate."),
        duration_frames=72, requirement_ids=("visual",),
        source_options=() if generation_only else (video_source,),
    )
    audio_track = AudioTrackSpec(
        track_id="strategy-dialogue", audio_kind=AudioKind.DIALOGUE,
        asset_id=voice.asset_id, shot_id=child_shot_id,
        trim_start_sample=0, trim_duration_samples=72_000,
    )
    audio = ProductionAudioUse(
        component_id="audio-1", requirement_ids=("dialogue",), source=audio_source, track=audio_track,
    )
    base_caption = base_inputs.composition_spec.caption_tracks[0]
    caption = CaptionTrackBinding(
        binding_id="strategy-caption", caption_asset_id=base_caption.caption_asset_id,
        source_audio_track_id=audio_track.track_id, shot_id=None if global_caption else child_shot_id,
        style_reference=base_caption.style_reference,
    )
    has_audio = not generation_only or generation_audio
    coverage = ProductionCoverage(
        coverage_id="strategy-coverage-1", allocation_id="strategy-allocation-1",
        units=(visual,), audio=(audio,) if has_audio else (),
        captions=(caption,) if has_audio else (),
    )
    protected_requirement_ids = ("visual", "dialogue") if has_audio else ("visual",)
    intent = ProductionIntent(
        task_id="strategy-task-1",
        allowed_operations=((ProductionOperation.GENERATE_FULL_SHOT,) if generation_only else
            (ProductionOperation.TRIM_EXISTING,)) + ((ProductionOperation.REPLACE_AUDIO,) if has_audio else ()),
        protected_requirement_ids=protected_requirement_ids,
        coverage_options=(coverage,),
    )
    parent = seal_artifact(parent.model_copy(update={
        "revision": parent.revision + 1,
        "content_hash": "0" * 64,
        "duration_policy": parent.duration_policy.model_copy(update={"seconds": 3.0}),
        "production_intent": intent,
    }))
    parent_ref = ArtifactReference(
        artifact_id=parent.artifact_id, revision=parent.revision, content_hash=parent.content_hash,
        path=Path(f"creative/shots/{parent.content_hash}.yaml"),
    )
    project = seal_artifact(root_loaded.project.model_copy(update={
        "revision": root_loaded.project.revision + 1,
        "content_hash": "0" * 64,
        "artifacts": root_loaded.project.artifacts.model_copy(update={
            "shots": (parent_ref, *root_loaded.project.artifacts.shots[1:]),
        }),
    }))
    committer = ProductionStateCommitter(root)
    base = prepare_project_registry_commit(
        manifest=root_loaded.manifest, project=project, registry=registry, attempt_id="strategy-authoring",
    )
    committer.commit(replace(base, artifacts=tuple(sorted(
        (*base.artifacts, _prepared_yaml(parent_ref.path, parent)),
        key=lambda item: item.relative_path.as_posix(),
    ))))

    loaded = load_production_project(root / "project.yaml")
    _activate_graph(root, replace(base_inputs, project=loaded))
    loaded = load_production_project(root / "project.yaml")
    acceptance = _acceptance(protected_requirement_ids)
    component_generation_acceptance = _generation_acceptance() if generation_only else None
    allocation = ProductionRequirementAllocation(
        allocation_id=coverage.allocation_id,
        parent_shot_id=parent.shot_id,
        parent_shot_content_hash=parent.content_hash,
        task_id=intent.task_id,
        parent_acceptance_hash=acceptance.profile_content_hash,
        parent_requirement_ids=protected_requirement_ids,
        components=(
            ComponentRequirementAllocation(
                component_id="visual-1", requirement_ids=("visual",),
                generation_acceptance=component_generation_acceptance,
            ),
        ) + (() if not has_audio else (
            ComponentRequirementAllocation(component_id="audio-1", requirement_ids=("dialogue",)),
        )),
    )
    policy = seal_artifact(QaPolicy(
        artifact_id="strategy-qa", revision=1, content_hash="0" * 64,
        creation_receipt_id="strategy-qa",
        source_provenance=(SourceReference(kind="derived", reference="strategy-fixture"),),
        policy_id="strategy-qa", policy_version="1", required_layers=(QaLayer.SEMANTIC,),
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10, silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(safe_area_inset_milli=50, caption_overflow_tolerance_milli=0),
        strategy_rules_version="1", semantic_requirement="required",
        semantic_authorities=(TECHNICAL,),
        generation_evaluation_authorities=(GenerationEvaluationAuthority(evaluator=TECHNICAL, proof="technical"),),
        domain_acceptance=acceptance,
        production_allocations=(allocation,),
        production_source_evidence=(() if generation_only else (
            _source_evidence(
                evidence_id="video-source-evidence", parent_hash=parent.content_hash,
                acceptance_hash=acceptance.profile_content_hash, component_id="visual-1",
                source=video_source, asset_size=video.size_bytes, verdict=source_verdict,
            ),
        )) + (() if not has_audio else (
            _source_evidence(
                evidence_id="audio-source-evidence", parent_hash=parent.content_hash,
                acceptance_hash=acceptance.profile_content_hash, component_id="audio-1",
                source=audio_source, asset_size=voice.size_bytes, verdict=source_verdict,
            ),
        )),
    ))
    committer.activate_qa_policy(
        policy, expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="strategy-qa",
    )
    load_production_project(root / "project.yaml")
    return PersistedStrategyFixture(
        root=root, committer=committer, parent_shot_id=parent.shot_id,
        child_shot_id=child_shot_id, task_id=intent.task_id,
        component_generation_acceptance=component_generation_acceptance,
    )
