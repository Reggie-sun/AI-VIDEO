from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from ai_video.errors import AiVideoError
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.shot_continuity_m0_policy import M0ValidationPolicyId
from ai_video.production.shot_continuity_m0_fast_validation import (
    M0FastQualificationProfile,
    derive_m0_fast_qualification_seed,
)
from ai_video.production.video_transition import (
    P0QualificationInput,
    P0QualificationPreparedReceipt,
)
from scripts.prepare_shot_continuity_p0 import (
    _m0_stack,
    _parser,
    _qualification_inputs,
    prepare,
)
from scripts.materialize_shot_continuity_m0 import _parser as _materialize_parser


REPO_ROOT = Path(__file__).resolve().parents[1]
FAST_PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/minimax_h3_t8_c4_m0_fast_v1_profile.json"
)
FAST_PREPARED_RECEIPT_FIXTURE = REPO_ROOT / (
    "tests/fixtures/shot_continuity/m0_fast_v1_prepared_receipt.json"
)


def _sources() -> tuple[tuple[SimpleNamespace, ...], tuple[SimpleNamespace, ...]]:
    assets = tuple(
        SimpleNamespace(
            sha256=str(index) * 64,
            width=1659,
            height=948,
        )
        for index in range(1, 5)
    )
    receipts = tuple(
        SimpleNamespace(prompt_fingerprint=str(index + 4) * 64)
        for index in range(1, 5)
    )
    return assets, receipts


@pytest.mark.parametrize(
    ("policy_id", "steps", "turbo_lora", "capability_id"),
    (
        (
            M0ValidationPolicyId.FAST_V1,
            4,
            True,
            "c4-native-boundary-motion-fast-qualification-candidate",
        ),
        (
            M0ValidationPolicyId.QUALITY_V1,
            20,
            False,
            "c4-native-boundary-motion-qualification-candidate",
        ),
    ),
)
def test_preparation_binds_explicit_policy_to_calibration_and_m0_stack(
    policy_id: M0ValidationPolicyId,
    steps: int,
    turbo_lora: bool,
    capability_id: str,
) -> None:
    assets, receipts = _sources()

    inputs = _qualification_inputs(
        shot_assets=assets,
        shot_receipts=receipts,
        approved_at="2026-08-26T10:00:00+08:00",
        m0_policy_id=policy_id,
    )
    calibration = next(
        item for item in inputs if item.input_kind == "calibration_fixture"
    )
    stack = _m0_stack(policy_id)

    assert calibration.schema_version == "2"
    assert calibration.payload["m0_validation_policy_id"] == policy_id.value
    assert calibration.payload["steps"] == steps
    assert calibration.payload["turbo_lora"] is turbo_lora
    assert stack.capability_id == capability_id


def test_p0_cli_requires_one_explicit_m0_policy() -> None:
    parser = _parser()
    common = [
        "--root",
        "out",
        "--a1",
        "a1.png",
        "--a2",
        "a2.png",
        "--a3",
        "a3.png",
        "--a4",
        "a4.png",
        "--approved-at",
        "2026-08-26T10:00:00+08:00",
        "--imported-at",
        "2026-08-26T10:00:01+08:00",
    ]

    with pytest.raises(SystemExit):
        parser.parse_args(common)
    assert parser.parse_args(
        [*common, "--m0-policy", "fast-v1"]
    ).m0_policy is M0ValidationPolicyId.FAST_V1


def test_m0_materialization_cli_requires_one_explicit_policy() -> None:
    parser = _materialize_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--root", "prepared"])
    assert parser.parse_args(
        ["--root", "prepared", "--m0-policy", "quality-v1"]
    ).m0_policy is M0ValidationPolicyId.QUALITY_V1


def test_shipped_fast_profile_binds_the_exact_fast_prepared_receipt() -> None:
    profile_document = json.loads(FAST_PROFILE_PATH.read_text(encoding="utf-8"))
    profile = M0FastQualificationProfile.model_validate(profile_document)
    receipt = P0QualificationPreparedReceipt.model_validate_json(
        FAST_PREPARED_RECEIPT_FIXTURE.read_bytes()
    )

    assert profile.prepared_receipt_hash == receipt.content_hash
    assert profile.project_content_hash == receipt.project.content_hash
    assert profile.registry_content_hash == receipt.registry.content_hash
    assert profile.initial_execution_stack_hash == (
        receipt.candidate_stacks[0].execution_stack_hash
    )
    assert profile.m1_execution_stack_hash == (
        receipt.candidate_stacks[1].execution_stack_hash
    )
    assert profile.sealed_seed == derive_m0_fast_qualification_seed(
        profile_document
    )


def _image(root: Path, ordinal: int) -> Path:
    directory = root / f"a{ordinal}"
    directory.mkdir(parents=True)
    path = directory / f"a{ordinal}.png"
    Image.new("RGB", (1659, 948), (ordinal * 20,) * 3).save(path)
    (directory / "metadata.json").write_text(
        json.dumps(
            {
                "backend": "chatgpt-web",
                "mode": "direct-typescript-browser",
                "prompt": f"rainy-station-a{ordinal}",
                "created_at": "2026-08-26T09:00:00+08:00",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_p0_state_rejects_policy_and_selected_m0_stack_mismatch(
    tmp_path: Path,
) -> None:
    images = tuple(_image(tmp_path / "inputs", ordinal) for ordinal in range(1, 5))
    root = tmp_path / "production"
    prepare(
        argparse.Namespace(
            root=root,
            a1=images[0],
            a2=images[1],
            a3=images[2],
            a4=images[3],
            approved_at="2026-08-26T10:00:00+08:00",
            imported_at="2026-08-26T10:01:00+08:00",
            m0_policy=M0ValidationPolicyId.FAST_V1,
        )
    )
    writer = ProductionStateCommitter(root)
    receipt, stacks, policies, validation_set, inputs = (
        writer.reopen_p0_qualification_prepared()
    )
    calibration = next(
        item for item in inputs if item.input_kind == "calibration_fixture"
    )
    quality_payload = {
        **calibration.payload,
        "m0_validation_policy_id": "quality-v1",
        "steps": 20,
        "turbo_lora": False,
    }
    quality_calibration = P0QualificationInput.create(
        **{
            **calibration.model_dump(mode="python", exclude={"content_hash"}),
            "payload": quality_payload,
        }
    )
    changed_inputs = tuple(
        quality_calibration if item.input_kind == "calibration_fixture" else item
        for item in inputs
    )
    changed_receipt = P0QualificationPreparedReceipt.create(
        **{
            **{
                field: getattr(receipt, field)
                for field in type(receipt).model_fields
                if field != "content_hash"
            },
            "calibration_fixture_hash": quality_calibration.content_hash,
        }
    )

    with pytest.raises(AiVideoError, match="policy.*stack|stack.*policy"):
        writer._validate_p0_bundle(
            changed_receipt,
            candidate_stacks=stacks,
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=changed_inputs,
        )
