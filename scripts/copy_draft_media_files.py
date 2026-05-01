#!/usr/bin/env python3
"""Deprecated workbook-led draft media copy entrypoint."""

from __future__ import annotations


MESSAGE = """Deprecated: scripts/copy_draft_media_files.py is no longer part of the live catalogue workflow.
Media preparation is no longer orchestrated from the retired workbook-led pipeline.
Use current Studio/build guidance for source JSON changes and media-specific work.
The retired workbook-led implementation has been removed so this command cannot run hidden compatibility copying."""


def main() -> int:
    print(MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
