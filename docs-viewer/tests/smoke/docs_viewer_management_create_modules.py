#!/usr/bin/env python3
"""Smoke-check committed Docs Viewer create presentation contracts."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_RUNTIME_PREFIX = "/docs-viewer/runtime/js/shared/"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def translate_path(self, path: str) -> str:
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path.startswith(SHARED_RUNTIME_PREFIX):
            relative_path = clean_path.removeprefix(SHARED_RUNTIME_PREFIX)
            return str(
                REPO_ROOT
                / "site/docs-viewer/runtime/js/shared"
                / relative_path
            )
        return super().translate_path(path)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_create_presentation_coordinator(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const actions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-actions.js'
            );
            const parentPayload = {
                ok: true,
                scope: 'studio',
                doc_id: 'created-parent',
                target: {
                    scope: 'studio',
                    doc_id: 'created-parent'
                },
                record: {
                    doc_id: 'created-parent',
                    title: 'Created parent'
                }
            };
            const childPayload = {
                ok: true,
                scope: 'studio',
                sub_scope: 'tags',
                doc_id: 'created-child',
                target: {
                    scope: 'studio',
                    sub_scope: 'tags',
                    doc_id: 'created-child'
                },
                record: {
                    doc_id: 'created-child',
                    title: 'Created child'
                }
            };

            async function run(payloadOrError, options = {}) {
                const events = [];
                let createCount = 0;
                try {
                    const value = await actions.runInteractiveDocumentCreate({
                        create: () => {
                            createCount += 1;
                            events.push(['create']);
                            return payloadOrError instanceof Error
                                ? Promise.reject(payloadOrError)
                                : Promise.resolve(payloadOrError);
                        },
                        refreshAndSelect: (target) => {
                            events.push(['refresh', target]);
                            if (options.refreshError) {
                                throw new Error(options.refreshError);
                            }
                            return target;
                        },
                        openSource: (target) => {
                            events.push(['source', target]);
                            if (options.sourceError) {
                                throw new Error(options.sourceError);
                            }
                            return options.sourceResult === undefined
                                ? target
                                : options.sourceResult;
                        }
                    });
                    return {
                        createCount,
                        events,
                        result: value,
                        error: null
                    };
                } catch (error) {
                    return {
                        createCount,
                        events,
                        result: null,
                        error: {
                            message: error.message,
                            committed: error.committed === true,
                            target: error.target || null
                        }
                    };
                }
            }

            const success = await run(parentPayload);

            const committedError = new Error('projection rebuild failed');
            committedError.payload = Object.assign({}, childPayload, {
                ok: false,
                committed: true,
                retry_create: false,
                error: 'projection rebuild failed'
            });
            const committedRecovery = await run(committedError);

            const preCommitError = await run(new Error('source write failed'));
            const refreshFailure = await run(parentPayload, {
                refreshError: 'refresh failed'
            });
            const sourceFailure = await run(parentPayload, {
                sourceError: 'source mount failed'
            });
            const sourceRejected = await run(parentPayload, {
                sourceResult: false
            });
            const mismatchedPayload = Object.assign({}, parentPayload, {
                doc_id: 'different-document'
            });
            const mismatchFailure = await run(mismatchedPayload);

            const sourceSuccessRequests = [];
            const sourceSuccess = await actions.requestCommittedDocumentSource(
                childPayload.target,
                (modeId, options) => {
                    sourceSuccessRequests.push({
                        modeId,
                        target: options.context.sourceTarget
                    });
                    options.onAccepted();
                    return true;
                }
            );
            const sourceFailureRequests = [];
            let requestedSourceFailure = null;
            try {
                await actions.requestCommittedDocumentSource(
                    childPayload.target,
                    (modeId, options) => {
                        sourceFailureRequests.push({
                            modeId,
                            target: options.context
                                ? options.context.sourceTarget
                                : null,
                            force: options.force === true
                        });
                        if (modeId === 'markdown-source') {
                            options.onFailed(new Error('source mount failed'));
                        }
                        return true;
                    }
                );
            } catch (error) {
                requestedSourceFailure = error.message;
            }

            return {
                success,
                committedRecovery,
                preCommitError,
                refreshFailure,
                sourceFailure,
                sourceRejected,
                mismatchFailure,
                requestedSource: {
                    success: sourceSuccess,
                    successRequests: sourceSuccessRequests,
                    failure: requestedSourceFailure,
                    failureRequests: sourceFailureRequests
                },
                messages: {
                    preCommit: actions.interactiveDocumentCreateErrorMessage(
                        new Error('source write failed')
                    ),
                    postCommit: actions.interactiveDocumentCreateErrorMessage(
                        sourceFailure.error
                            ? Object.assign(
                                new Error(sourceFailure.error.message),
                                { committed: true }
                            )
                            : null
                    )
                }
            };
        }"""
    )

    parent_target = {"scope": "studio", "doc_id": "created-parent"}
    child_target = {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": "created-child",
    }
    expected_prefix = "Document created, but could not be opened in Source."

    assert result["success"] == {
        "createCount": 1,
        "events": [
            ["create"],
            ["refresh", parent_target],
            ["source", parent_target],
        ],
        "result": {
            "payload": {
                "ok": True,
                "scope": "studio",
                "doc_id": "created-parent",
                "target": parent_target,
                "record": {
                    "doc_id": "created-parent",
                    "title": "Created parent",
                },
            },
            "target": parent_target,
        },
        "error": None,
    }
    assert result["committedRecovery"]["createCount"] == 1
    assert result["committedRecovery"]["events"] == [
        ["create"],
        ["refresh", child_target],
        ["source", child_target],
    ]
    assert result["committedRecovery"]["result"]["target"] == child_target
    assert result["committedRecovery"]["error"] is None

    assert result["preCommitError"] == {
        "createCount": 1,
        "events": [["create"]],
        "result": None,
        "error": {
            "message": "source write failed",
            "committed": False,
            "target": None,
        },
    }
    assert result["refreshFailure"] == {
        "createCount": 1,
        "events": [["create"], ["refresh", parent_target]],
        "result": None,
        "error": {
            "message": f"{expected_prefix} refresh failed",
            "committed": True,
            "target": parent_target,
        },
    }
    assert result["sourceFailure"] == {
        "createCount": 1,
        "events": [
            ["create"],
            ["refresh", parent_target],
            ["source", parent_target],
        ],
        "result": None,
        "error": {
            "message": f"{expected_prefix} source mount failed",
            "committed": True,
            "target": parent_target,
        },
    }
    assert result["sourceRejected"] == {
        "createCount": 1,
        "events": [
            ["create"],
            ["refresh", parent_target],
            ["source", parent_target],
        ],
        "result": None,
        "error": {
            "message": (
                f"{expected_prefix} "
                "Source mode did not accept the committed target."
            ),
            "committed": True,
            "target": parent_target,
        },
    }
    assert result["mismatchFailure"] == {
        "createCount": 1,
        "events": [["create"]],
        "result": None,
        "error": {
            "message": (
                f"{expected_prefix} Create service target does not match "
                "its committed document."
            ),
            "committed": True,
            "target": None,
        },
    }
    assert result["requestedSource"] == {
        "success": child_target,
        "successRequests": [
            {
                "modeId": "markdown-source",
                "target": child_target,
            }
        ],
        "failure": "source mount failed",
        "failureRequests": [
            {
                "modeId": "markdown-source",
                "target": child_target,
                "force": False,
            },
            {
                "modeId": "rendered-document",
                "target": None,
                "force": True,
            },
        ],
    }
    assert result["messages"] == {
        "preCommit": "Create failed. source write failed",
        "postCommit": f"{expected_prefix} source mount failed",
    }


def assert_management_client_preserves_committed_error_payload(
    page: Page,
) -> None:
    result = page.evaluate(
        """async () => {
            const client = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-client.js'
            );
            const payload = {
                ok: false,
                operation: 'create',
                committed: true,
                retry_create: false,
                scope: 'studio',
                doc_id: 'created-parent',
                target: {
                    scope: 'studio',
                    doc_id: 'created-parent'
                },
                record: {
                    doc_id: 'created-parent',
                    title: 'Created parent'
                },
                error: 'projection rebuild failed'
            };
            let request = null;
            try {
                await client.createManagedDoc(
                    { title: 'Created parent', parent_id: '' },
                    {
                        baseUrl: 'http://127.0.0.1:9999',
                        scope: 'studio',
                        fetch: (url, options) => {
                            request = {
                                url,
                                method: options.method,
                                body: JSON.parse(options.body)
                            };
                            return Promise.resolve({
                                ok: false,
                                status: 500,
                                json: () => Promise.resolve(payload)
                            });
                        }
                    }
                );
            } catch (error) {
                return {
                    request,
                    status: error.status,
                    message: error.message,
                    payload: error.payload
                };
            }
            return { request, status: 0, message: '', payload: null };
        }"""
    )
    assert result == {
        "request": {
            "url": "http://127.0.0.1:9999/docs/create",
            "method": "POST",
            "body": {
                "scope": "studio",
                "title": "Created parent",
                "parent_id": "",
            },
        },
        "status": 500,
        "message": "projection rebuild failed",
        "payload": {
            "ok": False,
            "operation": "create",
            "committed": True,
            "retry_create": False,
            "scope": "studio",
            "doc_id": "created-parent",
            "target": {
                "scope": "studio",
                "doc_id": "created-parent",
            },
            "record": {
                "doc_id": "created-parent",
                "title": "Created parent",
            },
            "error": "projection rebuild failed",
        },
    }


def assert_document_mode_failure_callback(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import(
                '/docs-viewer/runtime/js/shared/docs-viewer-document-display-mode-host.js'
            );
            const actions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-actions.js'
            );
            const root = document.createElement('div');
            const warnings = [];
            const host = module.createDocsViewerDocumentDisplayModeHost({
                root,
                mount: document.createElement('div'),
                showWarning: (message, isError) => {
                    warnings.push([message, isError]);
                },
                viewRegistry: {
                    resolveMode: (modeId) => {
                        if (modeId === 'markdown-source') {
                            return {
                                available: true,
                                mode: {
                                    id: 'markdown-source',
                                    load: () => Promise.resolve({
                                        mount: () => Promise.reject(
                                            new Error('source mount failed')
                                        )
                                    })
                                }
                            };
                        }
                        return {
                            available: true,
                            mode: { id: 'rendered-document' }
                        };
                    }
                }
            });
            let failure = '';
            try {
                await actions.requestCommittedDocumentSource(
                    {
                        scope: 'studio',
                        doc_id: 'created-parent'
                    },
                    (modeId, options) => host.requestMode(modeId, options)
                );
            } catch (error) {
                failure = error.message;
            }
            await new Promise(resolve => window.setTimeout(resolve, 0));
            return {
                failure,
                activeMode: host.activeModeId(),
                projectedMode: root.dataset.documentDisplayMode,
                warnings
            };
        }"""
    )
    assert result == {
        "failure": "source mount failed",
        "activeMode": "rendered-document",
        "projectedMode": "rendered-document",
        "warnings": [["source mount failed", True]],
    }


def run_smoke(page: Page, base_url: str) -> None:
    page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded")
    assert_create_presentation_coordinator(page)
    assert_management_client_preserves_committed_error_payload(page)
    assert_document_mode_failure_callback(page)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".", help="Repo root to serve.")
    args = parser.parse_args(argv)

    server, base_url = start_static_server(Path(args.site_root))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                run_smoke(page, base_url)
                if errors:
                    raise AssertionError(f"page errors: {errors}")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    print("Docs Viewer management create modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
