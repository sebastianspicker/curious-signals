"""Command-line entry point for the curious-signals local tooling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .workflows import ToolError, build, bundle, check_generated, validate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m curious_signals")
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser(
        "build", help="expand core source XML into phyphox artifacts"
    )
    build_parser.add_argument("directory", nargs="?", type=Path, help="output directory")
    build_parser.add_argument("--output", type=Path, help="output directory")
    commands.add_parser(
        "validate", help="validate protocol, XML, firmware, and astronomy contracts"
    )
    commands.add_parser("check-generated", help="compare generated artifacts without writing")
    bundle_parser = commands.add_parser(
        "bundle", help="build core artifacts and create a deterministic ZIP"
    )
    bundle_parser.add_argument("archive", nargs="?", type=Path, help="archive path")
    bundle_parser.add_argument("--output", type=Path, help="archive path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build":
            if args.directory and args.output:
                raise ToolError("build accepts either DIRECTORY or --output, not both")
            files = build(args.output or args.directory)
            print(f"Built {len(files)} phyphox files.")
            return 0
        if args.command == "check-generated":
            errors = check_generated()
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            print("OK")
            return 0
        if args.command == "validate":
            errors = validate()
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            print("OK")
            return 0
        if args.archive and args.output:
            raise ToolError("bundle accepts either ARCHIVE or --output, not both")
        print(f"Created {bundle(args.output or args.archive)}")
        return 0
    except ToolError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
