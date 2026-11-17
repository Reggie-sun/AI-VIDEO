"""Historical evidence contracts, not generated-media quality or a routing score."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/jimeng-seedance-history.json'
AUDIT = json.loads(FIXTURE.read_text())
CASES = AUDIT['cases']


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_case_reopens_exact_tracked_record(case):
    record = case['record']
    path = ROOT / record['path']
    assert path.resolve().is_relative_to((ROOT / 'docs/record_for_agent').resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
    # This verifies the cited historical record, not its media or natural-language claims.
    assert case['channel'] == 'jimeng'
    for field in ('goal', 'finding', 'timecode', 'repair', 'user_feedback',
                  'engineering', 'agent_observation', 'repair_acceptance', 'generalization'):
        assert case[field]


def test_archive_does_not_promote_fetch_or_repair_to_acceptance():
    cases = {c['id']: c for c in CASES}
    assert cases['jieshi-mini-realperson']['agent_observation'] == 'NOT_EVALUATED'
    assert cases['shizhen-s03-005-state-refs']['repair_acceptance'] == 'NOT_EVALUATED'
    assert cases['shizhen-s03-004-hover']['agent_observation'] == 'FAIL'
    assert AUDIT['live_media_review'] == 'NOT_EVALUATED'


def test_ark_fast_comparison_is_not_a_jimeng_sample():
    excluded = {row['record'] for row in AUDIT['excluded']}
    ark = 'docs/record_for_agent/2026-10-21-jieshi-seedance-20-fast-comparison.md'
    assert ark in excluded
    assert all(c['record']['path'] != ark for c in CASES)


def test_case_identities_are_unique_and_missing_media_is_not_fabricated():
    assert len({c['id'] for c in CASES}) == len(CASES)
    for case in CASES:
        media = case.get('media')
        if media and media.get('exists'):
            assert len(media['sha256']) == 64
            assert media['path']
        elif media:
            assert media.get('sha256') is None
    # No media file is required in CI; local bytes checks belong to the audit.


# Reuse actual existing control-plane tests; these are not surrogate image judges.
CASE_REGRESSIONS = {
    'yanshengyuan-two-shot-limited-acceptance': ('test_junction_review_gate.py', 'test_cut_review_without_exact_normal_speed_human_audio_evidence_stays_not_evaluated'),
    'shizhen-s03-cg-hover': ('test_reference_planning.py', 'test_motion_selection_requires_video_and_exact_duty_not_extra_stills'),
    'shizhen-s03-004-hover': ('test_jimeng_causal_compilation.py', 'test_whitebox_video_duty_reaches_native_prompt_and_exact_media_binding'),
    'shizhen-s03-005-state-refs': ('test_jimeng_causal_compilation.py', 'test_reference_duty_is_expressed_beside_its_exact_native_material'),
    'shizhen-duplicate-scan': ('test_junction_review_gate.py', 'test_cut_review_without_exact_normal_speed_human_audio_evidence_stays_not_evaluated'),
    'jieshi-mini-cg': ('test_jimeng_causal_compilation.py', 'test_causal_recompile_rejects_resealed_native_prompt_tampering'),
    'jieshi-mini-realperson': ('test_junction_review_gate.py', 'test_cut_review_without_exact_normal_speed_human_audio_evidence_stays_not_evaluated'),
    'yanshengyuan-junction': ('test_junction_review_gate.py', 'test_observed_audio_failure_is_preserved_even_without_pass_eligibility'),
}


@pytest.mark.parametrize('case_id,target', CASE_REGRESSIONS.items())
def test_historical_failure_maps_to_existing_executable_regression(case_id, target):
    import ast
    assert case_id in {c['id'] for c in CASES}
    filename, function = target
    module = ast.parse((ROOT / 'tests' / filename).read_text())
    assert function in {node.name for node in module.body if isinstance(node, ast.FunctionDef)}


def test_repair_media_is_not_mislabeled_as_original_failure():
    cases = {c['id']: c for c in CASES}
    for key in ('shizhen-duplicate-scan', 'yanshengyuan-junction'):
        case = cases[key]
        assert case['media_role'] == 'repaired_composition'
        original = case['original_failure_media']
        if original and original.get('sha256'):
            assert original['sha256'] != case['media']['sha256']
    composition = cases['shizhen-duplicate-scan']
    assert composition['is_composition'] is True
    assert composition['model'] == 'NOT_APPLICABLE_COMPOSITION'
    assert composition['source_models']


def test_bounded_clip_acceptance_does_not_accept_later_composition():
    cases = {c['id']: c for c in CASES}
    accepted = cases['yanshengyuan-two-shot-limited-acceptance']
    assert accepted['human_acceptance'] == 'ACCEPTED_BOUNDED_TWO_CLIPS_AND_S02_AUDIO'
    assert accepted['human_evidence']['sha256']
    assert cases['yanshengyuan-junction']['repair_acceptance'] == 'NOT_EVALUATED'
