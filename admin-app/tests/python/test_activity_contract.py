#!/usr/bin/env python3
"""Test wrapper for the Studio activity contract verifier."""

from __future__ import annotations

import runpy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    runpy.run_path(str(REPO_ROOT / "studio" / "checks" / "verify_activity_contract.py"), run_name="__main__")


def test_activity_contract_verifier() -> None:
    main()


if __name__ == "__main__":
    main()
