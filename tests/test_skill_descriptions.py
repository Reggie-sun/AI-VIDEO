"""Metadata contracts only: these tests do not measure actual Agent routing."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1] / '.agents' / 'skills'


def description(name):
    return yaml.safe_load((ROOT / name / 'SKILL.md').read_text().split('---', 2)[1])['description']


@pytest.mark.parametrize('name', ['h3-video', 'seedance-authoring', 'vidu-authoring'])
def test_provider_metadata_requires_selection_and_rejects_generic_mode_trigger(name):
    value = description(name)
    assert 'selected' in value
    assert 'Generic T2V' in value
    assert 'I2V' in value
    assert 'do not select this Provider' in value
    assert 'Not for' in value or 'not for' in value
    assert 'Triggers:' not in value


@pytest.mark.parametrize('suffix', ['expert', 'blockout', 'animation', 'rigging', 'previs-storyboard'])
def test_blender_metadata_declares_task_and_exclusion(suffix):
    value = description('scenario-blender-' + suffix)
    assert value.startswith('Use for ')
    assert 'Not for' in value
    assert 'Provider' in value


def test_director_and_memory_metadata_preserve_separate_responsibilities():
    assert 'not a replacement for the per-Shot post-media Gate' in description('open-video')
    assert 'Does not write session records or distill Learning Claims' in description('retrieve-ai-video-memory')
    assert 'Not for retrieval-only tasks or session recording alone' in description('distill-ai-video-learning')


def test_blender_protocol_remains_required_without_loading_all_domains():
    value = description("scenario-blender-expert")
    assert "before every Blender task" in value
    assert "only for the corresponding task" in value
