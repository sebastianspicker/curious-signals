"""Command-line entry point for the curious-signals local tooling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import ToolError
from .checkout import Checkout


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m curious_signals")
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser(
        "build", help="expand core source XML into phyphox artifacts"
    )
    build_parser.add_argument("--output", type=Path, help="output directory")
    commands.add_parser("validate", help="validate protocol, XML, and astronomy contracts")
    commands.add_parser("check-generated", help="compare generated artifacts without writing")
    bundle_parser = commands.add_parser(
        "bundle", help="build core artifacts and create a deterministic ZIP"
    )
    bundle_parser.add_argument(
        "--output", type=Path, default=Path("phyphox-experiments.zip"), help="archive path"
    )
    commands.add_parser("provision", help="install pinned Arduino core and libraries")
    commands.add_parser("compile", help="verify installed pins and compile the Arduino sketch")
    return parser


def _report(errors: list[str]) -> int:
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK")
    return 0


def _run(command: str, args: argparse.Namespace, checkout: Checkout) -> int:
    if command == "build":
        from .generation import build

        files = build(checkout, args.output)
        print(f"Built {len(files)} phyphox files.")
        return 0
    if command == "check-generated":
        from .generation import check_generated

        return _report(check_generated(checkout))
    if command == "validate":
        from .validation import validate

        return _report(validate(checkout))
    if command == "bundle":
        from .generation import bundle

        print(f"Created {bundle(checkout, args.output)}")
        return 0
    if command == "provision":
        from .arduino import provision

        provision(checkout.arduino_toolchain)
        return 0
    from .arduino import compile_sketch

    compile_sketch(checkout.arduino_toolchain, checkout.sketch_dir)
    print("OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args.command, args, Checkout.default())
    except ToolError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
