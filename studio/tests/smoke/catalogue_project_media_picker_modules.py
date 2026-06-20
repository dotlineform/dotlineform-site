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
              <main id="catalogueWorkRoot" class="studioPage catalogueWorkPage">
                <div id="catalogueWorkFields" class="studioForm__fields catalogueWorkForm__fields"></div>
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
                text: (key, fallback) => {
                    if (key === 'entry_modal_cancel_button') return 'Cancel from ui-text';
                    if (key === 'project_media_modal_title') return 'Title from ui-text';
                    if (key === 'project_media_select_button') return 'Save from ui-text';
                    return fallback;
                },
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
    assert page.locator('button[data-role="modal-cancel"]').text_content() == "cancel"
    assert page.locator('button[data-role="modal-primary"]').text_content() == "ok"
    folder_input = page.locator('[data-role="file-picker-folder-input"]')
    file_list = page.locator('[data-role="file-picker-file-list"]')
    subfolder_list = page.locator('[data-role="file-picker-subfolder-list"]')
    page.wait_for_selector('[data-role="file-picker-file-list"] [data-listbox-option-value="cover.jpg"]')
    page.wait_for_function(
        "() => document.activeElement && document.activeElement.dataset.role === 'file-picker-file-list'"
    )
    assert folder_input.input_value() == "natural"
    assert file_list.evaluate("node => node.dataset.selectedValue") == "cover.jpg"
    assert subfolder_list.evaluate("node => node.dataset.selectedValue || ''") == ""
    assert page.locator(".sharedFilePicker__label").count() == 0
    open_focus_result = page.evaluate(
        """() => ({
            activeRole: document.activeElement.dataset.role,
            popupHidden: document.querySelector('[data-role="file-picker-folder-popup"]').hidden
        })"""
    )
    assert open_focus_result == {"activeRole": "file-picker-file-list", "popupHidden": True}

    page.keyboard.press("Tab")
    tab_from_file_result = page.evaluate(
        """() => ({
            activeRole: document.activeElement.dataset.role || '',
            modalContainsFocus: document.querySelector('[data-role="studio-modal"]').contains(document.activeElement)
        })"""
    )
    assert tab_from_file_result == {"activeRole": "modal-cancel", "modalContainsFocus": True}
    file_list.focus()
    for _ in range(4):
        page.keyboard.press("Tab")
    trap_result = page.evaluate(
        """() => {
            const modal = document.querySelector('[data-role="studio-modal"]');
            return {
                modalContainsFocus: modal.contains(document.activeElement),
                activeRole: document.activeElement.dataset.role || ''
            };
        }"""
    )
    assert trap_result["modalContainsFocus"] is True

    parent_folder_option = page.locator('[data-role="file-picker-subfolder-list"] [data-listbox-option-value=""]')
    install_option = page.locator('[data-role="file-picker-subfolder-list"] [data-listbox-option-value="install"]')
    assert parent_folder_option.text_content() == "natural"
    assert install_option.text_content() == "⨽ install"
    install_option.click()
    page.wait_for_selector('[data-role="file-picker-file-list"] [data-listbox-option-value="view-01.jpg"]')
    assert subfolder_list.evaluate("node => node.dataset.selectedValue") == "install"
    assert file_list.evaluate("node => node.dataset.selectedValue") == "view-01.jpg"
    parent_folder_option.click()
    page.wait_for_selector('[data-role="file-picker-file-list"] [data-listbox-option-value="cover.jpg"]')
    assert subfolder_list.evaluate("node => node.dataset.selectedValue || ''") == ""
    assert file_list.evaluate("node => node.dataset.selectedValue") == "cover.jpg"

    folder_input.focus()
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
    folder_input.press("Tab")
    tab_result = page.evaluate(
        """() => ({
            popupHidden: document.querySelector('[data-role="file-picker-folder-popup"]').hidden,
            modalContainsFocus: document.querySelector('[data-role="studio-modal"]').contains(document.activeElement)
        })"""
    )
    assert tab_result == {"popupHidden": True, "modalContainsFocus": True}
    folder_input.focus()
    folder_input.fill("ner")
    page.wait_for_selector('[data-search-list-value="nerve"]')
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
    page.wait_for_selector('[data-role="file-picker-file-list"] [data-listbox-option-value="nerve - copy.jpg"]')
    assert file_list.evaluate("node => node.dataset.selectedValue") == "nerve - copy.jpg"
    wheel_result = page.evaluate(
        """() => {
            const fileList = document.querySelector('[data-role="file-picker-file-list"]');
            const event = new WheelEvent('wheel', { deltaY: 100, bubbles: true, cancelable: true });
            const dispatchResult = fileList.dispatchEvent(event);
            return {
                value: fileList.dataset.selectedValue,
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


def assert_project_media_multi_file_picker(page: Page) -> None:
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
              <main id="catalogueWorkRoot" class="studioPage catalogueWorkPage"></main>
            `;
            const pickerModule = await import('/studio/app/frontend/js/catalogue-project-media-picker.js');
            const root = document.getElementById('catalogueWorkRoot');
            const modalHost = document.createElement('div');
            root.appendChild(modalHost);
            const state = {
                root,
                modalHost,
                projectMediaPicker: {
                    folders: [],
                    folderLoadPromise: null
                }
            };
            window.__multiFilePickerCalls = [];
            window.__multiFilePickerResult = null;
            window.__multiFilePickerPromise = pickerModule.openProjectMediaMultiFileModal(state, {
                text: (key, fallback) => fallback,
                initialSelection: {
                    project_folder: 'natural'
                },
                disabledSubfolders: ['used'],
                loadProjectFolders: async (query) => {
                    window.__multiFilePickerCalls.push(['folders', query]);
                    return {
                        ok: true,
                        project_folders: [{ project_folder: 'natural' }]
                    };
                },
                loadProjectFiles: async (request) => {
                    window.__multiFilePickerCalls.push(['files', request.projectFolder, request.projectSubfolder || '', request.query || '']);
                    if (request.projectSubfolder === 'details') {
                        return {
                            ok: true,
                            subfolders: [{ project_subfolder: 'used' }, { project_subfolder: 'details' }],
                            files: [{ filename: 'detail-01.jpg' }, { filename: 'detail-02.png' }]
                        };
                    }
                    return {
                        ok: true,
                        subfolders: [{ project_subfolder: 'used' }, { project_subfolder: 'details' }],
                        files: [{ filename: 'cover.jpg' }]
                    };
                }
            }).then((result) => {
                window.__multiFilePickerResult = result;
                return result;
            });
        }"""
    )

    page.wait_for_selector('[data-role="studio-modal"]')
    assert page.locator("#studioModalTitle").text_content() == "New detail section"
    assert page.locator('button[data-role="modal-primary"]').text_content() == "Create"
    file_list = page.locator('[data-role="file-picker-file-list"]')
    used_option = page.locator('[data-role="file-picker-subfolder-list"] [data-listbox-option-value="used"]')
    details_option = page.locator('[data-role="file-picker-subfolder-list"] [data-listbox-option-value="details"]')
    page.wait_for_selector('[data-role="file-picker-file-list"] [data-listbox-option-value="cover.jpg"]')
    assert used_option.get_attribute("aria-disabled") == "true"
    used_option.evaluate("node => node.click()")
    assert page.locator('[data-role="file-picker-subfolder-list"]').evaluate("node => node.dataset.selectedValue || ''") == ""
    details_option.click()
    page.wait_for_selector('[data-role="file-picker-file-list"] [data-listbox-option-value="detail-02.png"]')
    assert file_list.evaluate(
        """node => Array.from(node.querySelectorAll('[aria-selected="true"]')).map(option => option.dataset.listboxOptionValue)"""
    ) == ["detail-01.jpg", "detail-02.png"]
    assert page.locator('[data-role="file-picker-selection-count"]').text_content() == "2 selected"
    assert page.locator('[data-role="modal-primary"]').is_disabled() is False

    page.locator('[data-role="file-picker-deselect-all"]').click()
    assert page.locator('[data-role="file-picker-selection-count"]').text_content() == "0 selected"
    assert page.locator('[data-role="modal-primary"]').is_disabled() is True
    page.locator('[data-role="file-picker-select-all"]').click()
    assert page.locator('[data-role="file-picker-selection-count"]').text_content() == "2 selected"
    assert page.locator('[data-role="modal-primary"]').is_disabled() is False

    page.locator('button[data-role="modal-primary"]').click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached")
    page.wait_for_function("() => Boolean(window.__multiFilePickerResult)")
    result = page.evaluate("window.__multiFilePickerResult")
    assert result["confirmed"] is True
    assert result["selection"]["project_folder"] == "natural"
    assert result["selection"]["project_subfolder"] == "details"
    assert result["selection"]["filenames"] == ["detail-01.jpg", "detail-02.png"]
    assert result["selection"]["file_titles"] == [
        {"filename": "detail-01.jpg", "title": "detail-01"},
        {"filename": "detail-02.png", "title": "detail-02"},
    ]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_project_media_picker(page)
            assert_project_media_multi_file_picker(page)
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
