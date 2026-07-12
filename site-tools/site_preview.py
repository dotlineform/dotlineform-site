#!/usr/bin/env python3
"""Serve the tracked public site while ignoring normal client disconnects."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer, test
from pathlib import Path


class SitePreviewRequestHandler(SimpleHTTPRequestHandler):
    def copyfile(self, source: object, outputfile: object) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the tracked public site")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4000)
    parser.add_argument("--directory", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    directory = str(args.directory.resolve())

    class RootedSitePreviewRequestHandler(SitePreviewRequestHandler):
        def __init__(self, *handler_args: object, **handler_kwargs: object) -> None:
            super().__init__(*handler_args, directory=directory, **handler_kwargs)

    test(
        HandlerClass=RootedSitePreviewRequestHandler,
        ServerClass=ThreadingHTTPServer,
        port=args.port,
        bind=args.host,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
