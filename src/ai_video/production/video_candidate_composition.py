"""Pure CompositionSpec projection for a generated-video candidate."""

from __future__ import annotations

from dataclasses import replace

from ai_video.production.dependency import ProductionDependencyInputs
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import CompositionSpec, LoadedProductionProject


_ZERO_HASH = "0" * 64


def build_video_candidate_composition_spec(
    base_spec: CompositionSpec,
    *,
    target_shot_id: str,
    target_asset_role: str,
    output_asset_id: str,
) -> CompositionSpec:
    """Reseal the one Composition layer replaced by a generated video."""

    target_layers = tuple(
        layer
        for layer in base_spec.layers
        if layer.shot_id == target_shot_id
        and layer.asset_role == target_asset_role
    )
    if len(target_layers) != 1:
        raise ValueError(
            "Video activation target must bind one exact CompositionSpec layer."
        )
    return seal_artifact(
        base_spec.model_copy(
            update={
                "revision": base_spec.revision + 1,
                "content_hash": _ZERO_HASH,
                "layers": tuple(
                    layer.model_copy(update={"asset_id": output_asset_id})
                    if layer == target_layers[0]
                    else layer
                    for layer in base_spec.layers
                ),
            }
        )
    )


def video_candidate_dependency_inputs_are_exact(
    *,
    candidate_inputs: ProductionDependencyInputs,
    base_inputs: ProductionDependencyInputs,
    candidate_project: LoadedProductionProject,
    base_project: LoadedProductionProject,
    target_shot_id: str,
    target_asset_role: str,
    output_asset_id: str,
) -> bool:
    """Return whether only Project and the exact target layer changed."""

    if (
        candidate_inputs.project != candidate_project
        or replace(
            candidate_inputs,
            project=base_project,
            composition_spec=base_inputs.composition_spec,
        )
        != base_inputs
    ):
        return False
    try:
        expected_spec = build_video_candidate_composition_spec(
            base_inputs.composition_spec,
            target_shot_id=target_shot_id,
            target_asset_role=target_asset_role,
            output_asset_id=output_asset_id,
        )
    except ValueError:
        return False
    return candidate_inputs.composition_spec == expected_spec


__all__ = [
    "build_video_candidate_composition_spec",
    "video_candidate_dependency_inputs_are_exact",
]
