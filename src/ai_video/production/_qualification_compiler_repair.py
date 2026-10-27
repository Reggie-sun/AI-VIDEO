"""One first paid no-effect compiler recovery after retained known-media trials.

Pure scope predicate only. Existing committer checks the registered grant,
complete durable experience and paid history, quota extension and fresh permit.
"""
from ai_video.production.generation_diagnosis import compare_compiled_requests
from ai_video.production.generation_runtime_repair import retarget_preserves_strategy
from ai_video.production.jimeng_prompt import normalize_jimeng_prompt_text


def allows_first_no_effect_compiler_repair(binding, selected) -> bool:
    try:
        if selected is None or binding.policy.execution_purpose != "qualification":
            return False
        inputs, repair = binding.inputs, binding.decision.runtime_repair
        limits = inputs.limits
        if (repair is None or repair.schema_version != "runtime-repair/3"
                or repair.paid_no_effect_retarget is None
                or repair.paid_no_effect_extension is not None
                or binding.decision.intervention is not None
                or limits.paid_submits_used < 2
                or limits.paid_submit_ceiling != limits.paid_submits_used + 1
                or inputs.policy.max_resamples != 0 or limits.generation_forbidden
                or limits.allowed_remote_candidates != (selected.candidate_id,)
                or len(inputs.candidates) != 1 or len(inputs.runtime_repairs) != 1
                or inputs.runtime_repairs[0].consumed
                or inputs.runtime_repairs[0].authorization != repair
                or repair.paid_no_effect_retarget.target_scope_hash != selected.scope_hash
                or any(e.outcome == "unknown_outcome" for e in inputs.evidence)):
            return False
        latest = next(e for e in inputs.evidence if e.evidence_hash == inputs.latest_attempt_hash)
        if (latest.outcome != "not_submitted" or latest.artifact_sha256 is not None
                or latest.findings or latest.unresolved_quality_refs
                or latest.task_id != limits.task_id
                or latest.shot_id != binding.context.target_shot_id
                or latest.attempt_id != repair.attempt_id
                or latest.evidence_hash != repair.evidence_hash):
            return False
        retained = {}
        attempts = {}
        for evidence in inputs.evidence:
            if evidence.task_id != limits.task_id:
                continue
            if evidence.shot_id != latest.shot_id:
                return False
            if evidence.evidence_hash != latest.evidence_hash and (
                    evidence.outcome != "media" or evidence.artifact_sha256 is None):
                return False
            key = (evidence.attempt_id, evidence.request_hash)
            identity = (evidence.shot_id, evidence.outcome, evidence.artifact_sha256)
            if (key in retained and retained[key] != identity
                    or evidence.attempt_id in attempts and attempts[evidence.attempt_id] != key):
                return False
            retained[key] = identity
            attempts[evidence.attempt_id] = key
        if len(retained) != limits.paid_submits_used:
            return False
        sources = [x for x in inputs.experiences if latest in x.evidence]
        if len(sources) != 1:
            return False
        previous = sources[0].candidate
        old_variants = [v for v in previous.capabilities.variants if v.capability_id == previous.capability_id]
        variants = [v for v in selected.capabilities.variants if v.capability_id == selected.capability_id]
        if len(old_variants) != 1 or len(variants) != 1:
            return False
        baseline = inputs.baseline_request
        current = binding.compiled_request.activation_scope.request
        if (old_variants[0].provider_kind != "jimeng" or variants[0].provider_kind != "jimeng"
                or old_variants[0].model_id != variants[0].model_id
                or previous.scope_hash != latest.recipe_scope_hash
                or previous.output_requirement != selected.output_requirement
                or not retarget_preserves_strategy(previous, selected)
                or baseline is None or baseline.request_input_hash != latest.request_hash
                or previous.compiler_contract.compiler_version != "1"
                or selected.compiler_contract.compiler_version != "2"
                or baseline.adapter_compiler_version != "1" or current.adapter_compiler_version != "2"
                or baseline.adapter_compiler_id != current.adapter_compiler_id
                or current.adapter_compiler_id != selected.compiler_contract.compiler_id
                or current.adapter_compiler_hash != selected.compiler_contract.compiler_hash
                or baseline.adapter_compiler_hash != previous.compiler_contract.compiler_hash
                or current.prompt_text != normalize_jimeng_prompt_text(baseline.prompt_text)):
            return False
        changed = set(compare_compiled_requests(baseline, current)["changed_variables"])
        return changed <= {"prompt_text", "provider_profile", "adapter_compiler_version", "adapter_compiler_hash"}
    except (AttributeError, KeyError, StopIteration, TypeError, ValueError):
        return False
