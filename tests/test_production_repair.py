from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.review import validate_repair_scope


def test_repair_scope_accepts_only_exact_affected_nodes():
    assert validate_repair_scope(
        expected_node_ids=("caption:a", "composition:a", "render:a"),
        actual_node_ids=("render:a", "caption:a", "composition:a"),
    ) == ("caption:a", "composition:a", "render:a")


def test_repair_scope_rejects_blanket_or_missing_invalidation():
    with pytest.raises(AiVideoError):
        validate_repair_scope(
            expected_node_ids=("caption:a", "render:a"),
            actual_node_ids=("caption:a", "render:a", "voice:unrelated"),
        )
    with pytest.raises(AiVideoError):
        validate_repair_scope(
            expected_node_ids=("caption:a", "render:a"),
            actual_node_ids=("render:a",),
        )
