"""Small shared harness for retained Docs Viewer route-boundary smokes."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from threading import Thread

from playwright.sync_api import Page


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


def start_docs_viewer_server(
    *,
    review_enabled: bool = False,
) -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=False,
        review_enabled=review_enabled,
    )
    server = DocsViewerServer(("127.0.0.1", 0), REPO_ROOT, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(
        config,
        port=server.server_address[1],
        base_url=base_url,
    )
    Thread(target=server.serve_forever, daemon=True).start()
    return server, base_url


def wait_for_document(
    page: Page,
    title: str,
    timeout_ms: int,
) -> None:
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_function(
        """expectedTitle => document.querySelector('#docsViewerContent h1')
            ?.textContent.trim() === expectedTitle""",
        arg=title,
        timeout=timeout_ms,
    )
