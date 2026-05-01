#!/usr/bin/env python3
"""Deprecated workbook-to-JSON source comparison entrypoint."""

from __future__ import annotations


MESSAGE = """Deprecated: scripts/compare_catalogue_sources.py is retired.
The retired workbook source is not part of the live catalogue workflow.
Use `./scripts/validate_catalogue_source.py` and scoped JSON build previews to verify current canonical source records.
The retired workbook comparison implementation has been removed so this command cannot preserve a parallel workbook-source contract."""


def main() -> int:
    print(MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
