from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
import ai_video.production.shot_continuity_m0_qualification as m0_qualification
from ai_video.production.shot_continuity_m0_qualification import (
    M0QualificationCompileInputs,
    compile_m0_qualification_workflow,
    load_m0_qualification_execution_sources,
    validate_m0_sources_against_stack,
)
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    StackComponentIdentity,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json"
FROZEN_PROMPT = """For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced as the exact first frame; the ending frame aligns with <Picture 2>; <Picture 3> fully defines identity and wardrobe; <Video 1> supplies the opening gait phase and parallel camera velocity.

integrated_multimodal_description: [Shot 1] Live-action, photorealistic cinematic medium right-facing side-profile shot on the same rain-soaked railway platform at blue hour. The exact same lone adult East Asian woman with a short blunt black bob, mustard-yellow hooded raincoat, black trousers, black boots and the same red cross-body leather satchel walks steadily screen-right toward the clock. A chest-height 50mm-equivalent camera tracks parallel with small amplitude at slow constant speed, keeping a level horizon and stable body scale. She preserves the supplied gait phase, decelerates naturally, and arrives at the exact approved last-frame pose. Exactly one person; no cut, zoom, axis reversal, teleport, text, logo, wardrobe change or unmotivated camera movement.
overall_soundscape: Steady rain strikes the platform roof and wet concrete. Measured boot footsteps and a small physical leather-satchel movement remain synchronized with the walk; distant station ambience stays restrained.
non_diegetic_music: No non-diegetic music."""


def _inputs(**updates: object) -> M0QualificationCompileInputs:
    values = {
        "prompt": FROZEN_PROMPT,
        "seed": 1234,
        "first_frame": "a1.png",
        "last_frame": "a2.png",
        "reference": "identity.png",
        "reference_video": "motion.mp4",
    }
    values.update(updates)
    return M0QualificationCompileInputs(**values)


def test_m0_sources_are_exact_and_compile_literal_hybrid_stock20() -> None:
    sources = load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    workflow = compile_m0_qualification_workflow(
        sources=sources,
        inputs=_inputs(),
    )

    assert sources.materialization.candidate_label == "m0"
    assert sources.materialization.profile_hash == hashlib.sha256(
        sources.materialization.profile_bytes
    ).hexdigest()
    assert sources.materialization.compiler_hash == hashlib.sha256(
        sources.materialization.compiler_bytes
    ).hexdigest()
    assert sources.materialization.workflow_hash == hashlib.sha256(
        sources.materialization.workflow_bytes
    ).hexdigest()
    profile_source = json.loads(sources.materialization.profile_bytes)
    assert set(profile_source) == {
        "binding_bytes_base64",
        "profile_bytes_base64",
        "schema_version",
    }
    assert workflow["6"]["inputs"]["task_type"] == "Hybrid"
    assert workflow["7"]["inputs"] == {
        "av_latent": ["6", 1],
        "model": ["1", 0],
        "sampler_name": "dual_clock_euler",
        "scheduler": "native_flow",
        "shift_audio": 3.0,
        "shift_video": 12.0,
        "steps": 20,
    }
    conditioning = workflow["6"]["inputs"]
    assert conditioning["first_frame"] == ["13", 0]
    assert conditioning["last_frame"] == ["14", 0]
    assert conditioning["ref_images.ref_image_0"] == ["15", 0]
    assert conditioning["ref_videos.ref_video_0"] == ["16", 0]
    assert not any(key.startswith("ref_video_audios") for key in conditioning)
    assert not any(key.startswith("ref_audios") for key in conditioning)
    assert workflow["13"]["inputs"]["image"] == "a1.png"
    assert workflow["14"]["inputs"]["image"] == "a2.png"
    assert workflow["15"]["inputs"]["image"] == "identity.png"
    assert workflow["16"]["inputs"]["video"] == "motion.mp4"
    assert all(
        node["class_type"] not in {"LoraLoaderBypassModelOnly", "LoraLoader"}
        for node in workflow.values()
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("first_frame", ""),
        ("last_frame", ""),
        ("reference", ""),
        ("reference_video", ""),
    ),
)
def test_m0_compiler_rejects_missing_exact_anchor(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        _inputs(**{field: value})


def test_m0_compiler_rejects_prompt_drift() -> None:
    sources = load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    with pytest.raises(AiVideoError, match="prompt"):
        compile_m0_qualification_workflow(
            sources=sources,
            inputs=_inputs(prompt=FROZEN_PROMPT + " drift"),
        )


def test_m0_source_loader_rejects_profile_or_workflow_drift(tmp_path: Path) -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    copied_workflow = tmp_path / "workflow.json"
    copied_binding = tmp_path / "binding.yaml"
    copied_workflow.write_bytes(
        (REPO_ROOT / profile["workflow_path"]).read_bytes() + b"\n"
    )
    copied_binding.write_bytes((REPO_ROOT / profile["binding_path"]).read_bytes())
    profile["workflow_path"] = copied_workflow.name
    profile["binding_path"] = copied_binding.name
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(AiVideoError, match="hash"):
        load_m0_qualification_execution_sources(
            profile_path=profile_path,
            artifact_root=tmp_path,
        )


def test_m0_source_loader_rejects_resealed_node_id_class_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    workflow = json.loads(
        (REPO_ROOT / profile["workflow_path"]).read_text(encoding="utf-8")
    )
    workflow["13"]["class_type"], workflow["16"]["class_type"] = (
        workflow["16"]["class_type"],
        workflow["13"]["class_type"],
    )
    workflow_path = tmp_path / "workflow.json"
    workflow_bytes = json.dumps(
        workflow,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    workflow_path.write_bytes(workflow_bytes)
    binding_path = tmp_path / "binding.yaml"
    binding_bytes = (REPO_ROOT / profile["binding_path"]).read_bytes()
    binding_path.write_bytes(binding_bytes)
    compiler_path = tmp_path / "compiler.py"
    compiler_path.write_text("# test compiler identity\n", encoding="utf-8")
    monkeypatch.setattr(m0_qualification, "__file__", str(compiler_path))
    profile.update(
        {
            "workflow_path": workflow_path.name,
            "workflow_sha256": hashlib.sha256(workflow_bytes).hexdigest(),
            "binding_path": binding_path.name,
            "binding_sha256": hashlib.sha256(binding_bytes).hexdigest(),
        }
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(AiVideoError, match="sealed contract"):
        m0_qualification.load_m0_qualification_execution_sources(
            profile_path=profile_path,
            artifact_root=tmp_path,
        )


def test_m0_sources_reject_candidate_identity_drift() -> None:
    sources = load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    profile = sources.profile
    values = {
        "materialization_status": "unmaterialized",
        "candidate_id": profile.candidate_id,
        "contract_version": profile.contract_version,
        "provider_kind": profile.provider_kind,
        "deployment_identity": profile.deployment_identity,
        "model_id": profile.model_id,
        "capability_id": profile.capability_id,
        "profile_hash": "none",
        "compiler_hash": "none",
        "workflow_hash": "none",
        "components": tuple(
            StackComponentIdentity(
                ordinal=ordinal,
                kind=item.kind,
                component_id=item.component_id,
                content_hash=item.sha256,
            )
            for ordinal, item in enumerate(profile.components)
        ),
        "sampler_identity": profile.sampler,
        "scheduler_identity": profile.scheduler,
        "runtime_seals": profile.runtime_seals,
        "output_contract_hash": profile.output_contract_hash,
    }
    stack = GenerationExecutionStackIdentity.create(**values)
    assert stack.execution_stack_hash == profile.initial_execution_stack_hash
    validate_m0_sources_against_stack(sources, stack)

    drifted = GenerationExecutionStackIdentity.create(
        **{**values, "candidate_id": "m0-drifted-candidate"}
    )
    with pytest.raises(AiVideoError, match="selected stack"):
        validate_m0_sources_against_stack(sources, drifted)
