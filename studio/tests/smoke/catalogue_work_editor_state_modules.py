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
      <section id="catalogueWorkDetailBrowserPanel">
        <input id="catalogueWorkDetailBrowserSearch" />
        <button id="catalogueWorkDetailBrowserSearchClear"></button>
        <div id="catalogueWorkDetailBrowserActions"></div>
        <div id="catalogueWorkDetailBrowserSectionActions"></div>
        <div id="catalogueWorkDetailBrowserSections"></div>
        <div id="catalogueWorkDetailBrowserImages"></div>
      </section>
      <div id="catalogueWorkResourcesPanel">
        <div id="catalogueWorkResourcesActions"></div>
        <div id="catalogueWorkResourcesMeta"></div>
        <div id="catalogueWorkResourcesResults"></div>
      </div>
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
                mediaPublishPending: state.mediaPublishPending,
                mediaConfig: state.mediaConfig,
                modalHost: state.modalHost,
                detailBrowserPanelTag: state.detailBrowserPanelNode && state.detailBrowserPanelNode.tagName,
                detailBrowserSearchTag: state.detailBrowserSearchNode && state.detailBrowserSearchNode.tagName,
                detailBrowserSelectedSectionId: state.detailBrowserSelectedSectionId,
                resourcesPanelTag: state.resourcesPanelNode && state.resourcesPanelNode.tagName,
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
    assert result["busyKeys"] == "isSaving,isBuilding,isDeleting"
    assert result["mode"] == "single"
    assert result["currentWorkId"] == ""
    assert result["bulkWorkIds"] == 0
    assert result["bulkRecordsIsMap"] is True
    assert result["touchedFieldsIsSet"] is True
    assert result["validationErrorsIsMap"] is True
    assert result["mediaPublishPending"] is False
    assert result["mediaConfig"] == {"rootId": "catalogueWorkRoot", "source": "stub-media"}
    assert result["modalHost"] == {"rootId": "catalogueWorkRoot", "source": "stub-modal"}
    assert result["detailBrowserPanelTag"] == "SECTION"
    assert result["detailBrowserSearchTag"] == "INPUT"
    assert result["detailBrowserSelectedSectionId"] == ""
    assert result["resourcesPanelTag"] == "DIV"
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
            state.previewNode.innerHTML = `
              <button data-media-refresh="work">media</button>
            `;
            window.__workEventCalls = [];
            const push = (...args) => window.__workEventCalls.push(args);
            eventModule.bindWorkEditorEvents(state, {{
                bindSelectionControls: () => push('bindSelectionControls'),
                updateWorkDetailBrowser: () => push('updateWorkDetailBrowser'),
                openEmbeddedEntryModal: (kind, index = null) => push('openEmbeddedEntryModal', kind, index),
                deleteEmbeddedEntry: (kind, index) => push('deleteEmbeddedEntry', kind, index),
                setNewWorkMode: () => push('setNewWorkMode'),
                refreshWorkMedia: () => push('refreshWorkMedia'),
                saveCurrentWork: () => push('saveCurrentWork'),
                applyPublicationChange: () => push('applyPublicationChange'),
                deleteCurrentWork: () => push('deleteCurrentWork')
            }});
        }}"""
    )
    page.fill("#catalogueWorkDetailBrowserSearch", "001")
    page.click("#catalogueWorkNew")
    page.click('[data-media-refresh="work"]')
    page.click("#catalogueWorkSave")
    page.click("#catalogueWorkPublication")
    page.click("#catalogueWorkDelete")
    calls = page.evaluate("window.__workEventCalls")
    assert calls == [
        ["bindSelectionControls"],
        ["updateWorkDetailBrowser"],
        ["setNewWorkMode"],
        ["refreshWorkMedia"],
        ["saveCurrentWork"],
        ["applyPublicationChange"],
        ["deleteCurrentWork"],
    ]


def assert_save_then_media_publish_sequence(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/studio/app/frontend/js/catalogue-work-media-publish.js');
            const actionsModule = await import('/studio/app/frontend/js/catalogue-work-actions.js');
            const enabledCalls = [];
            let enabledPending = false;
            const enabled = await module.runWorkSaveThenMediaPublish({
                save: async () => enabledCalls.push('save'),
                mediaPublishEnabled: () => {
                    enabledCalls.push('check');
                    return true;
                },
                publishMedia: async () => {
                    enabledCalls.push('publishMedia');
                    return true;
                },
                setMediaPublishPending: (pending) => {
                    enabledPending = pending;
                    enabledCalls.push(`pending:${pending}`);
                }
            });
            const failedCalls = [];
            let failedPending = false;
            const failed = await module.runWorkSaveThenMediaPublish({
                save: async () => failedCalls.push('save'),
                mediaPublishEnabled: () => {
                    failedCalls.push('check');
                    return true;
                },
                publishMedia: async () => {
                    failedCalls.push('publishMedia');
                    return false;
                },
                setMediaPublishPending: (pending) => {
                    failedPending = pending;
                    failedCalls.push(`pending:${pending}`);
                }
            });
            const disabledCalls = [];
            const disabled = await module.runWorkSaveThenMediaPublish({
                save: async () => disabledCalls.push('save'),
                mediaPublishEnabled: () => {
                    disabledCalls.push('check');
                    return false;
                },
                publishMedia: async () => disabledCalls.push('publishMedia'),
                setMediaPublishPending: (pending) => disabledCalls.push(`pending:${pending}`)
            });
            const eligibleState = {
                mode: 'single',
                currentWorkId: '00008',
                currentRecord: { status: 'published', media_version: 2 },
                serverAvailable: true,
                isSaving: false,
                isBuilding: false,
                isDeleting: false,
                buildPreview: {
                    readiness: {
                        items: [{ key: 'work_media', status: 'ready' }]
                    }
                }
            };
            const eligible = module.workMediaPublishEnabled(eligibleState, {
                draftHasChanges: () => false
            });
            const dirty = module.workMediaPublishEnabled(eligibleState, {
                draftHasChanges: () => true
            });
            const sourceSaveRequired = module.workSaveActionRequired({
                mode: 'single',
                mediaPublishPending: false
            }, true);
            const mediaRetryRequired = module.workSaveActionRequired({
                mode: 'single',
                mediaPublishPending: true
            }, false);
            const cleanSaveRequired = module.workSaveActionRequired({
                mode: 'single',
                mediaPublishPending: false
            }, false);
            const bulkRetryRequired = module.workSaveActionRequired({
                mode: 'bulk',
                mediaPublishPending: true
            }, false);
            const completedRemoteMedia = actionsModule.catalogueRemoteMediaWarning({
                status: 'completed',
                failed: 0,
                failed_targets: []
            });
            const detailRemoteWarning = actionsModule.catalogueRemoteMediaWarning({
                status: 'warning',
                failed: 3,
                failed_targets: [
                    { kind: 'work_details', id: '00008-001' }
                ]
            });
            const deleteRemoteWarning = actionsModule.catalogueDeleteRemoteCleanupWarning({
                cleanup: {
                    r2_media: {
                        status: 'warning',
                        failed: 6,
                        failed_targets: [
                            { kind: 'works', id: '00008' },
                            { kind: 'work_details', id: '00008-001' }
                        ]
                    }
                }
            });
            return {
                enabled,
                enabledCalls,
                enabledPending,
                failed,
                failedCalls,
                failedPending,
                disabled,
                disabledCalls,
                eligible,
                dirty,
                sourceSaveRequired,
                mediaRetryRequired,
                cleanSaveRequired,
                bulkRetryRequired,
                completedRemoteMedia,
                detailRemoteWarning,
                deleteRemoteWarning
            };
        }"""
    )
    assert result == {
        "enabled": True,
        "enabledCalls": ["save", "check", "pending:true", "publishMedia", "pending:false"],
        "enabledPending": False,
        "failed": True,
        "failedCalls": ["save", "check", "pending:true", "publishMedia"],
        "failedPending": True,
        "disabled": False,
        "disabledCalls": ["save", "check"],
        "eligible": True,
        "dirty": False,
        "sourceSaveRequired": True,
        "mediaRetryRequired": True,
        "cleanSaveRequired": False,
        "bulkRetryRequired": False,
        "completedRemoteMedia": None,
        "detailRemoteWarning": {
            "failed": 3,
            "targets": ["work detail 00008-001"],
        },
        "deleteRemoteWarning": {
            "failed": 6,
            "targets": ["work 00008", "work detail 00008-001"],
        },
    }


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


def assert_detail_browser_search_filters_suffix(page: Page) -> None:
    result = page.evaluate(
        f"""async () => {{
            document.body.innerHTML = `{WORK_EDITOR_DOM}`;
            const stateModule = await import('/studio/app/frontend/js/catalogue-work-editor-state.js');
            const browserModule = await import('/studio/app/frontend/js/catalogue-work-detail-browser.js');
            const elements = stateModule.collectWorkEditorElements();
            const state = stateModule.createWorkEditorState(elements, {{
                mediaConfigLoader: () => ({{}}),
                modalHostFactory: () => ({{}})
            }});
            state.config = {{ app: {{ routes: {{}} }} }};
            state.currentWorkId = '00001';
            state.currentRecord = {{ work_id: '00001', status: 'published' }};
            state.currentLookup = {{
                detail_sections: [
                    {{
                        section_id: 'front',
                        section_title: 'front',
                        details: [
                            {{ detail_uid: '00001-001', detail_id: '001', title: 'one' }},
                            {{ detail_uid: '00001-002', detail_id: '002', title: 'two' }}
                        ]
                    }},
                    {{
                        section_id: 'back',
                        section_title: 'back',
                        details: [
                            {{ detail_uid: '00001-011', detail_id: '011', title: 'eleven' }},
                            {{ detail_uid: '00001-111', detail_id: '111', title: 'one eleven' }},
                            {{ detail_uid: '00001-222', detail_id: '222', title: 'two twenty two' }}
                        ]
                    }}
                ]
            }};
            browserModule.updateWorkDetailBrowser(state, {{ text: (_key, fallback) => fallback }});
            const detailToolbarHidden = document.querySelector('#catalogueWorkDetailBrowserActions').hidden;
            const newDisabledForPublished = document.querySelector('#catalogueWorkDetailBrowserSectionActions [data-record-list-action="new"]').disabled;
            state.detailBrowserSearchNode.value = '1';
            browserModule.updateWorkDetailBrowser(state, {{ text: (_key, fallback) => fallback }});
            const valuesAfterSearch = Array.from(document.querySelectorAll('#catalogueWorkDetailBrowserImages [data-record-list-cell="detailUid"]'))
                .map((node) => node.textContent.trim());
            const clearHiddenAfterSearch = state.detailBrowserSearchClearNode.hidden;
            state.detailBrowserSearchNode.value = '00001-011';
            browserModule.updateWorkDetailBrowser(state, {{ text: (_key, fallback) => fallback }});
            const normalizedSearchValue = state.detailBrowserSearchNode.value;
            const valuesAfterFullUid = Array.from(document.querySelectorAll('#catalogueWorkDetailBrowserImages [data-record-list-cell="detailUid"]'))
                .map((node) => node.textContent.trim());
            state.currentRecord.status = 'draft';
            browserModule.updateWorkDetailBrowser(state, {{ text: (_key, fallback) => fallback }});
            const newDisabledForDraft = document.querySelector('#catalogueWorkDetailBrowserSectionActions [data-record-list-action="new"]').disabled;
            return {{
                valuesAfterSearch,
                clearHiddenAfterSearch,
                normalizedSearchValue,
                valuesAfterFullUid,
                detailToolbarHidden,
                newDisabledForPublished,
                newDisabledForDraft
            }};
        }}"""
    )
    assert result == {
        "valuesAfterSearch": ["00001-001", "00001-011", "00001-111"],
        "clearHiddenAfterSearch": False,
        "normalizedSearchValue": "011",
        "valuesAfterFullUid": ["00001-011"],
        "detailToolbarHidden": True,
        "newDisabledForPublished": False,
        "newDisabledForDraft": True,
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
            state.mediaPublishPending = true;
            routeModule.setLoadedWorkRecord(state, '00008', {{
                work_id: '00008',
                title: 'Smoke work',
                year: '2026',
                year_display: '2026',
                status: 'draft',
                series_ids: ['001']
            }}, routeOptions);
            const pendingAfterRecordLoad = state.mediaPublishPending;
            state.mediaPublishPending = true;
            routeModule.setNewWorkMode(state, routeOptions);
            const pendingAfterNewMode = state.mediaPublishPending;
            state.mediaPublishPending = true;
            routeModule.setEmptySearchMode(state, routeOptions);
            return {{
                hasContextNode: Object.prototype.hasOwnProperty.call(state, 'contextNode'),
                pendingAfterRecordLoad,
                pendingAfterNewMode,
                pendingAfterEmptyMode: state.mediaPublishPending,
                statusTexts: textWrites
                    .filter((write) => write.id === 'catalogueWorkStatus')
                    .map((write) => write.text),
                targetIds: Array.from(new Set(textWrites.map((write) => write.id))).sort()
            }};
        }}"""
    )
    assert result["hasContextNode"] is False
    assert result["pendingAfterRecordLoad"] is False
    assert result["pendingAfterNewMode"] is False
    assert result["pendingAfterEmptyMode"] is False
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
                width_px: '1600',
                media_version: 1
            }};
            state.currentWorkId = '00008';
            state.serverAvailable = true;
            state.draft = {{
                ...state.currentRecord,
                project_folder: 'nerve',
                project_subfolder: '',
                project_filename: 'replacement.jpg'
            }};
            state.baselineDraft = {{ ...state.draft }};
            state.mediaPreviewVersion = 'media-refresh-token';
            state.mediaConfig = {{
                worksPrimaryBase: '/assets/works/img/',
                stagedWorksPrimaryBase: '/studio/media/catalogue/works/srcset_images/primary/',
                primaryDisplayWidth: 800,
                primaryFullWidth: 1600,
                primarySuffix: 'primary',
                assetFormat: 'webp'
            }};
            state.buildPreview = {{
                local_media: {{
                    tasks: [
                        {{
                            kind: 'work',
                            id: '00008',
                            source_width_px: 3000,
                            source_height_px: 2000
                        }}
                    ]
                }},
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
                        }}
                    ]
                }}
            }};
            const options = {{
                text: (_key, fallback) => fallback,
                draftHasChanges: () => true
            }};
            formModule.renderWorkEditorFields(state, elements, options);
            sectionsModule.renderWorkCurrentPreview(state, options);
            sectionsModule.renderWorkReadiness(state, options);
            const refreshButton = state.previewNode.querySelector('[data-media-refresh="work"]');
            const previewImage = state.previewNode.querySelector('[data-preview-image]');
            return {{
                captionText: state.previewNode.querySelector('.catalogueRecordPreview__caption').textContent.replace(/\\s+/g, ' ').trim(),
                previewActionsText: state.previewNode.querySelector('.catalogueRecordPreview__actions').textContent.replace(/\\s+/g, ' ').trim(),
                previewImageSrc: previewImage ? previewImage.getAttribute('src') : '',
                refreshDisabled: refreshButton ? refreshButton.disabled : null,
                publishButtonPresent: Boolean(state.previewNode.querySelector('[data-media-publish="work"]')),
                readonlyFieldCount: state.readonlyNode.querySelectorAll('[data-readonly-field]').length,
                readinessText: state.readinessNode.textContent.replace(/\\s+/g, ' ').trim()
            }};
        }}"""
    )
    assert result["captionText"] == "nerve · July 1990 - January 1995 2000 x 3000 px media version 1 · staged candidate 2"
    assert result["previewActionsText"] == "Refresh media"
    assert result["previewImageSrc"] == "/studio/media/catalogue/works/srcset_images/primary/00008-primary-800.webp?v=media-refresh-token"
    assert result["refreshDisabled"] is False
    assert result["publishButtonPresent"] is False
    assert result["readonlyFieldCount"] == 0
    assert "Source media is ready" not in result["readinessText"]
    assert "projects/nerve/nerve.jpg" not in result["readinessText"]
    assert "Local thumbnails are current" not in result["readinessText"]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_state_factory(page)
            assert_event_binder(page)
            assert_save_then_media_publish_sequence(page)
            assert_work_search_list_selection(page)
            assert_detail_browser_search_filters_suffix(page)
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
