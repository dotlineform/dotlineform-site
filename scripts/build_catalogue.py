#!/usr/bin/env python3
"""Deprecated workbook-led catalogue build entrypoint."""

from __future__ import annotations


MESSAGE = """Deprecated: scripts/build_catalogue.py is no longer part of the live catalogue workflow.
Use Studio catalogue pages to edit canonical JSON source records.
Use `./scripts/catalogue_json_build.py --work-id <work_id> [--write]` for scoped runtime rebuilds.
The retired workbook-led implementation has been removed so this command cannot run a hidden compatibility pipeline."""


def main() -> int:
    print(MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
