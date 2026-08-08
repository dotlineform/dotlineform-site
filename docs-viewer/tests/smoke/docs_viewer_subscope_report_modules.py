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
          const targets = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-document-target.js'
          );
          const importControllers = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-import-controller.js'
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
          let invalidCollectionError = '';
          try {
            targets.normalizeManagedDocumentCollectionTarget({
              scope: 'studio',
              sub_scope: 'tags',
              doc_id: 'not-a-collection'
            });
          } catch (error) {
            invalidCollectionError = error.message;
          }
          const collectionTargets = {
            parent: targets.normalizeManagedDocumentCollectionTarget({
              scope: ' Studio '
            }),
            child: targets.normalizeManagedDocumentCollectionTarget({
              scope: ' Studio ',
              sub_scope: ' Tags '
            }),
            childFrozen: Object.isFrozen(
              targets.normalizeManagedDocumentCollectionTarget({
                scope: 'studio',
                sub_scope: 'tags'
              })
            ),
            invalidCollectionError
          };
          const modalOpenRecords = [];
          const modalTerminalRecords = [];
          const appDestinations = [];
          const appRefreshes = [];
          const completionRecords = [];
          let initializedImportOptions = null;
          let importController = null;
          const restoreFocus = document.createElement('button');
          restoreFocus.dataset.docsSubscopeImport = 'true';
          const modalController = {
            openImportModal: options => {
              modalOpenRecords.push({
                restoreFocusMatches: options.restoreFocus === restoreFocus
              });
              return importController.initialize('studio');
            },
            projectImportTerminalResult: () => {
              modalTerminalRecords.push('terminal');
            }
          };
          importController = importControllers.createDocsViewerManagementImportController({
            refs: {
              root: document.createElement('section'),
              bootStatus: document.createElement('p')
            },
            callbacks: {
              getModalController: () => modalController,
              loadImportModule: () => Promise.resolve({
                initDocsHtmlImport: options => {
                  initializedImportOptions = options;
                  return {
                    refreshStagedFiles: () => {
                      appRefreshes.push('refresh');
                    },
                    setDestination: (destination, options) => {
                      appDestinations.push({ destination, options });
                    }
                  };
                }
              }),
              onImportComplete: detail => {
                completionRecords.push({
                  owner: 'default',
                  target: detail.target
                });
              },
              viewerScope: () => 'studio'
            }
          });
          await importController.open(
            {
              destination: { scope: 'studio', sub_scope: 'tags' },
              destinationLabel: 'studio / Tags',
              restoreFocus
            }
          );
          await initializedImportOptions.onTerminalResult({
            target: {
              scope: 'studio',
              sub_scope: 'tags',
              doc_id: 'imported-child'
            }
          });
          await importController.open({
            destination: { scope: 'studio' }
          });
          await initializedImportOptions.onTerminalResult({
            target: {
              scope: 'studio',
              doc_id: 'imported-parent'
            }
          });
          const importControllerProjection = {
            appDestinations,
            appRefreshes,
            completionRecords,
            initialDestination: initializedImportOptions.initialDestination,
            initialDestinationLabel: initializedImportOptions.initialDestinationLabel,
            modalOpenRecords,
            modalTerminalRecords
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
            collectionTargets,
            importControllerProjection,
            requests,
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
    assert result["collectionTargets"] == {
        "parent": {"scope": "studio"},
        "child": {"scope": "studio", "sub_scope": "tags"},
        "childFrozen": True,
        "invalidCollectionError": (
            "Managed document collection target must contain exactly scope, "
            "with sub_scope only for a configured child collection."
        ),
    }
    assert result["importControllerProjection"] == {
        "appDestinations": [
            {
                "destination": {"scope": "studio"},
                "options": {
                    "label": "",
                },
            }
        ],
        "appRefreshes": ["refresh"],
        "completionRecords": [
            {
                "owner": "default",
                "target": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "imported-child",
                },
            },
            {
                "owner": "default",
                "target": {
                    "scope": "studio",
                    "doc_id": "imported-parent",
                },
            },
        ],
        "initialDestination": {"scope": "studio", "sub_scope": "tags"},
        "initialDestinationLabel": "studio / Tags",
        "modalOpenRecords": [
            {"restoreFocusMatches": True},
            {"restoreFocusMatches": False},
        ],
        "modalTerminalRecords": ["terminal", "terminal"],
    }
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


def assert_filter_source_boundaries(site_root: Path) -> None:
    shared_root = site_root / "site/docs-viewer/runtime/js/shared"
    filter_source = (shared_root / "docs-subscope-report-filter.js").read_text(
        encoding="utf-8"
    )
    report_source = (shared_root / "docs-subscope-report.js").read_text(
        encoding="utf-8"
    )
    assert "fetch(" not in filter_source
    assert "import " not in filter_source
    assert "docs-viewer-management" not in report_source
    assert "docs-viewer-search" not in report_source


def assert_filter_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const filter = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report-filter.js'
          );
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          const manageRegistry = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-customisation-registry.js'
          );
          const pureDocuments = Object.freeze([
            Object.freeze({
              doc_id: 'first',
              title: 'Alpha beta',
              group: 'subject',
              ui_status: 'needle'
            }),
            Object.freeze({
              doc_id: 'needle',
              title: 'ALPINE',
              group: 'domain'
            }),
            Object.freeze({
              doc_id: 'third',
              title: 'Beta',
              group: 'subject'
            })
          ]);
          const ids = documents => documents.map(documentRecord => documentRecord.doc_id);
          const pure = {
            prefix: ids(filter.projectDocsSubscopeDocuments(
              pureDocuments,
              { query: 'alp' }
            )),
            normalized: ids(filter.projectDocsSubscopeDocuments(
              pureDocuments,
              { query: '  ALPHA   B ' }
            )),
            ignoresGroup: ids(filter.projectDocsSubscopeDocuments(
              pureDocuments,
              { query: 'alp', group: 'DOMAIN' }
            )),
            ignoresDocId: ids(filter.projectDocsSubscopeDocuments(
              pureDocuments,
              { query: 'needle' }
            ))
          };

          history.replaceState({}, '', '/?scope=analysis&doc=parent-doc');
          document.body.innerHTML = '<main><section id="filter-report"></section></main>';
          const root = document.querySelector('#filter-report');
          const requests = [];
          const refreshes = [];
          const projections = [];
          const toolbarProjections = [];
          window.fetch = async input => {
            const url = new URL(String(input), window.location.href);
            requests.push(url.pathname);
            const response = payload => ({
              ok: true,
              status: 200,
              json: async () => payload
            });
            if (url.pathname === '/filter/manifest.json') {
              return response({
                customisation: {
                  id: 'analysis_tags',
                  data: { groups: ['subject', 'domain', 'form', 'theme'] }
                },
                docs: [
                  { doc_id: 'alpha', title: 'Alpha', customisation: { group: 'subject' } },
                  { doc_id: 'alpine', title: 'Alpine', customisation: { group: 'domain' } },
                  { doc_id: 'beta', title: 'Beta', customisation: { group: 'subject' } },
                  { doc_id: 'gamma', title: 'Gamma', customisation: { group: 'form' } },
                  { doc_id: 'alps', title: 'Alps' }
                ]
              });
            }
            if (url.pathname.startsWith('/filter/by-id/')) {
              const docId = decodeURIComponent(
                url.pathname.split('/').pop().replace(/\\.json$/, '')
              );
              return response({
                doc_id: docId,
                title: docId === 'alpha' ? 'Alpha' : docId,
                content_html: `<h2>${docId}</h2>`
              });
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };
          const analysisTags = await manageRegistry.resolveManagementDocsSubscopeCustomisation({
            id: 'analysis_tags'
          });
          const contribution = Object.assign({}, analysisTags, {
            notify: event => {
              if (event.type === 'refresh') {
                refreshes.push(ids(event.documents));
              }
              if (event.type === 'projection') {
                projections.push(ids(event.documents));
              }
            },
            renderListToolbar: ({ documents }) => {
              toolbarProjections.push(ids(documents));
            }
          });
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Tags',
                manifestUrl: '/filter/manifest.json',
                byIdUrlBase: '/filter/by-id',
                subScopeCustomisation: { id: 'analysis_tags' }
              }]
            },
            subscopeReportContribution: contribution,
            viewerScope: 'analysis'
          });

          const snapshot = () => {
            const input = root.querySelector('.docsViewerReport__searchInput');
            const filterLabel = root.querySelector(`label[for="${input.id}"]`);
            const status = root.querySelector('.docsViewerReport__status');
            return {
              activeGroup: root.querySelector(
                '[data-docs-subscope-group][aria-pressed="true"]'
              )?.dataset.docsSubscopeGroup ?? null,
              clearLabel: root.querySelector(
                '.docsViewerReport__searchClear'
              )?.getAttribute('aria-label') || '',
              empty: root.querySelector('.docsViewerReport__empty')?.textContent || '',
              filterLabel: filterLabel?.textContent || '',
              filterLabelHidden: filterLabel?.classList.contains('visually-hidden') || false,
              groupLabels: Array.from(
                root.querySelectorAll('[data-docs-subscope-group]')
              ).map(button => button.textContent),
              placeholder: input.placeholder,
              query: input.value,
              rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
                .map(row => row.dataset.reportSubdocId),
              status: status?.textContent || '',
              statusHidden: status?.classList.contains('visually-hidden') || false,
              statusRole: status?.getAttribute('role') || ''
            };
          };
          const initial = snapshot();
          const input = root.querySelector('.docsViewerReport__searchInput');
          input.value = '  ALP ';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          const prefix = {
            ...snapshot(),
            requests: requests.slice()
          };
          root.querySelector('[data-docs-subscope-group="subject"]').click();
          const subject = snapshot();
          root.querySelector(
            '[data-report-subdoc-id="alpha"] .docsViewerReport__subscopeButton'
          ).click();
          await new Promise(resolve => {
            const poll = () => {
              if (root.dataset.reportState === 'detail') return resolve();
              setTimeout(poll, 0);
            };
            poll();
          });
          const detail = {
            filtersHidden: root.querySelector('[data-docs-subscope-filters]').hidden,
            requests: requests.slice()
          };
          root.querySelector('.docsReportDetail__back').click();
          const afterBack = snapshot();
          root.querySelector('[data-docs-subscope-group=""]').click();
          const allWithQuery = snapshot();
          root.querySelector('[data-docs-subscope-group="subject"]').click();
          root.querySelector('.docsViewerReport__searchClear').click();
          const afterClear = snapshot();
          root.querySelector('[data-docs-subscope-group=""]').click();
          input.value = 'zzz';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          const noMatch = snapshot();
          return {
            afterBack,
            afterClear,
            allWithQuery,
            detail,
            initial,
            noMatch,
            prefix,
            projections,
            pure,
            refreshes,
            subject,
            toolbarProjections
          };
        }"""
    )
    assert result["pure"] == {
        "prefix": ["first", "needle"],
        "normalized": ["first"],
        "ignoresGroup": ["first", "needle"],
        "ignoresDocId": [],
    }
    assert result["initial"] == {
        "activeGroup": "",
        "clearLabel": "Clear Tags title filter",
        "empty": "",
        "filterLabel": "Filter Tags by title",
        "filterLabelHidden": True,
        "groupLabels": [
            "all",
            "subject",
            "domain",
            "form",
            "theme",
        ],
        "placeholder": "search",
        "query": "",
        "rowIds": ["alpha", "alpine", "alps", "beta", "gamma"],
        "status": "5 Tags documents",
        "statusHidden": True,
        "statusRole": "status",
    }, result["initial"]
    assert result["prefix"]["rowIds"] == ["alpha", "alpine", "alps"]
    assert result["prefix"]["status"] == "3 of 5 Tags documents"
    assert result["prefix"]["requests"] == ["/filter/manifest.json"]
    assert result["subject"]["rowIds"] == ["alpha"]
    assert result["subject"]["query"] == "  ALP "
    assert result["subject"]["activeGroup"] == "subject"
    assert result["subject"]["status"] == "1 of 5 Tags documents"
    assert result["detail"] == {
        "filtersHidden": True,
        "requests": ["/filter/manifest.json", "/filter/by-id/alpha.json"],
    }
    assert result["afterBack"]["query"] == "  ALP "
    assert result["afterBack"]["activeGroup"] == "subject"
    assert result["afterBack"]["rowIds"] == ["alpha"]
    assert result["allWithQuery"]["query"] == "  ALP "
    assert result["allWithQuery"]["activeGroup"] == ""
    assert result["allWithQuery"]["rowIds"] == ["alpha", "alpine", "alps"]
    assert result["afterClear"]["query"] == ""
    assert result["afterClear"]["activeGroup"] == "subject"
    assert result["afterClear"]["rowIds"] == ["alpha", "beta"]
    assert result["noMatch"]["rowIds"] == []
    assert result["noMatch"]["status"] == "0 of 5 Tags documents"
    assert result["noMatch"]["empty"] == "No tags match the current filters."
    assert result["refreshes"] == [
        ["alpha", "alpine", "beta", "gamma", "alps"],
    ]
    assert result["projections"] == result["toolbarProjections"]
    assert result["projections"] == [
        ["alpha", "alpine", "alps", "beta", "gamma"],
        ["alpha", "alpine", "alps"],
        ["alpha"],
        ["alpha"],
        ["alpha", "alpine", "alps"],
        ["alpha"],
        ["alpha", "beta"],
        ["alpha", "alpine", "alps", "beta", "gamma"],
        [],
    ]


def assert_report_module(page: Page) -> None:
    page.evaluate(
        """() => {
          window.syntheticDetailMode = 'immediate';
          window.syntheticDetailResolve = null;
          window.syntheticManifestDocs = [
            {
              doc_id: 'visible-doc',
              title: 'Visible document',
              ui_status: 'done',
              publishable: true
            },
            {
              doc_id: 'hidden-doc',
              title: 'Hidden document',
              ui_status: 'draft',
              publishable: false
            }
          ];
          window.syntheticManifestFailure = false;
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
              if (window.syntheticManifestFailure) {
                return {
                  ok: false,
                  status: 503,
                  json: async () => ({})
                };
              }
              return response({
                docs: window.syntheticManifestDocs
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
            listToolbarInFilterRow: root.querySelector(
              '[data-docs-subscope-filters] '
                + '[data-report-contribution-host="list-toolbar"]'
            ) !== null,
            leadingColumn: root.dataset.reportLeadingColumn || '',
            states: window.syntheticReportStates,
            contributionEvents: window.syntheticContributionEvents
          };
        }"""
    )
    expected_managed = {
        "rowIds": ["hidden-doc", "visible-doc"],
        "labels": [
            "Hidden document, draft",
            "Visible document, done",
        ],
        "titlePrefixes": 2,
        "leadingControls": 1,
        "leadingHosts": 2,
        "listToolbar": "List contribution",
        "listToolbarInFilterRow": True,
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
                "type": "projection",
                "collection": {"scope": "studio", "sub_scope": "tags"},
                "state": "",
                "reason": "filters-projected",
                "target": None,
                "documentIds": ["hidden-doc", "visible-doc"],
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
          title: document.querySelector('.docsReportDetail').dataset.reportSubdocTitle,
          titleNodeCount: document.querySelectorAll('.docsReportDetail__title').length,
          backLabel: document.querySelector('.docsReportDetail__back')
            ?.getAttribute('aria-label') || '',
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
        "titleNodeCount": 0,
        "backLabel": "Back to all tags",
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
          window.syntheticManifestDocs = [
            { doc_id: 'visible-doc', title: 'Visible document' }
          ];
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
          window.syntheticManifestDocs = [
            { doc_id: 'visible-doc', title: 'Visible document' }
          ];
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
          window.syntheticManifestDocs = [
            { doc_id: 'visible-doc', title: 'Visible document' }
          ];
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
          window.syntheticManifestDocs = [];
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: emptyRoot,
            routeContext: { subScopes: [subScope] },
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
          window.syntheticManifestFailure = true;
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: failedRoot,
            routeContext: { subScopes: [subScope] },
            subscopeReportContribution: {
              notify: event => failedEvents.push({
                type: event.type,
                state: event.state || '',
                reason: event.reason || ''
              })
            },
            viewerScope: 'studio'
          });
          window.syntheticManifestFailure = false;
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
                    "type": "projection",
                    "state": "",
                    "reason": "filters-projected",
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
            "text": (
                "Filter Tags by title×0 Tags documents"
                "No documents are available in Tags."
            ),
        },
        "failed": {
            "contributionHosts": 0,
            "events": [
                {"type": "mount", "state": "", "reason": ""},
                {
                    "type": "state",
                    "state": "loading",
                    "reason": "report-loading",
                },
                {
                    "type": "state",
                    "state": "error",
                    "reason": "report-load-failed",
                },
            ],
            "state": "error",
            "text": "Failed to load docs sub-scope manifest (503)",
        },
    }

    public = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          window.syntheticPayloadDocId = '';
          window.syntheticManifestDocs = [
            { doc_id: 'visible-doc', title: 'Visible document' }
          ];
          document.body.innerHTML = '<main><section id="public-report"></section></main>';
          const root = document.querySelector('#public-report');
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: {
              subScopes: [{
                subScope: 'tags',
                title: 'Concepts',
                manifestUrl: '/synthetic/manifest.json',
                byIdUrlBase: '/synthetic/by-id'
              }]
            },
            viewerScope: 'studio'
          });
          const button = root.querySelector('.docsViewerReport__subscopeButton');
          const input = root.querySelector('.docsViewerReport__searchInput');
          const filterLabel = root.querySelector(`label[for="${input.id}"]`);
          const status = root.querySelector('.docsViewerReport__status');
          return {
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(node => node.dataset.reportSubdocId),
            filterLabel: filterLabel?.textContent || '',
            filterLabelHidden: filterLabel?.classList.contains('visually-hidden') || false,
            groupControls: root.querySelectorAll('[data-docs-subscope-group]').length,
            listLabel: root.querySelector('.docsViewerReport__rows')
              ?.getAttribute('aria-label') || '',
            placeholder: input.placeholder,
            status: status?.textContent || '',
            statusHidden: status?.classList.contains('visually-hidden') || false,
            statusIcons: root.querySelectorAll('.docsViewer__navStatus').length,
            nonPublishableIcons: root.querySelectorAll('.docsViewer__publishableExclusion').length,
            contributionHosts: root.querySelectorAll(
              '[data-report-contribution-host]'
            ).length,
            ariaLabel: button ? button.getAttribute('aria-label') : null
          };
        }"""
    )
    assert public == {
        "rowIds": ["visible-doc"],
        "filterLabel": "Filter Concepts by title",
        "filterLabelHidden": True,
        "groupControls": 0,
        "listLabel": "Concepts",
        "placeholder": "search",
        "status": "1 Concepts document",
        "statusHidden": True,
        "statusIcons": 0,
        "nonPublishableIcons": 0,
        "contributionHosts": 0,
        "ariaLabel": None,
    }


def assert_subscope_selection_contribution(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          const defaults = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-default-contribution.js'
          );
          const composition = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-composition.js'
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
            if (url.pathname === '/synthetic/manifest.json') {
              return response({
                docs: [
                  { doc_id: 'a', title: 'A', publishable: true },
                  { doc_id: 'b', title: 'B', ui_status: 'draft', publishable: false },
                  { doc_id: 'c', title: 'C', publishable: true }
                ]
              });
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
          const copied = [];
          const prepared = [];
          const root = document.querySelector('#selection-report');
          const defaultContribution = defaults.createDocsViewerManagementSubscopeDefaultContribution({
            clientOptions: { baseUrl: window.location.origin },
            managementContext: true,
            nonPublishableEmoji: '🚫',
            onCopyDocuments: payload => copied.push(payload),
            onPreparePackage: payload => prepared.push(payload),
            root: document.querySelector('.docsViewer'),
            uiStatusByValue: new Map([
              ['draft', { label: 'Draft', emoji: '📝' }]
            ])
          });
          const contribution = composition.composeDocsViewerManagementSubscopeContributions({
            defaultContribution
          });
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
            nonPublishableIcons: root.querySelectorAll('.docsViewer__publishableExclusion').length,
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId),
            statusIcons: root.querySelectorAll('.docsViewer__navStatus').length,
            toolbarInFilterRow: root.querySelector(
              '[data-docs-subscope-filters] '
                + '[data-report-contribution-host="list-toolbar"]'
            ) !== null
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
          const copyButton = root.querySelector(
            '[data-docs-viewer-action="copy"]'
          );
          const copyBefore = {
            disabled: copyButton.disabled,
            label: copyButton.textContent,
            reason: copyButton.dataset.docsViewerDisabledReason || ''
          };
          copyButton.click();
          await Promise.resolve();
          await Promise.resolve();
          const copiedState = {
            copied,
            menuHidden: root.querySelector(
              '.docsViewerReport__subscopeActionsMenu'
            ).hidden
          };
          const filterInput = root.querySelector('.docsViewerReport__searchInput');
          filterInput.value = 'B';
          filterInput.dispatchEvent(new Event('input', { bubbles: true }));
          const filtered = {
            ...selectionSnapshot(),
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId)
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
          root.querySelector('.docsViewerReport__searchClear').click();
          const restoredAfterFilter = selectionSnapshot();

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
            copyBefore,
            copiedState,
            detail,
            done,
            escaped,
            filtered,
            initial,
            opened,
            outsideClosed,
            preparedState,
            ranged,
            reentered,
            restoredAfterFilter,
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
        "visibleCheckboxes": 3,
        "actionIds": ["copy", "prepare-document-package"],
        "nonPublishableIcons": 1,
        "rowIds": ["a", "b", "c"],
        "statusIcons": 1,
        "toolbarInFilterRow": True,
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
    assert result["copyBefore"] == {
        "disabled": False,
        "label": "⧉Copy to…",
        "reason": "",
    }
    assert result["copiedState"] == {
        "copied": [
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_ids": ["a", "b", "c"],
            }
        ],
        "menuHidden": True,
    }
    assert result["preparedState"] == {
        "actionsExpanded": "false",
        "checkedIds": ["b"],
        "menuHidden": True,
        "prepareDisabled": False,
        "prepareReason": "",
        "selectionControlHidden": False,
        "selectionState": "active",
        "visibleCheckboxes": 1,
        "prepared": [
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_ids": ["a", "b", "c"],
            }
        ],
    }
    assert result["filtered"] == {
        "actionsExpanded": "false",
        "checkedIds": ["b"],
        "menuHidden": True,
        "prepareDisabled": False,
        "prepareReason": "",
        "selectionControlHidden": False,
        "selectionState": "active",
        "visibleCheckboxes": 1,
        "rowIds": ["b"],
    }
    assert result["restoredAfterFilter"]["checkedIds"] == ["a", "b", "c"]
    assert result["restoredAfterFilter"]["visibleCheckboxes"] == 3
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
          window.syntheticManifestFailure = false;
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
            if (url.pathname === '/synthetic/manifest.json') {
              if (window.syntheticManifestFailure) {
                return {
                  ok: false,
                  status: 503,
                  json: async () => ({})
                };
              }
              return response({
                customisation: {
                  id: 'analysis_tags',
                  data: { groups: ['subject', 'domain', 'form', 'theme'] }
                },
                docs: [
                  {
                    doc_id: 'detail-doc',
                    title: 'Detail',
                    ui_status: 'draft',
                    publishable: false,
                    customisation: { group: 'subject' }
                  },
                  {
                    doc_id: 'no-status-doc',
                    title: 'No status',
                    publishable: true,
                    customisation: { group: 'domain' }
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
                    include_non_publishable: true,
                    supports_include_non_publishable: true,
                    supports_missing_summary_only: true,
                    default_missing_summary_only: false
                  },
                  limits: { max_documents: null },
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
                    publishable: false
                  },
                  {
                    doc_id: 'no-status-doc',
                    parent_id: '',
                    title: 'No status',
                    summary: '',
                    selectable: true,
                    publishable: true
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
          let latestDetailProjection = null;
          const serialState = state => {
            const {
              refreshCollection,
              refreshDocument,
              subdocInfo,
              subdocRecord,
              ...serial
            } = state;
            return serial;
          };
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
            publishSubscopeReportState: state => {
              if (state.state === 'detail') {
                latestDetailProjection = {
                  info: state.subdocInfo,
                  record: state.subdocRecord,
                  target: state.subdocTarget
                };
              }
              states.push(serialState(state));
            },
            routeContext: { reportRegistryUrl: '/reports-registry.json' },
            setStatus: (message, isError) => {
              managementStatuses.push({ message, isError });
            },
            scopeConfigState: {
              docNonPublishableEmoji: '🚫',
              scopeConfigs: [{
                scope_id: 'studio',
                subScopes: [{
                  subScope: 'tags',
                  title: 'Tags',
                  manifestUrl: '/synthetic/manifest.json',
                  byIdUrlBase: '/synthetic/by-id',
                  subScopeCustomisation: { id: 'analysis_tags' }
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
            detailProjection: latestDetailProjection,
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
            nonPublishableIcons: content.querySelectorAll('.docsViewer__publishableExclusion').length,
            listToolbarHosts: content.querySelectorAll(
              '[data-report-contribution-host="list-toolbar"]'
            ).length,
            detailToolbarHosts: content.querySelectorAll(
              '[data-report-contribution-host="detail-toolbar"]'
            ).length,
            groupLabels: Array.from(content.querySelectorAll(
              '[data-docs-subscope-group]'
            )).map(button => button.textContent)
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
            manifestRequests: requests.filter(path => (
              path.startsWith('/synthetic/manifest.json')
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
          window.syntheticManifestFailure = true;
          const failureStates = [];
          const failureContent = document.createElement('main');
          document.body.appendChild(failureContent);
          await bridge.mountDocsViewerManageDocumentExtras({
            ...context,
            content: failureContent,
            publishSubscopeReportState: state => failureStates.push(serialState(state))
          });
          window.syntheticManifestFailure = false;
          const failedManifest = {
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
            failedManifest,
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
    assert mounted["beforeClear"]["detailProjection"] == {
        "info": None,
        "record": {
            "doc_id": "detail-doc",
            "title": "Detail",
            "ui_status": "draft",
            "publishable": False,
        },
        "target": {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": "detail-doc",
        },
    }
    manifest_requests = [
        request
        for request in mounted["beforeClear"]["requests"]
        if request.startswith("/synthetic/manifest.json")
    ]
    assert manifest_requests == ["/synthetic/manifest.json"]
    expected_rows = [
        {
            "docId": "detail-doc",
            "label": "Detail, Draft, Excluded from next Publish",
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
    assert mounted["beforeClear"]["nonPublishableIcons"] == 1
    assert mounted["beforeClear"]["listToolbarHosts"] == 1
    assert mounted["beforeClear"]["detailToolbarHosts"] == 1
    assert mounted["beforeClear"]["groupLabels"] == [
        "all",
        "subject",
        "domain",
        "form",
        "theme",
    ]
    assert mounted["beforeClear"]["states"][-1] == {
        "state": "detail",
        "reason": "detail-loaded",
        "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
        "collectionTarget": {"scope": "studio", "sub_scope": "tags"},
        "collectionLabel": "studio / Tags",
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
        "manifestRequests": 1,
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
            "collectionTarget": {"scope": "studio", "sub_scope": "tags"},
            "collectionLabel": "studio / Tags",
            "subdocTarget": None,
        },
        "status": {"message": "", "isError": False},
        "subdoc": None,
    }
    assert mounted["historyNavigation"] == {
        "backSubdoc": None,
        "forwardSubdoc": None,
    }
    assert mounted["failedManifest"] == {
        "states": [
            {
                "state": "loading",
                "reason": "report-mount",
                "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
                "collectionTarget": {"scope": "studio", "sub_scope": "tags"},
                "collectionLabel": "studio / Tags",
                "subdocTarget": None,
            },
            {
                "state": "loading",
                "reason": "report-loading",
                "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
                "collectionTarget": {"scope": "studio", "sub_scope": "tags"},
                "collectionLabel": "studio / Tags",
                "subdocTarget": None,
            },
            {
                "state": "error",
                "reason": "report-load-failed",
                "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
                "collectionTarget": {"scope": "studio", "sub_scope": "tags"},
                "collectionLabel": "studio / Tags",
                "subdocTarget": None,
            },
        ],
        "text": "Failed to load docs sub-scope manifest (503)",
        "contributionHosts": 0,
    }
    assert mounted["latestAfterNonReport"] == {
        "state": "inactive",
        "reason": "non-report-document",
        "parentTarget": None,
        "collectionTarget": None,
        "collectionLabel": "",
        "subdocTarget": None,
    }


def assert_subscope_create_contribution_and_report_refresh(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const bridge = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          document.body.innerHTML = (
            '<section class="docsViewer"><main id="create-report"></main></section>'
          );
          window.syntheticCreatedDocs = [];
          const fetches = [];
          window.fetch = async (input, options = {}) => {
            const url = new URL(String(input), window.location.href);
            fetches.push({
              path: url.pathname,
              cache: options.cache || 'default'
            });
            const response = payload => ({
              ok: true,
              status: 200,
              json: async () => payload
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
              return response({ ok: true, capabilities: {} });
            }
            if (url.pathname === '/synthetic/manifest.json') {
              return response({ docs: window.syntheticCreatedDocs });
            }
            if (url.pathname.startsWith('/synthetic/by-id/')) {
              const docId = decodeURIComponent(
                url.pathname.split('/').pop().replace(/\\.json$/, '')
              );
              const record = window.syntheticCreatedDocs.find(
                doc => doc.doc_id === docId
              );
              if (!record) {
                return { ok: false, status: 404, json: async () => ({}) };
              }
              return response({
                doc_id: record.doc_id,
                title: record.title,
                content_html: `<h2>${record.title}</h2>`
              });
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };

          const copyCalls = [];
          const createCalls = [];
          const releases = [];
          const states = [];
          const statuses = [];
          const content = document.querySelector('#create-report');
          await bridge.mountDocsViewerManageDocumentExtras({
            appContext: { kind: 'manage' },
            content,
            doc: { doc_id: 'parent-doc' },
            managementContext: true,
            managementDocumentActions: {
              copySubscopeDocuments: (selection, options) => {
                copyCalls.push({
                  selection,
                  hasRestoreFocus: Boolean(options.restoreFocus)
                });
                return Promise.resolve(null);
              },
              createSubscopeDocument: (collection, options) => {
                createCalls.push({
                  collection,
                  refreshAndSelectType: typeof options.refreshAndSelect
                });
                return new Promise((resolve, reject) => {
                  releases.push(record => {
                    window.syntheticCreatedDocs.push(record);
                    const target = {
                      scope: collection.scope,
                      sub_scope: collection.sub_scope,
                      doc_id: record.doc_id
                    };
                    Promise.resolve(options.refreshAndSelect(target))
                      .then(resolve, reject);
                  });
                });
              }
            },
            managementService: { baseUrl: window.location.origin },
            payload: {
              viewer_report: 'docs_subscope',
              viewer_report_access: 'local',
              viewer_report_subscope: 'tags'
            },
            publishSubscopeReportState: state => states.push(state),
            routeContext: { reportRegistryUrl: '/reports-registry.json' },
            setStatus: (message, isError) => {
              statuses.push({ message, isError });
            },
            scopeConfigState: {
              scopeConfigs: [{
                scope_id: 'studio',
                subScopes: [{
                  subScope: 'tags',
                  title: 'Tags',
                  manifestUrl: '/synthetic/manifest.json',
                  byIdUrlBase: '/synthetic/by-id'
                }]
              }]
            },
            viewerScope: 'studio'
          });

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
          const serialReportState = () => {
            const {
              refreshCollection,
              refreshDocument,
              subdocInfo,
              subdocRecord,
              ...state
            } = states.at(-1);
            return state;
          };
          const newButton = () => content.querySelector(
            '[data-docs-subscope-new="true"]'
          );
          const initial = {
            actionsDisabled: content.querySelector(
              '[data-docs-subscope-actions]'
            ).disabled,
            contributionHosts: content.querySelectorAll(
              '[data-report-contribution-host="list-toolbar"]'
            ).length,
            emptyText: content.querySelector(
              '.docsViewerReport__empty'
            ).textContent,
            importButtons: content.querySelectorAll(
              '[data-docs-subscope-import="true"]'
            ).length,
            newButtons: content.querySelectorAll(
              '[data-docs-subscope-new="true"]'
            ).length,
            rowIds: Array.from(content.querySelectorAll(
              '[data-report-subdoc-id]'
            )).map(row => row.dataset.reportSubdocId)
          };

          const refreshTypes = {
            collection: typeof states.at(-1).refreshCollection,
            document: typeof states.at(-1).refreshDocument
          };
          const importedRecord = {
            doc_id: 'imported-first',
            title: 'Imported first',
            publishable: false
          };
          window.syntheticCreatedDocs.push(importedRecord);
          await states.at(-1).refreshDocument({
            scope: 'studio',
            sub_scope: 'tags',
            doc_id: importedRecord.doc_id
          });
          await waitFor(() => (
            content.querySelector('.docsReportDetail')
              ?.dataset.reportSubdocId === 'imported-first'
          ));
          const imported = {
            detailText: content.querySelector(
              '.docsReportDetail__body'
            ).textContent,
            state: serialReportState(),
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };

          content.querySelector('.docsReportDetail__back').click();
          await waitFor(() => content.querySelector(
            '.docsViewerReport'
          )?.dataset.reportState === 'list');
          const packageHistoryLength = history.length;
          window.syntheticCreatedDocs[0] = {
            ...window.syntheticCreatedDocs[0],
            title: 'Imported first refreshed'
          };
          window.syntheticCreatedDocs.push({
            doc_id: 'package-imported',
            title: 'Package imported',
            publishable: true
          });
          await states.at(-1).refreshCollection({
            scope: 'studio',
            sub_scope: 'tags'
          });
          await waitFor(() => content.querySelector(
            '[data-report-subdoc-id="package-imported"]'
          ));
          const packageImported = {
            historyLength: history.length,
            reportState: content.querySelector('.docsViewerReport')
              ?.dataset.reportState,
            rowIds: Array.from(content.querySelectorAll(
              '.docsViewerReport__row[data-report-subdoc-id]'
            )).map(row => row.dataset.reportSubdocId),
            rowTitles: Array.from(content.querySelectorAll(
              '[data-report-subdoc-id] .docsViewerReport__title'
            )).map(node => node.textContent),
            selectionState: content.querySelector('.docsViewerReport')
              ?.dataset.reportSubscopeSelection || '',
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };
          content.querySelector('[data-docs-subscope-actions]').click();
          content.querySelector(
            '[data-docs-subscope-selection-command="select-all"]'
          ).click();
          content.querySelector('[data-docs-viewer-action="copy"]').click();
          await Promise.resolve();
          await Promise.resolve();
          const copied = copyCalls.slice();
          newButton().click();
          const inFlight = {
            ariaLabel: newButton().getAttribute('aria-label'),
            calls: createCalls.length,
            disabled: newButton().disabled
          };
          newButton().click();
          inFlight.callsAfterSecondClick = createCalls.length;
          releases[0]({
            doc_id: 'created-first',
            title: 'Created first',
            publishable: false
          });
          await waitFor(() => (
            content.querySelector('.docsReportDetail')
              ?.dataset.reportSubdocId === 'created-first'
          ));
          const first = {
            calls: createCalls.slice(),
            detailText: content.querySelector(
              '.docsReportDetail__body'
            ).textContent,
            state: serialReportState(),
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };

          content.querySelector('.docsReportDetail__back').click();
          await waitFor(() => content.querySelector(
            '.docsViewerReport'
          )?.dataset.reportState === 'list');
          newButton().click();
          releases[1]({
            doc_id: 'created-second',
            title: 'Created second',
            publishable: false
          });
          await waitFor(() => (
            content.querySelector('.docsReportDetail')
              ?.dataset.reportSubdocId === 'created-second'
          ));
          const second = {
            calls: createCalls.slice(),
            detailText: content.querySelector(
              '.docsReportDetail__body'
            ).textContent,
            refreshEvents: states.filter(state => (
              state.reason === 'detail-loaded'
            )).length,
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };

          return {
            copied,
            fetches: fetches.filter(record => (
              record.path.startsWith('/synthetic/')
            )),
            first,
            imported,
            inFlight,
            initial,
            packageHistoryLength,
            packageImported,
            refreshTypes,
            second,
            statuses
          };
        }"""
    )

    assert result["initial"] == {
        "actionsDisabled": True,
        "contributionHosts": 1,
        "emptyText": "No documents are available in Tags.",
        "importButtons": 0,
        "newButtons": 1,
        "rowIds": [],
    }
    assert result["inFlight"] == {
        "ariaLabel": "New",
        "calls": 1,
        "disabled": True,
        "callsAfterSecondClick": 1,
    }
    expected_collection = {"scope": "studio", "sub_scope": "tags"}
    assert result["copied"] == [
        {
            "selection": {
                **expected_collection,
                "doc_ids": ["imported-first", "package-imported"],
            },
            "hasRestoreFocus": True,
        }
    ]
    assert result["refreshTypes"] == {
        "collection": "function",
        "document": "function",
    }
    expected_imported = {
        "detailText": "Imported first",
        "state": {
            "state": "detail",
            "reason": "detail-loaded",
            "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
            "collectionTarget": expected_collection,
            "collectionLabel": "studio / Tags",
            "subdocTarget": {
                **expected_collection,
                "doc_id": "imported-first",
            },
        },
        "subdoc": "imported-first",
    }
    if result["imported"] != expected_imported:
        raise AssertionError(
            f"unexpected imported document refresh: {result['imported']!r}"
        )
    expected_package_imported = {
        "historyLength": result["packageHistoryLength"],
        "reportState": "list",
        "rowIds": ["imported-first", "package-imported"],
        "rowTitles": ["Imported first refreshed", "Package imported"],
        "selectionState": "inactive",
        "subdoc": None,
    }
    if result["packageImported"] != expected_package_imported:
        raise AssertionError(
            f"unexpected imported package refresh: {result['packageImported']!r}"
        )
    expected_call = {
        "collection": expected_collection,
        "refreshAndSelectType": "function",
    }
    assert result["first"] == {
        "calls": [expected_call],
        "detailText": "Created first",
        "state": {
            "state": "detail",
            "reason": "detail-loaded",
            "parentTarget": {"scope": "studio", "doc_id": "parent-doc"},
            "collectionTarget": expected_collection,
            "collectionLabel": "studio / Tags",
            "subdocTarget": {
                **expected_collection,
                "doc_id": "created-first",
            },
        },
        "subdoc": "created-first",
    }
    assert result["second"] == {
        "calls": [expected_call, expected_call],
        "detailText": "Created second",
        "refreshEvents": 3,
        "subdoc": "created-second",
    }
    assert result["statuses"] == []
    assert result["fetches"] == [
        {"path": "/synthetic/manifest.json", "cache": "default"},
        {"path": "/synthetic/manifest.json", "cache": "no-store"},
        {"path": "/synthetic/by-id/imported-first.json", "cache": "no-store"},
        {"path": "/synthetic/manifest.json", "cache": "no-store"},
        {"path": "/synthetic/manifest.json", "cache": "no-store"},
        {"path": "/synthetic/by-id/created-first.json", "cache": "no-store"},
        {"path": "/synthetic/manifest.json", "cache": "no-store"},
        {"path": "/synthetic/by-id/created-second.json", "cache": "no-store"},
    ]


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
          window.syntheticManifestDocs = [
            { doc_id: 'detail-doc', title: 'Detail' },
            { doc_id: 'sibling-doc', title: 'Sibling' }
          ];
          window.fetch = async input => {
            const url = new URL(String(input), window.location.href);
            if (url.pathname.endsWith('/manifest.json')) {
              return {
                ok: true,
                status: 200,
                json: async () => ({ docs: window.syntheticManifestDocs })
              };
            }
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
          const events = [];
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: root,
            routeContext: { subScopes: [subScope] },
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
            reportState: root.dataset.reportState,
            rowIds: Array.from(root.querySelectorAll('[data-report-subdoc-id]'))
              .map(row => row.dataset.reportSubdocId),
            subdoc: new URLSearchParams(location.search).get('subdoc')
          };
          let duplicateCommitError = '';
          try {
            await commitDeletedDocument(target);
          } catch (error) {
            duplicateCommitError = error.message;
          }

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
          window.syntheticManifestDocs = [
            { doc_id: 'detail-doc', title: 'Detail' }
          ];
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            reportMeta: { subScope: 'tags' },
            reportRoot: unmountRoot,
            routeContext: { subScopes: [subScope] },
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
            duplicateCommitError,
            unmounted
          };
        }"""
    )

    assert result["local"] == {"reconciled": True, "mode": "local"}
    expected_local_state = {
        "historyLength": result["historyLength"],
        "reportState": "list",
        "rowIds": ["sibling-doc"],
        "subdoc": None,
    }
    if result["localState"] != expected_local_state:
        raise AssertionError(
            f"unexpected local delete reconciliation: {result['localState']!r}"
        )
    assert result["duplicateCommitError"] == (
        "Document was deleted, but the report manifest did not contain one exact target."
    )
    assert {
        "type": "refresh",
        "state": "",
        "reason": "document-deleted-local",
        "documentIds": ["sibling-doc"],
    } in result["events"]
    assert result["unmounted"] == {
        "reconciled": False,
        "mode": "unmounted",
    }


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


def assert_default_report_and_customisation_framework(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const report = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-report.js'
          );
          const defaults = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-default-contribution.js'
          );
          const composition = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-composition.js'
          );
          const manageRegistry = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-customisation-registry.js'
          );
          const publicRegistry = await import(
            '/site/docs-viewer/runtime/js/shared/docs-subscope-customisation-registry.js'
          );
          history.replaceState({}, '', '/?scope=studio&doc=parent-doc');
          document.body.innerHTML = '<main id="candidate-host"></main>';
          const host = document.querySelector('#candidate-host');
          const copied = [];
          Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: {
              writeText: text => {
                copied.push(text);
                return Promise.resolve();
              }
            }
          });
          document.execCommand = command => {
            if (command !== 'copy') return false;
            copied.push(document.querySelector('textarea')?.value || '');
            return true;
          };
          window.fetch = async input => {
            const url = new URL(String(input), location.href);
            const response = payload => ({
              ok: true,
              status: 200,
              json: async () => payload
            });
            if (url.pathname === '/candidate/default-manifest.json') {
              return response({ docs: [
                {
                  doc_id: 'alpha', title: 'Alpha', ui_status: 'done',
                  publishable: true, last_updated: '2026-07-30 09:00:00'
                },
                {
                  doc_id: 'alpha-2', title: 'Alpha', ui_status: 'draft',
                  publishable: false, last_updated: '2026-07-30 09:00:00'
                },
                {
                  doc_id: 'beta', title: 'Beta', publishable: true,
                  last_updated: 'not-a-date'
                },
                {
                  doc_id: 'zeta', title: 'Zeta', publishable: true,
                  last_updated: '2026-07-31 09:00:00'
                }
              ] });
            }
            if (url.pathname === '/candidate/empty-manifest.json') {
              return response({ docs: [] });
            }
            if (url.pathname === '/candidate/custom-manifest.json') {
              return response({
                customisation: {
                  id: 'synthetic',
                  data: { categories: ['x', 'y'] }
                },
                docs: [
                  {
                    doc_id: 'x-one', title: 'X One', publishable: true,
                    last_updated: '', customisation: { category: 'x' }
                  },
                  {
                    doc_id: 'y-one', title: 'Y One', publishable: true,
                    last_updated: '', customisation: { category: 'y' }
                  }
                ]
              });
            }
            if (url.pathname === '/candidate/mismatch-manifest.json') {
              return response({ docs: [] });
            }
            if (url.pathname.includes('/candidate/by-id/')) {
              const docId = decodeURIComponent(
                url.pathname.split('/').pop().replace(/\\.json$/, '')
              );
              return response({
                doc_id: docId,
                title: docId,
                content_html: `<h2>${docId}</h2>`
              });
            }
            return { ok: false, status: 404, json: async () => ({}) };
          };

          const lifecycle = [];
          const created = [];
          const prepared = [];
          const publishableTargets = [];
          const publishableContexts = [];
          const copyTargets = [];
          const copyStatuses = [];
          const defaultContribution = defaults.createDocsViewerManagementSubscopeDefaultContribution({
            managementContext: true,
            markdownLinkForDocument: (target, doc) => {
              copyTargets.push(target);
              return `[${doc.title}](/docs/?scope=${target.scope}&doc=parent-doc&subdoc=${target.doc_id})`;
            },
            onCreateDocument: target => created.push(target),
            onLifecycleEvent: event => lifecycle.push(event.type),
            onPreparePackage: target => prepared.push(target),
            onSetPublishable: (target, context) => {
              publishableTargets.push(target);
              publishableContexts.push({
                hasRefreshCollection: typeof context.refreshCollection === 'function',
                hasRestoreFocus: Boolean(context.restoreFocus)
              });
              return Promise.resolve();
            },
            setStatus: (message, isError) => copyStatuses.push({ message, isError }),
            uiStatusByValue: new Map([
              ['done', { label: 'Done', emoji: '✅' }],
              ['draft', { label: 'Draft', emoji: '📝' }]
            ])
          });
          const composedDefault = composition.composeDocsViewerManagementSubscopeContributions({
            defaultContribution
          });
          const root = document.createElement('section');
          host.appendChild(root);
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'parent-doc' },
            managementContext: true,
            reportMeta: { subScope: 'default' },
            reportRoot: root,
            routeContext: { subScopes: [{
              subScope: 'default',
              title: 'Default',
              manifestUrl: '/candidate/default-manifest.json',
              byIdUrlBase: '/candidate/by-id'
            }] },
            subscopeReportContributionPromise: Promise.resolve(composedDefault),
            viewerScope: 'studio'
          });
          const rowIds = node => Array.from(
            node.querySelectorAll('[data-report-subdoc-id]')
          ).map(row => row.dataset.reportSubdocId);
          const checkedIds = node => Array.from(
            node.querySelectorAll('[data-docs-subscope-selection-checkbox]:checked')
          ).map(input => input.dataset.docsSubscopeSelectionCheckbox);
          const initial = {
            rows: rowIds(root),
            sortMode: root.querySelector('[data-docs-subscope-sort]')
              ?.dataset.docsSubscopeSort || '',
            newPresent: root.querySelector('[data-docs-subscope-new]') !== null,
            customFilters: root.querySelectorAll('[data-docs-subscope-custom-filter]').length,
            statusIcons: root.querySelectorAll('.docsViewer__navStatus').length,
            nonPublishableIcons: root.querySelectorAll('.docsViewer__publishableExclusion').length,
            setPublishablePresent: root.querySelector(
              '[data-docs-viewer-action="set-publishable"]'
            ) !== null
          };
          root.querySelector('[data-docs-subscope-new]').click();
          await Promise.resolve();
          root.querySelector('[data-docs-subscope-actions]').click();
          root.querySelector('[data-docs-subscope-selection-checkbox="zeta"]').click();
          const selectedBeforeSort = checkedIds(root);
          root.querySelector('[data-docs-subscope-sort]').click();
          const afterSort = {
            rows: rowIds(root),
            checked: checkedIds(root),
            sortMode: root.querySelector('[data-docs-subscope-sort]')
              ?.dataset.docsSubscopeSort || ''
          };
          root.querySelector('[data-docs-subscope-selection-command="select-all"]').click();
          root.querySelector('[data-docs-subscope-actions]').click();
          root.querySelector('[data-docs-viewer-action="prepare-document-package"]').click();
          await Promise.resolve();
          await Promise.resolve();
          root.querySelector('[data-docs-subscope-actions]').click();
          root.querySelector('[data-docs-viewer-action="set-publishable"]').click();
          await Promise.resolve();
          await Promise.resolve();
          root.querySelector(
            '[data-report-subdoc-id="alpha"] .docsViewerReport__subscopeButton'
          ).click();
          await new Promise(resolve => {
            const poll = () => root.querySelector('[data-docs-subscope-copy-link]')
              ? resolve()
              : setTimeout(poll, 0);
            poll();
          });
          root.querySelector('[data-docs-subscope-copy-link]').click();
          await Promise.resolve();
          await Promise.resolve();
          const detail = {
            copied: copied.slice(),
            copyTargets: copyTargets.slice(),
            statuses: copyStatuses.slice(),
            target: root.querySelector('[data-docs-subscope-copy-link]') !== null
          };
          root.remove();
          await new Promise(resolve => setTimeout(resolve, 0));
          history.replaceState({}, '', '/?scope=studio&doc=empty-parent');

          const emptyCreated = [];
          const emptyDefault = defaults.createDocsViewerManagementSubscopeDefaultContribution({
            managementContext: true,
            onCreateDocument: target => emptyCreated.push(target)
          });
          const emptyRoot = document.createElement('section');
          host.appendChild(emptyRoot);
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'empty-parent' },
            managementContext: true,
            reportMeta: { subScope: 'empty' },
            reportRoot: emptyRoot,
            routeContext: { subScopes: [{
              subScope: 'empty',
              title: 'Empty',
              manifestUrl: '/candidate/empty-manifest.json',
              byIdUrlBase: '/candidate/by-id'
            }] },
            subscopeReportContribution: composition.composeDocsViewerManagementSubscopeContributions({
              defaultContribution: emptyDefault
            }),
            viewerScope: 'studio'
          });
          const emptySnapshot = {
            actionsDisabled: emptyRoot.querySelector('[data-docs-subscope-actions]')?.disabled ?? null,
            newDisabled: emptyRoot.querySelector('[data-docs-subscope-new]')?.disabled ?? null,
            setPublishablePresent: emptyRoot.querySelector(
              '[data-docs-viewer-action="set-publishable"]'
            ) !== null,
            text: emptyRoot.querySelector('.docsViewerReport__empty')?.textContent || ''
          };
          emptyRoot.querySelector('[data-docs-subscope-new]')?.click();
          await Promise.resolve();
          history.replaceState({}, '', '/?scope=studio&doc=custom-parent');

          const customTargets = { list: [], selection: [], detail: [] };
          const customContribution = {
            id: 'synthetic',
            createFilters: ({ data }) => [{
              id: 'category',
              initialValue: 'x',
              matches: ({ document, value }) => (
                !value || document.customisation?.category === value
              ),
              render: ({ host: filterHost, value, setValue }) => {
                data.categories.forEach(category => {
                  const button = filterHost.ownerDocument.createElement('button');
                  button.type = 'button';
                  button.dataset.syntheticFilter = category;
                  button.setAttribute('aria-pressed', category === value ? 'true' : 'false');
                  button.textContent = category;
                  button.addEventListener('click', () => setValue(category));
                  filterHost.appendChild(button);
                });
              }
            }],
            renderRow: ({ document: doc, trailingHost }) => {
              const marker = trailingHost.ownerDocument.createElement('span');
              marker.dataset.syntheticRow = doc.doc_id;
              marker.textContent = doc.customisation.category;
              trailingHost.appendChild(marker);
            },
            renderListToolbar: ({ host: toolbarHost, registerAction }) => {
              const action = registerAction({
                id: 'synthetic-list', placement: 'list-toolbar',
                targetKind: 'collection', capability: true,
                emptyState: 'enabled', refreshEffect: 'none',
                handler: target => customTargets.list.push(target)
              });
              const button = toolbarHost.ownerDocument.createElement('button');
              button.type = 'button';
              button.dataset.syntheticListAction = 'true';
              button.addEventListener('click', () => action.invoke());
              toolbarHost.appendChild(button);
            },
            renderSelectionToolbar: ({ host: selectionHost, registerAction }) => {
              const action = registerAction({
                id: 'synthetic-selection', placement: 'selection',
                targetKind: 'selection', capability: true,
                emptyState: 'disabled', refreshEffect: 'none',
                handler: target => customTargets.selection.push(target)
              });
              const button = selectionHost.ownerDocument.createElement('button');
              button.type = 'button';
              button.dataset.syntheticSelectionAction = 'true';
              button.disabled = !action.enabled;
              button.addEventListener('click', () => action.invoke());
              selectionHost.appendChild(button);
            },
            renderDetailToolbar: ({ host: detailHost, registerAction }) => {
              const action = registerAction({
                id: 'synthetic-detail', placement: 'detail-toolbar',
                targetKind: 'validated-detail', capability: true,
                emptyState: 'omitted', refreshEffect: 'none',
                handler: target => customTargets.detail.push(target)
              });
              const button = detailHost.ownerDocument.createElement('button');
              button.type = 'button';
              button.dataset.syntheticDetailAction = 'true';
              button.addEventListener('click', () => action.invoke());
              detailHost.appendChild(button);
            }
          };
          const customDefault = defaults.createDocsViewerManagementSubscopeDefaultContribution({
            managementContext: true
          });
          const customRoot = document.createElement('section');
          host.appendChild(customRoot);
          await report.mountDocsSubscopeReport({
            doc: { doc_id: 'custom-parent' },
            managementContext: true,
            reportMeta: { subScope: 'custom' },
            reportRoot: customRoot,
            routeContext: { subScopes: [{
              subScope: 'custom',
              title: 'Custom',
              manifestUrl: '/candidate/custom-manifest.json',
              byIdUrlBase: '/candidate/by-id',
              subScopeCustomisation: { id: 'synthetic' }
            }] },
            subscopeReportContribution: composition.composeDocsViewerManagementSubscopeContributions({
              customisationContribution: customContribution,
              defaultContribution: customDefault
            }),
            viewerScope: 'studio'
          });
          const customInitial = {
            rows: rowIds(customRoot),
            rowFeatures: customRoot.querySelectorAll('[data-synthetic-row]').length,
            listAction: customRoot.querySelector('[data-synthetic-list-action]') !== null,
            selectionActionDisabled: customRoot.querySelector(
              '[data-synthetic-selection-action]'
            )?.disabled ?? null
          };
          customRoot.querySelector('[data-synthetic-list-action]')?.click();
          customRoot.querySelector('[data-docs-subscope-actions]')?.click();
          customRoot.querySelector(
            '[data-docs-subscope-selection-checkbox="x-one"]'
          )?.click();
          customRoot.querySelector('[data-synthetic-selection-action]')?.click();
          customRoot.querySelector('[data-synthetic-filter="y"]')?.click();
          const customFiltered = rowIds(customRoot);
          const customDetailButton = customRoot.querySelector(
            '[data-report-subdoc-id="y-one"] .docsViewerReport__subscopeButton'
          );
          if (customDetailButton) {
            customDetailButton.click();
            await new Promise(resolve => {
              const poll = () => customRoot.querySelector('[data-synthetic-detail-action]')
                ? resolve()
                : setTimeout(poll, 0);
              poll();
            });
            customRoot.querySelector('[data-synthetic-detail-action]').click();
          }
          await Promise.resolve();
          history.replaceState({}, '', '/?scope=studio&doc=failed-parent');

          let unknownRegistry = '';
          try {
            await manageRegistry.resolveManagementDocsSubscopeCustomisation({ id: 'unknown' });
          } catch (error) {
            unknownRegistry = error.message;
          }
          let unavailableContract = null;
          const unavailableContribution = composition.composeDocsViewerManagementSubscopeContributions({
            customisationContribution: {
              id: 'unavailable-test',
              renderListToolbar: ({ registerAction }) => {
                const registration = registerAction({
                  id: 'unavailable-list', placement: 'list-toolbar',
                  targetKind: 'collection',
                  capability: { available: false, reason: 'Unavailable in this scope.' },
                  emptyState: 'disabled', refreshEffect: 'none',
                  handler: () => {}
                });
                unavailableContract = {
                  disabledReason: registration.disabledReason,
                  enabled: registration.enabled,
                  hidden: registration.hidden,
                  target: registration.target
                };
              }
            }
          });
          unavailableContribution.renderListToolbar({
            collection: { scope: 'studio', sub_scope: 'custom' },
            documents: [],
            host: document.createElement('div')
          });
          let invalidTarget = '';
          const invalidContribution = composition.composeDocsViewerManagementSubscopeContributions({
            customisationContribution: {
              id: 'invalid-test',
              renderDetailToolbar: ({ registerAction }) => registerAction({
                id: 'invalid-detail', placement: 'detail-toolbar',
                targetKind: 'validated-detail', capability: true,
                emptyState: 'omitted', refreshEffect: 'none',
                handler: () => {}
              })
            }
          });
          try {
            invalidContribution.renderDetailToolbar({
              collection: { scope: 'studio', sub_scope: 'custom' },
              host: document.createElement('div'),
              target: {
                scope: 'studio', sub_scope: 'custom', doc_id: 'x-one', extra: true
              }
            });
          } catch (error) {
            invalidTarget = error.message;
          }
          const failedRoot = document.createElement('section');
          host.appendChild(failedRoot);
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'default' },
            reportRoot: failedRoot,
            routeContext: { subScopes: [{
              subScope: 'default', title: 'Default',
              manifestUrl: '/candidate/default-manifest.json',
              byIdUrlBase: '/candidate/by-id'
            }] },
            subscopeReportContributionPromise: Promise.reject(new Error('module failed')),
            viewerScope: 'studio'
          });
          const mismatchRoot = document.createElement('section');
          host.appendChild(mismatchRoot);
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'mismatch' },
            reportRoot: mismatchRoot,
            routeContext: { subScopes: [{
              subScope: 'mismatch', title: 'Mismatch',
              manifestUrl: '/candidate/mismatch-manifest.json',
              byIdUrlBase: '/candidate/by-id',
              subScopeCustomisation: { id: 'analysis_tags' }
            }] },
            subscopeReportContribution: {},
            viewerScope: 'studio'
          });
          history.replaceState({}, '', '/?scope=studio&doc=callback-parent');
          const callbackRoot = document.createElement('section');
          host.appendChild(callbackRoot);
          const callbackDefault = defaults.createDocsViewerManagementSubscopeDefaultContribution({
            managementContext: true
          });
          await report.mountDocsSubscopeReport({
            reportMeta: { subScope: 'callback' },
            reportRoot: callbackRoot,
            routeContext: { subScopes: [{
              subScope: 'callback', title: 'Callback',
              manifestUrl: '/candidate/custom-manifest.json',
              byIdUrlBase: '/candidate/by-id',
              subScopeCustomisation: { id: 'synthetic' }
            }] },
            subscopeReportContribution: composition.composeDocsViewerManagementSubscopeContributions({
              defaultContribution: callbackDefault,
              customisationContribution: {
                id: 'callback-failure',
                notify: event => {
                  if (event.type === 'selection') throw new Error('selection callback failed');
                }
              }
            }),
            viewerScope: 'studio',
            managementContext: true
          });
          const callbackFailure = {
            state: callbackRoot.dataset.reportState,
            text: callbackRoot.textContent
          };
          return {
            afterSort,
            callbackFailure,
            created,
            customFiltered,
            customInitial,
            customTargets,
            detail,
            emptyCreated,
            emptySnapshot,
            failed: {
              state: failedRoot.dataset.reportState,
              text: failedRoot.textContent
            },
            initial,
            invalidTarget,
            lifecycle,
            mismatch: {
              state: mismatchRoot.dataset.reportState,
              text: mismatchRoot.textContent
            },
            prepared,
            publishableContexts,
            publishableTargets,
            registries: {
              manage: manageRegistry.listManagementDocsSubscopeCustomisationIds(),
              public: publicRegistry.listPublicDocsSubscopeCustomisationIds(),
              unknownRegistry
            },
            selectedBeforeSort,
            unavailableContract
          };
        }"""
    )
    assert result["initial"] == {
        "rows": ["alpha", "alpha-2", "beta", "zeta"],
        "sortMode": "title-asc",
        "newPresent": True,
        "customFilters": 0,
        "statusIcons": 2,
        "nonPublishableIcons": 1,
        "setPublishablePresent": True,
    }
    assert result["selectedBeforeSort"] == ["zeta"]
    assert result["created"] == [
        {"scope": "studio", "sub_scope": "default"}
    ]
    assert result["afterSort"] == {
        "rows": ["zeta", "alpha", "alpha-2", "beta"],
        "checked": ["zeta"],
        "sortMode": "last-updated-desc",
    }
    assert result["prepared"][0]["scope"] == "studio"
    assert result["prepared"][0]["sub_scope"] == "default"
    assert sorted(result["prepared"][0]["doc_ids"]) == [
        "alpha", "alpha-2", "beta", "zeta"
    ]
    assert result["publishableTargets"] == [{
        "scope": "studio",
        "sub_scope": "default",
        "doc_ids": ["zeta", "alpha", "alpha-2", "beta"],
    }], result
    assert result["publishableContexts"] == [{
        "hasRefreshCollection": True,
        "hasRestoreFocus": True,
    }], result
    assert result["detail"] == {
        "copied": [
            "[Alpha](/docs/?scope=studio&doc=parent-doc&subdoc=alpha)"
        ],
        "copyTargets": [
            {"scope": "studio", "sub_scope": "default", "doc_id": "alpha"}
        ],
        "statuses": [],
        "target": True,
    }, result
    assert "unmount" in result["lifecycle"]
    assert result["emptySnapshot"] == {
        "actionsDisabled": True,
        "newDisabled": False,
        "setPublishablePresent": False,
        "text": "No documents are available in Empty.",
    }, result
    assert result["emptyCreated"] == [
        {"scope": "studio", "sub_scope": "empty"}
    ]
    assert result["customInitial"] == {
        "rows": ["x-one"],
        "rowFeatures": 1,
        "listAction": True,
        "selectionActionDisabled": True,
    }
    assert result["customFiltered"] == ["y-one"]
    assert result["customTargets"] == {
        "list": [{"scope": "studio", "sub_scope": "custom"}],
        "selection": [
            {"scope": "studio", "sub_scope": "custom", "doc_ids": ["x-one"]}
        ],
        "detail": [
            {"scope": "studio", "sub_scope": "custom", "doc_id": "y-one"}
        ],
    }
    assert result["registries"] == {
        "manage": ["analysis_tags", "dotlineform_projects"],
        "public": [],
        "unknownRegistry": "Manage Docs sub-scope customisation is unavailable: unknown",
    }
    assert result["unavailableContract"] == {
        "disabledReason": "Unavailable in this scope.",
        "enabled": False,
        "hidden": False,
        "target": {"scope": "studio", "sub_scope": "custom"},
    }
    assert result["invalidTarget"] == "Sub-scope action detail target is invalid."
    assert result["failed"] == {"state": "error", "text": "module failed"}
    assert result["callbackFailure"] == {
        "state": "error",
        "text": "selection callback failed",
    }
    assert result["mismatch"] == {
        "state": "error",
        "text": (
            "Docs sub-scope customisation identity did not match its manifest projection."
        ),
    }


def assert_dotlineform_projects_customisation(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const module = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-dotlineform-projects.js'
          );
          const registry = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-customisation-registry.js'
          );
          const documents = [
            {
              doc_id: 'architecture',
              authoring_subject: {
                state: 'valid', kind: 'folder', key: 'projects/16 forms', fields: ['folder_path']
              },
              customisation: { folder_path: 'projects/16 forms' }
            },
            {
              doc_id: 'architecture-notes',
              authoring_subject: {
                state: 'valid', kind: 'folder', key: 'projects/16 forms', fields: ['folder_path']
              },
              customisation: { folder_path: 'projects/16 forms' }
            },
            {
              doc_id: 'pathless',
              authoring_subject: { state: 'none', kind: 'none', key: '', fields: [] }
            }
          ];
          const opened = [];
          const statuses = [];
          const assignments = [];
          const refreshed = [];
          let rejectAssignment = false;
          const contribution = module.createDocsViewerManagementSubscopeDotlineformProjects({
            descriptor: {
              id: 'dotlineform_projects',
              capabilities: {
                assignableFieldGroups: ['authoring_subject']
              }
            },
            collection: { scope: 'dotlineform', sub_scope: 'projects' },
            root: document.body,
            readMetadata: async target => ({
              ...target,
              record: {
                doc_id: target.doc_id,
                authoring_subject: {
                  state: 'valid', kind: 'folder', key: 'projects/16 forms', fields: ['folder_path']
                },
                customisation: {
                  folder_path: 'projects/16 forms', work_id: '', series_id: ''
                }
              },
              source_revision: 'sha256:' + 'a'.repeat(64)
            }),
            assignFieldGroup: async (target, payload) => {
              if (rejectAssignment) throw new Error('Folder is outside the configured base.');
              assignments.push({ target, payload });
              return {
                ok: true,
                operation: 'assign_field_group',
                target,
                scope: target.scope,
                sub_scope: target.sub_scope,
                doc_id: target.doc_id,
                field_group: 'authoring_subject',
                fields: payload.fields,
                source_revision: 'sha256:' + 'b'.repeat(64),
                summary_text: 'Subject updated.'
              };
            },
            openLocalTarget: async target => {
              opened.push(target);
              return { summary_text: 'Local target opened.' };
            },
            setStatus: (message, isError) => statuses.push({ message, isError })
          });

          function renderRow(documentRecord) {
            const titlePrefixHost = document.createElement('span');
            const trailingHost = document.createElement('span');
            contribution.renderRow({
              document: documentRecord,
              documents,
              titlePrefixHost,
              trailingHost
            });
            return trailingHost;
          }
          const linkedRow = renderRow(documents[0]);
          const pathlessRow = renderRow(documents[2]);
          const linkedInfo = contribution.projectDetailInfo({
            collection: { scope: 'dotlineform', sub_scope: 'projects' },
            document: documents[0],
            target: {
              scope: 'dotlineform',
              sub_scope: 'projects',
              doc_id: 'architecture'
            }
          });
          const pathlessInfo = contribution.projectDetailInfo({
            collection: { scope: 'dotlineform', sub_scope: 'projects' },
            document: documents[2],
            target: {
              scope: 'dotlineform',
              sub_scope: 'projects',
              doc_id: 'pathless'
            }
          });

          function detailToolbar(documentRecord) {
            const host = document.createElement('div');
            document.body.appendChild(host);
            contribution.renderDetailToolbar({
              document: documentRecord,
              host,
              registerAction: definition => {
                const enabled = definition.capability === true
                  || definition.capability?.available === true;
                return {
                  enabled,
                  disabledReason: enabled ? '' : definition.capability.reason,
                  hidden: false,
                  invoke: () => Promise.resolve(definition.handler(
                    {
                      scope: 'dotlineform',
                      sub_scope: 'projects',
                      doc_id: documentRecord.doc_id
                    },
                    {
                      refreshDocument: async target => {
                        refreshed.push(target);
                        return target;
                      }
                    }
                  ))
                };
              },
              target: {
                scope: 'dotlineform',
                sub_scope: 'projects',
                doc_id: documentRecord.doc_id
              }
            });
            return host;
          }
          const linkedToolbar = detailToolbar(documents[0]);
          const linkedButton = linkedToolbar.querySelector('[data-docs-projects-open-folder]');
          const assignButton = linkedToolbar.querySelector('[data-docs-projects-assign-subject]');
          linkedButton.click();
          await new Promise(resolve => setTimeout(resolve, 0));
          const pathlessToolbar = detailToolbar(documents[2]);
          const pathlessButton = pathlessToolbar.querySelector('[data-docs-projects-open-folder]');

          assignButton.click();
          await new Promise(resolve => setTimeout(resolve, 0));
          let modalHost = document.querySelector('[data-docs-viewer-management-modal-host="true"]');
          const initialModal = {
            checked: modalHost.querySelector('input[name="docs-project-subject"]:checked').value,
            folderHidden: modalHost.querySelector('[data-project-subject-folder]').hidden,
            folderValue: modalHost.querySelector('[data-project-subject-folder-input]').value,
            title: modalHost.querySelector('.docsViewer__modalTitle').textContent
          };
          modalHost.querySelector('button[data-role="modal-cancel"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          const cancelled = {
            assignments: assignments.length,
            refreshed: refreshed.length
          };

          assignButton.click();
          await new Promise(resolve => setTimeout(resolve, 0));
          modalHost = document.querySelector('[data-docs-viewer-management-modal-host="true"]');
          const folderRadio = modalHost.querySelector('input[value="folder"]');
          folderRadio.checked = true;
          folderRadio.dispatchEvent(new Event('change', { bubbles: true }));
          modalHost.querySelector('[data-project-subject-folder-input]').value =
            '/configured/base/projects/future';
          modalHost.querySelector('button[data-role="modal-primary"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => setTimeout(resolve, 0));

          rejectAssignment = true;
          assignButton.click();
          await new Promise(resolve => setTimeout(resolve, 0));
          modalHost = document.querySelector('[data-docs-viewer-management-modal-host="true"]');
          const noneRadio = modalHost.querySelector('input[value="none"]');
          noneRadio.checked = true;
          noneRadio.dispatchEvent(new Event('change', { bubbles: true }));
          modalHost.querySelector('button[data-role="modal-primary"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => setTimeout(resolve, 0));
          const containedError = {
            folderDisabled: modalHost.querySelector(
              '[data-project-subject-folder-input]'
            ).disabled,
            modalOpen: Boolean(modalHost.querySelector('[data-role="docs-viewer-management-modal"]')),
            status: modalHost.querySelector('[data-role="modal-status"]').textContent,
            submitDisabled: modalHost.querySelector('button[data-role="modal-primary"]').disabled
          };
          modalHost.querySelector('button[data-role="modal-cancel"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));

          const configuredCollection = module.createDocsViewerManagementSubscopeDotlineformProjects({
            descriptor: { id: 'dotlineform_projects' },
            collection: { scope: 'studio', sub_scope: 'project-notes' }
          });
          const configuredHost = document.createElement('div');
          const configuredActionIds = [];
          configuredCollection.renderDetailToolbar({
            document: {
              doc_id: 'configured',
              authoring_subject: { state: 'none', kind: 'none', key: '', fields: [] }
            },
            host: configuredHost,
            registerAction: definition => {
              configuredActionIds.push(definition.id);
              return {
                disabledReason: 'Unavailable.',
                enabled: false,
                hidden: false,
                invoke: () => Promise.reject(new Error('Unavailable.'))
              };
            },
            target: { scope: 'studio', sub_scope: 'project-notes', doc_id: 'configured' }
          });
          const analysisContribution = await registry.resolveManagementDocsSubscopeCustomisation({
            id: 'analysis_tags'
          }, {
            collection: { scope: 'analysis', sub_scope: 'tags' }
          });
          let collectionTargetError = '';
          try {
            module.createDocsViewerManagementSubscopeDotlineformProjects({
              descriptor: { id: 'dotlineform_projects' },
              collection: { scope: '', sub_scope: 'project-notes' }
            });
          } catch (error) {
            collectionTargetError = error.message;
          }
          let rowError = '';
          try {
            contribution.projectDetailInfo({
              collection: { scope: 'dotlineform', sub_scope: 'projects' },
              document: {
                doc_id: 'invalid-subject',
                authoring_subject: {
                  state: 'valid', kind: 'folder', key: 'projects/a', fields: ['extra']
                }
              },
              target: {
                scope: 'dotlineform', sub_scope: 'projects', doc_id: 'invalid-subject'
              }
            });
          } catch (error) {
            rowError = error.message;
          }

          return {
            assignments,
            analysisSubjectAction: typeof analysisContribution.renderDetailToolbar,
            assignButton: {
              disabled: assignButton.disabled,
              text: assignButton.textContent
            },
            cancelled,
            collectionTargetError,
            configuredCollectionId: configuredCollection.id,
            configuredActionIds,
            configuredSubjectAction: Boolean(
              configuredHost.querySelector('[data-docs-projects-assign-subject]')
            ),
            containedError,
            genericMetadataEditor: typeof contribution.mountMetadataEditor,
            initialModal,
            linkedButton: {
              disabled: linkedButton.disabled,
              text: linkedButton.textContent
            },
            linkedInfo,
            linkedRow: {
              stage: linkedRow.querySelector('[data-project-publication-stage]').dataset.projectPublicationStage,
              text: linkedRow.querySelector('[data-project-publication-stage]').textContent
            },
            opened,
            pathlessButton: {
              disabled: pathlessButton.disabled,
              title: pathlessButton.title
            },
            pathlessInfo,
            pathlessRow: {
              childCount: pathlessRow.childElementCount,
              text: pathlessRow.textContent
            },
            registryIds: registry.listManagementDocsSubscopeCustomisationIds(),
            refreshed,
            rowError,
            statuses
          };
        }"""
    )

    assert result == {
        "assignments": [
            {
                "target": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                    "doc_id": "architecture",
                },
                "payload": {
                    "source_revision": "sha256:" + "a" * 64,
                    "field_group": "authoring_subject",
                    "fields": {
                        "folder_path": "/configured/base/projects/future",
                        "work_id": "",
                        "series_id": "",
                    },
                    "confirm": True,
                },
            }
        ],
        "analysisSubjectAction": "undefined",
        "assignButton": {"disabled": False, "text": "Subject"},
        "cancelled": {"assignments": 0, "refreshed": 0},
        "collectionTargetError": "Projects customisation collection target is invalid.",
        "configuredCollectionId": "dotlineform_projects",
        "configuredActionIds": ["open-project-folder"],
        "configuredSubjectAction": False,
        "containedError": {
            "folderDisabled": True,
            "modalOpen": True,
            "status": "Folder is outside the configured base.",
            "submitDisabled": False,
        },
        "genericMetadataEditor": "undefined",
        "initialModal": {
            "checked": "folder",
            "folderHidden": False,
            "folderValue": "projects/16 forms",
            "title": "Assign subject",
        },
        "linkedButton": {"disabled": False, "text": "Open in Finder"},
        "linkedInfo": {
            "actions": {"assignSubject": True},
            "fields": [
                {
                    "detail": "projects/16 forms",
                    "id": "authoring_subject",
                    "label": "Subject",
                    "state": "folder",
                    "value": "Folder",
                },
                {
                    "detail": "No editorial copy",
                    "id": "publication",
                    "label": "Publication",
                    "state": "working",
                    "value": "Working",
                }
            ],
        },
        "linkedRow": {
            "stage": "working",
            "text": "Working",
        },
        "opened": ["projects/16%20forms"],
        "pathlessButton": {
            "disabled": True,
            "title": "This document has no valid Folder subject.",
        },
        "pathlessInfo": {
            "actions": {"assignSubject": True},
            "fields": [
                {
                    "detail": "",
                    "id": "authoring_subject",
                    "label": "Subject",
                    "state": "none",
                    "value": "None",
                },
                {
                    "detail": "No editorial copy",
                    "id": "publication",
                    "label": "Publication",
                    "state": "working",
                    "value": "Working",
                }
            ],
        },
        "pathlessRow": {"childCount": 1, "text": "Working"},
        "registryIds": ["analysis_tags", "dotlineform_projects"],
        "refreshed": [
            {
                "scope": "dotlineform",
                "sub_scope": "projects",
                "doc_id": "architecture",
            }
        ],
        "rowError": (
            "Projects document authoring_subject must be a normalized object."
        ),
        "statuses": [
            {"message": "Local target opened.", "isError": False},
        ],
    }


def assert_subscope_customisation_capability_projection(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const config = await import(
            '/site/docs-viewer/runtime/js/shared/docs-viewer-config-controller.js'
          );
          const basic = config.normalizeDocsViewerSubScopeCustomisation({
            id: 'analysis_tags'
          });
          const assignable = config.normalizeDocsViewerSubScopeCustomisation({
            id: 'synthetic_fields',
            capabilities: {
              assignable_field_groups: ['authoring_subject', 'tag_fields']
            }
          });
          let unknownCapabilityError = '';
          let duplicateGroupError = '';
          try {
            config.normalizeDocsViewerSubScopeCustomisation({
              id: 'synthetic_fields',
              capabilities: {
                assignable_field_groups: ['authoring_subject'],
                settings: {}
              }
            });
          } catch (error) {
            unknownCapabilityError = error.message;
          }
          try {
            config.normalizeDocsViewerSubScopeCustomisation({
              id: 'synthetic_fields',
              capabilities: {
                assignable_field_groups: ['authoring_subject', 'authoring_subject']
              }
            });
          } catch (error) {
            duplicateGroupError = error.message;
          }
          return {
            assignable: {
              groups: assignable.capabilities.assignableFieldGroups,
              hasAuthoringSubject: config.hasDocsViewerAssignableFieldGroup(
                assignable,
                'authoring_subject'
              ),
              hasMissing: config.hasDocsViewerAssignableFieldGroup(
                assignable,
                'missing'
              ),
              id: assignable.id,
              keys: Object.keys(assignable).sort()
            },
            basic: {
              id: basic.id,
              keys: Object.keys(basic)
            },
            duplicateGroupError,
            unknownCapabilityError
          };
        }"""
    )

    assert result == {
        "assignable": {
            "groups": ["authoring_subject", "tag_fields"],
            "hasAuthoringSubject": True,
            "hasMissing": False,
            "id": "synthetic_fields",
            "keys": ["capabilities", "id"],
        },
        "basic": {
            "id": "analysis_tags",
            "keys": ["id"],
        },
        "duplicateGroupError": (
            "Docs Viewer sub_scope_customisation assignable_field_groups "
            "contains an invalid or duplicate id."
        ),
        "unknownCapabilityError": (
            "Docs Viewer sub_scope_customisation capabilities must contain "
            "exactly assignable_field_groups."
        ),
    }


def assert_dotlineform_projects_catalogue_subjects(page: Page) -> None:
    result = page.evaluate(
        """async () => {
          const module = await import(
            '/docs-viewer/runtime/js/management/docs-viewer-management-subscope-dotlineform-projects.js'
          );
          const records = {
            work: {
              doc_id: 'work-doc',
              authoring_subject: {
                state: 'valid', kind: 'work', key: '00123', fields: ['work_id']
              },
              customisation: { publication_targets: [{
                editorial: {
                  scope: 'analysis', sub_scope: 'works',
                  doc_id: 'd-20260802-101500-a1b2c3'
                },
                available: true,
                title: 'Editorial draft',
                viewer_url: '/docs/?scope=analysis&doc=works&subdoc=d-20260802-101500-a1b2c3',
                publication: null
              }, {
                editorial: {
                  scope: 'analysis', sub_scope: 'works',
                  doc_id: 'd-20260802-101501-b2c3d4'
                },
                available: true,
                title: 'Published editorial',
                viewer_url: '/docs/?scope=analysis&doc=works&subdoc=d-20260802-101501-b2c3d4',
                publication: { public_url: '/analysis/published' }
              }] }
            },
            series: {
              doc_id: 'series-doc',
              authoring_subject: {
                state: 'valid', kind: 'series', key: '026', fields: ['series_id']
              }
            },
            none: {
              doc_id: 'none-doc',
              authoring_subject: { state: 'none', kind: 'none', key: '', fields: [] },
              customisation: { publication_targets: [{
                editorial: {
                  scope: 'analysis', sub_scope: 'works',
                  doc_id: 'd-20260802-101502-c3d4e5'
                },
                available: false,
                title: '',
                viewer_url: '',
                publication: null
              }] }
            },
            malformed: {
              doc_id: 'malformed-doc',
              authoring_subject: {
                state: 'malformed', kind: 'work', key: '', fields: ['work_id'],
                evidence: { work_id: 123 }
              }
            },
            conflicting: {
              doc_id: 'conflicting-doc',
              authoring_subject: {
                state: 'conflicting', kind: 'conflict', key: '',
                fields: ['folder_path', 'series_id'],
                evidence: { folder_path: 'projects/nerve', series_id: '026' }
              }
            }
          };
          const registryPayload = {
            schema_version: 'docs_semantic_token_registry_v1',
            target_lookup_url: '/target-lookup.json',
            families: [{
              key: 'catalogue', labels: {}, occurrence_fields: [], ui_contributions: {},
              target_types: [
                { key: 'work', label: 'Work', id_policy: {}, lookup_adapter: 'work', lookup_fields: [] },
                { key: 'series', label: 'Series', id_policy: {}, lookup_adapter: 'series', lookup_fields: [] },
                { key: 'moment', label: 'Moment', id_policy: {}, lookup_adapter: 'moment', lookup_fields: [] }
              ]
            }]
          };
          const lookupPayload = {
            targets: [
              { family: 'catalogue', target_type: 'work', target_id: '00123', title: 'Nerve', href: '/works/?work=00123', meta: [] },
              { family: 'catalogue', target_type: 'series', target_id: '026', title: 'Nerve Series', href: '/series/?series=026', meta: [] },
              { family: 'catalogue', target_type: 'moment', target_id: '099', title: 'Nerve Moment', href: '/moments/?moment=099', meta: [] }
            ]
          };
          const fetchCalls = [];
          const fetchImpl = async url => {
            fetchCalls.push(url);
            return {
              ok: true,
              json: async () => url === '/target-lookup.json' ? lookupPayload : registryPayload
            };
          };
          const assignments = [];
          const contribution = module.createDocsViewerManagementSubscopeDotlineformProjects({
            descriptor: {
              id: 'dotlineform_projects',
              capabilities: { assignableFieldGroups: ['authoring_subject'] }
            },
            collection: { scope: 'dotlineform', sub_scope: 'projects' },
            root: document.body,
            fetch: fetchImpl,
            readMetadata: async target => ({
              ...target,
              record: {
                doc_id: target.doc_id,
                authoring_subject: records.work.authoring_subject,
                customisation: { folder_path: '', work_id: '00123', series_id: '' }
              },
              source_revision: 'sha256:' + 'a'.repeat(64)
            }),
            assignFieldGroup: async (target, payload) => {
              assignments.push({ target, payload });
              return {
                target,
                field_group: 'authoring_subject',
                fields: payload.fields,
                source_revision: 'sha256:' + 'b'.repeat(64),
                summary_text: 'Subject updated.'
              };
            }
          });

          function cue(record) {
            const titleHost = document.createElement('span');
            const trailingHost = document.createElement('span');
            const projected = contribution.renderRow({
              document: record,
              titlePrefixHost: titleHost,
              trailingHost
            });
            const nodes = Array.from(
              trailingHost.querySelectorAll('[data-project-publication-stage]')
            );
            return {
              labels: projected.accessibleLabels,
              stages: nodes.map(node => node.dataset.projectPublicationStage),
              text: nodes.map(node => node.textContent).join(''),
              hrefs: nodes.map(node => node.getAttribute('href') || ''),
              subjectIcons: titleHost.querySelectorAll('[data-project-subject-icon]').length
            };
          }
          function info(record) {
            return contribution.projectDetailInfo({
              collection: { scope: 'dotlineform', sub_scope: 'projects' },
              document: record,
              target: {
                scope: 'dotlineform', sub_scope: 'projects', doc_id: record.doc_id
              }
            }).fields[0];
          }
          function publicationInfo(record) {
            return contribution.projectDetailInfo({
              collection: { scope: 'dotlineform', sub_scope: 'projects' },
              document: record,
              target: {
                scope: 'dotlineform', sub_scope: 'projects', doc_id: record.doc_id
              }
            }).fields.slice(1);
          }

          const toolbar = document.createElement('div');
          document.body.appendChild(toolbar);
          contribution.renderDetailToolbar({
            document: records.work,
            host: toolbar,
            registerAction: definition => ({
              enabled: definition.capability === true || definition.capability?.available === true,
              disabledReason: '',
              hidden: false,
              invoke: () => Promise.resolve(definition.handler(
                { scope: 'dotlineform', sub_scope: 'projects', doc_id: 'work-doc' },
                { refreshDocument: async target => target }
              ))
            }),
            target: { scope: 'dotlineform', sub_scope: 'projects', doc_id: 'work-doc' }
          });
          toolbar.querySelector('[data-docs-projects-assign-subject]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => setTimeout(resolve, 0));
          let modalHost = document.querySelector('[data-docs-viewer-management-modal-host="true"]');
          let search = modalHost.querySelector('#docsViewerProjectSubjectCatalogueSearch');
          const initial = {
            checked: modalHost.querySelector('input[name="docs-project-subject"]:checked').value,
            hasIntro: modalHost.textContent.includes('Assign the authoring subject for'),
            hiddenLegend: modalHost.querySelector('[data-project-subject-options] legend').classList.contains('visually-hidden'),
            primaryLabel: modalHost.querySelector('button[data-role="modal-primary"]').textContent,
            searchValue: search.value,
            resultsHidden: modalHost.querySelector('[data-project-subject-results]').hidden,
            expanded: search.getAttribute('aria-expanded'),
            selectedSummaryAbsent: !modalHost.querySelector('[data-project-subject-selected]'),
            types: Array.from(modalHost.querySelectorAll('[data-target-index]')).map(node => (
              node.querySelector('.docsViewerCatalogueTargetPicker__rowKind').textContent
            ))
          };
          const seriesRadio = modalHost.querySelector('input[value="series"]');
          seriesRadio.checked = true;
          seriesRadio.dispatchEvent(new Event('change', { bubbles: true }));
          search.value = 'Nerve';
          search.dispatchEvent(new Event('input', { bubbles: true }));
          const seriesTypes = Array.from(modalHost.querySelectorAll('[data-target-index]')).map(node => (
            node.querySelector('.docsViewerCatalogueTargetPicker__rowKind').textContent
          ));
          modalHost.querySelector('[data-target-index="0"]').click();
          const selectedSeries = {
            searchValue: search.value,
            resultsHidden: modalHost.querySelector('[data-project-subject-results]').hidden,
            expanded: search.getAttribute('aria-expanded'),
            resultCount: modalHost.querySelectorAll('[data-target-index]').length
          };
          search.value = 'Nerve';
          search.dispatchEvent(new Event('input', { bubbles: true }));
          const editedSeries = {
            resultsHidden: modalHost.querySelector('[data-project-subject-results]').hidden,
            expanded: search.getAttribute('aria-expanded'),
            types: Array.from(modalHost.querySelectorAll('[data-target-index]')).map(node => (
              node.querySelector('.docsViewerCatalogueTargetPicker__rowKind').textContent
            ))
          };
          modalHost.querySelector('[data-target-index="0"]').click();
          modalHost.querySelector('button[data-role="modal-primary"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => setTimeout(resolve, 0));
          records.work.authoring_subject = {
            state: 'valid', kind: 'work', key: '00999', fields: ['work_id']
          };
          toolbar.querySelector('[data-docs-projects-assign-subject]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => setTimeout(resolve, 0));
          modalHost = document.querySelector('[data-docs-viewer-management-modal-host="true"]');
          search = modalHost.querySelector('#docsViewerProjectSubjectCatalogueSearch');
          const unavailable = {
            checked: modalHost.querySelector('input[name="docs-project-subject"]:checked').value,
            searchValue: search.value,
            resultsHidden: modalHost.querySelector('[data-project-subject-results]').hidden,
            expanded: search.getAttribute('aria-expanded'),
            status: modalHost.querySelector('[data-project-subject-search-status]').textContent
          };
          modalHost.querySelector('button[data-role="modal-primary"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          unavailable.submitStatus = modalHost.querySelector('[data-role="modal-status"]').textContent;
          modalHost.querySelector('button[data-role="modal-cancel"]').click();
          await new Promise(resolve => setTimeout(resolve, 0));
          records.work.authoring_subject = {
            state: 'valid', kind: 'work', key: '00123', fields: ['work_id']
          };
          toolbar.remove();

          return {
            assignments,
            cues: {
              work: cue(records.work),
              series: cue(records.series),
              none: cue(records.none),
              malformed: cue(records.malformed),
              conflicting: cue(records.conflicting)
            },
            fetchCalls,
            info: {
              work: info(records.work),
              series: info(records.series),
              none: info(records.none),
              malformed: info(records.malformed),
              conflicting: info(records.conflicting)
            },
            publicationInfo: {
              work: publicationInfo(records.work),
              series: publicationInfo(records.series),
              none: publicationInfo(records.none)
            },
            initial,
            selectedSeries,
            editedSeries,
            seriesTypes,
            unavailable
          };
        }"""
    )

    assert result == {
        "assignments": [
            {
                "target": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                    "doc_id": "work-doc",
                },
                "payload": {
                    "source_revision": "sha256:" + "a" * 64,
                    "field_group": "authoring_subject",
                    "fields": {
                        "folder_path": "",
                        "work_id": "",
                        "series_id": "026",
                    },
                    "confirm": True,
                },
            }
        ],
        "cues": {
            "work": {
                "labels": [
                    (
                        "Pre-publish: Editorial draft "
                        "(analysis/works/d-20260802-101500-a1b2c3)"
                    ),
                    (
                        "Published: Published editorial "
                        "(analysis/works/d-20260802-101501-b2c3d4)"
                    ),
                ],
                "stages": ["pre-publish", "published"],
                "text": "🟠🟢",
                "hrefs": [
                    (
                        "/docs/?scope=analysis&doc=works"
                        "&subdoc=d-20260802-101500-a1b2c3"
                    ),
                    (
                        "/docs/?scope=analysis&doc=works"
                        "&subdoc=d-20260802-101501-b2c3d4"
                    ),
                ],
                "subjectIcons": 0,
            },
            "series": {
                "labels": ["Working"],
                "stages": ["working"],
                "text": "Working",
                "hrefs": [""],
                "subjectIcons": 0,
            },
            "none": {
                "labels": [
                    "Unavailable: analysis/works/d-20260802-101502-c3d4e5"
                ],
                "stages": ["unavailable"],
                "text": "⚠️",
                "hrefs": [""],
                "subjectIcons": 0,
            },
            "malformed": {
                "labels": ["Working"],
                "stages": ["working"],
                "text": "Working",
                "hrefs": [""],
                "subjectIcons": 0,
            },
            "conflicting": {
                "labels": ["Working"],
                "stages": ["working"],
                "text": "Working",
                "hrefs": [""],
                "subjectIcons": 0,
            },
        },
        "fetchCalls": [
            "/docs-viewer/config/semantic-tokens/registry.json",
            "/target-lookup.json",
            "/docs-viewer/config/semantic-tokens/registry.json",
            "/target-lookup.json",
        ],
        "info": {
            "work": {
                "detail": "00123", "id": "authoring_subject", "label": "Subject",
                "state": "work", "value": "Work",
            },
            "series": {
                "detail": "026", "id": "authoring_subject", "label": "Subject",
                "state": "series", "value": "Series",
            },
            "none": {
                "detail": "", "id": "authoring_subject", "label": "Subject",
                "state": "none", "value": "None",
            },
            "malformed": {
                "detail": "Malformed work_id declaration: 123", "id": "authoring_subject",
                "label": "Subject", "state": "warning", "value": "Authoring warning",
            },
            "conflicting": {
                "detail": (
                    'Conflicting declarations: folder_path="projects/nerve", '
                    'series_id="026"'
                ),
                "id": "authoring_subject", "label": "Subject", "state": "warning",
                "value": "Authoring warning",
            },
        },
        "publicationInfo": {
            "work": [
                {
                    "detail": "analysis/works/d-20260802-101500-a1b2c3",
                    "id": "publication_1",
                    "label": "Publication",
                    "state": "pre-publish",
                    "value": "🟠 Pre-publish — Editorial draft",
                },
                {
                    "detail": "analysis/works/d-20260802-101501-b2c3d4",
                    "id": "publication_2",
                    "label": "Publication",
                    "state": "published",
                    "value": "🟢 Published — Published editorial",
                },
            ],
            "series": [
                {
                    "detail": "No editorial copy",
                    "id": "publication",
                    "label": "Publication",
                    "state": "working",
                    "value": "Working",
                }
            ],
            "none": [
                {
                    "detail": "analysis/works/d-20260802-101502-c3d4e5",
                    "id": "publication_1",
                    "label": "Publication",
                    "state": "unavailable",
                    "value": "⚠️ Unavailable",
                }
            ],
        },
        "initial": {
            "checked": "work",
            "hasIntro": False,
            "hiddenLegend": True,
            "primaryLabel": "OK",
            "searchValue": "Nerve",
            "resultsHidden": True,
            "expanded": "false",
            "selectedSummaryAbsent": True,
            "types": [],
        },
        "selectedSeries": {
            "searchValue": "Nerve Series",
            "resultsHidden": True,
            "expanded": "false",
            "resultCount": 0,
        },
        "editedSeries": {
            "resultsHidden": False,
            "expanded": "true",
            "types": ["series"],
        },
        "seriesTypes": ["series"],
        "unavailable": {
            "checked": "work",
            "searchValue": "work:00999",
            "resultsHidden": True,
            "expanded": "false",
            "status": (
                "Current Work 00999 is unavailable. Choose a current target or another subject."
            ),
            "submitStatus": "Choose a current Work target.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repository root to serve.")
    args = parser.parse_args(argv)
    site_root = Path(args.site_root).expanduser().resolve()
    assert_filter_source_boundaries(site_root)
    server, base_url = start_static_server(site_root)
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
                assert_filter_projection(page)
                assert_report_module(page)
                assert_subscope_selection_contribution(page)
                assert_subscope_create_contribution_and_report_refresh(page)
                assert_report_delete_reconciliation(page)
                assert_delete_workflow(page)
                assert_manage_report_bridge(page)
                assert_default_report_and_customisation_framework(page)
                assert_subscope_customisation_capability_projection(page)
                assert_dotlineform_projects_customisation(page)
                assert_dotlineform_projects_catalogue_subjects(page)
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
