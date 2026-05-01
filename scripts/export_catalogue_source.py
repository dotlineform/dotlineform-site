#!/usr/bin/env python3
"""Deprecated workbook-to-catalogue-source export entrypoint."""

from __future__ import annotations


MESSAGE = """Deprecated: scripts/export_catalogue_source.py is retired.
Canonical catalogue source JSON is maintained directly in assets/studio/data/catalogue/.
Use Studio, the configured bulk-import flow, source validation, and scoped JSON build previews instead.
The retired workbook export implementation has been removed so this command cannot recreate source JSON from a historical workbook."""


def main() -> int:
    print(MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
