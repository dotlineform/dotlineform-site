#!/usr/bin/env python3
"""Test wrapper for the catalogue field-registry verifier."""

from __future__ import annotations

import runpy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    runpy.run_path(str(REPO_ROOT / "studio" / "services" / "catalogue" / "verify_catalogue_field_registry.py"), run_name="__main__")


def test_catalogue_field_registry_verifier() -> None:
    main()


if __name__ == "__main__":
    main()
