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
                <div id="catalogueWorkDetailFields"></div><input id="catalogueWorkDetailSearchGlobal" />
                <div id="catalogueWorkDetailPopup"></div><div id="catalogueWorkDetailPopupList"></div>
                <button id="catalogueWorkDetailOpen"></button><button id="catalogueWorkDetailSave"></button>
                <button id="catalogueWorkDetailDelete"></button>
                <div id="catalogueWorkDetailSaveMode"></div><div id="catalogueWorkDetailContext"></div>
                <div id="catalogueWorkDetailStatus"></div><div id="catalogueWorkDetailWarning"></div>
                <div id="catalogueWorkDetailResult"></div>
              </section>
              <section id="catalogueSeriesRoot">
                <div id="catalogueSeriesLoading"></div><div id="catalogueSeriesEmpty"></div>
                <div id="catalogueSeriesFields"></div>
                <input id="catalogueSeriesSearch" /><div id="catalogueSeriesPopup"></div>
                <div id="catalogueSeriesPopupList"></div><button id="catalogueSeriesOpen"></button>
                <button id="catalogueSeriesNew"></button><button id="catalogueSeriesSave"></button>
                <button id="catalogueSeriesPublication"></button><button id="catalogueSeriesDelete"></button>
                <div id="catalogueSeriesSaveMode"></div><div id="catalogueSeriesContext"></div>
                <div id="catalogueSeriesStatus"></div><div id="catalogueSeriesWarning"></div>
                <div id="catalogueSeriesResult"></div>
                <div id="catalogueSeriesSidePanel"></div>
                <h2 id="catalogueSeriesMembersHeading"></h2><div id="catalogueSeriesMembersActions"></div>
                <div id="catalogueSeriesMembersMeta"></div>
                <div id="catalogueSeriesMembersResults"></div>
              </section>
            `;
            const seriesModule = await import('/studio/app/frontend/js/catalogue-series-editor-state.js');
            const seriesState = seriesModule.createSeriesEditorState(seriesModule.collectSeriesEditorElements(), {
                seriesTypeOptions: new Map([['custom', { label: 'Custom' }]])
            });
            return {
                seriesRoute: seriesModule.SERIES_ROUTE_STATE.route,
                seriesType: seriesState.seriesTypeOptions.get('custom').label,
                seriesMemberMaps: seriesState.memberSeriesIdsByWorkId instanceof Map && seriesState.baselineMemberSeriesIdsByWorkId instanceof Map
            };
        }"""
    )
    assert result["seriesRoute"] == "catalogue-series"
    assert result["seriesType"] == "Custom"
    assert result["seriesMemberMaps"] is True


def assert_sibling_event_binders(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <button id="seriesNew"></button><button id="seriesSave"></button><button id="seriesPub"></button>
              <button id="seriesDelete"></button>
              <div id="seriesReady"></div>
              <div id="seriesMembers"></div>
            `;
            const seriesEvents = await import('/studio/app/frontend/js/catalogue-series-editor-events.js');
            window.__siblingCalls = [];
            const push = (...args) => window.__siblingCalls.push(args);
            seriesEvents.bindSeriesEditorEvents({
                readinessNode: document.getElementById('seriesReady'),
                newButton: document.getElementById('seriesNew'),
                saveButton: document.getElementById('seriesSave'),
                publicationButton: document.getElementById('seriesPub'),
                deleteButton: document.getElementById('seriesDelete')
            }, {
                bindSelectionControls: () => push('series.bind'),
                setNewSeriesMode: () => push('series.new'),
                saveCurrentSeries: () => push('series.save'),
                applyPublicationChange: () => push('series.pub'),
                deleteCurrentSeries: () => push('series.delete')
            });
        }"""
    )
    for selector in [
        "#seriesNew",
        "#seriesSave",
        "#seriesPub",
        "#seriesDelete",
    ]:
        if selector.endswith("Search"):
            page.fill(selector, "a")
        else:
            page.click(selector)
    calls = page.evaluate("window.__siblingCalls")
    assert calls == [
        ["series.bind"],
        ["series.new"],
        ["series.save"],
        ["series.pub"],
        ["series.delete"],
    ]


def assert_series_shared_search(page: Page) -> None:
    page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <section id="seriesSearchFixture">
                <input id="catalogueSeriesSearch" />
                <div id="catalogueSeriesPopup"><span id="catalogueSeriesPopupList" hidden></span></div>
                <button id="catalogueSeriesOpen"></button>
              </section>
            `;
            const selectionModule = await import('/studio/app/frontend/js/catalogue-series-selection.js');
            const records = new Map([
                ['001', { series_id: '001', title: 'Red Forms' }],
                ['002', { series_id: '002', title: 'Blue Forms' }],
                ['010', { series_id: '010', title: 'Red Archive' }]
            ]);
            const state = {
                mode: 'single',
                seriesById: records,
                searchNode: document.getElementById('catalogueSeriesSearch'),
                popupNode: document.getElementById('catalogueSeriesPopup'),
                popupListNode: document.getElementById('catalogueSeriesPopupList'),
                openButton: document.getElementById('catalogueSeriesOpen'),
                draft: {},
                rebuildPending: true
            };
            window.__seriesSearchCalls = [];
            const context = {
                loadSeriesLookupRecord: async (seriesId) => {
                    window.__seriesSearchCalls.push(['load', seriesId]);
                    return { series: records.get(seriesId), record_hash: `hash-${seriesId}` };
                },
                setLoadedSeries: (seriesId, record, options) => {
                    window.__seriesSearchCalls.push(['loaded', seriesId, record.title, options.recordHash]);
                },
                refreshBuildPreview: async () => window.__seriesSearchCalls.push(['refresh']),
                updateEditorState: () => window.__seriesSearchCalls.push(['update']),
                saveCurrentSeries: async () => window.__seriesSearchCalls.push(['save']),
                setEmptySearchMode: () => window.__seriesSearchCalls.push(['empty']),
                text: (_key, fallback) => fallback
            };
            selectionModule.bindSeriesSelectionControls(state, context);
            window.__seriesSelectionState = state;
        }"""
    )
    page.fill("#catalogueSeriesSearch", "red")
    page.wait_for_selector('#catalogueSeriesSearchList [data-search-list-value="001"]', state="attached")
    result = page.evaluate(
        """() => ({
            values: Array.from(document.querySelectorAll('#catalogueSeriesSearchList [data-search-list-value]')).map((node) => node.dataset.searchListValue),
            labels: Array.from(document.querySelectorAll('#catalogueSeriesSearchList .catalogueSeriesSearch__title')).map((node) => node.textContent)
        })"""
    )
    assert result == {
        "values": ["001", "010"],
        "labels": ["Red Forms", "Red Archive"],
    }
    page.press("#catalogueSeriesSearch", "Enter")
    page.wait_for_function("() => window.__seriesSearchCalls.some((call) => call[0] === 'loaded' && call[1] === '001')")
    assert page.evaluate("document.querySelector('#catalogueSeriesSearch').value") == "001 Red Forms"

    page.evaluate(
        """() => {
            window.__seriesSelectionState.mode = 'new';
            window.__seriesSelectionState.draft = {};
            window.__seriesSearchCalls.length = 0;
        }"""
    )
    page.fill("#catalogueSeriesSearch", "12")
    new_mode_result = page.evaluate(
        """() => ({
            draftSeriesId: window.__seriesSelectionState.draft.series_id,
            popupHidden: document.querySelector('#catalogueSeriesSearchList').hidden,
            calls: window.__seriesSearchCalls
        })"""
    )
    assert new_mode_result == {
        "draftSeriesId": "012",
        "popupHidden": True,
        "calls": [["update"]],
    }


def assert_shared_message_clearer(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <section id="messageRoot">
                <p id="messageStatus"></p>
                <button id="messageButton">Clear</button>
              </section>
            `;
            const messageModule = await import('/studio/app/frontend/js/catalogue-editor-message-controller.js');
            const statusNode = document.getElementById('messageStatus');
            const root = document.getElementById('messageRoot');
            const controller = messageModule.createCatalogueEditorMessageController({ statusNode });
            let renderCount = 0;
            controller.setActionTextWithState(statusNode, 'Saved.', 'success');
            const before = statusNode.textContent;
            messageModule.bindCatalogueEditorActionMessageClearer(root, controller, {
                isBusy: () => false,
                renderMessages: () => {
                    renderCount += 1;
                    controller.render();
                }
            });
            document.getElementById('messageButton').click();
            return {
                before,
                after: statusNode.textContent,
                hasActionMessages: controller.hasActionMessages,
                renderCount
            };
        }"""
    )
    assert result == {
        "before": "Saved.",
        "after": "",
        "hasActionMessages": False,
        "renderCount": 1,
    }


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_sibling_state_factories(page)
            assert_sibling_event_binders(page)
            assert_series_shared_search(page)
            assert_shared_message_clearer(page)
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
