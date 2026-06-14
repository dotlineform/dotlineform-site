#!/usr/bin/env python3
"""Smoke-check Catalogue project media picker JavaScript modules."""

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


def assert_project_media_picker(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <style>
                .catalogueProjectMediaPicker__folderPopup {
                  display: grid;
                  gap: 4px;
                  max-height: 54px;
                  overflow: auto;
                }
                .catalogueProjectMediaPicker__folderOption {
                  display: block;
                  min-height: 28px;
                }
              </style>
              <main id="catalogueWorkRoot" class="tagStudioPage catalogueWorkPage">
                <div id="catalogueWorkFields" class="tagStudioForm__fields catalogueWorkForm__fields"></div>
                <div id="catalogueWorkReadonly"></div>
              </main>
            `;
            const formModule = await import('/studio/app/frontend/js/catalogue-work-form.js');
            window.__projectMediaCalls = [];
            const state = {
                root: document.getElementById('catalogueWorkRoot'),
                mode: 'single',
                draft: {},
                seriesById: new Map(),
                fieldNodes: new Map(),
                fieldStatusNodes: new Map(),
                readonlyNodes: new Map(),
                bulkTouchedFields: new Set(),
                isSaving: false,
                isBuilding: false,
                isDeleting: false,
                buildPreview: null,
                currentWorkId: '00008',
                currentRecord: { work_id: '00008' },
                serverAvailable: true,
                modalHost: document.createElement('div')
            };
            state.draft.project_folder = 'existing folder';
            state.root.appendChild(state.modalHost);
            const options = {
                text: (_key, fallback) => fallback,
                onFieldInput: (fieldKey) => {
                    const node = state.fieldNodes.get(fieldKey);
                    if (node && 'value' in node) state.draft[fieldKey] = node.value.trim();
                },
                onStateChange: () => {},
                draftHasChanges: () => false,
                loadProjectFolders: async (query) => {
                    window.__projectMediaCalls.push(['folders', query]);
                    return {
                        ok: true,
                        project_folders: [
                            { project_folder: 'a folder 01' },
                            { project_folder: 'a folder 02' },
                            { project_folder: 'a folder 03' },
                            { project_folder: 'a folder 04' },
                            { project_folder: 'a folder 05' },
                            { project_folder: 'a folder 06' },
                            { project_folder: 'a folder 07' },
                            { project_folder: 'a folder 08' },
                            { project_folder: 'a folder 09' },
                            { project_folder: 'a folder 10' },
                            { project_folder: 'a folder 11' },
                            { project_folder: 'a folder 12' },
                            { project_folder: 'natural' },
                            { project_folder: 'international' },
                            { project_folder: 'nerve' }
                        ]
                    };
                },
                loadProjectFiles: async (request) => {
                    window.__projectMediaCalls.push(['files', request.projectFolder, request.projectSubfolder || '', request.query || '']);
                    if (!request.projectSubfolder) {
                        return {
                            ok: true,
                            subfolders: [{ project_subfolder: 'install' }],
                            files: []
                        };
                    }
                    return {
                        ok: true,
                        subfolders: [{ project_subfolder: 'install' }],
                        files: [{ filename: 'view-01.jpg' }]
                    };
                }
            };
            formModule.renderWorkEditorFields(state, {
                fieldsNode: document.getElementById('catalogueWorkFields'),
                readonlyNode: document.getElementById('catalogueWorkReadonly')
            }, options);
            state.fieldNodes.get('project_folder').value = state.draft.project_folder;
            window.__projectMediaState = state;
        }"""
    )
    folder_input = page.locator("#catalogueWorkField-project_folder")
    folder_input.click()
    selection = page.evaluate(
        """() => {
            const input = document.getElementById('catalogueWorkField-project_folder');
            return {
                value: input.value,
                selectionStart: input.selectionStart,
                selectionEnd: input.selectionEnd
            };
        }"""
    )
    assert selection["value"] == "existing folder"
    assert selection["selectionStart"] == 0
    assert selection["selectionEnd"] == len("existing folder")

    folder_input.fill("a")
    page.wait_for_selector('[data-search-list-value="a folder 01"]')
    transient_result = page.evaluate(
        """() => ({
            draftProjectFolder: window.__projectMediaState.draft.project_folder,
            fieldValue: document.getElementById('catalogueWorkField-project_folder').value
        })"""
    )
    assert transient_result == {"draftProjectFolder": "existing folder", "fieldValue": "a"}
    page.locator('[data-search-list-value="a folder 01"]').hover()
    assert page.evaluate("""() => document.getElementById('catalogueProjectFolderPopup').dataset.navigation""") == "pointer"
    folder_input.press("ArrowDown")
    folder_input.press("ArrowDown")
    highlight_result = page.evaluate(
        """() => {
            const popup = document.getElementById('catalogueProjectFolderPopup');
            const first = document.querySelector('[data-search-list-value="a folder 01"]');
            const second = document.querySelector('[data-search-list-value="a folder 02"]');
            return {
                navigation: popup.dataset.navigation,
                selectedCount: popup.querySelectorAll('[aria-selected="true"]').length,
                firstSelected: first.getAttribute('aria-selected'),
                secondSelected: second.getAttribute('aria-selected')
            };
        }"""
    )
    assert highlight_result["navigation"] == "keyboard"
    assert highlight_result["selectedCount"] == 1
    assert highlight_result["firstSelected"] == "false"
    assert highlight_result["secondSelected"] == "true"
    for _ in range(8):
        folder_input.press("ArrowDown")
    scroll_result = page.evaluate(
        """() => {
            const input = document.getElementById('catalogueWorkField-project_folder');
            const popup = document.getElementById('catalogueProjectFolderPopup');
            const active = document.getElementById(input.getAttribute('aria-activedescendant'));
            const popupStyle = window.getComputedStyle(popup);
            const bottomPadding = parseFloat(popupStyle.paddingBottom) || 0;
            const activeRect = active.getBoundingClientRect();
            const popupRect = popup.getBoundingClientRect();
            return {
                active: input.getAttribute('aria-activedescendant'),
                scrollTop: popup.scrollTop,
                activeBottom: activeRect.bottom,
                visibleBottom: popupRect.bottom - bottomPadding,
                selectedCount: popup.querySelectorAll('[aria-selected="true"]').length
            };
        }"""
    )
    assert scroll_result["active"] == "catalogueProjectFolderPopup-option-9"
    assert scroll_result["scrollTop"] > 0
    assert scroll_result["activeBottom"] <= scroll_result["visibleBottom"], scroll_result
    assert scroll_result["selectedCount"] == 1
    folder_input.press("Escape")

    folder_input.fill("nat")
    page.wait_for_selector('[data-search-list-value="natural"]')
    assert page.locator('[data-search-list-value="international"]').count() == 0
    folder_input.press("Escape")
    reset_result = page.evaluate(
        """() => ({
            value: document.getElementById('catalogueWorkField-project_folder').value,
            popupHidden: document.getElementById('catalogueProjectFolderPopup').hidden
        })"""
    )
    assert reset_result == {"value": "existing folder", "popupHidden": True}

    folder_input.fill("nat")
    page.wait_for_selector('[data-search-list-value="natural"]')
    folder_input.press("ArrowDown")
    active_result = page.evaluate(
        """() => ({
            active: document.getElementById('catalogueWorkField-project_folder').getAttribute('aria-activedescendant'),
            selected: document.querySelector('[data-search-list-value="natural"]').getAttribute('aria-selected')
        })"""
    )
    assert active_result["active"] == "catalogueProjectFolderPopup-option-0"
    assert active_result["selected"] == "true"
    folder_input.press("ArrowUp")
    field_result = page.evaluate(
        """() => ({
            active: document.getElementById('catalogueWorkField-project_folder').getAttribute('aria-activedescendant'),
            selected: document.querySelector('[data-search-list-value="natural"]').getAttribute('aria-selected')
        })"""
    )
    assert field_result["active"] is None
    assert field_result["selected"] == "false"

    folder_input.press("ArrowDown")
    folder_input.press("Enter")
    page.wait_for_selector('[data-role="studio-modal"]')
    page.wait_for_selector('[data-project-file="view-01.jpg"]')
    page.locator('[data-project-file="view-01.jpg"]').click()
    page.locator('[data-role="modal-primary"]').click()
    result = page.evaluate(
        """() => {
            const state = window.__projectMediaState;
            return {
                projectFolder: state.draft.project_folder,
                projectSubfolder: state.draft.project_subfolder,
                projectFilename: state.draft.project_filename,
                folderInput: document.getElementById('catalogueWorkField-project_folder').value,
                subfolderInput: document.getElementById('catalogueWorkField-project_subfolder').value,
                filenameInput: document.getElementById('catalogueWorkField-project_filename').value,
                calls: window.__projectMediaCalls
            };
        }"""
    )
    assert result["projectFolder"] == "natural"
    assert result["projectSubfolder"] == "install"
    assert result["projectFilename"] == "view-01.jpg"
    assert result["folderInput"] == "natural"
    assert result["subfolderInput"] == "install"
    assert result["filenameInput"] == "view-01.jpg"
    assert ["folders", ""] in result["calls"]
    assert ["files", "natural", "", ""] in result["calls"]
    assert ["files", "natural", "install", ""] in result["calls"]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_project_media_picker(page)
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
