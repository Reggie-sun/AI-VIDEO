"""Command-line stage selection for the exact-snapshot development Harness."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Sequence


def _add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", action="append", help="Advisory inspect path; repeatable.")
    parser.add_argument("--staged", action="store_true", help="Use the exact staged index delta.")
    parser.add_argument("--base-ref", help="Use merge-base(base-ref, head-ref)..head-ref.")
    parser.add_argument("--head-ref", default="HEAD", help="Commit-range head (default: HEAD).")
    parser.add_argument(
        "--level", choices=("focused", "related", "full"), default="related",
        help="focused: affected modules; related: modules and contracts; full: every suite.",
    )


def main(argv: Sequence[str] | None = None, *, harness) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser(
        "inspect", help="Show engineering-completion checks, not media-submit readiness."
    )
    verify_parser = subparsers.add_parser(
        "verify", help="Run engineering-completion checks and write a receipt."
    )
    receipt_parser = subparsers.add_parser(
        "verify-receipt", help="Verify receipt integrity and freshness."
    )
    subparsers.add_parser("policy-audit", help="Fail on unmapped owned repository files.")
    _add_scope_arguments(inspect_parser)
    _add_scope_arguments(verify_parser)
    verify_parser.add_argument("--run-id")
    receipt_parser.add_argument("receipt", type=Path)
    receipt_parser.add_argument("--require-level", choices=("related", "full"))
    args = parser.parse_args(argv)

    if args.command == "verify-receipt":
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        report = harness.receipt_freshness(receipt, receipt_dir=args.receipt.resolve().parent)
        print(json.dumps(report, sort_keys=True))
        sufficient = args.require_level != "full" or report["full_regression_passed"]
        return 0 if report["fresh"] and sufficient else 1

    policy = harness.load_policy()
    if args.command == "policy-audit":
        report = harness.audit_policy_coverage(policy)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if not any(
            report[key]
            for key in (
                "unmapped_paths",
                "unverified_paths",
                "missing_check_test_paths",
                "unreferenced_test_paths",
                "docs_contract_diagnostics",
            )
        ) else 1

    receipt_path: Path | None = None
    try:
        scope = harness.discover_scope(
            harness.PROJECT_ROOT,
            paths=args.path,
            staged=args.staged,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
        )
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))

    if args.command == "inspect":
        inspection = harness.inspect_paths(scope["changed_paths"], policy, level=args.level)
        inspection["scope"] = scope
        inspection["verification_purpose"] = "engineering_completion"
        inspection["media_submit_authority"] = False
        inspection["media_acceptance_authority"] = False
        print(json.dumps(inspection, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    try:
        harness.validate_completion_scope(scope)
        source_snapshot = harness._scope_snapshot(harness.PROJECT_ROOT, scope)
        harness.validate_scope_snapshot(scope, source_snapshot)
        with harness.isolated_verification_workspace(
            harness.PROJECT_ROOT, scope, source_snapshot=source_snapshot
        ) as execution_root:
            execution_policy_path = execution_root / ".agent/harness/policy.yaml"
            execution_policy = harness.load_policy(execution_policy_path)
            inspection = harness.inspect_paths(
                scope["changed_paths"], execution_policy, level=args.level
            )
            if inspection["unfocused_paths"]:
                raise ValueError(
                    "focused verification requires a module mapping: "
                    f"{inspection['unfocused_paths']}"
                )
            harness.materialize_npm_workspace_dependencies(
                harness.PROJECT_ROOT,
                execution_root,
                execution_policy,
                inspection["check_ids"],
            )
            receipt_path, passed = harness.verify_inspection(
                inspection,
                execution_policy,
                scope=scope,
                source_snapshot=source_snapshot,
                project_root=harness.PROJECT_ROOT,
                execution_root=execution_root,
                run_id=args.run_id,
                policy_sha256=harness._sha256(execution_policy_path.read_bytes()),
                workspace_cleanup_required=True,
                snapshot_after=lambda: harness._scope_snapshot(harness.PROJECT_ROOT, scope),
            )
        harness.receipt_io.record_workspace_cleanup(receipt_path, status="passed")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        if receipt_path is not None and receipt_path.is_file():
            try:
                harness.receipt_io.record_workspace_cleanup(
                    receipt_path,
                    status="failed",
                    error=f"isolated workspace cleanup failed: {exc}",
                )
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "passed" if passed else "failed",
                "receipt": receipt_path.relative_to(harness.PROJECT_ROOT).as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 1
