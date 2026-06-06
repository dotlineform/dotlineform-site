#!/usr/bin/env python3
"""Audit a built public site against the projection contract manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audit_projection_contract import (
    DEFAULT_CONTRACT_PATH,
    ProjectionContractError,
    audit_public_build,
    load_contract,
    print_failures,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-root",
        default="_site",
        help="Built site root to audit. Defaults to _site.",
    )
    parser.add_argument(
        "--contract",
        default=DEFAULT_CONTRACT_PATH,
        type=Path,
        help="Projection contract manifest path.",
    )
    args = parser.parse_args(argv)

    contract_path = args.contract if args.contract.is_absolute() else Path.cwd() / args.contract
    try:
        contract = load_contract(contract_path)
    except (OSError, ValueError, ProjectionContractError) as exc:
        print(f"FAIL: projection contract invalid: {exc}", file=sys.stderr)
        return 1

    failures = audit_public_build(Path(args.site_root), contract)
    if failures:
        print_failures(failures)
        return 1

    print(f"public build surface OK: {Path(args.site_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
