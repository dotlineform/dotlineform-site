#!/usr/bin/env python3
"""Smoke-check sibling Catalogue editor state and event-owner modules."""

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


def assert_sibling_state_factories(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <section id="catalogueWorkDetailRoot">
                <div id="catalogueWorkDetailLoading"></div><div id="catalogueWorkDetailEmpty"></div>
                <div id="catalogueWorkDetailFields"></div><div id="catalogueWorkDetailReadonly"></div>
                <div id="catalogueWorkDetailPreview"></div><div id="catalogueWorkDetailSummary"></div>
                <div id="catalogueWorkDetailReadiness"></div><div id="catalogueWorkDetailRuntimeState"></div>
                <div id="catalogueWorkDetailBuildImpact"></div><input id="catalogueWorkDetailSearchGlobal" />
                <div id="catalogueWorkDetailPopup"></div><div id="catalogueWorkDetailPopupList"></div>
                <button id="catalogueWorkDetailOpen"></button><button id="catalogueWorkDetailSave"></button>
                <button id="catalogueWorkDetailPublication"></button><button id="catalogueWorkDetailDelete"></button>
                <div id="catalogueWorkDetailSaveMode"></div><div id="catalogueWorkDetailContext"></div>
                <div id="catalogueWorkDetailStatus"></div><div id="catalogueWorkDetailWarning"></div>
                <div id="catalogueWorkDetailResult"></div>
              </section>
              <section id="catalogueSeriesRoot">
                <div id="catalogueSeriesLoading"></div><div id="catalogueSeriesEmpty"></div>
                <div id="catalogueSeriesFields"></div><div id="catalogueSeriesReadonly"></div>
                <div id="catalogueSeriesSummary"></div><div id="catalogueSeriesReadiness"></div>
                <div id="catalogueSeriesRuntimeState"></div><div id="catalogueSeriesBuildImpact"></div>
                <input id="catalogueSeriesSearch" /><div id="catalogueSeriesPopup"></div>
                <div id="catalogueSeriesPopupList"></div><button id="catalogueSeriesOpen"></button>
                <button id="catalogueSeriesNew"></button><button id="catalogueSeriesSave"></button>
                <button id="catalogueSeriesPublication"></button><button id="catalogueSeriesDelete"></button>
                <div id="catalogueSeriesSaveMode"></div><div id="catalogueSeriesContext"></div>
                <div id="catalogueSeriesStatus"></div><div id="catalogueSeriesWarning"></div>
                <div id="catalogueSeriesResult"></div><div id="catalogueSeriesMeta"></div>
                <h2 id="catalogueSeriesMembersHeading"></h2><div id="catalogueSeriesMemberSearchRow"></div>
                <input id="catalogueSeriesMemberSearch" /><div id="catalogueSeriesMemberSearchMeta"></div>
                <input id="catalogueSeriesMemberAdd" /><button id="catalogueSeriesMemberAddButton"></button>
                <div id="catalogueSeriesMembersMeta"></div><div id="catalogueSeriesMembersStatus"></div>
                <div id="catalogueSeriesMembersResults"></div>
              </section>
              <section id="catalogueMomentRoot">
                <div id="catalogueMomentLoading"></div><div id="catalogueMomentEmpty"></div>
                <input id="catalogueMomentSearch" /><div id="catalogueMomentPopup"></div>
                <div id="catalogueMomentPopupList"></div><button id="catalogueMomentOpen"></button>
                <button id="catalogueMomentNew"></button><div id="catalogueMomentSaveMode"></div>
                <div id="catalogueMomentContext"></div><div id="catalogueMomentStatus"></div>
                <div id="catalogueMomentWarning"></div><div id="catalogueMomentResult"></div>
                <button id="catalogueMomentSave"></button><button id="catalogueMomentPublication"></button>
                <button id="catalogueMomentDelete"></button><div id="catalogueMomentFields"></div>
                <div id="catalogueMomentReadonly"></div><h2 id="catalogueMomentSideHeading"></h2>
                <div id="catalogueMomentSummary"></div><div id="catalogueMomentReadiness"></div>
                <div id="catalogueMomentRuntimeState"></div><div id="catalogueMomentBuildImpact"></div>
                <div id="catalogueMomentImportSource"></div><label id="catalogueMomentImportFileLabel"></label>
                <input id="catalogueMomentImportFile" /><div id="catalogueMomentImportFileDescription"></div>
                <div id="catalogueMomentImportSourceSummary"></div><div id="catalogueMomentImportImageGuidance"></div>
                <button id="catalogueMomentImportPreview"></button><button id="catalogueMomentImportApply"></button>
              </section>
            `;
            const detailModule = await import('/assets/studio/js/catalogue-work-detail-editor-state.js');
            const seriesModule = await import('/assets/studio/js/catalogue-series-editor-state.js');
            const momentModule = await import('/assets/studio/js/catalogue-moment-editor-state.js');
            const detailState = detailModule.createWorkDetailEditorState(
                detailModule.collectWorkDetailEditorElements(),
                { mediaConfigLoader: () => ({ source: 'detail-media' }) }
            );
            const seriesState = seriesModule.createSeriesEditorState(seriesModule.collectSeriesEditorElements(), {
                seriesTypeOptions: new Map([['custom', { label: 'Custom' }]])
            });
            const momentState = momentModule.createMomentEditorState(momentModule.collectMomentEditorElements());
            return {
                detailRoute: detailModule.WORK_DETAIL_ROUTE_STATE.route,
                detailBulkKey: detailModule.WORK_DETAIL_ROUTE_STATE.bulkIdsKey,
                detailMedia: detailState.mediaConfig,
                detailMaps: detailState.detailSearchByUid instanceof Map && detailState.bulkTouchedFields instanceof Set,
                seriesRoute: seriesModule.SERIES_ROUTE_STATE.route,
                seriesType: seriesState.seriesTypeOptions.get('custom').label,
                seriesMemberMaps: seriesState.memberSeriesIdsByWorkId instanceof Map && seriesState.baselineMemberSeriesIdsByWorkId instanceof Map,
                momentRoute: momentModule.MOMENT_ROUTE_STATE.route,
                momentImportKey: momentModule.MOMENT_ROUTE_STATE.importModeKey,
                momentBusyKeys: momentModule.MOMENT_ROUTE_STATE.busyKeys.join(','),
                momentImportAliases: momentState.importStatusNode === momentState.statusNode
                    && momentState.importWarningNode === momentState.warningNode
                    && momentState.importResultNode === momentState.resultNode,
                momentRows: Array.isArray(momentState.momentRows)
            };
        }"""
    )
    assert result["detailRoute"] == "catalogue-work-detail"
    assert result["detailBulkKey"] == "bulkDetailUids"
    assert result["detailMedia"] == {"source": "detail-media"}
    assert result["detailMaps"] is True
    assert result["seriesRoute"] == "catalogue-series"
    assert result["seriesType"] == "Custom"
    assert result["seriesMemberMaps"] is True
    assert result["momentRoute"] == "catalogue-moment"
    assert result["momentImportKey"] == "isImportMode"
    assert result["momentBusyKeys"] == "isSaving,isBuilding,isDeleting,importIsBusy"
    assert result["momentImportAliases"] is True
    assert result["momentRows"] is True


def assert_sibling_event_binders(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <button id="detailSave"></button><button id="detailPub"></button><button id="detailDelete"></button>
              <div id="detailReady"><button data-media-refresh>media</button></div>
              <button id="seriesNew"></button><button id="seriesSave"></button><button id="seriesPub"></button>
              <button id="seriesDelete"></button><input id="seriesMemberSearch" />
              <input id="seriesMemberAdd" /><button id="seriesMemberAddButton"></button>
              <div id="seriesReady"><button data-prose-import>prose</button></div>
              <div id="seriesMembers"><button data-member-primary="001"></button><button data-member-remove="002"></button></div>
              <button id="momentNew"></button><button id="momentSave"></button><button id="momentPub"></button>
              <button id="momentDelete"></button><input id="momentImportFile" />
              <button id="momentPreview"></button><button id="momentApply"></button>
              <div id="momentReady"><button data-media-refresh>media</button><button data-prose-import>prose</button></div>
            `;
            const detailEvents = await import('/assets/studio/js/catalogue-work-detail-editor-events.js');
            const seriesEvents = await import('/assets/studio/js/catalogue-series-editor-events.js');
            const momentEvents = await import('/assets/studio/js/catalogue-moment-editor-events.js');
            window.__siblingCalls = [];
            const push = (...args) => window.__siblingCalls.push(args);
            detailEvents.bindWorkDetailEditorEvents({
                readinessNode: document.getElementById('detailReady'),
                saveButton: document.getElementById('detailSave'),
                publicationButton: document.getElementById('detailPub'),
                deleteButton: document.getElementById('detailDelete')
            }, {
                bindSelectionControls: () => push('detail.bind'),
                refreshWorkDetailMedia: () => push('detail.media'),
                saveCurrentDetail: () => push('detail.save'),
                applyPublicationChange: () => push('detail.pub'),
                deleteCurrentDetail: () => push('detail.delete')
            });
            seriesEvents.bindSeriesEditorEvents({
                readinessNode: document.getElementById('seriesReady'),
                newButton: document.getElementById('seriesNew'),
                saveButton: document.getElementById('seriesSave'),
                publicationButton: document.getElementById('seriesPub'),
                deleteButton: document.getElementById('seriesDelete'),
                memberSearchNode: document.getElementById('seriesMemberSearch'),
                memberAddNode: document.getElementById('seriesMemberAdd'),
                memberAddButton: document.getElementById('seriesMemberAddButton'),
                membersResultsNode: document.getElementById('seriesMembers')
            }, {
                bindSelectionControls: () => push('series.bind'),
                importSeriesProse: () => push('series.prose'),
                setNewSeriesMode: () => push('series.new'),
                saveCurrentSeries: () => push('series.save'),
                applyPublicationChange: () => push('series.pub'),
                deleteCurrentSeries: () => push('series.delete'),
                updateMemberList: () => push('series.memberSearch'),
                addMember: () => push('series.add'),
                makeMemberPrimary: (workId) => push('series.primary', workId),
                removeMember: (workId) => push('series.remove', workId)
            });
            momentEvents.bindMomentEditorEvents({
                newButton: document.getElementById('momentNew'),
                saveButton: document.getElementById('momentSave'),
                publicationButton: document.getElementById('momentPub'),
                deleteButton: document.getElementById('momentDelete'),
                importFileNode: document.getElementById('momentImportFile'),
                importPreviewButton: document.getElementById('momentPreview'),
                importApplyButton: document.getElementById('momentApply'),
                readinessNode: document.getElementById('momentReady')
            }, {
                bindSelectionControls: () => push('moment.bind'),
                enterImportMode: () => push('moment.new'),
                saveCurrentMoment: () => push('moment.save'),
                applyPublicationChange: () => push('moment.pub'),
                deleteCurrentMoment: () => push('moment.delete'),
                updateImportFile: (value) => push('moment.file', value),
                previewMomentImport: () => push('moment.preview'),
                applyMomentImport: () => push('moment.apply'),
                refreshMomentMedia: () => push('moment.media'),
                importMomentProse: () => push('moment.prose')
            });
        }"""
    )
    for selector in [
        "#detailReady [data-media-refresh]",
        "#detailSave",
        "#detailPub",
        "#detailDelete",
        "#seriesReady [data-prose-import]",
        "#seriesNew",
        "#seriesSave",
        "#seriesPub",
        "#seriesDelete",
        "#seriesMemberSearch",
        "#seriesMemberAddButton",
        "#seriesMembers [data-member-primary]",
        "#seriesMembers [data-member-remove]",
        "#momentNew",
        "#momentSave",
        "#momentPub",
        "#momentDelete",
        "#momentPreview",
        "#momentApply",
        "#momentReady [data-media-refresh]",
        "#momentReady [data-prose-import]",
    ]:
        if selector.endswith("Search"):
            page.fill(selector, "a")
        else:
            page.click(selector)
    page.fill("#seriesMemberAdd", "enter")
    page.press("#seriesMemberAdd", "Enter")
    page.fill("#momentImportFile", "keys.md")
    calls = page.evaluate("window.__siblingCalls")
    assert calls == [
        ["detail.bind"],
        ["series.bind"],
        ["moment.bind"],
        ["detail.media"],
        ["detail.save"],
        ["detail.pub"],
        ["detail.delete"],
        ["series.prose"],
        ["series.new"],
        ["series.save"],
        ["series.pub"],
        ["series.delete"],
        ["series.memberSearch"],
        ["series.add"],
        ["series.primary", "001"],
        ["series.remove", "002"],
        ["moment.new"],
        ["moment.save"],
        ["moment.pub"],
        ["moment.delete"],
        ["moment.preview"],
        ["moment.apply"],
        ["moment.media"],
        ["moment.prose"],
        ["series.add"],
        ["moment.file", "keys.md"],
    ]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_sibling_state_factories(page)
            assert_sibling_event_binders(page)
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
