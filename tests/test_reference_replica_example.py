"""Content regression of the standalone example's normal offline CLI."""

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from scripts.replica._local import agentcut_project


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/reference-replica/giftcard-jp"
# SHA-256 of each upstream layers.json built by the pinned 80abf28 CLI.
UPSTREAM_LAYERS = {
    "giftcard-jp-replica": "49d4e08528d7f6af3e217cfc366c95814b654cb78c2cfb5d5dc73761e20c95ab",
    "giftcard-jp-part1": "5417f39ba1321e7f5bcf6ca34525ab12b88735e6ccb8c8e4ceca810e7a42cdd4",
    "giftcard-jp-part2": "555f7aea6b998fc0c31badae638e0e91d9503f309cf1aad81515c487f9cf91cd",
}


def test_giftcard_full_and_parts_match_the_pinned_layers(tmp_path):
    projects = tmp_path / "projects"
    main = projects / "giftcard-jp-replica"
    (main / "assets").mkdir(parents=True)
    (main / "project.json").write_bytes(b"{}")
    command = [sys.executable, str(EXAMPLE / "build_layers.py"), "parts", "--projects-root", str(projects)]

    for _ in range(2):
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True, timeout=30)
        measured = {
            slug: hashlib.sha256((projects / slug / "layers.json").read_bytes()).hexdigest()
            for slug in UPSTREAM_LAYERS
        }
        assert measured == UPSTREAM_LAYERS


def test_agentcut_project_path_cannot_be_inside_production(tmp_path):
    production = tmp_path / "production"
    editor = production / "agentcut"
    editor.mkdir(parents=True)
    (production / "project.yaml").write_text("{}", encoding="utf-8")
    (editor / "project.json").write_text("{}", encoding="utf-8")

    with pytest.raises(AiVideoError) as failure:
        agentcut_project(editor)
    assert failure.value.code is ErrorCode.CONFIG_INVALID
