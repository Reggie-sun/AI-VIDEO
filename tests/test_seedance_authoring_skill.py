from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "seedance-authoring"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
OPEN_VIDEO_SKILL_PATH = ROOT / ".agents" / "skills" / "open-video" / "SKILL.md"
REFERENCE_NAMES = {
    "authoring-common.md",
    "seedance-2.0.md",
    "seedance-2.5.md",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_seedance_authoring_is_a_minimal_progressively_loaded_skill() -> None:
    expected_files = {
        SKILL_PATH,
        *(SKILL_ROOT / "references" / name for name in REFERENCE_NAMES),
    }

    assert SKILL_ROOT.is_dir()
    assert {path for path in expected_files if not path.is_file()} == set()
    assert {path for path in SKILL_ROOT.rglob("*") if path.is_file()} == expected_files

    text = _read(SKILL_PATH)
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None
    frontmatter = yaml.safe_load(match.group(1))
    assert frontmatter["name"] == "seedance-authoring"
    description = frontmatter["description"]
    assert description.startswith("Use when ")
    assert "approved AI-VIDEO Shot" in description
    assert "prompt and reference authoring" in description
    assert "Seedance" in description

    linked = set(re.findall(r"references/([a-z0-9.-]+\.md)", text))
    assert linked == REFERENCE_NAMES


def test_dispatch_keeps_modes_as_profiles_and_versions_fail_closed() -> None:
    text = _read(SKILL_PATH)
    normalized = " ".join(text.split())

    assert "T2V" in text
    assert "I2V" in text
    assert "R2V" in text
    assert "FLF2V" in text
    assert "edit" in text
    assert "extend" in text
    assert "mode profile" in text
    assert "MUST NOT dispatch a mode-specific Skill" in text
    assert "Load `references/authoring-common.md`" in text
    assert "exactly one version overlay" in text
    assert "references/seedance-2.0.md" in text
    assert "references/seedance-2.5.md" in text
    assert "第一版 authoring package 有意不支持 Seedance 1.5/1.0" in text
    assert "unknown, future, mixed, or stale" in normalized
    assert "fail closed" in text


def test_skill_keeps_runtime_and_production_authority_outside() -> None:
    text = _read(SKILL_PATH)

    assert "runtime_skill_calls = 0" in text
    for owner in (
        "capability registry",
        "Shot Contract",
        "Provider adapter",
        "ProductionStateCommitter",
        "continuity engine",
        "Harness",
    ):
        assert owner in text
    for forbidden in (
        "MUST NOT select a Provider",
        "MUST NOT submit, poll, fetch, retry, or recover",
        "MUST NOT create an asset manifest",
        "MUST NOT activate or accept media",
    ):
        assert forbidden in text

def test_common_knowledge_uses_semantic_roles_and_observed_state() -> None:
    text = _read(SKILL_ROOT / "references" / "authoring-common.md")

    for concept in (
        "first_frame",
        "last_frame",
        "reference_image",
        "motion reference",
        "must_not_transfer",
        "accepted observed state",
        "direct operation wording",
    ):
        assert concept in text


def test_version_overlays_are_authoring_only_and_defer_runtime_facts() -> None:
    for version in ("2.0", "2.5"):
        text = _read(SKILL_ROOT / "references" / f"seedance-{version}.md")
        assert "authoring-only" in text
        assert "current AI-VIDEO capability/profile" in text
        assert "doubao-" not in text
        assert "Provider payload" not in text


def test_canonical_routing_selects_seedance_without_expanding_higgsfield() -> None:
    agents = _read(ROOT / "AGENTS.md")
    playbook = _read(ROOT / ".agent" / "context" / "control-plane-playbook.md")

    assert "Approved Shot + selected Seedance target | `seedance-authoring`" in agents
    assert "Non-Seedance model / Provider prompt adaptation | `higgsfield`" in agents
    assert "`seedance-authoring` MUST use" in playbook
    assert "Non-Seedance" in playbook
    assert "-> seedance-authoring:" in playbook
    assert "MUST NOT direct-dispatch" in playbook
    for retired in (
        "higgsfield-seedance",
        "higgsfield-seedance-2-5",
        "higgsfield-seedance-vfx",
        "higgsfield-troubleshoot",
    ):
        assert retired in playbook


def test_selected_profile_preserves_exact_runtime_identity() -> None:
    text = _read(SKILL_PATH)

    assert "exact selected Seedance model/profile identity" in text
    assert (
        "exact model/profile identity + version family + mode + runtime surface"
        in text
    )


def test_all_raw_creative_input_routes_to_director_before_seedance() -> None:
    seedance = _read(SKILL_PATH)
    open_video = _read(OPEN_VIDEO_SKILL_PATH)
    playbook = _read(ROOT / ".agent" / "context" / "control-plane-playbook.md")

    assert "DIRECTOR_PREFLIGHT_REQUEST" in seedance
    assert "prompt presence 不等于" in seedance
    assert "模糊方向" in seedance
    assert "完整 draft prompt" in seedance
    assert "coverage_strategy=single_take|multi_shot" in seedance
    assert "不得按时长阈值选择" in seedance
    assert "MUST NOT" in seedance
    assert "one uninterrupted shot" in seedance
    assert "creative_input_kind" in open_video
    assert "missing" in open_video
    assert "direction" in open_video
    assert "draft_prompt" in open_video
    assert "A user prompt is raw input, not approval" in open_video
    assert "feasibility input, not a creative branch" in open_video
    assert "validate_director_coverage.py" in open_video
    assert "strategy_source=agent_directed" in open_video
    assert "Raw Creative Input Director Strategy Gate" in playbook
    assert "prompt presence" in playbook
    assert "VIDEO_EXTEND" in playbook
    assert "时长阈值" in playbook
