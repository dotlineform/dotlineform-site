#!/usr/bin/env python3
"""Smoke-check Docs Viewer semantic token picker modules."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_VIEWER_SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"
DOCS_VIEWER_REPO_RUNTIME_PREFIX = "/docs-viewer/runtime/js/"
DOCS_VIEWER_REPO_CSS_PREFIX = "/docs-viewer/static/css/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        if path.startswith(DOCS_VIEWER_SHARED_RUNTIME_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_SHARED_RUNTIME_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "site/docs-viewer/runtime/js/shared" / relative_path)
        if path.startswith(DOCS_VIEWER_REPO_RUNTIME_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_REPO_RUNTIME_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "docs-viewer/runtime/js" / relative_path)
        if path.startswith(DOCS_VIEWER_REPO_CSS_PREFIX):
            relative_path = path.removeprefix(DOCS_VIEWER_REPO_CSS_PREFIX).split("?", 1)[0].split("#", 1)[0]
            return str(REPO_ROOT / "docs-viewer/static/css" / relative_path)
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def install_fixture(page: Page) -> None:
    page.evaluate(
        """async () => {
            const registry = await import('/docs-viewer/runtime/js/management/source-editor/semantic-reference-registry.js');
            const targets = await import('/docs-viewer/runtime/js/management/source-editor/semantic-targets.js');
            const tokenEditor = await import('/docs-viewer/runtime/js/management/source-editor/semantic-token-editor.js');
            const picker = await import('/docs-viewer/runtime/js/management/source-editor/semantic-token-picker-view.js');
            window.__docsViewerSemanticPickerSmoke = { registry, targets, tokenEditor, picker };
        }"""
    )


def assert_helper_modules(page: Page) -> None:
    result = page.evaluate(
        """() => {
            const smoke = window.__docsViewerSemanticPickerSmoke;
            const registry = smoke.registry.normalizeSemanticReferenceRegistry({
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/published/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'series', source_editor: { picker: true, selection_search: true } },
                    { kind: 'work', source_editor: { picker: true, selection_search: true } }
                ]
            });
            const rows = smoke.targets.normalizeSemanticTargets({
                targets: [
                    { kind: 'series', id: '005', title: '3 symbols', meta: ['2007'] },
                    { kind: 'work', id: '00638', title: '3 symbols', meta: ['2007', '3 symbols'] },
                    { kind: 'unknown', id: '1', title: 'Ignored' }
                ]
            }, registry);
            const matches = smoke.targets.collectSemanticTargetMatches(rows, 'symbols', registry, 10);
            return {
                targetLookupUrl: registry.targetLookupUrl,
                rows: rows.map((row) => `${row.kind}:${row.id}`),
                matches: matches.map((row) => `${row.kind}:${row.id}`),
                token: smoke.tokenEditor.buildSemanticReferenceToken(matches[0])
            };
        }"""
    )
    if result != {
        "targetLookupUrl": "/docs-viewer/published/semantic-references/target-lookup.json",
        "rows": ["series:005", "work:00638"],
        "matches": ["series:005", "work:00638"],
        "token": "[[ref:series:005|3 symbols]]",
    }:
        raise AssertionError(f"semantic picker helper contract changed: {result!r}")


def assert_picker_inserts_token(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsViewerSemanticPickerSmoke;
            const mount = document.createElement('div');
            document.body.appendChild(mount);
            const textarea = document.createElement('textarea');
            textarea.value = 'Before symbols after';
            textarea.selectionStart = 7;
            textarea.selectionEnd = 14;
            document.body.appendChild(textarea);
            const selectionListeners = new Set();
            const adapter = {
                focus() {
                    textarea.focus();
                },
                getSelection() {
                    return {
                        start: textarea.selectionStart,
                        end: textarea.selectionEnd,
                        text: textarea.value.slice(textarea.selectionStart, textarea.selectionEnd)
                    };
                },
                onSelectionChange(listener) {
                    selectionListeners.add(listener);
                    return () => selectionListeners.delete(listener);
                },
                replaceSelection(value) {
                    textarea.setRangeText(value, textarea.selectionStart, textarea.selectionEnd, 'end');
                    return true;
                }
            };
            const registryPayload = {
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/published/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'series', source_editor: { picker: true, selection_search: true } },
                    { kind: 'work', source_editor: { picker: true, selection_search: true } }
                ]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_reference_target_lookup_v1',
                targets: [
                    { kind: 'series', id: '005', title: '3 symbols', meta: ['2007'] },
                    { kind: 'work', id: '00638', title: '3 symbols', meta: ['2007', '3 symbols'] }
                ]
            };
            const fakeFetch = async (url) => ({
                ok: true,
                json: async () => String(url).includes('target-lookup') ? targetPayload : registryPayload
            });
            const view = smoke.picker.createSemanticTokenPickerView();
            await view.mount({
                mount,
                fetch: fakeFetch,
                sourceEditorServices: {
                    getActiveSourceEditorContextAdapter() {
                        return adapter;
                    }
                }
            });
            const rowTexts = Array.from(mount.querySelectorAll('[data-target-index]')).map((node) => node.textContent.trim());
            mount.querySelector('[data-target-index="0"]').click();
            return {
                query: mount.querySelector('input').value,
                rowTexts,
                textareaValue: textarea.value,
                status: mount.querySelector('.docsViewerSemanticPicker__status').textContent.trim()
            };
        }"""
    )
    if result["query"] != "symbols":
        raise AssertionError(f"semantic picker did not seed query from selection: {result!r}")
    if result["rowTexts"] != ["3 symbolsseries0052007", "3 symbolswork006382007 · 3 symbols"]:
        raise AssertionError(f"semantic picker rendered unexpected rows: {result!r}")
    if result["textareaValue"] != "Before [[ref:series:005|3 symbols]] after":
        raise AssertionError(f"semantic picker did not insert token: {result!r}")
    if result["status"] != "Inserted series:005.":
        raise AssertionError(f"semantic picker status changed: {result!r}")


def assert_selection_seeded_query_clears_after_source_delete(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsViewerSemanticPickerSmoke;
            const mount = document.createElement('div');
            document.body.appendChild(mount);
            const textarea = document.createElement('textarea');
            textarea.value = 'Before symbols after';
            textarea.selectionStart = 7;
            textarea.selectionEnd = 14;
            document.body.appendChild(textarea);
            const selectionListeners = new Set();
            const adapter = {
                focus() {
                    textarea.focus();
                },
                getSelection() {
                    return {
                        start: textarea.selectionStart,
                        end: textarea.selectionEnd,
                        text: textarea.value.slice(textarea.selectionStart, textarea.selectionEnd)
                    };
                },
                onSelectionChange(listener) {
                    selectionListeners.add(listener);
                    return () => selectionListeners.delete(listener);
                },
                replaceSelection() {
                    return true;
                }
            };
            const registryPayload = {
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/published/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'series', source_editor: { picker: true, selection_search: true } },
                    { kind: 'work', source_editor: { picker: true, selection_search: true } }
                ]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_reference_target_lookup_v1',
                targets: [
                    { kind: 'series', id: '005', title: '3 symbols', meta: ['2007'] },
                    { kind: 'work', id: '00638', title: '3 symbols', meta: ['2007', '3 symbols'] }
                ]
            };
            const fakeFetch = async (url) => ({
                ok: true,
                json: async () => String(url).includes('target-lookup') ? targetPayload : registryPayload
            });
            const view = smoke.picker.createSemanticTokenPickerView();
            await view.mount({
                mount,
                fetch: fakeFetch,
                sourceEditorServices: {
                    getActiveSourceEditorContextAdapter() {
                        return adapter;
                    }
                }
            });
            const input = mount.querySelector('input');
            const seededQuery = input.value;
            textarea.setRangeText('', 7, 14, 'start');
            selectionListeners.forEach((listener) => listener());
            const queryAfterDelete = input.value;
            const rowsAfterDelete = mount.querySelectorAll('[data-target-index]').length;
            const status = mount.querySelector('.docsViewerSemanticPicker__status');
            const statusAfterDelete = status.textContent.trim();
            const statusHiddenAfterDelete = status.hidden;
            input.value = 'symbols';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            selectionListeners.forEach((listener) => listener());
            return {
                seededQuery,
                queryAfterDelete,
                rowsAfterDelete,
                statusAfterDelete,
                statusHiddenAfterDelete,
                manualQueryAfterEmptySelection: input.value,
                manualRowsAfterEmptySelection: mount.querySelectorAll('[data-target-index]').length
            };
        }"""
    )
    if result["seededQuery"] != "symbols":
        raise AssertionError(f"semantic picker did not seed query before delete: {result!r}")
    if result["queryAfterDelete"] != "":
        raise AssertionError(f"semantic picker did not clear selection-seeded query after delete: {result!r}")
    if result["rowsAfterDelete"] != 0:
        raise AssertionError(f"semantic picker did not clear rows after selection delete: {result!r}")
    if result["statusAfterDelete"] != "" or not result["statusHiddenAfterDelete"]:
        raise AssertionError(f"semantic picker clear status changed: {result!r}")
    if result["manualQueryAfterEmptySelection"] != "symbols" or result["manualRowsAfterEmptySelection"] != 2:
        raise AssertionError(f"semantic picker cleared manual query after empty selection: {result!r}")


def assert_picker_inserts_token_at_caret(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const smoke = window.__docsViewerSemanticPickerSmoke;
            const mount = document.createElement('div');
            document.body.appendChild(mount);
            const textarea = document.createElement('textarea');
            textarea.value = 'Before  after';
            textarea.selectionStart = 7;
            textarea.selectionEnd = 7;
            document.body.appendChild(textarea);
            const adapter = {
                focus() {
                    textarea.focus();
                },
                getSelection() {
                    return {
                        start: textarea.selectionStart,
                        end: textarea.selectionEnd,
                        text: textarea.value.slice(textarea.selectionStart, textarea.selectionEnd)
                    };
                },
                onSelectionChange() {
                    return () => {};
                },
                replaceSelection(value) {
                    textarea.setRangeText(value, textarea.selectionStart, textarea.selectionEnd, 'end');
                    return true;
                }
            };
            const registryPayload = {
                schema_version: 'docs_semantic_reference_registry_v1',
                target_lookup_url: '/docs-viewer/published/semantic-references/target-lookup.json',
                kinds: [
                    { kind: 'series', source_editor: { picker: true, selection_search: true } },
                    { kind: 'work', source_editor: { picker: true, selection_search: true } }
                ]
            };
            const targetPayload = {
                schema_version: 'docs_semantic_reference_target_lookup_v1',
                targets: [
                    { kind: 'series', id: '005', title: '3 symbols', meta: ['2007'] },
                    { kind: 'work', id: '00638', title: '3 symbols', meta: ['2007', '3 symbols'] }
                ]
            };
            const fakeFetch = async (url) => ({
                ok: true,
                json: async () => String(url).includes('target-lookup') ? targetPayload : registryPayload
            });
            const view = smoke.picker.createSemanticTokenPickerView();
            await view.mount({
                mount,
                fetch: fakeFetch,
                sourceEditorServices: {
                    getActiveSourceEditorContextAdapter() {
                        return adapter;
                    }
                }
            });
            const input = mount.querySelector('input');
            input.value = 'symbols';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            mount.querySelector('[data-target-index="0"]').click();
            return {
                rowTexts: Array.from(mount.querySelectorAll('[data-target-index]')).map((node) => node.textContent.trim()),
                textareaValue: textarea.value,
                status: mount.querySelector('.docsViewerSemanticPicker__status').textContent.trim()
            };
        }"""
    )
    if result["rowTexts"] != ["3 symbolsseries0052007", "3 symbolswork006382007 · 3 symbols"]:
        raise AssertionError(f"semantic picker rendered unexpected caret rows: {result!r}")
    if result["textareaValue"] != "Before [[ref:series:005|3 symbols]] after":
        raise AssertionError(f"semantic picker did not insert token at caret: {result!r}")
    if result["status"] != "Inserted series:005.":
        raise AssertionError(f"semantic picker caret status changed: {result!r}")


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
    install_fixture(page)
    assert_helper_modules(page)
    assert_picker_inserts_token(page)
    assert_selection_seeded_query_clears_after_source_delete(page)
    assert_picker_inserts_token_at_caret(page)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=Path("."))
    parser.add_argument("--timeout-ms", type=int, default=10000)
    args = parser.parse_args()

    server, base_url = start_static_server(args.site_root)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_default_timeout(args.timeout_ms)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                run_smoke(page, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        raise AssertionError(f"page errors during Docs Viewer semantic picker module smoke: {errors!r}")
    print("Docs Viewer semantic token picker modules OK")


if __name__ == "__main__":
    main()
