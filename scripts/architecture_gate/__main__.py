from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from scripts.architecture_gate.gate import (
    check_architecture,
    render_text,
    update_baseline,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.architecture_gate",
        description="Check architecture debt without changing production state.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="evaluate architecture regressions")
    check.add_argument("--root", type=Path, default=Path.cwd())
    check.add_argument("--base-ref", help="compare against a Git ref instead of the baseline")
    check.add_argument("--format", choices=("text", "json"), default="text")
    update = commands.add_parser(
        "update-baseline",
        help="explicitly replace the deterministic architecture baseline",
    )
    update.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "update-baseline":
        try:
            path = update_baseline(args.root)
        except (OSError, ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
            print(f"Architecture baseline update failed: {exc}", file=sys.stderr)
            return 2
        print(f"Updated architecture baseline: {path}")
        return 0

    result = check_architecture(args.root, base_ref=args.base_ref)
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 1 if result.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
