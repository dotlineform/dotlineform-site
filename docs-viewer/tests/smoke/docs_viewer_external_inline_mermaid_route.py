#!/usr/bin/env python3
"""Smoke-check external-local route loading and lazy Mermaid rendering."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
DIAGRAM_DOC_ID = "d-20260724-131900-a1b2c3"
PLAIN_DOC_ID = "d-20260724-131901-d4e5f6"
MERMAID_ASSET_PATH = "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js"


def source_text(*, doc_id: str, title: str, body: str) -> str:
    return f"""---
doc_id: {doc_id}
title: {title}
added_date: "2026-07-24 13:19:00"
last_updated: "2026-07-24 13:19:00"
ui_status: in-progress
parent_id: ""
---
{body}
"""


def prepare_external_scope(projects_base: Path) -> None:
    documents_root = projects_base / "docs-viewer/scopes/notes/source/documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    (projects_base / "docs-viewer/media").mkdir(parents=True, exist_ok=True)
    (documents_root / f"{PLAIN_DOC_ID}.md").write_text(
        source_text(
            doc_id=PLAIN_DOC_ID,
            title="External Notes Without Diagram",
            body="# External Notes Without Diagram\n\nThis document has no Mermaid fence.",
        ),
        encoding="utf-8",
    )
    (documents_root / f"{DIAGRAM_DOC_ID}.md").write_text(
        source_text(
            doc_id=DIAGRAM_DOC_ID,
            title="External Notes Mermaid Proof",
            body="""# External Notes Mermaid Proof

```mermaid
flowchart LR
  Source --> Target
```
""",
        ),
        encoding="utf-8",
    )


def build_external_scope() -> None:
    for path in (
        REPO_ROOT,
        REPO_ROOT / "docs-viewer/build",
        REPO_ROOT / "docs-viewer/services",
    ):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    from docs_builder.pipeline import DocsDataBuilder  # noqa: PLC0415
    from docs_scope_config import load_docs_scope_configs  # noqa: PLC0415

    config = load_docs_scope_configs(REPO_ROOT, scope_ids=("notes",))["notes"]
    DocsDataBuilder(repo_root=REPO_ROOT, config=config).run(write=True)


def assert_plain_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
    mermaid_requests: list[str],
    wait_for_document,
) -> None:
    page.goto(
        f"{base_url}/docs/?scope=notes&doc={PLAIN_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_document(page, "External Notes Without Diagram", timeout_ms)
    if page.locator(".docsViewer__diagram[data-docs-viewer-diagram-kind='inline-mermaid']").count():
        raise AssertionError("plain external-local document rendered an inline Mermaid host")
    if mermaid_requests:
        raise AssertionError(f"plain external-local document loaded Mermaid: {mermaid_requests!r}")


def assert_mermaid_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
    mermaid_requests: list[str],
    wait_for_document,
) -> None:
    page.goto(
        f"{base_url}/docs/?scope=notes&doc={DIAGRAM_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_document(page, "External Notes Mermaid Proof", timeout_ms)
    page.wait_for_function(
        """() => document.querySelector(
            '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"] > svg'
        )""",
        timeout=timeout_ms,
    )
    state = page.locator("#docsViewerContent").evaluate(
        """content => ({
            diagrams: content.querySelectorAll(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            ).length,
            errors: content.querySelectorAll('.docsViewer__diagramError').length,
            fences: content.querySelectorAll('pre > code.language-mermaid').length,
            svgs: content.querySelectorAll(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"] > svg'
            ).length
        })"""
    )
    if state != {"diagrams": 1, "errors": 0, "fences": 0, "svgs": 1}:
        raise AssertionError(f"external-local Mermaid did not render: {state!r}")
    paths = [urlparse(url).path for url in mermaid_requests]
    if paths != [MERMAID_ASSET_PATH]:
        raise AssertionError(f"external-local Mermaid asset requests changed: {paths!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    previous_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    with TemporaryDirectory(prefix="docs-viewer-external-mermaid-") as temporary_directory:
        projects_base = Path(temporary_directory) / "Projects"
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_base)
        prepare_external_scope(projects_base)
        try:
            build_external_scope()
            from docs_viewer_route_smoke_support import (  # noqa: PLC0415
                start_docs_viewer_server,
                wait_for_document,
            )

            server, base_url = start_docs_viewer_server()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    errors: list[str] = []
                    try:
                        page = browser.new_page(viewport={"width": 1280, "height": 900})
                        page.on("pageerror", lambda error: errors.append(error.stack or str(error)))
                        mermaid_requests: list[str] = []
                        page.on(
                            "request",
                            lambda request: mermaid_requests.append(request.url)
                            if "/docs-viewer/runtime/vendor/mermaid/" in request.url
                            else None,
                        )
                        assert_plain_route(
                            page,
                            base_url,
                            args.timeout_ms,
                            mermaid_requests,
                            wait_for_document,
                        )
                        assert_mermaid_route(
                            page,
                            base_url,
                            args.timeout_ms,
                            mermaid_requests,
                            wait_for_document,
                        )
                    finally:
                        browser.close()
                if errors:
                    raise AssertionError(f"page errors during external-local route smoke: {errors!r}")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            if previous_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = previous_projects_base

    print("Docs Viewer external-local Mermaid boundary OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
