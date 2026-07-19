#!/usr/bin/env python3
"""Smoke-check the standalone Docs Viewer service manage route."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import sys
from pathlib import Path
from threading import Thread
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


DOCS_VIEWER_DOC_ID = "d-20260424-000000-50b63f"


def start_server() -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )
    server = DocsViewerServer(("127.0.0.1", 0), REPO_ROOT, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(config, port=server.server_address[1], base_url=base_url)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, base_url


def query_value(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def request_paths(urls: list[str]) -> set[str]:
    return {urlparse(url).path for url in urls}


def read_json_url(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_service_basics(base_url: str) -> None:
    health = read_json_url(f"{base_url}/health")
    if health.get("service") != "docs_viewer" or health.get("ok") is not True:
        raise AssertionError(f"unexpected health response: {health!r}")

    capabilities = read_json_url(f"{base_url}/capabilities")
    studio_caps = capabilities.get("capabilities", {}).get("scopes", {}).get("studio", {})
    if capabilities.get("capabilities", {}).get("docs_management") is not True:
        raise AssertionError(f"expected Docs Viewer management to be enabled: {capabilities!r}")
    if studio_caps.get("available") is not True or studio_caps.get("generated_data_reads") is not True:
        raise AssertionError(f"expected real Studio generated data reads: {studio_caps!r}")


def assert_origin_rejection(base_url: str) -> None:
    payload = json.dumps({"scope": "studio", "doc_id": DOCS_VIEWER_DOC_ID}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/docs/delete-preview",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Origin": "https://example.com",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise AssertionError(f"expected disallowed Origin to return 403, got {error.code}") from error
    else:
        raise AssertionError("disallowed Origin should be rejected")


def wait_for_manage_doc(page: Page, title: str, timeout_ms: int) -> None:
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_function(
        """expectedTitle => {
            const heading = document.querySelector("#docsViewerContent h1");
            const actions = document.querySelector('[data-docs-viewer-control-surface-mount="app-management"]');
            const button = document.querySelector("#docsViewerManageActionsButton");
            return heading &&
                heading.textContent.trim() === expectedTitle &&
                actions &&
                !actions.hidden &&
                button &&
                !button.disabled;
        }""",
        arg=title,
        timeout=timeout_ms,
    )


def manage_route_state(page: Page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """async root => {
            const routeConfigUrl = root.dataset.routeConfigUrl || "";
            const payload = await fetch(routeConfigUrl).then(response => response.json());
            const routeConfig = (payload.routes || []).find(record => record.route_id === root.dataset.routeId) || {};
            return {
                appKind: root.dataset.docsViewerAppKind || "",
                managementUi: root.dataset.managementUi || "",
                sourceService: root.dataset.sourceService || "",
                ready: root.dataset.docsViewerReady || "",
                busy: root.dataset.docsViewerBusy || "",
                includeScopeParam: root.dataset.includeScopeParam || "",
                routeId: root.dataset.routeId || "",
                routeConfigUrl,
                docsPaths: routeConfig.docs_paths || {},
                viewerBaseUrl: routeConfig.viewer_base_url || "",
                generatedBaseUrl: routeConfig.services?.generated_data?.base_url || "",
                sourceBaseUrl: routeConfig.services?.source?.base_url || "",
                managementBaseUrl: routeConfig.services?.management?.base_url || ""
            };
        }"""
    )


def assert_manage_route_contract(state: dict[str, object], base_url: str) -> None:
    docs_paths = state.get("docsPaths") if isinstance(state.get("docsPaths"), dict) else {}
    if state["appKind"] != "manage" or state["managementUi"] != "true" or state["sourceService"] != "true":
        raise AssertionError(f"manage route did not expose the manage app/service context: {state!r}")
    if state["viewerBaseUrl"] != "/docs/":
        raise AssertionError(f"manage route did not use the manage route: {state!r}")
    if state["ready"] != "true" or state["busy"] == "true":
        raise AssertionError(f"manage route did not expose ready route state: {state!r}")
    if state["includeScopeParam"] != "true":
        raise AssertionError(f"manage route did not include scope param: {state!r}")
    if state["routeId"] != "docs-manage":
        raise AssertionError(f"manage route used unexpected route id: {state!r}")
    if state["routeConfigUrl"] != "/docs-viewer/config/routes/docs-viewer-routes.json":
        raise AssertionError(f"manage route used unexpected route config: {state!r}")
    if (
        state["managementBaseUrl"] != base_url
        or state["generatedBaseUrl"] != base_url
        or state["sourceBaseUrl"] != base_url
    ):
        raise AssertionError(f"manage route did not receive service base URL: {state!r}")
    if docs_paths.get("index_tree_url") != "/docs-viewer/scopes/studio/published/documents/index-tree.json":
        raise AssertionError(f"manage route config missing index_tree_url: {state!r}")
    if docs_paths.get("recent_url") != "/docs-viewer/scopes/studio/published/documents/recent.json":
        raise AssertionError(f"manage route config missing recent_url: {state!r}")
    if docs_paths.get("search_index_url") != "/docs-viewer/scopes/studio/published/search/index.json":
        raise AssertionError(f"manage route config missing search_index_url: {state!r}")


def assert_generated_requests(paths: set[str]) -> None:
    for expected in ["/docs/index-tree", "/docs/doc"]:
        if expected not in paths:
            raise AssertionError(f"expected generated service request {expected!r}; saw {sorted(paths)!r}")


def assert_delete_uses_first_remaining_root(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions.js');
            const docs = [
                { doc_id: 'analytics', parent_id: '' },
                { doc_id: 'dlf', parent_id: '' },
                { doc_id: 'section', parent_id: '' },
                { doc_id: 'section-child', parent_id: 'section' }
            ];
            const resolveLoadableDocId = docId => docId === 'section' ? 'section-child' : docId;
            return {
                afterDlf: module.firstRemainingRootDocId(docs, 'dlf', resolveLoadableDocId),
                afterAnalytics: module.firstRemainingRootDocId(docs, 'analytics', resolveLoadableDocId),
                afterOnly: module.firstRemainingRootDocId([{ doc_id: 'only', parent_id: '' }], 'only')
            };
        }"""
    )
    if result != {"afterDlf": "analytics", "afterAnalytics": "dlf", "afterOnly": ""}:
        raise AssertionError(f"unexpected post-delete root fallback: {result!r}")


def assert_action_target_definitions(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js');
            const definitions = module.listDocsViewerActionDefinitions();
            const groupedIds = (target, selectionPolicy = '') => definitions
                .filter(definition => definition.target === target && (definition.selectionPolicy || '') === selectionPolicy)
                .map(definition => definition.id)
                .sort();
            const multiContext = {
                activeDocId: 'active',
                primaryDocId: 'second',
                selectedDocIds: ['first', 'second', 'first']
            };
            const emptySelectionContext = module.createDocsViewerActionContext({ activeDocId: 'active' });
            const multiSelectionContext = module.createDocsViewerActionContext({
                activeDocId: 'active',
                primaryDocId: 'second',
                selectedDocIds: ['first', 'second', 'first']
            });
            const invocationContext = module.createDocsViewerActionContext({
                activeDocId: 'active',
                invocationDocId: 'context'
            });
            let unknownRejected = false;
            try {
                module.resolveDocsViewerAction('invented-action', emptySelectionContext);
            } catch (error) {
                unknownRejected = /Unknown Docs Viewer action/.test(String(error && error.message || ''));
            }
            const surfaceActionIds = Array.from(document.querySelectorAll('[data-docs-viewer-action]'))
                .map(node => node.dataset.docsViewerAction)
                .filter(Boolean);
            const unknownSurfaceActionIds = Array.from(new Set(surfaceActionIds.filter(actionId => (
                !module.getDocsViewerActionDefinition(actionId)
            )))).sort();
            return {
                active: groupedIds('active-document'),
                all: groupedIds('selection', 'all'),
                document: groupedIds('document'),
                exactlyOne: groupedIds('selection', 'exactly-one'),
                primary: groupedIds('selection', 'primary'),
                scope: groupedIds('scope'),
                emptySelectionContext,
                multiSelectionContext,
                invocationContext,
                resolutions: {
                    active: module.resolveDocsViewerAction('bookmark', multiContext),
                    copySubtree: module.resolveDocsViewerAction('copy-subtree', multiContext),
                    all: module.resolveDocsViewerAction('move', multiContext),
                    exactlyOne: module.resolveDocsViewerAction('delete', multiContext),
                    primary: module.resolveDocsViewerAction('info', multiContext),
                    scope: module.resolveDocsViewerAction('export-docs', multiContext),
                    emptyDelete: module.resolveDocsViewerAction('delete', emptySelectionContext),
                    multiMove: module.resolveDocsViewerAction('move', multiSelectionContext),
                    contextCopy: module.resolveDocsViewerAction('copy-link', invocationContext),
                    toolbarOpenVsCode: module.resolveDocsViewerAction('open-vscode', emptySelectionContext),
                    contextOpenVsCode: module.resolveDocsViewerAction('open-vscode', invocationContext)
                },
                surfaceActionIds: Array.from(new Set(surfaceActionIds)).sort(),
                unknownRejected,
                unknownSurfaceActionIds
            };
        }"""
    )
    expected = {
        "active": [
            "bookmark",
            "copy-subtree",
            "edit-metadata",
            "info",
            "markdown-save",
            "markdown-source",
            "source-add-file",
            "source-add-image",
        ],
        "all": ["move"],
        "document": ["open-vscode"],
        "exactlyOne": ["delete", "show"],
        "primary": [
            "copy-link",
            "new-child",
            "new-sibling",
            "open",
        ],
        "scope": [
            "delete-scope",
            "delete-sub-scope",
            "export-docs",
            "import",
            "new",
            "new-scope",
            "new-sub-scope",
            "publish-docs",
            "rebuild-docs",
            "rename-scope",
            "settings",
            "show-non-viewable",
        ],
        "emptySelectionContext": {
            "activeDocId": "active",
            "invocationDocId": "",
            "primaryDocId": "",
            "selectedDocIds": [],
        },
        "multiSelectionContext": {
            "activeDocId": "active",
            "invocationDocId": "",
            "primaryDocId": "second",
            "selectedDocIds": ["first", "second"],
        },
        "invocationContext": {
            "activeDocId": "active",
            "invocationDocId": "context",
            "primaryDocId": "context",
            "selectedDocIds": [],
        },
        "resolutions": {
            "active": {
                "actionId": "bookmark",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "active-document",
                "targetDocIds": ["active"],
            },
            "copySubtree": {
                "actionId": "copy-subtree",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "active-document",
                "targetDocIds": ["active"],
            },
            "all": {
                "actionId": "move",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "exactlyOne": {
                "actionId": "delete",
                "disabledReason": "Available for one document only.",
                "enabled": False,
                "selectionPolicy": "exactly-one",
                "target": "selection",
                "targetDocIds": [],
            },
            "primary": {
                "actionId": "info",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "active-document",
                "targetDocIds": ["active"],
            },
            "scope": {
                "actionId": "export-docs",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "scope",
                "targetDocIds": [],
            },
            "emptyDelete": {
                "actionId": "delete",
                "disabledReason": "Select one document.",
                "enabled": False,
                "selectionPolicy": "exactly-one",
                "target": "selection",
                "targetDocIds": [],
            },
            "multiMove": {
                "actionId": "move",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "contextCopy": {
                "actionId": "copy-link",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "primary",
                "target": "selection",
                "targetDocIds": ["context"],
            },
            "toolbarOpenVsCode": {
                "actionId": "open-vscode",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "document",
                "targetDocIds": ["active"],
            },
            "contextOpenVsCode": {
                "actionId": "open-vscode",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "document",
                "targetDocIds": ["context"],
            },
        },
        "surfaceActionIds": [
            "bookmark",
            "copy-link",
            "copy-subtree",
            "delete",
            "delete-scope",
            "delete-sub-scope",
            "edit-metadata",
            "export-docs",
            "import",
            "info",
            "markdown-source",
            "new",
            "new-child",
            "new-scope",
            "new-sibling",
            "new-sub-scope",
            "open",
            "open-vscode",
            "publish-docs",
            "rebuild-docs",
            "rename-scope",
            "settings",
            "show",
            "show-non-viewable",
        ],
        "unknownRejected": True,
        "unknownSurfaceActionIds": [],
    }
    if result != expected:
        raise AssertionError(f"unexpected Docs Viewer action target contract: {result!r}")


def assert_open_source_target_handoff(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const definitions = await import('/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js');
            const actions = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions.js');
            const requests = [];
            let hiddenCount = 0;
            const controller = actions.createDocsViewerManagementActionController({
                root: null,
                documentIndex: {
                    docsById: new Map([
                        ['active', { doc_id: 'active', title: 'Active' }],
                        ['invoked', { doc_id: 'invoked', title: 'Invoked' }]
                    ])
                },
                management: {},
                selectedDocument: {},
                context: {},
                resolveAction: function (actionId, targetDocId) {
                    const options = { activeDocId: 'active', selectedDocIds: [] };
                    if (arguments.length > 1) options.invocationDocId = targetDocId;
                    return definitions.resolveDocsViewerAction(
                        actionId,
                        definitions.createDocsViewerActionContext(options)
                    );
                },
                callbacks: {
                    hideContextMenu: () => { hiddenCount += 1; },
                    managementClientOptions: () => ({
                        baseUrl: 'http://docs.test',
                        scope: 'studio',
                        fetch: (url, options) => {
                            requests.push({ url, body: JSON.parse(options.body) });
                            return Promise.resolve({
                                ok: true,
                                status: 200,
                                json: () => Promise.resolve({ ok: true })
                            });
                        }
                    }),
                    renderManagementUi: () => {},
                    setManagementBusy: () => {},
                    setManagementMessage: () => {}
                }
            });
            await controller.handleOpenSource('vscode');
            await controller.handleOpenSource('vscode', 'invoked');
            return { hiddenCount, requests };
        }"""
    )
    expected = {
        "hiddenCount": 2,
        "requests": [
            {
                "url": "http://docs.test/docs/open-source",
                "body": {"scope": "studio", "doc_id": "active", "editor": "vscode"},
            },
            {
                "url": "http://docs.test/docs/open-source",
                "body": {"scope": "studio", "doc_id": "invoked", "editor": "vscode"},
            },
        ],
    }
    if result != expected:
        raise AssertionError(f"unexpected source-open target handoff: {result!r}")


def assert_copy_subtree_module_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const capabilities = await import('/docs-viewer/runtime/js/management/docs-viewer-management-capabilities.js');
            const client = await import('/docs-viewer/runtime/js/management/docs-viewer-management-client.js');
            const payload = {
                copy_subtree: { preview: true, apply: true },
                scopes: {
                    studio: { scope_type: 'local', available: true, copy_subtree_target: true, root: 'scopes/studio' },
                    public: { scope_type: 'public', available: true, copy_subtree_target: true, root: 'scopes/public' },
                    notes: { scope_type: 'local_external', available: true, copy_subtree_target: true, root: 'scopes/notes' },
                    processing: { scope_type: 'local', available: true, copy_subtree_target: true, root: 'scopes/processing' },
                    missing: { scope_type: 'local', available: false, copy_subtree_target: true, root: 'scopes/missing' },
                    readonly: { scope_type: 'local', available: true, copy_subtree_target: false, root: 'scopes/readonly' }
                }
            };
            const requests = [];
            const fetch = (url, options) => {
                requests.push({ url, body: JSON.parse(options.body) });
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ ok: true })
                });
            };
            await client.previewManagedDocSubtreeCopy('source-doc', 'notes', {
                baseUrl: 'http://manage.test', scope: 'studio', fetch
            });
            await client.applyManagedDocSubtreeCopy({ schema_version: 'receipt' }, {
                baseUrl: 'http://manage.test', scope: 'studio', fetch
            });
            return {
                supported: capabilities.copySubtreeSupported(payload),
                targets: capabilities.copySubtreeTargetScopes(payload, 'studio'),
                requests
            };
        }"""
    )
    expected = {
        "supported": True,
        "targets": [
            {"scopeId": "notes", "label": "notes", "root": "scopes/notes"},
            {"scopeId": "processing", "label": "processing", "root": "scopes/processing"},
        ],
        "requests": [
            {
                "url": "http://manage.test/docs/copy-subtree-preview",
                "body": {"scope": "studio", "source_doc_id": "source-doc", "target_scope": "notes"},
            },
            {
                "url": "http://manage.test/docs/copy-subtree-apply",
                "body": {
                    "scope": "studio",
                    "apply_plan": {"schema_version": "receipt"},
                    "confirm": True,
                },
            },
        ],
    }
    if result != expected:
        raise AssertionError(f"unexpected Copy Subtree module contract: {result!r}")


def exercise_manage_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
) -> tuple[set[str], set[str], set[str], set[str], str]:
    generated_requests: list[str] = []
    import_module_requests: list[str] = []
    scope_lifecycle_requests: list[str] = []
    copy_subtree_requests: list[str] = []
    page.on(
        "request",
        lambda request: generated_requests.append(request.url)
        if any(path in request.url for path in ("/docs/index-tree", "/docs/doc"))
        else None,
    )
    page.on(
        "request",
        lambda request: import_module_requests.append(request.url)
        if "/docs-viewer/runtime/js/import/" in request.url
        else None,
    )
    page.on(
        "request",
        lambda request: scope_lifecycle_requests.append(request.url)
        if "/docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js" in request.url
        else None,
    )
    page.on(
        "request",
        lambda request: copy_subtree_requests.append(request.url)
        if "/docs-viewer/runtime/js/management/docs-viewer-copy-subtree-workflow.js" in request.url
        else None,
    )

    page.goto(f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)
    assert_action_target_definitions(page)
    assert_open_source_target_handoff(page)
    assert_delete_uses_first_remaining_root(page)
    assert_manage_route_contract(manage_route_state(page), base_url)
    if import_module_requests:
        raise AssertionError(f"Docs Import modules loaded before the import action: {import_module_requests!r}")
    if scope_lifecycle_requests:
        raise AssertionError(f"scope lifecycle flow loaded before a lifecycle action: {scope_lifecycle_requests!r}")
    if copy_subtree_requests:
        raise AssertionError(f"copy subtree flow loaded before the copy action: {copy_subtree_requests!r}")

    vscode_button = page.locator("#docsViewerManageOpenVsCodeButton")
    if vscode_button.count() != 1 or vscode_button.is_hidden() or vscode_button.is_disabled():
        raise AssertionError("Open in VS Code should be an enabled document-toolbar action")
    if vscode_button.get_attribute("data-docs-viewer-control-surface") != "main-view":
        raise AssertionError("Open in VS Code should be owned by the main-view control surface")
    if vscode_button.get_attribute("data-docs-viewer-action") != "open-vscode":
        raise AssertionError("Document-toolbar control should invoke the shared open-vscode action")
    if vscode_button.get_attribute("title") != "Open in VS Code":
        raise AssertionError("Open in VS Code document-toolbar action should have an explicit label")
    page.wait_for_function(
        """() => {
            const icon = document.querySelector('#docsViewerManageOpenVsCodeButton img');
            return icon && icon.complete && icon.naturalWidth === 100 && icon.naturalHeight === 100;
        }""",
        timeout=timeout_ms,
    )
    vscode_icon = vscode_button.locator("img")
    if not vscode_icon.get_attribute("src").endswith("/docs-viewer/runtime/js/management/icons/vscode.svg"):
        raise AssertionError("Open in VS Code should use the official stable icon asset")
    if vscode_icon.get_attribute("alt") != "" or vscode_icon.get_attribute("aria-hidden") != "true":
        raise AssertionError("Decorative VS Code icon should defer its accessible name to the button")

    copy_button = page.locator("#docsViewerManageCopySubtreeButton")
    if copy_button.count() != 1 or copy_button.is_hidden() or copy_button.is_disabled():
        raise AssertionError("Copy subtree should be an enabled index-toolbar action for the active document")
    if copy_button.get_attribute("data-docs-viewer-control-surface") != "index-view":
        raise AssertionError("Copy subtree action should be owned by the index-view control surface")
    index_toolbar = page.locator('[data-docs-viewer-control-surface-mount="index-view"]')
    index_panel_toggle = page.locator("#docsViewerSidebarToggle")
    index_panel_toggle.click()
    page.wait_for_function(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            const toolbar = document.querySelector('[data-docs-viewer-control-surface-mount="index-view"]');
            const toggle = document.querySelector('#docsViewerSidebarToggle');
            return root?.dataset.indexPanelState === 'collapsed' &&
                toolbar && getComputedStyle(toolbar).display === 'none' &&
                toggle && !toggle.hidden && toggle.getAttribute('aria-label') === 'Restore index panel';
        }""",
        timeout=timeout_ms,
    )
    if not copy_button.is_hidden():
        raise AssertionError("Collapsed index panel should hide the complete index-view toolbar")
    index_panel_toggle.click()
    page.wait_for_function(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            const toolbar = document.querySelector('[data-docs-viewer-control-surface-mount="index-view"]');
            return root?.dataset.indexPanelState === 'normal' &&
                toolbar && getComputedStyle(toolbar).display !== 'none';
        }""",
        timeout=timeout_ms,
    )
    if index_toolbar.is_hidden() or copy_button.is_hidden():
        raise AssertionError("Restored index panel should show its index-view toolbar")
    with page.expect_request(
        lambda request: urlparse(request.url).path.endswith("/docs-viewer-copy-subtree-workflow.js"),
        timeout=timeout_ms,
    ):
        copy_button.click()
    page.goto(f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)
    assert_copy_subtree_module_contract(page)

    page.locator("#docsViewerManageActionsButton").click()
    page.wait_for_function(
        '() => document.querySelector("#docsViewerManageActionsMenu")?.hidden === false',
        timeout=timeout_ms,
    )
    page.locator("#docsViewerContent h1").click()
    page.wait_for_function(
        '() => document.querySelector("#docsViewerManageActionsMenu")?.hidden === true',
        timeout=timeout_ms,
    )
    page.locator("#docsViewerManageActionsButton").click()
    page.keyboard.press("Escape")
    page.wait_for_function(
        '() => document.querySelector("#docsViewerManageActionsMenu")?.hidden === true',
        timeout=timeout_ms,
    )

    page.locator("#docsViewerManageImportButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#docsViewerImportModal");
            const root = document.querySelector("#docsHtmlImportRoot");
            return modal && !modal.hidden && root && root.dataset.studioReady === "true";
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerImportCancelButton").evaluate("button => button.click()")

    page.locator("#docsViewerManageEditButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#docsViewerMetadataModal");
            const title = document.querySelector("#docsViewerMetadataTitleInput");
            return modal && !modal.hidden && title && title.value.trim();
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerMetadataCancelButton").evaluate("button => button.click()")

    page.locator("#docsViewerManageSourceButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            const actions = document.querySelector('[data-docs-viewer-control-surface-mount="main-view"]');
            return root?.dataset.documentDisplayMode === 'markdown-source'
                && actions
                && Array.from(actions.children).map(node => node.dataset.docsViewerControl).join(',') === 'open-vscode,source-add-image,source-add-file,save-markdown-source,markdown-source,info'
                && !document.querySelector('#docsViewerManageSourceSaveButton')?.disabled;
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerManageSourceButton").evaluate("button => button.click()")
    page.wait_for_function(
        "() => document.querySelector('#docsViewerRoot')?.dataset.documentDisplayMode === 'rendered-document'",
        timeout=timeout_ms,
    )

    page.locator("#docsViewerManageSettingsButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#docsViewerSettingsModal");
            const save = document.querySelector("#docsViewerSettingsSaveButton");
            const textInput = document.querySelector("#docsViewerSettingsTextInput");
            const booleanInput = document.querySelector("#docsViewerSettingsBooleanInput");
            return modal && !modal.hidden && save && !save.disabled &&
                ((textInput && !textInput.disabled) || (booleanInput && !booleanInput.disabled));
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerSettingsCancelButton").evaluate("button => button.click()")

    page.locator("#docsViewerManageNewScopeButton").evaluate("button => button.click()")
    page.wait_for_selector(
        '[data-docs-viewer-management-modal-host="true"] [data-role="scope-id"]',
        state="visible",
        timeout=timeout_ms,
    )
    page.locator(
        '[data-docs-viewer-management-modal-host="true"] button[data-role="modal-cancel"]'
    ).evaluate("button => button.click()")

    page.locator("#docsViewerManageRenameScopeButton").evaluate("button => button.click()")
    rename_host = page.locator('[data-docs-viewer-management-modal-host="true"]')
    page.wait_for_selector(
        '[data-docs-viewer-management-modal-host="true"] [data-role="scope-rename-new-id"]',
        state="visible",
        timeout=timeout_ms,
    )
    if rename_host.locator('[data-role="scope-rename-target"]').count() != 1:
        raise AssertionError("Rename scope modal should contain one scope selector")
    if rename_host.locator(".docsViewerScopeLifecycle__section").count() != 0:
        raise AssertionError("Rename scope modal should not render lifecycle preview sections")
    if "Links containing the old scope id are not rewritten." not in rename_host.inner_text():
        raise AssertionError("Rename scope modal should state the manual link-rewrite boundary")
    if rename_host.locator('button[data-role="modal-primary"]').inner_text().strip() != "Rename":
        raise AssertionError("Rename scope modal should use a direct Rename action")
    rename_host.locator('button[data-role="modal-cancel"]').evaluate("button => button.click()")

    page.locator("#docsViewerManageDeleteScopeButton").evaluate("button => button.click()")
    delete_host = page.locator('[data-docs-viewer-management-modal-host="true"]')
    page.wait_for_selector(
        '[data-docs-viewer-management-modal-host="true"] [data-role="scope-delete-target"]',
        state="visible",
        timeout=timeout_ms,
    )
    delete_options = delete_host.locator('[data-role="scope-delete-target"] option').all_inner_texts()
    if not any(" - scopes/" in label for label in delete_options):
        raise AssertionError(f"External delete target should use a portable root label: {delete_options!r}")
    if any("/Users/" in label for label in delete_options):
        raise AssertionError(f"Delete target labels should not expose user-specific roots: {delete_options!r}")
    delete_host.locator('button[data-role="modal-cancel"]').evaluate("button => button.click()")
    return (
        request_paths(generated_requests),
        request_paths(import_module_requests),
        request_paths(scope_lifecycle_requests),
        request_paths(copy_subtree_requests),
        page.url,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        assert_service_basics(base_url)
        assert_origin_rejection(base_url)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(exc.stack or str(exc)))
                (
                    generated_paths,
                    import_module_paths,
                    scope_lifecycle_paths,
                    copy_subtree_paths,
                    final_url,
                ) = exercise_manage_route(
                    page,
                    base_url,
                    args.timeout_ms,
                )
            finally:
                browser.close()

        assert_generated_requests(generated_paths)
        if "/docs-viewer/runtime/js/import/docs-html-import.js" not in import_module_paths:
            raise AssertionError(f"expected lazy Docs Import module request; saw {sorted(import_module_paths)!r}")
        if "/docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js" not in scope_lifecycle_paths:
            raise AssertionError(f"expected lazy scope lifecycle module request; saw {sorted(scope_lifecycle_paths)!r}")
        if "/docs-viewer/runtime/js/management/docs-viewer-copy-subtree-workflow.js" not in copy_subtree_paths:
            raise AssertionError(f"expected lazy copy subtree module request; saw {sorted(copy_subtree_paths)!r}")
        if query_value(final_url, "mode"):
            raise AssertionError(f"expected clean manage URL without mode query, got {final_url}")
        if errors:
            raise AssertionError(f"page errors during Docs Viewer service smoke: {errors!r}")
        print(f"Docs Viewer service manage shell OK: {base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
