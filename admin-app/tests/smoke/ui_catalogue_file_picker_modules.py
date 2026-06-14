#!/usr/bin/env python3
"""Smoke-check the shared File Picker JavaScript component contract."""

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
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_file_picker_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <style>
                .sharedSearchList__popup {
                  display: grid;
                  gap: 4px;
                  max-height: 64px;
                  overflow: auto;
                  padding: 4px 4px 8px;
                }
                .sharedSearchList__option {
                  border: 0;
                  display: block;
                  min-height: 28px;
                  width: 100%;
                }
              </style>
              <button id="primary" disabled>ok</button>
              <div id="picker"></div>
              <button id="missingPrimary" disabled>ok</button>
              <div id="missingPicker"></div>
            `;
            const module = await import('/shared/frontend/js/file-picker.js');
            const calls = [];
            const primary = document.getElementById('primary');
            let submitCount = 0;
            const picker = module.createFilePicker(document.getElementById('picker'), {
                id: 'filePickerSmoke',
                primaryNode: primary,
                initialSelection: { folder: 'natural', subfolder: 'install', filename: 'view-01.jpg' },
                loadFolders: async () => {
                    calls.push(['folders']);
                    return ['natural', 'nerve'];
                },
                loadFiles: async ({ folder, subfolder }) => {
                    calls.push(['files', folder, subfolder || '']);
                    if (folder === 'natural' && !subfolder) {
                        return {
                            subfolders: [{ subfolder: 'install' }, { subfolder: 'proof' }],
                            files: [{ filename: 'cover.jpg' }]
                        };
                    }
                    if (folder === 'natural' && subfolder === 'install') {
                        return {
                            subfolders: [{ subfolder: 'install' }, { subfolder: 'proof' }],
                            files: [{ filename: 'view-01.jpg' }]
                        };
                    }
                    if (folder === 'natural' && subfolder === 'proof') {
                        return {
                            subfolders: [{ subfolder: 'install' }, { subfolder: 'proof' }],
                            files: [{ filename: 'proof.jpg' }]
                        };
                    }
                    if (folder === 'nerve') {
                        return {
                            subfolders: [],
                            files: [{ filename: 'nerve - copy.jpg' }, { filename: 'nerve.jpg' }]
                        };
                    }
                    return { subfolders: [], files: [] };
                },
                onSubmit: () => {
                    submitCount += 1;
                }
            });
            await picker.ready;
            const initial = {
                folder: document.querySelector('#picker [data-role="file-picker-folder-input"]').value,
                subfolder: document.querySelector('#picker [data-role="file-picker-subfolder-list"]').value,
                filename: document.querySelector('#picker [data-role="file-picker-file-list"]').value,
                primaryDisabled: primary.disabled,
                submit: picker.submit()
            };

            const subfolderList = document.querySelector('#picker [data-role="file-picker-subfolder-list"]');
            const subfolderWheelEvent = new WheelEvent('wheel', { deltaY: 100, bubbles: true, cancelable: true });
            const subfolderWheelDispatch = subfolderList.dispatchEvent(subfolderWheelEvent);
            await new Promise((resolve) => setTimeout(resolve, 0));
            const afterSubfolderWheel = {
                subfolder: subfolderList.value,
                filename: document.querySelector('#picker [data-role="file-picker-file-list"]').value,
                defaultPrevented: subfolderWheelEvent.defaultPrevented,
                dispatchResult: subfolderWheelDispatch
            };

            const folderInput = document.querySelector('#picker [data-role="file-picker-folder-input"]');
            folderInput.focus();
            folderInput.value = 'ner';
            folderInput.dispatchEvent(new Event('input', { bubbles: true }));
            await picker.ready;
            await new Promise((resolve) => setTimeout(resolve, 0));
            const prefixMatches = Array.from(document.querySelectorAll('#picker [data-search-list-value]')).map((node) => node.dataset.searchListValue);
            const transientPrimaryDisabled = primary.disabled;
            folderInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, cancelable: true }));
            folderInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
            await new Promise((resolve) => setTimeout(resolve, 0));
            const fileList = document.querySelector('#picker [data-role="file-picker-file-list"]');
            const afterFolderCommit = {
                folder: folderInput.value,
                filename: fileList.value,
                primaryDisabled: primary.disabled
            };
            fileList.dispatchEvent(new WheelEvent('wheel', { deltaY: 100, bubbles: true, cancelable: true }));
            fileList.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
            const afterWheel = {
                filename: fileList.value,
                submitCount,
                submit: picker.submit()
            };

            const missingPrimary = document.getElementById('missingPrimary');
            const missingPicker = module.createFilePicker(document.getElementById('missingPicker'), {
                id: 'filePickerMissingSmoke',
                primaryNode: missingPrimary,
                initialSelection: { folder: 'missing', filename: 'gone.jpg' },
                loadFolders: async () => ['natural'],
                loadFiles: async () => ({ subfolders: [], files: [] })
            });
            await missingPicker.ready;
            const missing = {
                folder: document.querySelector('#missingPicker [data-role="file-picker-folder-input"]').value,
                status: document.querySelector('#missingPicker [data-role="file-picker-status"]').textContent,
                primaryDisabled: missingPrimary.disabled,
                submit: missingPicker.submit()
            };

            return {
                afterFolderCommit,
                afterSubfolderWheel,
                afterWheel,
                calls,
                initial,
                missing,
                prefixMatches,
                transientPrimaryDisabled
            };
        }"""
    )
    assert result["initial"]["folder"] == "natural"
    assert result["initial"]["subfolder"] == "install"
    assert result["initial"]["filename"] == "view-01.jpg"
    assert result["initial"]["primaryDisabled"] is False
    assert result["initial"]["submit"]["selection"] == {
        "scope": "",
        "folder": "natural",
        "subfolder": "install",
        "filename": "view-01.jpg",
    }
    assert result["afterSubfolderWheel"] == {
        "subfolder": "proof",
        "filename": "proof.jpg",
        "defaultPrevented": True,
        "dispatchResult": False,
    }
    assert result["prefixMatches"] == ["nerve"]
    assert result["transientPrimaryDisabled"] is True
    assert result["afterFolderCommit"] == {
        "folder": "nerve",
        "filename": "nerve - copy.jpg",
        "primaryDisabled": False,
    }
    assert result["afterWheel"]["filename"] == "nerve.jpg"
    assert result["afterWheel"]["submitCount"] == 1
    assert result["afterWheel"]["submit"]["selection"] == {
        "scope": "",
        "folder": "nerve",
        "subfolder": "",
        "filename": "nerve.jpg",
    }
    assert result["missing"]["folder"] == ""
    assert result["missing"]["status"] == "file not found"
    assert result["missing"]["primaryDisabled"] is True
    assert result["missing"]["submit"]["ok"] is False
    assert ["files", "natural", ""] in result["calls"]
    assert ["files", "natural", "install"] in result["calls"]
    assert ["files", "nerve", ""] in result["calls"]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_file_picker_contract(page)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()
