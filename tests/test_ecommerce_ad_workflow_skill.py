from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
import re
import socket
import subprocess
import sys
from types import ModuleType
from typing import Callable

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "ecommerce-ad-workflow"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
SCRIPT_PATH = SKILL_ROOT / "scripts" / "validate_contract.py"
MODEL_PATH = SKILL_ROOT / "scripts" / "contract_models.py"
GATES_PATH = SKILL_ROOT / "scripts" / "contract_gates.py"
INPUT_SCHEMA_PATH = SKILL_ROOT / "schemas" / "ecommerce-ad-input.schema.json"
PACKAGE_SCHEMA_PATH = (
    SKILL_ROOT / "schemas" / "ecommerce-ad-production-package.schema.json"
)
INPUT_EXAMPLE_PATH = (
    SKILL_ROOT / "templates" / "30s-vertical-product-ad.input.example.json"
)
PACKAGE_EXAMPLE_PATH = (
    SKILL_ROOT / "templates" / "30s-vertical-product-ad.package.example.json"
)
REFERENCE_NAMES = {
    "product-truth-and-claims.md",
    "audience-angle-and-proof.md",
    "hooks.md",
    "ad-beat-sequences.md",
    "product-presentation.md",
    "advertising-copy-graphics.md",
    "audio-pacing-and-coverage.md",
    "creative-variants.md",
    "runtime-handoff.md",
    "ad-qc.md",
    "external-method-sources.md",
}


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


@lru_cache(maxsize=1)
def _validator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "ecommerce_ad_workflow_validator", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_cli(kind: str, path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--kind", kind, "--file", str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _diagnostic_codes(result: subprocess.CompletedProcess[str]) -> set[str]:
    document = json.loads(result.stdout)
    return {item["code"] for item in document["diagnostics"]}


def _rehash_package(payload: dict[str, object]) -> None:
    identity_payload = copy.deepcopy(payload)
    identity_payload.pop("package_id", None)
    payload["package_id"] = _canonical_sha256(identity_payload)


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _assert_invalid_package(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
    expected_code: str,
) -> dict[str, object]:
    payload = _load_json(PACKAGE_EXAMPLE_PATH)
    mutate(payload)
    _rehash_package(payload)
    path = tmp_path / f"invalid-{expected_code}.json"
    _write_payload(path, payload)

    result = _run_cli("package", path)

    assert result.returncode == 2, result.stdout
    assert result.stderr == ""
    document = json.loads(result.stdout)
    assert document["status"] == "invalid"
    assert expected_code in _diagnostic_codes(result)
    return document


def _assert_invalid_input(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
    expected_code: str,
) -> dict[str, object]:
    payload = _load_json(INPUT_EXAMPLE_PATH)
    mutate(payload)
    path = tmp_path / f"invalid-input-{expected_code}.json"
    _write_payload(path, payload)

    result = _run_cli("input", path)

    assert result.returncode == 2, result.stdout
    assert result.stderr == ""
    document = json.loads(result.stdout)
    assert document["status"] == "invalid"
    assert expected_code in _diagnostic_codes(result)
    return document


def test_expected_skill_package_files_exist() -> None:
    expected = {
        SKILL_PATH,
        SCRIPT_PATH,
        MODEL_PATH,
        GATES_PATH,
        INPUT_SCHEMA_PATH,
        PACKAGE_SCHEMA_PATH,
        INPUT_EXAMPLE_PATH,
        PACKAGE_EXAMPLE_PATH,
        *(SKILL_ROOT / "references" / name for name in REFERENCE_NAMES),
    }

    assert {path for path in expected if not path.is_file()} == set()


@pytest.mark.skipif(not SKILL_PATH.is_file(), reason="Skill not implemented yet")
def test_skill_frontmatter_is_discoverable_and_routes_progressively() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None
    frontmatter = yaml.safe_load(match.group(1))

    assert frontmatter["name"] == "ecommerce-ad-workflow"
    description = frontmatter["description"]
    assert description.startswith("Use when ")
    assert "ecommerce" in description.lower()
    assert "product advertising" in description.lower()
    assert "AI comic" in description

    linked = set(re.findall(r"references/([a-z0-9-]+\.md)", text))
    assert linked == REFERENCE_NAMES
    assert all((SKILL_ROOT / "references" / name).is_file() for name in linked)


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_checked_in_schemas_are_exact_pydantic_contract_views() -> None:
    module = _validator_module()

    assert INPUT_SCHEMA_PATH.read_text(encoding="utf-8") == module.schema_text(
        "input"
    )
    assert PACKAGE_SCHEMA_PATH.read_text(encoding="utf-8") == module.schema_text(
        "package"
    )
    assert _load_json(INPUT_SCHEMA_PATH)["additionalProperties"] is False
    assert _load_json(PACKAGE_SCHEMA_PATH)["additionalProperties"] is False

    package_schema = _load_json(PACKAGE_SCHEMA_PATH)
    definitions = package_schema["$defs"]
    assert "objection_handling" in definitions["AdStrategy"]["required"]
    assert "promise_boundary" in definitions["HookContract"]["required"]
    assert "bound_ids" in definitions["HookComponent"]["required"]
    assert set(
        definitions["CreativeVariant"]["properties"]["held_constants"]["items"][
            "enum"
        ]
    ) == {
        "claim_ledger",
        "cta_destination",
        "delivery_intent",
        "objective",
        "platform_constraints",
        "product_identity",
        "product_truth",
        "rights",
        "unchanged_strategy_fields",
    }


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_valid_30_second_vertical_examples_validate_and_are_hash_bound() -> None:
    input_payload = _load_json(INPUT_EXAMPLE_PATH)
    package_payload = _load_json(PACKAGE_EXAMPLE_PATH)

    input_result = _run_cli("input", INPUT_EXAMPLE_PATH)
    package_result = _run_cli("package", PACKAGE_EXAMPLE_PATH)

    assert input_result.returncode == 0
    assert json.loads(input_result.stdout) == {
        "diagnostics": [],
        "kind": "input",
        "status": "valid",
    }
    assert input_result.stderr == ""
    assert package_result.returncode == 0
    assert json.loads(package_result.stdout) == {
        "diagnostics": [],
        "kind": "package",
        "status": "valid",
    }
    assert package_result.stderr == ""
    assert package_payload["source_input_hash"] == _canonical_sha256(input_payload)
    identity_payload = copy.deepcopy(package_payload)
    identity_payload.pop("package_id")
    assert package_payload["package_id"] == _canonical_sha256(identity_payload)


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_authoring_readiness_cannot_encode_production_acceptance() -> None:
    module = _validator_module()
    package_payload = _load_json(PACKAGE_EXAMPLE_PATH)
    package = module.EcommerceAdProductionPackage.model_validate_json(
        PACKAGE_EXAMPLE_PATH.read_text(encoding="utf-8")
    )

    report_model = type(package.ad_qc_report)
    handoff_model = type(package.runtime_handoff)
    assert package.ad_qc_report.ready is True
    assert set(report_model.model_fields) == {"ready", "findings"}
    assert set(handoff_model.model_fields) == {
        "delivery_intent",
        "proposals",
        "requirements",
        "classified_gaps",
    }
    assert {
        "production_verdict",
        "review_receipt",
        "final_acceptance",
        "manifest_revision",
        "activation",
    }.isdisjoint(package_payload["runtime_handoff"])

@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize(
    "forbidden_field",
    [
        "episode_mode",
        "episode_context",
        "cliffhanger",
        "serial_arc",
        "ai_comic_package",
        "character_bible",
    ],
)
def test_forbidden_ai_comic_input_fields_have_stable_diagnostics(
    tmp_path: Path, forbidden_field: str
) -> None:
    payload = _load_json(INPUT_EXAMPLE_PATH)
    payload[forbidden_field] = "PRIVATE-FORBIDDEN-BODY"
    path = tmp_path / "forbidden-input.json"
    _write_payload(path, payload)

    result = _run_cli("input", path)

    assert result.returncode == 2
    assert result.stderr == ""
    document = json.loads(result.stdout)
    assert document["diagnostics"] == [
        {
            "code": "forbidden_field",
            "message": "field is forbidden by the ecommerce workflow boundary",
            "path": f"$.{forbidden_field}",
        }
    ]
    assert "PRIVATE-FORBIDDEN-BODY" not in result.stdout


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_medical_claim_is_rejected_even_with_source_and_disclaimer(
    tmp_path: Path,
) -> None:
    payload = _load_json(INPUT_EXAMPLE_PATH)
    allowed = payload["product_truth"]["allowed_claims"]
    allowed[0]["claim_type"] = "MEDICAL_OR_THERAPEUTIC"
    payload["product_truth"]["required_disclaimers"] = ["Results vary"]
    path = tmp_path / "medical.json"
    _write_payload(path, payload)

    result = _run_cli("input", path)

    assert result.returncode == 2
    assert "medical_claim_forbidden" in _diagnostic_codes(result)
    assert result.stderr == ""


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize("rights_status", ["UNKNOWN", "RESTRICTED"])
def test_input_requires_confirmed_asset_and_truth_source_rights(
    tmp_path: Path, rights_status: str
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["product"]["source_assets"][0]["rights_status"] = rights_status
        payload["product_truth"]["sources"][0]["rights_status"] = rights_status

    _assert_invalid_input(tmp_path, mutate, "rights_not_confirmed")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_claim_sources_must_exactly_support_the_referenced_facts(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["product_truth"]["allowed_claims"][0]["source_ids"] = [
            "source-product-image"
        ]

    _assert_invalid_input(tmp_path, mutate, "claim_lineage")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_package_snapshot_revalidates_rights_and_claim_sources(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["product_truth"]["source_assets"][0]["rights_status"] = "UNKNOWN"
        payload["product_truth"]["allowed_claims"][0]["source_ids"] = [
            "source-product-image"
        ]

    _assert_invalid_package(tmp_path, mutate, "rights_not_confirmed")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_package_snapshot_revalidates_exact_claim_source_lineage(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["product_truth"]["allowed_claims"][0]["source_ids"] = [
            "source-product-image"
        ]
        payload["claim_ledger"][1]["source_ids"] = ["source-product-image"]

    _assert_invalid_package(tmp_path, mutate, "claim_lineage")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_used_claim_requires_exact_fact_and_source_lineage(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["claim_ledger"][0]["fact_ids"] = ["fact-does-not-exist"]

    document = _assert_invalid_package(tmp_path, mutate, "claim_lineage")

    assert any(item["path"].startswith("$.claim_ledger") for item in document["diagnostics"])


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize("defect", ["unknown_usage", "missing_form"])
def test_used_claim_requires_real_usage_and_a_declared_form(
    tmp_path: Path, defect: str
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        entry = payload["claim_ledger"][0]
        if defect == "unknown_usage":
            entry["used_at"] = ["copy-does-not-exist"]
        else:
            entry["spoken_form"] = None
            entry["visual_form"] = None

    _assert_invalid_package(tmp_path, mutate, "claim_lineage")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_hook_component_claims_must_bind_used_claims(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["hook_contract"]["components"][0]["claim_ids"] = [
            "claim-does-not-exist"
        ]

    _assert_invalid_package(tmp_path, mutate, "claim_lineage")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_product_name_must_be_visible_or_audible(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        for item in payload["copy_graphics_plan"]:
            item["text"] = "Portable power"
        for item in payload["audio_plan"]["events"]:
            if item.get("verbatim_line"):
                item["verbatim_line"] = "Blend anywhere"

    _assert_invalid_package(tmp_path, mutate, "product_name_missing")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_hook_requires_an_observable_first_second_component(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        for component in payload["hook_contract"]["components"]:
            component["cue_seconds"] = 1.0

    _assert_invalid_package(tmp_path, mutate, "hook_first_second")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_hook_requires_visual_dialogue_copy_and_audio_components(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["hook_contract"]["components"] = [
            item
            for item in payload["hook_contract"]["components"]
            if item["kind"] != "AUDIO"
        ]

    _assert_invalid_package(tmp_path, mutate, "hook_contract")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_beats_shots_presentations_copy_and_audio_are_traceable(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["ad_beats"][0]["shot_ids"] = ["shot-missing"]

    _assert_invalid_package(tmp_path, mutate, "traceability")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize("relation", ["presentation", "copy", "audio", "storyboard"])
def test_traceability_requires_exact_bidirectional_membership(
    tmp_path: Path, relation: str
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        if relation == "presentation":
            payload["ad_beats"][0]["presentation_ids"] = []
        elif relation == "copy":
            payload["shot_intents"][1]["copy_ids"] = []
        elif relation == "audio":
            payload["ad_beats"][2]["audio_event_ids"] = ["audio-music"]
        else:
            payload["storyboard"][0]["shot_ids"] = ["shot-intro"]

    _assert_invalid_package(tmp_path, mutate, "traceability")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize("relation", ["presentation", "copy", "audio"])
def test_traceability_rejects_cross_beat_and_shot_pairs(
    tmp_path: Path, relation: str
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        if relation == "presentation":
            payload["product_presentation"][0]["shot_id"] = "shot-demo"
            payload["shot_intents"][0]["presentation_ids"] = []
            payload["shot_intents"][2]["presentation_ids"].append(
                "presentation-intro"
            )
        elif relation == "copy":
            product_label = next(
                item
                for item in payload["copy_graphics_plan"]
                if item["copy_id"] == "copy-product-label"
            )
            product_label["shot_id"] = "shot-demo"
            payload["shot_intents"][1]["copy_ids"] = []
            payload["shot_intents"][2]["copy_ids"].append("copy-product-label")
        else:
            demo_hit = next(
                item
                for item in payload["audio_plan"]["events"]
                if item["event_id"] == "audio-demo-hit"
            )
            demo_hit["shot_ids"] = ["shot-proof"]
            payload["shot_intents"][2]["audio_event_ids"] = ["audio-music"]
            payload["shot_intents"][3]["audio_event_ids"].append("audio-demo-hit")

    _assert_invalid_package(tmp_path, mutate, "traceability")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_product_presentation_requires_intro_demo_hero_and_cta_roles(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        for item in payload["product_presentation"]:
            item["role"] = "INTRO"

    _assert_invalid_package(tmp_path, mutate, "product_presentation_roles")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_physical_interaction_without_source_or_runtime_capability_is_blocked(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        item = payload["product_presentation"][0]
        item["mode"] = "PHYSICAL_INTERACTION_REQUIRED"
        item["talent_interaction"] = "PHYSICAL_CONTACT"
        item["capability_requirement_ids"] = []

    _assert_invalid_package(tmp_path, mutate, "blocked_capability_gap")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize(
    "classification",
    ["REQUIRES_SOURCE_GENERATION_STRATEGY", "REQUIRES_RUNTIME_CAPABILITY"],
)
def test_physical_interaction_with_only_a_missing_capability_is_blocked(
    tmp_path: Path, classification: str
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        item = payload["product_presentation"][0]
        item["mode"] = "PHYSICAL_INTERACTION_REQUIRED"
        item["talent_interaction"] = "PHYSICAL_CONTACT"
        item["capability_requirement_ids"] = ["req-physical"]
        payload["runtime_handoff"]["requirements"].append(
            {
                "requirement_id": "req-physical",
                "capability": "physical_product_interaction",
                "classification": classification,
                "rationale": "The required physical interaction is not available.",
            }
        )
        payload["runtime_handoff"]["classified_gaps"].append(
            {
                "gap_id": "gap-physical",
                "classification": classification,
                "requirement_ids": ["req-physical"],
                "blocker_code": "blocked_capability_gap",
                "rationale": "Physical interaction remains unavailable.",
            }
        )

    _assert_invalid_package(tmp_path, mutate, "blocked_capability_gap")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_physical_interaction_rejects_self_asserted_supported_capability(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        item = payload["product_presentation"][0]
        item["mode"] = "PHYSICAL_INTERACTION_REQUIRED"
        item["talent_interaction"] = "PHYSICAL_CONTACT"
        item["capability_requirement_ids"] = ["req-physical"]
        payload["runtime_handoff"]["requirements"].append(
            {
                "requirement_id": "req-physical",
                "capability": "physical_product_interaction",
                "classification": "SUPPORTED_CURRENTLY",
                "rationale": "This self-assertion has no authoritative evidence.",
            }
        )
        payload["runtime_handoff"]["classified_gaps"].append(
            {
                "gap_id": "gap-physical",
                "classification": "SUPPORTED_CURRENTLY",
                "requirement_ids": ["req-physical"],
                "blocker_code": None,
                "rationale": "This self-assertion is not Runtime evidence.",
            }
        )

    _assert_invalid_package(tmp_path, mutate, "blocked_capability_gap")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_runtime_requirements_require_exact_classified_gap_closure(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["runtime_handoff"]["requirements"].append(
            {
                "requirement_id": "req-unclassified",
                "capability": "advertising_copy_graphics",
                "classification": "REQUIRES_RUNTIME_CAPABILITY",
                "rationale": "This requirement is not classified by a gap.",
            }
        )

    _assert_invalid_package(tmp_path, mutate, "runtime_handoff")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_commercial_copy_cannot_be_serialized_only_as_dialogue_subtitles(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        for item in payload["copy_graphics_plan"]:
            item["role"] = "DIALOGUE_SUBTITLE"

    _assert_invalid_package(tmp_path, mutate, "commercial_copy_roles")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_non_intentional_audio_gap_blocks_package_readiness(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["audio_plan"]["events"][1]["start_seconds"] = 15.0

    _assert_invalid_package(tmp_path, mutate, "audio_coverage_gap")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_on_camera_dialogue_requires_speaker_shot_line_and_lip_sync(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        event = next(
            item
            for item in payload["audio_plan"]["events"]
            if item["kind"] == "DIALOGUE"
        )
        event["speaker_id"] = None
        event["lip_sync_required"] = False

    _assert_invalid_package(tmp_path, mutate, "dialogue_binding")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_noisy_native_lead_in_cannot_be_kept_without_measurement_policy(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        policy = payload["audio_plan"]["source_audio_policies"][0]
        policy["lead_in_noise_risk"] = True
        policy["policy"] = "KEEP"
        policy["p6_measurement_required"] = False

    _assert_invalid_package(tmp_path, mutate, "source_audio_policy")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_source_audio_policy_must_be_unique_per_shot(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["audio_plan"]["source_audio_policies"].append(
            copy.deepcopy(payload["audio_plan"]["source_audio_policies"][0])
        )

    _assert_invalid_package(tmp_path, mutate, "source_audio_policy")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_cta_and_brand_end_card_must_bind_the_final_beat_and_shot(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["copy_graphics_plan"] = [
            item
            for item in payload["copy_graphics_plan"]
            if item["role"] not in {"CTA", "BRAND_END_CARD"}
        ]

    _assert_invalid_package(tmp_path, mutate, "cta_brand_closure")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_cta_copy_and_end_card_must_both_bind_the_final_shot(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        for item in payload["copy_graphics_plan"]:
            if item["role"] in {"CTA", "BRAND_END_CARD"}:
                item["shot_id"] = "shot-proof"

    _assert_invalid_package(tmp_path, mutate, "cta_brand_closure")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_creative_variant_changes_exactly_one_variable_and_holds_truth_constant(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        variant = payload["creative_variant_matrix"]["variants"][0]
        variant["changed_variable"] = ["HOOK", "CTA"]
        variant["held_constants"] = ["delivery_intent"]

    _assert_invalid_package(tmp_path, mutate, "variant_isolation")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_variant_matrix_binds_the_exact_master_strategy(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["creative_variant_matrix"]["master_strategy_id"] = "strategy-missing"

    _assert_invalid_package(tmp_path, mutate, "variant_isolation")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
@pytest.mark.parametrize(
    "forbidden_field",
    [
        "provider_name",
        "credential",
        "permit",
        "manifest_revision",
        "timeline_frames",
        "render_path",
        "p6_pass",
        "final_acceptance",
        "activation",
    ],
)
def test_runtime_handoff_rejects_execution_and_acceptance_fields(
    tmp_path: Path, forbidden_field: str
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["runtime_handoff"][forbidden_field] = "PRIVATE-RUNTIME-BODY"

    document = _assert_invalid_package(tmp_path, mutate, "forbidden_runtime_field")

    assert "PRIVATE-RUNTIME-BODY" not in json.dumps(document)


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_delivery_intent_cannot_be_changed_to_a_product_still(tmp_path: Path) -> None:
    def mutate(payload: dict[str, object]) -> None:
        payload["runtime_handoff"]["delivery_intent"] = "static_image"

    _assert_invalid_package(tmp_path, mutate, "delivery_intent")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_same_commercial_typography_treatment_across_every_shot_is_rejected(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        shots = [item["shot_id"] for item in payload["shot_intents"]]
        template = copy.deepcopy(payload["copy_graphics_plan"][0])
        repeated = []
        for index, shot_id in enumerate(shots):
            item = copy.deepcopy(template)
            item["copy_id"] = f"copy-mechanical-{index}"
            item["shot_id"] = shot_id
            item["role"] = "HEADLINE"
            item["text"] = "Same headline"
            item["treatment_id"] = "same-treatment"
            repeated.append(item)
        payload["copy_graphics_plan"] = repeated + [
            item
            for item in payload["copy_graphics_plan"]
            if item["role"] in {"CTA", "BRAND_END_CARD", "PRODUCT_LABEL"}
        ]
        payload["claim_ledger"][0]["used_at"] = [
            "hook-visual",
            "beat-hook",
            "copy-mechanical-0",
        ]
        payload["claim_ledger"][1]["used_at"] = [
            "beat-proof",
            "copy-mechanical-3",
        ]
        hook_copy = next(
            item
            for item in payload["hook_contract"]["components"]
            if item["kind"] == "COPY"
        )
        hook_copy["bound_ids"] = ["copy-mechanical-0"]

    _assert_invalid_package(tmp_path, mutate, "mechanical_typography")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_equal_shot_durations_without_equal_rhythm_rationale_are_rejected(
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, object]) -> None:
        for index, shot in enumerate(payload["shot_intents"]):
            shot["start_seconds"] = index * 6.0
            shot["end_seconds"] = (index + 1) * 6.0
            shot["duration_basis"] = "HOOK_DENSITY"

    _assert_invalid_package(tmp_path, mutate, "mechanical_pacing")


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_validator_is_local_read_only_and_does_not_consume_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _validator_module()
    before = {
        path.relative_to(SKILL_ROOT).as_posix(): path.read_bytes()
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
    }

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("validator attempted a forbidden external or write effect")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(Path, "replace", forbidden)
    monkeypatch.setattr(Path, "rename", forbidden)
    monkeypatch.setenv("ARK_API_KEY", "PRIVATE-CREDENTIAL-MARKER")

    module.validate_file("package", PACKAGE_EXAMPLE_PATH)

    after = {
        path.relative_to(SKILL_ROOT).as_posix(): path.read_bytes()
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
    }
    assert after == before


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_validator_imports_no_runtime_network_provider_or_ai_comic_dependency() -> None:
    imported_roots: set[str] = set()
    sources: list[str] = []
    for script_path in (SCRIPT_PATH, MODEL_PATH, GATES_PATH):
        source = script_path.read_text(encoding="utf-8")
        sources.append(source)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "ai_video",
            "httpx",
            "keyring",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
    )
    assert all("../ai-comic-workflow" not in source for source in sources)
    assert all("skills-lock.json" not in source for source in sources)


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_malformed_json_is_exit_2_and_does_not_echo_document_body(
    tmp_path: Path,
) -> None:
    path = tmp_path / "malformed.json"
    path.write_text('{"private": "PRIVATE-BODY"', encoding="utf-8")

    result = _run_cli("input", path)

    assert result.returncode == 2
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "diagnostics": [
            {
                "code": "malformed_json",
                "message": "file is not valid JSON",
                "path": "$",
            }
        ],
        "kind": "input",
        "status": "invalid",
    }
    assert "PRIVATE-BODY" not in result.stdout


@pytest.mark.skipif(not SCRIPT_PATH.is_file(), reason="Validator not implemented yet")
def test_internal_failure_is_exit_3_with_sanitized_stable_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _validator_module()

    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("PRIVATE-INTERNAL-BODY")

    monkeypatch.setattr(module, "validate_file", fail)
    exit_code = module.main(
        ["--kind", "input", "--file", str(INPUT_EXAMPLE_PATH)]
    )
    captured = capsys.readouterr()

    assert exit_code == 3
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "diagnostics": [
            {
                "code": "validator_internal_failure",
                "message": "validator could not complete",
                "path": "$",
            }
        ],
        "kind": "input",
        "status": "error",
    }
    assert "PRIVATE-INTERNAL-BODY" not in captured.out
