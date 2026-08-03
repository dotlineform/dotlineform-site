#!/usr/bin/env python3
"""Smoke-check shared folder navigation and Docs Import source preference."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class FolderPickerStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        if path == "/docs-viewer/runtime/js/shared-frontend/folder-picker.js":
            path = "/shared/frontend/js/folder-picker.js"
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    handler = partial(FolderPickerStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_shared_folder_picker(page: Page) -> None:
    page.evaluate(
        """async () => {
          const module = await import(
            '/docs-viewer/runtime/js/shared-frontend/folder-picker.js'
          );
          document.body.innerHTML = '<div id="picker"></div>';
          const directories = {
            '.': {
              current_directory: '.',
              current_selectable: false,
              parent_directory: null,
              directories: [{ label: 'projects', source_directory: 'projects' }]
            },
            projects: {
              current_directory: 'projects',
              current_selectable: true,
              parent_directory: '.',
              directories: [
                { label: 'alpha', source_directory: 'projects/alpha' },
                { label: 'broken', source_directory: 'projects/broken' }
              ]
            },
            'projects/alpha': {
              current_directory: 'projects/alpha',
              current_selectable: true,
              parent_directory: 'projects',
              directories: [
                { label: 'empty', source_directory: 'projects/alpha/empty' }
              ]
            },
            'projects/alpha/empty': {
              current_directory: 'projects/alpha/empty',
              current_selectable: true,
              parent_directory: 'projects/alpha',
              directories: []
            }
          };
          const loads = [];
          const errors = [];
          const submits = [];
          window.folderPickerFixture = {
            directories,
            errors,
            loads,
            submits,
            controller: module.createFolderPicker(
              document.getElementById('picker'),
              {
                initialDirectory: 'projects',
                loadDirectory: async ({ directory }) => {
                  loads.push(directory);
                  if (directory === 'projects/broken') {
                    throw new Error('Synthetic folder failure.');
                  }
                  return directories[directory];
                },
                onError: error => errors.push(error.message),
                onSubmit: async ({ directory }) => {
                  submits.push(directory);
                  return directory;
                }
              }
            )
          };
          await window.folderPickerFixture.controller.ready;
        }"""
    )
    assert page.locator("[data-directory]").all_text_contents() == [
        "alpha",
        "broken",
    ]
    assert page.locator('[data-directory][aria-selected="true"]').text_content() == (
        "alpha"
    )
    assert page.locator("[data-breadcrumbs]").text_content() == (
        "Projects/projects"
    )
    assert page.locator('[data-nav="."]').text_content() == "Projects"
    assert page.locator("[data-status]").count() == 0

    page.locator("[data-list]").press("End")
    assert page.locator('[data-directory][aria-selected="true"]').text_content() == (
        "broken"
    )
    page.locator("[data-list]").press("Enter")
    page.wait_for_function(
        "window.folderPickerFixture.errors.length === 1"
    )
    assert page.evaluate("window.folderPickerFixture.controller.getDirectory()") == (
        "projects"
    )
    assert page.evaluate("window.folderPickerFixture.errors") == [
        "Synthetic folder failure."
    ]

    page.locator("[data-list]").press("Home")
    page.locator("[data-list]").press("Enter")
    page.wait_for_function(
        "window.folderPickerFixture.controller.getDirectory() === 'projects/alpha'"
    )
    page.locator("[data-directory]").click()
    page.wait_for_function(
        "window.folderPickerFixture.controller.getDirectory() === 'projects/alpha/empty'"
    )
    assert page.locator(".sharedFolderPicker__empty").text_content() == (
        "No folders in this location."
    )
    assert page.locator("[data-breadcrumbs]").text_content() == (
        "Projects/projects/alpha/empty"
    )
    assert page.locator("[data-nav]").all_text_contents() == [
        "Projects",
        "projects",
        "alpha",
    ]
    assert page.locator("[data-parent]").count() == 0
    page.locator('[data-nav="projects/alpha"]').click()
    page.wait_for_function(
        "window.folderPickerFixture.controller.getDirectory() === 'projects/alpha'"
    )
    page.locator('[data-nav="."]').click()
    page.wait_for_function(
        "window.folderPickerFixture.controller.getDirectory() === '.'"
    )
    try:
        page.evaluate("window.folderPickerFixture.controller.submit()")
    except Exception as error:  # Playwright projects the rejected promise.
        if "Choose a folder below the Projects root" not in str(error):
            raise
    page.locator("[data-directory]").click()
    page.wait_for_function(
        "window.folderPickerFixture.controller.getDirectory() === 'projects'"
    )
    assert page.evaluate(
        """async () => {
          await window.folderPickerFixture.controller.submit();
          return window.folderPickerFixture.submits;
        }"""
    ) == ["projects"]


def assert_import_source_preference(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const module = await import(
            '/docs-viewer/runtime/js/import/docs-import-source-selection.js'
          );
          const values = new Map([
            [module.DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY, 'missing/source']
          ]);
          const storage = {
            getItem: key => values.get(key) || null,
            setItem: (key, value) => values.set(key, value),
            removeItem: key => values.delete(key)
          };
          const directoryRequests = [];
          const candidateRequests = [];
          const payload = directory => ({
            current_directory: directory,
            current_selectable: true,
            parent_directory: '.',
            directories: []
          });
          const controller = module.createDocsImportSourceSelection({
            storage,
            loadDirectory: async ({ directory }) => {
              directoryRequests.push(directory);
              if (directory === 'missing/source') {
                throw new Error('Remembered source is missing.');
              }
              return payload(directory);
            },
            loadCandidates: async ({ directory }) => {
              candidateRequests.push(directory);
              return [];
            },
            openFolderPicker: request => {
              window.sourcePickerRequest = request;
              return true;
            }
          });
          await controller.initialize();
          const checkpoints = [[
            controller.getDirectory(),
            values.get(module.DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY) || ''
          ]];
          await controller.chooseFolder({ id: 'choose' });
          await window.sourcePickerRequest.onSubmit({ directory: 'projects/alpha' });
          checkpoints.push([
            controller.getDirectory(),
            values.get(module.DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY) || ''
          ]);
          await controller.useImportStaging();
          checkpoints.push([
            controller.getDirectory(),
            values.get(module.DOCS_IMPORT_SOURCE_DIRECTORY_STORAGE_KEY) || ''
          ]);
          return {
            checkpoints,
            directoryRequests,
            candidateRequests
          };
        }"""
    )
    assert result == {
        "checkpoints": [
            ["data-sharing/import-staging", ""],
            ["projects/alpha", "projects/alpha"],
            ["data-sharing/import-staging", ""],
        ],
        "directoryRequests": [
            "missing/source",
            "data-sharing/import-staging",
            "projects/alpha",
            "data-sharing/import-staging",
        ],
        "candidateRequests": [
            "data-sharing/import-staging",
            "projects/alpha",
            "data-sharing/import-staging",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    server, base_url = start_static_server(args.site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(base_url, wait_until="domcontentloaded")
                assert_shared_folder_picker(page)
                assert_import_source_preference(page)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print("docs import folder source modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
