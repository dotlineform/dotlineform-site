#!/usr/bin/env python3
"""Smoke-check inline Mermaid on an isolated external-local manage route."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
NOTES_DIAGRAM_DOC_ID = "d-20260724-131900-a1b2c3"
NOTES_PLAIN_DOC_ID = "d-20260724-131901-d4e5f6"
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


def prepare_notes_scope(projects_base: Path) -> Path:
    notes_root = projects_base / "docs-viewer/scopes/notes"
    documents_root = notes_root / "source/documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    (documents_root / f"{NOTES_PLAIN_DOC_ID}.md").write_text(
        source_text(
            doc_id=NOTES_PLAIN_DOC_ID,
            title="External Notes Without Diagram",
            body="# External Notes Without Diagram\n\nThis document has no Mermaid fence.",
        ),
        encoding="utf-8",
    )
    (documents_root / f"{NOTES_DIAGRAM_DOC_ID}.md").write_text(
        source_text(
            doc_id=NOTES_DIAGRAM_DOC_ID,
            title="External Notes Mermaid Proof",
            body="""# External Notes Mermaid Proof

Before the diagram.

```mermaid
flowchart LR
  accTitle: External local runtime proof
  accDescr: An external local Notes document renders through the managed reader
  Source --> Target
```

After the diagram.
""",
        ),
        encoding="utf-8",
    )
    return notes_root


def build_notes_scope() -> None:
    build_root = REPO_ROOT / "docs-viewer/build"
    services_root = REPO_ROOT / "docs-viewer/services"
    for path in (REPO_ROOT, build_root, services_root):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    from docs_builder.pipeline import DocsDataBuilder  # noqa: PLC0415
    from docs_scope_config import load_docs_scope_configs  # noqa: PLC0415

    config = load_docs_scope_configs(REPO_ROOT, scope_ids=("notes",))["notes"]
    DocsDataBuilder(repo_root=REPO_ROOT, config=config).run(write=True)


def assert_diagram_free_external_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
    mermaid_requests: list[str],
    wait_for_manage_doc,
    *,
    expected_mermaid_requests: int,
) -> None:
    page.goto(
        f"{base_url}/docs/?scope=notes&doc={NOTES_PLAIN_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, "External Notes Without Diagram", timeout_ms)
    state = page.locator("#docsViewerContent").evaluate(
        """content => ({
            diagrams: content.querySelectorAll(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            ).length,
            fences: content.querySelectorAll('pre > code.language-mermaid').length
        })"""
    )
    if state != {"diagrams": 0, "fences": 0}:
        raise AssertionError(f"diagram-free external-local document changed: {state!r}")
    if len(mermaid_requests) != expected_mermaid_requests:
        raise AssertionError(
            f"diagram-free external-local document loaded Mermaid: {mermaid_requests!r}"
        )


def assert_external_mermaid_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
    mermaid_requests: list[str],
    wait_for_manage_doc,
) -> None:
    page.goto(
        f"{base_url}/docs/?scope=notes&doc={NOTES_DIAGRAM_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, "External Notes Mermaid Proof", timeout_ms)
    page.wait_for_function(
        """() => {
            const content = document.querySelector('#docsViewerContent');
            const host = content?.querySelector(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            );
            return host?.querySelector(':scope > svg')
                && host.closest('.docsViewer__diagramFrame')
                    ?.querySelector('.docsViewer__diagramDetailControl');
        }""",
        timeout=timeout_ms,
    )
    state = page.locator("#docsViewerContent").evaluate(
        """content => {
            const host = content.querySelector(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            );
            const svg = host?.querySelector(':scope > svg');
            const frame = host?.closest('.docsViewer__diagramFrame');
            const control = frame?.querySelector('.docsViewer__diagramDetailControl');
            return {
                diagrams: content.querySelectorAll(
                    '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
                ).length,
                fences: content.querySelectorAll('pre > code.language-mermaid').length,
                failures: content.querySelectorAll('.docsViewer__diagramError').length,
                title: svg?.querySelector('title')?.textContent.trim() || '',
                description: svg?.querySelector('desc')?.textContent.trim() || '',
                frameKind: frame?.dataset.docsViewerDiagramFrame || '',
                controlKind: control?.dataset.docsViewerDiagramDetailKind || '',
                controlLabel: control?.getAttribute('aria-label') || '',
                controlTag: control?.tagName || '',
                controlTarget: control?.getAttribute('target') || '',
                controlHref: control?.getAttribute('href') || ''
            };
        }"""
    )
    if (
        state["diagrams"] != 1
        or state["fences"] != 0
        or state["failures"] != 0
        or state["title"] != "External local runtime proof"
        or not str(state["description"]).startswith("An external local Notes document")
        or state["frameKind"] != "inline-mermaid"
        or state["controlKind"] != "inline-mermaid"
        or state["controlLabel"] != "Open diagram"
        or state["controlTag"] != "BUTTON"
        or state["controlTarget"] != ""
        or state["controlHref"] != ""
    ):
        raise AssertionError(
            f"external-local Mermaid did not receive the managed reader contract: {state!r}"
        )
    paths = [urlparse(url).path for url in mermaid_requests]
    if paths != [MERMAID_ASSET_PATH]:
        raise AssertionError(
            f"external-local Mermaid did not load exactly one checked asset: {paths!r}"
        )


def run_route_smoke(
    page: Page,
    base_url: str,
    timeout_ms: int,
    wait_for_manage_doc,
) -> None:
    mermaid_requests: list[str] = []
    page.on(
        "request",
        lambda request: mermaid_requests.append(request.url)
        if "/docs-viewer/runtime/vendor/mermaid/" in request.url
        else None,
    )
    assert_diagram_free_external_route(
        page,
        base_url,
        timeout_ms,
        mermaid_requests,
        wait_for_manage_doc,
        expected_mermaid_requests=0,
    )
    assert_external_mermaid_route(
        page,
        base_url,
        timeout_ms,
        mermaid_requests,
        wait_for_manage_doc,
    )
    assert_diagram_free_external_route(
        page,
        base_url,
        timeout_ms,
        mermaid_requests,
        wait_for_manage_doc,
        expected_mermaid_requests=1,
    )
    if [urlparse(url).path for url in mermaid_requests] != [MERMAID_ASSET_PATH]:
        raise AssertionError(
            f"external-local navigation did not reuse the Mermaid session: {mermaid_requests!r}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    previous_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    with TemporaryDirectory(prefix="docs-viewer-external-mermaid-") as temporary_directory:
        projects_base = Path(temporary_directory) / "Projects"
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_base)
        notes_root = prepare_notes_scope(projects_base)
        try:
            build_notes_scope()
            from docs_viewer_service_manage import (  # noqa: PLC0415
                start_server,
                wait_for_manage_doc,
            )

            server, base_url = start_server()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    errors: list[str] = []
                    try:
                        page = browser.new_page(viewport={"width": 1280, "height": 900})
                        page.on("pageerror", lambda error: errors.append(error.stack or str(error)))
                        run_route_smoke(
                            page,
                            base_url,
                            args.timeout_ms,
                            wait_for_manage_doc,
                        )
                    finally:
                        browser.close()
                if errors:
                    raise AssertionError(
                        f"page errors during external-local inline Mermaid smoke: {errors!r}"
                    )
            finally:
                server.shutdown()
                server.server_close()

            persistent_derivatives = [
                path.relative_to(notes_root).as_posix()
                for suffix in ("*.mmd", "*.svg")
                for path in notes_root.rglob(suffix)
            ]
            if persistent_derivatives:
                raise AssertionError(
                    f"inline Mermaid created persistent media: {persistent_derivatives!r}"
                )
        finally:
            if previous_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = previous_projects_base

    print("Docs Viewer external-local inline Mermaid route smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
