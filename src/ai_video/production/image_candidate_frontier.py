"""Compare image invalidation against the same canonical baseline projection."""
from dataclasses import replace

from ai_video.production.dependency import asset_node_id, build_production_dependency_graph, resolve_dependency_state
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import DependencyLifecycle


def unchanged_nonfresh_image_nodes(*, base_inputs, base_dependency_states, resolution,
                                  request, prior_asset_ids):
    """Exclude pre-existing work only when its canonical desired identity is unchanged.

    A bootstrap graph can omit registered asset nodes. Re-projecting the current
    role makes that pre-existing work visible without claiming it is fresh.
    The candidate's new output reference is replaced only in this write-free
    baseline; delivery timing and actual dependency state remain untouched.
    """
    spec = base_inputs.composition_spec
    if any(layer.asset_id == request.output_asset_id for layer in spec.layers):
        if len(prior_asset_ids) != 1:
            # No unique bound preimage: keep the existing strict frontier.
            baseline = {state.node_id: state for state in base_dependency_states}
        else:
            previous = prior_asset_ids[0]
            layers = tuple(layer.model_copy(update={"asset_id": previous})
                if (layer.asset_id == request.output_asset_id
                    and layer.shot_id == request.target_shot_id
                    and layer.asset_role == request.target_asset_role)
                else layer for layer in spec.layers)
            spec = seal_artifact(spec.model_copy(update={"layers": layers, "content_hash": "0" * 64}))
            graph = build_production_dependency_graph(replace(base_inputs, composition_spec=spec))
            baseline = {state.node_id: state for state in
                resolve_dependency_state(graph, base_dependency_states).states}
    else:
        graph = build_production_dependency_graph(base_inputs)
        baseline = {state.node_id: state for state in
            resolve_dependency_state(graph, base_dependency_states).states}
    original = {state.node_id: state for state in base_dependency_states}
    registered_assets = {asset_node_id(asset.asset_id) for asset in base_inputs.project.registry.assets}
    return {state.node_id for state in resolution.states
        if state.node_id in baseline
        and baseline[state.node_id].lifecycle is not DependencyLifecycle.FRESH
        and baseline[state.node_id].desired_fingerprint == state.desired_fingerprint
        and ((state.node_id in original
              and original[state.node_id].lifecycle is not DependencyLifecycle.FRESH
              and original[state.node_id].desired_fingerprint == state.desired_fingerprint)
             or (state.node_id not in original and state.node_id in registered_assets))}
