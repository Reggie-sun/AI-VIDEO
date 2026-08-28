from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "distill-ai-video-learning"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
TEMPLATE_PATH = SKILL_ROOT / "templates" / "learning-claim.md"
RECORD_SKILL_PATH = (
    ROOT / ".agents" / "skills" / "record-ai-video-session" / "SKILL.md"
)
RETRIEVE_SKILL_PATH = (
    ROOT / ".agents" / "skills" / "retrieve-ai-video-memory" / "SKILL.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_learning_skill_package_is_minimal_and_discoverable() -> None:
    expected = {
        SKILL_PATH,
        TEMPLATE_PATH,
        SKILL_ROOT / "scripts" / "validate_evidence_identity.py",
    }

    assert {path for path in expected if not path.is_file()} == set()
    package_files = {
        path
        for path in SKILL_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    assert package_files == expected

    text = _read(SKILL_PATH)
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None
    frontmatter = yaml.safe_load(match.group(1))
    assert frontmatter["name"] == "distill-ai-video-learning"
    assert "automatically" in frontmatter["description"]
    assert "user confirmation" in frontmatter["description"]
    assert "templates/learning-claim.md" in text


def test_learning_skill_has_bounded_candidate_and_confirmation_contract() -> None:
    text = _read(SKILL_PATH)
    normalized = " ".join(text.split()).casefold()

    for threshold in (
        "two independent attempts",
        "controlled comparison with multiple arms",
        "materially supports, counters, narrows, or reopens an existing claim",
    ):
        assert threshold in text
    for field in (
        "failure_pattern",
        "hypothesis",
        "supporting_evidence",
        "counter_evidence",
        "scope",
        "exclusions",
        "evidence_status",
        "recommended_action",
        "adoption_target",
        "approval_status",
        "adoption_status",
    ):
        assert field in text

    assert "PENDING_CONFIRMATION" in text
    assert "CONFIRMED" in text
    assert "REJECTED" in text
    assert "exact candidate bytes SHA-256" in text
    assert "candidate checkpoint commit" in text
    assert "git show" in text
    assert "confirmed_candidate_commit" in text
    assert "active_claim_version: 0" in text
    assert "`NONE` is allowed only as the sentinel" in text
    assert "confirmation_evidence" in text
    assert "changed bytes require a new confirmation" in normalized
    assert "ADOPTED" in text
    assert "target owner verification" in text
    assert "preserve the active claim" in normalized
    assert "does not replace the active claim" in normalized
    for identity in (
        "evidence_id",
        "independence_key",
        "experiment_id",
        "attempt_id",
        "arm_id",
        "artifact_sha256",
    ):
        assert identity in text
    for basis in (
        "TWO_INDEPENDENT_ATTEMPTS",
        "CONTROLLED_MULTI_ARM",
        "MATERIAL_EXISTING_CLAIM_UPDATE",
    ):
        assert basis in text
    assert "document count" in normalized
    assert "RAG hit" in text
    assert "proof layer" in normalized
    assert "unique `independence_key`" in text


def test_learning_skill_keeps_automatic_work_advisory_and_fail_closed() -> None:
    text = _read(SKILL_PATH)

    for target in (
        "Skill",
        "Provider Policy",
        "Preflight",
        "Contract",
        "Gate",
    ):
        assert target in text
    for forbidden in (
        "MUST NOT call a Provider",
        "MUST NOT generate media",
        "MUST NOT write Manifest, Registry, P6, or Final Acceptance state",
        "MUST NOT automatically retry, activate, push, or release",
        "MUST NOT commit an adoption target before user confirmation",
        "MUST NOT modify an adoption target before user confirmation",
    ):
        assert forbidden in text

    assert "RAG score is not evidence confidence" in text
    assert "no_candidate" in text


def test_record_skill_automatically_routes_stable_records_to_learning_evaluation() -> None:
    text = _read(RECORD_SKILL_PATH)
    normalized = " ".join(text.split()).casefold()

    assert "distill-ai-video-learning" in text
    assert "automatic learning evaluation" in text
    assert "must not wait for the user to request distillation" in normalized
    assert "no_candidate" in text
    assert "does not authorize adoption" in text
    assert "session boundary" in normalized
    assert "experiment boundary" in normalized
    assert "Evidence Index" in text
    assert "does not count" in normalized


def test_learning_claim_template_separates_evidence_approval_and_adoption() -> None:
    text = _read(TEMPLATE_PATH)

    assert "document_kind: learning_claim" in text
    assert "active_claim_version: 0" in text
    assert "active_evidence_status: NONE" in text
    assert "active_adoption_status: NOT_ADOPTED" in text
    assert "pending_claim_version: 1" in text
    assert "pending_evidence_status: SUPPORTED" in text
    assert "pending_approval_status: PENDING_CONFIRMATION" in text
    assert "pending_adoption_status: NOT_ADOPTED" in text
    assert "confirmed_candidate_sha256:" in text
    assert "confirmed_candidate_commit:" in text
    assert "confirmed_by:" in text
    assert "confirmed_at:" in text
    assert "confirmation_evidence:" in text
    assert 'evidence_index_version: "1"' in text
    assert "admission_basis:" in text
    assert "material_update_target_claim:" in text
    assert "material_update_previous_evidence:" in text
    assert "material_update_delta:" in text
    assert "| evidence_ref | independence_key |" in text
    for heading in (
        "## Active Claim",
        "## Pending Candidate",
        "### Failure Pattern",
        "### Hypothesis",
        "### Supporting Evidence",
        "### Counter Evidence",
        "### Scope And Exclusions",
        "### Evidence Assessment",
        "### Recommended Action",
        "### Adoption Target",
        "### Confirmation",
        "### Adoption Evidence",
        "## Supersession And Reopen Conditions",
    ):
        assert heading in text


def test_learning_claim_template_uses_english_headings_and_chinese_body() -> None:
    skill = _read(SKILL_PATH)
    text = _read(TEMPLATE_PATH)
    body = text.split("---\n", 2)[2]
    headings = [
        line.lstrip("# ")
        for line in body.splitlines()
        if line.startswith("#")
    ]
    normalized_skill = " ".join(skill.split())

    assert "English section titles" in normalized_skill
    assert "Chinese narrative" in normalized_skill
    assert headings
    assert all(not re.search(r"[\u4e00-\u9fff]", heading) for heading in headings)
    assert re.search(r"[\u4e00-\u9fff]", body)
    for field in (
        "`failure_pattern`",
        "`hypothesis`",
        "`supporting_evidence`",
        "`counter_evidence`",
        "`adoption_target`",
    ):
        assert field in body


def test_checked_in_learning_claims_follow_active_pending_contract() -> None:
    learning_root = ROOT / "docs" / "record_for_agent" / "learning"

    for path in learning_root.rglob("*.md") if learning_root.is_dir() else ():
        text = _read(path)
        match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert match is not None, path
        frontmatter = yaml.safe_load(match.group(1))
        assert frontmatter["document_kind"] == "learning_claim", path
        for key in (
            "claim_id",
            "active_claim_version",
            "active_evidence_status",
            "active_adoption_status",
            "pending_claim_version",
            "pending_evidence_status",
            "pending_approval_status",
            "pending_adoption_status",
            "confirmed_candidate_sha256",
            "confirmed_candidate_commit",
            "confirmed_by",
            "confirmed_at",
            "confirmation_evidence",
        ):
            assert key in frontmatter, (path, key)
        assert "## Active Claim" in text, path
        assert "## Pending Candidate" in text, path

        active_version = frontmatter["active_claim_version"]
        if active_version == 0:
            assert frontmatter["active_evidence_status"] == "NONE", path
            assert frontmatter["active_adoption_status"] == "NOT_ADOPTED", path
        else:
            assert frontmatter["active_evidence_status"] in {
                "SINGLE_CASE",
                "SUPPORTED",
                "CONTESTED",
                "REFUTED",
                "RETIRED",
            }, path
            assert frontmatter["active_adoption_status"] in {
                "ADOPTED",
                "RETIRED",
            }, path

        assert frontmatter["pending_evidence_status"] in {
            "SINGLE_CASE",
            "SUPPORTED",
            "CONTESTED",
            "REFUTED",
            "RETIRED",
        }, path
        assert frontmatter["pending_approval_status"] in {
            "PENDING_CONFIRMATION",
            "CONFIRMED",
            "REJECTED",
        }, path
        assert frontmatter["pending_adoption_status"] in {
            "NOT_ADOPTED",
            "APPLYING",
        }, path

        if frontmatter["pending_approval_status"] == "CONFIRMED":
            assert re.fullmatch(
                r"[0-9a-f]{64}", frontmatter["confirmed_candidate_sha256"]
            ), path
            assert re.fullmatch(
                r"[0-9a-f]{40,64}", frontmatter["confirmed_candidate_commit"]
            ), path
            assert frontmatter["confirmed_by"], path
            assert frontmatter["confirmed_at"], path
            assert frontmatter["confirmation_evidence"], path


def test_canonical_routing_keeps_learning_in_development_governance() -> None:
    agents = _read(ROOT / "AGENTS.md")
    playbook = _read(ROOT / ".agent" / "context" / "control-plane-playbook.md")
    matrix = _read(ROOT / "docs" / "agent-primary-contract-matrix.md")
    baseline = _read(ROOT / "docs" / "v0.2-runtime-baseline.md")
    roadmap = _read(ROOT / "docs" / "v0.2-agentic-production-roadmap.md")
    retrieval = _read(RETRIEVE_SKILL_PATH)

    assert "## Experience Learning Routing" in agents
    assert "`distill-ai-video-learning` after stable record" in agents
    assert "### Experience Learning And Confirmation" in playbook
    assert "| Experience Learning And Confirmation |" in matrix
    assert "Q1 automatic recommendation" in baseline
    assert "| Experience Learning + Human Confirmation |" in roadmap
    assert "`advisory_learning`" in retrieval
