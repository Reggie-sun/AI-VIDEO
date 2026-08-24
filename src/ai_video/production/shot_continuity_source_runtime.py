"""Cohesive source runtime helper for the Shot Continuity upstream source Production closure.

This module binds the canonical four-Shot project, a sealed ``CompositionSpec``
binding each Shot's ``approved_endpoint`` asset, the pinned HyperFrames
0.7.103 renderer identity, and explicit stable contract fingerprints into one
immutable :class:`ProductionDependencyInputs`. It exposes the single immutable
dependency graph that owns the source runtime, the deterministic bootstrap
path that drives ``ProductionStateCommitter.bootstrap_dependency_graph``, and
the generic ``make_video_candidate_preparer`` closure that the committer binds
to the exact same :class:`ProductionDependencyInputs`.

The helper is deliberately write-free: it constructs and binds immutable values
only. ``ProductionStateCommitter`` remains the unique owner of all durable
Manifest writes, lifecycle transitions, and explicit recovery. The dependency
graph resolver remains the pure graph owner, and the generic candidate
preparer remains a deterministic, write-free closure. This module never
imports the qualification profile, never inspects P0 evidence, and never
invokes a Provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    CompositionLayerSpec,
    CompositionSpec,
    DeliveryProfile,
    RendererIdentity,
    RendererKind,
    SourceReference,
    TransitionKind,
    TransitionSpec,
)

if TYPE_CHECKING:
    from ai_video.production.dependency import ProductionDependencyInputs
    from ai_video.production.models import (
        DependencyGraphTransition,
        DependencyGraphSnapshot,
        LoadedProductionProject,
    )
    from ai_video.production.state_commit import ProductionStateCommitter


HYPERFRAMES_VERSION: str = "0.7.103"
SOURCE_RUNTIME_CONTRACT_SCHEMA: str = (
    "ai-video-shot-continuity-source-runtime-contract/1"
)
SOURCE_RUNTIME_CONTRACT_FINGERPRINT: str = canonical_sha256(
    {
        "schema": SOURCE_RUNTIME_CONTRACT_SCHEMA,
        "hyperframes_version": HYPERFRAMES_VERSION,
        "approved_endpoint_role": "approved_endpoint",
        "composition_schema_version": "2.0",
    }
)
APPROVED_ENDPOINT_ROLE: str = "approved_endpoint"
RESOLVER_CONTRACT_FINGERPRINT: str = canonical_sha256(
    {"schema": f"{SOURCE_RUNTIME_CONTRACT_SCHEMA}:resolver"}
)
SOURCE_MATERIALIZER_CONTRACT_FINGERPRINT: str = canonical_sha256(
    {"schema": f"{SOURCE_RUNTIME_CONTRACT_SCHEMA}:source-materializer"}
)
RENDER_CONTRACT_FINGERPRINT: str = canonical_sha256(
    {"schema": f"{SOURCE_RUNTIME_CONTRACT_SCHEMA}:render"}
)
_ZERO_HASH = "0" * 64


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _sealed_composition_spec(
    *,
    project_id: str,
    shot_ids: tuple[str, ...],
    layers: tuple[CompositionLayerSpec, ...],
    delivery_profile: DeliveryProfile,
    revision: int,
) -> CompositionSpec:
    """Build one canonical, sealed ``CompositionSpec``.

    The spec is sealed through :func:`seal_artifact` so its ``content_hash`` is
    bound to the exact canonical bytes, and is revalidated through
    ``CompositionSpec.model_validate`` so any owner that consumes the helper
    observes the same artifact identity.
    """

    transitions = tuple(
        TransitionSpec(
            from_shot_id=source,
            to_shot_id=target,
            kind=TransitionKind.CUT,
            duration_frames=0,
        )
        for source, target in zip(shot_ids, shot_ids[1:])
    )
    spec = CompositionSpec(
        artifact_id="composition-rainy-station-source-qualification",
        revision=revision,
        content_hash=_ZERO_HASH,
        creation_receipt_id=SOURCE_RUNTIME_CONTRACT_FINGERPRINT,
        source_provenance=(
            SourceReference(
                kind="derived",
                reference=SOURCE_RUNTIME_CONTRACT_SCHEMA,
                content_hash=SOURCE_RUNTIME_CONTRACT_FINGERPRINT,
            ),
        ),
        composition_id=f"{project_id}-source-qualification",
        shot_ids=shot_ids,
        layers=layers,
        transitions=transitions,
        delivery_profile=delivery_profile,
        requested_renderer=RendererKind.HYPERFRAMES,
    )
    sealed = seal_artifact(spec)
    return CompositionSpec.model_validate(sealed.model_dump(mode="python"))


@dataclass(frozen=True)
class SourceRuntimeClosure:
    """Read-only projection from one canonical loaded project.

    The closure binds the canonical ``ProductionDependencyInputs``, the
    immutable ``DependencyGraphSnapshot`` it produces, and the canonical
    desired fingerprint map. It deliberately does not own Manifest state and
    never reads or writes the filesystem.
    """

    inputs: "ProductionDependencyInputs"
    graph: "DependencyGraphSnapshot"
    desired_fingerprints: Mapping[str, str]


def _approved_endpoint_layer(
    project: "LoadedProductionProject",
    shot: object,
) -> CompositionLayerSpec:
    shot_id = getattr(shot, "shot_id")
    roles = [
        role
        for role in getattr(shot, "required_asset_roles", ())
        if getattr(role, "role", None) == APPROVED_ENDPOINT_ROLE
    ]
    if len(roles) != 1:
        raise _invalid(
            "Source runtime Shot must declare exactly one approved_endpoint role.",
            detail=f"shot_id={shot_id}",
        )
    role = roles[0]
    asset_ids = tuple(getattr(role, "asset_ids", ()))
    if len(asset_ids) != 1:
        raise _invalid(
            "Source runtime approved_endpoint role must bind exactly one asset.",
            detail=f"shot_id={shot_id}",
        )
    asset_id = asset_ids[0]
    asset_record = next(
        (
            item
            for item in project.registry.assets
            if getattr(item, "asset_id", None) == asset_id
        ),
        None,
    )
    if asset_record is None:
        raise _invalid(
            "Source runtime approved_endpoint asset is not registered.",
            detail=f"shot_id={shot_id} asset_id={asset_id}",
        )
    visual_strategy = getattr(shot, "visual_strategy", None)
    expected_mime_type = (
        "image/png"
        if getattr(visual_strategy, "value", visual_strategy) == "static_image"
        else "video/mp4"
    )
    if not (
        getattr(asset_record, "mime_type", None) == expected_mime_type
        and getattr(asset_record, "width", 0) > 0
        and getattr(asset_record, "height", 0) > 0
    ):
        raise _invalid(
            "Source runtime approved_endpoint asset type does not match its Shot.",
            detail=f"shot_id={shot_id} asset_id={asset_id}",
        )
    return CompositionLayerSpec(
        layer_id=f"{shot_id}-approved-endpoint",
        shot_id=shot_id,
        asset_role=APPROVED_ENDPOINT_ROLE,
        asset_id=asset_id,
    )


def build_source_composition_spec(
    project: "LoadedProductionProject",
) -> CompositionSpec:
    """Build the sealed CompositionSpec that binds each Shot approved_endpoint.

    The spec must come from the canonical loaded project: one layer per Shot,
    each layer binding the Shot's unique ``approved_endpoint`` asset role.
    The composition is sealed through :func:`seal_artifact` so the resulting
    content hash is content-addressed.
    """

    if not project.shots:
        raise _invalid("Source runtime requires at least one canonical Shot.")
    shot_ids = tuple(getattr(shot, "shot_id") for shot in project.shots)
    if len(set(shot_ids)) != len(shot_ids):
        raise _invalid(
            "Source runtime requires unique Shot shot_ids in the canonical project."
        )
    layers = tuple(_approved_endpoint_layer(project, shot) for shot in project.shots)
    return _sealed_composition_spec(
        project_id=project.project.project_id,
        shot_ids=shot_ids,
        layers=layers,
        delivery_profile=project.project.delivery_profile,
        revision=1 + sum(getattr(shot, "revision") - 1 for shot in project.shots),
    )


def build_source_dependency_inputs(
    project: "LoadedProductionProject",
) -> "ProductionDependencyInputs":
    """Build canonical ``ProductionDependencyInputs`` for the source runtime.

    Uses the pinned HyperFrames 0.7.103 renderer identity and the stable
    :data:`SOURCE_RUNTIME_CONTRACT_FINGERPRINT` for every contract slot. The
    exact same instance is returned by
    :func:`make_source_video_candidate_preparer`, so the generic candidate
    preparer and the dependency graph observe one canonical input set.
    """

    from ai_video.production.dependency import ProductionDependencyInputs

    spec = build_source_composition_spec(project)
    return ProductionDependencyInputs(
        project=project,
        composition_spec=spec,
        renderer=RendererIdentity(
            kind=RendererKind.HYPERFRAMES, version=HYPERFRAMES_VERSION
        ),
        voice_requests=(),
        resolver_contract_fingerprint=RESOLVER_CONTRACT_FINGERPRINT,
        source_materializer_contract_fingerprint=(
            SOURCE_MATERIALIZER_CONTRACT_FINGERPRINT
        ),
        render_contract_fingerprint=RENDER_CONTRACT_FINGERPRINT,
        caption_style_fingerprints=(),
    )


def build_source_dependency_graph(
    inputs: "ProductionDependencyInputs",
) -> "DependencyGraphSnapshot":
    """Return the immutable dependency graph for the source runtime."""

    from ai_video.production.dependency import build_production_dependency_graph

    return build_production_dependency_graph(inputs)


def build_source_closure(
    project: "LoadedProductionProject",
) -> SourceRuntimeClosure:
    """Return the canonical source runtime closure for the loaded project."""

    from ai_video.production.dependency import desired_fingerprints

    inputs = build_source_dependency_inputs(project)
    graph = build_source_dependency_graph(inputs)
    desired = desired_fingerprints(graph)
    return SourceRuntimeClosure(
        inputs=inputs,
        graph=graph,
        desired_fingerprints=desired,
    )


def build_source_dependency_transition(
    *,
    committer: "ProductionStateCommitter",
    project: "LoadedProductionProject",
    graph: "DependencyGraphSnapshot",
    desired: Mapping[str, str],
) -> "DependencyGraphTransition":
    """Bind the immutable source graph through ``prepare_dependency_graph_transition``.

    The helper performs no filesystem writes; it only returns a pure
    ``DependencyGraphTransition`` so callers can hand it to
    ``ProductionStateCommitter.bootstrap_dependency_graph``.
    """

    from ai_video.production._state_commit_common import (
        prepare_dependency_graph_transition,
    )

    from ai_video.production.dependency import (
        build_applied_dependency_evidence,
        resolve_dependency_state,
    )

    manifest = committer._read_manifest()
    if manifest != project.manifest:
        raise _invalid("Source dependency graph base Manifest is stale.")
    inputs = build_source_dependency_inputs(project)
    states = resolve_dependency_state(
        graph,
        build_applied_dependency_evidence(inputs, None),
    ).states
    return prepare_dependency_graph_transition(
        expected_manifest_revision=manifest.manifest_revision,
        base_dependency_graph=project.manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired,
    )


def bootstrap_source_dependency_graph(
    committer: "ProductionStateCommitter",
    project: "LoadedProductionProject",
    *,
    attempt_id: str,
) -> tuple["DependencyGraphSnapshot", object]:
    """Bootstrap the source dependency graph exactly once.

    The closure constructs the canonical inputs and graph, derives the
    desired fingerprint map, prepares the immutable ``DependencyGraphTransition``
    through ``prepare_dependency_graph_transition``, and delegates the
    durable Manifest write to ``ProductionStateCommitter.bootstrap_dependency_graph``.
    Returns ``(graph, manifest)``.
    """

    closure = build_source_closure(project)
    transition = build_source_dependency_transition(
        committer=committer,
        project=project,
        graph=closure.graph,
        desired=closure.desired_fingerprints,
    )
    manifest = committer.bootstrap_dependency_graph(
        attempt_id=attempt_id,
        graph=closure.graph,
        transition=transition,
        expected_desired_fingerprints=closure.desired_fingerprints,
    )
    return closure.graph, manifest


def make_source_video_candidate_preparer(project: "LoadedProductionProject"):
    """Return the generic video candidate preparer bound to the source runtime.

    The closure observes the exact same :class:`ProductionDependencyInputs` as
    the canonical dependency graph built by :func:`build_source_closure`. It
    never inspects the qualification profile and never activates or submits a
    Provider call; activation and Provider effects remain with
    ``ProductionStateCommitter`` and the qualification caller.
    """

    from ai_video.production.video_candidate import make_video_candidate_preparer

    inputs = build_source_dependency_inputs(project)
    return make_video_candidate_preparer(inputs)


def make_source_production_committer(
    project_root: str | Path,
    project: "LoadedProductionProject",
) -> "ProductionStateCommitter":
    """Construct the canonical writer with the exact source candidate closure."""

    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video_candidate import make_video_candidate_preparer

    closure = build_source_closure(project)
    pointer = project.manifest.active_dependency_graph
    if (
        pointer is None
        or project.dependency_graph != closure.graph
        or pointer.content_hash != closure.graph.content_hash
    ):
        raise _invalid(
            "Source candidate committer requires the exact active dependency graph."
        )

    return ProductionStateCommitter(
        project_root,
        video_candidate_preparer=make_video_candidate_preparer(closure.inputs),
    )


__all__ = [
    "APPROVED_ENDPOINT_ROLE",
    "HYPERFRAMES_VERSION",
    "RENDER_CONTRACT_FINGERPRINT",
    "RESOLVER_CONTRACT_FINGERPRINT",
    "SOURCE_RUNTIME_CONTRACT_FINGERPRINT",
    "SOURCE_RUNTIME_CONTRACT_SCHEMA",
    "SOURCE_MATERIALIZER_CONTRACT_FINGERPRINT",
    "SourceRuntimeClosure",
    "bootstrap_source_dependency_graph",
    "build_source_closure",
    "build_source_composition_spec",
    "build_source_dependency_graph",
    "build_source_dependency_inputs",
    "build_source_dependency_transition",
    "make_source_production_committer",
    "make_source_video_candidate_preparer",
]
