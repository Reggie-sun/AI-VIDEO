from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts import docs_contract_gate


REPO_ROOT = Path(__file__).resolve().parents[1]


def _surface(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "surface_id": "example",
        "canonical_spec": "docs/superpowers/specs/example.md",
        "canonical": True,
        "spec_status": "accepted",
        "implementation_status": "implemented_offline",
        "live_status": "not_applicable",
        "quality_status": "not_evaluated",
        "release_status": "unreleased",
        "runtime_status_owner": "docs/v0.2-runtime-baseline.md",
        "roadmap_owner": "docs/v0.2-agentic-production-roadmap.md",
        "contract_version": "example/1",
        "implementation_paths": ["src/example.py"],
        "test_paths": ["tests/test_example.py"],
        "harness_check_ids": ["example_tests"],
        "assertions": [
            {
                "type": "python_literal_equals",
                "path": "src/example.py",
                "symbol": "Example.CONTRACT_VERSION",
                "expected": "example/1",
            }
        ],
    }
    value.update(overrides)
    return value


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _metadata(surface: dict[str, object]) -> dict[str, object]:
    fields = (
        *docs_contract_gate.METADATA_FIELDS,
        *docs_contract_gate.OPTIONAL_METADATA_FIELDS,
    )
    return {field: surface[field] for field in fields if field in surface}


def _write_spec(
    root: Path, surface: dict[str, object], *, path: str | None = None
) -> None:
    spec_path = root / (path or str(surface["canonical_spec"]))
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    front_matter = yaml.safe_dump(_metadata(surface), sort_keys=False).rstrip()
    spec_path.write_text(
        f"---\n{front_matter}\n---\n\n# Example\n", encoding="utf-8"
    )


def _repository(
    tmp_path: Path, surfaces: list[dict[str, object]] | None = None
) -> Path:
    values = surfaces or [_surface()]
    _write_yaml(
        tmp_path / ".agent/harness/docs-contracts.yaml",
        {"schema_version": 1, "surfaces": values},
    )
    _write_yaml(
        tmp_path / ".agent/harness/policy.yaml",
        {"checks": {"example_tests": {"argv": ["true"]}}},
    )
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs/v0.2-runtime-baseline.md").write_text(
        "baseline\n", encoding="utf-8"
    )
    (tmp_path / "docs/v0.2-agentic-production-roadmap.md").write_text(
        "roadmap\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src/example.py").write_text(
        'class Example:\n    CONTRACT_VERSION = "example/1"\n', encoding="utf-8"
    )
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests/test_example.py").write_text(
        "def test_example():\n    assert True\n", encoding="utf-8"
    )
    for surface in values:
        path = surface.get("canonical_spec")
        if (
            isinstance(path, str)
            and not Path(path).is_absolute()
            and ".." not in Path(path).parts
        ):
            _write_spec(tmp_path, surface)
    return tmp_path


def _check(root: Path) -> docs_contract_gate.CheckResult:
    return docs_contract_gate.check_repository(root)


def _fields(result: docs_contract_gate.CheckResult) -> set[str]:
    return {item.field for item in result.diagnostics}


def test_current_complete_registry_passes() -> None:
    result = docs_contract_gate.check_repository(REPO_ROOT)
    assert result.ok, "\n".join(item.render() for item in result.diagnostics)


def test_registry_schema_version_is_validated(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    registry_path = root / docs_contract_gate.REGISTRY_PATH
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["schema_version"] = 2
    _write_yaml(registry_path, registry)

    result = _check(root)

    assert any(item.field == "schema_version" for item in result.diagnostics)


def test_duplicate_surface_id_fails(tmp_path: Path) -> None:
    first = _surface()
    second = _surface(canonical_spec="docs/superpowers/specs/other.md")
    root = _repository(tmp_path, [first, second])
    _write_spec(root, second)
    result = _check(root)
    assert not result.ok
    assert "surface_id" in _fields(result)


def test_two_active_canonical_specs_for_surface_fail(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _write_spec(root, _surface(canonical_spec="docs/superpowers/specs/other.md"))
    result = _check(root)
    assert not result.ok
    assert any(
        item.field == "canonical_spec" and "at most one" in item.expected
        for item in result.diagnostics
    )


def test_active_canonical_spec_omitted_from_registry_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    orphan = _surface(
        surface_id="orphan",
        canonical_spec="docs/superpowers/specs/orphan.md",
    )
    _write_spec(root, orphan)

    result = _check(root)

    assert any(item.field == "surface_registry" for item in result.diagnostics)


def test_active_canonical_spec_must_match_registered_path(tmp_path: Path) -> None:
    registered = _surface(canonical=False)
    root = _repository(tmp_path, [registered])
    active = _surface(canonical_spec="docs/superpowers/specs/other.md")
    _write_spec(root, active)

    result = _check(root)

    assert any(
        item.field == "surface_registry"
        and item.expected == "docs/superpowers/specs/example.md"
        and item.source_path == "docs/superpowers/specs/other.md"
        for item in result.diagnostics
    )


def test_missing_canonical_spec_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "docs/superpowers/specs/example.md").unlink()
    assert "canonical_spec" in _fields(_check(root))


def test_spec_metadata_mismatch_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _write_spec(root, _surface(contract_version="example/2"))
    assert any(
        item.field == "contract_version" for item in _check(root).diagnostics
    )


def test_invalid_spec_front_matter_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "docs/superpowers/specs/example.md").write_text(
        "---\nsurface_id: [\n---\n", encoding="utf-8"
    )

    result = _check(root)

    assert any(item.field == "spec_metadata" for item in result.diagnostics)


@pytest.mark.parametrize(
    ("mutation", "field"),
    [
        (
            lambda root, registry: registry["surfaces"][0][
                "harness_check_ids"
            ].append("unknown"),
            "harness_check_ids",
        ),
        (lambda root, registry: (root / "src/example.py").unlink(), "implementation_paths[0]"),
        (lambda root, registry: (root / "tests/test_example.py").unlink(), "test_paths[0]"),
    ],
)
def test_registry_evidence_failures(
    tmp_path: Path, mutation, field: str
) -> None:
    root = _repository(tmp_path)
    registry_path = root / docs_contract_gate.REGISTRY_PATH
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    mutation(root, registry)
    _write_yaml(registry_path, registry)
    assert field in _fields(_check(root))


def test_python_symbol_exists_and_absent(tmp_path: Path) -> None:
    surface = _surface(
        assertions=[
            {
                "type": "python_symbol_exists",
                "path": "src/example.py",
                "symbol": "Example",
            },
            {
                "type": "python_symbol_absent",
                "path": "src/example.py",
                "symbol": "Forbidden",
            },
        ]
    )
    root = _repository(tmp_path, [surface])
    assert _check(root).ok
    (root / "src/example.py").write_text("Forbidden = 1\n", encoding="utf-8")
    result = _check(root)
    assert len(
        [item for item in result.diagnostics if item.field.startswith("assertions")]
    ) == 2


def test_python_literal_version_mismatch_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "src/example.py").write_text(
        'class Example:\n    CONTRACT_VERSION = "example/2"\n', encoding="utf-8"
    )
    result = _check(root)
    assert any(
        item.actual == "example/2" and item.expected == "example/1"
        for item in result.diagnostics
    )


def test_python_literal_reads_class_annotation(tmp_path: Path) -> None:
    surface = _surface(
        assertions=[
            {
                "type": "python_literal_equals",
                "path": "src/example.py",
                "symbol": "Example.SCHEMA_VERSION",
                "expected": "1.0",
            }
        ]
    )
    root = _repository(tmp_path, [surface])
    (root / "src/example.py").write_text(
        'from typing import Literal\n\nclass Example:\n    SCHEMA_VERSION: Literal["1.0"]\n',
        encoding="utf-8",
    )

    assert _check(root).ok


def test_python_literal_reads_multi_value_class_annotation(tmp_path: Path) -> None:
    surface = _surface(
        assertions=[
            {
                "type": "python_literal_equals",
                "path": "src/example.py",
                "symbol": "Example.SCHEMA_VERSION",
                "expected": ["1.0", "1.1"],
            }
        ]
    )
    root = _repository(tmp_path, [surface])
    (root / "src/example.py").write_text(
        'from typing import Literal\n\nclass Example:\n    SCHEMA_VERSION: Literal["1.0", "1.1"]\n',
        encoding="utf-8",
    )

    assert _check(root).ok


def test_quality_schema_annotation_change_without_metadata_fails(
    tmp_path: Path,
) -> None:
    surface = _surface(
        contract_version="quality-experience-record/1.0",
        assertions=[
            {
                "type": "python_literal_equals",
                "path": "src/example.py",
                "symbol": "QualityExperienceRecordV1.schema_version",
                "expected": "1.0",
            }
        ],
    )
    root = _repository(tmp_path, [surface])
    (root / "src/example.py").write_text(
        "from typing import Literal\n\n"
        "class OtherRecord:\n"
        '    schema_version: Literal["1.0"]\n\n'
        "class QualityExperienceRecordV1:\n"
        '    schema_version: Literal["2.0"]\n',
        encoding="utf-8",
    )

    result = _check(root)

    assert any(
        item.field == "assertions[0]"
        and item.expected == "1.0"
        and item.actual == "2.0"
        for item in result.diagnostics
    )


def test_superseded_spec_cannot_be_canonical(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_surface(spec_status="superseded")])
    result = _check(root)
    assert any(
        item.field == "canonical" and item.expected == "false"
        for item in result.diagnostics
    )


@pytest.mark.parametrize(
    "path", ["../outside.md", "/tmp/outside.md", "docs/../outside.md"]
)
def test_unsafe_paths_fail(tmp_path: Path, path: str) -> None:
    root = _repository(tmp_path, [_surface(canonical_spec=path)])
    result = _check(root)
    assert any(
        item.field == "canonical_spec" and "safe" in item.expected
        for item in result.diagnostics
    )


@pytest.mark.parametrize(
    ("field", "relative"),
    [
        ("canonical_spec", "docs/superpowers/specs/example.md"),
        ("implementation_paths[0]", "src/example.py"),
        ("test_paths[0]", "tests/test_example.py"),
    ],
)
def test_evidence_paths_reject_symlink_escape(
    tmp_path: Path, field: str, relative: str
) -> None:
    root = _repository(tmp_path)
    target = root / relative
    outside = tmp_path.parent / f"{tmp_path.name}-{target.name}"
    outside.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.unlink()
    target.symlink_to(outside)

    result = _check(root)

    assert any(
        item.field == field and "non-symlink" in item.expected
        for item in result.diagnostics
    )


def test_assertion_path_rejects_symlink_escape(tmp_path: Path) -> None:
    surface = _surface(
        implementation_paths=[],
        implementation_status="not_started",
        test_paths=[],
        assertions=[
            {
                "type": "text_contains",
                "path": "anchors/contract.txt",
                "text": "contract/1",
            }
        ],
    )
    root = _repository(tmp_path, [surface])
    outside = tmp_path.parent / f"{tmp_path.name}-contract.txt"
    outside.write_text("contract/1\n", encoding="utf-8")
    anchor = root / "anchors/contract.txt"
    anchor.parent.mkdir()
    anchor.symlink_to(outside)

    result = _check(root)

    assert any(
        item.field == "assertions[0].path" and "non-symlink" in item.expected
        for item in result.diagnostics
    )


def test_assertion_kinds(tmp_path: Path) -> None:
    surface = _surface(
        assertions=[
            {"type": "file_exists", "path": "src/example.py"},
            {"type": "file_absent", "path": "src/removed.py"},
            {
                "type": "text_contains",
                "path": "src/example.py",
                "text": "CONTRACT_VERSION",
            },
            {
                "type": "text_not_contains",
                "path": "src/example.py",
                "text": "legacy/0",
            },
            {
                "type": "regex_matches_exactly_once",
                "path": "src/example.py",
                "pattern": r"CONTRACT_VERSION\s*=",
            },
        ]
    )
    root = _repository(tmp_path, [surface])
    assert _check(root).ok


def test_diagnostics_have_stable_order(tmp_path: Path) -> None:
    surface = _surface(
        assertions=[
            {"type": "file_exists", "path": "z-missing"},
            {"type": "file_exists", "path": "a-missing"},
        ]
    )
    root = _repository(tmp_path, [surface])
    first = _check(root).diagnostics
    second = _check(root).diagnostics
    assert first == second == tuple(sorted(first))


def test_check_does_not_write_repository_files(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    before = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert _check(root).ok
    after = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_gate_source_has_no_runtime_network_or_write_calls() -> None:
    source = Path(docs_contract_gate.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not any(
        name == "ai_video" or name.startswith("ai_video.") for name in imports
    )
    assert not imports.intersection({"requests", "socket", "urllib", "httpx"})
    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "subprocess" not in imports


def test_planner_contract_change_without_spec_metadata_fails(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path)
    (root / "src/example.py").write_text(
        'class Example:\n    CONTRACT_VERSION = "example/2"\n', encoding="utf-8"
    )
    assert any(
        item.field == "assertions[0]" for item in _check(root).diagnostics
    )


def test_implemented_quality_surface_marked_not_started_fails(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path, [_surface(implementation_status="not_started")])
    assert {"implementation_paths", "test_paths"}.issubset(_fields(_check(root)))


def test_implemented_surface_requires_harness_owner(tmp_path: Path) -> None:
    root = _repository(tmp_path, [_surface(harness_check_ids=[])])

    result = _check(root)

    assert "harness_check_ids" in _fields(result)


def test_cli_exit_codes(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    command = [
        sys.executable,
        "-m",
        "scripts.docs_contract_gate",
        "check",
        "--root",
        str(root),
    ]
    passed = subprocess.run(
        command, cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert passed.returncode == 0
    (root / "src/example.py").unlink()
    failed = subprocess.run(
        command, cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert failed.returncode == 1
    assert "surface=example" in failed.stdout
