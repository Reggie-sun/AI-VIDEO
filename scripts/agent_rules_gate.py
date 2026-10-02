"""Read-only Development Governance checks; offline proof never grants acceptance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


REGISTRY = Path(".agent/harness/agent-rules.yaml")
POLICY = Path(".agent/harness/policy.yaml")


def _file(root: Path, relative: str) -> Path:
    candidate = root / relative
    if candidate.is_absolute() and not candidate.is_relative_to(root):
        raise ValueError(f"outside repository: {relative}")
    # Normalize links only after checking components for symlinks.
    for part in (candidate, *candidate.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"symlink: {relative}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"missing or escaping file: {relative}")
    return resolved


def _anchors(text: str) -> set[str]:
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    counts: dict[str, int] = {}
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
        if in_code or not re.match(r"^#{1,6}\s+", line):
            continue
        title = re.sub(r"^#{1,6}\s+|\s+#+$", "", line).lower()
        slug = re.sub(r"[^\w\s-]", "", title).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(f"{slug}-{count}" if count else slug)
    return result


def _links(root: Path, path: Path, text: str) -> list[str]:
    errors = []
    # Inline Markdown links in these controlled guide files; fenced recipes are ignored.
    text = re.sub(r"(?ms)^```.*?^```[^\n]*", "", text)
    for target in re.findall(r"\]\(([^\s)]+)\)", text):
        url = urlsplit(target.strip("<>"))
        if url.scheme or url.netloc:
            continue
        try:
            relative = (
                str(path.parent.relative_to(root) / unquote(url.path))
                if url.path
                else str(path.relative_to(root))
            )
            linked = _file(root, relative)
            if url.fragment and linked.suffix != ".md":
                raise ValueError("anchors require a Markdown target")
            if url.fragment and unquote(url.fragment) not in _anchors(
                linked.read_text(encoding="utf-8")
            ):
                errors.append(f"broken anchor: {path.relative_to(root)} -> {target}")
        except (OSError, ValueError) as exc:
            errors.append(f"broken link: {path.relative_to(root)} -> {target}: {exc}")
    return errors


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def check_repository(root: Path | str = Path(".")) -> list[str]:
    root = Path(root).resolve()
    errors: list[str] = []
    try:
        registry = yaml.safe_load(
            _file(root, str(REGISTRY)).read_text(encoding="utf-8")
        )
        policy = yaml.safe_load(_file(root, str(POLICY)).read_text(encoding="utf-8"))
        if (
            not isinstance(registry, dict)
            or type(registry.get("version")) is not int
            or registry["version"] != 1
        ):
            raise ValueError("invalid registry version")
        if not isinstance(policy, dict) or not isinstance(policy.get("checks"), dict):
            raise ValueError("invalid policy checks")
        documents, rules = registry.get("documents"), registry.get("rules")
        if (
            not isinstance(documents, list)
            or not documents
            or not isinstance(rules, list)
            or not rules
        ):
            raise ValueError("documents and rules must be nonempty lists")
        if not _positive(registry.get("context_max_bytes")):
            raise ValueError("context_max_bytes must be positive")
        routed = set(policy.get("always_check_ids", [])) | set(
            policy.get("fallback_check_ids", [])
        )
        for category in policy.get("categories", {}).values():
            routed.update(category.get("check_ids", []))
        identifiers: set[str] = set()
        for rule in rules:
            if (
                not isinstance(rule, dict)
                or not isinstance(rule.get("id"), str)
                or not rule["id"]
            ):
                raise ValueError("invalid rule id")
            if rule["id"] in identifiers:
                errors.append(f"duplicate rule: {rule['id']}")
            identifiers.add(rule["id"])
            if (
                rule.get("proof") not in {"offline_regression", "structure_only"}
                or not isinstance(rule.get("remaining"), str)
                or not rule["remaining"].strip()
            ):
                errors.append(f"invalid proof boundary: {rule['id']}")
            checks = rule.get("checks")
            if (
                not isinstance(checks, list)
                or not checks
                or any(not isinstance(c, str) for c in checks)
            ):
                errors.append(f"nonempty check references required: {rule['id']}")
                continue
            for check in checks:
                if check not in policy["checks"]:
                    errors.append(f"unknown check: {rule['id']} -> {check}")
                elif check not in routed:
                    errors.append(f"unrouted check: {rule['id']} -> {check}")
        registered: set[str] = set()
        for document in documents:
            if not isinstance(document, dict) or not isinstance(
                document.get("path"), str
            ):
                raise ValueError("invalid document")
            relative = document["path"]
            if (
                Path(relative).is_absolute()
                or ".." in Path(relative).parts
                or relative in registered
                or not (
                    relative == "AGENTS.md"
                    or (
                        relative.startswith(".agent/context/")
                        and Path(relative).suffix == ".md"
                    )
                )
            ):
                raise ValueError(f"unsafe or duplicate document: {relative}")
            registered.add(relative)
            if not _positive(document.get("max_lines")) or not _positive(
                document.get("max_bytes")
            ):
                raise ValueError(f"invalid document budget: {relative}")
            path = _file(root, relative)
            data = path.read_bytes()
            text = data.decode("utf-8")
            if (
                len(data) > document["max_bytes"]
                or len(text.splitlines()) > document["max_lines"]
            ):
                errors.append(f"document budget exceeded: {relative}")
            errors.extend(_links(root, path, text))
        if "AGENTS.md" not in registered:
            errors.append("AGENTS.md must be registered")
        context = root / ".agent/context"
        if context.is_symlink():
            raise ValueError("symlink context root")
        total = 0
        for path in sorted(context.rglob("*")):
            if path.is_symlink():
                errors.append(f"symlink context: {path.relative_to(root)}")
            elif path.is_file():
                relative = str(path.relative_to(root))
                if relative not in registered:
                    errors.append(f"unregistered context: {relative}")
                total += path.stat().st_size
        if total > registry["context_max_bytes"]:
            errors.append("context total byte budget exceeded")
    except (
        OSError,
        ValueError,
        TypeError,
        AttributeError,
        UnicodeError,
        yaml.YAMLError,
    ) as exc:
        errors.append(f"agent rules gate: {exc}")
    return sorted(errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    errors = check_repository(args.root)
    print(
        json.dumps(
            {
                "ok": not errors,
                "proof": "development_governance_only",
                "errors": errors,
            },
            ensure_ascii=False,
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
