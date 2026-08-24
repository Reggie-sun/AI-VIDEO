from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
import ai_video.production.shot_continuity_m0_qualification as m0_qualification
import ai_video.production.shot_continuity_source_stack as source_stack_module
from ai_video.production.hashing import canonical_sha256
from ai_video.production.shot_continuity_m0_qualification import (
    M0QualificationCompileInputs,
    compile_m0_qualification_workflow,
    derive_m0_qualification_seed,
    load_m0_qualification_execution_sources,
    validate_m0_sources_against_stack,
)
from ai_video.production.shot_continuity_source_stack import (
    load_shot_continuity_source_execution_sources,
    validate_shot_continuity_source_stack,
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

EXPECTED_NODE_SCHEMA_SEALS = (
    ("UNETLoader", "0803bca8808c9e196cac6a5029c01943786166ec1c643e00389b8bdc1396c8ee"),
    ("CLIPLoader", "e9f485efa1b625aed932d738f4bd78e1770f573acbe551c2a800972d92ee1385"),
    ("VAELoader", "437f9bf7258fa818125a864fb43fdefa5f1fdc5b80a4f6f318a76bc9d21a9f4e"),
    ("MiniMaxH3AudioConditioningT8", "26bc55ff0ef05087f4f0b79b23b2e6a06988bc46325e0bb46114f8ffedf714ca"),
    ("MiniMaxH3DualClockSamplerT8", "3543e78f8adea01f8b80f154206c80ced606675f74be70ad624baedf30045b34"),
    ("RandomNoise", "41d9d603f14caf9196ebc80c5b5a5f68d4c303341b307a3a1230c461d64eebcc"),
    ("BasicGuider", "c561c18f4ab40c62009ced56fce369d4cdcbc5fbc3b8f2e0cbb654b475c0940b"),
    ("SamplerCustomAdvanced", "261a495a933da3a3ffd113e1f909c0d714a60e4643eac6a057a1c488ffa19716"),
    ("MiniMaxH3AVDecodeT8", "3856b31ab00fbf3f02d53589c18fd1487a272fe6d0be870fcb5dab93febc2930"),
    ("VHS_VideoCombine", "d718d775baa3c3e3e0f3323f3d82ffc6eedf79c5a2b8df721abe1b52f0f8c231"),
    ("LoadImage", "ecf1b0bb9558c1a84dea6e1fcf4f9a9d79ac5d09ed557092f1c062abcef4ead6"),
    ("VHS_LoadVideo", "59389f8b463b29fd0571e4fe2dc99f2cea8ee7ad6fe8752d171411b10ca12b34"),
)


def _inputs(**updates: object) -> M0QualificationCompileInputs:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    values = {
        "prompt": FROZEN_PROMPT,
        "seed": profile["sealed_seed"],
        "first_frame": "a1.png",
        "last_frame": "a2.png",
        "reference": "identity.png",
        "reference_video": "motion.mp4",
    }
    values.update(updates)
    return M0QualificationCompileInputs(**values)


def _object_info() -> dict[str, object]:
    result: dict[str, object] = {}
    for node_name, _ in EXPECTED_NODE_SCHEMA_SEALS:
        required = {"value": ["INT", {"default": 1}]}
        if node_name == "LoadImage":
            required = {"image": [["before.png"], {"image_upload": True}]}
        elif node_name == "VHS_LoadVideo":
            required = {"video": [["before.mp4"], {"video_upload": True}]}
        result[node_name] = {
            "input": {"required": required},
            "input_order": {"required": list(required)},
            "output_name": ["OUTPUT"],
        }
    return result


def test_source_stack_seals_exact_local_fl2va_quality_sources() -> None:
    sources = load_shot_continuity_source_execution_sources(
        artifact_root=REPO_ROOT,
    )

    assert sources.materialization.candidate_label == "source"
    assert sources.initial_stack.materialization_status == "unmaterialized"
    assert sources.materialized_stack.materialization_status == "materialized"
    assert sources.materialized_stack.execution_stack_hash != (
        sources.initial_stack.execution_stack_hash
    )
    assert sources.materialized_stack.profile_hash == hashlib.sha256(
        sources.materialization.profile_bytes
    ).hexdigest()
    assert tuple(item.component_id for item in sources.initial_stack.components) == (
        "pruned-fl2va",
        "qwen-clip",
        "video-vae",
        "audio-vae",
    )
    validate_shot_continuity_source_stack(sources, sources.initial_stack)
    validate_shot_continuity_source_stack(sources, sources.materialized_stack)


def test_source_stack_rejects_profile_or_identity_drift(tmp_path: Path) -> None:
    canonical = json.loads(
        (REPO_ROOT / "workflows/profiles/minimax_h3_fl2va_quality.json").read_text(
            encoding="utf-8"
        )
    )
    canonical["cloud_fallback_enabled"] = True
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(canonical), encoding="utf-8")

    with pytest.raises(AiVideoError, match="profile"):
        load_shot_continuity_source_execution_sources(
            artifact_root=tmp_path,
            profile_path=profile_path,
        )

    sources = load_shot_continuity_source_execution_sources(
        artifact_root=REPO_ROOT,
    )
    changed = GenerationExecutionStackIdentity.create(
        **{
            **{
                name: getattr(sources.initial_stack, name)
                for name in type(sources.initial_stack).model_fields
                if name != "execution_stack_hash"
            },
            "candidate_id": "different-source",
        }
    )
    with pytest.raises(AiVideoError, match="exact execution sources"):
        validate_shot_continuity_source_stack(sources, changed)


@pytest.mark.parametrize("drift", ("workflow", "binding"))
def test_source_stack_rejects_internally_resealed_semantic_drift(
    tmp_path: Path,
    drift: str,
) -> None:
    profile = json.loads(
        (REPO_ROOT / "workflows/profiles/minimax_h3_fl2va_quality.json").read_text(
            encoding="utf-8"
        )
    )
    workflow = json.loads((REPO_ROOT / profile["workflow_path"]).read_text())
    binding = (REPO_ROOT / profile["binding_path"]).read_text(encoding="utf-8")
    if drift == "workflow":
        workflow["8"]["inputs"]["sampler_name"] = "euler"
    else:
        binding = binding.replace(
            'prompt: ["5", "inputs", "prompt"]',
            'prompt: ["6", "inputs", "noise_seed"]',
        )

    workflow_path = tmp_path / profile["workflow_path"]
    binding_path = tmp_path / profile["binding_path"]
    profile_path = tmp_path / "workflows/profiles/source.json"
    workflow_path.parent.mkdir(parents=True)
    binding_path.parent.mkdir(parents=True)
    profile_path.parent.mkdir(parents=True)
    workflow_payload = json.dumps(workflow).encode()
    binding_payload = binding.encode()
    workflow_path.write_bytes(workflow_payload)
    binding_path.write_bytes(binding_payload)
    profile["workflow_sha256"] = hashlib.sha256(workflow_payload).hexdigest()
    profile["binding_sha256"] = hashlib.sha256(binding_payload).hexdigest()
    profile["profile_content_hash"] = canonical_sha256(
        {key: value for key, value in profile.items() if key != "profile_content_hash"}
    )
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(AiVideoError, match="topology|bindings|settings"):
        load_shot_continuity_source_execution_sources(
            artifact_root=tmp_path,
            profile_path=profile_path,
        )


def test_source_stack_validates_and_seals_the_same_reopened_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_relative = Path("workflows/profiles/minimax_h3_fl2va_quality.json")
    profile_path = tmp_path / profile_relative
    profile_bytes = (REPO_ROOT / profile_relative).read_bytes()
    profile = json.loads(profile_bytes)
    workflow_path = tmp_path / profile["workflow_path"]
    binding_path = tmp_path / profile["binding_path"]
    compiler_path = tmp_path / "compiler.py"
    workflow_bytes = (REPO_ROOT / profile["workflow_path"]).read_bytes()
    binding_bytes = (REPO_ROOT / profile["binding_path"]).read_bytes()
    for path, payload in (
        (profile_path, profile_bytes),
        (workflow_path, workflow_bytes),
        (binding_path, binding_bytes),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    compiler_path.write_bytes(Path(source_stack_module.comfy_video.__file__).read_bytes())
    monkeypatch.setattr(
        source_stack_module.comfy_video,
        "__file__",
        str(compiler_path),
    )

    original_read = source_stack_module._read_regular_file_nofollow
    replaced: set[Path] = set()

    def replace_after_read(path: Path, **kwargs: object) -> object:
        snapshot = original_read(path, **kwargs)
        resolved = Path(path).resolve()
        if resolved == profile_path.resolve() and resolved not in replaced:
            profile_path.write_text("{}", encoding="utf-8")
            replaced.add(resolved)
        elif resolved == workflow_path.resolve() and resolved not in replaced:
            workflow_path.write_text("{}", encoding="utf-8")
            replaced.add(resolved)
        return snapshot

    monkeypatch.setattr(
        source_stack_module,
        "_read_regular_file_nofollow",
        replace_after_read,
    )

    sources = load_shot_continuity_source_execution_sources(
        artifact_root=tmp_path,
        profile_path=profile_path,
    )

    assert sources.materialization.workflow_bytes == workflow_bytes
    assert sources.profile.profile_content_hash == profile["profile_content_hash"]
    assert replaced == {profile_path.resolve(), workflow_path.resolve()}


def test_m0_profile_seals_exact_live_node_schemas() -> None:
    sources = load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )

    assert tuple(
        (item.node_name, item.schema_sha256)
        for item in sources.profile.node_schema_seals
    ) == EXPECTED_NODE_SCHEMA_SEALS
    assert sources.profile.sealed_seed == derive_m0_qualification_seed(
        sources.profile.model_dump(mode="python")
    )


@pytest.mark.parametrize("mutation", ("missing", "drift"))
def test_m0_profile_rejects_missing_or_drifted_sealed_seed(mutation: str) -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    if mutation == "missing":
        profile.pop("sealed_seed")
    else:
        profile["sealed_seed"] += 1

    with pytest.raises(ValueError, match="sealed_seed|sealed seed"):
        m0_qualification.M0QualificationProfile.model_validate(profile)


def test_m0_profile_rejects_incomplete_node_schema_seals() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    profile["node_schema_seals"] = profile["node_schema_seals"][:-1]

    with pytest.raises(ValueError, match="node_schema_seals"):
        m0_qualification.M0QualificationProfile.model_validate(profile)


def test_m0_live_node_schema_preflight_replays_and_denies_drift() -> None:
    sources = load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    object_info = _object_info()
    sealed = m0_qualification.m0_node_schema_seals(object_info)
    test_sources = replace(
        sources,
        profile=sources.profile.model_copy(update={"node_schema_seals": sealed}),
    )

    m0_qualification.validate_m0_live_node_schemas(object_info, test_sources)

    drifted = json.loads(json.dumps(object_info))
    drifted["UNETLoader"]["input"]["required"]["value"][1]["default"] = 2
    with pytest.raises(AiVideoError, match="node schema"):
        m0_qualification.validate_m0_live_node_schemas(drifted, test_sources)

    missing = dict(object_info)
    missing.pop("VHS_LoadVideo")
    with pytest.raises(AiVideoError, match="node schema"):
        m0_qualification.validate_m0_live_node_schemas(missing, test_sources)


def test_m0_node_schema_seals_ignore_runtime_file_inventory() -> None:
    before = _object_info()
    after = json.loads(json.dumps(before))
    after["LoadImage"]["input"]["required"]["image"][0] = ["after.png"]
    after["VHS_LoadVideo"]["input"]["required"]["video"][0] = ["after.mp4"]

    assert m0_qualification.m0_node_schema_seals(
        before
    ) == m0_qualification.m0_node_schema_seals(after)


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
    assert workflow["8"]["inputs"]["noise_seed"] == sources.profile.sealed_seed
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
