from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT / "src" / "ai_video"
DEVELOPMENT_IMPORT_PREFIXES = (
    "scripts.composition_playbooks",
    "scripts.composition_shadow",
)
DEVELOPMENT_PATH_MARKERS = (
    ".agent/playbooks/composition",
    ".agent\\playbooks\\composition",
)


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            modules.update(
                f"{node.module}.{alias.name}"
                for alias in node.names
                if alias.name != "*"
            )
    return modules


def test_import_scanner_catches_from_package_import_form() -> None:
    tree = ast.parse("from scripts import composition_shadow")

    assert "scripts.composition_shadow" in _imported_modules(tree)


def test_product_runtime_does_not_depend_on_composition_playbook_tooling() -> None:
    violations: list[str] = []
    for path in sorted(PRODUCT_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports = _imported_modules(tree)
        if any(
            module == prefix or module.startswith(f"{prefix}.")
            for module in imports
            for prefix in DEVELOPMENT_IMPORT_PREFIXES
        ):
            violations.append(f"{path.relative_to(ROOT)} imports development tooling")
        if any(marker in source for marker in DEVELOPMENT_PATH_MARKERS):
            violations.append(f"{path.relative_to(ROOT)} reads composition playbooks")

    assert violations == []


def test_shadow_tooling_has_no_provider_or_lifecycle_dependency() -> None:
    forbidden_prefixes = (
        "ai_video.production.shot_router",
        "ai_video.production.state_commit",
        "ai_video.production.manifest",
        "ai_video.production.registry",
        "ai_video.production.dependency",
        "ai_video.production.video",
        "ai_video.quality_gates",
        "ai_video.quality_intelligence",
        "httpx",
        "requests",
        "socket",
        "subprocess",
    )
    violations: list[str] = []
    for relative in (
        "scripts/composition_playbooks.py",
        "scripts/composition_shadow.py",
    ):
        path = ROOT / relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _imported_modules(tree):
            if any(
                module == prefix or module.startswith(f"{prefix}.")
                for prefix in forbidden_prefixes
            ):
                violations.append(f"{relative}: {module}")

    assert violations == []


def test_proposal_is_absent_from_canonical_production_hash_owners() -> None:
    for relative in (
        "src/ai_video/planning/_planner_models.py",
        "src/ai_video/planning/video_planner.py",
        "src/ai_video/production/video_requirement.py",
        "src/ai_video/production/dependency.py",
        "src/ai_video/production/shot_router.py",
        "src/ai_video/quality_gates/shot_readiness_gate.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "CompositionStrategyProposal" not in source
        assert ".agent/playbooks/composition" not in source
