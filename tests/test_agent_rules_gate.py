from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts import agent_rules_gate as gate
from scripts.agent_harness_policy import inspect_paths, load_policy


ROOT = Path(__file__).resolve().parents[1]


def fixture_root(tmp_path: Path) -> Path:
    (tmp_path / ".agent/harness").mkdir(parents=True)
    (tmp_path / ".agent/context").mkdir()
    (tmp_path / "AGENTS.md").write_text(
        "# Guide\n\n[Detail](.agent/context/detail.md#safety)\n"
    )
    (tmp_path / ".agent/context/detail.md").write_text(
        "# Detail\n\n## Safety\n\nSafe.\n"
    )
    registry = {
        "version": 1,
        "documents": [
            {"path": "AGENTS.md", "max_lines": 10, "max_bytes": 200},
            {"path": ".agent/context/detail.md", "max_lines": 10, "max_bytes": 200},
        ],
        "context_max_bytes": 200,
        "rules": [
            {
                "id": "strict-reader",
                "checks": ["reader_tests"],
                "proof": "offline_regression",
                "remaining": "Current live bytes require separate validation.",
            }
        ],
    }
    (tmp_path / gate.REGISTRY).write_text(yaml.safe_dump(registry))
    policy = {
        "checks": {
            "reader_tests": {"argv": ["python", "-m", "pytest", "tests/test_reader.py"]}
        },
        "always_check_ids": ["reader_tests"],
        "categories": {},
    }
    (tmp_path / gate.POLICY).write_text(yaml.safe_dump(policy))
    return tmp_path


def mutate(root: Path, update) -> None:
    path = root / gate.REGISTRY
    data = yaml.safe_load(path.read_text())
    update(data)
    path.write_text(yaml.safe_dump(data))


def test_valid_snapshot_is_read_only(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    before = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    assert gate.check_repository(root) == []
    assert before == {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "update",
    [
        lambda d: d.update(version=2),
        lambda d: d.update(rules=[]),
        lambda d: d.update(documents=[]),
        lambda d: d["rules"][0].update(checks=[]),
        lambda d: d["rules"][0].update(checks=["missing"]),
        lambda d: d["rules"][0].update(proof="production_accepted"),
        lambda d: d["rules"][0].update(remaining=""),
        lambda d: d["rules"].append(copy.deepcopy(d["rules"][0])),
        lambda d: d["documents"][0].update(path="../outside.md"),
        lambda d: d["documents"][0].update(path=".env"),
        lambda d: d["documents"][0].update(max_lines=True),
    ],
)
def test_invalid_registry_fails_closed(tmp_path: Path, update) -> None:
    root = fixture_root(tmp_path)
    mutate(root, update)
    assert gate.check_repository(root)


def test_declared_check_must_actually_be_routed(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    path = root / gate.POLICY
    policy = yaml.safe_load(path.read_text())
    policy["always_check_ids"] = []
    path.write_text(yaml.safe_dump(policy))
    assert any("unrouted" in e for e in gate.check_repository(root))


@pytest.mark.parametrize("text", ["# Guide\n" * 12, "# Guide\n" + "中" * 100])
def test_document_growth_cannot_hide_in_long_lines(tmp_path: Path, text: str) -> None:
    root = fixture_root(tmp_path)
    (root / "AGENTS.md").write_text(text)
    assert any("budget" in e for e in gate.check_repository(root))


def test_new_context_requires_explicit_registration(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    (root / ".agent/context/new.md").write_text("# New\n")
    assert any("unregistered context" in e for e in gate.check_repository(root))


@pytest.mark.parametrize(
    "target",
    [
        "missing.md",
        ".agent/context/detail.md#missing",
        "../outside.md",
        'missing.md "Safety rules"',
        '../outside.md "Safety rules"',
    ],
)
def test_broken_or_escaping_document_link_is_rejected(
    tmp_path: Path, target: str
) -> None:
    root = fixture_root(tmp_path)
    (root / "AGENTS.md").write_text(f"# Guide\n[link]({target})\n")
    assert gate.check_repository(root)


def test_document_symlink_is_rejected(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    (root / "AGENTS.md").unlink()
    (root / "AGENTS.md").symlink_to(root / ".agent/context/detail.md")
    assert any("symlink" in e for e in gate.check_repository(root))


@pytest.mark.parametrize(
    "reference",
    [
        "[safety][rules]\n\n[rules]: missing.md",
        '[safety][rules]\n\n[rules]: ../outside.md "Safety"',
        "[rules][]\n\n[rules]: missing.md",
        "[safety][missing]",
    ],
)
def test_broken_reference_links_fail_closed(tmp_path: Path, reference: str) -> None:
    root = fixture_root(tmp_path)
    (root / "AGENTS.md").write_text("# Guide\n" + reference + "\n")
    assert gate.check_repository(root)


def test_valid_titled_and_reference_links(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    (root / "AGENTS.md").write_text(
        '# Guide\n[Detail](.agent/context/detail.md#safety "Safety")\n'
        '[Safety][rules]\n\n[rules]: .agent/context/detail.md#safety "Safety"\n'
    )
    assert gate.check_repository(root) == []


def test_total_context_budget_and_non_markdown_anchor(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    mutate(root, lambda d: d.update(context_max_bytes=1))
    assert any("context total" in e for e in gate.check_repository(root))
    (root / "helper.py").write_text("raise RuntimeError('must not execute')\n")
    (root / "AGENTS.md").write_text("# Guide\n[helper](helper.py#entry)\n")
    assert any("Markdown target" in e for e in gate.check_repository(root))


def test_repository_rules_and_policy_routes() -> None:
    assert gate.check_repository(ROOT) == []
    policy = load_policy(ROOT / gate.POLICY)
    for path in [
        "AGENTS.md",
        ".agent/context/control-plane-playbook.md",
        ".agent/context/t8-latentsync-local-runtime.md",
        str(gate.REGISTRY),
        "scripts/agent_rules_gate.py",
        "tests/test_agent_rules_gate.py",
    ]:
        inspection = inspect_paths([path], policy)
        assert not inspection["fallback_paths"]
        assert {"agent_rules_check", "agent_rule_invariants"} <= set(
            inspection["check_ids"]
        )
