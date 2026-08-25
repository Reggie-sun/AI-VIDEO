from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import subprocess
import tempfile
import tomllib
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.architecture_gate.metrics import (
    build_snapshot,
    current_sources,
    git_sources,
    module_path,
)
from scripts.architecture_gate.models import (
    ArchitectureSnapshot,
    DependencyException,
    DependencyRule,
    ExceptionRule,
    FileMetric,
    Finding,
    GateResult,
    ImportContext,
    ImportEdge,
    ModuleSet,
    Policy,
    Severity,
    SyntaxErrorEvidence,
)


_SIZE_RECOMMENDATIONS = (
    "move the new responsibility behind an existing cohesive module boundary",
    "extract a cohesive domain module while preserving public contracts",
    "reduce equivalent code elsewhere in this module",
    "keep an indivisible correctness-critical transaction lifecycle together when separation would weaken its invariants",
    "use an explicit reviewed exception only when separation would materially worsen correctness",
)

_POLICY_KEYS = frozenset(
    {
        "schema_version",
        "source_roots",
        "baseline",
        "normal_loc",
        "blocking_loc",
        "severe_loc",
        "fan_out_warning",
        "exclude",
        "exceptions",
        "module_sets",
        "dependency_rules",
        "dependency_exceptions",
    }
)


def check_architecture(root: Path, *, base_ref: str | None = None) -> GateResult:
    root = Path(root).resolve()
    try:
        policy = _load_policy(root)
        current = build_snapshot(current_sources(root, policy), policy)
        if base_ref is not None:
            base = build_snapshot(git_sources(root, policy, base_ref), policy)
            stale_baseline = False
        else:
            base = _load_baseline(root, policy)
            stale_baseline = True
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
        tomllib.TOMLDecodeError,
        json.JSONDecodeError,
    ) as exc:
        return GateResult((_baseline_invalid(str(exc)),))

    findings = _compare(current, base, policy)
    findings.extend(_dependency_findings(current, policy))
    if stale_baseline:
        findings.extend(_stale_baseline_findings(current, base))
    return GateResult(tuple(sorted(findings, key=_finding_sort_key)))


def update_baseline(root: Path) -> Path:
    root = Path(root).resolve()
    policy = _load_policy(root)
    snapshot = build_snapshot(current_sources(root, policy), policy)
    payload = {
        "schema_version": 1,
        "policy_fingerprint": _policy_fingerprint(policy),
        "files": {
            path: metric.to_dict() for path, metric in sorted(snapshot.files.items())
        },
        "cycles": [list(cycle) for cycle in snapshot.cycles],
    }
    baseline_path = root / policy.baseline
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=baseline_path.parent,
            prefix=f".{baseline_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, baseline_path)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
    return baseline_path


def render_text(result: GateResult) -> str:
    blocks: list[str] = []
    for finding in result.findings:
        lines = [
            f"{finding.code} {finding.slug}",
            "",
            f"Path: {finding.path}",
            f"Severity: {finding.severity.value}",
        ]
        labels = {
            "base_loc": "Base LOC",
            "current_loc": "Current LOC",
            "delta": "Delta",
            "fan_out": "Fan-out",
            "modules": "Modules",
        }
        for key, value in finding.measurements.items():
            label = labels.get(key, key.replace("_", " ").title())
            if key == "delta" and isinstance(value, int):
                rendered = f"{value:+d}"
            elif isinstance(value, list):
                rendered = ", ".join(str(item) for item in value)
            else:
                rendered = str(value)
            lines.append(f"{label}: {rendered}")
        lines.extend(["", "Reason:", finding.reason, "", "Recommended actions:"])
        lines.extend(f"- {action}" for action in finding.recommendations)
        blocks.append("\n".join(lines))

    errors = sum(item.severity is Severity.ERROR for item in result.findings)
    warnings = sum(item.severity is Severity.WARN for item in result.findings)
    information = sum(item.severity is Severity.INFO for item in result.findings)
    status = "FAIL" if result.has_errors else "PASS"
    summary = (
        f"Architecture gate: {status} "
        f"({errors} error(s), {warnings} warning(s), {information} info finding(s))"
    )
    return "\n\n".join([*blocks, summary])


def _load_policy(root: Path) -> Policy:
    config_path = root / "architecture_gate.toml"
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    schema_version = raw.get("schema_version")
    if type(schema_version) is not int:
        raise ValueError("architecture_gate.toml schema_version must be an integer")
    if schema_version not in (1, 2):
        raise ValueError("architecture_gate.toml schema_version must be 1 or 2")
    if schema_version == 2:
        unknown_keys = sorted(set(raw) - _POLICY_KEYS)
        if unknown_keys:
            raise ValueError(
                "architecture_gate.toml has unknown top-level field(s): "
                + ", ".join(unknown_keys)
            )
    source_roots = tuple(_safe_relative(item, "source root") for item in raw["source_roots"])
    baseline = _safe_relative(raw["baseline"], "baseline path")
    exceptions = tuple(
        ExceptionRule(
            pattern=_safe_pattern(item.get("pattern"), "exception pattern"),
            reason=_required_text(item.get("reason"), "exception reason"),
        )
        for item in _required_tables(raw.get("exceptions", []), "exceptions")
    )
    module_sets = tuple(
        ModuleSet(
            name=_required_text(item.get("name"), "module set name"),
            patterns=tuple(
                _safe_pattern(pattern, "module set pattern")
                for pattern in _required_list(
                    item.get("patterns", []), "module set patterns"
                )
            ),
        )
        for item in _required_tables(raw.get("module_sets", []), "module sets")
    )
    module_set_names = [item.name for item in module_sets]
    if len(module_set_names) != len(set(module_set_names)):
        raise ValueError("module set names must be unique")
    for module_set in module_sets:
        if not module_set.patterns:
            raise ValueError(f"module set {module_set.name!r} must declare patterns")

    dependency_rules = tuple(
        DependencyRule(
            id=_dependency_rule_id(item.get("id")),
            source_module_set=_required_text(
                item.get("source_module_set"), "dependency rule source module set"
            ),
            forbidden_targets=tuple(
                _safe_module_name(target, "forbidden target")
                for target in _required_list(
                    item.get("forbidden_targets", []), "forbidden targets"
                )
            ),
            target_match=_required_text(
                item.get("target_match"), "dependency rule target match"
            ),
            contract_ref=_required_text(
                item.get("contract_ref"), "dependency rule contract ref"
            ),
            severity=_dependency_severity(item.get("severity")),
        )
        for item in _required_tables(
            raw.get("dependency_rules", []), "dependency rules"
        )
    )
    rule_ids = [item.id for item in dependency_rules]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("duplicate dependency rule id")
    known_module_sets = frozenset(module_set_names)
    for rule in dependency_rules:
        if rule.source_module_set not in known_module_sets:
            raise ValueError(
                f"dependency rule {rule.id!r} references unknown module set "
                f"{rule.source_module_set!r}"
            )
        if not rule.forbidden_targets:
            raise ValueError(
                f"dependency rule {rule.id!r} must declare forbidden targets"
            )
        if rule.target_match not in ("exact", "prefix"):
            raise ValueError(
                f"dependency rule {rule.id!r} target_match must be exact or prefix"
            )

    dependency_exceptions = tuple(
        DependencyException(
            rule_id=_required_text(item.get("rule_id"), "dependency exception rule id"),
            source_path=_safe_exact_relative(
                item.get("source_path"), "dependency exception exact source path"
            ),
            target_module=_safe_module_name(
                item.get("target_module"), "dependency exception target module"
            ),
            owner_ref=_required_text(
                item.get("owner_ref"), "dependency exception owner ref"
            ),
            reason=_required_text(item.get("reason"), "dependency exception reason"),
            review_by=_review_date(item.get("review_by")),
        )
        for item in _required_tables(
            raw.get("dependency_exceptions", []), "dependency exceptions"
        )
    )
    known_rule_ids = frozenset(rule_ids)
    exception_keys: set[tuple[str, str, str]] = set()
    for exception in dependency_exceptions:
        if exception.rule_id not in known_rule_ids:
            raise ValueError(
                f"dependency exception references unknown rule {exception.rule_id!r}"
            )
        key = (exception.rule_id, exception.source_path, exception.target_module)
        if key in exception_keys:
            raise ValueError("duplicate dependency exception")
        exception_keys.add(key)
        if exception.review_by < date.today():
            raise ValueError(
                f"dependency exception for {exception.source_path!r} expired on "
                f"{exception.review_by.isoformat()}"
            )

    if schema_version == 1 and (
        module_sets or dependency_rules or dependency_exceptions
    ):
        raise ValueError("dependency contract requires schema_version 2")
    policy = Policy(
        schema_version=schema_version,
        source_roots=source_roots,
        baseline=baseline,
        normal_loc=int(raw["normal_loc"]),
        blocking_loc=int(raw["blocking_loc"]),
        severe_loc=int(raw["severe_loc"]),
        fan_out_warning=int(raw["fan_out_warning"]),
        exclude=tuple(
            _safe_pattern(pattern, "exclude pattern") for pattern in raw.get("exclude", [])
        ),
        exceptions=exceptions,
        module_sets=module_sets,
        dependency_rules=dependency_rules,
        dependency_exceptions=dependency_exceptions,
    )
    if not (
        0 < policy.normal_loc < policy.blocking_loc < policy.severe_loc
        and policy.fan_out_warning > 0
    ):
        raise ValueError("architecture gate thresholds must be positive and increasing")
    return policy


def _load_baseline(root: Path, policy: Policy) -> ArchitectureSnapshot:
    baseline_path = root / policy.baseline
    if not baseline_path.is_file():
        raise ValueError(f"architecture baseline does not exist: {policy.baseline}")
    raw = json.loads(baseline_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1:
        raise ValueError("architecture baseline schema_version must be 1")
    if raw.get("policy_fingerprint") != _policy_fingerprint(policy):
        raise ValueError("architecture baseline policy fingerprint does not match config")
    files: dict[str, FileMetric] = {}
    for path, metric in raw.get("files", {}).items():
        safe_path = _safe_relative(path, "baseline file path")
        files[safe_path] = FileMetric(
            effective_loc=int(metric["effective_loc"]),
            fan_out=int(metric["fan_out"]),
            module=_required_text(metric["module"], "baseline module"),
        )
    cycles = tuple(
        sorted(tuple(sorted(_required_text(module, "cycle module") for module in cycle)) for cycle in raw.get("cycles", []))
    )
    return ArchitectureSnapshot(
        files=dict(sorted(files.items())),
        cycles=cycles,
        size_exempt_paths=frozenset(
            path
            for path in files
            if any(
                fnmatch.fnmatch(path, rule.pattern)
                for rule in policy.exceptions
            )
        ),
    )


def _policy_fingerprint(policy: Policy) -> str:
    payload = {
        "source_roots": policy.source_roots,
        "normal_loc": policy.normal_loc,
        "blocking_loc": policy.blocking_loc,
        "severe_loc": policy.severe_loc,
        "fan_out_warning": policy.fan_out_warning,
        "exclude": policy.exclude,
        "exceptions": [
            {"pattern": item.pattern, "reason": item.reason} for item in policy.exceptions
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _compare(
    current: ArchitectureSnapshot,
    base: ArchitectureSnapshot,
    policy: Policy,
) -> list[Finding]:
    findings: list[Finding] = []
    for path, current_metric in current.files.items():
        base_metric = base.files.get(path)
        if path not in current.size_exempt_paths:
            if base_metric is None:
                if current_metric.effective_loc > policy.normal_loc:
                    findings.append(_new_oversized(path, current_metric, policy))
            elif (
                current_metric.effective_loc > policy.normal_loc
                and current_metric.effective_loc > base_metric.effective_loc
            ):
                findings.append(
                    _oversized_growth(path, base_metric, current_metric, policy)
                )

        if current_metric.fan_out >= policy.fan_out_warning and (
            base_metric is None or base_metric.fan_out < policy.fan_out_warning
        ):
            findings.append(_fan_out(path, current_metric, policy))

    base_cycle_sets = tuple(frozenset(cycle) for cycle in base.cycles)
    for cycle in current.cycles:
        current_cycle = frozenset(cycle)
        if not any(current_cycle <= base_cycle for base_cycle in base_cycle_sets):
            cycle_paths = sorted(
                path for module in cycle if (path := module_path(current, module)) is not None
            )
            findings.append(_new_cycle(cycle_paths[0] if cycle_paths else "<import-graph>", cycle))
    return findings


def _dependency_findings(
    current: ArchitectureSnapshot,
    policy: Policy,
) -> list[Finding]:
    if not policy.dependency_rules:
        return []
    findings = [_syntax_error_finding(item) for item in current.syntax_errors]
    module_sets = {item.name: item for item in policy.module_sets}
    for module_set_name in sorted(
        {rule.source_module_set for rule in policy.dependency_rules}
    ):
        module_set = module_sets[module_set_name]
        if not any(
            fnmatch.fnmatch(path, pattern)
            for path in current.files
            for pattern in module_set.patterns
        ):
            findings.append(
                _empty_dependency_module_set(
                    module_set_name,
                    tuple(
                        rule.id
                        for rule in policy.dependency_rules
                        if rule.source_module_set == module_set_name
                    ),
                )
            )
    exceptions = {
        (item.rule_id, item.source_path, item.target_module): item
        for item in policy.dependency_exceptions
    }
    used_exceptions: set[tuple[str, str, str]] = set()
    emitted: set[tuple[str, str, str]] = set()

    for edge in current.import_edges:
        if edge.context is not ImportContext.RUNTIME:
            continue
        for rule in policy.dependency_rules:
            source_set = module_sets[rule.source_module_set]
            if not any(
                fnmatch.fnmatch(edge.source_path, pattern)
                for pattern in source_set.patterns
            ):
                continue
            matched_target = _matched_dependency_target(edge, rule)
            if matched_target is None:
                continue
            key = (rule.id, edge.source_path, matched_target)
            if key in exceptions:
                used_exceptions.add(key)
                continue
            if key in emitted:
                continue
            emitted.add(key)
            findings.append(_forbidden_dependency(edge, rule, matched_target))

    for key, exception in sorted(exceptions.items()):
        if key not in used_exceptions:
            findings.append(_stale_dependency_exception(exception))
    return findings


def _target_matches(target: str, forbidden: str, match: str) -> bool:
    if match == "exact":
        return target == forbidden
    return target == forbidden or target.startswith(f"{forbidden}.")


def _matched_dependency_target(
    edge: ImportEdge,
    rule: DependencyRule,
) -> str | None:
    for forbidden in rule.forbidden_targets:
        if _target_matches(edge.target_module, forbidden, rule.target_match):
            return edge.target_module
        if edge.import_from_base is not None and _target_matches(
            edge.import_from_base, forbidden, rule.target_match
        ):
            return edge.import_from_base
    return None


def _syntax_error_finding(error: SyntaxErrorEvidence) -> Finding:
    return Finding(
        code="ARCH100",
        slug="dependency-source-syntax-error",
        severity=Severity.ERROR,
        path=error.path,
        reason=(
            "The source could not be parsed, so the Architecture Gate cannot prove "
            f"its dependency contract: {error.detail}"
        ),
        measurements={"line": error.lineno},
        recommendations=(
            "repair the syntax error before evaluating or updating architecture evidence",
        ),
    )


def _forbidden_dependency(
    edge: ImportEdge,
    rule: DependencyRule,
    matched_target: str,
) -> Finding:
    return Finding(
        code=rule.id,
        slug="forbidden-module-dependency",
        severity=rule.severity,
        path=edge.source_path,
        reason=(
            f"A runtime import crosses the dependency boundary declared by {rule.contract_ref}."
        ),
        measurements={
            "line": edge.lineno,
            "source_module": edge.source_module,
            "target_module": matched_target,
            "contract_ref": rule.contract_ref,
        },
        recommendations=(
            "depend on the canonical boundary allowed by the referenced contract",
            "change the machine contract only when the semantic owner intentionally changes",
        ),
    )


def _empty_dependency_module_set(
    module_set: str,
    rule_ids: tuple[str, ...],
) -> Finding:
    return Finding(
        code="ARCH100",
        slug="empty-dependency-module-set",
        severity=Severity.ERROR,
        path="architecture_gate.toml",
        reason=(
            "An active dependency module set matches no current source files, so its "
            "rules cannot provide enforcement."
        ),
        measurements={"module_set": module_set, "rule_ids": list(rule_ids)},
        recommendations=(
            "repair the module set patterns or remove the inactive dependency rules",
        ),
    )


def _stale_dependency_exception(exception: DependencyException) -> Finding:
    return Finding(
        code="ARCH100",
        slug="stale-dependency-exception",
        severity=Severity.ERROR,
        path=exception.source_path,
        reason=(
            f"The exact exception for {exception.target_module!r} no longer matches a "
            "forbidden runtime import."
        ),
        measurements={
            "rule_id": exception.rule_id,
            "target_module": exception.target_module,
            "owner_ref": exception.owner_ref,
            "review_by": exception.review_by.isoformat(),
        },
        recommendations=(
            "remove the stale exception from architecture_gate.toml",
        ),
    )


def _oversized_growth(
    path: str,
    base: FileMetric,
    current: FileMetric,
    policy: Policy,
) -> Finding:
    blocking = current.effective_loc > policy.blocking_loc
    severe = current.effective_loc > policy.severe_loc
    debt_kind = "severe architecture debt" if severe else "architecture debt"
    return Finding(
        code="ARCH001",
        slug="oversized-module-growth",
        severity=Severity.ERROR if blocking else Severity.WARN,
        path=path,
        reason=(
            f"This module already carries {debt_kind}, and the current change increases "
            "its effective production LOC. Historical debt is grandfathered; growth is not."
        ),
        measurements={
            "base_loc": base.effective_loc,
            "current_loc": current.effective_loc,
            "delta": current.effective_loc - base.effective_loc,
        },
        recommendations=_SIZE_RECOMMENDATIONS,
    )


def _new_oversized(path: str, current: FileMetric, policy: Policy) -> Finding:
    blocking = current.effective_loc > policy.blocking_loc
    debt_kind = (
        "severe architecture debt"
        if current.effective_loc > policy.severe_loc
        else "architecture debt"
    )
    return Finding(
        code="ARCH002",
        slug="new-oversized-module",
        severity=Severity.ERROR if blocking else Severity.WARN,
        path=path,
        reason=(
            f"This new production module begins with {debt_kind} above the reviewed architecture size boundary. "
            "Size is a review proxy, not proof of poor cohesion."
        ),
        measurements={"current_loc": current.effective_loc},
        recommendations=_SIZE_RECOMMENDATIONS,
    )


def _new_cycle(path: str, cycle: tuple[str, ...]) -> Finding:
    return Finding(
        code="ARCH003",
        slug="dependency-cycle-regression",
        severity=Severity.ERROR,
        path=path,
        reason="The current first-party module import graph introduces a dependency cycle absent from the base snapshot.",
        measurements={"modules": list(cycle)},
        recommendations=(
            "move the shared contract toward the dependency root",
            "invert one dependency behind an existing stable boundary",
            "avoid a second state owner or compatibility import solely to hide the cycle",
        ),
    )


def _fan_out(path: str, current: FileMetric, policy: Policy) -> Finding:
    return Finding(
        code="ARCH005",
        slug="module-fan-out-review-signal",
        severity=Severity.INFO,
        path=path,
        reason="This module newly crosses the first-party fan-out review threshold; fan-out alone is not blocking.",
        measurements={
            "fan_out": current.fan_out,
            "warning_threshold": policy.fan_out_warning,
        },
        recommendations=(
            "confirm the imports belong to one cohesive responsibility",
            "prefer existing stable domain boundaries over convenience imports",
        ),
    )


def _stale_baseline_findings(
    current: ArchitectureSnapshot,
    base: ArchitectureSnapshot,
) -> list[Finding]:
    return [
        Finding(
            code="ARCH004",
            slug="stale-architecture-baseline-entry",
            severity=Severity.INFO,
            path=path,
            reason="The baseline still records a production module that no longer exists in the current snapshot.",
            measurements={},
            recommendations=(
                "run the explicit update-baseline command after reviewing the deletion or split",
            ),
        )
        for path in sorted(set(base.files) - set(current.files))
    ]


def _baseline_invalid(detail: str) -> Finding:
    return Finding(
        code="ARCH004",
        slug="architecture-baseline-invalid",
        severity=Severity.ERROR,
        path=".architecture/architecture-baseline.json",
        reason=f"Architecture gate configuration or baseline is invalid: {detail}",
        measurements={},
        recommendations=(
            "repair the reviewed config or run the explicit update-baseline command",
            "do not widen or refresh the baseline merely to hide a regression",
        ),
    )


def _safe_relative(value: Any, label: str) -> str:
    text = _required_text(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or text == ".":
        raise ValueError(f"{label} must be a contained relative path")
    return path.as_posix()


def _safe_pattern(value: Any, label: str) -> str:
    text = _required_text(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a contained relative glob")
    return text


def _safe_exact_relative(value: Any, label: str) -> str:
    text = _safe_relative(value, label)
    if any(character in text for character in "*?["):
        raise ValueError(f"{label} must not contain wildcards")
    return text


def _safe_module_name(value: Any, label: str) -> str:
    text = _required_text(value, label)
    if any(character in text for character in "*?[]"):
        raise ValueError(f"{label} must be an exact module name")
    if any(not part.isidentifier() for part in text.split(".")):
        raise ValueError(f"{label} must be a dotted Python module name")
    return text


def _dependency_severity(value: Any) -> Severity:
    text = _required_text(value, "dependency rule severity")
    if text != "error":
        raise ValueError("dependency rule severity must be error")
    return Severity.ERROR


def _dependency_rule_id(value: Any) -> str:
    text = _required_text(value, "dependency rule id")
    number = text.removeprefix("ARCH")
    if not number.isdigit() or int(number) < 101:
        raise ValueError("dependency rule id must be ARCH101 or higher")
    return text


def _review_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    text = _required_text(value, "dependency exception review_by")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            "dependency exception review_by must be an ISO date"
        ) from exc


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _required_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a list")
    return value


def _required_tables(value: Any, label: str) -> list[dict[str, Any]]:
    rows = _required_list(value, label)
    if any(not isinstance(item, dict) for item in rows):
        raise TypeError(f"{label} must contain tables")
    return rows


def _finding_sort_key(finding: Finding) -> tuple[int, str, str]:
    order = {Severity.ERROR: 0, Severity.WARN: 1, Severity.INFO: 2}
    return order[finding.severity], finding.code, finding.path
