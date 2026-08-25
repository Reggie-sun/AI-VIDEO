from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.architecture_gate.gate import (
    check_architecture,
    render_text,
    update_baseline,
)


def _write_config(
    root: Path,
    *,
    fan_out_warning: int = 14,
    exception: tuple[str, str] | None = None,
) -> None:
    exception_text = ""
    if exception is not None:
        pattern, reason = exception
        exception_text = (
            "\n[[exceptions]]\n"
            f'pattern = "{pattern}"\n'
            f'reason = "{reason}"\n'
        )
    (root / "architecture_gate.toml").write_text(
        "schema_version = 1\n"
        'source_roots = ["src"]\n'
        'baseline = ".architecture/architecture-baseline.json"\n'
        "normal_loc = 800\n"
        "blocking_loc = 1500\n"
        "severe_loc = 3000\n"
        f"fan_out_warning = {fan_out_warning}\n"
        "exclude = [\n"
        '  "**/generated/**",\n'
        '  "**/vendor/**",\n'
        '  "**/vendored/**",\n'
        '  "**/migrations/**",\n'
        '  "**/snapshots/**",\n'
        '  "**/*_pb2.py",\n'
        "]\n"
        + exception_text,
        encoding="utf-8",
    )


def _write_v2_config(root: Path, contract: str = "") -> None:
    (root / "architecture_gate.toml").write_text(
        "schema_version = 2\n"
        'source_roots = ["src"]\n'
        'baseline = ".architecture/architecture-baseline.json"\n'
        "normal_loc = 800\n"
        "blocking_loc = 1500\n"
        "severe_loc = 3000\n"
        "fan_out_warning = 14\n"
        "exclude = []\n"
        + contract,
        encoding="utf-8",
    )


def _single_dependency_rule(
    *,
    source_pattern: str = "src/app/*.py",
    forbidden_target: str = "scripts",
    target_match: str = "prefix",
    exception: str = "",
) -> str:
    return (
        "\n[[module_sets]]\n"
        'name = "application"\n'
        f'patterns = ["{source_pattern}"]\n'
        "\n[[dependency_rules]]\n"
        'id = "ARCH101"\n'
        'source_module_set = "application"\n'
        f'forbidden_targets = ["{forbidden_target}"]\n'
        f'target_match = "{target_match}"\n'
        'contract_ref = "docs/agent-primary-contract-matrix.md#development-governance-isolation"\n'
        'severity = "error"\n'
        + exception
    )


def _write_module(root: Path, relative_path: str, lines: list[str]) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _sized_module(root: Path, relative_path: str, effective_loc: int) -> Path:
    return _write_module(
        root,
        relative_path,
        [f"value_{index} = {index}" for index in range(effective_loc)],
    )


def _codes(result) -> list[str]:
    return [finding.code for finding in result.findings]


@pytest.fixture
def architecture_repo(tmp_path: Path) -> Path:
    _write_config(tmp_path)
    return tmp_path


def test_existing_oversized_file_is_grandfathered_when_unchanged(
    architecture_repo: Path,
):
    _sized_module(architecture_repo, "src/app/legacy.py", 1601)
    update_baseline(architecture_repo)

    result = check_architecture(architecture_repo)

    assert not result.has_errors
    assert "ARCH001" not in _codes(result)


def test_schema_v2_without_dependency_rules_preserves_metrics_behavior(tmp_path: Path):
    _write_v2_config(
        tmp_path,
        "\n[[module_sets]]\n"
        'name = "application"\n'
        'patterns = ["src/app/**/*.py"]\n',
    )
    _sized_module(tmp_path, "src/app/legacy.py", 1601)

    update_baseline(tmp_path)
    with (tmp_path / "src/app/legacy.py").open("a", encoding="utf-8") as handle:
        handle.write("new_responsibility = 1\n")

    result = check_architecture(tmp_path)

    assert result.has_errors
    assert "ARCH001" in _codes(result)


def test_schema_v1_preserves_metrics_only_syntax_behavior(tmp_path: Path):
    _write_config(tmp_path)
    _write_module(tmp_path, "src/app/broken.py", ["def broken(:"])
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    assert not result.has_errors
    assert "ARCH100" not in _codes(result)


@pytest.mark.parametrize(
    ("contract", "expected_detail"),
    [
        (
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "missing"\n'
            'forbidden_targets = ["scripts"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n',
            "unknown module set",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = ["scripts"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "warn"\n',
            "severity",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = ["scripts"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = ["ai_video.production"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#legacy"\n'
            'severity = "error"\n',
            "duplicate dependency rule id",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = [""]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n',
            "forbidden target",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = "scripts"\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n',
            "forbidden targets must be a list",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH001"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = ["scripts"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n',
            "ARCH101 or higher",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = ["scripts"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n'
            "\n[[dependency_exceptions]]\n"
            'rule_id = "ARCH101"\n'
            'source_path = "src/app/consumer.py"\n'
            'target_module = "scripts.tool"\n'
            'owner_ref = "matrix#governance"\n'
            'reason = "temporary"\n'
            'review_by = "not-a-date"\n',
            "review_by",
        ),
        (
            "\n[[module_sets]]\n"
            'name = "application"\n'
            'patterns = ["src/app/**/*.py"]\n'
            "\n[[dependency_rules]]\n"
            'id = "ARCH101"\n'
            'source_module_set = "application"\n'
            'forbidden_targets = ["scripts"]\n'
            'target_match = "prefix"\n'
            'contract_ref = "matrix#governance"\n'
            'severity = "error"\n'
            "\n[[dependency_exceptions]]\n"
            'rule_id = "ARCH101"\n'
            'source_path = "src/app/*.py"\n'
            'target_module = "scripts.tool"\n'
            'owner_ref = "matrix#governance"\n'
            'reason = "temporary"\n'
            'review_by = "2099-01-01"\n',
            "exact source path",
        ),
    ],
)
def test_schema_v2_rejects_invalid_dependency_contract(
    tmp_path: Path,
    contract: str,
    expected_detail: str,
):
    _write_v2_config(tmp_path, contract)

    result = check_architecture(tmp_path)

    assert result.has_errors
    assert result.findings[0].code == "ARCH004"
    assert expected_detail in result.findings[0].reason


def test_schema_v2_rejects_non_table_module_set_entry(tmp_path: Path):
    _write_v2_config(tmp_path, '\nmodule_sets = ["application"]\n')

    result = check_architecture(tmp_path)

    assert result.has_errors
    assert result.findings[0].code == "ARCH004"
    assert "module sets must contain tables" in result.findings[0].reason


def test_schema_v2_rejects_unknown_top_level_contract_tables(tmp_path: Path):
    _write_v2_config(tmp_path, _single_dependency_rule())
    _write_module(tmp_path, "src/app/consumer.py", ["import scripts.tool"])
    update_baseline(tmp_path)
    config_path = tmp_path / "architecture_gate.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        .replace("[[module_sets]]", "[[module_set]]")
        .replace("[[dependency_rules]]", "[[dependency_rule]]"),
        encoding="utf-8",
    )

    result = check_architecture(tmp_path)

    assert result.has_errors
    assert result.findings[0].code == "ARCH004"
    assert "unknown top-level field" in result.findings[0].reason


@pytest.mark.parametrize("invalid_version", ["2.0", "true"])
def test_schema_version_requires_an_exact_integer(
    tmp_path: Path,
    invalid_version: str,
):
    _write_v2_config(tmp_path, _single_dependency_rule())
    config_path = tmp_path / "architecture_gate.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "schema_version = 2", f"schema_version = {invalid_version}"
        ),
        encoding="utf-8",
    )

    result = check_architecture(tmp_path)

    assert result.has_errors
    assert result.findings[0].code == "ARCH004"
    assert "schema_version must be an integer" in result.findings[0].reason


def test_existing_oversized_file_can_shrink_without_a_finding(
    architecture_repo: Path,
):
    path = _sized_module(architecture_repo, "src/app/legacy.py", 1601)
    update_baseline(architecture_repo)
    path.write_text("value = 1\n", encoding="utf-8")

    result = check_architecture(architecture_repo)

    assert not result.has_errors
    assert "ARCH001" not in _codes(result)


def test_existing_oversized_file_growth_is_blocking(
    architecture_repo: Path,
):
    path = _sized_module(architecture_repo, "src/app/legacy.py", 1601)
    update_baseline(architecture_repo)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("new_responsibility = 1\n")

    result = check_architecture(architecture_repo)

    finding = next(item for item in result.findings if item.code == "ARCH001")
    assert result.has_errors
    assert finding.slug == "oversized-module-growth"
    assert finding.severity.value == "ERROR"
    assert finding.path == "src/app/legacy.py"
    assert finding.measurements == {
        "base_loc": 1601,
        "current_loc": 1602,
        "delta": 1,
    }


@pytest.mark.parametrize(
    ("effective_loc", "expected_code", "expected_severity"),
    [
        (800, None, None),
        (801, "ARCH002", "WARN"),
        (1501, "ARCH002", "ERROR"),
    ],
)
def test_new_file_size_policy(
    architecture_repo: Path,
    effective_loc: int,
    expected_code: str | None,
    expected_severity: str | None,
):
    update_baseline(architecture_repo)
    _sized_module(architecture_repo, "src/app/new_module.py", effective_loc)

    result = check_architecture(architecture_repo)
    finding = next(
        (item for item in result.findings if item.code == expected_code),
        None,
    )

    if expected_code is None:
        assert not result.findings
    else:
        assert finding is not None
        assert finding.severity.value == expected_severity
    assert result.has_errors is (expected_severity == "ERROR")


def test_new_severely_oversized_file_is_blocking_and_named_as_severe(
    architecture_repo: Path,
):
    update_baseline(architecture_repo)
    _sized_module(architecture_repo, "src/app/new_severe.py", 3001)

    result = check_architecture(architecture_repo)

    finding = next(item for item in result.findings if item.code == "ARCH002")
    assert finding.severity.value == "ERROR"
    assert "severe architecture debt" in finding.reason


def test_generated_and_test_files_are_not_normal_production_modules(
    architecture_repo: Path,
):
    update_baseline(architecture_repo)
    _write_module(
        architecture_repo,
        "src/app/generated/client.py",
        ["# Generated by protocol compiler"]
        + [f"value_{index} = {index}" for index in range(1601)],
    )
    _sized_module(architecture_repo, "tests/test_large_fixture.py", 1601)

    result = check_architecture(architecture_repo)

    assert not result.findings


def test_generated_header_is_ignored_outside_generated_directory(
    architecture_repo: Path,
):
    update_baseline(architecture_repo)
    _write_module(
        architecture_repo,
        "src/app/protocol_bindings.py",
        ["# @generated; DO NOT EDIT"]
        + [f"value_{index} = {index}" for index in range(1601)],
    )

    assert not check_architecture(architecture_repo).findings


def test_explicit_exception_is_versioned_and_deterministic(tmp_path: Path):
    _write_config(
        tmp_path,
        exception=("src/app/declarative.py", "reviewed declarative mapping"),
    )
    _sized_module(tmp_path, "src/app/declarative.py", 1601)

    first = update_baseline(tmp_path).read_bytes()
    second = update_baseline(tmp_path).read_bytes()
    baseline = json.loads(second)

    assert first == second
    assert "src/app/declarative.py" in baseline["files"]
    assert not check_architecture(tmp_path).findings


def test_existing_dependency_cycle_is_grandfathered(architecture_repo: Path):
    _write_module(architecture_repo, "src/app/a.py", ["import app.b"])
    _write_module(architecture_repo, "src/app/b.py", ["import app.a"])
    update_baseline(architecture_repo)

    result = check_architecture(architecture_repo)

    assert "ARCH003" not in _codes(result)
    assert not result.has_errors


def test_existing_dependency_cycle_can_shrink_without_a_false_regression(
    architecture_repo: Path,
):
    _write_module(architecture_repo, "src/app/a.py", ["import app.b"])
    _write_module(
        architecture_repo,
        "src/app/b.py",
        ["import app.a", "import app.c"],
    )
    c_path = _write_module(architecture_repo, "src/app/c.py", ["import app.a"])
    update_baseline(architecture_repo)
    c_path.write_text("VALUE = 1\n", encoding="utf-8")

    result = check_architecture(architecture_repo)

    assert "ARCH003" not in _codes(result)
    assert not result.has_errors


def test_new_dependency_cycle_is_blocking(architecture_repo: Path):
    _write_module(architecture_repo, "src/app/a.py", ["import app.b"])
    b_path = _write_module(architecture_repo, "src/app/b.py", ["VALUE = 1"])
    update_baseline(architecture_repo)
    b_path.write_text("import app.a\n", encoding="utf-8")

    result = check_architecture(architecture_repo)

    finding = next(item for item in result.findings if item.code == "ARCH003")
    assert result.has_errors
    assert finding.slug == "dependency-cycle-regression"
    assert finding.path == "src/app/a.py"
    assert finding.measurements["modules"] == ["app.a", "app.b"]


def test_size_exception_cannot_hide_a_new_dependency_cycle(tmp_path: Path):
    _write_config(
        tmp_path,
        exception=("src/app/declarative.py", "reviewed declarative mapping"),
    )
    _write_module(
        tmp_path,
        "src/app/declarative.py",
        ["import app.consumer"]
        + [f"value_{index} = {index}" for index in range(1601)],
    )
    consumer = _write_module(tmp_path, "src/app/consumer.py", ["VALUE = 1"])
    update_baseline(tmp_path)
    consumer.write_text("import app.declarative\n", encoding="utf-8")

    result = check_architecture(tmp_path)

    assert "ARCH002" not in _codes(result)
    assert "ARCH003" in _codes(result)
    assert result.has_errors


def test_normal_new_dependency_does_not_fail(architecture_repo: Path):
    _write_module(architecture_repo, "src/app/a.py", ["VALUE = 1"])
    _write_module(architecture_repo, "src/app/b.py", ["VALUE = 2"])
    update_baseline(architecture_repo)
    (architecture_repo / "src/app/a.py").write_text(
        "import app.b\nVALUE = 1\n",
        encoding="utf-8",
    )

    result = check_architecture(architecture_repo)

    assert "ARCH003" not in _codes(result)
    assert not result.has_errors


def test_nested_and_type_checking_imports_do_not_create_false_cycles(
    architecture_repo: Path,
):
    _write_module(
        architecture_repo,
        "src/app/a.py",
        [
            "from typing import TYPE_CHECKING",
            "if TYPE_CHECKING:",
            "    import app.b",
            "def load_b():",
            "    import app.b",
        ],
    )
    _write_module(architecture_repo, "src/app/b.py", ["import app.a"])
    update_baseline(architecture_repo)

    result = check_architecture(architecture_repo)

    assert "ARCH003" not in _codes(result)
    assert not result.has_errors


def test_dependency_rule_checks_nested_runtime_but_not_type_checking_imports(
    tmp_path: Path,
):
    _write_v2_config(tmp_path, _single_dependency_rule())
    _write_module(
        tmp_path,
        "src/app/consumer.py",
        [
            "from typing import TYPE_CHECKING",
            "if TYPE_CHECKING:",
            "    import scripts.type_only",
            "def load_tool():",
            "    import scripts.runtime_tool",
            "if True:",
            "    import scripts.control_flow_tool",
            "import other.scripts.tool",
        ],
    )
    _write_module(tmp_path, "src/other/scripts/tool.py", ["VALUE = 1"])
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    findings = [item for item in result.findings if item.code == "ARCH101"]
    assert result.has_errors
    assert [item.path for item in findings] == [
        "src/app/consumer.py",
        "src/app/consumer.py",
    ]
    assert [item.measurements["line"] for item in findings] == [5, 7]
    assert [item.measurements["target_module"] for item in findings] == [
        "scripts.runtime_tool",
        "scripts.control_flow_tool",
    ]


def test_dependency_rule_normalizes_relative_imports(tmp_path: Path):
    _write_v2_config(
        tmp_path,
        _single_dependency_rule(
            source_pattern="src/app/private/*.py",
            forbidden_target="app.forbidden",
            target_match="exact",
        ),
    )
    _write_module(tmp_path, "src/app/forbidden.py", ["VALUE = 1"])
    _write_module(
        tmp_path,
        "src/app/private/consumer.py",
        ["from .. import forbidden"],
    )
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == "ARCH101")
    assert finding.measurements["target_module"] == "app.forbidden"
    assert finding.measurements["line"] == 1


def test_dependency_parser_syntax_error_fails_closed(tmp_path: Path):
    _write_v2_config(tmp_path, _single_dependency_rule())
    _write_module(tmp_path, "src/app/broken.py", ["def broken(:"])
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == "ARCH100")
    assert result.has_errors
    assert finding.slug == "dependency-source-syntax-error"
    assert finding.path == "src/app/broken.py"
    assert finding.measurements["line"] == 1


def test_dependency_rule_is_not_grandfathered_or_written_to_baseline(tmp_path: Path):
    _write_v2_config(tmp_path, _single_dependency_rule())
    _write_module(tmp_path, "src/app/consumer.py", ["import scripts.tool"])

    baseline_path = update_baseline(tmp_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    result = check_architecture(tmp_path)

    assert result.has_errors
    assert "ARCH101" in _codes(result)
    assert "dependency_rules" not in baseline
    assert "dependency_exceptions" not in baseline


def test_exact_dependency_exception_waives_only_the_matching_edge(tmp_path: Path):
    exception = (
        "\n[[dependency_exceptions]]\n"
        'rule_id = "ARCH101"\n'
        'source_path = "src/app/consumer.py"\n'
        'target_module = "scripts.allowed"\n'
        'owner_ref = "docs/agent-primary-contract-matrix.md#development-governance-isolation"\n'
        'reason = "bounded migration"\n'
        'review_by = "2099-01-01"\n'
    )
    _write_v2_config(tmp_path, _single_dependency_rule(exception=exception))
    _write_module(
        tmp_path,
        "src/app/consumer.py",
        ["import scripts.allowed", "import scripts.blocked"],
    )
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    findings = [item for item in result.findings if item.code == "ARCH101"]
    assert [item.measurements["target_module"] for item in findings] == [
        "scripts.blocked"
    ]


def test_exact_dependency_exception_distinguishes_from_import_targets(tmp_path: Path):
    exception = (
        "\n[[dependency_exceptions]]\n"
        'rule_id = "ARCH101"\n'
        'source_path = "src/app/consumer.py"\n'
        'target_module = "scripts.allowed"\n'
        'owner_ref = "docs/agent-primary-contract-matrix.md#development-governance-isolation"\n'
        'reason = "bounded migration"\n'
        'review_by = "2099-01-01"\n'
    )
    _write_v2_config(tmp_path, _single_dependency_rule(exception=exception))
    _write_module(
        tmp_path,
        "src/app/consumer.py",
        ["from scripts import allowed, blocked"],
    )
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    findings = [item for item in result.findings if item.code == "ARCH101"]
    assert [item.measurements["target_module"] for item in findings] == [
        "scripts.blocked"
    ]
    assert not any(
        item.slug == "stale-dependency-exception" for item in result.findings
    )


def test_external_exact_rule_blocks_from_import_base_module(tmp_path: Path):
    _write_v2_config(
        tmp_path,
        _single_dependency_rule(
            forbidden_target="scripts.tool",
            target_match="exact",
        ),
    )
    _write_module(
        tmp_path,
        "src/app/consumer.py",
        ["from scripts.tool import value"],
    )
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == "ARCH101")
    assert finding.measurements["target_module"] == "scripts.tool"


def test_dependency_rule_fails_when_source_module_set_matches_no_files(
    tmp_path: Path,
):
    _write_v2_config(
        tmp_path,
        _single_dependency_rule(source_pattern="src/appp/*.py"),
    )
    _write_module(tmp_path, "src/app/consumer.py", ["import scripts.tool"])
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    finding = next(
        item
        for item in result.findings
        if item.slug == "empty-dependency-module-set"
    )
    assert result.has_errors
    assert finding.code == "ARCH100"
    assert finding.measurements["module_set"] == "application"


def test_stale_dependency_exception_fails_closed(tmp_path: Path):
    exception = (
        "\n[[dependency_exceptions]]\n"
        'rule_id = "ARCH101"\n'
        'source_path = "src/app/consumer.py"\n'
        'target_module = "scripts.removed"\n'
        'owner_ref = "docs/agent-primary-contract-matrix.md#development-governance-isolation"\n'
        'reason = "bounded migration"\n'
        'review_by = "2099-01-01"\n'
    )
    _write_v2_config(tmp_path, _single_dependency_rule(exception=exception))
    _write_module(tmp_path, "src/app/consumer.py", ["VALUE = 1"])
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == "ARCH100")
    assert result.has_errors
    assert finding.slug == "stale-dependency-exception"


def test_expired_dependency_exception_is_invalid_configuration(tmp_path: Path):
    exception = (
        "\n[[dependency_exceptions]]\n"
        'rule_id = "ARCH101"\n'
        'source_path = "src/app/consumer.py"\n'
        'target_module = "scripts.tool"\n'
        'owner_ref = "docs/agent-primary-contract-matrix.md#development-governance-isolation"\n'
        'reason = "bounded migration"\n'
        'review_by = "2000-01-01"\n'
    )
    _write_v2_config(tmp_path, _single_dependency_rule(exception=exception))
    _write_module(tmp_path, "src/app/consumer.py", ["import scripts.tool"])

    result = check_architecture(tmp_path)

    assert result.has_errors
    assert result.findings[0].code == "ARCH004"
    assert "expired" in result.findings[0].reason


@pytest.mark.parametrize(
    ("source_path", "import_statement", "expected_code"),
    [
        ("src/ai_video/product.py", "import scripts.tool", "ARCH101"),
        (
            "src/ai_video/cli.py",
            "import ai_video.production.project",
            "ARCH102",
        ),
        (
            "src/ai_video/production/service.py",
            "import ai_video.planning.video_planner",
            "ARCH103",
        ),
        (
            "src/ai_video/production/service.py",
            "import ai_video.quality_gates.shot_readiness_gate",
            "ARCH103",
        ),
        (
            "src/ai_video/production/service.py",
            "import ai_video.quality_intelligence.capture",
            "ARCH103",
        ),
        (
            "src/ai_video/production/_state_commit_example.py",
            "import ai_video.production.state_commit",
            "ARCH104",
        ),
    ],
)
def test_repository_dependency_rules_block_representative_imports(
    tmp_path: Path,
    source_path: str,
    import_statement: str,
    expected_code: str,
):
    repository_root = Path(__file__).resolve().parents[1]
    shutil.copyfile(
        repository_root / "architecture_gate.toml",
        tmp_path / "architecture_gate.toml",
    )
    _write_module(tmp_path, source_path, [import_statement])
    update_baseline(tmp_path)

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == expected_code)
    assert finding.path == source_path
    assert finding.measurements["line"] == 1


def test_new_high_fan_out_is_reviewer_information(tmp_path: Path):
    _write_config(tmp_path, fan_out_warning=2)
    for name in ("b", "c", "d"):
        _write_module(tmp_path, f"src/app/{name}.py", ["VALUE = 1"])
    update_baseline(tmp_path)
    _write_module(
        tmp_path,
        "src/app/a.py",
        ["import app.b", "import app.c", "import app.d"],
    )

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == "ARCH005")
    assert finding.severity.value == "INFO"
    assert finding.measurements["fan_out"] == 3
    assert not result.has_errors


def test_check_never_rewrites_baseline(architecture_repo: Path):
    _sized_module(architecture_repo, "src/app/legacy.py", 801)
    baseline_path = update_baseline(architecture_repo)
    before = baseline_path.read_bytes()
    (architecture_repo / "src/app/legacy.py").write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    check_architecture(architecture_repo)

    assert baseline_path.read_bytes() == before


def test_stale_baseline_entry_is_reported_and_explicit_update_prunes_it(
    architecture_repo: Path,
):
    path = _write_module(architecture_repo, "src/app/old.py", ["VALUE = 1"])
    baseline_path = update_baseline(architecture_repo)
    path.unlink()

    result = check_architecture(architecture_repo)
    finding = next(item for item in result.findings if item.code == "ARCH004")
    assert finding.severity.value == "INFO"
    assert not result.has_errors

    update_baseline(architecture_repo)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert "src/app/old.py" not in baseline["files"]


def test_missing_baseline_fails_closed_with_stable_finding(
    architecture_repo: Path,
):
    result = check_architecture(architecture_repo)

    assert result.has_errors
    finding = result.findings[0]
    assert finding.code == "ARCH004"
    assert finding.slug == "architecture-baseline-invalid"


def test_text_output_is_structured_and_actionable(architecture_repo: Path):
    path = _sized_module(architecture_repo, "src/app/legacy.py", 1601)
    update_baseline(architecture_repo)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("new_responsibility = 1\n")

    output = render_text(check_architecture(architecture_repo))

    assert "ARCH001 oversized-module-growth" in output
    assert "Path: src/app/legacy.py" in output
    assert "Severity: ERROR" in output
    assert "Base LOC: 1601" in output
    assert "Current LOC: 1602" in output
    assert "Delta: +1" in output
    assert "Reason:" in output
    assert "Recommended actions:" in output
    assert "transaction lifecycle" in output


def test_git_base_ref_takes_precedence_over_committed_baseline(
    architecture_repo: Path,
):
    path = _sized_module(architecture_repo, "src/app/legacy.py", 1601)
    update_baseline(architecture_repo)
    subprocess.run(["git", "init", "-q"], cwd=architecture_repo, check=True)
    subprocess.run(["git", "add", "architecture_gate.toml", ".architecture", "src"], cwd=architecture_repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Architecture Gate Test",
            "-c",
            "user.email=architecture-gate@example.invalid",
            "commit",
            "-qm",
            "baseline",
        ],
        cwd=architecture_repo,
        check=True,
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("new_responsibility = 1\n")
    update_baseline(architecture_repo)

    result = check_architecture(architecture_repo, base_ref="HEAD")

    assert result.has_errors
    assert "ARCH001" in _codes(result)


def test_invalid_git_base_ref_is_an_actionable_baseline_finding(
    architecture_repo: Path,
):
    update_baseline(architecture_repo)

    result = check_architecture(architecture_repo, base_ref="missing-ref")

    assert result.has_errors
    assert _codes(result) == ["ARCH004"]
    assert "missing-ref" in result.findings[0].reason


def test_current_repository_records_split_production_state_baseline():
    repository_root = Path(__file__).resolve().parents[1]

    result = check_architecture(repository_root)
    baseline = json.loads(
        (
            repository_root / ".architecture/architecture-baseline.json"
        ).read_text(encoding="utf-8")
    )

    assert not result.has_errors
    files = baseline["files"]
    assert files["src/ai_video/production/state_commit.py"]["effective_loc"] <= 800
    assert files["src/ai_video/production/_state_commit_recovery.py"][
        "effective_loc"
    ] <= 800
    assert files["src/ai_video/production/_state_commit_recovery_attempts.py"][
        "effective_loc"
    ] <= 800
    assert files["src/ai_video/production/_state_commit_recovery_fs.py"][
        "effective_loc"
    ] <= 800


def test_real_production_state_fixture_flags_regrowth_past_normal_limit(
    tmp_path: Path,
):
    repository_root = Path(__file__).resolve().parents[1]
    _write_config(tmp_path)
    target = tmp_path / "src/ai_video/production/state_commit.py"
    target.parent.mkdir(parents=True)
    shutil.copyfile(
        repository_root / "src/ai_video/production/state_commit.py",
        target,
    )
    update_baseline(tmp_path)
    baseline = json.loads(
        (tmp_path / ".architecture/architecture-baseline.json").read_text(
            encoding="utf-8"
        )
    )
    base_loc = baseline["files"][
        "src/ai_video/production/state_commit.py"
    ]["effective_loc"]
    growth = 801 - base_loc
    with target.open("a", encoding="utf-8") as handle:
        handle.writelines(
            f"ARCHITECTURE_GATE_ARTIFICIAL_GROWTH_{index} = True\n"
            for index in range(growth)
        )

    result = check_architecture(tmp_path)

    finding = next(item for item in result.findings if item.code == "ARCH001")
    assert finding.path == "src/ai_video/production/state_commit.py"
    assert finding.measurements == {
        "base_loc": base_loc,
        "current_loc": 801,
        "delta": growth,
    }
    assert finding.severity.value == "WARN"
