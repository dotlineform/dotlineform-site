#!/usr/bin/env python3
"""Smoke-check local-folder link browser module boundaries."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    root = site_root.expanduser().resolve()
    handler = partial(QuietStaticHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def browser_contract(page: Page) -> dict[str, object]:
    return page.evaluate(
        r"""async () => {
          const links = await import('/docs-viewer/runtime/js/management/source-editor/local-folder-links.js');
          const editorModule = await import('/docs-viewer/runtime/js/management/source-editor/source-editor.js');
          const basePath = '/configured/base';
          const acceptedInputs = [
            '/configured/base/projects/3 symbols',
            String.raw`/configured/base/projects/3\ symbols`,
            'file:///configured/base/projects/3%20symbols',
            'file://localhost/configured/base/projects/3%20symbols'
          ];
          const accepted = acceptedInputs.map((value) => links.normalizeLocalFolderPath(value, basePath));
          const unicode = links.normalizeLocalFolderPath("/configured/base/München/✓ !'()*~", basePath);
          const rejected = [
            '/outside/base/project', '/configured/base', ' /configured/base/project',
            '/configured/base/project?query', '/configured/base/a/../b',
            'file://remote/configured/base/project', 'file:///configured/base/bad%ZZ',
            '~/project', '$HOME/project', '/configured/base/trailing\\'
          ].map((value) => links.normalizeLocalFolderPath(value, basePath));
          const ordinary = {
            prose: links.markdownRangeIsOrdinary('Before\n\nAfter', 7, 7),
            inline: links.markdownRangeIsOrdinary('`code`', 2, 2),
            fenced: links.markdownRangeIsOrdinary('```\ncode\n```', 5, 5),
            indented: links.markdownRangeIsOrdinary('    code', 5, 5),
            comment: links.markdownRangeIsOrdinary('<!-- secret -->', 6, 6),
            pre: links.markdownRangeIsOrdinary('<pre>secret</pre>', 6, 6)
          };

          const root = document.createElement('div');
          const mount = document.createElement('div');
          root.appendChild(mount);
          document.body.appendChild(root);
          const mode = editorModule.createDocsViewerSourceEditorMode();
          const editorContext = {
            root,
            mount,
            sourceTarget: { scope: 'studio', doc_id: 'doc' },
            documentView: { projectToolbar: () => {}, requestMode: () => {} },
            collectionProvider: {
              readSource: async () => ({
                scope: 'studio', doc_id: 'doc', source_revision: 'sha256:test',
                source_body: 'Before\n\nAfter'
              })
            },
            sourceEditorServices: {
              localFolderLinksCapability: () => ({
                authoring: true, activation: true, base_path: basePath
              })
            }
          };
          await mode.mount(editorContext);
          const textarea = mount.querySelector('textarea');
          textarea.setSelectionRange(7, 7);
          const paste = new Event('paste', { bubbles: true, cancelable: true });
          Object.defineProperty(paste, 'clipboardData', {
            value: { getData: () => '/configured/base/projects/3 symbols' }
          });
          textarea.dispatchEvent(paste);
          const inserted = {
            prevented: paste.defaultPrevented,
            value: textarea.value,
            status: mount.querySelector('.docsViewerSourceEditor__status').textContent,
            dirty: !mount.querySelector('.docsViewerSourceEditor__dirty').hidden
          };
          textarea.value = '`code`';
          textarea.setSelectionRange(2, 2);
          const codePaste = new Event('paste', { bubbles: true, cancelable: true });
          Object.defineProperty(codePaste, 'clipboardData', {
            value: { getData: () => '/configured/base/projects/blocked' }
          });
          textarea.dispatchEvent(codePaste);
          const blocked = { prevented: codePaste.defaultPrevented, value: textarea.value };
          mode.unmount(editorContext);

          const content = document.createElement('div');
          content.innerHTML = '<a href="#" data-docs-viewer-local-target="projects/3%20symbols">Folder</a>';
          document.body.appendChild(content);
          const requests = [], statuses = [];
          window.fetch = async (url, options) => {
            requests.push({ url, method: options.method, body: JSON.parse(options.body) });
            return { ok: true, status: 200, json: async () => ({ ok: true, summary_text: 'Local target opened.' }) };
          };
          const activationContext = {
            content,
            managementService: { baseUrl: 'http://manage.local' },
            setStatus: (message, isError) => statuses.push({ message, isError })
          };
          links.mountLocalFolderLinkActivation(activationContext);
          links.mountLocalFolderLinkActivation(activationContext);
          content.querySelector('a').click();
          await new Promise((resolve) => setTimeout(resolve, 0));
          window.fetch = async (url, options) => {
            requests.push({ url, method: options.method, body: JSON.parse(options.body) });
            return { ok: false, status: 404, json: async () => ({ ok: false, summary_text: 'The local-folder target does not exist.' }) };
          };
          content.querySelector('a').click();
          await new Promise((resolve) => setTimeout(resolve, 0));
          return { accepted, unicode, rejected, ordinary, inserted, blocked, requests, statuses };
        }"""
    )


def assert_contract(result: dict[str, object]) -> None:
    accepted = result["accepted"]
    if any(item["markdown"] != "[3 symbols](dlf-local:projects/3%20symbols)" for item in accepted):
        raise AssertionError(f"supported paste normalization changed: {result!r}")
    if result["unicode"]["encodedTarget"] != "M%C3%BCnchen/%E2%9C%93%20%21%27%28%29%2A~":
        raise AssertionError(f"Unicode target encoding changed: {result!r}")
    if any(item is not None for item in result["rejected"]):
        raise AssertionError(f"unsafe authoring input was recognized: {result!r}")
    if result["ordinary"] != {
        "prose": True, "inline": False, "fenced": False,
        "indented": False, "comment": False, "pre": False,
    }:
        raise AssertionError(f"Markdown context exclusion changed: {result!r}")
    if result["inserted"] != {
        "prevented": True,
        "value": "Before\n[3 symbols](dlf-local:projects/3%20symbols)\nAfter",
        "status": "Local link inserted. Undo to restore the pasted path.",
        "dirty": True,
    }:
        raise AssertionError(f"Source paste insertion changed: {result!r}")
    if result["blocked"] != {"prevented": False, "value": "`code`"}:
        raise AssertionError(f"code-context paste was intercepted: {result!r}")
    expected_request = {
        "url": "http://manage.local/docs/open-local-target",
        "method": "POST",
        "body": {"target": "projects/3%20symbols"},
    }
    if result["requests"] != [expected_request, expected_request]:
        raise AssertionError(f"activation request was not exact or was duplicated: {result!r}")
    if result["statuses"] != [
        {"message": "Local target opened.", "isError": False},
        {"message": "The local-folder target does not exist.", "isError": True},
    ]:
        raise AssertionError(f"activation status handling changed: {result!r}")


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/site/404.html", wait_until="domcontentloaded")
            assert_contract(browser_contract(page))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".")
    args = parser.parse_args()
    run(Path(args.site_root))
    print("Docs Viewer local-folder link modules OK")


if __name__ == "__main__":
    main()
