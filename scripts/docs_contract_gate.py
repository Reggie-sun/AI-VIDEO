"""Deterministic documentation contract verification for Development Governance.

The gate reads repository text and Python syntax only. It never imports Product
Runtime modules, contacts providers, reads credentials, or writes repository files.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml


REGISTRY_PATH = Path(".agent/harness/docs-contracts.yaml")
POLICY_PATH = Path(".agent/harness/policy.yaml")
SPECS_ROOT = PurePosixPath("docs/superpowers/specs")
SCHEMA_VERSION = 1

STATUS_VALUES = {
    "spec_status": {"proposed", "accepted", "superseded"},
    "implementation_status": {
        "not_started",
        "foundation_only",
        "implemented_offline",
        "implemented",
    },
    "live_status": {"not_applicable", "not_run", "partial", "accepted"},
    "quality_status": {
        "not_applicable",
        "not_evaluated",
        "partial",
        "accepted",
    },
    "release_status": {"unreleased", "released"},
}
METADATA_FIELDS = (
    "surface_id",
    "canonical",
    *STATUS_VALUES,
    "runtime_status_owner",
    "roadmap_owner",
)
OPTIONAL_METADATA_FIELDS = ("contract_version",)
IMPLEMENTED_STATUSES = {"foundation_only", "implemented_offline", "implemented"}
ASSERTION_TYPES = {
    "file_exists",
    "file_absent",
    "python_symbol_exists",
    "python_symbol_absent",
    "python_literal_equals",
    "text_contains",
    "text_not_contains",
    "regex_matches_exactly_once",
}


@dataclasses.dataclass(frozen=True, order=True)
class Diagnostic:
    surface_id: str
    field: str
    source_path: str
    expected: str
    actual: str

    def render(self) -> str:
        return (
            f"surface={self.surface_id} field={self.field} "
            f"expected={self.expected!r} actual={self.actual!r} "
            f"source={self.source_path}"
        )


@dataclasses.dataclass(frozen=True)
class CheckResult:
    diagnostics: tuple[Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "diagnostics": [dataclasses.asdict(item) for item in self.diagnostics],
        }


def _diagnostic(
    diagnostics: list[Diagnostic],
    surface_id: object,
    field: str,
    source_path: object,
    expected: object,
    actual: object,
) -> None:
    diagnostics.append(
        Diagnostic(
            surface_id=str(surface_id),
            field=field,
            source_path=str(source_path),
            expected=_display(expected),
            actual=_display(actual),
        )
    )


def _display(value: object) -> str:
    if value is None:
        return "<missing>"
    if isinstance(value, (dict, list, tuple, bool, int, float)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def _safe_relative(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(
        part not in {"", ".", ".."} for part in path.parts
    )


def _resolve(root: Path, relative: str) -> Path:
    return root.joinpath(*PurePosixPath(relative).parts)


def _contained_path(root: Path, relative: str) -> tuple[Path | None, str | None]:
    """Resolve a repository path without accepting symlink components."""

    candidate = _resolve(root, relative)
    current = root
    for part in PurePosixPath(relative).parts:
        current /= part
        if current.is_symlink():
            return None, f"symlink component: {current.relative_to(root)}"
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        return None, type(exc).__name__
    if not resolved.is_relative_to(root):
        return None, "outside repository"
    return candidate, None


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _front_matter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, flags=re.DOTALL)
    if match is None:
        return None
    value = yaml.safe_load(match.group(1))
    return value if isinstance(value, dict) else None


def _list(value: object) -> list[Any] | None:
    return value if isinstance(value, list) else None


def _path_field(
    diagnostics: list[Diagnostic],
    *,
    root: Path,
    surface_id: str,
    field: str,
    value: object,
    source: str,
    required: bool = True,
    prefix: PurePosixPath | None = None,
) -> Path | None:
    if value is None and not required:
        return None
    if not _safe_relative(value):
        _diagnostic(
            diagnostics,
            surface_id,
            field,
            source,
            "safe repository-relative path",
            value,
        )
        return None
    relative = PurePosixPath(str(value))
    if prefix is not None and relative != prefix and prefix not in relative.parents:
        _diagnostic(
            diagnostics,
            surface_id,
            field,
            source,
            f"path under {prefix}",
            value,
        )
        return None
    path, path_error = _contained_path(root, str(value))
    if path is None:
        _diagnostic(
            diagnostics,
            surface_id,
            field,
            source,
            "repository-contained non-symlink path",
            path_error,
        )
        return None
    if not path.is_file():
        _diagnostic(
            diagnostics,
            surface_id,
            field,
            str(value),
            "existing file",
            "missing",
        )
        return None
    return path


def _defined_symbol(tree: ast.Module, dotted: str) -> ast.AST | None:
    parts = dotted.split(".")
    if not parts or any(not part.isidentifier() for part in parts):
        return None
    body: Iterable[ast.stmt] = tree.body
    found: ast.AST | None = None
    for index, part in enumerate(parts):
        found = None
        for node in body:
            if isinstance(
                node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name == part:
                found = node
                break
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(
                    isinstance(target, ast.Name) and target.id == part
                    for target in targets
                ):
                    found = node
                    break
        if found is None:
            return None
        if index < len(parts) - 1:
            if not isinstance(found, ast.ClassDef):
                return None
            body = found.body
    return found


def _literal(node: ast.AST) -> object:
    if isinstance(node, ast.Assign):
        return ast.literal_eval(node.value)
    if isinstance(node, ast.AnnAssign):
        if node.value is not None:
            return ast.literal_eval(node.value)
        annotation = node.annotation
        if isinstance(annotation, ast.Subscript):
            name = annotation.value
            is_literal = (
                isinstance(name, ast.Name) and name.id == "Literal"
            ) or (
                isinstance(name, ast.Attribute) and name.attr == "Literal"
            )
            if is_literal:
                values = annotation.slice.elts if isinstance(
                    annotation.slice, ast.Tuple
                ) else [annotation.slice]
                literals = tuple(ast.literal_eval(value) for value in values)
                return literals[0] if len(literals) == 1 else literals
    raise ValueError("symbol is not a literal assignment")


def _assertion_path(
    diagnostics: list[Diagnostic],
    surface_id: str,
    assertion: dict[str, Any],
    index: int,
    registry_source: str,
) -> str | None:
    value = assertion.get("path")
    if not _safe_relative(value):
        _diagnostic(
            diagnostics,
            surface_id,
            f"assertions[{index}].path",
            registry_source,
            "safe repository-relative path",
            value,
        )
        return None
    return str(value)


def _check_assertion(
    diagnostics: list[Diagnostic],
    *,
    root: Path,
    surface_id: str,
    assertion: object,
    index: int,
    registry_source: str,
) -> None:
    field = f"assertions[{index}]"
    if not isinstance(assertion, dict):
        _diagnostic(
            diagnostics, surface_id, field, registry_source, "mapping", assertion
        )
        return
    kind = assertion.get("type")
    if kind not in ASSERTION_TYPES:
        _diagnostic(
            diagnostics,
            surface_id,
            f"{field}.type",
            registry_source,
            sorted(ASSERTION_TYPES),
            kind,
        )
        return
    relative = _assertion_path(
        diagnostics, surface_id, assertion, index, registry_source
    )
    if relative is None:
        return
    path, path_error = _contained_path(root, relative)
    if path is None:
        _diagnostic(
            diagnostics,
            surface_id,
            f"{field}.path",
            registry_source,
            "repository-contained non-symlink path",
            path_error,
        )
        return
    if kind == "file_exists":
        if not path.is_file():
            _diagnostic(
                diagnostics, surface_id, field, relative, "file exists", "missing"
            )
        return
    if kind == "file_absent":
        if path.exists():
            _diagnostic(
                diagnostics, surface_id, field, relative, "file absent", "present"
            )
        return
    if not path.is_file():
        _diagnostic(
            diagnostics,
            surface_id,
            field,
            relative,
            "existing assertion source",
            "missing",
        )
        return
    if kind.startswith("python_"):
        symbol = assertion.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            _diagnostic(
                diagnostics,
                surface_id,
                f"{field}.symbol",
                relative,
                "Python dotted symbol",
                symbol,
            )
            return
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, SyntaxError) as exc:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                relative,
                "parseable Python",
                type(exc).__name__,
            )
            return
        node = _defined_symbol(tree, symbol)
        if kind == "python_symbol_exists" and node is None:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                relative,
                f"symbol {symbol} exists",
                "missing",
            )
        elif kind == "python_symbol_absent" and node is not None:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                relative,
                f"symbol {symbol} absent",
                "present",
            )
        elif kind == "python_literal_equals":
            if node is None:
                _diagnostic(
                    diagnostics,
                    surface_id,
                    field,
                    relative,
                    f"literal {symbol}",
                    "symbol missing",
                )
            else:
                try:
                    actual = _literal(node)
                except (ValueError, TypeError, SyntaxError):
                    actual = "<non-literal>"
                expected = assertion.get("expected")
                if actual != expected:
                    _diagnostic(
                        diagnostics,
                        surface_id,
                        field,
                        relative,
                        expected,
                        actual,
                    )
        return
    text = path.read_text(encoding="utf-8")
    if kind in {"text_contains", "text_not_contains"}:
        expected = assertion.get("text")
        if not isinstance(expected, str):
            _diagnostic(
                diagnostics,
                surface_id,
                f"{field}.text",
                relative,
                "string",
                expected,
            )
        elif kind == "text_contains" and expected not in text:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                relative,
                f"contains {expected!r}",
                "not found",
            )
        elif kind == "text_not_contains" and expected in text:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                relative,
                f"does not contain {expected!r}",
                "found",
            )
        return
    pattern = assertion.get("pattern")
    if not isinstance(pattern, str):
        _diagnostic(
            diagnostics,
            surface_id,
            f"{field}.pattern",
            relative,
            "regex string",
            pattern,
        )
        return
    try:
        count = len(re.findall(pattern, text, flags=re.MULTILINE))
    except re.error as exc:
        _diagnostic(
            diagnostics,
            surface_id,
            f"{field}.pattern",
            relative,
            "valid regex",
            str(exc),
        )
        return
    if count != 1:
        _diagnostic(
            diagnostics, surface_id, field, relative, "exactly 1 match", count
        )


def _validate_surface(
    diagnostics: list[Diagnostic],
    *,
    root: Path,
    surface: object,
    index: int,
    policy_checks: set[str],
    registry_source: str,
) -> None:
    placeholder = f"<surface:{index}>"
    if not isinstance(surface, dict):
        _diagnostic(
            diagnostics, placeholder, "surface", registry_source, "mapping", surface
        )
        return
    surface_id = surface.get("surface_id")
    if not isinstance(surface_id, str) or not surface_id:
        _diagnostic(
            diagnostics,
            placeholder,
            "surface_id",
            registry_source,
            "non-empty string",
            surface_id,
        )
        surface_id = placeholder
    canonical = surface.get("canonical")
    if not isinstance(canonical, bool):
        _diagnostic(
            diagnostics, surface_id, "canonical", registry_source, "boolean", canonical
        )
    for field, allowed in STATUS_VALUES.items():
        actual = surface.get(field)
        if actual not in allowed:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                registry_source,
                sorted(allowed),
                actual,
            )
    if surface.get("spec_status") == "superseded" and canonical is True:
        _diagnostic(
            diagnostics, surface_id, "canonical", registry_source, False, True
        )

    spec_path = _path_field(
        diagnostics,
        root=root,
        surface_id=surface_id,
        field="canonical_spec",
        value=surface.get("canonical_spec"),
        source=registry_source,
        prefix=SPECS_ROOT,
    )
    for field in ("runtime_status_owner", "roadmap_owner"):
        _path_field(
            diagnostics,
            root=root,
            surface_id=surface_id,
            field=field,
            value=surface.get(field),
            source=registry_source,
        )

    implementation_paths = _list(surface.get("implementation_paths"))
    test_paths = _list(surface.get("test_paths"))
    implementation_status = surface.get("implementation_status")
    for field, values in (
        ("implementation_paths", implementation_paths),
        ("test_paths", test_paths),
    ):
        if values is None:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                registry_source,
                "list",
                surface.get(field),
            )
            continue
        if implementation_status in IMPLEMENTED_STATUSES and not values:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                registry_source,
                "non-empty implementation evidence",
                values,
            )
        if implementation_status == "not_started" and values:
            _diagnostic(
                diagnostics,
                surface_id,
                field,
                registry_source,
                "empty for not_started",
                values,
            )
        for item_index, value in enumerate(values):
            _path_field(
                diagnostics,
                root=root,
                surface_id=surface_id,
                field=f"{field}[{item_index}]",
                value=value,
                source=registry_source,
            )

    check_ids = _list(surface.get("harness_check_ids"))
    if check_ids is None:
        _diagnostic(
            diagnostics,
            surface_id,
            "harness_check_ids",
            registry_source,
            "list",
            surface.get("harness_check_ids"),
        )
    else:
        if implementation_status in IMPLEMENTED_STATUSES and not check_ids:
            _diagnostic(
                diagnostics,
                surface_id,
                "harness_check_ids",
                registry_source,
                "non-empty implemented-surface verification ownership",
                check_ids,
            )
        for check_id in check_ids:
            if not isinstance(check_id, str) or check_id not in policy_checks:
                _diagnostic(
                    diagnostics,
                    surface_id,
                    "harness_check_ids",
                    registry_source,
                    "known Harness check ID",
                    check_id,
                )

    assertions = _list(surface.get("assertions"))
    if assertions is None:
        _diagnostic(
            diagnostics,
            surface_id,
            "assertions",
            registry_source,
            "list",
            surface.get("assertions"),
        )
    else:
        for assertion_index, assertion in enumerate(assertions):
            _check_assertion(
                diagnostics,
                root=root,
                surface_id=surface_id,
                assertion=assertion,
                index=assertion_index,
                registry_source=registry_source,
            )

    if "contract_version" in surface and not isinstance(
        surface["contract_version"], str
    ):
        _diagnostic(
            diagnostics,
            surface_id,
            "contract_version",
            registry_source,
            "string",
            surface["contract_version"],
        )

    if spec_path is not None:
        spec_source = str(spec_path.relative_to(root))
        try:
            metadata = _front_matter(spec_path)
        except (OSError, yaml.YAMLError) as exc:
            _diagnostic(
                diagnostics,
                surface_id,
                "spec_metadata",
                spec_source,
                "valid YAML front matter",
                type(exc).__name__,
            )
            metadata = None
        if metadata is None:
            _diagnostic(
                diagnostics,
                surface_id,
                "spec_metadata",
                spec_source,
                "YAML front matter",
                "missing or invalid",
            )
        else:
            for field in METADATA_FIELDS:
                if metadata.get(field) != surface.get(field):
                    _diagnostic(
                        diagnostics,
                        surface_id,
                        field,
                        spec_source,
                        surface.get(field),
                        metadata.get(field),
                    )
            for field in OPTIONAL_METADATA_FIELDS:
                if field in surface or field in metadata:
                    if metadata.get(field) != surface.get(field):
                        _diagnostic(
                            diagnostics,
                            surface_id,
                            field,
                            spec_source,
                            surface.get(field),
                            metadata.get(field),
                        )


def _audit_active_specs(
    root: Path,
    diagnostics: list[Diagnostic],
    registered_specs: dict[str, str],
) -> None:
    specs_root, _ = _contained_path(root, str(SPECS_ROOT))
    if specs_root is None or not specs_root.is_dir():
        return
    active: dict[str, list[str]] = {}
    for path in sorted(specs_root.rglob("*.md")):
        relative = str(path.relative_to(root))
        safe_path, _ = _contained_path(root, relative)
        if safe_path is None:
            continue
        try:
            metadata = _front_matter(safe_path)
        except (OSError, yaml.YAMLError):
            continue
        if not metadata or metadata.get("canonical") is not True:
            continue
        surface_id = metadata.get("surface_id")
        if metadata.get("spec_status") == "superseded":
            _diagnostic(
                diagnostics,
                surface_id or "<unknown>",
                "canonical",
                str(path.relative_to(root)),
                False,
                True,
            )
            continue
        if isinstance(surface_id, str) and surface_id:
            active.setdefault(surface_id, []).append(relative)
            registered_path = registered_specs.get(surface_id)
            if registered_path != relative:
                _diagnostic(
                    diagnostics,
                    surface_id,
                    "surface_registry",
                    relative,
                    registered_path or "registered canonical spec",
                    relative if registered_path else "omitted",
                )
    for surface_id, paths in sorted(active.items()):
        if len(paths) > 1:
            _diagnostic(
                diagnostics,
                surface_id,
                "canonical_spec",
                ", ".join(paths),
                "at most one active canonical spec",
                paths,
            )


def check_contract(
    root: Path | str = Path("."),
    registry_path: Path | str | None = None,
    policy_path: Path | str | None = None,
) -> CheckResult:
    """Check one repository snapshot without mutating it."""

    root_path = Path(root).resolve()
    registry = (
        Path(registry_path)
        if registry_path is not None
        else root_path / REGISTRY_PATH
    )
    policy = Path(policy_path) if policy_path is not None else root_path / POLICY_PATH
    diagnostics: list[Diagnostic] = []
    registry_source = (
        str(registry.relative_to(root_path))
        if registry.is_relative_to(root_path)
        else str(registry)
    )

    try:
        registry_data = _load_yaml(registry)
    except (OSError, yaml.YAMLError) as exc:
        _diagnostic(
            diagnostics,
            "<registry>",
            "registry",
            registry_source,
            "readable YAML mapping",
            type(exc).__name__,
        )
        return CheckResult(tuple(sorted(diagnostics)))
    if not isinstance(registry_data, dict):
        _diagnostic(
            diagnostics,
            "<registry>",
            "registry",
            registry_source,
            "YAML mapping",
            registry_data,
        )
        return CheckResult(tuple(sorted(diagnostics)))
    if registry_data.get("schema_version") != SCHEMA_VERSION:
        _diagnostic(
            diagnostics,
            "<registry>",
            "schema_version",
            registry_source,
            SCHEMA_VERSION,
            registry_data.get("schema_version"),
        )

    try:
        policy_data = _load_yaml(policy)
    except (OSError, yaml.YAMLError) as exc:
        _diagnostic(
            diagnostics,
            "<registry>",
            "harness_policy",
            str(policy),
            "readable YAML mapping",
            type(exc).__name__,
        )
        policy_data = {}
    checks_value = policy_data.get("checks", {}) if isinstance(policy_data, dict) else {}
    policy_checks = set(checks_value) if isinstance(checks_value, dict) else set()

    surfaces = registry_data.get("surfaces")
    if not isinstance(surfaces, list):
        _diagnostic(
            diagnostics,
            "<registry>",
            "surfaces",
            registry_source,
            "list",
            surfaces,
        )
        return CheckResult(tuple(sorted(diagnostics)))
    identifiers: dict[str, int] = {}
    registered_specs: dict[str, str] = {}
    for index, surface in enumerate(surfaces):
        if isinstance(surface, dict) and isinstance(surface.get("surface_id"), str):
            surface_id = surface["surface_id"]
            if surface_id in identifiers:
                _diagnostic(
                    diagnostics,
                    surface_id,
                    "surface_id",
                    registry_source,
                    "unique",
                    f"duplicate indexes {identifiers[surface_id]},{index}",
                )
            identifiers.setdefault(surface_id, index)
            canonical_spec = surface.get("canonical_spec")
            if isinstance(canonical_spec, str):
                registered_specs.setdefault(surface_id, canonical_spec)
        _validate_surface(
            diagnostics,
            root=root_path,
            surface=surface,
            index=index,
            policy_checks=policy_checks,
            registry_source=registry_source,
        )
    _audit_active_specs(root_path, diagnostics, registered_specs)
    return CheckResult(tuple(sorted(diagnostics)))


def check_repository(root: Path | str = Path(".")) -> CheckResult:
    """Stable public seam used by the Harness audit."""

    return check_contract(root)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = check_contract(args.root, args.registry, args.policy)
    if args.json:
        print(
            json.dumps(
                result.to_dict(), indent=2, sort_keys=True, ensure_ascii=False
            )
        )
    elif result.ok:
        print("Documentation contract gate passed.")
    else:
        for diagnostic in result.diagnostics:
            print(diagnostic.render())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
