"""Normalize xmllint XInclude output for committed phyphox artifacts."""

from __future__ import annotations

import re


def postprocess(xml_text: str) -> str:
    """Strip generator-only XML base metadata without changing experiment XML."""

    without_base = re.sub(r'\s+xml:base="[^"]*"', "", xml_text)
    return without_base.replace(' xmlns:xi="http://www.w3.org/2001/XInclude"', "")
