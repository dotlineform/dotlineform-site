#!/usr/bin/env python3
"""Smoke-check shared Docs Viewer modal keyboard focus behavior."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_shared_focus_trap(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const modalModule = await import('/docs-viewer/runtime/js/management/docs-viewer-modal-lifecycle.js');
          document.documentElement.setAttribute('data-theme', 'dark');
          for (const href of [
            '/site/docs-viewer/static/css/docs-viewer-theme.css',
            '/site/docs-viewer/static/css/docs-viewer.css',
            '/docs-viewer/static/css/docs-viewer-manage.css'
          ]) {
            await new Promise((resolve, reject) => {
              const stylesheet = document.createElement('link');
              stylesheet.rel = 'stylesheet';
              stylesheet.href = href;
              stylesheet.addEventListener('load', resolve, { once: true });
              stylesheet.addEventListener('error', reject, { once: true });
              document.head.appendChild(stylesheet);
            });
          }
          document.body.innerHTML = `
            <button id="outside">Outside</button>
            <div class="docsViewer__modal" id="modal">
              <select id="scope"><option>studio</option></select>
              <select id="file" size="10"><option>one.md</option></select>
              <button id="cancel">Cancel</button>
              <button id="run">Import</button>
            </div>`;
          const modal = document.querySelector('#modal');

          function pressTab(shiftKey = false) {
            const event = new KeyboardEvent('keydown', {
              key: 'Tab',
              shiftKey,
              bubbles: true,
              cancelable: true
            });
            const trapped = modalModule.trapDocsViewerModalFocus(event, modal);
            return {
              trapped,
              prevented: event.defaultPrevented,
              activeId: document.activeElement && document.activeElement.id
            };
          }

          document.querySelector('#scope').focus();
          const internalForward = pressTab();
          document.querySelector('#run').focus();
          const wrapForward = pressTab();
          const wrapBackward = pressTab(true);
          document.querySelector('#outside').focus();
          const recoverOutside = pressTab();
          return { internalForward, wrapForward, wrapBackward, recoverOutside };
        }"""
    )
    expected = {
        "internalForward": {
            "trapped": True,
            "prevented": True,
            "activeId": "file",
        },
        "wrapForward": {
            "trapped": True,
            "prevented": True,
            "activeId": "scope",
        },
        "wrapBackward": {
            "trapped": True,
            "prevented": True,
            "activeId": "run",
        },
        "recoverOutside": {
            "trapped": True,
            "prevented": True,
            "activeId": "scope",
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected shared modal focus traversal: {result!r}")


def assert_choice_modal_radio_navigation(page: Page) -> None:
    page.evaluate(
        """async () => {
          const modalModule = await import('/docs-viewer/runtime/js/management/docs-viewer-management-modal-shell.js');
          document.body.innerHTML = `
            <main class="docsViewer" id="root">
              <button id="open">Open</button>
              <div style="height: 2000px"></div>
            </main>`;
          window.scrollTo(0, 400);
          document.querySelector('#open').addEventListener('click', () => {
            window.choiceModalResult = modalModule.openDocsViewerChoiceModal({
              root: document.querySelector('#root'),
              title: 'Choose scope',
              value: 'analysis',
              choices: [
                { value: 'analysis', label: 'analysis' },
                { value: 'library', label: 'library' },
                { value: 'moments', label: 'moments' }
              ],
              primaryLabel: 'Preview copy',
              cancelLabel: 'Cancel'
            });
          });
        }"""
    )
    page.locator("#open").click()
    page.wait_for_function("document.activeElement?.value === 'analysis'")
    page.evaluate("window.scrollTo(0, 400)")

    def state() -> dict[str, object]:
        return page.evaluate(
            """() => {
              const active = document.activeElement;
              const focusStyle = getComputedStyle(active);
              return {
                active: active?.value || active?.dataset?.role || active?.textContent || '',
                checked: document.querySelector('input[type="radio"]:checked')?.value || '',
                scrollY: window.scrollY,
                outlineStyle: focusStyle.outlineStyle,
                outlineWidth: focusStyle.outlineWidth
              };
            }"""
        )

    opened = state()
    page.keyboard.press("Tab")
    tab_to_cancel = state()
    page.keyboard.press("Shift+Tab")
    shift_tab_to_group = state()
    page.keyboard.press("ArrowDown")
    down_to_library = state()
    page.keyboard.press("ArrowDown")
    down_to_moments = state()
    page.keyboard.press("ArrowDown")
    down_wraps = state()
    page.keyboard.press("ArrowUp")
    up_wraps = state()
    page.keyboard.press("Escape")
    closed = page.evaluate(
        """async () => {
          const result = await window.choiceModalResult;
          await new Promise(resolve => setTimeout(resolve, 0));
          return {
            confirmed: Boolean(result && result.confirmed),
            focusReturnedTo: document.activeElement?.id || '',
            htmlOverflow: document.documentElement.style.overflow,
            bodyOverflow: document.body.style.overflow,
            scrollY: window.scrollY
          };
        }"""
    )

    result = {
        "opened": opened,
        "tabToCancel": tab_to_cancel,
        "shiftTabToGroup": shift_tab_to_group,
        "downToLibrary": down_to_library,
        "downToMoments": down_to_moments,
        "downWraps": down_wraps,
        "upWraps": up_wraps,
        "closed": closed,
    }
    expected = {
        "opened": {
            "active": "analysis",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "none",
            "outlineWidth": "0px",
        },
        "tabToCancel": {
            "active": "modal-cancel",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "shiftTabToGroup": {
            "active": "analysis",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "downToLibrary": {
            "active": "library",
            "checked": "library",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "downToMoments": {
            "active": "moments",
            "checked": "moments",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "downWraps": {
            "active": "analysis",
            "checked": "analysis",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "upWraps": {
            "active": "moments",
            "checked": "moments",
            "scrollY": 400,
            "outlineStyle": "solid",
            "outlineWidth": "2px",
        },
        "closed": {
            "confirmed": False,
            "focusReturnedTo": "open",
            "htmlOverflow": "",
            "bodyOverflow": "",
            "scrollY": 400,
        },
    }
    if result != expected:
        raise AssertionError(f"unexpected choice modal radio navigation: {result!r}")


def assert_metadata_status_list_selection(page: Page) -> None:
    page.route(
        "**/docs-viewer/runtime/js/shared/docs-viewer-render.js",
        lambda route: route.fulfill(
            path=str(REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-render.js"),
            content_type="text/javascript",
        ),
    )
    page.evaluate(
        """async () => {
          const modalModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-modals.js'
          );
          const shellModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js'
          );
          document.body.innerHTML = `
            <main class="docsViewer" id="root">
              <button id="open">Open</button>
              <div data-docs-viewer-management-shell-mount></div>
            </main>`;
          const root = document.querySelector('#root');
          const refs = shellModule.renderDocsViewerManagementShell({
            document,
            root,
            mount: root.querySelector('[data-docs-viewer-management-shell-mount]')
          });
          const doc = {
            doc_id: 'status-doc',
            title: 'Status document',
            summary: '',
            date: '',
            date_display: '',
            ui_status: 'done',
            parent_id: '',
            viewable: true
          };
          const management = {
            managementBusy: false,
            metadataEditingDocId: ''
          };
          const controller = modalModule.createDocsViewerManagementModalController({
            refs,
            documentIndex: {
              docsById: new Map([[doc.doc_id, doc]])
            },
            management,
            scopeConfig: {
              uiStatuses: [
                { ui_status: 'draft', label: 'Draft', emoji: '📝' },
                { ui_status: 'done', label: 'Done', emoji: '✅' }
              ]
            },
            callbacks: {
              currentActiveDoc: () => doc,
              hideContextMenu: () => {},
              isDocNonViewable: () => false,
              metadataParentOptions: () => [{ value: '', label: 'Root' }],
              onMetadataSubmit: () => {},
              onSettingsSubmit: event => event.preventDefault(),
              viewerScope: () => 'studio'
            }
          });
          controller.wireEvents();
          void controller.openMetadataModal(doc, {
            target: { scope: 'studio', doc_id: doc.doc_id },
            showParent: true
          });
        }"""
    )
    status_input = page.locator("#docsViewerMetadataStatusInput")
    initial = status_input.evaluate(
        """select => ({
          labels: Array.from(select.options).map(option => option.textContent),
          selectedIndex: select.selectedIndex,
          value: select.value
        })"""
    )
    if initial != {
        "labels": ["📝 Draft", "✅ Done"],
        "selectedIndex": 1,
        "value": "done",
    }:
        raise AssertionError(f"unexpected metadata status options: {initial!r}")

    status_input.locator('option[value="done"]').click()
    cleared_by_click = status_input.evaluate(
        "select => ({ selectedIndex: select.selectedIndex, value: select.value })"
    )
    if cleared_by_click != {"selectedIndex": -1, "value": ""}:
        raise AssertionError(f"clicking selected status did not clear it: {cleared_by_click!r}")

    status_input.select_option("draft")
    status_input.focus()
    page.keyboard.press("Delete")
    cleared_by_keyboard = status_input.evaluate(
        "select => ({ selectedIndex: select.selectedIndex, value: select.value })"
    )
    if cleared_by_keyboard != {"selectedIndex": -1, "value": ""}:
        raise AssertionError(f"Delete did not clear metadata status: {cleared_by_keyboard!r}")


def assert_metadata_parent_duplicate_title_selection(page: Page) -> None:
    page.evaluate(
        """async () => {
          const modalModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-modals.js'
          );
          const shellModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js'
          );
          document.body.innerHTML = `
            <main class="docsViewer" id="root">
              <div data-docs-viewer-management-shell-mount></div>
            </main>`;
          const root = document.querySelector('#root');
          const refs = shellModule.renderDocsViewerManagementShell({
            document,
            root,
            mount: root.querySelector('[data-docs-viewer-management-shell-mount]')
          });
          const doc = {
            doc_id: 'editing-doc',
            title: 'Editing document',
            summary: '',
            date: '',
            date_display: '',
            ui_status: 'draft',
            parent_id: 'd-semantic-b',
            viewable: true
          };
          const controller = modalModule.createDocsViewerManagementModalController({
            refs,
            documentIndex: {
              docsById: new Map([[doc.doc_id, doc]])
            },
            management: {
              managementBusy: false,
              metadataEditingDocId: ''
            },
            scopeConfig: {
              uiStatuses: [
                { ui_status: 'draft', label: 'Draft', emoji: '📝' }
              ]
            },
            callbacks: {
              hideContextMenu: () => {},
              isDocNonViewable: () => false,
              metadataParentOptions: () => [
                { value: '', label: 'Root' },
                { value: 'd-semantic-a', label: 'Semantic Tokens' },
                { value: 'd-semantic-b', label: 'Semantic Tokens' },
                { value: 'd-other', label: 'Other parent' }
              ],
              onMetadataSubmit: () => {},
              onSettingsSubmit: event => event.preventDefault(),
              viewerScope: () => 'studio'
            }
          });
          controller.wireEvents();
          void controller.openMetadataModal(doc, {
            target: { scope: 'studio', doc_id: doc.doc_id },
            showParent: true
          });
          window.metadataParentDuplicateTitleFixture = { controller, doc, refs };
        }"""
    )
    parent_input = page.locator("#docsViewerMetadataParentInput")
    initial = page.evaluate(
        """() => {
          const fixture = window.metadataParentDuplicateTitleFixture;
          return {
            display: fixture.refs.metadataParentInput.value,
            resolved: fixture.controller.resolveMetadataParentId(fixture.doc)
          };
        }"""
    )
    if initial != {"display": "Semantic Tokens", "resolved": "d-semantic-b"}:
        raise AssertionError(f"current duplicate-title parent identity was lost: {initial!r}")

    parent_input.fill("Semantic")
    suggestions = page.locator("#docsViewerMetadataParentPopup [data-parent-index]")
    suggestion_details = suggestions.evaluate_all(
        """buttons => buttons.map(button => ({
          title: button.querySelector('.docsViewer__parentOptionTitle')?.textContent || '',
          meta: button.querySelector('.docsViewer__parentOptionMeta')?.textContent || ''
        }))"""
    )
    expected_suggestions = [
        {"title": "Semantic Tokens", "meta": "d-semantic-a"},
        {"title": "Semantic Tokens", "meta": "d-semantic-b"},
    ]
    if suggestion_details != expected_suggestions:
        raise AssertionError(f"duplicate-title suggestions are not distinguishable: {suggestion_details!r}")

    suggestions.nth(0).click()
    mouse_selection = page.evaluate(
        """() => {
          const fixture = window.metadataParentDuplicateTitleFixture;
          return {
            display: fixture.refs.metadataParentInput.value,
            popupHidden: fixture.refs.metadataParentPopup.hidden,
            resolved: fixture.controller.resolveMetadataParentId(fixture.doc)
          };
        }"""
    )
    if mouse_selection != {
        "display": "Semantic Tokens",
        "popupHidden": True,
        "resolved": "d-semantic-a",
    }:
        raise AssertionError(f"mouse selection lost duplicate-title identity: {mouse_selection!r}")

    parent_input.fill("Semantic Tokens")
    ambiguous_manual_entry = page.evaluate(
        """() => {
          const fixture = window.metadataParentDuplicateTitleFixture;
          return fixture.controller.resolveMetadataParentId(fixture.doc);
        }"""
    )
    if ambiguous_manual_entry is not None:
        raise AssertionError(
            f"manual duplicate-title entry should remain ambiguous: {ambiguous_manual_entry!r}"
        )

    parent_input.fill("d-semantic-a")
    exact_id_entry = page.evaluate(
        """() => {
          const fixture = window.metadataParentDuplicateTitleFixture;
          return fixture.controller.resolveMetadataParentId(fixture.doc);
        }"""
    )
    if exact_id_entry != "d-semantic-a":
        raise AssertionError(f"exact parent id entry no longer resolves: {exact_id_entry!r}")

    parent_input.fill("Semantic")
    parent_input.press("ArrowDown")
    parent_input.press("Enter")
    keyboard_selection = page.evaluate(
        """() => {
          const fixture = window.metadataParentDuplicateTitleFixture;
          return {
            display: fixture.refs.metadataParentInput.value,
            resolved: fixture.controller.resolveMetadataParentId(fixture.doc)
          };
        }"""
    )
    if keyboard_selection != {
        "display": "Semantic Tokens",
        "resolved": "d-semantic-b",
    }:
        raise AssertionError(f"keyboard selection lost duplicate-title identity: {keyboard_selection!r}")


def assert_sub_scope_metadata_omits_parent_field(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const modalModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-modals.js'
          );
          const shellModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js'
          );
          document.body.innerHTML = `
            <main class="docsViewer" id="root">
              <div data-docs-viewer-management-shell-mount></div>
            </main>`;
          const root = document.querySelector('#root');
          const refs = shellModule.renderDocsViewerManagementShell({
            document,
            root,
            mount: root.querySelector('[data-docs-viewer-management-shell-mount]')
          });
          const doc = {
            doc_id: 'detail-doc',
            title: 'Detail',
            summary: 'Full local summary',
            date: '2026-07-27',
            date_display: 'July 2026',
            ui_status: 'draft',
            group: 'subject',
            viewable: false
          };
          const controller = modalModule.createDocsViewerManagementModalController({
            refs,
            documentIndex: {
              docsById: new Map([['selected-fallback', {
                doc_id: 'selected-fallback',
                title: 'Must not be used'
              }]])
            },
            management: {
              managementBusy: false,
              metadataEditingDocId: 'selected-fallback'
            },
            scopeConfig: {
              uiStatuses: [
                { ui_status: 'draft', label: 'Draft', emoji: '📝' },
                { ui_status: 'done', label: 'Done', emoji: '✅' }
              ]
            },
            callbacks: {
              hideContextMenu: () => {},
              isDocNonViewable: record => record.viewable === false,
              metadataParentOptions: () => {
                throw new Error('Sub-scope modal must not build Parent options.');
              },
              onMetadataSubmit: () => {},
              onSettingsSubmit: event => event.preventDefault(),
              viewerScope: () => 'studio'
            }
          });
          controller.wireEvents();
          void controller.openMetadataModal(doc, {
            target: {
              scope: 'studio',
              sub_scope: 'tags',
              doc_id: 'detail-doc'
            },
            showParent: false,
            choices: {
              ui_status: ['draft'],
              group: ['subject', 'domain', 'form', 'theme']
            }
          });
          return {
            visibleNames: Array.from(
              refs.metadataForm.querySelectorAll('input:not([disabled]), textarea:not([disabled]), select:not([disabled])')
            ).map(node => node.name).filter(Boolean),
            parentHidden: refs.metadataParentField.hidden,
            parentDisabled: refs.metadataParentInput.disabled,
            title: refs.metadataTitleInput.value,
            summary: refs.metadataSummaryInput.value,
            date: refs.metadataDateInput.value,
            dateDisplay: refs.metadataDateDisplayInput.value,
            status: refs.metadataStatusInput.value,
            group: refs.metadataGroupInput.value,
            groupOptions: Array.from(refs.metadataGroupInput.options).map(option => option.value),
            nonViewable: refs.metadataNonViewableInput.checked,
            editingDocId: refs.metadataDocId.textContent
          };
        }"""
    )
    if result != {
        "visibleNames": [
            "title",
            "summary",
            "date",
            "date_display",
            "ui_status",
            "group",
            "non_viewable",
        ],
        "parentHidden": True,
        "parentDisabled": True,
        "title": "Detail",
        "summary": "Full local summary",
        "date": "2026-07-27",
        "dateDisplay": "July 2026",
        "status": "draft",
        "group": "subject",
        "groupOptions": ["", "subject", "domain", "form", "theme"],
        "nonViewable": True,
        "editingDocId": "detail-doc",
    }:
        raise AssertionError(f"unexpected sub-scope metadata field shape: {result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repository root to serve.")
    args = parser.parse_args(argv)
    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(base_url, wait_until="domcontentloaded")
                assert_shared_focus_trap(page)
                assert_choice_modal_radio_navigation(page)
                assert_metadata_status_list_selection(page)
                assert_metadata_parent_duplicate_title_selection(page)
                assert_sub_scope_metadata_omits_parent_field(page)
            finally:
                browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer modal focus modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
