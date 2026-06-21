#!/usr/bin/env python3
"""Smoke-check Local Studio serves its own shell and keeps Docs Viewer assets out."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_http_status(url: str, expected_status: int) -> None:
    try:
        urllib.request.urlopen(url, timeout=10)
    except urllib.error.HTTPError as error:
        if error.code != expected_status:
            raise AssertionError(f"expected {expected_status} for {url}, got {error.code}") from error
        return
    raise AssertionError(f"expected {expected_status} for {url}, got 200")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        assert_http_status(f"{base_url}/docs/?scope=studio&doc=docs-viewer", 404)
        assert_http_status(f"{base_url}/docs-viewer/runtime/js/docs-viewer.js", 404)
        assert_http_status(f"{base_url}/docs-viewer/static/css/docs-viewer.css", 404)
        assert_http_status(f"{base_url}/assets/docs/interactive/library/coincidence-salience.html", 404)

        with urllib.request.urlopen(f"{base_url}/studio/", timeout=10) as response:
            body = response.read().decode("utf-8")
        if "docsViewerRoot" in body:
            raise AssertionError("Local Studio home unexpectedly contains Docs Viewer shell markup")

        with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
            runtime_config = json.loads(response.read().decode("utf-8"))
        if "docs" in runtime_config["app"]["runtime"]["services"]:
            raise AssertionError("Local Studio unexpectedly exposed Docs Viewer service endpoints")
        if "external_links" in runtime_config:
            raise AssertionError("Local Studio unexpectedly exposed Docs Viewer external link config")

        print(f"local Studio Docs Viewer boundary OK: {base_url}/studio/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
