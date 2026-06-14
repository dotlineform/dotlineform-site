#!/usr/bin/env python3
"""Smoke-check Catalogue work editor integration with the shared file picker."""

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
                draft: {
                    project_folder: 'natural',
                    project_subfolder: '',
                    project_filename: 'cover.jpg'
                },
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
                            { project_folder: 'international' },
                            { project_folder: 'natural' },
                            { project_folder: 'nerve' }
                        ]
                    };
                },
                loadProjectFiles: async (request) => {
                    window.__projectMediaCalls.push(['files', request.projectFolder, request.projectSubfolder || '', request.query || '']);
                    if (request.projectFolder === 'natural' && !request.projectSubfolder) {
                        return {
                            ok: true,
                            subfolders: [{ project_subfolder: 'install' }],
                            files: [{ filename: 'cover.jpg' }, { filename: 'direct-02.jpg' }]
                        };
                    }
                    if (request.projectFolder === 'natural' && request.projectSubfolder === 'install') {
                        return {
                            ok: true,
                            subfolders: [{ project_subfolder: 'install' }],
                            files: [{ filename: 'view-01.jpg' }]
                        };
                    }
                    if (request.projectFolder === 'nerve') {
                        return {
                            ok: true,
                            subfolders: [],
                            files: [{ filename: 'nerve - copy.jpg' }, { filename: 'nerve.jpg' }]
                        };
                    }
                    return { ok: true, subfolders: [], files: [] };
                }
            };
            formModule.renderWorkEditorFields(state, {
                fieldsNode: document.getElementById('catalogueWorkFields'),
                readonlyNode: document.getElementById('catalogueWorkReadonly')
            }, options);
            formModule.applyDraftToInputs(state, options);
            window.__projectMediaState = state;
        }"""
    )

    choose_button = page.locator('[data-project-media-choose="work"]')
    assert choose_button.text_content() == "📂"
    assert choose_button.get_attribute("aria-label") == "Choose image..."
    assert page.locator("#catalogueWorkField-project_folder").get_attribute("type") == "hidden"
    assert page.locator('[data-project-media-display="project_folder"]').text_content() == "natural"
    assert page.locator('[data-project-media-display="project_subfolder"]').text_content() == "—"
    assert page.locator('[data-project-media-display="project_filename"]').text_content() == "cover.jpg"

    choose_button.click()
    page.wait_for_selector('[data-role="studio-modal"]')
    assert page.locator("#studioModalTitle").text_content() == "select file"
    folder_input = page.locator('[data-role="file-picker-folder-input"]')
    file_list = page.locator('[data-role="file-picker-file-list"]')
    subfolder_list = page.locator('[data-role="file-picker-subfolder-list"]')
    page.wait_for_selector('[data-role="file-picker-file-list"] option[value="cover.jpg"]')
    assert folder_input.input_value() == "natural"
    assert file_list.input_value() == "cover.jpg"
    assert subfolder_list.evaluate("node => node.selectedIndex") == -1

    folder_input.fill("ner")
    page.wait_for_selector('[data-search-list-value="nerve"]')
    transient_result = page.evaluate(
        """() => ({
            draftProjectFolder: window.__projectMediaState.draft.project_folder,
            modalOpen: Boolean(document.querySelector('[data-role="studio-modal"]')),
            fieldValue: document.querySelector('[data-role="file-picker-folder-input"]').value,
            primaryDisabled: document.querySelector('[data-role="modal-primary"]').disabled
        })"""
    )
    assert transient_result == {
        "draftProjectFolder": "natural",
        "modalOpen": True,
        "fieldValue": "ner",
        "primaryDisabled": True,
    }
    folder_input.press("Escape")
    reset_result = page.evaluate(
        """() => ({
            modalOpen: Boolean(document.querySelector('[data-role="studio-modal"]')),
            fieldValue: document.querySelector('[data-role="file-picker-folder-input"]').value,
            popupHidden: document.querySelector('[data-role="file-picker-folder-popup"]').hidden
        })"""
    )
    assert reset_result == {"modalOpen": True, "fieldValue": "natural", "popupHidden": True}

    folder_input.fill("ner")
    page.wait_for_selector('[data-search-list-value="nerve"]')
    folder_input.press("ArrowDown")
    folder_input.press("Enter")
    page.wait_for_selector('[data-role="file-picker-file-list"] option[value="nerve - copy.jpg"]')
    assert file_list.input_value() == "nerve - copy.jpg"
    wheel_result = page.evaluate(
        """() => {
            const fileList = document.querySelector('[data-role="file-picker-file-list"]');
            const event = new WheelEvent('wheel', { deltaY: 100, bubbles: true, cancelable: true });
            const dispatchResult = fileList.dispatchEvent(event);
            return {
                value: fileList.value,
                defaultPrevented: event.defaultPrevented,
                dispatchResult
            };
        }"""
    )
    assert wheel_result == {"value": "nerve.jpg", "defaultPrevented": True, "dispatchResult": False}
    file_list.press("Enter")
    page.wait_for_selector('[data-role="studio-modal"]', state="detached")

    result = page.evaluate(
        """() => {
            const state = window.__projectMediaState;
            return {
                projectFolder: state.draft.project_folder,
                projectSubfolder: state.draft.project_subfolder,
                projectFilename: state.draft.project_filename,
                folderValue: document.getElementById('catalogueWorkField-project_folder').value,
                subfolderValue: document.getElementById('catalogueWorkField-project_subfolder').value,
                filenameValue: document.getElementById('catalogueWorkField-project_filename').value,
                folderDisplay: document.querySelector('[data-project-media-display="project_folder"]').textContent,
                subfolderDisplay: document.querySelector('[data-project-media-display="project_subfolder"]').textContent,
                filenameDisplay: document.querySelector('[data-project-media-display="project_filename"]').textContent,
                calls: window.__projectMediaCalls
            };
        }"""
    )
    assert result["projectFolder"] == "nerve"
    assert result["projectSubfolder"] == ""
    assert result["projectFilename"] == "nerve.jpg"
    assert result["folderValue"] == "nerve"
    assert result["subfolderValue"] == ""
    assert result["filenameValue"] == "nerve.jpg"
    assert result["folderDisplay"] == "nerve"
    assert result["subfolderDisplay"] == "—"
    assert result["filenameDisplay"] == "nerve.jpg"
    assert ["folders", ""] in result["calls"]
    assert ["files", "natural", "", ""] in result["calls"]
    assert ["files", "nerve", "", ""] in result["calls"]


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
