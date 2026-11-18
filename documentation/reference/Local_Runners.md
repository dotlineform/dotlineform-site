---
draft: false
doc_id: d-20260422-174736-9bd0fc
title: Local Runners
added_date: "2026-04-22 17:47:36"
last_updated: "2026-11-18"
parent_id: d-20260413-000000-d314b7

---

# Local Runners

## Choose A Runner

| Command | Starts |
| --- | --- |
| `bin/local-studio` | Studio Catalogue authoring and its local APIs. |
| `docs-viewer/bin/docs-viewer` | Docs Viewer with generated reads and separately enabled Manage/Review. Export its environment for standalone startup. |
| `bin/site-preview` | The static `site/` preview after validation. |
| `bin/local-all` | The sibling services under one supervisor. |

Use the individual owner for a focused session and the supervisor for a cross-app session. [Environment and standalone Docs startup](Local_Setup.md#environment)

## Default Boundaries

| Surface | Default URL |
| --- | --- |
| Public preview | `http://127.0.0.1:4000/` |
| Studio | `http://127.0.0.1:8765/studio/catalogue-work/` |
| Docs Viewer | `http://127.0.0.1:8776/docs/` |
| Docs Review | `http://127.0.0.1:8776/docs-review/`, when enabled. |

Each service owns its pages and APIs. Studio links can point to the Docs reader or public preview through configured site bases. Changing one binding also requires keeping its consumer links aligned. [Configuration owners](Configuration_And_Extension_Points.md#find-the-owner)

## All-Services Runner

`bin/local-all` sources the local environment, checks configured enabled bindings for conflicts, then starts preview, Studio and Docs in that order. A child exit stops the other children and returns failure, including an unexpected clean exit. Ctrl+C stops the supervised session. Review defaults on in the supervisor.

The current implementation always starts the Studio runner, even when `STUDIO_APP_ENABLED=0`. That child exits immediately and the supervisor then stops its siblings. Until the logged code follow-up is settled, use the individual preview and Docs runners for a session without Studio. [Supervisor source](../../bin/local-all) · [Follow-up tracker](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups)

## Configuration

Studio uses `STUDIO_APP_HOST`, `STUDIO_APP_PORT`, `STUDIO_APP_ENABLED` and `STUDIO_APP_ACCESS_LOG`. Preview uses `SITE_HOST`, `SITE_PORT`, `SITE_ROOT`, `SITE_PYTHON` and `SITE_VALIDATE`; `SITE_ENABLED` controls supervisor inclusion. Docs uses `DOCS_VIEWER_HOST`, `DOCS_VIEWER_PORT` and `DOCS_VIEWER_BASE_URL` plus the process flags described in Local Setup.

`SITE_PREVIEW_BASE` can override the preview cross-link base. Studio's runtime projection derives its Docs link from the Docs host/port or explicit base URL. Docs derives its Studio link from the Studio host/port. Runner/service source owns the exact defaults and argument parsing. Access logging is opt-in. Ordinary successful requests are quiet, while error logging retains service, method, path and status. [Studio runner](../../bin/local-studio) · [Preview runner](../../bin/site-preview) · [Docs service](../../docs-viewer/services/docs_viewer_service.py) · [Studio projection](../../studio/app/server/studio/studio_app_config.py)

## Early Browser Disconnects

Studio, Docs Viewer and preview use the shared `IgnoreEarlyDisconnectMixin`. It suppresses a `ConnectionResetError` only before the first request line has been read. Header/body/application failures retain their error paths. Preview separately handles abandoned file responses. Restart the affected Python server after changing this code. [Shared boundary](../../studio/shared/python/local_http_logging.py)

### Focused Disconnect Test Coverage

The user approved this test specification on 2026-10-24. The exact selection is `studio/tests/python/test_local_http_disconnects.py`; no profile definition or existing test is changed. The existing `studio` profile discovers this file through its complete `studio/tests/python` directory selection; it has no separate entry in the smaller explicit profiles. The tests protect the phase boundary that separates harmless early resets from real request failures, using the production mixin and Python's real `BaseHTTPRequestHandler` parser/dispatch over in-memory socket substitutes.

| Selector | Input and expected outcome |
| --- | --- |
| `test_early_reset_closes_without_dispatch` | The first request-line read raises `ConnectionResetError`; construction completes with the connection marked closed, no application dispatch and no response. |
| `test_header_reset_propagates` | A valid GET request line is followed by a reset while reading headers; the error propagates before application dispatch. |
| `test_body_reset_propagates` | A POST with a declared body resets during the application's body read; the error propagates after dispatch, with no response. |
| `test_application_errors_propagate` | A parsed GET handler raises either `ConnectionResetError` or `RuntimeError`; the exact application exception propagates. |
| `test_normal_request_still_returns_response` | A complete GET reaches the handler and returns an ordinary HTTP 200 response with the expected body. |

The file owns its in-memory reader/socket and minimal GET/POST handler; there are no fixtures, application-service imports, real sockets, servers, ports, credentials, external workspace reads or writes. Only ordinary pytest/bytecode caches may be created. This selection proves the shared HTTP boundary, not real browser reset timing, application-route behavior, live stderr formatting or the three server classes' wiring; those integrations receive source review. Run `python3 -m pytest studio/tests/python/test_local_http_disconnects.py -q` when changing this boundary. Expected runtime is seconds with low setup/compute cost; maintenance is limited to this small stdlib adapter. Run once, then repeat only after a relevant change or failure. Code review and the selected run record complete this scope.

[Earlier run evidence](../deliveries/Runtime_Configuration_And_Recovery_Review.md#early-disconnect-delivery) records the accepted implementation and its limits.
