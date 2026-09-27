"""Exact intent joins are structural evidence, never creative acceptance."""

import hashlib
import json
import socket
import subprocess

import pytest

from scripts import creative_goal_binding as binding
from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
from test_open_video_skill import _load_validator


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def goal_inputs(root, *, kind="advertising", strategy="single_take", contract=None):
    root.mkdir(parents=True, exist_ok=True)
    action = "可见使用动作" if kind == "advertising" else "人物递出物件"
    source = f"前轮：{action}。不要凭空增加人物。\n当轮：继续生成。\n"
    raw = source.encode("utf-8")
    intents = [
        {"intent_item_id": name, "statement": quote, "origin": "explicit_user",
         "related_intent_ids": [], "source_refs": [{"source_hash": hashlib.sha256(raw).hexdigest(),
         "locator": f"brief:{index + 1}", "intent_item_id": name, "quote": quote, "origin": "explicit_user"}]}
        for index, (name, quote) in enumerate((("action", action), ("exclusion", "不要凭空增加人物")))
    ]
    count = 2 if strategy == "multi_shot" else 1
    coverage = {"schema_version": "4", "request": {
        "creative_input_kind": "direction", "creative_input_evidence": source,
        "creative_constraints": [{"constraint_id": "action", "scope": "beat_specific", "source_text": action},
            {"constraint_id": "exclusion", "scope": "global", "source_text": "不要凭空增加人物"}],
        "target_duration_seconds": 10, "coverage_strategy": strategy,
        "strategy_source": "agent_directed", "director_decision_rationale": "行动与反应承载目标。",
        "strategy_request_evidence": None, "director_skill": "open-video"},
        "coverage_units": [{"unit_id": f"unit_{i}", "duration_seconds": 10 / count,
            "beat_function": "decision" if i == 0 else "reaction", "objective": f"行动与反应 {i}",
            "open_state": "手持物件，尚未递出", "close_state": "递出后等待对方反应",
            "shot_scale": "medium" if i == 0 else "close_up",
            "camera_treatment": "static" if i == 0 else "push_in", "camera_intent": "观察人物行动",
            "visible_change": f"物件与人物关系变化 {i}",
            "transition_out": "cut" if i < count - 1 else "end",
            "constraint_ids": ["action", "exclusion"]} for i in range(count)],
        "intent_items": intents, "intent_groups": {"must_happen": [{"intent_item_id": "action"}],
            "must_not_happen": [{"intent_item_id": "exclusion"}], "preferred_performance": [],
            "timing_targets": [], "acceptable_variation": []}}
    if contract is None:
        contract = FinalOutputContract(goal_id=kind, goal_version="1", user_goal=source,
            requirements=tuple(FinalOutputRequirement(requirement_id=name, observable=text, proof="human")
                for name, text in (("action", action), ("exclusion", "不要凭空增加人物"))))
    (root / "input.txt").write_bytes(raw)
    write_json(root / "coverage.json", coverage)
    write_json(root / "contract.json", contract.model_dump(mode="json"))
    envelope = {"schema_version": "creative-goal-binding/1", "authority": "development_only",
        **{name: {"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
            for name, path in (("creative_input", "input.txt"), ("coverage", "coverage.json"),
                ("final_output_contract", "contract.json"))},
        "bindings": [{"intent_item_id": "action", "constraint_ids": ["action"],
            "unit_ids": [f"unit_{i}" for i in range(count)], "requirement_ids": [contract.requirements[-1].requirement_id]},
            {"intent_item_id": "exclusion", "constraint_ids": ["exclusion"], "unit_ids": [],
             "requirement_ids": [contract.requirements[-1].requirement_id]}]}
    path = root / "binding.json"
    write_json(path, envelope)
    return path, envelope, coverage, contract


def reseal(path, envelope, name, payload):
    target = path.parent / envelope[name]["path"]
    write_json(target, payload)
    envelope[name]["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    write_json(path, envelope)


@pytest.fixture(autouse=True)
def no_effects(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Binding validation must have no network, subprocess or media effects")
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize("kind,strategy", [("advertising", "single_take"), ("drama", "single_take"),
    ("advertising", "multi_shot"), ("drama", "multi_shot")])
def test_valid_exact_join_and_global_without_dedicated_unit(tmp_path, kind, strategy):
    path, envelope, _, contract = goal_inputs(tmp_path, kind=kind, strategy=strategy)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    verified = binding.load_goal_binding(path)
    assert verified.contract == contract
    assert verified.binding_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert verified.binding == envelope
    assert verified.diagnostics == ()
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("mutation,code", [
    ("missing_user", "unbound_user_intent"), ("missing_requirement", "unbound_user_intent"),
    ("missing_scope", "unresolved_intent_scope"), ("missing_unit", "uncovered_intent_unit"),
    ("unknown_requirement", "unknown_requirement"), ("unknown_intent", "unknown_intent"),
    ("unknown_constraint", "unknown_constraint"), ("unknown_unit", "unknown_unit"),
    ("duplicate_row", "duplicate_binding"), ("duplicate_unit", "duplicate_binding"),
    ("duplicate_constraint", "duplicate_binding"), ("duplicate_requirement", "duplicate_binding"),
    ("unknown_field", "invalid_binding"), ("wrong_version", "unsupported_binding_version"),
    ("wrong_authority", "invalid_binding"), ("empty_bindings", "unbound_user_intent")])
def test_invalid_mapping_fails_read_only(tmp_path, mutation, code):
    path, envelope, _, _ = goal_inputs(tmp_path, strategy="multi_shot")
    row = envelope["bindings"][0]
    if mutation == "missing_user":
        envelope["bindings"].pop(0)
    elif mutation == "missing_requirement": row["requirement_ids"] = []
    elif mutation == "missing_scope": row["constraint_ids"] = []
    elif mutation == "missing_unit": row["unit_ids"].pop()
    elif mutation.startswith("unknown_") and mutation != "unknown_field":
        key = {"unknown_intent": "intent_item_id", "unknown_requirement": "requirement_ids",
            "unknown_unit": "unit_ids", "unknown_constraint": "constraint_ids"}[mutation]
        row[key] = "unknown" if key == "intent_item_id" else ["unknown"]
    elif mutation == "duplicate_row": envelope["bindings"].append(row)
    elif mutation.startswith("duplicate_"):
        key = mutation.removeprefix("duplicate_") + "_ids"
        row[key].append(row[key][0])
    elif mutation == "unknown_field": row["mutable_status"] = "accepted"
    elif mutation == "wrong_version": envelope["schema_version"] = "creative-goal-binding/2"
    elif mutation == "wrong_authority": envelope["authority"] = "production"
    else: envelope["bindings"] = []
    write_json(path, envelope)
    with pytest.raises(binding.GoalBindingError) as exc:
        binding.load_goal_binding(path)
    assert exc.value.code == code
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize("name", ["creative_input", "coverage", "final_output_contract"])
def test_stale_file_reference(tmp_path, name):
    path, envelope, _, _ = goal_inputs(tmp_path)
    with (tmp_path / envelope[name]["path"]).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(binding.GoalBindingError) as exc:
        binding.load_goal_binding(path)
    assert exc.value.code == ("source_identity_mismatch" if name == "creative_input" else "stale_binding")


@pytest.mark.parametrize("raw", [b"\xff", "changed input".encode(),
    "前轮：可见使用动作。不要凭空增加人物。\r\n当轮：继续生成。\r\n".encode()])
def test_source_is_exact_utf8_bytes_not_trimmed_or_newline_normalized(tmp_path, raw):
    path, envelope, _, _ = goal_inputs(tmp_path)
    (tmp_path / "input.txt").write_bytes(raw)
    envelope["creative_input"]["sha256"] = hashlib.sha256(raw).hexdigest()
    write_json(path, envelope)
    with pytest.raises(binding.GoalBindingError) as exc:
        binding.load_goal_binding(path)
    assert exc.value.code in {"invalid_encoding", "source_identity_mismatch"}


@pytest.mark.parametrize("escape", ["../outside.txt", "/tmp/outside.txt", "folder/../input.txt", "link.txt", "dir/input.txt", "."])
def test_nonregular_or_escaping_references_rejected(tmp_path, escape):
    path, envelope, _, _ = goal_inputs(tmp_path / "inputs")
    (tmp_path / "outside.txt").write_text("outside")
    (path.parent / "link.txt").symlink_to(path.parent / "input.txt")
    (path.parent / "dir").symlink_to(path.parent, target_is_directory=True)
    envelope["creative_input"]["path"] = escape
    write_json(path, envelope)
    with pytest.raises(binding.GoalBindingError) as exc:
        binding.load_goal_binding(path)
    assert exc.value.code == "invalid_reference"


def test_legacy_v3_and_empty_v4_inventory_remain_compatible_only_at_old_entry(tmp_path):
    path, envelope, coverage, _ = goal_inputs(tmp_path)
    validator = _load_validator()
    coverage["intent_items"] = []
    coverage["intent_groups"] = {name: [] for name in coverage["intent_groups"]}
    assert validator.validate_director_coverage(coverage)["status"] == "passed"
    reseal(path, envelope, "coverage", coverage)
    with pytest.raises(binding.GoalBindingError, match="unbound_user_intent"):
        binding.load_goal_binding(path)
    coverage["schema_version"] = "3"
    del coverage["intent_items"], coverage["intent_groups"]
    assert validator.validate_director_coverage(coverage)["status"] == "passed"
    reseal(path, envelope, "coverage", coverage)
    with pytest.raises(binding.GoalBindingError, match="unsupported_coverage_version"):
        binding.load_goal_binding(path)


def test_existing_validator_rejects_changed_quote_even_with_current_file_hash(tmp_path):
    path, envelope, coverage, _ = goal_inputs(tmp_path)
    coverage["intent_items"][0]["source_refs"][0]["quote"] = "Invented quote"
    reseal(path, envelope, "coverage", coverage)
    with pytest.raises(binding.GoalBindingError, match="invalid_coverage"):
        binding.load_goal_binding(path)


def test_director_choice_cannot_replace_a_missing_user_binding(tmp_path):
    path, envelope, coverage, _ = goal_inputs(tmp_path)
    choice = {**coverage["intent_items"][0], "intent_item_id": "choice", "origin": "director_choice"}
    choice["source_refs"] = [{**choice["source_refs"][0], "intent_item_id": "choice", "origin": "director_choice"}]
    coverage["intent_items"].append(choice)
    coverage["intent_groups"]["must_happen"].append({"intent_item_id": "choice"})
    envelope["bindings"][0]["intent_item_id"] = "choice"
    reseal(path, envelope, "coverage", coverage)
    with pytest.raises(binding.GoalBindingError, match="unbound_user_intent"):
        binding.load_goal_binding(path)


def test_approved_static_brand_direction_and_vague_semantics_are_only_structurally_verified(tmp_path):
    path, envelope, coverage, contract = goal_inputs(tmp_path)
    source = "用户：同意固定商品静物品牌片。不要凭空增加人物。\n"
    raw = source.encode()
    (tmp_path / "input.txt").write_bytes(raw)
    envelope["creative_input"]["sha256"] = hashlib.sha256(raw).hexdigest()
    coverage["request"]["creative_input_evidence"] = source
    coverage["request"]["creative_constraints"][0].update(scope="global", source_text="固定商品静物品牌片")
    coverage["intent_items"][0]["statement"] = "固定商品静物品牌片"
    coverage["intent_items"][0]["source_refs"][0]["quote"] = "固定商品静物品牌片"
    for item in coverage["intent_items"]:
        item["source_refs"][0]["source_hash"] = hashlib.sha256(raw).hexdigest()
    envelope["bindings"][0]["unit_ids"] = []
    reseal(path, envelope, "coverage", coverage)
    vague = contract.model_copy(update={"user_goal": "整体好看"})
    reseal(path, envelope, "final_output_contract", vague.model_dump(mode="json"))
    assert binding.load_goal_binding(path).diagnostics == ()


@pytest.mark.parametrize("target", ["binding.json", "coverage.json", "contract.json"])
def test_unknown_or_duplicate_json_fields_are_rejected(tmp_path, target):
    path, envelope, _, _ = goal_inputs(tmp_path)
    file = tmp_path / target
    if target == "binding.json":
        file.write_text('{"schema_version":"creative-goal-binding/1","schema_version":"creative-goal-binding/1"}')
    else:
        payload = json.loads(file.read_text())
        payload["unrecognized_field"] = True
        name = "coverage" if target == "coverage.json" else "final_output_contract"
        reseal(path, envelope, name, payload)
    with pytest.raises(binding.GoalBindingError):
        binding.load_goal_binding(path)


def test_private_cli_json_and_safe_failure(tmp_path, capsys):
    path, envelope, _, _ = goal_inputs(tmp_path)
    assert binding.main(["--binding", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["authority"] == "development_only"
    assert result["contract_hash"] == binding.load_goal_binding(path).contract.contract_hash
    envelope["bindings"] = []
    write_json(path, envelope)
    assert binding.main(["--binding", str(path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["diagnostics"][0]["code"] == "unbound_user_intent"
    assert "前轮" not in json.dumps(result, ensure_ascii=False)
