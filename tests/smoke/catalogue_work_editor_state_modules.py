#!/usr/bin/env python3
"""Smoke-check Work editor state and event-owner JavaScript modules."""

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


WORK_EDITOR_DOM = """
  <main>
    <section id="catalogueWorkRoot">
      <div id="catalogueWorkLoading"></div>
      <div id="catalogueWorkEmpty"></div>
      <div id="catalogueWorkFields"></div>
      <div id="catalogueWorkReadonly"></div>
      <div id="catalogueWorkPreview"></div>
      <div id="catalogueWorkSummary"></div>
      <div id="catalogueWorkReadiness"></div>
      <div id="catalogueWorkRuntimeState"></div>
      <div id="catalogueWorkBuildImpact"></div>
      <h2 id="catalogueWorkDetailsHeading"></h2>
      <a id="catalogueWorkNewDetailLink"></a>
      <div id="catalogueWorkDetailsSearchRow"></div>
      <input id="catalogueWorkDetailSearch" />
      <div id="catalogueWorkDetailsMeta"></div>
      <section><div id="catalogueWorkDetailsResults"></div></section>
      <h2 id="catalogueWorkFilesHeading"></h2>
      <button id="catalogueWorkNewFileLink"></button>
      <div id="catalogueWorkFilesMeta"></div>
      <section><div id="catalogueWorkFilesResults"></div></section>
      <h2 id="catalogueWorkLinksHeading"></h2>
      <button id="catalogueWorkNewLinkLink"></button>
      <div id="catalogueWorkLinksMeta"></div>
      <section><div id="catalogueWorkLinksResults"></div></section>
      <input id="catalogueWorkSearch" />
      <div id="catalogueWorkPopup"></div>
      <div id="catalogueWorkPopupList"></div>
      <button id="catalogueWorkOpen"></button>
      <button id="catalogueWorkNew"></button>
      <button id="catalogueWorkSave"></button>
      <button id="catalogueWorkPublication"></button>
      <button id="catalogueWorkDelete"></button>
      <div id="catalogueWorkSaveMode"></div>
      <div id="catalogueWorkContext"></div>
      <div id="catalogueWorkStatus"></div>
      <div id="catalogueWorkWarning"></div>
      <div id="catalogueWorkResult"></div>
      <div id="catalogueWorkMeta"></div>
    </section>
  </main>
"""


def assert_state_factory(page: Page) -> None:
    result = page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const module = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const elements = module.collectWorkEditorElements();
            const state = module.createWorkEditorState(elements, {{
                mediaConfigLoader: (root) => ({{ rootId: root.id, source: 'stub-media' }}),
                modalHostFactory: (options) => ({{ rootId: options.root.id, source: 'stub-modal' }})
            }});
            const routeOptions = module.createWorkRouteStateOptions(state, {{
                text: (key, fallback) => `${{key}}:${{fallback}}`,
                setTextWithState: () => 'set-text',
                setOpenInputMode: () => 'open-mode',
                setPopupVisibility: () => 'popup',
                applyDraftToInputs: () => 'draft',
                applyReadonly: () => 'readonly',
                clearReadonlyFields: () => 'clear-readonly',
                updateEditorState: () => 'update'
            }}, {{
                customOption: 'custom'
            }});
            return {{
                collected: Boolean(elements && elements.root),
                routeName: module.WORK_ROUTE_STATE.route,
                bulkKey: module.WORK_ROUTE_STATE.bulkIdsKey,
                busyKeys: module.WORK_ROUTE_STATE.busyKeys.join(','),
                mode: state.mode,
                currentWorkId: state.currentWorkId,
                bulkWorkIds: state.bulkWorkIds.length,
                bulkRecordsIsMap: state.bulkRecords instanceof Map,
                touchedFieldsIsSet: state.bulkTouchedFields instanceof Set,
                validationErrorsIsMap: state.validationErrors instanceof Map,
                mediaConfig: state.mediaConfig,
                modalHost: state.modalHost,
                detailsPanelTag: state.detailsPanelNode && state.detailsPanelNode.tagName,
                filesPanelTag: state.filesPanelNode && state.filesPanelNode.tagName,
                linksPanelTag: state.linksPanelNode && state.linksPanelNode.tagName,
                routeOptionText: routeOptions.text('key', 'fallback'),
                routeOptionCustom: routeOptions.customOption,
                routeOptionUpdate: routeOptions.updateEditorState()
            }};
        }}"""
    )
    assert result["collected"] is True
    assert result["routeName"] == "catalogue-work"
    assert result["bulkKey"] == "bulkWorkIds"
    assert result["busyKeys"] == "isSaving,isBuilding,isPreviewingBuild,isDeleting"
    assert result["mode"] == "single"
    assert result["currentWorkId"] == ""
    assert result["bulkWorkIds"] == 0
    assert result["bulkRecordsIsMap"] is True
    assert result["touchedFieldsIsSet"] is True
    assert result["validationErrorsIsMap"] is True
    assert result["mediaConfig"] == {"rootId": "catalogueWorkRoot", "source": "stub-media"}
    assert result["modalHost"] == {"rootId": "catalogueWorkRoot", "source": "stub-modal"}
    assert result["detailsPanelTag"] == "SECTION"
    assert result["filesPanelTag"] == "SECTION"
    assert result["linksPanelTag"] == "SECTION"
    assert result["routeOptionText"] == "key:fallback"
    assert result["routeOptionCustom"] == "custom"
    assert result["routeOptionUpdate"] == "update"


def assert_event_binder(page: Page) -> None:
    page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const stateModule = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const eventModule = await import('/studio/app/frontend/js/catalogue-work-editor-events.js');
            const elements = stateModule.collectWorkEditorElements();
            const state = stateModule.createWorkEditorState(elements, {{
                mediaConfigLoader: () => ({{}}),
                modalHostFactory: () => ({{}})
            }});
            state.filesResultsNode.innerHTML = `
              <button data-download-edit="2">edit download</button>
              <button data-download-delete="3">delete download</button>
            `;
            state.linksResultsNode.innerHTML = `
              <button data-link-edit="4">edit link</button>
              <button data-link-delete="5">delete link</button>
            `;
            state.readinessNode.innerHTML = `
              <button data-media-refresh>media</button>
              <button data-prose-import>prose</button>
            `;
            window.__workEventCalls = [];
            const push = (...args) => window.__workEventCalls.push(args);
            eventModule.bindWorkEditorEvents(state, {{
                bindSelectionControls: () => push('bindSelectionControls'),
                updateDetailSections: () => push('updateDetailSections'),
                openEmbeddedEntryModal: (kind, index = null) => push('openEmbeddedEntryModal', kind, index),
                deleteEmbeddedEntry: (kind, index) => push('deleteEmbeddedEntry', kind, index),
                setNewWorkMode: () => push('setNewWorkMode'),
                refreshWorkMedia: () => push('refreshWorkMedia'),
                importWorkProse: () => push('importWorkProse'),
                saveCurrentWork: () => push('saveCurrentWork'),
                applyPublicationChange: () => push('applyPublicationChange'),
                deleteCurrentWork: () => push('deleteCurrentWork')
            }});
        }}"""
    )
    page.fill("#catalogueWorkDetailSearch", "001")
    page.click("#catalogueWorkNewFileLink")
    page.click("#catalogueWorkNewLinkLink")
    page.click("[data-download-edit]")
    page.click("[data-download-delete]")
    page.click("[data-link-edit]")
    page.click("[data-link-delete]")
    page.click("#catalogueWorkNew")
    page.click("[data-media-refresh]")
    page.click("[data-prose-import]")
    page.click("#catalogueWorkSave")
    page.click("#catalogueWorkPublication")
    page.click("#catalogueWorkDelete")
    calls = page.evaluate("window.__workEventCalls")
    assert calls == [
        ["bindSelectionControls"],
        ["updateDetailSections"],
        ["openEmbeddedEntryModal", "download", None],
        ["openEmbeddedEntryModal", "link", None],
        ["openEmbeddedEntryModal", "download", 2],
        ["deleteEmbeddedEntry", "download", 3],
        ["openEmbeddedEntryModal", "link", 4],
        ["deleteEmbeddedEntry", "link", 5],
        ["setNewWorkMode"],
        ["refreshWorkMedia"],
        ["importWorkProse"],
        ["saveCurrentWork"],
        ["applyPublicationChange"],
        ["deleteCurrentWork"],
    ]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_state_factory(page)
            assert_event_binder(page)
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
