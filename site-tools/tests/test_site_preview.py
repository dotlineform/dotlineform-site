#!/usr/bin/env python3
"""Focused checks for the public-site preview handler."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys

import pytest


SITE_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(SITE_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SITE_TOOLS_ROOT))

from site_preview import SitePreviewRequestHandler  # noqa: E402


class DisconnectingOutput:
    def __init__(self, error: OSError) -> None:
        self.error = error

    def write(self, _chunk: bytes) -> None:
        raise self.error


@pytest.mark.parametrize("error", [BrokenPipeError(), ConnectionResetError()])
def test_copyfile_ignores_client_disconnects(error: OSError) -> None:
    handler = object.__new__(SitePreviewRequestHandler)

    handler.copyfile(BytesIO(b"response"), DisconnectingOutput(error))


def test_copyfile_preserves_unexpected_io_errors() -> None:
    handler = object.__new__(SitePreviewRequestHandler)

    with pytest.raises(OSError, match="unexpected"):
        handler.copyfile(BytesIO(b"response"), DisconnectingOutput(OSError("unexpected")))
