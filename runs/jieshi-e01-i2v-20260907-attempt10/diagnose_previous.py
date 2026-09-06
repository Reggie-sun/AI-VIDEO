"""Project the frozen previous Gate without changing its observations or bytes."""
import hashlib
import json
from pathlib import Path

from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.generation_decision import GenerationCandidate
from ai_video.production.generation_diagnosis import AttemptEvidence, Finding, diagnose_exact_result
from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
from ai_video.production.hashing import canonical_sha256
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.video import VideoGenerationRequest
from ai_video.production.vidu import ViduVideoProvider
from ai_video.production.vidu_profile import ViduProviderProfile

RUN = Path(__file__).resolve().parent
PREVIOUS = RUN.parent / "jieshi-e01-i2v-20260906-attempt09"
PREP = PREVIOUS / "preparation-v1"
SHA = "7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302"


def save(name, value):
    value = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    raw = (PREVIOUS / f"production-s01-v9/state/video-generation/fetch/files/{SHA}.mp4").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA and len(raw) == 3476468
    gate = (PREP / "shot-01-gate.md").read_bytes()
    gate_sha = hashlib.sha256(gate).hexdigest()
    rows = []
    for line in gate.decode().splitlines():
        if line.startswith("| "):
            cells = tuple(s.strip() for s in line.strip("|").split("|"))
            if len(cells) == 3 and cells[1] in {"PASS", "FAIL", "NOT_EVALUATED"}:
                rows.append(cells)
    assert len(rows) == 15, "Do not silently omit historical required findings"
    rules = tuple(RequirementExpression(
        requirement_id=f"legacy-{index:02d}", level="acceptance",
        stage="final_composition" if title == "Final narrative subtitle" else "raw_generation",
        dimension=title, observable=title,
        tolerance="Preserve the frozen Gate wording; any interpretation correction needs an explicit new owner version.",
        measurement=observation,
        proof="human" if title == "Mouth/ambience/mix quality" else
              "technical" if title in {"Registered first/last inputs", "1080p 9:16 output", "Native audio"} else "analyzer",
        production_owner="jieshi-episode-01/S01/shot-01-gate",
    ) for index, (title, _, observation) in enumerate(rows, 1))
    ids = tuple(rule.requirement_id for rule in rules)
    payload = dict(domain_id="jieshi", profile_id="s01-attempt09-gate-projection", profile_version="1",
        measurement_contract_version="legacy-gate-projection/1", required_requirement_ids=ids,
        generation_requirements=tuple(r.model_dump(mode="json", exclude={"native_text"}) for r in rules),
        source_gate_sha256=gate_sha,
        authority="Retrospective diagnosis projection only; not a claim this typed recipe was sealed before attempt09. Native expression coverage is not prepared for submit. Final subtitle belongs to composition under accepted decision-loop spec.")
    rubric_hash = canonical_sha256(payload)
    acceptance = DomainAcceptancePolicy(**{k: payload[k] for k in (
        "domain_id", "profile_id", "profile_version", "measurement_contract_version", "required_requirement_ids")},
        profile_content_hash=rubric_hash, profile_payload={**payload, "content_hash": rubric_hash})
    baseline = VideoGenerationRequest.model_validate(json.loads((PREP / "compiled-request.json").read_text())["request"])
    assert baseline.seed is None
    profile = ViduProviderProfile.model_validate_json((PREVIOUS / "provider-profile.json").read_bytes())
    requirement = json.loads((PREP / "verified-requirement.json").read_text())["requirement"]
    compiler = AdapterCompilerContract.create(compiler_id=baseline.adapter_compiler_id, compiler_version=baseline.adapter_compiler_version)
    assert baseline.provider_profile == profile.pointer() and baseline.adapter_compiler_hash == compiler.compiler_hash
    recipe = GenerationRecipe(seed=SeedPolicy(kind="uncontrolled"), profile_sha256=profile.pointer().profile_sha256,
        compiler_hash=compiler.compiler_hash, requirement_hash=requirement["requirement_hash"],
        rubric_hash=rubric_hash, acceptance_policy=acceptance, expressions=rules)
    candidate = GenerationCandidate(candidate_id="historical-attempt09", provider_profile=profile.pointer(),
        capabilities=ViduVideoProvider(profile=profile, transport=None, credential=lambda: None).capabilities(),
        capability_id="viduq3-pro-i2v-v1", compiler_contract=compiler,
        output_requirement=baseline.output_requirement, recipe=recipe)
    facts = canonical_sha256({k: v for k, v in requirement.items() if k not in {"requirement_id", "requirement_hash"}})
    evidence = AttemptEvidence(task_id="jieshi-e01-s01-repair", shot_id="S01", attempt_id="attempt09",
        recipe_scope_hash=candidate.scope_hash, facts_hash=facts, rubric_hash=rubric_hash,
        request_hash=baseline.request_input_hash, artifact_sha256=SHA, outcome="media",
        findings=tuple(Finding(requirement_id=rule.requirement_id, rubric_hash=rubric_hash,
            stage=rule.stage, proof=rule.proof, verdict=row[1], source_sha256=gate_sha, observation=row[2])
            for rule, row in zip(rules, rows) if rule.stage == "raw_generation"))
    result = diagnose_exact_result(evidence, (evidence,), recipe)
    assert set(result.failure_classes) == {"QUALITY_FAILURE", "EVIDENCE_GAP"}
    save("historical-candidate.json", candidate)
    save("historical-evidence.json", evidence)
    save("previous-diagnosis.json", result)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
