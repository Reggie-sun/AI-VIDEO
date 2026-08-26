from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import ai_video.production.shot_continuity_m0_qualification as m0_qualification
import ai_video.production.shot_continuity_m0_fast_validation as m0_fast
import ai_video.production.shot_continuity_source_stack as source_stack_module
import scripts.materialize_shot_continuity_m0 as materialize_script
import pytest
from PIL import Image

from ai_video.errors import AiVideoError
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
from ai_video.production.paths import (
    canonical_execution_stack_materialization_source_path,
    canonical_p0_qualification_input_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_m0_policy import M0ValidationPolicyId
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    StackComponentIdentity,
)
from scripts.materialize_shot_continuity_m0 import materialize
from scripts.prepare_shot_continuity_p0 import prepare


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/"
    "minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)
FAST_PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/"
    "minimax_h3_t8_c4_m0_fast_v1_profile.json"
)


def _materialized_m0(sources) -> GenerationExecutionStackIdentity:
    profile = sources.profile
    unmaterialized = GenerationExecutionStackIdentity.create(
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
    assert unmaterialized.execution_stack_hash == profile.initial_execution_stack_hash
    return unmaterialized.materialize(sources.materialization)


def _bundle(sources):
    profile = sources.profile
    m0 = _materialized_m0(sources)
    m1 = SimpleNamespace(
        execution_stack_hash=profile.m1_execution_stack_hash,
        materialization_status="unmaterialized",
        components=(
            SimpleNamespace(
                component_id="hybrid-artifact-candidate-v1",
                presence="absent",
                content_hash="none",
            ),
        ),
    )
    receipt = SimpleNamespace(
        content_hash="a" * 64,
        project=SimpleNamespace(content_hash=profile.project_content_hash),
        registry=SimpleNamespace(content_hash=profile.registry_content_hash),
    )
    policies = (
        SimpleNamespace(
            policy_hash="b" * 64,
            source_execution_stack_hash=m0.execution_stack_hash,
            destination_execution_stack_hash=m0.execution_stack_hash,
        ),
        SimpleNamespace(
            policy_hash="c" * 64,
            source_execution_stack_hash=m0.execution_stack_hash,
            destination_execution_stack_hash=m0.execution_stack_hash,
        ),
        SimpleNamespace(
            policy_hash="d" * 64,
            source_execution_stack_hash=m0.execution_stack_hash,
            destination_execution_stack_hash=m0.execution_stack_hash,
        ),
    )
    validation_set = SimpleNamespace(content_hash="e" * 64)
    calibration = SimpleNamespace(
        input_kind="calibration_fixture",
        content_hash="f" * 64,
        execution_stack_hashes=(m0.execution_stack_hash,),
        payload={
            "prompt_sha256": profile.prompt_sha256,
            "task_type": profile.task_type,
            "steps": profile.steps,
            "sampler": profile.sampler,
            "scheduler": profile.scheduler,
            "turbo_lora": profile.turbo_lora,
        },
    )
    inputs = (
        calibration,
        SimpleNamespace(
            input_kind="effect_budget",
            content_hash="1" * 64,
            execution_stack_hashes=(m0.execution_stack_hash,),
            payload={},
        ),
    )
    return receipt, (m0, m1), policies, validation_set, inputs


def _resolved_m0_request(sources, stack_hash: str):
    profile = sources.profile
    return SimpleNamespace(
        execution_stack_hash=stack_hash,
        provider_name=profile.provider_kind,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        capability_id=profile.capability_id,
        provider_profile=SimpleNamespace(
            profile_id=profile.candidate_id,
            profile_version=f"v{profile.contract_version}",
            profile_sha256=sources.profile_document_hash,
        ),
        adapter_compiler_hash=sources.materialization.compiler_hash,
        execution_kind=SimpleNamespace(value="local"),
        billing_kind=SimpleNamespace(value="local_unmetered"),
        mode=SimpleNamespace(value="image_to_video"),
        prompt_text=(
            "For the target video, at 0.00 seconds into the target video, "
            "<Picture 1> (from [Shot 1]) is fully referenced as the exact first "
            "frame; the ending frame aligns with <Picture 2>; <Picture 3> fully "
            "defines identity and wardrobe; <Video 1> supplies the opening gait "
            "phase and parallel camera velocity.\n\n"
            "integrated_multimodal_description: [Shot 1] Live-action, "
            "photorealistic cinematic medium right-facing side-profile shot on "
            "the same rain-soaked railway platform at blue hour. The exact same "
            "lone adult East Asian woman with a short blunt black bob, "
            "mustard-yellow hooded raincoat, black trousers, black boots and the "
            "same red cross-body leather satchel walks steadily screen-right "
            "toward the clock. A chest-height 50mm-equivalent camera tracks "
            "parallel with small amplitude at slow constant speed, keeping a "
            "level horizon and stable body scale. She preserves the supplied "
            "gait phase, decelerates naturally, and arrives at the exact approved "
            "last-frame pose. Exactly one person; no cut, zoom, axis reversal, "
            "teleport, text, logo, wardrobe change or unmotivated camera "
            "movement.\n"
            "overall_soundscape: Steady rain strikes the platform roof and wet "
            "concrete. Measured boot footsteps and a small physical leather-"
            "satchel movement remain synchronized with the walk; distant station "
            "ambience stays restrained.\n"
            "non_diegetic_music: No non-diegetic music."
        ),
        effective_seed=profile.sealed_seed,
        effective_negative_prompt_text="",
        image_bindings=tuple(
            SimpleNamespace(role=role)
            for role in ("first_frame", "last_frame", "reference")
        ),
        media_bindings=(
            SimpleNamespace(kind="video", role="reference_video"),
        ),
        c4_multi_anchor_binding=SimpleNamespace(
            tier=SimpleNamespace(value="motion_boundary"),
            motion_tail=SimpleNamespace(content_hash="1" * 64),
        ),
        effective_output=SimpleNamespace(
            timing_mode="frame_count",
            frame_count=profile.frame_count,
            duration_seconds=None,
            dimension_mode="exact",
            width=profile.width,
            height=profile.height,
            fps=profile.fps,
            container=profile.output_container,
            mime_type="video/mp4",
            native_audio=profile.native_audio,
        ),
    )


class _ReadOnlyCommitter:
    def __init__(self, bundle) -> None:
        self.bundle = bundle
        self.reopen_calls: list[tuple[str, ...]] = []

    def reopen_p0_qualification_prepared(
        self, *, required_materialized_candidates: tuple[str, ...]
    ):
        self.reopen_calls.append(required_materialized_candidates)
        return self.bundle

    def reopen_p0_qualification_source_stacks(
        self, *, require_materialized: bool = False
    ):
        return ()


def _tree_snapshot(root: Path) -> dict[str, tuple[int, int, str]]:
    return {
        path.relative_to(root).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _real_materialized_committer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    policy_id: M0ValidationPolicyId = M0ValidationPolicyId.QUALITY_V1,
) -> tuple[ProductionStateCommitter, Path, Path]:
    profile_module = (
        m0_fast
        if policy_id is M0ValidationPolicyId.FAST_V1
        else m0_qualification
    )
    canonical_profile_path = (
        FAST_PROFILE_PATH
        if policy_id is M0ValidationPolicyId.FAST_V1
        else PROFILE_PATH
    )
    source_root = tmp_path / "sources"
    source_root.mkdir()
    image_paths = tuple(source_root / f"a{index}.png" for index in range(1, 5))
    for index, path in enumerate(image_paths, start=1):
        Image.new("RGB", (1659, 948), (index * 20, index * 30, index * 40)).save(path)
    (source_root / "metadata.json").write_text(
        json.dumps(
            {
                "backend": "chatgpt-web",
                "mode": "direct-typescript-browser",
                "prompt": "Frozen rainy-station qualification reference.",
                "created_at": "2026-08-23T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    root = tmp_path / "project"
    prepare(
        SimpleNamespace(
            root=root,
            a1=image_paths[0],
            a2=image_paths[1],
            a3=image_paths[2],
            a4=image_paths[3],
            approved_at="2026-08-23T00:01:00+00:00",
            imported_at="2026-08-23T00:02:00+00:00",
            m0_policy=policy_id,
        )
    )
    committer = ProductionStateCommitter(root)
    receipt, _, _, _, _ = committer.reopen_p0_qualification_prepared()
    profile = json.loads(canonical_profile_path.read_text(encoding="utf-8"))
    profile.update(
        {
            "project_content_hash": receipt.project.content_hash,
            "registry_content_hash": receipt.registry.content_hash,
            "prepared_receipt_hash": receipt.content_hash,
        }
    )
    profile["sealed_seed"] = (
        m0_fast.derive_m0_fast_qualification_seed(profile)
        if policy_id is M0ValidationPolicyId.FAST_V1
        else m0_qualification.derive_m0_qualification_seed(profile)
    )
    artifact_root = tmp_path / "artifacts"
    profile_path = artifact_root / "workflows/qualification/profile.json"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    for relative in (profile["workflow_path"], profile["binding_path"]):
        copied = artifact_root / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes((REPO_ROOT / relative).read_bytes())
    compiler_path = (
        artifact_root
        / f"src/ai_video/production/{Path(profile_module.__file__).name}"
    )
    compiler_path.parent.mkdir(parents=True)
    compiler_path.write_bytes(Path(profile_module.__file__).read_bytes())
    monkeypatch.setattr(profile_module, "__file__", str(compiler_path))
    source_compiler_path = (
        artifact_root / "src/ai_video/production/comfy_video.py"
    )
    source_compiler_path.parent.mkdir(parents=True, exist_ok=True)
    source_compiler_path.write_bytes(
        Path(source_stack_module.comfy_video.__file__).read_bytes()
    )
    monkeypatch.setattr(
        source_stack_module.comfy_video,
        "__file__",
        str(source_compiler_path),
    )
    source_profile_path = artifact_root / source_stack_module.SOURCE_PROFILE_PATH
    source_profile = json.loads(
        (REPO_ROOT / source_stack_module.SOURCE_PROFILE_PATH).read_text(
            encoding="utf-8"
        )
    )
    source_profile_path.parent.mkdir(parents=True, exist_ok=True)
    source_profile_path.write_text(
        json.dumps(source_profile, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    for relative in (
        source_profile["workflow_path"],
        source_profile["binding_path"],
    ):
        copied = artifact_root / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes((REPO_ROOT / relative).read_bytes())
    monkeypatch.setattr(materialize_script, "REPO_ROOT", artifact_root)
    materialize(
        root=root,
        artifact_root=artifact_root,
        profile_path=profile_path,
        attempt_id="test-real-m0-materialization-v1",
        m0_policy_id=policy_id,
    )
    return ProductionStateCommitter(root), profile_path, artifact_root


def test_m0_validation_preflight_reopens_and_consumes_exact_materialized_hashes() -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    committer = _ReadOnlyCommitter(_bundle(sources))
    preflight_owner = getattr(
        m0_qualification,
        "reopen_m0_validation_preflight",
        None,
    )

    assert preflight_owner is not None, (
        "M0 Validation V1 requires one guarded pre-effect reopen owner"
    )
    first = preflight_owner(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    replay = preflight_owner(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )

    assert first == replay
    assert first.candidate_label == "m0"
    assert first.execution_stack_hash == committer.bundle[1][0].execution_stack_hash
    assert first.profile_hash == sources.materialization.profile_hash
    assert first.compiler_hash == sources.materialization.compiler_hash
    assert first.workflow_hash == sources.materialization.workflow_hash
    assert first.qualification_receipt_hash == committer.bundle[0].content_hash
    assert first.validation_set_hash == committer.bundle[3].content_hash
    assert first.policy_hashes == tuple(
        item.policy_hash for item in committer.bundle[2]
    )
    assert first.qualification_input_hashes == tuple(
        (item.input_kind, item.content_hash) for item in committer.bundle[4]
    )
    assert committer.reopen_calls == [("m0",), ("m0",)]


def test_m0_materialization_owner_reseals_source_drift_and_replays_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committer, profile_path, artifact_root = _real_materialized_committer(
        tmp_path,
        monkeypatch,
    )
    before = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    manifest_before = load_production_project(
        committer._project_root / "project.yaml"
    ).manifest
    compiler_path = Path(m0_qualification.__file__)
    compiler_path.write_bytes(compiler_path.read_bytes() + b"\n# resealed compiler\n")

    resealed = materialize(
        root=committer._project_root,
        artifact_root=artifact_root,
        profile_path=profile_path,
        attempt_id="test-real-m0-reseal-v2",
        m0_policy_id=M0ValidationPolicyId.QUALITY_V1,
    )
    after = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )

    assert resealed["m0_execution_stack_hash"] != before[1][0].execution_stack_hash
    assert after[1][1] == before[1][1]
    assert after[0].content_hash != before[0].content_hash
    assert tuple(item.policy_hash for item in after[2]) != tuple(
        item.policy_hash for item in before[2]
    )
    assert after[3].content_hash != before[3].content_hash
    source_stack = committer.reopen_p0_qualification_source_stacks(
        require_materialized=True
    )[0]
    expected_stack_hashes = tuple(
        sorted((source_stack.execution_stack_hash, after[1][0].execution_stack_hash))
    )
    assert all(
        item.execution_stack_hashes == expected_stack_hashes
        for item in after[4]
    )
    assert resealed["claims"]["provider_effects"] == 0
    assert resealed["claims"]["video_generated"] is False

    tree_before_replay = _tree_snapshot(committer._project_root)
    replayed = materialize(
        root=committer._project_root,
        artifact_root=artifact_root,
        profile_path=profile_path,
        attempt_id="test-real-m0-reseal-replay",
        m0_policy_id=M0ValidationPolicyId.QUALITY_V1,
    )
    manifest_after = load_production_project(
        committer._project_root / "project.yaml"
    ).manifest
    assert replayed == resealed
    assert manifest_after.manifest_revision == manifest_before.manifest_revision + 1
    assert _tree_snapshot(committer._project_root) == tree_before_replay


def test_fast_m0_materialization_reopens_and_replays_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committer, profile_path, artifact_root = _real_materialized_committer(
        tmp_path,
        monkeypatch,
        M0ValidationPolicyId.FAST_V1,
    )
    prepared = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    tree_before_replay = _tree_snapshot(committer._project_root)

    replayed = materialize(
        root=committer._project_root,
        artifact_root=artifact_root,
        profile_path=profile_path,
        attempt_id="test-real-fast-m0-materialization-replay",
        m0_policy_id=M0ValidationPolicyId.FAST_V1,
    )
    first_preflight = m0_fast.reopen_m0_fast_validation_preflight(
        committer=committer,
        profile_path=profile_path,
        artifact_root=artifact_root,
    )
    replay_preflight = m0_fast.reopen_m0_fast_validation_preflight(
        committer=committer,
        profile_path=profile_path,
        artifact_root=artifact_root,
    )

    assert replayed["m0_validation_policy_id"] == "fast-v1"
    assert replayed["m0_execution_stack_hash"] == prepared[1][0].execution_stack_hash
    assert replayed["claims"]["provider_effects"] == 0
    assert replayed["claims"]["video_generated"] is False
    assert first_preflight == replay_preflight
    assert first_preflight.execution_stack_hash == prepared[1][0].execution_stack_hash
    assert _tree_snapshot(committer._project_root) == tree_before_replay


def test_m0_materialization_owner_reseals_independent_source_compiler_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committer, profile_path, artifact_root = _real_materialized_committer(
        tmp_path,
        monkeypatch,
    )
    before = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    source_before = committer.reopen_p0_qualification_source_stacks(
        require_materialized=True
    )[0]
    source_compiler = Path(source_stack_module.comfy_video.__file__)
    source_compiler.write_bytes(
        source_compiler.read_bytes() + b"\n# source compiler reseal\n"
    )

    resealed = materialize(
        root=committer._project_root,
        artifact_root=artifact_root,
        profile_path=profile_path,
        attempt_id="test-real-source-reseal-v2",
        m0_policy_id=M0ValidationPolicyId.QUALITY_V1,
    )
    after = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    source_after = committer.reopen_p0_qualification_source_stacks(
        require_materialized=True
    )[0]

    assert source_after.execution_stack_hash != source_before.execution_stack_hash
    assert after[1] == before[1]
    assert after[0].content_hash != before[0].content_hash
    assert after[3].content_hash != before[3].content_hash
    assert resealed["claims"]["provider_effects"] == 0
    assert resealed["claims"]["video_generated"] is False

    tree_before_replay = _tree_snapshot(committer._project_root)
    replayed = materialize(
        root=committer._project_root,
        artifact_root=artifact_root,
        profile_path=profile_path,
        attempt_id="test-real-source-reseal-replay",
        m0_policy_id=M0ValidationPolicyId.QUALITY_V1,
    )
    assert replayed == resealed
    assert _tree_snapshot(committer._project_root) == tree_before_replay


@pytest.mark.parametrize(
    "field",
    ("initial_execution_stack_hash", "prepared_receipt_hash"),
)
def test_m0_materialized_reseal_rejects_seed_root_reselection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    committer, profile_path, artifact_root = _real_materialized_committer(
        tmp_path,
        monkeypatch,
    )
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    original_seed = profile["sealed_seed"]
    profile[field] = "1" * 64
    profile["sealed_seed"] = m0_qualification.derive_m0_qualification_seed(profile)
    assert profile["sealed_seed"] != original_seed
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    tree_before = _tree_snapshot(committer._project_root)

    with pytest.raises(ValueError, match="seed derivation roots"):
        materialize(
            root=committer._project_root,
            artifact_root=artifact_root,
            profile_path=profile_path,
            attempt_id=f"test-m0-reseal-{field}-drift",
            m0_policy_id=M0ValidationPolicyId.QUALITY_V1,
        )
    assert _tree_snapshot(committer._project_root) == tree_before


def test_m0_pre_submit_guard_requires_request_to_bind_reopened_stack() -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    committer = _ReadOnlyCommitter(_bundle(sources))
    guard = m0_qualification.M0ValidationPreSubmitGuard(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )

    valid = _resolved_m0_request(
        sources,
        committer.bundle[1][0].execution_stack_hash,
    )
    guard(valid)
    with pytest.raises(AiVideoError, match="execution stack"):
        guard(SimpleNamespace(**{**vars(valid), "execution_stack_hash": "0" * 64}))

    assert committer.reopen_calls == [("m0",), ("m0",)]


@pytest.mark.parametrize(
    ("drift", "message"),
    (
        ("candidate", "candidate identity"),
        ("profile", "profile identity"),
        ("compiler", "compiler"),
        ("mode", "local motion-boundary"),
        ("anchors", "four-anchor"),
        ("motion_tail", "four-anchor"),
        ("prompt", "prompt"),
        ("seed", "seed"),
        ("output", "output"),
        ("timing_mode", "output"),
        ("frame_count", "output"),
        ("missing_frame_count", "output"),
    ),
)
def test_m0_pre_submit_guard_denies_request_drift_before_effect(
    drift: str,
    message: str,
) -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    committer = _ReadOnlyCommitter(_bundle(sources))
    guard = m0_qualification.M0ValidationPreSubmitGuard(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    request = _resolved_m0_request(
        sources,
        committer.bundle[1][0].execution_stack_hash,
    )
    if drift == "candidate":
        request = SimpleNamespace(**{**vars(request), "model_id": "other-model"})
    elif drift == "profile":
        request.provider_profile.profile_sha256 = "0" * 64
    elif drift == "compiler":
        request.adapter_compiler_hash = "0" * 64
    elif drift == "mode":
        request.mode = SimpleNamespace(value="reference_to_video")
    elif drift == "anchors":
        request.image_bindings = request.image_bindings[:2]
    elif drift == "motion_tail":
        request.c4_multi_anchor_binding.motion_tail = None
    elif drift == "prompt":
        request.prompt_text += " drift"
    elif drift == "seed":
        request.effective_seed = sources.profile.sealed_seed + 1
    elif drift == "output":
        request.effective_output.width += 32
    elif drift == "timing_mode":
        request.effective_output.timing_mode = "exact_seconds"
        request.effective_output.frame_count = None
        request.effective_output.duration_seconds = 5
    elif drift == "frame_count":
        request.effective_output.frame_count = 125
    else:
        del request.effective_output.frame_count

    with pytest.raises(AiVideoError, match=message):
        guard(request)

    assert committer.reopen_calls == [("m0",)]


def test_m0_request_drift_denies_before_preview_intent_or_submit() -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    qualification = _ReadOnlyCommitter(_bundle(sources))
    request = _resolved_m0_request(
        sources,
        qualification.bundle[1][0].execution_stack_hash,
    )
    request.effective_output.frame_count = 125
    provider = SimpleNamespace(
        preview=lambda _request: pytest.fail("preview must remain zero effect"),
        submit_local=lambda *_args: pytest.fail("submit must remain zero effect"),
    )

    class _SubmitCommitter:
        def __init__(self) -> None:
            self.intent_calls = 0
            self.attempt = SimpleNamespace(
                status=StateCommitStatus.RUNNING,
                paid_provider_state=None,
                video_generation_state=SimpleNamespace(
                    phase=VideoAttemptPhase.REQUEST,
                    request=SimpleNamespace(),
                ),
            )

        def _read_manifest(self):
            return SimpleNamespace()

        def _video_attempt(self, _manifest, _attempt_id):
            return self.attempt

        def _reopen_video_request(self, _pointer):
            return request

        def record_local_video_submit_intent(self, **_kwargs):
            self.intent_calls += 1
            pytest.fail("intent must remain zero effect")

    submit_committer = _SubmitCommitter()
    service = VideoGenerationService(
        committer=submit_committer,
        provider=provider,
    )
    guard = m0_qualification.M0ValidationPreSubmitGuard(
        committer=qualification,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )

    with pytest.raises(AiVideoError, match="output"):
        service.submit_local_once(
            attempt_id="m0-validation-v1",
            pre_submit_guard=guard,
        )

    assert submit_committer.intent_calls == 0


def test_m0_guard_denies_execution_source_drift_after_reopen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = m0_qualification.load_m0_qualification_execution_sources
    stable = original(profile_path=PROFILE_PATH, artifact_root=REPO_ROOT)
    committer = _ReadOnlyCommitter(_bundle(stable))
    calls = 0

    def drifting_load(**kwargs):
        nonlocal calls
        calls += 1
        sources = original(**kwargs)
        if calls == 2:
            drifted = sources.materialization.from_bytes(
                candidate_label="m0",
                profile_bytes=sources.materialization.profile_bytes,
                compiler_bytes=sources.materialization.compiler_bytes,
                workflow_bytes=sources.materialization.workflow_bytes + b"drift",
            )
            return replace(sources, materialization=drifted)
        return sources

    monkeypatch.setattr(
        m0_qualification,
        "load_m0_qualification_execution_sources",
        drifting_load,
    )
    guard = m0_qualification.M0ValidationPreSubmitGuard(
        committer=committer,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )

    with pytest.raises(AiVideoError, match="drifted after the guarded reopen"):
        guard(
            _resolved_m0_request(
                stable,
                committer.bundle[1][0].execution_stack_hash,
            )
        )

    assert calls == 2


@pytest.mark.parametrize(
    "drift",
    (
        "project",
        "registry",
        "m1_hash",
        "m1_materialized",
        "hybrid_present",
        "calibration_prompt",
        "dependent_input_stack",
    ),
)
def test_m0_validation_preflight_denies_frozen_target_drift(drift: str) -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    bundle = copy.deepcopy(_bundle(sources))
    receipt, stacks, _, _, inputs = bundle
    if drift == "project":
        receipt.project.content_hash = "0" * 64
    elif drift == "registry":
        receipt.registry.content_hash = "0" * 64
    elif drift == "m1_hash":
        stacks[1].execution_stack_hash = "0" * 64
    elif drift == "m1_materialized":
        stacks[1].materialization_status = "materialized"
    elif drift == "hybrid_present":
        stacks[1].components[0].presence = "present"
        stacks[1].components[0].content_hash = "0" * 64
    elif drift == "calibration_prompt":
        inputs[0].payload["prompt_sha256"] = "0" * 64
    else:
        inputs[1].execution_stack_hashes = ("0" * 64,)
    committer = _ReadOnlyCommitter(bundle)

    with pytest.raises(AiVideoError, match="frozen qualification"):
        m0_qualification.reopen_m0_validation_preflight(
            committer=committer,
            profile_path=PROFILE_PATH,
            artifact_root=REPO_ROOT,
        )

    assert committer.reopen_calls == [("m0",)]


@pytest.mark.parametrize("missing", ("calibration", "hybrid"))
def test_m0_validation_preflight_denies_incomplete_target(missing: str) -> None:
    sources = m0_qualification.load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    receipt, stacks, policies, validation_set, inputs = _bundle(sources)
    if missing == "calibration":
        inputs = tuple(
            item for item in inputs if item.input_kind != "calibration_fixture"
        )
    else:
        stacks[1].components = ()
    committer = _ReadOnlyCommitter(
        (receipt, stacks, policies, validation_set, inputs)
    )

    with pytest.raises(AiVideoError, match="incomplete"):
        m0_qualification.reopen_m0_validation_preflight(
            committer=committer,
            profile_path=PROFILE_PATH,
            artifact_root=REPO_ROOT,
        )

    assert committer.reopen_calls == [("m0",)]


def test_real_m0_validation_preflight_replay_is_project_tree_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committer, profile_path, artifact_root = _real_materialized_committer(
        tmp_path, monkeypatch
    )
    root = committer._project_root
    before = _tree_snapshot(root)

    first = m0_qualification.reopen_m0_validation_preflight(
        committer=committer,
        profile_path=profile_path,
        artifact_root=artifact_root,
    )
    replay = m0_qualification.reopen_m0_validation_preflight(
        committer=committer,
        profile_path=profile_path,
        artifact_root=artifact_root,
    )

    assert replay == first
    assert _tree_snapshot(root) == before


@pytest.mark.parametrize("tamper", ("persisted_source", "dependent_evidence"))
def test_real_m0_validation_preflight_tamper_fails_without_additional_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
) -> None:
    committer, profile_path, artifact_root = _real_materialized_committer(
        tmp_path, monkeypatch
    )
    root = committer._project_root
    _, stacks, _, _, inputs = committer.reopen_p0_qualification_prepared(
        required_materialized_candidates=("m0",)
    )
    if tamper == "persisted_source":
        target = root / canonical_execution_stack_materialization_source_path(
            "workflow", stacks[0].workflow_hash
        )
    else:
        dependent = next(item for item in inputs if item.input_kind == "effect_budget")
        target = root / canonical_p0_qualification_input_path(
            dependent.input_kind,
            dependent.content_hash,
        )
    target.write_bytes(target.read_bytes() + b"tamper")
    after_tamper = _tree_snapshot(root)

    with pytest.raises(AiVideoError):
        m0_qualification.reopen_m0_validation_preflight(
            committer=committer,
            profile_path=profile_path,
            artifact_root=artifact_root,
        )

    assert _tree_snapshot(root) == after_tamper
