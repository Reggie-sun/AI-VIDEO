from pathlib import Path

from production_e2e_support import BaseAiComicCallCounts
from production_project_factory import make_base_ai_comic_e2e_runtime


def test_base_ai_comic_support_is_deterministic_and_has_no_direct_state_writer(
    tmp_path: Path,
) -> None:
    first = make_base_ai_comic_e2e_runtime(tmp_path / "first")
    second = make_base_ai_comic_e2e_runtime(tmp_path / "second")

    assert first.synthetic_inputs_hash == second.synthetic_inputs_hash
    assert first.call_counts == BaseAiComicCallCounts()
    assert not hasattr(first, "write_manifest")
    assert not hasattr(first, "activate_registry")
