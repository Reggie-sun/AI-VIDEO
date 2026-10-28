"""Offline checks for task data. Does not qualify media, bootstrap or submit."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.production._video_intent_validation import (
    validate_conditioning_compatibility,
    validate_generation_intent_for_continuity,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import Shot
from ai_video.production.video_requirement import (
    AudioNeed,
    ConditioningCompatibilityEvidence,
    GenerationIntent,
    OutputNeed,
    ProviderNeutralGenerationIntentProjection,
    QualityNeed,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    row = json.loads((HERE / "row.json").read_text())
    data = json.loads((HERE / "data.json").read_text())
    prompt = (HERE / "native-prompt.zh.txt").read_text().strip()
    assert prompt == row["shot"]["intent"]
    assert len(prompt) <= 500
    assert not any("A" <= char <= "Z" or "a" <= char <= "z" for char in prompt)
    assert len(data["images"]) == 2
    assert [ref["role"] for ref in row["generation"]["references"]] == ["approved_keyframe", "last_frame"]
    assert [ref["asset_id"] for ref in row["generation"]["references"]] == [image["asset_id"] for image in data["images"]]
    assert data["actual_model_inputs_planned"] == [image["asset_id"] for image in data["images"]]
    assert sha(ROOT / data["source_contract"]["path"]) == data["source_contract"]["sha256"]
    packet = {"source_snapshot_sha256": canonical_sha256({"row": row, "data": data}),
              "assets": [{"id": image["node_id"], "type": "image", "data": {"resourceId": image["resource_id"]}}
                         for image in data["images"]]}
    registry, artifacts = prepare_canvas_png_assets(packet=packet, selections=data["images"], allowed_asset_root=ROOT)
    assert len(registry.assets) == 2
    assert all(asset.source_kind.value == "derived" for asset in registry.assets)
    assert artifacts
    intent = GenerationIntent.model_validate(row["generation"]["generation_intent"])
    assert canonical_sha256(intent.model_dump(mode="json")) == data["intent_sha256"]
    diagnostics = validate_generation_intent_for_continuity(intent, audio_need=AudioNeed.REQUIRED)
    assert diagnostics == ()
    # Structural-only in-memory Shot validation. This is not a sealed project artifact.
    Shot.model_validate({"artifact_id": "MC00-task-local-structure-check", "revision": 1,
        "content_hash": "0" * 64, "creation_receipt_id": "MC00-task-local-structure-check",
        "source_provenance": [{"kind": "derived", "reference": data["source_contract"]["path"],
                               "content_hash": data["source_contract"]["sha256"]}], **row["shot"]})
    compatibility = ConditioningCompatibilityEvidence.model_validate(row["generation"]["conditioning_compatibility"])
    expected_blockers = validate_conditioning_compatibility(compatibility)
    assert "conditioning_compatibility.same_subject_scale" in expected_blockers
    projected = {key: value for key, value in row["generation"].items() if key not in {"references", "intent_evidence"}}
    projected["generation_intent"] = intent
    projected["conditioning_compatibility"] = compatibility
    projected["output_need"] = OutputNeed.model_validate(projected["output_need"])
    projected["quality_need"] = QualityNeed.model_validate(projected["quality_need"])
    projected["audio_need"] = AudioNeed(projected["audio_need"])
    projected["semantic_reference_roles"] = ["first_frame", "last_frame"]
    try:
        ProviderNeutralGenerationIntentProjection.create(**projected)
    except ValidationError as exc:
        assert any("projection requires compatible conditioning" in error["msg"] for error in exc.errors())
    else:
        raise AssertionError("pending conditioning must not become an executable projection")
    for path in HERE.glob("*.py"):
        ast.parse(path.read_text())
    report = {"scope": "task-local offline authoring preparation only", "status": "DRAFT_BLOCKED_NOT_EXECUTABLE",
        "prompt_chars": len(prompt), "pure_chinese_prompt": True, "planned_actual_inputs": 2,
        "standard_png_preparation_in_memory": "PASS", "generation_intent_fields": "PASS",
        "shot_structure_in_memory": "PASS", "overall_projection_expected_rejection": "PASS",
        "conditioning_blockers": list(expected_blockers),
        "files": [{"path": path.name, "sha256": sha(path)} for path in sorted(HERE.glob("*.json"))
                  if path.name != "offline-validation.json"],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "new_run_present_at_validation": (ROOT / "runs/shizhen-macro-opening-20261028/MC00-city-v1").exists(),
        "run_writes_by_this_script": 0, "platform_calls_by_this_script": 0, "new_permit_by_this_script": False,
        "not_proven": ["live profile identity", "native quote", "conditioning compatibility", "camera path feasibility",
                       "actual endpoint pixels", "sound or original-speed junction", "production qualification"]}
    (HERE / "offline-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "prompt_chars", "standard_png_preparation_in_memory",
        "generation_intent_fields", "overall_projection_expected_rejection", "conditioning_blockers")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
