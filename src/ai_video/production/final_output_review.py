"""Review-owned final-output adjudication; no media effects or state writes."""

from collections.abc import Mapping
from typing import Literal

from pydantic import Field

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.models import EvidenceStrength, QaLayer, QaVerdict


class FinalOutputFinding(StrictModel):
    requirement_id: str = Field(min_length=1)
    verdict: Literal["pass", "fail", "not_evaluated"]
    observation: str = Field(min_length=1)


class FinalOutputObservation(StrictModel):
    contract_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_request_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    viewing_speed_milli: int | None = Field(default=None, strict=True, gt=0)
    findings: tuple[FinalOutputFinding, ...] = Field(min_length=1)


def adjudicate_final_output(contract, evidence, *, review_request_content_hash):
    """Require all authored observations; never infer a human viewing verdict."""
    rules = {r.requirement_id: r for r in contract.requirements}
    observations = {name: [] for name in rules}
    incomplete = False
    for item in evidence:
        payload = item.measured_payload.get("final_output")
        if not isinstance(payload, Mapping):
            incomplete = True
            continue
        try:
            source = FinalOutputObservation.model_validate(dict(payload))
        except ValueError:
            incomplete = True
            continue
        if (source.contract_hash != contract.contract_hash
                or source.review_request_content_hash != review_request_content_hash):
            incomplete = True
            continue
        ids = [f.requirement_id for f in source.findings]
        if len(ids) != len(set(ids)) or not set(ids) <= set(rules):
            incomplete = True
            continue
        for finding in source.findings:
            rule = rules[finding.requirement_id]
            if rule.proof == "human" and (
                item.strength is not EvidenceStrength.HUMAN
                or source.viewing_speed_milli != 1000
            ):
                incomplete = True
                continue
            observations[finding.requirement_id].append(finding.verdict)
    if any("fail" in values for values in observations.values()):
        return QaVerdict.FAIL
    if incomplete or any(not values or any(v != "pass" for v in values) for values in observations.values()):
        return QaVerdict.NOT_EVALUATED
    return QaVerdict.PASS


def adjudicate_semantic_review(policy, evidence, *, review_request_content_hash):
    """Apply the final-output contract before domain-specific semantic checks."""
    authorized = [
        item
        for item in evidence
        if item.strength
        in {EvidenceStrength.EXPLICIT_EVALUATOR, EvidenceStrength.HUMAN}
        and item.tool_identity in policy.semantic_authorities
        and isinstance(item.measured_payload.get("evaluator_identity"), str)
        and item.measured_payload.get("evaluator_identity")
        == f"{item.tool_identity.name}@{item.tool_identity.version}"
    ]
    if not authorized:
        return QaVerdict.NOT_EVALUATED
    if policy.final_output is not None:
        final_verdict = adjudicate_final_output(policy.final_output, authorized,
            review_request_content_hash=review_request_content_hash)
        if final_verdict is not QaVerdict.PASS or policy.domain_acceptance is None:
            return final_verdict
    if policy.domain_acceptance is not None:
        if policy.domain_acceptance.domain_id != "ecommerce":
            return QaVerdict.NOT_EVALUATED
        from ai_video.production.ecommerce_media_acceptance import (
            EcommerceAcceptanceEvidencePayload,
            adjudicate_ecommerce_acceptance,
        )
        from ai_video.production.ecommerce_quality_gate import (
            validate_ecommerce_review_evidence_binding,
        )

        verdicts: list[QaVerdict] = []
        for item in authorized:
            if not validate_ecommerce_review_evidence_binding(
                policy=policy,
                evidence=item,
                review_request_content_hash=review_request_content_hash,
            ):
                return QaVerdict.NOT_EVALUATED
            payload = item.measured_payload.get("domain_acceptance")
            if not isinstance(payload, Mapping):
                return QaVerdict.NOT_EVALUATED
            try:
                typed_payload = EcommerceAcceptanceEvidencePayload.model_validate(
                    dict(payload)
                )
            except ValueError:
                return QaVerdict.NOT_EVALUATED
            verdicts.append(
                adjudicate_ecommerce_acceptance(
                    policy.domain_acceptance,
                    typed_payload,
                )
            )
        if any(verdict is QaVerdict.FAIL for verdict in verdicts):
            return QaVerdict.FAIL
        if any(verdict is not QaVerdict.PASS for verdict in verdicts):
            return QaVerdict.NOT_EVALUATED
        return QaVerdict.PASS
    return (
        QaVerdict.PASS
        if all(item.measured_payload.get("semantic_match") is True for item in authorized)
        else QaVerdict.FAIL
    )


def require_viable_repair_proposal(action):
    """Known violations reject previews and all other operation kinds equally."""
    if action.known_requirement_violations:
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output no-regression gate: proposal has known requirement violations.")


def reopen_review_verdict(root, pointer):
    """Recompute the existing review chain under its exact retained QA policy."""
    from ai_video.production.project import (
        load_qa_policy, load_review_evidence, load_review_receipt, load_review_request,
    )
    from ai_video.production.review import adjudicate_review_evidence

    receipt = load_review_receipt(root, pointer)
    request = load_review_request(root, receipt.review_request)
    policy = load_qa_policy(root, receipt.qa_policy)
    evidence = tuple(load_review_evidence(root, p) for p in receipt.evidence)
    if (request.qa_policy != receipt.qa_policy
            or request.render_state != receipt.render_state
            or request.render_output_sha256 != receipt.render_output_sha256
            or request.timeline_fingerprint != receipt.timeline_fingerprint
            or request.dependency_graph.revision_id != receipt.dependency_graph_revision_id
            or receipt.layer not in request.requested_layers
            or any(e.tool_identity not in request.evidence_tool_identities for e in evidence)
            or any(e.tool_identity not in receipt.tool_identities for e in evidence)):
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output review request/evidence identity mismatch.")
    verdict = adjudicate_review_evidence(policy, receipt.layer, evidence,
        review_request_content_hash=request.content_hash, caption_context=request.caption_context)
    if verdict is not receipt.verdict:
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output review verdict differs from its original evidence.")
    return receipt


def require_repair_baseline(root, approved, policy):
    """Keep all original requirements and exact baseline evidence immutable."""
    require_viable_repair_proposal(approved.selected_repair_action)
    pointers = approved.baseline_review_receipts
    if not pointers or tuple(p.review_id for p in pointers) != approved.review_receipt_ids:
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output repair requires exact complete baseline review pointers.")
    reviews = tuple(reopen_review_verdict(root, p) for p in pointers)
    layers = {r.layer for r in reviews}
    required = set(policy.required_layers) - {QaLayer.FINAL_ACCEPTANCE}
    if (len(layers) != len(reviews) or not required <= layers
            or any(r.qa_policy != approved.qa_policy
                or r.render_state != approved.render_state
                or r.render_output_sha256 != approved.render_output_sha256
                or r.timeline_fingerprint != approved.timeline_fingerprint
                or r.dependency_graph_revision_id != approved.dependency_graph.revision_id
                for r in reviews)):
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output repair baseline omits requirements or substitutes identities.")
    return reviews


def reopen_repair_approval(root, pointer):
    from ai_video.production.hashing import verify_artifact_hash
    from ai_video.production.models import ApprovedRepairReceipt
    from ai_video.production.paths import _read_regular_file_nofollow

    snapshot = _read_regular_file_nofollow(root / pointer.path, contained_by=root / "state")
    approved = ApprovedRepairReceipt.model_validate_json(snapshot.data)
    if (snapshot.file_sha256 != pointer.file_sha256 or approved.content_hash != pointer.content_hash
            or approved.repair_id != pointer.repair_id or not verify_artifact_hash(approved)):
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID, "Final-output repair approval identity is invalid.")
    return approved


def require_preserved_repair_layers(root, manifest, request, policy):
    """A subsequent repair cannot reset the same goal's prior layer obligations."""
    from ai_video.production.models import StateCommitStatus
    from ai_video.production.project import load_qa_policy

    goal = policy.final_output
    required = set()
    for attempt in manifest.attempts:
        if attempt.operation != "repair" or attempt.status is not StateCommitStatus.SUCCEEDED:
            continue
        prior = reopen_repair_approval(root, attempt.approved_repair_receipt)
        previous_policy = load_qa_policy(root, prior.qa_policy)
        previous_goal = previous_policy.final_output
        if (goal is not None and previous_goal is not None
                and (goal.goal_id, goal.goal_version) != (previous_goal.goal_id, previous_goal.goal_version)):
            continue
        required.update(p.layer for p in prior.baseline_review_receipts)
        required.update(set(previous_policy.required_layers) - {QaLayer.FINAL_ACCEPTANCE})
    if not required <= {p.layer for p in request.baseline_review_receipts}:
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output subsequent repair cannot omit the original goal's review requirements.")


def require_no_regression_outcome(root, approved, receipt, manifest, current_render):
    from ai_video.production.project import load_qa_policy

    if manifest.active_qa_policy != approved.qa_policy:
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output repair cannot replace its frozen goal/QA policy.")
    policy = load_qa_policy(root, approved.qa_policy)
    baseline = require_repair_baseline(root, approved, policy)
    # Protect optional baseline layers too; missing proof is never no-regression.
    required = {r.layer for r in baseline} | (set(policy.required_layers) - {QaLayer.FINAL_ACCEPTANCE})
    reviews = tuple(reopen_review_verdict(root, p) for p in receipt.fresh_review_receipts)
    layers = {r.layer for r in reviews}
    if len(layers) != len(reviews):
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            "Final-output no-regression gate: duplicate review layers.")
    for review in reviews:
        if (review.qa_policy != approved.qa_policy
                or review.render_state != manifest.active_render_state
                or review.render_output_sha256 != current_render.output.file_sha256
                or review.timeline_fingerprint != current_render.timeline_fingerprint
                or review.dependency_graph_revision_id != manifest.active_dependency_graph.revision_id):
            raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
                "Final-output no-regression gate: new output needs new exact evidence.")
    actual = QaVerdict.PASS
    if any(r.verdict is QaVerdict.FAIL for r in reviews):
        actual = QaVerdict.FAIL
    elif not required <= layers or any(r.verdict is not QaVerdict.PASS for r in reviews):
        actual = QaVerdict.NOT_EVALUATED
    if receipt.verdict != actual.value:
        raise AiVideoError(ErrorCode.REPAIR_SCOPE_INVALID,
            f"Final-output no-regression gate: repair {actual.value.upper()}; claimed outcome differs from complete evidence.")


def require_closed_repairs(root, manifest):
    """Final Acceptance cannot bypass the approved repair's comparison gate."""
    from ai_video.production.hashing import verify_artifact_hash
    from ai_video.production.models import RepairOutcomeReceipt, StateCommitStatus
    from ai_video.production.paths import _read_regular_file_nofollow
    from ai_video.production.project import load_qa_policy

    current_goal = load_qa_policy(root, manifest.active_qa_policy).final_output
    pending = set()
    latest = None
    for attempt in manifest.attempts:
        if attempt.operation != "repair" or attempt.status is not StateCommitStatus.SUCCEEDED:
            continue
        pointer = attempt.approved_repair_receipt
        approved = reopen_repair_approval(root, pointer)
        original_policy = load_qa_policy(root, approved.qa_policy)
        original_goal = original_policy.final_output
        if (original_goal is not None and current_goal is not None
                and (original_goal.goal_id, original_goal.goal_version)
                    != (current_goal.goal_id, current_goal.goal_version)):
            # This accepts only the explicitly versioned new goal. The old
            # approval, failed reviews and lack of successful outcome stay intact.
            continue
        if approved.baseline_review_receipts:
            require_repair_baseline(root, approved, original_policy)
        pending.add(pointer)
        latest = pointer
    latest_passed = latest is None
    for pointer in manifest.repair_outcome_receipts:
        snapshot = _read_regular_file_nofollow(root / pointer.path, contained_by=root / "state")
        outcome = RepairOutcomeReceipt.model_validate_json(snapshot.data)
        if (snapshot.file_sha256 != pointer.file_sha256
                or outcome.content_hash != pointer.content_hash
                or not verify_artifact_hash(outcome)):
            raise AiVideoError(ErrorCode.FINAL_ACCEPTANCE_INVALID,
                "Final-output repair outcome identity is invalid.")
        pending.discard(outcome.approved_receipt)
        if outcome.approved_receipt == latest:
            latest_passed = outcome.verdict == "pass"
    if pending or not latest_passed:
        raise AiVideoError(ErrorCode.FINAL_ACCEPTANCE_INVALID,
            "Final-output no-regression gate: repairs need closed outcomes and the latest repair must pass before Final Acceptance.")
