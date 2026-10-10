"""Prepare canvas authoring/render transactions using the canonical graph owner."""
from dataclasses import replace
import hashlib

from ai_video.production.dependency import (
    ProductionDependencyInputs, build_applied_dependency_evidence,
    build_dependency_graph, build_production_dependency_graph, desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production._dependency_authoring import (
    build_authoring_dependency_projection, build_authoring_project_evidence_states,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    DependencyLifecycle, DependencyNodeKind, DependencyNodeState,
    RenderDependencyEvidence, RendererIdentity,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact, _canonical_json_bytes, prepare_dependency_graph_transition,
)


def initialize_canvas_graph(committer, attempt_id):
    loaded = load_production_project(committer.project_root / "project.yaml")
    if loaded.manifest.active_dependency_graph is not None:
        return loaded.manifest
    projection = build_authoring_dependency_projection(loaded)
    graph = build_dependency_graph(nodes=projection.nodes, edges=projection.edges)
    desired = desired_fingerprints(graph)
    states = build_authoring_project_evidence_states(graph=graph, projection=projection,
        project_pointer=loaded.manifest.active_project, desired=desired)
    transition = prepare_dependency_graph_transition(expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=None, candidate_graph=graph, candidate_dependency_states=states,
        expected_desired_fingerprints=desired)
    return committer.bootstrap_dependency_graph(attempt_id=attempt_id, graph=graph,
        transition=transition, expected_desired_fingerprints=desired)


def canvas_dependency_inputs(loaded, spec, renderer_version, *, voice_requests=(), caption_style_fingerprints=()):
    """Static contract versions; actual media and state fingerprints come from owners."""
    contract = lambda name: canonical_sha256({"canvas-contract": name, "version": "1"})
    return ProductionDependencyInputs(project=loaded, composition_spec=spec,
        renderer=RendererIdentity(kind="hyperframes", version=renderer_version),
        voice_requests=tuple(voice_requests), resolver_contract_fingerprint=contract("canonical-resolver"),
        source_materializer_contract_fingerprint=contract("canonical-hyperframes-source"),
        render_contract_fingerprint=contract("canonical-hyperframes-render"),
        caption_style_fingerprints=tuple(caption_style_fingerprints))


def canvas_render_transition_preparer(committer, inputs):
    """No traversal, fingerprint or invalidation duplication; only bind actual render proof."""
    graph = build_production_dependency_graph(inputs)
    applied = build_applied_dependency_evidence(inputs, None)
    desired = desired_fingerprints(graph)
    render_kinds = {DependencyNodeKind.COMPOSITION_SPEC, DependencyNodeKind.RESOLVED_TIMELINE,
                    DependencyNodeKind.RENDERER_SOURCE, DependencyNodeKind.RENDER}

    def prepare(activation):
        current = load_production_project(committer.project_root / "project.yaml").manifest
        if (activation.current_project != current.active_project or
                activation.current_registry != current.active_registry):
            raise ValueError("render inputs changed before graph activation")
        rendered = tuple(DependencyNodeState(node_id=n.node_id, graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[n.node_id], applied_fingerprint=desired[n.node_id],
            lifecycle=DependencyLifecycle.FRESH, applied_evidence=RenderDependencyEvidence(
                owner="render_state", pointer=activation.next_render_state,
                artifact_id=n.artifact_id, artifact_fingerprint=desired[n.node_id]))
            for n in graph.nodes if n.kind in render_kinds)
        states = resolve_dependency_state(graph, (*applied, *rendered)).states
        transition = prepare_dependency_graph_transition(expected_manifest_revision=activation.expected_manifest_revision,
            base_dependency_graph=current.active_dependency_graph, candidate_graph=graph,
            candidate_dependency_states=states, expected_desired_fingerprints=desired)
        payload = _canonical_json_bytes(graph)
        artifact = PreparedArtifact(transition.candidate_dependency_graph.path, payload,
                                    hashlib.sha256(payload).hexdigest())
        return replace(activation, artifacts=tuple(sorted((*activation.artifacts, artifact),
            key=lambda a: a.relative_path.as_posix())), dependency_graph_transition=transition)

    return prepare


def canvas_video_candidate_preparer(*, renderer_version="0.7.103"):
    """Prepare a single-Shot candidate projection via the existing video owner.

    This is an unresolved candidate CompositionSpec, never a rendered source
    timeline. The canonical video owner replaces its one layer with verified
    output and derives the candidate Project/Registry/graph transaction.
    """
    from ai_video.production.composition_contracts import CompositionLayerSpec, CompositionSpec
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.models import SourceReference
    from ai_video.production.video_candidate import make_video_candidate_preparer

    def prepare(loaded, request, *candidate_evidence):
        scope = request.activation_scope.request
        spec = seal_artifact(CompositionSpec(artifact_id="canvas-video-candidate", revision=1,
            content_hash="0" * 64, creation_receipt_id=request.request_input_hash,
            source_provenance=(SourceReference(kind="derived", reference=request.generation_id,
                                              content_hash=request.request_input_hash),),
            composition_id="canvas-video-candidate", shot_ids=(scope.target_shot_id,),
            layers=(CompositionLayerSpec(layer_id="candidate", shot_id=scope.target_shot_id,
                asset_role=scope.target_asset_role, asset_id=request.output_asset_id),),
            delivery_profile=loaded.project.delivery_profile))
        inputs = canvas_dependency_inputs(loaded, spec, renderer_version)
        return make_video_candidate_preparer(inputs)(loaded, request, *candidate_evidence)

    return prepare


def canvas_audio_transition_preparer(committer, *, shot_id, asset_id, audio_kind, renderer_version="0.7.103"):
    """Bind an audio owner's candidate Registry to the normal P5 projection."""
    from ai_video.production.composition_contracts import AudioTrackSpec, CompositionLayerSpec, CompositionSpec
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.models import AssetRegistrySnapshot, SourceReference

    def prepare(commit):
        base = load_production_project(committer.project_root / "project.yaml")
        payload = next(a.payload for a in commit.artifacts if a.relative_path == commit.next_registry.path)
        registry = AssetRegistrySnapshot.model_validate_json(payload)
        candidate = base.model_copy(update={"registry": registry, "manifest": base.manifest.model_copy(
            update={"active_project": commit.next_project, "active_registry": commit.next_registry})})
        shot = next(s for s in base.shots if s.shot_id == shot_id)
        video_ids = [i for r in shot.required_asset_roles if r.role == "primary_visual" for i in r.asset_ids]
        if len(video_ids) != 1:
            raise ValueError("audio preparation requires one adopted Shot visual")
        spec = seal_artifact(CompositionSpec(schema_version="2.1", artifact_id="canvas-audio-candidate",
            composition_id="canvas-audio-candidate", revision=1, content_hash="0" * 64,
            creation_receipt_id=commit.attempt_id,
            source_provenance=(SourceReference(kind="derived", reference=shot.artifact_id,
                                              content_hash=shot.content_hash),),
            shot_ids=(shot_id,), delivery_profile=base.project.delivery_profile,
            layers=(CompositionLayerSpec(layer_id="visual", shot_id=shot_id,
                asset_role="primary_visual", asset_id=video_ids[0]),),
            audio_tracks=(AudioTrackSpec(track_id="native-audio", shot_id=shot_id,
                asset_id=asset_id, audio_kind=audio_kind),)))
        inputs = canvas_dependency_inputs(candidate, spec, renderer_version)
        graph = build_production_dependency_graph(inputs)
        states = resolve_dependency_state(graph, build_applied_dependency_evidence(inputs, None)).states
        transition = prepare_dependency_graph_transition(expected_manifest_revision=commit.expected_manifest_revision,
            base_dependency_graph=base.manifest.active_dependency_graph, candidate_graph=graph,
            candidate_dependency_states=states, expected_desired_fingerprints=desired_fingerprints(graph))
        raw = _canonical_json_bytes(graph)
        return replace(commit, dependency_graph_transition=transition,
            artifacts=tuple(sorted((*commit.artifacts, PreparedArtifact(
                transition.candidate_dependency_graph.path, raw, hashlib.sha256(raw).hexdigest())),
                key=lambda a: a.relative_path.as_posix())))
    return prepare
