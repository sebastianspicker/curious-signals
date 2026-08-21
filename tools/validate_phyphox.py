#!/usr/bin/env python3
from __future__ import annotations

from phyphox_repo_contracts import main
from phyphox_xml_contracts import ValidationError, validate_phyphox

__all__ = ["ValidationError", "validate_phyphox", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
