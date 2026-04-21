#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys


def postprocess(xml_text: str) -> str:
    # Remove xml:base attributes added by xmllint --xinclude, because they are not
    # part of the intended phyphox experiment format and create noisy diffs.
    xml_text = re.sub(r'\s+xml:base="[^"]*"', "", xml_text)

    # If XInclude namespace is left behind after expansion, strip it (no xi: nodes remain).
    xml_text = xml_text.replace(' xmlns:xi="http://www.w3.org/2001/XInclude"', "")

    return xml_text


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Post-process expanded phyphox XML (strip xml:base and leftover xi namespace)."
    )
    ap.add_argument("file", nargs="?", help="Input file. If omitted, reads stdin.")
    args = ap.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                xml_text = f.read()
        except OSError as e:
            print(f"Error: cannot read {args.file}: {e}", file=sys.stderr)
            return 1
    else:
        try:
            xml_text = sys.stdin.read()
        except OSError as e:
            print(f"Error: cannot read stdin: {e}", file=sys.stderr)
            return 1

    sys.stdout.write(postprocess(xml_text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
