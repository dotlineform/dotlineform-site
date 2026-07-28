#!/usr/bin/env python3
"""Smoke-check managed sub-scope report state and toolbar projection modules."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        translated = Path(super().translate_path(path))
        request_path = urlsplit(path).path
        shared_prefix = "/docs-viewer/runtime/js/shared/"
        if translated.exists() or not request_path.startswith(shared_prefix):
            return str(translated)
        relative = request_path.removeprefix(shared_prefix)
        return str(
            Path(self.directory)
            / "site/docs-viewer/runtime/js/shared"
            / relative
        )


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_control_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const controls = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-report-controls.js'
          );
          const client = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-client.js'
          );
          const documentControllerModule = await import(
            '/site/docs-viewer/runtime/js/shared/docs-viewer-document-controller.js'
          );
          const parent = { scope: 'studio', doc_id: 'parent-doc' };
          const subdoc = { scope: 'studio', sub_scope: 'tags', doc_id: 'detail-doc' };

          function compact(projection) {
            return Object.fromEntries(Object.entries(projection).map(([key, value]) => [
              key,
              {
                state: value.state,
                target: value.target
              }
            ]));
          }

          const cases = {
            ordinary: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'rendered-document',
              ordinaryTarget: parent
            })),
            list: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'rendered-document',
              reportActive: true,
              reportState: 'list',
              parentTarget: parent
            })),
            detail: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'rendered-document',
              reportActive: true,
              reportState: 'detail',
              parentTarget: parent,
              subdocTarget: subdoc
            })),
            loading: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'rendered-document',
              reportActive: true,
              reportState: 'loading',
              parentTarget: parent
            })),
            invalid: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'rendered-document',
              reportActive: true,
              reportState: 'invalid',
              parentTarget: parent
            })),
            error: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'rendered-document',
              reportActive: true,
              reportState: 'error',
              parentTarget: parent
            })),
            source: compact(controls.projectDocsViewerReportControlState({
              documentMode: 'markdown-source',
              reportActive: true,
              reportState: 'detail',
              parentTarget: parent,
              subdocTarget: subdoc
            }))
          };

          const requests = [];
          const managementFetch = async (url, options) => {
            requests.push({
              url,
              method: options.method,
              body: options.body ? JSON.parse(options.body) : null
            });
            return {
              ok: true,
              status: 200,
              json: async () => ({
                ok: true,
                scope: 'studio',
                sub_scope: 'tags',
                documents: []
              })
            };
          };
          const inventory = await client.readManagedSubScopeDocuments('Studio', 'Tags', {
            baseUrl: 'http://127.0.0.1:8789',
            fetch: managementFetch
          });
          const deleteOptions = {
            baseUrl: 'http://127.0.0.1:8789',
            fetch: managementFetch
          };
          const sourceRevision = 'sha256:' + 'a'.repeat(64);
          await client.previewManagedSubScopeDocDelete(subdoc, deleteOptions);
          await client.applyManagedSubScopeDocDelete(
            subdoc,
            sourceRevision,
            deleteOptions
          );
          let missingTargetError = '';
          try {
            await client.readManagedSubScopeDocuments('studio', '', {
              baseUrl: 'http://127.0.0.1:8789'
            });
          } catch (error) {
            missingTargetError = error.message;
          }
          let parentDeleteError = '';
          try {
            await client.previewManagedSubScopeDocDelete(parent, deleteOptions);
          } catch (error) {
            parentDeleteError = error.message;
          }
          let revisionError = '';
          try {
            await client.applyManagedSubScopeDocDelete(
              subdoc,
              'not-a-revision',
              deleteOptions
            );
          } catch (error) {
            revisionError = error.message;
          }

          const navigationStates = [];
          const content = document.createElement('main');
          const results = document.createElement('section');
          const more = document.createElement('section');
          document.body.append(content, results, more);
          const documentController = documentControllerModule.initDocsViewerDocumentController({
            content,
            hasActiveQuery: () => false,
            more,
            projectDocumentShell: () => {},
            publishSubscopeReportState: state => navigationStates.push(state),
            renderBookmarkToggle: () => {},
            renderBookmarkUi: () => {},
            renderManagementUi: () => {},
            renderMeta: () => {},
            renderSidebar: () => {},
            results,
            routeSession: {},
            scopeConfig: {},
            selectedDocument: {},
            setRecentModeActive: () => {}
          });
          documentController.renderDocLoadingState({
            doc_id: 'next-doc',
            title: 'Next'
          });
          return {
            cases,
            requests,
            inventory,
            missingTargetError,
            parentDeleteError,
            revisionError,
            navigationStates
          };
        }"""
    )

    parent = {"scope": "studio", "doc_id": "parent-doc"}
    subdoc = {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": "detail-doc",
    }
    cases = result["cases"]
    assert cases["ordinary"]["editMetadata"]["target"] == parent
    assert cases["ordinary"]["openVsCode"]["target"] == parent
    assert cases["ordinary"]["parentSource"]["target"] == parent
    assert cases["ordinary"]["subdocSource"]["state"]["hidden"] is True

    assert cases["list"]["editMetadata"]["target"] == parent
    assert cases["list"]["openVsCode"]["target"] == parent
    assert cases["list"]["parentSource"]["target"] == parent
    assert cases["list"]["parentSource"]["state"]["label"] == "Parent Source"
    assert cases["list"]["subdocSource"]["state"] == {
        "hidden": False,
        "disabled": True,
        "label": "Subdoc Source",
    }
    assert cases["list"]["returnToDoc"]["state"]["hidden"] is True
    assert cases["detail"]["editMetadata"]["target"] == subdoc
    assert cases["detail"]["openVsCode"]["target"] == subdoc
    assert cases["detail"]["subdocSource"]["target"] == subdoc
    assert cases["detail"]["parentSource"]["target"] == parent

    for state_name in ("loading", "invalid", "error"):
        assert cases[state_name]["editMetadata"]["state"]["disabled"] is True
        assert cases[state_name]["editMetadata"]["target"] is None
        assert cases[state_name]["openVsCode"]["state"]["disabled"] is True
        assert cases[state_name]["openVsCode"]["target"] is None
        assert cases[state_name]["subdocSource"]["state"]["disabled"] is True
        assert cases[state_name]["subdocSource"]["target"] is None
        assert cases[state_name]["parentSource"]["state"]["disabled"] is False
        assert cases[state_name]["parentSource"]["target"] == parent

    source = cases["source"]
    assert source["editMetadata"]["state"]["hidden"] is True
    assert source["openVsCode"]["state"]["hidden"] is False
    assert source["openVsCode"]["state"]["disabled"] is False
    assert source["openVsCode"]["target"] is None
    assert source["parentSource"]["state"]["hidden"] is False
    assert source["parentSource"]["state"]["disabled"] is True
    assert source["subdocSource"]["state"]["hidden"] is False
    assert source["subdocSource"]["state"]["disabled"] is True
    assert source["returnToDoc"]["state"] == {
        "hidden": False,
        "disabled": False,
        "label": "Return to doc",
    }

    assert result["requests"] == [
        {
            "url": (
                "http://127.0.0.1:8789/docs/sub-scope-documents"
                "?scope=studio&sub_scope=tags"
            ),
            "method": "GET",
            "body": None,
        },
        {
            "url": "http://127.0.0.1:8789/docs/delete-preview",
            "method": "POST",
            "body": {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "detail-doc",
            },
        },
        {
            "url": "http://127.0.0.1:8789/docs/delete-apply",
            "method": "POST",
            "body": {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "detail-doc",
                "source_revision": "sha256:" + ("a" * 64),
                "confirm": True,
            },
        }
    ]
    assert result["inventory"]["documents"] == []
    assert (
        result["missingTargetError"]
        == "Managed sub-scope inventory requires scope and sub_scope."
    )
    assert (
        result["parentDeleteError"]
        == "Sub-scope document delete requires a sub-scope target."
    )
    assert (
        result["revisionError"]
        == "Sub-scope document delete requires a sha256 source revision."
    )
    assert result["navigationStates"] == [
        {
            "state": "inactive",
            "reason": "navigation-start",
            "documentMountGeneration": 1,
            "parentTarget": None,
            "subdocTarget": None,
        }
    ]


def assert_report_module(page: Page) -> None:
    page.evaluate(
        """() => {
          window.syntheticDetailMode = 'immediate';
          window.syntheticDetailResolve = null;
          window.syntheticPayloadDocId = '';
          window.fetch = async input => {
            const url = new URL(String(input), window.location.href);
            const response = payload => ({
              ok: true,
              status: 200,
              json: async () => payload,
              text: async () => JSON.stringify(payload)
            });
            if (url.pathname.endsWith('/manifest.json')) {
              return response({
                docs: [{ doc_id: 'visible-doc', title: 'Visible document' }]
              });
            }
            if (url.pathname.includes('/by-id/')) {
              const docId = decodeURIComponent(url.pathname.split('/').pop().replace(/\\.json$/, ''));
              if (window.syntheticDetailMode === 'deferred') {
                return await new Promise(resolve => {
                  window.syntheticDetailResolve = () => resolve(response({
                    doc_id: window.syntheticPayloadDocId || docId,
                    title: docId === 'hidden-doc' ? 'Hidden document' : 'Visible document',
                    content_html: `<h2>${docId}</h2>`
                  }));
                });
              }
              return response({
                doc_id: window.syntheticPayloadDocId || docId,
                title: docId === 'hidden-doc' ? 'Hidden document' : 'Visible document',
                content_html: `<h2>${docId}</h2>`
              });
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };
        }"""
    )

    managed = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          document.body.innerHTML = '<main id="content"><section id="report"></section></main>';
          const root = document.querySelector('#report');
          window.syntheticReportStates = [];
          window.syntheticContributionEvents = [];
          const contribution = {
            notify: event => {
              window.syntheticContributionEvents.push({
                type: event.type,
                collection: event.collection,
                state: event.state || '',
                reason: event.reason || '',
                target: event.target || null,
                documentIds: Array.isArray(event.documents)
                  ? event.documents.map(doc => doc.doc_id)
                  : []
              });
              if (event.type === 'state') {
                window.syntheticReportStates.push({
                  state: event.state,
                  reason: event.reason,
                  target: event.target || null
                });
              }
            },
            renderRow: ({ document, leadingHost, titlePrefixHost }) => {
              const prefix = titlePrefixHost.ownerDocument.createElement('span');
              prefix.className = 'synthetic-title-prefix';
              prefix.textContent = '•';
              titlePrefixHost.appendChild(prefix);
              if (document.doc_id === 'hidden-doc') {
                const leading = leadingHost.ownerDocument.createElement('span');
                leading.className = 'synthetic-leading-control';
                leading.textContent = 'leading';
                leadingHost.appendChild(leading);
              }
              return {
                accessibleLabels: document.ui_status ? [document.ui_status] : []
              };
            },
            renderListToolbar: ({ host }) => {
              const button = host.ownerDocument.createElement('button');
              button.type = 'button';
              button.textContent = 'List contribution';
              host.appendChild(button);
            },
            renderDetailToolbar: ({ host, target }) => {
              const button = host.ownerDocument.createElement('button');
              button.type = 'button';
              button.dataset.targetDocId = target.doc_id;
              button.textContent = 'Detail contribution';
              host.appendChild(button);
            }
          };
          window.syntheticReportContribution = contribution;
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                manifestUrl: '/synthetic/manifest.json',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            subscopeDocumentSource: {
              documents: [
                {
                  doc_id: 'visible-doc',
                  title: 'Visible document',
                  ui_status: 'done',
                  viewable: true
                },
                {
                  doc_id: 'hidden-doc',
                  title: 'Hidden document',
                  ui_status: 'draft',
                  viewable: false
                }
              ]
            },
            subscopeReportContribution: contribution,
            viewerScope: 'studio'
          });
          return {
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(node => node.dataset.reportSubdocId),
            labels: Array.from(root.querySelectorAll('.docsViewerReport__subscopeButton'))
              .map(node => node.getAttribute('aria-label')),
            titlePrefixes: root.querySelectorAll('.synthetic-title-prefix').length,
            leadingControls: root.querySelectorAll('.synthetic-leading-control').length,
            leadingHosts: root.querySelectorAll(
              '[data-report-contribution-host="row-leading"]'
            ).length,
            listToolbar: root.querySelector(
              '[data-report-contribution-host="list-toolbar"]'
            )?.textContent || '',
            leadingColumn: root.dataset.reportLeadingColumn || '',
            states: window.syntheticReportStates,
            contributionEvents: window.syntheticContributionEvents
          };
        }"""
    )
    expected_managed = {
        "rowIds": ["visible-doc", "hidden-doc"],
        "labels": [
            "Visible document, done",
            "Hidden document, draft",
        ],
        "titlePrefixes": 2,
        "leadingControls": 1,
        "leadingHosts": 2,
        "listToolbar": "List contribution",
        "leadingColumn": "true",
        "states": [
            {"state": "loading", "reason": "report-loading", "target": None},
            {"state": "list", "reason": "list-view", "target": None},
        ],
        "contributionEvents": [
            {
                "type": "mount",
                "collection": {"scope": "studio", "sub_scope": "tags"},
                "state": "",
                "reason": "",
                "target": None,
                "documentIds": [],
            },
            {
                "type": "state",
                "collection": {"scope": "studio", "sub_scope": "tags"},
                "state": "loading",
                "reason": "report-loading",
                "target": None,
                "documentIds": [],
            },
            {
                "type": "refresh",
                "collection": {"scope": "studio", "sub_scope": "tags"},
                "state": "",
                "reason": "documents-loaded",
                "target": None,
                "documentIds": ["visible-doc", "hidden-doc"],
            },
            {
                "type": "state",
                "collection": {"scope": "studio", "sub_scope": "tags"},
                "state": "list",
                "reason": "list-view",
                "target": None,
                "documentIds": [],
            },
        ],
    }
    if managed != expected_managed:
        raise AssertionError(f"unexpected managed report projection: {managed!r}")

    page.locator('[data-report-subdoc-id="hidden-doc"] button').click()
    page.wait_for_function(
        """() => window.syntheticReportStates.some(
          state => state.state === 'detail' && state.target?.doc_id === 'hidden-doc'
        )"""
    )
    detail = page.evaluate(
        """() => ({
          reportState: document.querySelector('#report').dataset.reportState,
          title: document.querySelector('.docsReportDetail__title').textContent,
          detailToolbar: document.querySelector(
            '[data-report-contribution-host="detail-toolbar"]'
          )?.textContent || '',
          toolbarTarget: document.querySelector(
            '[data-report-contribution-host="detail-toolbar"] button'
          )?.dataset.targetDocId || '',
          toolbarAfterBack: document.querySelector(
            '[data-report-contribution-host="detail-toolbar"]'
          )?.previousElementSibling?.classList.contains('docsReportDetail__back') || false,
          latest: window.syntheticReportStates.at(-1)
        })"""
    )
    assert detail == {
        "reportState": "detail",
        "title": "Hidden document",
        "detailToolbar": "Detail contribution",
        "toolbarTarget": "hidden-doc",
        "toolbarAfterBack": True,
        "latest": {
            "state": "detail",
            "reason": "detail-loaded",
            "target": {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "hidden-doc",
            },
        },
    }

    page.locator(".docsReportDetail__back").click()
    page.evaluate("window.syntheticDetailMode = 'deferred'")
    page.locator('[data-report-subdoc-id="visible-doc"] button').click()
    page.wait_for_function("() => typeof window.syntheticDetailResolve === 'function'")
    loading_detail_toolbar_count = page.locator(
        '[data-report-contribution-host="detail-toolbar"]'
    ).count()
    if loading_detail_toolbar_count != 0:
        raise AssertionError(
            "detail contribution mounted before the by-id payload was validated"
        )
    page.locator(".docsReportDetail__back").click()
    page.evaluate("window.syntheticDetailResolve()")
    page.wait_for_timeout(25)
    stale = page.evaluate(
        """() => ({
          reportState: document.querySelector('#report').dataset.reportState,
          latest: window.syntheticReportStates.at(-1),
          detailAfterLatestList: (() => {
            const lastList = window.syntheticReportStates
              .map(state => state.state)
              .lastIndexOf('list');
            return window.syntheticReportStates
              .slice(lastList + 1)
              .some(state => state.state === 'detail');
          })()
        })"""
    )
    assert stale == {
        "reportState": "list",
        "latest": {"state": "list", "reason": "list-view", "target": None},
        "detailAfterLatestList": False,
    }

    page.evaluate("document.querySelector('#report').remove()")
    page.wait_for_function(
        "() => window.syntheticReportStates.at(-1)?.state === 'unmounted'"
    )
    unmount_events = page.evaluate(
        """() => window.syntheticContributionEvents.slice(-2).map(event => ({
          type: event.type,
          state: event.state,
          reason: event.reason,
          collection: event.collection
        }))"""
    )
    assert unmount_events == [
        {
            "type": "state",
            "state": "unmounted",
            "reason": "report-unmount",
            "collection": {"scope": "studio", "sub_scope": "tags"},
        },
        {
            "type": "unmount",
            "state": "",
            "reason": "report-unmount",
            "collection": {"scope": "studio", "sub_scope": "tags"},
        },
    ]

    remounted = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          const root = document.createElement('section');
          root.id = 'remounted-report';
          document.querySelector('#content').appendChild(root);
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                manifestUrl: '/synthetic/manifest.json',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            subscopeDocumentSource: {
              documents: [{ doc_id: 'visible-doc', title: 'Visible document' }]
            },
            subscopeReportContribution: window.syntheticReportContribution,
            viewerScope: 'studio'
          });
          return {
            mountEvents: window.syntheticContributionEvents
              .filter(event => event.type === 'mount').length,
            refreshEvents: window.syntheticContributionEvents
              .filter(event => event.type === 'refresh').length,
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId),
            listToolbar: root.querySelector(
              '[data-report-contribution-host="list-toolbar"]'
            )?.textContent || ''
          };
        }"""
    )
    assert remounted == {
        "mountEvents": 2,
        "refreshEvents": 2,
        "rowIds": ["visible-doc"],
        "listToolbar": "List contribution",
    }

    invalid = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc&subdoc=missing-doc');
          document.body.innerHTML = '<main><section id="invalid-report"></section></main>';
          const states = [];
          const root = document.querySelector('#invalid-report');
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                manifestUrl: '/synthetic/manifest.json',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            subscopeDocumentSource: {
              documents: [{ doc_id: 'visible-doc', title: 'Visible document' }]
            },
            subscopeReportContribution: {
              notify: event => {
                if (event.type === 'state') states.push({
                  state: event.state,
                  reason: event.reason,
                  target: event.target || null
                });
              }
            },
            viewerScope: 'studio'
          });
          return {
            reportState: root.dataset.reportState,
            latest: states.at(-1),
            text: root.textContent
          };
        }"""
    )
    assert invalid == {
        "reportState": "error",
        "latest": {"state": "invalid", "reason": "unlisted-detail", "target": None},
        "text": "Docs sub-scope detail is not listed: missing-doc",
    }

    mismatched = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          window.syntheticDetailMode = 'immediate';
          window.syntheticPayloadDocId = 'other-doc';
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc&subdoc=visible-doc');
          document.body.innerHTML = '<main><section id="mismatched-report"></section></main>';
          const states = [];
          const root = document.querySelector('#mismatched-report');
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                manifestUrl: '/synthetic/manifest.json',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            subscopeDocumentSource: {
              documents: [{ doc_id: 'visible-doc', title: 'Visible document' }]
            },
            subscopeReportContribution: {
              notify: event => {
                if (event.type === 'state') states.push({
                  state: event.state,
                  reason: event.reason,
                  target: event.target || null
                });
              }
            },
            viewerScope: 'studio'
          });
          return {
            latest: states.at(-1),
            publishedDetail: states.some(state => state.state === 'detail'),
            text: root.textContent
          };
        }"""
    )
    assert mismatched == {
        "latest": {
            "state": "error",
            "reason": "detail-load-failed",
            "target": None,
        },
        "publishedDetail": False,
        "text": "Docs sub-scope detail payload did not match the requested document.",
    }

    source_boundaries = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          document.body.innerHTML = `
            <main>
              <section id="empty-report"></section>
              <section id="failed-report"></section>
            </main>`;
          const subScope = {
            subScope: 'tags',
            title: 'Tags',
            manifestUrl: '/synthetic/manifest.json',
            byIdUrlBase: '/synthetic/by-id'
          };
          const emptyEvents = [];
          const emptyRoot = document.querySelector('#empty-report');
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: emptyRoot,
            routeContext: { subScopes: [subScope] },
            subscopeDocumentSource: { documents: [] },
            subscopeReportContribution: {
              notify: event => emptyEvents.push({
                type: event.type,
                state: event.state || '',
                reason: event.reason || '',
                documentIds: Array.isArray(event.documents)
                  ? event.documents.map(doc => doc.doc_id)
                  : []
              }),
              renderListToolbar: () => {}
            },
            viewerScope: 'studio'
          });

          const failedEvents = [];
          const failedRoot = document.querySelector('#failed-report');
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: failedRoot,
            routeContext: { subScopes: [subScope] },
            subscopeDocumentSource: {
              documents: [],
              error: 'Managed inventory unavailable.'
            },
            subscopeReportContribution: {
              notify: event => failedEvents.push({
                type: event.type,
                state: event.state || '',
                reason: event.reason || ''
              })
            },
            viewerScope: 'studio'
          });
          return {
            empty: {
              contributionHosts: emptyRoot.querySelectorAll(
                '[data-report-contribution-host]'
              ).length,
              events: emptyEvents,
              state: emptyRoot.dataset.reportState,
              text: emptyRoot.textContent
            },
            failed: {
              contributionHosts: failedRoot.querySelectorAll(
                '[data-report-contribution-host]'
              ).length,
              events: failedEvents,
              state: failedRoot.dataset.reportState,
              text: failedRoot.textContent
            }
          };
        }"""
    )
    assert source_boundaries == {
        "empty": {
            "contributionHosts": 0,
            "events": [
                {
                    "type": "mount",
                    "state": "",
                    "reason": "",
                    "documentIds": [],
                },
                {
                    "type": "state",
                    "state": "loading",
                    "reason": "report-loading",
                    "documentIds": [],
                },
                {
                    "type": "refresh",
                    "state": "",
                    "reason": "documents-loaded",
                    "documentIds": [],
                },
                {
                    "type": "state",
                    "state": "list",
                    "reason": "list-view",
                    "documentIds": [],
                },
            ],
            "state": "list",
            "text": "0 Tags documentsTagsNo documents in this sub-scope.",
        },
        "failed": {
            "contributionHosts": 0,
            "events": [
                {"type": "mount", "state": "", "reason": ""},
                {
                    "type": "state",
                    "state": "error",
                    "reason": "document-source-failed",
                },
            ],
            "state": "error",
            "text": "Managed inventory unavailable.",
        },
    }

    public = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          window.syntheticPayloadDocId = '';
          document.body.innerHTML = '<main><section id="public-report"></section></main>';
          const root = document.querySelector('#public-report');
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                manifestUrl: '/synthetic/manifest.json',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            viewerScope: 'studio'
          });
          const button = root.querySelector('.docsViewerReport__subscopeButton');
          return {
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(node => node.dataset.reportSubdocId),
            statusIcons: root.querySelectorAll('.docsViewer__navStatus').length,
            nonViewableIcons: root.querySelectorAll('.docsViewer__draftPrefix').length,
            contributionHosts: root.querySelectorAll(
              '[data-report-contribution-host]'
            ).length,
            ariaLabel: button ? button.getAttribute('aria-label') : null
          };
        }"""
    )
    assert public == {
        "rowIds": ["visible-doc"],
        "statusIcons": 0,
        "nonViewableIcons": 0,
        "contributionHosts": 0,
        "ariaLabel": None,
    }


def assert_subscope_selection_contribution(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          const contributionModule = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-contribution.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          document.body.innerHTML = (
            '<section class="docsViewer"><main><section id="selection-report"></section></main></section>'
          );
          window.fetch = async input => {
            const url = new URL(String(input), window.location.href);
            const response = payload => ({
              ok: true,
              status: 200,
              json: async () => payload
            });
            if (url.pathname === '/capabilities') {
              return response({ ok: true, capabilities: {} });
            }
            if (url.pathname.includes('/by-id/')) {
              const docId = decodeURIComponent(
                url.pathname.split('/').pop().replace(/\\.json$/, '')
              );
              return response({
                doc_id: docId,
                title: docId.toUpperCase(),
                content_html: `<h2>${docId}</h2>`
              });
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };
          const prepared = [];
          const root = document.querySelector('#selection-report');
          const contribution = contributionModule.createDocsViewerManagementSubscopeContribution({
            clientOptions: { baseUrl: window.location.origin },
            managementContext: true,
            nonViewableEmoji: '🚫',
            onPreparePackage: payload => prepared.push(payload),
            root: document.querySelector('.docsViewer'),
            uiStatusByValue: new Map([
              ['draft', { label: 'Draft', emoji: '📝' }]
            ])
          });
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            subscopeDocumentSource: {
              documents: [
                { doc_id: 'a', title: 'A', viewable: true },
                { doc_id: 'b', title: 'B', ui_status: 'draft', viewable: false },
                { doc_id: 'c', title: 'C', viewable: true }
              ]
            },
            subscopeReportContribution: contribution,
            viewerScope: 'studio'
          });
          const selectionSnapshot = () => {
            const checkboxes = Array.from(
              root.querySelectorAll('[data-docs-subscope-selection-checkbox]')
            );
            const actions = root.querySelector('[data-docs-subscope-actions]');
            const menu = root.querySelector('.docsViewerReport__subscopeActionsMenu');
            const selectionControl = root.querySelector(
              '.docsViewerReport__subscopeSelectionControl'
            );
            const prepare = root.querySelector(
              '[data-docs-viewer-action="prepare-document-package"]'
            );
            return {
              actionsExpanded: actions?.getAttribute('aria-expanded') || '',
              checkedIds: checkboxes.filter(checkbox => checkbox.checked)
                .map(checkbox => checkbox.dataset.docsSubscopeSelectionCheckbox),
              menuHidden: menu?.hidden ?? true,
              prepareDisabled: prepare?.disabled ?? true,
              prepareReason: prepare?.dataset.docsViewerDisabledReason || '',
              selectionControlHidden: selectionControl?.hidden ?? true,
              selectionState: root.dataset.reportSubscopeSelection || '',
              visibleCheckboxes: checkboxes.filter(checkbox => (
                !checkbox.closest('[data-report-contribution-host="row-leading"]')?.hidden
              )).length
            };
          };
          const initial = {
            ...selectionSnapshot(),
            actionIds: Array.from(root.querySelectorAll('[data-docs-viewer-action]'))
              .map(button => button.dataset.docsViewerAction),
            nonViewableIcons: root.querySelectorAll('.docsViewer__draftPrefix').length,
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId),
            statusIcons: root.querySelectorAll('.docsViewer__navStatus').length
          };

          root.querySelector('[data-docs-subscope-actions]').click();
          const opened = selectionSnapshot();
          const first = root.querySelector('[data-docs-subscope-selection-checkbox="a"]');
          const last = root.querySelector('[data-docs-subscope-selection-checkbox="c"]');
          first.click();
          last.checked = true;
          last.dispatchEvent(new MouseEvent('click', { bubbles: true, shiftKey: true }));
          const ranged = {
            ...selectionSnapshot(),
            reportState: root.dataset.reportState,
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };
          root.querySelector(
            '[data-docs-viewer-action="prepare-document-package"]'
          ).click();
          await Promise.resolve();
          await Promise.resolve();
          const preparedState = {
            ...selectionSnapshot(),
            prepared
          };

          root.querySelector('[data-docs-subscope-actions]').click();
          root.querySelector('[data-docs-subscope-selection-command="clear"]').click();
          const cleared = selectionSnapshot();
          root.querySelector('[data-docs-subscope-selection-command="select-all"]').click();
          const selectedAll = {
            ...selectionSnapshot(),
            selectAllDisabled: root.querySelector(
              '[data-docs-subscope-selection-command="select-all"]'
            ).disabled
          };

          root.querySelector(
            '[data-report-subdoc-id="b"] .docsViewerReport__subscopeButton'
          ).click();
          await new Promise(resolve => {
            const poll = () => {
              if (root.dataset.reportState === 'detail') {
                resolve();
                return;
              }
              setTimeout(poll, 0);
            };
            poll();
          });
          const detail = {
            selectedIds: Array.from(
              root.querySelectorAll('[data-docs-subscope-selection-checkbox]:checked')
            ).map(checkbox => checkbox.dataset.docsSubscopeSelectionCheckbox),
            toolbarHidden: root.querySelector(
              '[data-report-contribution-host="list-toolbar"]'
            ).hidden
          };
          root.querySelector('.docsReportDetail__back').click();
          const afterBack = selectionSnapshot();
          root.querySelector('[data-docs-subscope-selection-command="done"]').click();
          const done = selectionSnapshot();

          const actions = root.querySelector('[data-docs-subscope-actions]');
          actions.click();
          const reentered = selectionSnapshot();
          document.dispatchEvent(new KeyboardEvent('keydown', {
            bubbles: true,
            key: 'Escape'
          }));
          const escaped = {
            ...selectionSnapshot(),
            actionsFocused: document.activeElement === actions
          };
          actions.click();
          document.querySelector('.docsViewer').click();
          const outsideClosed = selectionSnapshot();
          return {
            afterBack,
            cleared,
            detail,
            done,
            escaped,
            initial,
            opened,
            outsideClosed,
            preparedState,
            ranged,
            reentered,
            selectedAll
          };
        }"""
    )
    expected_initial = {
        "actionsExpanded": "false",
        "checkedIds": [],
        "menuHidden": True,
        "prepareDisabled": True,
        "prepareReason": "Select one or more documents.",
        "selectionControlHidden": True,
        "selectionState": "inactive",
        "visibleCheckboxes": 0,
        "actionIds": ["prepare-document-package"],
        "nonViewableIcons": 1,
        "rowIds": ["a", "b", "c"],
        "statusIcons": 1,
    }
    if result["initial"] != expected_initial:
        raise AssertionError(
            f"unexpected initial sub-scope selection state: {result['initial']!r}"
        )
    assert result["opened"] == {
        "actionsExpanded": "true",
        "checkedIds": [],
        "menuHidden": False,
        "prepareDisabled": True,
        "prepareReason": "Select one or more documents.",
        "selectionControlHidden": False,
        "selectionState": "active",
        "visibleCheckboxes": 3,
    }
    assert result["ranged"] == {
        "actionsExpanded": "true",
        "checkedIds": ["a", "b", "c"],
        "menuHidden": False,
        "prepareDisabled": False,
        "prepareReason": "",
        "selectionControlHidden": False,
        "selectionState": "active",
        "visibleCheckboxes": 3,
        "reportState": "list",
        "subdoc": None,
    }
    assert result["preparedState"] == {
        "actionsExpanded": "false",
        "checkedIds": ["a", "b", "c"],
        "menuHidden": True,
        "prepareDisabled": False,
        "prepareReason": "",
        "selectionControlHidden": False,
        "selectionState": "active",
        "visibleCheckboxes": 3,
        "prepared": [
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_ids": ["a", "b", "c"],
            }
        ],
    }
    assert result["cleared"]["checkedIds"] == []
    assert result["cleared"]["prepareDisabled"] is True
    assert result["cleared"]["prepareReason"] == "Select one or more documents."
    assert result["selectedAll"]["checkedIds"] == ["a", "b", "c"]
    assert result["selectedAll"]["selectAllDisabled"] is True
    assert result["detail"] == {
        "selectedIds": ["a", "b", "c"],
        "toolbarHidden": True,
    }
    assert result["afterBack"]["checkedIds"] == ["a", "b", "c"]
    assert result["afterBack"]["menuHidden"] is True
    assert result["done"]["checkedIds"] == []
    assert result["done"]["selectionControlHidden"] is True
    assert result["done"]["selectionState"] == "inactive"
    assert result["reentered"]["checkedIds"] == []
    assert result["reentered"]["menuHidden"] is False
    assert result["escaped"]["menuHidden"] is True
    assert result["escaped"]["actionsFocused"] is True
    assert result["outsideClosed"]["menuHidden"] is True


def assert_manage_report_bridge(page: Page) -> None:
    mounted = page.evaluate(
        """async () => {
          let bridge;
          try {
            bridge = await import(
              '/docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js'
            );
          } catch (error) {
            return { importError: String(error && (error.stack || error.message) || error) };
          }
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          document.body.innerHTML = (
            '<section class="docsViewer"><main id="bridge-content"></main></section>'
          );
          const requests = [];
          const requestBodies = [];
          const managementStatuses = [];
          window.syntheticInventoryFailure = false;
          window.fetch = async (input, options = {}) => {
            const url = new URL(String(input), window.location.href);
            requests.push(url.pathname + url.search);
            requestBodies.push({
              path: url.pathname,
              body: options.body ? JSON.parse(options.body) : null
            });
            const response = payload => ({
              ok: true,
              status: 200,
              json: async () => payload,
              text: async () => JSON.stringify(payload)
            });
            if (url.pathname === '/reports-registry.json') {
              return response({
                reports: [{
                  report_id: 'docs_subscope',
                  title: 'Sub-scope',
                  default_access: 'local',
                  loader_id: 'docs_subscope'
                }]
              });
            }
            if (url.pathname === '/capabilities') {
              return response({
                ok: true,
                capabilities: {
                  document_delete: {
                    preview: true,
                    apply: true,
                    sub_scope_detail: true
                  }
                }
              });
            }
            if (url.pathname === '/docs/sub-scope-documents') {
              if (window.syntheticInventoryFailure) {
                return {
                  ok: false,
                  status: 503,
                  json: async () => ({ ok: false, error: 'Synthetic inventory failed.' })
                };
              }
              return response({
                ok: true,
                scope: 'studio',
                sub_scope: 'tags',
                documents: [
                  {
                    doc_id: 'detail-doc',
                    title: 'Detail',
                    ui_status: 'draft',
                    viewable: false
                  },
                  {
                    doc_id: 'no-status-doc',
                    title: 'No status',
                    viewable: true
                  }
                ]
              });
            }
            if (url.pathname === '/docs/packages/config') {
              return response({
                ok: true,
                scope: 'studio',
                sub_scope: 'tags',
                workspace: { available: true, message: '' },
                scopes: [{ scope: 'studio', label: 'Studio' }],
                profiles: [{
                  profile_id: 'document-content',
                  label: 'Document content',
                  supports_return_import: false,
                  description: 'Flat child collection export.',
                  target_format: 'jsonl',
                  supported_target_formats: ['jsonl'],
                  content_format: 'markdown',
                  supported_content_formats: ['markdown'],
                  record_shape: 'document_rows',
                  selection: {
                    include_descendants: false,
                    include_non_viewable: true,
                    supports_include_non_viewable: true,
                    supports_missing_summary_only: true,
                    default_missing_summary_only: false
                  },
                  limits: { max_documents: null },
                  external_context: {
                    task: 'Review selected child records',
                    response_guidance: 'Return observations',
                    field_descriptions: { doc_id: 'Stable document id' }
                  },
                  document_fields: [{ output_path: 'doc_id' }]
                }]
              });
            }
            if (url.pathname === '/docs/packages/documents') {
              return response({
                ok: true,
                scope: 'studio',
                sub_scope: 'tags',
                flat_collection: true,
                records: [
                  {
                    doc_id: 'detail-doc',
                    parent_id: '',
                    title: 'Detail',
                    summary: '',
                    selectable: true,
                    viewable: false
                  },
                  {
                    doc_id: 'no-status-doc',
                    parent_id: '',
                    title: 'No status',
                    summary: '',
                    selectable: true,
                    viewable: true
                  }
                ]
              });
            }
            if (url.pathname.endsWith('/detail-doc.json')) {
              return response({
                doc_id: 'detail-doc',
                title: 'Detail',
                content_html: '<h2>Detail</h2>'
              });
            }
            if (url.pathname === '/docs/delete-preview') {
              return response({
                ok: true,
                operation: 'preview',
                target: {
                  scope: 'studio',
                  sub_scope: 'tags',
                  doc_id: 'detail-doc'
                },
                scope: 'studio',
                sub_scope: 'tags',
                doc_id: 'detail-doc',
                title: 'Detail',
                source_revision: 'sha256:' + 'c'.repeat(64),
                allowed: true,
                blockers: [],
                warnings: [],
                delete_count: 1
              });
            }
            if (url.pathname === '/docs/delete-apply') {
              return response({
                ok: true,
                operation: 'apply',
                target: {
                  scope: 'studio',
                  sub_scope: 'tags',
                  doc_id: 'detail-doc'
                },
                scope: 'studio',
                sub_scope: 'tags',
                doc_id: 'detail-doc',
                source_revision: 'sha256:' + 'c'.repeat(64),
                deleted_doc_ids: ['detail-doc'],
                delete_count: 1
              });
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };
          const states = [];
          const content = document.querySelector('#bridge-content');
          const context = {
            appContext: { kind: 'manage' },
            content,
            doc: { doc_id: 'parent-doc' },
            managementContext: true,
            managementService: { baseUrl: window.location.origin },
            payload: {
              viewer_report: 'docs_subscope',
              viewer_report_access: 'local',
              viewer_report_subscope: 'tags'
            },
            publishSubscopeReportState: state => states.push(state),
            routeContext: { reportRegistryUrl: '/reports-registry.json' },
            setStatus: (message, isError) => {
              managementStatuses.push({ message, isError });
            },
            scopeConfigState: {
              docNonViewableEmoji: '🚫',
              scopeConfigs: [{
                scope_id: 'studio',
                subScopes: [{
                  subScope: 'tags',
                  title: 'Tags',
                  manifestUrl: '/synthetic/manifest.json',
                  byIdUrlBase: '/synthetic/by-id'
                }]
              }],
              uiStatusByValue: new Map([
                ['draft', { label: 'Draft', emoji: '📝' }]
              ])
            },
            viewerScope: 'studio'
          };
          await bridge.mountDocsViewerManageDocumentExtras(context);
          const waitFor = predicate => new Promise(resolve => {
            const poll = () => {
              if (predicate()) {
                resolve();
                return;
              }
              setTimeout(poll, 0);
            };
            poll();
          });
          content.querySelector('[data-docs-subscope-actions]').click();
          content.querySelector(
            '[data-docs-subscope-selection-checkbox="detail-doc"]'
          ).click();
          const prepareButton = content.querySelector(
            '[data-docs-viewer-action="prepare-document-package"]'
          );
          prepareButton.click();
          await waitFor(() => document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ));
          const prepareModal = document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          );
          const packageState = {
            checkedIds: Array.from(content.querySelectorAll(
              '[data-docs-subscope-selection-checkbox]:checked'
            )).map(checkbox => checkbox.dataset.docsSubscopeSelectionCheckbox),
            descendantsHidden: prepareModal.querySelector(
              '[data-package-include-descendants-field]'
            )?.hidden ?? null,
            requests: requests.filter(path => path.startsWith('/docs/packages/'))
          };
          prepareModal.querySelector('[data-role="modal-cancel"]').click();
          await waitFor(() => !document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ));
          await waitFor(() => !prepareButton.disabled);
          packageState.checkedIdsAfterCancel = Array.from(content.querySelectorAll(
            '[data-docs-subscope-selection-checkbox]:checked'
          )).map(checkbox => checkbox.dataset.docsSubscopeSelectionCheckbox);

          content.querySelector('[data-report-subdoc-id="detail-doc"] button').click();
          await waitFor(() => states.some(state => (
            state.state === 'detail'
            && state.subdocTarget?.doc_id === 'detail-doc'
          )));
          await waitFor(() => {
            const button = content.querySelector('[data-docs-subscope-delete="true"]');
            return button && !button.disabled;
          });
          const beforeClear = {
            requests: requests.slice(),
            states: states.slice(),
            rows: Array.from(content.querySelectorAll(
              '.docsViewerReport__row[data-report-subdoc-id]'
            ))
              .map(row => ({
                docId: row.dataset.reportSubdocId,
                label: row.querySelector('button')?.getAttribute('aria-label')
              })),
            statusIcons: content.querySelectorAll('.docsViewer__navStatus').length,
            nonViewableIcons: content.querySelectorAll('.docsViewer__draftPrefix').length,
            listToolbarHosts: content.querySelectorAll(
              '[data-report-contribution-host="list-toolbar"]'
            ).length,
            detailToolbarHosts: content.querySelectorAll(
              '[data-report-contribution-host="detail-toolbar"]'
            ).length
          };
          const deleteButton = content.querySelector(
            '[data-docs-subscope-delete="true"]'
          );
          const historyLengthBeforeDelete = history.length;
          deleteButton.click();
          await waitFor(() => document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ));
          const cancelButton = document.querySelector(
            'button[data-role="modal-cancel"]'
          );
          await waitFor(() => document.activeElement === cancelButton);
          const cancelFocused = document.activeElement === cancelButton;
          const modalHostWithinViewer = Boolean(
            document.querySelector(
              '.docsViewer > [data-docs-viewer-management-modal-host="true"]'
            )
          );
          const cancelModalText = document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ).textContent;
          cancelButton.click();
          await waitFor(() => !document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ));
          await waitFor(() => document.activeElement === deleteButton);
          const cancelState = {
            applyRequests: requests.filter(path => path === '/docs/delete-apply').length,
            deleteFocused: document.activeElement === deleteButton,
            focusedCancel: cancelFocused,
            modalHostWithinViewer,
            modalText: cancelModalText,
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };

          deleteButton.click();
          await waitFor(() => document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ));
          document.querySelector('button[data-role="modal-primary"]').click();
          await waitFor(() => (
            content.querySelector('.docsViewerReport')?.dataset.reportState === 'list'
            && !content.querySelector('[data-report-subdoc-id="detail-doc"]')
          ));
          const deleteState = {
            historyLength: history.length,
            inventoryRequests: requests.filter(path => (
              path.startsWith('/docs/sub-scope-documents?')
            )).length,
            requestBodies: requestBodies.filter(record => (
              record.path === '/docs/delete-preview'
              || record.path === '/docs/delete-apply'
            )),
            rowIds: Array.from(content.querySelectorAll(
              '[data-report-subdoc-id]'
            )).map(row => row.dataset.reportSubdocId),
            state: states.at(-1),
            status: managementStatuses.at(-1),
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };
          const navigateHistory = direction => new Promise(resolve => {
            window.addEventListener('popstate', () => resolve(), { once: true });
            history[direction]();
          });
          await navigateHistory('back');
          const backSubdoc = new URLSearchParams(location.search).get('subdoc');
          await navigateHistory('forward');
          const forwardSubdoc = new URLSearchParams(location.search).get('subdoc');
          window.syntheticInventoryFailure = true;
          const failureStates = [];
          const failureContent = document.createElement('main');
          document.body.appendChild(failureContent);
          await bridge.mountDocsViewerManageDocumentExtras({
            ...context,
            content: failureContent,
            publishSubscopeReportState: state => failureStates.push(state)
          });
          window.syntheticInventoryFailure = false;
          const failedInventory = {
            states: failureStates,
            text: failureContent.textContent,
            contributionHosts: failureContent.querySelectorAll(
              '[data-report-contribution-host]'
            ).length
          };
          await bridge.mountDocsViewerManageDocumentExtras({
            publishSubscopeReportState: context.publishSubscopeReportState,
            payload: {}
          });
          return {
            beforeClear,
            cancelState,
            deleteState,
            failedInventory,
            historyNavigation: { backSubdoc, forwardSubdoc },
            historyLengthBeforeDelete,
            latestAfterNonReport: states.at(-1),
            packageState
          };
        }"""
    )

    if mounted.get("importError"):
        raise AssertionError(f"manage report bridge import failed: {mounted['importError']}")

    expected_package_state = {
        "checkedIds": ["detail-doc"],
        "checkedIdsAfterCancel": ["detail-doc"],
        "descendantsHidden": True,
        "requests": [
            "/docs/packages/config?scope=studio&sub_scope=tags",
            "/docs/packages/documents?scope=studio&sub_scope=tags",
        ],
    }
    if mounted["packageState"] != expected_package_state:
        raise AssertionError(
            f"unexpected sub-scope package bridge state: {mounted['packageState']!r}"
        )
    inventory_requests = [
        request
        for request in mounted["beforeClear"]["requests"]
        if request.startswith("/docs/sub-scope-documents?")
    ]
    assert inventory_requests == [
        "/docs/sub-scope-documents?scope=studio&sub_scope=tags"
    ]
    expected_rows = [
        {
            "docId": "detail-doc",
            "label": "Detail, Draft, non-viewable",
        },
        {
            "docId": "no-status-doc",
            "label": None,
        },
    ]
    if mounted["beforeClear"]["rows"] != expected_rows:
        raise AssertionError(
            f"unexpected managed contribution rows: {mounted['beforeClear']['rows']!r}"
        )
    assert mounted["beforeClear"]["statusIcons"] == 1
    assert mounted["beforeClear"]["nonViewableIcons"] == 1
    assert mounted["beforeClear"]["listToolbarHosts"] == 1
    assert mounted["beforeClear"]["detailToolbarHosts"] == 1
    assert mounted["beforeClear"]["states"][-1] == {
        "state": "detail",
        "reason": "detail-loaded",
        "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
        "subdocTarget": {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": "detail-doc",
        },
    }
    assert mounted["cancelState"]["applyRequests"] == 0
    assert mounted["cancelState"]["deleteFocused"] is True
    assert mounted["cancelState"]["focusedCancel"] is True
    assert mounted["cancelState"]["modalHostWithinViewer"] is True
    assert "Document ID: detail-doc" in mounted["cancelState"]["modalText"]
    assert "Sub-scope: studio/tags" in mounted["cancelState"]["modalText"]
    assert mounted["cancelState"]["subdoc"] == "detail-doc"
    assert mounted["deleteState"] == {
        "historyLength": mounted["historyLengthBeforeDelete"],
        "inventoryRequests": 1,
        "requestBodies": [
            {
                "path": "/docs/delete-preview",
                "body": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail-doc",
                },
            },
            {
                "path": "/docs/delete-preview",
                "body": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail-doc",
                },
            },
            {
                "path": "/docs/delete-apply",
                "body": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail-doc",
                    "source_revision": "sha256:" + ("c" * 64),
                    "confirm": True,
                },
            },
        ],
        "rowIds": ["no-status-doc"],
        "state": {
            "state": "list",
            "reason": "list-view",
            "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
            "subdocTarget": None,
        },
        "status": {"message": "", "isError": False},
        "subdoc": None,
    }
    assert mounted["historyNavigation"] == {
        "backSubdoc": None,
        "forwardSubdoc": None,
    }
    assert mounted["failedInventory"] == {
        "states": [
            {
                "state": "loading",
                "reason": "report-mount",
                "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
                "subdocTarget": None,
            },
            {
                "state": "error",
                "reason": "document-source-failed",
                "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
                "subdocTarget": None,
            },
        ],
        "text": "Synthetic inventory failed.",
        "contributionHosts": 0,
    }
    assert mounted["latestAfterNonReport"] == {
        "state": "inactive",
        "reason": "non-report-document",
        "parentTarget": None,
        "subdocTarget": None,
    }


def assert_report_delete_reconciliation(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          const target = {
            scope: 'studio',
            sub_scope: 'tags',
            doc_id: 'detail-doc'
          };
          const subScope = {
            subScope: 'tags',
            title: 'Tags',
            manifestUrl: '/synthetic/manifest.json',
            byIdUrlBase: '/synthetic/by-id'
          };
          window.fetch = async input => {
            const url = new URL(String(input), window.location.href);
            if (url.pathname.endsWith('/detail-doc.json')) {
              return {
                ok: true,
                status: 200,
                json: async () => ({
                  doc_id: 'detail-doc',
                  title: 'Detail',
                  content_html: '<h2>Detail</h2>'
                })
              };
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };

          history.replaceState(
            {},
            '',
            '/?scope=studio&doc=parent-doc&subdoc=detail-doc'
          );
          document.body.innerHTML = '<main><section id="reconcile-report"></section></main>';
          const root = document.querySelector('#reconcile-report');
          let commitDeletedDocument = null;
          let refreshCalls = 0;
          const events = [];
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: { subScopes: [subScope] },
            subscopeDocumentSource: {
              documents: [
                { doc_id: 'detail-doc', title: 'Detail' },
                { doc_id: 'sibling-doc', title: 'Sibling' }
              ],
              refresh: async () => {
                refreshCalls += 1;
                return [{ doc_id: 'sibling-doc', title: 'Sibling' }];
              }
            },
            subscopeReportContribution: {
              notify: event => events.push({
                type: event.type,
                state: event.state || '',
                reason: event.reason || '',
                documentIds: Array.isArray(event.documents)
                  ? event.documents.map(doc => doc.doc_id)
                  : []
              }),
              renderDetailToolbar: context => {
                commitDeletedDocument = context.commitDeletedDocument;
              }
            },
            viewerScope: 'studio'
          });
          const historyLength = history.length;
          const local = await commitDeletedDocument(target);
          const localState = {
            historyLength: history.length,
            refreshCalls,
            reportState: root.dataset.reportState,
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId),
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };
          const recovered = await commitDeletedDocument(target);
          const recoveredState = {
            refreshCalls,
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId)
          };

          history.replaceState(
            {},
            '',
            '/?scope=studio&doc=parent-doc&subdoc=detail-doc'
          );
          const unmountParent = document.createElement('main');
          const unmountRoot = document.createElement('section');
          unmountParent.appendChild(unmountRoot);
          document.body.appendChild(unmountParent);
          let unmountedCommit = null;
          let unmountedRefreshCalls = 0;
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: unmountRoot,
            routeContext: { subScopes: [subScope] },
            subscopeDocumentSource: {
              documents: [{ doc_id: 'detail-doc', title: 'Detail' }],
              refresh: async () => {
                unmountedRefreshCalls += 1;
                return [];
              }
            },
            subscopeReportContribution: {
              renderDetailToolbar: context => {
                unmountedCommit = context.commitDeletedDocument;
              }
            },
            viewerScope: 'studio'
          });
          unmountRoot.remove();
          await new Promise(resolve => setTimeout(resolve, 0));
          const unmounted = await unmountedCommit(target);

          return {
            events,
            historyLength,
            local,
            localState,
            recovered,
            recoveredState,
            unmounted,
            unmountedRefreshCalls
          };
        }"""
    )

    assert result["local"] == {"reconciled": True, "mode": "local"}
    expected_local_state = {
        "historyLength": result["historyLength"],
        "refreshCalls": 0,
        "reportState": "list",
        "rowIds": ["sibling-doc"],
        "subdoc": None,
    }
    if result["localState"] != expected_local_state:
        raise AssertionError(
            f"unexpected local delete reconciliation: {result['localState']!r}"
        )
    assert result["recovered"] == {"reconciled": True, "mode": "refetch"}
    assert result["recoveredState"] == {
        "refreshCalls": 1,
        "rowIds": ["sibling-doc"],
    }
    assert {
        "type": "refresh",
        "state": "",
        "reason": "document-deleted-local",
        "documentIds": ["sibling-doc"],
    } in result["events"]
    assert {
        "type": "refresh",
        "state": "",
        "reason": "document-deleted-recovery",
        "documentIds": ["sibling-doc"],
    } in result["events"]
    assert result["unmounted"] == {
        "reconciled": False,
        "mode": "unmounted",
    }
    assert result["unmountedRefreshCalls"] == 0


def assert_delete_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const module = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-delete-workflow.js'
          );
          document.body.innerHTML = '<main id="workflow-root"></main>';
          const root = document.querySelector('#workflow-root');
          const target = {
            scope: 'studio',
            sub_scope: 'tags',
            doc_id: 'detail-doc'
          };
          const revision = 'sha256:' + 'b'.repeat(64);
          const capabilities = {
            capabilities: {
              document_delete: {
                preview: true,
                apply: true,
                sub_scope_detail: true
              }
            }
          };
          const preview = {
            operation: 'preview',
            target,
            scope: target.scope,
            sub_scope: target.sub_scope,
            doc_id: target.doc_id,
            title: 'Detail',
            source_revision: revision,
            allowed: true,
            blockers: [],
            warnings: ['Synthetic warning.'],
            delete_count: 1
          };
          const applied = {
            operation: 'apply',
            target,
            scope: target.scope,
            sub_scope: target.sub_scope,
            doc_id: target.doc_id,
            source_revision: revision,
            deleted_doc_ids: [target.doc_id],
            delete_count: 1
          };

          function button() {
            const value = document.createElement('button');
            root.appendChild(value);
            return value;
          }

          const successStatuses = [];
          const successCalls = [];
          let confirmOptions = null;
          const successButton = button();
          const success = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: successButton,
            target,
            title: 'Detail',
            readCapabilities: async () => capabilities,
            previewDelete: async value => {
              successCalls.push(['preview', value]);
              return preview;
            },
            confirmDelete: async options => {
              confirmOptions = options;
              return true;
            },
            applyDelete: async (value, valueRevision) => {
              successCalls.push(['apply', value, valueRevision]);
              return applied;
            },
            commitDeletedDocument: async value => {
              successCalls.push(['commit', value]);
              return { reconciled: true, mode: 'local' };
            },
            setStatus: (message, isError) => {
              successStatuses.push({ message, isError });
            }
          });
          const successAvailable = await success.initialize();
          const successResult = await success.run();

          let cancelApplyCount = 0;
          const cancelButton = button();
          const cancel = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: cancelButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: async () => preview,
            confirmDelete: async () => false,
            applyDelete: async () => {
              cancelApplyCount += 1;
              return applied;
            },
            commitDeletedDocument: async () => ({ reconciled: true })
          });
          await cancel.initialize();
          await cancel.run();

          let blockerConfirmCount = 0;
          const blockerStatuses = [];
          const blockerButton = button();
          const blocker = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: blockerButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: async () => ({
              allowed: false,
              blockers: ['Synthetic blocker.']
            }),
            confirmDelete: async () => {
              blockerConfirmCount += 1;
              return true;
            },
            commitDeletedDocument: async () => ({ reconciled: true }),
            setStatus: (message, isError) => blockerStatuses.push({ message, isError })
          });
          await blocker.initialize();
          await blocker.run();

          const staleStatuses = [];
          const staleButton = button();
          const stale = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: staleButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: async () => preview,
            confirmDelete: async () => true,
            applyDelete: async () => {
              const error = new Error('Synthetic source revision conflict.');
              error.status = 409;
              throw error;
            },
            commitDeletedDocument: async () => {
              throw new Error('stale apply must not reconcile');
            },
            setStatus: (message, isError) => staleStatuses.push({ message, isError })
          });
          await stale.initialize();
          await stale.run();

          const recoveryStatuses = [];
          const recoveryButton = button();
          const recovery = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: recoveryButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: async () => preview,
            confirmDelete: async () => true,
            applyDelete: async () => {
              const error = new Error('Synthetic rebuild failure.');
              error.payload = {
                source_restored: true,
                retry_safe: true
              };
              throw error;
            },
            commitDeletedDocument: async () => {
              throw new Error('failed apply must not reconcile');
            },
            setStatus: (message, isError) => recoveryStatuses.push({ message, isError })
          });
          await recovery.initialize();
          await recovery.run();

          const unavailableStatuses = [];
          const unavailableButton = button();
          const unavailable = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: unavailableButton,
            target,
            readCapabilities: async () => {
              throw new Error('Synthetic management service unavailable.');
            },
            commitDeletedDocument: async () => ({ reconciled: true }),
            setStatus: (message, isError) => unavailableStatuses.push({ message, isError })
          });
          const unavailableResult = await unavailable.initialize();

          let resolvePreview;
          let unmountedConfirmCount = 0;
          const unmountedButton = button();
          const unmounted = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: unmountedButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: () => new Promise(resolve => {
              resolvePreview = resolve;
            }),
            confirmDelete: async () => {
              unmountedConfirmCount += 1;
              return true;
            },
            commitDeletedDocument: async () => ({ reconciled: false, mode: 'unmounted' })
          });
          await unmounted.initialize();
          const unmountedRun = unmounted.run();
          unmounted.destroy();
          resolvePreview(preview);
          await unmountedRun;

          let modalAbortApplyCount = 0;
          const modalAbortButton = button();
          const modalAbort = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: modalAbortButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: async () => preview,
            applyDelete: async () => {
              modalAbortApplyCount += 1;
              return applied;
            },
            commitDeletedDocument: async () => ({ reconciled: false })
          });
          await modalAbort.initialize();
          const modalAbortRun = modalAbort.run();
          await new Promise(resolve => {
            const poll = () => {
              if (document.querySelector('[data-role="docs-viewer-management-modal"]')) {
                resolve();
                return;
              }
              setTimeout(poll, 0);
            };
            poll();
          });
          const modalOpenedBeforeDestroy = true;
          modalAbort.destroy();
          await modalAbortRun;
          const modalPresentAfterDestroy = Boolean(document.querySelector(
            '[data-role="docs-viewer-management-modal"]'
          ));

          let resolveApply;
          let applyEnteredResolve;
          let committedAfterDestroy = 0;
          const applyEntered = new Promise(resolve => {
            applyEnteredResolve = resolve;
          });
          const applyingButton = button();
          const applying = module.createDocsViewerManagementSubscopeDeleteWorkflow({
            button: applyingButton,
            target,
            readCapabilities: async () => capabilities,
            previewDelete: async () => preview,
            confirmDelete: async () => true,
            applyDelete: () => {
              applyEnteredResolve();
              return new Promise(resolve => {
                resolveApply = resolve;
              });
            },
            commitDeletedDocument: async () => {
              committedAfterDestroy += 1;
              return { reconciled: false, mode: 'unmounted' };
            }
          });
          await applying.initialize();
          const applyingRun = applying.run();
          await applyEntered;
          applying.destroy();
          resolveApply(applied);
          await applyingRun;

          return {
            capability: {
              direct: module.subScopeDetailDeleteCapability(capabilities),
              missing: module.subScopeDetailDeleteCapability({ capabilities: {} })
            },
            success: {
              available: successAvailable,
              calls: successCalls,
              confirm: {
                body: confirmOptions.body,
                cancelLabel: confirmOptions.cancelLabel,
                initialFocus: confirmOptions.initialFocus,
                primaryLabel: confirmOptions.primaryLabel,
                primaryTone: confirmOptions.primaryTone,
                restoreFocusMatches: confirmOptions.restoreFocus === successButton,
                signalProvided: Boolean(confirmOptions.signal),
                title: confirmOptions.title
              },
              enabled: !successButton.disabled,
              result: successResult,
              statuses: successStatuses
            },
            cancel: {
              applyCount: cancelApplyCount,
              enabled: !cancelButton.disabled
            },
            blocker: {
              confirmCount: blockerConfirmCount,
              enabled: !blockerButton.disabled,
              status: blockerStatuses.at(-1)
            },
            stale: {
              enabled: !staleButton.disabled,
              status: staleStatuses.at(-1)
            },
            recovery: {
              enabled: !recoveryButton.disabled,
              status: recoveryStatuses.at(-1)
            },
            unavailable: {
              enabled: !unavailableButton.disabled,
              result: unavailableResult,
              status: unavailableStatuses.at(-1),
              title: unavailableButton.title
            },
            unmounted: {
              confirmCount: unmountedConfirmCount,
              disabled: unmountedButton.disabled
            },
            modalAbort: {
              applyCount: modalAbortApplyCount,
              disabled: modalAbortButton.disabled,
              modalOpenedBeforeDestroy,
              modalPresentAfterDestroy
            },
            applying: {
              committedAfterDestroy,
              disabled: applyingButton.disabled
            }
          };
        }"""
    )

    target = {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": "detail-doc",
    }
    assert result["capability"] == {"direct": True, "missing": False}
    assert result["success"]["available"] is True
    assert result["success"]["enabled"] is True
    assert result["success"]["calls"] == [
        ["preview", target],
        ["apply", target, "sha256:" + ("b" * 64)],
        ["commit", target],
    ]
    assert result["success"]["confirm"] == {
        "body": [
            "Document: Detail",
            "Document ID: detail-doc",
            "Sub-scope: studio/tags",
            "Synthetic warning.",
        ],
        "cancelLabel": "Cancel",
        "initialFocus": "cancel",
        "primaryLabel": "Delete document",
        "primaryTone": "danger",
        "restoreFocusMatches": True,
        "signalProvided": True,
        "title": "Delete Detail?",
    }
    assert result["success"]["result"]["deleted_doc_ids"] == ["detail-doc"]
    assert result["success"]["statuses"][-1] == {
        "message": "",
        "isError": False,
    }
    assert result["cancel"] == {"applyCount": 0, "enabled": True}
    assert result["blocker"] == {
        "confirmCount": 0,
        "enabled": True,
        "status": {"message": "Synthetic blocker.", "isError": True},
    }
    assert result["stale"] == {
        "enabled": True,
        "status": {
            "message": "Synthetic source revision conflict.",
            "isError": True,
        },
    }
    assert result["recovery"] == {
        "enabled": True,
        "status": {
            "message": (
                "Synthetic rebuild failure. "
                "The source was restored and it is safe to retry."
            ),
            "isError": True,
        },
    }
    assert result["unavailable"] == {
        "enabled": False,
        "result": False,
        "status": {
            "message": "Synthetic management service unavailable.",
            "isError": True,
        },
        "title": "Sub-scope detail Delete is unavailable.",
    }
    assert result["unmounted"] == {"confirmCount": 0, "disabled": True}
    assert result["modalAbort"] == {
        "applyCount": 0,
        "disabled": True,
        "modalOpenedBeforeDestroy": True,
        "modalPresentAfterDestroy": False,
    }
    assert result["applying"] == {
        "committedAfterDestroy": 1,
        "disabled": True,
    }


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
                page.on(
                    "requestfailed",
                    lambda request: errors.append(
                        f"request failed: {request.url}: {request.failure}"
                    ),
                )
                page.on(
                    "response",
                    lambda response: (
                        errors.append(
                            f"response {response.status}: {response.url}"
                        )
                        if response.status >= 400
                        else None
                    ),
                )
                page.goto(base_url, wait_until="domcontentloaded")
                assert_control_projection(page)
                assert_report_module(page)
                assert_subscope_selection_contribution(page)
                assert_report_delete_reconciliation(page)
                assert_delete_workflow(page)
                assert_manage_report_bridge(page)
            finally:
                browser.close()
            if errors:
                raise AssertionError(f"page errors: {errors}")
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer sub-scope report modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
