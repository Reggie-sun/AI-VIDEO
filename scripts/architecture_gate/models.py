from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ExceptionRule:
    pattern: str
    reason: str


@dataclass(frozen=True)
class Policy:
    source_roots: tuple[str, ...]
    baseline: str
    normal_loc: int
    blocking_loc: int
    severe_loc: int
    fan_out_warning: int
    exclude: tuple[str, ...]
    exceptions: tuple[ExceptionRule, ...]


@dataclass(frozen=True)
class FileMetric:
    effective_loc: int
    fan_out: int
    module: str

    def to_dict(self) -> dict[str, int | str]:
        return {
            "effective_loc": self.effective_loc,
            "fan_out": self.fan_out,
            "module": self.module,
        }


@dataclass(frozen=True)
class ArchitectureSnapshot:
    files: dict[str, FileMetric]
    cycles: tuple[tuple[str, ...], ...]
    size_exempt_paths: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Finding:
    code: str
    slug: str
    severity: Severity
    path: str
    reason: str
    measurements: dict[str, Any]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "slug": self.slug,
            "severity": self.severity.value,
            "path": self.path,
            "reason": self.reason,
            "measurements": self.measurements,
            "recommended_actions": list(self.recommendations),
        }


@dataclass(frozen=True)
class GateResult:
    findings: tuple[Finding, ...]

    @property
    def has_errors(self) -> bool:
        return any(finding.severity is Severity.ERROR for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "FAIL" if self.has_errors else "PASS",
            "findings": [finding.to_dict() for finding in self.findings],
        }
