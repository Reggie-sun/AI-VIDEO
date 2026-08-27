from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.shot_continuity_m0_fast_validation import (
    compile_m0_fast_qualification_workflow,
    load_m0_fast_qualification_execution_sources,
    validate_m0_fast_sources_against_stack,
)
from ai_video.production.shot_continuity_m0_qualification import (
    M0QualificationCompileInputs,
)
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    StackComponentIdentity,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/"
    "minimax_h3_t8_c4_m0_fast_v1_profile.json"
)
QUALITY_COMPILER_SHA256 = "a6ece8f8fb7da5a0d0b4ece0a2924e5a2d68d79d682ad20f66075a4cc2a73f14"
FROZEN_PROMPT = """For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced as the exact first frame; the ending frame aligns with <Picture 2>; <Picture 3> fully defines identity and wardrobe; <Video 1> supplies the opening gait phase and parallel camera velocity.

integrated_multimodal_description: [Shot 1] Live-action, photorealistic cinematic medium right-facing side-profile shot on the same rain-soaked railway platform at blue hour. The exact same lone adult East Asian woman with a short blunt black bob, mustard-yellow hooded raincoat, black trousers, black boots and the same red cross-body leather satchel walks steadily screen-right toward the clock. A chest-height 50mm-equivalent camera tracks parallel with small amplitude at slow constant speed, keeping a level horizon and stable body scale. She preserves the supplied gait phase, decelerates naturally, and arrives at the exact approved last-frame pose. Exactly one person; no cut, zoom, axis reversal, teleport, text, logo, wardrobe change or unmotivated camera movement.
overall_soundscape: Steady rain strikes the platform roof and wet concrete. Measured boot footsteps and a small physical leather-satchel movement remain synchronized with the walk; distant station ambience stays restrained.
non_diegetic_music: No non-diegetic music."""


def _inputs(seed: int) -> M0QualificationCompileInputs:
    return M0QualificationCompileInputs(
        prompt=FROZEN_PROMPT,
        seed=seed,
        first_frame="first.png",
        last_frame="last.png",
        reference="identity.png",
        reference_video="motion.mp4",
    )


def _initial_stack(sources: object) -> GenerationExecutionStackIdentity:
    profile = sources.profile
    return GenerationExecutionStackIdentity.create(
        materialization_status="unmaterialized",
        candidate_id=profile.candidate_id,
        contract_version=profile.contract_version,
        provider_kind=profile.provider_kind,
        deployment_identity=profile.deployment_identity,
        model_id=profile.model_id,
        capability_id=profile.capability_id,
        profile_hash="none",
        compiler_hash="none",
        workflow_hash="none",
        components=tuple(
            StackComponentIdentity(
                ordinal=ordinal,
                kind=item.kind,
                component_id=item.component_id,
                content_hash=item.sha256,
            )
            for ordinal, item in enumerate(profile.components)
        ),
        sampler_identity=profile.sampler,
        scheduler_identity=profile.scheduler,
        runtime_seals=profile.runtime_seals,
        output_contract_hash=profile.output_contract_hash,
    )


def test_fast_sources_seal_hybrid_four_anchor_turbo4_without_mutating_quality_compiler() -> None:
    sources = load_m0_fast_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    workflow = compile_m0_fast_qualification_workflow(
        sources=sources,
        inputs=_inputs(sources.profile.sealed_seed),
    )

    assert sources.profile.validation_policy_id == "fast-v1"
    assert sources.profile.task_type == "Hybrid"
    assert sources.profile.steps == 4
    assert sources.profile.turbo_lora is True
    assert sources.profile.lora.filename == (
        "minimax_h3_turbo_4step_ema_comfyui.safetensors"
    )
    assert sources.profile.lora.sha256 == (
        "5b8ad6cb7ac206852006f4efa3ce2d679cd6ffb5d5b8a4edce8e981393289df5"
    )
    assert workflow["2"] == {
        "class_type": "LoraLoaderBypassModelOnly",
        "inputs": {
            "lora_name": sources.profile.lora.filename,
            "model": ["1", 0],
            "strength_model": 1.0,
        },
    }
    assert workflow["7"]["inputs"]["model"] == ["2", 0]
    assert workflow["7"]["inputs"]["steps"] == 4
    conditioning = workflow["6"]["inputs"]
    assert conditioning["first_frame"] == ["13", 0]
    assert conditioning["last_frame"] == ["14", 0]
    assert conditioning["ref_images.ref_image_0"] == ["15", 0]
    assert conditioning["ref_videos.ref_video_0"] == ["16", 0]
    assert hashlib.sha256(
        (REPO_ROOT / "src/ai_video/production/shot_continuity_m0_qualification.py").read_bytes()
    ).hexdigest() == QUALITY_COMPILER_SHA256


def test_fast_stack_identity_is_distinct_and_exactly_validated() -> None:
    sources = load_m0_fast_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    initial = _initial_stack(sources)

    assert initial.execution_stack_hash == sources.profile.initial_execution_stack_hash
    assert initial.execution_stack_hash != sources.profile.quality_execution_stack_hash
    validate_m0_fast_sources_against_stack(sources, initial)
    validate_m0_fast_sources_against_stack(
        sources,
        initial.materialize(sources.materialization),
    )

    drifted = initial.model_copy(update={"capability_id": "quality"})
    with pytest.raises(AiVideoError, match="selected stack identity"):
        validate_m0_fast_sources_against_stack(sources, drifted)


def test_fast_profile_and_workflow_bytes_are_content_addressed() -> None:
    profile_bytes = PROFILE_PATH.read_bytes()
    profile = json.loads(profile_bytes)
    workflow = REPO_ROOT / profile["workflow_path"]
    binding = REPO_ROOT / profile["binding_path"]

    assert hashlib.sha256(workflow.read_bytes()).hexdigest() == profile["workflow_sha256"]
    assert hashlib.sha256(binding.read_bytes()).hexdigest() == profile["binding_sha256"]


@pytest.mark.parametrize(
    ("node_id", "input_name", "drifted_value"),
    (
        ("9", "conditioning", ["8", 0]),
        ("10", "guider", ["8", 0]),
        ("11", "av_latent", ["9", 0]),
    ),
)
def test_fast_compiler_rejects_internal_dataflow_drift(
    node_id: str,
    input_name: str,
    drifted_value: list[object],
) -> None:
    sources = load_m0_fast_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    drifted = copy.deepcopy(sources)
    drifted.workflow[node_id]["inputs"][input_name] = drifted_value

    with pytest.raises(AiVideoError, match="sealed contract"):
        compile_m0_fast_qualification_workflow(
            sources=drifted,
            inputs=_inputs(sources.profile.sealed_seed),
        )
