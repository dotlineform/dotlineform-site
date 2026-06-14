#!/usr/bin/env python3
"""Smoke-check the shared Search List JavaScript component contract."""

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


def assert_shared_search_list_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <style>
                .sharedSearchList__popup {
                  box-sizing: border-box;
                  max-height: 64px;
                  overflow: auto;
                  padding: 4px 4px 8px;
                }
                .sharedSearchList__option {
                  border: 0;
                  display: grid;
                  grid-template-columns: minmax(0, 1fr) auto;
                  min-height: 28px;
                  width: 100%;
                }
              </style>
              <input id="sharedSearchSmoke" value="current">
              <div id="sharedSearchSmokePopup"></div>
              <input id="sharedSearchDefault">
              <div id="sharedSearchDefaultPopup"></div>
            `;
            const module = await import('/shared/frontend/js/search-list.js');
            const input = document.getElementById('sharedSearchSmoke');
            const popup = document.getElementById('sharedSearchSmokePopup');
            const commits = [];
            const transients = [];
            const cancels = [];
            const controller = module.bindSearchList(input, popup, {
                id: 'sharedSearchSmokeList',
                maxOptions: 20,
                loadOptions: async () => [
                    { value: 'natural', type: 'folder' },
                    { value: 'nerve', type: 'folder' },
                    { value: 'international', type: 'folder' },
                    { value: 'nimbus', type: 'folder' },
                    { value: 'north', type: 'folder' },
                    { value: 'number', type: 'folder' },
                    { value: 'needle', type: 'folder' },
                    { value: 'near', type: 'folder' }
                ],
                filterOptions: (options, query) => options.filter((option) => option.value.startsWith(query.toLowerCase())),
                getOptionValue: (option) => option.value,
                renderOption: (option) => `<span class="searchSmokeTitle">${option.value}</span><span class="searchSmokeMeta">${option.type}</span>`,
                onTransientInput: ({ value }) => transients.push(value),
                onCancel: ({ value }) => cancels.push(value),
                onCommit: (option, { value }) => commits.push({ option: option.value, value })
            });

            input.focus();
            await controller.refresh();
            const selectedText = input.selectionStart === 0 && input.selectionEnd === input.value.length;

            input.value = 'n';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await controller.refresh();
            const prefixMatches = Array.from(popup.querySelectorAll('[data-search-list-value]')).map((node) => node.dataset.searchListValue);
            const hasTwoColumnMarkup = Boolean(popup.querySelector('.searchSmokeTitle') && popup.querySelector('.searchSmokeMeta'));

            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, cancelable: true }));
            const firstSelected = popup.querySelector('[aria-selected="true"]')?.dataset.searchListValue || '';
            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true, cancelable: true }));
            const activeAfterUp = input.getAttribute('aria-activedescendant');

            for (let index = 0; index < 7; index += 1) {
                input.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, cancelable: true }));
            }
            const activeNode = document.getElementById(input.getAttribute('aria-activedescendant'));
            const popupStyle = window.getComputedStyle(popup);
            const bottomPadding = parseFloat(popupStyle.paddingBottom) || 0;
            const activeRect = activeNode.getBoundingClientRect();
            const popupRect = popup.getBoundingClientRect();
            const scrollResult = {
                scrollTop: popup.scrollTop,
                activeBottom: activeRect.bottom,
                visibleBottom: popupRect.bottom - bottomPadding
            };

            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
            await new Promise((resolve) => setTimeout(resolve, 0));

            input.value = 'temporary';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await controller.refresh();
            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));

            const defaultInput = document.getElementById('sharedSearchDefault');
            const defaultPopup = document.getElementById('sharedSearchDefaultPopup');
            const defaultController = module.bindSearchList(defaultInput, defaultPopup, {
                id: 'sharedSearchDefaultList',
                loadOptions: async () => ['natural', 'international', 'nerve']
            });
            defaultInput.focus();
            defaultInput.value = 'at';
            defaultInput.dispatchEvent(new Event('input', { bubbles: true }));
            await defaultController.refresh();
            const defaultContainsMatches = Array.from(defaultPopup.querySelectorAll('[data-search-list-value]')).map((node) => node.dataset.searchListValue);

            return {
                activeAfterUp,
                cancels,
                commits,
                defaultContainsMatches,
                firstSelected,
                hasTwoColumnMarkup,
                inputValueAfterEscape: input.value,
                popupHiddenAfterEscape: popup.hidden,
                prefixMatches,
                scrollResult,
                selectedText,
                transients
            };
        }"""
    )
    assert result["selectedText"] is True
    assert result["prefixMatches"] == ["natural", "nerve", "nimbus", "north", "number", "needle", "near"]
    assert "international" not in result["prefixMatches"]
    assert result["hasTwoColumnMarkup"] is True
    assert result["firstSelected"] == "natural"
    assert result["activeAfterUp"] is None
    assert result["scrollResult"]["scrollTop"] > 0
    assert result["scrollResult"]["activeBottom"] <= result["scrollResult"]["visibleBottom"], result["scrollResult"]
    assert result["commits"] == [{"option": "near", "value": "near"}]
    assert result["transients"] == ["n", "temporary"]
    assert result["cancels"] == ["near"]
    assert result["inputValueAfterEscape"] == "near"
    assert result["popupHiddenAfterEscape"] is True
    assert result["defaultContainsMatches"] == ["natural", "international"]


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_shared_search_list_contract(page)
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
