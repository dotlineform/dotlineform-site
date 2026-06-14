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
      <div id="catalogueWorkPopup">
        <input id="catalogueWorkSearch" />
        <span id="catalogueWorkPopupList" hidden></span>
      </div>
      <button id="catalogueWorkOpen"></button>
      <button id="catalogueWorkNew"></button>
      <button id="catalogueWorkSave"></button>
      <button id="catalogueWorkPublication"></button>
      <button id="catalogueWorkDelete"></button>
      <div id="catalogueWorkSaveMode"></div>
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
                contextNodeInState: Object.prototype.hasOwnProperty.call(state, 'contextNode'),
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
    assert result["contextNodeInState"] is False
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
            state.fieldsNode.innerHTML = `
              <button data-prose-import="work">prose</button>
            `;
            state.filesResultsNode.innerHTML = `
              <button data-download-edit="2">edit download</button>
              <button data-download-delete="3">delete download</button>
            `;
            state.linksResultsNode.innerHTML = `
              <button data-link-edit="4">edit link</button>
              <button data-link-delete="5">delete link</button>
            `;
            state.previewNode.innerHTML = `
              <button data-media-refresh="work">media</button>
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
    page.click('[data-media-refresh="work"]')
    page.click('[data-prose-import="work"]')
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


def assert_work_search_list_selection(page: Page) -> None:
    page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const stateModule = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const selectionModule = await import('/studio/app/frontend/js/catalogue-work-selection.js');
            const elements = stateModule.collectWorkEditorElements();
            const state = stateModule.createWorkEditorState(elements, {{
                mediaConfigLoader: () => ({{}}),
                modalHostFactory: () => ({{}})
            }});
            const records = new Map([
                ['00001', {{ work_id: '00001', title: 'a poem divided into 4 parts', status: 'published' }}],
                ['00010', {{ work_id: '00010', title: 'slaughter composite', status: 'published' }}],
                ['00012', {{ work_id: '00012', title: 'loose bound book', status: 'published' }}],
                ['00533', {{ work_id: '00533', title: '2 bodies monoprint', status: 'published' }}],
                ['01002', {{ work_id: '01002', title: 'body space', status: 'published' }}]
            ]);
            state.workSearchById = records;
            state.sourceWorkRecordsById = new Map(records);
            window.__workSearchCalls = [];
            const context = {{
                loadWorkLookupRecord: async (workId) => {{
                    window.__workSearchCalls.push(['load', workId]);
                    return {{ work: records.get(workId) }};
                }},
                setLoadedWorkRecord: (workId, record) => {{
                    window.__workSearchCalls.push(['loaded', workId, record.title]);
                }},
                setLoadedBulkWorks: () => window.__workSearchCalls.push(['bulk']),
                refreshBuildPreview: async () => window.__workSearchCalls.push(['refresh']),
                updateEditorState: () => window.__workSearchCalls.push(['update']),
                text: (_key, fallback) => fallback
            }};
            selectionModule.bindWorkSelectionControls(state, context);
            window.__workSelectionState = state;
        }}"""
    )
    page.fill("#catalogueWorkSearch", "1")
    page.wait_for_selector('#catalogueWorkSearchList [data-search-list-value="00001"]', state="attached")
    numeric_result = page.evaluate(
        """() => ({
            values: Array.from(document.querySelectorAll('#catalogueWorkSearchList [data-search-list-value]')).map((node) => node.dataset.searchListValue),
            labels: Array.from(document.querySelectorAll('#catalogueWorkSearchList .catalogueWorkSearch__title')).map((node) => node.textContent)
        })"""
    )
    assert numeric_result["values"] == ["00001", "00010", "00012", "01002"]
    assert numeric_result["labels"] == [
        "a poem divided into 4 parts",
        "slaughter composite",
        "loose bound book",
        "body space",
    ]

    page.fill("#catalogueWorkSearch", "2 b")
    page.wait_for_selector('#catalogueWorkSearchList [data-search-list-value="00533"]', state="attached")
    title_result = page.evaluate(
        """() => ({
            values: Array.from(document.querySelectorAll('#catalogueWorkSearchList [data-search-list-value]')).map((node) => node.dataset.searchListValue),
            firstTitle: document.querySelector('#catalogueWorkSearchList .catalogueWorkSearch__title').textContent
        })"""
    )
    assert title_result == {"values": ["00533"], "firstTitle": "2 bodies monoprint"}
    page.press("#catalogueWorkSearch", "Enter")
    page.wait_for_function("() => window.__workSearchCalls.some((call) => call[0] === 'loaded' && call[1] === '00533')")
    assert page.evaluate("document.querySelector('#catalogueWorkSearch').value") == "00533"

    page.evaluate(
        """() => {
            window.__workSelectionState.mode = 'new';
            window.__workSelectionState.draft = {};
            window.__workSearchCalls.length = 0;
        }"""
    )
    page.fill("#catalogueWorkSearch", "123")
    new_mode_result = page.evaluate(
        """() => ({
            draftWorkId: window.__workSelectionState.draft.work_id,
            popupHidden: document.querySelector('#catalogueWorkSearchList').hidden,
            calls: window.__workSearchCalls
        })"""
    )
    assert new_mode_result == {
        "draftWorkId": "00123",
        "popupHidden": True,
        "calls": [["update"]],
    }


def assert_route_state_status_target(page: Page) -> None:
    result = page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const stateModule = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const routeModule = await import('/studio/app/frontend/js/catalogue-work-route-state.js');
            const elements = stateModule.collectWorkEditorElements();
            const state = stateModule.createWorkEditorState(elements, {{
                mediaConfigLoader: () => ({{}}),
                modalHostFactory: () => ({{}})
            }});
            const textWrites = [];
            const routeOptions = stateModule.createWorkRouteStateOptions(state, {{
                text: (key) => key,
                setTextWithState: (node, text) => textWrites.push({{ id: node && node.id, text }}),
                setOpenInputMode: () => undefined,
                setPopupVisibility: () => undefined,
                applyDraftToInputs: () => undefined,
                applyReadonly: () => undefined,
                clearReadonlyFields: () => undefined,
                updateEditorState: () => undefined
            }});
            routeModule.setLoadedWorkRecord(state, '00008', {{
                work_id: '00008',
                title: 'Smoke work',
                year: '2026',
                year_display: '2026',
                status: 'draft',
                series_ids: ['001']
            }}, routeOptions);
            routeModule.setNewWorkMode(state, routeOptions);
            routeModule.setEmptySearchMode(state, routeOptions);
            return {{
                hasContextNode: Object.prototype.hasOwnProperty.call(state, 'contextNode'),
                statusTexts: textWrites
                    .filter((write) => write.id === 'catalogueWorkStatus')
                    .map((write) => write.text),
                targetIds: Array.from(new Set(textWrites.map((write) => write.id))).sort()
            }};
        }}"""
    )
    assert result["hasContextNode"] is False
    assert result["statusTexts"] == ["save_status_loaded", "new_status_loaded", "missing_work_param"]
    assert result["targetIds"] == ["catalogueWorkResult", "catalogueWorkStatus", "catalogueWorkWarning"]


def assert_series_chip_public_links(page: Page) -> None:
    result = page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const stateModule = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const formModule = await import('/studio/app/frontend/js/catalogue-work-form.js');
            const elements = stateModule.collectWorkEditorElements();
            const state = stateModule.createWorkEditorState(elements, {{
                mediaConfigLoader: () => ({{}}),
                modalHostFactory: () => ({{}})
            }});
            state.config = {{
                app: {{
                    runtime: {{
                        sites: {{
                            public_preview: {{ base: 'http://127.0.0.1:4000' }}
                        }}
                    }}
                }}
            }};
            state.draft = {{
                series_ids: '026'
            }};
            state.baselineDraft = {{ ...state.draft }};
            state.seriesById.set('026', {{ series_id: '026', title: 'collected 1989-1998' }});
            formModule.renderWorkEditorFields(state, elements, {{ text: (_key, fallback) => fallback }});
            const chipLink = document.querySelector('.catalogueWorkSeriesPicker__chipLink');
            return {{
                chipHref: chipLink && chipLink.href,
                chipText: chipLink && chipLink.textContent.replace(/\\s+/g, ' ').trim()
            }};
        }}"""
    )
    assert result["chipHref"] == "http://127.0.0.1:4000/series/?series=026", result
    assert result["chipText"] == "collected 1989-1998 026"


def assert_media_refresh_button_uses_preview_actions(page: Page) -> None:
    result = page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const stateModule = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const formModule = await import('/studio/app/frontend/js/catalogue-work-form.js');
            const sectionsModule = await import('/studio/app/frontend/js/catalogue-work-sections.js');
            const elements = stateModule.collectWorkEditorElements();
            const state = stateModule.createWorkEditorState(elements, {{
                mediaConfigLoader: () => ({{}}),
                modalHostFactory: () => ({{}})
            }});
            state.config = {{
                app: {{
                    runtime: {{
                        sites: {{
                            public_preview: {{ base: 'http://127.0.0.1:4000' }}
                        }}
                    }}
                }}
            }};
            state.currentRecord = {{
                work_id: '00008',
                title: 'nerve',
                status: 'published',
                year_display: 'July 1990 - January 1995',
                height_px: '2263',
                width_px: '1600'
            }};
            state.currentWorkId = '00008';
            state.serverAvailable = true;
            state.draft = {{ ...state.currentRecord }};
            state.baselineDraft = {{ ...state.draft }};
            state.mediaConfig = {{
                worksPrimaryBase: '/assets/works/img/',
                primaryDisplayWidth: 800,
                primaryFullWidth: 1600,
                primarySuffix: 'primary',
                assetFormat: 'webp'
            }};
            state.buildPreview = {{
                readiness: {{
                    items: [
                        {{
                            key: 'work_media',
                            title: 'media',
                            status: 'ready',
                            exists: true,
                            summary: 'Source media is ready and local thumbnails are current in assets/works/img/00008-thumb-96.webp.',
                            source_path: 'projects/nerve/nerve.jpg',
                            next_step: 'Local thumbnails are current for this record.'
                        }},
                        {{
                            key: 'work_prose',
                            title: 'prose',
                            status: 'ready',
                            exists: true,
                            summary: 'Staged prose is ready.',
                            source_path: 'var/docs/catalogue/import-staging/works/00008.md'
                        }}
                    ]
                }}
            }};
            const options = {{
                text: (_key, fallback) => fallback,
                draftHasChanges: () => false
            }};
            formModule.renderWorkEditorFields(state, elements, options);
            sectionsModule.renderWorkCurrentPreview(state, options);
            sectionsModule.renderWorkReadiness(state, options);
            const refreshButton = state.previewNode.querySelector('[data-media-refresh="work"]');
            const proseButton = state.fieldsNode.querySelector('[data-prose-import="work"]');
            return {{
                captionText: state.previewNode.querySelector('.catalogueRecordPreview__caption').textContent.replace(/\\s+/g, ' ').trim(),
                previewActionsText: state.previewNode.querySelector('.catalogueRecordPreview__actions').textContent.replace(/\\s+/g, ' ').trim(),
                stagedProseLabel: state.fieldsNode.querySelector('.catalogueWorkStagedProse .tagStudioForm__label').textContent,
                stagedProseValue: state.fieldsNode.querySelector('[data-staged-prose-value="work"]').textContent,
                proseDisabled: proseButton ? proseButton.disabled : null,
                refreshDisabled: refreshButton ? refreshButton.disabled : null,
                readonlyFieldCount: state.readonlyNode.querySelectorAll('[data-readonly-field]').length,
                readinessText: state.readinessNode.textContent.replace(/\\s+/g, ' ').trim()
            }};
        }}"""
    )
    assert result["captionText"] == "nerve · July 1990 - January 1995 2263 x 1600 px"
    assert result["previewActionsText"] == "Preview update Refresh media"
    assert result["stagedProseLabel"] == "staged prose"
    assert result["stagedProseValue"] == "00008.md"
    assert result["proseDisabled"] is False
    assert result["refreshDisabled"] is False
    assert result["readonlyFieldCount"] == 0
    assert "Source media is ready" not in result["readinessText"]
    assert "projects/nerve/nerve.jpg" not in result["readinessText"]
    assert "Local thumbnails are current" not in result["readinessText"]
    assert "Staged prose is ready." not in result["readinessText"]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_state_factory(page)
            assert_event_binder(page)
            assert_work_search_list_selection(page)
            assert_route_state_status_target(page)
            assert_series_chip_public_links(page)
            assert_media_refresh_button_uses_preview_actions(page)
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
